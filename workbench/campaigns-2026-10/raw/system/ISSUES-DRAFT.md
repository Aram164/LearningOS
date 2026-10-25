# Issue drafts from the GLM campaigns (not filed)

The orchestrator drafts these for CONFIRMED findings only. Filing belongs to
Aram or the landing session. Each entry names its verdict file. The duplicate
search was run against `Aram164/LearningOS`, with `--state all`.

---

## C1-B-1. A partial shelving apply marks the packet `applied` and drops the remainder from the review queue

Verdict: `C1-B/CLAUDE-VERDICT.md`.
Reproduction: `C1-B/review.apply/partial-apply-hides-remainder/test_partial_shelving_apply.py`.
To run it, register it in `tests/group_map.py` under `studyplan`.

**Title:** review.apply: a partial apply sets shelving.state=applied and hides the unapplied items from review_items

**Body:**

The shelving view gives each proposal item its own checkbox
(`obsidian-ui/src/views/shelving-view.ts:245-247`), so applying a subset is
an ordinary gesture.

After a subset is applied:
- `shelving_apply` sets `shelving.state = "applied"` unconditionally
  (`tools/learning_os/app/handlers/capture.py:543`).
- `build_review_items` publishes a shelving row only while
  `state == "proposed"` (`tools/learning_os/derive/projection/review.py:79`).
- The unapplied items stay in `shelving.items`, still `selected: true`, and a
  later `review.apply` of them is accepted.
- They no longer appear in the manifest's `review_items`, and the map claims
  the whole packet is applied.

No canonical data is damaged. The destination-exists check still blocks a
double write.

**Reproduce:** the test above, on `main` `d6c47790`. It fails with
`assert 'shelving' in []`.

**Decide, then fix one way:**
- **(a) Unselected means pending.** Keep `state: proposed` while unapplied
  items remain. Record the applied items per item, so that the queue row and
  the packet agree on what is left.
- **(b) Unselected means declined.** Drop the unselected items at apply time,
  refuse their later apply, and say so in the `review.apply` invariants in
  `system/contracts/capabilities.yaml`.

Not reached in the live tree yet: every live shelving block is `state: none`.

---

## C1-C-1. note.revise can retarget a question and void a reference note's material_analysis binding

Verdict: `C1-C/CLAUDE-VERDICT.md`.
Reproduction: `C1-C/note.revise/revise-voids-dedicated-guarantees/test_revise_voids_dedicated_guarantees.py`.
To run it, register it under `gateway`.

**Fix the test's helper before attaching it.** `_binding_describes_body`
compares against `"sha256:" + hex`, but the test stores bare hex. As
delivered, witness 2 fails on its precondition, not on the defect.

**Title:** note.revise lets the general path change handler-owned facts of question and reference notes

**Body:**

`note_revise` (`tools/learning_os/app/handlers/notes.py:186-199`) checks only
`id`, `type` and `role`. Everything else in the replacement file is written
verbatim. `ARCHITECTURE.md` §5.7 says the reference and question roles keep
their dedicated capabilities "so provenance bindings and question wording can
never be bypassed by the general path". `note.revise` is that general path for
existing notes.

**Observed on `main` `d6c47790`:**
1. **Question target.** A revise that changes `atlas_question.target`
   commits with rc 0. `atlas.question.save` refuses the same change
   (`retarget-refused`, `handlers/atlas.py:313-317`).
2. **Reference binding.** A revise that keeps the frontmatter and replaces the
   body commits with rc 0. `material_analysis.frozen_input_bytes` and
   `frozen_input_sha256` then describe bytes the body no longer holds, though
   `note.schema.json` defines them as "the note body is exactly the file's
   last N bytes".

No validator rule covers either field, so validation stays green.

**Reach:** 29 live notes carry `material_analysis`. There are no question
notes yet.

**Fix:**
- For `role: question`: require `atlas_question.target` to stay unchanged,
  or refuse and point to `atlas.question.save`.
- For notes with `material_analysis`: refuse a body or binding change, since
  re-analysis is a new `note.analysis.save`.
- Add the rule to the `note.revise` invariants in `capabilities.yaml`.

---

## C1-C-2. garden.seed.create can write a seed the garden reader skips (recommend: don't file alone)

Verdict: `C1-C/CLAUDE-VERDICT.md`.
Reproduction: `C1-C/garden.seed.create/invisible-reserved-slug/test_garden_invisible_reserved_slug.py`.
To run it, register it under `gateway`.

**Title:** garden.seed.create has no reserved-slug check, so a seed titled "README" is skipped by load_garden

**Body:**

`_seed_slug` (`tools/learning_os/app/handlers/capture.py:53-71`) can produce
`readme`, and `load_garden` (`store/loading/knowledge.py:111-113`) skips that
stem as meta. In a garden with no `README.md`, or on a case-sensitive
filesystem, the receipted seed `knowledge/garden/readme.md` is unreadable by
its stable id, unsearchable, and missing from the Nebula.

**Not reachable on Aram's Mac:** `knowledge/garden/README.md` exists, the
default filesystem is case-insensitive, and the collision loop
(`capture.py:181`) writes `readme-2.md` instead.

**Fix:** refuse the slug `readme` with a typed refusal.

---

## C1-D-1 and C1-D-2 (low; recommend one hygiene issue together with C1-C-2)

Verdict: `C1-D/CLAUDE-VERDICT.md`.
Reproductions:
- `C1-D/capture.create/same-second-file-capture-overwrite/test_same_second_file_capture_overwrite.py`
- `C1-D/material.context/zero-limit-widened/test_zero_limit_widened.py`

Register both under `gateway`.

**Title (bundled):** Three small guard gaps where a write or read path skips the check its neighbour applies

**Body:**

1. **`capture.create`, file branch** (`handlers/capture.py:109-111`). It takes
   one stamped fallback name, `{stamp}-{src.name}`, and never checks it
   again. A third file capture with the same basename, committed in the same
   clock second, overwrites the second capture's bytes while that capture's
   receipt still names the path. The text branch loops for a free name.
   Reachable only with a frozen observation clock, since commits are
   serialized and take seconds. Fix: use the same serial loop.
2. **`material.context`** (`handlers/materials.py:1204-1206`).
   `req.get("limit") or 20` turns an explicit `--limit 0` into a full page,
   so the 1..20 window check never sees it. The request schema also lacks
   `minimum: 1`. Fix: pass the limit through unchanged and let
   `_window_values` refuse it.
3. **`garden.seed.create`** (C1-C-2). There is no reserved-slug check, so a
   seed titled "README" is skipped by `load_garden` on a case-sensitive
   filesystem.

Each has a failing pytest on `main` `d6c47790`. None damages canonical
data.

---

## C1-E-1. backup.manifest silently omits a symlinked subdirectory inside a declared tree (latent)

Verdict: `C1-E/CLAUDE-VERDICT.md`.
Reproduction: `C1-E/backup.manifest/symlinked-subtree-silent-omit/test_symlinked_subtree_silent_omit.py`.
To run it, register it under `gateway`.

**Title:** backup-manifest exits green while a symlinked subdirectory inside a declared tree is left out of the inventory

**Body:**

`_admitted_paths` (`tools/learning_os/app/backup_manifest.py:295-307`) walks
declared trees with `os.walk`, which by default does not follow links.
`_admit_file` refuses symlinked files. A symlinked directory inside a
declared tree therefore produces no entries and no refusal. The manifest is
schema-valid, exits 0, and passes `verify_backup_manifest`, which uses the
same walk.

The module refuses the neighbouring cases:
- a declared tree that is itself a symlink (`_inside`);
- unreadable declared content (`_refuse_unreadable`).

This case should refuse too, or record the skipped subtree as data, the way
the `materials/.flat` aliases are recorded.

**Reach:** latent. The live Core tree has no symlinked directory today; its
only symlink is the root file `CLAUDE.md`. The gap opens if a subtree is
ever moved to external storage and linked back.

**Fix:** refuse on any symlinked directory inside a declared tree, or record
it explicitly in the manifest.

---

## C1-E-2. A coordination section edit re-flows blank lines in the other sections (fold into the hygiene issue)

Verdict: `C1-E/CLAUDE-VERDICT.md`.
Reproduction: `C1-E/coordination.section.revise/whole-document-reflow/test_whole_document_reflow.py`.
To run it, register it under `gateway`.

**Item 4 for the bundled hygiene issue:**

`replace_h2_section` (`domain/render.py:106-117`) re-serialises the whole
document, so `coordination.section.revise` and `workspace.next-action.update`
normalise blank lines in sections they did not touch. That breaks "other
section content is preserved" byte for byte. The existing test cannot see it
because it compares with `.strip()`.

On live data, 1 of 6 files would change: `workspace-bs-foundations/CONTEXT.md`
loses one blank line.

**Fix:** splice the section's line range instead of re-serialising.
