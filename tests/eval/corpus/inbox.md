Unrouted captures in work/inbox/ at the start of the world. Key = file name.
`routed:` removes a capture from the inbox on that date (it was filed).

=== 20260502-spam-filter-idea.md
date: 2026-05-02
routed: 2026-05-07
---
spam filter exercise — maybe count words per class and multiply? ask in tutorial

=== 20260812-lazy-plan-explain-paste.md
date: 2026-08-12
---
pasted from the notebook:

    naive plan:
    FILTER [(col("country")) == (String(DE))] FROM
      INNER JOIN:
      LEFT PLAN ON: [col("customer_id")]
        CSV SCAN orders.csv; PROJECT */31 COLUMNS
      RIGHT PLAN ON: [col("id")]
        CSV SCAN customers.csv; PROJECT */12 COLUMNS

    optimized plan:
    INNER JOIN:
    LEFT PLAN ON: [col("customer_id")]
      CSV SCAN orders.csv; PROJECT 3/31 COLUMNS
    RIGHT PLAN ON: [col("id")]
      CSV SCAN customers.csv; PROJECT 2/12 COLUMNS; SELECTION: [(col("country")) == (String(DE))]

why did the filter disappear from the top?? and where did the other columns go

=== 20260816-drf-paper-link.md
date: 2026-08-16
---
read later: Dominant Resource Fairness (Ghodsi et al., NSDI 2011) — the
speaker at the internship fair mentioned it for GPU sharing

=== 20260903-pvalue-reminder.md
date: 2026-09-03
---
!!! did it AGAIN in the mock: wrote "p = 0.02 so 2% chance H0 is true". NO.
p-value = probability of data at least this extreme IF H0 is true.

=== 20260910-tessera-todo.md
date: 2026-09-10
---
tessera todo
- [ ] filter-below-join rule (only when predicate columns come from one side)
- [ ] projection pruning
- [ ] property test: execute(optimize(q)) == execute(q) for random q
- [ ] rules fighting each other → optimizer never terminates? (merge-filters vs split-filters)
- [x] constant folding of 1 = 1

=== 20260914-batchnorm-forum-question.md
date: 2026-09-14
---
forum thread: someone says batch norm does NOT actually fix internal
covariate shift and the original explanation is wrong?? check before the exam

=== 20260915-os-oral-questions.md
date: 2026-09-15
---
Questions from last year's OS orals (from Jana and Tim):
- Explain how the scheduler on your laptop decides what runs next.
- What is the difference between a process and a thread?
- Walk me through what happens on a page fault.
- Why is a TLB needed? What happens on a context switch to the TLB?
- How can deadlock be prevented? Which condition would you break in practice?
- What is priority inversion? Give a real example.

=== 20260916-sleep-podcast.md
date: 2026-09-16
---
podcast: sleep after learning helps consolidation — people who slept after
studying word pairs recalled ~20% more the next day. maybe stop studying at
midnight before the exams?
