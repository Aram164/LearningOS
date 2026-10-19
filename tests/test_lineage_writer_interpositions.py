"""Actual handlers invalidate a prepared whole-ledger replacement.

Only the shared file revision is guarded by the suspended replacement, so
unrelated canonical changes cannot make this witness pass accidentally.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_call, file_sha256
from repo_builders import run_los

from learning_os.derive.semantics.lineage import dump_ledger
from learning_os.store.transactions import (
    TransactionConflict,
    TransactionService,
    artifact_revision,
)

ARTIFACT = "file:operations/transactions/lineage.yaml"
CAPABILITIES = {
    "module": "module.plan.import", "unit": "unit.plan.revise", "route": "route.patch",
    "source-replacement": "source.record.revise", "source-rebase": "source.record.revise",
    "publication": "unit.material-synthesis.publish", "restamp": "lineage.restamp",
}


@pytest.mark.parametrize("writer", CAPABILITIES)
def test_each_actual_handler_invalidates_a_prepared_lineage_replacement(mini_repo, tmp_path, monkeypatch, writer):
    capability = CAPABILITIES[writer]
    root = mini_repo
    mode = "gateway"
    payload = {}
    artifacts = []
    argv = ()
    if writer == "module":
        from test_phaseB_prospective_lineage import _write_demo_plan
        package, _ = _write_demo_plan(root, tmp_path)
        payload = {"module_id": "module-demo", "file": str(package), "file_sha256": file_sha256(package)}
        artifacts = ["module-demo", "unit-demo-l01", ARTIFACT]
    elif writer == "unit":
        from test_unit_plan_revision import _ledger_only_fixture
        _, _, argv = _ledger_only_fixture(root, tmp_path)
        mode = "cli"
    elif writer == "route":
        from test_verbatim_anchor_admission import _patch_world
        evidence = _patch_world(root)
        checked = run_los(root, "route-patch", "unit-demo-l01", "route-test", "--changes",
            json.dumps({"locator": "lecture-01.pdf, PDF p. 1"}), "--claim-evidence", json.dumps(evidence), "--check")
        assert checked.returncode == 0, checked.stderr
        report = json.loads(checked.stdout)
        payload, artifacts = report["next"]["payload"], report["artifact_ids"]
    elif writer in {"source-replacement", "source-rebase"}:
        from test_source_record_revise import (
            _check,
            _dossier_digest,
            _dossier_unit,
            _package,
            _rebase_request,
            _revise,
            _shaped_setup,
            _staged_replacement,
            _with_material_tree,
            _write_dossier,
        )
        if writer == "source-replacement":
            from repo_builders import _valid_dossier
            _with_material_tree(root)
            unit_dir = _dossier_unit(root)
            _write_dossier(unit_dir, _valid_dossier(root, "route-demo-l01-book", "Chapter 1"))
            record = _revise(material_syntheses=[{"unit_id": "unit-demo-l01", "dossier": _staged_replacement(root)}])
        else:
            _, live = _shaped_setup(root)
            record = _revise(dossier_rebases=[_rebase_request(_dossier_digest(live))])
        checked = _check(root, _package(tmp_path, record))
        payload = {"record": record, "expected_diff_sha256": checked["diff_sha256"]}
        artifacts = checked["artifact_ids"]
    elif writer == "publication":
        import scenario_harness as harness
        data = harness.load_case_file(Path(__file__).parent / "scenarios/cases/unit.material-synthesis.publish.yaml")
        case = {**next(row for row in data["cases"] if row["id"] == "publish-dossier"),
                "fixture": data["fixture"], "observations": data["observations"]}
        work = tmp_path / "publication"
        work.mkdir()
        context = harness._prepare_world(case, capability, work)
        root = context.root
        mode = "scenario"
    else:
        from test_lineage_restamp import _judged_repo, _reviewed_check

        from learning_os.store.session import githistory
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
            monkeypatch.delenv(name, raising=False)
        for name in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
            monkeypatch.setenv(name, "2020-01-02T03:04:05+00:00")
        githistory.last_commit_dates.cache_clear()
        root, cid, _ = _judged_repo(tmp_path / "restamp")
        report = tmp_path / "restamp-check.json"
        _, claims_sha = _reviewed_check(root, cid, report)
        argv = ("lineage-restamp", "--claim-ids", cid, "--claims-sha256", claims_sha, "--review-report", str(report))
        mode = "cli"

    path = root / "operations/transactions/lineage.yaml"
    prepared = path.read_bytes() if path.exists() else dump_ledger({}).encode()
    observed_revision = artifact_revision(root, ARTIFACT)
    receipts_before = set((root / "operations/transactions").glob("transaction-*.yaml"))
    if mode == "gateway":
        proc = approved_v2_call(root, capability=capability, payload=payload,
                               artifact_ids=artifacts, idempotency_key="interposed-" + writer)
        assert proc.returncode == 0, proc.stdout + proc.stderr
    elif mode == "cli":
        proc = run_los(root, *argv)
        assert proc.returncode == 0, proc.stdout + proc.stderr
    else:
        actual = harness._run_step(context, capability, case, 0)
        harness.check_witnesses(context)
        assert actual["exit"] == 0, actual
    foreign = path.read_bytes()
    assert foreign != prepared
    assert artifact_revision(root, ARTIFACT) == observed_revision + 1
    receipts_after = set((root / "operations/transactions").glob("transaction-*.yaml"))
    receipts = [yaml.safe_load(item.read_text()) for item in receipts_after - receipts_before]
    assert any(row["capability"] == capability and any(
        write["path"] == "operations/transactions/lineage.yaml" for write in row["writes"]) for row in receipts)

    # A fresh canonical snapshot cannot compensate for an obsolete ledger
    # observation: isolate the file guard with no snapshot/owner guard at all.
    service = TransactionService(root)
    with pytest.raises(TransactionConflict):
        service.commit(capability="unit.plan.revise", writes={path: prepared}, artifact_ids=[ARTIFACT],
                       expected_revisions={ARTIFACT: observed_revision})
    assert path.read_bytes() == foreign
    assert set((root / "operations/transactions").glob("transaction-*.yaml")) == receipts_after
    # Disabled-protection counterexample in this disposable world: omitting
    # the observed revision really would overwrite the interposed lineage.
    service.commit(capability="unit.plan.revise", writes={path: prepared}, artifact_ids=[ARTIFACT])
    assert path.read_bytes() == prepared
