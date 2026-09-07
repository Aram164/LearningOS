# Verified Operator Questions (VOQs)

Decided home for the Phase 1 fixture set (Intelligence Plane Phase 0 record:
`work/proposals/intelligence-plane-phase0-record.md`).

## What lives here (from Phase 1)

~20 question/procedure/expected-property triples, each a small YAML file:

- scope-authority judgments ("which record owns this fact?")
- critique-point fixability ("is this point actionable work?")
- "is clean" procedure (zero errors + no new warning signature)
- Bayes-evidence procedure
- route-validity dossier procedure

## Split rule

15 examples any model may study; **5 held out** as eval only, never as
examples. `tests/test_verified_operator_questions.py` enforces the split:
the held-out set is scored per model (informative, not a gate).

## Phase 0 status

No fixtures yet — only this path decision. Phase 1 adds the triples plus
the suite.
