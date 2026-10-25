# C2 report — module-hu-aml

Campaign: GLM C2, 2026-10-24. Evidence only — no fixes, no fix packages
(`module-plan-import --check` included), no issues filed. Verified by
GLM-5.3-Flash in one session; a 20% re-check against the PDFs by GLM-5.3 is a
separate later session. Item id L2-7.

## 1. What was run

- Clone: `~/los-glm-C2-2026-10/repository`, cloned `--no-hardlinks` from the
  live checkout, branch `takeover/complete-and-install-2026-10-23` at
  `a2e2d49d3e4978849c270d55a9583897a2fadbad`, clean tree. Never pushed.
- Venv: `python3.14`, `pip install -e '.[dev]'` per Ground rules. No
  `make setup`, no `make hooks`.
- Materials read in place, read-only, via
  `~/los-glm-C2-2026-10/materials -> <workspace>/LearningOS/materials` (the
  validator expects it mounted there; nothing wrote to the materials tree).
- Validator: `.venv/bin/python tools/validate.py --compact` — **0 errors,
  1468 warnings** with materials mounted. The 31 that name module-hu-aml are
  saved verbatim beside this report as
  `validator-warnings-hu-aml.txt`.
- Re-run scripts in `scripts/` next to this report, run with the clone's venv
  python: `c2_route_audit.py` (checks A/B/B'/D on all 265 routes),
  `c2_resources_audit.py` (checks E1–E5 on all 796 stage resources),
  `c2_sections_audit.py` (check C), plus the findings JSONs they wrote.
  Ligatures (ﬀ ﬁ ﬂ ﬃ), quotes (′ ’ ‘ “ ”), whitespace and Unicode form
  (NFC/NFD — macOS stores filenames NFD, the YAML is NFC) normalised before
  every string comparison; misses confirmed against the whole document, never
  one page; page numbers treated as PDF page numbers per the campaign, except
  where a row's own wording says otherwise (finding F1).

## 2. Findings

### F1 — real, minor, systematic: three exam-prep rows anchor pages as PRINTED numbers; every other anchor in the module uses PDF numbers

In `curriculum/modules/module-hu-aml/units/unit-aml-exam-prep/study-map.yaml`,
the three `source-murphy-pml1` rows write bare page anchors that are the
book's *printed* page numbers, not PDF page numbers:

| row | claims | actual (outline of `pml1.pdf`, 860 pp.) | delta |
|---|---|---|---|
| stage-aml-foundations-repair (reference) | §11.2.2 p. 372 | §11.2.2 Least squares estimation → PDF p. 402 (header prints "372") | 30 |
| same row | §11.2.4 goodness of fit p. 380 | §11.2.4 Measuring goodness of fit → PDF p. 410 (header "380") | 30 |
| stage-aml-linear-optimization-repair (reference) | §8.1.3 pp. 277–281 | → PDF pp. 307–310 (p.307 header "…277") | 30 |
| same row | §8.3 pp. 289–291 | → PDF pp. 319–321 (p.319 header "8.3. Second-order methods 289") | 30 |
| same row | §8.4.6 pp. 298–301 | → PDF pp. 328–331 (p.328 header "298") | 30 |
| stage-aml-neural-transformer-loop (reference) | §15.4 pp. 518–525 (519, 521) | → PDF pp. 548–555; §15.4.1 → PDF 549 (header "…519"); §15.4.3 → PDF 551 (header "…521") | 30 |
| same row | §15.5 pp. 526–532 (526, 527, 528, 529) | → PDF pp. 556–562; 15.5.1→556 ("526"), 15.5.2→557, 15.5.3→558, 15.5.4→559 | 30 |

All nine sub-anchors verified: each claimed number equals the printed page
number printed in the target page's own header; the copy in the vault has a
constant +30 printed→PDF offset here. The repository convention is PDF page
numbers (CAMPAIGNS.md pitfalls: "Page numbers are PDF page numbers, never
printed ones"; the module's own source-map routes write
`pdf pp. 402-405`-style and are outline-correct; the geron rows in the same
study map write `pdf p. …` and are exact). So a reader who opens `pml1.pdf`
at the claimed page lands 30 pages early — e.g. "§11.2.2 p. 372" opens PDF
p. 372, which is §10 logistic-regression material (it happens to discuss the
NLL too, which masks the miss).

Why `make check` stays clean: the numbers are inside the real page count, and
the rows carry no `material://` URI for the validator to cross-check.

Provenance: the rows are content-identical to the 2026-08-22 completeness
plan's embedded map (see F2) — original debt of that pass, not later damage.

### F2 — the 31 validator warnings: all real, all in unit-aml-exam-prep, and the unbound shape is ORIGINAL DESIGN plus an unapplied improvement — not damage

Triage of all 31 `RESOURCE-SCOPE-UNBOUND` warnings (0 noise):

- **9 × "no source_id is named"** — one per unbound non-`reference` row whose
  locator is a knowledge-note menu (`note-aml-l02-mock-exam through
  note-aml-l11-mock-exam…` etc.). Real per the validator's own contract.
- **22 × "the unit's source disposition is recorded, but no route for this
  unit matches this source and locator"** — rows that name a `source_id` and a
  prose locator (`lecture-slides/VL 02-nearest-neighbor.pdf; VL 03…`,
  `exercise-slides/Übung 02–07.pdf and the matching Bonusblätter`,
  `geron-copy2.pdf (3rd ed.) Ch 4 'Training Models'…`). Real: no declared
  route carries that exact (source, locator) pair.
- Exact reconciliation against the study map's 46 unbound rows: 9 + 22
  warned; the 15 unwarned rows are 14 `kind: reference` rows (exempt by
  design — `plan_rigor.py:569` returns early for pointers) plus 1 `read` row
  (`exercise-slides/Übung 10.pdf, slides 2–3`) whose (source_id, locator)
  exactly equals declared route `route-5f890476996a6d9847807cc6`'s pair
  (`plan_rigor.py:591` passes it). 46 = 9 + 22 + 15.

Provenance — the test from CAMPAIGNS.md ("compare with the workspace
`outputs/` original before calling anything damage"):

1. The map's own `source_plan.path` cites
   `work/active/workspace-aml-exam-prep/outputs/AML-exam-execution-plan-2026-08-19.yaml`;
   that plan's exam-prep section is **19 rows, all unbound, same 10 stages**.
2. `AML-material-completeness-plan.yaml` (2026-08-22) embeds the exam-prep map
   with **46 rows, all unbound — content-identical to the live file
   (46/46 rows match on stage/kind/triage/locator)**. Applied same day
   (transactions `20260822-031453/-033330`).
3. A later plan DID bind these rows:
   `AML-exam-plan-final-2026-09-11-r2.yaml` carries 39 exam-prep rows, 23 of
   them bound via `material_ref.route_id`. But **it was never applied**: no
   transaction between 2026-09-11 and 2026-09-20 touches
   `unit-aml-exam-prep/study-map.yaml` (the six touching it are 08-19 ×2,
   08-22 ×2, 09-01, 09-20), and the live file still cites the 08-19 plan. The
   09-20 write (`transaction-20260920-034916-001`, `unit.plan.revise`, codex
   channel, operator-approved) is the node-linkage backfill — its output map
   `work/active/node-linkage-backfill-2026-09-20/outputs/maps/` is also
   46 unbound rows, same as live.

So nothing was overwritten: the unbound rows are the original design of the
08-19/08-22 passes, and the bound variant exists only as an unapplied plan.
This is unmigrated critique-point-1 debt (the same family M2's report
records), recorded here as evidence; boundary 17 reserves the fix for Aram.

### F3 — observations (no defect claim)

- **Prose-compressed locators in the exam-prep lane.** Route
  `route-b3c9cda951cabf0f92743436` ("Current AML exercises and bonus
  sheets") has locator `exercise-slides/Übung 02-11.pdf and
  bonus-exercises/zusatz-blatt01-04.pdf` — no such files exist; the real
  files are `Übung 02.pdf`…`Übung 11.pdf` and `zusatz-blatt01.pdf`…
  `zusatz-blatt04.pdf`. Five unbound exam-prep rows use the same compressed
  style (`VL 01–11`, `Übung 02–07.pdf`, `Übung 02–11.pdf`). The validator
  tolerates them because they carry no `material://` URI; a reader must
  expand the ranges by hand. Original shape (present in the 08-19 plan).
- **External source names a local-looking file.** Route
  `route-69c5b6e2f97ec6539c186fca` (source-mit-6034-quizzes) locates
  `MIT6_034F10_quiz3_2010.pdf, Fall 2010 Quiz 3, Problem 2, Parts B-C`;
  that source has no folder in the materials tree, so the named file cannot
  be addressed locally. External-by-design source; noted because every other
  PDF-naming locator in the module resolves.
- **d2l / jurafsky rows unverifiable locally.** The exam-prep rows citing
  d2l §11.1/11.3/11.5/11.6/11.7 and "Jurafsky & Martin Chapter 8 —
  Transformers" name sources with no materials-tree folder
  (ASSUMPTION: the d2l section numbers match d2l's published chapter-11
  structure; not checkable in this clone).

## 3. Clean checks (all 0 defects)

- **A — vault_path vs locator (routes):** all 28 `vault_path` URIs in the
  source map resolve and name the file their locator names. (2 initial flags
  were my matcher's space handling, fixed.)
- **A′ — named files exist:** of 30+ initial flags, all resolve except the
  two F3 prose-compressed locators and the F3 MIT quiz file.
- **A (stage resources):** all 796 rows across 12 study maps checked — 0
  dangling `route_id`s, 0 unresolvable `vault_path`s, 0 rows whose explicit
  `vault_path` names a file other than its own route's locator (the bound
  form of the M2 broadcast signature is absent).
- **B — page ranges:** 0 out-of-range page or slide numbers in any route or
  row. Spot-exact: `Übung 08.pdf (48 pp.)` = exactly 48 pages;
  `VL 11-transformers.pdf (81 pages)` = 81; slides 73–81, 2–3 within counts.
- **B′ — printed→PDF offsets:** 0 conflicts; every geron/pml1 anchor in the
  source map carries explicit `pdf pp.` and matches the PDF's outline
  (e.g. §11.2.2 → 402, §15.4 → 548, §8.1.3 → 307; geron Ch 14 → 619/620).
- **B (exam-prep geron row, 14 anchors):** every named page verified against
  `geron-copy2.pdf` (1126 pp): visual cortex 620, exercises 694, attention
  772, original Transformer 776, positional encodings 779–780, multi-head
  781, masking 785, exercises 794; Faster Optimizers 485–494 with Momentum
  486, Nesterov 487, AdaGrad 489, RMSProp 490, Adam 491. `solutions-public.pdf`
  §10.1 at PDF p. 25 exact; §11.3 and §13.1 present.
- **C — sections/TOC vs text:** 153 real section references in routes; 137
  verified directly (125 by outline title, 6 by whole-document text, 6
  slide ranges by page count). The 16 initial misses all resolved as checker
  artifacts, each verified against the document: 13 × `csc411.pdf` §-refs
  (§3.1 Basis function regression, §3.2 Overfitting and Regularization, §3.3
  Artificial Neural Networks, §3.4 K-Nearest Neighbors, §8.2 Logistic
  Regression, §8.3 Artificial Neural Networks, §8.4 K-NN Classification,
  §8.6 Classification by LS Regression, §9 Gradient Descent, §9.1 Finite
  differences — all in the book's own Contents); 2 × `zusatz-blatt01.pdf`
  ("Aufgabe 1 (Vektorisierung)", "Aufgabe 2 (k-Nächste Nachbarn)" both on
  the sheet); 1 × "Chapter 8" inside the L11 route's angle_detail, which is
  the neighbouring jurafsky route's title in discriminator prose, not a claim
  about the deck. The 227 quoted-prose "misses" are the same discriminator
  titles by construction of the auto-generated angle_detail text — noise.
- **D — duplicates:** 0 duplicate locator or angle_detail strings among
  sibling routes of any (source_id, unit_id) group (265 routes, 44 sources).
- **Carriage shape:** 10 routes are carried by every stage of their unit
  (the current lecture deck of each of l02/l04/l05/l06/l07/l08/l09/l10/l11
  plus Murphy's optimization chapter in l06). By design: P5/P6 (09-01)
  embed the same row counts (l02: 64 unbound then, 64 bound now), and the
  deck is each unit's declared scope authority.

## 4. Provenance chain (l01–l11)

- P5/P6 (2026-09-01) embed all eleven lecture maps unbound (l01:37, l02:64,
  l03:81, l04:74, l05:61, l06:83, l07:61, l08:90, l09:87, l10:82, l11:45
  rows); applied via `transaction-20260901-*`.
- `transaction-20260907-142206-001` (`module.materials.compact`) rewrote all
  eleven maps binding rows via `material_ref`, preserving counts exactly
  (l01–l02, l07–l11: counts unchanged).
- `coursera-replacement-2026-09-16` bound l03–l06 and removed exactly 4 rows
  per unit (the retired Coursera video rows; documented in its
  `coursera-retire-plan.yaml`; its map drafts match today's counts
  77/70/57/80). Follow-up `transaction-20260923-043610-001` touched l03 only.
- Net: every lecture-unit row today is bound, and my per-row checks above
  verify each binding against its own route.

## 5. Out of scope / method notes

- No fixes, no fix packages, no issues filed (boundary 17; Aram's kickoff:
  evidence only).
- 20% GLM-5.3 re-check against the PDFs is a separate session, per campaign.
- Method note for the re-check: `materials/.flat`'s source folders are
  symlinks into the physical tree, so `Path.rglob` finds nothing unless
  `recurse_symlinks=True` (3.13+), and filename comparisons need NFC/NFD
  normalisation plus space-insensitive suffix matching (`VL 01-….pdf`,
  `Übung 02 .pdf`). The M2 sections-audit's farm search silently matched
  nothing on this machine for the same reason; this session's scripts fix it.
- ASSUMPTIONs: d2l/jurafsky external TOC structure (F3); the (source_id,
  unit_id)-repair mechanism named in CAMPAIGNS.md is not re-derived here —
  nothing in this module needed it (no broadcast shape found).
