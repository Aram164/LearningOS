# Successful read-only Task IR tasks return an unrecognized status and lose useful context

- Workflow: requested P1 architecture assessment through `tools/agent_run.py --task` against a synthetic fixture.
- Tested state: Core `3541789` plus the isolated evidence/checksum repair; read-result projection and CLI exit mapping are unchanged. macOS/Python 3.14.4.
- Expected: successful read-only tasks exit successfully and return bounded useful context with its snapshot.
- Observed: a task containing valid `context.inspect` and `material.find` reports both operation statuses `ok`, top-level status `previewed`, and CLI exit 3. Canonical fingerprint is unchanged. The inspect output contains only the record ID and a null snapshot. `_outputs_from_report` also drops the runtime contract from `session.propose`; that loss is verified by code inspection, not a positive authored-runtime integration run.
- Reproduction: run workbench `assessment_probe.py`; `assessment-integration.log` retains the actual CLI report and exit code.
- Impact: callers treat a successful read-only task as failure, and inspecting context or proposing a session cannot deliver its central result through the public task report.
- Smallest improvement: settle read-only tasks from their actual operation results and align the CLI mapping; carry bounded inspect/session projections and snapshots from the existing runner. Reuse existing full-report references for larger content.
- Acceptance: real CLI tests distinguish successful and refused read-only tasks; a valid authored runtime target produces a snapshot-bound session contract without evidence/mastery claims or canonical changes. No new session entity or requirement store. This remains later P1 acceptance work.
- GitHub: not filed. Automatic approval review rejected publishing the first prepared issue to `Aram164/LearningOS`, stating that the specific contents and destination require explicit approval; the remaining issue submissions were halted. The exact ready-to-file body is this note, without this final status line.
