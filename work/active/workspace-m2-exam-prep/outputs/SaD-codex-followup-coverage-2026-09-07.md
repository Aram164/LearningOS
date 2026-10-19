# SaD follow-up to Gemini's repair — 2026-09-07

Gemini's `ea4bf14ab698c31790b8aa9f5a7032bf3a4af3b2` repaired several placements but did not complete the semantic audit. This report supersedes its repair-completeness claims. The user explicitly authorized Codex to check the work and patch omissions. It does not certify every external video or book chapter.

## Local

The bounded repair covers all 15 SaD lecture maps, clustering and the SaD exam-prep map. It preserves the existing module and stage order, IDs, learner choices, progress, notes, attachments, feedback and unrelated module records. The full source map is carried through the public module import, with changes limited to SaD contextual routes. Source registries and material files are not rewritten.

Verified source evidence:

- All 15 current lecture PDFs: physical page structure and content sections checked against extracted text; all 106 lecture stages receive explicit physical page slices. These are focused assignments, not claims that every listed stage subtopic is fully developed in its deck. Geometric waiting times, LSH depth and L15 outlook scope carry explicit limits.
- L01 pp. 3–10, 12–24, 37–40: study-duration example, separate medical example, course map and bibliography. Classification and base rates belong to L01's own content.
- L03 pp. 24–27, 29–43: matrix solution and numeric gradient-descent updates. L04 p. 43 states partition and total probability; the proof is omitted.
- L08 pp. 31–36 and Dekking §22.3 pp. 338–339: loglikelihood and least squares. Gaussian independent errors with common variance are model assumptions, not guaranteed by the CLT.
- Blitzstein §1.5 pp. 37–38, OpenIntro §2.2 pp. 61–69, Dekking Ch 18 pp. 275–290 and Ch 21 pp. 318–322: retain Gemini's useful additions with specific contributions and limits.
- Kelleher §5.4.2 pp. 234–241; §6.3 p. 300 onward; §6.4.4 pp. 324–328; §7.6 p. 416: kd-tree search, Naive Bayes before Bayesian networks, Markov blanket, and explicit absence of artificial neural networks from Ch 7. False detailed comparisons and the misleading L15 route title are corrected.
- Kelleher §6.7 pp. 344–350: Gaussian Naive Bayes exercise 3 is a question, not a verified worked solution. The unlocated solution manual remains unresolved.
- Blatt 1 p. 3: covariance/Pearson in 2(a), regression in 2(b)–(c). The initial scatterplot is explicitly a plan-authored warm-up using Tabelle 2, not a purported official subtask.
- Übungsblatt 3 p. 2 and UE4 pp. 36–49: Poisson, Binomial and Hypergeometric, not Geometric. Blatt 4 p. 3, 3(a)(4), explicitly uses Geometric(p=0.02) for a later CLT simulation; it is added as a complementary bridge with the simulation deferred to L08.
- Blatt 4 p. 2: supplied sample, bootstrap standard error, 80% interval and standard-deviation/standard-error distinction. It is not a direct z-interval task. The file is visibly headed Übungsblatt 4, contradicting the old “no recoverable sheet number” claim. Its 2026 heading and sds25 URL are recorded as provenance ambiguity.
- Blatt 5 p. 3: affine outputs 2(a), softmax and decisions 2(b), cross-entropy 2(c), decision rule 2(d). Early tasks no longer demand the whole sheet. The task is one-layer, not a multilayer forward-pass exercise.
- Cornell Fall 2018 HW8 actual PDF: regression-tree construction 1(a) p. 1; pruning 1(b) pp. 1–3; AdaBoost normalization proof Problem 2 p. 3. Spring 2018 HW8 TeX covers ridge regression, perceptrons and kernels and is excluded. Fall PDF and TeX differ on 1(b), so the pruning solution is not certified. Appropriate regression and pruning placements are added; introductory stages defer them.
- UE7 pp. 32–43 defines clustering and families; pp. 44–74 works the algorithm through convergence; p. 75 discusses properties; p. 87 has retrieval questions. Assignments are split by stage and the false claim that UE7 has no worked trace is removed. Its p. 77 exam dates are explicitly 2025 and cannot establish current administration.
- L10 p. 27 (printed 28): independently checked z=-1.7392527131 and lower-tail p=0.0409951605 from n=10, sigma=2, xbar=98.9, mu0=100. The deck's missing sqrt(n) is exposed beside the two relevant stages.
- L11 pp. 37–38 (printed 38–39): rendered p. 38 visibly shows precision-recall axes but calls this ROC. The stage and exam review now distinguish ROC/PR and require a threshold calculation and correct AUC interpretation.
- L04 p. 44 (printed 47): the stated 0.1% prevalence means 0.001, not the displayed 0.0001. With both test rates 0.99, the probability of being healthy conditional on a positive result is 0.909836. L13 p. 31 also overstates that every discussed distance is a metric: cosine similarity is not a distance and 1-cosine has a simple triangle-inequality counterexample. Both corrections appear beside their affected stage readings.

Detailed drafts, before-state evidence and page-by-page stage mapping:
`LearningOS/workbench/audits/sad-semantics-2026-09-07/codex-review/` (`repair.yaml`, `before.json`, `before-hashes.json`, `page-slices.json`, `inventory.json`). The prior `AUDIT.md`, `coverage-evidence.json` and checked images remain evidence, not proof that Gemini closed every finding.

## Linked

Primary pages checked 2026-09-07:

- [scikit-learn nearest-neighbor algorithms](https://scikit-learn.org/stable/modules/neighbors.html#nearest-neighbor-algorithms): §1.6.4.2 KD-tree, §1.6.4.3 ball tree and the algorithm-choice discussion within §1.6.4; the old 1.6.5/1.6.6 attribution is corrected.
- [ROC definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html) and [precision-recall definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html): TPR/FPR and precision/recall respectively.
- [3Blue1Brown episode 3 companion](https://www.3blue1brown.com/lessons/backpropagation/): conceptual account, followed by the calculus lesson. It is not described as a numeric worked backward pass.

Unchanged external routes remain available with their existing selections and placements. Their earlier judgments are inherited, not newly certified; untouched videos and remote exercises were not exhaustively replayed in this follow-up. No new global source evaluation is inferred.

Gemini changed the shared workspace's `sources`, `unit_ids`, `Current Scope` and `Next Action`, replacing the user's separate subject calibration instructions. This repair restores those four fields from the exact pre-Gemini commit. Other workspace fields and all non-SaD curriculum are preserved.

The no-write routing preflight exposed that the restored workspace already referenced registered `source-swanson-principles-probability` without a module source-map entry. A reference-only entry restores that existing option and satisfies the referential contract; it adds no stage assignment or global evaluation. This is a prerequisite to preserving the workspace source list, not a new reading recommendation.

## Completeness

The six import attestations apply to the **bounded revision and its explicit inventory/dispositions**, not a claim that the entire curriculum or every existing source is perfect. Every changed material claim above has opened source evidence; unchanged external sources are retained as inherited/unreverified, and unavailable items are explicit unresolved dispositions. The companion inventory enumerates all SaD routes and placements rather than using registered-source totals as proof.

- Local inventory complete for this repair: current decks and exercise files, relevant book excerpts, Cornell PDF/TeX discrepancy and referenced dependencies inspected. All 106 lecture stage slices recorded individually.
- Linked inventory complete for this repair: the official pages being changed were opened; other linked routes are retained as inherited, not newly signed off.
- Materials opened and content checked for changed claims: yes. Prior rendered source evidence is reused where applicable and L11's ROC/PR diagram was rendered and checked directly.
- Current/prior scope reconciled: stable stage sequence retained; misleading Cornell semester and tutorial administrative dates exposed; source content is distinguished from exam-priority decisions.
- Duplicates and numbering checked: physical PDF pages specified separately from printed slide labels; Fall/Spring Cornell files are not interchangeable; stage and route identities are preserved except for one explicitly added Geometric bridge route.
- Exclusions and unresolved gaps recorded: see the exact list below. These are not silently replaced with invented content.

Unresolved dispositions:

1. **Sachs/Hedderich bibliography item:** named on L01 p. 40, but no registered or locally located copy. Deferred explicitly on the module's current-course source entry. Teschl remains its existing unavailable candidate; Kelleher, Bishop and Goodfellow remain registered options.
2. **Exercise dependencies:** `seattle_house_prices.csv`, `insurance_payouts.csv`, `International_Education_Costs.csv`, and each sheet's own `aufgabe3.py` template were not found in the registered manifest or bounded no-ignore materials/workbench filename search. Exact Moodle files are required for data-dependent implementations; paper-only parts remain usable. This is not a claim that the files exist nowhere on the computer.
3. **Kelleher Gaussian NB solutions:** question verified; a complete solution manual not located.
4. **Cornell pruning solution:** Fall PDF 1(b) differs from the TeX task. Do not treat a neighboring solution file as a verified answer to that PDF part.
5. **Official exam inclusion:** L15 outlook and the precise priority of the Geometric extension need authoritative course scope evidence. Existing exam flags are preserved; no official exclusion or mastery is invented.
6. **Broader material quality:** every untouched external source, author claim and exercise-bank solution has not been individually re-audited. This repair closes the source-backed omissions listed above; it is not universal semantic signoff.

Application/verification evidence will be recorded in the workbench closeout after guarded preflight, import, receipt/projection reconciliation and paired checks. No commit, push or UI installation is part of this follow-up.
