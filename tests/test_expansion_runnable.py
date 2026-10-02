"""Every emitted expansion runs as printed with the documented invocation (#85).

Expansions are bare argv after the program (no ``los `` prefix); reads
that bind a snapshot carry ``--expected-snapshot``. ALL-CAPS words are
placeholders the caller fills from the same response — the test fills
each from the parent payload (or the seeded repo) and asserts exit 0.
"""

from __future__ import annotations

import hashlib
import json
import shlex
from pathlib import Path

import yaml
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.abilities import ability_fingerprint
from learning_os.loader import load_repo

ANALYSIS_BODY = """# Density intuition

The density chapter explains probability mass spreading over intervals.
A worked example integrates the uniform density step by step.
"""


def _seed_material(root: Path, name: str, data: bytes) -> str:
    target = root.parent / "materials" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _plant_note(root: Path, note_id: str, body: str, binding: dict) -> None:
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": "Planted analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": binding}
    path = root / "knowledge/notes/mathematics" / f"{note_id}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body.encode("utf-8"))


def _rich_repo(root: Path) -> dict:
    """Seed every family one expansion can point at; return fill values."""
    add_curriculum(root)
    _add_material_overview(root)
    module_path = root / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    write_yaml(root / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2,
        "scope": "The lecture as taught.", "status": "active",
        "scope_sources": [], "artifacts": {}, "workspace_ids": [],
    })
    digest = _seed_material(root, "deck.pdf", b"live bytes")
    anchors = [{"topic": f"Topic {number}", "purpose": "integration",
                "locator": f"deck.pdf, p. {number + 1}",
                "note": f"Anchor note {number}."} for number in range(9)]
    _plant_note(root, "note-context-anchored", ANALYSIS_BODY, {
        "resolution": "resolved", "material": "deck.pdf",
        "source_id": "source-demo-book",
        "recorded_source_digest": digest, "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(
            ANALYSIS_BODY.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(ANALYSIS_BODY.encode("utf-8")),
        "anchors": anchors,
    })
    ability = {
        "title": "Derive simple least squares", "claim": "Derive slope.",
        "conditions": ["intercept included"],
        "evidence_spec": ["correct derivation"],
        "concept_ids": ["concept-expected-value"], "module_ids": [],
        "review": {"state": "reviewed", "reviewed_by": "test",
                   "reviewed_on": "2026-09-23"},
    }
    (root / "knowledge/abilities.yaml").write_text(yaml.safe_dump({
        "abilities": [
            {**ability, "id": "ability-sad-ols",
             "preparation_routes": []},
            {**ability, "id": "ability-aml-ols",
             "preparation_routes": []},
            {**ability, "id": "ability-aml-extension",
             "preparation_routes": []},
        ],
        "bridges": [],
    }, sort_keys=False), encoding="utf-8")
    repo = load_repo(root)
    ledger = root / "work/active/workspace-demo/ability-observations.jsonl"
    with ledger.open("a", encoding="utf-8") as handle:
        for number in (1, 2):
            row = {
                "id": f"ability-observation-{number}",
                "ability_id": "ability-sad-ols",
                "ability_sha256": ability_fingerprint(
                    repo.abilities["ability-sad-ols"]),
                "claim": "Derived from the stated problem.",
                "work_ref": f"conversation://test/work-{number}",
                "confirmation_ref":
                    f"conversation://test/confirmation-{number}",
                "activity": "worked derivation", "result": "correct",
                "timestamp": f"2026-09-23T10:{number:02d}:00Z",
                "conditions": ["intercept included"],
                "evidence_tags": ["correct derivation"],
                "assistance": "none", "confirmed_by": "learner",
            }
            handle.write(json.dumps(row) + "\n")
    (root / "work/inbox/drop.txt").write_text("a drop\n", encoding="utf-8")
    brief = json.loads(run_los(
        root, "plan-edit-context", "unit-demo-l01", "--brief").stdout)
    return {
        "QUERY": "density",
        "ID": "unit-demo-l01",
        "UNIT_ID": "unit-demo-l01",
        "ROUTE_ID": brief["inventory"]["route_ids"][0],
        "NOTE_ID": "note-demo",
        "STAGE_ID": "stage-demo",
        "ABILITY_ID": "ability-sad-ols",
        "NEXT_OFFSET": "1",
    }


def _filled(command: str, fills: dict, snapshot: str) -> list[str]:
    """Bare argv with every placeholder filled; asserts none remain."""
    assert not command.startswith("los "), command
    argv = [fills.get(part, part) for part in shlex.split(command)]
    argv = [snapshot if part == "SNAPSHOT" else part for part in argv]
    leftovers = [part for part in argv
                 if part in fills or part == "SNAPSHOT"
                 or (part.isupper() and "_" in part)]
    assert not leftovers, (command, argv)
    return argv


def _run(root: Path, command: str, fills: dict, snapshot: str):
    proc = run_los(root, *_filled(command, fills, snapshot))
    assert proc.returncode == 0, f"{command}: {proc.stderr}"
    return proc


def test_plan_brief_expansions_run_and_carry_the_snapshot(mini_repo: Path):
    fills = _rich_repo(mini_repo)
    payload = json.loads(run_los(
        mini_repo, "plan-edit-context", "unit-demo-l01", "--brief").stdout)
    snapshot = payload["snapshot_id"]
    expand = payload["expand"]
    commands = [expand["full"], expand["full_audit"],
                expand["adjacent_unit_source_reuse"],
                *expand["route_batches"], *expand["stages"].values(),
                expand["analysis_search"],
                payload["analysis_refs"]["related_expand"]]
    assert commands
    for command in commands:
        assert f"--expected-snapshot {snapshot}" in command, command
        _run(mini_repo, command, fills, snapshot)
    for row in payload["preflight"]:
        assert not row["check"].startswith("los "), row


def test_search_page_expansion_runs(mini_repo: Path):
    _rich_repo(mini_repo)
    payload = json.loads(run_los(
        mini_repo, "search", "", "--page", "--limit", "1").stdout)
    assert payload["total"] > 1
    nxt = payload["expand"]["next"]
    assert f"--expected-snapshot {payload['snapshot_id']}" in nxt
    _run(mini_repo, nxt, {}, payload["snapshot_id"])


def test_ability_expansions_run(mini_repo: Path):
    fills = _rich_repo(mini_repo)
    horizon = json.loads(run_los(
        mini_repo, "ability-context", "--limit", "1").stdout)
    assert horizon["total"] == 3
    nxt = horizon["expansions"]["next"]
    assert f"--expected-snapshot {horizon['snapshot_id']}" in nxt
    _run(mini_repo, nxt, fills, horizon["snapshot_id"])
    _run(mini_repo, horizon["expand"], fills, horizon["snapshot_id"])
    brief = json.loads(run_los(
        mini_repo, "ability-context", "ability-sad-ols", "--brief").stdout)
    for key, command in brief["expand"].items():
        if key == "evidence":
            assert "--expected-snapshot" in command, command
        _run(mini_repo, command, fills, brief["snapshot_id"])
    for summary in brief["encounters"]:
        if "expand" in summary:
            _run(mini_repo, summary["expand"], fills, brief["snapshot_id"])
    section = json.loads(run_los(
        mini_repo, "ability-context", "ability-sad-ols",
        "--section", "evidence", "--limit", "1").stdout)
    assert section["total"] == 2
    _run(mini_repo, section["expansions"]["next"], fills,
         section["snapshot_id"])


def test_material_context_anchors_expansion_runs(mini_repo: Path):
    fills = _rich_repo(mini_repo)
    payload = json.loads(run_los(
        mini_repo, "material-context", "density", "--limit", "1").stdout)
    command = payload["expand"]["anchors"]
    assert f"--expected-snapshot {payload['snapshot_id']}" in command
    proc = _run(mini_repo, command, fills, payload["snapshot_id"])
    item = json.loads(proc.stdout)["items"][0]
    assert item["anchor_returned"] == item["anchor_total"] == 9


def test_unit_list_detail_runs(mini_repo: Path):
    fills = _rich_repo(mini_repo)
    page = json.loads(run_los(
        mini_repo, "unit-list", "--compact", "--limit", "1").stdout)
    fills = {**fills, "UNIT_ID": page["items"][0]["id"]}
    _run(mini_repo, page["detail"], fills, page["snapshot_id"])


def test_bootstrap_expansions_run(mini_repo: Path):
    fills = _rich_repo(mini_repo)
    payload = json.loads(run_los(mini_repo, "bootstrap", "--brief").stdout)
    snapshot = payload["snapshot_id"]
    expand = payload["expand"]
    assert expand["plan_brief"], "the owed unit must offer a prep command"
    assert f"--expected-snapshot {snapshot}" in expand["full_compact"]
    assert f"--expected-snapshot {snapshot}" in expand["ability_context"]
    commands = [value for key, value in expand.items()
                if key != "plan_brief"] + expand["plan_brief"]
    per_key = {"capability_detail": {**fills, "NAME": "operator.bootstrap"},
               "inbox_read": {**fills, "NAME": "drop.txt"}}
    for key, value in expand.items():
        if key == "plan_brief":
            for command in value:
                _run(mini_repo, command, fills, snapshot)
        else:
            _run(mini_repo, value, per_key.get(key, fills), snapshot)
    assert commands


def test_material_span_expansions_run(mini_repo: Path):
    fills = _rich_repo(mini_repo)
    payload = json.loads(run_los(
        mini_repo, "material-span", fills["UNIT_ID"], fills["ROUTE_ID"]).stdout)
    snapshot = payload["snapshot_id"]
    for command in (payload["expansion"],
                    payload["analysis_refs"]["expand"]):
        assert f"--expected-snapshot {snapshot}" in command, command
        _run(mini_repo, command, fills, snapshot)


def test_los_help_names_the_venv_python():
    los = Path(__file__).resolve().parent.parent / "tools" / "los.py"
    bad = [line for line in los.read_text(encoding="utf-8").splitlines()
           if line.lstrip().startswith("python tools/")]
    assert bad == []
