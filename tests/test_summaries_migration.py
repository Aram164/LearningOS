"""Summary migration: freeze once, map reviewably, migrate through the gateway.

End-to-end over a synthetic repository: all four resolutions bind
correctly, migrated bodies are byte-identical to the frozen bytes, the
manifest binds the mapping hash, reruns replay, and every phase refuses
changed or corrupt inputs instead of reinterpreting them.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml
from repo_builders import write_yaml

DRIVER = Path(__file__).resolve().parent.parent / "tools" / "migrations" / \
    "summaries_to_notes_v1.py"
REAL_TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _run(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(DRIVER), "--root", str(root), *args],
        capture_output=True, text=True, timeout=300)


MARKER = ("<!-- GENERATED file - do not edit; promoted by "
          "tools/material_summarize.py --promote -->\n\n")


def _entry(cache: Path, digest: str, pages: str, material: str,
           body: bytes, model: str = "test-model 1"):
    target = cache / digest / f"pages-{pages}"
    target.mkdir(parents=True)
    (target / "summary.md").write_bytes(
        MARKER.encode("utf-8") + body)
    start, end = (int(part) for part in pages.split("-"))
    (target / "meta.json").write_text(json.dumps(
        {"_generated": {
            "warning": "GENERATED file - do not edit; rebuilt by "
                       "python tools/material_summarize.py --promote",
            "generator": "tools/material_summarize.py"},
         "material": material, "sha256": digest,
         "page_range": [start, end], "model": model,
         "built": "2026-09-21", "scope": "chapter"}), encoding="utf-8")


def _seed(mini_repo: Path) -> Path:
    """Four cache entries covering resolved/stale/unavailable/unresolved."""
    los = mini_repo.parent
    materials = los / "materials"
    file_a = materials / "file-a.pdf"
    file_a.write_bytes(b"physical bytes a")
    file_b = materials / "file-b.pdf"
    file_b.write_bytes(b"physical bytes b, changed")
    file_d = materials / "file-d.pdf"
    file_d.write_bytes(b"physical bytes d")
    flat = materials / ".flat" / "alias-a"
    flat.mkdir(parents=True)
    (flat / "file-a.pdf").symlink_to("../../file-a.pdf")
    digest_a = hashlib.sha256(b"physical bytes a").hexdigest()
    digest_b_old = hashlib.sha256(b"physical bytes b").hexdigest()
    digest_c = hashlib.sha256(b"physical bytes c").hexdigest()
    digest_d = hashlib.sha256(b"physical bytes d").hexdigest()
    cache = mini_repo / "generated" / "summaries"
    _entry(cache, digest_a, "1-2", "file-a.pdf", b"Analysis A. " * 20)
    _entry(cache, digest_b_old, "1-2", "file-b.pdf", b"Analysis B. " * 20)
    _entry(cache, digest_c, "1-2", "file-c.pdf", b"Analysis C. " * 20)
    _entry(cache, digest_d, "1-2", "file-d.pdf", b"Analysis D. " * 20)
    sources_path = mini_repo / "sources" / "sources.yaml"
    sources = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
    sources["sources"].append(
        {"id": "source-alias-a", "title": "Alias A", "type": "book",
         "authors": ["A. Author"],
         "material": "material://alias-a/file-a.pdf",
         "evaluations": [{"concepts": ["concept-expected-value"],
                          "roles": ["first-learning"], "level": "introductory",
                          "strengths": ["covers file A"]}]})
    write_yaml(sources_path, sources)
    # The migrate phase dispatches through <root>/tools/los.py; link the
    # real CLI (its learning_os imports resolve venv-wide, as in prod).
    (mini_repo / "tools" / "los.py").symlink_to(REAL_TOOLS / "los.py")
    # Retired migrations replay only against their own generation: declare
    # the historical contract version so the lifecycle guard admits this
    # fixture (same pattern as the route-identity migration tests). The
    # fingerprint stays the live one: the migrate phase transacts through
    # the gateway, and post-commit validation compares schema bytes, not
    # the replay generation.
    live_contract = yaml.safe_load(
        (Path(__file__).resolve().parent.parent / "system" / "contracts" /
         "data-contract.yaml").read_text(encoding="utf-8"))
    (mini_repo / "system" / "contracts" / "data-contract.yaml").write_text(
        yaml.safe_dump({"contract_version": 35,
                        "schema_fingerprint":
                            live_contract["schema_fingerprint"]}),
        encoding="utf-8")
    return cache


def test_freeze_map_migrate_roundtrip_with_all_resolutions(mini_repo):
    _seed(mini_repo)
    frozen = _run(mini_repo, "freeze", "--apply")
    assert frozen.returncode == 0, frozen.stderr
    assert "froze 4 entries" in frozen.stdout
    mapped = _run(mini_repo, "map", "--apply")
    assert mapped.returncode == 0, mapped.stderr
    mapping = yaml.safe_load(
        (mini_repo / "operations" / "migrations" /
         "summary-mapping-2026-09-21-r2.yaml").read_text(encoding="utf-8"))
    by_id = {row["note_id"]: row for row in mapping["rows"]}
    assert by_id["note-file-a-pp001-002"]["resolution"] == "resolved"
    assert by_id["note-file-a-pp001-002"]["binding"]["source_id"] == "source-alias-a"
    assert by_id["note-file-b-pp001-002"]["resolution"] == "stale"
    assert "source_id" not in by_id["note-file-b-pp001-002"]["binding"]
    assert by_id["note-file-c-pp001-002"]["resolution"] == "unavailable"
    assert by_id["note-file-d-pp001-002"]["resolution"] == "unresolved"

    migrated = _run(mini_repo, "migrate", "--apply")
    assert migrated.returncode == 0, migrated.stdout + migrated.stderr
    for row in mapping["rows"]:
        frozen_body = (mini_repo / "operations" / "migrations" /
                       "summary-freeze-2026-09-21" / row["digest"] /
                       row["pages"] / "summary.md").read_bytes()
        note_bytes = (mini_repo / row["note_path"]).read_bytes()
        length = row["binding"]["frozen_input_bytes"]
        assert note_bytes[-length:] == frozen_body
    manifest = yaml.safe_load(
        (mini_repo / "operations" / "migrations" /
         "summary-migration-manifest-r2.yaml").read_text(encoding="utf-8"))
    assert manifest["mapping_sha256"] == hashlib.sha256(
        (mini_repo / "operations" / "migrations" /
         "summary-mapping-2026-09-21-r2.yaml").read_bytes()).hexdigest()
    assert [note["replayed"] for note in manifest["notes"]] == [False] * 4

    # A repeated migration replays identical rows instead of duplicating.
    again = _run(mini_repo, "migrate", "--apply")
    assert again.returncode == 0, again.stdout + again.stderr
    manifest = yaml.safe_load(
        (mini_repo / "operations" / "migrations" /
         "summary-migration-manifest-r2.yaml").read_text(encoding="utf-8"))
    assert [note["replayed"] for note in manifest["notes"]] == [True] * 4


def test_freeze_refuses_recorded_checksum_mismatch(mini_repo):
    _seed(mini_repo)
    cache = mini_repo / "generated" / "summaries"
    meta_path = next(cache.rglob("meta.json"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["summary_sha256"] = "00" * 32
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    frozen = _run(mini_repo, "freeze", "--apply")
    assert frozen.returncode == 2
    assert "checksum mismatch" in frozen.stderr


def test_map_refuses_changed_frozen_bytes(mini_repo):
    _seed(mini_repo)
    assert _run(mini_repo, "freeze", "--apply").returncode == 0
    frozen_body = next((mini_repo / "operations" / "migrations" /
                        "summary-freeze-2026-09-21").rglob("summary.md"))
    with frozen_body.open("ab") as handle:
        handle.write(b"changed")
    mapped = _run(mini_repo, "map", "--apply")
    assert mapped.returncode == 2
    assert "frozen input changed" in mapped.stderr


def test_migrate_refuses_without_apply_and_after_tampering(mini_repo):
    _seed(mini_repo)
    assert _run(mini_repo, "freeze", "--apply").returncode == 0
    assert _run(mini_repo, "map", "--apply").returncode == 0
    dry = _run(mini_repo, "migrate")
    assert dry.returncode == 2
    assert "requires --apply" in dry.stderr
    assert list((mini_repo / "knowledge" / "notes").rglob("note-file-*.md")) == []
    frozen_body = next((mini_repo / "operations" / "migrations" /
                        "summary-freeze-2026-09-21").rglob("summary.md"))
    with frozen_body.open("ab") as handle:
        handle.write(b"changed")
    tampered = _run(mini_repo, "migrate", "--apply")
    assert tampered.returncode == 2
    assert "frozen input changed" in tampered.stderr
    assert list((mini_repo / "knowledge" / "notes").rglob("note-file-*.md")) == []


def test_migrate_is_retired_on_newer_declared_contracts(mini_repo):
    _seed(mini_repo)
    live = Path(__file__).resolve().parent.parent / "system" / "contracts" / \
        "data-contract.yaml"
    (mini_repo / "system" / "contracts" / "data-contract.yaml").write_text(
        live.read_text(encoding="utf-8"), encoding="utf-8")
    frozen = _run(mini_repo, "freeze", "--apply")
    assert frozen.returncode == 2
    assert "is retired" in frozen.stdout
    assert not (mini_repo / "operations" / "migrations").exists()
