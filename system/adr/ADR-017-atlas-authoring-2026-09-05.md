# ADR-017 — The Atlas becomes authorable: Aram writes the graph

**Date:** 2026-09-05 · **Status:** accepted (Aram) — recorded by the executor
from the decisions Aram confirmed in the Atlas continuation plan
(`LearningOS-ARCHITECTURE-AND-ATLAS-EXECUTION-PLAN-2026-09-05.md` §3). If that
reading of his confirmation is wrong, this record is wrong and must be fixed
before the capabilities it licenses ship.

**Supersedes nothing. Amends:** ADR-016 decision 9 only — the read-only first
release. Decisions 1–8 and 10 of ADR-016 remain in force and this design
depends on them: strict relations still order learning, semantic ones still
never do, arrows still show study order while the inspector states the
canonical sentence, and modules remain lenses rather than an axis.

## Context

ADR-016 decision 9 fixed the first Atlas release as read-only, on the reasoning
that no governed capability existed for writing `knowledge/concept-relations.yaml`
and that relation authoring deserved "its own Core command, evidence
requirements, preview and receipt" rather than a dead affordance. That
reasoning is not retired. What changed is that the later programme it deferred
is now the current one, and Aram has stated the condition that ends the
deferral: a read-only Atlas does not do the job he built the third pillar for.
He connects mathematics to machine learning to databases himself; an interface
that can only display connections somebody else entered is an intermediate
milestone, not the feature.

## Decisions

**1. A governed relation-authoring capability exists.** Writing the concept
relation registry is now a declared command with the ordinary V2 transaction
machinery — explicit operations, snapshot and registry-revision guards, exact
previous rows bound on replace and remove, atomic refusal on duplicates,
unknown endpoints and prerequisite cycles, and a receipt. Its declaration in
`system/contracts/capabilities.yaml` is the contract; this record only
licenses it to exist. The Garden's `relationship.create` still governs a
different record family and is not reused.

**2. Aram is the author; the AI is a proposer.** Core stores and validates his
assertions and checks them for consistency and integrity. Neither Core nor any
model acquires authority to decide that two concepts are related. AI
investigation is on demand, returns its reasoning and sources, and produces
proposals that stay visibly pending until he selects them. An approved proposal
enters through the same authority as a manual edit and never through a second
path.

**3. Manual authoring never depends on AI.** Creating, editing or removing a
connection must work with no provider configured, without shelving, without an
external editor and without hand-written YAML. This is the acceptance condition
for the capability, not a preference.

**4. A personal question is a note, not a new store.** Questions targeting a
concept or an authored relation reuse the `role: question` note family and the
cross-cutting durable-question pattern that `system/ARCHITECTURE.md` §12
already permits. Question lifecycle is carried in its own field and never
folded into note `state`, which keeps meaning rough/evolving/mature/deprecated.
A saved question asserts nothing about mastery, ignorance, or a prerequisite.

**5. Absence keeps the three meanings ADR-016 gave it.** A missing authored
connection, missing linked evidence, and a question Aram has recorded remain
distinct, and none of them is evidence of any of the others. Authoring adds a
way to fill the first; it does not let the interface start guessing at the
other two.

## Consequences

- ADR-016 decision 9's statement that no governed relation-writing capability
  exists is retired. Its requirement that such a capability carry a Core
  command, evidence requirements, preview and receipt is retained in full and
  becomes the acceptance standard for decision 1 above.
- The inspector's "no governed relation editor is available" wording from
  ADR-016 decision 9 is retired with it. The affordance it forbade is now real,
  so the prohibition on a *dead* affordance is satisfied by implementing the
  editor rather than by hiding it.
- Removing a connection removes an assertion. It never deletes either concept,
  its notes, its materials, or a question recorded against it.
- A question whose recorded target stops existing keeps its recorded target and
  shows the missing-target state. Nothing retargets a question automatically.
- The stored note shape and the published projection change, so both are
  versioned through their own producers. Older notes stay valid and no existing
  note is rewritten by inference.
