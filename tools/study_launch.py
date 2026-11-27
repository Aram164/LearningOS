#!/usr/bin/env python3
"""Foreground Seatbelt + study-broker launcher for LearningOS study sessions (PLAN-D D1/D3).

Replaces client-side hook AST/path parsing with an OS-enforced macOS Seatbelt
boundary (``/usr/bin/sandbox-exec``) paired with an unsandboxed AF_UNIX broker
(``tools/learning_os/adapters/study_broker.py``):

- Read-denies ``LearningOS/.env``, ``LearningOS/materials/``,
  ``LearningOS/reading-memory/``,
  ``generated/{.text-cache,material-search,material-outlines,derived-state}/``,
  ``knowledge/summaries/``,
  and non-``.gitkeep`` children of ``operations/ai-actions/requests/``.
- Denies every write by default (D-02). Writes are allowed only to the
  session's scratch directory, ``/dev``, ``/private/tmp`` and the state of
  the runtime being launched. Claude Code and Codex get a home of their own
  for each study session (``CLAUDE_CONFIG_DIR``, ``CODEX_HOME``) under
  ``~/.local/state/learningos/study-runtimes/``, so their transcripts,
  caches and settings never reach Aram's real ``~/.claude`` or ``~/.codex``.
  Claude Code writes nothing in the real home folder: it runs on a dedicated
  study token (``~/.config/learningos/claude_study_token`` ->
  ``CLAUDE_CODE_OAUTH_TOKEN``), and ``~/.config/learningos`` is read- and
  write-denied in every launch. Codex keeps only ``auth.json`` linked to the
  real login (at versions verified to save it in place). agy and the Gemini CLI
  have no such home, so their launches keep the traced path rules (ADR-022 §3). ``LearningOS/``,
  every instruction, config or executable surface in the real runtime
  folders and the wrapper's instruction paths stay denied. A denylist on
  top of ``(allow default)`` reopened the gap for every runtime or
  instruction file it did not name: ``CLAUDE.md`` in any parent folder,
  agy's MCP config, a CLI binary under ``~/.local/bin`` or Homebrew's
  prefix, ``~/Library/LaunchAgents``.
- Filters inherited host environment variables by exact name (POSIX,
  terminal, proxy and certificate settings, and each provider's credentials,
  endpoint and model choice) plus the locale, XDG and CoreFoundation
  prefixes. Unrelated secrets, host ``LOS_OBSERVATIONS`` and every variable a
  host Claude Code or Codex session sets for its children (its messaging
  socket and token, ids, notes folder, feature flags) are dropped, and so is
  ``SSH_AUTH_SOCK``.
- Denies connecting to the host's SSH agent socket and to any unix socket
  under ``~/.ssh``; the study gate and other sockets stay reachable.
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
- Keeps each Claude Code or Codex home after the session, keyed by the study
  session UUID, so a resumed launch (``--session`` or
  ``--resume-runtime-id``) finds its transcript again; ``--resume-runtime-id``
  also finds the one home whose transcripts carry that vendor id. Homes unused
  for 30 days are removed at the next Claude Code or Codex launch.
- Runs Codex only at versions verified to save ``auth.json`` in place, which
  the study home's login link depends on; any other version is refused.
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
import time
import tomllib
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import FrameType

from learning_os.adapters.process_group import terminate_process_group
from learning_os.adapters.study_broker import GATE_SOCK_ENV, BrokerServer, StudyBroker
from learning_os.store.contracts.write_scopes import (
    WriteScopeError,
    guard_tool_output_path,
    scoped_write_target,
)
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

#: Runtimes that get a home of their own for each study session instead of
#: Aram's real ``~/.claude`` or ``~/.codex`` (ADR-022 §3, 2026-11-20). agy
#: has no home override and the Gemini CLI cannot sign in any more, so both
#: keep path rules.
HOMED_RUNTIMES = ("claude", "codex")
RUNTIME_HOME_MARKER_NAME = ".learningos-runtime-home.json"
_RUNTIME_HOME_MARKER_SCHEMA = 1
_RUNTIME_HOME_MARKER_OWNER = "learningos-study-runtime-home"
#: Where the homes live, relative to ``$HOME``: no spaces, because both
#: runtimes build shell-snapshot and temp paths under their home, and kept
#: across reboots, so a resumed launch still finds its transcript.
_RUNTIME_HOMES_REL = Path(".local") / "state" / "learningos" / "study-runtimes"
#: A vendor session id the resume lookup may search for (Claude Code and
#: Codex use UUIDs); anything else skips the lookup.
_VENDOR_ID_SAFE = re.compile(r"[A-Za-z0-9._-]{1,128}")
#: Display and model preferences copied from the real Claude Code settings
#: into a new home. Hooks, permissions, ``env``, plugins, marketplaces, the
#: status line, API-key helpers and MCP servers are never copied: each runs
#: code or adds instructions.
_CLAUDE_SETTINGS_COPY = ("model", "effortLevel", "theme", "tui", "modelSettings")
#: Onboarding state copied from the real ``~/.claude.json``, so an
#: interactive launch shows no first-run dialog.
_CLAUDE_GLOBAL_COPY = ("hasCompletedOnboarding", "lastOnboardingVersion")
#: Preference strings copied from the real Codex config. Its ``notify``
#: program, plugins, MCP servers and global model are not.
_CODEX_CONFIG_COPY = ("personality", "service_tier")
#: A study home whose last launch is older than this is removed at the next
#: Claude Code or Codex launch (2026-11-21). It is Claude Code's own default
#: transcript retention (``cleanupPeriodDays``), after which the transcripts
#: a resume needs are gone anyway. The home being launched or resumed is
#: never removed: the lookup runs first and every launch refreshes the
#: home's marker.
_RUNTIME_HOME_RETENTION_DAYS = 30
#: Codex versions verified to save ``auth.json`` in place (opened with
#: truncate and written, never replaced by a renamed temp file): read in
#: ``FileAuthStorage::save``, ``codex-rs/login/src/auth/storage.rs``, at the
#: release tag. A study home's login is a link to the real ``auth.json`` and
#: depends on exactly that, so any other version is refused (ADR-022 §3).
_CODEX_IN_PLACE_AUTH_VERSIONS = frozenset({"0.153.4"})
#: The SSH agent: its variable is not forwarded, and connecting to its socket,
#: or to any socket under ``~/.ssh`` (OpenSSH's default ``agent/`` folder,
#: ControlMaster sockets), is denied. Reads are open, so a study agent could
#: find the socket without the variable and sign with Aram's keys: push to
#: his repositories, log in to his hosts (2026-11-21).
_SSH_AGENT_ENV = "SSH_AUTH_SOCK"
#: Where the dedicated study token lives (2026-11-21): Aram mints it with
#: ``claude setup-token`` and saves it here, mode 0600. A Claude Code launch
#: runs on it instead of his interactive login. The launcher reads it
#: unsandboxed; inside every launch the whole folder is read- and
#: write-denied.
_STUDY_SECRETS_REL = Path(".config") / "learningos"
_CLAUDE_STUDY_TOKEN_REL = _STUDY_SECRETS_REL / "claude_study_token"
_CLAUDE_STUDY_TOKEN_MAX_BYTES = 4096
_CLAUDE_TOKEN_ENV = "CLAUDE_CODE_OAUTH_TOKEN"
#: Variables the launcher sets for the runtime it starts. Host values are
#: dropped for every launch, even if a later allowlist entry would admit one:
#: each would point a runtime back at a shared folder or login. A host
#: ``CLAUDE_CODE_OAUTH_TOKEN`` included: a Claude Code launch gets the study
#: token instead, and no other launch needs one.
_RUNTIME_HOME_ENV = (
    "CLAUDE_CONFIG_DIR",
    "CLAUDE_SECURESTORAGE_CONFIG_DIR",
    "CLAUDE_CODE_TMPDIR",
    _CLAUDE_TOKEN_ENV,
    "CODEX_HOME",
)

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

#: What a study runtime may take from the host about its provider, scoped by
#: runtime name (amended 2026-11-21). Vendor prefixes (``CLAUDE_``, ``CODEX_``, …)
#: used to pass whole, forwarding host session control channels and flags into
#: the sandbox. Claude Code uses its dedicated study token, so it inherits
#: model preferences only — never ``ANTHROPIC_API_KEY``,
#: ``ANTHROPIC_AUTH_TOKEN``, ``ANTHROPIC_BASE_URL``, or
#: ``ANTHROPIC_CUSTOM_HEADERS``, which could override or redirect that auth.
#: ``--cmd`` receives no provider variables at all.
_CHILD_ENV_PROVIDER_BY_RUNTIME: dict[str, frozenset[str]] = {
    "claude": frozenset({
        "ANTHROPIC_MODEL",
        "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    }),
    "codex": frozenset({
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "CODEX_API_KEY",
    }),
    "gemini": frozenset({
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_GENAI_USE_VERTEXAI",
    }),
    "agy": frozenset({
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "AGY_ACCOUNT",
        "AGY_ADC_AUTH",
    }),
}

#: Locale, XDG base-directory and CoreFoundation settings: the user's system
#: environment, never a vendor's or a session's.
_CHILD_ENV_ALLOW_PREFIXES = (
    "LC_",
    "XDG_",
    "__CF_",
)


def _build_child_env(
    host_env: Mapping[str, str],
    *,
    sock_path: Path,
    session_id: str,
    scratch_dir: Path,
    child_cwd: Path,
    runtime_env: Mapping[str, str] | None = None,
    runtime: str | None = None,
) -> dict[str, str]:
    """Filter inherited host env down to exact system names and the launched runtime.

    Default-deny: a variable passes only by exact system name
    (``_CHILD_ENV_ALLOW_EXACT``), an explicit per-runtime provider entry
    (``_CHILD_ENV_PROVIDER_BY_RUNTIME``), or a system prefix (locale, XDG,
    CoreFoundation). ``--cmd`` (``runtime is None``) receives no provider
    variables; Claude Code's study token enters only via ``runtime_env``.
    """
    provider_allow = (
        frozenset()
        if runtime is None
        else _CHILD_ENV_PROVIDER_BY_RUNTIME.get(runtime, frozenset())
    )
    child_env = {
        k: v
        for k, v in host_env.items()
        if (
            k in _CHILD_ENV_ALLOW_EXACT
            or k in provider_allow
            or k.startswith(_CHILD_ENV_ALLOW_PREFIXES)
        )
        and k not in _RUNTIME_HOME_ENV
    }
    child_env.update(runtime_env or {})
    child_env[GATE_SOCK_ENV] = str(sock_path)
    child_env["LOS_SESSION_ID"] = session_id
    child_env["LOS_SCRATCH_DIR"] = str(scratch_dir)
    child_env["TMPDIR"] = str(scratch_dir)
    child_env["PWD"] = str(child_cwd)
    child_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return child_env


def runtime_home_env(
    runtime: str,
    runtime_home: Path,
    scratch_dir: Path,
    *,
    claude_token: str | None = None,
) -> dict[str, str]:
    """Point ``runtime`` at its own study home (and Claude Code at its study token).

    Claude Code (2026-11-21) runs on the dedicated study token
    (``CLAUDE_CODE_OAUTH_TOKEN``), never on Aram's interactive login, which
    it never touches. In claude 2.1.283 credentials from that variable carry
    no refresh token, so nothing is refreshed and no refresh lock is taken
    (``La``/``tL``). On a 401 it keeps a user-supplied token (``FOo``); it
    adopts a stored credential only in a remote session or over
    ``ANTHROPIC_UNIX_SOCKET``, and ``CLAUDE_SECURESTORAGE_CONFIG_DIR`` is left
    unset, so secure storage resolves to this home's own keychain item
    (``JL``), which does not exist: there is nothing to adopt, whatever the
    path. ``CLAUDE_CODE_TMPDIR`` moves the per-user temp root out of
    ``/private/tmp/claude-<uid>``, where unsandboxed sessions keep their task
    output. ``DISABLE_AUTOUPDATER``: the sandbox refuses writes to Claude
    Code's install folder, so an update started inside it can only fail
    ("Auto-update failed" in every interactive study launch, because a new
    home lacks the real config's ``autoUpdates`` setting).
    """
    if runtime == "claude":
        env = {
            "CLAUDE_CONFIG_DIR": str(runtime_home),
            "CLAUDE_CODE_TMPDIR": str(scratch_dir),
            "DISABLE_AUTOUPDATER": "1",
        }
        if claude_token is not None:
            env[_CLAUDE_TOKEN_ENV] = claude_token
        return env
    if runtime == "codex":
        return {"CODEX_HOME": str(runtime_home)}
    return {}


def _sbpl_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def session_uuid_for_runtime(runtime: str, external_id: str) -> str:
    """Derive a deterministic lowercase UUIDv5 for non-UUID vendor handles."""
    return str(uuid.uuid5(LEARNINGOS_STUDY_NAMESPACE, f"{runtime}:{external_id}"))


#: Paths every launch may write besides its scratch directory: terminals and
#: ``/dev/null``, and ``/private/tmp``, where Claude Code's Bash tool hands its
#: working directory back to the CLI.
_SYSTEM_WRITE_SUBPATHS = (Path("/dev"), Path("/private/tmp"))

#: Claude Code's per-user temp folder, where unsandboxed sessions keep their
#: scratchpads and background-task output (``/private/tmp/claude-<uid>``).
#: A study launch points Claude Code's temp root at its scratch directory
#: instead (``CLAUDE_CODE_TMPDIR``), so no part of this folder is writable.
_CLAUDE_USER_TMP = Path("/private/tmp") / f"claude-{os.getuid()}"

#: The login keychain, for agy's and the Gemini CLI's sign-ins. A Claude
#: Code launch no longer writes it: it runs on the study token, refreshes
#: nothing and has no keychain item of its own (2026-11-21).
_LOGIN_KEYCHAIN = "Library/Keychains"

#: agy state under ``$HOME`` that an agy launch writes during a normal session
#: (traced 2026-11-20 by diffing the home folder around one launch of agy
#: 1.5.12): conversations, transcripts, memory it records itself, logs and
#: caches. agy has no home override (no data-dir flag; the binary's
#: ``ANTIGRAVITY_EXECUTABLE_DATA_DIR`` only serves sidecar plugins), so agy
#: keeps these path rules; no other launch may write them.
_AGY_WRITABLE_SUBDIRS = (
    ".gemini/antigravity-cli/conversations",
    ".gemini/antigravity-cli/brain",
    ".gemini/antigravity-cli/annotations",
    ".gemini/antigravity-cli/implicit",
    ".gemini/antigravity-cli/presence",
    ".gemini/antigravity-cli/log",
    ".gemini/antigravity-cli/cache",
    ".gemini/antigravity-cli/crashes",
    ".gemini/antigravity-cli/scratch",
    "Library/Logs/Antigravity",
)
_SQLITE_SIDECARS = ("", "-wal", "-shm", "-journal")
_AGY_WRITABLE_FILES = (
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
#: Gemini CLI state, written by agy launches too, and npm's logs from the MCP
#: servers both start with npx. npm's package cache and npx's installs stay
#: denied: an unsandboxed agent runs the MCP servers it starts from there.
_GEMINI_WRITABLE_SUBDIRS = (".gemini/tmp", ".gemini/history", ".npm/_logs")

#: What each runtime may still write in the real home folder, relative to
#: ``$HOME``: subpaths, then literals. Claude Code writes nothing there: it
#: runs on the study token. Codex keeps only the login it shares with
#: unsandboxed sessions; it saves a refreshed login in place (codex 0.153.4
#: ``FileAuthStorage::save`` opens ``auth.json`` with truncate and writes it;
#: ``refresh_token`` reads it again first), so writing through the study
#: home's link keeps both sides on one rotating refresh token. A ``--cmd``
#: launch gets nothing.
_RUNTIME_REAL_HOME_SUBPATHS: dict[str, tuple[str, ...]] = {
    "claude": (),
    "codex": (),
    "agy": (*_AGY_WRITABLE_SUBDIRS, *_GEMINI_WRITABLE_SUBDIRS, _LOGIN_KEYCHAIN),
    "gemini": (*_GEMINI_WRITABLE_SUBDIRS, _LOGIN_KEYCHAIN),
}
_CODEX_REAL_AUTH = ".codex/auth.json"
_CODEX_AUTH_LINK = "auth.json"
_RUNTIME_REAL_HOME_LITERALS: dict[str, tuple[str, ...]] = {
    "claude": (),
    "codex": (_CODEX_REAL_AUTH,),
    "agy": _AGY_WRITABLE_FILES,
    "gemini": (),
}
#: Instruction, configuration and executable surfaces in the real runtime
#: folders. A runtime only reads these; a write would reach the next session
#: that loads them, sandboxed or not.
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
    """The folder name Claude Code gives a project under ``projects/`` and in
    its temp root. A study home holds that folder for the Core checkout; the
    tests use this to find a home's transcripts."""
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
    runtime: str | None = None,
    runtime_home: Path | None = None,
    agent_sockets: Sequence[Path] = (),
) -> str:
    """Generate a non-regex macOS Seatbelt profile for one LearningOS checkout.

    Seatbelt applies the last rule that matches, so the order is the policy:
    reads are open except the protected trees; every write is denied; the
    scratch directory (``write_roots``), the study home of ``runtime``
    (``runtime_home``), ``/dev``, ``/private/tmp`` and what ``runtime`` must
    still write in the real home folder are allowed back; and the surfaces
    that must never be written (``LearningOS/``, the real runtime folders'
    memory, instruction and config files, the home's ownership marker and
    Codex's login link, the stage directory) are denied again last.
    ``runtime=None`` is a ``--cmd`` launch: no runtime state at all.
    Connecting to the SSH agent (``agent_sockets``) or to any socket under
    ``~/.ssh`` is denied; every other unix socket, the study gate included,
    stays reachable.
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
    system_parts = [
        f'(subpath "{_sbpl_quote(str(Path(os.path.realpath(root))))}")'
        for root in _SYSTEM_WRITE_SUBPATHS
    ]
    lines.append(f"(allow file-write* {' '.join(dict.fromkeys(system_parts))})")
    # /private/tmp stays open, but not the per-user folder where unsandboxed
    # Claude Code sessions keep their scratchpads and background-task output:
    # a script or output planted there is run or read outside the sandbox. A
    # sandboxed Claude Code keeps its own temp root in the scratch directory
    # (CLAUDE_CODE_TMPDIR), which is allowed after this, wherever it was
    # allocated.
    lines.append(
        f'(deny file-write* (subpath "{_sbpl_quote(str(_CLAUDE_USER_TMP))}"))'
    )
    roots = [*write_roots, *((runtime_home,) if runtime_home is not None else ())]
    if roots:
        root_parts = [
            f'(subpath "{_sbpl_quote(str(Path(os.path.realpath(root))))}")'
            for root in roots
        ]
        lines.append(f"(allow file-write* {' '.join(dict.fromkeys(root_parts))})")

    deny_seen: set[Path] = set()
    real_home = Path(os.path.realpath(home_dir if home_dir is not None else Path.home()))
    home_ok = (
        real_home != Path("/")
        and real_home != real_learningos
        and not is_within(real_home, real_learningos)
    )
    if home_ok and real_home != real_wrapper and runtime is not None:
        runtime_parts = [
            f'(subpath "{_sbpl_quote(str(real_home / rel))}")'
            for rel in _RUNTIME_REAL_HOME_SUBPATHS.get(runtime, ())
        ] + [
            f'(literal "{_sbpl_quote(str(candidate))}")'
            for rel in _RUNTIME_REAL_HOME_LITERALS.get(runtime, ())
            for candidate in dict.fromkeys(
                (real_home / rel, Path(os.path.realpath(real_home / rel)))
            )
        ]
        if runtime_parts:
            lines.append(f"(allow file-write* {' '.join(dict.fromkeys(runtime_parts))})")

    # Denied again after the allows, whatever root it sits in: LearningOS/
    # itself, then memory, instruction, configuration and code surfaces.
    lines.append(f'(deny file-write* (subpath "{_sbpl_quote(str(real_learningos))}"))')
    if home_ok:
        claude_dir = real_home / ".claude"
        lines.append(f'(deny file-write* (subpath "{_sbpl_quote(str(claude_dir))}"))')
        # The study token's folder: no launch reads or writes it. A Claude
        # Code launch gets the token through its environment.
        secrets_dir = real_home / _STUDY_SECRETS_REL
        for candidate in dict.fromkeys((secrets_dir, Path(os.path.realpath(secrets_dir)))):
            if (
                candidate == Path("/")
                or is_within(candidate, real_learningos)
                or is_within(real_learningos, candidate)
            ):
                continue
            quoted_secrets = _sbpl_quote(str(candidate))
            lines.append(f'(deny file-read* (subpath "{quoted_secrets}"))')
            lines.append(f'(deny file-write* (subpath "{quoted_secrets}"))')
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

    if runtime_home is not None:
        # The home's ownership marker, and Codex's login link itself (not its
        # target, so the final component is not resolved): the link can be
        # written through, but neither removed nor replaced from inside.
        real_runtime_home = Path(os.path.realpath(runtime_home))
        guarded = [real_runtime_home / RUNTIME_HOME_MARKER_NAME]
        if runtime == "codex":
            guarded.append(real_runtime_home / _CODEX_AUTH_LINK)
        for literal in guarded:
            lines.append(f'(deny file-write* (literal "{_sbpl_quote(str(literal))}"))')

    for extra in deny_extra_subpaths:
        real_extra = Path(os.path.realpath(extra))
        quoted = _sbpl_quote(str(real_extra))
        lines.append(f'(deny file-read* (subpath "{quoted}"))')
        lines.append(f'(deny file-write* (subpath "{quoted}"))')
    for extra_literal in deny_extra_literals:
        real_lit = Path(os.path.realpath(extra_literal))
        lines.append(f'(deny file-write* (literal "{_sbpl_quote(str(real_lit))}"))')

    # The SSH agent. Seatbelt matches a unix socket by its resolved path, and
    # a symlink, or a hard link made outside the sandbox, to a denied socket
    # is refused too (measured 2026-11-21); so each rule names the real path.
    unix_parts = [
        f'(path-literal "{_sbpl_quote(os.path.realpath(sock))}")' for sock in agent_sockets
    ]
    if home_ok:
        unix_parts.append(f'(subpath "{_sbpl_quote(str(real_home / ".ssh"))}")')
    for part in dict.fromkeys(unix_parts):
        lines.append(f"(deny network-outbound (remote unix-socket {part}))")
    return "\n".join(lines) + "\n"


def host_agent_sockets(host_env: Mapping[str, str]) -> tuple[Path, ...]:
    """The SSH agent sockets a study launch must make unreachable.

    The host's ``SSH_AUTH_SOCK``, and the one launchd hands every login
    session (``launchctl getenv SSH_AUTH_SOCK``), so a launch from a shell
    without the variable is covered too. Real paths, as Seatbelt matches them.
    """
    candidates = [host_env.get(_SSH_AGENT_ENV, "")]
    try:
        launchd = subprocess.run(
            ["/bin/launchctl", "getenv", _SSH_AGENT_ENV],
            capture_output=True, text=True, timeout=5, stdin=subprocess.DEVNULL,
        )
        candidates.append(launchd.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return tuple(dict.fromkeys(
        Path(os.path.realpath(raw)) for raw in candidates if raw and os.path.isabs(raw)
    ))


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


def runtime_home_parent(home_dir: Path, real_learningos: Path, runtime: str) -> Path:
    """The folder holding every study home of ``runtime`` for one checkout."""
    checkout = hashlib.sha256(str(real_learningos).encode("utf-8")).hexdigest()[:12]
    return home_dir / _RUNTIME_HOMES_REL / checkout / runtime


def _vendor_session_globs(runtime: str, vendor_id: str) -> tuple[str, ...]:
    """Where ``runtime`` keeps the transcript of vendor session ``vendor_id``."""
    if runtime == "claude":
        return (f"projects/*/{vendor_id}.jsonl",)
    if runtime == "codex":
        return (
            f"sessions/*/*/*/rollout-*-{vendor_id}.jsonl",
            f"archived_sessions/rollout-*-{vendor_id}.jsonl*",
        )
    return ()


def _validate_runtime_home_marker(
    marker: Path,
    *,
    real_learningos: Path,
    runtime: str,
) -> None:
    try:
        lstat = os.lstat(marker)
    except FileNotFoundError as exc:
        raise ValueError(
            f"refusing study home without its ownership marker "
            f"({RUNTIME_HOME_MARKER_NAME}): {marker.parent}"
        ) from exc
    if stat.S_ISLNK(lstat.st_mode) or not stat.S_ISREG(lstat.st_mode):
        raise ValueError(f"study home marker must be a regular file: {marker}")
    if lstat.st_uid != os.geteuid():
        raise ValueError(f"study home marker must be owned by current user: {marker}")
    if (lstat.st_mode & 0o077) != 0:
        raise ValueError(
            f"study home marker has unsafe permissions "
            f"({oct(stat.S_IMODE(lstat.st_mode))}): {marker}"
        )
    try:
        fd = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            raw: object = json.loads(handle.read())
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"unreadable study home marker {marker}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"invalid study home marker {marker}: expected JSON object")
    if (
        raw.get("schema") != _RUNTIME_HOME_MARKER_SCHEMA
        or raw.get("owner") != _RUNTIME_HOME_MARKER_OWNER
    ):
        raise ValueError(f"not a LearningOS study home: {marker.parent}")
    if raw.get("learningos") != str(real_learningos):
        raise ValueError(
            f"study home belongs to LearningOS root {raw.get('learningos')!r}, "
            f"refusing it for {real_learningos}"
        )
    if raw.get("runtime") != runtime:
        raise ValueError(
            f"study home belongs to runtime {raw.get('runtime')!r}, refusing it for {runtime}"
        )


def _find_home_for_vendor_session(
    parent: Path,
    *,
    runtime: str,
    vendor_id: str,
    real_learningos: Path,
) -> Path | None:
    """The one study home whose transcripts carry ``vendor_id``, if any.

    A home whose marker does not belong to this checkout and runtime is
    ignored. Two homes claiming the same vendor session are refused rather
    than guessed between, because an agent can plant a transcript under any
    name in its own home.
    """
    if not _VENDOR_ID_SAFE.fullmatch(vendor_id) or not parent.is_dir():
        return None
    patterns = _vendor_session_globs(runtime, vendor_id)
    matches: list[Path] = []
    for entry in sorted(parent.iterdir(), key=lambda p: p.name):
        if entry.is_symlink() or not entry.is_dir():
            continue
        try:
            _validate_runtime_home_marker(
                entry / RUNTIME_HOME_MARKER_NAME,
                real_learningos=real_learningos,
                runtime=runtime,
            )
        except ValueError:
            continue
        if any(next(entry.glob(pattern), None) is not None for pattern in patterns):
            matches.append(entry)
    if len(matches) > 1:
        listed = ", ".join(str(match) for match in matches)
        raise ValueError(
            f"--resume-runtime-id {vendor_id!r} names a session found in several study "
            f"homes ({listed}); pass --session with the study session UUID to pick one"
        )
    return matches[0] if matches else None


def resolve_runtime_home(
    *,
    runtime: str,
    session_id: str,
    resume_runtime_id: str | None,
    home_dir: Path,
    real_learningos: Path,
) -> Path:
    """Where this launch's study home lives (``prepare_runtime_home`` makes it).

    The home is keyed by the study session UUID, so ``--session S`` and a
    repeated ``--resume-runtime-id H`` return to the same home. When no home
    exists yet under the UUID derived from ``H``, the earlier home whose
    transcripts carry vendor session ``H`` is reused, so a conversation that a
    plain launch started can still be resumed.
    """
    parent = runtime_home_parent(home_dir, real_learningos, runtime)
    direct = parent / session_id
    if resume_runtime_id is None or os.path.lexists(direct):
        return direct
    found = _find_home_for_vendor_session(
        parent,
        runtime=runtime,
        vendor_id=resume_runtime_id.strip(),
        real_learningos=real_learningos,
    )
    return found if found is not None else direct


def _mkdir_private_parents(path: Path) -> None:
    """Create ``path`` and its missing ancestors with mode 0700."""
    missing: list[Path] = []
    current = path
    while not os.path.lexists(current) and current.parent != current:
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        try:
            os.mkdir(directory, 0o700)
        except FileExistsError:
            pass


def _write_private_file(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}
    return {str(key): value for key, value in raw.items()} if isinstance(raw, dict) else {}


def _seed_claude_home(home: Path, *, real_home: Path, core_paths: Sequence[Path]) -> None:
    """A minimal Claude Code config: no onboarding, theme or trust dialog."""
    real_global = _read_json_object(real_home / ".claude.json")
    real_settings = _read_json_object(real_home / ".claude" / "settings.json")
    global_config: dict[str, object] = {
        key: real_global[key] for key in _CLAUDE_GLOBAL_COPY if key in real_global
    }
    global_config["hasCompletedOnboarding"] = True
    global_config["projects"] = {
        str(core): {"hasTrustDialogAccepted": True} for core in core_paths
    }
    settings = {key: real_settings[key] for key in _CLAUDE_SETTINGS_COPY if key in real_settings}
    _write_private_file(home / ".claude.json", json.dumps(global_config, indent=2) + "\n")
    _write_private_file(home / "settings.json", json.dumps(settings, indent=2) + "\n")


def _seed_codex_home(home: Path, *, real_home: Path, core_paths: Sequence[Path]) -> None:
    """A minimal Codex config: the file login store and a trusted Core.

    Codex loads Core's ``.codex/config.toml`` (its model) only for a trusted
    project, and trust is recorded in ``$CODEX_HOME/config.toml``.
    """
    real_codex = real_home / ".codex"
    try:
        with (real_codex / "config.toml").open("rb") as handle:
            real_config: dict[str, object] = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        real_config = {}
    lines = [
        "# Written by tools/study_launch.py for one study session (ADR-022 §3).",
        "# The login stays in ~/.codex/auth.json; auth.json here links to it.",
        'cli_auth_credentials_store = "file"',
    ]
    for key in _CODEX_CONFIG_COPY:
        value = real_config.get(key)
        if isinstance(value, str):
            lines.append(f"{key} = {json.dumps(value)}")
    for core in core_paths:
        lines += ["", f"[projects.{json.dumps(str(core))}]", 'trust_level = "trusted"']
    _write_private_file(home / "config.toml", "\n".join(lines) + "\n")
    try:
        installation_id = (real_codex / "installation_id").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    if installation_id.strip():
        _write_private_file(home / "installation_id", installation_id)


def _ensure_codex_auth_link(home: Path, *, real_home: Path) -> None:
    """Keep the home's ``auth.json`` a link to the one login Codex refreshes.

    Codex rotates its refresh token. A private copy refreshed inside the
    sandbox would leave the real ``~/.codex/auth.json`` holding a dead token
    and log every other Codex session out.
    """
    link = home / _CODEX_AUTH_LINK
    target = str(real_home / _CODEX_REAL_AUTH)
    try:
        link_stat = os.lstat(link)
    except FileNotFoundError:
        os.symlink(target, link)
        return
    if not stat.S_ISLNK(link_stat.st_mode) or os.readlink(link) != target:
        raise ValueError(
            f"refusing Codex study home {home}: {link} must link to {target}, the login "
            "unsandboxed Codex sessions refresh too; remove this home, and log in outside "
            "the sandbox"
        )


def prepare_runtime_home(
    home: Path,
    *,
    runtime: str,
    real_learningos: Path,
    session_id: str,
    real_home: Path,
    core_paths: Sequence[Path],
) -> Path:
    """Create and seed, or validate, the study home of one launch.

    A new home gets ``0700`` folders, a write-protected ownership marker and a
    minimal config for ``runtime``. An existing one must be a real directory
    owned by the user, ``0700``, with a marker for this checkout and runtime;
    the launcher writes nothing else into it, so the runtime's own state (its
    transcripts above all) carries over to the resumed launch.
    """
    homes_root = real_home / _RUNTIME_HOMES_REL
    absolute_home = Path(os.path.abspath(home))
    if is_within(Path(os.path.realpath(absolute_home.parent)), real_learningos):
        raise ValueError(f"study home must live outside LearningOS/: {absolute_home}")
    try:
        # Prove the home's folder is below <home>/.local/state/learningos/
        # study-runtimes/ before anything is created or seeded there. The home
        # itself is checked below, so a linked home keeps its own refusal.
        home_parent = scoped_write_target(homes_root, absolute_home.parent, ("**",))
    except WriteScopeError as exc:
        raise ValueError(f"study home must live under {homes_root}: {home}") from exc
    expanded = home_parent / absolute_home.name
    try:
        home_stat = os.lstat(expanded)
    except FileNotFoundError:
        _mkdir_private_parents(expanded.parent)
        try:
            os.mkdir(expanded, 0o700)
        except FileExistsError as exc:
            raise ValueError(f"study home appeared unexpectedly: {expanded}") from exc
        try:
            os.chmod(expanded, 0o700)
            marker = {
                "schema": _RUNTIME_HOME_MARKER_SCHEMA,
                "owner": _RUNTIME_HOME_MARKER_OWNER,
                "learningos": str(real_learningos),
                "runtime": runtime,
                "created_by_session": session_id,
            }
            _write_private_file(
                expanded / RUNTIME_HOME_MARKER_NAME, json.dumps(marker, indent=2) + "\n"
            )
            if runtime == "claude":
                _seed_claude_home(expanded, real_home=real_home, core_paths=core_paths)
            elif runtime == "codex":
                _seed_codex_home(expanded, real_home=real_home, core_paths=core_paths)
        except Exception:
            shutil.rmtree(expanded, ignore_errors=True)
            raise
    else:
        if stat.S_ISLNK(home_stat.st_mode) or not stat.S_ISDIR(home_stat.st_mode):
            raise ValueError(f"study home must be a real directory: {expanded}")
        if home_stat.st_uid != os.geteuid():
            raise ValueError(f"study home must be owned by current user: {expanded}")
        if (home_stat.st_mode & 0o077) != 0:
            raise ValueError(
                f"study home has unsafe permissions "
                f"({oct(stat.S_IMODE(home_stat.st_mode))}): {expanded}"
            )
        _validate_runtime_home_marker(
            expanded / RUNTIME_HOME_MARKER_NAME, real_learningos=real_learningos, runtime=runtime
        )
        # The marker's mtime is the home's last use, for retention; the
        # sandbox cannot change it (the marker is write-denied inside).
        os.utime(expanded / RUNTIME_HOME_MARKER_NAME)
    if runtime == "codex":
        _ensure_codex_auth_link(expanded, real_home=real_home)
    return Path(os.path.realpath(expanded))


def _runtime_home_last_use(home: Path) -> float | None:
    """When the launcher last used ``home``, or ``None`` if it is not one of its homes.

    A home is the launcher's only with a regular, private, user-owned marker
    naming its owner and schema; anything else under the homes root is left
    alone.
    """
    marker = home / RUNTIME_HOME_MARKER_NAME
    try:
        home_stat = os.lstat(home)
        marker_stat = os.lstat(marker)
    except OSError:
        return None
    if (
        stat.S_ISLNK(home_stat.st_mode)
        or not stat.S_ISDIR(home_stat.st_mode)
        or home_stat.st_uid != os.geteuid()
        or not stat.S_ISREG(marker_stat.st_mode)
        or marker_stat.st_uid != os.geteuid()
        or (marker_stat.st_mode & 0o077) != 0
    ):
        return None
    try:
        fd = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            raw: object = json.loads(handle.read())
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if (
        not isinstance(raw, dict)
        or raw.get("schema") != _RUNTIME_HOME_MARKER_SCHEMA
        or raw.get("owner") != _RUNTIME_HOME_MARKER_OWNER
    ):
        return None
    return marker_stat.st_mtime


def prune_runtime_homes(home_dir: Path, *, keep: Path, now: float) -> list[Path]:
    """Remove the study homes, of any checkout and runtime, unused for 30 days.

    ``keep`` (the home this launch uses) is never removed. ``shutil.rmtree``
    does not follow symlinks, so a link a study agent left in its home (to
    ``~/.codex/auth.json``, or anywhere) is removed, never its target.
    """
    root = home_dir / _RUNTIME_HOMES_REL
    cutoff = now - _RUNTIME_HOME_RETENTION_DAYS * 86400
    keep_real = Path(os.path.realpath(keep))
    removed: list[Path] = []
    try:
        checkouts = sorted(root.iterdir())
    except OSError:
        return removed
    for checkout in checkouts:
        if checkout.is_symlink() or not checkout.is_dir():
            continue
        for runtime_dir in sorted(checkout.iterdir()):
            if runtime_dir.is_symlink() or not runtime_dir.is_dir():
                continue
            for home in sorted(runtime_dir.iterdir()):
                if Path(os.path.realpath(home)) == keep_real:
                    continue
                last_use = _runtime_home_last_use(home)
                if last_use is None or last_use >= cutoff:
                    continue
                shutil.rmtree(home, ignore_errors=True)
                if not os.path.lexists(home):
                    removed.append(home)
    return removed


def _parse_codex_cli_version(raw: str) -> str | None:
    """Extract an unambiguous ``codex-cli X.Y.Z`` token pair without regex prose matching."""
    tokens = raw.split()
    matches: list[str] = []
    for index, token in enumerate(tokens[:-1]):
        if token != "codex-cli":
            continue
        candidate = tokens[index + 1]
        parts = candidate.split(".")
        if len(parts) == 3 and all(part.isascii() and part.isdigit() for part in parts):
            matches.append(candidate)
    return matches[0] if len(matches) == 1 else None


def check_codex_saves_login_in_place(binary: str) -> str:
    """Return the Codex version, or refuse one not verified to save in place.

    A study home's ``auth.json`` links to the real login. A Codex that saved
    it by renaming a temp file over it could not save through the link: it
    would fetch a rotated token pair and lose it, which would likely log
    every Codex session out. ASSUMPTION: the auth server rejects a reused
    refresh token. Fails closed: an unreadable version is refused too.
    """
    try:
        probe = subprocess.run(
            [binary, "--version"],
            capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"refusing --runtime codex: cannot read its version: {exc}") from exc
    version = _parse_codex_cli_version(probe.stdout)
    if probe.returncode != 0 or version is None:
        raise ValueError(
            f"refusing --runtime codex: `{binary} --version` gave no codex-cli version "
            f"(exit {probe.returncode})"
        )
    if version not in _CODEX_IN_PLACE_AUTH_VERSIONS:
        verified = ", ".join(sorted(_CODEX_IN_PLACE_AUTH_VERSIONS))
        raise ValueError(
            f"refusing --runtime codex: codex {version} is not verified to save its login "
            f"in place (verified: {verified}). A study home links auth.json to the real "
            "~/.codex/auth.json, and a Codex that saved it by rename would lose a rotated "
            "token pair. Re-verify FileAuthStorage::save in "
            f"codex-rs/login/src/auth/storage.rs at tag rust-v{version}: it must open "
            "auth.json with truncate and write it, not rename a temp file over it. Then add "
            f"{version} to _CODEX_IN_PLACE_AUTH_VERSIONS in tools/study_launch.py"
        )
    return version


def read_claude_study_token(home_dir: Path) -> str:
    """Read Aram's dedicated Claude Code study token, failing closed.

    The token lives at ``~/.config/learningos/claude_study_token`` (minted with
    ``claude setup-token`` outside the sandbox). Error messages never include
    file contents, and ``O_NOFOLLOW | O_NONBLOCK`` refuses symlinks and keeps a
    FIFO from hanging the launcher.
    """
    real_home = Path(os.path.realpath(home_dir))
    secrets_dir = real_home / _STUDY_SECRETS_REL
    token_path = real_home / _CLAUDE_STUDY_TOKEN_REL
    remediation = (
        f"run `claude setup-token` outside the sandbox and save it to {token_path} (mode 0600)"
    )
    try:
        parent_stat = os.lstat(secrets_dir)
    except FileNotFoundError as exc:
        raise ValueError(
            f"refusing --runtime claude: missing study token at {token_path}; {remediation}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"refusing --runtime claude: cannot inspect {secrets_dir}: "
            f"{exc.strerror or exc}; {remediation}"
        ) from exc
    if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(parent_stat.st_mode):
        raise ValueError(
            f"refusing --runtime claude: {secrets_dir} must be a real directory; {remediation}"
        )
    if parent_stat.st_uid != os.geteuid():
        raise ValueError(
            f"refusing --runtime claude: {secrets_dir} must be owned by current user; {remediation}"
        )
    if (parent_stat.st_mode & 0o077) != 0:
        raise ValueError(
            f"refusing --runtime claude: {secrets_dir} has unsafe permissions "
            f"({oct(stat.S_IMODE(parent_stat.st_mode))}); run chmod 0700 {secrets_dir}"
        )
    try:
        lstat = os.lstat(token_path)
    except FileNotFoundError as exc:
        raise ValueError(
            f"refusing --runtime claude: missing study token at {token_path}; {remediation}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"refusing --runtime claude: cannot inspect {token_path}: "
            f"{exc.strerror or exc}; {remediation}"
        ) from exc
    if stat.S_ISLNK(lstat.st_mode) or not stat.S_ISREG(lstat.st_mode):
        raise ValueError(
            f"refusing --runtime claude: study token at {token_path} must be a regular file, "
            f"not a symlink or special file; {remediation}"
        )
    try:
        fd = os.open(token_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise ValueError(
            f"refusing --runtime claude: cannot open study token at {token_path}: "
            f"{exc.strerror or exc}; {remediation}"
        ) from exc
    try:
        with os.fdopen(fd, "rb") as handle:
            fstat = os.fstat(handle.fileno())
            if not stat.S_ISREG(fstat.st_mode):
                raise ValueError(
                    f"refusing --runtime claude: study token at {token_path} must be a regular "
                    f"file; {remediation}"
                )
            if fstat.st_uid != os.geteuid():
                raise ValueError(
                    f"refusing --runtime claude: study token at {token_path} must be owned by "
                    f"current user; {remediation}"
                )
            if (fstat.st_mode & 0o077) != 0:
                raise ValueError(
                    f"refusing --runtime claude: study token at {token_path} has unsafe "
                    f"permissions ({oct(stat.S_IMODE(fstat.st_mode))}); run chmod 0600 "
                    f"{token_path}; {remediation}"
                )
            raw = handle.read(_CLAUDE_STUDY_TOKEN_MAX_BYTES + 1)
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(
            f"refusing --runtime claude: cannot read study token at {token_path}: "
            f"{exc.strerror or exc}; {remediation}"
        ) from exc
    if len(raw) > _CLAUDE_STUDY_TOKEN_MAX_BYTES:
        raise ValueError(
            f"refusing --runtime claude: study token at {token_path} exceeds "
            f"{_CLAUDE_STUDY_TOKEN_MAX_BYTES} bytes; {remediation}"
        )
    try:
        token = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"refusing --runtime claude: study token at {token_path} is not valid UTF-8; "
            f"{remediation}"
        ) from exc
    if not token:
        raise ValueError(
            f"refusing --runtime claude: study token at {token_path} is empty; {remediation}"
        )
    if any(ch in token for ch in ("\n", "\r", "\x00")):
        raise ValueError(
            f"refusing --runtime claude: study token at {token_path} must be a single line; "
            f"{remediation}"
        )
    return token


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
        "--observations-file",
        default=None,
        help=(
            "explicit observations YAML/JSON forwarded only to the host broker "
            "(never inherited from ambient LOS_OBSERVATIONS)"
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
    runtime: str | None = None,
    resume_runtime_id: str | None = None,
    runtime_binary: str | None = None,
    observations_path: str | None = None,
) -> int:
    """Start the host study broker, execute ``command`` inside Seatbelt, and reap session state.

    ``runtime`` names the agent CLI ``command`` starts (``None`` for
    ``--cmd``). It selects the runtime state the profile allows, and for
    Claude Code and Codex the study home the child is pointed at.
    ``runtime_binary`` is that CLI's executable (default ``command[0]``); a
    Claude Code launch first reads its dedicated study token
    (``read_claude_study_token``), and a Codex launch first checks its version
    (``check_codex_saves_login_in_place``).
    """
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

        home_dir = Path(os.environ["HOME"]) if os.environ.get("HOME") else Path.home()
        runtime_home: Path | None = None
        claude_token: str | None = None
        if runtime in HOMED_RUNTIMES:
            real_home = Path(os.path.realpath(home_dir))
            try:
                if runtime == "claude":
                    claude_token = read_claude_study_token(real_home)
                if runtime == "codex":
                    check_codex_saves_login_in_place(runtime_binary or command[0])
                runtime_home = prepare_runtime_home(
                    resolve_runtime_home(
                        runtime=runtime,
                        session_id=session_id,
                        resume_runtime_id=resume_runtime_id,
                        home_dir=real_home,
                        real_learningos=real_learningos,
                    ),
                    runtime=runtime,
                    real_learningos=real_learningos,
                    session_id=session_id,
                    real_home=real_home,
                    core_paths=tuple(dict.fromkeys((Path(os.path.abspath(core_root)), real_core))),
                )
            except (ValueError, OSError) as exc:
                print(f"study_launch: {exc}", file=sys.stderr)
                return 2
            # After the lookup and the marker refresh, so the home being
            # launched or resumed is the newest one and is passed to keep.
            removed = prune_runtime_homes(real_home, keep=runtime_home, now=time.time())
            if removed:
                print(
                    f"study_launch: removed {len(removed)} study home(s) unused for over "
                    f"{_RUNTIME_HOME_RETENTION_DAYS} days",
                    file=sys.stderr,
                )

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
        sb_path.write_text(
            build_seatbelt_profile(
                real_core,
                deny_extra_subpaths=(stage_dir,),
                deny_extra_literals=deny_literals,
                home_dir=home_dir,
                write_roots=(scratch_dir,),
                runtime=runtime,
                runtime_home=runtime_home,
                agent_sockets=host_agent_sockets(os.environ),
            ),
            encoding="utf-8",
        )

        broker = StudyBroker(
            real_core,
            session_id,
            scratch_dir=scratch_dir,
            stage_root=stage_dir,
            observations_path=observations_path,
        )
        server = BrokerServer(broker, sock_path)
        server.start()

        child_env = _build_child_env(
            os.environ,
            runtime=runtime,
            sock_path=sock_path,
            session_id=session_id,
            scratch_dir=scratch_dir,
            child_cwd=child_cwd,
            runtime_env=(
                runtime_home_env(
                    runtime,
                    runtime_home,
                    scratch_dir,
                    claude_token=claude_token,
                )
                if runtime is not None and runtime_home is not None
                else None
            ),
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
        requested_scratch = raw_scratch if raw_scratch.is_absolute() else caller_cwd / raw_scratch
        try:
            # A caller-chosen scratch directory must never be canonical data.
            scratch_override = guard_tool_output_path(requested_scratch, allow_existing_dir=True)
        except WriteScopeError as exc:
            print(f"study_launch: refusing --scratch-dir: {exc}", file=sys.stderr)
            return 2
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
        runtime=args.runtime,
        resume_runtime_id=args.resume_runtime_id,
        observations_path=args.observations_file,
    )


if __name__ == "__main__":
    raise SystemExit(main())
