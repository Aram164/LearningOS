Workspaces of the synthetic learner. Each item: `=== workspace-id`, YAML
frontmatter fields plus `date` (last touch), optional `history` (earlier
touches), optional `archived: true`; then the CONTEXT.md body.

=== workspace-statlearn-retake
title: Statistical Learning retake (2. Termin)
created: 2026-07-14
date: 2026-09-15
status: active
standing: false
deadline: 2026-10-06
program_ids: [program-bachelors]
module_ids: [module-tuh-statlearn]
unit_ids: [unit-statlearn-l03, unit-statlearn-l05, unit-statlearn-l07, unit-statlearn-l09, unit-statlearn-l11]
concepts: [concept-naive-bayes, concept-regularization, concept-bias-variance-tradeoff, concept-pca, concept-backpropagation]
notes: [note-naive-bayes-spam-filter, note-bias-variance-decomposition-lecture, note-ridge-regression-penalty, note-pca-by-hand, note-statlearn-mock-exam-september]
---
## Objective

Pass the Statistical Learning exam at the 2. Termin. Withdrew from the July
sitting because L07–L11 were not solid; the retake is the only remaining
chance this academic year.

## Current Scope

L05 (generative vs discriminative) is half done. L07 regularization is the
biggest gap. L09 PCA stalled when I paused the linear algebra refresh in June —
the SVD part is exam scope and I still owe it. L11 not started.

## Open Questions

- Is the SVD proof likely to be asked, or only the PCA computation?
- Do I need to memorize the ridge closed form or just derive it?

## Next Action

Finish the L05 comparison (stage 2), then start the L07 ridge/lasso stage.
Book a mock exam under timed conditions for the first week of October.

## Deferred

- Kernel methods beyond the SVM definition — not on the exam sheet.

=== workspace-os-oral-prep
title: Operating Systems oral exam prep
created: 2026-08-19
date: 2026-09-16
status: active
standing: false
deadline: 2026-10-12
program_ids: [program-bachelors]
module_ids: [module-tuh-os]
unit_ids: [unit-os-l02, unit-os-l05, unit-os-l07]
concepts: [concept-cpu-scheduling, concept-proportional-share, concept-virtual-memory, concept-deadlock]
notes: [note-cpu-scheduling-round-robin, note-cfs-fair-share, note-virtual-memory-address-translation, note-deadlock-four-conditions, note-os-scheduling-exercise-bank]
---
## Objective

Be able to talk fluently for 30 minutes about scheduling, virtual memory and
deadlock, including follow-up "why" questions.

## Current Scope

Scheduling first (L02), then virtual memory (L05), then concurrency (L07).

## Open Questions

- How deep does the chair go on CFS internals (red-black tree, vruntime)?

## Next Action

Continue the proportional-share stage: work one stride-scheduling example by
hand, then explain vruntime aloud.

=== workspace-dataframe-skill
title: Lazy dataframe engines (skill)
created: 2026-08-04
date: 2026-09-10
status: active
standing: false
program_ids: [program-skills]
module_ids: [module-skill-dataframes]
unit_ids: [unit-dataframes-lazy-plans, unit-dataframes-joins-at-scale, unit-dataframes-lineage]
concepts: [concept-lazy-evaluation, concept-query-optimization, concept-data-provenance]
notes: [note-lazy-evaluation-query-plans, note-data-lineage-debugging]
---
## Objective

Get fluent with a lazy dataframe engine: read query plans, predict what the
optimizer will do, and debug wrong results in multi-step pipelines.

## Current Scope

Reading explain() output (stage 2 of the lazy-plans unit).

## Open Questions

- Which optimizations are rule-based and which use statistics?

## Next Action

Annotate three explain() plans and name each optimization that fired.

=== workspace-tessera-engine
title: Tessera query engine
created: 2026-07-30
date: 2026-09-09
status: active
standing: false
project_id: project-tessera
program_ids: [program-skills]
module_ids: [module-skill-dataframes]
unit_ids: [unit-dataframes-lazy-plans]
concepts: [concept-query-optimization, concept-visitor-pattern, concept-rust-ownership]
notes: [note-tagless-visitor-pattern-ast, note-rust-ownership-borrowing]
---
## Objective

A working rule-based optimizer for Tessera's logical plans.

## Current Scope

Rewrite rules over the plan tree. Parser and executor are done.

## Open Questions

- How do I make rule application terminate when two rules undo each other?
- Should projection pruning run before or after filter pushdown?

## Next Action

Implement the filter-below-join rule and write tests that compare results
before and after rewriting.

=== workspace-ledgerline
title: Ledgerline notes tool
created: 2026-08-01
date: 2026-08-24
status: blocked
standing: false
project_id: project-ledgerline
program_ids: [program-skills]
concepts: [concept-event-sourcing, concept-idempotency]
notes: [note-event-sourcing-append-only, note-idempotency-keys-api]
---
## Objective

Design the receipt format for Ledgerline before writing any code.

## Current Scope

Paused until after the October exams (decision 2026-08-24).

## Open Questions

- Should a receipt store the full new text or a diff?
- How to make retried saves not produce duplicate receipts?

## Next Action

None until after 2026-10-12.

=== workspace-linalg-refresh
title: Linear algebra refresh
created: 2026-05-04
date: 2026-06-12
status: active
standing: false
program_ids: [program-skills]
module_ids: [module-skill-linalg-refresh]
unit_ids: [unit-linalg-eigen, unit-linalg-svd]
concepts: [concept-eigendecomposition, concept-svd, concept-low-rank-approximation]
notes: [note-eigenvectors-intuition, note-svd-geometric, note-low-rank-approximation]
---
## Objective

Refresh eigenvectors and the SVD well enough to follow the ML lectures.

## Current Scope

Low-rank approximation (stage 2 of the SVD unit).

## Open Questions

- Could low-rank approximation be how recommenders fill in missing ratings?

## Next Action

Finish the image-compression experiment at ranks 5, 20 and 50.

=== workspace-dbsys-exam
title: Database Systems exam prep
created: 2026-06-20
date: 2026-07-20
archived: true
status: complete
standing: false
program_ids: [program-bachelors]
module_ids: [module-tuh-dbsys]
concepts: [concept-query-optimization, concept-transactions-acid, concept-write-ahead-logging]
notes: [note-algebraic-equivalences-pushdown, note-write-ahead-logging-aries, note-db-exam-cheatsheet]
---
## Objective

Pass the Database Systems exam on 2026-07-15.

## Current Scope

Complete. Exam taken 2026-07-15.

## Open Questions

None.

## Next Action

None — archived after the exam.

=== workspace-statlearn-retake @2026-07-14
---
## Objective

Pass the Statistical Learning exam at the 2. Termin.

## Current Scope

Everything from L05 onwards.

## Open Questions

- Which lectures are exam-relevant beyond the slides?

## Next Action

Register for the 2. Termin when the window opens; start L05 stage 1.

=== workspace-statlearn-retake @2026-08-31
---
## Objective

Pass the Statistical Learning exam at the 2. Termin. Withdrew from the July
sitting because L07–L11 were not solid; the retake is the only remaining
chance this academic year.

## Current Scope

L05 stage 1 (derivation) in progress; L07 map created today.

## Open Questions

- Is the SVD proof likely to be asked, or only the PCA computation?

## Next Action

Finish the L05 derivation without slides.

=== workspace-os-oral-prep @2026-08-19
---
## Objective

Be able to talk fluently for 30 minutes about scheduling, virtual memory and
deadlock.

## Current Scope

Scheduling first (L02).

## Open Questions

- How deep does the chair go on CFS internals?

## Next Action

Solve the classic-policy exercises (Gantt charts).

=== workspace-tessera-engine @2026-08-04
---
## Objective

A working rule-based optimizer for Tessera's logical plans.

## Current Scope

Plan-tree representation and the rule driver.

## Open Questions

- How do I make rule application terminate when two rules undo each other?

## Next Action

Write the transform_up driver and the first three rules.
