
## 2026-09-21 — second fan-out bug, practice dashboard (transcribed notebook page, filed by the operator)

Revenue per region doubled for "North" last week — impossible.

Walked back step by step with row counts:
- orders (week): 48,210 rows ✓
- ⋈ customers: 48,210 ✓
- ⋈ regions on region_code: 96,420 ✗ ← here

regions table had two rows for code "N" (old name + new name after the
rename). Every North order matched twice. Dedup the dimension table and add a
uniqueness check on the dim key before joining.

Second time a join fan-out has bitten me.
