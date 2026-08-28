# ADR-015 — The Module × Concept crossing is published, with its evidence

**Date:** 2026-08-28 · **Status:** accepted (Aram)

**Supersedes nothing. Extends:** ADR-005 (domain atlas), ADR-006 (interface
boundary — the projection is Core's, the rendering is the UI's).

## Context

The domain atlas (ADR-005) answers *what is in this domain*. It exists because
retrieval kept collapsing to the active workspace's domain, and it fixed that.

It does not answer the question a learner carrying four modules at once
actually has: **this concept appears in several of them — are they the same
thing, and can one week's work serve all of them?** Backpropagation and the
bias–variance tradeoff are both explicitly tagged in AML and Statistik &
Datenanalyse. Before this projection, the repository did not publish that
crossing, so the answer had to be reconstructed by hand whenever it mattered.

The crossing was not published because nothing had decided what would license a
cell. That is the whole difficulty: a Module × Concept table is trivial to
produce badly. Match on titles, or on shared words, or on note similarity, and
it fills up immediately with relationships nobody authored — and the cost of a
wrong cell is not a failing test, it is a learner planning one week of work on
the belief that two modules share ground they do not.

While building this, a second thing surfaced. `unit_to_concepts` and
`concept_to_units` have been published in the manifest since v2 and **have
always been empty**. They read only knowledge-map node `concept_ids`; no node
has ever carried one. Meanwhile 376 of 416 stages carry `concepts` tags,
covering 124 distinct concepts. Nothing caught it because an index derived
independently from the tree has nothing to disagree with.

## Decision

**1. Publish edges, not a table.** `module_concept_edges` is a top-level
manifest key: rows of `{module_id, concept_id, evidence}`, ordered by
`(module_id, concept_id)`. An interface pivots them into rows-and-columns
whichever way it wants; Core does not decide the layout (ADR-006).

**2. An edge requires explicit authored evidence, and carries it.** Two
sources, both authored by a person, both reviewable:

| kind | source | identity retained |
|---|---|---|
| `stage-concept` | a stage's `concepts` tag | unit, study map, stage |
| `knowledge-node` | a knowledge-map node's reviewed `concept_ids` | unit, node |

Nothing else licenses a cell. **No concept is ever inferred** from a title,
prose, a note body, a source evaluation, a shared word, or a similarity score.
The unit schema's phrasing for `concept_ids` governs the whole projection:
*absence means not mapped, never that no relationship exists.*

The evidence is not diagnostic metadata — it is the reason the feature is
allowed to exist. A cell the learner cannot interrogate is a claim they have to
take on faith, and this projection makes claims about how to spend their weeks.
`evidence` therefore has `minItems: 1` in the schema: an edge with no evidence
is an inferred edge, and the contract refuses to publish one.

**3. The four concept indexes come from the edges.** `unit_to_concepts`,
`concept_to_units`, and the new `module_to_concepts` / `concept_to_modules` are
all derived from `module_concept_edges` rather than recomputed. A cell in the
Atlas and a row in the indexes cannot diverge, because there is one computation.
This is what repairs the two empty tables: 0 → 52 and 0 → 124.

**4. The Atlas screen is replaced, not added to.** The existing route keeps its
place; the Domain Atlas landing becomes the crossing. A sixth view would leave
two atlases and no answer to which one to open — the failure ADR-005 was
written against, repeated one level up.

**5. Default to what is shared.** The screen opens on concepts carried by more
than one module (32 of 124 today), because that is the question. All 124 are one
toggle away. The generated `domain-atlas.md` stays reachable as a fallback
action; it is not the primary surface any more.

## Consequences

- Manifest contract **v8**. Additive, and it still bumps: consumers declare an
  exact version and fail closed. The UI lock moves in the same release.
- **The projection's reach is bounded by what is tagged.** Five of thirteen
  modules have no edges in the release snapshot, because their stages carry no
  concept tags. That is
  visible absence, not silence — and repairing it is authoring work on the
  stages, done on use, never a bulk backfill.
- Fixing the bump helper was a prerequisite. `bump()` inherited the previous
  version's `schema_path` and `schema_sha256`, so a v8 contract would have
  declared `manifest-v7.schema.json` and validated v8 output against the v7
  shape. It now selects the new version's schema, hashes it, and refuses to
  bump at all if that schema has not been written yet.

## Rejected

- **Inferring edges from note or source text.** The cheapest way to a full
  table and the reason not to build one. See decision 2.
- **A `concepts` field on the module record.** A fifth place to state something
  two authored places already state, with no way to keep it honest.
- **A sixth Atlas view.** See decision 4.
- **Backfilling stage concept tags to fill the empty five modules.** Authoring
  work with a real cost, unrelated to whether the crossing is published. Left
  to on-use repair.
