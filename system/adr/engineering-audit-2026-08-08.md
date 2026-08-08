# Engineering audit — 2026-08-08

**Author:** Aram (external-perspective audit of the current pushed heads)
**Status:** findings recorded, **remediation not started**
**Scope:** LearningOS Core + Obsidian UI, audited as pushed — not as discussed in
any prior conversation.

> **Why this file exists.** The audit was produced in a session whose sandbox was
> wedged, so none of it could be acted on. It is filed here so the work can start
> cold without re-deriving anything, in the same spirit as ADR-009's own framing.
> Findings are preserved as written; nothing below has been re-argued or softened.

## Audited heads

| Repo | Commit | Branch | CI |
|---|---|---|---|
| Core | `a89d66d13b52cd105bb233adb5b2e970ec6e5e40` | `feature/improvement-stage-0-v1` | **green** — 240 tests, 0 validation errors |
| UI | `6121957b70641b5a990334173e4eb380adfb3d90` | `feature/improvement-stage-1b-closed-host-slice-v1` | **red** |

## Overall judgment

> The fundamental architecture is still very good. There is no evidence of
> architectural collapse, unsafe persistence, or a need for redesign.
>
> What exists is a collection of **cross-layer integration defects,
> lifecycle-state inconsistencies, and contract/governance weaknesses produced by
> very rapid recent evolution.**

The hard parts — canonical ownership, transactions, validation, identity,
migrations, provenance — are mostly strong. The weak areas are where one layer
interprets another.

| Area | Assessment |
|---|---:|
| Overall architectural model | 9.1/10 |
| Canonical data model | 9.2/10 |
| Transaction safety | 9.4/10 |
| Schema/versioning discipline | 9.2/10 |
| Core internal engineering | 9.0/10 |
| Projection architecture | 8.3/10 |
| Semantic consistency of current data | 8.0/10 |
| Core ↔ UI interface discipline | 7.3/10 currently |
| UI internal architecture | 7.5–8.0/10 |
| Repository/release governance | 6.5–7.0/10 |
| Current release readiness | **Not release-clean yet** |

---

# Findings

## 1. CRITICAL — Core changed the manifest interface without changing its version

Core now publishes a new top-level `topics` collection, and every projected
source gains `topics: [...]`. That is exactly what ADR-009 needs. But Core still
emits `"contract_version": 2` inside `_generated`, while the UI contract still
declares `MANIFEST_CONTRACT_VERSION = 2` and `ManifestV2` has no top-level
`topics`. The UI's manifest lock likewise says v2 and enumerates permitted
top-level fields; `topics` is absent. **This is why UI CI is red.**

This is more than a stale test. LearningOS has explicitly adopted
*versioned interface + consumer fails closed*. Adding a new top-level interface
field while continuing to call the interface v2 violates one of its own
strongest rules. The problem is not that adding `topics` is wrong — it is
`old declared contract + new actual shape`.

**Root cause.** Core owns the *canonical-record* contract
(`system/contracts/data-contract.yaml`) but the *manifest/projection* contract is
effectively owned on the consumer side, in the UI repo. So Core can change the
manifest, pass its own CI, push, and only then have the UI discover the
incompatibility.

**Fix.** A real **manifest contract v3**, distinct from the canonical data
contract (currently v4). Two contracts, stated explicitly:

```
Canonical record format      v4
Manifest/interface projection v2 → v3
```

Core should own e.g. `system/contracts/manifest-contract.yaml` (or a JSON
Schema / locked fixture). A Core change that alters the public projection should
fail **Core CI** unless the interface contract is deliberately bumped.

## 2. HIGH — `project.create` / `project.update` violate the capability-contract model

Most capabilities follow a clean path: envelope → validate payload against
generated schema → translate to CLI arguments → same command implementation.
`project.create` and `project.update` are special-cased.

The gateway expects `{ "project": { ... } }` (implementation does
`payload.get("project")` and requires an object). But the declared generated
payload schema for `project.create` requires `{ "file": "..." }`, and
`project.update` requires `{ "file": ..., "project_id": ... }`. Neither declares
a `project` field. The special path also skips `_validate_payload()`.

So an agent obeying the declared schema gets rejected, while an agent sending the
*undeclared* shape is accepted because validation was skipped. The capability
gateway is supposed to be the deterministic boundary around probabilistic agents;
at that boundary the machine-readable contract must be exceptionally trustworthy.

**Fix.** Move project create/update onto the same domain-operation path as
everything else, rather than a gateway-only special case.

## 3. HIGH — Algo2 is simultaneously "dropped" and "ready"

The workspace is unambiguous: `status: blocked`, "DROPPED from the autumn cycle.
No registration. No study. Required now — nothing. Next Action — None."

The module remains `status: enrolled` because there was no formal university
withdrawal — defensible and documented. But the operational curriculum objects
disagree: the unit says `status: ready`, the study map says `status: ready`, and
the stage says `status: pending` with `scope_triage: required-now`.

The repository therefore says, at once: *do nothing* / *ready* / *ready* /
*required now*.

**Fix.** Keep `module: enrolled`. Set `workspace: blocked`, `unit: paused`,
`study map: paused`, preserving the stage underneath — administratively enrolled,
operationally paused, reinstatement plan intact.

**Add an invariant:** a blocked workspace representing the sole/current execution
context for a unit cannot coexist with a `ready` or `active` unit/map unless an
explicit exception is declared. That converts a one-off fix into a class of
impossible states.

## 4. HIGH — `module.status` combines two different state machines

The schema allows `planned, enrolled, active, paused, awaiting-grade, completed,
dropped, archived`. But `planned / enrolled / awaiting-grade / completed /
dropped` are **administrative** states, while `active / paused` are
**operational** — and the axes coexist. Algo2 is administratively enrolled and
operationally blocked. PPDS is administratively submitted/grade-pending and
operationally paused.

The UI is already guessing wrong: Home's *Continue elsewhere* loops modules and
excludes only `complete` and `archived`, so `enrolled` counts as active work.
PPDS is `status: enrolled` despite its notes saying the project is submitted and
the grade pending, and its only unit is `paused` — yet Home can still list it.
Algo2 can appear there too.

**Fix (small).** Core projects `administrative_status`, `operational_state` and
`is_actionable`; the UI consumes `is_actionable` instead of interpreting module
status. This respects the rule that the UI should not derive semantics.
**Longer term:** make `status` purely administrative and let operational state
live in units/maps/workspaces.

## 5. HIGH/MEDIUM — the source-domain projection partly undoes the faceted design

ADR-009 correctly separates **domain** (what is this about?) from **current use**
(where is this being used?). But `_source_thematic_groups()` starts with the
source's authored groups and then *adds* groups from collections containing the
source and from modules whose source-map uses it. **Usage context therefore
changes projected intellectual identity.**

Concrete case: `source-dmmls-boehm` is canonically tagged only
`thematic-group-ml-systems`. The AMLS module belongs to ML Systems, Machine
Learning and Data Systems, and DMMLS is in the AMLS source map — so the
projection can present DMMLS as all three. That conflates *what DMMLS is* with
*where DMMLS happens to be useful* — precisely what the faceted redesign was
meant to solve.

**Fix.** Now that ADR-007 has assigned explicit groups to every source, remove
inherited group membership from projection: domain = authored
`thematic_group_ids`; current use = `source_to_modules` / `source_to_units`.
Collections must not silently redefine source domain. If contextual placement is
wanted, project it as `contextual_group_ids` — do not call it domain membership.

## 6. MEDIUM-HIGH — the AI context handoff discards the resource identity just created

The UI now knows `resource_id`, `source_id`, `label`, `locator`, `scope_triage`,
`url` and vault path for a stage resource. But `explicitAiContext()` sends the
agent only `selected_source_ids` and `selected_materials` plus module/unit/stage
IDs — not `resource_id`, `label`, `locator` or `scope_triage`.

The material flattening is worse: precedence is `material_uri → vault_path → url
→ material_path`. In AMLS L03 the four papers (SystemML, SPOOF, SPORES, TASO)
share one `vault_path` (`AMLS-Source-Papers-Reading-List.md`) but have distinct
resource IDs and distinct URLs. The handoff can therefore become the same
reading-list path four times. The system knows these are four distinct objects,
then throws that knowledge away while handing context to the semantic operator —
the one layer that most needs resource identity.

**Fix.** Send `selected_resources` as structured objects (`resource_id`,
`source_id`, `label`, `locator`, `scope_triage`, `url`, `material_path`). Keep
`selected_source_ids` as a convenience if desired, but never collapse semantic
objects to one path string.

## 7. MEDIUM — "By current use" disagrees between Core and UI

Core's model: a source is currently used by a module when it is in a module
source-map **or** cited by a stage. The manifest already carries separate
`source_to_modules` and `source_to_units` indexes, where `source_to_modules`
includes every source-map entry and `source_to_units` only explicitly
routed/cited relationships.

The UI derives modules *from units*, so it loses module-level usage when
`unit_routes: []`. Real case in M2:
`source-swanson-principles-probability` has `role: reference, priority: 99,
unit_routes: []` and is still deliberately in the M2 source-map. Core can
correctly say "current use: M2" while the UI fails to count it.

**Fix.** Use `indexes.source_to_modules` directly for the module facet — another
case of the UI re-deriving what Core already projected correctly.

## 8. MEDIUM — resource-specific feedback is written correctly but displayed ambiguously

Half fixed. Unit view now reads `resource.id` / `resource.scope_triage` and sends
`resource_id` to the gateway when rating. But the *Stage context* rendering of
existing feedback uses only `source_id` + `feedback`, ignoring `resource_id`,
`note` and `recorded`. So "SystemML → helpful" and "SPORES → too advanced" both
render as `source-amls-ss26-lectures · …`. Ambiguity restored on the read path.

**Fix.** Resolve `resource_id → stage.resources[id]` and display the resource
label, with source secondary. Needs a regression test using two resource IDs from
the same parent source.

## 9. MEDIUM — Home's definition of "today" is UTC, not local

`new Date().toISOString().slice(0, 10)` is UTC. At 01:00 Europe/Berlin on
2026-08-08, UTC is still 2026-08-07, so the *Today* deadline filter can be a day
wrong around local midnight.

**Fix.** Build the calendar date from local components (`getFullYear`,
`getMonth`, `getDate`) or an explicit local-date utility.

## 10. MEDIUM — "Continue elsewhere" is not priority-aware

Home collects modules/projects and effectively does `rows.slice(0, 5)` without
ranking against the current coordination plan. The section claims "other active
modules and projects", but the five rows are a consequence of manifest ordering,
not AMLS priority / AML synergy / M2 / thesis slack. This is made worse by PPDS
and Algo2 counting as active (see #4), so five slots can fill with
Foundation/Algo2/AML/AMLS/PPDS while something actionable is omitted.

**Fix.** Not another hand-coded UI sort — Core should expose actionability and
priority well enough for the UI to render a mechanically derived ordered list.

## 11. MEDIUM — ADR-007 is materially stale

It still says in effect "Migration step 1 applied. Steps 2–6 pending." and
retains old statements about the earlier group count, though the eight-group
migration is complete. For an ordinary project this is documentation debt; for
LearningOS, whose explicit goal is that *an external agent should be able to read
the repository cold and understand its current truth*, a stale ADR is a
**semantic input bug**.

**Fix.** Make the top unmistakable — `STATUS: ACCEPTED AND MIGRATED. Migration
complete. Historical proposal/context below.` — preserving decision history
underneath. ADR-009 is much better already because it marks its original "do not
implement yet" section as historical/superseded.

## 12. MEDIUM (product gap) — Search ignores the actual knowledge base

Global Search remains structural: modules, projects, units, sources, topic packs,
workspaces — but not first-class **notes** and **concepts**. This needs no
Elasticsearch, embeddings or AI search: Core already projects notes and concepts
into the manifest and the app already opens note/concept records. A minimal
correct taxonomy:

```
Knowledge → Notes, Concepts
Learning  → Modules, Units
Sources   → Sources, Topic Packs
Projects  → Projects
```

Product incompleteness, not a correctness bug.

## 13. MEDIUM/LOW — the UI exposes half the feedback vocabulary

Canonical schema supports `helpful, too-advanced, wrong-perspective,
useful-for-derivation, useful-for-review, skipped`. The rate menu exposes only
Helpful, Too advanced, Useful for review. Not necessarily wrong — the UI should
stay simple — but it should be a **deliberate** mapping to a canonical subset
rather than an accidental omission. Probably expose *Useful for derivation* too;
`wrong-perspective` and `skipped` can live in a less prominent menu.

## 14. TECH DEBT — the UI type boundary is looser than it appears

`export type ProjectionRecord = Record<string, any>` means much of the apparent
type safety is recovered manually inside every view via `projectedString()`,
`projectedText()`, `projectedStrings()`, `projectedRecords()` (UnitView,
LibraryView, …). Boundary narrowing from JSON is correct, but the same
translation concern is distributed through rendering classes, so views own raw
projection interpretation *and* view-model construction *and* routing state *and*
filter semantics *and* rendering *and* interaction.

**Eventual cleanup:** `ManifestStore → projection adapters → typed domain/view
models → Views`, e.g. `src/projection/{primitives,unit-model,library-model,
module-model,project-model}.ts`, so `UnitView` receives `resource.triage` and
never learns the wire name `scope_triage`. **Do not do this now** as a broad
refactor — it is maintainability debt, not urgent correctness.

## 15. Core maintainability hotspot — the loader

`tools/learning_os/loader.py` is ~35 KB and a lot of Core semantics flows through
it. Not automatically a problem; a loader for a filesystem-backed domain
naturally becomes substantial. Split it only along real responsibility seams
(curriculum / source / knowledge / project loaders) with independent
invariants and tests — never purely to reduce line count.

## 16. Capability payload schemas are less precise than canonical schemas

`source.feedback.record`'s machine payload schema describes `feedback: string`,
`source_id: string`, `resource_id: string` without the canonical enums/patterns,
while the canonical study-map schema later enforces `resource-[...]`,
`source-[...]` and the six allowed feedback values. An invalid agent payload
passes the outer capability schema and fails downstream. Safe (the transaction
rolls back) but unnecessarily late. The generated machine contract should carry
argparse choices and ID patterns into the JSON Schema so bad requests fail at the
boundary with a precise message.

## 17. Repository governance is weaker than the software architecture

Core `main` is **47 commits behind** the active working branch; UI `main` is
**53 behind**. Working branches are unprotected and required status checks are
disabled.

Two consequences. **Agent discoverability:** a fresh agent landing on
`github.com/Aram164/LearningOS` sees `main` and may inspect an architecture a
week and 47 commits behind reality — bad for a system whose canonical branch
should be discoverable without conversation memory. **Release safety:** the
current UI head is red, and nothing prevents treating it as the active branch.

**Fix.** Once green Core + green UI + compatible manifest contract + normalized
semantic state are in place, merge or fast-forward the intended stable line into
`main` and tag the coherent Core+UI pair. At minimum, protect `main`.

## 18. Cross-repo CI is the missing piece

Core CI (schemas, validation, tests, weekly URL audit) and UI CI (build,
typecheck, contract check, tests, installer dry-run, plugin artifact) are both
well designed. The missing test is
`CURRENT CORE MANIFEST → CURRENT UI CONTRACT → compatible?`, which today only
exists indirectly, after both repos have independently moved. This is the primary
reason the current manifest problem could land. Establish a shared compatibility
fixture, or a small workflow that retrieves the expected Core manifest contract.

## 19. UI dependency installation could be more reproducible

CI runs `npm install --ignore-scripts`. With an authoritative
`package-lock.json`, it should be `npm ci --ignore-scripts`, which turns lockfile
drift into a failure instead of letting install rewrite the tree. Low severity,
straightforward hardening.

## 20. Core writer locking is Unix-specific

The operator lock uses `fcntl`, making the implementation Unix/macOS-only.
Entirely acceptable for the current environment; worth documenting if LearningOS
is meant to become portable. Do not solve Windows locking without a real need.

---

# What was inspected and found healthy

## 21. Generated-output publication is well engineered

The generator generates all content first, writes each output through a temporary
sibling, uses `os.replace()` for atomic per-file publication, deliberately
publishes `manifest.json` **last**, then removes stale generated files. Since
Obsidian treats `manifest.json` as the interface, publishing it last acts as the
commit marker. Not a filesystem-wide atomic transaction, but an excellent
tradeoff for this architecture. **Do not redesign.**

## 22. The transaction engine is one of the strongest pieces of the system

Path confinement, artifact revisions, optimistic concurrency, pre-write backups,
atomic temp/replace writes, canonical validation, projection publication,
transaction receipts, rollback. On failure it restores canonical files, restores
the revision ledger, removes any receipt created by the failed attempt, and
republishes the prior projection. No indication of a fundamental persistence
flaw. **The subsystem to disturb least.**

## 23. The resource-identity design held up

No conceptual problem warrants backing out ADR-009. Identity belongs to the
teaching object, not the citation occurrence, so repeated papers share identities;
activities get no resource IDs, preventing entity proliferation. The
resource-feedback write path validates the relationship before writing, and the
current Core commit moved its tests into a mini repository after discovering
earlier tests had polluted the real transaction ledger — exactly how a mature
test suite should evolve. Current GitHub transaction state contains no unwanted
2026-08-08 test receipts.

## 24. Resource triage in Unit view is good

Scope now drives presentation: *Do this / If you get stuck / Depth — not now /
Reference — preserved*. This directly addresses the "sea of sources" problem at
the learning-stage level.

*Minor caveat:* unranked legacy resources are treated like primary ones.
Backward-compatible, but `unranked` is not semantically `required-now`. Do not
change the fallback globally — that could hide old material incorrectly.
Normalize old frequently-used plans gradually, on use.

## 25. The faceted Library is right, but navigation could go one step further

The Core model (same source → Domain / Topic / Purpose / Form / Current use, with
overlapping membership) is fundamentally correct. But the Obsidian flow still
starts at *Library → choose domain → facet those sources*. A truly faceted
browser would offer peer entrances — **By Domain / By Topic / By Purpose / By
Form / By Current Use** — so *Topic → ML Compilation* is reachable without first
deciding whether the item belongs under ML, ML Systems, Algorithms or Software.
Not a data-model bug; the last UX step to realize the polyhierarchical idea.

## 26. The remaining collection cleanup should not be automated

ADR-009 correctly leaves `ml-broaden-later` and computable bookshelves open. Some
collections are merely computable ("all ML books") and should become views;
others encode human curation and order ("recommended AML learning sequence") and
should remain explicit objects. **Do not bulk-delete collections just because
facets now exist.** The rule *preserve collections where ordering/curation
carries meaning* is sound.

## 27. One minor ADR-009 residue

ADR-009 is substantially cleaned up and clearly says it is implemented, but still
retains an early `Decision gate: after the AMLS sitting` even though its status
says both features were already built. Far less serious than ADR-007 because the
later historical explanation makes the sequence understandable — but label the
old gate `Original decision gate (superseded)` for cold-agent readability.

*(Confirmed against the file: `ADR-009-…-2026-08-08.md` line 10 still carries the
unqualified gate directly beneath a status of "accepted and implemented".)*

## 28. Audit the source taxonomy after changing domain projection

The faceted system only works if each axis stays independent —
`domain ≠ use`, `topic ≠ concept`, `role ≠ type`, `lifecycle ≠ collection`. The
biggest current violation is `domain ← module usage` via
`_source_thematic_groups()`. Once fixed, run a one-time comparison of *projected*
vs *authored* domain memberships for every source; any difference should require
an explicit rationale.

## 29. What was NOT found

| Concern | Assessment |
|---|---|
| Canonical writes bypass transaction handling | No evidence |
| Core permits obvious partial canonical commits | Transaction service explicitly rolls back |
| Manifest written before supporting projection state | No — manifest published last |
| Resource IDs duplicate citation occurrences | No — implementation correctly fixed this |
| Faceted model became free-form tag soup | No — controlled vocabulary |
| UI moved semantic AI reasoning into Core | No |
| Obsidian directly owns canonical state | No architectural sign |
| ADR-009 requires physical material duplication | No |
| External materials need to return to Git | No |
| Current Core CI unhealthy | Core exact head is green |
| A new architectural rewrite is needed | **Definitely not recommended** |

---

# 30. The architectural lesson

Almost every serious finding sits *between* layers, not inside one:

```
Core projection      ↕ UI manifest contract
Module admin status  ↕ UI actionability
Workspace state      ↕ unit/map state
Resource identity    ↕ AI context handoff
Source domain        ↕ module usage
Capability decl.     ↕ project special-case implementation
```

That is useful information about architectural maturity: the components are
solid, so the next engineering phase should focus on **making boundaries
impossible to disagree across** — more invariants and shared contracts, not more
features.

---

# 31. Remediation order

1. **Fix the manifest interface contract.** Introduce manifest v3, make Core own
   it, update UI, return exact-head UI CI to green.
2. **Fix project capability contract divergence.** Eliminate or properly contract
   the project special cases.
3. **Normalize Algo2 operational state.** Blocked workspace → paused unit/map;
   preserve the reinstatement plan; add a cross-layer invariant.
4. **Stop Home interpreting administrative `module.status` as actionability.**
   Project operational state from Core.
5. **Fix source domain projection.** Stop module/collection use from silently
   redefining intellectual domain membership.
6. **Send structured resources to the external agent.** Preserve resource ID,
   source ID, label, locator, triage and target.
7. **Fix "By current use" to use `source_to_modules`.**
8. **Render resource-specific feedback as resource-specific feedback.**
9. **Fix Home local-date calculation and priority-order "Continue elsewhere".**
10. **Update ADR-007 and minor ADR-009 historical labeling.**
11. **Add notes/concepts to global structural search.**
12. **After behavior stabilizes, extract a typed UI projection/model layer.**
13. **Then consolidate the working branches into protected, discoverable stable
    branches and tag a coherent Core/UI release.**

**Items 12–13 must not precede the behavioral bugs.**

---

# Final judgment

LearningOS is **not currently release-clean**, because UI CI is red, the manifest
contract is genuinely inconsistent, Algo2's operational state is contradictory,
and several new ADR-009 semantics are lost at boundaries.

The system itself remains **well architected, unusually disciplined for a
personal knowledge system, and mature enough that most defects are integration
invariants rather than fundamental design mistakes.**

The pieces hardest to retrofit later are already good — canonical ownership,
stable identities, closed schemas, format history, migration fixtures,
transaction receipts, optimistic concurrency, rollback, deterministic
projections, external-agent boundary, dumb presentation layer. The weaker pieces
are comparatively fixable — cross-repo interface versioning, lifecycle
normalization, projection semantics, UI interpretation, branch/release
governance, typed consumer adapters.

**Recommendation: do not redesign.** Declare a short **"integrity consolidation"
phase**, fix the P0/P1 items, make both repositories green simultaneously, then
freeze architectural work for a while and use the system. Done correctly, overall
engineering quality should move from roughly **8.7–9.0/10** to about **9.2/10**,
with remaining debt mostly ordinary maintainability work.

---

# Session note — 2026-08-08

Remediation could not begin: the operating sandbox was wedged
(`No space left on device` at VM boot), leaving no shell — no `git`, no `pytest`,
no `make check`, no `npm run build`. Aram's own machine was verified healthy
(212 GB free). Nothing in either repository was modified in that session; this
file is the only artifact.

**Standing constraint for UI work (Aram, 2026-08-08):** new or restructured UI
surfaces are to be designed with the Figma plugin *before* code is written —
specifically the faceted Library entrances (#25), the search taxonomy (#12) and
the feedback-vocabulary menu (#13). Pure defect fixes that do not change layout
(#9 local date, #8 feedback label resolution) may go straight to code.

**Cold-start next session:** items 1–2 first (manifest contract v3, then the
project capability path). Both are verifiable by the existing test suites, and
item 1 is the release blocker.

---

# Remediation log

Findings above are preserved as written. This section records what was done
about them, and — where it matters — what has not yet been proven.

## Items 1–2 — 2026-08-08, **VERIFIED — both repositories green simultaneously**

The sandbox was wedged again in the following session (identical
`No space left on device` at VM boot), so both items were authored with no shell
at all — no `git`, no `pytest`, no `validate.py`, no `npm` — and then run by
Aram on his own machine.

| | result |
|---|---|
| `tools/manifest_contract.py` (real repository, not the fixture) | v3 matches 26 top-level keys |
| `tools/validate.py` | **0 errors, 0 warnings** |
| Core `pytest` | **259 passed**, 1 skipped (was 240) |
| UI `npm run check` | **green** — build, typecheck ×2, contract check, 22 module tests, full dashboard + AI-action suites, host surface, deterministic build |
| new cross-repo check | `contract: mirror of core v3 verified` |

That clears the release blocker: UI CI is no longer red, and the manifest
contract is consistent across both repositories.

One correction landed on the way: the hand-written `history` entry used a plain
YAML scalar containing `": "`, which does not parse. Bumps go through
`yaml.safe_dump`, so the tool would not have produced it — only the
hand-authored baseline had the flaw.

Two claims that were made and should NOT be read as verified: the `git diff
--stat` "generator is a no-op" check was mis-specified (it diffs against HEAD,
so it cannot answer that question). What does hold is
`test_payload_schemas_match_the_cli_parser` plus the new assertion on the exact
`oneOf` shape, both of which passed.

**Item 1 — manifest contract v3.** The projection contract now has a producer-side
owner, which is the actual root cause the finding names.

- `system/contracts/manifest-contract.yaml` — new. Declares v3 and the exact
  key sets, with a history entry recording the v2 baseline retroactively.
- `learning_os/contracts/manifest_contract.py` — new. `build_manifest` calls
  `enforce()` on every build and refuses to publish a shape the contract does
  not declare, so drift fails in Core's own run rather than downstream.
  `_generated.contract_version` is now *read* from the contract, never
  hardcoded: one source for the version announced and the shape declared.
- `tools/manifest_contract.py` — new CLI: check, `--show`, `--bump --note`.
  `--bump` builds with enforcement off, which is the escape hatch the
  chicken-and-egg otherwise creates.
- `tests/test_manifest_contract.py` — new, including a reproduction of this
  finding: add a top-level key without bumping, and the build refuses.
- Validator gained `MANIFEST-CONTRACT-UNREADABLE` — deliberately shallow, since
  proving a *match* means building a manifest, which does not belong in a
  pre-commit hook.
- UI mirrored: `contracts/manifest-v3.lock.json`, `CONTRACT_VERSION`,
  `MANIFEST_CONTRACT_VERSION`, `ManifestV2.topics`, fixture vault, and the two
  fail-closed tests. `check-contract.mjs` now also verifies the mirror against
  Core's declaration when Core is checked out beside it — a partial answer to
  finding #18, not a replacement for it.

Two things surfaced that the finding did not mention. The UI lock never listed
`workspace_to_modules` / `workspace_to_units`, which Core has emitted since the
v2 baseline — nothing had ever compared the lock against a real Core build, so
the omission survived. And three separate contracts share the field name
`contract_version` (operator v2, record format v4, manifest v3); that collision
is a plausible contributor to the original mistake and is now commented at each
site.

`src/contracts/manifest-v2.ts` keeps its filename at v3. Renaming it touches
~20 import sites and belongs to remediation item 12, which must not precede the
behavioral fixes.

**Item 2 — project capability path.** The gateway special case is gone;
`project.create` / `project.update` dispatch like every other capability.

The finding leaves open which side to move. Making the gateway file-based would
force an agent holding a project record to invent a temporary file, so the
inline object was kept and *declared* instead: `project-create` / `project-update`
now take `--file` or `--project` as a required mutually exclusive group, and
the generated schema says so. That needed two small extensions to the schema
generator — an object-typed argument (`json_object`) and `oneOf` emission for
required mutually exclusive groups. No other command uses such a group, so no
other generated schema changes.

The payload schemas were hand-written to match what the generator should
produce; running `tools/generate_capability_schemas.py` must be a no-op, and
`git diff` afterwards is the check on that.

`test_capability_dispatch.py` no longer excludes the two project capabilities
from the round-trip assertion — that exclusion was the finding's own footprint
in the test suite.

**Gap worth naming.** The new manifest contract locks *top-level* keys, the
`_generated` block and the index tables. It says nothing about the fields inside
a projected record, so item 4 below adds three fields to every module record
without tripping it. That is the right granularity for now — locking every
record shape would duplicate the canonical schemas — but nobody should read the
contract as protecting record fields, because it does not.

## Items 3–4 — 2026-08-08, **VERIFIED — both repositories green**

Written in the same shell-less session as items 1–2 (fifth identical
`No space left on device`) and run by Aram on his own machine.

| | result |
|---|---|
| `tools/validate.py` before and after regeneration | **0 errors, 0 warnings** |
| Core `pytest` | **275 passed**, 1 skipped (259 + exactly the 16 added: 4 lifecycle, 12 module-lifecycle) |
| UI `npm run check` | **green**, including the new non-actionable-module case |

Two corrections on the way, both mine: `StudyMap` is a plain record holder with
no `status` property (unlike `Workspace` and `LearningPath`), and the migration
preservation bug below.

**Still unproven:** the intended *behavioural* change. That Algo 2, PPDS and the
IUG seminar disappear from Home's "Continue elsewhere" while M2, AML, AMLS, the
thesis, Python and the bridges module remain is a claim about live data, and the
UI suite only exercises the synthetic fixture. It wants one look in Obsidian.

**Item 3 — Algo2 lifecycle.** The module stays `enrolled`; there was no
university withdrawal and the record should not pretend otherwise. The
operational layers move together: `unit-algo2-exam-prep` and
`study-map-algo2-exam-prep` go `ready` → `paused`, the workspace stays
`blocked`.

The stage underneath is deliberately untouched — still `pending` with
`scope_triage: required-now`. Inside a *paused* map that reads correctly: it
says what comes first when this resumes, which is what the preserved
reinstatement plan is for. It was only contradictory while the map claimed to be
ready.

`check_lifecycle_coherence` makes the class of state impossible:
`LIFECYCLE-BLOCKED-UNIT` and `LIFECYCLE-BLOCKED-MAP` fire when a unit is
`ready`/`active` while every active workspace attached to it is blocked. The
join is read from both sides, so a one-sided edit can only add an unblocked
context and relax the rule, never invent a failure. A unit worked in two
workspaces, one blocked, is ordinary and untouched.

The audit asked for an explicit exception hatch. **Not added** — no real case
needs one, and an unused escape route in a lifecycle rule mostly invites
silencing the rule instead of fixing the state. If one appears, an optional
`lifecycle_exception` on the unit is the shape, with a schema bump so the
exception is itself declared. Recorded here as a deliberate deviation.

**Item 4 — the two state machines.** Core now projects
`administrative_status`, `operational_state` and `is_actionable` on every module
record; `status` stays exactly as authored. Operational state is derived from
the units, not from the module's own field, because a module cannot be active
while everything under it is paused.

Home consumes `is_actionable`. Its old filter was worse than the audit
recorded: it excluded `'complete'` while module records use `'completed'`, so it
had never excluded anything at all.

Expected effect on live data — Algo 2 and PPDS and the IUG seminar drop out of
"Continue elsewhere" (all units paused); M2, AML, AMLS, the thesis, Python and
the bridges module stay. That is the whole intended behavioural change, and it
is the thing to eyeball in the UI after the suites pass.

Splitting `status` itself into two fields remains the longer-term fix and a
breaking change to every stored module record; it is not attempted here.

**A latent bug the pause surfaced — not in the audit.**
`test_live_migration_is_idempotent_in_dry_run` failed, wanting to write `ready`
back over the paused Algo 2 unit and map. The cause was in
`tools/migrations/curriculum_v2.py`: AML, M2 and AMLS are protected by
`preserve_existing_units` — its docstring states the rule, that partitioned
units become canonical after the first seed and a re-run must preserve later
refinement — but **Algo 2, PPDS and the IUG seminar were seeded
unconditionally**. Any hand refinement of those three would have been silently
reverted by an `--apply` re-run; nothing would have reported it, because the
seed and the disk had simply always agreed. They are now preserved like the
rest. The pause was the first refinement any of them had ever received.
