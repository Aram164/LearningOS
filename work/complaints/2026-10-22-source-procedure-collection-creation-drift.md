# Source procedure still describes collection creation as unavailable

Observed 2026-10-22 while adding the GitHub Student Developer Pack to learning sources.

## Verified observation and impact

`system/procedures/add-or-evaluate-a-source.md:14–16` says no approved capability creates a collection. Its collection step at lines 375–384 writes a fixture collection directly. The current operator contract instead requires `collection.create`, and `.venv/bin/python tools/los.py capabilities collection.create --json` exposes the implemented command and its reviewed-file hash, absence, transaction and revision safeguards.

This caused an extra contract/capability cross-check during an ordinary source-registration task. The transcript explicitly limits its hand edit to a disposable fixture, so this report does not allege that it authorizes live canonical edits. Its stated capability gap and example are nevertheless stale.

Core HEAD during the observation: `480869d24bd3359c122017e1b5f6bdc2e31b3525`, with other authorized implementation work in progress. The procedure was unchanged locally. Python environment: the repository's existing `.venv` on macOS, timezone Europe/Berlin.

## Reproduction and proof

1. Read the source procedure's introduction and collection-creation step.
2. Run `.venv/bin/python tools/los.py capabilities collection.create --json`.
3. Preflight an absent collection from a reviewed file with `collection-create --file FILE --file-sha256 SHA256 --check`, then seal/apply `collection.create` through the gateway.

The real task succeeded using that capability:

- Preflight: `ok: true`, `check: true`, `collection: github-student-developer-pack`, `warnings_delta: []`.
- Apply: `ok: true`, `files_written: 1`, artifact `collection:github-student-developer-pack` revision `1`.
- Receipt: `operations/transactions/transaction-20261022-003423-001.yaml`.
- Reviewed draft digest: `sha256:3fd1feee00b4fca3da6caac250af66e7c3185e52a218e84d3954926a42d1d305`.
- Session validation: zero errors, 1462 existing warnings; warning baseline passed with no new signature.

Full bounded outputs are retained outside Core at `LearningOS/workbench/github-student-pack-2026-10-22/collection-check.json`, `collection-receipt.json`, and `session-review.json`. They are local evidence, not assumed to be available remotely.

## Smallest improvement and acceptance

Update this procedure to demonstrate the existing governed creation path rather than an obsolete fixture-only exception. Keep source intake, examination and collection roles separate.

- The introduction accurately names the available capability.
- The executable collection step drafts outside the canonical destination, binds the exact reviewed bytes, and uses the snapshot/revision-guarded gateway.
- The transcript verifies the receipt and creation revision; duplicate destinations and changed bytes remain refused.
- The affected executable transcript passes after its recorded expectations are updated.

No unrelated implementation is requested by this observation. Issue filing is authorized by the standing problem-reporting rule.

Filed: [LearningOS #5](https://github.com/Aram164/LearningOS/issues/5). Existing repository issues were searched first; none matched this procedure drift.
