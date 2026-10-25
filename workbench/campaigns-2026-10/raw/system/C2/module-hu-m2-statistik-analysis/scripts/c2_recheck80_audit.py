#!/usr/bin/env python3
"""C2-R (L2-14): re-check the M2 routes the section audit silently skipped.

Round 2. The original c2_sections_audit.py fell back to Path.rglob over
materials/.flat for routes without a vault_path; rglob returns 0 files
through the .flat symlinks, so every such route that names a PDF hit the
bare `continue` (line 182). L1-234-CLAUDE-VERDICT.md measured the gap at
80 routes. This pass, read-only, never pushing:

  1. reproduces the L1-234 partition (600 = 16 URL + 318 resolved +
     186 no-PDF + 80 target) so the audited set is the same set;
  2. indexes every PDF under the materials tree with
     os.walk(followlinks=True) (the fix the block prescribes);
  3. captures named PDFs including names with spaces (the original
     PDFNAME regex stops at the first space and mis-captures
     '...(1).pdf'-style names);
  4. attributes every page mention to the PDF named directly before it
     (segment-wise), so 'ch02.pdf ... p. 123' checks p. 123 against
     ch02.pdf, not against an arbitrary candidate;
  5. verifies section refs via outline first, then whole-document text,
     adding a dotted-numeric search (§2.6 -> '2.6') that the original's
     dot-squashing made impossible for short keys;
  6. filters quoted-heading artifacts (possessive 's ...', filenames).

Run with the clone's venv python. Output: /tmp/c2_recheck80_v2.json.
"""
import contextlib
import io
import json
import logging
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from pypdf import PdfReader

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MOD = REPO / "curriculum/modules/module-hu-m2-statistik-analysis"
MATERIALS = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials")
URL_SOURCES = {"source-mit-1805", "source-mit-6034-quizzes",
               "source-cs229-problem-sets", "source-mmds-book"}
ALIAS = {"source-sad-uebungen": "source-sad-ss26-lectures"}
LIG = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
       "\ufb04": "ffl", "\u2032": "'", "\u2019": "'", "\u2018": "'",
       "\u201c": '"', "\u201d": '"', "\u00c4": "Ae", "\u00d6": "Oe",
       "\u00dc": "Ue", "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
       "\u00df": "ss"}

SEC_REF = re.compile(
    r"(§\s*\d+(?:\.\d+)*|Kapitel\s+\d+|Kap\.\s*\d+|Chapter\s+\d+|"
    r"Serie\s+\d+|Übungsaufgabe\s+\d+(?:\.\d+)*|Aufgabe\s+\d+(?:\.\d+)*|"
    r"slides?\s+\d+(?:\s*[-–]\s*\d+)?)", re.IGNORECASE)
QUOTED = re.compile(r"['\"„«]([^'\"“»]{6,80})['\"“»]")
SLIDES = re.compile(r"slides?\s+(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)
SLIDES_COUNT = re.compile(r"(\d+)\s+slides?", re.IGNORECASE)
PAGE_MENTION = re.compile(
    r"(PDF\s+|printed\s+|Physical\s+)?pp?\.\s*([ivxlcdm]+|\d+)"
    r"(?:\s*[-–]\s*([ivxlcdm]+|\d+))?"
    r"(?:\s*\(\s*(PDF\s+|printed\s+)?pp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*\))?",
    re.IGNORECASE)
PLACEHOLDER = re.compile(r"chNN", re.IGNORECASE)
TOKEN_STOP = set(";:|<>\"',")
DELIMS = set(" \t")

logging.getLogger("pypdf").setLevel(logging.CRITICAL)
_outlines = {}
_texts = {}
_pcs = {}


def norm(s):
    s = unicodedata.normalize("NFC", s)
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip().lower()


def nospace(s):
    return re.sub(r"\s+", "", s)


def build_pdf_index():
    idx = defaultdict(set)
    seen_dirs = set()
    for root, dirs, files in os.walk(MATERIALS, followlinks=True):
        real_root = os.path.realpath(root)
        if real_root in seen_dirs:
            dirs[:] = []
            continue
        seen_dirs.add(real_root)
        for f in files:
            if f.lower().endswith(".pdf"):
                # key is space-collapsed too: lookups use the same form
                idx[nospace(norm(f))].add(os.path.realpath(Path(root) / f))
    return idx


def pdf_names_with_spans(text):
    """(position, name) per '.pdf' occurrence, scanned backwards so that
    names with spaces survive and prose between two names is not eaten."""
    out = []
    for m in re.finditer(r"\.pdf", text, re.IGNORECASE):
        e = m.start()
        toks = []
        pos = e
        for _ in range(8):
            s = pos
            while s > 0 and text[s - 1] not in TOKEN_STOP and \
                    text[s - 1] not in DELIMS:
                s -= 1
            tok = text[s:pos]
            if not tok:
                break
            toks.append(tok)
            j = s
            while j > 0 and text[j - 1] in DELIMS:
                j -= 1
            if j == s or j == 0:
                break
            pos = j
        name = clean_name(" ".join(reversed(toks)) + ".pdf")
        out.append((m.start(), name.split("/")[-1]))
    return out


def lookup_pdf(name, idx, own_sid):
    n = nospace(norm(name))
    own = ALIAS.get(own_sid, own_sid)
    own_first = lambda ps: sorted(ps, key=lambda p: (own not in p, p))
    if n in idx:
        return ("exact", own_first(idx[n]))
    stem = re.sub(r"\.pdf$", "", n)
    stem = re.sub(r"(?:\.\.\.|…|\.)+$", "", stem)
    if stem != n and len(stem) >= 6:
        hits = {p for k, ps in idx.items() if k.startswith(stem) for p in ps}
        if len(hits) == 1:
            return ("prefix", own_first(hits))
        if hits:
            return ("prefix-ambiguous", own_first(hits))
    ends = {p for k, ps in idx.items() if k.endswith(n) for p in ps}
    if ends:
        return ("suffix", own_first(ends))
    return ("none", [])


def resolve_vp(vp):
    m = re.match(r"material://([^/\s]+)/(.+)$", vp)
    if not m:
        return None
    sid, rest = ALIAS.get(m.group(1), m.group(1)), m.group(2)
    for c in (MATERIALS / ".flat" / sid / rest, MATERIALS / rest):
        if c.is_file():
            return os.path.realpath(c)
    return None


def page_count(path):
    if str(path) not in _pcs:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _pcs[str(path)] = len(PdfReader(str(path)).pages)
        except Exception:
            _pcs[str(path)] = None
    return _pcs[str(path)]


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
        print(f"  !! outline failed {Path(path).name}: {exc}", file=sys.stderr)
        _outlines[str(path)] = []
    return _outlines[str(path)]


def full_text(path):
    if str(path) in _texts:
        return _texts[str(path)]
    pages, failed = [], []
    try:
        r = PdfReader(str(path))
        with contextlib.redirect_stderr(io.StringIO()):
            for i, pg in enumerate(r.pages, 1):
                try:
                    pages.append(norm(pg.extract_text() or ""))
                except Exception:
                    pages.append("")
                    failed.append(i)
    except Exception as exc:
        print(f"  !! text failed {Path(path).name}: {exc}", file=sys.stderr)
        _texts[str(path)] = ([], [-1])
        return _texts[str(path)]
    _texts[str(path)] = (pages, failed)
    return _texts[str(path)]


def key_for(ref):
    nref = norm(ref)
    key = re.sub(r"^(?:§|kapitel|kap\.|chapter|serie|übungsaufgabe|aufgabe)\s*",
                 "", nref).strip()
    return key.replace(" ", ""), nref


def dotted_pattern(key):
    """'2.6' -> bounded dotted search; None for bare numbers."""
    if not re.fullmatch(r"\d+(?:\.\d+)+", key):
        return None
    return re.compile(r"(?<![\d.])" + re.escape(key) + r"(?![\d.])")


def verify_sec(ref, paths):
    """Best status across candidate PDFs for one ref."""
    best = ("miss", "not in outline nor whole-document text", None)
    for p in paths:
        fname = Path(p).name
        key, nref = key_for(ref)
        m = SLIDES.search(ref)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
            pc = page_count(p)
            if pc is None:
                st, ev = "inconclusive", "page count unavailable"
            elif hi > pc:
                st, ev = "miss", f"slides up to {hi} but PDF has {pc} pages"
            else:
                return ("ok", f"slides {lo}-{hi} within {pc} pages", fname)
            best = _better(best, (st, ev, fname))
            continue
        ol = outline(p)
        olj = " | ".join(norm(t) for _, t, _ in ol)
        if key and key in olj.replace(" ", ""):
            hit = next(t for _, t, _ in ol if key in norm(t).replace(" ", ""))
            strong = len(key) >= 4 or norm(hit).startswith(key)
            st = "outline" if strong else "outline-weak"
            ev = f"outline entry: {hit[:70]}"
            if st == "outline":
                return (st, ev, fname)
            best = _better(best, (st, ev, fname))
            continue
        pages, failed = full_text(p)
        body = " ".join(pages)
        if failed == [-1]:
            best = _better(best, ("inconclusive", "whole doc unreadable", fname))
            continue
        found = False
        if key and len(key) >= 4 and key.replace(".", "") in body.replace(".", ""):
            found = True
        else:
            dp = dotted_pattern(key)
            if dp and dp.search(body):
                found = True
        if found:
            return ("text", "found in whole-document text", fname)
        if not body.strip():
            best = _better(best, ("inconclusive", "no text layer (scan?)", fname))
        elif failed:
            best = _better(best, ("inconclusive",
                                  f"text extraction failed on pages {failed[:8]}",
                                  fname))
    return best


def _better(a, b):
    rank = {"ok": 5, "outline": 4, "text": 4, "outline-weak": 3,
            "inconclusive": 2, "miss": 1}
    return b if rank[b[0]] > rank[a[0]] else a


def check_pages(text, owner_paths, all_paths):
    out = []
    for m in PAGE_MENTION.finditer(text):
        pre = (m.group(1) or "").strip().lower()
        a, b = m.group(2), m.group(3)
        pa, pb = m.group(5), m.group(6)
        paren_pre = (m.group(4) or "").strip().lower()
        claim = {"text": m.group(0)[:70]}
        if re.fullmatch(r"[ivxlcdm]+", a or "", re.IGNORECASE):
            claim.update(status="roman", note="roman numbering, not count-checked")
            out.append(claim)
            continue
        if a is None:
            continue
        use_paths = owner_paths or all_paths
        if pre == "printed" and pa and paren_pre == "pdf":
            lo, hi = int(pa), int(pb or pa)
            p0 = use_paths[0]
            pc = page_count(p0)
            off = int(pa) - int(a) if a.isdigit() else None
            if pc is None:
                claim.update(status="inconclusive", note="page count unavailable")
            elif hi > pc:
                claim.update(status="out-of-range", hi=hi, pages=pc)
            else:
                claim.update(status="pair-ok", pdf=f"{lo}-{hi}", pages=pc,
                             offset=off)
            out.append(claim)
            continue
        lo, hi = int(a), int(b or a)
        fits = []
        for p in use_paths[:6]:
            pc = page_count(p)
            if pc is not None and hi <= pc:
                fits.append((Path(p).name, pc))
        if use_paths and not fits:
            pcs = {Path(p).name: page_count(p) for p in use_paths[:6]}
            claim.update(status="out-of-range", hi=hi, pages_by_file=pcs,
                         prefix=pre or "bare")
        elif fits:
            claim.update(status="in-range", range=f"{lo}-{hi}",
                         files=fits[:3], prefix=pre or "bare")
        else:
            claim.update(status="inconclusive", note="no candidate files")
        out.append(claim)
    return out


def quoted_ok(q):
    q = q.strip()
    if q.lower().endswith(".pdf"):
        return False
    if re.match(r"^s\s", q):
        return False
    return True


def items():
    doc = yaml.safe_load((MOD / "source-map.yaml").read_text())
    for s in doc["sources"]:
        for r in s.get("unit_routes") or []:
            yield {"sid": s["source_id"], "uid": r["unit_id"], "id": r["id"],
                   "title": r.get("title", ""),
                   "locator": str(r.get("locator") or ""),
                   "angle": str(r.get("angle_detail") or ""),
                   "vault_path": r.get("vault_path")}


def main():
    idx = build_pdf_index()
    print(f"pdf index: {len(idx)} names, "
          f"{sum(len(v) for v in idx.values())} files")

    part = Counter()
    targets = []
    for it in items():
        text = it["locator"] + " \n " + it["angle"]
        if it["sid"] in URL_SOURCES:
            part["url"] += 1
        elif it["vault_path"]:
            rp = resolve_vp(it["vault_path"])
            part["resolved" if rp else "vault-unresolved"] += 1
        elif PDFNAMES(text):
            part["target"] += 1
            targets.append(it)
        else:
            part["no-pdf"] += 1
    print("partition:", dict(part), "total:", sum(part.values()))

    results = []
    for it in targets:
        text = it["locator"] + " \n " + it["angle"]
        spans = pdf_names_with_spans(text)
        # dedupe by normalized key, keep first span as anchor
        seen, names_u = set(), []
        for pos, n in spans:
            k = nospace(norm(n))
            if k not in seen:
                seen.add(k)
                names_u.append((pos, n))
        lookups, missing = [], []
        key2paths = {}
        key2kind = {}
        for pos, n in names_u:
            kind, paths = lookup_pdf(n, idx, it["sid"])
            k = nospace(norm(n))
            trimmed_from = None
            if kind == "none":
                # prose prefixes ride along the name ('companion exercise
                # volume to statistik.pdf'); drop leading words until hit
                words = n.split(" ")
                for i in range(1, len(words)):
                    k2, ps2 = lookup_pdf(" ".join(words[i:]), idx, it["sid"])
                    if k2 in ("exact", "prefix", "suffix"):
                        kind, paths, trimmed_from = k2, ps2, i
                        k = nospace(norm(" ".join(words[i:])))
                        break
            key2kind[k] = kind
            key2paths[k] = paths
            lookups.append({"name": n, "match": kind, "n": len(paths),
                            "trimmed_from": trimmed_from,
                            "paths": [p.replace(str(MATERIALS) + "/", "")
                                      for p in paths[:3]]})
            if kind == "none":
                missing.append(n)
        all_paths, seenp = [], set()
        for k in [nospace(norm(n)) for _, n in names_u]:
            for p in key2paths.get(k, []):
                if p not in seenp:
                    seenp.add(p)
                    all_paths.append(p)

        def owner_paths(at):
            k = None
            for pos, n in names_u:
                if pos <= at:
                    k = nospace(norm(n))
                else:
                    break
            if k is None and names_u:
                k = nospace(norm(names_u[0][1]))
            if k is None:
                return [], "none"
            paths = key2paths.get(k, [])
            if paths:
                return paths, key2kind[k]
            return all_paths, "owner-missing"

        rec = {"id": it["id"], "sid": it["sid"], "uid": it["uid"],
               "title": it["title"][:90], "locator": it["locator"][:400],
               "angle": it["angle"][:400], "pdf_names": [n for _, n in names_u],
               "lookups": lookups, "missing_pdfs": missing,
               "n_candidate_files": len(all_paths), "claims": []}

        if not all_paths:
            rec["class"] = "pdf-not-found"
            for n in missing:
                rec["claims"].append({"type": "name", "ref": n,
                                      "status": "not-found",
                                      "evidence": "no file under materials"})
        else:
            rec["class"] = "verified"
            for m in SEC_REF.finditer(text):
                st, ev, fname = verify_sec(m.group(1), all_paths)
                rec["claims"].append({"type": "section",
                                      "ref": m.group(1)[:80], "status": st,
                                      "evidence": ev[:110], "file": fname,
                                      "at": m.start()})
            for qm in QUOTED.finditer(text):
                q = qm.group(1)
                if len(q.split()) < 2 or not quoted_ok(q):
                    continue
                st, ev, fname = verify_sec(q, all_paths)
                rec["claims"].append({"type": "quoted", "ref": q[:80],
                                      "status": st, "evidence": ev[:110],
                                      "file": fname, "at": qm.start()})
            for cm in SLIDES_COUNT.finditer(text):
                ops, kind = owner_paths(cm.start())
                if ops:
                    pc = page_count(ops[0])
                    n_sl = int(cm.group(1))
                    if pc is None:
                        st, note = "inconclusive", "page count unavailable"
                    elif n_sl == pc:
                        st, note = "count-ok", f"{n_sl} slides == {pc} pages"
                    else:
                        st, note = ("count-mismatch",
                                    f"{n_sl} claimed vs {pc} pages")
                    rec["claims"].append({"type": "slide-count",
                                          "ref": cm.group(0), "status": st,
                                          "evidence": note,
                                          "file": Path(ops[0]).name})
            for pm in PAGE_MENTION.finditer(text):
                ops, kind = owner_paths(pm.start())
                for c in check_pages(pm.group(0), ops, all_paths):
                    c["at"] = pm.start()
                    c["owner_kind"] = kind
                    rec["claims"].append(c)
        results.append(rec)

    json.dump({"partition": dict(part), "results": results},
              open("/tmp/c2_recheck80_v2.json", "w"), ensure_ascii=False,
              indent=1)

    cls = Counter(r["class"] for r in results)
    stat = Counter(c["status"] for r in results for c in r["claims"])
    print("route classes:", dict(cls))
    print("claim statuses:", dict(stat))
    print("routes:", len(results))


STOPWORDS = {"the", "and", "or", "der", "die", "das", "ein", "eine",
             "mit", "von", "und", "for", "im", "in", "am", "zum", "zur",
             "of", "a", "to", "from", "through", "matching", "with"}


def clean_name(n):
    n = n.lstrip("([{'\"«„“ ")
    words = n.split(" ")
    while len(words) > 1 and words[0].lower().strip() in STOPWORDS:
        words = words[1:]
    return " ".join(words)


def PDFNAMES(text):
    return [n for _, n in pdf_names_with_spans(text)]


if __name__ == "__main__":
    main()
