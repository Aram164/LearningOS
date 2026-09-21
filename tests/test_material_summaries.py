"""Summary promotion admits structure, never judgment."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def _material_summarize():
    """Load the promoter as a module without running its CLI."""
    spec = importlib.util.spec_from_file_location(
        "material_summarize", TOOLS / "material_summarize.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DIGEST = "ab" * 32


def _text_cache(root: Path) -> Path:
    cache = root / "text-cache" / DIGEST
    cache.mkdir(parents=True)
    pages = {1: "Alpha page one. " * 40, 2: "Beta page two. " * 40,
             3: "Gamma page three. " * 40}
    for number, text in pages.items():
        (cache / f"pp-{number:04d}.txt").write_text(text, encoding="utf-8")
    (cache / "index.json").write_text(json.dumps(
        {"material": "deck/ch.pdf", "sha256": DIGEST, "pages": 3,
         "extractor": "test", "built": "2026-01-01"}))
    return root / "text-cache"


def _promote(ms, cache: Path, text: Path, draft: Path, **over):
    params = {"digest": DIGEST, "material": "deck/ch.pdf", "pages": "1-3",
              "model": "test-model 1"}
    params.update(over)
    return ms.main(["--promote", "--draft", str(draft),
                    "--digest", params["digest"], "--material", params["material"],
                    "--pages", params["pages"], "--model", params["model"],
                    "--text-cache", str(text), "--cache-dir", str(cache)])


def test_promote_keeps_draft_verbatim_with_provenance(tmp_path: Path, capsys):
    ms = _material_summarize()
    text = _text_cache(tmp_path)
    draft = tmp_path / "draft.md"
    body = "A detailed chapter compression. " * 20
    draft.write_text(body, encoding="utf-8")
    code = _promote(ms, tmp_path / "summaries", text, draft)
    out, _ = capsys.readouterr()
    assert code == 0, out
    target = tmp_path / "summaries" / DIGEST / "pages-1-3"
    stored = (target / "summary.md").read_text(encoding="utf-8")
    assert stored.endswith(body) and "GENERATED" in stored[:400]
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert "_generated" in meta
    assert (meta["material"], meta["sha256"], meta["page_range"],
            meta["model"], meta["scope"]) == (
        "deck/ch.pdf", DIGEST, [1, 3], "test-model 1", "chapter")
    assert json.loads(out)["digest"] == DIGEST


def test_promote_refuses_without_writing(tmp_path: Path, capsys):
    ms = _material_summarize()
    text = _text_cache(tmp_path)
    cache = tmp_path / "summaries"
    draft = tmp_path / "draft.md"
    draft.write_text("A detailed chapter compression. " * 20, encoding="utf-8")
    cases = [
        {"digest": "00" * 32},
        {"digest": "../../work/escape"},
        {"material": "other/ch.pdf"},
        {"pages": "2-9"},
        {"pages": "3-1"},
        {"model": ""},
    ]
    for over in cases:
        assert _promote(ms, cache, text, draft, **over) == 2
    tiny = tmp_path / "tiny.md"
    tiny.write_text("Too short.", encoding="utf-8")
    assert _promote(ms, cache, text, tiny) == 2
    huge = tmp_path / "huge.md"
    huge.write_text("x" * 100000, encoding="utf-8")
    assert _promote(ms, cache, text, huge) == 2
    capsys.readouterr()
    assert not cache.exists()


def test_promote_refuses_an_empty_source_range(tmp_path: Path, capsys):
    ms = _material_summarize()
    cache = tmp_path / "text-cache" / DIGEST
    cache.mkdir(parents=True)
    (cache / "pp-0001.txt").write_text("", encoding="utf-8")
    (cache / "index.json").write_text(json.dumps(
        {"material": "deck/ch.pdf", "sha256": DIGEST, "pages": 1,
         "extractor": "test", "built": "2026-01-01"}))
    draft = tmp_path / "draft.md"
    draft.write_text("A detailed chapter compression. " * 20, encoding="utf-8")
    code = _promote(ms, tmp_path / "summaries", tmp_path / "text-cache",
                    draft, pages="1-1")
    _, err = capsys.readouterr()
    assert code == 2
    assert "no text" in err
    assert not (tmp_path / "summaries").exists()


def test_promote_refuses_an_existing_range(tmp_path: Path, capsys):
    ms = _material_summarize()
    text = _text_cache(tmp_path)
    cache = tmp_path / "summaries"
    draft = tmp_path / "draft.md"
    draft.write_text("A detailed chapter compression. " * 20, encoding="utf-8")
    assert _promote(ms, cache, text, draft) == 0
    capsys.readouterr()
    assert _promote(ms, cache, text, draft) == 2
    _, err = capsys.readouterr()
    assert "already exists" in err


def _read_fixture(tmp_path, capsys):
    ms = _material_summarize()
    base = tmp_path / "materials"
    live = base / "deck/ch.pdf"
    live.parent.mkdir(parents=True)
    live.write_bytes(b"source identity; PDF extraction is not part of this lookup")
    digest = hashlib.sha256(live.read_bytes()).hexdigest()
    text = _text_cache(tmp_path)
    old = text / DIGEST
    index = json.loads((old / "index.json").read_text())
    index["sha256"] = digest
    (old / "index.json").write_text(json.dumps(index))
    old.rename(text / digest)
    cache = tmp_path / "summaries"
    draft = tmp_path / "draft.md"
    draft.write_text("A reusable reviewed explanation of the chapter. " * 10)
    assert _promote(ms, cache, text, draft, digest=digest) == 0
    capsys.readouterr()
    target = cache / digest / "pages-1-3"
    args = ["--read", "--material", "deck/ch.pdf", "--pages", "1-3",
            "--cache-dir", str(cache), "--materials-root", str(base)]
    return ms, live, target, digest, args


def test_repeated_summary_lookup_reuses_analysis_without_page_cache(tmp_path, capsys, monkeypatch):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)

    def no_page_cache(*args):
        pytest.fail("a summary hit must not inspect or re-extract page text")

    monkeypatch.setattr(ms, "cache_index", no_page_cache)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if "text-cache" in path.parts:
            pytest.fail("a summary hit must not read the page cache")
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "open", guarded_open)
        for _ in range(3):
            assert ms.main(args) == 0
            result = json.loads(capsys.readouterr().out)
            assert result["status"] == "hit"
            assert result["source_sha256"] == digest
            assert result["integrity"] == "verified"
            assert result["summary"] == (target / "summary.md").read_text()
            assert result["primary_evidence_required"] is True
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_summary_lookup_source_change_and_exact_scope(tmp_path, capsys):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    assert ms.main([*args, "--pages", "2-3"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "missing"
    live.write_bytes(b"new source")
    assert ms.main([*args, "--digest", digest]) == 1
    stale = json.loads(capsys.readouterr().out)
    assert stale["status"] == "stale" and "summary" not in stale
    assert ms.main(args) == 1
    missing = json.loads(capsys.readouterr().out)
    assert missing["status"] == "missing" and "summary" not in missing


def test_legacy_summary_is_preserved_and_integrity_not_invented(tmp_path, capsys):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    path = target / "meta.json"
    meta = json.loads(path.read_text())
    del meta["summary_sha256"]
    path.write_text(json.dumps(meta))
    before = path.read_bytes()
    assert ms.main(args) == 0
    assert json.loads(capsys.readouterr().out)["integrity"] == "legacy-unrecorded"
    assert path.read_bytes() == before


@pytest.mark.parametrize("damage", ["body", "material", "range", "digest", "meta",
                                    "partial", "oversize", "encoding", "escape"])
def test_summary_lookup_refuses_corrupt_or_unbounded_entries(tmp_path, capsys, damage):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    body, metadata = target / "summary.md", target / "meta.json"
    meta = json.loads(metadata.read_text())
    if damage == "body":
        body.write_text("Altered content")
    elif damage in {"material", "range", "digest"}:
        key, value = {"material": ("material", "other.pdf"),
                      "range": ("page_range", [1, 2]),
                      "digest": ("sha256", "00" * 32)}[damage]
        meta[key] = value
        metadata.write_text(json.dumps(meta))
    elif damage == "meta":
        metadata.write_text("[]")
    elif damage == "partial":
        metadata.unlink()
    elif damage == "oversize":
        body.write_bytes(b"x" * (ms.MAX_SUMMARY_BYTES + 1))
    elif damage == "encoding":
        body.write_bytes(b"\xff")
    else:
        body.unlink()
        body.symlink_to(live)
    assert ms.main(args) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "refused" and "summary" not in result


def test_summary_lookup_refuses_source_race_or_escape(tmp_path, capsys, monkeypatch):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    calls = iter([digest, "00" * 32])
    monkeypatch.setattr(ms, "sha256", lambda path: next(calls))
    assert ms.main(args) == 2
    assert "changed during lookup" in json.loads(capsys.readouterr().out)["reason"]
    assert ms.main([*args, "--material", "../outside.pdf"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "refused"


def _plant_analysis_note(mini_repo, material, digest, span, body: bytes):
    note_id = "note-adapter-demo-pp1-3"
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": "Adapter demo", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": {
                "resolution": "unresolved", "material": material,
                "recorded_source_digest": digest,
                "inspected_range": {"start": span[0], "end": span[1]},
                "frozen_input_sha256": hashlib.sha256(body).hexdigest(),
                "frozen_input_bytes": len(body)}}
    path = mini_repo / "knowledge/notes/mathematics" / f"{note_id}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body)
    return note_id, path


def test_read_prefers_durable_note_with_identical_bytes(
        mini_repo, tmp_path, capsys):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    cached = (target / "summary.md").read_bytes()
    note_id, _ = _plant_analysis_note(
        mini_repo, "deck/ch.pdf", digest, (1, 3), cached)
    cache, base = target.parent.parent, live.parent.parent
    assert ms._read_summary(cache, base, "deck/ch.pdf", (1, 3), None,
                            mini_repo) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "hit"
    assert result["store"] == "durable-note"
    assert result["note_id"] == note_id
    assert result["summary"].encode("utf-8") == cached


def test_read_falls_back_to_cache_without_durable_match(
        mini_repo, tmp_path, capsys):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    cache, base = target.parent.parent, live.parent.parent
    assert ms._read_summary(cache, base, "deck/ch.pdf", (1, 3), None,
                            mini_repo) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "hit"
    assert result["store"] == "summary-cache"
    assert result["summary"] == (target / "summary.md").read_text()


def test_read_refuses_tampered_durable_body(mini_repo, tmp_path, capsys):
    ms, live, target, digest, args = _read_fixture(tmp_path, capsys)
    _, path = _plant_analysis_note(
        mini_repo, "deck/ch.pdf", digest, (1, 3),
        (target / "summary.md").read_bytes())
    with path.open("ab") as handle:
        handle.write(b"tampered")
    cache, base = target.parent.parent, live.parent.parent
    assert ms._read_summary(cache, base, "deck/ch.pdf", (1, 3), None,
                            mini_repo) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "refused" and "summary" not in result
