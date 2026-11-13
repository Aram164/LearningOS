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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from learning_os.adapters import cli_parser
from learning_os.app.gateway import (
    STUDY_FENCE_CORE_ENV,
    STUDY_FENCE_SCRATCH_ENV,
    check_study_path,
)
from learning_os.domain.failures import WriteRefused
from learning_os.store.contracts.gateway import APPROVAL_KINDS, GATEWAY_CHANNELS
from learning_os.store.materials.reading_cards import valid_session

GATE_SOCK_ENV = "LOS_GATE_SOCK"

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

SEAL_GUARDS_STDIN_ENV = "LOS_SEAL_GUARDS_STDIN"

_SEAL_DOC = """Seal one GatewayEnvelopeV2 from caller-supplied intent (WORKFLOWS §25c)."""


def build_seal_parser(description: str | None = None) -> argparse.ArgumentParser:
    """Build the seal_envelope.py CLI parser (shared by A11 snapshot, CLI, and broker)."""
    parser = argparse.ArgumentParser(description=description or _SEAL_DOC)
    parser.add_argument("--root", default=None,
                        help="repository root (default: the checkout holding tools/)")
    parser.add_argument("--capability", default=None,
                        help="capability name (required unless derived from a "
                             "--guards-from record)")
    parser.add_argument("--payload", default=None,
                        help="payload JSON, or @PATH to a JSON file (required "
                             "unless derived from a --guards-from record)")
    parser.add_argument("--key", default=None,
                        help="idempotency key (required unless the --guards-from "
                             "record carries it)")
    parser.add_argument("--request-id", default=None,
                        help="request id (default: a fresh request-<key>-<random> "
                             "per run, as §25c step 4 asks; to retry, resubmit the "
                             "saved envelope instead of re-sealing)")
    parser.add_argument("--channel", default="operator",
                        help=f"one of: {', '.join(sorted(GATEWAY_CHANNELS))}")
    parser.add_argument("--session-id", default=None,
                        help="sealed session identity for this write's ledger "
                             "rows (default: none — resolution falls back to "
                             "LOS_SESSION_ID, then the channel; WORKFLOWS §25c "
                             "step 4)")
    parser.add_argument("--approval-kind", default="operator-approval",
                        help=f"one of: {', '.join(sorted(APPROVAL_KINDS))}")
    parser.add_argument("--snapshot", default=None,
                        help="expected snapshot (default: read live)")
    parser.add_argument("--revision", action="append", default=[],
                        help="guard ART=REV; repeatable")
    guards = parser.add_mutually_exclusive_group()
    guards.add_argument("--guards", default=None, choices=("auto",),
                        help="guard derivation: 'auto' runs the capability's "
                             "handler as a gateway dry run that stops before "
                             "any write, and reads revisions under the same "
                             "lock as the snapshot. Explicit --revision "
                             "entries override derived ones.")
    guards.add_argument("--guards-from", default=None, metavar="PATH",
                        help="seal from a check record at PATH instead of "
                             "deriving guards (mutually exclusive with "
                             "--guards and explicit guards)")
    parser.add_argument("--check-out", default=None, metavar="PATH",
                        help="with --guards auto on a registered operation, "
                             "also write the check record to PATH")
    parser.add_argument("--out", default=None,
                        help="write the envelope here (default: stdout)")
    parser.add_argument("--submit", action="store_true",
                        help="seal with derived guards, or with a reviewed "
                             "--guards-from record's, and submit through the "
                             "gateway in this one call, printing its result; "
                             "a retry with the same --key and payload replays "
                             "the committed receipt")
    return parser


def normalize_check_record(record: object) -> object:
    """Normalize a ``--check --report-out`` record to the schema-1 check record shape."""
    if (
        isinstance(record, dict)
        and record.get("schema") is None
        and record.get("mode") == "check"
        and record.get("ok") is True
        and isinstance(record.get("gateway_envelope"), dict)
        and isinstance(record.get("expected_snapshot"), str)
        and isinstance(record.get("expected_revisions"), dict)
    ):
        envelope = record["gateway_envelope"]
        return {
            "schema": 1,
            "ok": record.get("ok"),
            "capability": record.get("capability") or envelope.get("capability"),
            "expected_snapshot": record["expected_snapshot"],
            "expected_revisions": record["expected_revisions"],
            "payload": envelope.get("payload"),
            "idempotency_key": record.get("idempotency_key"),
        }
    return record


@dataclass(frozen=True)
class BrokerResult:
    """Result returned by the study broker over LOS_GATE_SOCK."""

    exit_code: int
    stdout: str
    stderr: str
    check_out_text: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "check_out_text": self.check_out_text,
        }


Runner = Callable[
    [list[str], Path, dict[str, str], str | None],
    tuple[int, str, str],
]


def _default_runner(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    stdin_data: str | None,
) -> tuple[int, str, str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        input=stdin_data,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


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


def _check_payload_paths(
    obj: object,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path,
) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in EXTERNAL_INPUT_PATH_KEYS:
                if isinstance(value, str):
                    check_study_path(
                        value,
                        core_root=core_root,
                        scratch_dir=scratch_dir,
                        cwd=cwd,
                        label=key,
                        allow_core=True,
                    )
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        if isinstance(item, str):
                            check_study_path(
                                item,
                                core_root=core_root,
                                scratch_dir=scratch_dir,
                                cwd=cwd,
                                label=key,
                                allow_core=True,
                            )
                        elif item is not None:
                            raise WriteRefused(f"study broker: {key} paths must be strings")
                elif value is not None:
                    raise WriteRefused(f"study broker: {key} path must be a string")
            else:
                _check_payload_paths(
                    value, core_root=core_root, scratch_dir=scratch_dir, cwd=cwd,
                )
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _check_payload_paths(
                item, core_root=core_root, scratch_dir=scratch_dir, cwd=cwd,
            )


def _read_study_json_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path,
    label: str,
) -> str:
    resolved = check_study_path(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=True,
    )
    try:
        return resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(f"study broker: cannot read {label} {resolved}: {exc}") from exc


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
        observations_path: str | None = None,
        python_executable: Path | None = None,
        runner: Runner | None = None,
    ) -> None:
        if not valid_session(session_id):
            raise ValueError(f"invalid study session UUID: {session_id!r}")
        self.core_root = Path(os.path.realpath(Path(core_root).resolve()))
        self.session_id = session_id
        self.scratch_dir = (
            Path(os.path.realpath(Path(scratch_dir).resolve()))
            if scratch_dir is not None
            else None
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
        self._runner = runner or _default_runner
        self._lock = threading.Lock()
        self._los_parser = cli_parser.build_parser()
        self._seal_parser = build_seal_parser()

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
        from learning_os.store.materials.reading_cards import protected_reads

        for closed in protected_reads(self.core_root):
            real_closed = Path(os.path.realpath(closed))
            if resolved == real_closed or real_closed in resolved.parents:
                raise WriteRefused(
                    f"study broker: client cwd inside protected tree: {resolved}"
                )
        return resolved

    def _child_env(self, *, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = dict(os.environ)
        env.pop(GATE_SOCK_ENV, None)
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
            code, out, err = self._runner(cmd, cwd, env, stdin_data)
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
                    check_study_path(
                        pfile,
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
                        label="--payload-file",
                        allow_core=True,
                    )
                    raw_env = (
                        stdin_text
                        if stdin_text is not None
                        else _read_study_json_file(
                            pfile,
                            core_root=self.core_root,
                            scratch_dir=self.scratch_dir,
                            cwd=cwd,
                            label="--payload-file",
                        )
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
                _check_payload_paths(
                    env_dict.get("payload"),
                    core_root=self.core_root,
                    scratch_dir=self.scratch_dir,
                    cwd=cwd,
                )
                child_stdin = raw_env
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
                for attr in ("file", "review_report"):
                    val = getattr(ns, attr, None)
                    if isinstance(val, str):
                        check_study_path(
                            val,
                            core_root=self.core_root,
                            scratch_dir=self.scratch_dir,
                            cwd=cwd,
                            label=f"--{attr.replace('_', '-')}",
                            allow_core=True,
                        )
                report_out = getattr(ns, "report_out", None)
                if isinstance(report_out, str):
                    check_study_path(
                        report_out,
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
                        label="--report-out",
                        allow_core=False,
                    )
                rec = getattr(ns, "record", None)
                if rec is not None:
                    _check_payload_paths(
                        rec,
                        core_root=self.core_root,
                        scratch_dir=self.scratch_dir,
                        cwd=cwd,
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

            record_cap: str | None = None
            child_stdin: str | None = None
            extra_env: dict[str, str] | None = None
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
                _check_payload_paths(
                    normalized.get("payload"),
                    core_root=self.core_root,
                    scratch_dir=self.scratch_dir,
                    cwd=cwd,
                )
                rewritten = _rewrite_value_option(
                    rewritten, "--guards-from", self._seal_parser, "-"
                )
                child_stdin = raw_guards
                extra_env = {SEAL_GUARDS_STDIN_ENV: "1"}

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
                _check_payload_paths(
                    payload_obj,
                    core_root=self.core_root,
                    scratch_dir=self.scratch_dir,
                    cwd=cwd,
                )

            if ns.check_out is not None:
                with tempfile.TemporaryDirectory() as check_tmp:
                    check_target = Path(check_tmp) / "check.json"
                    run_argv = _rewrite_value_option(
                        rewritten, "--check-out", self._seal_parser, str(check_target)
                    )
                    res = self._run_core(
                        self.core_root / "tools" / "seal_envelope.py",
                        run_argv,
                        cwd=cwd,
                        stdin_data=child_stdin,
                        extra_env=extra_env,
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
        except WriteRefused as exc:
            return _refuse(str(exc))

        return self._run_core(
            self.core_root / "tools" / "seal_envelope.py",
            rewritten,
            cwd=cwd,
            stdin_data=child_stdin,
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
            return self._handle_study_hook(req)
        return _refuse(f"study broker: unsupported tool {tool!r}")


class BrokerServer:
    """Single-process AF_UNIX stream server wrapping StudyBroker."""

    def __init__(self, broker: StudyBroker, sock_path: Path) -> None:
        self.broker = broker
        self.sock_path = Path(sock_path)
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(str(self.sock_path))
        self._sock.listen(16)
        self._sock.settimeout(0.2)
        self._stop_event = threading.Event()
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
            with conn:
                self._serve_conn(conn)

    def _serve_conn(self, conn: socket.socket) -> None:
        chunks: list[bytes] = []
        while True:
            data = conn.recv(65536)
            if not data:
                break
            nl = data.find(b"\n")
            if nl != -1:
                chunks.append(data[:nl])
                break
            chunks.append(data)
        raw = b"".join(chunks).decode("utf-8", errors="replace").strip()
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
        wire = (json.dumps(res.to_dict(), ensure_ascii=False) + "\n").encode("utf-8")
        conn.sendall(wire)

    def close(self) -> None:
        self._stop_event.set()
        try:
            self._sock.close()
        except OSError:
            pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)


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
    if subcmd == "capability":
        ns, code, _, _ = _parse_quiet(parser, argv)
        if ns is not None:
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
    out = resp.get("stdout")
    err = resp.get("stderr")
    if isinstance(out, str) and out:
        sys.stdout.write(out)
    if isinstance(err, str) and err:
        sys.stderr.write(err)
    code_val = resp.get("exit_code")
    return int(code_val) if isinstance(code_val, int) else 2
