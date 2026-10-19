---
id: note-sad-l10-islp-fwer-fdr-pp571-581
type: note
role: reference
title: 'SaD L10 complementary angle: FWER versus FDR in ISLP'
created: '2026-09-24'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: machine-learning/classical/islp/islp.pdf
  source_id: source-islp
  recorded_source_digest: 278d3bdd49a8a480c2ff8e03245822caad8a3a48e81afd6d039c52c8fc13ad60
  live_source_digest: 278d3bdd49a8a480c2ff8e03245822caad8a3a48e81afd6d039c52c8fc13ad60
  inspected_range:
    start: 571
    end: 581
  frozen_input_sha256: 8e40c16a4dff85b815ad943cefbb44672eba9e5ace477b1d909278b2837d23e8
  frozen_input_bytes: 1570
  model: Codex GPT-6 2026-09
  built: '2026-09-24'
---

# SaD L10 complementary angle: FWER versus FDR in ISLP

Material inspected: ISLP Python edition, Chapter 13, physical PDF pp. 571-581. This is a bounded analysis of the multiple-testing sections, not an endorsement of the whole chapter as required course scope.

- Section 13.3 defines family-wise error rate as the probability of at least one false rejection. The fund-manager example shows how unadjusted per-test thresholds inflate it. The Bonferroni per-test threshold alpha/m is derived on physical p. 573; Holm's ordered step-down rule and its greater power follow on pp. 574-575.
- Section 13.4 changes the target: false discovery proportion is the fraction of rejections that are false, and FDR is its expectation over repeated data sets. This is a different guarantee from FWER, useful when many exploratory hypotheses are tested.
- Physical p. 581 gives the Benjamini-Hochberg ordered-p-value procedure and states its guarantee under independent or mildly dependent p-values. It is not a universal dependence-free guarantee.
- Source angle: ISLP develops two distinct multiplicity goals with a running data example and algorithms. The current SaD L10 deck only gestures at a multiple-testing correction and p-hacking; ISLP supplies the optional FDR method and comparison.

Plan implication: retain this source in the complete L10 material menu, label its FDR/BH part optional, and correct the route's claim that the current lecture itself names false discoveries. Keep the core required stage on the course's false-positive inflation and Bonferroni intuition.
