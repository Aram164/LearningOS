# [P2] Summary serialization exceeds its declared byte budget

Affected workflow: experimental agent operator plans.

Calling `summarize({"x": "a" * 10000}, fields=["x"], max_bytes=120)` returned 162 UTF-8 bytes; replacing the text with `ä` returned 276 bytes. The implementation slices characters, then adds a JSON wrapper and escaping after the limit check. The current test checks JSON parsing and `_truncated_bytes >= 0`; it never checks the encoded length. The `clusters` path also bypasses the summarizer entirely.

Expected: bound the final serialized UTF-8 output, including metadata and escaping, or explicitly reject a budget too small for a minimal envelope. Acceptance: assert the actual encoded length for ASCII, multibyte characters, quotes/backslashes, selected fields, and cluster output. Account for report overhead separately when claiming total agent-visible bytes.

Environment and limits: review of the uncommitted `experiment/agent-operator-readiness-20261026` worktree on base `dad2d8f1f0843742b6b003db8228333650fc6038`, 2026-10-26. Tool SHA-256 `e5421c0a91b06c23bb21ff63e1542fbdd5c38463c31099847640d7cda1de2720`. The nine supplied focused tests pass; the write reproductions used disposable synthetic fixtures. No live learner write, source repair, commit, push, merge or full local gate was performed. Retained local evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/review/reproduce.py` and `review/results.json`; affected code `tools/agent_run.py:192`.

Issue: https://github.com/Aram164/LearningOS/issues/54

## Local repair verified — 2026-10-26

The byte limit now applies to the final UTF-8 JSON encoding, including escaping and truncation metadata. Cluster output also obeys the limit while retaining counts and an expansion route, or returns an explicit budget error. Tests cover ASCII, multibyte/emoji text, escapes, selected fields, invalid budgets, and cluster omission counts. The benchmark measures full stdout/stderr bytes separately from step-output fields.

38 runner checks and 102 workflow/architecture checks passed. Full hosted CI remains pending. Repair evidence: `LearningOS/workbench/agent-operator-readiness-2026-10-26/fixes/REPORT.md`; source SHA-256 `3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d`. Outcome issue: https://github.com/Aram164/LearningOS/issues/54
