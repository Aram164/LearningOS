## Capture 2026-09-22 — message from a friend (internship), filed by the operator

```text
"our migration script deadlocked in Postgres: transaction 1 updates accounts
then ledger, transaction 2 updates ledger then accounts. postgres killed one
of them with 'deadlock detected'. fix was to always touch tables in the same
order" — that's literally the exam question
```

Connects to: note-deadlock-four-conditions (a global lock order breaks circular wait); note-two-phase-locking-deadlocks (the database finds the waits-for cycle and aborts a victim — Postgres' 'deadlock detected'); work/inbox/20260915-os-oral-questions.md ("How can deadlock be prevented? Which condition would you break in practice?").
