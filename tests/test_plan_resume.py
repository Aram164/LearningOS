"""Resume from the saved review report: four outcomes, no new mutation.

`verify_plan_receipt.py` is the resume/verification command and the saved
--check JSON is the report it consumes. Request and receipt identity
resolve through the idempotency ledger, so a fresh process resumes
without reconstructing paths, guards, envelopes, or retry identity:

- committed-and-verified (0): receipt exists, projection agrees.
- committed-but-verification-failed (1): receipt exists, state drifted.
- not-applied-or-stale-preflight (3): nothing committed for this request.
- uncertain-requires-replay-lookup (2): the lookup itself is inconclusive.
- invalid-evidence (2): the report is not a preflight for this unit.

A failed verification is never permission to issue a new mutation:
re-running the saved reviewed apply replays the same receipt when
canonical state still matches it, and fails closed without a new commit
when state drifted past the receipt.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from repo_builders import (
    _compact_revision,
    _compact_setup,
    run_los,
    write_yaml,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "verify_plan_receipt.py"
GENERATE = REPO_ROOT / "tools" / "generate.py"


def _revision_file(root: Path, tmp_path: Path, angle: str, name: str) -> Path:
    path = tmp_path / name
    write_yaml(path, _compact_revision(
        root, route_changes={"update": [{
            "route_id": "route-demo-book",
            "fields": {"angle": angle}}]}))
    return path


def _check(root: Path, revision_file: Path):
    proc = run_los(root, "unit-plan-revise", "unit-demo-l01",
                   "--file", str(revision_file), "--check")
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _apply(root: Path, revision_file: Path, report: dict, report_file: Path):
    return run_los(root, "unit-plan-revise", "unit-demo-l01",
                   "--file", str(revision_file),
                   "--apply-reviewed-sha256", report["reviewed_file_sha256"],
                   "--review-report", str(report_file))


def _generate(root: Path):
    proc = subprocess.run([sys.executable, str(GENERATE), "--root", str(root)],
                          text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr


def _verify(root: Path, report_file: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root),
         "--unit", "unit-demo-l01", "--report", str(report_file), *extra],
        text=True, capture_output=True)


def _angle(root: Path) -> str:
    from learning_os.loader import load_repo
    live_map = load_repo(root).module_source_maps["module-demo"]
    return next(r for s in live_map["sources"] for r in s["unit_routes"]
                if r.get("id") == "route-demo-book")["angle"]


def test_lost_response_resolves_identity_from_report(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path, "Angle after resume.", "rev.yaml")
    report = _check(mini_repo, revision_file)
    report_file = tmp_path / "review.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")
    applied = _apply(mini_repo, revision_file, report, report_file)
    assert applied.returncode == 0, applied.stderr
    # The apply response is lost here: only the saved report survives.
    _generate(mini_repo)
    verify = _verify(mini_repo, report_file)
    assert verify.returncode == 0, verify.stderr
    assert verify.stdout.splitlines()[0] == "state: committed-and-verified"
    key = report["gateway_envelope"]["idempotency_key"]
    ledger = yaml.safe_load(
        (mini_repo / "operations/transactions/idempotency.yaml").read_text(
            encoding="utf-8"))
    committed = ledger["entries"][key]["receipt_path"]
    assert f"receipt {committed}" in verify.stdout
    assert report["gateway_envelope"]["request_id"] in verify.stdout
    # Retrying the saved apply after the lost response replays it exactly.
    replayed = _apply(mini_repo, revision_file, report, report_file)
    assert replayed.returncode == 0, replayed.stderr
    assert json.loads(replayed.stdout)["receipt_path"] == committed


def test_unapplied_preflight_reports_stale(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path, "Angle never applied.", "rev.yaml")
    report = _check(mini_repo, revision_file)
    report_file = tmp_path / "review.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")
    verify = _verify(mini_repo, report_file)
    assert verify.returncode == 3
    assert verify.stdout.splitlines()[0] == "state: not-applied-or-stale-preflight"
    assert "no committed receipt" in verify.stderr


def test_changed_draft_refuses_reviewed_apply(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path, "Original angle.", "rev.yaml")
    report = _check(mini_repo, revision_file)
    report_file = tmp_path / "review.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")
    with revision_file.open("a", encoding="utf-8") as handle:
        handle.write("# draft edited after review\n")
    applied = _apply(mini_repo, revision_file, report, report_file)
    assert applied.returncode == 2
    assert "reviewed bytes changed since --check" in applied.stderr
    assert _angle(mini_repo) == "A synthetic angle."


def test_old_review_report_never_applies(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    file_a = _revision_file(mini_repo, tmp_path, "First angle wins.", "a.yaml")
    file_b = _revision_file(mini_repo, tmp_path, "Second angle loses.", "b.yaml")
    report_a = _check(mini_repo, file_a)
    report_b = _check(mini_repo, file_b)
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"
    path_a.write_text(json.dumps(report_a), encoding="utf-8")
    path_b.write_text(json.dumps(report_b), encoding="utf-8")
    applied = _apply(mini_repo, file_a, report_a, path_a)
    assert applied.returncode == 0, applied.stderr
    stale = _apply(mini_repo, file_b, report_b, path_b)
    assert stale.returncode == 3
    assert "STALE_SNAPSHOT" in stale.stdout
    assert _angle(mini_repo) == "First angle wins."
    verify = _verify(mini_repo, path_b)
    assert verify.returncode == 3
    assert verify.stdout.splitlines()[0] == "state: not-applied-or-stale-preflight"


def test_canonical_drift_fails_verification_without_new_mutation(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path, "First angle.", "rev.yaml")
    report = _check(mini_repo, revision_file)
    report_file = tmp_path / "review.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")
    applied = _apply(mini_repo, revision_file, report, report_file)
    assert applied.returncode == 0, applied.stderr
    _generate(mini_repo)
    verify = _verify(mini_repo, report_file)
    assert verify.returncode == 0, verify.stderr
    drift_file = _revision_file(mini_repo, tmp_path, "Drift angle.", "drift.yaml")
    drift_report = _check(mini_repo, drift_file)
    drift_path = tmp_path / "drift.json"
    drift_path.write_text(json.dumps(drift_report), encoding="utf-8")
    drifted = _apply(mini_repo, drift_file, drift_report, drift_path)
    assert drifted.returncode == 0, drifted.stderr
    verify = _verify(mini_repo, report_file)
    assert verify.returncode == 1
    assert verify.stdout.splitlines()[0] == \
        "state: committed-but-verification-failed"
    assert "never permission to issue a new mutation" in verify.stderr
    before = sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    replayed = _apply(mini_repo, revision_file, report, report_file)
    assert replayed.returncode == 2
    assert "changed since its recorded transaction" in replayed.stdout
    after = sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    assert after == before
    assert _angle(mini_repo) == "Drift angle."


def test_missing_receipt_is_uncertain_not_verified(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path, "Angle with lost receipt.", "rev.yaml")
    report = _check(mini_repo, revision_file)
    report_file = tmp_path / "review.json"
    report_file.write_text(json.dumps(report), encoding="utf-8")
    applied = _apply(mini_repo, revision_file, report, report_file)
    assert applied.returncode == 0, applied.stderr
    receipt = json.loads(applied.stdout)["receipt_path"]
    (mini_repo / receipt).unlink()
    verify = _verify(mini_repo, report_file)
    assert verify.returncode == 2
    assert verify.stdout.splitlines()[0] == "state: uncertain-requires-replay-lookup"
    assert "idempotency.yaml" in verify.stderr
