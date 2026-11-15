# AI task entry points

For code, architecture, contracts, tests or documentation changes, start with
[`system/DEVELOPER.md`](system/DEVELOPER.md). For operating learner state, use
the operator route below. Audience selects reading order, never an exemption
from relevant binding rules.

Read and obey [`system/OPERATOR.md`](system/OPERATOR.md). Discover capabilities
with `.venv/bin/python tools/los.py capabilities --compact --json`; start with the entry
read OPERATOR.md names for the task — a named route or stage starts with its
focused `plan-edit-context` read, an open question with `bootstrap --brief`.
Read one capability, command or task with `.venv/bin/python tools/los.py
capabilities NAME --json`; NAME may be a capability id, a CLI command, or a task id.
Do not recursively scan the repository or
sibling code repositories such as `Stratum/` to infer application state.
When operating learner records, run the named entry read first. Do not
precede it with directory listings, `--help` probes, or whole-document
reads unless that entry fails or the task crosses the scope it declares.
Code, architecture, contract, test and documentation changes still start
at `system/DEVELOPER.md` and inspect code as that route requires.

No agent has a standing role here: Aram assigns planning, reviewing and
implementing per task. Workspace-wide guidance for plans and reviews is in
`AGENTS.md` at the `semestercontext/` root.

## Sandboxed study mode

When running inside a study launch (`tools/study_launch.py` / `LOS_GATE_SOCK` active):

- **Search reading memory before opening PDFs:** Run `material-search` or
  `material-context` first. When calling `material-span ... --extract`, ask for
  narrow targeted pages (`--pages "pdf p. N"`): extracts fail or truncate above
  `6000` characters (`~2-4` dense PDF pages, max `20` pages). Pass
  `--omit-covered-text` when re-checking an already-covered span.
- **Settle open reading entries (max `4`):** Every uncovered span opens a
  `rd-...` debt. Interactive Claude `Stop` hooks prompt up to twice
  (`STOP_ASKS = 2`) before marking open entries overdue without blocking turns
  indefinitely; the gateway enforces settlement at the next uncovered study read
  whenever open debt reaches `4` or an overdue/adoptable entry exists, via
  `material-card-settle ENTRY --card '...'` or `--dismiss irrelevant --reason '...'`.
  In `--card` JSON, `paraphrase` is `20-800` chars, every kind in `kinds` must
  have at least one matching `pointers[].kind` and every pointer's `kind` must
  appear in `kinds` (matched sets), each `page` must lie in the entry's range,
  and each `label` is `1-160` chars.
- **Scratch & writes:** Write scratch, `--check-out`, and `--out` files only
  under `$LOS_SCRATCH_DIR`. Scratch resets across launches by default unless
  `--persist-scratch` or `--scratch-dir` initializes a dedicated,
  `.learningos-scratch.json`-marked, single-session directory outside
  `LearningOS/` (pre-existing unrelated or other-session directories are
  refused; remove retained scratch manually when finished). On a resumed
  confirmation turn without the prior check file, re-run `--check-out` /
  `--check` into `$LOS_SCRATCH_DIR` and inspect the new record before
  submitting with `--guards-from`; replacement/import/revise capabilities
  refuse `--submit` without `--guards-from`.
