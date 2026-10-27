# Projection readiness opened YAML outside the receipt owner

Task: improvement-list safety item 22, added to PR #61.
Verified source baseline: Core `531b63f` on macOS, Python 3.14.

`receipt_completed` in `tools/learning_os/app/projection_readiness.py` previously
accepted any relative path resolving within the repository. `_completed` opened
that YAML before checking transaction authority. A non-receipt YAML would fail
authority, but it should never have been opened as a receipt in the first place.

Expected: only files under `operations/transactions/` may enter receipt
verification. Observed source behavior: the boundary was the entire root.
This is a source-verified read-boundary defect; no claim is made that a forged
receipt succeeded or that private data was returned.

Repair: a shared path guard confines both admission and the subsequent receipt
read to the transaction directory and rejects absolute paths, escapes and
symlinks. New fixture tests replace the authority reader with a failure sentinel
and prove out-of-area paths are refused before that reader is called; an
in-root symlink to a YAML file outside the transaction directory also refuses.
Existing real gateway receipts continue to pass their authority checks.

Acceptance: bounded paths refuse before opening; authentic transaction receipts
still satisfy completion, dependency ordering and projection settlement. No
receipt, ledger, snapshot or publication safeguard is weakened.

Issue: https://github.com/Aram164/LearningOS/issues/63
