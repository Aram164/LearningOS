"""Shared readiness uses real gateway authority and exact projection bytes."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.app.projection_readiness import (
    dependency_ready,
    observe,
    receipt_completed,
    settlement_ready,
)

ROOT = Path(__file__).resolve().parents[1]


def capture(root, key):
    proc = subprocess.run([sys.executable, str(ROOT / "tools/seal_envelope.py"),
        "--root", str(root), "--session-id", "readiness-test", "--capability", "capture.create",
        "--payload", json.dumps({"text": key}), "--key", key, "--submit"],
        capture_output=True, text=True)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    response = json.loads(proc.stdout)
    return {"receipt_path": response["receipt_path"], "snapshot_after": response["snapshot_after"]}


def test_dependency_ready_at_latest_and_later_known_write(mini_repo):
    a = capture(mini_repo, "ready-a")
    b = capture(mini_repo, "ready-b")
    assert dependency_ready(mini_repo, [a], [a, b]) == (True, "ready")
    assert dependency_ready(mini_repo, [b], [a])[0] is False
    assert dependency_ready(mini_repo, [a, b], [a, b]) == (True, "ready")


def test_dependency_ready_refuses_a_stale_projection_after_an_unpublished_edit(mini_repo):
    a = capture(mini_repo, "ready-a")
    assert dependency_ready(mini_repo, [a], [a]) == (True, "ready")
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text() + "\nUnpublished authored edit.\n")
    ready, reason = dependency_ready(mini_repo, [a], [a])
    assert ready is False and reason != "ready"


def test_unknown_projection_and_missing_receipt_refuse(mini_repo):
    a = capture(mini_repo, "ready-a")
    assert not receipt_completed(mini_repo, a["receipt_path"], "sha256:wrong")
    bad = {"receipt_path": "operations/transactions/nope.yaml", "snapshot_after": a["snapshot_after"]}
    assert not dependency_ready(mini_repo, [bad], [bad])[0]
    path = mini_repo / "generated/manifest.json"
    data = json.loads(path.read_text())
    data["_generated"]["snapshot_id"] = "sha256:wrong"
    path.write_text(json.dumps(data))
    assert observe(mini_repo)["published"] is False


def test_settlement_mode_separates_completion_from_currency(mini_repo):
    a = capture(mini_repo, "ready-a")
    capture(mini_repo, "ready-b")
    out = settlement_ready(mini_repo, a["receipt_path"], a["snapshot_after"])
    assert out["write_completed"] is True and out["settled"] is True
    assert out["current_snapshot_id"] != a["snapshot_after"]
    # Authored edits without publication invalidate currency, not history.
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text() + "\nNew authored text.\n")
    out = settlement_ready(mini_repo, a["receipt_path"], a["snapshot_after"])
    assert out["write_completed"] is True and out["settled"] is False


def test_forged_receipt_is_not_completion(mini_repo):
    path = mini_repo / "operations/transactions/forged.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("status: committed\nsnapshot_after: sha256:fake\n")
    assert not receipt_completed(mini_repo, str(path.relative_to(mini_repo)), "sha256:fake")


@pytest.mark.parametrize("relative", [
    "knowledge/notes/fake.yaml", "operations/transactions/../../knowledge/fake.yaml",
    "operations/transactions-other/fake.yaml", "../outside.yaml", "/tmp/outside.yaml",
])
def test_receipt_paths_are_rejected_before_authority_read(mini_repo, monkeypatch, relative):
    def unexpected(*args):
        pytest.fail("receipt outside the transaction boundary was opened")

    monkeypatch.setattr(Path, "open", unexpected)
    assert not receipt_completed(mini_repo, relative, "sha256:fake")


def test_receipt_symlink_cannot_escape_transaction_boundary(mini_repo):
    target = mini_repo / "knowledge/fake-receipt.yaml"
    target.write_text("status: committed\nsnapshot_after: sha256:fake\n")
    path = mini_repo / "operations/transactions/linked.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)
    assert not receipt_completed(mini_repo, str(path.relative_to(mini_repo)), "sha256:fake")


def test_receipt_parent_symlink_cannot_escape_transaction_boundary(mini_repo, monkeypatch):
    directory = mini_repo / "operations/transactions/linked-parent"
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.symlink_to(mini_repo / "knowledge", target_is_directory=True)
    monkeypatch.setattr(Path, "open", lambda *_: pytest.fail("escaped receipt was opened"))
    assert not receipt_completed(mini_repo, "operations/transactions/linked-parent/fake.yaml", "sha256:fake")


def test_publication_cache_is_deeply_immutable_and_identity_still_validates(mini_repo):
    from learning_os.app import projection_readiness as readiness

    capture(mini_repo, "immutable-publication")
    pair = readiness._publication(str(mini_repo.resolve()),
        readiness._stat(mini_repo / "generated/manifest.json"),
        readiness._stat(mini_repo / "generated/manifest.identity.json"))
    assert pair is not None
    with pytest.raises(TypeError):
        pair[0]["_generated"]["snapshot_id"] = "forged"
    with pytest.raises(TypeError):
        pair[1]["snapshot_id"] = "forged"
    assert observe(mini_repo)["published"] is True


def test_authority_retries_once_after_a_real_concurrent_commit(mini_repo, monkeypatch):
    from learning_os.app import projection_readiness as readiness

    first = capture(mini_repo, "race-first")
    actual = readiness.collect_authority
    calls = []

    def concurrent(*args, **kwargs):
        authority = actual(*args, **kwargs)
        calls.append(1)
        if len(calls) == 1:
            capture(mini_repo, "race-second")
        return authority

    monkeypatch.setattr(readiness, "collect_authority", concurrent)
    result = settlement_ready(mini_repo, first["receipt_path"], first["snapshot_after"])
    assert result["write_completed"] is True and result["settled"] is True
    assert result["current_snapshot_id"] != first["snapshot_after"]
    assert len(calls) == 2


def test_repeated_ledger_instability_fails_closed(mini_repo, monkeypatch):
    from learning_os.app import projection_readiness as readiness

    first = capture(mini_repo, "unstable-first")
    actual = readiness.collect_authority
    calls = []

    def concurrent(*args, **kwargs):
        authority = actual(*args, **kwargs)
        calls.append(1)
        ledger = mini_repo / "operations/transactions/idempotency.yaml"
        ledger.write_text(ledger.read_text() + "\n")
        return authority

    monkeypatch.setattr(readiness, "collect_authority", concurrent)
    assert not receipt_completed(mini_repo, first["receipt_path"], first["snapshot_after"])
    assert len(calls) == 2


def test_receipt_change_during_authority_read_cannot_reuse_old_verification(mini_repo, monkeypatch):
    from learning_os.app import projection_readiness as readiness

    first = capture(mini_repo, "receipt-race")
    actual = readiness.collect_authority
    calls = []

    def concurrent(*args, **kwargs):
        authority = actual(*args, **kwargs)
        calls.append(1)
        (mini_repo / first["receipt_path"]).write_text("snapshot_after: forged\n")
        return authority

    monkeypatch.setattr(readiness, "collect_authority", concurrent)
    assert not receipt_completed(mini_repo, first["receipt_path"], first["snapshot_after"])
    assert len(calls) == 1
