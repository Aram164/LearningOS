# Material URIs accept control characters and spaces in canonical spelling

Observed while inspecting `tools/learning_os/store/materials/resolution.py` on Core
commit `1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
`material_uri_authority` validates a `material://` URI's safety. It rejects empty
payloads, absolute payloads and backslashes, but it does not reject control
characters such as newline or tab, nor other whitespace. `canonical_material_uri`
then collapses `.` and empty path segments and returns a canonical spelling that
can contain those characters:

- `material://source-x/foo\nbar.pdf` -> authority `source-x`,
  canonical `material://source-x/foo\nbar.pdf`
- `material://source-x/foo\tbar.pdf` -> authority `source-x`,
  canonical `material://source-x/foo\tbar.pdf`

By contrast, `safe_material_locator` rejects `\n` (and `\`), and
`leading_material_locator` rejects `\n` (and `\`). So a material URI can be
accepted and canonically spelled with characters that the locator layer would
refuse, and the resulting URI cannot be a single-line YAML scalar or a usable
path.

## Reproduction and proof
Call `material_uri_authority` and `canonical_material_uri` on URIs containing
newline or tab. Both return non-None values containing the control character.
Call `safe_material_locator` on the corresponding locator; it returns None.

Relevant code:
- `tools/learning_os/store/materials/resolution.py`,
  `material_uri_authority` and `canonical_material_uri`.
- `safe_material_locator` and `leading_material_locator` in the same module.

## Smallest improvement and acceptance
Reject control characters and embedded whitespace in the payload of
`material_uri_authority`, matching the locator layer's boundary, and make
`canonical_material_uri` return None for any payload that authority rejects.
Keep valid file and directory URIs working, including those with ordinary
path segments.

- Newline, tab and other control characters in a material URI yield no
  authority and no canonical spelling.
- `canonical_material_uri` agrees with `material_uri_authority` on rejection.
- Existing valid URIs (files, directories, dot/double-slash spellings) keep
  their canonical forms.
- Focused tests cover the control-character cases alongside the existing
  spelling cases.

No canonical data was changed by this observation.

## Filing status
Filed: https://github.com/Aram164/LearningOS/issues/15
