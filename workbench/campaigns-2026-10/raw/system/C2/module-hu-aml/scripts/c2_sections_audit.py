#!/usr/bin/env python3
"""C2 check C for module-hu-aml: named sections/TOC entries against the material.

For every route of the module:
  - extract section references (§n.n, Kapitel n, Chapter n, Serie n, Aufgabe n.m,
    quoted headings, 'slides a-b');
  - verify against the local PDF: outline titles first, then whole-document
    page text (never a single page);
  - verify slide ranges against the real page count.

Ligatures/quotes normalised, whitespace collapsed, NFC everywhere (macOS
stores filenames NFD). Sources whose locator names no farm PDF are skipped.
"""
import contextlib
import io
import json
import logging
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import yaml
from pypdf import PdfReader

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MOD = REPO / "curriculum/modules/module-hu-aml"
MATERIALS = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials")
LIG = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
       "\ufb04": "ffl", "\u2032": "'", "\u2019": "'", "\u2018": "'",
       "\u201c": '"', "\u201d": '"', "\u00c4": "Ae", "\u00d6": "Oe",
       "\u00dc": "Ue", "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
       "\u00df": "ss"}

logging.getLogger("pypdf").setLevel(logging.CRITICAL)


def norm(s):
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip().lower()


def squeeze(s):
    return re.sub(r"[\s]+", "", unicodedata.normalize("NFC", s)).lower()


_FARM = None


def farm_files():
    global _FARM
    if _FARM is None:
        _FARM = [p for p in (MATERIALS / ".flat").rglob("*.pdf",
                                                        recurse_symlinks=True)
                 if p.is_file()]
    return _FARM


def resolve(vp):
    m = re.match(r"material://([^/\s]+)/(.+)$", vp)
    if not m:
        return None
    sid, rest = m.group(1), m.group(2)
    for form in ("NFC", "NFD"):
        r2 = unicodedata.normalize(form, rest)
        for cand in (MATERIALS / ".flat" / sid / r2, MATERIALS / r2):
            if cand.is_file():
                return cand
    return None


def find_pdf(name):
    n = squeeze(name)
    for p in farm_files():
        pn = squeeze(p.name)
        if pn == n or pn.endswith(n) or n.endswith(pn):
            return p
    return None


_outlines = {}
_texts = {}
_pc = {}


def page_count(path):
    if str(path) not in _pc:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _pc[str(path)] = len(PdfReader(str(path)).pages)
        except Exception:
            _pc[str(path)] = None
    return _pc[str(path)]


def outline(path):
    if str(path) in _outlines:
        return _outlines[str(path)]
    flat = []
    try:
        r = PdfReader(str(path))

        def rec(ol, depth=0):
            for it in ol:
                if isinstance(it, list):
                    rec(it, depth + 1)
                else:
                    pg = r.get_destination_page_number(it)
                    flat.append((depth, it.title, None if pg is None else pg + 1))
        with contextlib.redirect_stderr(io.StringIO()):
            rec(r.outline)
    except Exception as exc:
        print(f"  !! outline {Path(path).name}: {exc}", file=sys.stderr)
    _outlines[str(path)] = flat
    return flat


def full_text(path):
    if str(path) in _texts:
        return _texts[str(path)]
    pages = []
    try:
        r = PdfReader(str(path))
        with contextlib.redirect_stderr(io.StringIO()):
            for pg in r.pages:
                pages.append(norm(pg.extract_text() or ""))
    except Exception as exc:
        print(f"  !! text {Path(path).name}: {exc}", file=sys.stderr)
    _texts[str(path)] = pages
    return pages


SEC_REF = re.compile(
    r"(§\s*\d+(?:\.\d+)*|Kapitel\s+\d+|Kap\.\s*\d+|Chapter\s+\d+|"
    r"Serie\s+\d+|Übungsaufgabe\s+\d+(?:\.\d+)*|Aufgabe\s+\d+(?:\.\d+)*|"
    r"slides?\s+\d+(?:\s*[-–]\s*\d+)?)", re.IGNORECASE)
QUOTED = re.compile(r"['\"„«]([^'\"“»]{6,80})['\"“»]")
SLIDES = re.compile(r"slides?\s+(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)
PDFNAME = re.compile(r"([^\s;:|<>\"']*[^\s;:|<>\"'.,])\.pdf", re.IGNORECASE)


def verify_sec(ref, path):
    nref = norm(ref)
    m = SLIDES.search(ref)
    if m:
        lo = int(m.group(1))
        hi = int(m.group(2) or m.group(1))
        pc = page_count(path)
        if pc is None:
            return "weak", "page count unavailable"
        if hi > pc:
            return "miss", f"slides up to {hi} but PDF has {pc} pages"
        return "ok", f"slides {lo}-{hi} within {pc} pages"
    ol = outline(path)
    olj = " | ".join(norm(t) for _, t, _ in ol)
    key = re.sub(r"^(?:§|kapitel|kap\.|chapter|aufgabe|serie|übungsaufgabe)\s*",
                 "", nref).strip()
    key = key.replace(" ", "")
    if key and key in olj.replace(" ", ""):
        hit = next(t for _, t, _ in ol if key in norm(t).replace(" ", ""))
        return "outline", f"outline entry: {hit[:70]}"
    body = " ".join(full_text(path))
    if key and len(key) >= 4 and key.replace(".", "") in body.replace(".", ""):
        return "text", "found in page text"
    return "miss", "not in outline nor whole-document text"


def items():
    doc = yaml.safe_load((MOD / "source-map.yaml").read_text())
    for s in doc["sources"]:
        for r in s.get("unit_routes") or []:
            yield {"kind": "route", "sid": s["source_id"], "uid": r["unit_id"],
                   "id": r["id"], "title": r.get("title", ""),
                   "text": str(r.get("locator") or "") + " \n " +
                           str(r.get("angle_detail") or ""),
                   "vault_path": r.get("vault_path")}


def main():
    results = []
    for it in items():
        path = resolve(it["vault_path"]) if it["vault_path"] else None
        if path is None:
            m = PDFNAME.search(it["text"])
            if m:
                path = find_pdf(m.group(1) + ".pdf")
        if path is None:
            continue
        refs = SEC_REF.findall(it["text"])
        quoted = [q for q in QUOTED.findall(it["text"]) if len(q.split()) >= 2]
        for ref in list(refs) + quoted[:2]:
            status, ev = verify_sec(ref, path)
            results.append({"item": it["id"], "uid": it["uid"], "sid": it["sid"],
                            "ref": ref, "file": path.name, "status": status,
                            "evidence": ev})
    print(Counter(r["status"] for r in results))
    misses = [r for r in results if r["status"] == "miss"]
    json.dump(results, open(Path(__file__).parent / "sections_results.json",
                            "w"), ensure_ascii=False, indent=1)
    print("checked:", len(results), "misses:", len(misses))
    for r in misses:
        print(json.dumps(r, ensure_ascii=False)[:260])


if __name__ == "__main__":
    main()
