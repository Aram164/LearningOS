"""Build the four L2-16 --check packages for module-hu-m2-statistik-analysis.

Run with the clone's venv from the repository root:
    .venv/bin/python work/active/workspace-m2-l2-16-packages-2026-10-25/build_packages.py

Writes the plan packages and coverage audits next to itself. Never applied:
--check only, per Aram's kickoff for item L2-16.
"""
from __future__ import annotations

import copy
import hashlib
import warnings
from pathlib import Path

import yaml
from pypdf import PdfReader

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
MOD = "module-hu-m2-statistik-analysis"
WS = Path(__file__).resolve().parent / "outputs"
WS.mkdir(exist_ok=True)
AUDIT_DIR = "work/active/workspace-m2-l2-16-packages-2026-10-25/outputs"
SM_PATH = ROOT / f"curriculum/modules/{MOD}/source-map.yaml"

CHECKS = {
    "local_inventory_complete": True,
    "linked_inventory_complete": True,
    "materials_opened_and_content_checked": True,
    "current_and_prior_scope_reconciled": True,
    "duplicates_and_numbering_checked": True,
    "exclusions_and_unresolved_gaps_recorded": True,
}

INGMATH_URI = "material://source-analysis-drill-blaetter-extern/IngMath2_Aufgaben.pdf"
VL09_URI = "material://source-aml-ss26-lectures/lecture-slides/VL 09-neural-networks.pdf"


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def dump(data) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def page_span(pdf: str, page: int, upto: int) -> str:
    reader = PdfReader(pdf)
    text = reader.pages[page - 1].extract_text() or ""
    return text[:upto].strip()


def contract(audit: str) -> dict:
    return {
        "version": 2,
        "plan_template_version": 1,
        "coverage_audit": f"{AUDIT_DIR}/{Path(audit).name}",
        "checks": dict(CHECKS),
        "intentional_reorders": [],
    }


# --------------------------------------------------------------------------- P1
def build_p1() -> dict:
    sm = yaml.safe_load(SM_PATH.read_text(encoding="utf-8"))
    routes = {}
    for src in sm["sources"]:
        for r in src.get("unit_routes", []):
            routes.setdefault(r["unit_id"], {})[r["id"]] = {"source_id": src["source_id"], **r}

    units = []
    bound = 0
    for n in (3, 4, 5, 6, 7):
        uid = f"unit-m2-analysis-ch0{n}"
        unit = yaml.safe_load(
            (ROOT / f"curriculum/modules/{MOD}/units/{uid}/unit.yaml").read_text(encoding="utf-8"))
        mp = yaml.safe_load(
            (ROOT / f"curriculum/modules/{MOD}/units/{uid}/study-map.yaml").read_text(encoding="utf-8"))
        for stage in mp["stages"]:
            for i, res in enumerate(stage.get("resources", [])):
                if not isinstance(res, dict) or res.get("route_id") or "material_ref" in res:
                    continue
                if res.get("kind") == "reference":
                    continue
                hits = [rid for rid, r in routes[uid].items()
                        if r.get("title") == res.get("label") and r.get("locator") == res.get("locator")]
                assert len(hits) == 1, (uid, stage["id"], res.get("label"))
                route = routes[uid][hits[0]]
                inherit = ["label", "source_id", "locator", "angle", "angle_detail"]
                if res.get("vault_path") is not None:
                    assert res.get("vault_path") == route.get("vault_path"), (uid, stage["id"])
                    inherit.append("vault_path")
                new = {"material_ref": {"route_id": hits[0], "inherit": inherit}}
                for key, value in res.items():
                    if key not in inherit:
                        new[key] = value
                stage["resources"][i] = new
                bound += 1
        units.append({"unit": unit, "study_map": mp})
    assert bound == 472, bound
    return {
        "module_id": MOD,
        "plan_contract": contract(
            "work/active/workspace-m2-l2-16-packages-2026-10-25/audit-p1-binding-2026-10-25.md"),
        "units": units,
    }


# --------------------------------------------------------------------------- P2
F1_RID = "route-b3e5bcb8f3813cbc477ac799"
F1_OLD = ("lecture-slides/VL 08-feedforward-neural-network.pdf and "
          "VL 09-training-neural-networks.pdf")
F1_NEW = ("lecture-slides/VL 08-feedforward-neural-network.pdf; "
          "lecture-slides/VL 09-neural-networks.pdf")


def edited_source_map(edits: dict[str, str]) -> dict:
    sm = yaml.safe_load(SM_PATH.read_text(encoding="utf-8"))
    seen = set()
    for src in sm["sources"]:
        for r in src.get("unit_routes", []):
            if r["id"] in edits:
                assert r.get("locator") == edits[r["id"]][0], r["id"]
                r["locator"] = edits[r["id"]][1]
                seen.add(r["id"])
    assert seen == set(edits), seen ^ set(edits)
    return sm


def build_p2() -> dict:
    quote = page_span(
        "../materials/machine-learning/classical/aml-ss26-lectures/lecture-slides/VL 09-neural-networks.pdf",
        2, 160)
    return {
        "module_id": MOD,
        "plan_contract": contract(
            "work/active/workspace-m2-l2-16-packages-2026-10-25/audit-p2-aml-l09-2026-10-25.md"),
        "source_map": edited_source_map({F1_RID: (F1_OLD, F1_NEW)}),
        "claim_evidence": [{
            "claim_id": f"covers:{F1_RID}",
            "evidence": [{
                "kind": "quote",
                "ref": VL09_URI,
                "text": quote,
                "page": 2,
                "note": ("the deck the corrected locator names; its own title slide pair p. 1-2 reads "
                         "'Training Feedforward Neural Networks' / 'Training Neural Networks', and "
                         "module-hu-aml binds the same file for unit-aml-l09 as "
                         "'VL 09-neural-networks.pdf (74 pages)'"),
            }],
        }],
    }


# --------------------------------------------------------------------------- P3
P3_EDITS = {
    "route-an-ch05-analysisdrillblaetterext-2": (
        "IngMath2_Aufgaben.pdf: Kap. 11 Stetige Funktionen p. 75 (§11.1 Motivation und Definition p. 75, "
        "§11.2 Eigenschaften stetiger reeller Funktionen p. 85, §11.3 Gleichmäßige Stetigkeit p. 90, "
        "§11.4 Grenzwerte von Funktionen p. 92); §12.3 Exponentialfunktion, Logarithmusfunktion p. 118. "
        "§12.2 Potenzreihen matches the §5.8 Exkurs and is skipped.",
        "IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg 1991): Kap. 11 Stetige Funktionen PDF p. 78 "
        "(printed p. 75) (§11.1 Motivation und Definition PDF p. 78 (printed p. 75), §11.2 Eigenschaften "
        "stetiger reeller Funktionen PDF p. 88 (printed p. 85), §11.3 Gleichmäßige Stetigkeit PDF p. 93 "
        "(printed p. 90), §11.4 Grenzwerte von Funktionen PDF p. 95 (printed p. 92)), §12.3 "
        "Exponentialfunktion, Logarithmusfunktion PDF p. 121 (printed p. 118). §12.2 Potenzreihen matches "
        "the §5.8 Exkurs and is skipped.",
    ),
    "route-an-ch06-analysisdrillblaetterext": (
        "IngMath2_Aufgaben.pdf: Kap. 13 Differenzierbare reelle Funktionen p. 127 (§13.1 Motivation und "
        "Definition p. 127, §13.2 Rechenregeln p. 132); Kap. 14 Anwendungen der Differentialrechnung p. 140 "
        "(§14.1 Mittelwertsätze p. 140, §14.2 Regeln von de l'Hospital p. 150, §14.3 Der Satz von Taylor "
        "p. 158, §14.4 Kurvendiskussion p. 180, §14.5 Noch einmal Polynominterpolation p. 190). Kap. 15 "
        "(numerische Lösung von Gleichungen) parallels the §6.6 Exkurs and is skipped.",
        "IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg 1991): Kap. 13 Differenzierbare reelle Funktionen "
        "PDF p. 130 (printed p. 127) (§13.1 Motivation und Definition PDF p. 130 (printed p. 127), §13.2 "
        "Rechenregeln PDF p. 135 (printed p. 132)), Kap. 14 Anwendungen der Differentialrechnung PDF p. 143 "
        "(printed p. 140) (§14.1 Mittelwertsätze PDF p. 143 (printed p. 140), §14.2 Regeln von de "
        "l'Hospital PDF p. 153 (printed p. 150), §14.3 Der Satz von Taylor PDF p. 161 (printed p. 158), "
        "§14.4 Kurvendiskussion PDF p. 183 (printed p. 180), §14.5 Noch einmal Polynominterpolation "
        "PDF p. 193 (printed p. 190)). Kap. 15 (numerische Lösung von Gleichungen) parallels the §6.6 "
        "Exkurs and is skipped.",
    ),
    "route-an-ch07-analysisdrillblaetterext": (
        "IngMath2_Aufgaben.pdf: Kap. 16 Das bestimmte Riemannsche Integral p. 219 (§16.1 Definition p. 219, "
        "§16.2 Integrierbarkeitskriterien p. 221, §16.3 Klassen integrierbarer Funktionen p. 225, §16.4 "
        "Rechenregeln p. 227); Kap. 17 Das unbestimmte Integral p. 234 (§17.1 Fundamentalsatz p. 234, "
        "§17.2 Partielle Integration p. 238, §17.3 Substitutionsregel p. 245, §17.4 Partialbruchzerlegung "
        "p. 246); Kap. 18 Uneigentliche Integrale p. 252 (§18.1 unbeschränkte Intervalle p. 252, §18.2 "
        "unbeschränkte Integranden p. 265). Kap. 19-20 (numerische Integration, Anwendungen) parallel the "
        "§7.4 Exkurs and are skipped.",
        "IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg 1991): Kap. 16 Das bestimmte Riemannsche Integral "
        "PDF p. 222 (printed p. 219) (§16.1 Definition PDF p. 222 (printed p. 219), §16.2 "
        "Integrierbarkeitskriterien PDF p. 224 (printed p. 221), §16.3 Klassen integrierbarer Funktionen "
        "PDF p. 228 (printed p. 225), §16.4 Rechenregeln PDF p. 230 (printed p. 227)), Kap. 17 Das "
        "unbestimmte Integral PDF p. 237 (printed p. 234) (§17.1 Fundamentalsatz PDF p. 237 (printed "
        "p. 234), §17.2 Partielle Integration PDF p. 241 (printed p. 238), §17.3 Substitutionsregel "
        "PDF p. 248 (printed p. 245), §17.4 Partialbruchzerlegung PDF p. 249 (printed p. 246)), Kap. 18 "
        "Uneigentliche Integrale PDF p. 255 (printed p. 252) (§18.1 unbeschränkte Intervalle PDF p. 255 "
        "(printed p. 252), §18.2 unbeschränkte Integranden PDF p. 268 (printed p. 265)). Kap. 19-20 "
        "(numerische Integration, Anwendungen) parallel the §7.4 Exkurs and are skipped.",
    ),
}

P3_QUOTES = {
    "route-an-ch05-analysisdrillblaetterext-2": (
        78, "Kapitel 11\nStetige Funktionen\n11.1 Motivation und Deﬁnition\nAufgabe 11.1 a) Zeigen Sie "
        "(unter Benutzung der geometrischen Deﬁnitionen),",
        "the page the corrected §11.1 anchor names; the page header carries the printed book number 75, "
        "so the PDF position is printed + 3 for this book (RECHECK-80 F2)"),
    "route-an-ch06-analysisdrillblaetterext": (
        161, "158 KAPITEL 14. ANWENDUNGEN DER DIFFERENTIALRECHNUNG\n14.3 Der Satz von Taylor",
        "the page the corrected §14.3 anchor names; its header carries the printed number 158, "
        "confirming the +3 offset measured in RECHECK-80 F2"),
    "route-an-ch07-analysisdrillblaetterext": (
        222, "Kapitel 16\nDas bestimmte Riemannsche\nIntegral\n16.1 Deﬁnition des Riemann Integrals",
        "the page the corrected §16.1 anchor names; the printed book number 219 is on the facing header "
        "sequence, the PDF position is printed + 3 per RECHECK-80 F2"),
}


def build_p3() -> dict:
    pdf = "../materials/mathematics/analysis/analysis-drill-blaetter-extern/IngMath2_Aufgaben.pdf"
    evidence = []
    for rid, (page, text, note) in P3_QUOTES.items():
        observed = page_span(pdf, page, len(text) + 80)
        assert text.split("\n")[0] in observed, (rid, observed[:80])
        evidence.append({
            "claim_id": f"covers:{rid}",
            "evidence": [{
                "kind": "quote", "ref": INGMATH_URI, "text": text, "page": page, "note": note,
            }],
        })
    return {
        "module_id": MOD,
        "plan_contract": contract(
            "work/active/workspace-m2-l2-16-packages-2026-10-25/audit-p3-ingmath2-2026-10-25.md"),
        "source_map": edited_source_map(P3_EDITS),
        "claim_evidence": evidence,
    }


# --------------------------------------------------------------------------- P4
def build_p4() -> dict:
    uid = "unit-m2-combined-exam-rehearsal"
    sm = yaml.safe_load(SM_PATH.read_text(encoding="utf-8"))
    by_source = {}
    for src in sm["sources"]:
        for r in src.get("unit_routes", []):
            if r["unit_id"] == uid:
                assert src["source_id"] not in by_source, src["source_id"]
                by_source[src["source_id"]] = r["id"]
    unit = yaml.safe_load(
        (ROOT / f"curriculum/modules/{MOD}/units/{uid}/unit.yaml").read_text(encoding="utf-8"))
    mp = yaml.safe_load(
        (ROOT / f"curriculum/modules/{MOD}/units/{uid}/study-map.yaml").read_text(encoding="utf-8"))
    bound = 0
    for stage in mp["stages"]:
        for i, res in enumerate(stage.get("resources", [])):
            if not isinstance(res, dict) or res.get("route_id") or "material_ref" in res:
                continue
            if res.get("kind") == "reference":
                continue
            sid = res.get("source_id")
            assert sid in by_source, (stage["id"], sid)
            new = {"material_ref": {"route_id": by_source[sid], "inherit": ["source_id"]}}
            for key, value in res.items():
                if key != "source_id":
                    new[key] = value
            stage["resources"][i] = new
            bound += 1
    assert bound == 9, bound
    return {
        "module_id": MOD,
        "plan_contract": contract(
            "work/active/workspace-m2-l2-16-packages-2026-10-25/audit-p4-rehearsal-2026-10-25.md"),
        "units": [{"unit": unit, "study_map": mp}],
    }


# ---------------------------------------------------------------------- audits
AUDITS = {
"audit-p1-binding-2026-10-25.md": """# Coverage audit — ch03–ch07 stage-binding migration (L2-16, 2026-10-25)

Scope: rebind the 472 unbound non-reference stage resources of the five
Analysis chapter units to the routes declared for their own unit, as
unit-m2-analysis-ch01 and -ch02 already are. No route changes, no scope
changes, no stage or resource additions or removals, no renumbering. The
migration is acting on critique point 1 (boundary 17), authorised by Aram's
kickoff for item L2-16; prepared as `--check` only, never applied.

## Local

- The five study maps read whole from
  `curriculum/modules/module-hu-m2-statistik-analysis/units/unit-m2-analysis-ch03..ch07/study-map.yaml`;
  the source map read whole from `curriculum/modules/{mod}/source-map.yaml`
  (97 sources, 600 routes).
- Every unbound non-reference row (ch03: 86, ch04: 69, ch05: 129, ch06: 127,
  ch07: 61; 472 total, matching CLAUDE-VERDICT.md) was matched against its
  unit's declared routes by exact (label, locator) equality. Each matched
  exactly one route; zero rows unmatched, zero ambiguous.
- The binding rule is the one ch01/ch02 already implement, verified
  mechanically: a stage binds a route exactly when the route's `covers` names
  the stage's knowledge id. ch01: 25 actual = 25 derived; ch02: 71 = 71.
  Applied to ch03–ch07 the same derivation places every one of the 472 rows
  on the stage it already sits on (row placement == covers placement, 0
  deviations), so no resource moves between stages.
- Field equality checked per row: `angle` and `angle_detail` equal the
  matched route's on all 472 rows; `vault_path` equals the route's on 349
  rows and is absent on both sides for the other 123. No row carries a value
  the route lacks, so every binding inherits
  [label, source_id, locator, angle, angle_detail] (+ vault_path where
  present) and the expanded effective map is unchanged except for the added
  `route_id`/`source_id`.
- Materials opened: the tree was validated through the module's own checks in
  the C2 session (all 318 vault_paths resolve, 0 page-range violations) and
  the C2-R re-check; no new material claims are introduced by this package.

## Linked

- All 97 sources and all 600 routes are carried forward untouched: the
  package contains no `source_map`, no `source_patches`, no route identity,
  covers or locator changes. Routes with `covers` but no stage row
  (route-an-ch03/04/05/06/07-henningdierks, route-an-ch03/05/06-wrathofmath —
  8 routes) remain unplaced; adding stage resources for them is a scope
  decision and is out of scope here.

## Completeness

- Every unbound teaching row of the five units is bound to a route declared
  for its own unit; after the package the module's 472
  RESOURCE-SCOPE-UNBOUND warnings of the ch03–ch07 family are gone and no
  resource's material, angle, kind or triage changes.
- Duplicates: the package introduces none — each row binds a distinct
  (stage, route) pair; the three template `angle_detail` pairs among sibling
  routes recorded by the C2 report (F4) are route-level history, untouched.
- Exclusions and unresolved gaps: the 14 potential (route, stage) pairs for
  the 8 never-placed routes named under Linked are excluded as new scope, not
  repair; the 9 prose rows of unit-m2-combined-exam-rehearsal are a separate
  confirmed family, packaged separately (P4).
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
""".format(mod=MOD),

"audit-p2-aml-l09-2026-10-25.md": """# Coverage audit — AML L09 deck name repair, route-b3e5bcb8 (L2-16, 2026-10-25)

Scope: one locator edit on one route of unit-m2-sad-l15, source
source-aml-ss26-lectures, confirmed as RECHECK-80 finding F1 (original
defect, not damage). `--check` only, never applied.

## Local

- The route read whole from
  `curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml`
  (route-b3e5bcb8f3813cbc477ac799, locator verbatim: "lecture-slides/
  VL 08-feedforward-neural-network.pdf and VL 09-training-neural-networks.pdf").
- The materials tree indexed by symlink-aware walk (527 PDFs):
  `VL 08-feedforward-neural-network.pdf` exists;
  `VL 09-training-neural-networks.pdf` exists nowhere; the real AML deck is
  `machine-learning/classical/aml-ss26-lectures/lecture-slides/VL
  09-neural-networks.pdf` (74 pages). Both files opened with pypdf: VL 09
  pp. 1-2 read (title pair "Training Feedforward Neural Networks" /
  "Training Neural Networks"); the deck's sha256 matches the registered
  materials manifest entry.
- module-hu-aml's own binding for the same deck read from its unit.yaml
  (unit-aml-l09: "VL 09-neural-networks.pdf (74 pages)") — the name M2's
  route should carry.
- Resolution checked with the repository's own resolver: the old locator
  resolves to zero files (two .pdf tokens defeat
  `leading_material_locator`; no vault_path); the corrected locator resolves
  to exactly the two real decks under the module's semicolon two-file
  convention (the same shape the module's L03 exercise route uses).

## Linked

- The five stage rows of unit-m2-sad-l15 that inherit this route's locator
  (stage-sad-l15-activation/-output/-forward/-backprop/-training, all
  material_ref rows) update automatically; their study map is not edited.
- No other route names the wrong deck (checked across all 600 routes of the
  module: 6 occurrences in the historical generated plans under
  work/active/workspace-m2-exam-prep/outputs/, all pre-canonical history;
  exactly one canonical route carries it).

## Completeness

- The locator's wrong filename is corrected and the two-deck promise becomes
  resolvable; the wording change is limited to the separator ("and" → ";",
  the module's own multi-file convention) and the one wrong filename token.
  The route's title, angle, angle_detail, covers, depth and scope are
  untouched.
- Evidence for the covers change: a verified quote from VL 09
  p. 2 (the deck's own subject matter), embedded in the package's
  claim_evidence as `covers:route-b3e5bcb8f3813cbc477ac799`.
- Exclusions: none. Unresolved gaps: none — the previously unreachable
  material becomes reachable under the corrected name.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
""".format(),

"audit-p3-ingmath2-2026-10-25.md": """# Coverage audit — IngMath2 printed-page anchors, three routes (L2-16, 2026-10-25)

Scope: page-anchor corrections on the three drill routes named by RECHECK-80
finding F2 (route-an-ch05-analysisdrillblaetterext-2,
route-an-ch06-analysisdrillblaetterext, route-an-ch07-analysisdrillblaetterext).
`--check` only, never applied.

## Local

- `IngMath2_Aufgaben.pdf` (312 pp) opened with pypdf end to end for the cited
  range (PDF pp. 75-270); the printed book page number is carried in each
  page's header, and the PDF position is printed + 3 throughout the cited
  span (title page + two Inhaltsverzeichnis pages), reproducing RECHECK-80
  F2's six measurements and extending them: all 28 section anchors named by
  the three locators were verified at printed + 3 (§11.1 75→78, §11.2 85→88,
  §11.3 90→93, §11.4 92→95, §12.3 118→121, §13.1 127→130, §13.2 132→135,
  §14.1 140→143, §14.2 150→153, §14.3 158→161, §14.4 180→183, §14.5 190→193,
  §16.1 219→222, §16.2 221→224, §16.3 225→228, §16.4 227→230, §17.1 234→237,
  §17.2 238→241, §17.3 245→248, §17.4 246→249, §18.1 252→255, §18.2 265→268,
  and the five chapter starts). Each heading's text was found on the expected
  PDF page; each page also displays the printed number.
- The corrected locators keep every section name and every printed number as
  a `(printed p. N)` cross-reference, and state each PDF position in the
  module's `PDF p. N` house style (the same style the klausuren-TUM routes
  use, verified exact by RECHECK-80).
- The filename gains the provenance paren the module's own ch03 IngMath2
  route already carries — `IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg
  1991):` — which also makes the locator resolvable: the current
  bare-colon form (`IngMath2_Aufgaben.pdf:`) defeats the repository's
  material-suffix token parser and resolves to zero files today; the
  corrected form resolves to the one real file, whose sha256 matches the
  registered materials manifest entry.

## Linked

- No other route or source is touched; the full source map is carried with
  exactly these three locator strings changed. The routes' covers, titles,
  angles and angle_detail are untouched (none carries page numbers).

## Completeness

- Every bare `p. N` anchor in the three locators becomes the correct PDF
  position with the printed number preserved as a cross-reference; a reader
  who jumps to a cited page now lands on the named section.
- Duplicates: none introduced. Exclusions: the ch03 route
  (route-an-ch03-analysisdrillblaetterext-5) carries the same printed-number
  anchors for Kap. 10 (§10.1 p. 2 → PDF p. 5, §10.2 p. 8 → 11, §10.3 p. 16 →
  19, §10.4 p. 35 → 38 — measured this session) but is NOT confirmed by the
  named verdicts; it is recorded in PACKAGES.md as a new finding for Aram and
  deliberately left unchanged here.
- Unresolved gaps: none — the book's offset is uniform + 3 across the whole
  cited span.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
""".format(),

"audit-p4-rehearsal-2026-10-25.md": """# Coverage audit — combined-exam-rehearsal prose rows (L2-16, 2026-10-25)

Scope: bind the 9 unbound teaching rows of unit-m2-combined-exam-rehearsal to
the routes declared for that unit, confirmed by C2 REPORT F2 (9 × "the unit's
source disposition is recorded, but no route for this unit matches this
source and locator") and CLAUDE-VERDICT.md ("all 481 real"). `--check` only,
never applied.

## Local

- The unit's study map read whole; the source map read whole. The unit has
  exactly one declared route per source across its four sources with rows
  (source-analysis-skript → route-686945337831d30097efd0a5,
  source-sad-ss26-lectures → route-eb5c6b1b09ac69064d94ade3,
  source-sad-uebungen → route-bba83db0dc9d9f588c11fe61,
  source-sad-klausuren-extern → route-1db639dec976a8c8a14a9bbc,
  source-analysis-klausuren-extern → route-b52242711bc5df661f001fa7,
  source-fau-klausur-ws1415 → route-16b01eb7e461c69ae61e851a): 6 routes, 9
  unbound rows, every row's source_id unambiguous.
- Each row's prose locator is a stage-specific re-description of its route's
  declared locator (the C2 report's reading; re-confirmed row by row this
  session). The binding inherits `source_id` only and keeps every
  stage-specific label, locator, angle and angle_detail verbatim as
  overrides, so the effective teaching content is unchanged.

## Linked

- All six routes carried forward untouched; no source map in the package, no
  route or source edits anywhere else in the module.

## Completeness

- All 9 RESOURCE-SCOPE-UNBOUND warnings of the unit are resolved by binding;
  no row's material claim changes.
- Duplicates: none introduced (each row binds the one route its source
  declares; two rows per route occur only where two stages genuinely draw on
  the same source, matching the routes' own two-mock design).
- Known deviation, recorded: the unit's routes carry coarse covers
  (knowledge-m2-joint-blueprint, knowledge-m2-joint-simulation) that predate
  the mock-one/mock-two/repair stage split, so the ch01/ch02 covers-derived
  placement rule does not reproduce these nine placements mechanically. The
  binding rests on the validator's own remediation for this exact warning
  ("bind the resource to a declared route for this unit") and on one-route-
  per-source uniqueness; no covers are edited.
- Exclusions: none. Unresolved gaps: none.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
""".format(),
}


def main() -> None:
    builders = {
        "package-p1-ch03-07-binding.yaml": build_p1,
        "package-p2-aml-l09-locator.yaml": build_p2,
        "package-p3-ingmath2-pages.yaml": build_p3,
        "package-p4-rehearsal-binding.yaml": build_p4,
    }
    for audit_name, text in AUDITS.items():
        (WS / audit_name).write_text(text, encoding="utf-8")
        print(f"wrote {audit_name}")
    for name, builder in builders.items():
        package = builder()
        text = dump(package)
        # The canonical-tree material sweep reads package YAML: a spaced URI in
        # a plain scalar truncates at the first space; the quoted form survives
        # (the bare regex stops at the closing quote and captures it whole).
        text = text.replace(f"ref: {VL09_URI}", f'ref: "{VL09_URI}"')
        path = WS / name
        path.write_text(text, encoding="utf-8")
        print(f"wrote {name}  file_sha256={sha256_file(path)}")


if __name__ == "__main__":
    main()
