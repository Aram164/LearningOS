# Conformance trial — first run (2026-09-11)

Finding 5 of the second reading: run the held-out conformance suite once,
so Phase 1's premise becomes a number. Harness:
`tools/evaluate_operator_questions.py` (format 2), fixtures under
`tests/fixtures/verified_operator_questions/` (15 examples, 5 held out).

## Method (no-peek protocol)

- `prepare` emitted the public package only (5 trials; keys `id`, `class`,
  `question`, `notes`; verified free of `procedure`/`expected`/`accepted`
  tokens before reading).
- The model (Muse Spark, via Codex CLI, 2026-09-11) never opened a held-out
  fixture file. Answer conventions were learned from two *example*
  fixtures only (answer = the procedure's native verdict). The L02 unit
  was grounded by inspecting canonical curriculum data (only `unit-amls-l02`
  carries a recorded `source_selections` entry).
- One submission round. No re-submission after seeing verdicts — fitting
  keys to adjudication outcomes would be gaming the eval, not measuring.

## Result

`score 1/5 (0 unanswered, 4 unadjudicated, 0 fixture-rot)`

| trial | verdict | note |
|---|---|---|
| voq-critique-point-resolved-closed | unadjudicated | re-checks to stated answer on its input; awaits adjudication |
| voq-evidence-stale-claim | unadjudicated | re-checks to stated answer on its input; awaits adjudication |
| voq-is-clean-grown-warning | **pass** | |
| voq-route-dossier-ungrounded-map | unadjudicated | re-checks to stated answer on its input; awaits adjudication |
| voq-scope-authority-source-selection | unadjudicated | re-checks to stated answer on its input; awaits adjudication |

- package_digest `sha256:e3b3ae985790412d6c36b9730fb9529765e450bfeb421134991241d6d525f4d9`
- key_digest `sha256:fe18229bce3ecd0ef001653052899dac7d49298e9f5a43fd83fb51734f2ab2ab`
- 0 fails, 0 fixture-rot: every adjudicated comparison passed and every
  fixture key executes healthy.

## Reading

Score: 1 pass, 4 unadjudicated, 0 fail, 0 fixture-rot. The four
unadjudicated verdicts are not model errors: the harness declines to
score procedures outside its adjudicated set instead of marking them
wrong, which is the harness working correctly. Each one is an
adjudication decision waiting — a human ruling (accept as equivalent, or
reject with reason), and making those rulings is what improves the
fixtures. Separately, every submitted procedure was re-checked through
the public `los semantic` surface and evaluated to its stated answer on
that input. That shows the model read the questions correctly; it is not
equivalence with the keys, which is precisely what adjudication (not
re-running) decides. And the grader was the model: treat this as a first
data point under a strict protocol, not a model comparison. The re-open
bar is a second trial (Astra, or Claude Code) under the same no-peek
rules; the machine-readable report is
`conformance-trial-2026-09-11.report.json`. The submission file is held
by the operator and bound by the report's `input_digest`, not committed,
so future trials cannot copy it.
