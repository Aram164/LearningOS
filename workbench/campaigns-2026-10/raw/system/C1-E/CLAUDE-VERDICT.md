# Claude's verdict on C1-E (2026-10-24, overnight orchestrator)

C1-E reported two findings. Both tests were re-run on Core `main`
`d6c47790`, in Claude's scratch clone, registered under `gateway`. Both fail
for the documented reason. The copies and the `group_map` edit were removed
afterwards.

GLM cites "#25" and "#31". Those are history numbers from code comments in
`backup_manifest.py`, not GitHub issues: GitHub #25 is a link-check bug, and
#31 does not exist.

## 1. `backup.manifest` skips a symlinked subdirectory without a trace

**CONFIRMED. Latent: unreachable in Aram's tree today. Moderate in kind,
low now.**

**What I checked:**
- `_admitted_paths` (`app/backup_manifest.py:295-307`) walks each declared
  tree with `os.walk`, whose `followlinks` is False by default.
- `_admit_file` refuses symlinked files.
- So a symlinked directory inside a declared tree produces no entries and no
  refusal. The manifest still exits 0, schema-valid.
- The restore verifier uses the same walk, so it also passes.
- This contradicts the module's own rule: unreadable declared content must
  refuse (`_refuse_unreadable`), and a declared tree that is itself a symlink
  refuses (`_inside`).

**Reachability:**
- A read-only `find -type l` over the live Core tree (skipping `.git`,
  `.venv`, `node_modules` and `generated`) finds one symlink: the root file
  `CLAUDE.md`. No symlinked directory.
- The materials tree has links only in the known `.flat` farm, which is
  recorded as aliases. GLM read this; I did not re-check it.
- So no live backup is missing data. The gap opens the day someone moves a
  subtree out and links it back.

**Fix:** refuse, like `_refuse_unreadable`, or record the skipped subtree as
manifest data. Refusing is the safer choice.

**Issue draft:** `ISSUES-DRAFT.md`, entry C1-E-1. It is worth its own
low-priority issue, because a backup that silently omits data is the failure
the module exists to prevent. No duplicate found: #17 (macOS in-tree
symlinks, closed) and #1 are different.

## 2. A one-section coordination edit re-flows blank lines in other sections

**CONFIRMED. Minor and cosmetic.**

- `replace_h2_section` (`domain/render.py:106-117`) re-serialises the whole
  body through `serialise` (`render.py:84-103`).
- `serialise` normalises blank lines around every heading.
- The existing test misses this because it compares sections with `.strip()`
  (`tests/test_coordination_revision.py:52-54`).
- The contract invariant, "other section content are preserved", is
  violated only in blank lines. No text changes.

**Reachability, measured read-only:** I ran `serialise(parse_sections(body))`
on the live `work/COORDINATION.md` and on the five live workspace
`CONTEXT.md` files with a `## Next Action` section.
- 5 of 6 are already in normalised form, so the next edit changes nothing
  else in them.
- `work/active/workspace-bs-foundations/CONTEXT.md` would lose one blank
  line.

**Fix:** splice the target section's line range instead of re-serialising.
Not urgent.

**Recommendation:** fold this into the hygiene issue together with C1-C-2,
C1-D-1 and C1-D-2, rather than filing it alone. Its draft entry is C1-E-2.

## Not verified

The "attacked and held" section. The C1 verification pass (L1-3) owns it.
