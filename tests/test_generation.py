"""Generator tests: determinism, coverage, backlink inversion, reset scenario."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo

TIMESTAMP_LINE = re.compile(r"^> Generated: .*$", re.MULTILINE)


def strip_timestamps(content: str, name: str) -> str:
    if name.endswith(".json"):
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
