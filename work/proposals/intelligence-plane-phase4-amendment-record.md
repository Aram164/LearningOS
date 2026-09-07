# Intelligence Plane — Phase 4 amendment record (no tracking, no costs)

Parent proposal: `intelligence-plane-plan.md`. Amends the Phase 4 record
(`intelligence-plane-phase4-record.md`, history — left untouched): the
telemetry append-only log, the static cost function, and the entire
cost-learning pathway are removed. The Agent Task IR survives as a pure
logical plan schema with static dispatch rules.

## What the amendment lands

- `tools/learning_os/semantics/tasks.py`: deleted `TelemetryRecord`,
  `record_telemetry`, `telemetry_to_dict`/`from_dict`,
  `append_telemetry`, `read_telemetry`, `TELEMETRY_RELATIVE`,
  `COST_MODEL_VERSION`, `COST_WEIGHTS`, `step_cost`, and the `_number`
  helper (no remaining callers). `route_step` keeps its policy vetoes
  (unpublished never external; model-only steps refuse deterministic)
  and dispatches the first feasible option — no prices, no tracking.
  `RouterDecision` loses its `cost` field. The IR, the physical
  planner, and all four rewrites are unchanged.
- `tools/learning_os/semantics/__init__.py`: the ten removed names
  leave the import block and `__all__`.
- `tests/test_agent_tasks.py`: telemetry and cost tests deleted; router
  tests re-pinned to first-feasible-wins plus the two veto fixtures.
- `operations/telemetry/` deleted (held only `.gitkeep`; no log data
  ever accumulated). Tree-contract declaration removed; ARCHITECTURE
  tree block regenerated via `tools/tree_contract.py --write`.
- Tasks section in `system/SEMANTIC-CONTRACT.md` rewritten for static
  dispatch; this record.

## Explicit non-changes

- No contract-version bump (still v2), no VOQ additions, no dossier,
  lineage, goal, or envelope change. No gateway change, no new write
  path, no hand-edit of rebuilt views. No critique-point action taken.
- Caller-supplied ordering survives in two places by design:
  `rewrite_cheapest_evidence_first` (pure, caller-priced) and
  first-feasible router dispatch. Neither tracks nor learns.

## Validation observed (2026-09-08 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (161/161) green; task suite green (11 passed); full suite
green (1267 passed, 1 skipped); views regenerated after the final
authored change.
