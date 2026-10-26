# Runner silently drops requested summary fields that are absent upstream

Affected workflow: selecting bounded fields from an operator read.

Verified on the uncommitted repaired runner (SHA-256 3c11a770c4a89c2d73b7d8947e6d11f842f30de01088fc1e9e519cb19a4bd44d), based on dad2d8f. summarize({"a": 1}, fields=["nope.deep"]) returned {}, so an operator could not distinguish a missing field from an empty selected result.

Expected: explicitly name every missing requested path, distinguish an existing null, and retain this information under truncation. Repair emits reserved _missing_fields metadata inside the UTF-8 budget; a budget unable to hold that metadata is explicitly refused. Regression cases fail against the retained before-source and cover ordinary selection, null, truncation and insufficient metadata budget.

No live learner data was written. Local evidence: LearningOS/workbench/agent-operator-readiness-2026-10-26/followup/red.log; tests/test_agent_run.py. Publication/CI results will be linked after the repair commit.

Issue: https://github.com/Aram164/LearningOS/issues/57
