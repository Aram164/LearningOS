# ADR-016 — The Atlas is a focused prerequisite graph, not a crossing table

**Date:** 2026-09-04 · **Status:** accepted (Aram)

**Supersedes nothing. Amends:** ADR-015 decision 5 only — the default the
screen opens on. Decisions 1–4 of ADR-015 remain in force and this design
depends on all four. **Extends:** ADR-005 (domain atlas), ADR-006 (the
projection is Core's, the rendering is the UI's).

## Context

ADR-015 published `module_concept_edges` and replaced the Domain Atlas screen
with a Module × Concept crossing table. That was the right move for the
question it was asked: *this concept appears in several modules — are they the
same thing, and can one week's work serve all of them?* The table answers it
directly, and 36 of 138 concepts currently carry evidence from more than one
module, 27 of them across AML and Statistik & Datenanalyse.

It is not the question a learner opening the Atlas usually has. That one is
narrower and comes first: **what must I understand to derive this?** The
crossing table cannot answer it, because module membership is not a learning
order. The repository already holds what does answer it — 99 authored concept
relations, of which 67 are `requires` or `builds-on` over 79 concepts — and
nothing rendered them.

Two further facts made the shape of the answer clear rather than optional.

**The strict subgraph is acyclic today, and nothing enforces that.** It is a
property of the current data, not an invariant. A prerequisite graph that may
contain a cycle cannot be presented as a learning order at all.

**The canonical sentence and the useful arrow point in opposite directions.**
Authoring reads subject to object: *logistic regression requires conditional
probability*. Study order reads the other way: *conditional probability →
logistic regression*. Both are correct and the interface owes the reader both.

## Decision

**1. The Atlas is a focused graph, and the focus is one concept.** The screen
answers a question about a selected concept — direct prerequisites left, the
concept centred, direct dependents right — rather than rendering the corpus.
Depth 1 by default; deeper is an explicit control, and whatever a depth bound
excludes is **counted and named, never silently dropped**.

**2. Two relation layers, and only one of them orders anything.**

- **Strict:** `requires` and `builds-on`. This layer alone defines learning
  order and path derivation.
- **Semantic:** `derives`, `generalizes`, `contrasts-with`, `equivalent-to`,
  `applies-in`, `motivates`. These explain the knowledge. They are drawn
  differently, they may cycle, and they never reorder a prerequisite.

A relation type is never promoted between layers to make a graph look better
connected.

**3. Arrows show study order; the inspector states the canonical sentence.**
Every visible strict edge points prerequisite → dependent, and the inspector
carries both readings: *"Logistic regression requires conditional probability"*
and *"Learn conditional probability before logistic regression."* Neither
direction is inferred; both are renderings of one authored row. The generated
Canvas is corrected to match, since it is built from the same relation set and
two projections of one fact must not disagree.

**4. Acyclicity of the strict subgraph is a Core invariant.**
`REL-PREREQ-CYCLE` fails validation on any cycle among `requires` /
`builds-on`, reporting one deterministic path. Semantic cycles remain valid.
Without this the UI would be presenting an order the data does not guarantee.

**5. Modules are lenses and evidence, never an axis of the graph.** A module
chip says where a concept is taught and opens the exact stage or knowledge-node
evidence that licenses the claim. No edge is ever derived from shared module
membership. This is ADR-015 decision 2 applied to a different surface.

**6. The crossing becomes a lens, not a sixth view.** Cross-module bridges and
Diagnostics are lenses inside the one Atlas route, reached from the same
screen and the same route state. ADR-015 decision 4 rejected adding a sixth
Atlas view and that still holds: this adds none.

**7. The default the screen opens on moves — this is the amendment.** ADR-015
decision 5 opens on concepts carried by more than one module. The Atlas opens
instead on **search and recently visited concepts**, with Cross-module bridges
and Diagnostics as named entry points beside it.

The reason ADR-015 gave for its default was that shared concepts are "the
question". That was true of a crossing table whose only job was to answer it.
This screen answers a narrower one, and opening on a list of 36 bridges answers
a different question before it has been asked. The bridges are one control
away and are not diminished; they stop being the greeting.

Nothing else in ADR-015 changes. Edges rather than tables, evidence licensing
every cell, indexes derived from the edges, and no sixth view all still bind.

**8. Route state is small, validated, and single-field.**

```text
{ name: "atlas", concept?, module?, lens?, depth? }
lens ∈ { prerequisites, path, semantic, bridges, diagnostics }
```

One `lens` field carries all five values even though the shell splits them
across two controls, because two fields would make `lens=prerequisites` with
`scope=diagnostics` expressible and it means nothing. Unknown values fall back
to the default rather than failing.

**9. The first release is read-only.** No governed capability exists for
writing `knowledge/concept-relations.yaml`, and the Garden's
`relationship.create` governs a different record family. The inspector may say
that no governed relation editor is available; it gets no dead "Add
connection" affordance. Relation authoring is a later programme with its own
Core command, evidence requirements, preview and receipt.

**10. Figma and the native Obsidian views are projections, never canon.** The
design file is a handoff surface. The generated Canvas and Obsidian's own graph
remain useful secondary views. Canonical meaning stays in Core.

## Consequences

- `REL-PREREQ-CYCLE` is a new error. The current registry is already acyclic,
  so it lands green and stays a guarantee rather than a repair.
- The generated Canvas changes direction for strict edges. Edge **identity** is
  unchanged — the id keeps its canonical `from--type--to` spelling — so the
  diff is a direction fix and not a rewrite.
- The UI reads the top-level `relations` rows rather than
  `backlinks.concept_relations`, which carries neither `context` nor `source`.
  No manifest version bump: v8 already publishes everything this needs.
- Provenance has **three** states the interface must keep apart — resolved,
  undocumented (the schema permits an absent `source`), and unresolved (a
  citation that does not resolve). The first two are normal; the third is named
  exactly and never substituted.
- Absence stays absence. A concept with no authored prerequisites says so; it
  is never called "foundational", and a leaf is never called "advanced".
