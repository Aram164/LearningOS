"""Validator unit tests against the synthetic minimal repo + the real repository."""

from __future__ import annotations

import textwrap

import yaml

from learning_os.loader import load_repo
from learning_os.rules import validate


def codes(issues, severity=None):
    return [i.code for i in issues if severity is None or i.severity == severity]


def run(root):
    return validate(load_repo(root))


# ---------------------------------------------------------------- clean base
def test_mini_repo_is_clean(mini_repo):
    issues = run(mini_repo)
    assert codes(issues, "E") == [], [str(i) for i in issues]


def test_real_repository_has_no_errors(repo_root):
    issues = run(repo_root)
    errors = [str(i) for i in issues if i.severity == "E"]
    assert errors == [], errors


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
