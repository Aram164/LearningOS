# Semantic Contract (Intelligence Plane)

A derived semantic layer above the stable LearningOS core. It answers "what
is worth investigating, what is the cheapest trustworthy way, and what
evidence must a change carry" — while keeping **autonomy in proposal
formation, conservatism in mutation**.

This layer is **interpretation, not stored truth**:

- Predicates are pure functions over existing records and the manifest
  projection. They create no fifth canonical knowledge family and no second
  source of truth.
- Nothing here writes canonical data, touches rebuilt views, or calls
  gateway capabilities. Semantic mutation proposals carry evidence and are
  validated before admission; only Aram authorizes them.
- The evaluator lives at `tools/learning_os/semantics/`. The producer
  (`genout.projection`) keeps answering derivations per row; the contract
  owns their meaning so agents read one declared layer.

## Predicates (Phase 1: 23)

Each predicate names its authoritative inputs — the only facts it may read —
and its fallback rule for incomplete or unknown input. The fallback direction
is always fail-closed: an unknown input never produces a confident
permission. Cap: any addition needs a Verified Operator Question or a
goal-detector motivating it.

| Name | Authoritative inputs | Authority | Fallback |
|---|---|---|---|
| `NeedsStudyMap` | unit status, module status, map coverage | OPERATOR.md rule 6 | unresolvable module accuses nobody |
| `ScopeAuthority` | fact kind + owning ids | OPERATOR.md boundaries 4–5 | unknown kind or ids → `"unknown"` |
| `AllowedMutation` | capability, target path, declared scopes | capabilities.yaml | malformed or empty → deny |
| `ShelvingApproval` | applied items, approved items | OPERATOR.md rule 9 | empty apply refused |
| `CritiquePointActionable` | point status, in-session authorization | CRITIQUE-POINTS rules 2–4 | unknown status defers |
| `MasteryDeclared` | statement kind | OPERATOR.md rule 10 | unknown kind is suspicion |
| `NoteChangeNeedsReview` | change kind | OPERATOR.md rule 2 | unknown kind requires review |
| `EvidenceComplete` | evidence entries | note.schema.json | malformed input incomplete |
| `ClaimStale` | contract versions, read/current revisions | revisions ledger | unchecked reads are stale |
| `SourceComplete` | selection state, locator, deferral reason | OPERATOR.md rule 14 | unknown state or blank reason fails |
| `RouteValid` | route/unit/source/locator | route_identity.py | any malformed field invalidates |
| `RouteEvaluated` | scope | module-source-map.schema.json | unevaluated or unknown → false |
| `StudyMapGrounded` | template version, resource/menu pairs | unit workflow | malformed rows unground |
| `PlanTemplateCurrent` | template version | OPERATOR.md rule 15 | only integer 1 passes |
| `RepoClean` | error count, new/grown warnings | OPERATOR.md "clean" | any count above zero fails |
| `SnapshotFresh` | expected/current snapshot | OPERATOR.md rule 12 | empty snapshots never fresh |
| `CanonicalWritePath` | channel | OPERATOR.md rule 16 | unknown channels are hand edits |
| `WorkspaceMayCoordinate` | claim kind | OPERATOR.md rule 6 | unknown kinds do not coordinate |
| `QuarantineExcluded` | path | OPERATOR.md rule 4 | malformed paths treated excluded |
| `ExternalSibling` | path | OPERATOR.md rule 3 | empty paths treated external |
| `RelationMayApply` | type, endpoints, inferred flag | ADR-015; OPERATOR.md rule 2 | inferred or malformed never applies |
| `DossierFresh` | cached/current hashes | Phase 5 dossier contract | empty maps never fresh |
| `AttemptConsistent` | attempt/sitting termins | OPERATOR.md rule 5 | malformed lists inconsistent |

Staleness is not completeness: artifacts a claim never read cannot stale
it, and an unreadable read set is stale rather than trusted. Deleting this
layer reverts cleanly — canonical data is untouched by every phase.

## Verified Operator Questions

~20 question/procedure/expected-property triples under
`tests/fixtures/verified_operator_questions/` (15 examples, 5 held out),
run by `tests/test_verified_operator_questions.py`. Examples prove the
predicates answer; held-out questions score as eval and are never
illustrated — a leaked held-out id fails the suite.

## Contract version

`CONTRACT_VERSION` in `tools/learning_os/semantics/predicates.py` is
currently **2**. Lineage sidecars (Phase 2) cite it so "what goes stale if
the contract changes" stays answerable. A bump must be a deliberate diff
with updated predicates, fixtures, and lineage.

## Status

Phase 1 (contract + VOQs): 23 predicates end-to-end with registry plus
`evaluate()` entry point, proven by `tests/test_semantic_contract.py` and
the VOQ suite. Full vision and work plan:
`work/proposals/intelligence-plane-plan.md`; phase records:
`work/proposals/intelligence-plane-phase0-record.md`,
`work/proposals/intelligence-plane-phase1-record.md`.
