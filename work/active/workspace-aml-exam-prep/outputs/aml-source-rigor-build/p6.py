"""Re-project every assembler-owned AML lecture map through exact targets."""

EDITS = {}
REBUILD_UNITS = {f"unit-aml-l{number:02d}" for number in range(1, 12)}
