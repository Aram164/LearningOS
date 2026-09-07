# Intelligence Plane — Phase 4 record (agent Task IR + telemetry + router)

Parent proposal: `intelligence-plane-plan.md`. Prior phases: Phase 0
(record), Phase 1 (23 predicates, contract v2, 20 VOQs), Phase 1.5
(policy-query envelope), Phase 2 (lineage sidecar), Phase 3 (goal engine).

## What Phase 4 lands

- `tools/learning_os/semantics/tasks.py`: Task IR (8 logical step kinds,
  validated, no model binding), physical planner (deterministic vs model,
  per-step table), four pure rewrites (pushdown, dossier dedup,
  cheapest-evidence-first, late materialization), static cost function
  with documented placeholder weights, policy-veto router (unpublished
  never external; model-only steps refuse deterministic), and the
  append-only JSONL telemetry log with validated rows carrying the cost
  model version.
- Telemetry home `operations/telemetry/log.jsonl`, declared in
  `tree-contract.yaml` (same precedent as the proposals queue) with the
  ARCHITECTURE block regenerated through the sanctioned projector.
  Git-tracked measurements; rotation policy arrives with the learning.
- `tests/test_agent_tasks.py`: IR validation, model-free planning,
  rewrite meaning-preservation, router fixtures incl. the proposal's own
  unpublished-material veto example, cost formula and cache benefit,
  telemetry append/read-back plus corrupt-log refusal.
- Tasks section in `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- No adaptive or RL routing: weights are static-first by design;
  promotion waits on significant telemetry.
- No model adapters or prompt libraries: executors stay abstract
  (`deterministic` vs `model` plus caller-named options); models remain
  interchangeable behind the IR.
- No contract-version bump (still v2), no VOQ additions, no dossier
  builder (Phase 5), no change envelope (Phase 6).
- No canonical migration, no gateway change, no new write path, no
  hand-edit of rebuilt views. No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (159/159) green; task suite green; full suite green; views
regenerated after the final authored change.
