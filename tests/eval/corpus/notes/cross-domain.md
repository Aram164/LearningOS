Durable notes — cross-domain syntheses and learning practice.

=== note-caching-everywhere
domain: cross-domain
title: The same cache idea in three courses
created: 2026-07-05
role: synthesis
state: rough
authorship: user
concepts: [concept-cpu-caches, concept-buffer-management, concept-dynamic-programming]
sources: []
---
Noticed while revising for the DB exam: three courses taught me the same
move — keep a small, fast copy of something expensive, and decide what to
throw away when it is full.

- CPU caches: hardware keeps recently used memory lines close to the core.
- Database buffer pool: the DBMS keeps disk pages in RAM.
- Memoization in dynamic programming: keep the answer to a subproblem instead
  of recomputing it.

The eviction question is different in each: hardware must decide in
nanoseconds with no knowledge of the program; the buffer pool knows whether a
page belongs to a scan; memoization often never evicts at all.

Not sure this is more than a pun, but writing it down.

=== note-spaced-repetition-scheduler
domain: cross-domain
title: How the review scheduler decides
created: 2026-04-12
role: synthesis
state: evolving
authorship: user
concepts: [concept-spaced-repetition]
sources: [source-anki-manual]
---
My flashcard app's scheduler (SM-2 style): after each review I rate the card;
the next interval is the previous interval × an ease factor (starting at 2.5).
"Again" resets the interval to one day and lowers the ease; "easy" raises it.

So a card I keep getting right is shown after 1, 3, 8, 20, 50 … days, and the
daily queue stays short even with thousands of cards.

Rules I set myself: no more than 20 new cards a day; never skip a day of
reviews (the backlog grows faster than you think); write cards myself instead
of downloading decks.

=== note-study-plan-retake-strategy
domain: cross-domain
title: Retake plan — splitting time fairly between two exams
created: 2026-07-26
role: synthesis
state: evolving
authorship: user
concepts: [concept-study-planning]
sources: []
contexts: [workspace-statlearn-retake, workspace-os-oral-prep]
---
Two exams in October, six weeks. How to schedule study time so neither
starves?

- Fixed weekly share: Statistical Learning gets two thirds of study blocks,
  OS one third, because the Klausur needs derivations under time pressure and
  the oral mostly needs fluent talking.
- If one subject falls behind its share for a week, it gets the first blocks
  of the next week (catch-up before new material).
- Hard rule: one mock exam per subject before the last week.

What I'm unsure about: whether to alternate subjects daily or in two-day
blocks. Daily switching feels productive but I lose the first half hour
getting back into the topic.

=== note-pomodoro-and-context-switching
domain: cross-domain
title: Pomodoro and the cost of switching subjects
created: 2026-05-01
role: synthesis
state: rough
authorship: user
concepts: [concept-study-planning]
sources: []
---
Tried 25-minute pomodoros for two weeks.

Worked for exercise sheets. Did not work for derivations: the bell rang right
when I finally had the whole proof in my head, and after the break it took ten
minutes to reload it.

Switching subjects between pomodoros was worse: going from OS to statistics
costs me roughly twenty minutes before I am properly thinking again. Now I do
one subject per half day and use 50-minute blocks for derivations.

=== note-weekly-review-log
domain: cross-domain
title: Weekly review log (summer)
created: 2026-06-30
updated: 2026-09-14
role: synthesis
state: evolving
authorship: user
concepts: [concept-study-planning]
sources: []
---
- **2026-06-30** — Linear algebra refresh paused; exams first. PCA stalled at
  the SVD step.
- **2026-07-20** — DB exam done. Withdrew from Statistical Learning 1. Termin.
- **2026-08-10** — Started the dataframe skill module. Tessera parser and
  executor working.
- **2026-08-24** — New priority decision (recorded in coordination).
  Ledgerline paused.
- **2026-09-07** — L05 stage 1 finished; the generative/discriminative
  comparison still open. OS scheduling going well.
- **2026-09-14** — Lost most of the week to a cold. Behind on L07. Did not
  touch Tessera.

=== note-how-i-take-notes
domain: cross-domain
title: How I take notes
created: 2026-04-10
role: synthesis
state: evolving
authorship: user
concepts: []
sources: []
---
Rules I am trying to follow in this repository:

- Write in my own words first, then check against the source.
- Derivations get every step, including the ones that felt obvious — they
  never feel obvious three weeks later.
- If I'm unsure, write "unsure" instead of smoothing it over.
- Wrong notes are not deleted; a later note corrects them and says so.
- Quick thoughts go to the inbox; half-formed ideas that might grow go to the
  garden.

=== note-oral-exam-prep-strategy
domain: cross-domain
title: Preparing for an oral exam
created: 2026-09-05
role: synthesis
state: rough
authorship: user
concepts: [concept-study-planning]
sources: []
contexts: [workspace-os-oral-prep]
---
Advice collected from two seniors who did the OS oral last year:

- The chair starts with "tell me about X" and follows up on whatever you say
  — so only mention things you can explain one level deeper.
- Draw while talking: Gantt charts for scheduling, page-table walks, the
  resource-allocation graph.
- Practise out loud, recorded, 5 minutes per topic, then listen back.

Exam date: I have it in my calendar as 14 October (from the registration
email draft); check the confirmed slot before booking travel.

=== note-semester-review-july
domain: cross-domain
title: End-of-semester review (July)
created: 2026-07-24
role: synthesis
state: rough
authorship: user
concepts: [concept-study-planning]
sources: []
---
What went well: Database Systems — steady weekly work, the exam felt fair.
What went badly: Statistical Learning — I kept postponing L07 onwards and
withdrew from the first sitting. Operating Systems — attended but did no
exercises after May.

Lessons:
- Exercise sheets every week, not in exam week.
- The linear algebra refresh should have been done *before* the semester.
- Too many parallel side projects in July.
