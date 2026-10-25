# `resolve_symlinks_inside` rejects in-tree symlink targets on macOS

Observed while inspecting `tools/learning_os/store/layout.py` on Core commit
`1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
`resolve_symlinks_inside` is the boundary helper used by material resolution,
material validation, backup verification and source revision. It walks the path
component by component, reads each symlink's target, and checks that the
target stays inside the authority root.

When a component is a symlink, it normalizes the target with
`Path(os.path.abspath(os.fspath(target)))` and then compares it to `authority`,
which was computed as `Path(os.path.abspath(os.fspath(root)))`. On macOS,
`/var` is a symlink to `/private/var`. A repository or materials tree reached
through `/var/...` (the spelling many tools and shells use) has an authority
root spelled `/private/var/...` after `Repo.root` is resolved, while the
lexically normalized symlink target keeps the `/var/...` spelling. The two
strings then disagree, and an in-tree symlink target is reported as
`symlink target escapes` even though it resolves inside the tree.

This blocks material resolution for any source whose `.flat` entry or material
file is a symlink in such a checkout, and it can make backup verification
refuse a tree that is actually inside its boundary.

## Reproduction and proof
Create a materials tree under `/var/...` (macOS) where `source-x/link.pdf`
is a symlink to `real.pdf` in the same directory. Calling
`resolve_symlinks_inside(materials_root, materials/source-x/link.pdf)` raises
`PathBoundaryError: symlink target escapes .../materials`. Both files are
inside the materials tree; the refusal is caused by the `/var` vs
`/private/var` spelling mismatch, not by the link target.

Relevant code: `tools/learning_os/store/layout.py`,
`resolve_symlinks_inside`, specifically the `authority = Path(os.path.abspath(...))`
and `normalized = Path(os.path.abspath(os.fspath(target)))` lines.

## Smallest improvement and acceptance
Normalize both sides the same way before the containment check: resolve the
authority root and each symlink target consistently (for example with
`Path.resolve()` or `os.path.realpath`), while retaining the lexical
pre-check that prevents touching an escaping target. The containment result
must be spelling-independent.

- A symlink whose target resolves inside the authority root is accepted
  regardless of `/var` vs `/private/var` spelling.
- A symlink whose target genuinely escapes the root is still refused.
- Existing material, backup and source-revision callers behave unchanged
  on real checkouts.
- Focused layout tests cover the symlink case on a path whose spelling
  differs by a symlinked prefix.

No canonical data was changed by this observation.

## Filing status
Filed: https://github.com/Aram164/LearningOS/issues/17
