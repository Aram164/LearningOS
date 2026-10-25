"""C2 audit for module-hu-betriebssysteme — checks A, B, C, D.

A: every vault_path / material:// URI resolves, via the system's own resolver,
   to the exact file it names.
B: every locator page range lies inside the PDF's real page count.
C: the angle/angle_detail/done_when content claims are verified against the
   PDF's extracted text (system extractor + ligature/quote/dash normalisation).
D: sibling-route duplicates and dangling references (route_id, knowledge ids).
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
sys.path.insert(0, str(REPO / "tools"))

import yaml  # noqa: E402
from learning_os.store.materials.resolution import resolve_material_target  # noqa: E402
from learning_os.store.materials.pdf_text import pdf_reader, pdf_page_text  # noqa: E402

MOD = REPO / "curriculum" / "modules" / "module-hu-betriebssysteme"
MATERIALS = REPO.parent / "materials"

src = yaml.safe_load((MOD / "source-map.yaml").read_text())
study = yaml.safe_load((MOD / "units" / "unit-bs-os-structure" / "study-map.yaml").read_text())
routes = src["sources"][0]["unit_routes"]
unit = study["stages"]

results = {"A": [], "B": [], "C": [], "D": {}}

# ---------------------------------------------------------------- check A
print("== A: material:// resolution ==")
uris = sorted({r["vault_path"] for r in routes})
for uri in uris:
    try:
        target = resolve_material_target(
            uri, resolution_root=MATERIALS / ".flat", boundary_root=MATERIALS
        )
        results["A"].append({"uri": uri, "ok": True, "target": str(target.relative_to(MATERIALS.resolve()))})
        print(f"  OK   {uri} -> {target.relative_to(MATERIALS.resolve())}")
    except Exception as exc:  # noqa: BLE001
        results["A"].append({"uri": uri, "ok": False, "error": str(exc)})
        print(f"  FAIL {uri}: {exc}")
# the one direct (non-inherited) resource, the vocabulary reference
vocab = next(r for s in unit for r in s["resources"] if r["id"] == "resource-bs-vocabulary")
try:
    target = resolve_material_target(
        vocab["vault_path"], resolution_root=MATERIALS / ".flat", boundary_root=MATERIALS
    )
    print(f"  OK   vocab {vocab['vault_path']} -> {target.relative_to(MATERIALS.resolve())}")
    results["A"].append({"uri": vocab["vault_path"], "ok": True, "target": str(target.relative_to(MATERIALS.resolve()))})
except Exception as exc:  # noqa: BLE001
    print(f"  FAIL vocab: {exc}")
    results["A"].append({"uri": vocab["vault_path"], "ok": False, "error": str(exc)})

# ---------------------------------------------------------------- check B
print("== B: page ranges vs real page count ==")
pdf_path = MATERIALS / "data-systems/architecture/bs-hu-prior-slides/02_structure.pdf"
reader = pdf_reader(pdf_path.read_bytes())
n_pages = len(reader.pages)
print(f"  real page count: {n_pages}")

def parse_pages(locator):
    m = re.search(r"pp\.\s*(\d+)\s*-\s*(\d+)", locator)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"p\.\s*(\d+)\s*$", locator.strip())
    if m:
        return int(m.group(1)), int(m.group(1))
    return None

page_items = [(r["id"], r["locator"]) for r in routes] + [("resource-bs-vocabulary", vocab["locator"])]
for ident, loc in page_items:
    rng = parse_pages(loc)
    ok = rng is not None and 1 <= rng[0] <= rng[1] <= n_pages
    results["B"].append({"id": ident, "locator": loc, "range": rng, "ok": ok})
    print(f"  {'OK  ' if ok else 'FAIL'} {ident}: {loc!r} -> {rng}")

# ---------------------------------------------------------------- text + C
TRANS = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
    "\u2019": "'", "\u2018": "'", "\u2032": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u00a0": " ",
}

def norm(s: str) -> str:
    for k, v in TRANS.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).casefold()

pages = {}
for p in range(1, n_pages + 1):
    try:
        pages[p] = norm(pdf_page_text(reader, p))
    except Exception as exc:  # noqa: BLE001
        print(f"  !! extraction failed p{p}: {exc}")
        pages[p] = ""

print("== C: content claims ==")
# C1: the plan package's claim_evidence anchor quotes, on their claimed pages
orig_plan = yaml.safe_load(Path(
    "/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/bs-initial-setup-2026-10-23/module-plan.yaml"
).read_text())
for ev in orig_plan["claim_evidence"]:
    q = next(e for e in ev["evidence"] if e["kind"] == "quote")
    page, text = q["page"], norm(q["text"])
    hit = text in pages.get(page, "")
    results["C"].append({"claim": ev["claim_id"], "quote_page": page, "quote": q["text"][:60], "ok": hit})
    print(f"  {'OK  ' if hit else 'FAIL'} {ev['claim_id']}: quote on p{page}")

# C2: per-route anchors from angle/angle_detail/done_when, over the route range
ANCHORS = {
    "route-bs-os-hardware": (1, 7, ["device controller", "cpu", "memory", "bus"]),
    "route-bs-interrupts": (8, 12, ["trap", "irql", "level 2", "28"]),
    "route-bs-memory": (13, 18, ["base register", "limit register", "page", "frame", "offset"]),
    "route-bs-privileges": (19, 22, ["mode bit", "ring"]),
    "route-bs-syscall-boundary": (23, 27, ["system call", "stack", "read"]),
    "route-bs-linux-example": (28, 34, ["0x80", "sys_alarm", "errno", "alarm"]),
    "route-bs-os-structures": (35, 44, ["microkernel", "nt", "ms-dos", "unix", "bsd"]),
}
for rid, (lo, hi, anchors) in ANCHORS.items():
    blob = " ".join(pages[p] for p in range(lo, hi + 1))
    row = {"route": rid, "range": [lo, hi], "anchors": {}}
    for a in anchors:
        where = [p for p in range(lo, hi + 1) if a in pages[p]]
        row["anchors"][a] = where
        print(f"  {'OK  ' if where else 'MISS'} {rid}: {a!r} on pages {where}")
    results["C"].append(row)

# p45 (documented as closing cartoon) and p46 vocabulary
print("  -- documented dispositions --")
print(f"  p45 text length: {len(pages[45])} chars  (documented: closing cartoon)")
print(f"  p46 text length: {len(pages[46])} chars")
for a in ["dma", "synchronous", "asynchronous"]:
    print(f"  {'OK  ' if a in pages[46] else 'MISS'} p46 contains {a!r}")
results["C"].append({"p45_len": len(pages[45]), "p46_len": len(pages[46]),
                     "p46_anchors": {a: a in pages[46] for a in ["dma", "synchronous", "asynchronous"]}})

# ---------------------------------------------------------------- check D
print("== D: duplicates and dangling references ==")
route_ids = {r["id"] for r in routes}
coll_loc, coll_ang = {}, {}
for r in routes:
    coll_loc.setdefault(" ".join(r["locator"].split()), []).append(r["id"])
    coll_ang.setdefault(" ".join(r["angle_detail"].split()), []).append(r["id"])
dup_loc = {k: v for k, v in coll_loc.items() if len(v) > 1}
dup_ang = {k: v for k, v in coll_ang.items() if len(v) > 1}
print(f"  duplicate locators among siblings: {dup_loc or 'none'}")
print(f"  duplicate angle_details among siblings: {dup_ang or 'none'}")

dangling = []
for s in unit:
    for res in s["resources"]:
        mr = res.get("material_ref") or {}
        for key in ("route_id",):
            rid = mr.get(key) or res.get(key)
            if rid and rid not in route_ids:
                dangling.append((s["id"], res["id"], key, rid))
        if not mr and not res.get("source_id"):
            dangling.append((s["id"], res["id"], "no material_ref and no source_id", ""))
print(f"  dangling route refs: {dangling or 'none'}")

knowledge_files = list((REPO / "knowledge").rglob("*.yaml")) + list((REPO / "knowledge").rglob("*.md"))
knowledge_blob = "\n".join(f.read_text(errors="ignore") for f in knowledge_files)
kneed = sorted({r["covers"][0] for r in routes} | {s["knowledge_node_id"] for s in unit})
kmissing = [k for k in kneed if f"id: {k}" not in knowledge_blob]
print(f"  knowledge ids needed: {len(kneed)}, missing from knowledge/: {kmissing or 'none'}")

results["D"] = {
    "dup_locators": dup_loc, "dup_angle_details": dup_ang,
    "dangling_route_refs": dangling, "missing_knowledge_ids": kmissing,
    "n_stage_resources": sum(len(s["resources"]) for s in unit),
}

out = Path(__file__).parent / "audit-abcd-results.json"
out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"\nwrote {out}")
