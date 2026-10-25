#!/usr/bin/env python3
"""C2 claim-based section verification.

A locator that names a section and a PDF page makes two checkable claims:
  1. the section exists in the material (outline title or page text);
  2. it really is on the named PDF page.
Both are verified here. Also flags numeric disagreements between a route's
own title/angle and its locator (the broadcast-damage signature).
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
       "\u00df": "ss", "\u2013": "-", "\u2212": "-"}


def norm(s):
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip().lower()


ALIAS = {"source-sad-uebungen": "source-sad-ss26-lectures"}
URL_SOURCES = {"source-mit-1805", "source-mit-6034-quizzes",
               "source-cs229-problem-sets", "source-mmds-book"}
logging.getLogger("pypdf").setLevel(logging.CRITICAL)

# §1.3 Wichtige Beziehungen in der Analysis printed p. 5 (PDF p. 15)
CLAIM = re.compile(
    r"(§\s*\d+(?:\.\d+)*|Kapitel\s+\d+|Kap\.\s*\d+|Chapter\s+\d+|Serie\s+\d+|"
    r"(?:Übungs)?aufgabe\s+\d+(?:\.\d+)*)?\s*"
    r"([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9,'’\-\./ ]{2,70}?)?\s*"
    r"(?:printed\s+pp?\.\s*\d+[^()\n]{0,30})?\s*"
    r"\(\s*PDF\s+pp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*\)", re.IGNORECASE)
QUOTED_PAGE = re.compile(
    r"['\"„]([^'\"“]{4,80})['\"“][^()\n]{0,40}?\(\s*PDF\s+pp?\.\s*(\d+)",
    re.IGNORECASE)
AUF_NUM = re.compile(r"(?:Übungs)?aufgabe\s+(\d+(?:\.\d+)*)|Serie\s+(\d+)|§\s*(\d+(?:\.\d+)*)",
                     re.IGNORECASE)

_outlines = {}
_pcount = {}
_pagecache = {}


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
    hits = [p for p in (MATERIALS / ".flat").rglob("*.pdf") if norm(p.name) == n]
    if not hits:
        hits = [p for p in (MATERIALS / ".flat").rglob("*.pdf") if norm(p.name).endswith(n)]
    return hits[0] if len(hits) >= 1 else None


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


def page_text(path, pdfp):
    key = (str(path), pdfp)
    if key not in _pagecache:
        try:
            r = PdfReader(str(path))
            with contextlib.redirect_stderr(io.StringIO()):
                t = r.pages[pdfp - 1].extract_text() or ""
        except Exception as exc:
            print(f"  !! text {Path(path).name} p{pdfp}: {exc}", file=sys.stderr)
            t = ""
        _pagecache[key] = norm(t)
    return _pagecache[key]


def page_count(path):
    if str(path) not in _pcount:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _pcount[str(path)] = len(PdfReader(str(path)).pages)
        except Exception:
            _pcount[str(path)] = None
    return _pcount[str(path)]


def verify_claim(kind, label, title, pdfp, path):
    """kind: sec/kap/serie/auf. Returns (status, evidence)."""
    pc = page_count(path)
    if pc is None or (pdfp and pdfp > pc):
        return "bad-page", f"PDF p.{pdfp} vs {pc} real pages"
    ol = outline(path)
    ntitle = norm(title) if title else ""
    # 1. outline agreement
    if ntitle:
        cands = [(d, t, p) for d, t, p in ol if p and norm(t) and
                 (ntitle in norm(t) or norm(t) in ntitle)]
        if cands:
            d, t, p = cands[0]
            if pdfp and abs(p - pdfp) <= 1:
                return "ok", f"outline '{t[:50]}' -> p{p} ~ claimed p{pdfp}"
            if pdfp:
                if ntitle in page_text(path, pdfp) or norm(t) in page_text(path, pdfp):
                    return "ok", f"page {pdfp} contains '{t[:40]}' (outline says p{p})"
                return "REFUTED", (f"outline '{t[:50]}' -> p{p}, claimed p{pdfp}, "
                                   f"page {pdfp} lacks the title")
            return "ok", f"outline '{t[:50]}' -> p{p}"
        # no outline hit: page text must contain the title
        if pdfp and ntitle in page_text(path, pdfp):
            return "ok", f"page {pdfp} contains '{title[:50]}'"
        # whole document fallback (never one page)
        hits = []
        try:
            r = PdfReader(str(path))
            with contextlib.redirect_stderr(io.StringIO()):
                for i, pg in enumerate(r.pages):
                    try:
                        if ntitle in norm(pg.extract_text() or ""):
                            hits.append(i + 1)
                            if len(hits) > 3:
                                break
                    except Exception:
                        continue
        except Exception as exc:
            return "unverified", f"page scan failed: {exc}"
        if hits:
            if pdfp and pdfp not in hits:
                return "REFUTED", f"'{title[:40]}' is on pages {hits}, claimed p{pdfp}"
            return "ok", f"found on pages {hits}" + (f" ~ claimed p{pdfp}" if pdfp else "")
        if pdfp:
            return "unverified", f"'{title[:40]}' not found in doc; claimed p{pdfp}"
        return "unverified", f"'{title[:40]}' not found in doc"
    # no title: only the page anchor can be sanity-checked
    return "page-only", f"p{pdfp} within {pc} pages"


def items():
    doc = yaml.safe_load((MOD / "source-map.yaml").read_text())
    for s in doc["sources"]:
        for r in s.get("unit_routes") or []:
            yield {"kind": "route", "sid": s["source_id"], "uid": r["unit_id"],
                   "id": r["id"], "title": r.get("title", ""),
                   "angle": str(r.get("angle") or ""),
                   "text": str(r.get("locator") or "") + " \n " +
                           str(r.get("angle_detail") or ""),
                   "vault_path": r.get("vault_path")}


def main():
    out = []
    idwarn = []
    for it in items():
        if it["sid"] in URL_SOURCES:
            continue
        path = resolve(it["vault_path"]) if it["vault_path"] else None
        if path is None:
            m = re.search(r"([^\s;:|<>\"']*[^\s;:|<>\"'.,])\.pdf", it["text"], re.I)
            if m:
                path = find_pdf(m.group(1) + ".pdf")
        if path is None:
            continue
        text = it["text"]
        # claim extraction: (label, title, pdfpage)
        claims = []
        for m in CLAIM.finditer(text):
            label, title, p1, p2 = m.groups()
            if not p1:
                continue
            claims.append((label or "", title or "", int(p1)))
        for m in QUOTED_PAGE.finditer(text):
            claims.append(("", m.group(1), int(m.group(2))))
        for label, title, pdfp in claims:
            kind = "sec"
            status, ev = verify_claim(kind, label, title, pdfp, path)
            out.append({"item": it["id"], "uid": it["uid"], "sid": it["sid"],
                        "label": label, "title": title, "page": pdfp,
                        "file": path.name, "status": status, "evidence": ev})
        # broadcast signature: numbers in route title/angle vs locator
        tt = it["title"] + " " + it["angle"]
        na = set()
        for m in AUF_NUM.finditer(tt):
            na.add(next(g for g in m.groups() if g))
        nl = set()
        for m in AUF_NUM.finditer(text):
            nl.add(next(g for g in m.groups() if g))
        if na and nl and not (na & nl):
            idwarn.append({"item": it["id"], "uid": it["uid"],
                           "title_nums": sorted(na), "locator_nums": sorted(nl),
                           "title": it["title"][:80]})
    from collections import Counter
    print(Counter(o["status"] for o in out))
    json.dump({"claims": out, "idwarn": idwarn},
              open("/tmp/c2_claims.json", "w"), ensure_ascii=False, indent=1)
    for o in out:
        if o["status"] in ("REFUTED", "bad-page", "unverified"):
            print(json.dumps(o, ensure_ascii=False)[:280])
    print("--- id warnings:", len(idwarn))
    for w in idwarn[:40]:
        print(json.dumps(w, ensure_ascii=False)[:240])


if __name__ == "__main__":
    main()
