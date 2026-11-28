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
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from learning_os.adapters import cli_parser, keeper_ingress
from learning_os.adapters.process_group import terminate_process_group
from learning_os.adapters.seal_parser import (
    SEAL_GUARDS_STDIN_ENV,
    build_seal_parser,
    normalize_check_record,
)
from learning_os.adapters.study_policies import (
    KEEPER_ALLOWED_COMMANDS,
    KEEPER_WRITE_CAPABILITIES,
    STUDY_ALLOWED_COMMANDS,
    STUDY_COMMANDS,
    STUDY_PREFLIGHT_COMMANDS,
    STUDY_READ_COMMANDS,
    STUDY_WRITE_CAPABILITIES,
)
from learning_os.adapters.study_policies import (
    SESSION_COMMANDS as _SESSION_COMMANDS,
)
from learning_os.domain.failures import WriteRefused
from learning_os.store.contracts.gateway import KEEPER_CHANNEL
from learning_os.store.contracts.write_scopes import guard_tool_output_path
from learning_os.store.materials.reading_cards import valid_session
from learning_os.store.study_fence import (
    MAX_STUDY_JSON_BYTES,
    STUDY_FENCE_CORE_ENV,
    STUDY_FENCE_SCRATCH_ENV,
    STUDY_STAGED_MANIFEST_ENV,
    RequestInputStager,
    check_study_new_output_path,
    check_study_path,
    is_within,
    protected_read_targets,
    read_study_json_file,
    write_local_output_file,
)

GATE_SOCK_ENV = "LOS_GATE_SOCK"

DEFAULT_READ_TIMEOUT_S = 5.0
DEFAULT_WRITE_TIMEOUT_S = 5.0
DEFAULT_MAX_REQUEST_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_WORKERS = 32
DEFAULT_CORE_TIMEOUT_S = 120.0
DEFAULT_LOCK_WAIT_S = 30.0

ALLOWED_LOS_READ_COMMANDS = STUDY_READ_COMMANDS
ALLOWED_STUDY_COMMANDS = STUDY_COMMANDS
ALLOWED_PREFLIGHT_COMMANDS = STUDY_PREFLIGHT_COMMANDS
ALLOWED_LOS_COMMANDS = STUDY_ALLOWED_COMMANDS
SESSION_COMMANDS = _SESSION_COMMANDS
ALLOWED_CAPABILITIES = STUDY_WRITE_CAPABILITIES


def _validate_study_envelope_origin(
    *,
    channel: object,
    approval_kind: object,
    label: str,
) -> BrokerResult | None:
    """Reject app, Keeper or non-operator-approved envelopes on both study write paths.

    Study writes keep their own provenance (`operator` or `codex`): the app's
    `ui` and the Keeper's `system-task` are refused whatever the envelope
    claims (2B: the broker derives authority from its launch profile).
    """
    if not isinstance(channel, str) or not channel.strip():
        return _refuse(f"study broker: {label} requires a non-empty channel")
    if channel == KEEPER_CHANNEL:
        return _refuse(
            f"study broker: 'system-task' is the Atlas Keeper's channel; a study "
            f"session cannot claim it ({label})"
        )
    if approval_kind != "operator-approval":
        return _refuse(
            f"study broker: {label} requires approval.kind == 'operator-approval', got {approval_kind!r}"
        )
    return None


def _validate_keeper_envelope_origin(
    *,
    channel: object,
    approval_kind: object,
    label: str,
) -> BrokerResult | None:
    """A Keeper envelope carries exactly the Keeper's provenance (2B)."""
    if channel != KEEPER_CHANNEL:
        return _refuse(
            f"study broker: a Keeper run writes only as {KEEPER_CHANNEL!r}, got {channel!r} ({label})"
        )
    if approval_kind != "operator-approval":
        return _refuse(
            f"study broker: {label} requires approval.kind == 'operator-approval', got {approval_kind!r}"
        )
    return None


ALLOWED_HOOK_EVENTS: frozenset[str] = frozenset({"session-start", "stop"})

#: Launch profiles (2B): `study` is a learner session; `keeper` is a
#: confined Atlas Keeper run (ADR-024) with its own policy and channel.
PROFILES = frozenset({"study", "keeper"})


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
    """Terminate an isolated Core process group (shared with the launcher)."""
    terminate_process_group(proc)


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


def _read_capped_text(path: Path) -> str | None:
    """Read a broker-produced JSON text file, refusing oversized output."""
    try:
        if not path.is_file():
            return None
        if path.stat().st_size > MAX_STUDY_JSON_BYTES:
            raise WriteRefused(
                f"study broker: output exceeds size limit "
                f"({MAX_STUDY_JSON_BYTES} bytes): {path}"
            )
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(f"study broker: cannot read output {path}: {exc}") from exc


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


def _top_level_option_action(
    token: str, parser: argparse.ArgumentParser,
) -> argparse.Action | None:
    head = token.partition("=")[0]
    action = parser._option_string_actions.get(head)
    if action is not None:
        return action
    if head.startswith("--"):
        matches = [
            act
            for opt, act in parser._option_string_actions.items()
            if opt.startswith(head)
        ]
        unique = {id(act): act for act in matches}
        if len(unique) == 1:
            return next(iter(unique.values()))
    return None


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
            action = _top_level_option_action(token, parser)
            if action is not None and action.nargs != 0:
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
        lock_wait_s: float = DEFAULT_LOCK_WAIT_S,
        profile: str = "study",
    ) -> None:
        if not valid_session(session_id):
            raise ValueError(f"invalid study session UUID: {session_id!r}")
        if profile not in PROFILES:
            raise ValueError(f"unknown broker profile: {profile!r}")
        self.profile = profile
        if profile == "keeper":
            self._allowed_commands = KEEPER_ALLOWED_COMMANDS
            self._allowed_capabilities = KEEPER_WRITE_CAPABILITIES
            self._preflight_commands: dict[str, str] = {}
            self._session_commands: frozenset[str] = frozenset()
            self._validate_origin = _validate_keeper_envelope_origin
        else:
            self._allowed_commands = ALLOWED_LOS_COMMANDS
            self._allowed_capabilities = ALLOWED_CAPABILITIES
            self._preflight_commands = ALLOWED_PREFLIGHT_COMMANDS
            self._session_commands = SESSION_COMMANDS
            self._validate_origin = _validate_study_envelope_origin
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
            guard_tool_output_path(stage_root, repo_root=self.core_root, allow_existing_dir=True).resolve()
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
        self.observations_path = observations_path
        if python_executable is not None:
            self.python_executable = Path(python_executable)
        else:
            venv_py = self.core_root / ".venv" / "bin" / "python"
            self.python_executable = venv_py if venv_py.is_file() else Path(sys.executable)
        self.core_timeout_s = float(core_timeout_s)
        if lock_wait_s <= 0:
            raise ValueError(f"lock_wait_s must be positive, got {lock_wait_s!r}")
        self.lock_wait_s = float(lock_wait_s)
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
                return str(guard_tool_output_path("/tmp", allow_existing_dir=True).resolve())
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
        for closed in protected_read_targets(self.core_root):
            if is_within(resolved, closed):
                raise WriteRefused(
                    f"study broker: client cwd inside protected tree: {resolved}"
                )
        return resolved

    # The Core child gets an explicit environment, not the host's whole
    # environment: POSIX/runtime basics plus LearningOS's own LOS_* inputs
    # (minus the broker-only gate socket and staged manifest, set below).
    _CHILD_ENV_EXACT: frozenset[str] = frozenset({
        "PATH", "HOME", "LANG", "LANGUAGE", "TMPDIR", "USER", "LOGNAME",
        "SHELL", "TERM", "TZ",
    })
    _CHILD_ENV_PREFIXES: tuple[str, ...] = ("LC_", "LOS_")

    def _child_env(self, *, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = {
            key: value
            for key, value in os.environ.items()
            if key in self._CHILD_ENV_EXACT
            or key.startswith(self._CHILD_ENV_PREFIXES)
        }
        env.pop(GATE_SOCK_ENV, None)
        env.pop(STUDY_STAGED_MANIFEST_ENV, None)
        # Only _run_keeper sets the Keeper handshake, per call.
        env.pop(keeper_ingress.HANDSHAKE_ENV, None)
        for obs_key in [k for k in env if k.startswith("LOS_OBSERVATIONS")]:
            env.pop(obs_key, None)
        env["LOS_SESSION_ID"] = self.session_id
        env[STUDY_FENCE_CORE_ENV] = str(self.core_root)
        if self.scratch_dir is not None:
            env[STUDY_FENCE_SCRATCH_ENV] = str(self.scratch_dir)
        else:
            env.pop(STUDY_FENCE_SCRATCH_ENV, None)
        if self.observations_path is not None:
            env["LOS_OBSERVATIONS"] = self.observations_path
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
        return self._run_command(cmd, cwd=cwd, stdin_data=stdin_data, extra_env=extra_env)

    def _run_keeper(
        self,
        tool: str,
        argv: list[str],
        *,
        cwd: Path,
        stdin_data: str | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> BrokerResult:
        """Run one Keeper write through the broker-internal ingress (2B)."""
        token, digest = keeper_ingress.new_handshake()
        cmd = [str(self.python_executable), "-I", "-m", keeper_ingress.MODULE]
        return self._run_command(
            cmd,
            cwd=cwd,
            stdin_data=keeper_ingress.request_text(token, tool, argv, stdin_data),
            extra_env={**(extra_env or {}), keeper_ingress.HANDSHAKE_ENV: digest},
        )

    def _run_command(
        self,
        cmd: list[str],
        *,
        cwd: Path,
        stdin_data: str | None,
        extra_env: dict[str, str] | None,
    ) -> BrokerResult:
        env = self._child_env(extra=extra_env)
        if not self._lock.acquire(timeout=self.lock_wait_s):
            return _refuse(
                f"study broker: busy — core request did not start within "
                f"{self.lock_wait_s:g}s; retry the request"
            )
        try:
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
        finally:
            self._lock.release()
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
            if subcmd == "ui-capability":
                return _refuse("study broker: apply this request from the LearningOS app")
            if subcmd not in self._allowed_commands:
                hint = ""
                if subcmd == "session-end":
                    hint = (
                        " (seal_envelope.py --submit already validates canonical "
                        "writes; commit or run .venv/bin/python tools/los.py session-end "
                        "outside study mode)"
                    )
                return _refuse(
                    f"study broker: command {subcmd!r} is not allowed in {self.profile} mode{hint}"
                )
            rewritten = list(argv)
            target_cmd = subcmd
            ns = None
            code = None
            out = ""
            err = ""
            probe_err = ""
            if subcmd == "material-span" and self.profile == "study":
                # Private reading memory belongs to learner study sessions
                # (ADR-021); a Keeper run quotes through the plain read.
                probe = list(argv)
                probe[idx] = "material-study-span"
                probe_ns, probe_code, probe_out, probe_err = _parse_quiet(
                    self._los_parser, probe
                )
                if probe_ns is not None and getattr(probe_ns, "extract", False) is True:
                    rewritten = probe
                    target_cmd = "material-study-span"
                    ns, code, out, err = probe_ns, probe_code, probe_out, probe_err
            if ns is None:
                ns, code, out, err = _parse_quiet(self._los_parser, rewritten)
            if ns is None:
                if code == 0:
                    return BrokerResult(exit_code=0, stdout=out, stderr=err)
                return _refuse(err or f"study broker: invalid arguments for {target_cmd}")
            if self.profile == "study" and target_cmd == "material-span" and getattr(ns, "extract", False) is True:
                return _refuse(
                    probe_err or "study broker: invalid arguments for material-study-span"
                )
            self._check_root_flag(getattr(ns, "root", None), cwd=cwd)
            if getattr(ns, "root", None) is None:
                rewritten = ["--root", str(self.core_root), *rewritten]
            given_session = getattr(ns, "session", None)
            if given_session is not None and self.profile == "keeper":
                return _refuse("study broker: reading-memory sessions are only available in study mode")
            if given_session is not None and given_session != self.session_id:
                return _refuse(
                    f"study broker: --session cannot differ from active session {self.session_id}"
                )
            if target_cmd in self._session_commands and given_session is None:
                rewritten.extend(["--session", self.session_id])

            child_stdin: str | None = None
            if target_cmd == "capability":
                cap_name = getattr(ns, "name", None)
                if not isinstance(cap_name, str) or cap_name not in self._allowed_capabilities:
                    return _refuse(
                        f"study broker: capability {cap_name!r} is not allowed in {self.profile} mode"
                    )
                pfile = getattr(ns, "payload_file", None)
                if not isinstance(pfile, str) or not pfile:
                    return _refuse("study broker: capability requires --payload-file")
                if pfile == "-":
                    if stdin_text is None:
                        return _refuse("study broker: --payload-file - requires envelope input")
                    raw_env = stdin_text
                else:
                    raw_env = read_study_json_file(
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
                if env_cap != cap_name or env_cap not in self._allowed_capabilities:
                    return _refuse(
                        f"study broker: envelope capability {env_cap!r} does not match allowed {cap_name!r}"
                    )
                env_session = env_dict.get("session_id")
                if env_session is not None and env_session != self.session_id:
                    return _refuse(
                        "study broker: envelope session_id cannot differ from active study session"
                    )
                approval_obj = env_dict.get("approval")
                origin_refusal = self._validate_origin(
                    channel=env_dict.get("channel"),
                    approval_kind=(
                        approval_obj.get("kind") if isinstance(approval_obj, dict) else None
                    ),
                    label="capability envelope",
                )
                if origin_refusal is not None:
                    return origin_refusal
                with tempfile.TemporaryDirectory(
                    prefix="los-req-", dir=self._stage_base(),
                ) as stage_tmp:
                    stage_dir = Path(os.path.realpath(stage_tmp))
                    stager = RequestInputStager(
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
                        stage_dir=stage_dir,
                    )
                    stager.stage_payload_paths(env_dict.get("payload"))
                    manifest_env = stager.manifest_env()
                    if self.profile == "keeper":
                        return self._run_keeper(
                            "capability",
                            rewritten,
                            cwd=cwd,
                            stdin_data=raw_env,
                            extra_env=manifest_env or None,
                        )
                    return self._run_core(
                        self.core_root / "tools" / "los.py",
                        rewritten,
                        cwd=cwd,
                        stdin_data=raw_env,
                        extra_env=manifest_env or None,
                    )
            elif target_cmd in self._preflight_commands:
                # Preflights are strictly read-only diagnostics (`--check`), so they stay
                # decoupled from `ALLOWED_CAPABILITIES` (e.g. `unit-plan-revise --check`
                # supports `--report-out` mediation even though canonical plan writes refuse).
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
                    stager = RequestInputStager(
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
                    report_out_text = _read_capped_text(host_report)
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
            if self.profile == "keeper":
                # The broker stamps the Keeper's provenance from its launch
                # profile (2B): a caller may omit both flags or repeat these
                # exact values, and any other claim is refused.
                for flag, wanted, value in (
                    ("--channel", KEEPER_CHANNEL, getattr(ns, "channel", None)),
                    ("--approval-kind", "operator-approval", getattr(ns, "approval_kind", None)),
                ):
                    given = any(_matches_option(token, flag, self._seal_parser) for token in argv)
                    if given and value != wanted:
                        return _refuse(
                            f"study broker: a Keeper run seals {flag} {wanted} only, got {value!r}"
                        )
                rewritten = list(argv)
                for flag in ("--channel", "--approval-kind"):
                    rewritten = _rewrite_value_option(rewritten, flag, self._seal_parser, None)
                rewritten.extend(["--channel", KEEPER_CHANNEL,
                                  "--approval-kind", "operator-approval"])
            else:
                origin_refusal = self._validate_origin(
                    channel=getattr(ns, "channel", None),
                    approval_kind=getattr(ns, "approval_kind", None),
                    label="seal_envelope",
                )
                if origin_refusal is not None:
                    return origin_refusal
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
                stager = RequestInputStager(
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
                        else read_study_json_file(
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
                    if not isinstance(rec_cap_obj, str) or rec_cap_obj not in self._allowed_capabilities:
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
                if not isinstance(effective_cap, str) or effective_cap not in self._allowed_capabilities:
                    return _refuse(
                        f"study broker: capability {effective_cap!r} is not allowed in {self.profile} mode"
                    )

                if ns.payload is not None:
                    if ns.payload.startswith("@"):
                        raw_payload = (
                            payload_at_text
                            if payload_at_text is not None
                            else read_study_json_file(
                                ns.payload[1:],
                                core_root=self.core_root,
                                scratch_dir=self.scratch_dir,
                                cwd=cwd,
                                label="--payload @PATH",
                            )
                        )
                    else:
                        raw_payload = ns.payload
                    payload_obj = _parse_json_dict(raw_payload, label="--payload")
                    stager.stage_payload_paths(payload_obj)
                    # Never expand payload JSON into a subprocess argument
                    # (E2BIG on large payloads): stage it host-only and pass
                    # an @PATH the host child reads back.
                    staged_payload = stage_dir / "payload.json"
                    pfd = os.open(
                        staged_payload,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o400,
                    )
                    with os.fdopen(pfd, "w", encoding="utf-8") as phandle:
                        phandle.write(raw_payload)
                    rewritten = _rewrite_value_option(
                        rewritten, "--payload", self._seal_parser,
                        f"@{staged_payload}",
                    )

                extra_env.update(stager.manifest_env())
                run_env = extra_env or None

                if ns.check_out is not None:
                    check_target = stage_dir / "check.json"
                    run_argv = _rewrite_value_option(
                        rewritten, "--check-out", self._seal_parser, str(check_target)
                    )
                    res = self._run_seal(run_argv, cwd=cwd, stdin_data=child_stdin,
                                         extra_env=run_env)
                    captured = _read_capped_text(check_target)
                    return BrokerResult(
                        exit_code=res.exit_code,
                        stdout=res.stdout,
                        stderr=res.stderr,
                        check_out_text=captured,
                    )

                return self._run_seal(rewritten, cwd=cwd, stdin_data=child_stdin,
                                      extra_env=run_env)
        except WriteRefused as exc:
            return _refuse(str(exc))

    def _run_seal(
        self,
        argv: list[str],
        *,
        cwd: Path,
        stdin_data: str | None,
        extra_env: dict[str, str] | None,
    ) -> BrokerResult:
        if self.profile == "keeper":
            return self._run_keeper("seal", argv, cwd=cwd, stdin_data=stdin_data,
                                    extra_env=extra_env)
        return self._run_core(
            self.core_root / "tools" / "seal_envelope.py",
            argv,
            cwd=cwd,
            stdin_data=stdin_data,
            extra_env=extra_env,
        )

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
            if self.profile == "keeper":
                return _refuse("study broker: reading-memory hooks are only available in study mode")
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
        self.sock_path = guard_tool_output_path(sock_path)
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
        if getattr(ns, "payload_file", None) == "-":
            stdin_text = sys.stdin.read()
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
