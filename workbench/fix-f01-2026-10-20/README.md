# F-01 fixing pass — workbench record (2026-10-20)

The record of the fixing pass that closed the F-01 scope hole and its
neighbours, published so a reviewer can read the plan, the outcome, the
measurements and the certification behind the branch — not only the diff.

It is published under `repository/workbench/` because the tree contract
declares that directory for *"published migration review documents and
execution evidence; not learner data"*, and this is exactly that.

## What is here

| file | what it is |
|---|---|
| [`FIXING-PLAN.md`](FIXING-PLAN.md) | the plan the fixing agent worked from, item by item (W1–W8), with the decisions it queued for Aram |
| [`OUTCOME.md`](OUTCOME.md) | what shipped, how it was verified, and what it does **not** do |
| [`GRANULARITY-274.md`](GRANULARITY-274.md) | Aram's question about the 274 source-level cases, answered with measurements |
| [`REPORT.md`](REPORT.md) | the report: the three answers, the warning decomposition, the two residuals |
| [`INTEGRATION.md`](INTEGRATION.md) | the integration branch: what it carries, how it was certified, how to reproduce it |
| [`tools/`](tools/) | the scripts the numbers come from |

## The scripts

Each takes the Core checkout it measures as its argument, or finds it
automatically (the nearest ancestor that *is* a Core checkout; otherwise the
nearest ancestor with one named `repository` beside it).

| script | what it measures |
|---|---|
| [`tools/measure_scope.py`](tools/measure_scope.py) | the population the scope rule reports: stage resources, route bindings, and the rows it reports, by cause |
| [`tools/breakdown.py`](tools/breakdown.py) | the modules' source-map shapes: rich routes vs legacy `unit_routes`, and the (source, locator) pairs each declares |
| [`tools/granularity.py`](tools/granularity.py) | the 1,462 reported rows, split by *what the records say*: no source named / the unit adopted it / the unit never disposed of it / no module adopted it |
| [`tools/unit_ownership.py`](tools/unit_ownership.py) | whether a unit-aware scope rule would flag anything the module-level rule passes: 685 rows take the (source, locator) path, and all 685 are declared by the row's own unit |
| [`tools/check_pins.py`](tools/check_pins.py) | whether every digest the scenario fixtures pin still matches the bytes it names — the check that caught the delivery record's digest being re-pinned in the wrong order |
| [`tools/split_by_cause.py`](tools/split_by_cause.py) | splits a churn by cause: the digests that moved with a record-shape change, put back, leaving the counts where they are |
| [`tools/rebuild_branch.sh`](tools/rebuild_branch.sh) | rebuilds the branch as one commit per finding, each green on its own |
| [`tools/snapshot_total.sh`](tools/snapshot_total.sh) | snapshots the final working state: every file that differs from the base |
| [`tools/verify_commits.sh`](tools/verify_commits.sh) | verifies every commit of the branch on its own, in its own worktree |
| [`tools/run_scope_probe.py`](tools/run_scope_probe.py) | runs the external harness's F-01 scope probe against a checkout of your choosing |

## The external evidence is not here

The evaluation harness that produced the findings — and the re-run of it
against the fixed tree — is published on its own branch,
`origin/evidence/los-canvas-2026-10-20`, because the harness sits at the
repository root and the tree contract denies an undeclared directory
there. Measured: `los-canvas/` at the root is one validation error
(`TREE-UNDECLARED`); the same directory under `workbench/` is accepted.
The fix commits cite `los-canvas/reports/t05` and
`los-canvas/canvas/probes/probe_scope_gap.py`, and those paths resolve
literally on that branch.

## Reproducing the measurements

From a Core checkout with its sibling `../obsidian-ui` and `../materials`:

```bash
.venv/bin/python workbench/fix-f01-2026-10-20/tools/granularity.py
```

The corpus numbers do not depend on the branch: the curriculum the rule
reads is the same in every commit of the fixing branch.
