# Scope fixes and cleanup integration

- [REPORT.md](REPORT.md): final behavior, measured populations, verification
  authority and remaining boundaries.
- [INTEGRATION.md](INTEGRATION.md): branch composition and exact-pair procedure.
- [OUTCOME.md](OUTCOME.md): implementation result and evidence pointers.
- [FIXING-PLAN.md](FIXING-PLAN.md): historical fixing plan.
- [GRANULARITY-274.md](GRANULARITY-274.md): original source-level analysis.

The scripts in `tools/` are reproducible from the published workbench and
from its original sibling workbench location. For example, from Core:

```sh
.venv/bin/python workbench/fix-f01-2026-10-20/tools/check_pins.py
.venv/bin/python workbench/fix-f01-2026-10-20/tools/unit_ownership.py
.venv/bin/python workbench/fix-f01-2026-10-20/tools/granularity.py
```

The historical rebuild and verification scripts are retained as execution
evidence; read their effects before running them. In particular,
`verify_in_place.sh` switches the primary checkout between revisions.

Runtime logs and completion receipts remain in the external session
workbench, `LearningOS/workbench/fix-f01-2026-10-20/snapshots/`, so recording a
successful gate does not create a new revision after the revision it verified.
The original external canvas is separate and is preserved unchanged.
