"""Seal tests for the S13 candidate (Task 5).

The --check-out/--guards-from flags, the unregistered --check-out refusal,
every --guards-from validation plus its record-driven sealing, and the
real registered record journey (check-out, seal from the record, apply)
with its two validations, through a test-only registered operation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest
from gateway_helpers import approved_v2_envelope

from learning_os.fingerprint import canonical_fingerprint
from learning_os.ops.proposal import Result
from learning_os.ops.registry import REGISTRY

SEAL = Path(__file__).resolve().parent.parent / "tools" / "seal_envelope.py"
# The unregistered probe operation for the seal-path tests: text in, JSON
# out, legacy dispatch. (capture.create held this role until S15 converted
# it; a session converting garden.seed.create repoints this again.)
CAPABILITY = "garden.seed.create"


def _seal(root: Path, out: Path, *, payload: dict, key: str,
          extra: list[str] | None = None):
    command = [sys.executable, str(SEAL), "--root", str(root),
               "--capability", CAPABILITY, "--payload", json.dumps(payload),
               "--key", key, "--out", str(out)]
    command.extend(extra or [])
    return subprocess.run(command, capture_output=True, text=True, timeout=120)


def _record(path: Path, *, capability=CAPABILITY, payload, snapshot,
            revisions, schema=1, ok=True):
    record = {"schema": schema, "capability": capability, "ok": ok,
              "payload": payload, "expected_snapshot": snapshot,
              "expected_revisions": revisions}
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def _live_snapshot(mini_repo: Path) -> str:
    return f"sha256:{canonical_fingerprint(mini_repo)}"


def test_no_leaked_test_registrations():
    # S13 registered zero operations; S15 registers converted ones, so the
    # handlers package exists by design. What must never leak is the
    # test-only operation outside its fixture.
    assert "test-only.pipe" not in REGISTRY


def test_check_out_unregistered_refuses_before_output(mini_repo: Path, tmp_path: Path):
    out = tmp_path / "check.json"
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "check-out probe"}, key="check-out-001",
                   extra=["--guards", "auto", "--check-out", str(out)])
    assert sealed.returncode == 2
    assert sealed.stderr == "seal_envelope: --check-out requires a registered operation\n"
    assert sealed.stdout == ""
    assert not out.exists()


def test_check_out_requires_guards_auto(mini_repo: Path, tmp_path: Path):
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "check-out probe"}, key="check-out-002",
                   extra=["--check-out", str(tmp_path / "check.json")])
    assert sealed.returncode == 2
    assert sealed.stderr == "seal_envelope: --check-out requires --guards auto\n"


def test_guards_from_with_revision_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "x"},
                     snapshot="sha256:0", revisions={})
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-001",
                   extra=["--guards-from", str(record), "--revision", "a=1"])
    assert sealed.returncode == 2
    assert sealed.stderr == ("seal_envelope: --guards-from cannot be combined "
                             "with explicit --revision guards\n")


def test_guards_from_with_snapshot_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "x"},
                     snapshot="sha256:0", revisions={})
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-002",
                   extra=["--guards-from", str(record), "--snapshot", "sha256:1"])
    assert sealed.returncode == 2
    assert sealed.stderr == ("seal_envelope: --guards-from cannot be combined "
                             "with explicit --snapshot\n")


def test_check_out_with_guards_from_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "x"},
                     snapshot="sha256:0", revisions={})
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-003",
                   extra=["--guards-from", str(record),
                          "--check-out", str(tmp_path / "check.json")])
    assert sealed.returncode == 2
    assert sealed.stderr == "seal_envelope: --check-out cannot be combined with --guards-from\n"


def test_guards_from_with_explicit_guards_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "x"},
                     snapshot="sha256:0", revisions={})
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-004",
                   extra=["--guards", "auto", "--guards-from", str(record)])
    assert sealed.returncode == 2
    assert "not allowed with" in sealed.stderr


def test_guards_from_schema_mismatch_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "x"},
                     snapshot="sha256:0", revisions={}, schema=2)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-005",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 2
    assert sealed.stderr == "seal_envelope: --guards-from record schema must be 1\n"


def test_guards_from_non_dict_record_refuses(mini_repo: Path, tmp_path: Path):
    record = tmp_path / "record.json"
    record.write_text("[1, 2]\n", encoding="utf-8")
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-006",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 2
    assert sealed.stderr == "seal_envelope: --guards-from record schema must be 1\n"


def test_guards_from_failed_check_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "x"},
                     snapshot="sha256:0", revisions={}, ok=False)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-007",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 2
    assert sealed.stderr == "seal_envelope: --guards-from record reports a failed check\n"


def test_guards_from_capability_mismatch_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", capability="capture.create",
                     payload={"text": "x"}, snapshot="sha256:0", revisions={})
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-008",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 2
    assert sealed.stderr == ("seal_envelope: --guards-from record is for capability "
                             "'capture.create', not 'garden.seed.create'\n")


def test_guards_from_payload_mismatch_refuses(mini_repo: Path, tmp_path: Path):
    record = _record(tmp_path / "record.json", payload={"text": "other"},
                     snapshot="sha256:0", revisions={})
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-009",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 2
    assert sealed.stderr == ("seal_envelope: --guards-from record payload differs "
                             "from the sealing payload\n")


def test_guards_from_missing_file_refuses(mini_repo: Path, tmp_path: Path):
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-010",
                   extra=["--guards-from", str(tmp_path / "absent-record.json")])
    assert sealed.returncode == 2
    assert sealed.stderr.startswith("seal_envelope: ")
    assert "absent-record.json" in sealed.stderr


def test_guards_from_malformed_json_refuses(mini_repo: Path, tmp_path: Path):
    record = tmp_path / "record.json"
    record.write_text("{bad json\n", encoding="utf-8")
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   payload={"text": "x"}, key="guards-from-011",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 2
    assert sealed.stderr.startswith("seal_envelope: ")


def test_guards_from_seals_with_record_guards(mini_repo: Path, tmp_path: Path):
    snapshot = _live_snapshot(mini_repo)
    revisions = {"test/artifact": 9}
    # Key order differs from the sealing payload and the sealing payload
    # carries a "check" entry: both must be canonicalized away.
    record = _record(tmp_path / "record.json",
                     payload={"a": 1, "b": 2},
                     snapshot=snapshot, revisions=revisions)
    out = tmp_path / "sealed.json"
    sealed = _seal(mini_repo, out,
                   payload={"check": {"ignored": True}, "b": 2, "a": 1},
                   key="guards-from-012",
                   extra=["--guards-from", str(record)])
    assert sealed.returncode == 0, sealed.stderr
    assert sealed.stderr == ""
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["capability"] == CAPABILITY
    assert envelope["idempotency_key"] == "guards-from-012"
    assert envelope["expected_snapshot"] == snapshot
    assert envelope["expected_revisions"] == revisions
    assert envelope["payload"] == {"check": {"ignored": True}, "b": 2, "a": 1}
    assert envelope["approval"]["kind"] == "operator-approval"
    assert len(envelope["approval"]["subject_sha256"]) == 71


def test_guards_from_ignores_live_state(mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    snapshot_before = _live_snapshot(mini_repo)
    record = _record(tmp_path / "record.json", payload={"text": "stable"},
                     snapshot=snapshot_before, revisions={"test/artifact": 4})
    first = tmp_path / "first.json"
    sealed = _seal(mini_repo, first, payload={"text": "stable"},
                   key="guards-from-013", extra=["--guards-from", str(record)])
    assert sealed.returncode == 0, sealed.stderr
    assert json.loads(first.read_text(encoding="utf-8"))["expected_snapshot"] == snapshot_before

    add_curriculum(mini_repo)
    snapshot_after = _live_snapshot(mini_repo)
    assert snapshot_after != snapshot_before
    second = tmp_path / "second.json"
    sealed = _seal(mini_repo, second, payload={"text": "stable"},
                   key="guards-from-014", extra=["--guards-from", str(record)])
    assert sealed.returncode == 0, sealed.stderr
    body = json.loads(second.read_text(encoding="utf-8"))
    assert body["expected_snapshot"] == snapshot_before
    assert body["expected_revisions"] == {"test/artifact": 4}

    control = tmp_path / "control.json"
    sealed = _seal(mini_repo, control, payload={"text": "live guard read"},
                   key="guards-from-015", extra=["--guards", "auto"])
    assert sealed.returncode == 0, sealed.stderr
    assert json.loads(control.read_text(encoding="utf-8"))["expected_snapshot"] == snapshot_after


# ---------------------------------------------------------------------------
# The registered record journey (Task 5): check-out, seal, apply.
# ---------------------------------------------------------------------------

TEST_OP = "test-only.pipe"
TEST_CLI_COMMAND = "test-only-pipe"


@pytest.fixture
def check_pipe(mini_repo, monkeypatch):
    """Register the test-only operation with full gateway wiring.

    Catalog row, payload schema and request schema land in the fixture
    repo; the real CLI parser gains the test subcommand for this test
    only; the registry is restored afterwards.
    """
    import yaml

    import los
    from learning_os.ops.registry import REGISTRY, register

    catalog = mini_repo / "system/contracts/capabilities.yaml"
    data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
    data["commands"][TEST_OP] = {
        "handler": "learning_os.adapters.cli.invoke:test-only.pipe",
        "cli_command": TEST_CLI_COMMAND,
        "writes": ["work/inbox/**"],
        "invariants": [],
    }
    catalog.write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    payload_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"test-only/{TEST_OP}",
        "type": "object",
        "properties": {
            "alpha": {"type": "string"},
            "beta": {"type": "integer"},
            "check": {"type": "boolean"},
        },
        "additionalProperties": False,
    }
    path = mini_repo / "system/schema/capabilities"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{TEST_OP}.schema.json").write_text(
        json.dumps(payload_schema, indent=2) + "\n", encoding="utf-8")
    request_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"test-only/{TEST_OP}",
        "type": "object",
        "properties": {
            "alpha": {"type": "string", "default": "A"},
            "beta": {"type": "integer", "default": 3},
            "expected_snapshot": {"type": "string"},
            "expected_revision": {"type": "array"},
        },
    }
    path = mini_repo / "system/schema/requests"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{TEST_OP}.schema.json").write_text(
        json.dumps(request_schema, indent=2) + "\n", encoding="utf-8")

    real_factory = los.build_parser

    def factory():
        parser = real_factory()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                sub = action.add_parser(TEST_CLI_COMMAND)
                sub.add_argument("--alpha", default="A")
                sub.add_argument("--beta", type=int, default=3)
                sub.set_defaults(func=lambda args: 0)
                break
        return parser

    monkeypatch.setattr(los, "build_parser", factory)

    def make(handler=None, *, kind="command", render_check=None):
        def default_handler(ctx, req):
            return Result({"echo": req.get("alpha")})

        register(TEST_OP, kind=kind, render_check=render_check)(
            handler or default_handler)

    yield make
    REGISTRY.pop(TEST_OP, None)


def _seal_in_process(root: Path, out: Path, *, capability: str,
                     payload: dict, key: str,
                     extra: list[str] | None = None) -> int:
    import seal_envelope

    argv = ["--root", str(root), "--capability", capability,
           "--payload", json.dumps(payload), "--key", key,
           "--out", str(out)]
    argv.extend(extra or [])
    return seal_envelope.main(argv)


def _journey_proposal(mini_repo: Path):
    from learning_os.ops.proposal import TransactionProposal

    target = mini_repo / "work/inbox/journey.md"
    return TransactionProposal(
        capability=TEST_OP,
        writes={target: "pipe\n"},
        artifact_ids=("test-only:journey",),
        expected_revisions={"test-only:journey": 0},
    )


def test_registered_check_out_writes_the_record(
        check_pipe, mini_repo: Path, tmp_path: Path, capsys):
    """--check-out on a registered operation writes a passing record."""

    def handler(ctx, req):
        assert ctx.invocation == "check"
        assert ctx.operation == TEST_OP
        return Result({"echo": "x"},
                      proposal=_journey_proposal(mini_repo))

    check_pipe(handler)
    record_path = tmp_path / "record.json"
    out = tmp_path / "sealed.json"
    code = _seal_in_process(
        mini_repo, out, capability=TEST_OP, payload={"alpha": "s"},
        key="journey-001",
        extra=["--guards", "auto", "--check-out", str(record_path)])
    assert code == 0, capsys.readouterr().err
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["schema"] == 1
    assert record["capability"] == TEST_OP
    assert record["ok"] is True
    assert record["errors"] == []
    assert record["payload"] == {"alpha": "s"}
    assert record["expected_revisions"] == {"test-only:journey": 0}
    assert record["writes"] == ["work/inbox/journey.md"]
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["expected_snapshot"] == record["expected_snapshot"]
    assert envelope["expected_revisions"] == record["expected_revisions"]
    assert not (mini_repo / "work/inbox/journey.md").exists()


def test_registered_journey_applies_with_exactly_two_validations(
        check_pipe, mini_repo: Path, tmp_path: Path, monkeypatch, capsys):
    """check-out, seal from the record, apply: one validate per check/apply."""

    from learning_os import rules as rules_module
    from learning_os.commands.capability import cmd_capability
    from learning_os.ops import check as check_module
    from learning_os.ops import commit as commit_module
    from learning_os.rules import core as rules_core

    def handler(ctx, req):
        return Result({"echo": "x"},
                      proposal=_journey_proposal(mini_repo))

    check_pipe(handler)
    calls: list = []
    real_validate = rules_core.validate

    def counted(repo, online=False):
        calls.append(repo)
        return real_validate(repo, online=online)

    monkeypatch.setattr(rules_core, "validate", counted)
    monkeypatch.setattr(rules_module, "validate", counted)
    monkeypatch.setattr(check_module, "validate", counted)
    monkeypatch.setattr(commit_module, "validate", counted)
    record_path = tmp_path / "record.json"
    checked = tmp_path / "checked.json"
    code = _seal_in_process(
        mini_repo, checked, capability=TEST_OP, payload={},
        key="journey-002",
        extra=["--guards", "auto", "--check-out", str(record_path)])
    assert code == 0, capsys.readouterr().err
    assert len(calls) == 1, "exactly one validate per check"

    applied = tmp_path / "applied.json"
    code = _seal_in_process(
        mini_repo, applied, capability=TEST_OP, payload={},
        key="journey-003",
        extra=["--guards-from", str(record_path)])
    assert code == 0, capsys.readouterr().err
    assert len(calls) == 1, "sealing from a record validates nothing"

    args = argparse.Namespace(
        root=str(mini_repo), name=TEST_OP,
        payload_file=str(applied), replay_only=False,
        _parser_factory=_check_parser_factory())
    assert cmd_capability(args) == 0, capsys.readouterr().err
    assert len(calls) == 2, "exactly one validate per apply"
    body = json.loads(capsys.readouterr().out)
    assert body["ok"] is True
    assert body["transaction_id"] is not None
    assert (mini_repo / "work/inbox/journey.md").read_text(
        encoding="utf-8") == "pipe\n"


def _check_parser_factory():
    import los

    return los.build_parser


def test_registered_seal_never_calls_legacy_derivation(
        check_pipe, mini_repo: Path, tmp_path: Path, monkeypatch, capsys):
    """The registered guards-auto path does not touch the interception."""

    import seal_envelope

    def handler(ctx, req):
        return Result({"echo": "x"},
                      proposal=_journey_proposal(mini_repo))

    check_pipe(handler)

    def fail(*args, **kwargs):
        raise AssertionError("legacy guard derivation must not run")

    monkeypatch.setattr(seal_envelope, "_derive_guards_auto", fail)
    out = tmp_path / "sealed.json"
    code = _seal_in_process(
        mini_repo, out, capability=TEST_OP, payload={},
        key="journey-004", extra=["--guards", "auto"])
    assert code == 0, capsys.readouterr().err


def test_registered_check_out_without_proposal_refuses(
        check_pipe, mini_repo: Path, tmp_path: Path, capsys):
    """--check-out needs a registered operation returning a proposal."""

    check_pipe()
    record_path = tmp_path / "record.json"
    out = tmp_path / "sealed.json"
    code = _seal_in_process(
        mini_repo, out, capability=TEST_OP, payload={},
        key="journey-005",
        extra=["--guards", "auto", "--check-out", str(record_path)])
    assert code == 2
    assert capsys.readouterr().err == (
        "seal_envelope: --check-out requires a registered operation "
        "returning a proposal\n")
    assert not record_path.exists()
    assert not out.exists()


def test_registered_guards_auto_without_proposal_refuses(
        check_pipe, mini_repo: Path, tmp_path: Path, capsys):
    """A proposal-less registered handler cannot derive guards."""

    check_pipe()
    out = tmp_path / "sealed.json"
    code = _seal_in_process(
        mini_repo, out, capability=TEST_OP, payload={},
        key="journey-006", extra=["--guards", "auto"])
    assert code == 2
    assert capsys.readouterr().err == (
        "seal_envelope: guard derivation stopped before any transaction "
        "(test-only.pipe returned no proposal); seal this payload with "
        "explicit --revision guards instead\n")
    assert not out.exists()


def test_registered_failed_check_writes_the_record_then_refuses(
        check_pipe, mini_repo: Path, tmp_path: Path, capsys):
    """A failed check still produces its record for the reviewer."""

    from learning_os.ops.proposal import TransactionProposal

    def handler(ctx, req):
        proposal = _journey_proposal(mini_repo)
        proposal = TransactionProposal(
            capability=proposal.capability, writes=proposal.writes,
            artifact_ids=proposal.artifact_ids,
            expected_revisions=dict(proposal.expected_revisions),
            validate_extra=lambda repo, issues: ["broken on purpose"])
        return Result({"echo": "x"}, proposal=proposal)

    check_pipe(handler)
    record_path = tmp_path / "record.json"
    out = tmp_path / "sealed.json"
    code = _seal_in_process(
        mini_repo, out, capability=TEST_OP, payload={},
        key="journey-007",
        extra=["--guards", "auto", "--check-out", str(record_path)])
    assert code == 2
    assert capsys.readouterr().err == (
        "seal_envelope: broken on purpose; fix the payload and seal again\n")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["ok"] is False
    assert record["errors"] == ["broken on purpose"]
    assert record["payload"] == {}
    assert not out.exists()


def test_registered_check_mode_renders_without_committing(
        check_pipe, mini_repo: Path, tmp_path: Path, capsys):
    """payload check:true checks the proposal and renders, never commits."""

    from learning_os.commands.capability import cmd_capability

    rendered_calls: list = []

    def handler(ctx, req):
        assert ctx.invocation == "check"
        return Result({"echo": "prepared", "changes": {"title": "Ä"}},
                      proposal=_journey_proposal(mini_repo))

    def render_check(record, prepared):
        rendered_calls.append(record)
        assert prepared == {"echo": "prepared", "changes": {"title": "Ä"}}
        return {"checked": record["ok"], "writes": record["writes"]}

    check_pipe(handler, render_check=render_check)
    envelope = approved_v2_envelope(
        mini_repo, capability=TEST_OP, payload={"check": True},
        artifact_ids=[], idempotency_key="journey-008")
    payload_file = tmp_path / "envelope.json"
    payload_file.write_text(json.dumps(envelope), encoding="utf-8")
    args = argparse.Namespace(
        root=str(mini_repo), name=TEST_OP, payload_file=str(payload_file),
        replay_only=False, _parser_factory=_check_parser_factory())
    assert cmd_capability(args) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["ok"] is True
    assert body["result"] == {"checked": True, "writes": ["work/inbox/journey.md"]}
    assert len(rendered_calls) == 1
    assert rendered_calls[0]["schema"] == 1
    assert not (mini_repo / "work/inbox/journey.md").exists()
    assert not list(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml"))
