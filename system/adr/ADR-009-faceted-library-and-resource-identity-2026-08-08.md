# ADR-009 — Faceted Library and stable resource identity

**Date:** 2026-08-08
**Status:** **accepted and implemented** (same day, on Aram's instruction to
build rather than defer). Both proposals shipped; see *What shipped* below for
what was built, what was deliberately left, and the two design corrections that
only appeared once the data was touched.
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

## On the timing

This ADR was first written as `proposed`, with the argument that neither
proposal is on the critical path to passing AMLS on 2026-08-27 and both are
cheaper to do well when rested. Aram overrode that and asked for the build; the
reasoning is preserved because it was sound and may be the right call next time.
The mitigating fact is that resource identity turned out to serve the exam
directly — the per-paper judgments it captures are generated by the very study
the deadline is about.

## Consequences

- Data contract v2 → **v4** (two independent record-format changes). Frozen
  fixtures `v3` and `v4` added to `FORMATS`; `v1` and `v2` still validate
  unchanged, so both steps are backward-compatible.
- Both items are removed from ADR-008's "deliberately not done" list in spirit;
  that list now points here.
- Neither proposal adds intelligence to the Core, which is the strongest
  argument for both: the Core stores identity, facets, relations and feedback;
  the agent decides which apply; the UI browses. The three-layer invariant is
  untouched.

## What shipped

Built in the order this ADR argued for (resource identity first), not the order
the proposal recommended. Two contract bumps, because these are two independent
record-format changes: **v3** (resource identity) and **v4** (topic facet).

**Resource identity.** Optional `id` on study-map stage resources; optional
`resource_id` on `source_feedback` with `source_id` still required for
provenance. Applied to **95 resources** across the AMLS bundle — 60 paper
citations, 13 bibliographies, 12 decks/recordings, 10 official sample-exam
items. Two new validator rules, both negative-tested: `RESOURCE-ID-CONFLICT`
(one id, two different objects) and `FEEDBACK-RESOURCE` / -`SOURCE` (feedback
naming a resource that is not on its stage, or claiming the wrong source).
Fixture `v3` freezes the shape, including a *contradictory* pair of judgments
about two resources in one source — the exact case v1/v2 could not express.

**Faceted Library.** New `topics` facet with a closed 37-entry vocabulary in
`sources/topics.yaml`, validated by `REF-TOPIC` / `REF-TOPIC-DOMAIN`. New
generated view `generated/library.md` projecting all 239 sources five ways —
domain, topic, purpose, form, current use — with overlapping counts. Fixture
`v4`. Nothing moved physically.

### Two corrections the design did not survive contact with

**1. Identity belongs to the paper, not the citation.** The plan implied
`resource-amls-l03-systemml`-style lecture-scoped ids. But AMLS turns out to
have **58 distinct papers behind 60 citations**: *Attention Is All You Need* is
cited by both L04 and L07, and the Hidden Technical Debt paper by both L01 and
L02 (worded differently each time — "…in Machine Learning Systems" vs "…in ML
Systems", same URL, same vault path). Lecture-scoped ids would have minted two
identities per paper and scattered exactly the feedback this ADR wants to
accumulate.

So ids name the object: one id, cited from as many stages as like. The
uniqueness rule was rewritten accordingly — repeated ids are legal, but a
repeated id must not vary in `source_id`, `url` or `vault_path`. Labels are
deliberately excluded from that check, because the two Hidden Technical Debt
citations are worded differently and normalising them would be rewriting Aram's
prose to satisfy a linter.

**2. Not everything in a bundle is a teaching object.** One AMLS resource —
"Explain-back against the Lecture 02 deck" — got no id. It is an *activity*, not
an object: nothing to reuse, nothing to judge. The restraint this ADR asks for
("papers, chapters, lectures, problem sets — never pages or paragraphs") needs
one more clause: **never activities either.** A test enforces it.

### Population policy, as chosen

Topics are seeded **on use**, not in bulk. 86 of 239 sources are routed by an
active exam module and a bulk pass over those was explicitly *not* taken; only
the five sources the next study block (AMLS L03) actually routes were
classified. The Library view therefore reports "**234 of 239 not yet classified
by topic**" as a first-class section rather than hiding it, because sparse is
the honest state and a browser that hid it would create pressure toward exactly
the judgment-inventing backfill ADR-005 forbids.

## Answers to the open questions

1. **Flat or nested topics?** *Flat.* Each topic declares a `domain`, but only
   as a display grouping for the Library — never a constraint on which sources
   may carry it. Nesting would reintroduce single-placement one level down. A
   test asserts at least one source carries a topic outside its own domain, so
   the facet cannot quietly degrade into a second name for `thematic_group_ids`.
2. **Does `lifecycle` become a field, retiring `ml-broaden-later`?** Not yet —
   still open. It is a real cleanup but touches curated collections, which is a
   deletion-shaped change and wants review.
3. **Which collections are computable and should be retired?** Open. The rule
   stands (keep a collection only when its *ordering* carries human meaning),
   but retiring shelves is destructive and was not done unreviewed.
4. **Rename `source_feedback` to `resource_feedback`?** *No.* The key stays;
   the shape widened. Renaming would invalidate every v1/v2 record for a
   cosmetic gain, and `source_id` remains required regardless.
5. **Ids everywhere, or only bundles?** *Only bundles, for now.* AMLS is the one
   place with a demonstrated need. ISLP chapters and CS229 problem sets are the
   obvious next candidates — when a second real need appears, not before.

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
