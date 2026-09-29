"""Reviewed local-material attach for an existing source, plus evaluation repair.

`source.record.revise` is the narrow answer to the 2026-09-29 shelving
complaint: a source whose verified local bytes now exist gains its `material`
link (and, when the old judgment is stale, a replacement `evaluations`) without
routing a source-library fact through a full module plan import. Identity and
intake-owned fields are never touched here; routes, selections, notes,
feedback and observations are unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call
from repo_builders import run_los, write_yaml

PDF = b"%PDF-1.4 demo bytes for the revise path\n"
URI = "material://source-demo-book/demo.pdf"
EVALS = [{"concepts": ["concept-expected-value"], "roles": ["first-learning"],
          "level": "introductory", "strengths": ["verified local PDF"]}]


def _sha(data: bytes = PDF) -> str:
    return hashlib.sha256(data).hexdigest()


def _material_tree(root: Path, data: bytes = PDF) -> Path:
    materials = root.parent / "materials"
    target = materials / "mathematics" / "demo" / "demo.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    flat = materials / ".flat"
    flat.mkdir(exist_ok=True)
    link = flat / "source-demo-book"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to("../mathematics/demo")
    return target


def _manifest(root: Path, sha: str | None = None, size: int | None = None):
    write_yaml(root / "records" / "materials-manifest.yaml", {
        "schema_version": 1, "captured": "2026-09-29", "totals": {},
        "files": {"mathematics/demo/demo.pdf":
                  {"size": len(PDF) if size is None else size,
                   "sha256": _sha() if sha is None else sha}},
    })


def _package(tmp_path: Path, record: dict) -> Path:
    path = tmp_path / "revise.yaml"
    write_yaml(path, record)
    return path


def _revise(**changes):
    value = {"id": "source-demo-book", "material": URI,
             "material_sha256": _sha(), "evaluations": EVALS}
    value.update(changes)
    return value


def _check(root: Path, package: Path):
    proc = run_los(root, "source-revise", "--file", str(package), "--check")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


def _refuses(root: Path, package: Path, fragment: str):
    proc = run_los(root, "source-revise", "--file", str(package), "--check")
    assert proc.returncode == 2, proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is False
    assert fragment in body["error"], body["error"]


def _with_material_tree(mini_repo: Path, data: bytes = PDF):
    _material_tree(mini_repo, data)
    _manifest(mini_repo)


# --------------------------------------------------------------------- check
def test_check_attach_reports_diff_and_writes_nothing(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    target = mini_repo / "sources" / "sources.yaml"
    before = target.read_bytes()
    body = _check(mini_repo, _package(tmp_path, _revise()))
    assert body["check"] is True
    assert body["diff_sha256"].startswith("sha256:")
    assert body["artifact_ids"] == ["source-demo-book"]
    assert body["expected_revisions"] == {"source-demo-book": 0}
    (row,) = body["diff"]
    assert row["id"] == "source-demo-book"
    assert set(row["fields"]) == {"material", "evaluations"}
    assert row["fields"]["material"] == {"before": None, "after": URI}
    assert row["refers"] == {"routes": [], "dossiers": []}
    assert target.read_bytes() == before


def test_check_evaluations_only_replace(mini_repo, tmp_path):
    record = _revise()
    del record["material"]
    del record["material_sha256"]
    body = _check(mini_repo, _package(tmp_path, record))
    (row,) = body["diff"]
    assert set(row["fields"]) == {"evaluations"}


def test_check_lists_referring_routes_and_bound_dossiers(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    module_dir = mini_repo / "curriculum" / "modules" / "module-demo"
    unit_dir = module_dir / "units" / "unit-demo-l01"
    unit_dir.mkdir(parents=True)
    write_yaml(module_dir / "module.yaml", {
        "id": "module-demo", "title": "Demo Module", "status": "active",
    })
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l01", "module_id": "module-demo", "title": "L01",
        "order": 1, "knowledge_map": {"nodes": []}, "source_selections": [],
    })
    write_yaml(mini_repo / "curriculum" / "modules" / "module-demo"
               / "source-map.yaml", {
        "type": "module-source-map", "module_id": "module-demo",
        "sources": [{"source_id": "source-demo-book", "role": "spine",
                     "why": "demo join", "priority": 0,
                     "unit_routes": [{"id": "route-demo-l01-book",
                                      "unit_id": "unit-demo-l01",
                                      "title": "Demo chapter",
                                      "format": "book",
                                      "angle": "The demo angle.",
                                      "covers": [], "depth": "survey",
                                      "scope": "current"}]}],
    })
    (unit_dir / "material-synthesis.yaml").write_text(
        yaml.safe_dump({"id": "dossier-demo", "unit_id": "unit-demo-l01"}),
        encoding="utf-8")
    body = _check(mini_repo, _package(tmp_path, _revise()))
    (row,) = body["diff"]
    assert row["refers"]["routes"] == [{
        "module_id": "module-demo", "unit_id": "unit-demo-l01",
        "route_id": "route-demo-l01-book"}]
    assert row["refers"]["dossiers"] == ["unit-demo-l01"]


def test_revise_rejects_unknown_and_malformed_ids(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    _refuses(mini_repo, _package(tmp_path, _revise(id="source-ghost")),
             "unknown source")
    _refuses(mini_repo, _package(tmp_path, _revise(id="not-a-source-id")),
             "must match source-<slug>")


def test_revise_refuses_foreign_fields(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    _refuses(mini_repo, _package(tmp_path, _revise(title="Retitled")),
             "owned by intake")
    _refuses(mini_repo, _package(tmp_path, _revise(topics=["t"])),
             "outside the revise allowlist")


def test_revise_with_no_changes_is_refused(mini_repo, tmp_path):
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["evaluations"] = EVALS
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    record = _revise()
    del record["material"]
    del record["material_sha256"]
    _refuses(mini_repo, _package(tmp_path, record), "no source-record changes")


def test_revise_needs_the_request_hash_for_a_material_change(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    record = _revise()
    del record["material_sha256"]
    _refuses(mini_repo, _package(tmp_path, record), "needs 'material_sha256'")
    _refuses(mini_repo, _package(tmp_path, _revise(material_sha256="nope")),
             "64 lowercase hex")


def test_revise_refuses_a_stray_request_hash(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    record = _revise()
    del record["material"]
    _refuses(mini_repo, _package(tmp_path, record),
             "without a 'material' change")


def test_revise_refuses_bytes_that_miss_the_request_hash(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    _refuses(mini_repo, _package(tmp_path, _revise(material_sha256=_sha(b"other"))),
             "do not match the request hash")


def test_revise_refuses_a_stale_or_missing_manifest_row(mini_repo, tmp_path):
    _material_tree(mini_repo)
    _manifest(mini_repo, sha=_sha(b"stale"))
    _refuses(mini_repo, _package(tmp_path, _revise()),
             "do not match the manifest")
    _manifest(mini_repo)
    target = mini_repo / "records" / "materials-manifest.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    data["files"] = {}
    target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _refuses(mini_repo, _package(tmp_path, _revise()),
             "absent from the materials manifest")


def test_revise_refuses_unresolvable_and_directory_material(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    _refuses(mini_repo, _package(
        tmp_path, _revise(material="material://source-demo-book/missing.pdf")),
        "does not resolve to a file")
    _refuses(mini_repo, _package(
        tmp_path, _revise(material="material://source-demo-book")),
        "must resolve to one file")


def test_revise_never_silently_replaces_a_different_material(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["material"] = "material://source-demo-book/old.pdf"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _refuses(mini_repo, _package(tmp_path, _revise()), "already holds")


# --------------------------------------------------------------------- apply
def test_apply_attaches_and_replaces_atomically(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    package = _package(tmp_path, _revise())
    checked = _check(mini_repo, package)
    proc = approved_v2_call(
        mini_repo, capability="source.record.revise",
        payload={"record": _revise(),
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["source-demo-book"], idempotency_key="revise-apply")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is True
    assert body["receipt_path"].endswith(".yaml")
    stored = yaml.safe_load(
        (mini_repo / "sources" / "sources.yaml").read_text(encoding="utf-8"))
    assert stored["sources"][0]["material"] == URI
    assert stored["sources"][0]["evaluations"] == EVALS
    assert stored["sources"][0]["title"] == "Demo Book"
    revisions = yaml.safe_load(
        (mini_repo / "operations" / "transactions" / "revisions.yaml")
        .read_text(encoding="utf-8"))
    assert revisions["revisions"]["source-demo-book"] == 1


def test_apply_needs_its_check_diff(mini_repo, tmp_path):
    _with_material_tree(mini_repo)
    checked = _check(mini_repo, _package(tmp_path, _revise()))
    missing = approved_v2_call(
        mini_repo, capability="source.record.revise",
        payload={"record": _revise()}, artifact_ids=["source-demo-book"],
        idempotency_key="revise-no-diff")
    inner = json.loads(json.loads(missing.stdout)["error"]["message"])
    assert inner["ok"] is False
    assert "expected-diff-sha256" in inner["error"]
    last = checked["diff_sha256"][-1]
    wrong = checked["diff_sha256"][:-1] + ("0" if last != "0" else "1")
    stale = approved_v2_call(
        mini_repo, capability="source.record.revise",
        payload={"record": _revise(), "expected_diff_sha256": wrong},
        artifact_ids=["source-demo-book"], idempotency_key="revise-wrong-diff")
    outer = json.loads(stale.stdout)["error"]["message"]
    assert "changed since check" in json.loads(outer)["error"]


def test_apply_refuses_bytes_changed_after_check(mini_repo, tmp_path):
    target = _material_tree(mini_repo)
    _manifest(mini_repo)
    checked = _check(mini_repo, _package(tmp_path, _revise()))
    swapped = b"%PDF-1.4 swapped bytes\n"
    target.write_bytes(swapped)
    # The inventory follows the swap, so only the reviewed request hash fires.
    _manifest(mini_repo, sha=_sha(swapped), size=len(swapped))
    proc = approved_v2_call(
        mini_repo, capability="source.record.revise",
        payload={"record": _revise(),
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["source-demo-book"], idempotency_key="revise-swapped")
    outer = json.loads(proc.stdout)["error"]["message"]
    assert "do not match the request hash" in json.loads(outer)["error"]
