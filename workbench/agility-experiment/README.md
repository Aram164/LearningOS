# Initial change-proportionality baseline

Date: 2026-10-28. Experimental development evidence. Initial raw results: [baseline.json](baseline.json); clean first-increment reproduction: [baseline-clean-d32d2cf8.json](baseline-clean-d32d2cf8.json), with [provenance](baseline-clean-d32d2cf8-provenance.json). Driver: [baseline.py](baseline.py). Campaign and decisions: [execution plan](../../work/proposals/2026-10-28-agility-experiment-plan.md).

## What ran

Three ordinary changes, with stage movement also measured on 2, 10 and 50 stages. Each run creates and deletes its own synthetic repository in a temporary directory. The production CLI performs a no-write preflight, a separate scripted review of the exact approved content, and one guarded application. There is no option to point the driver at a live repository.

The preservation oracle compares authored files before/after, checks the intended map or Unit change, and requires one transaction receipt. Setup and the oracle are excluded from the measured commands. A subprocess-local wrapper counts actual `Validator.run` calls; it changes no production code. Fixtures adopt their existing content warnings before the change, and every proposed change must pass the existing no-new-warning gate.

## Observed results

| Change | Existing stages | Draft bytes | Existing stage records reproduced | Existing route records reproduced | CLI commands | Full validations | Receipts |
|---|---:|---:|---:|---:|---:|---:|---:|
| Append one existing resource | 1 | 768 | 0 | 0 | 2 | 2 | 1 |
| Move one stage | 2 | 1,672 | 2 | 0 | 2 | 1 | 1 |
| Move one stage | 10 | 7,285 | 10 | 0 | 2 | 1 | 1 |
| Move one stage | 50 | 35,525 | 50 | 0 | 2 | 1 | 1 |
| Add one Unit | 1 | 3,464 | 0 | 1 | 2 | 2 | 1 |

All five runs passed the preservation oracle. Every preflight reported zero canonical writes. Stage movement used `unit.map.import` with its explicit reorder reason and exact snapshot/revision guards. Appending and Unit extension used `module.plan.import` and its saved-preflight apply shortcut.

The benchmark was independently rerun from the clean first-increment commit `d32d2cf8c25d3115740939962cbd1e0c7b3e152b` before the review-incorporation edits. All five structural results and draft hashes match this table and the initial run; measured source hashes match the clean tree. The reproduction and its provenance are separate retained artifacts, so later documentation commits do not pretend to be the commit that was measured.

**Decision:** stage movement is the first structural editing candidate: the same request required every stage record in its draft, growing from 1,672 to 35,525 bytes as the containing map grew. Resource appending already avoids reproducing old placements; reuse that behavior and investigate insertion/movement within a stage rather than implement append again. Unit extension remains a later candidate: the measured full import reproduced an existing route, but this one-route fixture does not quantify its growth on a real large module.

## Limits

- Draft bytes count the external YAML package only, not command text, the coverage-audit preparation, the generated review report, or the manually constructed Unit-map apply envelope. They are not total agent-authored bytes.
- Command counts cover preflight and apply only; fixture preparation, context discovery and report handling are excluded. They do not prove a minimum number of model calls or user interactions.
- Review is scripted synthetic authorization, not evidence of human review accuracy. The production review boundary remains intact.
- Local warm-environment timings are retained as observations in the JSON. They are not production latency or a cold/warm performance comparison.
- Actual model decisions, model tokens, user steps and monetary costs are unmeasured and recorded as null. No paid model sessions ran.
- In the original run, `core_base` records the parent HEAD of measured working changes and `source_sha256` pins the actual source, including the contract-diagnostic repair. In the clean reproduction, `core_base` is the exact tested first-increment commit; the separate provenance records its Git tree and clean status before/after the run.
- This is a small baseline and a preservation oracle, not the permanent twelve-scenario benchmark or full acceptance of the roadmap.

## Reproduce

From the experimental Core checkout, using its existing development environment:

```sh
.venv/bin/python workbench/agility-experiment/baseline.py --output /tmp/learningos-agility-baseline.json
```

The output records its source hashes, Python version, package hashes, measured command outputs/times, validation counts and authored files changed. All canonical mutations happen inside temporary fixtures.
