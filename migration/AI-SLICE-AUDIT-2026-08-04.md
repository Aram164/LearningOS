# `garden.shelve` — audit and implementation report

**Date:** 2026-08-04
**Scope:** `LearningOS/repository/`, `LearningOS/obsidian-ui/`. `Job/` was absent from the handoff bundle and was neither read nor referenced.
**Audited state:** core `d25004d` (= bundle `2bc3c72`), UI `568e086` (= bundle `9ba7bd8`)
**Result state:** core `c96f8ef`, UI unchanged

---

## 1. What happened to the branches

The handoff bundle carried the AI slice, but the working repositories did not: both `LearningOS/repository` and `LearningOS/obsidian-ui` were sitting on `codex/module-curriculum-redesign-v2` at the pre-slice bases (`1501eb4` / `cf27e77`). The slice existed only as patches.

Both repositories now carry a `feature/ai-garden-shelve-v1` branch created from those bases, with the bundle's patches applied via `git am`. Commit hashes differ from the bundle's (`git am` rewrites committer metadata); trees were diffed against the bundle and match exactly apart from `generated/` — which is gitignored, was stale at `source_revision: 1501eb4`, and has since been rebuilt.

Neither branch has been pushed. The recovered untracked artifacts (`Untitled*.canvas`, `system/skills/`) were left unstaged as instructed.

---

## 2. Baseline before any change

| Check | Result |
|---|---|
| `pytest tests/test_ai_actions.py` | 6 passed |
| `los.py validate` | 0 errors, 0 warnings (after `generate.py`; before it, 1 stale-manifest warning) |
| Full core suite | **122 passed in 26s** |
| UI `npm test` | all passed |
| UI `node tests/test-ai-actions.js` | 10 passed |

The handoff warns that curriculum-v2 tests can be slow and that a timeout must not be read as a pass. They are not slow — `test_curriculum_v2.py` is 21 tests in 5.1s. The apparent hang during the first run was the sandbox suspending a backgrounded process, not the suite. Every figure above comes from a foreground run that ran to completion.

Two notes on the handoff's own instructions: the baseline command references `requirements.txt`, but the file is `requirements-dev.txt`; and the checked-in `.venv` is a macOS build, so a fresh interpreter is needed on any other platform.

---

## 3. Findings

Severity is about what the defect costs if it fires, not how hard it is to hit. Each was reproduced against the code before being written up.

### H1 — Garden identity depended on which *other* files existed
`tools/learning_os/ai_actions.py:136` (pre-fix)

`_garden_id` scanned the whole garden tree and appended a disambiguating hash only when more than one file shared a stem. So creating an unrelated note **renamed an existing one**:

```
before: garden-note-seed-one
after : garden-note-seed-one-9b9c831c   # merely because topic/seed-one.md appeared
```

Target ID is the key for `garden-state/<id>.yaml`, `transcriptions/<id>.md`, receipt `updated_ids`, and relationship endpoints. A rename silently orphans all of them — the note looks unshelved, the prior transcription becomes unreachable, and the next delivery writes a second state file. This is the finding I would fix first even if nothing else were touched.

**Fixed:** identity now derives from the note's own relative path and nothing else. Root-level notes keep clean IDs; nested notes carry a path-derived suffix. A genuine collision raises a named error instead of quietly renaming.

**No migration was required** — the live repository has one garden note, zero requests, zero deliveries, zero receipts, and no garden state. This was the last moment when the fix was free.

### H2 — Staleness was repository-wide, not target-scoped
`ai_actions.py:519-522, 632-634` (pre-fix)

`_snapshot()` fingerprints the entire repository, and both `validate_delivery` and `apply_delivery` rejected any delivery whose fingerprint had moved. Editing an unrelated note between preparing and applying was enough:

```
REJECTED THOUGH TARGET UNCHANGED: delivery is stale: expected sha256:68abf7…, current sha256:a2abd8…
```

Feature specification §20.4 scopes staleness to the target ("The Garden entry changed after this AI request was prepared"). In a repository under normal daily use the implemented rule means a prepared request is stale almost immediately, which trains the user to re-prepare reflexively — the opposite of a meaningful guard.

**Fixed:** the hard gate is now the target revision plus the original attachment checksums, re-checked immediately before the write window. The repository fingerprint is retained as provenance in the request and in the receipt's `pre_snapshot`/`post_snapshot`. A changed *target* still hard-rejects with exit code 3, verified end-to-end.

The `--expected-snapshot` guard on `ai-action-prepare` is deliberately **unchanged**. That one is the interface asserting "the projection I am looking at is current", which is the same convention every other gateway write already uses (`stage-note`, `stage-progress`, `source-feedback`), and it is correct at preparation time. The defect was applying that same repository-wide test to work that had *already* been prepared.

### H3 — The provider/adapter boundary was enforced only in the UI
`ai_actions.py:384, 720-726` (pre-fix)

`prepare` checked the provider against `supported_providers` (which lists `claude` and `chatgpt`) but never asked whether an adapter existed. Adapter availability was a Python literal inside `manifest_projection`, and refusal lived in the Obsidian select element. The core therefore accepted:

```
ADAPTER AVAILABILITY: {'manual-bundle': True, 'claude': False, 'chatgpt': False}
PREPARED WITH UNAVAILABLE PROVIDER: {'preferred': 'claude', 'adapter': 'claude'}
```

Under ADR-006 the `los.py` CLI is a first-class interface, so a boundary the UI alone enforces is not enforced. The record also conflated provider with adapter (`adapter: claude` rather than `claude-code`), contradicting specification §8.2.

**Fixed:** new `system/contracts/ai-adapters.yaml` declares adapters, their providers, availability, and supported modes. `prepare` resolves provider → adapter, refuses an unavailable one, and refuses an adapter that does not support the action's interaction mode. The manifest projection reads the same contract. The projection stayed additive — `id` is still the provider name — so the UI needed no change and its tests pass untouched.

### H4 — `.apply.lock` was a crash-permanent, redundant mutex
`ai_actions.py:629-636, 697-700` (pre-fix)

`apply_delivery` created `operations/ai-actions/.apply.lock` with `O_CREAT|O_EXCL` and removed it in a `finally`. A kill between those points leaves the file behind forever, and the next attempt raises:

```
STALE LOCK RAISES: FileExistsError -> [Errno 17] File exists
is AIActionError? False
```

`FileExistsError` is not caught by `main()`'s handlers, so the CLI would print a traceback rather than an actionable refusal — and the subsystem would stay wedged until someone deleted a dotfile they had no reason to know about. It was also redundant: `cmd_ai_action_apply_delivery` already runs inside `_operator_lock`, an `fcntl.flock` the OS releases on process exit.

**Fixed:** removed. The service documents that callers hold the operator lock. A second `flock` on the same path from the same process would have deadlocked, so acquiring one inside the service was not the alternative.

### M5 — The registry was versioned but the service hard-coded the pilot
`ai_actions.py:385-386` (pre-fix)

`if action_id != "garden.shelve": raise ActionPolicyError("only the garden.shelve pilot is implemented")`. A second registry entry listed correctly and then refused for a reason found nowhere in the contract, against acceptance criterion 18.

**Fixed:** actions declare `status: implemented | planned`. `garden.shelve` is marked implemented; anything else refuses with `action <id> is declared planned`, driven by data.

### M6 — Untrusted provider output landed before it was validated
`ai_actions.py:265-281` (pre-fix)

`import_delivery_directory` copied the bundle to its final path under `deliveries/` and only then validated, deleting it on failure. Provider output is untrusted by the handoff's own framing; a rejected bundle should never occupy a canonical-looking path even briefly, and the copy had no size or entry bound.

**Fixed:** bundles stage into `operations/ai-actions/incoming/` (gitignored), validate there, and are published by `os.replace` only on success. Added caps of 512 entries and 32 MB. Symlink rejection retained.

### M7 — Re-shelving silently overwrote the previous transcription
`ai_actions.py:561` (pre-fix)

The destination is target-keyed, so a second approved delivery replaced the first AI reading with `deleted_ids: []` — a loss the receipt actively denied. Recoverable from Git only if the first had been committed.

**Fixed:** an existing transcription must be named explicitly by the delivery (`supersedes: transcription-<target-id>`), otherwise the transaction refuses and reports which request produced the incumbent. Supersession is recorded in the receipt's new `superseded_ids`.

### M8 — The declared write scopes were never enforced
`system/contracts/capabilities.yaml`

The contract declares a `writes:` allowlist per capability, and CLAUDE.md hard rule 12 requires a **post-action scope check** on gateway writes. Nothing read either. The real allowlist was implicit in Python string literals — free to drift from the contract that documents it.

**Fixed:** every canonical destination is checked against the `writes:` prefixes its capability declares, before any bytes are written. Gateway bookkeeping under `operations/ai-actions/` is explicitly exchange state and out of scope by design. A regression test rewrites the contract and confirms the write is refused.

### Low — documented, not changed

- **Naming drift.** The specification says `garden-entry` (§7, §8); the implementation uses `garden-note` consistently across core, contracts, and UI. Changing it now would churn IDs for no gain; the specification should adopt `garden-note`.
- **Manifest version.** `contract-lock.json` declares `manifest_contract_version: 2` while specification §23 anticipates v3. The additive projection into v2 is a reasonable call and should be recorded as an ADR rather than left as a silent difference.
- **Deferred capabilities.** `ai_action.cancel`, `retry`, `history`, `get` (§22) are unimplemented. Correct for Phase 1, but `capabilities.yaml` should say so rather than omit them.
- **Structure.** Specification §24 describes `domain/application/ports/adapters` packages; the implementation is one module, now 971 lines. That is a deliberate deferral, not an oversight — splitting it is a broad rewrite and belongs to Phase 2, when the Claude adapter gives the ports something to be a port *for*.

---

## 4. Verification after the changes

| Check | Before | After |
|---|---|---|
| `tests/test_ai_actions.py` | 6 passed | **14 passed** (8 regression tests added) |
| Full core suite | 122 passed | **130 passed in 29s** |
| `los.py validate` | 0 errors, 0 warnings | **0 errors, 0 warnings** |
| UI `npm test` | all passed | all passed (unchanged) |
| UI `node tests/test-ai-actions.js` | 10 passed | 10 passed (unchanged) |

Beyond the unit tests, the full workflow was exercised through the real CLI against a complete copy of the live repository, including attachments:

1. `ai-action-prepare` wrote the seven-file bundle;
2. an unrelated note was edited — under the old rule this alone invalidated the request;
3. `ai-action-import-delivery` accepted it;
4. `ai-action-apply-delivery` committed, producing a receipt, an AI-derived transcription carrying its provenance, and separate garden state;
5. the original seed's SHA-256 was **unchanged**;
6. the seed itself was then edited and a second delivery was correctly refused as stale with exit code 3, publishing nothing.

Rollback was also observed unintentionally and worked: an invalid repository state (a malformed note from the test scaffold) aborted the transaction, and no garden state, receipt, or transcription survived.

---

## 5. Migration and rollback

Nothing in the canonical tree was migrated, and no authored note was touched. The changes are confined to the gateway module, its contracts, its tests, `.gitignore`, and `system/AI-ACTIONS.md`.

- **Undo the corrections, keep the slice:** `git revert c96f8ef`
- **Undo everything and restore the prior state:** `git checkout codex/module-curriculum-redesign-v2` — the branch is untouched at `1501eb4` (UI: `cf27e77`)
- **Discard the branch entirely:** `git branch -D feature/ai-garden-shelve-v1` in each repository
- **`generated/` is disposable** and rebuilt by `python tools/generate.py`; it is gitignored and carries no state.

One behavioural change is worth stating plainly: a delivery prepared under the old rules and applied under the new ones is now *accepted* in situations where it would previously have been rejected (unrelated repository drift). Since no requests, deliveries, or receipts exist yet, nothing prepared under the old rules is outstanding.

---

## 6. Follow-up clean-up (commit `66d50ce`)

A redundancy pass over the slice, measured by instrumenting a real transaction rather than by reading.

**Dead code.** `FilesystemAIActionRepository.save_receipt` was never called — `apply_delivery` wrote the receipt inline. Replaced by a `receipt_path` helper the live path actually uses.

**Duplicate transaction reads.** `apply_delivery` called `validate_delivery`, which loaded the delivery, the request and the target, then loaded all three again. Validation now hands back what it already read. The two *freshness* guards deliberately still re-read — that is the whole point of checking twice, once at validation and once immediately before the write window.

| Per `apply_delivery` | Before | After |
|---|---|---|
| `delivery.yaml` parsed | 2 | 1 |
| `request.yaml` parsed | 2 | 1 |
| Garden tree walked and hashed | 4 | 3 |
| `capabilities.yaml` parsed | once per staged path | 1 |

The three remaining Garden walks are two intentional guards plus the manifest projection; removing any of them would weaken the staleness check.

**An authored file was being rewritten for nothing.** The apply staged `knowledge/relationships.yaml` whenever the registry was non-empty — not whenever the delivery added a relation. Once you have a single relation on file, every later shelving would re-serialise your hand-written YAML, reformatting it and destroying comments. Now it is written only when a `relationship.create` operation actually adds one, pinned by a test that puts a comment in the file and asserts the bytes are unchanged.

**Structure.** The parallel `staged` / `origin` dictionaries became one map of path → (content, authorising capability), and the manifest's AI shape is defined in exactly one place instead of being duplicated in the fallback.

Line lengths were left alone: the repository has no linter config and its own modules run to 127 characters, so reflowing to 100 would have been my preference imposed as churn.

**Not deleted, flagged instead.** The untracked `system/skills/` holds three pre-v3 skill files (`lecture-unit-builder`, `promotion-ritual`, `semester-kickoff`). All three reference the retired `Masters-Planning/` tree — `check_system.py`, `CONCEPT-INDEX.md`, `DEGREE-WIRING.md` — which v3 replaced and which the installed v3 `lecture-unit-builder` skill explicitly calls retired. `lecture-unit-builder` is a superseded duplicate of a skill you already have installed; the other two have no v3 successor anywhere. They are untracked, so deleting them is unrecoverable, and §5 of the operating contract puts deletion of authored material behind explicit approval. They need either a v3 rewrite or a deliberate goodbye.

> **Resolved 2026-08-14 — v3 rewrite, not goodbye.** All three were rewritten
> against current v3 procedure and no longer name `Masters-Planning/`,
> `check_system.py`, `CONCEPT-INDEX.md` or `DEGREE-WIRING.md`:
> `lecture-unit-builder` → WORKFLOWS §23 (knowledge map + complete material
> menu + choose-before-sequencing; the study map is optional);
> `promotion-ritual` → CLAUDE.md §14 Harvest the Garden, the promotion judgment
> `los.py` deliberately excludes; `semester-kickoff` → WORKFLOWS §24 Turn the
> semester (§19 close / §20 carry / §18 start), replacing the retired
> folder-scaffolding notion of a semester. Each file now delegates procedure to
> the workflow it implements and states only its own gates and quality bar —
> restated procedure is what went stale the first time. Two names are now
> imprecise for what they do (`promotion-ritual` = Garden harvest,
> `semester-kickoff` = the whole term boundary); renaming was left to Aram.

The three empty `Untitled*.canvas` files (each literally `{}`) and four stray `__pycache__` directories were removed.

---

## 7. Recommended next steps

1. Run the suite on your own machine — the checked-in `.venv` is stale and macOS-specific, so `make setup` first.
2. Decide whether `feature/ai-garden-shelve-v1` merges into `codex/module-curriculum-redesign-v2` or stays a branch until Phase 2.
3. Review the untracked `system/skills/` (three skill files) and the three empty `Untitled*.canvas` files — they were deliberately left unstaged and the canvases look like Obsidian accidents.
4. Record the manifest-v2-additive decision and the `garden-note` naming as ADRs so the specification and implementation stop disagreeing on paper.
5. Phase 2 (Claude adapter) is the right moment to split the module along §24's ports and adapters — the seam now exists in `AdapterRegistry`.
