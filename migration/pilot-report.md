# Stage-1 Pilot Report — Learning OS v3

> **Date:** 2026-07-17 · **Gate:** BUILD-SPEC Step 6 / MIGRATION Phase 3 ·
> **Status: pilot complete — STOPPED for user review. Stage 2 must not begin
> before approval.**

## 1. What was built before the pilot could run

The previous session had completed Phases 0–2 (baseline commit, 45,636-file
inventory, scaffold). BUILD-SPEC Steps 3–5 were still missing, so this session
implemented them first — they are prerequisites of the gate:

- **Step 3 — loader** (`tools/learning_os/loader.py`): one API for consolidated
  AND partitioned registries, Markdown frontmatter, module records, workspaces,
  COORDINATION.md. YAML dates normalized so the logical model is
  representation-independent.
- **Step 4 — validator** (`tools/validate.py`): JSON-Schema conformance for all
  seven record types + every rule in VALIDATION.md (identity, references,
  registries, ownership boundaries, module attempts, files, workspaces, links,
  generated-file boundaries; `--online` URL audit). Writes the validation report
  into the gitignored output tree. Replaces `check_links.py` / `check_system.py`
  / routine offline lychee for the v3 tree (legacy validators are retired at
  cutover, not now).
- **Step 5 — generator** (`tools/generate.py`): manifest, concept index, source
  index **with per-lecture and per-concept selector views**
  (first-learning/review/implementation), module view, coordination view (exam
  spine + workspace frontmatter + COORDINATION facts + Git neglect signals),
  backlinks, health report. Deterministic except timestamps (verified).
- **Tests** (`tests/`, pytest): 32 tests — validator rules, generation
  determinism, reset scenario, backlink inversion, manifest coverage, acceptance
  scenarios 2/4/5/7/8. **All 32 pass.**

Toolchain requirement: Python 3.10+, `pyyaml`, `jsonschema>=4`, `pytest`.

## 2. Pilot set migrated (MIGRATION §Phase 3 — all mandatory items)

| Phase-3 requirement | Delivered |
|---|---|
| **AML–SaD Master Wiring (mandatory)** | Decomposed: 50 concept relations → `knowledge/concept-relations.yaml`; slide-verified judgments → evaluations on `source-aml-ss26-lectures` / `source-sad-ss26-lectures`; narrative + sequencing preserved **verbatim** in `note-aml-sad-master-wiring` (role: crosswalk) |
| One complete ML lecture unit | AML L07: `note-aml-l07-linear-classifiers` (reference) + exercise bank + mock exam + Bonusblatt-04 solutions; Mini Plan → `workspace-aml-exam-prep/inputs/` |
| One mathematics unit | SaD L02: `note-sad-l02-descriptive-basics` + exercise bank; Mini Plan → `workspace-m2-exam-prep/inputs/` |
| One source crosswalk | `SaD_Source-Crosswalk_L01-L15.md` decomposed: judgments → 24 source records (61 contextual evaluations); narrative → `note-sad-source-crosswalk` (no judgment tables — the generated selector renders them) |
| One user-authored synthesis note | `note-regression-sad-aml-islp-bridge` (verbatim body; Q3 target) |
| One active operational area + COORDINATION facts | `workspace-m2-exam-prep` + `workspace-aml-exam-prep` (scaffolds with required sections, scope triage, Deferred); 3 deferral facts in COORDINATION.md, no exam dates there |
| Module records (≥2, incl. withdrawal + 2. Termin + Kombimodul) | 4 modules in `records/modules.yaml`: **M2 (Kombimodul**, components, withdrawn T1**)**, **AML (withdrawn T1 → 2. Termin plan)**, AMLS, Algo 2. All exam dates live ONLY here (grep-tested) |
| One handwritten attachment | `note-sad-hypothesis-testing-handwritten` + 11 page scans under `knowledge/attachments/…/` (from `Teil 03.pdf`; original preserved untouched in the legacy tree) |

Counts: **11 notes · 48 concepts · 50 relations · 24 sources (61 evaluations) ·
4 modules · 2 active workspaces · 14 path-map rows.**

## 3. Validation & acceptance results

- `python tools/validate.py`: **0 errors, 18 warnings** — all warnings are
  unresolved `material://` URIs, expected until Step 8 moves materials
  (reported-not-fatal by design).
- `python -m pytest`: **32/32 pass**, including: Scenario 5 (delete + rebuild the
  output tree, byte-identical except timestamps), Scenario 7 (attempt lifecycle
  registered→withdrawn→registered representable; real repo has withdrawal +
  Kombimodul; **no attempt date appears outside modules.yaml**), Scenario 8
  spot-checks, Scenario 2 (no scalar ratings), Scenario 4 (move keeps ID).
- Applicable ACCEPTANCE-TESTS sections A–J: pass for the pilot scope. Not yet
  applicable: full-migration items (J's final report, Step 8 separation, cutover
  K items that need day-to-day operation).

## 4. Frozen criteria (PILOT-CRITERIA.md) — **5/5 PASS**

Method: each question answered with legacy files closed, from canonical v3
records + generated views only; then spot-checked that every judgment used
exists in source records or relations, not only in the crosswalk note.

- **Q1 (L05 source selection + prerequisites): PASS.** The generated per-lecture
  selector (`source-aml-ss26-lectures — L05`) answers in one place: intuition →
  StatQuest (MLE video "second watch with Bernoulli in mind"); first learning →
  ISLP §4.3 / CS229-2022 L3; derivation → lecture sl. 40–62 + Murphy Ch 10 +
  CS229 notes; what SaD already covers → relations (`concept-maximum-likelihood
  derives MSE` with SaD-08 context; `logistic-regression requires
  conditional-probability` defined in SaD 04).
- **Q2 (SaD 04–10 reverse map + order): PASS.** The requires/builds-on chain
  reproduces the pipeline order (probability → RV → distributions → Normal/CLT →
  estimation → testing); twins emerge from shared concepts across the two
  lecture-source evaluations (e.g. `concept-maximum-likelihood` carries both the
  SaD L08 and AML L05 evaluations); the §1.2 twin table survives verbatim inside
  the migrated wiring note — a v3 artifact, zero legacy opens.
- **Q3 (context reconstruction): PASS.** "lineare Regression" resolves via alias
  → `concept-linear-regression` → `note-regression-sad-aml-islp-bridge`, whose §0
  states exactly what it was trying to answer; `contexts` ties it to
  workspace-m2-exam-prep. Honest evidence answer: no `evidence` entries yet — the
  bridge was built, not yet worked through.
- **Q4 (slide-verified corrections): PASS.** "L07 contains NO SVM", "L09 OWNS NN
  regularization", "no batch norm" all live as evaluations on
  `source-aml-ss26-lectures` — not only in the note.
- **Q5 (Klausur-level SaD practice by role): PASS.** Role+concept filtering
  returns `note-sad-l02-exercise-bank` (exercise-bank) and the Klausur tier:
  FAU WS14/15 ⭐ (mock-exam, German exam format, clusters N1–N4), Dekking,
  Arbeitsbuch, UE sheets, 18.05 exams, 6.034 quizzes (ML half).

## 5. Facts that need YOUR confirmation (recorded, flagged, reversible)

> **Resolved 2026-07-17 (post-pilot, Aram):** see §9 addendum — all three items
> confirmed and recorded; nothing open here anymore.

1. ~~**AML Rücktritt** — unconfirmed~~ → executed, confirmed.
2. ~~**M2** — Rücktritt/registration unconfirmed~~ → executed, confirmed.
3. ~~**AMLS sitting** — unchosen~~ → last course-run slot, registered attempt
   recorded.

## 6. Decisions taken (flag if you disagree)

- **Handwritten attachment policy:** 120-dpi JPEG page renders (16 MB) instead of
  committing the 67 MB original PDF; original untouched in the legacy tree.
  Decide the Stage-2 policy (renders vs originals in Git).
- **Mini Plans → workspace `inputs/`** (operational study scripts), not notes.
- **AML book crosswalk**: only the L05/L06/L07 judgments were decomposed (what
  the frozen questions and the L07 unit need); rows L02–L04/L08–L10 + its
  narrative note are Stage 2.
- Two new workspaces created (`workspace-m2-exam-prep`, `workspace-aml-exam-prep`)
  as the operational homes of the two exam tracks.
- Migrated note bodies are **verbatim**; each carries a clearly-marked
  *Migration note* blockquote with provenance and companion mapping — no prose
  was rewritten.

## 7. Semantic-risk list

- The SaD crosswalk's per-lecture table was NOT copied into its v3 note (by
  spec); if any judgment failed to make it into a source record, it survives
  only in the legacy original. Mitigation: legacy file untouched; selector view
  compared against the original during this pilot.
- `concept-classification-metrics` bundles several retrieval terms (confusion
  matrix, precision/recall, F1) — split later if too coarse.
- Created dates for the SaD L02 unit fall back to the legacy Git first-commit
  date (2026-07-11); the build week (KW 28) had no day-precision record.

## 8. Verdict & next step

Pilot **passes its own gate** (5/5 frozen questions, 0 validation errors, 32/32
tests). The riskiest bet of v3 — decomposed evaluations + generated selectors
matching the hand-crafted crosswalks — held for the hardest document.

**Awaiting your review.** On approval: Stage 2 (Phases 4–8 — full migration,
material separation, regeneration, cutover). Commands:
`python tools/validate.py` · `python tools/generate.py` · `python -m pytest`.

## 9. Addendum (2026-07-17, post-pilot facts from Aram)

- **Both Rücktritte confirmed executed** ("2 exams were stepped back"): AML
  attempt 1 and M2 attempt 1 stand as `withdrawn` — verification hedges removed
  from modules.yaml, COORDINATION, workspaces and unresolved.md.
- **AMLS sitting decided: the last course-run slot.** Recorded as a `registered`
  attempt (termin 3) in modules.yaml; it now heads the generated exam spine.
- **Attachment policy decided: commit the whole original PDF when possible.**
  Applied to the pilot: `teil-03.pdf` (67 MB, md5-identical to the legacy
  original) replaces the interim 120-dpi page renders. Stage-2 caveat: Teil 01
  (109 MB) and Teil 02 (101 MB) exceed GitHub's 100 MB per-file limit — needs a
  split-or-exception decision if a remote is added (LFS already rejected).
