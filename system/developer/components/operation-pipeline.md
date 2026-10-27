# operation-pipeline

## Purpose

Admit, lock, dispatch and settle one operation through the shared application boundary.

## Owned paths

- `tools/learning_os/app/__init__.py`
- `tools/learning_os/app/pipeline.py`
- `tools/learning_os/app/registry.py`
- `tools/learning_os/app/admission.py`
- `tools/learning_os/app/claim_admission.py`
- `tools/learning_os/app/commit.py`
- `tools/learning_os/app/context.py`
- `tools/learning_os/app/lock.py`
- `tools/learning_os/app/outcomes.py`
- `tools/learning_os/app/encoders.py`
- `tools/learning_os/app/render.py`
- `tools/learning_os/app/check.py`
- `tools/learning_os/app/proposal.py`
- `tools/learning_os/app/gateway.py`
- `tools/learning_os/app/validation.py`
- `tools/learning_os/app/validation_service.py`
- `tools/learning_os/app/projection.py`
- `tools/learning_os/app/ranking.py`
- `tools/learning_os/app/session.py`
- `tools/learning_os/app/agent_plans.py`
- `tools/learning_os/app/agent_presentation.py`
- `tools/learning_os/app/agent_reporting.py`
- `tools/learning_os/app/task_ir.py`
- `tools/learning_os/app/projection_readiness.py`
- `tools/learning_os/app/read_session.py`

## Entry points

- `tools/learning_os/app/pipeline.py::run_cli`
- `tools/learning_os/app/pipeline.py::run_gateway`
- `tools/learning_os/app/commit.py::commit_proposal`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `backup`, `contracts`, `derived-store`, `diagnostics`, `domain`, `evidence`, `learner-derivations`, `legacy-archive`, `loading`, `materials`, `operation-handlers`, `projection`, `semantics`, `session-ledger`, `transactions`, `validation`.

Used by: `ai-delivery`, `cli-adapter`, `operation-handlers`, `plan-gate`.
<!-- system-map:end -->

## Invariants

- Never dispatch an unadmitted write or bypass snapshot/replay checks. Pinning: `tests/test_ops_pipeline.py`.
- Declare `OperationEffects` per operation independently of invocation kind. Pinning: `tests/test_agent_run.py`.
  Only `READ` permits the runner to schedule a read. `DERIVED_WRITE` includes
  optional report, cache, staging and export output; `CANONICAL_WRITE` includes
  canonical records and Git/session mutations. The default is `UNKNOWN`, a
  write barrier. This scheduling metadata grants no write authority.

Admission lives in `system/contracts/capabilities.yaml`; `app/admission.py` constants
`GESTURE_ALLOWLIST` and `UI_REVIEWED_ALLOWLIST` enforce it. The UI mirrors
its permitted gesture set and checks parity in its own contract check.

### Experimental Task IR P1

`task_ir.py` compiles four closed operations into the existing runner/gateway.
Read results retain bounded content, snapshot pins and expansion references; route binding requires complete discovery.
Private evidence retains original check/envelope bytes with digests and root/session/request bindings through the shared atomic writer.
Apply submits copied original bytes; interrupted outcomes use gateway replay-only and the strict committed-evidence verifier. Missing proof stays uncertain;
preview never replaces in-flight evidence, and interrupted requests are never
resealed. Legacy previews lacking original bytes require a new reviewed request ID.
Operator assertions do not authenticate human review. There is no new journal, session entity, approval protocol or general graph composition.
Pinning: `tests/test_task_ir.py`.

## Pinning tests

- `tests/test_ops_pipeline.py`
- `tests/test_observation_gesture.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
