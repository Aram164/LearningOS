# Session report — s02-novice-2026-09-25 (INTERIM)

> Interim checkpoint written mid-run at the learner's request. S14, S15 and S26
> have not been run yet; this file will be replaced by the final report.

- Plan / role: N — blind consumer, novice
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e
- Started: 2026-09-25T00:13:20Z

## Scenario outcomes so far

| Scenario | Classification | One-line reason |
|---|---|---|
| S00 | PASS_WITH_FRICTION | Correct 5-line orientation in 8 tool calls; default Python 3.11 refused, bootstrap --brief is one minified JSON line mixing past and future deadlines |
| S01 | ROBUSTNESS_FAILURE | Repo healthy (0 errors, baseline OK), but make setup failed and left a poisoned .venv; make test-fast: 34 failed / 10m51s; the test run wrote a phantom needs-attention operation into the learner's diagnostics |
| S02 | PASS_WITH_FRICTION | Q01–Q12 answered with evidence; unranked substring search, `related` misses the connections questions turn on, stage working notes have no read command |
| S04 | PASS_WITH_FRICTION | A09 filed to the OS L07 stage note with a receipt after approval; computing the approval intent hash needed an implementation read |
| S06 | PASS_WITH_FRICTION | All three captures recognised as duplicates; one kept as a new Garden seed; no append/retire capability, Garden and inbox not searchable |
| S10 | PASS_WITH_FRICTION | Precise "where was I"; progress recorded to the stage note with a receipt; resume/workspace next action do not reflect it |

## Failures recorded so far

F-s01-test-trace-leak-01, F-s01-test-fast-red-02, F-s01-setup-stale-venv-03, F-s04-operations-merge-04 (see failures.jsonl).
