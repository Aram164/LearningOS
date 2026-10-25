# Claude's verdict on C1-C (2026-10-24, overnight orchestrator)

C1-C reported two findings. Both tests were re-run on Core `main`
`d6c47790`, in Claude's scratch clone, registered under `gateway` in
`tests/group_map.py`. The test copies and the `group_map` edit were removed
afterwards.

## 1. `note.revise` bypasses the question and reference guarantees

**CONFIRMED. Moderate severity. The finding stands, but one of its two
tests is broken.**

**Witness 1 (question target):** fails on `main` as documented.
`note.revise` exits 0 and the stored `atlas_question.target` changes, while
`atlas.question.save` refuses the same change
(`handlers/atlas.py:313-317`).

**Witness 2 (reference binding): the delivered test is wrong.** It fails at
line 147, the precondition, before `note.revise` is ever called.
- The test stores `frozen_input_sha256` as bare hex.
- Its helper `_binding_describes_body` compares the stored value against
  `"sha256:" + hex`, so it reports False even on the untouched note.

With that one comparison fixed in my copy (strip an optional `sha256:`
prefix), the precondition passes. The test then fails at line 170 for the
documented reason: after the revise, `material_analysis` still claims bytes
the body no longer holds. **The claim holds. Fix the test before it goes into
an issue.**

**Root cause, read:** `handlers/notes.py:186-199` checks only id, type and
role. Everything else in the replacement is written verbatim.
- The `note.revise` contract (`capabilities.yaml:516-519`) promises only "id
  and role remain stable".
- `ARCHITECTURE.md` §5.7 says the reference and question roles keep their
  dedicated capabilities "so provenance bindings and question wording can
  never be bypassed by the general path". It also names `note.revise` as the
  update path.

So this is a real gap between the architecture and the general update path,
not a misused API. The replacement in the test is an ordinary revise: same
frontmatter, new body.

**Reachable in Aram's tree:**
- **The reference case, yes.** 29 live notes under `knowledge/notes/` carry
  `material_analysis`. Any agent that "edits" one through `note.revise`
  leaves its binding false, and validation stays green.
- **The question case, not yet.** The live tree has 0 `role: question`
  notes.

**Fix:** as GLM suggests. For `role: question`, require the target to stay
equal, or route edits to `atlas.question.save`. For notes with
`material_analysis`, refuse a body or binding change, or re-bind it. Add the
rule to the `note.revise` invariants.

**Issue draft:** `ISSUES-DRAFT.md`, entry C1-C-1. No duplicate found: the
searches for "note.revise", "material_analysis" and "atlas_question" hit only
#21 and #22, which are unrelated.

## 2. `garden.seed.create` can write a seed named `readme.md` that no reader admits

**CONFIRMED in the mini-repo. Not reachable in Aram's tree. Low severity.**

The test fails on `main` as documented: `note-read garden-note-readme` says
"note not found". The asymmetry is real:
- `_seed_slug` (`handlers/capture.py:53-71`) has no reserved-name check.
- `load_garden` (`store/loading/knowledge.py:111-113`) skips the `readme`
  stem.

**Why Aram's tree is safe:**
- The live `knowledge/garden/README.md` exists, and so does the clone's.
- macOS filesystems are case-insensitive by default (APFS).
- So the collision loop at `capture.py:181` (`while target.exists()`) finds
  `readme.md` taken and writes `readme-2.md`, which the reader admits.

The bug needs a case-sensitive filesystem, or a garden with no README, which
is the shape of the test's mini-repo. GLM did not consider the collision
loop.

**Fix:** a one-line reserved-slug guard. Cheap, not urgent.

**Recommendation: don't file it on its own.** This follows the C1-A
finding-1 precedent: real, but unreachable here. A short draft is still in
`ISSUES-DRAFT.md` as C1-C-2, in case Aram wants a hygiene issue.

## Not verified

The "attacked and held" section. The C1 verification pass (L1-2) owns it.
