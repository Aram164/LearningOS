# ADR-010 — The bounded first-party Job surface (read model + write path)

**Date:** 2026-08-14 · **Status:** accepted (Aram)
**Supersedes nothing. Extends:** ADR-003 (Job↔LearningOS boundary workflow),
ADR-004 (hygiene-sweep carve-out), ADR-006 (interface layer boundary).
**Records retroactively:** the first-party Job view exception Aram approved on
2026-08-12, which until now existed only as prose in `CLAUDE.md` §13 and
`ARCHITECTURE.md` §24 with no decision record behind it.

## Context

`Job/` is quarantined (`CLAUDE.md` §13): outside the default search space, never
read, indexed, or cited without an explicit conversational command. Invariant 24
states that Master's quarantined content and Job content never enter the normal
manifest.

That invariant was written for *leakage* — the failure where employment-specific
material seeps into the academic canon, into recommendations, into AI context.
It was not written to mean the learner may never look at their own job material
through their own application. Read literally, it left Aram with a folder the
system refused to show him, and so the Job area developed no surface at all:
`scratch/` stayed empty although the workspace's `Next Action` said to log
sessions there, and note drift was detected but never repaired, because every
repair was a manual edit nobody was prompted to make.

Two decisions were needed. One had already been made in conversation and never
recorded; the other is new.

## Decision

**1. A bounded read model (approved 2026-08-12, recorded here).**
Deliberately opening the Job destination is itself an explicit Job access
gesture. It invokes the `job-dashboard-v1` query, which reads only
`Job/dashboard.yaml` and its allowlisted note, workspace, plan, and paper paths.
The response is read-only, ephemeral, and confined to that view. It is never
written to `generated/manifest.json`, indexed by global search, included in
recommendations or AI context, or reachable through ordinary file-opening paths.
Closing the app ends the grant.

**2. A bounded write path (new).**
Job work produces material — session logs, note re-verification, track progress.
Those writes go through the same gateway discipline as canonical writes, with
one difference: the transaction is rooted at `Job/` rather than at the
repository.

Rooting the existing `TransactionService` at `Job/` is what makes this safe, and
it is the whole of the mechanism. Containment is not a new check to maintain —
it falls out of the engine's existing `_safe_relative` guard, which refuses any
path outside its root. A Job write therefore *cannot* reach the canon, for the
same reason and by the same code that a canonical write cannot reach outside the
repository. The revision ledger and receipts land under
`Job/operations/transactions/`, so the audit trail stays on the Job side of the
boundary where it belongs.

Three capabilities are introduced, each requiring `--confirm-job-access`:

| capability | writes | purpose |
|---|---|---|
| `job.session.log` | `Job/workspace-job-deem/scratch/**` | append one session entry |
| `job.note.stamp` | `Job/notes/**` | re-stamp a living note's `verified_against` |
| `job.track.progress` | `Job/operations/progress.yaml` | record a completed track session |

## Boundaries this decision does not move

- The **quit test** (`Job/WORKFLOW.md` §1) still decides placement. Transferable
  knowledge goes to the canon even when job-motivated; only employment-specific
  artifacts live in `Job/`.
- **Reference stays one-way.** Job may cite canonical IDs; the canon never cites,
  indexes, or reads Job. `canonical_shelf` in `dashboard.yaml` is a Job-side
  pointer list, not a canonical backlink.
- **Promotion stays manual** (`WORKFLOW.md` §4): Job → canon happens only on
  Aram's explicit say-so, item by item, stripped of employer-internal detail,
  through `work/inbox/` and normal routing. No write capability here creates a
  side door.
- **Note authorship is unchanged.** `Job/notes/README.md` is binding: *"You write
  the notes; I file, restructure, and prune them."* `job.note.stamp` edits only
  the living-note header lines — `verified_against` and `status` — and never the
  body. Drift is *reported* with a diff; whether the prose still holds is Aram's
  judgment, not the tool's.

## Consequences

**Authored files are not machine-rewritten.** Track progress lives in a
machine-owned `Job/operations/progress.yaml`, not in the hand-authored
`dashboard.yaml`. The 2026-08-08 engineering audit found a bug of exactly this
shape in the canon — an authored YAML re-serialised on every write, destroying
comments — and the same mistake is refused here by construction. The dashboard
reader merges progress at read time; the authored config stays untouched.

**The snapshot guard is Job-scoped.** `canonical_fingerprint` digests the
canonical roots (`knowledge/`, `curriculum/`, `work/`, …), none of which exist
under `Job/`, so rooted there it would return a constant and silently mean
nothing. `TransactionService.commit` therefore takes an optional `fingerprint`
hook; the canon keeps its existing default, and the Job writer supplies a digest
over the Job artifacts it actually touches. A receipt that records a snapshot
records a real one.

**Job state remains invisible to the canon.** No capability here writes outside
`Job/`, nothing calls `_publish`, and no validator sweeps the tree — `make check`
neither validates Job content nor is weakened by its existence. The only
pre-existing exception stands unchanged: ADR-004 lets the hygiene sweep list
*file names and mtimes* (never content) under
`Job/workspace-job-deem/inputs/` to detect cross-boundary shadow copies.

**A failure mode is closed.** Before this, the honest description of the Job area
was that the system could see it and not touch it, so the disciplines it defined
for itself — session logging, the `verified_against` contract — had no mechanism
and quietly did not happen. An unenforceable discipline is not a stricter policy
than an enforced one; it is an absent one.
