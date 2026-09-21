"""Brief preparation form: what the next command needs, nothing else.

`plan-edit-context --brief` projects identities, guards, id inventories,
the audit's missing-evidence lists, reusable analysis references, required
follow-up inputs, applicable preflight checks, and explicit expandable
commands. Full route bodies, the study map, and analysis prose stay behind
the expand references — every listed expansion must run as printed.
"""

from __future__ import annotations

import hashlib
import json
import shlex
from pathlib import Path

import yaml
from repo_builders import add_curriculum, run_los, write_yaml

ANALYSIS_BODY = """# Density intuition

The density chapter explains probability mass spreading over intervals.
A worked example integrates the uniform density step by step.
"""


def _plant_note(root: Path, note_id: str, body: str, binding: dict):
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": "Planted analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": binding}
    path = root / "knowledge/notes/mathematics" / f"{note_id}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body.encode("utf-8"))


def _seed_material(root: Path, name: str, data: bytes) -> str:
    target = root.parent / "materials" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _seed_unit(root: Path):
    add_curriculum(root)
    digest = _seed_material(root, "deck.pdf", b"%PDF brief\n")
    _plant_note(root, "note-brief-density", ANALYSIS_BODY, {
        "resolution": "resolved",
        "material": "deck.pdf",
        "source_id": "source-demo-book",
        "recorded_source_digest": digest,
        "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(ANALYSIS_BODY.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(ANALYSIS_BODY.encode("utf-8")),
    })
    unit_dir = root / "curriculum/modules/module-demo/units/unit-demo-l01"
    write_yaml(unit_dir / "material-synthesis.yaml", {
        "schema_version": 1, "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis", "unit_id": "unit-demo-l01",
        "status": "approved",
        "route_assessments": [{
            "route_id": "route-demo-density",
            "source_id": "source-demo-book",
            "locator": "deck.pdf, pp. 1-3",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "Derives density intuition from first principles.",
            "best_for": "A worked example of uniform density integration.",
        }],
    })
    map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "id": "route-demo-density", "unit_id": "unit-demo-l01",
        "title": "Density", "locator": "deck.pdf, pp. 1-3",
        "depth": "core", "scope": "current",
    }]
    write_yaml(map_path, source_map)


def _brief(root: Path, *args: str) -> dict:
    proc = run_los(root, "plan-edit-context", "unit-demo-l01", "--brief", *args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def test_brief_carries_preparation_without_bodies(mini_repo):
    _seed_unit(mini_repo)
    payload = _brief(mini_repo)
    assert payload["contract"] == "plan-edit-context-brief"
    assert payload["unit_id"] == "unit-demo-l01"
    assert payload["module_id"] == "module-demo"
    for key in ("study_map", "routes", "source_selections"):
        assert key not in payload, key
    for key in ("artifact_revisions", "inventory", "unit_audit",
                "analysis_refs", "required_inputs", "preflight", "expand"):
        assert key in payload, key
    assert payload["inventory"]["route_ids"] == ["route-demo-density"]
    assert payload["inventory"]["stage_ids"] == ["stage-demo"]
    # Exact missing evidence: the route is current-scope but placed nowhere.
    assert payload["unit_audit"]["current_or_prerequisite_unplaced"] == [
        "route-demo-density"]
    refs = payload["analysis_refs"]["analysis_notes"]
    assert [ref["note_id"] for ref in refs] == ["note-brief-density"]
    assert refs[0]["freshness"] == "current"
    assert refs[0]["review"] == "unreviewed"
    assert payload["analysis_refs"]["approved_assessment_routes"] == [
        "route-demo-density"]
    assert ANALYSIS_BODY.splitlines()[2] not in json.dumps(payload)
    assert sorted(payload["artifact_revisions"]) == [
        "module-demo", "study-map-demo-l01", "unit-demo-l01"]
    assert payload["required_inputs"]["route_patch"]["changes"]["fields"]
    assert {row["operation"] for row in payload["preflight"]} == {
        "route-patch", "unit-plan-revise", "unit-map-import",
        "module-plan-import", "verify"}


def test_brief_expand_commands_run_as_printed(mini_repo):
    _seed_unit(mini_repo)
    payload = _brief(mini_repo)
    expand = payload["expand"]
    commands = [expand["full"], expand["full_audit"],
                *expand["route_batches"], *expand["stages"].values()]
    assert expand["route_batches"] == [
        "los plan-edit-context unit-demo-l01 --route-ids route-demo-density"]
    for command in commands:
        argv = shlex.split(command)
        assert argv.pop(0) == "los"
        proc = run_los(mini_repo, *argv)
        assert proc.returncode == 0, f"{command}: {proc.stderr}"
    search = expand["analysis_search"].replace("QUERY", "density")
    argv = shlex.split(search)
    assert argv.pop(0) == "los"
    proc = run_los(mini_repo, *argv)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["items"]


def test_brief_refuses_selectors_and_audit(mini_repo):
    _seed_unit(mini_repo)
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                   "--brief", "--route-id", "route-demo-density")
    assert proc.returncode == 2
    assert "expand one route" in proc.stderr
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                   "--brief", "--audit")
    assert proc.returncode == 2
    assert "already carries the unit audit" in proc.stderr
