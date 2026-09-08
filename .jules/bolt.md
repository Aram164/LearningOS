## 2025-02-18 - Optimize YAML normalizer
**Learning:** In highly recursive AST-like tree visits in Python (like normalizing parsed YAML), using `isinstance` combined with dynamic imports inside the function adds significant overhead per node. Most nodes are simple primitives (str, int, bool, dict, list) rather than special objects (like datetime).
**Action:** Always prefer exact type matching (`type(value) is X`) for fast-paths of primitive types and standard collections in recursive structures before falling back to `isinstance` for custom types or inheritance checks.
