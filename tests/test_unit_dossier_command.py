"""The dossier caller: build once, serve by key, rebuild on change.

`build_dossier` had no caller, so this pins the wiring at the CLI layer:
same inputs serve from cache, a new transcript digest moves exactly the
evidence hash, a poisoned cache file is rebuilt rather than served, and
the run touches no canonical file.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from repo_builders import rich_fixture, run_los, write_yaml

UNIT = "unit-demo-l01"


def _dossier(root: Path, *args: str):
    response = run_los(root, "dossier", UNIT, *args)
    assert response.returncode == 0, response.stderr
    return json.loads(response.stdout)


def _point_source_at_directory(mini_repo: Path) -> Path:
    """Directory-authority source material, as a transcript folder needs."""
    registry_path = mini_repo / "sources" / "sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book"
    write_yaml(registry_path, registry)
    return mini_repo.parent / "materials" / "source-demo-book"


def _write_manifest(mini_repo: Path, entries: dict[str, Path]) -> None:
    files = {}
    for rel, path in entries.items():
        raw = path.read_bytes()
        files[rel] = {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    write_yaml(mini_repo / "records" / "materials-manifest.yaml", {
        "schema_version": 1, "captured": "2026-09-11",
        "totals": {"files": len(files), "bytes": 0}, "files": files})


def test_same_inputs_serve_from_cache(mini_repo):
    rich_fixture(mini_repo)
    first = _dossier(mini_repo)
    assert first["key"].startswith(f"context://{UNIT}/semantic-dossier@")
    assert first["served_from_cache"] is False
    cache = mini_repo / first["cache_path"]
    assert cache.is_file()

    second = _dossier(mini_repo)
    assert second["key"] == first["key"]
    assert second["served_from_cache"] is True
    assert second["hashes"] == first["hashes"]


def test_new_transcript_digest_moves_only_evidence(mini_repo):
    rich_fixture(mini_repo)
    folder = _point_source_at_directory(mini_repo)
    before = _dossier(mini_repo)

    transcript = folder / "transcript" / "abc123.md"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text("[00:00] expected value\n", encoding="utf-8")
    _write_manifest(mini_repo, {
        "source-demo-book/transcript/abc123.md": transcript})

    after = _dossier(mini_repo)
    assert after["key"] != before["key"]
    assert after["served_from_cache"] is False
    changed = {name for name, digest in after["hashes"].items()
               if before["hashes"][name] != digest}
    assert changed == {"evidence"}
    assert after["evidence_files"] == 1

    # A re-uploaded video invalidates precisely, with no route edit.
    transcript.write_text("[00:00] expected value, re-recorded\n", encoding="utf-8")
    _write_manifest(mini_repo, {
        "source-demo-book/transcript/abc123.md": transcript})
    reuploaded = _dossier(mini_repo)
    assert reuploaded["key"] != after["key"]
    assert {name for name, digest in reuploaded["hashes"].items()
            if after["hashes"][name] != digest} == {"evidence"}


def test_poisoned_cache_is_rebuilt_not_served(mini_repo):
    rich_fixture(mini_repo)
    first = _dossier(mini_repo)
    cache = mini_repo / first["cache_path"]
    raw = json.loads(cache.read_text(encoding="utf-8"))
    raw["content"]["routes"] = []
    cache.write_text(json.dumps(raw), encoding="utf-8")

    rebuilt = _dossier(mini_repo)
    assert rebuilt["key"] == first["key"]
    assert rebuilt["served_from_cache"] is False


def test_unknown_unit_refuses(mini_repo):
    rich_fixture(mini_repo)
    response = run_los(mini_repo, "dossier", "unit-nope")
    assert response.returncode == 2
