# Synthetic authoring campaign

This package is a reproducible, blinded evaluation of LearningOS's ordinary
plan and material work. It replaces the 2026-09-24 study-loop campaign's
scenario set. The historical campaign remains available in Git at `6eb27b9`;
its runs and scores are not current evidence for this package.

The public world is a fictional learner's five-month history plus an owned
query-plan lab. It contains realistic old and current record shapes, exact
local material bytes, linked sources, active learner work and a modern rich
route with a deliberate stage override. `public/scenarios.yaml` contains
requests, procedures and scripted learner replies. Expected outcomes are in
`private/oracle.tar.gz.enc`; the key is held by the campaign owner and is
never given to blind operators.

## Layout

| Path | Purpose |
|---|---|
| `CAMPAIGN.md` | Session order, scoring and repair contract |
| `corpus/` | Public synthetic history and source material |
| `public/` | Scenarios, blind operator brief and result schemas |
| `tools/build_world.py` | Deterministic disposable installation builder |
| `tools/observe.py` | Independent before/after file, receipt and journal observer |
| `tools/check_run.py` | Run record completeness, without reading the oracle |
| `tools/oracle_vault.py` | Seal and open the oracle outside the repository |
| `tools/prepare_native.py` | Build the exact disposable Core/UI vault pair |
| `metrics/score_workflows.py` | Judge-side evidence worksheet and observer flags |
| `private/` | Sealed oracle and its manifest only |

Large run outputs and screenshots belong outside both product repositories,
for example under `/private/tmp/los-eval-runs/`. Decrypted oracle files and the
key belong in the judge-only home directory, away from operator scratch.
The campaign report records evidence paths and SHA-256 digests. `tests/eval/`
does not collect as part of ordinary pytest.

## Build and check

From the Core root, using its `.venv/bin/python`:

```bash
.venv/bin/python tests/eval/selftest.py
.venv/bin/python tests/eval/tools/build_world.py \
  --out /private/tmp/los-write-world-01 --source-rev PRODUCT_SHA
.venv/bin/python tests/eval/tools/check_run.py /private/tmp/los-eval-runs/RUN_ID
```

Use a new output directory for every run. The builder refuses locations in
the tree it runs from and inside any existing Git working tree, refuses a
nonempty output directory, and has no destructive reset flag. A pinned base
revision is in `corpus/world.yaml`. Blind and repair runs build from an exact
commit (`--source-rev SHA`); `WORKTREE` is for harness development and records
the source HEAD, a status digest and a digest of the product files it copied.

Before blind runs, run the self-test, freeze the public scenario revision and
the sealed oracle, and give the consumer only `public/SESSION-BRIEF.md` plus a
plan letter. A consumer never reads `private/`, scorers, other run records,
implementation files during normal use, or the agent's earlier memory. An
accidental leak invalidates blindness and must be recorded.

The package observes product behaviour; it cannot establish educational
effectiveness or real multi-month use. The native UI scenarios require a
disposable vault and a running Obsidian process. Headless UI tests do not
substitute for them.
