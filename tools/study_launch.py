#!/usr/bin/env python3
"""Foreground Seatbelt + study-broker launcher for LearningOS study sessions (PLAN-D D1/D3).

Replaces client-side hook AST/path parsing with an OS-enforced macOS Seatbelt
boundary (``/usr/bin/sandbox-exec``) paired with an unsandboxed AF_UNIX broker
(``tools/learning_os/adapters/study_broker.py``):

- Read-denies ``LearningOS/.env``, ``LearningOS/materials/``,
  ``LearningOS/reading-memory/``,
  ``generated/{text-cache,material-search,material-outlines,derived-state}/``,
  ``knowledge/summaries/``,
  and non-``.gitkeep`` children of ``operations/ai-actions/requests/``.
- Denies every write by default (D-02). Writes are allowed only to the
  session's scratch directory, ``/dev``, ``/private/tmp`` and the runtime
  state each runtime writes during a normal session (traced 2026-11-20:
  ``~/.claude/{projects,…}``, agy's conversation, transcript, log and cache
  paths, ``~/.codex/`` minus its config and code, npm's cache, and the
  keychain). ``LearningOS/``, every instruction, config or executable
  surface inside an allowed runtime root (``~/.claude/projects/*/memory``,
  ``~/.codex/{AGENTS*.md,config.toml,rules,skills,plugins,…}``, agy's
  settings, knowledge, MCP config and binaries) and the wrapper's
  instruction paths stay denied. A denylist on top of ``(allow default)``
  reopened the gap for every runtime or instruction file it did not name:
  ``CLAUDE.md`` in any parent folder, agy's MCP config, a CLI binary under
  ``~/.local/bin`` or Homebrew's prefix, ``~/Library/LaunchAgents``.
- Filters inherited host environment variables through an explicit allowlist
  (dropping unrelated secrets and host ``LOS_OBSERVATIONS``) before launch.
- Runs the child with ``cwd=LearningOS/repository``; for ``--cmd -- ...`` argv
  tokens (except inline code following ``-c``/``-e``/``-m``), rewrites
  caller-relative existing path tokens under ``caller_cwd`` that lie outside
  ``CORE`` to absolute paths while leaving non-existent path tokens relative.
- Allocates ``$LOS_SCRATCH_DIR`` (``$TMPDIR``) outside ``LearningOS/`` and mints
  an authoritative study session UUID before launching ``claude``, ``codex``,
  ``gemini``, ``agy``, or ``--cmd`` (ephemeral by default; pass
  ``--persist-scratch`` or ``--scratch-dir`` to retain a dedicated,
  ``.learningos-scratch.json``-owned, session-bound scratch directory across
  resumed launches until manually removed).
- Records ``ReadingStore.session_end`` and cleans up the socket in ``finally:``
  even on child crash or kill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import FrameType

from learning_os.adapters.process_group import terminate_process_group
from learning_os.adapters.study_broker import GATE_SOCK_ENV, BrokerServer, StudyBroker
from learning_os.store.materials.reading_cards import (
    ReadingStore,
    ReadingStoreError,
    valid_session,
)
from learning_os.store.study_fence import (
    is_within,
    protected_read_literals,
    protected_read_targets,
    protected_reads,
)

SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
LEARNINGOS_STUDY_NAMESPACE = uuid.UUID("7f3b0c4a-5e2d-4c8a-9b1f-3e6d1a2c4b8e")
RUNTIMES = ("claude", "codex", "gemini", "agy")
SCRATCH_MARKER_NAME = ".learningos-scratch.json"
_SCRATCH_MARKER_SCHEMA = 1
_SCRATCH_MARKER_OWNER = "learningos-study-scratch"

_CHILD_ENV_ALLOW_EXACT = frozenset({
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "TERM",
    "COLORTERM",
    "FORCE_COLOR",
    "NO_COLOR",
    "TERM_PROGRAM",
    "TERM_PROGRAM_VERSION",
    "LANG",
    "TZ",
    "PWD",
    "SHLVL",
    "TMPDIR",
    "VIRTUAL_ENV",
    "SSH_AUTH_SOCK",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "NODE_EXTRA_CA_CERTS",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONUTF8",
    "PYTHONIOENCODING",
    "MallocNanoZone",
})

_CHILD_ENV_ALLOW_PREFIXES = (
    "LC_",
    "XDG_",
    "__CF_",
    "ANTHROPIC_",
    "CLAUDE_",
    "OPENAI_",
    "CODEX_",
    "GEMINI_",
    "GOOGLE_",
    "AGY_",
)


def _build_child_env(
    host_env: Mapping[str, str],
    *,
    sock_path: Path,
    session_id: str,
    scratch_dir: Path,
    child_cwd: Path,
) -> dict[str, str]:
    """Filter inherited host env down to an explicit runtime/provider allowlist."""
    child_env = {
        k: v
        for k, v in host_env.items()
        if k in _CHILD_ENV_ALLOW_EXACT or k.startswith(_CHILD_ENV_ALLOW_PREFIXES)
    }
    child_env[GATE_SOCK_ENV] = str(sock_path)
    child_env["LOS_SESSION_ID"] = session_id
    child_env["LOS_SCRATCH_DIR"] = str(scratch_dir)
    child_env["TMPDIR"] = str(scratch_dir)
    child_env["PWD"] = str(child_cwd)
    child_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return child_env


def _sbpl_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def session_uuid_for_runtime(runtime: str, external_id: str) -> str:
    """Derive a deterministic lowercase UUIDv5 for non-UUID vendor handles."""
    return str(uuid.uuid5(LEARNINGOS_STUDY_NAMESPACE, f"{runtime}:{external_id}"))


_CLAUDE_WRITABLE_CACHE_SUBDIRS = (
    "projects",
    "debug",
    "todos",
    "tasks",
    "shell-snapshots",
    "file-history",
    "statsig",
    "session-env",
    "telemetry",
)

#: Paths every launch may write besides its scratch directory: terminals and
#: ``/dev/null``, and ``/private/tmp``, where Claude Code's Bash tool hands its
#: working directory back to the CLI.
_SYSTEM_WRITE_SUBPATHS = (Path("/dev"), Path("/private/tmp"))

#: Runtime state under ``$HOME`` that a study runtime writes during a normal
#: session, traced 2026-11-20 by diffing the home folder around one launch of
#: claude 2.1.283, agy 1.5.12 and codex 0.153.4. Writes anywhere else under
#: ``$HOME`` are denied by default, so a runtime that starts writing somewhere
#: new fails visibly instead of widening the boundary in silence.
_RUNTIME_WRITABLE_SUBDIRS = (
    # Claude Code's subdirectories are allowed in their own block below, after
    # ~/.claude is denied, so its project memory can be denied again last.
    # agy: conversations, transcripts, memory it records itself, logs, caches.
    ".gemini/antigravity-cli/conversations",
    ".gemini/antigravity-cli/brain",
    ".gemini/antigravity-cli/annotations",
    ".gemini/antigravity-cli/implicit",
    ".gemini/antigravity-cli/presence",
    ".gemini/antigravity-cli/log",
    ".gemini/antigravity-cli/cache",
    ".gemini/antigravity-cli/crashes",
    ".gemini/antigravity-cli/scratch",
    ".gemini/tmp",
    ".gemini/history",
    "Library/Logs/Antigravity",
    # npx, which runtimes use to start MCP servers; npm verifies its cache.
    ".npm/_cacache",
    ".npm/_logs",
    ".npm/_npx",
    # Credential refreshes go through the login keychain.
    "Library/Keychains",
    # Codex keeps sessions and SQLite state directly under ~/.codex; its
    # read-only surfaces are re-denied in _RUNTIME_READ_ONLY.
    ".codex",
)
_SQLITE_SIDECARS = ("", "-wal", "-shm", "-journal")
_RUNTIME_WRITABLE_FILES = (
    *(f".gemini/antigravity-cli/conversation_summaries.db{s}" for s in _SQLITE_SIDECARS),
    ".gemini/antigravity-cli/jetbox_summaries_proto.pb",
    ".gemini/antigravity-cli/jetski_state.pbtxt",
    ".gemini/antigravity-cli/last_check.timestamp",
    ".gemini/antigravity-cli/cli.log",
    *(f".gemini/antigravity/conversation_summaries.db{s}" for s in _SQLITE_SIDECARS),
    ".gemini/antigravity/agyhub_summaries_proto.pb",
)
# Not allowed, on purpose: agy saves its credential-scope cache through a
# randomly named temp file inside the Antigravity IDE's own app-data folder,
# which also holds the IDE's settings and extensions. agy logs the refusal and
# runs normally (verified 2026-11-20).
#: Instruction, configuration and executable surfaces inside an allowed
#: runtime root. A runtime only reads these; a write would reach the next
#: session that loads them, sandboxed or not.
_RUNTIME_READ_ONLY = (
    ".codex/AGENTS.md",
    ".codex/AGENTS.override.md",
    ".codex/config.toml",
    ".codex/rules",
    ".codex/skills",
    ".codex/plugins",
    ".codex/prompts",
    ".codex/automations",
    ".codex/hooks",
    ".codex/hooks.json",
)


_CLAUDE_PROJECT_SLUG_UNSAFE = re.compile(r"[^A-Za-z0-9-]")


def _claude_project_slug(path: Path) -> str:
    return _CLAUDE_PROJECT_SLUG_UNSAFE.sub("-", str(path))


def _add_write_deny_target(
    lines: list[str],
    seen: set[Path],
    target: Path,
    *,
    real_learningos: Path,
) -> None:
    resolved = Path(os.path.realpath(target))
    for candidate in dict.fromkeys((target, resolved)):
        if (
            candidate == Path("/")
            or is_within(candidate, real_learningos)
            or is_within(real_learningos, candidate)
            or candidate in seen
        ):
            continue
        seen.add(candidate)
        lines.append(f'(deny file-write* (subpath "{_sbpl_quote(str(candidate))}"))')


def build_seatbelt_profile(
    core_root: Path,
    *,
    deny_extra_subpaths: Sequence[Path] = (),
    deny_extra_literals: Sequence[Path] = (),
    home_dir: Path | None = None,
    write_roots: Sequence[Path] = (),
) -> str:
    """Generate a non-regex macOS Seatbelt profile for one LearningOS checkout.

    Seatbelt applies the last rule that matches, so the order is the policy:
    reads are open except the protected trees; every write is denied; the
    scratch directory (``write_roots``), ``/dev``, ``/private/tmp`` and the
    traced runtime state are allowed back; and the surfaces that must never be
    written (``LearningOS/``, memory and instruction files inside allowed
    runtime roots, the stage directory) are denied again last.
    """
    real_core = Path(os.path.realpath(Path(core_root).resolve()))
    real_learningos = Path(os.path.realpath(real_core.parent))
    real_wrapper = real_learningos.parent
    requests_dir = real_core / "operations" / "ai-actions" / "requests"
    real_req = Path(os.path.realpath(requests_dir))
    real_gitkeep = real_req / ".gitkeep"

    lines = [
        "(version 1)",
        "(allow default)",
    ]
    for closed in protected_reads(real_core):
        real_closed = Path(os.path.realpath(closed))
        lines.append(f'(deny file-read* (subpath "{_sbpl_quote(str(real_closed))}"))')
    lines.append(
        '(allow file-read* '
        f'(literal "{_sbpl_quote(str(real_req))}") '
        f'(literal "{_sbpl_quote(str(real_gitkeep))}"))'
    )
    for lit in protected_read_literals(real_core):
        lex_lit = real_learningos / lit.name if lit.parent == real_core.parent else Path(lit)
        real_lit = Path(os.path.realpath(lit))
        for candidate in dict.fromkeys((lex_lit, real_lit)):
            lines.append(f'(deny file-read* (literal "{_sbpl_quote(str(candidate))}"))')

    # Every write is denied unless a later rule allows it back (D-02).
    lines.append("(deny file-write*)")
    allow_parts = [
        f'(subpath "{_sbpl_quote(str(Path(os.path.realpath(root))))}")'
        for root in (*_SYSTEM_WRITE_SUBPATHS, *write_roots)
    ]
    lines.append(f"(allow file-write* {' '.join(dict.fromkeys(allow_parts))})")

    deny_seen: set[Path] = set()
    real_home = Path(os.path.realpath(home_dir if home_dir is not None else Path.home()))
    home_ok = (
        real_home != Path("/")
        and real_home != real_learningos
        and not is_within(real_home, real_learningos)
    )
    if home_ok and real_home != real_wrapper:
        runtime_parts = [
            f'(subpath "{_sbpl_quote(str(real_home / rel))}")'
            for rel in _RUNTIME_WRITABLE_SUBDIRS
        ] + [
            f'(literal "{_sbpl_quote(str(real_home / rel))}")'
            for rel in _RUNTIME_WRITABLE_FILES
        ]
        lines.append(f"(allow file-write* {' '.join(runtime_parts)})")

    # Denied again after the allows, whatever root it sits in: LearningOS/
    # itself, then memory, instruction, configuration and code surfaces.
    lines.append(f'(deny file-write* (subpath "{_sbpl_quote(str(real_learningos))}"))')
    if home_ok:
        claude_dir = real_home / ".claude"
        lines.append(f'(deny file-write* (subpath "{_sbpl_quote(str(claude_dir))}"))')
        if real_home != real_wrapper:
            claude_allow = " ".join(
                f'(subpath "{_sbpl_quote(str(claude_dir / sub))}")'
                for sub in _CLAUDE_WRITABLE_CACHE_SUBDIRS
            )
            lines.append(f"(allow file-write* {claude_allow})")
            claude_projects = claude_dir / "projects"
            memory_targets: list[Path] = []
            if claude_projects.is_dir():
                for entry in sorted(claude_projects.iterdir(), key=lambda p: p.name):
                    if entry.is_dir():
                        memory_targets.append(entry / "memory")
            for workspace_root in (real_wrapper, real_learningos, real_core):
                memory_targets.append(
                    claude_projects / _claude_project_slug(workspace_root) / "memory"
                )
            for memory_dir in memory_targets:
                _add_write_deny_target(
                    lines, deny_seen, memory_dir, real_learningos=real_learningos
                )
        for read_only in _RUNTIME_READ_ONLY:
            _add_write_deny_target(
                lines, deny_seen, real_home / read_only, real_learningos=real_learningos
            )
        for user_instr in (
            real_home / ".claude.json",
            real_home / ".claude.json.backup",
            real_home / ".zshrc",
            real_home / ".zshenv",
            real_home / ".zprofile",
            real_home / ".zlogin",
            real_home / ".zlogout",
            real_home / ".bashrc",
            real_home / ".bash_profile",
            real_home / ".bash_login",
            real_home / ".profile",
            real_home / ".codex" / "AGENTS.md",
            real_home / ".codex" / "AGENTS.override.md",
            real_home / ".codex" / "config.toml",
            real_home / ".codex" / "rules",
            real_home / ".codex" / "skills",
            real_home / ".gemini" / "GEMINI.md",
            real_home / ".gemini" / "settings.json",
            real_home / ".gemini" / "skills",
            real_home / ".agents",
            real_home / ".config" / "opencode",
        ):
            _add_write_deny_target(
                lines, deny_seen, user_instr, real_learningos=real_learningos
            )

    for wrapper_instr in (
        real_wrapper / "AGENTS.md",
        real_wrapper / "CLAUDE.md",
        real_wrapper / "CLAUDE.local.md",
        real_wrapper / "GEMINI.md",
        real_wrapper / ".mcp.json",
        real_wrapper / ".claude",
        real_wrapper / ".opencode",
        real_wrapper / ".codex",
        real_wrapper / ".gemini",
    ):
        _add_write_deny_target(
            lines, deny_seen, wrapper_instr, real_learningos=real_learningos
        )

    for extra in deny_extra_subpaths:
        real_extra = Path(os.path.realpath(extra))
        quoted = _sbpl_quote(str(real_extra))
        lines.append(f'(deny file-read* (subpath "{quoted}"))')
        lines.append(f'(deny file-write* (subpath "{quoted}"))')
    for extra_literal in deny_extra_literals:
        real_lit = Path(os.path.realpath(extra_literal))
        lines.append(f'(deny file-write* (literal "{_sbpl_quote(str(real_lit))}"))')
    return "\n".join(lines) + "\n"


_RUNTIME_PATH_FLAGS = ("--settings", "--mcp-config", "--plugin-dir", "--add-dir")


def _is_relative_path_token(value: str) -> bool:
    if not value or len(value) >= 1024 or "\n" in value or value.startswith(("~", "-")):
        return False
    candidate = Path(value)
    if candidate.is_absolute():
        return False
    return (
        "/" in value
        or (os.altsep is not None and os.altsep in value)
        or value in (".", "..")
        or value.startswith(("./", "../"))
    )


def _resolve_caller_path(
    value: str,
    *,
    caller_cwd: Path,
    real_core: Path,
    protected: Sequence[Path] = (),
) -> str:
    if not value or len(value) >= 1024 or "\n" in value or value.startswith("~"):
        return value
    candidate = Path(value)
    if candidate.is_absolute():
        return value
    try:
        if (real_core / candidate).exists():
            return value
        caller_target = caller_cwd / candidate
        if not caller_target.exists():
            return value
        real_target = Path(os.path.realpath(caller_target))
    except OSError:
        return value
    if any(is_within(real_target, closed) for closed in protected):
        return value
    # Keep symlinks intact (e.g. .venv/bin/python -> homebrew python) while making the path absolute.
    return os.path.abspath(caller_target)


def _normalize_caller_args(
    extra: Sequence[str],
    *,
    caller_cwd: Path,
    real_core: Path,
) -> list[str]:
    if caller_cwd == real_core:
        return list(extra)
    protected = tuple(Path(os.path.realpath(p)) for p in protected_read_targets(real_core))
    out: list[str] = []
    expect_path = False
    for token in extra:
        if expect_path:
            out.append(
                _resolve_caller_path(
                    token, caller_cwd=caller_cwd, real_core=real_core, protected=protected
                )
            )
            expect_path = False
            continue
        if token in _RUNTIME_PATH_FLAGS:
            out.append(token)
            expect_path = True
            continue
        rewritten = token
        for flag in _RUNTIME_PATH_FLAGS:
            prefix = f"{flag}="
            if token.startswith(prefix):
                rewritten = prefix + _resolve_caller_path(
                    token[len(prefix):],
                    caller_cwd=caller_cwd,
                    real_core=real_core,
                    protected=protected,
                )
                break
        out.append(rewritten)
    return out


def _normalize_cmd_args(
    command: Sequence[str],
    *,
    caller_cwd: Path,
    real_core: Path,
) -> list[str]:
    if caller_cwd == real_core:
        return list(command)
    protected = tuple(Path(os.path.realpath(p)) for p in protected_read_targets(real_core))
    out: list[str] = []
    prev_token = ""
    for idx, token in enumerate(command):
        if prev_token in ("-c", "-e", "-m") and idx > 0:
            out.append(token)
            prev_token = token
            continue
        if token.startswith("--") and "=" in token:
            flag, raw_val = token.split("=", 1)
            if _is_relative_path_token(raw_val):
                resolved = _resolve_caller_path(
                    raw_val, caller_cwd=caller_cwd, real_core=real_core, protected=protected
                )
                token = f"{flag}={resolved}"
        elif _is_relative_path_token(token):
            token = _resolve_caller_path(
                token, caller_cwd=caller_cwd, real_core=real_core, protected=protected
            )
        out.append(token)
        prev_token = token
    return out


def _resolve_runtime_command(
    *,
    runtime: str | None,
    use_cmd: bool,
    extra: Sequence[str],
    caller_cwd: Path | None = None,
    real_core: Path | None = None,
) -> list[str]:
    tail = list(extra)
    if tail and tail[0] == "--":
        tail = tail[1:]
    if use_cmd:
        if not tail:
            raise ValueError("--cmd requires a command to execute")
        if caller_cwd is not None and real_core is not None:
            return _normalize_cmd_args(tail, caller_cwd=caller_cwd, real_core=real_core)
        return tail
    assert runtime is not None
    if caller_cwd is not None and real_core is not None:
        tail = _normalize_caller_args(tail, caller_cwd=caller_cwd, real_core=real_core)
    binary = shutil.which(runtime)
    if binary is None:
        raise ValueError(f"runtime binary {runtime!r} was not found on PATH")
    binary_path = os.path.abspath(binary)
    if runtime == "codex":
        return [
            binary_path,
            "-s",
            "danger-full-access",
            "-c",
            "shell_environment_policy.inherit=all",
            *tail,
        ]
    return [binary_path, *tail]


def _allocate_outside_dir(prefix: str, real_learningos: Path) -> Path:
    candidate = Path(os.path.realpath(tempfile.mkdtemp(prefix=prefix)))
    if is_within(candidate, real_learningos):
        shutil.rmtree(candidate, ignore_errors=True)
        candidate = Path(
            os.path.realpath(tempfile.mkdtemp(prefix=prefix, dir="/tmp"))
        )
    return candidate


def _allocate_scratch_dir(real_learningos: Path) -> Path:
    return _allocate_outside_dir("los-study-scratch-", real_learningos)


def _persistent_scratch_path(real_learningos: Path, session_id: str) -> Path:
    base = Path(os.path.realpath(tempfile.gettempdir()))
    if is_within(base, real_learningos):
        base = Path(os.path.realpath("/tmp"))
    token = hashlib.sha256(
        f"{os.geteuid()}:{real_learningos}:{session_id}".encode()
    ).hexdigest()[:16]
    return base / f"los-study-scratch-{os.geteuid()}-{token}"


def _validate_scratch_marker(
    marker: Path,
    *,
    real_learningos: Path,
    session_id: str,
) -> None:
    try:
        lstat = os.lstat(marker)
    except FileNotFoundError as exc:
        raise ValueError(
            f"refusing existing directory without LearningOS scratch marker "
            f"({SCRATCH_MARKER_NAME}): {marker.parent}; pass a fresh path so "
            "LearningOS can initialize a dedicated scratch directory"
        ) from exc
    if stat.S_ISLNK(lstat.st_mode) or not stat.S_ISREG(lstat.st_mode):
        raise ValueError(f"scratch ownership marker must be a regular file: {marker}")
    if lstat.st_uid != os.geteuid():
        raise ValueError(f"scratch ownership marker must be owned by current user: {marker}")
    if (lstat.st_mode & 0o077) != 0:
        raise ValueError(
            f"scratch ownership marker has unsafe permissions "
            f"({oct(stat.S_IMODE(lstat.st_mode))}): {marker}"
        )
    try:
        fd = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            raw: object = json.loads(handle.read())
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"unreadable scratch ownership marker {marker}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"invalid scratch ownership marker {marker}: expected JSON object")
    if raw.get("schema") != _SCRATCH_MARKER_SCHEMA or raw.get("owner") != _SCRATCH_MARKER_OWNER:
        raise ValueError(
            f"scratch directory is not initialized for LearningOS study scratch: {marker.parent}"
        )
    recorded_learningos = raw.get("learningos")
    if recorded_learningos != str(real_learningos):
        raise ValueError(
            f"scratch directory belongs to LearningOS root {recorded_learningos!r}, "
            f"refusing reuse for {real_learningos}"
        )
    recorded_session = raw.get("session_id")
    if recorded_session != session_id:
        raise ValueError(
            f"scratch directory belongs to study session {recorded_session!r}, "
            f"refusing reuse by session {session_id!r}"
        )


def _write_scratch_marker(
    marker: Path,
    *,
    real_learningos: Path,
    session_id: str,
    mode: str,
) -> None:
    payload = {
        "schema": _SCRATCH_MARKER_SCHEMA,
        "owner": _SCRATCH_MARKER_OWNER,
        "learningos": str(real_learningos),
        "session_id": session_id,
        "mode": mode,
    }
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def _prepare_persistent_scratch_dir(
    path: Path,
    real_learningos: Path,
    *,
    session_id: str,
    mode: str,
) -> Path:
    expanded = Path(os.path.abspath(path.expanduser()))
    if expanded.is_symlink():
        raise ValueError(f"scratch directory must not be a symlink: {expanded}")
    candidate = Path(os.path.realpath(expanded))
    if is_within(candidate, real_learningos):
        raise ValueError(f"scratch directory must live outside LearningOS/: {candidate}")
    forbidden = {
        Path(os.path.realpath("/")),
        Path(os.path.realpath("/tmp")),
        Path(os.path.realpath(tempfile.gettempdir())),
        Path(os.path.realpath(Path.home())),
    }
    if candidate in forbidden:
        raise ValueError(f"scratch directory must be a dedicated subdirectory: {candidate}")

    marker = candidate / SCRATCH_MARKER_NAME
    try:
        st = os.lstat(candidate)
    except FileNotFoundError:
        candidate.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            os.mkdir(candidate, 0o700)
        except FileExistsError as exc:
            raise ValueError(f"scratch directory already exists unexpectedly: {candidate}") from exc
        try:
            os.chmod(candidate, 0o700)
            _write_scratch_marker(
                marker, real_learningos=real_learningos, session_id=session_id, mode=mode
            )
        except Exception:
            shutil.rmtree(candidate, ignore_errors=True)
            raise
        return Path(os.path.realpath(candidate))

    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ValueError(f"scratch directory must be a real directory: {candidate}")
    if st.st_uid != os.geteuid():
        raise ValueError(f"scratch directory must be owned by current user: {candidate}")
    _validate_scratch_marker(marker, real_learningos=real_learningos, session_id=session_id)
    if (st.st_mode & 0o077) != 0:
        raise ValueError(
            f"scratch directory has unsafe permissions "
            f"({oct(stat.S_IMODE(st.st_mode))}): {candidate}"
        )
    return candidate


def _resolve_session_id(
    *,
    explicit_session: str | None,
    resume_runtime_id: str | None,
    runtime_tag: str,
) -> str:
    if explicit_session is not None and resume_runtime_id is not None:
        raise ValueError("--session and --resume-runtime-id are mutually exclusive")
    if explicit_session is not None:
        if not valid_session(explicit_session):
            raise ValueError(f"--session must be a valid lowercase UUID, got {explicit_session!r}")
        return explicit_session
    if resume_runtime_id is not None:
        trimmed = resume_runtime_id.strip()
        if not trimmed:
            raise ValueError("--resume-runtime-id cannot be blank")
        return session_uuid_for_runtime(runtime_tag, trimmed)
    return str(uuid.uuid4())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="LearningOS repository root (default: the checkout holding tools/)",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--runtime",
        choices=RUNTIMES,
        default=None,
        help="run an interactive/headless agent CLI under the study boundary",
    )
    target.add_argument(
        "--cmd",
        action="store_true",
        help="run the trailing command under the study boundary (e.g. --cmd -- sh -c ...)",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="resume an explicit lowercase study session UUID",
    )
    parser.add_argument(
        "--resume-runtime-id",
        default=None,
        help="derive a deterministic UUIDv5 session from an external vendor handle",
    )
    scratch = parser.add_mutually_exclusive_group()
    scratch.add_argument(
        "--persist-scratch",
        action="store_true",
        help=(
            "initialize and retain a dedicated per-session $LOS_SCRATCH_DIR "
            "(.learningos-scratch.json-marked) across resumed launches; remove it manually when done"
        ),
    )
    scratch.add_argument(
        "--scratch-dir",
        default=None,
        help=(
            "initialize and retain a dedicated host scratch path outside LearningOS/ for this "
            "session only (refuses existing unrelated or other-session dirs; remove manually when done)"
        ),
    )
    parser.add_argument(
        "target_args",
        nargs=argparse.REMAINDER,
        help="arguments forwarded to the runtime or --cmd command",
    )
    return parser


def launch_study(
    *,
    core_root: Path,
    command: list[str],
    session_id: str,
    sandbox_exec: Path | None = None,
    platform: str = sys.platform,
    cwd: Path | None = None,
    persist_scratch: bool = False,
    scratch_dir_override: Path | None = None,
) -> int:
    """Start the host study broker, execute ``command`` inside Seatbelt, and reap session state."""
    effective_sandbox = SANDBOX_EXEC if sandbox_exec is None else sandbox_exec
    if platform != "darwin" or not effective_sandbox.is_file():
        print(
            "study_launch: failing closed — macOS /usr/bin/sandbox-exec is required",
            file=sys.stderr,
        )
        return 2

    real_core = Path(os.path.realpath(core_root.resolve()))
    real_learningos = Path(os.path.realpath(real_core.parent))
    child_cwd = (
        Path(os.path.realpath(Path(cwd).resolve())) if cwd is not None else real_core
    )
    if not child_cwd.is_dir():
        print(
            f"study_launch: working directory does not exist: {child_cwd}",
            file=sys.stderr,
        )
        return 2
    store = ReadingStore(real_core)

    session_started = False
    scratch_dir: Path | None = None
    keep_scratch = persist_scratch or (scratch_dir_override is not None)
    sock_dir: Path | None = None
    stage_dir: Path | None = None
    server: BrokerServer | None = None
    proc: subprocess.Popen[bytes] | None = None
    terminated_by_signal = False
    sigterm_installed = False
    prev_sigterm = signal.getsignal(signal.SIGTERM)

    def _terminate_group(active: subprocess.Popen[bytes], *, force: bool = False) -> None:
        """Terminate the launcher child's whole process group (shared impl)."""
        if force:
            import contextlib as _ctx
            if active.poll() is not None:
                return
            with _ctx.suppress(OSError, ProcessLookupError):
                os.killpg(os.getpgid(active.pid), signal.SIGKILL)
            with _ctx.suppress(subprocess.TimeoutExpired):
                active.wait(timeout=5)
            return
        terminate_process_group(active, grace_s=5.0)

    def _on_sigterm(_signum: int, _frame: FrameType | None) -> None:
        nonlocal terminated_by_signal
        terminated_by_signal = True
        if proc is not None and proc.poll() is None:
            import contextlib as _ctx
            with _ctx.suppress(OSError, ProcessLookupError):
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

    try:
        if scratch_dir_override is not None:
            try:
                scratch_dir = _prepare_persistent_scratch_dir(
                    scratch_dir_override,
                    real_learningos,
                    session_id=session_id,
                    mode="explicit-scratch-dir",
                )
            except (ValueError, OSError) as exc:
                print(f"study_launch: {exc}", file=sys.stderr)
                return 2
        elif persist_scratch:
            try:
                scratch_dir = _prepare_persistent_scratch_dir(
                    _persistent_scratch_path(real_learningos, session_id),
                    real_learningos,
                    session_id=session_id,
                    mode="persist-scratch",
                )
            except (ValueError, OSError) as exc:
                print(f"study_launch: {exc}", file=sys.stderr)
                return 2

        try:
            store.touch(session_id, start=True)
            session_started = True
        except ReadingStoreError as exc:
            print(f"study_launch: reading store unavailable: {exc}", file=sys.stderr)
            return 2

        if scratch_dir is None:
            scratch_dir = _allocate_scratch_dir(real_learningos)
        sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losg-", dir="/tmp")))
        stage_dir = _allocate_outside_dir("losb-", real_learningos)
        sock_path = sock_dir / "gate.sock"
        sb_path = sock_dir / "study.sb"
        deny_literals = (scratch_dir / SCRATCH_MARKER_NAME,) if keep_scratch else ()
        home_override = Path(os.environ["HOME"]) if os.environ.get("HOME") else None
        sb_path.write_text(
            build_seatbelt_profile(
                real_core,
                deny_extra_subpaths=(stage_dir,),
                deny_extra_literals=deny_literals,
                home_dir=home_override,
                write_roots=(scratch_dir,),
            ),
            encoding="utf-8",
        )

        broker = StudyBroker(
            real_core,
            session_id,
            scratch_dir=scratch_dir,
            stage_root=stage_dir,
            observations_path=os.environ.get("LOS_OBSERVATIONS"),
        )
        server = BrokerServer(broker, sock_path)
        server.start()

        child_env = _build_child_env(
            os.environ,
            sock_path=sock_path,
            session_id=session_id,
            scratch_dir=scratch_dir,
            child_cwd=child_cwd,
        )

        signal.signal(signal.SIGTERM, _on_sigterm)
        sigterm_installed = True

        proc = subprocess.Popen(
            [str(effective_sandbox), "-f", str(sb_path), *command],
            env=child_env,
            cwd=str(child_cwd),
            start_new_session=True,
        )
        exit_code = proc.wait()
        return 143 if terminated_by_signal and exit_code < 0 else exit_code
    except KeyboardInterrupt:
        if proc is not None and proc.poll() is None:
            _terminate_group(proc)
        return 130
    finally:
        if sigterm_installed:
            signal.signal(signal.SIGTERM, prev_sigterm)
        if proc is not None and proc.poll() is None:
            _terminate_group(proc)
        if server is not None:
            server.close()
        if session_started:
            try:
                ReadingStore(real_core).session_end(session_id)
            except ReadingStoreError as exc:
                print(f"study_launch: failed to record session_end: {exc}", file=sys.stderr)
        if stage_dir is not None:
            shutil.rmtree(stage_dir, ignore_errors=True)
        if sock_dir is not None:
            shutil.rmtree(sock_dir, ignore_errors=True)
        if scratch_dir is not None and not keep_scratch:
            shutil.rmtree(scratch_dir, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    caller_cwd = Path(os.path.realpath(Path.cwd()))
    core_root = (
        Path(args.root).expanduser().resolve()
        if args.root
        else Path(__file__).resolve().parent.parent
    )
    real_core = Path(os.path.realpath(core_root))
    runtime_tag = args.runtime or "cmd"
    scratch_override: Path | None = None
    if args.scratch_dir is not None:
        raw_scratch = Path(args.scratch_dir).expanduser()
        scratch_override = raw_scratch if raw_scratch.is_absolute() else caller_cwd / raw_scratch
    try:
        command = _resolve_runtime_command(
            runtime=args.runtime,
            use_cmd=bool(args.cmd),
            extra=args.target_args,
            caller_cwd=caller_cwd,
            real_core=real_core,
        )
        session_id = _resolve_session_id(
            explicit_session=args.session,
            resume_runtime_id=args.resume_runtime_id,
            runtime_tag=runtime_tag,
        )
    except ValueError as exc:
        print(f"study_launch: {exc}", file=sys.stderr)
        return 2
    return launch_study(
        core_root=core_root,
        command=command,
        session_id=session_id,
        cwd=real_core,
        persist_scratch=bool(args.persist_scratch),
        scratch_dir_override=scratch_override,
    )


if __name__ == "__main__":
    raise SystemExit(main())
