# Material URI fragments are not stripped during resolution

Observed while inspecting `tools/learning_os/store/materials/resolution.py` on Core
commit `1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
RFC 3986 treats `#page=2` as a fragment that qualifies a resource rather than
naming it. `parse_reference_uri` in `tools/learning_os/derive/validation/references.py`
already splits the fragment before resolving, and `uris_in` in
`tools/learning_os/derive/validation/materials.py` strips it with `_normalise`.
The material resolution layer does not:

- `material_uri_authority("material://source-x/foo.pdf#page=2")` returns
  `source-x`, so the URI is treated as safe.
- `canonical_material_uri(...)` preserves the fragment in its canonical spelling.
- `material_location(...)` and `resolve_material_target(...)` build a path that
  includes `foo.pdf#page=2`, so the file is reported missing even though
  `foo.pdf` exists.

A source or evidence reference that carries a page selector therefore cannot be
resolved to its bytes, and a validator-facing reference that uses the fragment
form fails to match its on-disk file.

## Reproduction and proof
Create `materials/source-x/foo.pdf`, then call `resolve_material_target` or
`material_location` with `material://source-x/foo.pdf#page=2`. Both fail with a
FileNotFoundError naming `foo.pdf#page=2`. The same URI's authority is non-None.

Relevant code:
- `tools/learning_os/store/materials/resolution.py`,
  `material_uri_authority`, `canonical_material_uri`, `material_location`,
  `resolve_material_target`.
- `tools/learning_os/derive/validation/references.py`, `parse_reference_uri`
  (already splits the fragment).
- `tools/learning_os/derive/validation/materials.py`, `_normalise`
  (already strips the fragment).

## Smallest improvement and acceptance
Strip the fragment in the resolution layer before path construction, the same
way the validator and reference parser already do. Preserve the fragment in
reference/evidence handling where it is a page selector; do not treat it as a
filename component.

- `material_location` and `resolve_material_target` resolve
  `material://source-x/foo.pdf#page=2` to `foo.pdf`.
- `material_exists` reflects the file, not the fragment.
- URIs without fragments behave exactly as before.
- Focused tests cover fragment URIs alongside the existing spelling cases.

No canonical data was changed by this observation.

## Filing status
Filed: https://github.com/Aram164/LearningOS/issues/16
