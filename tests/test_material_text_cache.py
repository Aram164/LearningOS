"""Digest-keyed page-text cache: extract once, read many times."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def _material_text():
    """Load the cache tool as a module without running its CLI."""
    spec = importlib.util.spec_from_file_location(
        "material_text", TOOLS / "material_text.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tiny_pdf(text: str) -> bytes:
    """One-page PDF with real extractable text; offsets computed, not guessed."""
    stream = f"BT /F1 18 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
         b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
         + stream + b"\nendstream"),
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode("latin-1")
    return bytes(out)


def _tree(base: Path, spec: dict[str, bytes | None]) -> None:
    for rel, data in spec.items():
        if data is None:
            continue
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _manifest_yaml(spec: dict[str, bytes | None]) -> str:
    files = {}
    for rel, data in spec.items():
        if data is None:
            files[rel] = {"size": 4, "sha256": "f" * 64}
        else:
            files[rel] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return yaml.safe_dump({"schema_version": 1, "captured": "2026-01-01",
                           "totals": {"files": len(files),
                                      "bytes": sum(f["size"] for f in files.values())},
                           "files": files})


def _run(mt, base: Path, manifest: Path, cache: Path, capsys, *flags):
    code = mt.main(["--manifest", str(manifest), "--materials-root", str(base),
                    "--cache-dir", str(cache), *flags])
    out, _ = capsys.readouterr()
    return code, json.loads(out)


needs_pdftotext = pytest.mark.skipif(
    shutil.which("pdftotext") is None, reason="pdftotext missing")


@needs_pdftotext
def test_build_caches_pages_and_refresh_hits(tmp_path: Path, capsys):
    mt = _material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Hello cache page one"),
            "deck-b.pdf": _tiny_pdf("Second deck text"),
            "notes.txt": b"plain text stays out",
            "gone.pdf": None}
    base = tmp_path / "materials"
    _tree(base, spec)
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(_manifest_yaml(spec), encoding="utf-8")
    cache = tmp_path / "cache"

    code, summary = _run(mt, base, manifest, cache, capsys, "--build")
    assert code == 0
    assert summary["extracted"] == 2
    assert {s["reason"] for s in summary["skipped"]} == {"not-pdf", "missing"}
    assert summary["stale"] == []
    digest_a = hashlib.sha256(spec["deck-a.pdf"]).hexdigest()
    page = cache / digest_a / "pp-0001.txt"
    assert "Hello cache page one" in page.read_text(encoding="utf-8")
    index = json.loads((cache / digest_a / "index.json").read_text(encoding="utf-8"))
    assert (index["sha256"], index["pages"]) == (digest_a, 1)

    code, summary = _run(mt, base, manifest, cache, capsys, "--refresh")
    assert code == 0
    assert (summary["cached"], summary["extracted"], summary["pruned"]) == (2, 0, 0)


@needs_pdftotext
def test_changed_bytes_invalidate_and_orphans_pruned(tmp_path: Path, capsys):
    mt = _material_text()
    first = _tiny_pdf("First edition text")
    base = tmp_path / "materials"
    _tree(base, {"deck-a.pdf": first})
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(_manifest_yaml({"deck-a.pdf": first}), encoding="utf-8")
    cache = tmp_path / "cache"
    code, _ = _run(mt, base, manifest, cache, capsys, "--build")
    assert code == 0
    old_digest = hashlib.sha256(first).hexdigest()
    assert (cache / old_digest).is_dir()

    second = _tiny_pdf("Second edition text")
    (base / "deck-a.pdf").write_bytes(second)
    code, summary = _run(mt, base, manifest, cache, capsys, "--refresh")
    assert code == 0
    assert (summary["extracted"], summary["pruned"]) == (1, 1)
    assert summary["stale"] == ["deck-a.pdf"]
    assert not (cache / old_digest).exists()
    new_digest = hashlib.sha256(second).hexdigest()
    assert "Second edition text" in (
        cache / new_digest / "pp-0001.txt").read_text(encoding="utf-8")


def test_missing_manifest_fails_cleanly(tmp_path: Path, capsys):
    mt = _material_text()
    code = mt.main(["--manifest", str(tmp_path / "absent.yaml"),
                    "--materials-root", str(tmp_path),
                    "--cache-dir", str(tmp_path / "cache")])
    capsys.readouterr()
    assert code == 2
