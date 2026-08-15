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
gesture. It invokes the `job-dashboard-v2` query, which reads only
`Job/dashboard.yaml` and its allowlisted note, workspace, plan, and paper paths.
The response is read-only, ephemeral, and confined to that view. It is never
written to `generated/manifest.json`, indexed by global search, included in
recommendations or AI context, or reachable through ordinary file-opening paths.
Closing the app ends the grant.

**2. A bounded write path (new).**
Job work produces material — session logs, learner-authored notes, study plans,
tasks, note re-verification, and track progress.
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

Six capabilities are available, each requiring `--confirm-job-access`:

| capability | writes | purpose |
|---|---|---|
| `job.session.log` | `Job/workspace-job-deem/scratch/**` | append one session entry |
| `job.note.stamp` | `Job/notes/**` | re-stamp a living note's `verified_against` |
| `job.note.save` | `Job/notes/**` | create or explicitly revise exact learner-authored note text |
| `job.plan.save` | `Job/plans/**` | create or revise a structured long-term study plan |
| `job.task.save` | `Job/operations/tasks.yaml` | create, update, or complete a Job-only task |
| `job.track.progress` | `Job/operations/progress.yaml` | complete or reopen a declared track session |

The dashboard publishes a Job-specific snapshot plus per-artifact revisions.
Every UI mutation carries both; stale state is refused before a read-modify-write
operation begins. The UI refreshes only the ephemeral Job model after a
conflict, preserves the learner's draft, and never retries the rejected change
without another explicit save.

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
  the notes; I file, restructure, and prune them."* `job.note.save` persists only
  text the learner entered and explicitly approved; it is never an AI action.
  `job.note.stamp` edits only the living-note header lines — `verified_against`
  and `status` — and never the body. Drift is *reported* with a diff; whether the
  prose still holds is Aram's judgment, not the tool's.

## Consequences

**Authored configuration and legacy plans are not machine-rewritten.** Track
progress and tasks live in machine-owned files under `Job/operations/`, not in
the hand-authored `dashboard.yaml`. Editable study plans use structured files in
`Job/plans/`; a plan with the same stable id shadows its legacy Markdown source
without changing or deleting it. The 2026-08-08 engineering audit found a bug of
exactly this shape in the canon — an authored YAML re-serialised on every write,
destroying comments — and the same mistake is refused here by construction. The
dashboard reader merges all three sources at read time.

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

## Amendment 2026-08-15 — the Job surface renders as an ordinary LearningOS view

The first cut of the surface stated its own design rationale in its own UI. Each
section carried a sentence explaining why it was built that way: *"The workspace
decides this, not the view"*, *"One shelf, ordered by when you need it — not
split by whether it happens to be a track, a paper or a book"*, and, under every
canonical book, *"Lives in the LearningOS canon — Job points at it, never the
reverse."* Every one of those claims is true and none of them belonged on
screen. A view that argues for itself reads as internal tooling, and the reader
came to do a session, not to review the argument. They are recorded here
instead, which is where an argument is checkable.

Three further corrections, same cause:

- **The confidentiality banner is gone.** The sealed gate you click through to
  load the dashboard *is* the access gesture and states the contract. Repeating
  it above all three destinations restated something the reader had agreed to
  thirty seconds earlier. This is the rule `OWNERSHIP_STATEMENT` already
  follows — state it once, at the place where it is load-bearing.
- **Job uses the system's tab row.** Garden, Review and Job had each grown a
  private copy of one loop, and the third had drifted into a different look and
  skipped `is-active`. The definition now lives once in `components.ts` as
  `filterTabs`, and all three call it.
- **Job uses the system's card.** `los-job-note`, `los-job-material`,
  `los-job-drift` and `los-job-layer` were four boxes with a border and a title,
  none distinguishable from `los-card` in any way a reader could name. The
  stylesheet also still carried twenty classes from the retired four-tab design
  that no code emitted. Both are removed; the sheet drops from 286 lines to 57.

What is deliberately kept: an empty pipeline layer still says *"No note
describes this layer yet"*, because an undocumented layer is a finding rather
than an absence, and the drift queue still names the component each note
describes. Those are facts about the work, not commentary about the view.

The cost is that the canon-ownership rule for shelved books is now expressed
only by where the button goes — `Open in Library`, never a Job path — and is
enforced by a routing test rather than by a sentence the reader can see. If that
rule is ever violated the surface will no longer say so out loud; the test is
what has to catch it.

## Amendment 2026-08-15 — Job becomes an editable learning workspace

The reusable Figma library and three template families were used as the design
reference: product-development roadmaps for milestones and runway, quarterly
planning for horizon grouping, and meeting notes for the capture → refine →
revisit loop. Those patterns are translated into the existing LearningOS visual
language rather than copied as a second design system.

Job now has five destinations: **Today**, **Tasks**, **Plans**, **Notes**, and
**Library**. Today is a digest with one dominant next session plus small task,
plan, note, and drift previews. The other four destinations own the durable
work. This mirrors the normal LearningOS separation between a focused home and
the workspaces behind it, while keeping all Job data quarantined.

The implementation is distributed by responsibility:

- Core publishes and mutates the Job read model through declared capabilities.
- The gateway owns Job snapshots, revisions, serialization, and refusals.
- Feature modules own Tasks, Plans, Notes, Library, and Today independently.
- The boundary view composes those modules and owns only ephemeral view state.
- Shared LearningOS components and palette tokens remain the visual foundation;
  Job CSS contains only layout that the shared primitives cannot express.

Legacy Markdown study plans remain readable and can become editable by creating
a structured plan with the same stable id. No migration rewrites the original.
