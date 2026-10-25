# backup.manifest — a symlinked subtree inside a declared tree is silently omitted from the manifest

**Capability:** `backup.manifest` (query). **Severity:** moderate (latent — see
reachability). **Batch:** C1-E, item L2-6, 2026-10-24.

## Command

```
.venv/bin/python tools/los.py --root <mini-repo> backup-manifest --stdout
```

with the UI authority at `<parent>/obsidian-ui` (default layout) and, inside
the declared core tree `records/`, a symlink `records/archive ->
../../outside-stash/` whose target holds `deep/moved-notes.md` (a regular
file). The setup models the classic operator move: a subtree moved to
external storage and linked back into place.

Test: `test_symlinked_subtree_silent_omit.py` (clone copy:
`tests/test_c1e_backup_symlink_subtree.py`, registered in
`tests/group_map.py`, group `gateway`). Fails on base `d6c47790` in 0.27s.

## Observed (verbatim)

```
exit: 0
core/records entries: ['records/modules.yaml']
'archive' appears anywhere in the manifest: True
total entries: 222
aggregate: sha256:a1f8e0014dae7379295c9dd70107ec37e8acbfb6f05498d43c38a73288360000
```

(The one `archive` hit is the unrelated declared tree
`archive/workspaces`; nothing in the manifest mentions `records/archive`.)

The command exits 0 and the manifest validates against
`backup-manifest.schema.json`, with `records/archive/**` absent from the
entries and no marker anywhere recording the skip. The pytest failure:

```
AssertionError: backup-manifest completed green while the declared records tree's
symlinked subtree left the inventory without a trace; entries cover 222 files and
the manifest records no skipped subtree
```

The same blindness is shared by the verifier:
`verify_backup_manifest`'s "unaccounted" check compares against the same
`_admitted_paths` walk, so a restore from this manifest also verifies green.

## Expected

`system/contracts/capabilities.yaml`, `backup.manifest` invariants: the
manifest "hashes only producer-declared allowlisted roots" — the inventory
answers for exactly what the contract declared, and the module's own stated
principle (`tools/learning_os/app/backup_manifest.py:36-45`,
`_refuse_unreadable`, written for #25) is that declared-but-unreadable
content must refuse, because "its contents left the inventory without a
trace" is the one answer a backup must never give quietly. The module
already refuses a declared *tree* that is itself a symlink
(`_inside`, backup_manifest.py:155-171: "backup declaration traverses a
symlink") and records the one known symlink farm (`materials/.flat`) as
explicit alias data (#31) — the silently-skipped *subtree* case is the
remaining hole in the same guard.

## Root cause

`tools/learning_os/app/backup_manifest.py:295-307` (`_admitted_paths`):
`os.walk(tree, ...)` never descends symlinked directories
(`followlinks` defaults to False) and `_admit_file` (lines 174-192)
refuses symlinked files, so a symlinked subdirectory inside a declared
tree yields no entries — and unlike the declared-tree-symlink case
(`_inside` raises) and the unreadable-directory case (`_refuse_unreadable`
raises), nothing records or refuses what the walk skipped.

## Suggested fix

When the inventory walk encounters a symlinked directory (or, for
completeness, any non-regular entry it declines) inside a declared tree,
either refuse the inventory like `_refuse_unreadable` does, or record the
skipped subtree in the manifest as explicit data — the way
`_materials_aliases` already records the `.flat` farm — so the manifest
never claims completeness over a tree it partially declined to read. A
refusal is safest; a marker is compatible with operators who link
subtrees deliberately. Both satisfy the fix-agnostic test.
