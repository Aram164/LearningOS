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


def test_living_docs_cannot_copy_a_manifest_version(mini_repo):
    readme = mini_repo / "README.md"
    readme.write_text(
        "Read manifest v99 and hope this prose changes when the producer does.\n",
        encoding="utf-8",
    )
    assert "CONTRACT-DOC-STATIC-VERSION" in codes(run(mini_repo), "E")


@pytest.mark.full_repo
def test_real_repository_has_no_errors(repo_root):
    issues = run(repo_root)
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
