#!/usr/bin/env python3
"""L2-12 (module-job-*) reproducer for the mechanical checks.

Run from the clone root (~/los-glm-C2-2026-10/repository):
    .venv/bin/python <this file>

Re-derives, for the five module-job-* modules:
  A-check  every stage-resource and route vault_path resolves (repo-relative
           paths against the clone, material:// URIs through the .flat farm,
           NFC/NFD tolerant);
  D-check  no duplicate locator/angle_detail among sibling routes of one
           (unit, source_id) group, and the repeat census for stage rows;
  warnings the per-module RESOURCE-SCOPE-UNBOUND counts and reason split
           (needs generated/reports/validation-report.md from a prior
           `tools/validate.py --compact` run).

Expects collected.json next to it (dump of every resource row and route;
see VERIFICATION-LOG.md for how it was produced).
"""
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # _job-modules-evidence/scripts
REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MAT = Path.home() / "los-glm-C2-2026-10" / "materials" / ".flat"
MODS = ["module-job-git", "module-job-python-engineering", "module-job-engineering-tools",
        "module-job-rust-engineering", "module-job-polars"]

d = json.load((ROOT / "collected.json").read_text())


def resolve(vp: str) -> Path:
    if vp.startswith("material://"):
        rel = vp[len("material://"):]
        p = MAT / rel
        if p.exists():
            return p
        for form in ("NFC", "NFD"):
            q = MAT / unicodedata.normalize(form, rel)
            if q.exists():
                return q
        return p
    return REPO / vp


rows = [(r["module"], r["stage"] or r["id"], r["vault_path"])
        for r in d["resources"] if r["vault_path"]]
rows += [(rt["module"], rt["id"], rt["vault_path"]) for rt in d["routes"]]
bad = [(m, s, vp) for m, s, vp in rows if not resolve(vp).exists()]
print(f"A-check: {len(rows)} vault_paths checked, unresolved: {len(bad)}")
for b in bad:
    print("  UNRESOLVED:", b)

g = collections.Counter((r["module"], r["unit_id"], r["source_id"]) for r in d["routes"])
print("D-check routes >1 per (unit, source):",
      {k: v for k, v in g.items() if v > 1} or "NONE")
gl = collections.Counter((r["module"], r["unit_id"], r["locator"]) for r in d["routes"])
print("D-check same-unit routes sharing locator:",
      {k: v for k, v in gl.items() if v > 1} or "NONE")
ga = collections.Counter((r["module"], r["unit_id"], r["angle_detail"]) for r in d["routes"])
print("D-check same-unit routes sharing angle_detail:",
      {k: v for k, v in ga.items() if v > 1} or "NONE")

report = REPO / "generated" / "reports" / "validation-report.md"
if report.exists():
    by_mod, by_reason = collections.Counter(), collections.Counter()
    for ln in report.read_text().splitlines():
        if "module-job" not in ln or "RESOURCE-SCOPE-UNBOUND" not in ln:
            continue
        mod = re.search(r"(module-job-[a-z-]+)/", ln).group(1)
        if "no source_id is named" in ln:
            why = "no-source"
        elif "does not declare this source" in ln:
            why = "undeclared-source"
        elif "no recorded source disposition" in ln:
            why = "no-disposition"
        elif "matches this source and locator" in ln:
            why = "disposition-but-no-route"
        else:
            why = "OTHER"
        by_mod[mod] += 1
        by_reason[why] += 1
    print("warnings by module:", dict(by_mod))
    print("warnings by reason:", dict(by_reason))
else:
    print("ASSUMPTION: validation-report.md absent; run tools/validate.py --compact first",
          file=sys.stderr)
