## 2025-02-06 - Optimized _normalize() with fast paths
**Learning:** The `_normalize()` function in `tools/learning_os/loading/yamlio.py` traverses deep YAML structures to handle ISO date auto-parsing normalization. This results in heavy overhead, particularly due to using `isinstance` for common types like strings or numbers.
**Action:** Adding exact type matches (`type(value) is str`) and checking primitive types explicitly as a fast-path before using `isinstance()` or attempting slow paths like importing `datetime` reduces processing overhead during load operations.
