Observed during the authorized LearningOS clutter cleanup on 2026-10-22. UI commit: `0daf6b57bb68dc4d0c3d8609e3f7b144a2165802`; Core commit: `1d80aa03e674131a67bda37db04fce2d8076c62a`; macOS, existing Node/Python toolchains.

## Workflow and impact
Synthetic UI checks leave append-only diagnostic output in the persistent source fixture. Before cleanup, `fixture-vault/operations/diagnostics/traces.jsonl` contained 34,174 diagnostic events and occupied 15,951,579 bytes. This is recreatable test output, but accumulates between runs and adds checkout clutter.

## Reproduction and evidence
1. Run `npm run test:ui` using the persistent fixture.
2. Inspect the fixture diagnostic log, then run the tests again.
3. Compare the log size/event count.

`tests/harness.js:351` returns the fixture path from `adapter.getBasePath`. `src/main.ts:497-507` appends the production diagnostic envelope directly under that base path. An isolated copy with the old fixture log, installed fixture plugin and copied bases omitted passed the UI checks and 122 module checks; it recreated about 95 KB of tracing in one UI run. After actual cleanup, both test commands and the installer tests passed.

The experiment establishes persistent fixture output and a one-run recreation; it does not measure long-term growth rate. Production diagnostics remains useful and was preserved in the real vault. The historical canvas run's separate trace was retained by hash.

## Smallest improvement and acceptance
Use a temporary per-run fixture or inject a disposable diagnostic sink for synthetic tests, retaining coverage of the sink and production tracing behavior.

- Two consecutive test runs pass without growing a persistent fixture diagnostic file.
- Test failure still retains actionable evidence through a deliberate artifact policy.
- Production trace, Gateway recovery and diagnostic envelope behavior remain unchanged.

Local proof is retained under `LearningOS/workbench/cleanup-2026-10-22`, including the original deletion digest and passing logs. Those local artifacts are not assumed to be available on GitHub.


## Filing status
Duplicate search found no matching issue. Aram directly approved publication on 2026-10-22. Filed: https://github.com/Aram164/learningos-obsidian-ui/issues/4

## Local repair — 2026-10-22
The shared synthetic harness now copies each source fixture into a disposable per-process vault, excludes old diagnostics and cleans up after success, failure, SIGINT and SIGTERM. Failures retain the last 20 synthetic diagnostic events in the test log. Regressions exercise the unchanged production sink and prove repeated processes preserve the original fixture. The complete UI check passed, including 664 UI checks, 122 module checks and the 12,750-case response differential. No real-vault installation occurred. Evidence update: https://github.com/Aram164/learningos-obsidian-ui/issues/4#issuecomment-6347547353
