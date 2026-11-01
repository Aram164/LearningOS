# Hosted gates fail where ubuntu-latest resolves to Ubuntu 26.04

Task: push validate on Core main after landing a38d07f4859fcb7ad0f2eb388b06143bf8ae7d32. Run 41320762280 failed on both attempts: all four zz shards stopped at actions/setup-python with "The version '3.14.4' with architecture 'x64' was not found for Ubuntu 26.04". No test ran in those shards and the gate job was skipped.

The commit is not the cause. The review-branch validate 41317524496 on the same SHA passed all 11 jobs, on image ubuntu-24.04. The runner annotation says the ubuntu-latest label migrates to Ubuntu 26 from 2026-10-19, so the label resolves differently between runs and jobs. All jobs in .github/workflows/validate.yml and release-pair.yml, and the UI CI job, use ubuntu-latest while pinning Python 3.14.4 exactly.

Reproduction: run any validate or release-pair where a job lands on the 26.04 image, then read its setup-python step. Expected: the gate runs the same environment on every run. Observed: the outcome depends on which image the label resolves to, and the failure is not a test result. The safety gain from the check stays intact; nothing false passed. Red runs here only block.

Inference, not proof: failures will become more frequent as the rollout finishes. ASSUMPTION: Python 3.14.4 stays unavailable for 26.04 in the setup-python manifest.

Smallest investigation: pin runs-on to ubuntu-24.04 in both Core workflows and UI CI, as the Python version is already pinned, or move to a Python build published for 26.04 deliberately. Keep the exact Python pin, the shard population proof and the workflow tests. Accept when validate, release-pair and UI CI run on one declared image across all jobs.

Proof retained externally: LearningOS/workbench/gemini-arena-2026-11-01/evidence/main-validate-a38d07f-failed.log and main-validate-a38d07f-attempt2-failed.log. At the original observation this note existed only in the campaign drafts because landing it required another exact-pair gate.

Issue: https://github.com/Aram164/LearningOS/issues/91

2 November release finish: all jobs in the two Core workflows and UI CI now pin Ubuntu 24.04 on the isolated candidate branches. The new Core runner regression was red twice on the old labels and passes after pinning. Final hosted acceptance and landing are still required.
