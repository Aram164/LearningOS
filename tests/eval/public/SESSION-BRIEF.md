# Session brief — blind evaluation runs

You are participating in a blinded product evaluation of LearningOS. Your
kickoff message names your **run plan**, **run id** and **role**. The
harness mechanics are in [`CONSUMER-PROTOCOL.md`](CONSUMER-PROTOCOL.md):
read it next, and nothing else under `tests/eval/` except what it points to.

## Your stance

Act as a technically capable consumer meeting this LearningOS installation
for the first time. You are **not** a LearningOS maintainer. The question is
whether the system lets an unfamiliar user or agent do realistic learning and
knowledge-management work — safely, recoverably, without undocumented
implementation knowledge.

## Blindness

A sealed evaluation oracle lives in `tests/eval/private/`. Do not open,
decrypt or search for it, and do not look for a key. Do not read
`tests/eval/metrics/`, other runs under `tests/eval/runs/`, or other session
branches. If you see oracle material by accident, record it and mark the run
`"blind": false`.

## On a shared machine

Several evaluation chats may run at once on one computer, beside the owner's
own files and other agent sessions.

- Work only in your world (`~/los-eval/<run-id>*`), your session worktree and
  your scratchpad. Under `~/los-eval/`, open nothing but your own run's
  directories.
- Do not read or write your assistant's persistent memory (for Claude Code,
  `~/.claude/projects/*/memory/`). Do not read other sessions' transcripts
  (`~/.claude/projects/`, `~/.codex/`) or other chats' scratchpads. A memory
  index may already be in your context: do not open what it points to, and
  record in `run.json` → `deviations` anything it made you do differently.
- Your shell may start each command outside your world. Give every git
  command that changes state an explicit path (`git -C <path>`). Write files
  with a file-writing tool or a quoted heredoc (`<<'EOF'`), so that backticks
  or `$(…)` in your text are never executed.
- If anything outside your world changes by your hand, stop and tell the
  owner at once.
- Timing runs (plan P): record `uptime` before and after every measurement
  series, so the load of other work on the machine is visible next to your
  numbers.

## Two roles at once

- **Consumer** — do each scenario the way a real user or user-facing agent
  would. Prefer documented interfaces. Read implementation files only when
  the normal interface failed or was insufficient, and record every such read
  as friction. Do not silently repair anything.
- **Observer** — record what happened behind the curtain (traces, receipts,
  manifests, derived-state changes, git state, unexpected writes) with
  `tools/observe.py`, without changing behaviour.

## For every scenario, record

Before-state; goal; first action; every command; documentation consulted;
retries; confusion; corrective steps; questions asked to the learner; whether
implementation knowledge became necessary; the outcome the learner would see;
request/trace ids; transaction and approval behaviour; projection and
derived-state changes; unexpected writes; warnings/errors; the final diff.
Classify: PASS, PASS_WITH_FRICTION, FUNCTIONAL_FAILURE, ROBUSTNESS_FAILURE,
USABILITY_FAILURE, PERFORMANCE_FAILURE, AMBIGUOUS. Do not call something a
LearningOS defect because you chose a poor approach; say which it was when you
can tell.

## Adversarial principle

Do not adapt your expectations to what LearningOS happens to do. A confusing
documented workflow is evidence. When something fails: preserve the evidence,
retry once only if a reasonable user would, minimize the reproduction, do
**not** patch it, and continue with the remaining independent scenarios.

## Connection discovery

For probes and new material, genuinely try to find useful prior material.
Record the top results exactly as produced (best first, at most 10), each with
its reason, its evidence, and whether a product command or your own reading
surfaced it. Do not go back afterwards to hunt for "the intended" connection.

## Agent friction

Watch for unnecessary exploration, repeated context reconstruction, unclear
terminology, hidden prerequisites, commands that need implementation
knowledge, unstable output formats, reading generated files by hand, redundant
calls, guessing which operation is safe, and errors that do not say how to
recover. Do not propose new frameworks to remove small inconveniences.

## Robustness probes (plans X and P)

Their scenarios deliberately damage, interrupt, overload or corrupt **your
evaluation world** — that is the probe, and it is allowed there. Never touch
the repository you were started in, except to write your run directory.

## Safety

No force-push; no push to `main`; do not modify the sealed oracle; do not
weaken or delete tests; do not bypass LearningOS's approval or safety
mechanisms to make a scenario pass. Leave every file outside
`tests/eval/runs/<run-id>/` unchanged.

## End of run

`run.json`, `results/<Sxx>.json` for every scenario of your plan, and — where
your plan produces them — `answers.jsonl`, `connections.jsonl`,
`failures.jsonl`, `observations/`, `evidence/`, plus `SESSION_REPORT.md`, all
under `tests/eval/runs/<run-id>/`. Check with `tools/check_run.py`, commit
only that directory, push your session branch, and report its name.

Your goal is not to praise or criticize LearningOS. It is to produce
trustworthy evidence of what an unfamiliar consumer actually experiences.
