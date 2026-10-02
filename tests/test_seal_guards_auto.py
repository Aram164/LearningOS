"""Automatic guard derivation for the sealing helper (#80).

`seal_envelope.py --guards auto` derives the exact transaction artifact
set with a gateway dry run and reads revisions under the same lock as
the snapshot, so the sealed envelope commits on the first submission.
A concurrent canonical change still refuses as `STALE_SNAPSHOT`, and
explicit `--revision` entries still win.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from gateway_helpers import file_sha256, run_v2_capability

from learning_os.fingerprint import canonical_fingerprint

SEAL = Path(__file__).resolve().parent.parent / "tools" / "seal_envelope.py"

FIRST_SUBMISSION_CASES = [
    ("stage.progress.update", "guards-auto-progress-001",
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "status": "active"}),
    ("stage.note.write", "guards-auto-note-001",
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "text": "auto-guard note line"}),
    ("stage.attachment.add", "guards-auto-attach-001", None),  # needs a file
    ("source.feedback.record", "guards-auto-feedback-001",
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "source_id": "source-demo-book", "feedback": "helpful"}),
    ("capture.create", "guards-auto-capture-001",
     {"text": "auto-guard capture"}),
    ("garden.seed.create", "guards-auto-garden-001",
     {"text": "auto-guard seed"}),
]


def _seal(root: Path, out: Path, *, capability: str, payload: dict,
          key: str, extra: list[str] | None = None):
    command = [sys.executable, str(SEAL), "--root", str(root),
               "--capability", capability, "--payload", json.dumps(payload),
               "--key", key, "--guards", "auto", "--out", str(out)]
    command.extend(extra or [])
    return subprocess.run(command, capture_output=True, text=True, timeout=120)


def _submit(root: Path, envelope_path: Path):
    return run_v2_capability(
        root, json.loads(envelope_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("capability,key,payload", FIRST_SUBMISSION_CASES,
                         ids=[case[0] for case in FIRST_SUBMISSION_CASES])
def test_guards_auto_commits_on_the_first_submission(
        mini_repo: Path, tmp_path: Path, capability: str, key: str,
        payload: dict | None):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    if payload is None:  # stage.attachment.add needs a real approved file
        source = tmp_path / "attachment.txt"
        source.write_text("auto-guard attachment bytes", encoding="utf-8")
        payload = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                   "file": str(source), "file_sha256": file_sha256(source),
                   "label": "auto"}
    sealed = _seal(mini_repo, tmp_path / "sealed.json", capability=capability,
                   payload=payload, key=key)
    assert sealed.returncode == 0, sealed.stderr
    assert "guards auto:" in sealed.stderr
    applied = _submit(mini_repo, tmp_path / "sealed.json")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    body = json.loads(applied.stdout)
    assert body["ok"] is True, body
    assert body["replayed"] is False


def test_concurrent_canonical_change_still_refuses_as_stale_snapshot(
        mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    first = _seal(mini_repo, tmp_path / "first.json",
                  capability="garden.seed.create",
                  payload={"text": "sealed before the concurrent write"},
                  key="guards-auto-stale-001")
    assert first.returncode == 0, first.stderr
    concurrent = _seal(mini_repo, tmp_path / "concurrent.json",
                       capability="capture.create",
                       payload={"text": "concurrent write"},
                       key="guards-auto-stale-002")
    assert concurrent.returncode == 0, concurrent.stderr
    applied = _submit(mini_repo, tmp_path / "concurrent.json")
    assert applied.returncode == 0, applied.stdout
    assert json.loads(applied.stdout)["ok"] is True
    stale = _submit(mini_repo, tmp_path / "first.json")
    assert stale.returncode == 3, stale.stdout
    body = json.loads(stale.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "STALE_SNAPSHOT"


def test_explicit_revision_wins_over_derived_guards(mini_repo: Path,
                                                   tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="stage.progress.update",
                   payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                            "status": "active"},
                   key="guards-auto-override-001",
                   extra=["--revision", "unit-demo-l01=99"])
    assert sealed.returncode == 0, sealed.stderr
    envelope = json.loads((tmp_path / "sealed.json").read_text(encoding="utf-8"))
    assert envelope["expected_revisions"]["unit-demo-l01"] == 99
    assert envelope["expected_revisions"]["study-map-demo-l01"] == 0
    applied = _submit(mini_repo, tmp_path / "sealed.json")
    assert applied.returncode == 3, applied.stdout
    assert json.loads(applied.stdout)["error"]["code"] == "REVISION_CONFLICT"


def test_guard_derivation_writes_nothing(mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    fingerprint_before = canonical_fingerprint(mini_repo)
    tree_before = {path for path in mini_repo.rglob("*")}
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="source.feedback.record",
                   payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                            "source_id": "source-demo-book",
                            "feedback": "helpful"},
                   key="guards-auto-dry-001")
    assert sealed.returncode == 0, sealed.stderr
    assert canonical_fingerprint(mini_repo) == fingerprint_before
    assert {path for path in mini_repo.rglob("*")} == tree_before


def test_guard_derivation_refuses_an_invalid_payload_at_seal_time(
        mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="stage.progress.update",
                   payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                            "status": "done"},
                   key="guards-auto-invalid-001")
    assert sealed.returncode == 2
    assert "invalid payload" in sealed.stderr
    for allowed in ("active", "paused", "complete", "skipped", "revisit"):
        assert allowed in sealed.stderr


def test_envelope_without_schema_version_is_refused_before_dispatch(
        mini_repo: Path, tmp_path: Path):
    envelope = {"request_id": "req-no-version",
                "capability": "capture.create",
                "payload": {"text": "no version"}}
    payload_file = tmp_path / "envelope.json"
    payload_file.write_text(json.dumps(envelope), encoding="utf-8")
    result = subprocess.run(
        [sys.executable,
         str(Path(__file__).resolve().parent.parent / "tools" / "los.py"),
         "--root", str(mini_repo), "capability", "capture.create",
         "--payload-file", str(payload_file)],
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 2
    assert result.stdout == "", "a refused envelope must print no response"
    assert ("invalid capability envelope: schema_version 2 required "
            "(WORKFLOWS §25c)") in result.stderr


def test_guard_derivation_intercepts_every_commit_path(mini_repo: Path,
                                                       monkeypatch):
    """A handler that commits through its own TransactionService import is
    still stopped at the boundary.

    The AI delivery path constructs ``TransactionService`` from its own
    import rather than through ``support._write_transaction``. Intercepting
    one module's name would let such a handler reach the real ``commit``
    with the dry run's placeholder approval; the class-level boundary must
    capture it like any other.
    """
    import seal_envelope

    import los
    from learning_os import transactions

    real_build_parser = los.build_parser
    real_commit = transactions.TransactionService.commit

    def direct_commit_handler(args):
        probe = Path(args.root) / "work/inbox/direct-commit-probe.md"
        transactions.TransactionService(Path(args.root)).commit(
            capability="stage.note.write",
            writes={probe: "direct-commit probe\n"},
            artifact_ids=["unit-demo-l01"])
        return 0

    def build_parser():
        parser = real_build_parser()
        from learning_os.contracts.payloads import subparsers
        subparsers(parser)["stage-note"].set_defaults(func=direct_commit_handler)
        return parser

    monkeypatch.setattr(los, "build_parser", build_parser)
    before = canonical_fingerprint(mini_repo)
    receipts = sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml"))

    snapshot, derived = seal_envelope._derive_guards_auto(
        mini_repo, capability="stage.note.write",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "text": "direct-commit probe"},
        key="guards-auto-direct-001", request_id="request-guards-auto-direct-001",
        channel="operator", approval_kind="operator-approval", snapshot=None)

    assert derived == {"unit-demo-l01": 0}
    assert snapshot == f"sha256:{before}"
    assert canonical_fingerprint(mini_repo) == before
    assert sorted((mini_repo / "operations/transactions").glob(
        "transaction-*.yaml")) == receipts
    assert not (mini_repo / "work/inbox/direct-commit-probe.md").exists()
    assert transactions.TransactionService.commit is real_commit
