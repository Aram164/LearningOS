# Task IR read operations silently accept undeclared fields

- Workflow: requested architectural assessment of Task IR P1 before acceptance.
- Tested state: Core `3541789` plus the isolated evidence/checksum repair; `_operation` read branches are unchanged. Python 3.14.4, no learner writes.
- Expected: every operation has a closed input contract and refuses undeclared fields before execution.
- Observed: `_operation` in `tools/learning_os/app/task_ir.py` returns from all three read branches before its final extra-field check. `parse_spec` accepts `surprise: true` on `context.inspect`, `material.find`, and `session.propose`. It retains the field in the normalized digest while execution ignores it.
- Reproduction: call `parse_spec` with schema version 1, a request ID, and one valid read operation carrying `surprise: true`. Bounded output in workbench `assessment-parser.log` records all three acceptances.
- Impact: a misspelled constraint can be silently ignored; this is a compile-contract failure, not evidence of a gateway authorization bypass.
- Smallest improvement: apply the existing per-operation allowed-field check before every return. Add real-interface refusal cases for each read operation without creating another capability catalogue.
- Acceptance: all three read operations reject unknown fields before dispatch, while valid existing specifications still compile deterministically. No repair for this gap is included in the immediate verification increment.
- GitHub: not filed. Automatic approval review rejected publishing the first prepared issue to `Aram164/LearningOS`, stating that the specific contents and destination require explicit approval; the remaining issue submissions were halted. The exact ready-to-file body is this note, without this final status line.
