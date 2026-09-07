# Verified Operator Questions (VOQs)

Decided home for the Phase 1 fixture set (Intelligence Plane Phase 0 record:
`work/proposals/intelligence-plane-phase0-record.md`).

## File format

One YAML file per question, `voq-<class>-<topic>.yaml`:

```yaml
id: voq-scope-authority-exam-date   # == filename; unique
split: example                      # example | heldout
class: scope-authority               # one of the six classes below
question: "..."                      # the operator question, in words
procedure:
  predicate: ScopeAuthority          # registered in tools/learning_os/semantics/
  inputs: {...}                      # predicate kwargs
expected:
  equals: ...                        # exactly one of: equals, is_true, is_false, contains
notes: "..."                         # authority reference
```

## The set (20: 15 examples, 5 held out)

| Class | Examples | Held out |
|---|---|---|
| scope-authority | 3 | 1 |
| critique-point | 2 | 1 |
| is-clean | 2 | 1 |
| evidence | 2 | 1 |
| route-dossier | 3 | 1 |
| mutation | 3 | 0 |

## Split rule

Examples prove the predicates answer. The held-out set runs as eval only:
`tests/test_verified_operator_questions.py` scores it (`HELDOUT SCORE 5/5`)
without ever illustrating it. A held-out id quoted in predicates code, this
directory's examples, `system/SEMANTIC-CONTRACT.md`, the contract tests, or
the suite itself fails the no-leak test — a quoted held-out question stops
being held out. Per-model scoring happens outside the suite and is
informative, never a gate.
