# K3 — the Obsidian atlas against Core's projection (GLM 5.8 Flash)

**Status: DONE — all seven areas run, 0 findings, 6 test files green, coverage
gaps and observations recorded.**

## Setup (recorded per CAMPAIGNS.md "Clones and base")

- Clone root: `/Users/aramaljanadi/los-glm-K3-2026-10/` — full clones from
  GitHub (`Aram164/LearningOS`, `Aram164/learningos-obsidian-ui`), never the
  live checkout.
- Core pin: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`, fetched from branch
  `codex/operator-developer-docs-20261025`, checked out detached. HEAD
  re-verified after the final run: exact match.
- UI pin: `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`, detached. HEAD
  re-verified after the final run: exact match.
- No push, no branch on GitHub, no workflow dispatch, no CI. The clones are
  otherwise pristine (`git status --porcelain` shows only the six new
  untracked `tests/k3-*.js` files in the UI clone; the Core clone is clean at
  the pin).
- Data: fixtures only (store stubs shaped after `tests/test-atlas-graph.js`).
  No live vault opened, no learner data read, Obsidian app never launched.
- Reading route followed: UI `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`;
  Core `system/DEVELOPER.md`; ADR-016 (decisions 1–8), ADR-017 (decisions 1–4);
  `system/contracts/capabilities.yaml` entries for `atlas.question.save` and
  `concept.relations.change` (read-only); Core handler
  `tools/learning_os/app/handlers/atlas.py` and failure mapping
  (`domain/failures.py`, `app/outcomes.py`) read to pin the producer boundary.

## Test conventions

- Node test files in the UI clone at `tests/k3-*.js`, in the style of
  `tests/test-atlas-graph.js`: plain `node:assert/strict`, the repo's own
  source-module loader (`tests/source-module-loader.js`), store stubs carrying
  the ManifestStore read boundary (`get`, `of`, `modules`,
  `moduleConceptEdges`, `relations`).
- `atlas-view.ts` and its import graph load through the same loader with two
  inert host mocks — `obsidian` (`ItemView`, `Notice`, `Modal`, `setIcon`,
  `TFile`) and `electron` (`webUtils`, `shell`, pulled by `src/components.ts`).
  The loader's `mocks` parameter is the sanctioned seam. `Notice`
  construction is captured so refusal surfacing can be observed end to end.
- The UI has no test-file registry (unlike Core's `tests/group_map.py`);
  `tests/` is the sanctioned non-runtime location per UI `ARCHITECTURE.md`
  dependency rule 4 and no gate enumerates it, so the K3 files are run
  directly, one file at a time, and are deliberately NOT wired into
  `package.json` (they are campaign reproductions, not release gates).
- Gateway interactions use the real `GatewayClient` over a stubbed `runLos`
  that records every envelope and answers with V2 confirmations/refusals that
  echo the request identity — the same harness shape
  `tests/test-runtime-modules.js` uses.

## Baseline

- `npm install` in the private UI clone (the pinned tree has no vendored
  `node_modules`; without it even `tests/test-ci-policy.mjs` cannot load
  `typescript`).
- `node tests/test-atlas-graph.js` → PASS before any K3 file was written, and
  again in the final sweep. [logs/test-atlas-graph.out]
- `node tests/test-ci-policy.mjs` → PASS after install.

## Areas — final results

| # | Area (campaign spec) | Test file | Result |
|---|---|---|---|
| 1 | Route state, unknown values fall back (ADR-016 d8) | tests/k3-route-state.js | PASS |
| 2 | Focused graph: depth 1 default, exclusion counted+named (d1) | tests/k3-focused-graph.js | PASS |
| 3 | Layers: only strict orders; semantic never reorders path (d2) | tests/k3-focused-graph.js | PASS |
| 4 | Direction: strict arrow prerequisite→dependent; both sentences (d3) | tests/k3-direction-inspector.js | PASS |
| 5 | Modules are lenses; no edge from shared membership (d5) | tests/k3-module-lenses.js | PASS |
| 6 | Authoring: exact old rows, no AI, Core refusals surface (ADR-017 d1+d3) | tests/k3-authoring.js | PASS |
| 7 | Questions: save creates note, never touches note `state` (ADR-017 d4) | tests/k3-questions.js | PASS |

Final sweep (all exit 0, output in `logs/`):

```
cd /Users/aramaljanadi/los-glm-K3-2026-10/obsidian-ui
node tests/test-atlas-graph.js        # baseline
node tests/k3-route-state.js
node tests/k3-focused-graph.js
node tests/k3-direction-inspector.js
node tests/k3-module-lenses.js
node tests/k3-authoring.js
node tests/k3-questions.js
```

## What each area actually asserted

**1 — Route state** (`k3-route-state.js`; contract:
`src/contracts/route-v1.ts`, consumer: `AtlasView.adopt`; ADR-016 d8).
All six contract lens values survive `asAtlasLens`; 17 junk shapes (strings,
numbers, arrays, objects, functions, `NaN`, `null`, `undefined`) fall back to
`prerequisites` without throwing. Depth: `1`/`2` survive, string `'1'`/`'2'`
coerce, 15 junk shapes fall back to `1`. The view adopts garbage state
(`{concept: 'x', lens: 'crossing-table', depth: 'seven'}`) to the default
lens/depth with the valid concept carried; non-string non-null concept/module
values keep the previous selection (never garbage, never a throw); `null`
concept survives (entry browser). The adopted state is exactly the four
ADR-016 d8 fields — `concept`, `module`, `lens`, `depth` — and no second
lens-ish field (`scope`) exists: `lens` is one field.

**2 — Focused graph** (`k3-focused-graph.js`; contract:
`src/features/atlas/graph.ts` `neighbourhood`, `src/features/atlas/
presentation.ts` `conceptPlaneSlice`; ADR-016 d1). Omitting depth means depth 1
(`.depth === 1`). On a chain e←c←b←a with sibling d and semantic/unrecognized
neighbours of a: what the bound excludes is named with id AND label
(`beyond.prerequisites === ['Beta']` at depth 1 from e), `beyond.total` is the
sum of the four named remainders, and raising the bound consumes exactly the
named remainder (depth 2 names `a`, depth 3 empties it). The dependent
direction names and consumes the same way. A semantic neighbour the lens does
not draw is named (`beyond.semantic`), and turning the semantic lens on adds a
band without re-laning the strict nodes. An unrecognized-type neighbour is
named at every depth and never drawn or traversed at any depth bound. The
crowded-plane slice keeps the invariant "drawn or in the named remainder — none
vanish" (41 nodes: slice.nodes + slice.omitted = view.nodes), while the text
scope (`view.strictEdges`) stays unshortened at 40.

**3 — Layers** (`k3-focused-graph.js`; contract: `graph.ts`
`relationLayer`/`strictPath`; ADR-016 d2). Vocabulary is exactly
`{builds-on, requires}` strict and the six semantic types; five near-miss
strings (`'needs'`, `' DERIVES'`, …) are promoted by nothing. The
per-concept indexes carry only their own layer. A five-node chain threaded
with all six semantic relations across the layers produces a `strictPath`
byte-identical (layers, edges, total, ancestors) to the bare chain — semantic
edges never reorder the path lens. A semantic 3-cycle is valid and blocks
nothing; a strict 3-cycle blocks with one deterministic loop.

**4 — Direction** (`k3-direction-inspector.js`; contract: `graph.ts`
`toEdge`/sentences, `narrative.ts` `relationSentences`; ADR-016 d3). For every
strict edge: authored object = prerequisite = arrow tail (`studyFrom`), authored
subject = dependent = arrow head (`studyTo`); placement agrees (prerequisite
column −1, dependent +1); every derived path edge walks tail→head. The
inspector's sentence source carries both readings of one row:
`['Logistic regression requires Conditional probability.', 'Learn Conditional
probability before Logistic regression.']`. Semantic rows keep the authored
direction, invent no order, and render one sentence; unrecognized types render
under the authored verb with no order. A reverse-authored row
(`prerequisite requires dependent`) renders both readings of exactly what was
authored — the interface normalizes no claim into a plausible shape.

**5 — Modules are lenses** (`k3-module-lenses.js`; contract: `graph.ts`
`modulesFor`/`evidenceFor`/`bridges`; ADR-016 d5). Chips list only evidenced
modules (an `evidence: []` row licenses no chip — the same refusal Core makes
upstream), actionable first then by label, and each chip's evidence is the
exact licensed rows (knowledge-node and stage-concept fixtures deep-equal,
including unit/stage/map/node ids). The only edges on the graph are the
authored relation rows; every edge in every per-concept adjacency is an
authored row; two concepts sharing two modules have no adjacency of any layer.
A bridge lists its modules with per-module evidence and is not a relation
between the modules. Determinism holds under row reversal.

**6 — Authoring** (`k3-authoring.js`; contract:
`src/features/atlas/relation-editor.ts`, `src/views/atlas-view.ts`
`changeRelations`, `src/gateway-client.ts` `changeConceptRelations`, Core
capabilities.yaml `concept.relations.change`; ADR-017 d1+d3). `rowOf` drops
projection-added nulls (absent context/source are absent keys, never explicit
nulls — Core matches old rows exactly); `editDraft` binds `original ===
rowOf(edge)`; `draftRow` applies the same discipline to the new row. The write
path (view → real GatewayClient → stubbed CLI) sends exactly one envelope:
capability `concept.relations.change`, payload
`{change: {operations}}` deep-equal to the authored operations (replace with
the exact old row; remove with the exact stored row including context/source),
guarded by `expected_revisions = {'registry-concept-relations': <rev>}` — the
artifact id as Core names it. With settings carrying no AI provider at all, the
same batch runs and the capability list is exactly
`['concept.relations.change']` — no AI capability in the path (ADR-017 d3
acceptance). A Core refusal (V2 `ok:false`, code `VALIDATION_FAILED`, message
"prerequisite cycle: concept-a -> concept-b -> concept-c -> concept-a") is
surfaced, not swallowed: `changeRelations` does not reject, the draft survives
with `editor.error` set to Core's own reason, a `Notice` also fires, nothing is
selected, and the view is redrawn for correction. The UI-side pre-flight
(`draftRefusal`) refuses the same three classes before the write: duplicate
identity, unknown endpoints, strict cycles — including a loop closed *through
rows the edit does not touch* — while correctly allowing the reversal of a
single edge in an edit (the 2026-09-05 audit F11 regression) and any semantic
arrangement.

**7 — Questions** (`k3-questions.js`; contract:
`src/features/atlas/questions.ts`, `atlas-view.ts` `setQuestionState`,
`gateway-client.ts` `saveAtlasQuestion`, Core capabilities.yaml
`atlas.question.save` + handler `atlas.py:atlas_question_save`; ADR-017 d4).
The question lifecycle is read only from the `atlas_question.state` block
field: a note at `state: mature` (note lifecycle) with block `open` collects as
`open`; three notes differing only in note-level `state` collect identically;
an unknown block state collects nothing. Targets are kept exactly: a question
on a removed relation (identity `concept-b--requires--concept-a`) reads
`targetPresent: false` and keeps its tuple; a question on a missing concept
keeps its target and reads missing — nothing retargets. A relation question
never appears as a question about its endpoint concepts. Resolving sends
exactly `{question: {id, state}}` guarded by the note's own artifact revision —
no wording, no target (Core's invariant "learner wording and original target
are preserved" makes those handler-owned). The passthrough method carries a
full creation payload (title/text/target, concept list or relation tuple)
byte-for-byte, so the producer's creation contract is reachable unchanged.

## Findings

**None.** Every proposed defect candidate was refuted against the pinned pair:

- During authoring, three assertions failed and each failure was my fixture's
  arithmetic, not the product's: remainder sort is by label (Delta before
  Gamma), open-question sort is by title ("What…" before "Why…"), and the
  module list sorts non-actionable by label (Quiet before Zeta). Each was
  fixed in the test, not in the product, and the final logs are all green.
- A deliberately wrong stub error code (`REL-PREREQ-CYCLE` as a V2 code) made
  the client classify the refusal as *ambiguous* and enter recovery. Reading
  Core (`domain/failures.py`: `ValidationFailed.gateway_code =
  VALIDATION_FAILED`; `app/outcomes.py` maps `gateway_code` into the V2 error)
  showed the real refusal of this capability travels as `VALIDATION_FAILED` /
  `INVALID_REQUEST` — both in the UI's `DEFINITIVE_NO_COMMIT_CODES`, both
  classified *refused* and surfaced. `REL-PREREQ-CYCLE` is complaint prose
  inside the message, not the envelope code. The stub was corrected to the
  real pair; no product defect.

## Coverage gaps

Nothing here is a finding; each names behavior this run could not exercise.

1. **The DOM rendering layer.** Every `src/features/atlas/` module and
   `src/views/atlas-view.ts` *loads* under the two host mocks — the loader
   could not load none of them, so there is no Obsidian-API load gap — but
   node tests do not render. Untested: `renderFocusedGraph`/`renderOutline`/
   `renderPath` (columns, remainder toggles, aria labels),
   `renderInspector`/`connectionRow` (the actual inspector row that joins the
   two sentences), `renderBridges`/`renderDiagnostics`, `renderAtlas` shell
   (lens tab switching), the relation editor's endpoint pickers, question row
   click-through, `mountEdges` arrow geometry, `browser.ts`/`domains.ts`
   rendering, `disclosure.ts`. The read-model and narrative sources those
   renders consume are fully covered above; the wiring between them is not.
2. **No UI affordance creates a question.** Exhaustive grep of the pinned UI:
   `atlas.question.save` appears only in `gateway-client.ts` (the passthrough
   method) and the `gateway-v2.ts` capability list; the only production caller
   is `setQuestionState`, whose payload is `{id, state}`. `atlas_question`
   appears only on the read side (`questions.ts`) and in generated contract
   types. Core's handler *does* create question notes (new questions require
   `title`, `text`, `target`; created as `role: question` with
   `atlas_question: {state: 'open', target}`; handler-owned note fields never
   touched). So area 7's "saving a question on a concept or a relation creates
   a question note" is proven here only at the passthrough level: the UI can
   resolve/reopen, and can carry a creation payload unchanged, but offers no
   affordance that authors one. ADR-017 decision 4 does not mandate a UI
   creation affordance (questions enter through the CLI's
   `atlas-question-save` today), so this is an absence to count, not a bug —
   and it is Aram's call whether the Atlas should grow one.
3. **`renderQuestionNote`/shell question bands** (resolution buttons, orphaned
   rows) are DOM-bound; only their data sources are covered.
4. **Fixture-vault end-to-end.** The K3 areas ran on store stubs in the
   style of `test-atlas-graph.js`. `tests/test-fixture-workspace.js` and the
   fixture-vault manifest were not re-run as part of K3 (they are part of the
   UI's own gates, not this campaign's focused node tests).

## Observations (not findings, recorded for Codex and Aram)

1. **The route contract carries a sixth lens value.** ADR-016 decision 8
   enumerates `lens ∈ {prerequisites, path, semantic, bridges, diagnostics}`;
   `src/contracts/route-v1.ts` adds `domains` (the ADR-005 domain atlas folded
   into the same route; `lenses.ts` navigates to it). No ADR text amends
   decision 8's enumeration. The one-field rule and the unknown-falls-back rule
   both hold for all six values; only the enumeration differs from the ADR's
   written set. UI `route-v1.ts` is the owning contract for the UI route, so
   this is a documentation/ADR bookkeeping note, not a defect.
2. **`asAtlasDepth` coerces strings** (`'2'` → `2`) because persisted Obsidian
   state carries strings; junk falls back to 1. Deliberate, documented in the
   crossing's docstring.
3. **Depth domain is {1, 2}** (`ATLAS_DEPTHS`), so a hand-written `depth: 3`
   deep link opens at depth 1, not depth 2. Consistent with "deeper is an
   explicit control" having exactly two stops at this pin.
4. **Refusal vocabulary** (verified across both repos for area 6): UI
   `DEFINITIVE_NO_COMMIT_CODES` ∩ Core's WriteRefused-family gateway codes are
   aligned for this capability; the relations refusals (duplicate, unknown
   endpoint, cycle) surface as `VALIDATION_FAILED`/`INVALID_REQUEST`, and every
   such code short-circuits to the *refused* outcome with the draft kept —
   never into the recovery/ambiguous path that would block the next write.

## Reproductions

- Reproduction files (the six test files) live in the private UI clone at
  `/Users/aramaljanadi/los-glm-K3-2026-10/obsidian-ui/tests/k3-*.js`; captured
  outputs of the final sweep are in this folder's `logs/`. There are no
  failing tests to package into `K3/<slug>/` — no findings.
- To re-run from scratch: clone both repos at the pins above, `npm install`
  in the UI clone, then run the seven commands listed under "Areas — final
  results".

## ASSUMPTIONS

- None outstanding. Every claim about the repository in this report was
  verified against the pinned clones by reading the cited file or running the
  cited command. Verification by Codex is expected per CAMPAIGNS.md; a
  worker's own judgment is provisional.
