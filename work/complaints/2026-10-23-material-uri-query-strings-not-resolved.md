# Material URI query strings are not stripped during resolution

Observed while inspecting `tools/learning_os/store/materials/resolution.py` on Core
commit `1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
`material_uri_authority`, `canonical_material_uri`, `material_location` and
`resolve_material_target` treat the whole payload after `material://` as a path.
Unlike the validator (`_normalise` strips `#`) and the reference parser
(`parse_reference_uri` strips `#`), none of them split off a `?query` component.
A URI such as `material://source-x/foo.pdf?x=1` is therefore accepted as safe,
canonically spelled with the query, and resolved to a path named
`foo.pdf?x=1`, which does not exist.

This is the query-string counterpart of the fragment handling gap: the file
part and the selector part are not separated before path construction.

## Reproduction and proof
Create `materials/source-x/foo.pdf`, then call `material_location` or
`resolve_material_target` with `material://source-x/foo.pdf?x=1`. Both report
the file missing and name `foo.pdf?x=1`. `material_uri_authority` returns
`source-x`.

Relevant code:
- `tools/learning_os/store/materials/resolution.py`,
  `material_uri_authority`, `canonical_material_uri`, `material_location`,
  `resolve_material_target`.
- `tools/learning_os/derive/validation/materials.py`, `_normalise`
  (strips `#` only).
- `tools/learning_os/derive/validation/references.py`, `parse_reference_uri`
  (strips `#` only).

## Smallest improvement and acceptance
Split off and ignore (or reject) the query component before authority,
canonical spelling and path construction, matching the existing fragment
handling. Decide explicitly whether query selectors are supported; if not,
reject them in `material_uri_authority` rather than letting them reach path
construction.

- `material_location` and `resolve_material_target` no longer include `?...`
  in the resolved path.
- URIs without query components behave exactly as before.
- Focused tests cover query-string URIs alongside fragment URIs.

No canonical data was changed by this observation.

## Filing status
Filed: https://github.com/Aram164/LearningOS/issues/18
