"""The module-level scope obligation (OPERATOR.md rule 6, module level).

A studied academic module with an owning record and no units still owes its
initial units. No unit-level obligation can fire for it, because there is no
unit to owe anything — the module would otherwise be enrolled and invisible.

Derived, never authored: one truth table in the semantic contract, consumed
by the read surfaces, so the count, the badge and the queue cannot disagree.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from repo_builders import add_curriculum, run_los

from learning_os.derive.semantics.predicates import (
    module_record_is_owned,
    needs_scope,
)
from learning_os.derive.semantics.scan import collect_observations

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# The truth table
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("kind", "status", "unit_count", "owned", "owed", "why"),
    [
        ("academic", "enrolled", 0, True, True,
         "an enrolled academic module with no units owes its initial units"),
        ("academic", "active", 0, True, True,
         "so does an active one"),
        ("academic", "enrolled", 1, True, False,
         "one unit discharges it: planning has begun"),
        ("academic", "enrolled", 12, True, False,
         "a planned module is not owed anything"),
        ("academic", "paused", 0, True, False,
         "a paused academic module is not owed new planning — the "
         "administrative projection folds it into 'enrolled', the authored "
         "status does not"),
        ("academic", "dropped", 0, True, False,
         "a dropped module keeps its records as history"),
        ("academic", "archived", 0, True, False,
         "an archived module is never asked for new plans"),
        ("academic", "planned", 0, True, False,
         "a planned module is not enrolled yet"),
        ("skill", "active", 0, True, False,
         "a skill module has no registrar and no lecture plan"),
        ("project", "active", 0, True, False,
         "a project module has no registrar"),
        ("foundation", "active", 0, True, False,
         "a foundation module has no registrar"),
        ("academic", "enrolled", 0, False, False,
         "a module known only through the frozen compatibility mirror owns "
         "nothing, and a record written before the unit model cannot owe "
         "initial units"),
    ],
)
def test_the_truth_table(kind, status, unit_count, owned, owed, why):
    assert needs_scope(
        module_kind=kind,
        module_status=status,
        unit_count=unit_count,
        owned=owned,
    ) is owed, why


def test_a_paused_module_is_not_caught_by_the_administrative_projection():
    """The projection maps `paused` academic onto administrative `enrolled`.

    Using the administrative state here would flag every paused academic
    module in the tree. The predicate reads the authored status.
    """
    from learning_os.derive.projection.projection.lifecycle import module_lifecycle

    projected = module_lifecycle(
        {"kind": "academic", "status": "paused"}, [])
    assert projected["administrative_status"] == "enrolled"
    assert not needs_scope(
        module_kind="academic",
        module_status="paused",
        unit_count=0,
        owned=True,
    )


def test_the_compatibility_mirror_owns_nothing():
    assert module_record_is_owned(
        "curriculum/modules/module-hu-icop/module.yaml") is True
    assert module_record_is_owned("records/modules.yaml") is False
    assert module_record_is_owned(None) is False
    assert module_record_is_owned("") is False


# --------------------------------------------------------------------------
# The obligation on a real repository
# --------------------------------------------------------------------------

@pytest.mark.full_repo
def test_no_module_is_owed_on_the_checked_in_tree():
    """BS and ICOP each carry their first unit, so nothing is owed.

    Both were enrolled with no units when this obligation landed. Their first
    units (unit-bs-os-structure, unit-icop-l01-linear-programming) reached
    main with the live takeover records on 2026-10-25, and one unit discharges
    the obligation (the truth table above). The owed path, through the brief
    and the scan, is pinned on a synthetic repository below.
    """
    obs = collect_observations(ROOT)
    assert obs.scope_obligations == ()


# --------------------------------------------------------------------------
# The obligation on a synthetic repository
# --------------------------------------------------------------------------

def _write_module(root: Path, module_id: str, *, status: str, kind: str,
                  units: list[str]) -> None:
    module_dir = root / "curriculum/modules" / module_id
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(yaml.safe_dump({
        "id": module_id, "type": "module", "kind": kind,
        "area_id": "program-bachelors", "title": f"Module {module_id}",
        "status": status, "unit_order": list(units),
        "source_map": "source-map.yaml",
    }), encoding="utf-8")
    (module_dir / "source-map.yaml").write_text(yaml.safe_dump({
        "type": "module-source-map", "module_id": module_id, "sources": [],
    }), encoding="utf-8")
    for order, unit_id in enumerate(units, start=1):
        unit_dir = module_dir / "units" / unit_id
        unit_dir.mkdir(parents=True, exist_ok=True)
        (unit_dir / "unit.yaml").write_text(yaml.safe_dump({
            "id": unit_id, "type": "unit", "module_id": module_id,
            "kind": "lecture", "title": f"Unit {unit_id}", "order": order,
            "scope": "The lecture as taught.", "status": "not-started",
        }), encoding="utf-8")


def test_an_owned_module_with_units_is_not_owed(tmp_path):
    root = tmp_path / "repository"
    _write_module(root, "module-with-units", status="enrolled",
                  kind="academic", units=["unit-demo-l01"])
    obs = collect_observations(root)
    assert "module-with-units" not in obs.scope_obligations


def test_an_owned_module_without_units_is_owed(tmp_path):
    root = tmp_path / "repository"
    _write_module(root, "module-empty", status="enrolled",
                  kind="academic", units=[])
    obs = collect_observations(root)
    assert obs.scope_obligations == ("module-empty",)


def _write_owed_module(root: Path) -> str:
    """An enrolled academic module with no units, valid beside module-demo."""
    add_curriculum(root)
    module_id = "module-demo-empty"
    record = yaml.safe_load(
        (root / "curriculum/modules/module-demo/module.yaml").read_text(encoding="utf-8"))
    record.update({"id": module_id, "title": "Empty Demo Module", "unit_order": []})
    module_dir = root / "curriculum/modules" / module_id
    module_dir.mkdir(parents=True)
    (module_dir / "module.yaml").write_text(yaml.safe_dump(record), encoding="utf-8")
    (module_dir / "source-map.yaml").write_text(yaml.safe_dump({
        "type": "module-source-map", "module_id": module_id, "sources": [],
    }), encoding="utf-8")
    return module_id


def test_the_brief_reports_the_owed_modules(mini_repo):
    module_id = _write_owed_module(mini_repo)
    result = run_los(mini_repo, "bootstrap", "--brief", "--json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["owed_module_scopes"] == [module_id]


def test_the_scan_proposes_one_goal_per_owed_module(mini_repo):
    module_id = _write_owed_module(mini_repo)
    result = run_los(mini_repo, "intelligence-scan", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    rows = payload if isinstance(payload, list) else payload.get("goals", [])
    owed = [row for row in rows if row.get("detector") == "module-scope-obligation"]
    assert {row["goal_id"] for row in owed} == {f"module-scope-obligation:{module_id}"}
    for row in owed:
        # The queue item says planning has not started. It must never
        # claim the module is covered.
        assert "planning not started" in row["title"]
        assert "covered" not in row["title"]


def test_emitted_scope_goal_ids_round_trip_through_the_canonical_parser():
    from learning_os.derive.semantics.scan import ScanInput, scan_observations
    from learning_os.domain.ids import parse

    goals = scan_observations(ScanInput(scope_obligations=("module-demo-empty",)))
    assert len(goals) == 1
    assert parse("goal", goals[0].goal_id) == "module-scope-obligation:module-demo-empty"
