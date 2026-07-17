"""Regression tests for the recommended-improvements pass.

Covers the behaviors called out in the code review (see repository root
"recommended Improvements"): loader hardening (empty/duplicate/malformed
records), attachment containment on resolved paths, alias/date normalization,
deterministic generation, generated-file governance, and validator warnings
(orphans, binaries, stale inbox, Git neglect). Each maps to a numbered item.
"""

from __future__ import annotations

import datetime
import os
import shutil
import subprocess
import time

import yaml

from learning_os.genout import generate_all, mermaid_node_ids, write_outputs
from learning_os.loader import load_repo
from learning_os.rules import validate


def codes(issues, severity=None):
    return [i.code for i in issues if severity is None or i.severity == severity]


def run(root):
    return validate(load_repo(root))


def _snapshot(directory) -> dict[str, bytes]:
    """{relative-path: bytes} for every file under `directory` (dirs excluded)."""
    out: dict[str, bytes] = {}
    for f in sorted(directory.rglob("*")):
        if f.is_file():
            out[str(f.relative_to(directory))] = f.read_bytes()
    return out


def _add_active_workspaces(mini_repo, n: int) -> None:
    base = mini_repo / "work" / "active"
    template = (base / "workspace-demo" / "CONTEXT.md").read_text()
    for i in range(2, 2 + n):
        wid = f"workspace-demo-{i:02d}"
        d = base / wid
        d.mkdir()
        (d / "CONTEXT.md").write_text(template.replace("workspace-demo", wid))


# ---------------------------------------------------------- item 1/5/14: IDs
def test_empty_concept_id_is_rejected_at_load(mini_repo):
    f = mini_repo / "knowledge" / "concepts.yaml"
    data = yaml.safe_load(f.read_text())
    data["concepts"].append({"id": "", "label": "Empty"})
    f.write_text(yaml.safe_dump(data))
    repo = load_repo(mini_repo)
    assert "" not in repo.concepts            # not admitted to the model
    assert "PARSE" in codes(validate(repo), "E")


def test_missing_id_record_is_rejected(mini_repo):
    f = mini_repo / "knowledge" / "concepts.yaml"
    data = yaml.safe_load(f.read_text())
    data["concepts"].append({"label": "No id at all"})
    f.write_text(yaml.safe_dump(data))
    assert "PARSE" in codes(run(mini_repo), "E")


# ------------------------------------------------------ item 6/14: malformed
def test_malformed_yaml_partition_is_reported_not_fatal(mini_repo):
    part = mini_repo / "knowledge" / "concepts"
    part.mkdir()
    (part / "broken.yaml").write_text("concepts: [1, 2\n")  # unterminated flow seq
    repo = load_repo(mini_repo)                              # must not raise
    assert "concept-expected-value" in repo.concepts         # good data survives
    assert "PARSE" in codes(validate(repo), "E")


def test_non_mapping_registry_item_is_skipped(mini_repo):
    part = mini_repo / "knowledge" / "concepts"
    part.mkdir()
    (part / "extra.yaml").write_text(yaml.safe_dump(
        {"concepts": [42, {"id": "concept-new", "label": "New"}]}))
    repo = load_repo(mini_repo)
    assert "concept-new" in repo.concepts       # the valid sibling still loads
    assert "PARSE" in codes(validate(repo), "E")  # the 42 is reported


def test_duplicate_concept_id_is_error(mini_repo):
    part = mini_repo / "knowledge" / "concepts"
    part.mkdir()
    (part / "dup.yaml").write_text(yaml.safe_dump(
        {"concepts": [{"id": "concept-variance", "label": "Dup"}]}))
    assert "ID-DUP" in codes(run(mini_repo), "E")


# ------------------------------------------------- item 7/14: alias collision
def test_alias_collision_across_whitespace_and_case_warns(mini_repo):
    """' erwartungswert ' must collide with 'Erwartungswert' after
    strip().casefold() — the point of item 7."""
    f = mini_repo / "knowledge" / "concepts.yaml"
    data = yaml.safe_load(f.read_text())
    data["concepts"].append(
        {"id": "concept-mean", "label": "Mean", "aliases": ["  erwartungswert  "]})
    f.write_text(yaml.safe_dump(data))
    warnings = [str(i) for i in run(mini_repo) if i.code == "ALIAS-COLLISION"]
    assert warnings, "expected an ALIAS-COLLISION warning"
    # item 9: the diagnostic names the originating file for each concept
    assert "concepts.yaml" in warnings[0]


# --------------------------------------------------- item 4/14: containment
def test_attachment_path_traversal_is_rejected(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text().replace(
        "sources: [source-demo-book]",
        "sources: [source-demo-book]\nattachments:\n"
        "  - knowledge/attachments/note-demo/../note-evil/secret.pdf"))
    assert "ATTACH-PATH" in codes(run(mini_repo), "E")


def test_attachment_inside_its_dir_is_accepted(mini_repo):
    adir = mini_repo / "knowledge" / "attachments" / "note-demo"
    adir.mkdir(parents=True)
    (adir / "page-01.jpg").write_bytes(b"\xff\xd8\xff")  # a real file
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text().replace(
        "sources: [source-demo-book]",
        "sources: [source-demo-book]\nattachments:\n"
        "  - knowledge/attachments/note-demo/page-01.jpg"))
    got = codes(run(mini_repo))
    assert "ATTACH-PATH" not in got and "ATTACH-MISSING" not in got


# ------------------------------------------------------- item 8: date types
def test_mixed_type_attempt_dates_do_not_crash(mini_repo):
    """A bare-year int next to an ISO string must not raise on sorted()."""
    f = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(f.read_text())
    data["modules"][0]["attempts"] = [
        {"termin": 1, "date": 2027, "result": "withdrawn"},        # int
        {"termin": 2, "date": "2026-10-09", "result": "registered"},  # str
    ]
    f.write_text(yaml.safe_dump(data))
    issues = run(mini_repo)                       # must not raise TypeError
    assert "MOD-ORDER" in codes(issues, "E")      # 2027 then 2026 is out of order


# ------------------------------------------ item 11/12/27: deterministic gen
def test_generation_is_byte_for_byte_with_fixed_timestamp(mini_repo):
    a = generate_all(load_repo(mini_repo), generated_at="FIXED-TS")
    b = generate_all(load_repo(mini_repo), generated_at="FIXED-TS")
    assert a == b  # identical bytes, timestamps included


def test_repeated_write_outputs_is_filesystem_stable(mini_repo):
    gen = mini_repo / "generated"
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, generated_at="FIXED"))
    first = _snapshot(gen)
    repo2 = load_repo(mini_repo)
    write_outputs(repo2, generate_all(repo2, generated_at="FIXED"))
    second = _snapshot(gen)
    assert first == second  # same files, same bytes, nothing added or dropped


def test_reset_generation_reproduces_identical_content(mini_repo):
    gen = mini_repo / "generated"
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, generated_at="FIXED"))
    before = _snapshot(gen)
    shutil.rmtree(gen)
    repo2 = load_repo(mini_repo)
    write_outputs(repo2, generate_all(repo2, generated_at="FIXED"))
    after = _snapshot(gen)
    assert before == after  # identical content, not merely the same filenames


# ------------------------------------------------- item 13: stale generated
def test_stale_generated_file_is_removed(mini_repo):
    gen = mini_repo / "generated"
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, generated_at="FIXED"))
    stray = gen / "zzz-stale.md"
    stray.write_text("orphan view\n")
    repo2 = load_repo(mini_repo)
    write_outputs(repo2, generate_all(repo2, generated_at="FIXED"))
    assert not stray.exists()
    assert (gen / "manifest.json").exists()  # real outputs untouched


def test_deleted_collection_view_is_removed(mini_repo):
    coll = mini_repo / "sources" / "collections" / "reading-list.yaml"
    coll.write_text(yaml.safe_dump(
        {"title": "Reading list", "entries": [{"source": "source-demo-book"}]}))
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, generated_at="FIXED"))
    view = mini_repo / "generated" / "collections" / "reading-list.md"
    assert view.exists()
    coll.unlink()                                  # the collection goes away
    repo2 = load_repo(mini_repo)
    write_outputs(repo2, generate_all(repo2, generated_at="FIXED"))
    assert not view.exists()                       # its view must not linger


# --------------------------------------------- item 28: generated governance
def test_unexpected_file_in_generated_is_error(mini_repo):
    (mini_repo / "generated" / "rogue.md").write_text("> GENERATED marker\nhi\n")
    assert "GEN-UNKNOWN" in codes(run(mini_repo), "E")


def test_generated_file_without_header_is_error(mini_repo):
    (mini_repo / "generated" / "module-view.md").write_text("no header at all\n")
    assert "GEN-HEADER" in codes(run(mini_repo), "E")


# ------------------------------------------ item 26: workspace-count boundary
def test_no_workspace_count_warning_at_exactly_7(mini_repo):
    _add_active_workspaces(mini_repo, 6)  # 1 baseline + 6 = 7 non-standing
    assert "WS-COUNT" not in codes(run(mini_repo), "W")


def test_workspace_count_warning_at_exactly_8(mini_repo):
    _add_active_workspaces(mini_repo, 7)  # 1 baseline + 7 = 8 non-standing
    assert "WS-COUNT" in codes(run(mini_repo), "W")


# ----------------------------- item 29: orphans, binaries, inbox, Git neglect
def test_orphan_attachment_directory_warns(mini_repo):
    (mini_repo / "knowledge" / "attachments" / "note-nobody").mkdir(parents=True)
    assert "ATTACH-ORPHAN" in codes(run(mini_repo), "W")


def test_binary_under_knowledge_warns(mini_repo):
    (mini_repo / "knowledge" / "notes" / "mathematics" / "slides.pdf").write_bytes(
        b"%PDF-1.4\n")
    assert "BINARY-IN-KNOWLEDGE" in codes(run(mini_repo), "W")


def test_stale_inbox_item_warns(mini_repo):
    item = mini_repo / "work" / "inbox" / "old-capture.md"
    item.write_text("unrouted capture\n")
    old = time.time() - 20 * 86400
    os.utime(item, (old, old))
    assert "INBOX-STALE" in codes(run(mini_repo), "W")


def test_git_neglect_flags_untouched_workspace(mini_repo):
    old = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e",
        "GIT_AUTHOR_DATE": old, "GIT_COMMITTER_DATE": old,
    }
    subprocess.run(["git", "init", "-q"], cwd=mini_repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=mini_repo, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=mini_repo,
                   check=True, env=env)
    assert "WS-NEGLECT" in codes(run(mini_repo), "W")


# ------------------------------------------------------ item 10: mermaid IDs
def test_mermaid_node_ids_never_collide():
    m = mermaid_node_ids(["concept-a-b", "concept-a.b", "concept-a_b"])
    assert len(set(m.values())) == 3           # sanitize-collision disambiguated
    assert all(v[0].isalpha() or v[0] == "_" for v in m.values())
