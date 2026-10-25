"""C2 audit for module-hu-icop — checks A, B, C, D plus provenance diff.

A: every material:// URI and vault_path resolves to the exact file it names,
   via the system's own resolver; locator-named files match vault_path targets.
B: every locator page range lies inside the PDF's real page count (local PDFs
   only; URL-only rows are recorded as local-N/A).
C: the slide/section claims in angle_detail / objectives / done_when are
   verified against the PDFs' extracted text (ligature/quote normalisation).
D: sibling-route duplicates of locator/angle_detail, dangling route/knowledge
   references, and the live-vs-original-plan provenance diff.
"""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
sys.path.insert(0, str(REPO / "tools"))

import yaml  # noqa: E402
from learning_os.store.materials.resolution import resolve_material_target  # noqa: E402
from learning_os.store.materials.pdf_text import pdf_reader, pdf_page_text  # noqa: E402

MOD = REPO / "curriculum" / "modules" / "module-hu-icop"
UNIT = MOD / "units" / "unit-icop-l01-linear-programming"
MATERIALS = (REPO.parent / "materials").resolve()
ORIG_PLAN = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/icop-l01-2026-10-22/module-plan.yaml")

src = yaml.safe_load((MOD / "source-map.yaml").read_text())
study = yaml.safe_load((UNIT / "study-map.yaml").read_text())
unit = yaml.safe_load((UNIT / "unit.yaml").read_text())
orig = yaml.safe_load(ORIG_PLAN.read_text())

routes = {}
for s in src["sources"]:
    for r in s["unit_routes"]:
        routes[r["id"]] = {**r, "_source_id": s["source_id"]}

results = {"A": [], "B": {"rows": []}, "C": [], "D": {}, "provenance": {}}
out = Path(__file__).resolve().parent / "audit-abcd-results.json"


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    for a, b in (("ﬀ", "ff"), ("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬃ", "ffi"), ("ﬄ", "ffl"),
                 ("′", "'"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).lower()


# ---------------------------------------------------------------- provenance
print("== provenance: live vs original module-plan ==")
live_sm = {"type": src["type"], "module_id": src["module_id"],
           "sources": [{k: v for k, v in s.items() if k != "unit_routes"} for s in src["sources"]]}
orig_sm = {"type": orig["source_map"]["type"], "module_id": orig["source_map"]["module_id"],
           "sources": [{k: v for k, v in s.items() if k != "unit_routes"} for s in orig["source_map"]["sources"]]}
results["provenance"]["source_map_meta_equal"] = live_sm == orig_sm
print(f"  source_map (sans routes) equal: {live_sm == orig_sm}")

live_routes = {s["source_id"]: s["unit_routes"] for s in src["sources"]}
orig_routes = {s["source_id"]: s["unit_routes"] for s in orig["source_map"]["sources"]}
results["provenance"]["route_sets_equal"] = live_routes == orig_routes
if live_routes != orig_routes:
    for sid in sorted(set(live_routes) | set(orig_routes)):
        if live_routes.get(sid) != orig_routes.get(sid):
            l = {r["id"]: r for r in (live_routes.get(sid) or [])}
            o = {r["id"]: r for r in (orig_routes.get(sid) or [])}
            for rid in sorted(set(l) | set(o)):
                if l.get(rid) != o.get(rid):
                    lf, of = set((l.get(rid) or {}).items()), set((o.get(rid) or {}).items())
                    diff = {k for k, _ in lf ^ of}
                    print(f"  DIFF {sid}/{rid}: fields {sorted(diff)}")
                    results["provenance"].setdefault("route_field_diffs", []).append(
                        {"source": sid, "route": rid, "fields": sorted(diff)})

live_stages = study["stages"]
orig_units = orig["units"]
results["provenance"]["orig_unit_ids"] = [u.get("id") for u in orig_units]
orig_study = None
for u in orig_units:
    for key in ("study_map", "unit"):
        cand = u.get(key) if isinstance(u.get(key), dict) else None
        if cand and "stages" in cand:
            orig_study = cand
if orig_study is None:
    # stages may live directly on the unit patch
    orig_study = orig_units[0] if "stages" in orig_units[0] else {}
live_stage_map = {st["id"]: st for st in live_stages}
orig_stage_map = {st["id"]: st for st in orig_study.get("stages", [])}
print(f"  live stages: {len(live_stage_map)}, original stages: {len(orig_stage_map)}")
stage_diffs = []
for sid_ in sorted(set(live_stage_map) | set(orig_stage_map)):
    l, o = live_stage_map.get(sid_), orig_stage_map.get(sid_)
    if l is None or o is None:
        stage_diffs.append({"stage": sid_, "kind": "missing_in_live" if l is None else "missing_in_orig"})
        continue
    for k in sorted(set(l) | set(o)):
        if k in ("runtime_review", "fingerprint"):
            continue
        if l.get(k) != o.get(k):
            stage_diffs.append({"stage": sid_, "field": k})
results["provenance"]["stage_diffs"] = stage_diffs
for d in stage_diffs:
    print(f"  STAGE DIFF {d}")

# ---------------------------------------------------------------- check A
print("== A: material:// / vault_path resolution ==")


def resolve_uri(uri):
    return resolve_material_target(uri, resolution_root=MATERIALS / ".flat", boundary_root=MATERIALS)


loc_file = re.compile(r"^\s*([A-Za-z0-9_./\- ]+\.(?:pdf|png|mp4))\s*,")
for rid, r in sorted(routes.items()):
    vp = r.get("vault_path")
    if not vp:
        results["A"].append({"id": rid, "ok": None, "note": "no vault_path (url-only route)"})
        continue
    entry = {"id": rid, "vault_path": vp}
    try:
        target = resolve_uri(vp)
        entry["ok"] = True
        entry["target"] = str(target.relative_to(MATERIALS))
        m = loc_file.match(r.get("locator", ""))
        if m:
            named = m.group(1).strip()
            entry["locator_names"] = named
            entry["basename_match"] = target.name.lower() == named.lower().replace(" ", "")
            if not entry["basename_match"]:
                entry["ok"] = False
    except Exception as exc:  # noqa: BLE001
        entry["ok"] = False
        entry["error"] = str(exc)
    results["A"].append(entry)
    print(f"  {'OK  ' if entry['ok'] else 'FAIL'} {rid}: {vp} -> {entry.get('target', entry.get('error'))}")

# direct (non-route) resources: exercise bank x9 + mock exam + referenced notes
direct = [r for st in study["stages"] for r in st["resources"] if "route_id" not in r]
print(f"  direct resources (no route_id): {len(direct)}")
for r in direct:
    vp = r["vault_path"]
    p = REPO / vp
    ok = p.is_file()
    m = re.match(r"(note-[a-z0-9-]+):", r.get("locator", ""))
    id_match = (not m) or m.group(1) == p.stem
    results["A"].append({"id": r["id"], "vault_path": vp, "ok": ok and id_match,
                         "exists": ok, "locator_id_matches_stem": id_match})
    print(f"  {'OK  ' if ok and id_match else 'FAIL'} {r['id']}: {vp} exists={ok} locator-id-match={id_match}")

# artifact notes named in unit.yaml
for role, nid in unit["artifacts"].items():
    hits = list(REPO.glob(f"knowledge/**/{nid}.md"))
    results["A"].append({"id": f"artifact:{role}:{nid}", "ok": bool(hits), "found": [str(h.relative_to(REPO)) for h in hits]})
    print(f"  {'OK  ' if hits else 'FAIL'} artifact {role} {nid}: {[str(h.relative_to(REPO)) for h in hits]}")

# stage material_ref inheritance consistency
inh_fail = []
for st in study["stages"]:
    for r in st["resources"]:
        mr = r.get("material_ref")
        if not mr:
            continue
        route = routes.get(mr["route_id"])
        if route is None:
            inh_fail.append({"stage": st["id"], "resource": r["id"], "problem": "dangling route_id"})
            continue
        for f in mr.get("inherit", []):
            if f == "source_id":
                if route["_source_id"] is None:
                    inh_fail.append({"stage": st["id"], "resource": r["id"], "problem": "source_id missing"})
            elif route.get(f) is None:
                inh_fail.append({"stage": st["id"], "resource": r["id"], "field": f, "route": mr["route_id"]})
results["D"]["inherit_failures"] = inh_fail
print(f"  material_ref inherit failures: {len(inh_fail)}")

# ---------------------------------------------------------------- check B
print("== B: page ranges vs real page counts ==")
pdfs = {}
for name in ("ico_linearprogramming.pdf", "ico_organization.pdf"):
    p = MATERIALS / "algorithms/structures/icop-hu-ws2627" / name
    rd = pdf_reader(p.read_bytes())
    pdfs[name] = len(rd.pages)
    print(f"  {name}: {len(rd.pages)} pages")
for label, rel in (("korte-vygen", "optimization/korte-vygen/korte-vygen-combinatorial-optimization-5e.pdf"),
                   ("blum", "algorithms/structures/blum-algorithmen-datenstrukturen/blum-algorithmen-und-datenstrukturen-2e.pdf")):
    p = MATERIALS / rel
    rd = pdf_reader(p.read_bytes())
    pdfs[label] = len(rd.pages)
    print(f"  {label}: {len(rd.pages)} pages")
results["B"]["pdf_page_counts"] = pdfs  # noqa: present in dict form


def parse_pages(locator):
    m = re.search(r"pp\.\s*(\d+)\s*-\s*(\d+)", locator)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"pp\.\s*(\d+)\b", locator)
    if m:
        n = int(m.group(1))
        return n, n
    return None


def pdf_for_route(r):
    vp = r.get("vault_path") or ""
    if "ico_linearprogramming" in vp:
        return "ico_linearprogramming.pdf"
    if "ico_organization" in vp:
        return "ico_organization.pdf"
    if "korte-vygen" in vp:
        return "korte-vygen"
    if "blum" in vp:
        return "blum"
    return None


for rid, r in sorted(routes.items()):
    rng = parse_pages(r.get("locator", ""))
    if rng is None:
        results["B"]["rows"].append({"id": rid, "ok": None, "note": "no page range in locator"})
        continue
    label = pdf_for_route(r)
    if label is None:
        results["B"]["rows"].append({"id": rid, "range": rng, "ok": None, "note": "url-only; no local PDF"})
        continue
    n = pdfs[label]
    ok = 1 <= rng[0] <= rng[1] <= n
    results["B"]["rows"].append({"id": rid, "range": rng, "pdf": label, "pdf_pages": n, "ok": ok})
    if not ok:
        print(f"  FAIL {rid}: {rng} vs {label} {n} pages")
rows_b = results["B"]["rows"]
print(f"  page-range rows checked: {len([x for x in rows_b if x.get('ok') is not None])}, "
      f"violations: {len([x for x in rows_b if x.get('ok') is False])}")

# ---------------------------------------------------------------- check C
print("== C: angle_detail claims vs extracted text ==")
lp = pdf_reader((MATERIALS / "algorithms/structures/icop-hu-ws2627/ico_linearprogramming.pdf").read_bytes())
org = pdf_reader((MATERIALS / "algorithms/structures/icop-hu-ws2627/ico_organization.pdf").read_bytes())
kv = pdf_reader((MATERIALS / "optimization/korte-vygen/korte-vygen-combinatorial-optimization-5e.pdf").read_bytes())
blum = pdf_reader((MATERIALS / "algorithms/structures/blum-algorithmen-datenstrukturen/blum-algorithmen-und-datenstrukturen-2e.pdf").read_bytes())


def pages_of(reader, a, b):
    return {p: norm(pdf_page_text(reader, p)) for p in range(a, b + 1)}


C = []
def check(cid, ok, evidence):
    C.append({"id": cid, "ok": bool(ok), "evidence": evidence})
    print(f"  {'OK  ' if ok else 'FAIL'} {cid}: {evidence[:150]}")


def has_all(text, *needles):
    return all(norm(n) in text for n in needles)


def has_any(text, *needles):
    return any(norm(n) in text for n in needles)


lp_text = pages_of(lp, 1, 129)
org_text = pages_of(org, 1, len(org.pages))
kv_text = pages_of(kv, 68, 92)
blum_text = pages_of(blum, 228, 268)

# LP deck claims
check("lp-p23-shortest-path", has_any(lp_text[23], "shortest path", "shortest-path", "kürzester"),
      lp_text[23][:300])
check("lp-p55-vertex-question", has_all(lp_text[55], "vertex") or has_any(lp_text[55], "vertices", "extreme point"),
      lp_text[55][:300])
check("lp-p67-nondegeneracy", has_any(lp_text[67], "degener", "nondegener"),
      lp_text[67][:300])
check("lp-p87-phase1-questions", has_all(lp_text[87], "phase") or has_any(lp_text[87], "question", "?"),
      lp_text[87][:300])
check("lp-p89-bitsize", has_any(lp_text[89], "determinant", "cramer", "bit"),
      lp_text[89][:300])
check("lp-p90-kleeminty", has_any(lp_text[90], "klee", "minty"), lp_text[90][:200])
check("lp-p91-hirsch", has_any(lp_text[91], "hirsch"), lp_text[91][:200])
check("lp-p112-dual-of-dual", has_any(lp_text[112], "dual"), lp_text[112][:250])
check("lp-p114-both-infeasible", has_any(lp_text[114], "infeasible", "infeas."),
      lp_text[114][:250])
check("lp-p115-shortest-path-dual", has_any(lp_text[115], "shortest", "dual"), lp_text[115][:250])
check("lp-p125-summary", has_any(lp_text[125], "summary", "zusammenfassung", "recap"), lp_text[125][:250])
check("lp-p126-outlook", has_any(lp_text[126], "outlook", "ausblick", "next"), lp_text[126][:200])
check("lp-p128-inscribed-ball", has_any(lp_text[128], "ball", "exercise", "inscribed", "chebyshev"),
      lp_text[128][:250])
check("lp-p129-simplex-exercises", has_any(lp_text[129], "simplex", "exercise"), lp_text[129][:250])

# framing claim: pages 1-5 framing, work starts 6
framing = " ".join(lp_text[p] for p in range(1, 6))
check("lp-p1-5-framing", has_any(framing, "linear program", "lp", "overview", "organisation", "motivation"),
      framing[:250])

# organization deck claims
check("org-p12-sketches", has_any(org_text[12], "sketch", "board", "tafel", "whiteboard"), org_text[12][:250])
check("org-p15-oral-30min", has_all(org_text[15], "30") and has_any(org_text[15], "min", "minute", "mündlich", "oral", "muendlich"),
      org_text[15][:300])
check("org-p16-expectations", has_any(org_text[16], "exam", "prüfung", "definition", "proof", "exercise"),
      org_text[16][:300])

# Korte-Vygen Chapter 3
check("kv-p70-ch3-heading", has_any(kv_text[70], "linear programming", "kapitel 3", "chapter 3"), kv_text[70][:300])
kv_ex = " ".join(kv_text[p] for p in (87, 88, 89))
check("kv-p87-89-exercises", has_any(kv_ex, "exercise", "aufgabe"), kv_ex[:250])
kv_ref = " ".join(kv_text[p] for p in (89, 90))
check("kv-p89-90-references", has_any(kv_ref, "reference", "literatur", "bibliography"), kv_ref[:250])
check("kv-ch3-max-form", has_any(kv_text[70] + kv_text[71], "max"), (kv_text[70] + kv_text[71])[:250])

# Blum headings + offset
check("blum-p229-8.1", has_any(blum_text[229], "8.1", "modellierung", "modell"), blum_text[229][:300])
check("blum-p238-8.2", has_any(blum_text[238], "8.2", "simplex"), blum_text[238][:300])
check("blum-p245-start-basis", has_any(blum_text[245], "start", "basis", "phase", "zulässig", "zulaessig"),
      blum_text[245][:300])
check("blum-p249-8.3", has_any(blum_text[249], "8.3", "dual"), blum_text[249][:300])
check("blum-p255-stop-before-dual-simplex", has_any(blum_text[255], "dual") and has_any(blum_text[255] + blum_text[256], "dualsimplex", "dual simplex", "8.4"),
      blum_text[255][:250] + " || 256: " + blum_text[256][:150])
check("blum-p266-ex-8.15-16", has_any(blum_text[266], "8.15") and has_any(blum_text[266], "8.16"),
      blum_text[266][:300])
# printed-page offset claim: physical = printed + 12
offset_ok, offset_ev = None, []
for phys in (229, 238, 249, 266):
    t = blum_text[phys]
    cands = [int(x) for x in re.findall(r"\b(\d{1,3})\b", t) if 200 <= int(x) <= phys - 8]
    hit = (phys - 12) in cands
    offset_ev.append({"physical": phys, "printed_expected": phys - 12, "found_candidates": cands[:8], "hit": hit})
    offset_ok = hit if offset_ok is None else (offset_ok and hit)
check("blum-printed-offset-+12", bool(offset_ok), json.dumps(offset_ev))

# vault notes
aml_note = REPO / "knowledge/notes/machine-learning/note-aml-l06-gradient-descent.md"
aml = aml_note.read_text()
m7 = re.search(r"^#+\s*7[.\s)]", aml, re.M) or re.search(r"§7", aml)
check("aml-l06-s7-exists", bool(m7), f"heading match: {bool(m7)}")
exb = (REPO / "knowledge/notes/algorithms/note-icop-l01-exercise-bank.md").read_text()
check("exercise-bank-questions-answers", has_all(exb, "questions", "answers"), "sections found")
mock = (REPO / "knowledge/notes/algorithms/note-icop-l01-mock-exam.md").read_text()
check("mock-exam-then-answers", has_any(mock, "answer guide", "answers", "lösungen", "loesungen"), "sections found")
results["C"] = C

# ---------------------------------------------------------------- check D
print("== D: duplicates and dangling references ==")
loc_dupes = defaultdict(list)
ang_dupes = defaultdict(list)
for rid, r in routes.items():
    key = (r["_source_id"], r["unit_id"])
    loc_dupes[(r.get("locator"),)].append(rid) if False else None
    loc_dupes[r.get("locator")].append(rid)
    ang_dupes[(key, r.get("angle_detail"))].append(rid)
glob_loc_dupes = {k: v for k, v in loc_dupes.items() if len(v) > 1}
sib_ang_dupes = {f"{k[0]}::{(k[1] or '')[:60]}...": v for k, v in ang_dupes.items() if len(v) > 1}
results["D"]["duplicate_locators_any_source"] = glob_loc_dupes
results["D"]["sibling_duplicate_angle_details"] = {k: v for k, v in sib_ang_dupes.items()}
print(f"  duplicate locators (exact, any source): {len(glob_loc_dupes)}")
print(f"  sibling angle_detail duplicates (exact, within one source+unit): {len(sib_ang_dupes)}")
for k, v in sib_ang_dupes.items():
    print(f"    {len(v)} routes: {v} — {k[:120]}")

know_ids = {n["id"] for n in unit["knowledge_map"]["nodes"]}
covered = {k for r in routes.values() for k in r.get("covers", [])}
results["D"]["covers_not_in_knowledge_map"] = sorted(covered - know_ids)
results["D"]["knowledge_never_covered"] = sorted(know_ids - covered)
stage_ids = {st["id"] for st in study["stages"]}
dangling = []
for sel in unit.get("source_selections", []):
    if sel["route_id"] not in routes:
        dangling.append(("source_selections", sel["route_id"]))
    for st in sel["stage_ids"]:
        if st not in stage_ids:
            dangling.append(("source_selections-stage", st))
for st in study["stages"]:
    for r in st["resources"]:
        if "route_id" in r and r["route_id"] not in routes:
            dangling.append((st["id"], r["route_id"]))
results["D"]["dangling_references"] = dangling
print(f"  dangling references: {len(dangling)}")
print(f"  covers outside knowledge_map: {results['D']['covers_not_in_knowledge_map']}")
print(f"  knowledge nodes never covered: {results['D']['knowledge_never_covered']}")

out.write_text(json.dumps(results, indent=2, default=str))
print(f"\nwrote {out}")
