# The corpus classifies what binds, but not what binds this task

Task: build the operator's orientation surface — the discovery index an
agent reads first — after a review found that the capability catalogue, the
CLI operation contract and the request schemas each answered a different
part of "what does this command do, and how do I find it".

Workflow step exposed by: the discovery work itself. The operator contract
told the reader to read "the task-relevant sections of `system/ARCHITECTURE.md`,
`system/WORKFLOWS.md`, and the schemas/contracts they reference" — the one
selection an agent cannot make cold, and the one whose failure is silent.

**Observed.** `system/contracts/normative-corpus.yaml` indexes 81 documents
and classifies each one by class, status, authority and owner. It has no
applicability axis: there is no field that says which task a document binds.
`system/contracts/normative-corpus.schema.json` sets `additionalProperties:
false` and enumerates the permitted keys, so such a field cannot be added
without a schema bump — the gap is structural, not an oversight in one file.

**Inference (not verified as a cause).** A document that is binding but
irrelevant to the task at hand, and a task-relevant document that is binding
but overlooked, are indistinguishable from the corpus alone. Selection stays
a judgement the reader makes.

**What was done in this task, and what it did not close.**
`system/contracts/task-scope.yaml` now answers the task-shaped part: each of
the 13 entry tasks names the entry read that starts it, the executable
procedure that carries it, and the current binding documents that scope it.
The operator contract's entry table is compared with that contract on every
validation run, and a task's scope may name only a document the corpus
records as current and binding.

What stays open is the corpus itself. A document that is not reachable from
any task — a historical ADR, an informative rationale, a reference document no
procedure points at — is still classified only by class, status and
authority. Nothing asks which task, if any, each document is for, so a
document that *should* be in a task's scope and is not cannot be detected.

**Smallest improvement to investigate.** An optional `applies_to` field on
the corpus document object, carrying the task ids whose scope includes that
document, checked in both directions: every name in a task's scope must be a
current binding document (this exists), and every current binding document
that a task names must list that task. The second direction is the missing
one. It needs a schema bump (`additionalProperties: false`), and a
classification decision per document, so it is a content change as much as a
code change.

**Safety it must retain.** The corpus's own guarantee — that a document
without a classification is an error — must keep holding. The new axis must
not become a second way to make a document optional.

Filed on 2026-10-22: [LearningOS #8](https://github.com/Aram164/LearningOS/issues/8),
with the observed evidence, the part already implemented, the scope limit and
the acceptance criteria.

Scope limit: this note records the corpus-level gap. The task-scope contract
described above is the part that was implemented.

## Implementation follow-up, 2026-10-22

The resumed work adds optional `applies_to` to the corpus schema (vocabulary version 3), explicitly classifies every indexed document, and checks exact agreement with task scope in both directions. Unknown tasks, missing inverse edges and extra edges refuse task discovery and validation. Legacy declarations may omit the optional field; absence never relaxes their binding authority. Focused positive and negative tests pass; final paired release verification is pending.
