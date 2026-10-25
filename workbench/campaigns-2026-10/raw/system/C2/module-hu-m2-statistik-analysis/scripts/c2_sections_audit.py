#!/usr/bin/env python3
"""C2 check C: named sections/TOC entries against the material itself.

For every route (and stage resource carrying its own locator) of the module:
  - extract section references (§n.n, Kapitel n, Serie n, Aufgabe n.m,
    quoted headings, 'slides a-b');
  - verify against the local PDF: outline titles first, then whole-document
    page text (never a single page);
  - verify slide ranges against the real page count.

Ligatures/quotes normalised, whitespace collapsed. URL-only sources skipped.
"""
import io
import contextlib
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from pypdf import PdfReader

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MOD = REPO / "curriculum/modules/module-hu-m2-statistik-analysis"
MATERIALS = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials")
LIG = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
       "\ufb04": "ffl", "\u2032": "'", "\u2019": "'", "\u2018": "'",
       "\u201c": '"', "\u201d": '"', "\u00c4": "Ae", "\u00d6": "Oe",
       "\u00dc": "Ue", "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
       "\u00df": "ss"}


def norm(s):
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip().lower()


ALIAS = {"source-sad-uebungen": "source-sad-ss26-lectures"}
URL_SOURCES = {"source-mit-1805", "source-mit-6034-quizzes",
               "source-cs229-problem-sets", "source-mmds-book"}

SEC_REF = re.compile(
    r"(§\s*\d+(?:\.\d+)*|Kapitel\s+\d+|Kap\.\s*\d+|Chapter\s+\d+|"
    r"Serie\s+\d+|Übungsaufgabe\s+\d+(?:\.\d+)*|Aufgabe\s+\d+(?:\.\d+)*|"
    r"slides?\s+\d+(?:\s*[-–]\s*\d+)?)", re.IGNORECASE)
QUOTED = re.compile(r"['\"„«]([^'\"“»]{6,80})['\"“»]")
SLIDES = re.compile(r"slides?\s+(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)
PDFNAME = re.compile(r"([^\s;:|<>\"']*[^\s;:|<>\"'.,])\.pdf", re.IGNORECASE)

logging.getLogger("pypdf").setLevel(logging.CRITICAL)
_outlines = {}
_texts = {}


def resolve(vp):
    m = re.match(r"material://([^/\s]+)/(.+)$", vp)
    if not m:
        return None
    sid, rest = ALIAS.get(m.group(1), m.group(1)), m.group(2)
    for c in (MATERIALS / ".flat" / sid / rest, MATERIALS / rest):
        if c.is_file():
            return c
    return None


def find_pdf(name):
    n = norm(name)
    for p in (MATERIALS / ".flat").rglob("*.pdf"):
        pn = norm(p.name)
        if pn == n or pn.endswith(n):
            return p
    return None


def outline(path):
    if str(path) in _outlines:
        return _outlines[str(path)]
    try:
        r = PdfReader(str(path))
        flat = []

        def rec(ol, depth=0):
            for it in ol:
                if isinstance(it, list):
                    rec(it, depth + 1)
                else:
                    flat.append((depth, it.title,
                                 r.get_destination_page_number(it) + 1))
        with contextlib.redirect_stderr(io.StringIO()):
            rec(r.outline)
        _outlines[str(path)] = flat
    except Exception as exc:
        print(f"  !! outline failed {path.name}: {exc}", file=sys.stderr)
        _outlines[str(path)] = []
    return _outlines[str(path)]


def full_text(path):
    if str(path) in _texts:
        return _texts[str(path)]
    try:
        r = PdfReader(str(path))
        pages = []
        with contextlib.redirect_stderr(io.StringIO()):
            for pg in r.pages:
                pages.append(norm(pg.extract_text() or ""))
        _texts[str(path)] = pages
    except Exception as exc:
        print(f"  !! text failed {path.name}: {exc}", file=sys.stderr)
        _texts[str(path)] = []
    return _texts[str(path)]


def verify_sec(ref, path):
    """Return (status, evidence). status in ok / outline / text / miss / weak."""
    nref = norm(ref)
    ol = outline(path)
    # slide refs verified by page count
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
    # § / Kapitel / Aufgabe / Serie: outline title match
    olj = " | ".join(norm(t) for _, t, _ in ol)
    key = re.sub(r"^(?:§|kapitel|kap\.|chapter|aufgabe|serie|übungsaufgabe)\s*",
                 "", nref).strip()
    key = key.replace(" ", "")
    if key and key in olj.replace(" ", ""):
        hit = next(t for _, t, _ in ol if key in norm(t).replace(" ", ""))
        return "outline", f"outline entry: {hit[:70]}"
    # fall back to whole-document text (quoted heading case)
    body = " ".join(full_text(path))
    if key and len(key) >= 4 and key.replace(".", "") in body.replace(".", ""):
        return "text", "found in page text"
    return "miss", "not in outline nor whole-document text"


_pc = {}


def page_count(path):
    if str(path) not in _pc:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _pc[str(path)] = len(PdfReader(str(path)).pages)
        except Exception:
            _pc[str(path)] = None
    return _pc[str(path)]


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
        if it["sid"] in URL_SOURCES:
            continue
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
    from collections import Counter
    print(Counter(r["status"] for r in results))
    misses = [r for r in results if r["status"] == "miss"]
    json.dump(results, open("/tmp/c2_sections.json", "w"), ensure_ascii=False, indent=1)
    print("misses:", len(misses))
    for r in misses[:80]:
        print(json.dumps(r, ensure_ascii=False)[:260])


if __name__ == "__main__":
    main()
