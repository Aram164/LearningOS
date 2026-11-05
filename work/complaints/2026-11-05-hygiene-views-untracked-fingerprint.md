# HYGIENE-VIEWS can fire on a clean tree because the fingerprint covers untracked canonical files (2026-11-05)

Task: experimental branch `codex/review-shortcomings-20261105`, fixing the
findings of the 2026-11-05 review (finding 1.2: "HYGIENE-VIEWS: generated/
manifest.json is not the current authored snapshot — run `make views` fires
on a clean tree").

## Observation (verified)

`_hygiene_stale_views` (tools/learning_os/derive/validation/hygiene.py)
compares `generated/manifest.json`'s published `source_fingerprint` against a
fresh `canonical_fingerprint` (tools/learning_os/store/fingerprint.py) over
`CANONICAL_ROOTS`. That fingerprint hashes the on-disk tree, including
**untracked** canonical files. The stamp is only refreshed when someone runs
`make views`.

Measured this session: with untracked `work/complaints/
2026-11-04-installer-legacy-rollback-cli.md` present, the manifest stamp
matched (`0a081822…`). Excluding only that file — i.e. a clean tree, exactly
the state after the next `git stash`/clean checkout — recomputes to
`ceb339a9…` ≠ stamp, so `make check` reports HYGIENE-VIEWS as a warning on a
tree where every authored change is committed and nothing is stale in the
meaningful sense. The warning then tells the operator to regenerate views to
silence a difference that regeneration alone (without new authored content)
produces.

## Why this costs more than it should

The warning's purpose — authored changes committed without regenerating
views — is real and worth surfacing. But because the fingerprint includes
untracked canonical files, the same warning also fires when the *stamping
run* happened in a dirtier tree than the *checking* run. The operator cannot
distinguish "authored work is unregenerated" from "an untracked scratch file
changed the fingerprint" without recomputing fingerprints by hand. Safety
benefit retained: the check is content-addressed and catches genuine
authored/stamp drift; nothing here proposes weakening it.

## Smallest improvement to investigate

Either (a) exclude untracked files from `canonical_fingerprint` when the
hygiene check compares against a published stamp (the stamp's meaning is
"the authored snapshot this projection was built from", and untracked files
are not authored input a projection can carry), or (b) keep the fingerprint
as is and have the hygiene warning name the likely cause (untracked
canonical files present at last generation) so the operator can act in one
step. Either way the check must stay content-addressed and fail closed.

Related measured fact (same session, `tools/receipt_drift.py` sizing run):
snapshot contiguity between consecutive transaction receipts shows 123
non-contiguous pairs in ordinary history for the same underlying reason —
the fingerprint covers untracked canonical files that legitimately change
between commits. One root cause, two noisy signals.
