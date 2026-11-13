"""Default-deny study broker for Sandboxed LearningOS sessions (PLAN-D D2).

The broker runs unsandboxed on the host behind an AF_UNIX socket
(``LOS_GATE_SOCK``). Sandboxed runtimes (Claude, Codex, Gemini, ``--cmd``)
call ``tools/los.py`` and ``tools/seal_envelope.py`` as usual; pre-dispatch
shims forward the call here, where a strict allowlist, session/root pinning,
and external path firewall inspect every request before spawning Core with
``python -I``.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import functools
import io
import json
import os
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from learning_os.adapters import cli_parser
from learning_os.adapters.seal_parser import (
    SEAL_GUARDS_STDIN_ENV,
    build_seal_parser,
    normalize_check_record,
)
from learning_os.domain.failures import WriteRefused
from learning_os.store.materials.reading_cards import valid_session
from learning_os.store.study_fence import (
    STUDY_FENCE_CORE_ENV,
    STUDY_FENCE_SCRATCH_ENV,
    STUDY_STAGED_MANIFEST_ENV,
    call_dir_fd_op,
    check_study_new_output_path,
    check_study_path,
    find_real_ancestor,
    is_within,
    open_dir_chain_nofollow,
    protected_reads,
    read_optional_study_or_staged_file,
    read_study_file,
)

GATE_SOCK_ENV = "LOS_GATE_SOCK"

DEFAULT_READ_TIMEOUT_S = 5.0
DEFAULT_WRITE_TIMEOUT_S = 5.0
DEFAULT_MAX_REQUEST_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_WORKERS = 32
DEFAULT_CORE_TIMEOUT_S = 120.0

ALLOWED_LOS_READ_COMMANDS: frozenset[str] = frozenset({
    "status",
    "capabilities",
    "bootstrap",
    "resume",
    "dossier",
    "inspect",
    "search",
    "semantic",
    "note-read",
    "inbox-read",
    "inbox-list",
    "related",
    "program-list",
    "plan-template",
    "module-list",
    "unit-list",
    "study-sequence",
    "ability-context",
    "runtime-session",
    "plan-edit-context",
    "atlas-context",
    "operations",
    "projection-observe",
})

ALLOWED_STUDY_COMMANDS: frozenset[str] = frozenset({
    "material-search",
    "material-context",
    "material-span",
    "material-study-span",
    "material-card-settle",
})

ALLOWED_PREFLIGHT_COMMANDS: dict[str, str] = {
    "source-intake": "source.intake.record",
    "unit-plan-revise": "unit.plan.revise",
}

ALLOWED_LOS_COMMANDS: frozenset[str] = (
    ALLOWED_LOS_READ_COMMANDS
    | ALLOWED_STUDY_COMMANDS
    | frozenset({"capability", *ALLOWED_PREFLIGHT_COMMANDS})
)

SESSION_COMMANDS: frozenset[str] = frozenset({
    "material-study-span",
    "material-card-settle",
    "material-search",
    "material-context",
})

ALLOWED_CAPABILITIES: frozenset[str] = frozenset({
    "capture.create",
    "inbox.resolve",
    "stage.note.write",
    "stage.progress.update",
    "stage.attachment.add",
    "unit.note.append",
    "unit.plan.revise",
    "unit.source-selection.set",
    "detour.create",
    "detour.resolve",
    "note.create",
    "note.revise",
    "note.evidence.add",
    "note.analysis.save",
    "note.analysis.save_batch",
    "source.feedback.record",
    "source.intake.record",
    "concept.relations.change",
    "atlas.question.save",
    "garden.seed.create",
})

EXTERNAL_INPUT_PATH_KEYS: frozenset[str] = frozenset({
    "file",
    "body_file",
    "content_file",
    "attachment",
    "items_file",
    "drafts",
    "review_report",
})

ALLOWED_HOOK_EVENTS: frozenset[str] = frozenset({"session-start", "stop"})


@dataclass(frozen=True)
class BrokerResult:
    """Result returned by the study broker over LOS_GATE_SOCK."""

    exit_code: int
    stdout: str
    stderr: str
    check_out_text: str | None = None
    report_out_text: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "check_out_text": self.check_out_text,
            "report_out_text": self.report_out_text,
        }


Runner = Callable[
    [list[str], Path, dict[str, str], str | None],
    tuple[int, str, str],
]


def _terminate_process_group(proc: subprocess.Popen[str]) -> None:
    """Terminate an isolated Core process group with SIGTERM then SIGKILL."""
    with contextlib.suppress(OSError):
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=1.0)
        return
    except subprocess.TimeoutExpired:
        pass
    with contextlib.suppress(OSError):
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    with contextlib.suppress(OSError, subprocess.TimeoutExpired):
        proc.wait(timeout=2.0)


def _run_subprocess_bounded(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    stdin_data: str | None,
    *,
    timeout_s: float,
    proc_lock: threading.Lock | None = None,
    active_procs: set[subprocess.Popen[str]] | None = None,
    cancelled_event: threading.Event | None = None,
) -> tuple[int, str, str]:
    if proc_lock is not None:
        with proc_lock:
            if cancelled_event is not None and cancelled_event.is_set():
                return 2, "", "study broker: cancelled\n"
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                env=env,
                stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            if active_procs is not None:
                active_procs.add(proc)
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    try:
        try:
            out, err = proc.communicate(input=stdin_data, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            _terminate_process_group(proc)
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                proc.communicate(timeout=1.0)
            if cancelled_event is not None and cancelled_event.is_set():
                return 2, "", "study broker: cancelled\n"
            return (
                2,
                "",
                f"study broker: core subprocess timed out after {timeout_s:g}s\n",
            )
        if cancelled_event is not None and cancelled_event.is_set():
            return 2, out or "", (err or "") + "study broker: cancelled\n"
        return proc.returncode, out or "", err or ""
    finally:
        if proc_lock is not None and active_procs is not None:
            with proc_lock:
                active_procs.discard(proc)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                with contextlib.suppress(OSError):
                    stream.close()


def _default_runner(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    stdin_data: str | None,
) -> tuple[int, str, str]:
    return _run_subprocess_bounded(
        cmd,
        cwd,
        env,
        stdin_data,
        timeout_s=DEFAULT_CORE_TIMEOUT_S,
    )


def _refuse(reason: str) -> BrokerResult:
    line = reason if reason.endswith("\n") else reason + "\n"
    return BrokerResult(exit_code=2, stdout="", stderr=line)


def _real(path: Path | str, *, cwd: Path | None = None) -> Path:
    expanded = Path(path).expanduser()
    if not expanded.is_absolute() and cwd is not None:
        expanded = cwd / expanded
    return Path(os.path.realpath(expanded))


def _matches_option(token: str, canonical: str, parser: argparse.ArgumentParser) -> bool:
    head = token.partition("=")[0]
    if head == canonical:
        return True
    if not head.startswith("--") or not canonical.startswith(head):
        return False
    matches = [opt for opt in parser._option_string_actions if opt.startswith(head)]
    return matches == [canonical]


def _rewrite_value_option(
    argv: list[str],
    canonical: str,
    parser: argparse.ArgumentParser,
    replacement: str | None,
) -> list[str]:
    """Strip (``replacement=None``) or replace a single-value flag across spellings."""
    out: list[str] = []
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token == "--":
            out.extend(argv[idx:])
            break
        if _matches_option(token, canonical, parser):
            if "=" in token:
                if replacement is not None:
                    out.append(f"{canonical}={replacement}")
                idx += 1
                continue
            if idx + 1 >= len(argv):
                raise WriteRefused(f"missing value for {canonical}")
            if replacement is not None:
                out.extend([canonical, replacement])
            idx += 2
            continue
        out.append(token)
        idx += 1
    return out


def _find_subcommand(
    argv: list[str], parser: argparse.ArgumentParser,
) -> tuple[int | None, str | None]:
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token == "--":
            return None, None
        if token.startswith("-"):
            if "=" in token:
                idx += 1
                continue
            if _matches_option(token, "--root", parser) or _matches_option(
                token, "--lock-timeout", parser
            ):
                idx += 2
                continue
            idx += 1
            continue
        return idx, token
    return None, None


def _parse_quiet(
    parser: argparse.ArgumentParser, argv: list[str],
) -> tuple[argparse.Namespace | None, int | None, str, str]:
    cap_out, cap_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cap_out), contextlib.redirect_stderr(cap_err):
        try:
            ns = parser.parse_args(argv)
            return ns, None, cap_out.getvalue(), cap_err.getvalue()
        except SystemExit as exc:
            raw_code = exc.code
            code = raw_code if isinstance(raw_code, int) else 2
            return None, code, cap_out.getvalue(), cap_err.getvalue()


def _walk_payload_paths(
    obj: object,
    *,
    on_path: Callable[[str, str], None],
) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in EXTERNAL_INPUT_PATH_KEYS:
                if isinstance(value, str):
                    on_path(value, str(key))
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        if isinstance(item, str):
                            on_path(item, str(key))
                        elif item is not None:
                            raise WriteRefused(f"study broker: {key} paths must be strings")
                elif value is not None:
                    raise WriteRefused(f"study broker: {key} path must be a string")
            else:
                _walk_payload_paths(value, on_path=on_path)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _walk_payload_paths(item, on_path=on_path)


def _read_study_json_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path,
    label: str,
) -> str:
    anchored, content = read_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=True,
    )
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WriteRefused(f"study broker: cannot decode {label} {anchored}: {exc}") from exc


class _RequestInputStager:
    """Copy validated study input files into a host-only immutable request dir."""

    def __init__(
        self,
        *,
        core_root: Path,
        scratch_dir: Path | None,
        cwd: Path,
        stage_dir: Path,
    ) -> None:
        self.core_root = core_root
        self.scratch_dir = scratch_dir
        self.cwd = cwd
        self.stage_dir = stage_dir
        self.entries: dict[str, str] = {}

    def stage_path(self, raw_path: str, *, label: str, allow_core: bool = True) -> Path:
        anchored, data = read_optional_study_or_staged_file(
            raw_path,
            core_root=self.core_root,
            scratch_dir=self.scratch_dir,
            cwd=self.cwd,
            label=label,
            allow_core=allow_core,
        )
        if data is None:
            return anchored
        key = str(anchored)
        if key in self.entries:
            return anchored
        idx = len(self.entries)
        subdir = self.stage_dir / f"f{idx}"
        subdir.mkdir(mode=0o700)
        leaf_name = anchored.name or "input"
        staged_file = subdir / leaf_name
        fd = os.open(
            staged_file,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o400,
        )
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        self.entries[key] = f"f{idx}/{leaf_name}"
        return anchored

    def stage_payload_paths(self, obj: object) -> None:
        def _collect(raw_path: str, key: str) -> None:
            self.stage_path(raw_path, label=key, allow_core=True)

        _walk_payload_paths(obj, on_path=_collect)

    def manifest_env(self) -> dict[str, str]:
        if not self.entries:
            return {}
        manifest_path = self.stage_dir / "manifest.json"
        fd = os.open(
            manifest_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o400,
        )
        payload = json.dumps({"entries": self.entries}, ensure_ascii=False).encode("utf-8")
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        return {STUDY_STAGED_MANIFEST_ENV: str(manifest_path)}


def _parse_json_dict(raw_json: str, *, label: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw_json)
    except ValueError as exc:
        raise WriteRefused(f"study broker: invalid JSON for {label}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise WriteRefused(f"study broker: {label} must be a JSON object")
    return {str(k): v for k, v in parsed.items()}


class StudyBroker:
    """Authorizing host gateway mediating study requests over LOS_GATE_SOCK."""

    def __init__(
        self,
        core_root: Path,
        session_id: str,
        *,
        scratch_dir: Path | None = None,
        stage_root: Path | None = None,
        observations_path: str | None = None,
        python_executable: Path | None = None,
        runner: Runner | None = None,
        core_timeout_s: float = DEFAULT_CORE_TIMEOUT_S,
    ) -> None:
        if not valid_session(session_id):
            raise ValueError(f"invalid study session UUID: {session_id!r}")
        if core_timeout_s <= 0:
            raise ValueError(f"core_timeout_s must be positive, got {core_timeout_s!r}")
        self.core_root = Path(os.path.realpath(Path(core_root).resolve()))
        self.session_id = session_id
        self.scratch_dir = (
            Path(os.path.realpath(Path(scratch_dir).resolve()))
            if scratch_dir is not None
            else None
        )
        self.stage_root: Path | None = (
            Path(os.path.realpath(Path(stage_root).resolve()))
            if stage_root is not None
            else None
        )
        if self.stage_root is not None:
            for base in (self.core_root, self.scratch_dir):
                if base is not None and (
                    self.stage_root == base or base in self.stage_root.parents
                ):
                    raise ValueError(
                        f"stage_root must sit outside study core and scratch: {self.stage_root}"
                    )
        self.observations_path = (
            observations_path
            if observations_path is not None
            else os.environ.get("LOS_OBSERVATIONS")
        )
        if python_executable is not None:
            self.python_executable = Path(python_executable)
        else:
            venv_py = self.core_root / ".venv" / "bin" / "python"
            self.python_executable = venv_py if venv_py.is_file() else Path(sys.executable)
        self.core_timeout_s = float(core_timeout_s)
        self._custom_runner = runner
        self._lock = threading.Lock()
        self._proc_lock = threading.Lock()
        self._active_procs: set[subprocess.Popen[str]] = set()
        self._cancelled_event = threading.Event()
        self._los_parser = cli_parser.build_parser()
        self._seal_parser = build_seal_parser()

    def cancel(self) -> None:
        """Terminate any active Core child process groups without acquiring _lock."""
        with self._proc_lock:
            self._cancelled_event.set()
            procs = list(self._active_procs)
        for proc in procs:
            _terminate_process_group(proc)

    def _stage_base(self) -> str | None:
        if self.stage_root is not None:
            self.stage_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            return str(self.stage_root)
        default_tmp = Path(os.path.realpath(tempfile.gettempdir()))
        for base in (self.core_root, self.scratch_dir):
            if base is not None and is_within(default_tmp, base):
                return str(Path(os.path.realpath("/tmp")))
        return None

    def _validate_cwd(self, raw_cwd: object) -> Path:
        if raw_cwd is None:
            return self.core_root
        if not isinstance(raw_cwd, str) or not raw_cwd.strip():
            raise WriteRefused("study broker: invalid client cwd")
        try:
            resolved = Path(os.path.realpath(raw_cwd))
        except (RuntimeError, ValueError, OSError) as exc:
            raise WriteRefused(f"study broker: cannot resolve cwd {raw_cwd!r}: {exc}") from exc
        if not resolved.is_dir():
            raise WriteRefused(f"study broker: client cwd does not exist: {resolved}")
        for closed in protected_reads(self.core_root):
            if is_within(resolved, closed):
                raise WriteRefused(
                    f"study broker: client cwd inside protected tree: {resolved}"
                )
        return resolved

    def _child_env(self, *, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = dict(os.environ)
        env.pop(GATE_SOCK_ENV, None)
        env.pop(STUDY_STAGED_MANIFEST_ENV, None)
        env["LOS_SESSION_ID"] = self.session_id
        env[STUDY_FENCE_CORE_ENV] = str(self.core_root)
        if self.scratch_dir is not None:
            env[STUDY_FENCE_SCRATCH_ENV] = str(self.scratch_dir)
        else:
            env.pop(STUDY_FENCE_SCRATCH_ENV, None)
        if self.observations_path is not None:
            env["LOS_OBSERVATIONS"] = self.observations_path
        else:
            env.pop("LOS_OBSERVATIONS", None)
        env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
        if extra:
            env.update(extra)
        return env

    def _run_core(
        self,
        script: Path,
        argv: list[str],
        *,
        cwd: Path,
        stdin_data: str | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> BrokerResult:
        cmd = [str(self.python_executable), "-I", str(script), *argv]
        env = self._child_env(extra=extra_env)
        with self._lock:
            if self._custom_runner is not None:
                if self._cancelled_event.is_set():
                    return _refuse("study broker: cancelled")
                code, out, err = self._custom_runner(cmd, cwd, env, stdin_data)
            else:
                code, out, err = _run_subprocess_bounded(
                    cmd,
                    cwd,
                    env,
                    stdin_data,
                    timeout_s=self.core_timeout_s,
                    proc_lock=self._proc_lock,
                    active_procs=self._active_procs,
                    cancelled_event=self._cancelled_event,
                )
        return BrokerResult(exit_code=code, stdout=out, stderr=err)

    def _check_root_flag(self, raw_root: object, *, cwd: Path) -> None:
        if raw_root is None:
            return
        if not isinstance(raw_root, str):
            raise WriteRefused("study broker: invalid --root")
        try:
            resolved = _real(raw_root, cwd=cwd)
        except (RuntimeError, ValueError, OSError) as exc:
            raise WriteRefused(f"study broker: cannot resolve --root {raw_root!r}: {exc}") from exc
        if resolved != self.core_root:
            raise WriteRefused(
                f"study broker: --root must match study core root ({self.core_root}), got {resolved}"
            )

    def _handle_los(self, req: dict[str, object]) -> BrokerResult:
        raw_argv = req.get("argv")
        if not isinstance(raw_argv, list) or not all(isinstance(x, str) for x in raw_argv):
            return _refuse("study broker: argv must be a list of strings")
        argv = list(raw_argv)
        stdin_text = req.get("stdin_text")
        if stdin_text is not None and not isinstance(stdin_text, str):
            return _refuse("study broker: stdin_text must be a string")
        try:
            cwd = self._validate_cwd(req.get("cwd"))
            idx, subcmd = _find_subcommand(argv, self._los_parser)
            if subcmd is None:
                ns, code, out, err = _parse_quiet(self._los_parser, argv)
                if code == 0:
                    return BrokerResult(exit_code=0, stdout=out, stderr=err)
                return _refuse(err or "study broker: missing or invalid los subcommand")
            assert idx is not None
            if subcmd not in ALLOWED_LOS_COMMANDS:
                return _refuse(
                    f"study broker: command {subcmd!r} is not allowed in study mode"
                )
            rewritten = list(argv)
            target_cmd = subcmd
            if subcmd == "material-span" and any(
                t == "--extract" or (t.startswith("--ext") and "--extract".startswith(t))
                for t in argv[idx + 1:]
            ):
                rewritten[idx] = "material-study-span"
                target_cmd = "material-study-span"
            ns, code, out, err = _parse_quiet(self._los_parser, rewritten)
            if ns is None:
                if code == 0:
                    return BrokerResult(exit_code=0, stdout=out, stderr=err)
                return _refuse(err or f"study broker: invalid arguments for {target_cmd}")
            self._check_root_flag(getattr(ns, "root", None), cwd=cwd)
            if getattr(ns, "root", None) is None:
                rewritten = ["--root", str(self.core_root), *rewritten]
            given_session = getattr(ns, "session", None)
            if given_session is not None and given_session != self.session_id:
                return _refuse(
                    f"study broker: --session cannot differ from active session {self.session_id}"
                )
            if target_cmd in SESSION_COMMANDS and given_session is None:
                rewritten.extend(["--session", self.session_id])

            child_stdin: str | None = None
            if target_cmd == "capability":
                cap_name = getattr(ns, "name", None)
                if not isinstance(cap_name, str) or cap_name not in ALLOWED_CAPABILITIES:
                    return _refuse(
                        f"study broker: capability {cap_name!r} is not allowed in study mode"
                    )
                pfile = getattr(ns, "payload_file", None)
                if not isinstance(pfile, str) or not pfile:
                    return _refuse("study broker: capability requires --payload-file")
                if pfile == "-":
                    if stdin_text is None:
                        return _refuse("study broker: --payload-file - requires envelope input")
                    raw_env = stdin_text
                else:
                    if stdin_text is not None:
                        check_study_path(
                            pfile,
                            core_root=self.core_root,
                            scratch_dir=self.scratch_dir,
                            cwd=cwd,
                            label="--payload-file",
                            allow_core=True,
                        )
                        raw_env = stdin_text
                    else:
                        raw_env = _read_study_json_file(
                            pfile,
                            core_root=self.core_root,
                            scratch_dir=self.scratch_dir,
                            cwd=cwd,
                            label="--payload-file",
                        )
                    rewritten = _rewrite_value_option(
                        rewritten, "--payload-file", self._los_parser, "-"
                    )
                env_dict = _parse_json_dict(raw_env, label="capability envelope")
                env_cap = env_dict.get("capability")
                if env_cap != cap_name or env_cap not in ALLOWED_CAPABILITIES:
                    return _refuse(
                        f"study broker: envelope capability {env_cap!r} does not match allowed {cap_name!r}"
                    )
                env_session = env_dict.get("session_id")
                if env_session is not None and env_session != self.session_id:
                    return _refuse(
                        "study broker: envelope session_id cannot differ from active study session"
                    )
                with tempfile.TemporaryDirectory(
                    prefix="los-req-", dir=self._stage_base(),
                ) as stage_tmp:
                    stage_dir = Path(os.path.realpath(stage_tmp))
                    stager = _RequestInputStager(
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
                        stage_dir=stage_dir,
                    )
                    stager.stage_payload_paths(env_dict.get("payload"))
                    manifest_env = stager.manifest_env()
                    return self._run_core(
                        self.core_root / "tools" / "los.py",
                        rewritten,
                        cwd=cwd,
                        stdin_data=raw_env,
                        extra_env=manifest_env or None,
                    )
            elif target_cmd in ALLOWED_PREFLIGHT_COMMANDS:
                mapped_cap = ALLOWED_PREFLIGHT_COMMANDS[target_cmd]
                if mapped_cap not in ALLOWED_CAPABILITIES:
                    return _refuse(f"study broker: preflight {target_cmd!r} not allowlisted")
                if getattr(ns, "check", False) is not True:
                    return _refuse(
                        f"study broker: {target_cmd!r} is only permitted with --check preflight"
                    )
                if getattr(ns, "approve", False) or getattr(
                    ns, "apply_reviewed_sha256", None
                ) is not None:
                    return _refuse(
                        f"study broker: {target_cmd!r} preflight refuses apply/approve flags"
                    )
                report_out = getattr(ns, "report_out", None)
                anchored_report_out: Path | None = None
                if isinstance(report_out, str):
                    draft_val = getattr(ns, "file", None)
                    anchored_report_out = check_study_new_output_path(
                        report_out,
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
                        label="--report-out",
                        draft_path=draft_val if isinstance(draft_val, str) else None,
                    )
                with tempfile.TemporaryDirectory(
                    prefix="los-req-", dir=self._stage_base(),
                ) as stage_tmp:
                    stage_dir = Path(os.path.realpath(stage_tmp))
                    stager = _RequestInputStager(
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
                        stage_dir=stage_dir,
                    )
                    for attr in ("file", "review_report"):
                        val = getattr(ns, attr, None)
                        if isinstance(val, str):
                            stager.stage_path(
                                val,
                                label=f"--{attr.replace('_', '-')}",
                                allow_core=True,
                            )
                    rec = getattr(ns, "record", None)
                    if rec is not None:
                        stager.stage_payload_paths(rec)
                    manifest_env = stager.manifest_env()

                    host_report: Path | None = None
                    if anchored_report_out is not None:
                        host_report = stage_dir / "report.json"
                        rewritten = _rewrite_value_option(
                            rewritten,
                            "--report-out",
                            self._los_parser,
                            str(host_report),
                        )
                    res = self._run_core(
                        self.core_root / "tools" / "los.py",
                        rewritten,
                        cwd=cwd,
                        stdin_data=child_stdin,
                        extra_env=manifest_env or None,
                    )
                    if host_report is None:
                        return res
                    report_out_text = (
                        host_report.read_text(encoding="utf-8")
                        if host_report.is_file()
                        else None
                    )
                    stdout_text = res.stdout
                    if report_out_text is not None and anchored_report_out is not None:
                        stdout_text = _rewrite_saved_report_stdout(
                            stdout_text,
                            client_report_path=anchored_report_out,
                        )
                    return BrokerResult(
                        exit_code=res.exit_code,
                        stdout=stdout_text,
                        stderr=res.stderr,
                        report_out_text=report_out_text,
                    )
        except WriteRefused as exc:
            return _refuse(str(exc))

        return self._run_core(
            self.core_root / "tools" / "los.py",
            rewritten,
            cwd=cwd,
            stdin_data=child_stdin,
        )

    def _handle_seal(self, req: dict[str, object]) -> BrokerResult:
        raw_argv = req.get("argv")
        if not isinstance(raw_argv, list) or not all(isinstance(x, str) for x in raw_argv):
            return _refuse("study broker: argv must be a list of strings")
        argv = list(raw_argv)
        guards_from_text = req.get("guards_from_text")
        if guards_from_text is not None and not isinstance(guards_from_text, str):
            return _refuse("study broker: guards_from_text must be a string")
        payload_at_text = req.get("payload_at_text")
        if payload_at_text is not None and not isinstance(payload_at_text, str):
            return _refuse("study broker: payload_at_text must be a string")
        try:
            cwd = self._validate_cwd(req.get("cwd"))
            ns, code, out, err = _parse_quiet(self._seal_parser, argv)
            if ns is None:
                if code == 0:
                    return BrokerResult(exit_code=0, stdout=out, stderr=err)
                return _refuse(err or "study broker: invalid seal_envelope arguments")
            self._check_root_flag(ns.root, cwd=cwd)
            if ns.session_id is not None:
                stripped = ns.session_id.strip() if isinstance(ns.session_id, str) else ""
                if stripped != self.session_id:
                    return _refuse(
                        f"study broker: --session-id cannot differ from active session {self.session_id}"
                    )
            if ns.channel == "ui":
                return _refuse("study broker: 'ui' channel is refused")

            rewritten = list(argv)
            if ns.root is None:
                rewritten = ["--root", str(self.core_root), *rewritten]
            if ns.out is not None:
                check_study_path(
                    ns.out,
                    core_root=self.core_root,
                    scratch_dir=self.scratch_dir,
                    cwd=cwd,
                    label="--out",
                    allow_core=False,
                )
                rewritten = _rewrite_value_option(
                    rewritten, "--out", self._seal_parser, None
                )

            if ns.check_out is not None:
                check_study_path(
                    ns.check_out,
                    core_root=self.core_root,
                    scratch_dir=self.scratch_dir,
                    cwd=cwd,
                    label="--check-out",
                    allow_core=False,
                )

            with tempfile.TemporaryDirectory(
                prefix="seal-req-", dir=self._stage_base(),
            ) as stage_tmp:
                stage_dir = Path(os.path.realpath(stage_tmp))
                stager = _RequestInputStager(
                    core_root=self.core_root,
                    scratch_dir=self.scratch_dir,
                    cwd=cwd,
                    stage_dir=stage_dir,
                )

                record_cap: str | None = None
                child_stdin: str | None = None
                extra_env: dict[str, str] = {}
                if ns.guards_from is not None:
                    raw_guards = (
                        guards_from_text
                        if guards_from_text is not None
                        else _read_study_json_file(
                            ns.guards_from,
                            core_root=self.core_root,
                            scratch_dir=self.scratch_dir,
                            cwd=cwd,
                            label="--guards-from",
                        )
                    )
                    normalized = normalize_check_record(
                        _parse_json_dict(raw_guards, label="--guards-from record")
                    )
                    if not isinstance(normalized, dict):
                        return _refuse("study broker: invalid --guards-from record")
                    rec_cap_obj = normalized.get("capability")
                    if not isinstance(rec_cap_obj, str) or rec_cap_obj not in ALLOWED_CAPABILITIES:
                        return _refuse(
                            f"study broker: --guards-from capability {rec_cap_obj!r} is not allowed"
                        )
                    record_cap = rec_cap_obj
                    stager.stage_payload_paths(normalized.get("payload"))
                    rewritten = _rewrite_value_option(
                        rewritten, "--guards-from", self._seal_parser, "-"
                    )
                    child_stdin = raw_guards
                    extra_env[SEAL_GUARDS_STDIN_ENV] = "1"

                effective_cap = ns.capability or record_cap
                if not isinstance(effective_cap, str) or effective_cap not in ALLOWED_CAPABILITIES:
                    return _refuse(
                        f"study broker: capability {effective_cap!r} is not allowed in study mode"
                    )

                if ns.payload is not None:
                    if ns.payload.startswith("@"):
                        raw_payload = (
                            payload_at_text
                            if payload_at_text is not None
                            else _read_study_json_file(
                                ns.payload[1:],
                                core_root=self.core_root,
                                scratch_dir=self.scratch_dir,
                                cwd=cwd,
                                label="--payload @PATH",
                            )
                        )
                        rewritten = _rewrite_value_option(
                            rewritten, "--payload", self._seal_parser, raw_payload
                        )
                    else:
                        raw_payload = ns.payload
                    payload_obj = _parse_json_dict(raw_payload, label="--payload")
                    stager.stage_payload_paths(payload_obj)

                extra_env.update(stager.manifest_env())
                run_env = extra_env or None

                if ns.check_out is not None:
                    check_target = stage_dir / "check.json"
                    run_argv = _rewrite_value_option(
                        rewritten, "--check-out", self._seal_parser, str(check_target)
                    )
                    res = self._run_core(
                        self.core_root / "tools" / "seal_envelope.py",
                        run_argv,
                        cwd=cwd,
                        stdin_data=child_stdin,
                        extra_env=run_env,
                    )
                    captured = (
                        check_target.read_text(encoding="utf-8")
                        if check_target.is_file()
                        else None
                    )
                    return BrokerResult(
                        exit_code=res.exit_code,
                        stdout=res.stdout,
                        stderr=res.stderr,
                        check_out_text=captured,
                    )

                return self._run_core(
                    self.core_root / "tools" / "seal_envelope.py",
                    rewritten,
                    cwd=cwd,
                    stdin_data=child_stdin,
                    extra_env=run_env,
                )
        except WriteRefused as exc:
            return _refuse(str(exc))

    def _handle_study_hook(self, req: dict[str, object]) -> BrokerResult:
        event = req.get("event")
        if not isinstance(event, str) or event not in ALLOWED_HOOK_EVENTS:
            return _refuse(f"study broker: hook event {event!r} is not allowed")
        hook_payload = json.dumps({
            "session_id": self.session_id,
            "stop_hook_active": bool(req.get("stop_hook_active", False)),
        })
        return self._run_core(
            self.core_root / "tools" / "study_hooks.py",
            [event],
            cwd=self.core_root,
            stdin_data=hook_payload,
        )

    def handle_request(self, req: dict[str, object]) -> BrokerResult:
        """Validate and execute one study broker request."""
        tool = req.get("tool")
        if tool == "los":
            return self._handle_los(req)
        if tool == "seal_envelope":
            return self._handle_seal(req)
        if tool == "study_hook":
            return self._handle_study_hook(req)
        return _refuse(f"study broker: unsupported tool {tool!r}")


def _rewrite_saved_report_stdout(
    stdout_text: str,
    *,
    client_report_path: Path,
) -> str:
    try:
        parsed = json.loads(stdout_text)
    except ValueError:
        return stdout_text
    if isinstance(parsed, dict) and isinstance(parsed.get("saved_report"), dict):
        parsed["saved_report"]["path"] = str(client_report_path)
        return json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"
    return stdout_text


class BrokerServer:
    """Bounded concurrent AF_UNIX stream server wrapping StudyBroker."""

    def __init__(
        self,
        broker: StudyBroker,
        sock_path: Path,
        *,
        read_timeout_s: float = DEFAULT_READ_TIMEOUT_S,
        write_timeout_s: float = DEFAULT_WRITE_TIMEOUT_S,
        max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        if read_timeout_s <= 0:
            raise ValueError(f"read_timeout_s must be positive, got {read_timeout_s!r}")
        if write_timeout_s <= 0:
            raise ValueError(f"write_timeout_s must be positive, got {write_timeout_s!r}")
        if max_request_bytes <= 0:
            raise ValueError(f"max_request_bytes must be positive, got {max_request_bytes!r}")
        if max_workers < 1:
            raise ValueError(f"max_workers must be >= 1, got {max_workers!r}")
        self.broker = broker
        self.sock_path = Path(sock_path)
        self.read_timeout_s = float(read_timeout_s)
        self.write_timeout_s = float(write_timeout_s)
        self.max_request_bytes = int(max_request_bytes)
        self.max_workers = int(max_workers)
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(str(self.sock_path))
        with contextlib.suppress(OSError):
            os.chmod(self.sock_path, 0o600)
        self._sock.listen(max(16, self.max_workers))
        self._sock.settimeout(0.2)
        self._stop_event = threading.Event()
        self._worker_semaphore = threading.BoundedSemaphore(self.max_workers)
        self._workers_lock = threading.Lock()
        self._workers: set[threading.Thread] = set()
        self._conns: set[socket.socket] = set()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while not self._stop_event.is_set():
            try:
                conn, _ = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            if not self._worker_semaphore.acquire(blocking=False):
                try:
                    conn.settimeout(min(self.write_timeout_s, 1.0))
                    self._send_result(
                        conn,
                        _refuse("study broker: too many concurrent requests"),
                    )
                except OSError:
                    pass
                finally:
                    with contextlib.suppress(OSError):
                        conn.close()
                continue
            worker = threading.Thread(
                target=self._worker_entry,
                args=(conn,),
                daemon=True,
            )
            with self._workers_lock:
                if self._stop_event.is_set():
                    self._worker_semaphore.release()
                    with contextlib.suppress(OSError):
                        conn.close()
                    break
                self._workers.add(worker)
                self._conns.add(conn)
                worker.start()

    def _worker_entry(self, conn: socket.socket) -> None:
        try:
            with conn:
                self._serve_conn(conn)
        finally:
            with self._workers_lock:
                self._conns.discard(conn)
                self._workers.discard(threading.current_thread())
            self._worker_semaphore.release()

    def _read_request_bytes(self, conn: socket.socket) -> bytes:
        deadline = time.monotonic() + self.read_timeout_s
        chunks: list[bytes] = []
        total = 0
        while True:
            if self._stop_event.is_set():
                raise TimeoutError("study broker: server closed before request completed")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"study broker: request timed out after {self.read_timeout_s:g}s"
                )
            conn.settimeout(min(remaining, 0.25))
            try:
                data = conn.recv(65536)
            except TimeoutError:
                continue
            if not data:
                break
            nl = data.find(b"\n")
            if nl != -1:
                part = data[:nl]
                if total + len(part) > self.max_request_bytes:
                    raise ValueError(
                        f"study broker: request exceeds max size ({self.max_request_bytes} bytes)"
                    )
                chunks.append(part)
                break
            total += len(data)
            if total > self.max_request_bytes:
                raise ValueError(
                    f"study broker: request exceeds max size ({self.max_request_bytes} bytes)"
                )
            chunks.append(data)
        return b"".join(chunks)

    def _send_result(self, conn: socket.socket, res: BrokerResult) -> None:
        conn.settimeout(self.write_timeout_s)
        wire = (json.dumps(res.to_dict(), ensure_ascii=False) + "\n").encode("utf-8")
        conn.sendall(wire)

    def _serve_conn(self, conn: socket.socket) -> None:
        try:
            raw_bytes = self._read_request_bytes(conn)
        except (TimeoutError, ValueError) as exc:
            with contextlib.suppress(OSError):
                self._send_result(conn, _refuse(str(exc)))
            return
        except OSError:
            return

        raw = raw_bytes.decode("utf-8", errors="replace").strip()
        if not raw:
            res = _refuse("study broker: empty request")
        else:
            try:
                parsed = json.loads(raw)
            except ValueError as exc:
                res = _refuse(f"study broker: malformed request JSON: {exc}")
            else:
                if not isinstance(parsed, dict):
                    res = _refuse("study broker: request must be a JSON object")
                else:
                    res = self.broker.handle_request(
                        {str(k): v for k, v in parsed.items()}
                    )
        with contextlib.suppress(OSError):
            self._send_result(conn, res)

    def close(self) -> None:
        self._stop_event.set()
        with contextlib.suppress(OSError):
            self._sock.close()
        self.broker.cancel()
        with self._workers_lock:
            conns = list(self._conns)
            workers = list(self._workers)
        for conn in conns:
            with contextlib.suppress(OSError):
                conn.shutdown(socket.SHUT_RDWR)
            with contextlib.suppress(OSError):
                conn.close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        for worker in workers:
            worker.join(timeout=2.0)


def send_broker_request(sock_path: str, payload: dict[str, object]) -> dict[str, object]:
    """Send one newline-delimited JSON RPC request over LOS_GATE_SOCK."""
    wire = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)
        sock.sendall(wire)
        chunks: list[bytes] = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            nl = data.find(b"\n")
            if nl != -1:
                chunks.append(data[:nl])
                break
            chunks.append(data)
    raw = b"".join(chunks).decode("utf-8", errors="strict")
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise ValueError("study broker returned a non-object response")
    return {str(k): v for k, v in decoded.items()}


def _open_local_parent_dir_fd(
    parent: Path,
    *,
    mkdir_parents: bool,
    scratch_dir: Path | None,
) -> int:
    lex_parent = Path(os.path.abspath(parent))
    if scratch_dir is not None:
        real_scratch = Path(os.path.realpath(scratch_dir))
        matched = find_real_ancestor(lex_parent, real_scratch)
        if matched is None:
            raise OSError(errno.EACCES, "Refusing output outside study scratch", str(parent))
        _anc, rel_parts = matched
        if any(part in ("", ".", "..") for part in rel_parts):
            raise OSError(errno.EINVAL, "Refusing invalid local output directory", str(parent))
        base_path: Path = real_scratch
        tail_parts: tuple[str, ...] = rel_parts
    else:
        probe = lex_parent
        missing: list[str] = []
        while True:
            try:
                os.lstat(probe)
                break
            except FileNotFoundError:
                if probe.parent == probe:
                    raise
                missing.append(probe.name)
                probe = probe.parent
        for anc in (probe, *probe.parents):
            if anc.parent == anc:
                break
            if len(anc.parts) == 2 and anc.parts[1] in ("var", "tmp", "etc"):
                continue
            if anc.is_symlink():
                raise OSError(errno.ELOOP, "Refusing symlink parent target", str(anc))
        base_path = probe
        tail_parts = tuple(reversed(missing))

    if tail_parts and not mkdir_parents:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(parent))

    return open_dir_chain_nofollow(base_path, tail_parts, create_missing=mkdir_parents)


def write_local_output_file(
    target_text: str,
    content: str,
    *,
    mkdir_parents: bool = False,
    exclusive: bool = False,
    scratch_dir: Path | None = None,
) -> None:
    """Write mediated broker output locally without following symlinks or hardlinks."""
    target = Path(target_text).expanduser()
    if target.name in ("", ".", ".."):
        raise OSError(errno.EINVAL, "Refusing invalid local output target", target_text)
    if target.is_symlink():
        raise OSError(errno.ELOOP, "Refusing symlink local output target", str(target))
    effective_scratch = scratch_dir
    if effective_scratch is None:
        scratch_env = os.environ.get(STUDY_FENCE_SCRATCH_ENV, "").strip()
        if scratch_env:
            effective_scratch = Path(scratch_env)
    parent_fd = _open_local_parent_dir_fd(
        target.parent,
        mkdir_parents=mkdir_parents,
        scratch_dir=effective_scratch,
    )
    file_flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    if exclusive:
        file_flags |= os.O_EXCL
    if hasattr(os, "O_CLOEXEC"):
        file_flags |= os.O_CLOEXEC
    try:
        fd = call_dir_fd_op(
            functools.partial(os.open, target.name, file_flags, 0o644, dir_fd=parent_fd)
        )
    finally:
        os.close(parent_fd)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError(errno.EINVAL, "Refusing non-regular local output target", str(target))
        if st.st_nlink > 1:
            raise OSError(errno.EMLINK, "Refusing hardlinked local output target", str(target))
        if not exclusive:
            os.ftruncate(fd, 0)
        handle = os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(fd)
        raise
    with handle:
        handle.write(content)


def dispatch_los_via_socket(sock_path: str, argv: list[str]) -> int:
    """Client shim for ``tools/los.py`` when ``LOS_GATE_SOCK`` is set."""
    stdin_text: str | None = None
    parser = cli_parser.build_parser()
    idx, subcmd = _find_subcommand(argv, parser)
    ns, _code, _, _ = _parse_quiet(parser, argv)
    report_out_target = (
        getattr(ns, "report_out", None) if ns is not None else None
    )
    if subcmd == "capability" and ns is not None:
        pfile = getattr(ns, "payload_file", None)
        if pfile == "-":
            stdin_text = sys.stdin.read()
        elif isinstance(pfile, str) and pfile:
            try:
                stdin_text = Path(pfile).expanduser().read_text(encoding="utf-8")
            except OSError as exc:
                print(f"los: cannot read --payload-file {pfile}: {exc}", file=sys.stderr)
                return 2
    try:
        resp = send_broker_request(
            sock_path,
            {
                "tool": "los",
                "argv": argv,
                "cwd": os.getcwd(),
                "stdin_text": stdin_text,
            },
        )
    except (OSError, ValueError) as exc:
        print(f"los: study broker unavailable ({exc}); failing closed", file=sys.stderr)
        return 2
    report_out_text = resp.get("report_out_text")
    if isinstance(report_out_text, str):
        if not isinstance(report_out_target, str) or not report_out_target:
            print(
                "los: broker returned report output without a --report-out target",
                file=sys.stderr,
            )
            return 2
        try:
            write_local_output_file(report_out_target, report_out_text, exclusive=True)
        except OSError as exc:
            print(
                f"los: cannot write --report-out {report_out_target}: {exc}",
                file=sys.stderr,
            )
            return 2
    out = resp.get("stdout")
    err = resp.get("stderr")
    if isinstance(out, str) and out:
        sys.stdout.write(out)
    if isinstance(err, str) and err:
        sys.stderr.write(err)
    code_val = resp.get("exit_code")
    return int(code_val) if isinstance(code_val, int) else 2
