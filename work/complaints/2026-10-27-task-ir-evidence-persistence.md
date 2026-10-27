# Task IR P1 evidence persistence bypassed the shared atomic writer

- Workflow: continuing the P1 experiment and running its Core verification.
- Tested state: Core `3541789` on `codex/task-ir-p1-experiment`, paired UI `3c9a5f664c147790c490fae0a256e7764b4b9157`; macOS, Python 3.14.4. Only synthetic fixtures were mutated.
- Expected: private run evidence outside the data root uses the existing atomic persistence primitive, without canonical transaction receipts or a new lint exemption.
- Observed: `tools/learning_os/app/task_ir.py::_save_evidence` called `write_text` and `replace`; `tests/test_arch_writes.py::test_static_lint_matches_baseline` rejected both. The old predictable temporary path could also follow a symlink. The baseline combined command reported 2 failed, 44 passed, 2 xfailed; the other failure was the separately reported transcript hash.
- Smallest repair: reuse `store.transactions.atomic_write_bytes`, already used by `app.agent_reporting`, and reject redirected evidence/check destinations before use. The repair adds no ratchet or effect-classification exemption.
- Verification: `tests/test_task_ir.py` plus `tests/test_arch_writes.py` passed 39 cases, including six preview/apply symlink cases, a directory redirected into the data root, a failed checkpoint publication that prevented submission and retained the previous preview, and compatibility with previously persisted relative check-record paths. The existing file/directory synchronization test also passed. This does not establish protection against concurrent hostile directory replacement or complete P1 recovery acceptance.
- Evidence: `../repair-baseline.log`, `../repair-focused-final.log`, `../repair-durability.log` in the experiment workbench; reproduction commands are retained in `../REPAIR-PLAN.md`.
- GitHub: https://github.com/Aram164/LearningOS/issues/65
