# warning_baseline writes the baseline non-atomically (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: development gates — warning baseline.

Observation (verified): `tools/warning_baseline.py` `write_baseline` uses a single
non-atomic `write_text`. A crash mid-write truncates or corrupts
`operations/validation-warning-baseline.yaml`, which then refuses to load (exit 2,
fail-closed) and needs hand repair.

Inference: low probability, high annoyance; the failure is loud, not silent.

Safety retained: a corrupted baseline fails closed instead of silently passing.

Smallest improvement: write to a temp file in the same directory and `os.replace` it.
Safeguards to retain: unchanged; this only removes the corruption window.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "write_baseline is not atomic; a crash mid-write
corrupts the baseline".
