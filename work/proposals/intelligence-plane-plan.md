## Goal

Add a thin **Intelligence Plane** above the stable LearningOS core that answers "what is worth investigating, what is the cheapest trustworthy way, and what evidence must a change carry" — while keeping **autonomy in proposal formation, conservatism in mutation**.

## Success Criteria

- An agent can answer "what does this route/source/unit mean and is it supported?" from one declared semantic layer instead of re-deriving it from scattered YAML/rules.
- Model understanding of LearningOS is measurable via a conformance suite with held-out questions.
- The system surfaces candidate goals ("7 routes need revalidation", "this question class needs a contract addition") without performing any semantic mutation itself.
- Repeated multi-model tasks get cheaper through reuse (telemetry-informed routing + cached dossiers), with no change to canonical families, gateway authority, or snapshot/receipt guarantees.
- Every semantic mutation proposal carries machine-checkable evidence and is independently validated before admission.

## Context And Current Facts

- Entry point is `system/OPERATOR.md` (declared in `system/contracts/normative-corpus.yaml`); every `system/*.md` must be classified there or `make check` fails.
- Canonical knowledge stays limited to Notes, Concepts, Sources, Concept Relations; curriculum/operations/materials are separate planes.
- Writes go only through action-specific gateway capabilities (`module.plan.import`, `unit.map.import`, `route.patch`, etc.) under manifest-snapshot guards with append-only receipts in `operations/transactions/`.
- "Clean" means zero validator errors plus no new/grown warning signature (`python tools/warning_baseline.py --check` against `operations/validation-warning-baseline.yaml`).
- the rebuilt views is never hand-edited; application state is read via `list-*`/`inspect`/`search`/`related` over the manifest, not by parsing canonical YAML.
- `system/CRITIQUE-POINTS.md` is append-only: an open point is not a work item; acting on one needs Aram's explicit say-so in that session.
- Current gaps the vision correctly names: authority/coverage/staleness/evidence semantics are scattered; agents rebuild the same context per task; receipts say what changed through which capability, not why a semantic claim is believed; model selection is folklore ("Muse then Claude") rather than measured.
- Environment note: `python3 tools/los.py` currently cannot run here (`pyyaml`/`jsonschema` missing; `make setup` required). Plan validation assumes a working `.venv`.

## Constraints And Non-goals

Constraints:

- No fifth canonical knowledge family. The semantic layer is derived/queryable interpretation, not stored truth.
- No automatic semantic writes. Event rules may propose investigation, never mutate meaning.
- No weakening of OPERATOR.md hard boundaries: gateway scope, snapshot conflict reload, validate-after-change, critique-point gating, shelving approval.
- No silent corpus growth: any new `system/*.md` must be indexed in `normative-corpus.yaml` with class/authority/owner.
- Cost model must include tokens, latency, semantic risk, privacy risk, expected repair, and cache probability — not dollars alone.

Non-goals (explicitly deferred):

- Giant ontology, vector-DB-as-semantics, ECA auto-rewrite of learning semantics, RL self-modification of governance.
- Blackboard scheduler, fine-grained MVCC/serializability, TLA+ protocol models — only after phases 1–6 prove out.
- New model adapters or prompt libraries; models remain interchangeable executors behind the Task IR.

## Key Decisions

1. **Semantic Contract lives outside canonical data.** New derived layer, e.g. `system/SEMANTIC-CONTRACT.md` (binding reference, small: 15–25 predicates) + deterministic evaluator under `tools/learning_os/semantics/`. Predicates (`CurrentScopeAuthority`, `SupportedCoverage`, `EvidenceComplete`, `SemanticClaimStale`, `AllowedMutation`, etc.) are pure functions over existing records + manifest projection. Rejected alternative: storing semantic judgments as new canonical fields — would pollute the four-family limit and create a second source of truth.
2. **Verified Operator Questions (VOQs) are a test fixture, not runtime.** ~20 question/procedure/expected-property triples under `tests/fixtures/verified_operator_questions/` with a 15-example / 5-held-out split for benchmarking Muse/Claude/Astra. Rejected: baking VOQs into the gateway at runtime — bloat with no enforcement value.
3. **Lineage is a sidecar, not a canonical edit.** Per-claim `derived_from` (node revision, source hash, evidence segment, contract version, judged_by/reviewed_by, status) stored alongside receipts or as generated projection, never inside the canonical note/route body. Enables "what goes stale if X changes" without making canonical knowledge into AI beliefs.
4. **Candidate-goal engine is read-only detector + proposal queue.** `DETECTED → FORMULATED → ELIGIBLE → PROPOSED → AUTHORIZED → PLANNED → EXECUTING → VERIFIED → CLOSED` (plus `DEFERRED/REJECTED/STALE/SUPERSEDED`). Proposals queue under `work/proposals/` or `operations/`; only Aram authorizes. Rejected: Event-Condition-Action mutation — dangerous and violates critique-point rule.
5. **Task IR before cost learning.** First ship a logical plan schema + telemetry log (task type, inputs, model, tokens, tool calls, reviewer corrections, acceptance); route with a static cost table. Learn preferences only when statistics are significant. Rejected: starting with adaptive/RL routing — no data yet.
6. **Context dossiers are the rebuilt views cache with explicit hash keys.** `context://<unit|route>/semantic-dossier` keyed on unit/knowledge-map/source-map/route/evidence/contract-version hashes; invalidated per-dependency. Rejected: a new canonical dossier record.
7. **Proof-Carrying Change is a preflight envelope around existing gateways.** Intent, read/write sets, evidence locators, postconditions, validation plan; checked by `--check` + semantic-lineage checks before the existing `route.patch` / `module.plan.import` snapshot-guarded apply. Rejected: free-form diff review as the trust mechanism.

## Recommended Approach

Build six thin, independently shippable slices in the order the vision proposes, each reusing existing gates (validator, warning baseline, receipts, capabilities, manifest). Each slice adds at most one new concept plus its tests and docs; nothing lands without `make check`, `make warnings`, and its phase tests green. Stop/revert at any phase boundary with no canonical migration needed because no phase changes canonical schema.

## Work Plan

### Phase 0 — Guardrails and spike (0.5–1 session)

- Register intent: decide paths for semantic-contract doc, VOQ fixtures, proposal queue, telemetry log, dossier cache keys.
- Add empty schedulers/schemas with `make check` passing (normative-corpus entries, JSON schemas where needed).
- Spike one predicate end-to-end (e.g. `NeedsStudyMap` already derived as `needs_study_map`) to prove the evaluator pattern.

### Phase 1 — Semantic Contract + VOQs

- Define 15–25 predicates as pure functions over manifest/canonical reads; document each predicate's authoritative inputs and fallback-vs-authority rules.
- Add ~20 VOQs (scope authority, critique-point fixability, "is clean", Bayes-evidence procedure, route-validity dossier procedure). Mark 5 held-out.
- Add `tests/test_semantic_contract.py` + `tests/test_verified_operator_questions.py` (run held-out as eval, never as examples).
- Surfaces: `tools/learning_os/semantics/`, `system/SEMANTIC-CONTRACT.md` (or reference-class doc), fixtures.

### Phase 2 — Semantic lineage ("why is this believed?")

- Define claim-lineage record: claim, `derived_from` (revisions/hashes/segments/contract version), `judged_by`/`reviewed_by`, status (`supported/stale/contested`).
- Emit lineage for high-value derived claims only (route `covers` edges, scope-authority judgments, dossier freshness); store as sidecar/projection, backfilled lazily.
- Add impact query: "what depends on node-rev X / source-hash Y?" + `tests/test_semantic_lineage.py` (stale-propagation on fixture change).

### Phase 3 — Candidate-goal engine (Event → Condition → Proposal)

- Implement 5–6 read-only detectors: node-semantics changed with covering routes; source file changed underpinning claims; repeated operator-question class with no VOQ; repeated N-file inspection pattern with no dossier; systematic reviewer-correction pattern per task class.
- Proposal record with lifecycle states above; queue location TBD (see Open Questions); authorization remains an explicit Aram action, wired to the critique-point rule.
- Add `tests/test_goal_proposals.py` (detector fires on fixture, no write occurs, lifecycle transitions validate).

### Phase 4 — Agent Task IR + telemetry + static cost router

- Define Task IR schema: logical steps (`ReadKnowledgeNode → ReadExistingRoute → AcquireSourceEvidence → CompareCoverage → VerifyLocator → GenerateCandidateChange → ReviewEvidence → ApplyGovernedMutation`) with no model binding; physical planner maps steps to deterministic tool vs. Muse/Claude/Astra.
- Add telemetry append-only log: task type, IR, inputs, model, tokens/latency, tool calls, corrections, acceptance.
- Ship static cost function `C = w_t·tokens + w_l·latency + w_r·semantic_risk + w_p·privacy + w_f·expected_repair − w_c·cache_prob` with policy vetoes (e.g. unpublished material → contributor-model infeasible) and rewrite rules (predicate pushdown, projection pruning, cheapest-evidence-first, late materialization of large PDFs, dedup via dossiers).
- Learning comes later: promote static weights to fitted ones only with significant data. Tests: IR schema validation + router unit tests on fixtures + telemetry append tests.

### Phase 5 — Materialized context dossiers

- Dossier builder with declared inputs + hashes (unit/knowledge-map/source-map/routes/evidence/operator-contract/semantic-contract versions); content-addressed under the rebuilt views; per-dependency invalidation.
- Reuse path: Muse/Claude/Astra request same `context://…` key; validator ensures no hand-edit path.
- Tests: cache-hit on unchanged inputs, single-dependency invalidation on route change, no canonical mutation.

### Phase 6 — Proof-Carrying Change + translation validation

- Change envelope: intent, scope, read set with revisions, claims + evidence locators + hashes, write set (capability + payload), expected snapshot, postconditions, validation plan.
- Deterministic admission check runs before gateway apply: evidence resolves, read set fresh, snapshot matches, postconditions + `semantic-lineage-check` + `make check` pass; on failure return conflict/replan, never overwrite.
- Trust model: validate each transformation independently (untrusted producer → candidate → independent validators → accept/reject). Tests: admit-good fixture, reject stale-read, reject missing-evidence, reject out-of-scope write.

## Validation Plan

- Per phase: `make check` (zero errors), `python tools/warning_baseline.py --check` (no new/grown signature), `make test-fast`, then full `make test` before merging the phase.
- Phase 1: VOQ suite green on examples; held-out score reported per model (informative, not a gate).
- Phase 2: fixture mutation marks exactly the expected dependent claims stale; unrelated claims untouched.
- Phase 3: detector fixtures produce `PROPOSED` records with zero canonical diff and zero the rebuilt views hand-edit.
- Phase 4: router fixture picks deterministic validator for schema checks, cheapest local evidence first, policy-veto on privacy case; telemetry rows append with required fields.
- Phase 5: repeated dossier request hits cache; single-route fixture change invalidates only dependent dossiers.
- Phase 6: good envelope commits with exactly one receipt; stale/missing-evidence envelopes rejected without mutation.
- Highest-risk validation: Phase 6 admission checks (stale-write-never-commits, one-approval-one-scope, conflicting writes cannot both succeed). Exercise these fixtures explicitly.

## Risks / Rollback

- **Contract bloat**: cap Phase 1 at ~25 predicates and ~20 VOQs; any addition needs a VOQ or detector motivating it. Rollback: delete derived layer; canonical data untouched.
- **Lineage staleness theater**: lineage that nobody invalidates is worse than none. Mitigate with lazy backfill + impact-query tests. Rollback: drop sidecars.
- **Proposal spam**: detectors firing too often. Mitigate with eligibility thresholds + dedup (`STALE`/`SUPERSEDED`); queue is read-only so spam never mutates.
- **Premature optimization**: cost weights as folklore. Mitigate with static-first + significance gate before learning.
- **Cache poisoning**: dossier served after dependency change. Mitigate with hash-keyed invalidation tests.
- **Envelope bypass**: hand edits skipping the gateway. Mitigate by keeping `route.patch`/`module.plan.import` + snapshot guards as the only write path; envelope is preflight, not an alternative.
- All rollbacks are deletions of derived artifacts/docs/tests; no canonical migration is introduced by any phase.

## Open Questions

- Proposal queue home: `work/proposals/` vs. `operations/` — default to `work/proposals/` unless it conflicts with workspace conventions found during Phase 0.
- Lineage storage: receipt-adjacent sidecar vs. generated projection — decide in Phase 2 spike based on receipt schema churn.
- No other open questions; scope, authority, and non-goals are resolved above.
