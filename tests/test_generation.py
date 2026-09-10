"""Generator tests: determinism, coverage, backlink inversion, reset scenario."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from stress_check import _generation_stress

from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo

TIMESTAMP_LINE = re.compile(r"^> Generated: .*$", re.MULTILINE)


def strip_timestamps(content: str, name: str) -> str:
    if name.endswith((".json", ".canvas")):
        data = json.loads(content)
        data.get("_generated", {}).pop("generated_at", None)
        return json.dumps(data, indent=2, sort_keys=True)
    return TIMESTAMP_LINE.sub("> Generated: X", content)


def test_generation_deterministic_except_timestamps(mini_repo):
    repo = load_repo(mini_repo)
    a = generate_all(repo, generated_at="T1")
    b = generate_all(load_repo(mini_repo), generated_at="T2")
    assert set(a) == set(b)
    for name in a:
        assert strip_timestamps(a[name], name) == strip_timestamps(b[name], name), name


def test_generation_stress_tracks_the_declared_manifest_contract(mini_repo):
    """The atomic-read stress check must move with every manifest bump."""
    _digest, reads = _generation_stress(
        mini_repo, generations=2, readers=2, reads_per_reader=3)
    assert reads == 6


def test_generated_reset_rebuilds_everything(mini_repo):
    """Scenario 5 — delete generated/, rebuild: all outputs return, nothing canonical lost."""
    repo = load_repo(mini_repo)
    outputs = generate_all(repo, generated_at="T1")
    write_outputs(repo, outputs)
    gen = mini_repo / "generated"
    shutil.rmtree(gen)
    assert not gen.exists()
    repo2 = load_repo(mini_repo)
    outputs2 = generate_all(repo2, generated_at="T2")
    write_outputs(repo2, outputs2)
    for rel in outputs:
        assert (gen / rel).exists(), rel
    # canonical intact
    assert (mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md").exists()


def test_every_output_carries_generated_warning(mini_repo):
    repo = load_repo(mini_repo)
    outputs = generate_all(repo, generated_at="T1")
    for name, content in outputs.items():
        if name.endswith(".json"):
            assert "_generated" in json.loads(content), name
        else:
            assert "GENERATED" in content[:400], name


def test_manifest_covers_every_canonical_record(mini_repo):
    repo = load_repo(mini_repo)
    manifest = json.loads(generate_all(repo, generated_at="T1")["manifest.json"])
    ids = {r["id"] for r in manifest["records"]}
    for family in (repo.notes, repo.concepts, repo.sources, repo.modules, repo.workspaces):
        for rec_id in family:
            assert rec_id in ids, rec_id
    assert len(manifest["relations"]) == len(repo.relations)


def test_backlinks_equal_inverse_of_forward_references(mini_repo):
    repo = load_repo(mini_repo)
    backlinks = json.loads(generate_all(repo, generated_at="T1")["backlinks.json"])
    # independent recomputation of concept->notes from note frontmatter
    expected: dict[str, set] = {}
    for note in repo.notes.values():
        for cid in note.meta.get("concepts", []) or []:
            expected.setdefault(cid, set()).add(note.id)
    actual = {k: set(v) for k, v in backlinks["concept_to_notes"].items()}
    assert actual == expected
    expected_s: dict[str, set] = {}
    for note in repo.notes.values():
        for sid in note.meta.get("sources", []) or []:
            expected_s.setdefault(sid, set()).add(note.id)
    assert {k: set(v) for k, v in backlinks["source_to_notes"].items()} == expected_s
    # relation inversion
    for rel in repo.relations:
        out_edges = backlinks["concept_relations"][rel["from"]]["outgoing"]
        in_edges = backlinks["concept_relations"][rel["to"]]["incoming"]
        assert {"type": rel["type"], "to": rel["to"]} in out_edges
        assert {"type": rel["type"], "from": rel["from"]} in in_edges


def test_archived_workspace_excluded_from_indexes(mini_repo):
    arch = mini_repo / "archive" / "workspaces" / "2026" / "workspace-old-effort"
    arch.mkdir(parents=True)
    (arch / "CONTEXT.md").write_text(
        "---\nid: workspace-old-effort\ntype: workspace\ntitle: Old\n"
        "created: 2026-01-01\nstatus: complete\n---\n\n## Objective\n\nDone.\n"
        "\n## Current Scope\n\n-\n\n## Open Questions\n\n-\n\n## Next Action\n\n-\n",
        encoding="utf-8")
    repo = load_repo(mini_repo)
    outputs = generate_all(repo, generated_at="T1")
    assert "workspace-old-effort" not in outputs["concept-index.md"]
    assert "workspace-old-effort" not in outputs["source-index.md"]
    # but it is preserved in the manifest, marked archived
    manifest = json.loads(outputs["manifest.json"])
    rec = next(r for r in manifest["records"] if r["id"] == "workspace-old-effort")
    assert rec["archived"] is True


def test_generated_is_gitignored(repo_root):
    out = subprocess.run(["git", "check-ignore", "generated/manifest.json"],
                         cwd=repo_root, capture_output=True, text=True)
    assert out.returncode == 0, "generated/* must be gitignored"


@pytest.mark.full_repo
def test_real_repo_generates_and_selector_views_present(repo_root):
    repo = load_repo(repo_root)
    outputs = generate_all(repo, generated_at="T1")
    src_index = outputs["source-index.md"]
    assert "## Selector view — per lecture" in src_index
    assert "## Selector view — per concept" in src_index
    coord = outputs["coordination-view.md"]
    assert "## Exam spine" in coord
    assert "## Active workspaces" in coord
    assert "## Neglect signals (Git)" in coord


@pytest.mark.full_repo
def test_real_manifest_exposes_unregistered_sittings_and_registration_gate(repo_root):
    manifest = json.loads(generate_all(load_repo(repo_root), generated_at="T1")["manifest.json"])
    deadlines = manifest["academic_deadlines"]
    pending = {(row.get("module_id"), row.get("start_date"), row.get("end_date"))
               for row in deadlines
               if row.get("kind") == "exam" and row.get("registration_state") == "unregistered"}
    assert ("module-hu-aml", "2026-09-30", "2026-09-30") in pending
    assert ("module-hu-m2-statistik-analysis", "2026-10-09", "2026-10-09") in pending
    assert ("module-hu-algo2", "2026-10-05", "2026-10-08") in pending
    [window] = [row for row in deadlines
                if row.get("kind") == "registration-window"
                and row.get("start_date") == "2026-08-31"
                and row.get("end_date") == "2026-09-10"]
    assert {module["module_id"] for module in window["modules"]} == {
        "module-hu-aml", "module-hu-m2-statistik-analysis", "module-hu-algo2"
    }


# ---------------------------------------------------------------- domain atlas


def test_domain_atlas_at_a_glance_covers_all_domains(mini_repo):
    """ADR-005: the atlas always maps ALL seven buckets + the excluded strata."""
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    atlas = outputs["domain-atlas.md"]
    assert "## At a glance" in atlas
    for dom in ("mathematics", "machine-learning", "systems", "data-systems",
                "algorithms", "programming", "cross-domain"):
        assert f"- **{dom}**" in atlas, dom
        assert f"## {dom}" in atlas, dom
    assert "- **mathematics** — 1 note" in atlas
    assert "External code repositories" in atlas
    assert "Stratum/" in atlas
    assert "Master's Planning" not in atlas
    assert "Legacy tree" not in atlas
    assert "## Not in this map" in atlas


def test_normal_atlas_generation_never_stats_legacy(mini_repo, monkeypatch):
    repo = load_repo(mini_repo)
    original_is_dir = Path.is_dir

    def guarded_is_dir(path: Path):
        if "legacy" in {part.casefold() for part in path.parts}:
            raise AssertionError(f"normal atlas touched sealed Legacy boundary: {path}")
        return original_is_dir(path)

    monkeypatch.setattr(Path, "is_dir", guarded_is_dir)
    atlas = generate_all(repo, generated_at="T1")["domain-atlas.md"]

    assert "Legacy tree" not in atlas


def test_domain_atlas_shelves_harvest_descriptions_and_never_drop(mini_repo):
    """Shelf descriptions are harvested from canonical collection fields; a
    collection missing from the view mapping falls back to cross-domain."""
    (mini_repo / "sources" / "collections" / "math-bookshelf.yaml").write_text(
        "title: Math shelf\ndescription: The demo shelf purpose line.\n"
        "entries:\n  - source: source-demo-book\n    why: demo\n",
        encoding="utf-8")
    (mini_repo / "sources" / "collections" / "future-shelf.yaml").write_text(
        "title: Future shelf\nentries:\n  - source: source-demo-book\n    why: x\n",
        encoding="utf-8")
    atlas = generate_all(load_repo(mini_repo), generated_at="T1")["domain-atlas.md"]
    math_section = atlas.split("## mathematics")[1].split("\n## ")[0]
    assert "[Math shelf](collections/math-bookshelf.md)" in math_section
    assert "The demo shelf purpose line." in math_section
    cross_section = atlas.split("## cross-domain")[1].split("\n## ")[0]
    assert "[Future shelf](collections/future-shelf.md)" in cross_section


def test_domain_atlas_enumerates_and_links_every_note(mini_repo):
    """A map that only counts its territory cannot be navigated. Every note is
    listed under its role with a working relative link and its id, so the atlas
    answers "what is in this domain" without a second lookup (ADR-005)."""
    atlas = generate_all(load_repo(mini_repo), generated_at="T1")["domain-atlas.md"]
    math_section = atlas.split("## mathematics")[1].split("\n## ")[0]
    assert "Notes by role:" in math_section
    note = next(iter(load_repo(mini_repo).notes.values()))
    rel = note.path.relative_to(mini_repo).as_posix()
    assert f"](../{rel})" in math_section, "note link must resolve from generated/"
    assert f"`{note.id}`" in math_section
    # The compact session-start block stays a census, not a listing.
    glance = atlas.split("## At a glance")[1].split("\n## ")[0]
    assert f"`{note.id}`" not in glance


def test_collection_records_carry_their_curation(mini_repo):
    """The shelf, not the registry, is where reading strategy lives: interfaces
    get the description, the domain and each entry's group/role from the
    manifest, and never re-parse the collection YAML (ADR-006)."""
    (mini_repo / "sources" / "collections" / "math-bookshelf.yaml").write_text(
        "title: Math shelf\ndescription: The demo shelf purpose line.\n"
        "entries:\n  - source: source-demo-book\n    group: tier-1-now\n"
        "    why: Read this first.\n",
        encoding="utf-8")
    manifest = json.loads(
        generate_all(load_repo(mini_repo), generated_at="T1")["manifest.json"])
    shelf = next(row for row in manifest["records"]
                 if row["type"] == "collection" and row["id"] == "math-bookshelf")
    assert shelf["summary"] == "The demo shelf purpose line."
    assert shelf["domain"] == "mathematics"
    assert shelf["entries"] == [{"source": "source-demo-book", "group": "tier-1-now",
                                 "why": "Read this first."}]
    assert shelf["sources"] == ["source-demo-book"]


def test_health_reports_wiring_debt(mini_repo):
    """ADR-005 (3C): visibility debt is measured in the health report — a source
    with no concept-linked evaluation, no shelf, and no note reference is
    'least visible'; wired sources are counted, never listed as debt."""
    import yaml as _yaml
    src_file = mini_repo / "sources" / "sources.yaml"
    data = _yaml.safe_load(src_file.read_text(encoding="utf-8"))
    data["sources"].append({"id": "source-unwired", "title": "Unwired Thing",
                            "type": "book"})
    src_file.write_text(_yaml.safe_dump(data), encoding="utf-8")
    health = generate_all(load_repo(mini_repo), generated_at="T1")["reports/health.md"]
    assert "## Source wiring (visibility debt)" in health
    assert "concept-wired" in health and "1/2" in health
    assert "**least visible**" in health and "`source-unwired`" in health
    assert "Wire on use" in health


def test_health_flags_shelves_missing_an_explicit_atlas_domain(mini_repo):
    """Review 2026-09-09: a collection the shelf→domain map does not name
    renders as cross-domain. The health report names it so the fallback
    never fires silently; explicitly mapped shelves stay out of the signal."""
    import yaml as _yaml
    coll = mini_repo / "sources" / "collections"
    (coll / "shelf-unmapped.yaml").write_text(
        _yaml.safe_dump({"title": "Unmapped shelf", "entries": []}),
        encoding="utf-8")
    (coll / "math-bookshelf.yaml").write_text(
        _yaml.safe_dump({"title": "Mapped shelf", "entries": []}),
        encoding="utf-8")
    (coll / "exam-practice-banks.yaml").write_text(
        _yaml.safe_dump({"title": "Mixed exam banks", "entries": []}),
        encoding="utf-8")
    health = generate_all(load_repo(mini_repo), generated_at="T1")["reports/health.md"]
    assert "## Atlas shelf placement" in health
    assert "`shelf-unmapped`" in health
    assert "`math-bookshelf`" not in health
    assert "`exam-practice-banks`" not in health



@pytest.mark.parametrize("failure", ["revision", "status", "revision-timeout", "status-timeout", "missing-git"])
def test_git_failure_does_not_publish_manifest(mini_repo, monkeypatch, failure):
    (mini_repo / ".git").mkdir(exist_ok=True)
    from learning_os.errors import TransactionFailure

    repo = load_repo(mini_repo)
    manifest_path = mini_repo / "generated/manifest.json"
    manifest_path.write_text("previous manifest", encoding="utf-8")
    real_run = subprocess.run

    def run(args, **kwargs):
        if args[:2] not in (["git", "rev-parse"], ["git", "status"]):
            return real_run(args, **kwargs)
        query = "revision" if args[1] == "rev-parse" else "status"
        if failure == "missing-git":
            raise FileNotFoundError("git unavailable")
        if failure == query + "-timeout":
            raise subprocess.TimeoutExpired(args, 30)
        if failure == query:
            return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: unable to read index")
        return subprocess.CompletedProcess(args, 0, stdout="deadbeef" if query == "revision" else "", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    message = "timed out" if "timeout" in failure else "unavailable" if failure == "missing-git" else "unable to read index"
    with pytest.raises(TransactionFailure, match=message):
        write_outputs(repo, generate_all(repo, generated_at="T1"))
    assert manifest_path.read_text(encoding="utf-8") == "previous manifest"


def test_non_git_tree_generates_with_null_revision(mini_repo, monkeypatch):
    # Stop Git discovery before the containing checkout; do not mock Git's answer.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(mini_repo.parent))
    repo = load_repo(mini_repo)
    outputs = generate_all(repo)
    write_outputs(repo, outputs)
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text())
    assert manifest["_generated"]["source_revision"] is None
    assert manifest["_generated"]["source_dirty"] is False


@pytest.mark.parametrize("status, dirty", [("", False), (" M knowledge/concepts.yaml\n", True)])
def test_successful_git_queries_publish_answer(tmp_path, monkeypatch, status, dirty):
    (tmp_path / ".git").mkdir(exist_ok=True)
    from learning_os.genout.common import _git_state

    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0,
            stdout="deadbeef" if args[1] == "rev-parse" else status, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    assert _git_state(tmp_path) == ("deadbeef", dirty)


@pytest.mark.parametrize("marker", ["-", "*", "+", "1.", "12.", "1)", "12)"])
@pytest.mark.parametrize("continuation", ["  continuation", "continuation"])
@pytest.mark.parametrize("with_prose", [True, False])
def test_note_summary_prefers_prose_with_list_fallback(mini_repo, marker, continuation, with_prose):
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    body = f"# Title\n\n---\n{marker} first item\n{continuation}\n{marker} second item\n\n* * *\n"
    if with_prose:
        body += "\nReal prose paragraph."
    note.write_text(note.read_text().replace("Body prose.", body), encoding="utf-8")
    manifest = json.loads(generate_all(load_repo(mini_repo), generated_at="T1")["manifest.json"])
    projected = next(row for row in manifest["records"] if row["id"] == "note-demo")
    expected = "Real prose paragraph." if with_prose else "first item continuation second item"
    assert projected["summary"] == expected


def test_malformed_frontmatter_prevents_publication(mini_repo):
    from test_cli import run_los

    # ensure it is generated first
    run_los(mini_repo, "generate")
    manifest_path = mini_repo / "generated" / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()

    note = next(iter(load_repo(mini_repo).notes.values()))
    original_text = note.path.read_text(encoding="utf-8")

    # break it
    broken_text = original_text.replace("id: ", "id: [broken", 1)
    note.path.write_text(broken_text, encoding="utf-8")

    # try generate
    broken_response = run_los(mini_repo, "generate")
    assert broken_response.returncode != 0
    # The refusal has to name the file the operator must go and repair; a count
    # of failures is not something anyone can act on.
    assert "cannot publish" in broken_response.stderr
    assert str(note.path.relative_to(mini_repo)) in broken_response.stderr

    # check that manifest is unchanged
    assert manifest_path.read_bytes() == manifest_bytes

    # repair it
    note.path.write_text(original_text, encoding="utf-8")
    repaired_response = run_los(mini_repo, "generate")
    assert repaired_response.returncode == 0

def test_unborn_head_generates_with_null_revision(mini_repo):
    subprocess.run(["git", "init"], cwd=mini_repo, check=True)
    repo = load_repo(mini_repo)
    outputs = generate_all(repo)
    write_outputs(repo, outputs)
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text())
    # An unborn HEAD is empty history, not a failure: generation publishes with
    # no revision to name, and still reports the working tree honestly rather
    # than defaulting the flag (#10).
    assert manifest["_generated"]["source_revision"] is None
    assert manifest["_generated"]["source_dirty"] is True

def test_nested_export_boundaries(mini_repo):
    # mini_repo is an export inside the overall test runner repo
    repo = load_repo(mini_repo)
    outputs = generate_all(repo)
    write_outputs(repo, outputs)
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text())
    assert manifest["_generated"]["source_revision"] is None

def test_boundary_functions_agree(mini_repo):
    from learning_os.genout.common import _git_state, stable_generated_at
    from learning_os.githistory import read_history
    rev, dirty = _git_state(mini_repo)
    assert rev is None
    
    assert stable_generated_at(mini_repo) == "(no Git history available)"
    assert read_history(mini_repo, "-1", "--format=%H") == ""

def test_failing_git_status_refuses(mini_repo):
    from learning_os.errors import TransactionFailure
    subprocess.run(["git", "init"], cwd=mini_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "--allow-empty", "-m", "Initial"],
        cwd=mini_repo, check=True
    )
    
    index_file = mini_repo / ".git/index"
    index_file.write_bytes(b"corrupted_index_data")
    
    repo = load_repo(mini_repo)
    with pytest.raises(TransactionFailure, match="Git failed to check status|index file smaller than expected"):
        generate_all(repo)

def test_tools_generate_malformed_frontmatter_prevents_publication(mini_repo):
    import subprocess
    import sys

    generate_script = str(Path(__file__).parent.parent / "tools" / "generate.py")
    
    # ensure it is generated first
    subprocess.run([sys.executable, generate_script, "--root", str(mini_repo)],
                   cwd=str(mini_repo), check=True)
    manifest_path = mini_repo / "generated" / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()

    note = next(iter(load_repo(mini_repo).notes.values()))
    original_text = note.path.read_text(encoding="utf-8")

    # break it
    broken_text = original_text.replace("id: ", "id: [broken", 1)
    note.path.write_text(broken_text, encoding="utf-8")

    # try generate via tools/generate.py
    proc = subprocess.run([sys.executable, generate_script, "--root", str(mini_repo)],
                          cwd=str(mini_repo), capture_output=True, text=True)
    assert proc.returncode != 0
    assert "cannot publish" in proc.stdout or "cannot publish" in proc.stderr
    assert str(note.path.relative_to(mini_repo)) in proc.stdout or str(note.path.relative_to(mini_repo)) in proc.stderr
    
    # the existing manifest must not be overwritten
    assert manifest_path.read_bytes() == manifest_bytes
