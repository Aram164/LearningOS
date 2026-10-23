# Source revision refuses a symlinked materials tree

Observed while inspecting `source.record.revise` material attachment on Core
commit `1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
`_resolve_revise_material` in `tools/learning_os/app/handlers/sources.py` resolves
the live bytes of a material URI before attaching it to a source record. Its
mounted-tree guard rejects the path when `physical.is_symlink()` is true:

```python
physical = repo.learningos_root / "materials"
if physical.is_symlink() or not physical.is_dir():
    raise WriteRefused(...)
```

Other material readers treat a symlinked `materials/` root as mounted:
`materials_mount` in `tools/learning_os/store/materials/resolution.py` resolves
the symlink with `physical.resolve(strict=True)` and continues. `materials/` is
commonly a symlink to an external drive, so this guard makes material
attachment impossible in exactly the setups where the materials tree is mounted
through a symlink, even though reads, projections and validation all work.

## Reproduction and proof
With `materials/` as a real directory, `_resolve_revise_material` resolves
`material://source-demo/demo.pdf` and returns its manifest key, live SHA-256 and
size. With the same directory reached through a symlink at `materials/`, the
same call refuses with `materials tree not mounted at ...`.

Relevant code:
- `tools/learning_os/app/handlers/sources.py`, `_resolve_revise_material`,
  mounted-tree guard.
- `tools/learning_os/store/materials/resolution.py`, `materials_mount`,
  symlink handling.

## Smallest improvement and acceptance
Resolve the `materials/` root the same way `materials_mount` does before
testing whether it is a directory: accept a symlink that resolves to a directory,
and only refuse when it is absent or unresolvable. Keep the boundary checks in
`resolve_symlinks_inside` and the manifest comparison unchanged.

- A symlinked but readable `materials/` tree allows material attachment.
- An absent or broken `materials/` link still refuses with the mounted-tree
  message.
- The resolved path remains inside the admitted boundary.
- Focused source-revision tests cover the symlinked case.

No canonical data was changed by this observation.

## Filing status
Filed: https://github.com/Aram164/LearningOS/issues/14
