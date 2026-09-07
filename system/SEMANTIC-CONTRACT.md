# Semantic Contract (Intelligence Plane)

A derived semantic layer above the stable LearningOS core. It answers "what
is worth investigating, what is the cheapest trustworthy way, and what
evidence must a change carry" — while keeping **autonomy in proposal
formation, conservatism in mutation**.

This layer is **interpretation, not stored truth**:

- Predicates are pure functions over existing records and the manifest
  projection. They create no fifth canonical knowledge family and no second
  source of truth.
- Nothing here writes canonical data, touches `generated/`, or calls gateway
  capabilities. Semantic mutation proposals carry evidence and are validated
  before admission; only Aram authorizes them.
- The evaluator lives at `tools/learning_os/semantics/`. The producer
  (`genout.projection`) keeps answering derivations per row; the contract
  owns their meaning so agents read one declared layer.

## Predicates (Phase 0: 1 of ~25)

| Name | Authoritative inputs | Meaning |
|---|---|---|
| `NeedsStudyMap` | unit `status`, module `status`, map coverage | OPERATOR.md rule 6: a unit of an active/enrolled module owes a study map unless complete, archived, paused, or leaving active study |

Phase 1 grows this table toward ~25 predicates (`CurrentScopeAuthority`,
`SupportedCoverage`, `EvidenceComplete`, `SemanticClaimStale`,
`AllowedMutation`, …). Cap: any addition needs a Verified Operator Question
(`tests/fixtures/verified_operator_questions/`) or a goal-detector
motivating it. Deleting this layer reverts cleanly — canonical data is
untouched by every phase.

## Contract version

`CONTRACT_VERSION` in `tools/learning_os/semantics/predicates.py` is
currently **1**. Lineage sidecars (Phase 2) cite it so "what goes stale if
the contract changes" stays answerable. A bump must be a deliberate diff
with updated predicates, fixtures, and lineage.

## Status

Phase 0 (spike): one predicate end-to-end, registry plus `evaluate()` entry
point proven by `tests/test_semantic_contract.py`. Full vision and work
plan: `work/proposals/intelligence-plane-plan.md`; Phase 0 path decisions:
`work/proposals/intelligence-plane-phase0-record.md`.
