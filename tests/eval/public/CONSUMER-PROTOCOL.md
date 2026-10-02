# Blind operator protocol

You are the operator for Noor Haddad in a complete, disposable LearningOS
installation. Follow only the scenario ids assigned to your plan. Learn the
product from its shipped operator documentation and public CLI/UI, just as an
ordinary new operator would.

## Boundary

- Do not read or search `tests/eval/private/`, its encrypted content, the
  scorers, another run, earlier agent memory or campaign discussions. If any
  answer-key detail enters your context, record it and mark `blind: false`.
- Do not inspect implementation files for an ordinary task. If public
  interfaces force you to do so, record each file and why; it is friction.
- Do not patch Core or UI, alter the real learner checkout/vault, bypass a
  gateway, or invent an approval. Investigator scenarios may damage only a
  disposable world created for that case.
- A scripted reply is Noor speaking. Show the exact change before recording
  its approval in the form the product requires. If no reply covers a question,
  Noor says, "I do not know; choose the safest reversible path." Record it.
- `tests/eval/corpus/` is the world generator's input, not Noor's installation:
  do not read it. Everything Noor has is in the built world. A scenario's
  `inputs:` entry names the corpus source of a world file; use the world's
  copy (for example `<world>/LearningOS/materials/source-noor-lazy-lab/lab-notes.md`)
  and cite world paths. `eval-drop/` holds material that has not reached Noor
  yet; read it only when a scenario names it.

## World

From the Core checkout, build a fresh world outside `semestercontext`:

```bash
.venv/bin/python tests/eval/tools/build_world.py \
  --out /private/tmp/los-eval-world-RUN_ID --source-rev PRODUCT_REV
```

`PRODUCT_REV` is the exact product commit your kickoff names. Build with
validation (never `--no-validate`), and record the product revision and the
synthetic world HEAD separately. `WORKTREE` is for harness development only.

Run the product with the harness Python from the world root:
`/path/to/harness/.venv/bin/python tools/los.py …`. Where product output or
documentation prints `los …`, that means `python tools/los.py …` in the world
root. Never run a bare `los`; an installed entry point can be bound to a
different checkout. The harness Python already has every dependency; if you
choose to follow the product's `make setup` in a world, do it only in a world
that has no `.venv` of its own yet, and record it.

`EVAL-WORLD.json` names the synthetic repository, materials and arrivals.
Use a new directory for every `world: fresh`; keep the prior state only for
`world: continue` within your plan. The builder has no reset flag. Work in
the built `LearningOS/repository/`, using its own code and documentation.
Its product docs sometimes name Aram; in this world the learner is Noor.

## Plans

| Plan | Scenarios |
|---|---|
| B | S00–S01 |
| A | S01–S08 |
| E | S09–S14 |
| X | S15–S22 (or its halves X1: S15–S17 and X2: S18–S22, when two sessions share it) |
| U | S23–S25 |
| P | S26 |
| R | S27 |
| C, V, O | clean room, verifier, ad hoc: an explicitly declared subset |

The U plan uses a disposable vault made from its synthetic world, installs
the matching UI there, and drives actual Obsidian. Open Diagnostics and record
its live identity. Follow `public/NATIVE-UI.md`. Do not use the real vault. The P plan uses separate scale
worlds on one host; list every world in `run.json` `worlds`. C (clean room),
V (verifier) and O (ad hoc) declare their assigned subset explicitly in
`run.json`.

## Per scenario

Use `tools/observe.py snapshot` before and after, then `diff`, writing all
three JSON files under the run directory's `observations/`. When a scenario
uses several fresh worlds or copies, observe each one and record it as an
entry of the result's `cases` (label, world path and HEAD, before, after,
diff); the top-level before/after/diff stay the primary case. Save command
stdout/stderr in `evidence/` whenever it proves a finding. Record one
`results/Sxx.json` per assigned scenario, even when blocked or NOT_RUN, using
`public/schemas/scenario-result.schema.json`. Record failures in
`failures.jsonl` and reference their ids in the result. A reasonable user
retry is allowed once; record the first failure and retry separately.

The result includes the first read, all commands and documents, any
implementation-file reads, approvals, retries, questions, time, learner-facing
outcome, request ids, receipts, warning/error messages and before/after
observer paths. Write down the exact review report and draft digests for plan
and analysis operations. Save every envelope you submit, byte for byte, as
`envelopes/<Sxx>-<n>.json`, and every no-write review or preflight output
under `evidence/`; list them in the result's `internal.envelope_files` and
`internal.review_reports`. A receipted write without a saved envelope (for
example one admitted by the UI) needs an `internal.envelope_note` saying why.
When several worlds are involved, say which world each envelope was sealed in. For source questions, cite material and note ids or
paths, and distinguish product-found targets from your own file reading.

After S07, the conductor starts S08 in a fresh operator context on the same
world. The S08 operator receives the world path, S07's saved preflight report,
submitted envelope and idempotency key, but not the apply response or S07's
conversation. The original response remains in judge evidence. Treat its
outcome as unknown until operations, receipt and fresh projection prove it.
The conductor combines the two context segments into the A-plan run record.

Write `run.json` with plan, scenario ids, exact product and world revisions,
environment, blind status and deviations, plus `SESSION_REPORT.md`. Check the
run with:

```bash
.venv/bin/python tests/eval/tools/check_run.py /private/tmp/los-eval-runs/RUN_ID
```

The checker validates completeness and record shape; it does not score
correctness. Do not call an incomplete or inaccessible native app check a
pass. Do not change a scenario or the oracle after runs start without a
dated harness-change entry in `CAMPAIGN.md` and a fresh affected run.
