"""Append-only LearnKit export: plan/apply, keeps, refusals (P6 steps 37-40)."""
import json
import subprocess
import sys
from pathlib import Path

from gateway_helpers import approved_v2_call
from test_practice_verification import BANK_SOLUTION, _binding, _note

EXPORTER = Path(__file__).resolve().parent.parent / "tools" / "export_learnkit.py"
ITEM = "note-practice-bank#A1"


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
        "artifact_sha256": "c" * 64, "reviewer_id": "aram",
        "source_binding": binding, "comparison_sha256": None,
    }
    result = approved_v2_call(
        mini_repo, capability="practice.verification.record",
        payload={"record": record},
        artifact_ids=["registry-practice-index", "note-practice-bank"],
        idempotency_key="export-verify")
    assert result.returncode == 0, result.stdout + result.stderr


def test_init_check_apply_keep_cycle(mini_repo, tmp_path):
    _verify(mini_repo)
    vault = tmp_path / "practice-vault"
    plan = tmp_path / "plan.json"

    refused = export(mini_repo, "--vault", str(mini_repo / "vault"), "--init")
    assert refused.returncode == 2  # intersects the Core repository

    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    marker = json.loads((vault / ".learningos-practice-vault.json").read_text())
    assert marker["purpose"] == "learnkit-practice" and marker["experimental"]
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 2

    checked = export(mini_repo, "--vault", str(vault), "--check",
                     "--item", ITEM, "--out", str(plan))
    assert checked.returncode == 0, checked.stdout
    document = json.loads(plan.read_text())
    assert document["items"][0]["action"] == "create"
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

    before = cards[0].read_bytes()
    rechecked = export(mini_repo, "--vault", str(vault), "--check",
                       "--item", ITEM, "--out", str(plan))
    assert rechecked.returncode == 0
    assert json.loads(plan.read_text())["items"][0]["action"] == "keep"
    assert export(mini_repo, "--vault", str(vault), "--apply", str(plan)).returncode == 0
    assert cards[0].read_bytes() == before  # byte-identical replay


def test_changed_reviewed_card_refuses_with_exact_message(mini_repo, tmp_path):
    _verify(mini_repo)
    vault = tmp_path / "practice-vault"
    plan = tmp_path / "plan.json"
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
    import yaml
    old = yaml.safe_load((mini_repo / "knowledge/practice-index.yaml").read_text())["items"][0]
    record = {
        "item_id": ITEM, "expected_old": old,
        "new_status": "confirmed", "method": "explicit-review",
        "concept_ids": ["concept-expected-value"],
        "artifact_sha256": "d" * 64, "reviewer_id": "aram",
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


def test_unverified_and_linked_roots_refuse(mini_repo, tmp_path):
    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    vault = tmp_path / "practice-vault"
    plan = tmp_path / "plan.json"
    assert export(mini_repo, "--vault", str(vault), "--init").returncode == 0
    assert export(mini_repo, "--vault", str(vault), "--check",
                  "--item", ITEM, "--out", str(plan)).returncode == 0
    assert json.loads(plan.read_text())["items"][0]["action"] == "refuse"
    applied = export(mini_repo, "--vault", str(vault), "--apply", str(plan))
    assert applied.returncode == 2
    assert not (vault / "Cards").exists() or not list((vault / "Cards").glob("*.md"))

    linked = tmp_path / "linked"
    linked.symlink_to(vault, target_is_directory=True)
    assert export(mini_repo, "--vault", str(linked), "--init").returncode == 2

    unmarked = tmp_path / "unmarked"
    unmarked.mkdir()
    checked = export(mini_repo, "--vault", str(unmarked), "--check",
                     "--item", ITEM, "--out", str(plan))
    assert checked.returncode == 2
