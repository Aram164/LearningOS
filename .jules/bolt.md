## 2025-02-17 - Fast pathing primitive scalar leaves
**Learning:** In highly recursive functions dealing with vast nested structures like YAML parsers/normalizers, calling `isinstance()` for every primitive scalar (str, int, float, bool) adds significant overhead compared to explicit `type() is X` checks.
**Action:** When working on collection/tree traversers that normalize or traverse leaf nodes of primitive data types, write an early return path leveraging explicit `type(value)` comparisons for basic types, retaining `isinstance` selectively only for collections or dates.
