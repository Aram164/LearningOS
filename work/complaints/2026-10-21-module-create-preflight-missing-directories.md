# Creation preflight missed an uninitialized-copy structural failure

Task: exercise `module.create` with copies of the actual BS and ICOP records
on a disposable archive of Core commit `480869d24bd3`.

Observed: the first archive lacked the gitignored `generated` and `bases`
directories declared in `system/contracts/tree-contract.yaml`. For the BS
package, `module-create --check` returned `ok: true` and no warning delta,
and sealing succeeded. Applying the sealed envelope then refused with
`VALIDATION_FAILED`, naming `TREE-MISSING` for those two directories. No
receipt was emitted. After creating the two required directories in the
disposable copy, the probe was restarted with baseline validation first.

The initial check and apply outputs are preserved as
`LearningOS/workbench/module-creation-probe-2026-10-21/initial-uninitialized-copy-module-hu-betriebssysteme-check.json`
and `initial-uninitialized-copy-module-hu-betriebssysteme-apply.json`.

This was an incomplete disposable checkout, not a failure in the live vault.
The apply validation provided a real safety benefit by refusing the
structurally invalid tree. The preflight's success still did not predict the
apply result, causing a failed attempt and extra setup work.

Smallest improvement to investigate: compare preflight and apply validation
of required existing directories, or explicitly report that the preflight
normalizes them. Retain the apply guard and rollback; do not weaken the
tree contract. No implementation change was made during this task.

Filed on 2026-10-21: [LearningOS #3](https://github.com/Aram164/LearningOS/issues/3),
including the exact reviewed-package digest, successful preflight, apply
refusal, experiment limitations, and acceptance criteria.

