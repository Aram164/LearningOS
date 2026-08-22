# AML lane — plan fix applied, 2026-08-22

Answers the question put after the SaD and Analysis passes: *does AML need the
same treatment?* Measured the same way — practice- or implementation-depth
material per knowledge node — the answer was **yes for coverage, and yes for
pace, but not for re-routing**. AML's 199 existing routes were already
section-exact and angled; nothing needed correcting. What was missing was
material behind one lecture, and the pace prescription on the exam stages.

Applies `AML-material-coverage-audit-2026-08-22.md` plus the learner's standing
instruction of 2026-08-22: *fill gaps with everything that fits, do not plan time
per stage, give each stage the set of all possible materials and the angle they
highlight.*

**Records changed**

| File | Change |
|---|---|
| `curriculum/modules/module-hu-aml/source-map.yaml` | 199 → 223 routes; one new source block; the `source-d2l` `why` corrected |
| `…/units/unit-aml-exam-prep/unit.yaml` | `source_selections` 2 → 5, regenerated from the routes that reach this unit |
| `…/units/unit-aml-exam-prep/study-map.yaml` | every stage carries its menu; `estimate_minutes` removed from all ten |
| `work/active/workspace-aml-exam-prep/CONTEXT.md` | one source id added; one paragraph appended to Current Scope. Your 2026-08-19 cadence, administration and scope-correction prose and the Next Action are unchanged — the import's section replacement overwrote them and they were restored verbatim before this record was written |

Applied as one snapshot-guarded `module-plan-import`, receipt
`operations/transactions/transaction-20260822-031453-001.yaml`. Preflight clean
(`canonical_files_written: 0`), then `validate.py` → **0 errors, 0 warnings**,
`generate.py` rebuilt, `pytest tests/test_curriculum_v2.py` → 52 passed, 1
skipped, `git diff --check` clean. The source-map diff is 303 insertions against
2 deletions: nothing existing was rewritten.

---

## 1. The measurement that drove it

| | before | after |
|---|---|---|
| Nodes with no practice/implementation route | **20 of 78** | **6** |
| Nodes served by a single depth | 4 | 2 |
| Routes | 199 | 223 |
| L11 nodes with nothing workable | **9 of 9** | 1 |

L11 was the whole finding. It carried sixteen routes where every other lecture
carried 51–78, and its only non-deck route was a URL. L02, L04, L05, L07 and L09
were already clean and were not touched.

## 2. L11 now has three layers instead of none

- **Derivation** — Murphy §15.4 (attention as a soft dictionary lookup, p. 519) and
  §15.5 (self-attention p. 526, multi-head p. 527, positional encoding p. 528,
  the assembled block p. 529), which follow the deck's own order; §15.7 for the
  training objective and §20.5 for where embeddings come from.
- **Implementation** — Géron 3rd ed. Ch 16: tokenization and the vocabulary
  (pdf pp. 750–762), pretrained embeddings (763–769), attention → the original
  Transformer (772, 776) with a positional-encoding layer written from scratch
  (779–780), multi-head and masked attention (781–785).
- **Practice** — D2L Chapter 11, verified 2026-08-22: sections 11.1, 11.3, 11.5,
  11.6 and 11.7 each end in an Exercises subsection, one per L11 node. Plus
  Géron's Ch 16 questions 5 and 6.

## 3. Two prior dispositions overturned by the probe

**`geron-copy2.pdf` is not a duplicate.** The 2026-08-21 SaD audit recorded it as
"a second copy in the same folder; not routed". It is the **Third Edition
(October 2022, 1126 pp.)**; the routed `geron.pdf` is the **Second Edition Early
Release (2019, 510 pp.)** and stops inside Chapter 14 — no attention chapter at
all. The complete, newer book was the one sitting unrouted. AML now routes the
3rd edition and names the file in every locator. **The SaD lane is still routed
to the early release**; correcting that is a separate module package and is
recorded as carried, not done here.

**D2L was excluded from L11 on the strength of the wrong chapter.** Its `why`
read "Its RNN chapters are outside the 2026 AML L11 scope" — true of Chapter 10,
but Chapter 11 *is* the attention-and-transformers chapter, and it is the only
practice-depth Transformer material on the menu. The `why` now says what is
actually out of scope.

## 4. Four smaller nodes closed

| Node | Was | Now |
|---|---|---|
| `l06-convexity` | asserted by the deck, derived nowhere | Murphy §8.1.3 pp. 277–281 with the Hessian test; solution manual §10.1 computes the gradient **and** Hessian |
| `l06-newton` | compared but never derived | Murphy §8.3 pp. 289–291 (Newton p. 289, BFGS p. 290) |
| `l06-optimizers` | a slide of formulas | Murphy §8.4.6 builds AdaGrad → RMSProp → Adam in sequence (pp. 299–301); Géron 3rd ed. Ch 11 pp. 485–494 makes each a runnable call |
| `l08-metrics` | defined, never computed | Géron 3rd ed. Ch 3 — confusion matrix pdf p. 164, precision/recall p. 167, ROC p. 173 |
| `l10-motivation` | one line on a slide | Géron 3rd ed. Ch 14 visual cortex p. 620, and exercise Q1 p. 694 asks the argument back |
| `l01-prerequisites` | a 36-page diagnostic with no drill | `source-lineare-algebra-archive` — solved Übungen and Klausuren, routed as `prerequisite` for a failed primer check |

## 5. Stages became menus, and the pace came out

`estimate_minutes` is gone from all ten stages — 120, 360, 420, 900, 240, 180,
240, 180, 240, 120 minutes of prescribed pace. What stays is what is externally
fixed: the dated windows in the titles (19 August → 29 September, set by the
owning module's second sitting) and the exam-condition times inside `done_when` — the
120-minute mocks, the 45-minute mixed retrieval test, the 60-minute dress
rehearsal, the 30-minute taper pass.

| Stage | Resources before | After |
|---|---|---|
| AML.0 calibration | 2 | 5 |
| AML.1 L02–L04 repair | 3 | 7 |
| AML.2 L05–L07 repair | 3 | 6 |
| AML.3 L08→L11 loop | 3 | 8 |
| AML.4 integration + A4 | 2 | 3 |
| AML.5 mock 1 | 2 | 3 |
| AML.6 mock 1 repair | 1 | 4 |
| AML.7 mock 2 | 1 | 3 |
| AML.8 final repair | 2 | 5 |
| AML.9 taper | 1 | 2 |

Each resource now names the angle it contributes and the exact section, ranked
only required-now / helpful-now / reference-only. The late stages stay short on
purpose: a taper whose menu grows is not a taper.

**Objectives and `done_when` were not touched.** Only resources and
`estimate_minutes` changed.

**The L11 exercise gap is written into the record**, not implied: the AML.3
resource for the course exercises states outright that Übung 09–11 end at CNNs
and *there is no Transformer Übung*, and D2L Ch 11 is labelled as the substitute
for a sheet the course never issued.

## 6. Why AML did not get the Analysis re-routing

Analysis needed twelve routes split into forty-one because its books were routed
to nodes they did not contain and seven locators read "Not yet located". AML's
routes were checked and none of that is true here: 199 routes, every one already
carrying a lecture-specific angle, covers, depth, scope and an exact locator,
audited exhaustively on 2026-08-03 and again on 2026-08-19. The correct
conclusion for a lane in that state is to add what is missing, not to rewrite
what is right.

---

## Still open — your call, untouched

- **The SaD lane's Géron routes** point at the 2nd-edition early release. The
  complete 3rd edition is on the same shelf. That is a `module-hu-m2` package.
- **`knowledge-aml-l11-language-task`** has Murphy §15.7 at reference depth and no
  drill. The L11 mock is currently the only instrument that tests it.
- **A lecturer-worked Transformer sheet** still does not exist. D2L substitutes for
  it; only a course posting retires the gap.
- **The second-sitting duration** is still unconfirmed. Everything rehearses at 120
  minutes until a notice says otherwise.
- **L11 slides 73–81 "BONUS: Parallelizing"** remain scope-ambiguous and are carried
  as learn-anyway safety material.

No claim of mastery or readiness is made anywhere in this document.
