# C2 report — module-hu-icop (item L2-9, evidence only)

Session: GLM-5.3-Flash, 2026-10-24. Clone `~/los-glm-C2-2026-10/repository`
(branch `takeover/complete-and-install-2026-10-23`, HEAD `a2e2d49d`, clean tree,
**never pushed**). Materials read in place via the clone-parent symlink
`~/los-glm-C2-2026-10/materials` → live `LearningOS/materials/`.
Scripts and raw results: `scripts/audit_abcd.py`, `scripts/audit-abcd-results.json`.

## Verdict

**0 defects. 0 validator warnings for this module. Live shape = original
design (the 2026-10-22 operator package), verified by content diff, not
assumed.** Every locator, page range and slide/section claim I could test
against a real material held; the four initial checker misses were each
refuted as checker artifacts and are documented below so nobody re-chases them.

## What the module contains

- `module.yaml` + `source-map.yaml`: 11 sources, **53 routes** (9 HU deck
  routes on `ico_linearprogramming.pdf`, 1 on `ico_organization.pdf`, 1
  Korte–Vygen, 9 Blum, 2 MIT 18.200, 26 Cornell, 4 Stanford CS261, 1 MIT
  6.046J), 4 optional-depth sources with 0 routes.
- 1 unit `unit-icop-l01-linear-programming`, 9 stages, 48 route-bound stage
  resources + 10 direct resources (exercise bank ×9, mock exam ×1).
- 3 artifact notes in `knowledge/notes/algorithms/`.

## Provenance — original design, with receipts

The study map's `source_plan.path` names the applied package
`workbench/icop-l01-2026-10-22/module-plan.yaml` (read-only in the live
workbench). Programmatic diff of live vs package:

- `source_map` (sans routes): **equal**; all 53 routes: **equal**, field by
  field (`scripts/audit-abcd-results.json` → `provenance`).
- All 9 stages and the unit patch (`unit.yaml`): **equal**, excluding
  `runtime_review` (review stamps) and `study_map.source_plan` (apply-time
  bookkeeping that points back at the package — expected).

So nothing in the live module was overwritten by a later pass; there is no
damage to attribute. Two context items:

- The geometry stage's "Convexity does not imply a unique optimizer" wording
  is **in the 2026-10-22 package itself**. It matches
  `workbench/icop-l01-2026-10-22/convexity-correction-issue-draft.md`, which
  records that `note-aml-l06-gradient-descent` §7 claims a convex loss has
  "one global optimum", that the ICOP deck handles non-unique optima, and
  that the note itself was deliberately **not** rewritten. Consistent: the
  route references the note as prior convexity reading while carrying the
  caveat.
- `work/active/icop-l01-2026-10-22/outputs/` holds only `coverage-audit.md`.

## Check A — vault_path / material:// resolution: 31/31 pass

- All 21 route `material://` URIs resolve through the system resolver
  (`resolve_material_target`, resolution_root `materials/.flat`, resolved
  boundary root) to exactly the file named in the locator, e.g.
  `material://source-icop-hu-ws2627/ico_linearprogramming.pdf` →
  `algorithms/structures/icop-hu-ws2627/ico_linearprogramming.pdf`. The 9 LP
  routes' locators name `ico_linearprogramming.pdf` and the organization
  route names `ico_organization.pdf` — basename matches verified.
- 10/10 direct resources exist: `note-icop-l01-exercise-bank.md` (9 stages)
  and `note-icop-l01-mock-exam.md`, each locator's `note-…:` id matching the
  file stem. All 3 `unit.yaml` artifact notes exist
  (`note-icop-l01-reference/-exercise-bank/-mock-exam`).
- 0 dangling references: every `material_ref.route_id`, `source_selections`
  route/stage id, `covers` knowledge id and stage id resolves. Every
  knowledge node is covered by at least one route.

Note for reviewers: a naive inherit check flags 48 resources whose
`material_ref.inherit` lists `label` while routes define `title`. That is the
system's own mapping (`tools/learning_os/domain/material_refs.py:16` maps
`"label": "title"`), not a defect.

## Check B — page ranges vs real page counts: 20/20 pass, 0 violations

| PDF | real pages | ranges claimed | result |
|---|---|---|---|
| `ico_linearprogramming.pdf` | 129 | 9 route ranges 1-23 … 126-129 | all inside; they tile 1-129 contiguously with no gaps or overlaps; unit scope "physical pages 1-129" exact |
| `ico_organization.pdf` | 17 | 12-16 | inside |
| Korte–Vygen 5e | 664 | 70-90 | inside; physical p91 opens Chapter 4, so 70-90 is exactly Chapter 3 |
| Blum 2e | 279 | 229-232 … 266-266 (9 ranges) | all inside |

- 33 URL-only routes carry no page ranges (2× MIT 18.200, 13 Cornell videos,
  4 Stanford, 1 MIT 6.046J — N/A). The 13 Cornell **notes** routes claim
  remote page counts (`lecture_N.pdf, pdf pp. 1-M`); I fetched all 13 PDFs
  from `people.orie.cornell.edu` and counted: **13/13 exact** (L1:7, L2:5,
  L3:6, L4:6, L5:7, L6:7, L7:10, L8:3, L9:9, L14:9, L15:9, L16:9, L17:6;
  page 1 extracts empty — scanned handwriting, no text layer).

## Check C — angle_detail claims vs extracted text: all claims grounded

LP deck (slide N = physical page N; extraction normalised for ligatures,
quotes, dashes, whitespace). Key evidence, quoted from extraction:

- **forms / p23** — "Exercise: Let a digraph G be given along with vertices
  s, t ∈ V (G) and positive edge weights w : E(G) → R>0. Write a linear
  program whose optimum value is equal to the distance from s to t in G",
  plus transform-to-canonical/standard exercises. Grounds the done_when
  "Formulate the shortest-path LP on slide 23 … convert to both canonical
  and standard form". (The slide says "distance from s to t", not "shortest
  path" — see artifacts below.)
- **bases / p55** — vertex theorem and comments ("for every feasible and
  bounded linear program in standard form … there is a vertex").
- **pivots / p67** — standard-form LP with "some assumptions" (nondegeneracy
  caution site).
- **phase-one / p87, p89, p90-91** — first-stage LP questions on 87;
  pivot running-time/bit-size theorem on 89; Klee–Minty theorem (Klee and
  Minty [1972]) on 90; simplex wrap-up with Hirsch discussion on 91.
- **general-duality / p112, p114, p115** — "dual of the dual lp is again the
  primal lp" theorem+exercise on 112; "how could both primal and dual lp be
  infeasible?" worked pair on 114; "recall the linear program for determining
  the distance from s to t … use the transformation rules to cre[ate its
  dual]" on 115.
- **slackness / p125** — chapter "summary" slide.
- **oral-review / p126, p128, p129** — "outlook" on 126; "further exercises:
  … compute a largest ball that is a subset of a given polyhedron" on 128;
  "use the simplex algorithm to solve the following linear programs" on 129.
- **organization / p12, p15, p16** — "presentation uses a mix of pdf slides
  and the board" (sketches note) on 12; "oral exam … length is 30 minutes, in
  person" on 15 (also grounds `module.yaml` examination notes); exam-content
  expectations on 16.
- **Korte–Vygen** — "3 Linear Programming" heading on p70; Exercises section
  begins on p87 (items run through p89); "References" heading on p89 with
  entries on p90 — the angle_detail's "exposition 70-87, exercises 87-89,
  references 89-90" is exact, straddles included. The ch3 opening carries the
  max-form claim ("max{cx: Ax<=b}" convention warning is fair).
- **Blum** — chapter 8 opens p229 with §8.1 body prose (the literal running
  header "8.1 Grundlagen" appears p231); §8.2 simplex content at 238, tableau
  / starting-basis material at 245; §8.3 Dualität at 249; complementary-
  slackness ("komplementäre Schlupfbedingung") on 255 with the dual-simplex
  discussion beginning at the very bottom of p255 ("…von einer zulässigen
  Lösung des dualen linearen Programmes, einer dual zulässigen" → p256:
  "…wandert. Dieser heißt dualer Simplexalgorithmus.") — the route's "stop
  before dual-simplex discussion at the bottom of PDF page 255" is exact.
  "Übung 8.15" and "8.16" both on p266.
- **Blum printed-page offset +12** — verified on 8 physical pages
  (230→218, 231→219, 238→226, 245→233, 249→237, 255→243, 256→244, 266→254).
  The chapter opener p229 carries no folio at all.
- **Vault notes** — `note-aml-l06-gradient-descent` §7 exists; the exercise
  bank has `## Questions` (E1-E10) then `## Solutions and proof checks`; the
  mock exam has `## Timed questions` (Q1-Q5) then `## Solutions and marking
  guide`. The locators' "Answers"/"answer guide" wording is prose guidance,
  not a heading-name claim — verified in substance.
- Video-route `angle_detail`s make no page/section claims, only
  provenance-historical statements ("official course title … checked on
  2026-10-22") — recorded, not re-verified, except the URL spot-checks below.

## Check D — duplicates: template prose only, 0 defects

- **0 exact duplicate `locator` strings** among all 53 routes.
- 3 sibling `angle_detail` groups share boilerplate prose (8 Blum routes
  "Read only the stated subsection span…"; Cornell L3+L4 and Stanford L7-L10
  video boilerplate). All three groups are **byte-identical in the 2026-10-22
  package** (routes equal) → original design: every sibling is distinguished
  by its own `title` and `locator`; the shared paragraphs are deliberate
  guidance text, not a broadcast overwrite of route identity.

## Validator: 0 module warnings

`.venv/bin/python tools/validate.py --compact` on the clone: **0 error(s),
1468 warning(s)** tree-wide. `generated/reports/validation-report.md`
contains **zero rows for `module-hu-icop`** (by id and by path). Attribution
control: the same report reproduces the previously published per-module
counts exactly (m2-statistik 481, hu-aml 31), so the absence is real, not a
labelling failure. (The residual 6 non-curriculum warnings are
ATTACH-LOCAL-ABSENT pins and HYGIENE-VIEWS, module-independent.)

## External spot-checks

- HTTP 200: MIT 18.200 L12 resource page; Cornell `lp_course.html`.
- All 13 Cornell `lecture_N.pdf` fetched; page counts match claims 13/13.
- `theory.stanford.edu` (4 Stanford routes) **unreachable from this machine**
  (ECONNREFUSED on both curl and the fetch tool): **ASSUMPTION — not
  verified, and no evidence of a defect**; the routes' own angle_details
  already record that the schedule mapping was made at plan time.

## Checker artifacts (refuted — do not re-chase in the 20% re-check)

1. `lp-p23 "shortest path" not found`: the slide words it as "distance from
   s to t"; the digraph LP exercise is on p23 exactly.
2. `blum-p229 "8.1" heading not found`: p229 is the chapter opener carrying
   §8.1 body; literal "8.1 Grundlagen" first appears in the p231 running
   header. The locator span is content-correct.
3. `blum offset check "fail"`: caused by the folio-less opener; +12 holds on
   all 8 folio-bearing pages tested.
4. `exercise-bank "Answers" not found`: the answers section is titled
   "Solutions and proof checks"; locator wording is prose.

## Out of scope (per campaign)

No fixes prepared or applied (no `module-plan-import --check` run — evidence
only per Aram's kickoff), no issues filed, nothing pushed. Residuals not
audited: whether the optional-depth sources' names are still the ones the
Moodle screenshot showed (screenshot not re-read), and video-content claims
inside external lectures.
