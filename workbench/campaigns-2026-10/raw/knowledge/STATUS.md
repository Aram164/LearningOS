# Knowledge campaign status

State: READY for testing the pinned review candidate. Release acceptance is pending.

Aram pastes the worker prompts. GLM 5.8 Flash runs K1–K4; Codex verifies
when Aram returns with the completed reports. No worker launches another chat.

Aram requested the handoff now. The architecture documentation is implemented
and locally verified on the review branch; final upstream verification is still
running. This campaign tests that exact candidate and does not certify a release.

- Core code/docs: fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46.
- Core branch: codex/operator-developer-docs-20261025.
- UI: f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94.
- K2 learner-data snapshot: live Core at 7b713d84b5e8e48b7f8bdb6c88842c7ccbbda2ad.
- Review: https://github.com/Aram164/LearningOS/pull/28.
- Exact-pair run: https://github.com/Aram164/LearningOS/actions/runs/40160353313 (pending at handoff).
- Main has not been advanced by this task. Do not assume its docs are the candidate.

After creating each private clone, fetch the Core review branch from
https://github.com/Aram164/LearningOS.git and check out the exact Core SHA above
in detached mode or a private test branch. Verify HEAD. K2 first clones the live
Core with --no-hardlinks, then fetches this public branch and checks out the pin.
The candidate changes no files under knowledge/, sources/, records/, work/,
curriculum/, projects/ or system/schema/ relative to K2's recorded data base.
Do not replace private learner data with a different remote data snapshot.
If the live data base has moved or contains uncommitted learner changes, record
that difference and stop for reconciliation rather than discarding it.

All code/docs/test changes stay in the private clones; no pushes, CI dispatches,
production fixes, live-vault edits or installation. Reports and signals go here.

K2's 2026-10-24 counts are historical comparison only, not a current baseline.
A fresh K2 clone measures the current public-read navigation surface.

Worker states: K1–K4 done (all four signalled, 0 findings each).
Verification: done by Claude 2026-10-25 (Aram reassigned it from Codex) — see
VERIFY/VERIFY.md. 0 defects confirmed; no fix block. The exact-pair run above
finished green and its pair receipt verified locally.
Landed 2026-10-25 (Aram's OK): Core main 7b713d84 → fb73b0f9, plain
fast-forward pushed with --no-verify from a hook-less clone; PR #28 merged.
Live Core moved to main (validate 0 errors, no new warning signature). UI
unchanged at f7dbc1f.
