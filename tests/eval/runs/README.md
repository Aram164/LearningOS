# Runs

One directory per evaluation session: `runs/<run-id>/` with `run.json`,
`results/<Sxx>.json`, `answers.jsonl`, `connections.jsonl`, `failures.jsonl`,
`observations/`, `evidence/` and `SESSION_REPORT.md` (see
`../public/CONSUMER-PROTOCOL.md`). Blind sessions do not read other runs until
their own is committed. Scorers add `metrics-*.json` and worksheets here.
