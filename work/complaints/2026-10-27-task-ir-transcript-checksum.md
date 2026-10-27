# P1 strict type-checking addition invalidated an anchored transcript checksum

- Workflow: Core procedure verification after the Task IR P1 implementation.
- Tested state: Core `3541789`; isolated experiment, macOS/Python 3.14.4.
- Expected: the anchored-copy transcript records the exact current `pyproject.toml` bytes while preserving byte-for-byte fixture copying and checksum checking.
- Observed: `ea00749` added `tools/learning_os/app/task_ir.py` to the strict mypy file list. `system/procedures/add-or-evaluate-a-source.md:191` retained the prior hash, so `tests/test_procedures.py::test_every_transcript_passes` failed. Measured current hash: `sha256:3ceabba96c45022e7f726ab432e918da7769554aac8b2f757f0db9033955cef0`.
- Smallest repair: retain strict mypy coverage and update only the transcript's expected pyproject hash. Do not weaken `tests/procedure_helpers/los-anchored-copy` or add wildcard output.
- Acceptance: the exact hash matches `shasum -a 256 pyproject.toml`, and the complete procedure suite passes with its existing audit witnesses and expected failures. Final counts are retained in the workbench report.
- Evidence: `../repair-baseline.log`, `../repair-procedures.log`, and `../REPAIR-REPORT.md` in the experiment workbench.
- GitHub: not filed. Automatic approval review rejected publishing the first prepared issue to `Aram164/LearningOS`, stating that the specific contents and destination require explicit approval; the remaining issue submissions were halted. The exact ready-to-file body is this note, without this final status line.
