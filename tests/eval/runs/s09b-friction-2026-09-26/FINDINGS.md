# Remaining reproducible findings — S09b (landed product 8d1cc47)

All six reproduced 3/3 across independent fresh passes. No finding was
patched (measurement only). Cause key: 1 product defect, 2 doc/discoverability,
3 safety refusal, 4 agent mistake, 5 harness/environment.

## S09B-F1 — milestone_ids not inspectable (cause 2; baseline F-001, still open)

`project-list`/`inspect project-tessera` advertises `milestone_ids`
(`milestone-tessera-parser`, `milestone-tessera-optimizer`), but `inspect`
answers `record not found` (exit 2). Recovery: read the parent project's
`structure` nodes. Cost: 1 extra call + 2 failed commands per S02 run.

## S09B-F2 — no inbox listing command (cause 2; baseline, still open)

`inbox-list` is not a command; `inbox-read` needs a name nothing lists. Working
route `search inbox` (inbox-item rows) is undocumented as the listing path.
Cost: 2 extra calls per S02 run.

## S09B-F3 — setup cost per fresh world (cause 5+2)

`make setup` (venv + network pip install) took 76-100 s per fresh world and
dominates first-contact time (first correct route 81-120 s). Documented and
succeeded 3/3; baseline paid ~5 s cached. Product-side weight is small; the
variance is environmental.

## S09B-F4 — ledger file absent pre-write (cause 2)

WORKFLOWS 25c says to read `operations/transactions/revisions.yaml`, but the
file does not exist until the first write commits; only absent *artifacts*
are documented (as revision 0). Recovery: treat as all-zero baseline.
Cost: 1 failed read + inference per S10 run.

## S09B-F5 — guard sets discoverable only by refusal (cause 2)

The exact `expected_revisions` set per capability is stated nowhere:
stage.note.write needs {unit}, stage.progress.update needs {unit, study-map}
(module not needed; resume.yaml unguarded though changed). Recovery: the
INVALID_REQUEST message names the missing key exactly. Cost: 1 refused submit
+ reseal per S10 run.

## S09B-F6 — envelope ceremony weight (cause 2)

Small writes need snapshot reads, guard discovery, and hand-rolled
intent-hash sealing (recipe complete in 25c, but no helper seals envelopes).
Observed cost ~2-4 min for two small writes on a cold run; second write in a
pass reuses the recipe (S26 capture: 2 calls, first try).

## One-offs (not findings)

- S09B-O1: own sandbox workdir mistake, pass 1 S02 (cause 4/5).
- S09B-O2: own quoting/shape fumbles x3, pass 2 S10 (cause 4).

## Explicit non-findings

- No product defect (cause 1) observed: zero failures.jsonl entries; every
  refusal was designed (INVALID_REQUEST / record-not-found / invalid-choice)
  with an exact recovery.
- No deliberate safety refusal (cause 3) by product or agent environment.
- Implementation knowledge was NOT required: 0 implementation files read in
  9/9 scenario runs; every task completed from product/operator docs plus
  designed refusal feedback.
