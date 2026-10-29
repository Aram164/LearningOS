# Whole-file allocation during material checksum verification

Observed during Stage 7 of the authorized agility experiment at Core `b723696`: `store/materials/resolution.py::sha256_file` reads each material fully into a Python byte string before hashing. The retained three-sample driver (`workbench/agility-experiment/efficiency.py`) reports median peak allocation 16,777,466 bytes for a synthetic 16 MiB file across nine checksum measurements. This is Python allocation, not process RSS or measured production latency.

Expected: hash material bytes with bounded allocation while preserving the exact digest, read errors, per-build cache and independent reviewed-apply verification. Proposed smallest repair: stream the file into the existing SHA-256 algorithm. Keep stale bytes and added/removed inventory members refusing the apply. Acceptance and before/after evidence are in the Stage 7 plan/outcome; filing follows verification.

Verified repair: all nine after measurements peak at 394,425 Python bytes (median; 97.65% reduction), with identical digests and unchanged inventory checks. Runtime-efficiency tests pass; `stage7-before.json`, `stage7-after.json`, `stage7-comparison.json` and the Stage 7 outcome retain proof. Full hosted acceptance remains Stage 8.

Reported after duplicate search: [Core issue #74](https://github.com/Aram164/LearningOS/issues/74).

Stage 8 follow-up: hosted run 40945395574 fails the historical hash-count audit because its `sha256_bytes` spy no longer observes the streaming path. See `stage8/rest-0.log`, the Stage 8 outcome and the follow-up comment on #74. No code/test repair was made in the acceptance-only task.

Authorized repair follow-up: F13 now observes the shared material read rather than the obsolete byte-helper call. It proves one read across two routes and a fresh read plus invalidation after material changes on a later repository load. All 28 audit/efficiency cases pass; hosted exact-pair acceptance follows separately.
