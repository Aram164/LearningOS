# Finding: `note.revise` voids the dedicated capabilities' guarantees for question and reference notes

- **Capability:** `note.revise` (CLI `note-revise`), bypassing
  `atlas.question.save` and `note.analysis.save`.
- **Batch:** C1-C (families `note`, `atlas`, and the roles the two dedicated
  capabilities own).
- **Base:** `d6c4779029e366718b71bda158d2aa8f9da1db39` (GitHub `origin/main`).
- **Reproduction:** `tests/test_c1c_revise_guarantees.py` in the clone
  (registered in `tests/group_map.py`, group `gateway`); both witnesses fail
  on base. A copy is in this folder as
  `test_revise_voids_dedicated_guarantees.py`.

## The command

```
los capability atlas.question.save --payload-file <envelope; question id note-question-demo,
                                                     target {"concepts": ["concept-variance"]}>
los capability note.revise         --payload-file <envelope; note_id note-question-demo,
                                                     file <replacement .md>,
                                                     file_sha256 sha256:…>
```

The replacement file carries the note's own frontmatter with one edit —
`atlas_question.target` rewritten to
`{"concepts": ["concept-expected-value", "concept-variance"]}` — id, type,
role, title, created, authorship and state unchanged, plus a new body.

## What I observed, verbatim

Witness 1 — question target retargeted through the side door:

```
assert (0 != 0 or {'concepts': ...pt-variance']} == {'concepts': ...pt-variance']}
 +  where 0 = CompletedProcess([... 'capability', ...]).returncode

Differing items:
{'concepts': ['concept-expected-value', 'concept-variance']} != {'concepts': ['concept-variance']}
```

`note.revise` returned 0 (receipt written, `replayed: false`) and the stored
question now names a target the question was never saved with. The same
change through the front door is refused by design (below).

Witness 2 — reference-note provenance left describing bytes it no longer
preserves: a `note.analysis.save` note (`role: reference`, binding
`resolution: unresolved`, `frozen_input_bytes: len(body)`,
`frozen_input_sha256: sha256(body)`) was revised to a different body of a
different length with the frontmatter kept verbatim. The commit succeeds and
`material_analysis` still claims the schema's contract about the body:

```
note.schema.json, material_analysis.frozen_input_bytes.description:
  "Length in bytes of the preserved body: the note body is exactly the file's last N bytes."
```

The last N bytes of the revised file are the replacement prose, and their
sha256 is not `frozen_input_sha256`. The test asserts "refused, or the
binding still describes the body"; on base main neither holds.

## What I expected, and who says so

- `system/contracts/capabilities.yaml`, `atlas.question.save` invariant:
  **"learner wording and original target are preserved"** — and the handler
  enforces exactly that on its own path
  (`tools/learning_os/app/handlers/atlas.py:313-317`, refusal site
  `atlas.question.save.retarget-refused`, "the original question target is
  preserved").
- `system/schema/note.schema.json`, `material_analysis` descriptions quoted
  above: the binding is a standing claim about the note's own bytes, not a
  creation-time snapshot.
- `system/ARCHITECTURE.md` §5.7 states the principle the general path must
  uphold: the `reference` and `question` roles "keep their dedicated
  capabilities … **so provenance bindings and question wording can never be
  bypassed by the general path**". `note.create` honours this by refusing
  both roles; `note.revise` is the general path for existing notes and
  carries no equivalent guard.
- `system/OPERATOR.md:260-262` defines what revise is for: "An explicitly
  reviewed **semantic replacement** … preserves the note's ID, path, and
  role; moves, merges, splits, and role changes remain outside this
  capability." Retargeting a question or voiding a provenance binding is a
  semantic change outside the three preserved facts revise promises.

Expected: either `note.revise` refuses revisions that would change a
question's `atlas_question.target` or replace a reference note's body
(pointing at `atlas.question.save` / deprecate-and-re-save), or the handler
enforces the dedicated capabilities' guarantees on the replacement (target
equality; a re-bound `material_analysis`). The current middle — commit, keep
the stale facts — is the one the contracts rule out.

## Root cause

`tools/learning_os/app/handlers/notes.py:186-199` — `note_revise` validates
only `meta.get("id")`, `meta.get("type")` and `meta.get("role")` against the
existing note; everything else in the replacement file is written verbatim.
No downstream net catches it: the canonical validator has no rule on
`atlas_question.target` or `material_analysis` frozen bytes (grep over
`tools/learning_os/derive/validation/`: zero hits for both), the revised
files stay schema-valid, and every `REF-*` check passes when the replacement
names existing concepts. The staged canonical validation therefore blesses
both witnesses. Downstream readers do not re-verify either fact: plan-gate
dossiers pin `note_revision`/`note_digest` at approval time
(`derive/material_synthesis.py:238-248`) — they detect the revision but the
note itself is left carrying false claims.

## Suggested fix

In `note_revise`, load the existing note's role and branch: for
`role: question`, require the replacement's `atlas_question.target` to equal
the stored one (mirroring `atlas.question.save`'s retarget refusal) — or
refuse question notes outright and route edits through
`atlas.question.save`, which already owns bounded updates; for
`role: reference`, refuse any replacement whose body bytes do not satisfy the
stored `material_analysis` binding, and refuse any replacement that alters
the binding at all (re-analysis of new source bytes is a new
`note.analysis.save`, not a revision). Whichever shape is chosen, state it in
the `note.revise` invariants so the capability contract and the handler agree
on which fields are handler-owned for which roles. Severity: moderate — no
canonical corruption and validation stays green, but two standing
system claims ("the original target is preserved", "the body is exactly the
last N bytes") become false through an advertised capability, and the
question-target hole also bypasses the one guard that keeps an Atlas
question pointing at what the learner originally asked about.
