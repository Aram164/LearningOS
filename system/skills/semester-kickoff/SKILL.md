---
name: semester-kickoff
description: Turn the semester — walk every module of the closing term into close-or-carry, harvest the Garden, prune operational residue, and start the new term's modules and workspaces. Use at a term boundary, or when asked to "set up the new semester", "close the semester", or "turn the semester".
---

# Semester Kickoff — Turn the Semester (Learning OS v3)

Implements `system/WORKFLOWS.md` §24. §24 is pure orchestration: every step is an
existing atomic workflow, and this skill's job is to run the boundary without
skipping a fork, not to invent a procedure. Read §24 first — the five steps live
there and are deliberately not restated here.

In v3 a semester is **not** a folder to scaffold. There are no brain files, plan
trees, step-ID prefixes or per-semester tool copies to create: modules,
units and workspaces already carry that structure, and the term boundary only
settles state and opens what comes next.

## The forks that must not be skipped

**Every module of the closing term takes exactly one branch.** Truly done →
close it (§19). Something outlives it — a second attempt not yet sat, thesis
groundwork, an unfinished thread → carry it (§20). No module quietly stays
"active" into the new term because nobody asked.

**Closing has an order that matters.** Durable knowledge lands under
`knowledge/` *before* any workspace is archived (§19 step 2) — an archived
workspace is frozen, so promotion afterwards is too late and the knowledge is
stranded. `standing: true` efforts (degree planning, job) are exempt and never
close on a boundary.

**Harvest the Garden** (CLAUDE.md §14) — the `promotion-ritual` skill. Promote
the ripe, prune the dead, name what is left to gestate.

**Prune operational residue.** `COORDINATION.md` must mention no closed module
(§19 step 4); collections drop entries that served only the closed term (§6b);
the inbox ends empty (§21).

**Plan forward through §18, in its order.** Module record and registration
first, then promote *only* adopted sources into the module source map — never
the whole prospective sea — then one workspace per distinct effort (not one per
module), then dependencies in `COORDINATION.md`. Never open a workspace before
its module record exists; never mint a second record for a module already
present. A merely prospective Master's choice stays quarantined.

**Close with one reviewed commit** (§22 / `los session-end`) — the semester
turns once, reviewably, not across a scatter of half-commits.

## Hard constraints

Module facts are asked, never inferred: registration windows, exam dates, forms
and grades are recorded exactly as Aram or an official document states them
(§10), and they live only in the owning partitioned academic `module.yaml` —
never in prose, never in `COORDINATION.md`, never in a note. Verify the new
term's module list against the official system rather than last term's notes.

Rebuild and validate at the end of each fork, and finish at 0 errors, 0
warnings.
