"""Phase B: prospective lineage is admitted, never backfilled.

A module plan that creates, repairs, or removes a route-covers edge
carries per-claim evidence or refuses before apply — including the
no-write preflight. Prose-only edits and untouched routes earn no
records. On apply, the admitted records persist in the same transaction
as the canonical mutation.
"""

from __future__ import annotations

import types
from pathlib import Path

import yaml

from learning_os.commands.module import _phaseB_ledger_text, _phaseB_validate
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
)
from learning_os.revisions import dump_revisions
from learning_os.semantics.lineage import load_ledger

ROOT = Path(__file__).resolve().parent.parent


def _request():
    return GatewayRequestContext(
        request_id="request-phaseB",
        idempotency_key="phaseB-key",
        capability="module.plan.import",
        channel="operator",
        intent_sha256="sha256:" + "0" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "0" * 64,
    )


def _route(rid, covers, locator="Ch 1, the only section"):
    return {"id": rid, "unit_id": "unit-demo-l01", "covers": covers,
            "locator": locator, "angle": "a", "scope": "course"}


def _map(*routes):
    return {"type": "module-source-map", "module_id": "module-demo",
            "sources": [{"source_id": "source-demo-book", "unit_routes": list(routes)}]}


def _repo(live_map):
    return types.SimpleNamespace(module_source_maps={"module-demo": live_map})


def _root_with_revisions(tmp_path, revisions):
    rev_file = tmp_path / "operations" / "transactions" / "revisions.yaml"
    rev_file.parent.mkdir(parents=True, exist_ok=True)
    rev_file.write_text(dump_revisions(revisions), encoding="utf-8")
    return tmp_path


LIVE = _map(_route("route-keep", ["n1"]))
REVS = {"module-demo": 3, "unit-demo-l01": 2}


def _package(source_map, claim_evidence=None):
    package = {
        "module_id": "module-demo",
        "plan_contract": {
            "version": 2, "plan_template_version": 1,
            "coverage_audit": "work/active/w/CONTEXT.md",
            "checks": {"local_inventory_complete": True},
        },
        "module_patch": {}, "source_patches": [], "source_map": source_map,
        "units": [],
    }
    if claim_evidence is not None:
        package["claim_evidence"] = claim_evidence
    return package


def _changed_map():
    return _map(_route("route-keep", ["n1", "n3"]),
                _route("route-new", ["n9"], locator="Ch 9, the new section"))


def _evidence_for(*claim_ids, kind="route-locator", ref=None, note=None, reads=None):
    entries = []
    for claim_id in claim_ids:
        item = {"kind": kind, "ref": ref or "Ch 1"}
        if note is not None:
            item["note"] = note
        entry = {"claim_id": claim_id, "evidence": [item]}
        if reads is not None:
            entry["reads"] = reads
        entries.append(entry)
    return entries


def test_changed_covers_without_evidence_refuses(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    problems, _, _, _ = _phaseB_validate(root, _repo(LIVE), "module-demo",
                                         _package(_changed_map()))
    assert any("without claim evidence" in problem for problem in problems)


def test_evidence_for_unchanged_claims_refuses_as_backfill(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    problems, _, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo",
        _package(LIVE, _evidence_for("covers:route-keep")))
    assert any("never backfill" in problem for problem in problems)


def test_unknown_claim_ids_refuse(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    problems, _, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo",
        _package(_changed_map(), _evidence_for("covers:route-ghost")))
    assert any("route-ghost" in problem for problem in problems)


def test_unresolvable_locator_text_refuses(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    bad = _evidence_for("covers:route-keep", ref="Chapter Nonexistent")
    bad += _evidence_for("covers:route-new", ref="Ch 9")
    problems, _, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo", _package(_changed_map(), bad))
    assert any("absent from the recorded locator" in problem for problem in problems)


def test_unregistered_manifest_and_missing_repo_file_refuse(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    bad = _evidence_for("covers:route-keep", kind="manifest", ref="no/such.pdf")
    bad += _evidence_for("covers:route-new", kind="repo-file", ref="no/such.md")
    problems, _, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo", _package(_changed_map(), bad))
    assert any("unregistered manifest path" in problem for problem in problems)
    assert any("unreadable repo file" in problem for problem in problems)


def test_external_evidence_needs_a_verification_trail(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    bad = _evidence_for("covers:route-keep", kind="external",
                        ref="https://example.edu/reading")
    bad += _evidence_for("covers:route-new", kind="external", ref="not-a-url",
                         note="trail")
    problems, _, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo", _package(_changed_map(), bad))
    assert any("verification trail" in problem for problem in problems)
    assert any("must be an http(s) URL" in problem for problem in problems)


def test_stale_declared_reads_refuse(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    stale = _evidence_for("covers:route-keep", reads={"module-demo": 2})
    stale += _evidence_for("covers:route-new", reads={"module-demo": 3})
    problems, _, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo", _package(_changed_map(), stale))
    assert any("stale revision" in problem for problem in problems)


def test_prose_only_packages_earn_no_records(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    problems, changed, _, _ = _phaseB_validate(
        root, _repo(LIVE), "module-demo", _package(LIVE))
    assert problems == []
    assert changed == {}


def test_manifest_evidence_binds_its_digest(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    (root / "records").mkdir(parents=True, exist_ok=True)
    (root / "records" / "materials-manifest.yaml").write_text(
        yaml.safe_dump({"files": {"book/demo.pdf": {"size": 9, "sha256": "abc"}}}),
        encoding="utf-8")
    package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        _evidence_for("covers:route-keep", kind="manifest", ref="book/demo.pdf"))
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    records = load_ledger(_write_ledger_text(tmp_path, text))
    record = records["covers:route-keep"]
    assert record.derived_from.source_hashes == (("manifest:book/demo.pdf", "abc"),)
    assert record.admitted_by.request_id == "request-phaseB"
    # Post-apply stamping: the gateway increments module-demo on commit, so
    # the new claim stores 4, not the pre-commit 3. The touched unit is not
    # in the package units, so it stays at current instead of incrementing.
    assert dict(record.derived_from.revisions) == {
        "module-demo": 4, "unit-demo-l01": 2}


def _write_ledger_text(tmp_path, text):
    ledger = tmp_path / "operations" / "transactions" / "lineage.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(text, encoding="utf-8")
    schema_dir = tmp_path / "system" / "contracts"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "semantic-lineage-ledger.schema.json").write_text(
        (ROOT / "system" / "contracts" / "semantic-lineage-ledger.schema.json"
         ).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def test_repair_supersedes_without_destroying(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    package = _package(_changed_map(), _evidence_for(
        "covers:route-keep") + _evidence_for(
        "covers:route-new", ref="Ch 9"))
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        first = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                    changed, evidence, live)
    _write_ledger_text(tmp_path, first)
    live_map = _map(_route("route-keep", ["n1", "n3"]),
                    _route("route-new", ["n9"], locator="Ch 9, the new section"))
    second_package = _package(
        _map(_route("route-keep", ["n1"]),
             _route("route-new", ["n9"], locator="Ch 9, the new section")),
        _evidence_for("covers:route-keep"))
    problems, changed2, evidence2, _ = _phaseB_validate(
        root, _repo(live_map), "module-demo", second_package)
    assert problems == []
    with gateway_request_context(_request()):
        second = _phaseB_ledger_text(root, _repo(live_map), "module-demo",
                                     second_package, changed2, evidence2,
                                     _source_routes(live_map))
    records = load_ledger(_write_ledger_text(tmp_path, second))
    repaired = records["covers:route-keep"]
    assert repaired.supersedes is not None
    assert repaired.supersedes["statement"] == (
        "route-keep covers n1, n3")
    assert repaired.status == "supported"


def _source_routes(source_map):
    routes = {}
    for source in source_map.get("sources", []):
        for route in source.get("unit_routes") or []:
            routes[route["id"]] = route
    return routes


def _write_demo_plan(mini_repo, tmp_path):
    from repo_builders import add_curriculum, write_yaml

    add_curriculum(mini_repo)
    unit_path = (mini_repo / "curriculum/modules/module-demo/units"
                 / "unit-demo-l01/unit.yaml")
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Demo nodes.",
        "nodes": [{"id": "knowledge-demo-alpha", "title": "Alpha",
                   "summary": "First node."}],
    }
    audit_rel = "work/active/workspace-demo/outputs/demo-b-coverage-audit.md"
    audit = mini_repo / audit_rel
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Demo B audit\n\n## Local\n\nx\n\n## Linked\n\nx\n\n## Completeness\n\nx\n",
        encoding="utf-8",
    )
    rich = {"id": "route-demo-rich", "unit_id": "unit-demo-l01",
            "covers": ["knowledge-demo-alpha"], "scope": "current",
            "format": "book", "depth": "course-aligned",
            "locator": "Demo Book, Ch 9, pp. 100-110, the alpha section",
            "angle": "Teaches alpha.", "angle_detail": "Alpha in detail.",
            "title": "Demo alpha route"}
    package_data = {
        "module_id": "module-demo",
        "plan_contract": {
            "version": 2, "plan_template_version": 1,
            "coverage_audit": audit_rel,
            "checks": {
                "local_inventory_complete": True,
                "linked_inventory_complete": True,
                "materials_opened_and_content_checked": True,
                "current_and_prior_scope_reconciled": True,
                "duplicates_and_numbering_checked": True,
                "exclusions_and_unresolved_gaps_recorded": True,
            },
        },
        "module_patch": {}, "source_patches": [],
        "source_map": {
            "type": "module-source-map", "module_id": "module-demo",
            "sources": [{"source_id": "source-demo-book", "role": "course-material",
                         "why": "w", "priority": 0,
                         "unit_routes": ["unit-demo-l01", rich]}]},
        "units": [{"unit": unit}],
        "claim_evidence": [{"claim_id": "covers:route-demo-rich", "evidence": [
            {"kind": "route-locator", "ref": "Ch 9, pp. 100-110"}]}],
    }
    package = tmp_path / "plan.yaml"
    write_yaml(package, package_data)
    return package, package_data


def test_end_to_end_apply_persists_lineage_atomically(mini_repo, tmp_path):
    import json as _json

    from gateway_helpers import approved_v2_cli, file_sha256
    from repo_builders import run_los, write_yaml

    package, package_data = _write_demo_plan(mini_repo, tmp_path)

    bare = dict(package_data)
    bare.pop("claim_evidence")
    bare_package = tmp_path / "bare-plan.yaml"
    write_yaml(bare_package, bare)
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(bare_package), "--check")
    assert refused.returncode == 1
    assert "without claim evidence" in refused.stderr

    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(package), "--check")
    assert checked.returncode == 0, checked.stderr

    applied = approved_v2_cli(
        mini_repo, "module-plan-import", "module-demo",
        "--file", str(package), "--file-sha256", file_sha256(package),
        artifact_ids=["module-demo", "unit-demo-l01"],
        idempotency_key="phaseB-e2e-atomic",
    )
    assert applied.returncode == 0, applied.stderr
    result = _json.loads(applied.stdout)["result"]
    assert result["ok"] is True
    receipt = yaml.safe_load(
        (mini_repo / result["receipt_path"]).read_text(encoding="utf-8"))
    written = [row.get("path", "") for row in receipt.get("writes", [])
               if isinstance(row, dict)]
    assert any("lineage.yaml" in path for path in written)
    assert any("source-map.yaml" in path for path in written)
    ledger = yaml.safe_load(
        (mini_repo / "operations/transactions/lineage.yaml").read_text(
            encoding="utf-8"))
    assert ledger["schema_version"] == 2
    record = ledger["records"]["covers:route-demo-rich"]
    assert record["admitted_by"]["request_id"].startswith("request-")
    assert "knowledge-demo-alpha" in record["statement"]
    live_map = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/source-map.yaml"
         ).read_text(encoding="utf-8"))
    assert any(isinstance(route, dict) and route.get("id") == "route-demo-rich"
               for source in live_map["sources"]
               for route in source.get("unit_routes", []))


def test_removed_routes_withdraw_cascade(tmp_path):
    from learning_os.semantics.lineage import dump_ledger, emit_route_covers
    root = _root_with_revisions(tmp_path, REVS)
    old = emit_route_covers(
        route_id="route-drop", covers=["n2"],
        read_revisions=dict(REVS), judged_by="t",
        admitted_by={"request_id": "r", "idempotency_key": "k"},
        evidence=["route-locator:Ch 2"])
    _write_ledger_text(tmp_path, dump_ledger({"covers:route-drop": old}))
    package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        _evidence_for("covers:route-keep", "covers:route-drop"))
    repo = _repo(_map(_route("route-keep", ["n1"]), _route("route-drop", ["n2"])))
    problems, changed, evidence, live = _phaseB_validate(
        root, repo, "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, repo, "module-demo", package,
                                   changed, evidence, live)
    records = load_ledger(_write_ledger_text(tmp_path, text))
    assert records["covers:route-drop"].status == "withdrawn"
    assert "covers:route-keep" in records


def test_declared_reads_and_external_trail_persist(tmp_path):
    root = _root_with_revisions(
        tmp_path, {"module-demo": 3, "unit-demo-l01": 2, "some-artifact": 7})
    package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        [{"claim_id": "covers:route-keep",
          "evidence": [{"kind": "external", "ref": "https://example.edu/r",
                        "note": "opened 2026-09-08, section verified"}],
          "reads": {"module-demo": 3, "some-artifact": 7}}])
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    record = load_ledger(_write_ledger_text(tmp_path, text))["covers:route-keep"]
    # Declared reads store post-apply validity for incremented artifacts:
    # module-demo was fresh at 3 pre-commit and commits at 4, while the
    # untouched some-artifact stays at 7.
    assert dict(record.derived_from.revisions) == {
        "module-demo": 4, "unit-demo-l01": 2, "some-artifact": 7}
    assert record.derived_from.evidence == (
        "external:https://example.edu/r -- trail: opened 2026-09-08, section verified",)


def _apply_in_process(mini_repo, package, key, request_id):
    """Run module-plan-import through the real handler, not a subprocess.

    Subprocess helpers cannot carry a monkeypatched failure into the commit,
    so this drives the same handler ``cmd_capability`` would dispatch to,
    under an admitted gateway context with live snapshot and revision tokens.
    """
    from gateway_helpers import file_sha256

    import los
    from learning_os.commands.module import cmd_module_plan_import
    from learning_os.fingerprint import canonical_fingerprint
    from learning_os.revisions import load_revisions

    revisions = load_revisions(mini_repo)
    snapshot = f"sha256:{canonical_fingerprint(mini_repo)}"
    parser = los.build_parser()
    args = parser.parse_args([
        "--root", str(mini_repo), "module-plan-import", "module-demo",
        "--file", str(package), "--file-sha256", file_sha256(package),
        "--expected-snapshot", snapshot,
        "--expected-revision",
        f"module-demo={revisions.get('module-demo', 0)}",
        "--expected-revision",
        f"unit-demo-l01={revisions.get('unit-demo-l01', 0)}",
    ])
    request = GatewayRequestContext(
        request_id=request_id,
        idempotency_key=key,
        capability="module.plan.import",
        channel="operator",
        intent_sha256="sha256:" + "0" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "0" * 64,
        expected_snapshot=snapshot,
    )
    with gateway_request_context(request):
        return cmd_module_plan_import(args)


def test_mid_commit_failure_rolls_back_lineage_and_canonical(
        mini_repo, tmp_path, monkeypatch, capsys):
    import learning_os.transactions as transactions

    package, _ = _write_demo_plan(mini_repo, tmp_path)
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    lineage_path = mini_repo / "operations/transactions/lineage.yaml"
    before = source_map_path.read_bytes()
    assert not lineage_path.exists()

    real_write = transactions._atomic_write_bytes
    state = {"failed": False}

    def fail_lineage_write(path, content):
        if not state["failed"] and Path(path).name == "lineage.yaml":
            state["failed"] = True
            raise OSError("injected mid-commit failure")
        return real_write(path, content)

    monkeypatch.setattr(transactions, "_atomic_write_bytes", fail_lineage_write)
    code = _apply_in_process(
        mini_repo, package, "phaseB-e2e-rollback", "request-rollback-1")
    captured = capsys.readouterr()
    assert state["failed"]
    assert code == 2
    assert "injected mid-commit failure" in captured.err
    assert source_map_path.read_bytes() == before
    assert not lineage_path.exists()

    retry = _apply_in_process(
        mini_repo, package, "phaseB-e2e-rollback", "request-rollback-2")
    assert retry == 0
    assert lineage_path.is_file()


def test_new_claim_supported_immediately_after_own_commit(tmp_path):
    from learning_os.semantics.lineage import refresh
    from learning_os.semantics.predicates import CONTRACT_VERSION

    root = _root_with_revisions(tmp_path, REVS)
    package = _package(_changed_map(), _evidence_for(
        "covers:route-keep") + _evidence_for(
        "covers:route-new", ref="Ch 9"))
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    records = load_ledger(_write_ledger_text(tmp_path, text))
    # The gateway increments exactly module-demo here (no package units), so
    # post-apply state is module-demo 4 with the touched unit unmoved.
    post = {"module-demo": 4, "unit-demo-l01": 2}
    for claim_id in ("covers:route-keep", "covers:route-new"):
        assert refresh(
            records[claim_id], CONTRACT_VERSION, post, {},
        ).status == "supported"


def test_touched_unit_without_package_entry_stays_at_current(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    package = _package(_changed_map(), _evidence_for(
        "covers:route-keep") + _evidence_for(
        "covers:route-new", ref="Ch 9"))
    assert package.get("units") == []
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    record = load_ledger(_write_ledger_text(tmp_path, text))["covers:route-keep"]
    assert dict(record.derived_from.revisions)["unit-demo-l01"] == 2


def test_package_unit_gets_post_apply_bump(tmp_path):
    root = _root_with_revisions(tmp_path, REVS)
    package = _package(_changed_map(), _evidence_for(
        "covers:route-keep") + _evidence_for(
        "covers:route-new", ref="Ch 9"))
    package["units"] = [{"unit": {"id": "unit-demo-l01",
                                  "module_id": "module-demo"}}]
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    record = load_ledger(_write_ledger_text(tmp_path, text))["covers:route-keep"]
    assert dict(record.derived_from.revisions) == {
        "module-demo": 4, "unit-demo-l01": 3}


def test_manifest_digest_mutation_stales_and_missing_fails_closed(tmp_path):

    from learning_os.semantics.lineage import refresh
    from learning_os.semantics.predicates import CONTRACT_VERSION
    from learning_os.semantics.scan import live_evidence_digest

    root = _root_with_revisions(tmp_path, REVS)
    (root / "records").mkdir(parents=True, exist_ok=True)
    (root / "records" / "materials-manifest.yaml").write_text(
        yaml.safe_dump({"files": {"book/demo.pdf": {"size": 9, "sha256": "abc"}}}),
        encoding="utf-8")
    package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        _evidence_for("covers:route-keep", kind="manifest", ref="book/demo.pdf"))
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    record = load_ledger(_write_ledger_text(tmp_path, text))["covers:route-keep"]
    post = {"module-demo": 4, "unit-demo-l01": 2}

    def _live():
        from learning_os.semantics.scan import _scan_manifest_files

        files = _scan_manifest_files(root)
        digest = live_evidence_digest(root, "manifest:book/demo.pdf", files)
        return {} if digest is None else {"manifest:book/demo.pdf": digest}

    assert refresh(record, CONTRACT_VERSION, post, _live()).status == "supported"
    (root / "records" / "materials-manifest.yaml").write_text(
        yaml.safe_dump({"files": {"book/demo.pdf": {"size": 10, "sha256": "xyz"}}}),
        encoding="utf-8")
    assert refresh(record, CONTRACT_VERSION, post, _live()).status == "stale"
    (root / "records" / "materials-manifest.yaml").write_text(
        yaml.safe_dump({"files": {}}), encoding="utf-8")
    assert _live() == {}
    assert refresh(record, CONTRACT_VERSION, post, _live()).status == "stale"


def test_file_bytes_mutation_stales_and_unrelated_unchanged(tmp_path):
    import hashlib as _hashlib

    from learning_os.semantics.lineage import refresh
    from learning_os.semantics.predicates import CONTRACT_VERSION
    from learning_os.semantics.scan import live_evidence_digest

    root = _root_with_revisions(tmp_path, REVS)
    target = root / "work" / "evidence.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("version one", encoding="utf-8")
    package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        _evidence_for("covers:route-keep", kind="repo-file",
                      ref="work/evidence.md"))
    problems, changed, evidence, live = _phaseB_validate(
        root, _repo(LIVE), "module-demo", package)
    assert problems == []
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo", package,
                                   changed, evidence, live)
    records = load_ledger(_write_ledger_text(tmp_path, text))
    record = records["covers:route-keep"]
    expected = "sha256:" + _hashlib.sha256(b"version one").hexdigest()
    assert dict(record.derived_from.source_hashes) == {
        "file:work/evidence.md": expected}
    post = {"module-demo": 4, "unit-demo-l01": 2}

    def _live_for(key):
        from learning_os.semantics.scan import _scan_manifest_files

        digest = live_evidence_digest(root, key, _scan_manifest_files(root))
        return {} if digest is None else {key: digest}

    assert refresh(
        record, CONTRACT_VERSION, post, _live_for("file:work/evidence.md"),
    ).status == "supported"
    target.write_text("version two", encoding="utf-8")
    assert refresh(
        record, CONTRACT_VERSION, post, _live_for("file:work/evidence.md"),
    ).status == "stale"
    # An unrelated hash-less claim on the same revisions stays supported.
    other_package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        _evidence_for("covers:route-keep"))
    problems, changed2, evidence2, live2 = _phaseB_validate(
        root, _repo(LIVE), "module-demo", other_package)
    assert problems == []
    with gateway_request_context(_request()):
        other_text = _phaseB_ledger_text(root, _repo(LIVE), "module-demo",
                                         other_package, changed2, evidence2, live2)
    other = load_ledger(_write_ledger_text(tmp_path, other_text))[
        "covers:route-keep"]
    assert refresh(other, CONTRACT_VERSION, post, {}).status == "supported"
    target.unlink()
    assert _live_for("file:work/evidence.md") == {}
    assert refresh(
        record, CONTRACT_VERSION, post, _live_for("file:work/evidence.md"),
    ).status == "stale"


def test_deleted_edge_withdraw_spares_new_claim_post_apply(tmp_path):
    from learning_os.semantics.lineage import dump_ledger, emit_route_covers, refresh
    from learning_os.semantics.predicates import CONTRACT_VERSION

    root = _root_with_revisions(tmp_path, REVS)
    old = emit_route_covers(
        route_id="route-drop", covers=["n2"],
        read_revisions=dict(REVS), judged_by="t",
        admitted_by={"request_id": "r", "idempotency_key": "k"},
        evidence=["route-locator:Ch 2"])
    _write_ledger_text(tmp_path, dump_ledger({"covers:route-drop": old}))
    package = _package(
        _map(_route("route-keep", ["n1", "n3"])),
        _evidence_for("covers:route-keep", "covers:route-drop"))
    repo = _repo(_map(_route("route-keep", ["n1"]), _route("route-drop", ["n2"])))
    problems, changed, evidence, live = _phaseB_validate(
        root, repo, "module-demo", package)
    assert problems == []
    assert changed == {"route-keep": ["n1", "n3"], "route-drop": []}
    with gateway_request_context(_request()):
        text = _phaseB_ledger_text(root, repo, "module-demo", package,
                                   changed, evidence, live)
    records = load_ledger(_write_ledger_text(tmp_path, text))
    assert records["covers:route-drop"].status == "withdrawn"
    post = {"module-demo": 4, "unit-demo-l01": 2}
    assert refresh(
        records["covers:route-keep"], CONTRACT_VERSION, post, {},
    ).status == "supported"
    assert records["covers:route-keep"].status == "supported"


def test_post_commit_supported_end_to_end_via_gateway(mini_repo, tmp_path):

    from gateway_helpers import approved_v2_cli, file_sha256

    from learning_os.revisions import load_revisions
    from learning_os.semantics.lineage import load_ledger as _load_ledger
    from learning_os.semantics.lineage import refresh as _refresh
    from learning_os.semantics.predicates import CONTRACT_VERSION as _CONTRACT

    package, _ = _write_demo_plan(mini_repo, tmp_path)
    applied = approved_v2_cli(
        mini_repo, "module-plan-import", "module-demo",
        "--file", str(package), "--file-sha256", file_sha256(package),
        artifact_ids=["module-demo", "unit-demo-l01"],
        idempotency_key="phaseB-e2e-post-commit-supported",
    )
    assert applied.returncode == 0, applied.stderr
    ledger = _load_ledger(mini_repo)
    record = ledger["covers:route-demo-rich"]
    assert record.status == "supported"
    current = load_revisions(mini_repo)
    live_hashes = dict(record.derived_from.source_hashes)
    assert _refresh(
        record, _CONTRACT, current, live_hashes,
    ).status == "supported"

    # A deletion-only package must not bypass the lineage handler. The
    # previous test of its private writer combined deletion with addition,
    # which never exercised the handler's empty-changed-claims branch.
    from repo_builders import run_los, write_yaml

    package_data = yaml.safe_load(package.read_text(encoding="utf-8"))
    package_data["source_map"]["sources"][0]["unit_routes"] = ["unit-demo-l01"]
    evidence = package_data.pop("claim_evidence")
    write_yaml(package, package_data)
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(package), "--check")
    assert refused.returncode == 1
    assert "without claim evidence" in refused.stderr
    package_data["claim_evidence"] = evidence
    write_yaml(package, package_data)
    removed = approved_v2_cli(
        mini_repo, "module-plan-import", "module-demo",
        "--file", str(package), "--file-sha256", file_sha256(package),
        artifact_ids=["module-demo", "unit-demo-l01"],
        idempotency_key="phaseB-e2e-removal-only",
    )
    assert removed.returncode == 0, removed.stderr
    withdrawn = _load_ledger(mini_repo)["covers:route-demo-rich"]
    assert withdrawn.status == "withdrawn"
    assert withdrawn.supersedes["statement"] == record.statement
