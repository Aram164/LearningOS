"""Structured material inventory: observed bytes reconciled with rows.

A coverage audit may carry a fenced inventory-v1 block: explicitly scoped
material roots plus disposition rows. The preflight enumerates exactly
those roots and refuses missing rows, unobserved rows, digest drift, and
undeclared duplicate bytes. The check report binds the observed set; a
reviewed apply re-verifies it and refuses moved material. Audits without
the block keep the legacy marker + boolean path.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from repo_builders import (
    _compact_revision,
    _compact_setup,
    run_los,
    write_yaml,
)

AUDIT_REL = "work/active/workspace-demo/outputs/demo-coverage-audit.md"

ANGLE_CHANGES = {"update": [{
    "route_id": "route-demo-book",
    "fields": {"angle": "A sharper lecture-specific angle."}}]}


def _seed_materials(root: Path) -> dict[str, str]:
    base = root.parent / "materials" / "inventory-demo"
    files = {"deck.pdf": b"%PDF deck\n", "notes.txt": b"lecture notes\n"}
    digests = {}
    for name, data in files.items():
        target = base / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digests[f"inventory-demo/{name}"] = hashlib.sha256(data).hexdigest()
    return digests


def _write_audit(root: Path, block: str | None) -> None:
    text = ("# Complete demo coverage audit\n\n## Local inventory\n\nDone.\n\n"
            "## Linked inventory\n\nDone.\n\n## Completeness sign-off\n\nDone.\n")
    if block is not None:
        text += f"\n```inventory-v1\n{block}\n```\n"
    (root / AUDIT_REL).write_text(text, encoding="utf-8")


def _block(digests: dict[str, str], extra: str = "") -> str:
    rows = "".join(
        f'  - {{path: "{path}", sha256: "{digest}", disposition: routed}}\n'
        for path, digest in sorted(digests.items()))
    return ('roots: ["inventory-demo"]\nrows:\n' + rows + extra)


def _revision_file(root: Path, tmp_path: Path) -> Path:
    revision_file = tmp_path / "revision.yaml"
    write_yaml(revision_file, _compact_revision(
        root, route_changes=ANGLE_CHANGES))
    return revision_file


def _check(root: Path, revision_file: Path):
    return run_los(root, "unit-plan-revise", "unit-demo-l01",
                   "--file", str(revision_file), "--check")


def test_structured_inventory_binds_and_applies(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    digests = _seed_materials(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path)
    _write_audit(mini_repo, _block(digests, extra=(
        '  - {kind: linked, disposition: linked, '
        'reference: "https://example.edu/lecture", '
        'observed: "checked 2026-09-21"}\n')))
    checked = _check(mini_repo, revision_file)
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    binding = report["observed_material"]
    assert binding["sha256"].startswith("sha256:")
    assert binding["roots"] == ["inventory-demo"]
    assert binding["local_files"] == 2
    assert binding["rows"] == 3
    view = report["inventory_view"]
    assert [row["path"] for row in view["local"]] == sorted(digests)
    assert view["linked"][0]["reference"] == "https://example.edu/lecture"
    report_file = tmp_path / "review.json"
    report_file.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"],
                      "--review-report", str(report_file))
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)["ok"] is True


def test_missing_row_fails_check(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    digests = _seed_materials(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path)
    (mini_repo.parent / "materials" / "inventory-demo" / "extra.pdf").write_bytes(b"x\n")
    _write_audit(mini_repo, _block(digests))
    checked = _check(mini_repo, revision_file)
    assert checked.returncode == 2
    assert "lacks a row for observed file: inventory-demo/extra.pdf" in checked.stderr


def test_duplicate_bytes_need_a_duplicate_disposition(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    digests = _seed_materials(mini_repo)
    twin = mini_repo.parent / "materials" / "inventory-demo" / "twin.txt"
    twin.write_bytes(b"lecture notes\n")
    twin_digest = digests["inventory-demo/notes.txt"]
    revision_file = _revision_file(mini_repo, tmp_path)
    both_routed = _block({**digests, "inventory-demo/twin.txt": twin_digest})
    _write_audit(mini_repo, both_routed)
    checked = _check(mini_repo, revision_file)
    assert checked.returncode == 2
    assert "duplicate bytes need exactly one canonical row" in checked.stderr
    twin_row = ('  - {path: "inventory-demo/twin.txt", sha256: "' + twin_digest
                + '", disposition: routed}\n')
    twin_dup = ('  - {path: "inventory-demo/twin.txt", sha256: "' + twin_digest
                + '", disposition: duplicate, '
                'duplicate_of: "inventory-demo/notes.txt"}\n')
    declared = both_routed.replace(twin_row, twin_dup)
    _write_audit(mini_repo, declared)
    checked = _check(mini_repo, revision_file)
    assert checked.returncode == 0, checked.stderr


def test_changed_material_refuses_reviewed_apply(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    digests = _seed_materials(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path)
    _write_audit(mini_repo, _block(digests))
    checked = _check(mini_repo, revision_file)
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    report_file = tmp_path / "review.json"
    report_file.write_text(checked.stdout, encoding="utf-8")
    (mini_repo.parent / "materials" / "inventory-demo" / "deck.pdf").write_bytes(
        b"%PDF deck, revised\n")
    # Bytes moved under stale rows: the contract gate refuses the apply.
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"],
                      "--review-report", str(report_file))
    assert applied.returncode == 2
    assert "inventory digest differs from observed bytes" in applied.stderr
    from learning_os.loader import load_repo
    live_map = load_repo(mini_repo).module_source_maps["module-demo"]
    row = next(r for s in live_map["sources"] for r in s["unit_routes"]
               if r.get("id") == "route-demo-book")
    assert row["angle"] == "A synthetic angle."
    # Rows re-observed but report still old: the binding refuses the apply.
    new_digest = hashlib.sha256(b"%PDF deck, revised\n").hexdigest()
    _write_audit(mini_repo, _block({**digests,
                                   "inventory-demo/deck.pdf": new_digest}))
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"],
                      "--review-report", str(report_file))
    assert applied.returncode == 2
    assert "relevant material changed since --check" in applied.stderr
    # A fresh preflight on current bytes re-opens the round trip.
    rechecked = _check(mini_repo, revision_file)
    assert rechecked.returncode == 0, rechecked.stderr
    fresh = json.loads(rechecked.stdout)
    assert fresh["observed_material"]["sha256"] != report["observed_material"]["sha256"]
    report_file.write_text(rechecked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", fresh["reviewed_file_sha256"],
                      "--review-report", str(report_file))
    assert applied.returncode == 0, applied.stderr


def test_legacy_audit_without_block_skips_binding(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path)
    checked = _check(mini_repo, revision_file)
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert "observed_material" not in report
    assert "inventory_view" not in report


def test_inventory_rows_cannot_impersonate_or_escape(mini_repo, tmp_path):
    _compact_setup(mini_repo)
    digests = _seed_materials(mini_repo)
    revision_file = _revision_file(mini_repo, tmp_path)
    deck = digests["inventory-demo/deck.pdf"]
    linked_row = ('  - {kind: linked, disposition: linked, '
                  'reference: "https://x", sha256: "' + deck + '"}\n')
    deck_row = ('  - {path: "inventory-demo/deck.pdf", sha256: "' + deck
                + '", disposition: routed}\n')
    cases = [
        ('roots: ["inventory-demo"]\nrows:\n' + deck_row + linked_row,
         "would impersonate observed bytes"),
        ('roots: ["inventory-demo"]\nrows:\n'
         '  - {path: "../outside.pdf", sha256: "%s", disposition: routed}\n' % ("0" * 64),
         "escapes the materials tree"),
        ('roots: ["inventory-demo"]\nrows:\n'
         '  - {path: "source-demo-book/lecture-01.pdf", sha256: "%s", '
         "disposition: routed}\n" % ("0" * 64),
         "outside the declared roots"),
    ]
    for block, message in cases:
        _write_audit(mini_repo, block)
        checked = _check(mini_repo, revision_file)
        assert checked.returncode == 2, block
        assert message in checked.stderr, block
