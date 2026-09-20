"""Stage-5 manifest proof: real-repository replay on a disposable clone.

Copies the live tree (history included, so git-date pinning is real),
links the materials farm when present, then replays localized mutations
and proves byte-exact shadow equality with the expected reuse shape at
each step. Assertions stay at rebuilt/hit level plus structural prunes:
exact full partitions live in the synthetic matrix, which cannot drift
with the checked-in data.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from learning_os.derived.store import derived_dir, read_state
from learning_os.genout.manifest_derived import (
    AI_ACTIONS_ID,
    COUNTS_ID,
    EDGES_ID,
    GARDEN_ID,
    NOTES_ID,
    PROGRESS_ID,
    RECORDS_ID,
    RELATIONS_ID,
    REVIEW_ITEMS_ID,
    REVISIONS_ID,
    SEMANTIC_PAYLOAD_ID,
    STAGES_ID,
    STUDY_MAPS_ID,
    SYNTHSES_ID,
    TYPED_COLLECTIONS_ID,
    UNITS_ID,
    VALIDATION_PROOF_ID,
    compare_shadow_manifest,
)
from learning_os.githistory import last_commit_dates, last_commit_timestamps
from learning_os.loader import load_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
MATERIALS = REPO_ROOT.parent / "materials"
STAMP = "2026-09-20T00:00:00+02:00"
REPLAY_NOTE = (
    "knowledge/notes/algorithms/note-algo2-amortized-analysis-exercise-bank.md"
)


def _copy_live_tree(tmp_path: Path) -> Path:
    copy = tmp_path / "live"
    shutil.copytree(
        REPO_ROOT, copy,
        ignore=shutil.ignore_patterns(
            ".venv", "generated", "__pycache__", ".pytest_cache",
            ".ruff_cache", ".DS_Store"),
    )
    farm = tmp_path / "materials"
    if MATERIALS.is_dir() and not farm.exists():
        farm.symlink_to(MATERIALS)
    return copy


def _rerun(copy: Path):
    """One shadow comparison with fresh git observations, like a CLI run."""
    last_commit_dates.cache_clear()
    last_commit_timestamps.cache_clear()
    trace: list = []
    comparison = compare_shadow_manifest(load_repo(copy), STAMP, trace=trace)
    assert comparison.equivalent
    return {event.node: (event.status, event.reason) for event in trace}


def _rewrite(path: Path, mutate) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


@pytest.mark.full_repo
def test_real_repo_manifest_replay(tmp_path: Path):
    copy = _copy_live_tree(tmp_path)

    cold = _rerun(copy)
    assert cold
    assert all(status == "rebuilt" for status, _ in cold.values())

    warm = _rerun(copy)
    assert all(status == "hit" for status, _ in warm.values())

    note_a = copy / REPLAY_NOTE
    note_a.write_text(note_a.read_text(encoding="utf-8") + "\nReplay prose.\n",
                      encoding="utf-8")
    trailing = _rerun(copy)
    assert trailing[RECORDS_ID][0] == "hit"
    assert trailing[SEMANTIC_PAYLOAD_ID][0] == "hit"
    assert trailing[VALIDATION_PROOF_ID][0] == "rebuilt"

    note_b = next(
        note for note in sorted((copy / "knowledge/notes").rglob("*.md"))
        if note != note_a and "title: " in note.read_text(encoding="utf-8"))
    lines = note_b.read_text(encoding="utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines[:20]):
        if line.startswith("title: "):
            lines[index] = "title: Replay retitle\n"
            break
    note_b.write_text("".join(lines), encoding="utf-8")
    retitled = _rerun(copy)
    assert retitled[NOTES_ID][0] == "rebuilt"
    assert retitled[RECORDS_ID][0] == "rebuilt"
    assert retitled[TYPED_COLLECTIONS_ID] == (
        "rebuilt", "node-key-changed-output-same")
    assert retitled[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    def add_relation(doc) -> None:
        first = doc["relations"][0]
        doc["relations"].append({"from": first["to"], "type": "replay-link",
                                 "to": first["from"]})

    _rewrite(copy / "knowledge/concept-relations.yaml", add_relation)
    related = _rerun(copy)
    assert related[RELATIONS_ID][0] == "rebuilt"
    assert related[RECORDS_ID][0] == "hit"
    assert related[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    _rewrite(copy / "sources/registry/algorithms.yaml",
             lambda doc: doc["sources"][0].update(
                 title=doc["sources"][0]["title"] + " (replay)"))
    resourced = _rerun(copy)
    assert resourced[STUDY_MAPS_ID][0] == "rebuilt"
    assert resourced[UNITS_ID][0] == "hit"
    assert resourced[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    workspace = sorted((copy / "work/active").glob("*/CONTEXT.md"))[0]
    workspace.write_text(workspace.read_text(encoding="utf-8") + "\nReplay.\n",
                         encoding="utf-8")
    worked = _rerun(copy)
    assert worked[RECORDS_ID][0] == "hit"
    assert worked[SEMANTIC_PAYLOAD_ID][0] == "hit"

    def bump_ledger(doc) -> None:
        doc["revisions"]["unit-aml-l01"] = doc["revisions"]["unit-aml-l01"] + 1

    _rewrite(copy / "operations/transactions/revisions.yaml", bump_ledger)
    bumped = _rerun(copy)
    assert bumped[REVISIONS_ID][0] == "rebuilt"
    assert bumped[UNITS_ID][0] == "rebuilt"
    assert bumped[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    (copy / "work/inbox/replay-probe.md").write_text("# Replay\n", encoding="utf-8")
    routed = _rerun(copy)
    assert routed[REVIEW_ITEMS_ID][0] == "rebuilt"
    assert routed[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    (copy / "knowledge/garden/replay-seed.md").write_text(
        "Replay seed. #replay\n", encoding="utf-8")
    seeded = _rerun(copy)
    assert seeded[GARDEN_ID][0] == "rebuilt"
    assert seeded[AI_ACTIONS_ID][0] == "rebuilt"
    assert seeded[RECORDS_ID][0] == "hit"

    def flip_request(doc) -> None:
        doc["status"] = (
            "delivery-ready" if doc["status"] == "completed" else "completed")

    _rewrite(copy / "operations/ai-actions/requests/ai-request-sad-l04-pilot"
             / "request.yaml", flip_request)
    requested = _rerun(copy)
    assert requested[AI_ACTIONS_ID][0] == "rebuilt"
    assert requested[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    flipped = None
    for study_map in sorted(
            (copy / "curriculum/modules").glob("*/units/*/study-map.yaml")):
        doc = yaml.safe_load(study_map.read_text(encoding="utf-8"))
        target = next((stage for stage in doc.get("stages") or []
                       if isinstance(stage, dict) and stage.get("status") == "active"),
                      None)
        if target is not None:
            target["status"] = "complete"
            study_map.write_text(yaml.safe_dump(doc, sort_keys=False),
                                 encoding="utf-8")
            flipped = study_map
            break
    assert flipped is not None, "no active stage to flip"
    staged = _rerun(copy)
    assert staged[STAGES_ID][0] == "rebuilt"
    assert staged[PROGRESS_ID][0] == "rebuilt"
    assert staged[EDGES_ID] == ("rebuilt", "node-key-changed-output-same")

    edited = None
    for source_map in sorted((copy / "curriculum/modules").glob("*/source-map.yaml")):
        doc = yaml.safe_load(source_map.read_text(encoding="utf-8"))
        entry = next((row for row in doc.get("sources") or []
                      if isinstance(row, dict) and isinstance(row.get("why"), str)),
                     None)
        if entry is not None:
            entry["why"] += " (replay)"
            source_map.write_text(yaml.safe_dump(doc, sort_keys=False),
                                  encoding="utf-8")
            edited = source_map
            break
    assert edited is not None, "no source-map rationale to edit"
    angled = _rerun(copy)
    assert angled[STUDY_MAPS_ID] == ("rebuilt", "node-key-changed-output-same")
    assert angled[SYNTHSES_ID] == ("rebuilt", "node-key-changed-output-same")
    assert angled[UNITS_ID] == ("rebuilt", "node-key-changed-output-same")
    assert angled[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"

    subprocess.run(["git", "add", "-A"], cwd=copy, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=replay@local", "-c", "user.name=replay",
                    "commit", "-m", "replay", "--no-verify"],
                   cwd=copy, check=True, capture_output=True)
    committed = _rerun(copy)
    assert committed[COUNTS_ID][0] == "rebuilt"
    assert committed[VALIDATION_PROOF_ID][0] == "rebuilt"

    blob = derived_dir(copy) / read_state(copy)[RECORDS_ID].blob
    blob.write_bytes(b"forged-bytes")
    forged = _rerun(copy)
    assert forged[RECORDS_ID] == ("rebuilt", "cache-miss")
    assert forged[VALIDATION_PROOF_ID] == ("hit", "node-key-equal")

    healed = _rerun(copy)
    assert all(status == "hit" for status, _ in healed.values())

    shutil.rmtree(copy / "generated/derived-state")
    clean = _rerun(copy)
    assert all(status == "rebuilt" for status, _ in clean.values())
    assert all(reason == "cache-miss" for _, reason in clean.values())
