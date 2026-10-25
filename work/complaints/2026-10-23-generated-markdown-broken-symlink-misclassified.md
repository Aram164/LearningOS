# Generated Markdown broken symlink is misclassified as a directory

Observed while inspecting the shared generated-file reader
`tools/learning_os/domain/generated_reads.py` on Core commit
`1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
`generated_file_findings` reports GEN-JSON/GEN-HEADER findings for one generated
path. It is the single shared read used by both the generated-files validator
(`check_generated`) and the validation cache's derived-state pin
(`validator_inputs_digest`), so the two cannot drift.

For a `.json` path that is a broken symlink, the function correctly reports
`generated JSON is a broken symlink, not the published view — delete it and
rebuild`. For a `.md` path that is a broken symlink, it instead reports
`generated Markdown is a directory, not the published view — delete it and
rebuild`, because the Markdown branch tests `path.is_file()` before checking
whether the path is a symlink. The message is wrong for the actual shape and
hides the broken-link cause from an operator reading the validation output.

## Reproduction and proof
Create a broken symlink named `view.md` and one named `view.json`, then call
`generated_file_findings` on each. The JSON case reports a broken symlink; the
Markdown case reports a directory. A directory named `view.md` is correctly
reported as a directory; only the broken-symlink Markdown case is wrong.

Relevant code: `tools/learning_os/domain/generated_reads.py`, function
`generated_file_findings`, Markdown branch (`if not path.is_file()`) and JSON
branch (`if path.is_symlink() and not path.exists()`).

## Smallest improvement and acceptance
Add the same broken-symlink check to the Markdown branch before the `is_file()`
test, reporting `generated Markdown is a broken symlink, not the published view
— delete it and rebuild`. Keep the directory message for actual directories and
the existing unreadable/OSError and UnicodeDecodeError behavior.

- A broken symlink named `*.md` reports a broken symlink, matching the JSON
  case.
- A real directory named `*.md` still reports a directory.
- A regular generated Markdown file without a header still reports GEN-HEADER.
- The shared reader remains the single implementation used by both callers.

No canonical data or generated output was changed by this observation.

## Filing status
Filed: https://github.com/Aram164/LearningOS/issues/13
