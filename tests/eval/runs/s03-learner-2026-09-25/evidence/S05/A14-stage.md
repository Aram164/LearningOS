
## 2026-09-24 — plans 2 and 3 (stage note draft)

Plan 2 (group-by after join, then filter on the aggregate):
- the filter on total > 100 cannot move below the group-by (it needs the sum);
- the filter on year = 2025 did move below the join into the orders scan;
- "PROJECT 4/31 COLUMNS" on orders — only columns used anywhere survive.

Plan 3 (same subquery used twice):
- "CACHE" node: the shared subplan is computed once and reused.

Rule I'm seeing: a filter can move below an operator only if it depends on
nothing that operator creates.
