# semantics

## Purpose

Interpret evidence through predicates, policy, lineage, dossiers and proposals.

## Owned paths

- `tools/learning_os/derive/semantics/*`

## Entry points

- `tools/learning_os/derive/semantics/predicates.py::evaluate`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `contracts`, `derived-store`, `domain`, `learner-derivations`, `loading`, `materials`, `session-ledger`, `transactions`.

Used by: `ai-delivery`, `learner-derivations`, `operation-handlers`, `operation-pipeline`, `plan-gate`, `projection`, `validation`.
<!-- system-map:end -->

## Invariants

- Interpretation must never become stored learner truth or write authority. Pinning: `tests/test_semantic_contract.py`.

The evaluator registry is in `derive/semantics/predicates.py`; `policy.py`
returns normalized decisions, `lineage.py` owns claim freshness, `goals.py`
and `scan.py` own the proposal lifecycle, and `claim_status.py` interprets
exact occurrences. `claim_audits.py` owns the seeded pool/sample helpers.
`tasks.py` handles task IR and `dossiers.py` materializes bounded context.
`changes.py` is library preflight, not a wrapper over every live command.
Verified-question fixtures keep public facts separate from reference keys;
held-out material must never leak into an illustrated example.

## Pinning tests

- `tests/test_semantic_contract.py`
- `tests/test_semantic_lineage.py`
- `tests/test_claim_status_audits.py`
- `tests/test_agent_tasks.py`
- `tests/test_context_dossiers.py`
- `tests/test_proof_carrying_change.py`
- `tests/test_verified_operator_questions.py`
- `tests/test_model_question_scoring.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
