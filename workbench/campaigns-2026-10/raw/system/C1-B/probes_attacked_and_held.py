"""C1-B hunting probes: state-machine and shelving behaviour, observed live.

Exploratory file for the 2026-10-24 C1-B batch. Each test drives the real
V2 gateway against a two-stage mini fixture and records what actually
happens; a probe "failing" is an observed behaviour worth judging, not
necessarily a defect.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from conftest import build_mini_repo  # noqa: F401  (mini_repo lives in conftest)
from gateway_helpers import approved_v2_call
from repo_builders import add_curriculum, write_yaml
from learning_os.app.validation_service import collect
from learning_os.store.warning_baseline import write_baseline

STAGE_TWO_NOTE = ("curriculum/modules/module-demo/units/unit-demo-l01/"
                  "stages/stage-two/notes.md")


def two_stage_repo(mini_repo: Path) -> Path:
    """The demo curriculum plus a second, pending stage on the demo map."""
    add_curriculum(mini_repo)
    map_path = mini_repo / ("curriculum/modules/module-demo/units/"
                            "unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    first = data["stages"][0]
    (mini_repo / STAGE_TWO_NOTE).parent.mkdir(parents=True, exist_ok=True)
    (mini_repo / STAGE_TWO_NOTE).write_text("", encoding="utf-8")
    second = dict(first)
    second.update({
        "id": "stage-two", "title": "Variance", "status": "pending",
        "objective": "Derive variance.",
        "done_when": ["Explain the variance."],
        "working_note": STAGE_TWO_NOTE,
        "attachments": [], "source_feedback": [],
    })
    data["stages"].append(second)
    write_yaml(map_path, data)
    signatures, errors = collect(mini_repo)
    assert not errors, errors
    write_baseline(mini_repo, signatures, "C1-B probe fixture")
    return mini_repo


def _map_of(root: Path) -> dict:
    return yaml.safe_load((root / "curriculum/modules/module-demo/units/"
                           "unit-demo-l01/study-map.yaml").read_text())


def test_probe_detour_required_now_off_pending_stage(mini_repo):
    root = two_stage_repo(mini_repo)
    result = approved_v2_call(
        root, capability="detour.create",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-two",
                 "title": "Gap", "classification": "required-now"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-detour-pending")
    print("returncode:", result.returncode)
    print("stdout:", result.stdout[:800])
    print("stderr:", result.stderr[:800])
    stages = {s["id"]: s["status"] for s in _map_of(root)["stages"]}
    print("stages after:", stages, "map status:", _map_of(root)["status"])
    # Whatever happened, the tree must stay valid.
    signatures, errors = collect(root)
    assert not errors, [str(e) for e in errors[:5]]


def test_probe_detour_required_now_off_completed_stage(mini_repo):
    root = two_stage_repo(mini_repo)
    completed = approved_v2_call(
        root, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-two",
                 "status": "active"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-activate-two")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    done = approved_v2_call(
        root, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-two",
                 "status": "complete"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-complete-two")
    assert done.returncode == 0, done.stdout + done.stderr
    result = approved_v2_call(
        root, capability="detour.create",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-two",
                 "title": "Gap", "classification": "required-now"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-detour-complete")
    print("returncode:", result.returncode)
    print("stdout:", result.stdout[:800])
    print("stderr:", result.stderr[:800])
    signatures, errors = collect(root)
    assert not errors, [str(e) for e in errors[:5]]


def test_probe_stage_progress_pause_noncurrent_stage(mini_repo):
    root = two_stage_repo(mini_repo)
    result = approved_v2_call(
        root, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-two",
                 "status": "paused"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-pause-two")
    print("returncode:", result.returncode)
    print("stdout:", result.stdout[:800])
    print("stderr:", result.stderr[:800])
    if result.returncode == 0:
        data = _map_of(root)
        print("stages after:", {s["id"]: s["status"] for s in data["stages"]},
              "current:", data["current_stage"], "status:", data["status"])
    signatures, errors = collect(root)
    assert not errors, [str(e) for e in errors[:5]]


def test_probe_shelving_partial_apply(mini_repo):
    root = two_stage_repo(mini_repo)
    note_a = ("---\nid: note-probe-a\ntype: note\ntitle: Probe A\n"
              "created: 2026-10-24\nsources: [source-demo-book]\n---\n\nfirst\n")
    note_b = ("---\nid: note-probe-b\ntype: note\ntitle: Probe B\n"
              "created: 2026-10-24\nsources: [source-demo-book]\n---\n\nsecond\n")
    items = [
        {"id": "proposal-alpha", "kind": "durable-note", "title": "A",
         "destination": "knowledge/notes/mathematics/note-probe-a.md",
         "rationale": "probe", "content": note_a, "selected": True},
        {"id": "proposal-beta", "kind": "durable-note", "title": "B",
         "destination": "knowledge/notes/mathematics/note-probe-b.md",
         "rationale": "probe", "content": note_b, "selected": True},
    ]
    items_path = root / "work/probe-items.json"
    items_path.parent.mkdir(parents=True, exist_ok=True)
    items_path.write_text(json.dumps({"items": items}), encoding="utf-8")
    from gateway_helpers import approved_v2_envelope, run_v2_capability, file_sha256
    envelope = approved_v2_envelope(
        root, capability="review.prepare",
        payload={"unit_id": "unit-demo-l01",
                 "items_file": str(items_path),
                 "items_file_sha256": file_sha256(items_path)},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-shelve-prepare-2")
    prepared = run_v2_capability(root, envelope)
    print("prepare2 rc:", prepared.returncode)
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr

    half = approved_v2_call(
        root, capability="review.apply",
        payload={"unit_id": "unit-demo-l01",
                 "selected": ["proposal-alpha"]},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01", "proposal-alpha"],
        idempotency_key="c1b-shelve-apply-a")
    print("apply-a rc:", half.returncode)
    data = _map_of(root)
    print("shelving state:", data["shelving"]["state"],
          "items:", [i["id"] for i in data["shelving"].get("items", [])])
    assert (root / "knowledge/notes/mathematics/note-probe-a.md").exists()
    assert not (root / "knowledge/notes/mathematics/note-probe-b.md").exists()
    signatures, errors = collect(root)
    assert not errors, [str(e) for e in errors[:5]]

    rest = approved_v2_call(
        root, capability="review.apply",
        payload={"unit_id": "unit-demo-l01",
                 "selected": ["proposal-beta"]},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01", "proposal-beta"],
        idempotency_key="c1b-shelve-apply-b")
    print("apply-b rc:", rest.returncode)
    print("beta applied at state=applied:", rest.returncode == 0)
    signatures, errors = collect(root)
    assert not errors, [str(e) for e in errors[:5]]


def test_probe_selection_remove_guard(mini_repo):
    root = two_stage_repo(mini_repo)
    removed = approved_v2_call(
        root, capability="unit.source-selection.set",
        payload={"unit_id": "unit-demo-l01", "source_id": "source-demo-book",
                 "locator": "§1 Erwartungswert", "action": "remove"},
        artifact_ids=["unit-demo-l01"],
        idempotency_key="c1b-selection-remove")
    print("remove rc:", removed.returncode)
    print(removed.stdout[:500], removed.stderr[:500])
    unit = yaml.safe_load((root / "curriculum/modules/module-demo/units/"
                           "unit-demo-l01/unit.yaml").read_text())
    print("selections after:", unit.get("source_selections"))
