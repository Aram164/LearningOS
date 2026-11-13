#!/usr/bin/env python3
"""Foreground Seatbelt + study-broker launcher for LearningOS study sessions (PLAN-D D1/D3).

Replaces client-side hook AST/path parsing with an OS-enforced macOS Seatbelt
boundary (``/usr/bin/sandbox-exec``) paired with an unsandboxed AF_UNIX broker
(``tools/learning_os/adapters/study_broker.py``):

- Read-denies ``LearningOS/materials/``, ``LearningOS/reading-memory/``,
  ``generated/{text-cache,material-search,material-outlines,derived-state}/``,
  and non-``.gitkeep`` children of ``operations/ai-actions/requests/``.
- Write-denies all of ``LearningOS/``.
- Allocates ``$LOS_SCRATCH_DIR`` (``$TMPDIR``) outside ``LearningOS/`` and mints
  an authoritative study session UUID before launching ``claude``, ``codex``,
  ``gemini``, or ``--cmd``.
- Records ``ReadingStore.session_end`` and cleans up the socket in ``finally:``
  even on child crash or kill.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Sequence
from pathlib import Path
from types import FrameType

from learning_os.adapters.study_broker import GATE_SOCK_ENV, BrokerServer, StudyBroker
from learning_os.store.materials.reading_cards import (
    ReadingStore,
    ReadingStoreError,
    valid_session,
)
from learning_os.store.study_fence import is_within, protected_reads

SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
LEARNINGOS_STUDY_NAMESPACE = uuid.UUID("7f3b0c4a-5e2d-4c8a-9b1f-3e6d1a2c4b8e")
RUNTIMES = ("claude", "codex", "gemini")


def _sbpl_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def session_uuid_for_runtime(runtime: str, external_id: str) -> str:
    """Derive a deterministic lowercase UUIDv5 for non-UUID vendor handles."""
    return str(uuid.uuid5(LEARNINGOS_STUDY_NAMESPACE, f"{runtime}:{external_id}"))


def build_seatbelt_profile(
    core_root: Path,
    *,
    deny_extra_subpaths: Sequence[Path] = (),
) -> str:
    """Generate a non-regex macOS Seatbelt profile for one LearningOS checkout."""
    real_core = Path(os.path.realpath(Path(core_root).resolve()))
    real_learningos = Path(os.path.realpath(real_core.parent))
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
    lines.append(f'(deny file-write* (subpath "{_sbpl_quote(str(real_learningos))}"))')
    for extra in deny_extra_subpaths:
        real_extra = Path(os.path.realpath(extra))
        quoted = _sbpl_quote(str(real_extra))
        lines.append(f'(deny file-read* (subpath "{quoted}"))')
        lines.append(f'(deny file-write* (subpath "{quoted}"))')
    return "\n".join(lines) + "\n"


_RUNTIME_PATH_FLAGS = ("--settings", "--mcp-config", "--plugin-dir", "--add-dir")


def _resolve_caller_path(value: str, *, caller_cwd: Path, real_core: Path) -> str:
    if not value or value.startswith("~"):
        return value
    candidate = Path(value)
    if candidate.is_absolute():
        return value
    caller_target = caller_cwd / candidate
    if not (real_core / candidate).exists() and caller_target.exists():
        return str(caller_target.resolve())
    return value


def _normalize_caller_args(
    extra: Sequence[str],
    *,
    caller_cwd: Path,
    real_core: Path,
) -> list[str]:
    if caller_cwd == real_core:
        return list(extra)
    out: list[str] = []
    expect_path = False
    for token in extra:
        if expect_path:
            out.append(
                _resolve_caller_path(token, caller_cwd=caller_cwd, real_core=real_core)
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
                    token[len(prefix):], caller_cwd=caller_cwd, real_core=real_core
                )
                break
        out.append(rewritten)
    return out


def _select_launch_cwd(
    *,
    real_core: Path,
    caller_cwd: Path,
    command: Sequence[str],
    use_cmd: bool,
) -> Path:
    if not use_cmd or caller_cwd == real_core:
        return real_core
    cmd0 = command[0]
    cmd_path = Path(cmd0)
    is_relative_path = not cmd_path.is_absolute() and (
        "/" in cmd0
        or (os.altsep is not None and os.altsep in cmd0)
        or cmd0 in (".", "..")
        or cmd0.startswith(("./", "../"))
    )
    if (
        is_relative_path
        and not (real_core / cmd_path).exists()
        and (caller_cwd / cmd_path).exists()
    ):
        return caller_cwd
    return real_core


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
        return tail
    assert runtime is not None
    if caller_cwd is not None and real_core is not None:
        tail = _normalize_caller_args(tail, caller_cwd=caller_cwd, real_core=real_core)
    binary = shutil.which(runtime)
    if binary is None:
        raise ValueError(f"runtime binary {runtime!r} was not found on PATH")
    if runtime == "codex":
        return [
            binary,
            "-s",
            "danger-full-access",
            "-c",
            "shell_environment_policy.inherit=all",
            *tail,
        ]
    return [binary, *tail]


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
    sock_dir: Path | None = None
    stage_dir: Path | None = None
    server: BrokerServer | None = None
    proc: subprocess.Popen[bytes] | None = None
    terminated_by_signal = False
    sigterm_installed = False
    prev_sigterm = signal.getsignal(signal.SIGTERM)

    def _on_sigterm(_signum: int, _frame: FrameType | None) -> None:
        nonlocal terminated_by_signal
        terminated_by_signal = True
        if proc is not None and proc.poll() is None:
            proc.terminate()

    try:
        try:
            store.touch(session_id, start=True)
            session_started = True
        except ReadingStoreError as exc:
            print(f"study_launch: reading store unavailable: {exc}", file=sys.stderr)
            return 2

        scratch_dir = _allocate_scratch_dir(real_learningos)
        sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losg-", dir="/tmp")))
        stage_dir = _allocate_outside_dir("losb-", real_learningos)
        sock_path = sock_dir / "gate.sock"
        sb_path = sock_dir / "study.sb"
        sb_path.write_text(
            build_seatbelt_profile(real_core, deny_extra_subpaths=(stage_dir,)),
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

        child_env = dict(os.environ)
        child_env[GATE_SOCK_ENV] = str(sock_path)
        child_env["LOS_SESSION_ID"] = session_id
        child_env["LOS_SCRATCH_DIR"] = str(scratch_dir)
        child_env["TMPDIR"] = str(scratch_dir)
        child_env["PWD"] = str(child_cwd)
        child_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")

        signal.signal(signal.SIGTERM, _on_sigterm)
        sigterm_installed = True

        proc = subprocess.Popen(
            [str(effective_sandbox), "-f", str(sb_path), *command],
            env=child_env,
            cwd=str(child_cwd),
        )
        exit_code = proc.wait()
        return 143 if terminated_by_signal and exit_code < 0 else exit_code
    except KeyboardInterrupt:
        if proc is not None and proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        return 130
    finally:
        if sigterm_installed:
            signal.signal(signal.SIGTERM, prev_sigterm)
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
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
        if scratch_dir is not None:
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
    child_cwd = _select_launch_cwd(
        real_core=real_core,
        caller_cwd=caller_cwd,
        command=command,
        use_cmd=bool(args.cmd),
    )
    return launch_study(
        core_root=core_root,
        command=command,
        session_id=session_id,
        cwd=child_cwd,
    )


if __name__ == "__main__":
    raise SystemExit(main())
