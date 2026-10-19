"""Read-only live measurements; report/apply probes write only to a temp world.

Run with Core's Python; no Core source or live learner state is changed.
"""
from __future__ import annotations

import ast
from collections import Counter
import json
from math import comb
from pathlib import Path
import subprocess
import sys
import tempfile

CORE = Path(__file__).resolve().parents[2] / "repository"
RESULT_PATH = Path(__file__).with_name("VERIFICATION-2026-10-18.json")
sys.path[:0] = [str(CORE / "tools"), str(CORE / "tests")]

from jsonschema import Draft202012Validator
from learning_os.app.ranking import ranked_scan
from learning_os.derive.semantics.lineage import load_ledger
from learning_os.derive.semantics.restamp import analyze
from learning_os.domain.ids import KINDS
from learning_os.domain.plan_import import minimal_artifact_ids
from learning_os.store.loader import load_repo
from learning_os.store.materials.resolution import resolve_route_material_files
from learning_os.store.transactions import transaction_artifacts


def main() -> None:
    result = {"core": subprocess.check_output(
        ["git", "-C", str(CORE), "rev-parse", "HEAD"], text=True).strip()}
    goals, clusters, _ = ranked_scan(CORE)
    result["scan"] = {"goals": len(goals), "groups": len(clusters),
                      "detectors": dict(Counter(g.detector for g in goals)),
                      "outside_id_grammar": sum(
                          KINDS["goal"].pattern.fullmatch(g.goal_id) is None for g in goals)}
    restamp = analyze(CORE)
    result["restamp"] = restamp["totals"]
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    repo = load_repo(CORE)
    ledger = load_ledger(CORE)
    supported = {k for k, v in ledger.items()
                 if v.claim_kind == "route-covers" and v.status == "supported"}
    routes, active_classes, multi = [], Counter(), []
    for mid, smap in repo.module_source_maps.items():
        for source in smap.get("sources", []):
            for raw in source.get("unit_routes", []):
                if not isinstance(raw, dict):
                    continue
                route = {**raw, "source_id": source["source_id"]}
                routes.append(route)
                if repo.modules[mid].get("status") == "archived":
                    continue
                files = resolve_route_material_files(repo, route)
                if len(files) > 1:
                    multi.append(route["id"])
                # Descriptive inventory, not the proposed admission classifier.
                if files:
                    suffixes = "+".join(sorted({f.path.suffix.lower() for f in files}))
                    active_classes["resolved:" + suffixes] += 1
                elif route.get("vault_path"):
                    active_classes["unresolved-vault"] += 1
                elif route.get("url"):
                    active_classes["url-no-resolved-file"] += 1
                else:
                    active_classes["no-resolved-file-or-url"] += 1
    result["population"] = {"routes": len(routes), "supported": len(supported),
                            "unrecorded": sum("covers:" + r["id"] not in ledger for r in routes),
                            "active_resolution": dict(active_classes), "multi_file_routes": multi}
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    schema = json.loads((CORE / "system/schema/requests/goal.decide.schema.json").read_text())
    new_ids = ["lineage-stale:covers:route-demo@1234abcd", "claims-audit:1234abcd"]
    result["goal_schema_accepts_new_tokens"] = not list(
        Draft202012Validator(schema).iter_errors({"goal_id": new_ids, "close": True}))
    evidence_only = {CORE / "operations/transactions/lineage.yaml": "probe"}
    owners = minimal_artifact_ids(CORE, "module-demo", evidence_only, [])
    result["evidence_only_guard"] = {"check_owners_before_ledger_is_prepared": [],
                                   "apply_semantic_owners": owners,
                                   "apply_engine_artifacts": transaction_artifacts(CORE, owners, evidence_only)}
    emitters = {}
    for name in ["scan", "goals"]:
        tree = ast.parse((CORE / f"tools/learning_os/derive/semantics/{name}.py").read_text())
        arg = 1 if name == "scan" else 0
        emitters[name] = sorted({n.args[arg].value for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_emit" and len(n.args) > arg
            and isinstance(n.args[arg], ast.Constant) and isinstance(n.args[arg].value, str)})
    result["emitters"] = emitters
    result["zero_defect_hypergeometric_upper_95"] = {
        str(n): max(d for d in range(129 - n)
                    if comb(128 - d, n) / comb(128, n) >= .05)
        for n in [20, 30]}
    # Reuse the existing synthetic receipt regression with only the saved
    # report augmented. Both reviewed apply and full receipt verification run.
    import conftest
    from repo_builders import _compact_setup, _compact_revision, run_los, write_yaml
    with tempfile.TemporaryDirectory(prefix="los-plan-remainder-") as temporary:
        tmp = Path(temporary)
        mini = conftest.build_mini_repo(tmp)
        _compact_setup(mini)
        revision = _compact_revision(mini, route_changes={"update": [{
            "route_id": "route-demo-book", "fields": {"angle": "A sharper lecture-specific angle."}}]})
        draft = tmp / "revision.yaml"
        write_yaml(draft, revision)
        checked = run_los(mini, "unit-plan-revise", "unit-demo-l01", "--file", str(draft), "--check")
        assert checked.returncode == 0, checked.stderr
        report = json.loads(checked.stdout)
        report.update(claims={"probe": True}, claim_anchors=[{"probe": True}])
        saved = tmp / "check.json"
        saved.write_text(json.dumps(report))
        applied = run_los(mini, "unit-plan-revise", "unit-demo-l01", "--file", str(draft),
                          "--review-report", str(saved), "--apply-reviewed-sha256", report["reviewed_file_sha256"])
        assert applied.returncode == 0, applied.stderr
        response = json.loads(applied.stdout)
        for argv in [
            [str(CORE / "tools/generate.py"), "--root", str(mini)],
            [str(CORE / "tools/verify_plan_receipt.py"), "--root", str(mini),
             "--receipt", response["receipt_path"], "--unit", "unit-demo-l01",
             "--report", str(saved), "--expect-artifacts", "module-demo"],
        ]:
            proc = subprocess.run([sys.executable, *argv], capture_output=True, text=True, timeout=120)
            assert proc.returncode == 0, proc.stderr
        result["extra_report_fields"] = {"reviewed_apply_exit": applied.returncode,
                                         "receipt_verify_exit": proc.returncode,
                                         "receipt_verify_stdout": proc.stdout.strip()}
    result["core_git_status_after"] = subprocess.check_output(
        ["git", "-C", str(CORE), "status", "--porcelain"], text=True).strip()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
