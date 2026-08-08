# ADR-009 — Faceted Library and stable resource identity

**Date:** 2026-08-08
**Status:** **proposed** — designed and costed, deliberately not implemented.
**Supersedes:** nothing. Extends ADR-007 (subject taxonomy) and the two items
ADR-008 left open.
**Decision gate:** after the AMLS sitting. Nothing in this ADR is on the critical
path to an exam.

## Context

ADR-008 closed the semantic-residue problem but explicitly left two gaps open:
the faceted-library question, and per-resource feedback identity. Both were then
worked out in full. This ADR records the designs and what investigating them
revealed, so the work can start cold later without re-deriving anything.

The two proposals answer different questions and compose cleanly:

- **Faceted Library** — *what durable teaching objects do I have, and how do I
  find them?*
- **Resource identity** — *which exact part of one of those objects did I use,
  and what did I think of it?*

## Proposal 1 — Faceted / polyhierarchical Library

A hierarchical tree forces a source to declare one primary home. Goodfellow's
*Deep Learning* legitimately belongs to machine learning, optimization,
representation learning and generative modelling at once; ADR-007's subject tree
is a large improvement on the old semester/module folders but still asks for a
single placement. The proposal: **one identity, many classifications**, with
physical storage reduced to `materials/sources/<source-id>/` and every
intellectual organization generated as a projection.

Controlled facets, not free tags — a tag soup decays into
`deep-learning / DL / neural-networks / NN / advanced / advanced-reference` and
takes the organization with it. Roughly 8–10 domains, 20–40 topics, small
closed role and form vocabularies. Fine granularity stays with the concept
graph: *Deep Learning* is a Library filter, *batch normalization* is a concept.

### Finding: four of the five facets already exist and are populated

This is the main reason to record rather than build. Measured 2026-08-08 across
239 source records:

| Proposed facet | Already in the repo as | State |
|---|---|---|
| `domains` | `thematic_group_ids` (ADR-007) | all 239 tagged; ML 73, Mathematics 65, Software 54, Algorithms 32, ML Systems 17, Data Systems 14, Optimization 13, Method/Admin 7 |
| `form` | `type` | book 95, course 38, website 26, video 24, documentation 20, other 17, paper 11, lecture 5, software 3 |
| `roles` | `evaluations[].roles` | 410 assignments: first-learning 142, review 82, derivation 51, reference 35, exercise 33, implementation 33, intuition 26, mock-exam 8 |
| `used_by` | module source-maps + unit/stage resources | derivable today, no new field |
| **`topics`** | — | **the only real gap** |

So the faceted Library is **mostly a view problem, not a data-model problem**.
The `[Topics] [Purpose] [Format] [Current use]` browser can be generated almost
entirely from fields already on disk. The "sea of ML" it is meant to fix is
real and measured: 73 sources under one heading, 65 under another.

`lifecycle` is the partial fifth: `ml-broaden-later` currently encodes "study
this later" as a hand-maintained collection, which is a temporal intention
wearing a shelf's clothes. It should become a field and be generated across all
domains.

### Scope note on collections

16 collections exist. The rule from the original analysis holds and should
survive this change: keep a hand-maintained collection only when **the ordering
itself carries human meaning** ("AML recommended learning sequence"). Anything
computable from facets — "all ML books" = `domain: machine-learning` +
`type: book` — becomes a generated view. Several current bookshelves are
computable and would be retired into projections.

### Implementation sketch

1. Add optional `topics` to `sources.schema.json` with a closed vocabulary in a
   new `sources/topics.yaml`; do not duplicate the role/evaluation metadata that
   already exists.
2. Generate faceted Library views. Change nothing physical.
3. Only if the views prove out, flatten storage to
   `materials/sources/<source-id>/`. `material://` already resolves by source
   ID, so this is a move, not a redesign.

The honest cost is step 1: writing a controlled topic vocabulary and applying it
across 239 sources is a judgment-heavy pass, not a script.

## Proposal 2 — Stable per-resource IDs

A `source` sometimes denotes a **bundle**. `source-amls-ss26-lectures` currently
backs **96 distinct stage resources**: 60 curated primary papers, 13 full
bibliographies, 12 decks/recordings, 11 others. A stage resource carries
`kind / label / source_id / locator / url / vault_path / scope_triage` — and no
identity of its own.

The consequence is a representational gap, not an inconvenience. If Lecture 03
yields *SystemML: extremely useful*, *SPOOF: good implementation intuition*,
*SPORES: too advanced for now*, *TASO: unnecessary for the exam*, all four
judgments collapse onto one `source_id` and cannot be told apart.

Registering all 60 papers as Library sources is the wrong fix and is rejected:
it inflates the registry, duplicates course context, multiplies evaluation work,
degrades navigation, and promotes locally-selected papers into global canon
purely because the schema cannot address them. That is backwards.

### The distinction to encode

- **Source** — a stable teaching object in the global Library (ISLP, Goodfellow,
  the AMLS SS26 course, DDIA, CS229).
- **Resource** — a specific actionable item exposed from a source in a learning
  context (ISLP §3.2, the AMLS L03 SystemML paper, Lecture 03's deck, CS229
  Problem Set 2 Q4).

```yaml
- id: resource-amls-l03-systemml
  kind: read
  source_id: source-amls-ss26-lectures     # still required, for provenance
  label: SystemML — Declarative Machine Learning on Spark
  locator: AMLS paper reading list · Lecture 03
  scope_triage: required-now
```

Feedback then targets `resource_id` (with `source_id` kept for provenance), and
the field is better named `resource_feedback`. Three claims that are currently
collapsed become separable, and should be:

| level | example claim |
|---|---|
| source | "Goodfellow is rigorous but slow for first exposure." |
| resource | "§6.5 is excellent for the backprop derivation." |
| stage evidence | "This section closed my specific L09 gap." |

### The restraint that keeps it from becoming ontology bloat

Give stable identity only to items that are **reused across plans or judged
independently**: papers, chapters, course lectures, exercise sheets, problem
sets, videos, notebooks, official mock exams. Never pages, paragraphs, formulas
or sentences — those stay locators.

```
source-goodfellow-dl → resource-goodfellow-ch06 → locator: §6.5 Backpropagation
```

A secondary payoff: the same ISLP section cited by AML L03, the M2 regression
bridge and a future module could point at one `resource-islp-3-2-…`, so feedback
accumulates on the section rather than on the whole book.

## Decision

**Both proposals accepted in principle; neither implemented now.** Recorded as
`proposed` and gated on the AMLS sitting.

## Sequencing — and a disagreement worth preserving

The proposal recommends faceted Library first, because it fixes a global
usability problem. That is right on a long horizon.

**The operator's counter-recommendation is to do narrow resource identity
first**, for a timing reason rather than an architectural one. The next 19 days
run 13 AMLS lectures and 60 papers — exactly when per-paper judgments are
generated, and exactly the judgments that currently have nowhere to land. The
faceted browser improves browsing that can happen any time; resource IDs capture
information that is otherwise produced once and lost.

If resource identity is done first, AMLS is also the ideal pilot: one bundle,
96 resources, an already-verified inventory, and a mechanical ranking from
ADR-008 to attach ids to.

Both orderings are recorded because the argument, not the conclusion, is what a
later reader needs.

## Why neither is being built tonight

ADR-008 deferred the faceted library specifically because of the exam, and
nothing has changed except that the design got better. Faceted metadata means
writing a controlled vocabulary across 239 sources; resource identity means a
schema bump to contract v3, a new fixture, and touching 96 resources. Neither is
on the critical path to passing AMLS on 2026-08-27, and both are cheaper to do
well when rested.

## Consequences

- No code, schema or data changed by this ADR. `make check` unaffected.
- Data contract stays at v2. Implementing proposal 2 will require v3 plus a
  frozen `tests/fixtures/formats/v3/`, per the README procedure.
- Both items are removed from ADR-008's "deliberately not done" list in spirit;
  that list now points here.
- Neither proposal adds intelligence to the Core, which is the strongest
  argument for both: the Core stores identity, facets, relations and feedback;
  the agent decides which apply; the UI browses. The three-layer invariant is
  untouched.

## Open questions for implementation

1. Is `topics` flat, or nested under `domains`? Nesting reintroduces the
   single-placement problem one level down.
2. Does `lifecycle` become a source field, retiring `ml-broaden-later`?
3. Which of the 16 collections are computable from facets and should be retired
   into generated views?
4. Does `source_feedback` get renamed to `resource_feedback`, or gain
   `resource_id` alongside the existing shape for compatibility?
5. Do stage resources get ids everywhere, or only inside bundled sources until a
   second real need appears?
