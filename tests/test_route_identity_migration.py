"""The v13 route migration is deterministic, atomic, and never guesses."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from migrations.route_identity_v13 import plan_migration, plan_sha256
from repo_builders import _add_material_overview, add_curriculum, write_yaml

from learning_os.contracts.gateway import intent_sha256
from learning_os.fingerprint import canonical_fingerprint
from learning_os.routes import deterministic_route_id

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = ROOT / "tools/migrations/route_identity_v13.py"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _fixture(tmp_path: Path, routes: list, *, locator: str = "p. 35") -> Path:
    root = tmp_path / "repository"
    source_map = root / "curriculum/modules/module-demo/source-map.yaml"
    _write(source_map, {
        "type": "module-source-map",
        "module_id": "module-demo",
        "sources": [{
            "source_id": "source-demo",
            "role": "spine",
            "why": "Synthetic route fixture.",
            "priority": 0,
            "unit_routes": routes,
        }],
    })
    # A comment proves apply inserts fields rather than dumping/reformatting YAML.
    source_map.write_text(
        "# preserved source-map comment\n" + source_map.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write(
        root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
        {
            "id": "unit-demo-l01",
            "type": "unit",
            "module_id": "module-demo",
            "source_selections": [{
                "source_id": "source-demo",
                "locator": locator,
                "purpose": "Synthetic selection.",
            }],
        },
    )
    _write(
        root / "system/contracts/data-contract.yaml",
        {"contract_version": 13},
    )
    return root


def _route(title: str = "Exact formula route", locator: str = "p. 35") -> dict:
    return {
        "unit_id": "unit-demo-l01",
        "title": title,
        "format": "book",
        "angle": "Shows the exact formula.",
        "covers": ["knowledge-demo-formula"],
        "depth": "derivation",
        "scope": "current",
        "locator": locator,
    }


def _review(root: Path, decisions: list[dict]) -> dict:
    baseline = plan_migration(root)
    return {
        "schema_version": 1,
        "basis_plan_sha256": plan_sha256(baseline),
        "basis_snapshot_sha256": f"sha256:{canonical_fingerprint(root)}",
        "decisions": {
            f"R{index:03d}": decision
            for index, decision in enumerate(decisions, start=1)
        },
    }


def _decision(
    root: Path,
    *,
    action: str,
    route_ids: list[str],
    selection_index: int = 0,
    rationale: str = "Reviewed against the exact rich-route locator.",
) -> dict:
    relative = "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load((root / relative).read_text(encoding="utf-8"))
    selection = unit["source_selections"][selection_index]
    return {
        "unit_path": relative,
        "selection_index": selection_index,
        "expected_source_id": selection["source_id"],
        "expected_locator": selection["locator"],
        "action": action,
        "route_ids": route_ids,
        "rationale": rationale,
    }


def test_route_migration_direct_apply_is_disabled(tmp_path):
    route = _route()
    root = _fixture(tmp_path, [route])
    expected = deterministic_route_id("module-demo", "source-demo", route)

    planned = plan_migration(root)

    assert planned.ready
    assert len(planned.changes) == 2
    assert {row.route_id for row in planned.routes} == {expected}

    applied = subprocess.run(
        [sys.executable, str(MIGRATION), "--root", str(root), "--apply"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert applied.returncode == 2
    assert "route.identity.migrate GatewayEnvelopeV2" in applied.stdout
    source_text = (
        root / "curriculum/modules/module-demo/source-map.yaml"
    ).read_text(encoding="utf-8")
    unit_text = (
        root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    ).read_text(encoding="utf-8")
    assert source_text.startswith("# preserved source-map comment\n")
    assert f"id: {expected}" not in source_text
    assert f"route_id: {expected}" not in unit_text


def test_route_migration_gateway_is_receipted_and_idempotent(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"][0]["locator"] = "lecture-01.pdf"
    write_yaml(unit_path, unit)

    plan = plan_migration(mini_repo)
    assert plan.ready
    assert len(plan.changes) == 2
    envelope = {
        "schema_version": 2,
        "request_id": "request-route-v13",
        "idempotency_key": "route-v13-001",
        "capability": "route.identity.migrate",
        "channel": "operator",
        "expected_snapshot": f"sha256:{canonical_fingerprint(mini_repo)}",
        "expected_revisions": {"module-demo": 0, "unit-demo-l01": 0},
        "approval": {
            "kind": "operator-approval",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {"plan_sha256": plan_sha256(plan)},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    request = tmp_path / "route-v13.json"
    request.write_text(json.dumps(envelope), encoding="utf-8")
    applied = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(mini_repo),
            "capability", "route.identity.migrate",
            "--payload-file", str(request),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert applied.returncode == 0, applied.stderr or applied.stdout
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    assert response["transaction_id"]
    receipt = yaml.safe_load((mini_repo / response["receipt_path"]).read_text())
    assert receipt["schema_version"] == 2
    assert receipt["capability"] == "route.identity.migrate"
    assert {row["path"] for row in receipt["writes"]} == {
        "curriculum/modules/module-demo/source-map.yaml",
        "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
    }
    assert plan_migration(mini_repo).changes == ()

    replayed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(mini_repo),
            "capability", "route.identity.migrate",
            "--payload-file", str(request),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert replayed.returncode == 0, replayed.stderr or replayed.stdout
    assert json.loads(replayed.stdout)["replayed"] is True


def test_ambiguous_selection_blocks_the_entire_apply(tmp_path):
    root = _fixture(tmp_path, [
        _route("First exact route"),
        _route("Second exact route"),
    ])
    source_path = root / "curriculum/modules/module-demo/source-map.yaml"
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    before = {source_path: source_path.read_text(), unit_path: unit_path.read_text()}

    plan = plan_migration(root)

    assert not plan.ready
    assert "selection-ambiguous" in {problem.code for problem in plan.problems}
    refused = subprocess.run(
        [sys.executable, str(MIGRATION), "--root", str(root), "--apply"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert refused.returncode == 2
    assert "refusing direct --apply" in refused.stdout
    assert source_path.read_text() == before[source_path]
    assert unit_path.read_text() == before[unit_path]


def test_legacy_string_route_stays_readable_but_is_never_guessed(tmp_path):
    root = _fixture(tmp_path, ["unit-demo-l01"])

    plan = plan_migration(root)

    assert plan.routes == ()
    assert not plan.ready
    assert {problem.code for problem in plan.problems} == {"selection-unmatched"}
    source_change = [
        change for change in plan.changes if change.path.name == "source-map.yaml"
    ]
    assert source_change == []


def test_route_migration_never_traverses_symlinked_module(tmp_path):
    root = _fixture(tmp_path, [_route()])
    sealed = tmp_path / "sealed-module"
    _write(sealed / "source-map.yaml", {
        "type": "module-source-map",
        "module_id": "module-sealed",
        "sources": [{
            "source_id": "source-sealed",
            "role": "spine",
            "why": "Must never be read through the symlink.",
            "priority": 0,
            "unit_routes": [_route()],
        }],
    })
    (root / "curriculum/modules/module-sealed").symlink_to(
        sealed,
        target_is_directory=True,
    )

    plan = plan_migration(root)

    assert not plan.ready
    assert "unsafe-symlink-path" in {problem.code for problem in plan.problems}
    assert all(route.module_id != "module-sealed" for route in plan.routes)


def test_review_can_revise_one_selection_guard_without_reformatting(tmp_path):
    route = _route(locator="p. 35")
    root = _fixture(tmp_path, [route], locator="old pp. 34-36")
    route_id = deterministic_route_id("module-demo", "source-demo", route)
    unit_path = (
        root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    )
    before = unit_path.read_text(encoding="utf-8")
    review = _review(root, [_decision(
        root,
        action="revise-selection-guard",
        route_ids=[route_id],
    )])

    plan = plan_migration(root, review=review)

    assert plan.ready
    unit_change = next(change for change in plan.changes if change.path == unit_path)
    revised = yaml.safe_load(unit_change.after)
    assert revised["source_selections"] == [{
        "source_id": "source-demo",
        "route_id": route_id,
        "locator": "p. 35",
        "purpose": "Synthetic selection.",
    }]
    assert "purpose: Synthetic selection." in unit_change.after
    assert before.split("purpose:", 1)[1] == unit_change.after.split("purpose:", 1)[1]

    review_file = tmp_path / "route-review.yaml"
    review_file.write_text(
        yaml.safe_dump(review, sort_keys=False),
        encoding="utf-8",
    )
    standalone = subprocess.run(
        [
            sys.executable,
            str(MIGRATION),
            "--root", str(root),
            "--review-file", str(review_file),
            "--json",
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert standalone.returncode == 1
    assert json.loads(standalone.stdout)["ready"] is True
    assert unit_path.read_text(encoding="utf-8") == before


def test_review_split_preserves_fields_and_reviewed_route_order(tmp_path):
    first = _route("First exact route", "p. 35")
    second = _route("Second exact route", "p. 36")
    root = _fixture(tmp_path, [first, second], locator="pp. 35-36")
    unit_path = (
        root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    )
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"][0]["stage_ids"] = ["stage-demo-read"]
    write_yaml(unit_path, unit)
    first_id = deterministic_route_id("module-demo", "source-demo", first)
    second_id = deterministic_route_id("module-demo", "source-demo", second)
    review = _review(root, [_decision(
        root,
        action="split-selection",
        route_ids=[second_id, first_id],
    )])

    plan = plan_migration(root, review=review)

    assert plan.ready
    unit_change = next(change for change in plan.changes if change.path == unit_path)
    selections = yaml.safe_load(unit_change.after)["source_selections"]
    assert [selection["route_id"] for selection in selections] == [
        second_id, first_id,
    ]
    assert [selection["locator"] for selection in selections] == ["p. 36", "p. 35"]
    assert all(selection["purpose"] == "Synthetic selection." for selection in selections)
    assert all(selection["stage_ids"] == ["stage-demo-read"] for selection in selections)


def test_review_add_route_is_an_explicit_blocker(tmp_path):
    root = _fixture(tmp_path, [_route()], locator="not yet represented")
    review = _review(root, [_decision(
        root,
        action="add-route",
        route_ids=[],
        rationale="A new rich route must be authored and reviewed first.",
    )])

    plan = plan_migration(root, review=review)

    assert not plan.ready
    assert {problem.code for problem in plan.problems} == {
        "review-action-blocked",
    }
    unit_path = (
        root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    )
    assert all(change.path != unit_path for change in plan.changes)


def test_review_basis_drift_blocks_all_review_edits(tmp_path):
    root = _fixture(tmp_path, [_route()], locator="old locator")
    route_id = plan_migration(root).routes[0].route_id
    review = _review(root, [_decision(
        root,
        action="revise-selection-guard",
        route_ids=[route_id],
    )])
    review["basis_snapshot_sha256"] = "sha256:" + "0" * 64

    plan = plan_migration(root, review=review)

    assert not plan.ready
    assert "review-basis-snapshot-drift" in {
        problem.code for problem in plan.problems
    }
    unit_path = (
        root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    )
    assert all(change.path != unit_path for change in plan.changes)


def test_review_requires_keyed_ids_and_unique_selection_targets(tmp_path):
    root = _fixture(tmp_path, [_route()], locator="old locator")
    route_id = plan_migration(root).routes[0].route_id
    decision = _decision(
        root,
        action="revise-selection-guard",
        route_ids=[route_id],
    )
    review = _review(root, [decision])
    review["decisions"] = [decision]

    malformed = plan_migration(root, review=review)

    assert "review-malformed" in {
        problem.code for problem in malformed.problems
    }

    review = _review(root, [decision])
    review["decisions"]["R002"] = dict(decision)

    duplicate = plan_migration(root, review=review)

    assert "review-duplicate-decision" in {
        problem.code for problem in duplicate.problems
    }


def test_standalone_review_rejects_duplicate_yaml_ids(tmp_path):
    root = _fixture(tmp_path, [_route()], locator="old locator")
    baseline = plan_migration(root)
    snapshot = f"sha256:{canonical_fingerprint(root)}"
    review_file = tmp_path / "duplicate-review.yaml"
    review_file.write_text(
        "\n".join([
            "schema_version: 1",
            f'basis_plan_sha256: "{plan_sha256(baseline)}"',
            f'basis_snapshot_sha256: "{snapshot}"',
            "decisions:",
            "  R001: {}",
            "  R001: {}",
            "",
        ]),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(MIGRATION),
            "--root", str(root),
            "--review-file", str(review_file),
            "--json",
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    assert "found duplicate key 'R001'" in result.stdout


def test_gateway_approval_binds_inline_review_and_reviewed_plan(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"][0]["locator"] = "reviewed legacy locator"
    write_yaml(unit_path, unit)
    route = next(
        row for row in plan_migration(mini_repo).routes
        if row.unit_id == "unit-demo-l01"
        and row.source_id == unit["source_selections"][0]["source_id"]
    )
    review = _review(mini_repo, [_decision(
        mini_repo,
        action="revise-selection-guard",
        route_ids=[route.route_id],
    )])
    reviewed_plan = plan_migration(mini_repo, review=review)
    assert reviewed_plan.ready
    envelope = {
        "schema_version": 2,
        "request_id": "request-route-v13-review",
        "idempotency_key": "route-v13-review-001",
        "capability": "route.identity.migrate",
        "channel": "operator",
        "expected_snapshot": f"sha256:{canonical_fingerprint(mini_repo)}",
        "expected_revisions": {"module-demo": 0, "unit-demo-l01": 0},
        "approval": {
            "kind": "operator-approval",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {
            "plan_sha256": plan_sha256(reviewed_plan),
            "review": review,
        },
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    request = tmp_path / "route-v13-review.json"
    request.write_text(json.dumps(envelope), encoding="utf-8")

    applied = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(mini_repo),
            "capability", "route.identity.migrate",
            "--payload-file", str(request),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert applied.returncode == 0, applied.stderr or applied.stdout
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    selection = yaml.safe_load(unit_path.read_text(encoding="utf-8"))[
        "source_selections"
    ][0]
    assert selection["route_id"] == route.route_id
    assert selection["locator"] == route.locator
