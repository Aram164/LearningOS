# SaD follow-up to Codex's repair — 2026-09-07

Codex's follow-up (`814cc17`) closed audit sections §1–§7 and most of §8. This pass closes what
survived it, and it is deliberately bounded: Aram chose the bounded repair over a fresh audit of the
41 video routes and the external exercise banks, so those remain Codex's recorded limits rather than
anything this report certifies.

Every content claim below was checked against a file opened during this session. Nothing is inherited
from a prior report without saying so.

## Local

### What was still wrong, and what it now says

- **Kelleher section attributions, in the stage copies the route fix never reached.** Codex corrected
  the L13 and L14 *route* locators to §5.3 and §6.3 but left fourteen stage-level copies asserting
  §5.2.2 "the nearest-neighbour algorithm" (5 in L13) and §6.4.2 "the Naive Bayes model" (4 in L14).
  A third, which no earlier pass found, ran through the L12 route *and* its five stage copies:
  §4.2.3 "the ID3 algorithm". Kelleher's own contents (PDF pp. 8–13, read this session) give
  §4.2.3 Information Gain, §4.3 Standard Approach: The ID3 Algorithm, §4.3.1 A Worked Example;
  §5.2.2 Measuring Similarity Using Distance Metrics, §5.3 Standard Approach: The Nearest Neighbor
  Algorithm; §6.4.2 Continuous Features: Probability Density Functions, §6.3 Standard Approach: The
  Naive Bayes Model. All fourteen copies now carry the corrected locator. The three stage slices that
  had already been narrowed correctly — `§5.4.2, PDF pp. 234-241`, `§6.4.4, PDF pp. 324-328`,
  `§6.4.4, PDF p. 328` — were left untouched, because replacing them would have undone the page-slice
  work rather than repaired anything.

- **Kelleher and neural networks, in the two places the L15 correction did not reach.** The source
  record's own `why` still said Chapters 4–7 map to "trees, similarity, probability-based learning,
  and neural nets", and the exam-prep route still promised neural-network explanations and carried
  `knowledge-sad-exam-neural` in `covers`. Kelleher §7.6, PDF p. 416: "In this chapter we have not
  covered artificial neural networks." Both now describe Ch 7 as regression, gradient descent,
  logistic regression and SVMs. The `knowledge-sad-exam-neural` node keeps its coverage from the two
  other routes that carry it, so nothing was stranded.

- **The sheet-numbering claim.** `stage-m2-sad-calibrate` asserted "No Blatt3 or Blatt4 exists in the
  material root". `Übung-3.pdf` is Blatt 3, and page 1 of `Statistics_And_Data_Science.pdf` is headed
  **"Übungsblatt 4"**, Berlin, 10.06.2026. The claim is gone; the sheet identities are stated, and the
  provenance ambiguity Codex recorded — a 2026 heading against a `hu.berlin/sds25` link — is carried
  beside them without inferring any exam date from it.

- **Cornell HW8.** `stage-m2-sad-s10-trees-ensembles` said "2018Fall/HW8 or 2018Spring/HW8; choose
  one". Grepping both TeX sources: Spring 2018 HW8 is kernels, perceptrons and ridge regression, with
  no tree and no AdaBoost; Fall 2018 HW8 is regression-tree construction, pruning and AdaBoost
  normalisation. Only the Fall sheet serves this stage, and it is now named by problem and page, with
  the Fall PDF/TeX mismatch on Problem 1(b) kept visible so no neighbouring solution file is mistaken
  for its answer key. The exam-prep Cornell route also claimed "No local copy" — all four homework
  files are registered local material, so that claim is gone too. The two k-NN sets are no longer
  offered as an arbitrary "choose one": the Fall 2018 PDF has the published solution PDF, and the 2017
  Spring HTML set weights distance and dimensionality more heavily.

### The unit every prior pass skipped

`unit-m2-sad-exam-prep` was excluded from the identity recovery (its rows have no `angle` to match on)
and from Codex's page-slice work (it is a synthesis lane, not a lecture). It held **56 of the module's
56 unidentified placements**: none carried a `route_id`, and five carried no `source_id` either. Every
other SaD unit was already at full coverage.

The unit owns exactly twelve routes over twelve distinct sources — a 1:1 map, asserted in the builder
rather than assumed — so each sourced row attaches to the single route its source names. No fuzzy
matching and no first-match: an ambiguous source would have aborted the run. **51 rows gained their
route.** All 56 gained an `angle`, which none had before, and 39 locators became exact.

The remaining five rows are artifact references, not material: they name durable notes, which have no
source record by design. Their labels now carry the exact note ids, and all ten notes are registered
on the unit's artifact list so they are reachable from the unit rather than only from a stage row.
Source-less placements are ordinary here — 1,466 of the repository's 3,986 placements have no source —
so these five are not a defect; they are simply not material.

Locators that became exact were verified page by page against the file they name:

- Fahrmeir `statistik.pdf` — Kap. 2 PDF p. 46, Kap. 3 p. 126, Kap. 4 p. 193, Kap. 5 p. 242, Kap. 6
  p. 288, Kap. 7 p. 329, Kap. 9 p. 382, Kap. 10 p. 416, Kap. 11 p. 450, each confirmed by opening that
  page; and §3.5 Korrelation und Kausalität, §3.6 Regression, §4.5 Unabhängigkeit, §4.7 Der Satz von
  Bayes, §5.3, §6.3, §7.1, §7.2, §9.1, §10.2, §10.3 confirmed against the chapter contents pages.
- Fahrmeir `arbeitsbuch.pdf` — Kap. 5 PDF p. 96, Kap. 9 p. 180, Kap. 10 p. 200, Kap. 11 p. 219.
- `blitzstein.pdf` — Ch 1 PDF p. 18, Ch 2 p. 62.
- `kelleher.pdf` — Ch 1 p. 36, Ch 2 p. 57, Ch 4 p. 156, Ch 5 p. 215, Ch 6 p. 282, Ch 7 p. 351,
  Ch 8 p. 425.
- The four external exam PDFs and all four Cornell homework directories were confirmed present in the
  registered materials tree. MIT 18.05 and MIT 6.034 have no local copy — both are registered
  online-only sources — and their rows now say so instead of implying a local file.

A mechanical sweep supported the manual work: every `§X.Y` citation in every SaD route was matched
against the table of contents of the book it names, for all fifteen cited books held locally. That
sweep is what surfaced the §4.2.3 mislabel. Its remaining flags were TOC-parsing noise, checked and
dismissed one by one.

## Linked

No external page was opened in this pass and none is newly certified. Codex's checks of the
scikit-learn nearest-neighbour sections, the ROC and precision-recall definitions and the 3Blue1Brown
companion lesson stand as its evidence, unchanged and not re-signed here. The 41 video routes and the
external exercise banks remain inherited and unverified, exactly as Codex left them; this report does
not narrow that limit.

Analysis units, the joint rehearsal unit and every non-SaD module are untouched: the verifier requires
483 of the module's 486 routes and every non-SaD source record to be byte-identical, and asserts it
rather than assuming it.

## Completeness

- `local_inventory_complete`: true for this bounded repair — every changed claim names a file that was
  opened, and the exam-prep unit's full inventory of 56 placements was enumerated rather than sampled.
- `linked_inventory_complete`: true in the same bounded sense — no linked route was changed, so none
  needed re-opening; unchanged linked routes are retained as inherited, not certified.
- `materials_opened_and_content_checked`: true for every claim this pass changes. Kelleher, Fahrmeir
  (both volumes), Blitzstein, the two Cornell TeX sources and the Übungsblatt 4 title page were opened
  and read.
- `current_and_prior_scope_reconciled`: true. Stage order, ids, status, objectives, `done_when`,
  `exam_critical`, concepts, attachments, feedback and progress are unchanged everywhere — 1,527
  protected stage fields and 9,424 protected resource fields asserted equal.
- `duplicates_and_numbering_checked`: true. Physical PDF pages are kept distinct from printed slide
  labels; Fall and Spring Cornell sheets are no longer interchangeable; already-narrowed stage slices
  were preserved rather than overwritten.
- `exclusions_and_unresolved_gaps_recorded`: true; see below.

## Settled

**L15 outlook.** Aram decided this session: the CNN/RNN/Transformer stage keeps `exam_critical: true`,
and no exam exclusion is claimed. The plan already reads that way — Codex left the flag in place and
recorded that no official exclusion was verified — so nothing changed; the item moves off the open
list because the decision has now been made, not because evidence arrived.

**Geometric extension.** Unchanged from Codex's disposition: a complementary bridge to the Blatt 4
CLT simulation, with no inferred exam priority. Nothing in this pass touches it.

## Unresolved

1. **Exercise data files.** `seattle_house_prices.csv`, `insurance_payouts.csv`,
   `International_Education_Costs.csv` and each sheet's `aufgabe3.py` template. A full-depth search of
   `~/Desktop`, `~/Downloads` and `~/Documents` on 2026-09-07 found none of them. (Spotlight is
   unreliable on this machine — `mdfind -name kelleher.pdf` misses a file that is present — so the
   filesystem sweep is the evidence, not `mdfind`.) The action is now named on the source record:
   download the exact files from the Moodle course at `hu.berlin/sds25`. Paper-only parts stay usable;
   no substitute dataset is offered.
2. **Sachs/Hedderich**, named on L01 PDF p. 40. The same search found no copy. It stays deferred on
   the current-course source entry, with no fabricated source id, locator or reading.
3. **Kelleher's Gaussian Naive Bayes solution.** The exercise is verified; a complete solution manual
   is still not located. Unchanged from Codex.
4. **Cornell Problem 1(b).** The Fall 2018 PDF and TeX differ, so the pruning solution is not
   certified. Now stated in the exam-prep row as well as the L12 stage.
5. **The 41 video routes and the external exercise banks.** Not audited in this pass by decision, not
   by oversight. They remain inherited options, not verified ones.
6. **Broader material quality.** Every untouched external source, author claim and exercise-bank
   solution is still un-re-audited. This report closes the source-backed defects it lists; it is not a
   universal semantic sign-off, and no unexamined route receives an implicit pass.

Draft, preservation proof and change log:
`LearningOS/workbench/audits/sad-semantics-2026-09-07/claude-followup/`
(`build_repair.py`, `verify_repair.py`, `repair.yaml`, `before.json`, `before-hashes.json`,
`changes.json`).
