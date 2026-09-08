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

## Policy queries (Phase 1.5)

Predicates own judgments; `tools/learning_os/semantics/policy.py` owns the
query surface agents program against: one rule name in, one structured
`PolicyDecision` out — a normalized verdict (`allow`, `deny`, `defer`,
`needs-review`) plus the reasons behind it. `defer` is not `deny`: a
deferred critique point may return with authorization, while a denied
mutation must not be retried unchanged. Unknown rules fail closed;
malformed queries deny rather than raise. Seven rules (mutation scope,
shelving approval, critique gating, mastery, note review, write path,
workspace scope), each mapped from one predicate with its authority
attached. Rule composition into a change envelope belongs to Phase 6.

## Lineage (Phase 2, retraction in Phase 10)

A predicate answers; lineage remembers the answer's basis. Each high-value
claim — route `covers` edges, scope-authority judgments, dossier freshness,
and nothing else — carries what it read (artifact revisions, source hashes,
evidence locators), the contract version judged under, its judge and
reviewer, and a status: `supported`, `stale`, `contested`, or `withdrawn`.
Refresh delegates staleness to `ClaimStale`, so the system holds one
definition of stale; contest needs a reviewer, never a recompute; the
impact query reports exactly the claims a revision or hash move touches.
Retraction tracks assumptions between derived claims: invalidating one
withdraws everything that assumed it, recursively, in the sidecar only —
`retraction_impact` answers the blast radius before `withdraw` applies it,
withdrawn claims return only through fresh judgment, and pre-Phase-10
records carry no assumptions so they cascade only to themselves. Ledger
load validates assumption integrity: dangling references and cycles
refuse (LINEAGE-ASSUMPTION-MISSING / -CYCLE) before real data accumulates.

Storage is a receipt-adjacent sidecar (`operations/transactions/lineage.yaml`,
schema beside the other contracts), never a canonical edit and never a
projection — lineage must survive a rebuild. Backfill is lazy: records are
created when a claim is judged, never bulk-migrated. Since Phase B,
prospective claims are bound at admission: a `module.plan.import` that
creates, repairs, or removes a covers edge carries per-claim evidence or
refuses before apply, and the gateway persists the admitted records
(`admitted_by` request binding, `supersedes` repair chain) in the same
transaction as the canonical mutation. Readers:
`tools/learning_os/semantics/lineage.py`, proven by
`tests/test_semantic_lineage.py`.

For prospective covers claims, stored revisions describe post-apply
validity: only artifacts incremented by that transaction advance. Declared
reads are checked against pre-apply state; the original guarded revisions
remain in the package and receipt. A deletion-only import also carries
evidence and withdraws the removed claim and its explicit dependents.
The gateway's `judged_by` channel/approval label records admission context;
it is not proof of an independent semantic review. The evidence trail must
identify the actual review and its limits.

## Candidate goals (Phase 3)

The engine surfaces what is worth investigating and never mutates meaning
itself. Five read-only detectors — covering routes gone stale, sources
changed under claims, repeated question classes with no VOQ, inspections
with no dossier, systematic reviewer corrections — emit goals with
rationale and evidence, thresholded and deduplicated. Each goal then walks
`detected → formulated → eligible → proposed → authorized → planned →
executing → verified → closed` (plus `deferred/rejected/stale/superseded`),
one step at a time; only Aram authorizes. The queue lives under
`work/proposals/goals/`, one file per goal. Readers:
`tools/learning_os/semantics/goals.py`, proven by
`tests/test_goal_proposals.py`.

## Agent tasks (Phase 4, amended: no tracking, no costs)

A Task IR states what a task needs — eight logical step kinds from
knowledge reads to governed mutation — with no model bound to any step.
Every step carries an id, its dependencies, and a fixed effect class
(pure | judgment | mutation): the tuple order itself must satisfy every
edge, mutations are barriers no rewrite may move past, judgments never
deduplicate, and the four rewrites (predicate pushdown, dossier dedup,
cheapest evidence first, late materialization) cheapen plans only when
they prove the partial order survives — otherwise they refuse. Coverage
comparison is a semantic-support judgment that runs on a model;
acquiring evidence retrieves identified records and may run
deterministically, with interpretation left to the judgment step that
consumes it. Dedup collapses only exact-duplicate reads of clearly
identified records within one mutation-free segment — never across a
mutation, and never for acquisitions whose content identity is unproved.
Static dispatch applies policy vetoes — unpublished material never leaves
the repository, model-only steps refuse deterministic executors — and the
first feasible executor wins. No prices, no telemetry, no learning:
nothing here tracks what tasks cost or how models perform. Readers:
`tools/learning_os/semantics/tasks.py`, proven by
`tests/test_agent_tasks.py`.

## Context dossiers (Phase 5)

Agents rebuild the same context per task; dossiers materialize it once.
The builder hashes every dependency separately — knowledge map, source
map, routes, evidence content digests, both contract versions — and
addresses the bundle as `context://<unit-id>/semantic-dossier@<digest>`:
same inputs always hit the same key, any move changes exactly its hash
plus the digest, and a cache file whose content fails its hashes is
refused, never served. Evidence is content-addressed: callers resolve
each locator to the digest behind it (materials manifest checksums), so
changed bytes invalidate even when the URI never moves.
Freshness delegates to `DossierFresh`. Dossiers live under
`generated/dossiers/`, covered by the existing no-hand-edit path — no
canonical file may reference them, and the builder plus the store take
explicit paths and never walk the repository. Readers:
`tools/learning_os/semantics/dossiers.py`, proven by
`tests/test_context_dossiers.py`.

## Proof-carrying change (Phase 6, hardened: claims, not verdicts)

Integration status: the generic `admit` and `verify_postconditions` APIs are
library machinery, not a universal wrapper around all live commands.
The live module-plan import uses the bounded Phase B preflight and atomic
lineage path described above. The envelope guarantees below apply when
that API is invoked; they do not establish coverage of every gateway path.

Every semantic mutation arrives with its proof: intent, scope, read set
with revisions, claim ids, bare evidence references, the write set with
its capability, the snapshot read, postconditions bound to harness
observations, and a validation plan. The envelope carries no approval,
no lineage verdicts, no digests, no predicate inputs — those are
structurally unstatable in it. Deterministic admission runs before any
gateway apply against a trusted context the agent never touches:
session authorization, the capability contract (declared scopes ground
every write scope), the live lineage ledger, harness-resolved evidence,
current revisions, and the current snapshot. After the gateway applies,
postconditions evaluate against live observations the harness supplies —
a promised RepoClean passes only when the actual repository validates
clean. Anything else returns conflict, replan, or deny, never an
overwrite.
Conflicting writes cannot both succeed: the second read loses its
snapshot race by construction. The gateway still applies; the envelope
is preflight, and the snapshot guard stays the final word. Readers:
`tools/learning_os/semantics/changes.py`, proven by
`tests/test_proof_carrying_change.py`.

## Intelligence scan

OBSERVE → INTERPRET → PROPOSE, then Aram decides queue entry: `los
intelligence-scan` reads the current world, runs the Phase-3 detectors
over what it finds, prints candidate investigations, and exits. No
daemon, no background process, no telemetry database, no automatic
writes. v1 observes only what the repository already records — changed
files in a stateless recency window joined to knowledge nodes and
source definitions, lineage staleness against the revision ledger, and
derived study-map obligations. Critique points are deliberately
excluded (an open point is not a work item); question, inspection, and
correction counts have no observable source and those detectors stay
caller-fed; dossier freshness has no live-key registry. Readers:
`tools/learning_os/semantics/scan.py`, proven by
`tests/test_intelligence_scan.py`.

The scan also checks declared `file:` evidence against current in-repository
bytes and `manifest:` evidence against the current registered checksum.
Missing, unreadable, escaping, or unknown evidence references cannot be
verified and therefore stale the claim. Registered checksums do not detect
changed external material bytes until the materials inventory is refreshed;
remote URLs without a local digest dependency still need a fresh source
review. Scanning reports candidates; it never rewrites the lineage ledger.

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
the VOQ suite. Phase 1.5 adds the policy-query envelope; Phase 2 adds
lineage above. Full vision and work plan:
`work/proposals/intelligence-plane-plan.md`; phase records:
`work/proposals/intelligence-plane-phase0-record.md`,
`work/proposals/intelligence-plane-phase1-record.md`.
