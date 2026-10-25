# The material-integrity sweep reads complaint prose, so quoted fixture targets fail the whole tree

## Observed during authorized work

On 2026-10-23, finishing the interrupted Bachelor-thesis save (companion note `2026-10-23-projection-conflict-input-diagnostics.md`), I re-ran `.venv/bin/python tools/validate.py --compact` before reporting. Core HEAD was `1d80aa03e674131a67bda37db04fce2d8076c62a` on macOS with the repository virtual environment, in a checkout carrying several other sessions' uncommitted work.

The thesis session's own review had reported 0 errors at 01:59 local. My run at 04:12 reported `5 error(s), 1463 warning(s) — FAIL`. All five are `MATERIAL-MISSING`, attributed to `records/materials-manifest.yaml`, and none concerns a thesis path. `tools/warning_baseline.py --check` reports no new warning signature (1462 across 38, matching the baseline) and fails only on the five errors.

Verified:

- The five targets are `source-x/foo.pdf`, `source-x/foo.pdf?x=1`, `source-x/foo\nbar.pdf`, `source-x/foo\tbar.pdf` and `source-demo/demo.pdf`. In the notes each one follows the material URI scheme and sits inside an inline code span.
- The validator's own `uris_in` extracts exactly those five from four untracked complaint notes written between 02:29 and 02:42 local, and a tree-wide search finds the strings in no other file:
  - `2026-10-23-source-revise-refuses-symlinked-materials-root.md`
  - `2026-10-23-material-uri-control-characters-not-rejected.md`
  - `2026-10-23-material-uri-fragments-not-resolved.md`
  - `2026-10-23-material-uri-query-strings-not-resolved.md`
- Minimal reproduction: one scratch note under `work/complaints/` quoting a single nonexistent target raised the count from 5 to 6. Removing it returned the count to 5 and left the working tree exactly as found.
- Mechanism: `_referenced_materials` (`tools/learning_os/derive/validation/materials.py:254`) is a deliberate regex sweep over `_canonical_texts()` (`tools/learning_os/derive/validation/core.py:132`). Its domain, `CANONICAL_TREES` (`tools/learning_os/domain/validation.py:98`), includes `work`; only the garden and quarantine are skipped.
- The repository already treats `work/complaints/` as an evidence layer (`EVIDENCE_SUBTREE`, `tools/learning_os/domain/validation.py:118`), and `check_ownership` skips it for GEN-INPUT (`tools/learning_os/derive/validation/registries.py:179`, LearningOS #4). The material sweep has no such skip.

Aggravating: every error is labelled with `records/materials-manifest.yaml`, which is unchanged since HEAD, instead of the note that contains the reference. Finding the real source took a tree-wide search plus the validator's own extraction function.

Impact, taken from the documents and not exercised: `tools/hooks/pre-commit` runs `tools/validate.py --compact` and blocks the commit on any error, and OPERATOR.md ("What clean means") makes one error block every canonical write. I attempted neither a commit nor a write while the errors were present.

## Limits

I did not run validation with the four notes removed, because they belong to other sessions; the attribution rests on the validator's own extraction, the tree-wide search and the reproduction above. I did not check whether the link check, which also reads `_canonical_texts()`, treats complaint prose the same way. ASSUMPTION: including complaint prose in the material sweep is unintended. The sweep's docstring says "anywhere in the canonical trees" and does not mention complaints.

## Why the sweep adds little value here

Catching a canonical record whose material target no longer resolves is valuable and must stay. A complaint note exists to quote the failing input, so a quoted target there is evidence about the system, not a reference that any record resolves through. The standing problem-reporting rule asks agents to write exactly these notes, and each one that quotes a fixture target can leave the tree uncommittable.

## Smallest improvement to investigate

Skip the evidence subtree in the material-integrity sweep the way `check_ownership` already does, reusing `in_evidence`.

Acceptance criteria:

- A complaint note that quotes an unresolvable fixture target no longer raises `MATERIAL-MISSING`.
- An unresolvable target in any other canonical text still raises it.
- The exemption covers only `work/complaints/`, and a test exercises both sides.
- The resolution defects in #15, #16 and #18 stay separate problems.

Filed: https://github.com/Aram164/LearningOS/issues/19. Existing issues were searched first (the terms complaint prose, material reference sweep and MATERIAL-MISSING); #15, #16 and #18 cover how the quoted targets resolve, none covers the sweep reading complaint prose. Filed under the standing instruction in OPERATOR.md ("Report observed problems"); nothing was fixed at filing time.

## Repair

Prepared later on 2026-10-23 at Aram's request, in the working tree and not yet landed. `_referenced_materials` in `tools/learning_os/derive/validation/materials.py` now skips the evidence subtree with `in_evidence`, the same call `check_ownership` makes. Five tests in `tests/test_materials_manifest.py` pin both sides: a complaint, nested ones included, may quote an unresolvable target, while the same target in a canonical note, in a workspace file and in the prefix-sharing sibling `work/complaints-archive/` still raises `MATERIAL-MISSING`. Two mutations failed the right tests: removing the exemption failed both complaint cases, and widening it to all of `work` failed the workspace and sibling cases. With the change the checkout validates at 0 errors with no new warning signature. The issue stays open until the change lands.
