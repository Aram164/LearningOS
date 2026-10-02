"""Validator unit tests against the synthetic minimal repo + the real repository."""

from __future__ import annotations

import textwrap

import pytest
import yaml

from learning_os.loader import load_repo
from learning_os.rules import validate
from learning_os.rules.references import classify_markdown_link, parse_reference_uri


def codes(issues, severity=None):
    return [i.code for i in issues if severity is None or i.severity == severity]


def run(root):
    return validate(load_repo(root))


# ---------------------------------------------------------------- clean base
def test_mini_repo_is_clean(mini_repo):
    issues = run(mini_repo)
    assert codes(issues, "E") == [], [str(i) for i in issues]


_SHAPE_CASES = [
    # (file, field, malformed value): each crashed validate with a raw
    # TypeError/AttributeError naming no file before Validator.run contained
    # crashes on schema-invalid input.
    ("curriculum/modules/module-demo/module.yaml", "unit_order", [{"id": "unit-demo-l01"}]),
    ("curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml", "stages", "not-a-list"),
    ("work/active/workspace-demo/CONTEXT.md", "unit_ids", [{"id": "unit-demo-l01"}]),
    ("knowledge/notes/mathematics/note-demo.md", "concepts", [{"id": "concept-variance"}]),
]


@pytest.mark.parametrize(("rel", "field", "malformed"), _SHAPE_CASES)
def test_schema_invalid_record_is_a_named_error_not_a_crash(mini_repo, rel, field, malformed):
    """A record that fails its schema is reported by file, and a pass that
    reads records in their schema shape and crashes on it becomes one error
    naming that file (synthetic authoring campaign D2, whose unit-only repair
    left the same crash in every sibling record)."""
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    path = mini_repo / rel
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        _, front, body = text.split("---\n", 2)
        meta = yaml.safe_load(front)
        meta[field] = malformed
        path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n" + body,
                        encoding="utf-8")
    else:
        data = yaml.safe_load(text)
        data[field] = malformed
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    errors = [i for i in run(mini_repo) if i.severity == "E"]

    assert any(i.code == "SCHEMA" and i.path == rel for i in errors), [str(i) for i in errors]
    stopped = [i for i in errors if i.code == "SCHEMA-DEPENDENT"]
    assert all(rel in i.message for i in stopped), [str(i) for i in errors]


@pytest.mark.parametrize(("rel", "slot", "reference_code"), [
    ("curriculum/modules/module-demo/module.yaml", ("unit_order",), "REF-UNIT"),
    ("curriculum/modules/module-demo/source-map.yaml", ("sources", 0, "unit_routes"), "REF-UNIT"),
    ("projects/registry/project-demo.yaml", ("linked_module_ids",), "REF-MODULE"),
    ("work/active/workspace-demo/CONTEXT.md", ("unit_ids",), "REF-UNIT"),
    ("knowledge/notes/mathematics/note-demo.md", ("sources",), "REF-SOURCE"),
])
def test_scalar_id_list_is_schema_error_without_character_references(
    mini_repo, rel, slot, reference_code,
):
    from repo_builders import add_curriculum, add_manifest_fixtures

    add_curriculum(mini_repo)
    if rel.startswith("projects/"):
        add_manifest_fixtures(mini_repo)
    path = mini_repo / rel
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        _, front, body = text.split("---\n", 2)
        data = yaml.safe_load(front)
    else:
        data = yaml.safe_load(text)
    target = data
    for part in slot[:-1]:
        target = target[part]
    target[slot[-1]] = "not-a-list"
    if path.suffix == ".md":
        path.write_text("---\n" + yaml.safe_dump(data, sort_keys=False) + "---\n" + body,
                        encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    errors = [i for i in run(mini_repo) if i.severity == "E"]
    assert any(i.code == "SCHEMA" and i.path == rel for i in errors), errors
    assert not any(i.code == reference_code and i.path == rel for i in errors), errors


def test_schema_error_in_a_registry_partition_names_that_partition(mini_repo):
    """A partitioned registry is schema-checked as one merged document; the
    error must still name the partition file that holds the bad record, or the
    schema gate's SCHEMA-DEPENDENT message sends the operator to the wrong file."""
    partition = mini_repo / "sources" / "registry" / "extra.yaml"
    partition.parent.mkdir(parents=True)
    partition.write_text(yaml.safe_dump({"sources": [
        {"id": "source-extra-book", "title": "Extra Book", "type": "book",
         "authors": ["B. Author", {"name": "C. Author"}]},
    ]}), encoding="utf-8")

    schema = [i for i in run(mini_repo) if i.severity == "E" and i.code == "SCHEMA"]

    assert schema and all(i.path == "sources/registry/extra.yaml" for i in schema), \
        [str(i) for i in schema]


def test_a_crash_on_schema_valid_input_stays_loud(mini_repo, monkeypatch):
    """The schema gate contains only crashes on input already reported as
    schema-invalid; anywhere else a crash is a validator defect."""
    from learning_os.rules.core import Validator

    def broken(self):
        raise TypeError("defect in a validation pass")

    monkeypatch.setattr(Validator, "check_links", broken)
    with pytest.raises(TypeError, match="defect in a validation pass"):
        run(mini_repo)


def test_living_docs_cannot_copy_a_manifest_version(mini_repo):
    readme = mini_repo / "README.md"
    readme.write_text(
        "Read manifest v99 and hope this prose changes when the producer does.\n",
        encoding="utf-8",
    )
    assert "CONTRACT-DOC-STATIC-VERSION" in codes(run(mini_repo), "E")


@pytest.mark.full_repo
def test_real_repository_has_no_errors(real_issues):
    issues = real_issues
    errors = [str(i) for i in issues if i.severity == "E"]
    assert errors == [], errors


@pytest.mark.parametrize(
    ("value", "scheme", "target"),
    [
        ("note://note-demo", "note", "note-demo"),
        ("material://source-demo-book/chapter.pdf", "material",
         "source-demo-book/chapter.pdf"),
        ("https://example.com/path", "https", "example.com/path"),
    ],
)
def test_reference_uri_parsing_is_independent_of_repository_state(
    value, scheme, target
):
    parsed = parse_reference_uri(value)
    assert parsed is not None
    assert (parsed.scheme, parsed.target) == (scheme, target)


@pytest.mark.parametrize(
    ("value", "kind", "resolved_target"),
    [
        ("#section", "skip", "#section"),
        ("mailto:reader@example.com", "skip", "mailto:reader@example.com"),
        ("note://note-demo", "uri", "note://note-demo"),
        ("../notes/note-demo.md#proof", "relative", "../notes/note-demo.md"),
    ],
)
def test_markdown_link_classification_has_a_pure_testable_seam(
    value, kind, resolved_target
):
    classified = classify_markdown_link(value)
    assert (classified.kind, classified.target) == (kind, resolved_target)


# ------------------------------------------------------------------ identity
def test_bad_id_pattern_rejected(mini_repo):
    f = mini_repo / "knowledge" / "concepts.yaml"
    data = yaml.safe_load(f.read_text())
    data["concepts"].append({"id": "concept-Bad_ID", "label": "Bad"})
    f.write_text(yaml.safe_dump(data))
    assert "ID-PATTERN" in codes(run(mini_repo), "E")


def test_gratuitous_suffix_warns(mini_repo):
    f = mini_repo / "knowledge" / "concepts.yaml"
    data = yaml.safe_load(f.read_text())
    data["concepts"].append({"id": "concept-orphan-02", "label": "Orphan"})
    f.write_text(yaml.safe_dump(data))
    assert "ID-SUFFIX" in codes(run(mini_repo), "W")


# ---------------------------------------------------------------- references
def test_unresolved_note_concept_is_error(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text().replace("concept-expected-value", "concept-ghost"))
    assert "REF-CONCEPT" in codes(run(mini_repo), "E")


def test_relation_related_to_rejected(mini_repo):
    f = mini_repo / "knowledge" / "concept-relations.yaml"
    data = yaml.safe_load(f.read_text())
    data["relations"].append({"from": "concept-variance", "type": "related-to",
                              "to": "concept-expected-value"})
    f.write_text(yaml.safe_dump(data))
    issues = codes(run(mini_repo), "E")
    assert "REL-TYPE" in issues or "SCHEMA" in issues


def test_duplicate_relation_edge_is_error(mini_repo):
    f = mini_repo / "knowledge" / "concept-relations.yaml"
    data = yaml.safe_load(f.read_text())
    data["relations"].append(dict(data["relations"][0]))
    f.write_text(yaml.safe_dump(data))
    assert "REL-DUP" in codes(run(mini_repo), "E")


def _receipt(path, transaction_id, key):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({
        "id": transaction_id,
        "request": {"idempotency_key": key},
    }), encoding="utf-8")


def test_duplicate_idempotency_key_across_receipts_is_error(mini_repo):
    """Ledger loss + key reuse commits twice; the pair must be loud (JF-13)."""
    directory = mini_repo / "operations/transactions"
    _receipt(directory / "transaction-20260101-000000-001.yaml",
             "transaction-20260101-000000-001", "shared-key")
    _receipt(directory / "transaction-20260101-000001-001.yaml",
             "transaction-20260101-000001-001", "shared-key")
    messages = [str(i) for i in run(mini_repo) if i.severity == "E"]
    assert any("duplicate idempotency key 'shared-key'" in m for m in messages), messages
    _receipt(directory / "transaction-20260101-000001-001.yaml",
             "transaction-20260101-000001-001", "other-key")
    messages = [str(i) for i in run(mini_repo) if i.severity == "E"]
    assert not any("duplicate idempotency key" in m for m in messages), messages


def test_unreadable_idempotency_ledger_is_error_but_missing_is_fine(mini_repo):
    """Commit fails closed on a corrupt ledger; validate must say so (JF-13)."""
    ledger = mini_repo / "operations/transactions/idempotency.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("entries: [unclosed\n", encoding="utf-8")
    assert "TRANSACTION-IDEMPOTENCY" in codes(run(mini_repo), "E")
    ledger.unlink()
    assert "TRANSACTION-IDEMPOTENCY" not in codes(run(mini_repo), "E")


def _relations(mini_repo, rows):
    """Replace the relation registry with exactly ``rows``."""
    f = mini_repo / "knowledge" / "concept-relations.yaml"
    f.write_text(yaml.safe_dump({"relations": rows}))
    return f


def test_the_mini_repo_prerequisite_graph_is_acyclic(mini_repo):
    assert "REL-PREREQ-CYCLE" not in codes(run(mini_repo), "E")


def test_a_two_node_prerequisite_cycle_is_error(mini_repo):
    _relations(mini_repo, [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "requires", "to": "concept-variance"},
    ])
    issues = run(mini_repo)
    assert "REL-PREREQ-CYCLE" in codes(issues, "E")


def test_the_reported_cycle_is_stable_across_runs(mini_repo):
    """A cycle error that names a different path each run is one nobody can act
    on, so the walk is sorted and the first cycle found is the one reported."""
    _relations(mini_repo, [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "requires", "to": "concept-variance"},
    ])
    messages = {
        next(i.message for i in run(mini_repo) if i.code == "REL-PREREQ-CYCLE")
        for _ in range(3)
    }
    assert len(messages) == 1
    assert "->" in messages.pop()


def test_a_self_edge_is_reported_as_self_not_as_a_cycle(mini_repo):
    """REL-SELF already owns this case; the cycle rule must not double-report."""
    _relations(mini_repo, [
        {"from": "concept-variance", "type": "requires", "to": "concept-variance"},
    ])
    issues = codes(run(mini_repo), "E")
    assert "REL-SELF" in issues


def test_a_semantic_cycle_is_allowed(mini_repo):
    """Two concepts may motivate each other. Only the strict subgraph is an
    order, and only an order can be violated by a cycle."""
    _relations(mini_repo, [
        {"from": "concept-variance", "type": "motivates", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"},
    ])
    assert "REL-PREREQ-CYCLE" not in codes(run(mini_repo), "E")


def test_a_semantic_edge_does_not_close_a_strict_cycle(mini_repo):
    """The layers do not mix: a semantic edge back to a prerequisite is context,
    never a contradiction of the order."""
    _relations(mini_repo, [
        {"from": "concept-variance", "type": "requires", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "applies-in", "to": "concept-variance"},
    ])
    assert "REL-PREREQ-CYCLE" not in codes(run(mini_repo), "E")


# ----------------------------------------------------------------- ownership
def test_exam_date_duplication_in_coordination_is_error(mini_repo):
    f = mini_repo / "work" / "COORDINATION.md"
    f.write_text(f.read_text().replace(
        "- Demo module deferred to 2. Termin (date lives in records/modules.yaml)",
        "- Demo module deferred to 2. Termin on 2026-10-09"))
    assert "COORD-EXAM-DATE" in codes(run(mini_repo), "E")


def test_generated_reference_in_canonical_file_is_error(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text() + "\nSee generated/concept-index.md for the list.\n")
    assert "GEN-INPUT" in codes(run(mini_repo), "E")


def test_a_view_shaped_like_a_directory_is_a_named_error_not_a_crash(mini_repo):
    manifest = mini_repo / "generated/manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.mkdir(exist_ok=True)
    issues = [i for i in run(mini_repo)
              if i.code == "GEN-JSON" and i.severity == "E"]
    assert len(issues) == 1, [str(i) for i in run(mini_repo)]
    assert "directory" in str(issues[0]) and "rebuild" in str(issues[0])


def test_a_view_shaped_like_a_broken_symlink_names_the_symlink(mini_repo):
    manifest = mini_repo / "generated/manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.symlink_to(mini_repo / "generated/nowhere.json")
    issues = [i for i in run(mini_repo)
              if i.code == "GEN-JSON" and i.severity == "E"]
    assert len(issues) == 1, [str(i) for i in run(mini_repo)]
    assert "symlink" in str(issues[0]) and "rebuild" in str(issues[0])


def test_crosswalk_judgment_table_warns(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    text = note.read_text().replace("role: synthesis", "role: crosswalk")
    text += textwrap.dedent("""
        | Book | Strengths | Weaknesses |
        |---|---|---|
        | Demo | good | bad |
        """)
    note.write_text(text)
    assert "CROSSWALK-TABLE" in codes(run(mini_repo), "W")


# ------------------------------------------------------------------- modules
def test_registered_must_be_latest_attempt(mini_repo):
    f = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(f.read_text())
    data["modules"][0]["attempts"] = [
        {"termin": 1, "date": "2026-07-27", "result": "registered"},
        {"termin": 2, "date": "2026-10-09", "result": "withdrawn"},
    ]
    f.write_text(yaml.safe_dump(data))
    assert "MOD-REGISTERED" in codes(run(mini_repo), "E")


def test_grade_only_on_passed(mini_repo):
    f = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(f.read_text())
    data["modules"][0]["attempts"][0]["grade"] = 2.0
    f.write_text(yaml.safe_dump(data))
    assert "MOD-GRADE" in codes(run(mini_repo), "E")


def test_attempt_dates_must_be_ordered(mini_repo):
    f = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(f.read_text())
    data["modules"][0]["attempts"] = list(reversed(data["modules"][0]["attempts"]))
    # keep 'registered only on latest' satisfied
    data["modules"][0]["attempts"][0]["result"] = "withdrawn"
    data["modules"][0]["attempts"][1]["result"] = "registered"
    f.write_text(yaml.safe_dump(data))
    assert "MOD-ORDER" in codes(run(mini_repo), "E")


def test_structured_exam_ranges_must_be_forward_and_unique(mini_repo):
    f = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(f.read_text())
    data["modules"][0]["examination"] = {
        "type": "klausur",
        "sittings": [
            {"termin": 2, "date": "2026-10-09", "end_date": "2026-10-08"},
            {"termin": 2, "date": "2026-10-09", "end_date": "2026-10-08"},
        ],
        "registration_windows": [
            {"opens": "2026-09-10", "closes": "2026-08-31", "label": "Gate"},
        ],
    }
    f.write_text(yaml.safe_dump(data))
    result = set(codes(run(mini_repo), "E"))
    assert {"MOD-SITTING-DUP", "MOD-SITTING-RANGE", "MOD-REGISTRATION-RANGE"} <= result


# --------------------------------------------------------------------- files
def test_note_filename_must_equal_id(mini_repo):
    old = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    old.rename(old.with_name("wrong-name.md"))
    assert "FILE-NAME" in codes(run(mini_repo), "E")


def test_missing_attachment_is_error(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text().replace(
        "sources: [source-demo-book]",
        "sources: [source-demo-book]\nattachments:\n"
        "  - knowledge/attachments/note-demo/page-01.jpg"))
    assert "ATTACH-MISSING" in codes(run(mini_repo), "E")


# ---------------------------------------------------------------- workspaces
def test_missing_workspace_section_is_error(mini_repo):
    ctx = mini_repo / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    ctx.write_text(ctx.read_text().replace("## Next Action\n\nDo the demo thing.\n", ""))
    assert "WS-SECTION" in codes(run(mini_repo), "E")


def test_workspace_count_warning_at_8_plus(mini_repo):
    base = mini_repo / "work" / "active"
    template = (base / "workspace-demo" / "CONTEXT.md").read_text()
    for i in range(2, 10):
        wid = f"workspace-demo-{i:02d}"
        d = base / wid
        d.mkdir()
        (d / "CONTEXT.md").write_text(template.replace("workspace-demo", wid))
    assert "WS-COUNT" in codes(run(mini_repo), "W")


# --------------------------------------------------------------------- links
def test_broken_internal_link_is_error(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text() + "\n[missing](./does-not-exist.md)\n")
    assert "LINK-BROKEN" in codes(run(mini_repo), "E")


def test_material_uri_unresolved_is_warning_not_error(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text() + "\n[slides](material://source-demo-book/deck.pdf)\n")
    issues = run(mini_repo)
    assert "URI-MATERIAL" in codes(issues, "W")
    assert "URI-MATERIAL" not in codes(issues, "E")


def test_compact_mode_without_report_keeps_warning_details(mini_repo, repo_root):
    """Compact verification stays readable without hiding the warning debt."""
    import subprocess
    import sys

    script = repo_root / "tools" / "validate.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--compact", "--no-report",
         "--root", str(mini_repo)],
        text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    for issue in run(mini_repo):
        assert str(issue) in proc.stdout
    assert lines[-1].endswith("OK") or "OK (" in lines[-1]
    assert "warning(s)" in lines[-1]
