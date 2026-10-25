# Finding: a graded attempt's result can never be corrected through the declared capability

Capability: `module.attempt.record` (batch C1-A)
Reproduction: `test_graded_attempt_dead_end.py` (this folder). Status on base
`main` (`d6c4779029e366718b71bda158d2aa8f9da1db39`): **fails** — the dead-end
is present. It passes once the correction can be recorded.

## The command

Three V2 gateway envelopes for `module.attempt.record`, in order:

1. `{"module_id": "module-demo", "termin": 2, "date": "2026-10-09", "result": "sat"}`
2. `{"module_id": "module-demo", "termin": 3, "date": "2026-11-01", "result": "passed", "grade": 2.3}`
3. the correction: `{"module_id": "module-demo", "termin": 3, "date": "2026-11-01", "result": "withdrawn"}`

(no `grade` in step 3 — the stated fact no longer carries one). Step 3 is the
one under test; steps 1–2 build the legitimate state it must be able to
correct. Exact fixture and calls: see the test file.

## Observed (verbatim)

Steps 1–2 succeed; the row is
`{"termin": 3, "date": "2026-11-01", "result": "passed", "grade": 2.3}`.
Step 3 exits 2 with:

```
"error": {
  "code": "VALIDATION_FAILED",
  "message": "transaction failed canonical validation: E MOD-GRADE: module
  'module-demo' attempt[2] carries a grade but result is 'withdrawn' and
  module is not completed [curriculum/modules/module-demo/module.yaml]",
  "retryable": false, "details": {}
}
```

The row is unchanged. Because the handler only writes `grade` when the
request supplies one, no payload of this capability can remove the stale
grade — every correction to a non-passed result re-creates the same
MOD-GRADE state and is refused.

## Expected, and which line says so

The correction applies. `system/contracts/capabilities.yaml`,
`module.attempt.record` invariants:

> one module; appends a new attempts row or updates the row for the same
> termin; termin, date, result and optional grade/notes record Aram's stated
> exam fact

"updates the row for the same termin" is the declared half that is
unreachable, and the grade is "optional" per stated fact. The CLI help
(`los module-attempt --help`) repeats it: `--grade GRADE  optional grade
(1.0-5.0; ...)`. Nothing in the contract says a previously recorded grade
sticks to the termin forever.

The operator cannot go around it: boundary 16 (`system/OPERATOR.md`) forbids
hand-editing the record ("A hand edit is not a faster version of this path"),
and no other capability writes `attempts` — `module.sitting.update` touches
only `examination.sittings[].withdrawal_deadline`. The correction is
unreachable through the system.

## Root cause

`tools/learning_os/app/handlers/admin.py:114-125` — the update path sets
`row["date"]` and `row["result"]` unconditionally but guards `row["grade"]`
(and `row["notes"]`) behind "supplied in this request", so an omitted grade
keeps the previous row's value. The validator then refuses the resulting
state: `tools/learning_os/derive/validation/curriculum.py:21-27` (`MOD-GRADE`
— a grade on a non-passed attempt of a non-completed module is an error).
Two components that are each correct in isolation combine into a state the
gateway can enter but never leave.

## Suggested fix

Make the row a faithful restatement of the stated fact at update time: when
`module_attempt` updates an existing row and the new `result` is not
`"passed"` (the only result the validator allows a grade on) while the old
row carries a `grade`, drop the stale `grade` — and symmetrically drop stale
`notes` never supplied again is too aggressive, so scope the fix to `grade`.
Equivalently and more simply: when the request omits `grade`, remove
`row["grade"]` unless the resulting row would keep `result == "passed"`.
That keeps the common correction (fix a date on a passed row, grade
restated or unchanged row kept via a supplied grade) expressible while
making `result != passed` + grade impossible to reach or persist through
the gateway. Whichever shape is chosen, the contract line "updates the row
for the same termin" is the arbiter: the update must be able to complete.
