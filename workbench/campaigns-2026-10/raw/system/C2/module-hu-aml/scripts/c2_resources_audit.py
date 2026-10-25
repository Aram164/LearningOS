#!/usr/bin/env python3
"""C2 stage-resource audit for module-hu-aml study maps.

E1. every material_ref.route_id exists in the module source map (no dangling).
E2. effective vault_path of a resource (own field, else inherited from route)
    resolves; and a resource's OWN vault_path must name the same file its own
    route's locator names (mismatch = the broadcast signature, bound form).
E3. unbound rows (no route_id) — counted and listed (validator's family).
E4. per unit, the route->stages carriage matrix: routes carried by every
    stage of the unit (the shape to classify against the originals).
E5. duplicate locator strings among sibling stage resources within a unit
    (grouped by route, so identical inherited locators are one group).
"""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MOD = REPO / "curriculum/modules/module-hu-aml"
MATERIALS = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials")
LIG = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
       "\ufb04": "ffl", "\u2032": "'", "\u2019": "'", "\u2018": "'",
       "\u201c": '"', "\u201d": '"'}


def norm(s):
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()


def squeeze(s):
    """NFC, lowercase, no spaces — macOS stores NFD, YAML is NFC, and
    basenames here contain spaces ('VL 01-…')."""
    return re.sub(r"[\s]+", "", unicodedata.normalize("NFC", s)).lower()


PDF_NAME = re.compile(r"([^\s;:|<>\"']*[^\s;:|<>\"'.,])\.pdf", re.IGNORECASE)


def resolve(vp):
    m = re.match(r"material://([^/\s]+)/(.+)$", vp)
    if not m:
        return None
    sid, rest = m.group(1), m.group(2)
    for form in ("NFC", "NFD"):  # macOS stores NFD, YAML is NFC
        r2 = unicodedata.normalize(form, rest)
        for cand in (MATERIALS / ".flat" / sid / r2, MATERIALS / r2):
            if cand.is_file():
                return cand
    return None


def main():
    doc = yaml.safe_load((MOD / "source-map.yaml").read_text())
    routes = {}
    for s in doc["sources"]:
        for r in s.get("unit_routes") or []:
            routes[r["id"]] = {"source_id": s["source_id"], **r}

    findings = {"dangling_route": [], "own_vp_unresolvable": [],
                "own_vp_mismatch": [], "own_vp_no_loc_file": [],
                "unbound": [], "carriage": [], "d_res_dup": []}
    n_res = 0
    per_unit_routes = defaultdict(lambda: defaultdict(set))  # uid -> rid -> stages

    for sm_path in sorted(MOD.glob("units/*/study-map.yaml")):
        unit = sm_path.parent.name
        sm = yaml.safe_load(sm_path.read_text())
        for stage in sm.get("stages") or []:
            for i, res in enumerate(stage.get("resources") or []):
                if not isinstance(res, dict):
                    continue
                n_res += 1
                ref = res.get("material_ref") or {}
                rid = ref.get("route_id")
                inherit = ref.get("inherit") or []
                if not rid:
                    findings["unbound"].append({
                        "unit": unit, "stage": stage.get("id"), "idx": i,
                        "text": str(res.get("locator") or res.get("label") or "")[:120],
                        "vault_path": res.get("vault_path")})
                    continue
                base = routes.get(rid)
                if base is None:
                    findings["dangling_route"].append({
                        "unit": unit, "stage": stage.get("id"), "idx": i,
                        "route_id": rid})
                    continue
                per_unit_routes[unit][rid].add(stage.get("id"))

                own_vp = res.get("vault_path")
                eff_vp = own_vp or (base.get("vault_path")
                                    if "vault_path" in inherit else None)
                # E2: own vault_path must resolve and match own route's locator
                if own_vp:
                    target = resolve(own_vp)
                    if target is None:
                        findings["own_vp_unresolvable"].append({
                            "unit": unit, "stage": stage.get("id"),
                            "route_id": rid, "vault_path": own_vp})
                    else:
                        loc = str(base.get("locator") or "")
                        named = [m.group(1) + ".pdf" for m in PDF_NAME.finditer(loc)]
                        if not named:
                            findings["own_vp_no_loc_file"].append({
                                "unit": unit, "stage": stage.get("id"),
                                "route_id": rid, "vault_path": own_vp,
                                "locator": loc[:140]})
                        else:
                            fb = squeeze(target.name)
                            if not any(fb.endswith(squeeze(n).split("/")[-1])
                                       or squeeze(n).split("/")[-1].endswith(fb)
                                       for n in named):
                                findings["own_vp_mismatch"].append({
                                    "unit": unit, "stage": stage.get("id"),
                                    "route_id": rid, "vault_path": own_vp,
                                    "file": target.name,
                                    "locator_names": named[:4]})

    # E4: carriage matrix
    for unit, rmap in sorted(per_unit_routes.items()):
        n_stages = len({st for sts in rmap.values() for st in sts})
        for rid, sts in sorted(rmap.items()):
            if len(sts) == n_stages and n_stages > 1:
                findings["carriage"].append({
                    "unit": unit, "route_id": rid,
                    "title": routes[rid].get("title", ""),
                    "carried_by_all": len(sts), "of_stages": n_stages})

    # E5: duplicate effective locator strings among sibling bound resources
    #     of one unit (by route id — same route on sibling stages).
    print(f"resources: {n_res}")
    for k in ("dangling_route", "own_vp_unresolvable", "own_vp_mismatch",
              "own_vp_no_loc_file", "unbound"):
        print(f"{k}: {len(findings[k])}")
        for f in findings[k][:15]:
            print("   ", json.dumps(f, ensure_ascii=False)[:220])
    print(f"carried-by-every-stage routes: {len(findings['carriage'])}")
    for c in findings["carriage"]:
        print("   ", json.dumps(c, ensure_ascii=False)[:200])

    out = Path(__file__).parent / "resources_findings.json"
    out.write_text(json.dumps({"n_resources": n_res, **findings},
                              ensure_ascii=False, indent=1))
    print("written:", out)


if __name__ == "__main__":
    main()
