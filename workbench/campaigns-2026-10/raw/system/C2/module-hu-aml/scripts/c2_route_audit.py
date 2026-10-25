#!/usr/bin/env python3
"""C2 route audit for module-hu-aml.

Checks (CAMPAIGNS.md C2):
  A. vault_path / material:// resolves and matches the file named in locator.
  A'. any local PDF file named in a locator must exist somewhere in the farm.
  B. page ranges / PDF page numbers in locator sit inside the real page count.
  B'. printed->PDF offset consistency inside one locator.
  D. duplicate locator or angle_detail among sibling routes of one
     (source_id, unit_id) group.

Read-only. Materials root is read in place from the live checkout.
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml
from pypdf import PdfReader

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MODULE = "module-hu-aml"
MAP_PATH = REPO / "curriculum/modules" / MODULE / "source-map.yaml"
MATERIALS = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials")

LIG = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
       "\ufb04": "ffl", "\u2032": "'", "\u2019": "'", "\u2018": "'",
       "\u201c": '"', "\u201d": '"'}


def norm(s: str) -> str:
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()


# file names mentioned in a locator: greedy up to .pdf, trimmed of punctuation
PDF_NAME = re.compile(r"([^\s;:|<>\"']*[^\s;:|<>\"'.,])\.pdf", re.IGNORECASE)
PDF_PAGE = re.compile(r"PDF\s+p\.\s*(\d+)", re.IGNORECASE)
PRINTED_PAIR = re.compile(
    r"printed\s+pp?\.\s*(\d+)(?:\s*[-–]\s*printed\s+pp?\.\s*(\d+))?\s*"
    r"\(\s*PDF\s+pp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*\)", re.IGNORECASE)

_pagecount_cache: dict[str, int | None] = {}


def resolve(vault_path: str) -> Path | None:
    """material://<sid>/<rest> -> materials/.flat/<sid>/<rest> (id farm)."""
    m = re.match(r"material://([^/\s]+)/(.+)$", vault_path)
    if not m:
        return None
    sid, rest = m.group(1), m.group(2)
    cand = MATERIALS / ".flat" / sid / rest
    if cand.is_file():
        return cand
    cand2 = MATERIALS / rest  # physical form
    if cand2.is_file():
        return cand2
    return None


def page_count(path: Path) -> int | None:
    key = str(path)
    if key not in _pagecount_cache:
        try:
            _pagecount_cache[key] = len(PdfReader(str(path)).pages)
        except Exception as exc:  # noqa: BLE001
            print(f"  !! pypdf failed on {path.name}: {exc}", file=sys.stderr)
            _pagecount_cache[key] = None
    return _pagecount_cache[key]


def squeeze(s: str) -> str:
    """NFC, lowercase, no spaces — macOS filenames are NFD and carry stray
    spaces ('VL 01-…'); locators are NFC."""
    return re.sub(r"[\s]+", "", unicodedata.normalize("NFC", s)).lower()


_FARM_FILES: list[Path] | None = None


def farm_files() -> list[Path]:
    global _FARM_FILES
    if _FARM_FILES is None:
        # .flat's source dirs are symlinks into the physical tree; pathlib
        # does not follow them unless recurse_symlinks is set (3.13+).
        _FARM_FILES = [p for p in
                       (MATERIALS / ".flat").rglob("*.pdf", recurse_symlinks=True)
                       if p.is_file()]
    return _FARM_FILES


def find_any_pdf(name: str) -> Path | None:
    """Suffix (space-stripped, NFC) basename search across the id farm."""
    n = squeeze(name)
    for p in farm_files():
        pn = squeeze(p.name)
        if pn == n or pn.endswith(n) or n.endswith(pn):
            return p
    return None


def main() -> None:
    doc = yaml.safe_load(MAP_PATH.read_text())
    routes = []
    for src in doc["sources"]:
        sid = src["source_id"]
        for r in src.get("unit_routes") or []:
            routes.append({"source_id": sid, **r})
    print(f"routes: {len(routes)}")

    findings = {"a_vault": [], "b_pages": [], "b_offset": [], "d_dup": [],
                "a_file_named": []}

    # ---- check D: duplicates among siblings -------------------------------
    groups = defaultdict(list)
    for r in routes:
        groups[(r["source_id"], r["unit_id"])].append(r)
    for (sid, uid), members in sorted(groups.items()):
        for field in ("locator", "angle_detail"):
            seen = defaultdict(list)
            for r in members:
                seen[norm(str(r.get(field) or ""))].append(r["id"])
            for val, ids in seen.items():
                if len(ids) > 1 and val:
                    findings["d_dup"].append({
                        "group": f"{sid} / {uid}", "field": field,
                        "route_ids": ids, "value": val[:200]})
    print(f"D duplicates: {len(findings['d_dup'])}")

    # ---- checks A and B per route -----------------------------------------
    for r in routes:
        rid, sid = r["id"], r["source_id"]
        loc = str(r.get("locator") or "")
        vp = r.get("vault_path")
        named = [m.group(1) + ".pdf" for m in PDF_NAME.finditer(loc)]

        # A: vault_path resolves; its file is among the ones the locator names
        target = None
        if vp:
            target = resolve(vp)
            if target is None:
                findings["a_vault"].append({
                    "route": rid, "issue": "vault_path does not resolve",
                    "vault_path": vp})
            else:
                base = squeeze(target.name)
                if named and not any(base.endswith(squeeze(n).split("/")[-1])
                                     or squeeze(n).split("/")[-1].endswith(base)
                                     for n in named):
                    findings["a_vault"].append({
                        "route": rid, "issue": "vault_path file not named in locator",
                        "vault_path": vp, "locator_names": named[:5]})

        # A': locator names files that do not exist anywhere on the farm
        for n in named:
            if find_any_pdf(n) is None:
                findings["a_file_named"].append({
                    "route": rid, "file": n, "source_id": sid,
                    "has_vault_path": bool(vp)})

        # B: PDF pages inside real page count
        pages = [int(x) for x in PDF_PAGE.findall(loc)]
        # "slides 3-17" style: treat as PDF pages of the deck
        for m in re.finditer(r"slides?\s+(\d+)(?:\s*[-–]\s*(\d+))?", loc, re.I):
            pages.append(int(m.group(1)))
            if m.group(2):
                pages.append(int(m.group(2)))
        # resolve the file to measure: vault target, else first named file
        measure = target
        if measure is None and named:
            measure = find_any_pdf(named[0])
        if pages and measure is not None:
            pc = page_count(measure)
            if pc is not None:
                bad = [(p, pc) for p in pages if p < 1 or p > pc]
                if bad:
                    findings["b_pages"].append({
                        "route": rid, "file": measure.name,
                        "pages_mentioned": sorted(set(pages)), "real_pages": pc,
                        "out_of_range": bad, "locator": loc[:160]})
        # B': printed->PDF offset consistency within one locator
        offs = set()
        for m in PRINTED_PAIR.finditer(loc):
            pdfs = [m.group(3)] + ([m.group(4)] if m.group(4) else [])
            for pv in pdfs:
                offs.add(int(pv) - int(m.group(1)))
        if len(offs) > 1:
            findings["b_offset"].append({
                "route": rid, "offsets": sorted(offs), "locator": loc[:200]})

    print(f"A vault unresolvable/mismatch: {len(findings['a_vault'])}")
    print(f"A' named file missing: {len(findings['a_file_named'])}")
    print(f"B out-of-range pages: {len(findings['b_pages'])}")
    print(f"B' inconsistent printed->PDF offsets: {len(findings['b_offset'])}")

    out = Path(__file__).parent / "route_findings.json"
    out.write_text(json.dumps(findings, ensure_ascii=False, indent=1))
    print("written:", out)


if __name__ == "__main__":
    main()
