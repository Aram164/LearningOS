## 2025-02-12 - Optimized `_normalize` function in YAML loader
**Learning:** In highly recursive functions like YAML normalization (`_normalize` in `yamlio.py`), exact type matching for primitive types (`type(value) is str`, etc.) avoids the overhead of `isinstance` and `datetime` imports for every leaf node in a large YAML document. However, `isinstance` must be retained for dictionaries and lists to handle subclasses properly.
**Action:** Always check primitive types exactly before doing expensive collections parsing or inline imports in highly recursive structures.
