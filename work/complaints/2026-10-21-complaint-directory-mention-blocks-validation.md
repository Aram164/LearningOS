# A directory mention in complaint prose blocks canonical validation

Task: write up the module-creation preflight finding. Merely describing the
missing generated-output directory in `work/complaints/` triggered a blocking
`GEN-INPUT` error. The note did not consume a generated artifact as input.
Changing the prose to omit the directory's trailing slash allowed validation.

Reproduced on 2026-10-21 in the disposable repository from the module-creation
probe, based on Core `480869d24bd3359c122017e1b5f6bdc2e31b3525`. A new
`work/complaints/repro-generated-directory-mention.md` contained only a heading
and a sentence describing the two missing directories. Full validation exited
1 and reported `GEN-INPUT` for that complaint. The temporary file was removed
after the experiment; live canonical content was not modified by the probe.
The exact input wording is included in the filed issue; complete output is in
`LearningOS/workbench/module-creation-probe-2026-10-21/complaint-generated-directory-probe.json`.

Code evidence: `check_ownership` and `_references_generated` in
`tools/learning_os/derive/validation/registries.py` match the text, and
`Validator._canonical_texts` in `tools/learning_os/derive/validation/core.py`
includes the complaint. This establishes the blocking behavior; whether the
present policy deliberately prohibits such narrative mentions is a policy
question, not a verified intent.

Impact: required evidence reports need wording workarounds, and one harmless
complaint can block unrelated canonical writes. The dependency guard still
protects against actual use of derived artifacts as canonical inputs.

Smallest improvement to investigate: distinguish operational evidence prose
from actual generated-input dependencies, or document a supported literal
quotation form. Add coverage proving complaint narratives can be recorded
while genuine canonical dependencies still fail. No validator change was
made during this task.

Filed on 2026-10-21: [LearningOS #4](https://github.com/Aram164/LearningOS/issues/4),
with the exact input sentence, validation output, exit status, code locations,
policy uncertainty, and acceptance criteria.

Acted on 2026-10-22: the generated-input rule now fires on a reference to
something *under* the generated tree (`generated/<name>`) rather than on a
bare mention of the directory, and the dated observation records under
`work/complaints/` are exempt: nothing derives from them, so a complaint
that names the generated tree records the observation instead of depending
on it. A canonical file that consumes a generated artifact still fails.
