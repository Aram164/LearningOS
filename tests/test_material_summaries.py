"""Summary promotion admits structure, never judgment."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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
