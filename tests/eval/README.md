# LearningOS evaluation package

A reproducible, blinded evaluation of LearningOS. It holds a synthetic
learner's five-month history (the **world**), realistic scenarios, retrieval
questions and connection probes, harness tools that watch what the product
does internally, scorers, and a sealed ground-truth **oracle**. Fresh sessions
use the product without ever seeing the oracle; a separate judge scores them
afterwards.

The campaign plan (which session does what, with kickoff prompts) is in
[`CAMPAIGN.md`](CAMPAIGN.md).

## Public and private — the boundary

| | Who may read it | Where |
|---|---|---|
| **PUBLIC** | everyone, including blind consumer sessions | `corpus/`, `public/`, `tools/`, `runs/` (own run only until finished) |
| **HARNESS** | everyone; reading it teaches nothing about the answers, but blind consumers should not study `metrics/` | `metrics/`, `selftest.py`, `leak-adjudications.json` |
| **PRIVATE** | the judge and repair sessions only | `private/oracle.tar.gz.enc` — encrypted; key held by the campaign owner, never committed |

The oracle holds the relation judgments (MUST_CONNECT / USEFUL_CONNECT /
AMBIGUOUS / MUST_NOT_CONNECT for 351 target pairs over 50 probes), the
expected answers to 36 questions, the expected behaviour for 28 scenarios, and
the author's notes for the judge. Plaintext never enters the repository:
`tools/oracle_vault.py open` refuses to extract inside it, and `selftest.py`
fails if anything but the sealed files appears under `private/`.

### How a blind consumer session stays blind

1. It is started with the consumer prompt and pointed at
   [`public/CONSUMER-PROTOCOL.md`](public/CONSUMER-PROTOCOL.md). Nothing else
   in this package is required reading.
2. It never receives `LOS_EVAL_ORACLE_KEY`. Without it the sealed file is
   noise (AES-256-CBC, PBKDF2 600k iterations).
3. The world it works in is built from `corpus/` only. The builder refuses any
   header field that is not public, and the self-test (with the key) greps
   every built world and every commit touching `tests/eval/` for the oracle's
   own sentences.
4. Public files state goals, never expected outcomes. Scenario files contain
   the learner's words and scripted replies, not what a correct operator does.

## Layout

```
tests/eval/
├── README.md                this file
├── CAMPAIGN.md              the session plan and kickoff prompts
├── selftest.py              package self-tests (not part of make test)
├── leak-adjudications.json  leak-scan matches ruled independent wording (hashes only)
├── corpus/                  PUBLIC — the synthetic learner's material
│   ├── world.yaml           persona, timeline, pinned product revision
│   ├── registries.yaml      concepts, relations, sources, programs
│   ├── curriculum.yaml      modules, units, study maps, resume pointer
│   ├── notes/*.md           116 durable notes (bundle format: tools/bundle.py)
│   ├── stage-notes.md       stage working notes
│   ├── workspaces.md        workspaces (with earlier revisions)
│   ├── coordination.md      coordination record (with an earlier revision)
│   ├── inbox.md, garden.md  captures and Garden seeds
│   ├── projects.yaml        two projects
│   ├── arrivals.md          30 items handed to consumers during scenarios
│   └── materials/           external slide transcripts
├── public/                  PUBLIC — what consumers are asked to do
│   ├── SESSION-BRIEF.md     standing instructions for blind consumer chats
│   ├── CONSUMER-PROTOCOL.md
│   ├── scenarios.yaml       28 scenarios (S00–S27)
│   ├── questions.yaml       36 retrieval questions (Q01–Q36)
│   ├── connection-probes.yaml  20 canon + 30 arrival probes
│   ├── schemas/             run, scenario-result, answer, connection, failure
│   └── templates/           SESSION_REPORT.md, result.example.json
├── tools/                   harness (builds and observes; never scores)
│   ├── build_world.py       deterministic world builder
│   ├── bundle.py            corpus bundle reader
│   ├── observe.py           before/after snapshots and diffs of a world
│   ├── interrupt_probe.py   SIGKILL a write at chosen delays, classify the state
│   ├── scale_bench.py       timings at scale, with spread
│   ├── check_run.py         schema/id checks for a run directory
│   └── oracle_vault.py      seal / open / check the oracle
├── metrics/                 scorers (need the oracle to produce numbers)
│   ├── score_connections.py Recall@5/10, P@5, judged P@5, must-not rate, MRR, …
│   ├── score_retrieval.py   evidence hit, answer points, forbidden-claim flags
│   ├── friction.py          friction aggregated across runs
│   └── determinism.py       rebuild-after-delete and two-build comparisons
├── private/                 PRIVATE — sealed oracle + manifest
└── runs/                    one directory per session run
```

Why `tests/eval/` and not a top-level `eval/`: the repository's tree contract
(`system/contracts/tree-contract.yaml`) makes an undeclared top-level
directory a validation error, and declaring one would change a binding
contract. `tests/` has an unchecked interior, and nothing here matches
`test_*.py`, so the product's test suite does not collect it.

## Build a world

```bash
.venv/bin/python tests/eval/tools/build_world.py --out ~/los-eval/w1
.venv/bin/python tests/eval/tools/build_world.py --out ~/los-eval/w1 --source-rev WORKTREE   # patched product
.venv/bin/python tests/eval/tools/build_world.py --out ~/los-eval/big --scale 2000           # + filler notes
```

Any interpreter with PyYAML, jsonschema and pypdf works; the build ends by
running the world's own validator and view generator and fails if either
fails. Same corpus + product revision + scale + seed ⇒ same world HEAD.

## Recorded revisions

| What | Value |
|---|---|
| Product revision installed by default | `200a36185fd5c693b4464ce0bdff4be5b89ce584` (`corpus/world.yaml`) |
| World HEAD at that revision, scale 0 | `13ad2fcaa0e478afddba6451e29376ca00f0bc8e` since harness change H1 (see CAMPAIGN.md; the self-test prints it) |
| Timeline | 2026-04-06 → 2026-09-18, 133 commits, fixed author and dates |

## Self-tests

```bash
.venv/bin/python tests/eval/selftest.py --quick                 # public checks, scorers, lint
.venv/bin/python tests/eval/selftest.py                         # + two world builds, observer, determinism
LOS_EVAL_ORACLE_KEY=… .venv/bin/python tests/eval/selftest.py   # + oracle decrypts, ids resolve, leak scan
```

## For the judge (after the consumer runs)

```bash
export LOS_EVAL_ORACLE_KEY=…      # from the campaign owner
python tests/eval/tools/oracle_vault.py open --out ~/los-eval/oracle
python tests/eval/metrics/score_connections.py --oracle ~/los-eval/oracle/oracle --results tests/eval/runs/<run> --world <world repo>
python tests/eval/metrics/score_retrieval.py   --oracle ~/los-eval/oracle/oracle --results tests/eval/runs/<run> --world <world repo>
python tests/eval/metrics/friction.py tests/eval/runs/<run-a> tests/eval/runs/<run-b> …
```

Each scorer writes metrics JSON and a worksheet for human/LLM grading into the
run directory. Heuristic columns are labelled `HEURISTIC`.
