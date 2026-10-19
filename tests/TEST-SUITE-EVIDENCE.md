# Test-suite optimization evidence (2026-10-19)

This note records the measurements behind the derived-digest
normalization, the rich-world template, and `make test-parallel`. It is
evidence for review, not a gate. The audit scripts that produced the
historical numbers (`recording_diff.py`, `whatif_digest_rule.py`,
`size_accounting.py`) were run read-only from the audit worktree; their
method is described here so the numbers can be checked without them.

## Size and runtime baseline (old main, 074f4717)

- Production Python: 59,535 code lines in 267 files.
- Executable test + harness Python: 74,493 code lines (R_logic = 1.251).
- Recorded expectations: 81,402 lines in 1,089 files. Counting all
  tracked test material gives R_total = 4.485, so the perceived size is
  mostly recorded/fixture data, not test logic.
- Serial baseline run: 7,774 tests in 48m03s (7,765 passed; the only
  two failures were a missing Scrut binary in that venv, since fixed).
  Slowest files: scenario effects ~690s, refusal sites ~654s,
  architecture output ~459s — about 65% of all testcase time.

## How the 71.9% rewrite reduction was calculated

Corpus: every commit on `main` that rewrote at least one file under
`tests/scenarios/recorded/` — 70 commits, 3,586 changed recording files
(the denominator is file rewrites, not commits).

Method: for each changed file, both the parent and the commit version
were classified leaf-by-leaf (semantic outcome, canonical effect,
digest, output text, structure, other). 2,828 of 3,586 rewrites (78.9%)
changed only digest leaves — pure digest cascades with identical
behaviour. The candidate rule was then applied to *both* sides of every
changed file: number `intent_sha256`/`subject_sha256` values by first
appearance (`INTENT<n>`) and number session-ledger `paths` row hashes
for `operations/` files (`LEDGER<n>`), leaving canonical hashes
untouched. A rewrite "vanishes" when the two normalized sides become
equal. 2,578 of 3,586 vanish: **71.9%**.

Conditions and limitations:

- The rule was measured separately per family: INTENT-only removes
  0.5% of rewrites, LEDGER-only 0%, both together 71.9% — one fixture
  change moves both hashes, so both must be tokenized.
- Tokenization preserves equality relations (same value keeps the same
  token, distinct values keep distinct tokens), so it cannot make two
  different intents compare equal. It deliberately gives up the literal
  hash bytes, whose inputs (the snapshot and request) are recorded and
  compared field-by-field elsewhere.
- The corpus is historical and from the old main; it shows how much
  past churn the rule would have prevented, not a guarantee about
  future commits. No recordings were regenerated to obtain it.
- Cross-check on the C1 candidate diff (213 changed recordings):
  170 pure digest cascades, 42 representation-only, 1 semantic.

Since the independent review, discovery is restricted to well-formed
digests (`sha256:<64 lower hex>` for intent keys, bare `<64 lower hex>`
for ledger rows), and derived replacement is position-aware so a
canonical digest keeps its exact value even when the same hash is also
a derived digest. Negative controls for malformed digests, canonical
collisions, request-content changes, and token stability live with the
other `test_normalize_*` tests in `test_scenarios_effects.py`.

## Timing

- `make test-parallel` (4 workers by default on this branch,
  `WORKERS` configurable) ran 7,153 passed, 2 skipped, 2 xfailed in
  8m29s on the old-main branch at up to 12 workers.
- The serial scenario population (effects, session, recovery, health,
  both zz aggregators, one session) ran 1,770 passed, 1 skipped in
  20m15s.
- Limitation: the 48m03s serial figure is the whole suite serially,
  while the parallel figure excludes the two zz aggregators and
  deselects `live_install`; they are not a perfectly controlled
  benchmark pair. The honest claim is that parallel feedback is several
  times faster while the serial gate remains authoritative.

## Integrated verification (hardened pair, 2026-10-19)

Branch `test-suite/integration-hardened-2026-10-19`: hardened Core
`aab5f24e` plus the test-suite commits, against UI `60214f0b`.

- All 20 `test_normalize_*` tests pass, including the five new negative
  controls (malformed digests, valid-vs-malformed, canonical collision,
  request-change detection, token stability).
- Serial scenario population: 1,787 passed, 1 skipped in 20m58s.
- `make test-parallel` (4 workers): 7,309 passed, 4 skipped, 2 xfailed
  in 12m25s.
- `make system-check`: 7,933 passed, 5 skipped, 2 xfailed, and one
  failure in 51m06s — `test_perimeter.py::
  test_every_pending_disposition_entry_is_still_on_disk`. That test
  resolves the wrapper root as the repository's grandparent and
  expects `HANDOFF.md`/`original_research.txt` there; in a workbench
  worktree layout they are absent. It fails identically on the older
  published test-suite branch in the same layout and passes in the
  main checkout layout, so it is a pre-existing layout limitation, not
  an integration regression. The UI check then ran separately and
  passed (12,750 differential cases; deterministic build). The
  verified-pair stamp was not taken, because the serial gate did not
  complete green in this layout.
- Real-Obsidian and raw-vault restoration obligations (C3) remain open
  and are not certified by any of these runs.

## What was not changed

No test was deleted or thinned. `make system-check` is unchanged and
remains the paired acceptance gate; `make test-parallel` is developer
feedback only. Transaction, recovery, fault-injection, and UI-recovery
tests were preserved as-is.
