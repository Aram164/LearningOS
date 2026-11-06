# Procedure transcripts assume harness state a fresh agent cannot satisfy (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: procedure transcripts (start-here, capture-routing, build-write-envelope,
agent-plans).

Observation (verified, texts): every transcript opens with
`eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)"` before anything
sets `LOS_REPO` (the header says it "comes from the `LOS_REPO` environment variable the
test sets"), and uses bare `los` while start-here's macro sanctions
`.venv/bin/python tools/los.py` and `.venv/bin/los`. The `make setup` fallback appears
once, in start-here's operating rules, not where `.venv/bin/los` is first used. A
literal manual run fails on line one.

Inference: the transcripts present as agent-readable procedures but are
harness-executed (`tests/test_procedures.py`); nothing says "do not execute by hand
without harness setup", so a diligent agent fails confusingly.

Safety retained: the transcripts are machine-verified, which is stronger than prose;
the gap is presentation only.

Smallest improvement: one header line per transcript ("harness-executed via
tests/test_procedures.py; hand execution requires tests/procedure_helpers setup") or
set `LOS_REPO` in the header itself. Safeguards to retain: transcript content and
heading anchors unchanged (task-scope validates them).

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "procedure transcripts reference $LOS_REPO before it
exists; bare los is not the sanctioned form".
