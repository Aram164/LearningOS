"""Library reconciliation: every old occurrence gets exactly one disposition.

Synthetic umbrellas only. The real workspace is checked with
``tools/library_reconciliation.py check --report``, never by the suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import library_reconciliation as lr
import pytest
import yaml

WS = "work/active/workspace-test-reconciliation"
PLAN = "repository/work/active/workspace-plan/inputs/plan.md"
CATALOG = "repository/curriculum/quarantine/masters-planning/catalog.yaml"

LIST_MD = """\
# Learning resources

| Tag | Meaning |
|---|---|
| 📘 | book legend row, not a resource |

## Books

- **Alpha Book** — [landing](https://alpha.example/book/) · [chapter 2](https://alpha.example/book/ch2#top)
- Local copy `Plans/Math/alpha.pdf` and the plan `Plans/notes/plan.md`
- Already registered: `source-alpha`
- **Beta Notes** (no link yet)
- Module page: https://moseskonto.tu-berlin.de/moses/anzeigen.html?nummer=1
- Folder readme `README.md`
"""

PLAN_MD = """\
# Plan

Read [Alpha](https://www.alpha.example/book) first, then `source-alpha` chapter 3.
"""

DECLARED = {
    "schema": lr.INPUTS_SCHEMA,
    "base": "umbrella",
    "origins": [
        {"key": "lr", "path": "legacy/LIST.md", "kind": "resource-list", "scope": "active",
         "entries": True, "skip_table_headers": ["Tag"]},
        {"key": "ws-plan", "path": PLAN, "kind": "plan-input", "scope": "active",
         "entries": False},
    ],
    "targets": {
        "registry": {"directory": "repository/sources/registry", "files": ["core.yaml"]},
        "collections": {"directory": "repository/sources/collections",
                        "files": ["shelf.yaml"]},
        "masters_collections": [],
        "masters_catalog": CATALOG,
        "materials_manifest": "repository/records/materials-manifest.yaml",
        "materials_placement": "repository/tools/build_materials_tree.py",
    },
    "resolvers": {"path_map": "repository/migration/path-map.csv"},
    "identical_copies": [{"path": "legacy/copy/LIST.md", "same_as": "lr"}],
    "not_declared": [{"path": "legacy/Other/", "reason": "outside this pass"}],
}

REGISTRY = {"sources": [{
    "id": "source-alpha", "title": "Alpha Book", "type": "book",
    "url": "https://www.alpha.example/book",
    "identifiers": {"mirror": "https://mirror.example/alpha"},
}]}

MANUAL = """\
schema: library-reconciliation-dispositions/v1
objects:
- id: source-alpha
  kind: existing-active-source
  occurrences:
  - {ref: 'lr:9:u2', role: child, title: Chapter 2}
- id: candidate-source-beta-notes
  kind: new-masters-candidate
  title: Beta Notes
  occurrences: ['lr:12:e1']
- id: out-of-scope:folder-readme
  kind: out-of-scope
  reason: A folder's own readme, not a teaching object
  occurrences: ['lr:14:p1']
"""


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build(tmp_path: Path) -> Path:
    """A minimal umbrella (legacy/ beside repository/); returns the repository root."""
    umbrella = tmp_path / "umbrella"
    root = umbrella / "repository"
    _write(umbrella / "legacy/LIST.md", LIST_MD)
    _write(umbrella / "legacy/copy/LIST.md", LIST_MD)
    _write(umbrella / PLAN, PLAN_MD)
    _write(root / "sources/registry/core.yaml", yaml.safe_dump(REGISTRY, sort_keys=False))
    _write(root / "sources/collections/shelf.yaml",
           yaml.safe_dump({"entries": [{"source": "source-alpha"}]}))
    _write(root / "records/materials-manifest.yaml",
           yaml.safe_dump({"files": {"mathematics/alpha/alpha.pdf": {"size": 10}}}))
    _write(root / "tools/build_materials_tree.py", 'PLACEMENT = {"alpha": "mathematics"}\n')
    _write(root / "migration/path-map.csv",
           "old_path,new_path,type,decided_in_phase\n"
           "Plans/notes/plan.md,knowledge/notes/note-plan.md,note,pilot\n"
           "Plans/Other/README.md,knowledge/notes/note-other.md,note,pilot\n")
    _write(root / WS / lr.DECLARED_INPUTS, yaml.safe_dump(DECLARED, sort_keys=False))
    return root


def run(root: Path, command: str, *rest: str) -> int:
    return lr.main(["--root", str(root), command, "--workspace", WS, *rest])


def declared(root: Path) -> lr.Declared:
    return lr.load_declared(root / WS, root.parent)


def evaluate(root: Path, text: str) -> lr.Result:
    return lr.evaluate(declared(root), lr.parse_dispositions(yaml.safe_load(text), "test"))[0]


def review(root: Path, tmp_path: Path) -> None:
    """suggest -> manual decisions -> merge -> freeze -> report, as the workspace did."""
    auto, worklist = tmp_path / "auto.yaml", tmp_path / "worklist.md"
    manual = _write(tmp_path / "manual.yaml", MANUAL)
    assert run(root, "suggest", "--out", str(auto), "--worklist", str(worklist)) == 0
    assert run(root, "merge", str(auto), str(manual)) == 0
    assert run(root, "freeze") == 0
    assert run(root, "report") == 0


def test_extraction_gives_every_locator_a_stable_ref(tmp_path):
    root = build(tmp_path)
    occurrences, stats = lr.extract_all(declared(root))
    assert {o.ref: (o.kind, o.locator) for o in occurrences} == {
        "lr:9:u1": ("url", "https://alpha.example/book/"),
        "lr:9:u2": ("url", "https://alpha.example/book/ch2#top"),
        "lr:10:p1": ("path", "Plans/Math/alpha.pdf"),
        "lr:10:p2": ("path", "Plans/notes/plan.md"),
        "lr:11:s1": ("source-ref", "source-alpha"),
        "lr:12:e1": ("entry", "Beta Notes"),
        "lr:13:u1": ("url", "https://moseskonto.tu-berlin.de/moses/anzeigen.html?nummer=1"),
        "lr:14:p1": ("path", "README.md"),
        "ws-plan:3:u1": ("url", "https://www.alpha.example/book"),
        "ws-plan:3:s1": ("source-ref", "source-alpha"),
    }
    # The legend table is not a resource list; a plan input yields no entries.
    assert stats["lr"]["skipped_table_rows"] == 1
    assert stats["lr"]["resource_lines"] == 6
    by_ref = {o.ref: o for o in occurrences}
    assert by_ref["lr:9:u2"].normalized == "alpha.example/book/ch2"
    assert by_ref["ws-plan:3:u1"].normalized == by_ref["lr:9:u1"].normalized


def test_url_normalization_folds_host_and_slash_but_keeps_the_query():
    assert lr.normalize_url("HTTPS://WWW.Example.org/a/b/?x=1#frag") == "example.org/a/b?x=1"
    assert lr.normalize_url("http://example.org/") == "example.org"


def test_an_empty_review_leaves_every_occurrence_undispositioned(tmp_path, capsys):
    root = build(tmp_path)
    assert run(root, "check", "--json") == 1
    summary = json.loads(capsys.readouterr().out)
    assert (summary["occurrences"], summary["dispositioned"]) == (10, 0)
    assert [f["code"] for f in summary["findings"]] == ["UNDISPOSITIONED"] * 10
    assert len(summary["stale_inputs"]) == len(declared(root).hashed_files())


def test_freeze_refuses_while_findings_remain(tmp_path, capsys):
    root = build(tmp_path)
    assert run(root, "freeze") == 1
    assert "refusing to freeze" in capsys.readouterr().out
    assert not (root / WS / lr.DISPOSITIONS_FILE).exists()


def test_freeze_records_the_hashes_and_changes_nothing_else(tmp_path):
    root = build(tmp_path)
    auto, worklist = tmp_path / "auto.yaml", tmp_path / "worklist.md"
    manual = _write(tmp_path / "manual.yaml", MANUAL)
    assert run(root, "suggest", "--out", str(auto), "--worklist", str(worklist)) == 0
    assert run(root, "merge", str(auto), str(manual)) == 0
    target = root / WS / lr.DISPOSITIONS_FILE
    before = lr.load_dispositions(target)
    assert run(root, "freeze") == 0
    after = lr.load_dispositions(target)
    assert after.objects == before.objects  # omitted roles stay omitted
    assert set(after.reviewed_input_hashes) == {p for _, p in declared(root).hashed_files()}


def test_suggest_takes_only_mechanical_matches(tmp_path):
    root = build(tmp_path)
    auto, worklist = tmp_path / "auto.yaml", tmp_path / "worklist.md"
    assert run(root, "suggest", "--out", str(auto), "--worklist", str(worklist)) == 0
    suggested = lr.parse_dispositions(yaml.safe_load(auto.read_text(encoding="utf-8")), "auto")
    assert {c.ref: (o.id, c.role, c.basis)
            for o in suggested.objects for c in o.occurrences} == {
        "lr:9:u1": ("source-alpha", "landing", "exact-url"),
        "lr:10:p1": ("source-alpha", "local", "manifest-basename"),
        "lr:10:p2": ("out-of-scope:internal-document", "", "path-map"),
        "lr:11:s1": ("source-alpha", "reference", "source-id"),
        "lr:13:u1": ("out-of-scope:module-descriptor", "", "moses-host"),
        "ws-plan:3:u1": ("source-alpha", "landing", "exact-url"),
        "ws-plan:3:s1": ("source-alpha", "reference", "source-id"),
    }
    # A child page, a bare entry and a generic README (never matched by basename)
    # are left for a person.
    left = worklist.read_text(encoding="utf-8")
    assert all(ref in left for ref in ("lr:9:u2", "lr:12:e1", "lr:14:p1"))
    assert "](" not in left  # echoed lines carry no live (possibly broken) links


def test_a_complete_review_is_fresh_and_its_report_current(tmp_path, capsys):
    root = build(tmp_path)
    review(root, tmp_path)
    capsys.readouterr()
    assert run(root, "check", "--report", "--json") == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["ok"] and summary["report"] == "current"
    assert summary["by_disposition"] == {
        "existing-active-source": 6, "new-masters-candidate": 1, "out-of-scope": 3}
    frozen = lr.load_dispositions(root / WS / lr.DISPOSITIONS_FILE).reviewed_input_hashes
    assert frozen[CATALOG] == "absent"
    report = (root / WS / lr.REPORT_FILE).read_text(encoding="utf-8")
    assert "### Links not yet stored on their record (1)" in report
    assert "| `source-alpha` | child | `lr:9:u2` |" in report


def test_applied_check_preserves_review_and_detects_missing_target_evidence(tmp_path, capsys):
    root = build(tmp_path)
    review(root, tmp_path)
    registry = root / "sources/registry/core.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["sources"][0]["identifiers"]["chapter-2"] = "https://alpha.example/book/ch2#top"
    _write(registry, yaml.safe_dump(data, sort_keys=False))
    catalog = root.parent / CATALOG
    _write(catalog, yaml.safe_dump({"candidate_sources": [{
        "id": "candidate-source-beta-notes", "title": "Beta Notes",
        "provenance": ["legacy/LIST.md#L12"],
    }]}, sort_keys=False))
    capsys.readouterr()
    assert run(root, "check", "--report") == 1  # frozen pre-intake review remains intact
    assert run(root, "check", "--applied") == 0
    assert run(root, "report", "--applied") == 0
    assert run(root, "check", "--applied", "--report") == 0
    applied = json.loads((root / WS / lr.APPLIED_REPORT_FILE).read_text(encoding="utf-8"))
    assert applied["dispositioned"] == 10 and applied["new_masters_candidates"] == 1

    decisions = root / WS / lr.DISPOSITIONS_FILE
    reviewed_bytes = decisions.read_text(encoding="utf-8")
    _write(decisions, reviewed_bytes + "# changed after final proof\n")
    assert run(root, "check", "--applied") == 0
    assert run(root, "check", "--applied", "--report") == 1
    _write(decisions, reviewed_bytes)

    catalog_data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
    catalog_data["candidate_sources"][0]["provenance"] = []
    _write(catalog, yaml.safe_dump(catalog_data, sort_keys=False))
    assert run(root, "check", "--applied") == 1
    assert run(root, "check", "--applied", "--report") == 1


@pytest.mark.parametrize("relative", [
    PLAN,                                     # an origin
    "repository/sources/registry/core.yaml",  # a target the dispositions rely on
    CATALOG,                                  # absent at review time, created later
])
def test_changed_input_bytes_make_the_review_stale(tmp_path, capsys, relative):
    root = build(tmp_path)
    review(root, tmp_path)
    target = root.parent / relative
    before = target.read_text(encoding="utf-8") if target.exists() else ""
    _write(target, before + "\n# edited\n")
    capsys.readouterr()
    assert run(root, "check", "--json") == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["findings"] == [] and summary["stale_inputs"] == [relative]


def test_a_report_that_no_longer_matches_its_inputs_fails_the_check(tmp_path, capsys):
    root = build(tmp_path)
    review(root, tmp_path)
    retitle = _write(tmp_path / "retitle.yaml",
                     MANUAL.replace("title: Beta Notes", "title: Beta Lecture Notes"))
    assert run(root, "merge", str(retitle)) == 0
    capsys.readouterr()
    assert run(root, "check") == 0
    assert run(root, "check", "--report") == 1
    assert "report outdated" in capsys.readouterr().out


def test_an_undeclared_partition_and_a_drifted_copy_are_findings(tmp_path):
    root = build(tmp_path)
    _write(root / "sources/registry/extra.yaml", "sources: []\n")
    _write(root.parent / "legacy/copy/LIST.md", LIST_MD + "- drifted\n")
    found = lr.evaluate(declared(root), lr.Dispositions({}, []))[0].findings
    assert any(f.code == "LISTING" and "extra.yaml" in f.detail for f in found)
    assert any(f.code == "IDENTICAL-COPY" and "legacy/copy/LIST.md" in f.detail for f in found)


def test_one_occurrence_has_one_disposition_unless_same_kind_objects_share_a_mention(tmp_path):
    root = build(tmp_path)
    result = evaluate(root, """
objects:
- {id: source-alpha, kind: existing-active-source,
   occurrences: [{ref: 'lr:9:u1'}, {ref: 'lr:9:u2', role: alias}]}
- {id: candidate-source-alpha-site, kind: new-masters-candidate, title: Alpha site,
   occurrences: [{ref: 'lr:9:u1'}, {ref: 'lr:12:e1'}]}
- {id: candidate-source-beta-notes, kind: new-masters-candidate, title: Beta Notes,
   occurrences: [{ref: 'lr:12:e1'}]}
""")
    assert [f.detail for f in result.findings if f.code == "CONFLICT"] == [
        "lr:9:u1 claimed by source-alpha, candidate-source-alpha-site"]
    assert result.disposition["lr:12:e1"] == "new-masters-candidate"
    assert result.disposition["lr:9:u2"] == "alias-or-duplicate"
    mixed = evaluate(root, """
objects:
- {id: source-alpha, kind: existing-active-source, occurrences: ['lr:12:e1']}
- {id: candidate-source-beta-notes, kind: new-masters-candidate, title: Beta Notes,
   occurrences: ['lr:12:e1']}
""")
    assert any(f.code == "CONFLICT" and f.detail.startswith("lr:12:e1") for f in mixed.findings)


def test_targets_and_roles_must_agree_with_the_registry(tmp_path):
    root = build(tmp_path)
    result = evaluate(root, """
objects:
- {id: source-unknown, kind: existing-active-source, occurrences: [{ref: 'lr:9:u1', role: local}]}
- {id: source-alpha, kind: new-active-source, title: Alpha, type: book, occurrences: []}
- {id: source-gamma, kind: new-active-source, title: Gamma, occurrences: []}
- {id: candidate-source-beta, kind: existing-masters-candidate, occurrences: []}
- {id: 'unresolved:thing', kind: out-of-scope, occurrences: [{ref: 'lr:9:u2', role: alias}]}
- {id: source-alpha, kind: existing-active-source, shelf: machine-learning,
   occurrences: ['lr:99:u1'], extra_mentions: ['lr:999']}
- {id: whatever, kind: maybe, occurrences: []}
""")
    assert {(f.code, f.detail) for f in result.findings if f.code != "UNDISPOSITIONED"} == {
        ("TARGET", "source-unknown: not in the source registry"),
        ("ROLE", "lr:9:u1: role 'local' not allowed for a url"),
        ("TARGET", "source-alpha: already registered (existing)"),
        ("TARGET", "source-gamma: new source needs title and type"),
        ("TARGET", "candidate-source-beta: not in the Master's catalogue"),
        ("TARGET", "unresolved:thing: must be 'out-of-scope:<slug>'"),
        ("TARGET", "unresolved:thing: needs a reason"),
        ("ROLE", "lr:9:u2: alias needs a real object"),
        ("DUPLICATE-OBJECT", "source-alpha"),
        ("TARGET", "source-alpha: shelf 'machine-learning' is not a group id"),
        ("UNKNOWN-REF", "source-alpha: lr:99:u1"),
        ("UNKNOWN-REF", "source-alpha: extra mention lr:999"),
        ("KIND", "whatever: unknown kind 'maybe'"),
    }


def test_merge_lets_a_later_file_win_each_ref_it_claims():
    def parse(text: str) -> lr.Dispositions:
        return lr.parse_dispositions(yaml.safe_load(text), "test")

    base = parse("objects:\n- {id: source-alpha, kind: existing-active-source,"
                 " occurrences: ['lr:9:u1', 'lr:9:u2']}\n")
    later = parse("objects:\n- {id: candidate-source-alpha-ch2, kind: new-masters-candidate,"
                  " title: Alpha ch2, occurrences: ['lr:9:u2']}\n")
    merged = lr.merge_dispositions(base, [later])
    assert {o.id: [c.ref for c in o.occurrences] for o in merged.objects} == {
        "source-alpha": ["lr:9:u1"], "candidate-source-alpha-ch2": ["lr:9:u2"]}
    clash = parse("objects:\n- {id: source-alpha, kind: new-active-source, occurrences: []}\n")
    with pytest.raises(lr.ReconciliationError, match="conflicts"):
        lr.merge_dispositions(base, [clash])


def test_rendered_dispositions_are_deterministic_and_round_trip():
    order = {"lr": 0, "ws-plan": 1}
    original = lr.parse_dispositions(yaml.safe_load(MANUAL), "manual")
    text = lr.render_dispositions(original, order)
    again = lr.parse_dispositions(yaml.safe_load(text), "rendered")
    assert again == original
    assert lr.render_dispositions(again, order) == text
    lonely = lr.DispositionObject(id="out-of-scope:none", kind="out-of-scope", reason="r")
    assert "  occurrences: []" in lr.render_dispositions(lr.Dispositions({}, [lonely]), order)


def test_declared_paths_and_workspaces_stay_inside_their_roots(tmp_path, capsys):
    root = build(tmp_path)
    assert lr.main(["--root", str(root), "check", "--workspace", "../elsewhere"]) == 2
    assert "workspace must be a directory inside" in capsys.readouterr().err
    climbing = dict(DECLARED, origins=[dict(DECLARED["origins"][0], path="../outside.md")])
    _write(root / WS / lr.DECLARED_INPUTS, yaml.safe_dump(climbing, sort_keys=False))
    with pytest.raises(lr.ReconciliationError, match="must not climb"):
        declared(root)
