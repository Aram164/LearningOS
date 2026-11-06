# Captured-world pin covers data/ only; observations.json and meta.json are trusted unpinned (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: development gates — world capture/compare tooling.

Observation (verified, file:line): `tools/compare_world.py:99` (`_verify_data`)
recomputes only the `data/` tree pin. `tools/capture_world.py:150` writes
`observations.json` (clock, HEAD, commit dates) and `meta.json` (dirty-status hash,
dirty `system/` paths) beside it. `materials.json` *is* re-verified against the live
tree at step 3; `observations.json` and `meta.json` are trusted as captured.

Inference: tampering with `observations.json` silently changes the environment under
which a recorded identity claim is computed; `meta.json` likewise vouches for
dirty-state that is never re-checked.

Safety retained: the `data/` bytes and the materials tree are pinned and fail closed
on drift (`tests/test_arch_world.py` exercises data/ and materials tampering).

Smallest improvement: extend `_verify_data` to pin the two sidecars the same way as
`data/`, and add sidecar-tamper cases to `tests/test_arch_world.py`. Safeguards to
retain: fail-closed behavior on any mismatch; the pin must cover the exact bytes
captured, not a re-render.

Filing: GitHub issue not filed — `gh` CLI is unavailable in this environment (blocked
by tooling availability, 2026-11-06). Proposed issue title: "compare_world verifies
only data/: observations.json and meta.json are trusted unpinned".
