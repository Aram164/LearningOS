# The integration branch — both review branches, one certified revision

**Branch:** `integration/scope-and-cleanup-2026-10-20`
**Base:** the certified pair's Core, `40d8afe` (UI `66ca47aa`)
**Purpose:** one branch that carries both review branches, so that the
combination can be certified as a pair instead of two branches that are
each certified alone.

## What it carries

```
40d8afe  the certified pair's Core
  ├─ <merge>  the unverified-cleanup review branch
  │    a8564f6c  docs(core): describe the current learning_os package layout
  │    1774be5c  refactor(core): remove the dead refusal-rendering helpers
  │    7afa162c  refactor(core): one owner for the idempotency-ledger serializer
  ├─ <merge>  the F-01 scope fixes
  │    c7e50300  fix(core): F-02 — the resume screen names the requirement the write path accepts
  │    5f205fae  fix(core): F-03 — a note body may not carry its own frontmatter
  │    0fd50412  fix(core): F-04 — the two material resolvers agree on a fragment
  │    d0f9adff  fix(core): F-01 B — the CLI cannot mint the app's own provenance
  │    e14b1783  fix(core): F-01 C — workflows 23, 24 and 27 are a stop-and-ask
  │    8db9ffdf  fix(core): F-01 A — a stage resource must resolve to material its module adopted
  │    9e762c3d  fix(core): F-05 — the promotion's verification must name a content-bound artifact
  └─ <this commit>  docs: the fixing pass's workbench record
```

Two merge commits, not a rebase: the provenance of the branch is readable
from its history — which review contributed what, and where.

**The merge is clean, and it is clean for a reason.** The cleanup branch
touches 14 files, all in `tools/` and docs; the fixing branch touches the
code, the schemas, the procedures and the fixtures. They share no file, and
the cleanup branch touches no canonical root, so it moves no fingerprint and
needs no churn of its own. (Measured before the merge: both merges applied
without a conflict.)

## How it was certified

```bash
make system-check        # lint, typecheck, the offline validator, the
                         # warning-baseline gate, the whole pytest suite,
                         # the UI's npm run check, and the pair stamp
```

`make system-check` ends with `tools/verified_pairs.py stamp`, which writes
the memo that says *this* Core SHA, *this* UI SHA and *this* toolchain were
verified together. The stamp is a local memo (`.git/learningos-verified-pairs.jsonl`),
not a committed artifact: the authority for a released pair is the
release-pair receipt.

The certified revision is **this branch's tip**. To check it on your own
machine:

```bash
.venv/bin/python tools/verified_pairs.py check   # exit 0 iff the pair is stamped
.venv/bin/python tools/verified_pairs.py base    # the last stamped Core SHA
```

`make system-check` needs the sibling trees: `../obsidian-ui` for the UI's
own check and the paired Gateway-recovery test, and `../materials` for the
material-dependent scenarios. A checkout without them reports failures that
are environmental, not real.

## The fixing branch, commit by commit

Each of the seven commits is green on its own — verified in its own
worktree, with the whole suite, at that commit. The branch is therefore
reviewable one finding at a time, which is what the brief asked for ("the
canvas review was wrong twice before").

The two commits that carry the bulk of the churn are the two that needed it:

* **F-01 A** carries the scope rule, the measured warning baseline, the
  synthetic fixtures' own baselines, the 35 procedure transcripts and the
  211 scenario recordings — the rule changes what the demo world reports, so
  every transcript that prints a warning count and every recording that
  captures one moves with it.
* **F-05** carries the promotion schema, the data-contract bump (v56) and
  the transcripts and recordings that pin the world's canonical fingerprint
  — the schema's bytes moved, so every digest that covers them moved with it.

The split is by cause, not by convenience: the *digests* go with F-05 and
the *counts* go with F-01 A, so each commit's transcripts and recordings
match the world as it stands at that commit. The machinery is
`tools/split_by_cause.py` and `tools/rebuild_branch.sh` in this directory.

## What is deliberately not on this branch

* **`origin/main` is untouched.** Merging is Aram's call.
* **The external evaluation harness is not on this branch.** It is published
  as `origin/evidence/los-canvas-2026-10-20`, because the harness sits at
  the repository root and the tree contract denies an undeclared directory
  there — measured: `los-canvas/` at the root is one validation error
  (`TREE-UNDECLARED`), the same directory under `workbench/` is accepted.
  The fix commits cite `los-canvas/reports/t05` and
  `los-canvas/canvas/probes/probe_scope_gap.py`; those paths resolve
  literally on the evidence branch.
