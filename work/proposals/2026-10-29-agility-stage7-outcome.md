# Stage 7 — measured remaining costs

Stage 7 completes the bounded optimization pass after the Stage 6 review
corrections (Core `b723696`, UI `8e82f8a`). The two production changes are
streamed material checksums in `store/materials/resolution.py` and reuse of the
already-loaded repository in `app/handlers/materials.py::_unit_audit`. Existing
per-build cache lifetime, live-material observation and independent reviewed
apply checks remain intact. Data contract 62 and manifest contract 16 are unchanged.

## Measured result

Three disposable-fixture samples per pass, each with three standalone hashes
of a synthetic 16 MiB material:

| Observation | Before | After |
|---|---:|---:|
| Median peak Python checksum allocation | 16,777,466 bytes | 394,425 bytes |
| Brief-context repository loads | 2 | 1 |
| Cold / warm status validations | 1 / 0 | 1 / 0 |
| Explicit validation runs per invocation | 1 | 1 |
| Structured-inventory enumerations, preflight / apply | 3 / 4 | 3 / 4 |
| Material opens, inventory preflight / apply | 19 / 25 | 19 / 25 |

Checksum allocation falls 97.65%. This measures Python allocation, not process
RSS. Instrumented wall times remain in the raw evidence; no production latency,
CPU speedup, token or monetary saving is established. OS caches were not flushed.

Full, brief and stage-focused context stdout is byte-identical across all six
before/after samples (8,246 / 5,795 / 1,284 bytes respectively). Cold/warm status
stdout is identical within each fixture. Every no-write preflight preserves its
canonical fingerprint; every reviewed inventory apply changes only the expected
source-map file and leaves exactly one receipt. The repeated Stage 5 proportional
benchmark matches all five structural results and draft hashes: stage moves
remain 184 authored bytes at 2/10/50 stages, Unit addition 2,943, append 768.

Raw before/after data, source hashes, comparison, reproduction driver and focused
check logs live under `workbench/agility-experiment/stage7-*`; see the workbench
README and `stage7-provenance.json`. Before-source hashes were checked against
`b723696`; after hashes pin the two changed production files, without pretending
the measured working tree was already a clean commit. Instrumentation and clock
files sit outside the disposable fixture's observed validation perimeter.

## Verification

Both new regression failures were reproduced before the repair: an 8 MiB hash
allocated 8,388,858 bytes, and brief audit repository reuse was absent. Afterward,
27 runtime-efficiency tests and 174 owning inventory, revision, material-context,
observation, synthesis, cache and agent tests pass. One unrelated full procedure
entry test was excluded from this focused selection. New checks cover exact
binary/chunk-boundary digests, bounded allocation, resolved-path cache hits,
new-build material changes, failed-read retry, unchanged audit payload and fresh
observation of changed/deleted material despite repository reuse. Existing
inventory drift, membership and reviewed-apply refusals still pass.

Ruff, maintained mypy (19 files), reachability/architecture (288 modules),
system-map and all three import contracts pass. The import checker's local cache
was moved outside the governed tree before final validation. Validation reports
zero errors and 970 visible warnings; the managed baseline remains exactly 964
warnings across 32 signatures. The seven protected primary-checkout file hashes
remain unchanged. Stage 7 has no UI source change; the Stage 6 review's full UI
check remains the owning UI evidence at `8e82f8a`.

## Acceptance boundary

This is focused experimental acceptance. Full hosted exact-pair/artifact
acceptance remains Stage 8. Intermediate publication uses the already documented
`[skip ci]` bootstrap path and creates no verified-pair stamp. The Stage 6 idle
screen's midnight redraw limitation remains documented in its outcome. No actual
learner state, production installation, migration, merge, paid trial or subagent
was used. Stop after publishing Stage 7; Stage 8 has not started.

The measured inefficiencies are reported in [Core #74](https://github.com/Aram164/LearningOS/issues/74) and [Core #75](https://github.com/Aram164/LearningOS/issues/75), after searching for duplicates. Their retained complaint notes link the evidence and experimental repair.
