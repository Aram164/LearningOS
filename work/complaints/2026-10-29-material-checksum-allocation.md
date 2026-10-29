# Whole-file allocation during material checksum verification

Observed during Stage 7 of the authorized agility experiment at Core `b723696`: `store/materials/resolution.py::sha256_file` reads each material fully into a Python byte string before hashing. The retained three-sample driver (`workbench/agility-experiment/efficiency.py`) reports median peak allocation 16,777,466 bytes for a synthetic 16 MiB file across nine checksum measurements. This is Python allocation, not process RSS or measured production latency.

Expected: hash material bytes with bounded allocation while preserving the exact digest, read errors, per-build cache and independent reviewed-apply verification. Proposed smallest repair: stream the file into the existing SHA-256 algorithm. Keep stale bytes and added/removed inventory members refusing the apply. Acceptance and before/after evidence are in the Stage 7 plan/outcome; filing follows verification.

Verified repair: all nine after measurements peak at 394,425 Python bytes (median; 97.65% reduction), with identical digests and unchanged inventory checks. Runtime-efficiency tests pass; `stage7-before.json`, `stage7-after.json`, `stage7-comparison.json` and the Stage 7 outcome retain proof. Full hosted acceptance remains Stage 8.

Reported after duplicate search: [Core issue #74](https://github.com/Aram164/LearningOS/issues/74).
