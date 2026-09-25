# Consumer protocol — blind evaluation runs

You are running one blind evaluation session against a synthetic LearningOS
installation. This page covers the harness only: how to get a world, what to
record, and where to put it. **How to use LearningOS is part of what is being
measured** — nothing here explains it, and you should learn it the way any new
user or agent would, from the product itself.

## 1. Blindness

- The expected answers are sealed in `tests/eval/private/`. Do not open,
  decrypt, search or reason about that directory, and do not look for the key.
- Do not read the scorers under `tests/eval/metrics/` to infer what is
  expected. Reading `tests/eval/tools/` is allowed but counts as harness work,
  not product use.
- Do not read other runs' results under `tests/eval/runs/` before finishing
  your own.
- If you see oracle material by accident, stop, record what you saw in
  `run.json` → `deviations`, and mark the run `"blind": false`.

## 2. Build your world (harness step, not measured)

The world is a complete, separate LearningOS installation with a synthetic
learner's five-month history. Build it **outside** the repository:

```bash
# any Python ≥ 3.12 with PyYAML, jsonschema and pypdf; for example
python3.13 -m venv /tmp/evalenv && /tmp/evalenv/bin/pip install -q pyyaml jsonschema pypdf
/tmp/evalenv/bin/python tests/eval/tools/build_world.py --out ~/los-eval/<run-id>
```

You get:

| Path | What |
|---|---|
| `~/los-eval/<run-id>/LearningOS/repository/` | the installation — its own Git repository. Work **here** as the learner's operator. |
| `~/los-eval/<run-id>/LearningOS/materials/` | the learner's external materials |
| `~/los-eval/<run-id>/eval-drop/` | arrivals — new material the scenarios hand you. Not part of the installation. |
| `~/los-eval/<run-id>/EVAL-WORLD.json` | build record (product revision, world HEAD) — copy it into `run.json` |

To reset to the initial state: build again into a new directory (builds are
deterministic), or `git reset --hard` plus `git clean -fd` inside the world.
Reset only where a scenario says `world: fresh`.

The installation's documentation calls its owner "Aram". In this world the
learner is Noor Haddad; read "Aram" as "the learner". Nothing else about the
product has been changed.

You play two roles at once:

- **Consumer** — the learner's operator, doing what she asks with the
  product's documented interfaces. Reach for implementation files only when
  the normal interface failed or was insufficient, and record every such
  read as friction.
- **Observer** — you record what happened behind the curtain, without
  changing it.

**Approvals.** A scenario's scripted reply is the learner speaking. When
she approves a specific change you showed her, that is a real approval: carry
it out and record it in whatever form the product requires of its operator,
including any approval value the product asks the operator to compute from
the request. That is recording her approval, not bypassing it; acting without
her approval would be bypassing it. If your own agent environment still
refuses such a step, record the refusal (step, message, scenario) as friction
and continue — do not work around the refusal.

## 3. Run plans

Pick the plan your session was given. Run its scenarios in the order listed
in `public/scenarios.yaml`, honouring each scenario's `world:` field.

| Plan | Session role | Scenarios |
|---|---|---|
| B | baseline cartographer (first contact) | S00, S01, S26 |
| N | blind consumer — novice | S00, S01, S02 (Q01–Q12), S04, S06, S10, S14, S15, S26 |
| L | blind consumer — serious learner | S02, S03, S04, S05, S06, S07, S08, S13 |
| R | blind consumer — resuming another user's work | S00, S02, S09, S10, S11, S12, S16, S25, S26 |
| C | connection experiments | S03, S27 |
| X | abuse / failure investigator | S01, S17, S18, S19, S20, S21, S22, S24 |
| P | scale investigator | S23 |
| F | agent-friction investigator | S02 (Q06, Q07, Q13, Q15, Q27), S10, S26 — three times each, fresh world each time |

A scenario you cannot finish is still recorded (`classification` with the
reason). Never skip silently.

## 4. Per-scenario routine

```bash
OBS=tests/eval/tools/observe.py
W=~/los-eval/<run-id>/LearningOS/repository
R=tests/eval/runs/<run-id>
python $OBS snapshot $W --label S04-before --out $R/observations/S04-before.json
#   … do the scenario as the learner's operator …
python $OBS snapshot $W --label S04-after  --out $R/observations/S04-after.json
python $OBS diff $R/observations/S04-before.json $R/observations/S04-after.json \
    --out $R/observations/S04-diff.json
```

Then write `$R/results/S04.json` (schema `public/schemas/scenario-result.schema.json`).
Record, honestly and as you go:

- **Consumer experience**: goal; first action; every command; documents
  consulted; implementation files read; retries; confusions; corrective
  steps; questions you asked the learner; whether implementation knowledge
  became necessary; the outcome the learner would see; tool calls and minutes.
- **Internal behaviour**: request/trace ids (`los operations`), receipts,
  transaction and approval behaviour, projection and derived-state changes,
  unexpected writes, warnings/errors, the git diff stat. The observer diff
  gives most of this.
- **Friction** entries, tagged with the vocabulary in the schema.
- **Classification**: PASS, PASS_WITH_FRICTION, FUNCTIONAL_FAILURE,
  ROBUSTNESS_FAILURE, USABILITY_FAILURE, PERFORMANCE_FAILURE, AMBIGUOUS.
  Do not call something a product defect because you chose a poor approach;
  say which it was when you can tell.

Retrieval answers go to `$R/answers.jsonl`, connection results to
`$R/connections.jsonl`, failures to `$R/failures.jsonl` (schemas in
`public/schemas/`).

## 5. When something fails

1. Preserve the evidence (observer snapshots, command output into
   `$R/evidence/`).
2. Retry once, only if a reasonable user would.
3. Minimize the reproduction if you can.
4. **Do not patch LearningOS**, not even the world's copy, and do not
   bypass approval or safety mechanisms to make a scenario pass.
5. Record it in `failures.jsonl` and continue with the next independent
   scenario.

## 6. Connection results

For probes (`public/connection-probes.yaml`): genuinely try to find useful
prior material; record the top results exactly as produced, best first (at
most 10), each with the reason and the evidence you relied on; say which
product command surfaced each candidate or whether you found it by reading.
Do not go back afterwards to hunt for "the intended" connection.

## 7. Finish

- `$R/run.json` (schema `public/schemas/run.schema.json`), including
  `EVAL-WORLD.json` and any deviations from this protocol.
- `$R/SESSION_REPORT.md` from `public/templates/SESSION_REPORT.md`.
- Validate your records:
  `python tests/eval/tools/check_run.py $R` (schema and id checks only; it
  reads no answers).
- Commit **only** `tests/eval/runs/<run-id>/` to your session branch. Leave
  every other file in the repository unchanged. Do not push to `main`, do not
  force-push.

The Obsidian interface is outside this environment. Do not simulate it; mark
anything that depends on it NOT TESTED.
