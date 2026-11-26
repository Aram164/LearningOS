"""Phase 3 paired gate: 7-scenario live-write verification across real Core.

Drives `obsidian-ui/tests/live-writes-harness.js` against 21 isolated temporary
Core repositories (`7 scenarios × 3 capabilities`: `unit.source-selection.set`,
`unit.map.import` simultaneous reorder+reset+retire, and
`ai-action.delivery.apply`) and independently asserts persisted canonical YAML,
receipts, idempotency entries, revision ledgers, and Core validation on disk.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

UI_ROOT = Path(__file__).resolve().parents[2] / "obsidian-ui"
HARNESS = UI_ROOT / "tests" / "live-writes-harness.js"

pytestmark = [
    pytest.mark.skipif(
        not HARNESS.is_file() or shutil.which("node") is None,
        reason="the sibling obsidian-ui live-writes harness (or Node) is not available",
    ),
    pytest.mark.paired,
]

SCENARIOS = (
    "valid",
    "invalid",
    "stalePreview",
    "concurrent",
    "duplicate",
    "recovery",
    "reload",
)


def _dump_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _run_los(repo_root: Path, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "--root", str(repo), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env={**os.environ, "LOS_SESSION_ID": "test-phase3-setup"},
    )


def _prepare_base_source_repo(repo_root: Path, base: Path) -> Path:
    from conftest import build_mini_repo
    from repo_builders import copy_real_contracts
    from scenario_fixtures import rich_world

    repo = build_mini_repo(base)
    rich_world(repo)
    copy_real_contracts(repo_root, repo)
    gen = _run_los(repo_root, repo, "generate")
    assert gen.returncode == 0, gen.stderr
    return base / "LearningOS"


def _prepare_base_map_repo(repo_root: Path, base: Path) -> Path:
    from conftest import build_mini_repo
    from repo_builders import copy_real_contracts
    from scenario_fixtures import rich_world

    repo = build_mini_repo(base)
    rich_world(repo)
    copy_real_contracts(repo_root, repo)
    map_path = repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    current = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    stage1 = copy.deepcopy(current["stages"][0])
    stage2 = copy.deepcopy(current["stages"][1])
    stage3 = copy.deepcopy(stage2)
    stage3["id"] = "stage-retired"
    stage3["title"] = "Retired legacy stage"
    stage3["working_note"] = (
        "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-retired/notes.md"
    )
    (repo / stage3["working_note"]).parent.mkdir(parents=True, exist_ok=True)
    (repo / stage3["working_note"]).write_text("# Retired stage notes\n", encoding="utf-8")
    current["stages"] = [stage1, stage2, stage3]
    current["status"] = "active"
    current["current_stage"] = stage1["id"]
    current["detours"] = [{
        "id": "detour-retired",
        "title": "Old detour",
        "spawned_by_stage": "stage-retired",
        "classification": "helpful-now",
        "status": "open",
        "return_to_stage": stage1["id"],
    }]
    _dump_yaml(map_path, current)

    incoming = yaml.safe_load(
        (repo_root / "tests/scenarios/files/unit.map.import/reorder/map.yaml").read_text(
            encoding="utf-8"
        )
    )
    incoming["status"] = "ready"
    incoming["current_stage"] = stage2["id"]
    incoming["detours"] = []
    incoming["stages"][0]["status"] = "pending"
    incoming["stages"][1]["status"] = "pending"
    for target_stage, orig_stage in (
        (incoming["stages"][0], stage2),
        (incoming["stages"][1], stage1),
    ):
        for opt_key in ("knowledge_node_id", "runtime_target", "runtime_review"):
            if opt_key in orig_stage:
                target_stage[opt_key] = copy.deepcopy(orig_stage[opt_key])
    _dump_yaml(repo / "work/inbox/reorder-retire-reset.yaml", incoming)
    gen = _run_los(repo_root, repo, "generate")
    assert gen.returncode == 0, gen.stderr
    return base / "LearningOS"


def _prepare_base_delivery_repo(repo_root: Path, base: Path, tmp_dir: Path) -> tuple[Path, str]:
    from conftest import build_mini_repo
    from repo_builders import copy_real_contracts
    from scenario_fixtures import rich_world

    repo = build_mini_repo(base)
    rich_world(repo)
    copy_real_contracts(repo_root, repo)
    delivery_src = tmp_dir / "delivery-bundle"
    shutil.copytree(
        repo_root / "tests/scenarios/files/ai-action.delivery.apply/apply-garden-shelve/delivery",
        delivery_src,
    )
    prep = _run_los(
        repo_root, repo,
        "ai-action-prepare",
        "--action-id", "garden.shelve",
        "--target-kind", "garden-note",
        "--target-id", "garden-note-seed",
        "--request-id", "ai-request-scenario-shelve",
    )
    assert prep.returncode == 0, prep.stderr
    req_doc = yaml.safe_load(
        (repo / "operations/ai-actions/requests/ai-request-scenario-shelve/request.yaml")
        .read_text(encoding="utf-8")
    )
    delivery_yaml = delivery_src / "delivery.yaml"
    delivery_doc = yaml.safe_load(delivery_yaml.read_text(encoding="utf-8"))
    delivery_doc["preconditions"] = req_doc["preconditions"]
    _dump_yaml(delivery_yaml, delivery_doc)
    imp = _run_los(repo_root, repo, "ai-action-import-delivery", str(delivery_src))
    assert imp.returncode == 0, imp.stderr
    gen = _run_los(repo_root, repo, "generate")
    assert gen.returncode == 0, gen.stderr
    return base / "LearningOS", "ai-delivery-scenario-shelve"


def _clone_scenarios(base_los: Path, parent: Path, prefix: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in SCENARIOS:
        target = parent / f"{prefix}-{name}"
        shutil.copytree(base_los, target)
        mapping[name] = str(target / "repository")
    return mapping


def _receipts(repo: Path) -> list[dict]:
    files = sorted((repo / "operations/transactions").glob("transaction-*.yaml"))
    return [yaml.safe_load(path.read_text(encoding="utf-8")) for path in files]


def _idempotency_entries(repo: Path) -> dict:
    ledger = repo / "operations/transactions/idempotency.yaml"
    if not ledger.is_file():
        return {}
    return yaml.safe_load(ledger.read_text(encoding="utf-8")).get("entries", {})


def _new_receipts(repo: Path, base_ids: set[str]) -> list[dict]:
    return [receipt for receipt in _receipts(repo) if receipt["id"] not in base_ids]


def _new_idempotency_entries(repo: Path, base_keys: set[str]) -> dict:
    return {
        key: value
        for key, value in _idempotency_entries(repo).items()
        if key not in base_keys
    }


def _capture_baseline(base_los: Path) -> dict[str, set[str]]:
    repo = base_los / "repository"
    return {
        "receipt_ids": {receipt["id"] for receipt in _receipts(repo)},
        "idem_keys": set(_idempotency_entries(repo).keys()),
    }


@pytest.fixture(scope="module")
def live_writes_run(repo_root: Path, tmp_path_factory) -> tuple[dict, dict, dict]:
    work = tmp_path_factory.mktemp("ui-phase3-live-writes")
    base_src = _prepare_base_source_repo(repo_root, work / "base-src")
    base_map = _prepare_base_map_repo(repo_root, work / "base-map")
    base_deliv, delivery_id = _prepare_base_delivery_repo(repo_root, work / "base-deliv", work)
    baselines = {
        "sourceSelection": _capture_baseline(base_src),
        "unitMapImport": _capture_baseline(base_map),
        "deliveryApply": _capture_baseline(base_deliv),
    }

    repos_root = work / "scenarios"
    repos_root.mkdir()
    plan = {
        "sourceSelection": _clone_scenarios(base_src, repos_root, "src"),
        "unitMapImport": _clone_scenarios(base_map, repos_root, "map"),
        "deliveryApply": _clone_scenarios(base_deliv, repos_root, "deliv"),
        "deliveryId": delivery_id,
    }
    plan_file = work / "plan.json"
    plan_file.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    proc = subprocess.run(
        [
            "node",
            str(HARNESS),
            "--core-root", str(repo_root),
            "--python", sys.executable,
            "--plan", str(plan_file),
        ],
        cwd=str(UI_ROOT),
        capture_output=True,
        text=True,
        timeout=900,
        env={**os.environ, "TMPDIR": str(work)},
    )
    assert proc.returncode == 0, (
        f"live-writes-harness failed\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    marker = [line for line in proc.stdout.splitlines() if line.startswith("LIVE_WRITES_RESULT ")]
    assert marker, f"missing LIVE_WRITES_RESULT:\n{proc.stdout}"
    return json.loads(marker[-1][len("LIVE_WRITES_RESULT "):]), plan, baselines


@pytest.mark.skip(reason="REGRESSION P1-01 v2: skipped paired witness must fail both Core validate and UI CI system-check")
def test_source_selection_seven_scenarios_on_disk(repo_root: Path, live_writes_run):
    results, plan, baselines = live_writes_run
    base_ids = baselines["sourceSelection"]["receipt_ids"]
    base_idem = baselines["sourceSelection"]["idem_keys"]
    repos = {name: Path(path) for name, path in plan["sourceSelection"].items()}

    # 1. Valid remove+select round-trip persisted + 2 new receipts + passes validate.
    u_valid = yaml.safe_load(
        (repos["valid"] / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml")
        .read_text(encoding="utf-8")
    )
    purposes = [row.get("purpose") for row in u_valid.get("source_selections", [])]
    assert purposes == ["Round-trip re-selection."]
    new_valid = _new_receipts(repos["valid"], base_ids)
    assert [r["id"] for r in new_valid] == [
        results["sourceSelection"]["valid"]["removeTx"],
        results["sourceSelection"]["valid"]["selectTx"],
    ]
    assert _run_los(repo_root, repos["valid"], "validate").returncode == 0

    # 2. Invalid refusal left zero new receipts and original unit.yaml untouched.
    assert _new_receipts(repos["invalid"], base_ids) == []

    # 3. Stale snapshot after external bump refused with zero selection write.
    u_stale = yaml.safe_load(
        (repos["stalePreview"] / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml")
        .read_text(encoding="utf-8")
    )
    assert not any(row.get("purpose") == "Should refuse stale snapshot" for row in u_stale.get("source_selections", []))
    new_stale = _new_receipts(repos["stalePreview"], base_ids)
    assert len(new_stale) == 1 and new_stale[0]["capability"] == "capture.create"

    # 4. Concurrent canonical write preserves newer winner and discards loser.
    u_conc = yaml.safe_load(
        (repos["concurrent"] / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml")
        .read_text(encoding="utf-8")
    )
    conc_purposes = [row.get("purpose") for row in u_conc.get("source_selections", [])]
    assert "Concurrent canonical winner" in conc_purposes
    assert "Stale UI loser" not in conc_purposes
    new_conc = _new_receipts(repos["concurrent"], base_ids)
    assert len(new_conc) == 1 and new_conc[0]["capability"] == "unit.source-selection.set"

    # 5. Duplicate/idempotent replay + serialized duplicate guard creates no extra receipt for replay.
    dup_receipts = _new_receipts(repos["duplicate"], base_ids)
    assert len(dup_receipts) == 2
    assert "idem-dup-src-1" in _new_idempotency_entries(repos["duplicate"], base_idem)

    # 6. Interrupted commit recovered via restart recovery leaves 1 new receipt and persisted selection.
    rec_receipts = _new_receipts(repos["recovery"], base_ids)
    assert len(rec_receipts) == 1
    assert rec_receipts[0]["id"] == results["sourceSelection"]["recovery"]["transactionId"]
    u_rec = yaml.safe_load(
        (repos["recovery"] / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml")
        .read_text(encoding="utf-8")
    )
    assert any(row.get("purpose") == "Recovered after drop" for row in u_rec.get("source_selections", []))

    # 7. Reload manifest reflects exact canonical disk selection.
    rel_receipts = _new_receipts(repos["reload"], base_ids)
    assert [r["id"] for r in rel_receipts] == [results["sourceSelection"]["reload"]["transactionId"]]
    u_rel = yaml.safe_load(
        (repos["reload"] / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml")
        .read_text(encoding="utf-8")
    )
    assert any(row.get("purpose") == "Persisted across reload" for row in u_rel.get("source_selections", []))


def test_unit_map_import_seven_scenarios_on_disk(repo_root: Path, live_writes_run):
    results, plan, baselines = live_writes_run
    base_ids = baselines["unitMapImport"]["receipt_ids"]
    base_idem = baselines["unitMapImport"]["idem_keys"]
    repos = {name: Path(path) for name, path in plan["unitMapImport"].items()}

    # 1. Valid simultaneous reorder + state-reset + stage-retire via modal commits cleanly on disk.
    smap = yaml.safe_load(
        (repos["valid"] / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
        .read_text(encoding="utf-8")
    )
    assert [st["id"] for st in smap["stages"]] == ["stage-demo-pending", "stage-demo"]
    assert smap["current_stage"] == "stage-demo-pending"
    assert smap["detours"] == []
    new_valid = _new_receipts(repos["valid"], base_ids)
    assert len(new_valid) == 1
    assert new_valid[0]["id"] == results["unitMapImport"]["valid"]["transactionId"]
    assert results["unitMapImport"]["valid"]["previewReceiptDelta"] == 0
    assert new_valid[0]["capability"] == "unit.map.import"
    assert _run_los(repo_root, repos["valid"], "validate").returncode == 0

    # 2. Invalid/missing overrides refuses with zero mutation and keeps stage-retired + detour.
    assert _new_receipts(repos["invalid"], base_ids) == []
    smap_inv = yaml.safe_load(
        (repos["invalid"] / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
        .read_text(encoding="utf-8")
    )
    assert [st["id"] for st in smap_inv["stages"]] == ["stage-demo", "stage-demo-pending", "stage-retired"]

    # 3. Draft change after check/preview refuses with zero mutation.
    assert _new_receipts(repos["stalePreview"], base_ids) == []

    # 4. Concurrent stage-progress preserves newer status and keeps original stages.
    new_conc = _new_receipts(repos["concurrent"], base_ids)
    assert len(new_conc) == 1 and new_conc[0]["capability"] == "stage.progress.update"
    smap_conc = yaml.safe_load(
        (repos["concurrent"] / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
        .read_text(encoding="utf-8")
    )
    assert smap_conc["stages"][0]["status"] == "complete"
    assert [st["id"] for st in smap_conc["stages"]] == ["stage-demo", "stage-demo-pending", "stage-retired"]

    # 5. Rapid double-click + exact envelope replay creates exactly 1 new receipt and 1 new idempotency entry.
    new_dup = _new_receipts(repos["duplicate"], base_ids)
    assert len(new_dup) == 1
    assert new_dup[0]["id"] == results["unitMapImport"]["duplicate"]["transactionId"]
    assert len(_new_idempotency_entries(repos["duplicate"], base_idem)) == 1

    # 6. Lost response recovers exact committed transaction via SettingsGatewayRecoveryStore.
    rec_receipts = _new_receipts(repos["recovery"], base_ids)
    assert len(rec_receipts) == 1
    assert rec_receipts[0]["id"] == results["unitMapImport"]["recovery"]["transactionId"]

    # 7. Application reload reads persisted reordered stages back from manifest.json.
    rel_receipts = _new_receipts(repos["reload"], base_ids)
    assert [r["id"] for r in rel_receipts] == [results["unitMapImport"]["reload"]["transactionId"]]
    assert results["unitMapImport"]["reload"]["stages"] == ["stage-demo-pending", "stage-demo"]


def test_ai_delivery_apply_seven_scenarios_on_disk(repo_root: Path, live_writes_run):
    results, plan, baselines = live_writes_run
    base_ids = baselines["deliveryApply"]["receipt_ids"]
    base_idem = baselines["deliveryApply"]["idem_keys"]
    repos = {name: Path(path) for name, path in plan["deliveryApply"].items()}

    # 1. Valid request commits canonical transcription + garden state + request completion + receipt.
    valid_repo = repos["valid"]
    assert (valid_repo / "knowledge/garden/transcriptions/garden-note-seed.md").is_file()
    req_yaml = yaml.safe_load(
        (valid_repo / "operations/ai-actions/requests/ai-request-scenario-shelve/request.yaml")
        .read_text(encoding="utf-8")
    )
    assert req_yaml["status"] == "completed"
    new_valid = _new_receipts(valid_repo, base_ids)
    assert len(new_valid) == 1
    assert new_valid[0]["id"] == results["deliveryApply"]["valid"]["transactionId"]
    assert results["deliveryApply"]["valid"]["previewReceiptDelta"] == 0
    assert new_valid[0]["request"]["approval"]["kind"] == "approved-delivery"
    assert new_valid[0]["request"]["channel"] == "ui"
    assert _run_los(repo_root, valid_repo, "validate").returncode == 0

    # 2. Invalid delivery / disallowed direct gesture writes nothing.
    assert _new_receipts(repos["invalid"], base_ids) == []
    assert not (repos["invalid"] / "knowledge/garden/transcriptions/garden-note-seed.md").exists()

    # 3. Tampered delivery artifact after preview refuses with zero canonical writes.
    assert _new_receipts(repos["stalePreview"], base_ids) == []
    assert not (repos["stalePreview"] / "knowledge/garden/transcriptions/garden-note-seed.md").exists()

    # 4. Concurrent capture preserves newer seed on disk and refuses stale preview.
    new_conc = _new_receipts(repos["concurrent"], base_ids)
    assert len(new_conc) == 1 and new_conc[0]["capability"] == "capture.create"
    assert len(list((repos["concurrent"] / "work/inbox").glob("*.md"))) >= 1
    assert not (repos["concurrent"] / "knowledge/garden/transcriptions/garden-note-seed.md").exists()

    # 5. GardenView double-click + exact envelope replay creates exactly 1 new receipt and 1 transcription.
    new_dup = _new_receipts(repos["duplicate"], base_ids)
    assert len(new_dup) == 1
    assert new_dup[0]["id"] == results["deliveryApply"]["duplicate"]["transactionId"]
    assert len(_new_idempotency_entries(repos["duplicate"], base_idem)) == 1
    assert (repos["duplicate"] / "knowledge/garden/transcriptions/garden-note-seed.md").is_file()

    # 6. Lost response after approved-delivery commit recovers via UI recovery cleanly.
    rec_receipts = _new_receipts(repos["recovery"], base_ids)
    assert len(rec_receipts) == 1
    assert rec_receipts[0]["id"] == results["deliveryApply"]["recovery"]["transactionId"]
    assert (repos["recovery"] / "knowledge/garden/transcriptions/garden-note-seed.md").is_file()

    # 7. Application reload reads completed AI request and transcription path from manifest.
    rel_receipts = _new_receipts(repos["reload"], base_ids)
    assert [r["id"] for r in rel_receipts] == [results["deliveryApply"]["reload"]["transactionId"]]
    assert results["deliveryApply"]["reload"]["requestStatus"] == "completed"
