# V4 — AI actions end to end (GLM verification, 2026-10-25)

**Status: DONE — 0 findings, 7/7 cases HELD (+1 scope probe on the second
action), 1 coverage gap, 3 observations, 29 registered gateway tests green.**

## Base

- Core pin: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`
  (clone: `~/los-glm-V4-2026-10/repository`, verified with `git rev-parse HEAD`)
- UI pin: `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`
  (clone: `~/los-glm-V4-2026-10/obsidian-ui`, verified with `git rev-parse HEAD`)
- Core venv: Python 3.14.4, `pip install -e '.[dev]'` exit 0. UI `npm install` exit 0.
- Baseline on the pin: `tests/test_ai_actions.py` — 29 passed. No `make setup`,
  no `make hooks`, no network, no real model API. Stub/manual providers only.
- Registered probe file: `tests/test_v4_ai_gateway.py` (in my clone, registered
  in `tests/group_map.py` under `gateway` and in `.github/shard-manifest.json`
  leg `rest-0` per `system/DEVELOPER.md` "Add a test file") — 29 passed on the
  pin (`logs/pytest-v4-ai-gateway.log`). A copy is in `probes/`. No fixes, no
  pushes; the clone carries only the test file and its two registration lines.

## Reading route

1. `system/AI-ACTIONS.md` — the delivery bundle format, the manual-bundle
   workflow, the "Application is a GatewayEnvelopeV2-only write" rule, staleness
   scoping, supersedes, the post-action scope check.
2. `system/developer/components/ai-action-store.md` — owns
   `tools/learning_os/store/ai_actions/*`; entry point
   `binding.py::read_bound_delivery`; invariant "AI state is not permission to
   rewrite arbitrary learner records"; pinning test `tests/test_ai_actions.py`.
3. `system/developer/components/ai-delivery.md` — owns
   `tools/learning_os/app/ai_actions/*`; entry point
   `service.py::AIActionService`; invariant "A provider response must never
   authorize its own canonical mutation".
4. Invariant 12: `system/CLAUDE.md` no longer numbers invariants itself; it
   resolves former sections to `system/OPERATOR-POLICY.md`. Invariant 12 lives
   at `system/OPERATOR-POLICY.md:22`: "**General AI is read-only.** Canonical
   writes use an action-specific gateway capability, current snapshot,
   post-action scope check, validation, and regeneration." (Mirrored as rule 11
   in `system/OPERATOR.md:148`.)
5. AI-related capabilities from `tools/los.py capabilities --compact --json`:
   - write capability: `ai-action.delivery.apply` (command, CLI
     `ai-action-apply-delivery`, writes `operations/ai-actions/requests/**`).
   - domain capabilities reachable only through a delivery's operations:
     `garden.add-transcription`, `garden.update`, `relationship.create`,
     `unit.material-synthesis.publish`.
   - CLI verbs: `ai-action-list`, `ai-action-prepare`, `ai-action-status`,
     `ai-action-import-delivery`, `ai-action-validate-delivery`,
     `ai-action-apply-delivery`, `ai-action-append-slices`.
   - Adjacent per ADR-017: `concept.relations.change` (manual relation
     authoring; sole declared writer of `knowledge/concept-relations.yaml`).
   - Guarantee flags: `ai_actions_are_provider_independent`,
     `bounded_ai_actions_use_exact_context`.
6. Contracts: `system/contracts/ai-actions/{garden.shelve,unit.compare-materials}.yaml`,
   `system/contracts/ai-adapters.yaml` (manual-bundle available; claude and
   chatgpt unavailable), `system/contracts/capabilities.yaml` write scopes.
7. ADR-017 decisions 2 and 3 (proposals pending until selected, entering only
   through `concept.relations.change`; manual authoring with no provider).
8. `tests/gateway_helpers.py` — the V2 subprocess driver shape; and the
   pinning file `tests/test_ai_actions.py` (29 tests, all pass on the pin) so I
   attack only what it does not already cover.

## Results per item

All probes drive the real V2 gateway subprocess
(`los.py --root <fixture> capability ai-action.delivery.apply --payload-file -`,
envelope with `approved-delivery` authority, exactly as `tests/gateway_helpers.py`
shapes it) plus the public `ai-action-*` CLI verbs. 44 verdict lines, log at
`logs/probe-cases-final.log`; probes in `probes/probe_roundtrip.py` and
`probes/probe_cases.py`; the same probes are registered as
`tests/test_v4_ai_gateway.py` (24 tests, all pass on the pin — no findings).

| # | Case | Result |
|---|------|--------|
| 1 | Exact-target binding | **HELD** (4 probes) |
| 2 | Partial approval | **HELD** (2 probes) + 1 observation |
| 3 | Receipts written once, match application | **HELD** (5 probes) + 1 observation |
| 4 | Replay; foreign request id | **HELD** (3 probes) |
| 5 | Relation proposals pending; one path | **HELD** at every enforceable point (5 probes) + 1 coverage gap |
| 6 | No provider configured — manual paths | **HELD** (3 probes) |
| 7 | No direct canonical writes by a provider response | **HELD** (5 probes) |
| + | Second registered action `unit.compare-materials` | **HELD** (full round trip + replay) |

Details:

1. **Exact-target binding — HELD.** (a) Target edited after prepare, before
   import → `ai-action-import-delivery` refuses: "Garden target changed after
   request preparation". (b) Target edited after import; approval re-minted
   with a fresh snapshot and fresh revisions (the strongest form of the attack)
   → the gateway apply refuses with `STALE_SNAPSHOT` "Garden target changed
   after request preparation"; zero canonical side effects. The request's
   preconditions carry the target's content token, so no fresh envelope can
   launder a moved target. (c) `ai-action-prepare --expected-snapshot <stale>`
   refuses exactly as AI-ACTIONS.md documents. (d) An operation whose
   `target_id` names a different note is refused at import ("targets an
   unrelated artifact").
2. **Partial approval — HELD.** (a) There is no subset-selection surface: the
   payload schema for `ai-action.delivery.apply` is
   `additionalProperties: false` over `{delivery_id, delivery_sha256,
   artifact_sha256}`; adding `selected_operations` is refused ("Additional
   properties are not allowed"). Approval granularity is the whole delivery.
   (b) An approved three-operation delivery applies all three (transcription +
   garden-state + relationship), the receipt's `writes` covers every
   destination, and the request completes atomically. The shelving-style
   `selected` list belongs to `review.apply`, a different capability that no
   AI action may name (allowed/forbidden lists checked at import).
3. **Receipts — HELD.** One apply → exactly one ReceiptV2 under
   `operations/transactions/`. Exact replay → `replayed: true`, same receipt
   path, no receipt file added, no canonical write. Every `writes[].sha256_after`
   matches the bytes on disk, and `snapshot_after` equals the live projection
   fingerprint (regeneration happened). A second apply under a NEW idempotency
   key with a fresh snapshot is refused (transcription guard names the
   superseding rule). The manifest projection records the completed request.
4. **Replay / foreign request id — HELD.** The exact first envelope bytes
   replay with `replayed: true`, the same transaction id, and zero writes.
   A delivery naming an unknown request id is refused at import
   (`AI action request not found`). A delivery naming another existing
   request's id while carrying different preconditions is refused at import
   ("delivery preconditions must equal the prepared request preconditions").
5. **Relation proposals / one path — HELD where enforceable.** (a) In
   `system/contracts/capabilities.yaml`, exactly one capability declares writes
   over `knowledge/concept-relations.yaml`: the command
   `concept.relations.change`. (b) A delivery operation naming
   `concept.relations.change` is refused at import ("capability is not
   allowed") — an AI delivery cannot write the concept registry. (c) A garden
   apply that adds an AI relationship leaves `knowledge/concept-relations.yaml`
   byte-identical (the AI registry `operations/ai-actions/relationships.yaml`
   is a different record family, per ADR-017 decision 1). (d) The manual path
   needs no AI: an operator-approval envelope for
   `concept.relations.change` adds a relation, with no provider anywhere.
   (e) A `direct-user-gesture` approval claiming the relation editor fails
   closed outside the reviewed-UI channel (typed refusal naming the reviewed
   route). See Coverage gaps for the "visibly pending" half.
6. **No provider configured — HELD.** (a) `--provider claude` (declared
   unavailable on the pin) is refused at prepare with a typed message naming
   the adapter — from the CLI, exactly as the core enforces for the UI.
   (b) With every adapter declared unavailable: `ai-action-list` still works,
   prepare refuses typed, and manual concept authoring through the gateway
   still succeeds (ADR-017 decision 3). (c) On the pin's default state
   (only manual-bundle available) the full manual-bundle round trip completes.
7. **No direct canonical writes — HELD.** (a) A bundle containing a symlink is
   refused at import; the only side effects stay under
   `operations/ai-actions/`. (b) An `artifact_ref` with `../` traversal is
   refused ("unsafe bundle path") and the seed is untouched. (c) A rejected
   import never occupies `operations/ai-actions/deliveries/`. (d) An operation
   naming a canonical writer outside the request's allowlist (`note.create`)
   is refused. (e) Artifact bytes tampered after approval are refused at apply
   by the SHA-256 binding ("approved delivery artifact content hash does not
   match the imported bytes"); nothing canonical is written. The gateway apply
   writes only: the transcription, garden-state, the AI relationship registry,
   the request record, the receipt/ledgers, diagnostics, and the regenerated
   `generated/` projection.
8. **Second registered action — HELD.** `unit.compare-materials` prepares from
   a fixture unit with a real sliced PDF material, and an approved delivery
   publishing `unit.material-synthesis.publish` lands the dossier at
   `curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml`
   through the same gateway, regenerates the manifest, and replays exactly.
   Page-provenance enforcement refused an under-inspected citation on the way
   ("cites lecture-01.pdf pages never inspected"), and the envelope must cover
   the synthesis record id exactly — both fail-closed behaviors.

## Findings

None. Every attack in the seven cases is refused on the pin for the stated
reason, and every manual path works.

## Observations (no contract line violated)

- **O1 — a second, freshly-approved application of the same delivery is
  possible when no transcription guard applies.** For a garden.update-only
  delivery, applying twice under two distinct approval envelopes (different
  idempotency keys, each with a fresh, correct snapshot) produces two
  transactions, two ReceiptV2s, garden-state revision 1→2, and the request
  record moves to the second receipt. Each receipt was written once and
  matches its own application; no exact replay is involved; nothing outside
  `operations/` changed. Gateway semantics permit any capability to be applied
  again under a new approved intent, and AI-ACTIONS.md names no one-per-delivery
  rule. Probe 3d in `probes/probe_cases.py`; pinned as a behavior test in
  `tests/test_v4_ai_gateway.py`.
- **O2 — a duplicate `relationship.create` id is silently deduplicated, not
  refused.** Verified by probe: a delivery whose approved operations name an
  existing registry id applies, the pre-existing row survives with its own
  provenance, `created_ids` is empty, and the rest of the delivery (garden
  update) still lands. The receipt is honest about what was applied; the
  deduplication is visible in that the envelope must NOT cover the relation id
  (over-covering is refused by the exact-coverage rule). ADR-017 decision 1's
  duplicate-refusal requirement is scoped to `concept.relations.change`, not
  this record family. Pinned as `test_duplicate_relationship_id_is_deduplicated_not_applied`
  in `tests/test_v4_ai_gateway.py`.
- **O3 — the apply path does not re-check adapter availability.** Availability
  is a prepare-time gate (AI-ACTIONS.md says exactly that: prepare refuses an
  unavailable adapter); an imported delivery still applies after the adapter
  is later declared unavailable. Consistent with the documented boundary.
  Verified by reading `service.py` alongside probe 6; not separately pinned.

## Coverage gaps

- **G1 — "AI relation proposals stay visibly pending until selected"
  (V4 case 5 / ADR-017 decision 2) is not exercisable in Core.** Core has no
  store or surface where an AI *concept-relation* proposal awaits selection:
  the two registered actions produce garden transcriptions/state, AI-registry
  relationships (written only on approved apply), and unit dossiers. The
  proposal-pending mechanics therefore live — if anywhere — in a launcher
  layer outside Core, and no Core test can exercise the property. Everything
  ADR-017 decision 2 *enforces in Core* (entry only via
  `concept.relations.change`, refusals above) is verified HELD.
- **G2 — the Obsidian launcher side of the AI flow is untested here.** The UI
  clone is installed per the ground rules, but V4's cases are Core gateway
  properties; AI-ACTIONS.md states the interface "enforces nothing on its
  own". V2's scope covers UI rendering; the UI's AI-action surfaces were not
  exercised in this batch.
- **G3 — `ai-action-append-slices` (continuation passes) was not exercised.**
  It mutates only the request bundle (no canonical write); the campaign's
  seven cases do not reach it, and it has its own scenario case
  (`tests/scenarios/cases/ai-action.append-slices.yaml`).

## Untested scope

- `unit.compare-materials` slice/continuation mechanics (append-slices, page
  provenance) beyond what a minimal publish needs — that surface is V3's
  material territory and has its own scenario cases.
- The Obsidian UI launcher (UI clone installed per ground rules, but V4's cases
  are Core gateway properties; the UI enforces nothing itself per AI-ACTIONS.md).
- Any real provider adapter: only `manual-bundle` exists and no network is used.

## ASSUMPTIONS

- "Invariant 12 in system/CLAUDE.md" resolves to `system/OPERATOR-POLICY.md:22`
  via CLAUDE.md's own final paragraph (sections 1, 3–6 and 8–14 moved there);
  verified by reading both files. The campaign's paraphrase "general AI is
  read-only" matches OPERATOR-POLICY.md:22 exactly.
- The gateway subprocess driver in `tests/gateway_helpers.py` plus the
  `approved-delivery` approval kind (as built by `test_ai_actions.py`'s
  `apply_approved_delivery`) is what "the real V2 gateway" means for
  `ai-action.delivery.apply`; there is no other public entry.
- The campaign's "each [receipt] is written once" reads over receipts, not
  over deliveries: one receipt per approved transaction, replay never mints a
  second one. A second *approved* application (new envelope, new key) is a new
  transaction — recorded as observation O1, since no contract line forbids it.
