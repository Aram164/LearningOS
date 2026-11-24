"""Append-only LearnKit export: plan/apply, keeps, refusals (P6 steps 37-40)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from gateway_helpers import approved_v2_call
from repo_builders import run_los
from test_practice_verification import BANK_SOLUTION, _binding, _note, _reviewed_digest

EXPORTER = Path(__file__).resolve().parent.parent / "tools" / "export_learnkit.py"
ITEM = "note-practice-bank#A1"


@pytest.fixture
def outside():
    """A scratch root outside every checkout and the paired Core/UI workspace.

    CI puts pytest's basetemp inside its paired workspace
    (`<work>/LearningOS/{repository,obsidian-ui}`), which the exporter rightly
    refuses as a practice-vault location; the pytest temp path passed locally
    only because the local basetemp lies elsewhere.
    """
    root = Path(tempfile.mkdtemp(prefix="los-practice-export-")).resolve()
    yield root
    shutil.rmtree(root, ignore_errors=True)


def export(root, *args):
    return subprocess.run(
        [sys.executable, str(EXPORTER), "--root", str(root), *args],
        capture_output=True, text=True, timeout=120)


def _verify(mini_repo):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    binding = _binding(mini_repo)
    record = {
        "item_id": ITEM, "expected_old": None,
        "new_status": "source-matched", "method": "official-source",
        "concept_ids": ["concept-expected-value"],
        "artifact_sha256": _reviewed_digest(ITEM), "reviewer_id": "aram",
        "source_binding": binding, "comparison_sha256": None,
    }
    result = approved_v2_call(
        mini_repo, capability="practice.verification.record",
        payload={"record": record},
        artifact_ids=["registry-practice-index", "note-practice-bank"],
        idempotency_key="export-verify")
    assert result.returncode == 0, result.stdout + result.stderr


def test_init_check_apply_keep_cycle(mini_repo, outside):
    _verify(mini_repo)
    vault = outside / "practice-vault"
    plan = outside / "plan.json"

    refused = export(mini_repo, "--vault", str(mini_repo / "vault"), "--init")
    assert refused.returncode == 2  # intersects the Core repository

    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    marker = json.loads((vault / ".learningos-practice-vault.json").read_text())
    assert marker["purpose"] == "learnkit-practice" and marker["experimental"]
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 2
    for target in (mini_repo / "knowledge/practice-index.yaml", vault / "plan.json"):
        previous = target.read_bytes() if target.exists() else None
        blocked = export(mini_repo, "--vault", str(vault), "--check",
                         "--item", ITEM, "--out", str(target))
        assert blocked.returncode == 2 and "outside Core and the practice vault" in blocked.stdout
        assert (target.read_bytes() if target.exists() else None) == previous


    checked = export(mini_repo, "--vault", str(vault), "--check",
                     "--item", ITEM, "--out", str(plan))
    assert checked.returncode == 0, checked.stdout
    document = json.loads(plan.read_text())
    assert document["items"][0]["action"] == "create"
    assert len(document["source_content_hashes"][ITEM]) == 64
    assert "What is 2+2" not in plan.read_text()  # no card text in the plan

    applied = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert applied.returncode == 0, applied.stdout
    cards = list((vault / "Cards").glob("*.md"))
    assert len(cards) == 1
    body = cards[0].read_text()
    lines = body.splitlines()
    assert lines[0].startswith("Q | ") and "2+2" in lines[0]
    assert lines[1] == "A | 4 |"
    assert lines[2].startswith(f"I | {ITEM} · source-demo-book · pdf p. 1")
    assert lines[3] == "G | concept-expected-value |"
    assert "^learnkit-" not in body  # no plugin anchor is supplied

    # Model a plugin-owned leading anchor. The original create plan can be
    # replayed after an equivalent file appears.
    cards[0].write_text("^learnkit-12345\n" + body + "\n")
    before = cards[0].read_bytes()
    replay = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert json.loads(replay.stdout) == {"status": "applied", "created": 0, "kept": 1}
    assert cards[0].read_bytes() == before
    rechecked = export(mini_repo, "--vault", str(vault), "--check",
                       "--item", ITEM, "--out", str(plan))
    assert rechecked.returncode == 0
    assert json.loads(plan.read_text())["items"][0]["action"] == "keep"
    assert export(mini_repo, "--vault", str(vault), "--apply", str(plan)).returncode == 0
    assert cards[0].read_bytes() == before  # byte-identical replay
    updated = before + b"\n"
    cards[0].write_bytes(updated)
    refused = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert refused.returncode == 2 and "card changed since check" in refused.stdout
    assert cards[0].read_bytes() == updated



def test_changed_reviewed_card_refuses_with_exact_message(mini_repo, outside):
    _verify(mini_repo)
    vault = outside / "practice-vault"
    plan = outside / "plan.json"
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    assert export(mini_repo, "--vault", str(vault), "--check",
                  "--item", ITEM, "--out", str(plan)).returncode == 0
    assert export(mini_repo, "--vault", str(vault), "--apply", str(plan)).returncode == 0
    card = next((vault / "Cards").glob("*.md"))
    before = card.read_bytes()

    # Reverify against a changed canonical answer: the item is checked again
    # under a new content hash, so the existing card now differs.
    path = mini_repo / "knowledge/notes/mathematics/note-practice-bank.md"
    path.write_text(path.read_text().replace("\n4\n", "\nFour\n"), encoding="utf-8")
    context = run_los(mini_repo, "practice-context", "note-practice-bank", "--item-id", ITEM)
    assert context.returncode == 0, context.stdout + context.stderr
    old = json.loads(context.stdout)["items"][0]["stored_row"]
    record = {
        "item_id": ITEM, "expected_old": old,
        "new_status": "confirmed", "method": "explicit-review",
        "concept_ids": ["concept-expected-value"],
        "artifact_sha256": _reviewed_digest(
            ITEM, BANK_SOLUTION.replace("\n4\n", "\nFour\n")),
        "reviewer_id": "aram",
        "source_binding": None, "comparison_sha256": None,
    }
    result = approved_v2_call(
        mini_repo, capability="practice.verification.record",
        payload={"record": record},
        artifact_ids=["registry-practice-index", "note-practice-bank"],
        idempotency_key="export-reverify")
    assert result.returncode == 0, result.stdout + result.stderr

    assert export(mini_repo, "--vault", str(vault), "--check",
                  "--item", ITEM, "--out", str(plan)).returncode == 0
    assert json.loads(plan.read_text())["items"][0]["action"] == "changed-existing"
    applied = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert applied.returncode == 2
    assert ("Existing reviewed card differs. Resolve it through a separate "
            "card-replacement workflow.") in applied.stdout
    assert card.read_bytes() == before  # never rewritten


def test_unverified_and_linked_roots_refuse(mini_repo, outside):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    vault = outside / "practice-vault"
    plan = outside / "plan.json"
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    assert export(mini_repo, "--vault", str(vault), "--check",
                  "--item", ITEM, "--out", str(plan)).returncode == 0
    assert json.loads(plan.read_text())["items"][0]["action"] == "refuse"
    applied = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert applied.returncode == 2
    assert not (vault / "Cards").exists() or not list((vault / "Cards").glob("*.md"))

    linked = outside / "linked"
    linked.symlink_to(vault, target_is_directory=True)
    assert export(mini_repo, "--vault", str(linked), "--init").returncode == 2

    unmarked = outside / "unmarked"
    unmarked.mkdir()
    checked = export(mini_repo, "--vault", str(unmarked), "--check",
                     "--item", ITEM, "--out", str(plan))
    assert checked.returncode == 2


def test_a_fabricated_stored_excerpt_is_not_exported(mini_repo, outside):
    """A hand-edited proof cannot carry an item into the practice vault."""
    import yaml

    _verify(mini_repo)
    path = mini_repo / "knowledge/practice-index.yaml"
    data = yaml.safe_load(path.read_text())
    row = data["items"][0]
    row["source_bindings"][0]["quote"] = "Invented, nowhere on the page."
    row["verifications"][0]["source_binding"]["quote"] = "Invented, nowhere on the page."
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    vault = outside / "practice-vault"
    plan = outside / "plan.json"
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    assert export(mini_repo, "--vault", str(vault), "--check",
                  "--item", ITEM, "--out", str(plan)).returncode == 0
    [entry] = json.loads(plan.read_text())["items"]
    assert entry["action"] == "refuse" and "not checked" in entry["reason"]
    assert export(mini_repo, "--vault", str(vault), "--apply", str(plan)).returncode == 2
    assert not (vault / "Cards").exists() or not list((vault / "Cards").glob("*.md"))


def test_export_flock_busy_refusal_release_and_corrupt_sidecar(mini_repo, outside):
    _verify(mini_repo)
    vault = outside / "practice-vault"
    plan = outside / "plan.json"
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    assert export(mini_repo, "--vault", str(vault), "--check",
                  "--item", ITEM, "--out", str(plan)).returncode == 0

    sidecar = mini_repo / "knowledge/practice-index.yaml"
    saved_sidecar = sidecar.read_text(encoding="utf-8")
    sidecar.write_text("items: [\n", encoding="utf-8")
    bad_sidecar = export(mini_repo, "--vault", str(vault), "--check",
                         "--item", ITEM, "--out", str(outside / "bad.json"))
    assert bad_sidecar.returncode == 2
    assert "practice-index unreadable" in bad_sidecar.stdout + bad_sidecar.stderr
    import yaml
    leaked_data = yaml.safe_load(saved_sidecar)
    secret = "EXPORT_SECRET_LEAK_" + ("x" * 240)
    leaked_data["items"][0]["source_bindings"][0]["quote"] = secret
    leaked_data["items"][0]["verifications"][0]["source_binding"]["quote"] = secret
    sidecar.write_text(yaml.safe_dump(leaked_data, sort_keys=False), encoding="utf-8")
    overlong_sidecar = export(mini_repo, "--vault", str(vault), "--check",
                              "--item", ITEM, "--out", str(outside / "bad2.json"))
    assert overlong_sidecar.returncode == 2
    overlong_out = overlong_sidecar.stdout + overlong_sidecar.stderr
    assert "items.0.source_bindings.0.quote" in overlong_out
    assert "EXPORT_SECRET_LEAK_" not in overlong_out
    sidecar.write_text(saved_sidecar, encoding="utf-8")

    cards_dir = vault / "Cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    lock_path = cards_dir / ".los-export.lock"

    # Symlink lock refuses cleanly without unlinking the target.
    target = outside / "sym-target"
    target.write_text("keep", encoding="utf-8")
    os.symlink(str(target), lock_path)
    sym_refused = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert sym_refused.returncode == 2
    assert str(lock_path) in sym_refused.stdout + sym_refused.stderr
    assert target.read_text(encoding="utf-8") == "keep"
    lock_path.unlink()

    # Subprocess takes a kernel flock on the persistent lock file and signals readiness;
    # concurrent export refuses, and a later export acquires the same inode after exit.
    holder_script = (
        "import fcntl, os, sys; "
        "fd = os.open(sys.argv[1], os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600); "
        "fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); "
        "print('LOCKED', flush=True); "
        "sys.stdin.read()"
    )
    holder = subprocess.Popen(
        [sys.executable, "-c", holder_script, str(lock_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "LOCKED"
        lock_inode = lock_path.stat().st_ino
        busy_refused = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
        assert busy_refused.returncode == 2
        assert str(lock_path) in busy_refused.stdout + busy_refused.stderr
    finally:
        if holder.stdin is not None:
            holder.stdin.close()
        _, holder_err = holder.communicate(timeout=10)
    assert holder.returncode == 0, holder_err
    assert lock_path.exists() and lock_path.stat().st_ino == lock_inode

    after_release = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert after_release.returncode == 0, after_release.stdout + after_release.stderr
    assert lock_path.exists() and lock_path.stat().st_ino == lock_inode
