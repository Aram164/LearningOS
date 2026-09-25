# Session report — s00-baseline-2026-09-24

- Plan / role: B — baseline cartographer (first contact)
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 9a85f012bea38e7db8bd76edf6251136f9aa15e1 · Eval revision: 5ccd52aded5b3efb76fc3b62c8eded4f0b087639
- Started / finished: 2026-09-24T23:28Z / 2026-09-25T00:04Z

## What I set out to do

I ran plan B's three scenarios as a new operator meeting this installation for the first time: orient and report state and deadlines (S00), set up the tooling and check repository health without touching notes (S01), and do three ordinary requests while counting friction (S26). I used only the documentation the product points to (the CLAUDE.md adapter, `system/OPERATOR.md`, README, CLI help and capability definitions) and read implementation only when those failed. Each implementation read is recorded. S00 and S01 ran in one world; S26 ran in a second, identical fresh build.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S00 | PASS_WITH_FRICTION | A correct five-line state and deadline answer in 9 tool calls with zero writes. The interpreter had to be set up first, CLAUDE.md and OPERATOR.md give different "what next" entries, and the resume pointer disagrees with the study map's current stage without any flag. |
| S01 | ROBUSTNESS_FAILURE | Tooling works, the validator reports 0 errors, the warning baseline passes and no note changed. But `make setup` could not recover from its own first failure, and the documented `make test-fast` wrote a phantom "needs attention" request into the learner's `los operations`. It also failed 34 tests, many because it reads the product author's repository files. |
| S26 | USABILITY_FAILURE | All three goals were done. The one-line inbox capture took 13 calls and a read of `tools/learning_os/contracts/gateway.py`: the README command is refused, and the envelope's intent hash and request guard are documented nowhere. |

## Failures (see failures.jsonl)

- **F-s00-baseline-01 (S01, robustness): `make setup` does not recover from a failed first run.**
  - Expected: README says `make setup` is the per-clone setup and that `make setup PYTHON=python3.14` selects an interpreter.
  - What happened: the default `python3` here is 3.11, and the first run failed at `pip install -e` ("requires a different Python"). `make setup PYTHON=python3.12` then failed identically: `python3.12 -m venv .venv` over the existing venv leaves `.venv/bin/python` pointing to 3.11, even though `pyvenv.cfg` now says 3.12.3.
  - Recovery: only `rm -rf .venv` worked, and no document mentions it.
  - Minimal reproduction: `make setup` → `make setup PYTHON=python3.12` (both exit 2).
  - Could be my mistake: partly. README says 3.12+ is required, so running the override first would have avoided the first failure. The non-recovery is the defect.
- **F-s00-baseline-02 (S01, robustness): `make test-fast` writes into the learner's repository.**
  - Expected: README calls it "synthetic fixtures, no checked-in repository load".
  - What happened: it created `operations/diagnostics/traces.jsonl` (135 spans) in the learner's repository. `los operations` now lists `req-bad-payload` (`unknown.write`, AMBIGUOUS, reconcile-exact-request, needs_attention). Timestamps place the write inside the test run.
  - Could be my mistake: learners may not be meant to run the suite. Also, the agent host's ambient `TRACEPARENT` may have merged several test requests into one "operation" (45 attempts). I did not bisect which test wrote it.
- **F-s00-baseline-03 (S01, functional): `make test-fast` fails in a learner installation.**
  - What happened: 34 of 2,278 tests failed in 11 min 54 s. At least 17 raise FileNotFoundError or KeyError on files and scenario ids that exist only in the author's repository (`work/active/workspace-m2-exam-prep/...`, `operations/transactions/transaction-20260920-*.yaml`). One re-run of two test files reproduced it deterministically (21 failed, 12 passed).
  - Could be my mistake: about 6 failures inject faults with `chmod`, which cannot stop uid 0, so they are environmental. I did not compare against the product's own clone.
- **F-s00-baseline-04 (S26, usability): the documented inbox capture needs implementation knowledge.**
  - Expected: README lists `python tools/los.py capture --text "…"` as the inbox path.
  - What happened: it exits 2 ("canonical writes must use GatewayEnvelopeV2"). WORKFLOWS §25a step 4 and AI-ACTIONS name `intent_sha256(envelope)` but do not define it. `capabilities capture.create --json` does not mention that `expected_revisions` must contain `capture-request:<idempotency_key>`.
  - What worked: an envelope built with the product's own `intent_sha256` / `request_artifact_id` committed on the first attempt.
  - Could be my mistake: the Obsidian UI may build this envelope for humans, but OPERATOR.md, the agent entry point, names no helper.

## Friction that cost the most

1. **S01 setup and test run: 26 minutes wall, 22 tool calls.** Setup took 3 attempts plus a Makefile read (4 extra calls). The test target billed as "quick feedback" took 11 min 54 s, outlived the 10-minute foreground limit, and had to be backgrounded. My own wait loops then cost about 10 more minutes, which is my error, not the product's.
2. **S26 goal 2, one inbox line: 13 tool calls, against 1 and 3 for the other two goals.** That included 7 documents, 3 help screens and 1 implementation read, plus importing product internals to compute the approval hash.
3. **S00 before the first read: 3 of 9 calls on interpreter setup.** Python 3.11 was refused with an actionable hint. On top of that, the brief carries no as-of date or days-until, so answering "due soon" needed a second command (`resume`) or manual date arithmetic.

Smaller items:
- Search is literal: "caching" finds 1 note, "cache" finds 10.
- `warning_baseline` prints "0 warning(s)" beside a validator that reports 2–3, without saying they are exempt.
- CLAUDE.md hard rule 6 and §7 ("freshly rebuilt coordination view", `generated/domain-atlas.md`) disagree with OPERATOR.md (`bootstrap --brief` + `inspect coordination`) about the "what next" entry.

## What the product made easy

- **Read commands:** `bootstrap --brief`, `resume`, `inspect coordination`, batched `inspect`, `search` and `related` each answer in about 1.5 s. They return JSON with a `snapshot_id` and write nothing, and `generated/` stayed empty across S00.
- **`resume`:** one readable screen that includes day counts and dated, sourced recorded aims.
- **Errors that name the fix:** the Python-version ImportError gives two concrete fixes. The bare-write refusal names the exact capability command, where the schema is, and the doc section.
- **Validation:** fast (about 0.5 s) and clear. `make status` gives a good one-screen summary.
- **Writes, once a correct envelope exists:** it committed on the first attempt with a complete receipt (snapshot before/after, artifact revisions, write hashes, approval subject). `los operations` then showed a clean COMMITTED record.

## Behind the curtain

- **Reads vs. writes:** reads project in memory and never materialise `generated/`. The first gateway write (S26 capture) published the whole view set plus a `generated/derived-state/` cache: 138 files, 984 KB, at 00:00:29.
- **Uncommitted writes:** a gateway write leaves the inbox file, the receipt, `operations/transactions/idempotency.yaml` and `revisions.yaml` untracked until a session-end commit. HEAD does not move.
- **Trace ids:** LearningOS adopts an inherited `TRACEPARENT`. Every request in this agent session carried trace id `b3374ba2d506605f0e90a7e68fc300f5`, and `operation_id` equals `trace_id`, so separate requests from one agent session may collapse into one "operation". This is probably behind S01's 45-attempt phantom operation.
- **Resume pointer:** it names `stage-os-l02-02-proportional-share`, labelled `confirmed`, while `study-map-os-l02.current_stage` is `stage-os-l02-01-classic-policies` and stage 02 is `pending`. The StatLearn workspace note likewise says "stage 2" while the L05 map has stage 1 active. No command reports this.
- **Observer diffs:**
  - S00 changed nothing.
  - S01 changed no canonical files; it added derived views, the diagnostics trace and ignored tooling by-products, and installed Git hooks outside the worktree.
  - S26 added 4 canonical/operations files as expected, and no flags were raised.

## Uncertainties

- Whether the stage disagreement is intended world state or a projection issue. I did not read implementation to find out.
- Which test wrote the phantom trace, and whether it happens without an ambient `TRACEPARENT` or as a non-root user.
- How many of the 34 test failures also happen in the product's own clone.
- Whether the product meant agents to build envelopes by importing `learning_os.contracts.gateway`. No document says so.
- Minute counts are small because the agent works quickly. Tool-call counts are the better friction measure.

## Deviations from the protocol

- **S26 world:** built fresh in a second directory rather than by resetting the first world. Same world HEAD and the same canonical digest.
- **S26 interpreter:** reused the machine venv `~/losvenv` from S00, so S26 counts exclude setup.
- **Agent context:** the product's CLAUDE.md was already in context before the session began, auto-loaded from the host repository, whose copy is byte-identical.
- **`model` field:** omitted from run.json, per the session's policy on repository artifacts.
- **Wait loops:** my own wait loops were killed during S01. This was a harness mistake with no effect on the world.

## NOT TESTED

- The Obsidian UI, including whether it builds capture envelopes for a human.
- `make system-check` and the pre-push gate, which need the sibling `obsidian-ui` checkout; it is absent here.
- `los session-end` and committing the S26 capture, because the learner did not ask for a commit.
- `make test` (full suite) and `make stress`.
