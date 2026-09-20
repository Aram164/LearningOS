"""Pilot replay: the summary layer's mechanics stay reproducible.

The L06/L11 pilots live as prose records plus committed chapter drafts.
This suite replays every falsifiable part of those pilots against the
current promoter: admission still accepts the same drafts, refusal still
rejects the unpromotable range, ratios recompute, the page partition
tiles the deck, and applied findings still carry committed receipts.

Deliberately NOT asserted: the accept/reject grades themselves. Grades
are recorded observations of agent judgment, preserved verbatim in the
manifests; the suite tests the machinery and measurements behind them.

Units matter: the promoter counts Unicode characters of decoded text
while benchmarks measure UTF-8 bytes. Fixture page text is therefore
synthesized from recorded character counts; byte counts are used only
for the compression-ratio recomputation.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
FIXTURES = REPO / "tests" / "fixtures"


def _material_summarize():
    """Load the promoter as a module without running its CLI."""
    spec = importlib.util.spec_from_file_location(
        "material_summarize", TOOLS / "material_summarize.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _manifest(name: str) -> dict:
    return yaml.safe_load((FIXTURES / f"{name}.yaml").read_text(encoding="utf-8"))


def _fixture_text_cache(root: Path, digest: str, material: str,
                        total_pages: int, sizes: dict[int, int]) -> Path:
    """Build a text cache whose page files have exact character counts.

    Content carries multibyte characters so a byte-counting replay
    would visibly disagree with the recorded character counts.
    """
    cache = root / "text-cache" / digest
    cache.mkdir(parents=True)
    pattern = "Ünïcödé fixture sentence with math ∑∫√. "
    for page in range(1, total_pages + 1):
        chars = sizes.get(page, 400)
        repeats = chars // len(pattern) + 1
        (cache / f"pp-{page:04d}.txt").write_text(
            (pattern * repeats)[:chars], encoding="utf-8")
    (cache / "index.json").write_text(json.dumps(
        {"material": material, "sha256": digest, "pages": total_pages,
         "extractor": "test", "built": "2026-01-01"}))
    return root / "text-cache"


def _promote(ms, cache: Path, text: Path, draft: Path, digest: str,
             material: str, pages: str, model: str) -> int:
    return ms.main(["--promote", "--draft", str(draft),
                    "--digest", digest, "--material", material,
                    "--pages", pages, "--model", model,
                    "--text-cache", str(text), "--cache-dir", str(cache)])


def _chapter_params():
    params = []
    for name in ("pilot-l06", "pilot-l11"):
        spec = _manifest(name)
        for chapter in spec["chapters"]:
            params.append(pytest.param(spec, chapter, id=f"{name}-{chapter['draft']}"))
    return params


@pytest.mark.parametrize(("spec", "chapter"), _chapter_params())
def test_pilot_draft_replays_under_current_rules(tmp_path, capsys, spec, chapter):
    """Each committed pilot draft still promotes under today's rules."""
    ms = _material_summarize()
    start, end = chapter["pages"]
    per_page, remainder = divmod(chapter["source_chars"], end - start + 1)
    sizes = {page: per_page + (1 if page - start < remainder else 0)
             for page in range(start, end + 1)}
    text = _fixture_text_cache(tmp_path, spec["digest"], spec["material"],
                               spec["deck_pages"], sizes)
    draft = REPO / spec["draft_dir"] / chapter["draft"]
    body = draft.read_text(encoding="utf-8")
    assert len(body) == chapter["draft_chars"]
    assert len(body.encode("utf-8")) == chapter["draft_bytes"]
    cache = tmp_path / "summaries"
    code = _promote(ms, cache, text, draft, spec["digest"], spec["material"],
                    f"{start}-{end}", spec["model"])
    out, _ = capsys.readouterr()
    assert code == 0, out
    target = cache / spec["digest"] / f"pages-{start}-{end}"
    stored = (target / "summary.md").read_text(encoding="utf-8")
    assert stored.endswith(body)
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert (meta["material"], meta["sha256"], meta["page_range"],
            meta["model"], meta["scope"]) == (
        spec["material"], spec["digest"], [start, end],
        spec["model"], "chapter")


def test_pilot_tiny_range_stays_unpromotable(tmp_path, capsys):
    """L11 pp. 1-2 admit no summary: any 200-char draft exceeds 80%."""
    ms = _material_summarize()
    spec = _manifest("pilot-l11")
    (direct,) = [d for d in spec["direct_reads"] if d["pages"] == [1, 2]]
    assert direct["source_chars"] * 0.8 < 200
    start, end = direct["pages"]
    per_page, remainder = divmod(direct["source_chars"], end - start + 1)
    sizes = {page: per_page + (1 if page - start < remainder else 0)
             for page in range(start, end + 1)}
    text = _fixture_text_cache(tmp_path, spec["digest"], spec["material"],
                               spec["deck_pages"], sizes)
    draft = tmp_path / "draft.md"
    draft.write_text("Administrivia that cannot compress. " * 10, encoding="utf-8")
    assert len(draft.read_text(encoding="utf-8")) >= 200
    cache = tmp_path / "summaries"
    code = _promote(ms, cache, text, draft, spec["digest"], spec["material"],
                    f"{start}-{end}", spec["model"])
    _, err = capsys.readouterr()
    assert code == 2
    assert "80%" in err
    assert not cache.exists()


@pytest.mark.parametrize("name", ["pilot-l06", "pilot-l11"])
def test_pilot_triage_ratio_recomputes_from_files(name):
    """Recorded byte ratios match drafts + direct reads on disk."""
    spec = _manifest(name)
    draft_bytes = 0
    for chapter in spec["chapters"]:
        raw = (REPO / spec["draft_dir"] / chapter["draft"]).read_bytes()
        assert len(raw) == chapter["draft_bytes"]
        draft_bytes += len(raw)
    direct_bytes = sum(d["source_bytes"] for d in spec["direct_reads"])
    assert draft_bytes + direct_bytes == spec["triage_bytes"]
    ratio = spec["triage_bytes"] / spec["deck_bytes"]
    assert ratio == pytest.approx(spec["triage_ratio_bytes"], abs=0.001)


@pytest.mark.parametrize("name", ["pilot-l06", "pilot-l11"])
def test_pilot_partition_covers_every_page_exactly_once(name):
    """Each deck page is summary-triaged, direct-read, or excluded."""
    spec = _manifest(name)
    seen: dict[int, str] = {}

    def _claim(pages, kind):
        start, end = pages
        for page in range(start, end + 1):
            assert page not in seen, f"p{page} claimed twice"
            seen[page] = kind

    for chapter in spec["chapters"]:
        _claim(chapter["pages"], "summary")
    for direct in spec["direct_reads"]:
        _claim(direct["pages"], "direct")
    for excluded in spec["excluded"]:
        assert excluded["reason"].strip()
        _claim(excluded["pages"], "excluded")
    assert sorted(seen) == list(range(1, spec["deck_pages"] + 1))


@pytest.mark.parametrize("name", ["pilot-l06", "pilot-l11"])
def test_pilot_grades_are_recorded_observations(name):
    """Grades are preserved verbatim; their values are not asserted."""
    spec = _manifest(name)
    assert spec["chapters"]
    for chapter in spec["chapters"]:
        assert isinstance(chapter["grade"], str) and chapter["grade"].strip()


@pytest.mark.parametrize("name", ["pilot-l06", "pilot-l11"])
def test_pilot_applied_findings_carry_committed_receipts(name):
    """Each applied finding links a committed receipt with its write."""
    spec = _manifest(name)
    assert spec["receipts"]
    for expected in spec["receipts"]:
        receipt = yaml.safe_load(
            (REPO / expected["path"]).read_text(encoding="utf-8"))
        assert receipt["status"] == expected["status"] == "committed"
        assert receipt["capability"] == expected["capability"]
        actual_writes = [{"path": w["path"], "created": w["created"]}
                         for w in receipt["writes"]]
        assert actual_writes == expected["writes"]
        for artifact, after in expected["artifact_revisions_after"].items():
            assert receipt["artifact_revisions"][artifact]["after"] == after


def test_audit_flags_only_digest_mismatch(tmp_path, capsys):
    """Staleness is live-bytes-vs-digest; missing files are not stale."""
    import hashlib

    ms = _material_summarize()
    base = tmp_path / "materials"
    base.mkdir()
    live = base / "deck.pdf"
    live.write_bytes(b"%PDF-1.4 live bytes v1")
    digest = hashlib.sha256(live.read_bytes()).hexdigest()
    ranged = tmp_path / "summaries" / digest / "pages-1-2"
    ranged.mkdir(parents=True)
    (ranged / "meta.json").write_text(json.dumps(
        {"material": "deck.pdf", "sha256": digest, "page_range": [1, 2],
         "model": "test", "scope": "chapter"}))

    def _run():
        capsys.readouterr()
        code = ms.main(["--audit", "--cache-dir", str(tmp_path / "summaries"),
                        "--materials-root", str(base)])
        out, _ = capsys.readouterr()
        return code, json.loads(out)

    code, report = _run()
    assert (code, report["fresh"], report["stale"]) == (0, 1, [])
    live.write_bytes(b"%PDF-1.4 live bytes v2")
    code, report = _run()
    assert code == 1
    assert report["stale"] == [{"digest": digest, "range": "pages-1-2",
                                "material": "deck.pdf"}]
    live.unlink()
    code, report = _run()
    assert code == 0
    assert report["stale"] == []
    assert report["unverifiable"][0]["reason"] == "live material file missing"
