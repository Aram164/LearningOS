# Task IR evidence hardlinks can redirect preview writes into canonical files

- Workflow: independent P1 acceptance review of private evidence persistence.
- Tested state: Core `d707aaa` and the acceptance candidate, macOS/Python 3.14.4, disposable material fixtures only.
- Expected: preview cannot alter canonical files through its evidence/check output paths and creates no canonical receipt.
- Observed: the separate reviewer hard-linked `sources/sources.yaml` to the predictable Task IR check-record path. Preview followed the regular file, returned `needs_review`, changed canonical bytes/fingerprint, and produced zero receipts. The atomic sibling temporary path also accepts a hardlink unless checked before its write. Symlink-only checks do not detect these aliases.
- Smallest repair: refuse existing evidence/check/temp regular files whose link count differs from one before invoking any writer. Retain the existing shared atomic persistence primitive and external evidence directory.
- Acceptance evidence: `tests/test_task_ir.py::test_hard_linked_output_cannot_overwrite_canonical_data` covers check and temporary destinations and asserts unchanged canonical bytes/fingerprint and no receipts. Full Task IR candidate tests and final hosted pair results are recorded in the workbench acceptance report. This does not claim protection against hostile concurrent directory replacement.
- GitHub: https://github.com/Aram164/LearningOS/issues/65#issuecomment-6455314967
