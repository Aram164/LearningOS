# Runner loses the plan report on nonfinite step output

Affected workflow: executing an agent plan containing malformed numeric JSON output.

Verified on the uncommitted repaired runner (SHA-256 3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d), based on dad2d8f, before this follow-up. Python 3.14.4 accepts NaN/Infinity and overflowed 1e999 as floats when parsing step stdout. The summary encoder rejects them with ValueError; run_plan let that exception escape, losing the per-step report. The new regression cases failed against the retained before-source.

Expected: a typed INVALID_STEP_OUTPUT row, retained earlier results, and subsequent execution governed by on_error. Repair rejects nonfinite numbers during parsing and catches summary serialization failures at the step boundary. Four numeric cases cover NaN, Infinity, -Infinity and 1e999. No live learner data was written.

Local evidence: LearningOS/workbench/agent-operator-readiness-2026-10-26/followup/red.log; tests/test_agent_run.py. Publication/CI results will be linked after the repair commit.

Issue: https://github.com/Aram164/LearningOS/issues/56
