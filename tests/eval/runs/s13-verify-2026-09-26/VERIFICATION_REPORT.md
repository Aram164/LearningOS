# S13 hostile verification report (white-box verifier)

- Date: 2026-09-26. Branch: `muse/eval-s13-verify-2026-09-26`, forked from
  exact `7ffad843c48a61bc68c61aee7f29c0c274b8c1de` (frozen S11–S12 repair
  candidate; neither it nor the repair branch was modified).
- Product under test: the frozen repair tip. Base comparison: `84bda98`
  (S10 tip, pre-repair). Nothing was patched in this session.
- Worlds (seed 20260924 throughout): `w-tip` 78154b2b (scale 0, WORKTREE),
  `w-base` d4a27025 (scale 0, 84bda98), `w-tip-2k` a31a3804,
  `w-base-2k` 822c114c, `w-tip-10k` 62cac754, `w-base-10k` 31322632,
  plus `w-tip-b` (functional clone) and `w-tip-twin` (independent S24
  rebuild, head 78154b2b — identical). All under `/tmp/s13/` (outside repo).
- Oracle: opened into `/tmp/s13-oracle/` (throwaway, outside repo), README +
  AUTHOR-NOTES §§8–13 read (§14 does not exist), plaintext removed at the
  end. This report paraphrases throughout and quotes no oracle sentence;
  probe/question/scenario ids are the refs.
- Method: every repair was attacked with its campaign-original repro plus
  adversarial non-synthetic inputs; base-vs-tip controls where a behavior
  could be pre-existing. All world probes ran each world's own product
  code. Envelope writes used a docs-only sealer (WORKFLOWS §25c recipe +
  capability-schema CLI, stdlib only, zero implementation imports), which
  is itself the JF-05 sufficiency proof.

## Verdicts per repair

| Repair | Verdict | Evidence |
|---|---|---|
| JF-09 supersedes projection | HELD | Orig + multi-valid + body mentions + empty/self + dangling fail-closed; incoming edges plain sorted id strings; every unprojectable input validator-flagged with file named |
| JF-10 scope_sources default | HELD | Orig + null + wrongtype + other-module + 16-unit strip; projected default `[]`; clean-world manifest bytes identical base-vs-tip |
| JF-08 request-id gate | HELD | 19/19: 12 malformed shapes refused exit 1 pre-persist, valid/minted publish, planted bundles flagged AI-REQUEST-ID/AI-REQUEST-BUNDLE, boundary ids sync with projection |
| JF-11 write-time mapping | HELD | E-PARSE (note + module) and poison-bundle probes: exit 2 VALIDATION_FAILED retryable:false, zero orphan journals; exact-fix retry commits; bytes-changed retry STALE then re-seal commits; OSError stays typed retryable:true |
| JF-13 ledger detection | HELD | Duplicate-key (2 and 3 receipts) flagged naming both/all; malformed/dir idempotency ledger flagged; missing fine; intact replay byte-identical; rebuild confirmed absent (replay denial after loss) |
| JF-01 setup recovery | HELD + finding | 3.11-fail → 3.12 retry exit 0 with rebuild; reuse/no-python/version-switch legs pass; recovered venv validates clean. Finding F-s13-verify-01 (minor, repair-introduced): bogus PYTHON deletes the healthy .venv before failing |
| JF-05 envelope docs | HELD | From-docs-only capture AND stage.note.write committed; empty-guard refusal names the missing artifact; tamper→UNCONFIRMED, conflict→IDEMPOTENCY_CONFLICT, stale→exit 3; all five gap facts present + README bridge |
| JF-07 delivery docs+errors | HELD | From-docs-only delivery: import 0, validate 0, full envelope apply 0 with receipt (past the ledger's claim); 6 defects in one round; adapter names both sides; id/request_id named; 12+omission cap exact |
| JF-04 trace parenting | HELD | Ambient trace: 2 ops, fresh traces, 28/28 records parented, fresh attempt spans; malformed/empty/unset clean; base control still merges (probe-sensitive) |
| JF-03 suite spans | HELD | Full fresh-install test-fast leaves zero span files (only .gitkeep); targeted files 66/66 same; world tree clean after |
| JF-19 operations labels | HELD | Settlement incl. past-commit reason; behind-manifest verify-observation settled by views; conflict→NOT_COMMITTED; shared id names both keys; unknown id; SETTLED/REFUSED labels |
| JF-21 read agreement | HELD | 7/7 caught kills agree (single/batch/search pre-state, bootstrap green, healed pre-state); base control 4/4 exposes paused-vs-active split; S17 probe 20 trials zero PARTIAL |
| JF-14 read gaps | HELD | 17/17: stage-via-map, garden search+read, inbox text/missing/escape×2/abs/binary/symlink/dot-read/name-search/bytes-absent/dot-hidden/stale-guard; durable path unaffected |
| JF-17 resume progress | HELD | 18→20 lines + marker excerpt + Next line; dossier key moves; empty/missing→nothing-recorded-yet; escaping path→null without leak; Next-Action residual confirmed deferred |
| JF-23 small items | HELD | Commit-date sourcing (uncommitted stays, commit moves); atlas schema typed + string-target cleanly refused; state+deprecated on all 13 rows/6 types; revision-0 documented |
| JF-20 dir-shape recovery | HELD + wart | Empty dir rebuilt byte-identically; full dir refused exit 2 naming recovery, content kept; GEN-JSON/HEADER; status count; md-dir rebuilt; missing→warning+rebuild. Wart (minor, in improved code): GEN-JSON mislabels a symlink as "a directory" (base crashes there instead) |
| JF-18 dirty stamp | HELD | Marker on dirty canonical (incl. untracked-in-canonical + staged), absent for untracked-root scratch; clean stamp byte-identical to base; all views carry it |
| JF-02 suite health | HELD | Fresh-install world test-fast green: 2269 passed, 18 skipped, 107 deselected, rc=0; ambient-TRACEPARENT diagnostics 44 passed; pinned JF-11/OSError tests pass |
| S23 scale | PARTIAL | Warm-path extrapolation confirmed (10k warm 11.2s ∈ predicted 12–15s, 15.7× better); cold path still 154s (1.5×). Defect NOT closed (see §S23) |
| S19/S24 determinism | HELD | Rebuild-after-delete 20/20 byte-identical; twin build same HEAD, cross-directory raw-identical |
| S22 concurrency | HELD | 10 committed + 20 clean conflicts, receipts match, no dup keys, no journals, validate clean |

## New findings (failures.jsonl)

- F-s13-verify-01 (S01, minor, repair-introduced): `make setup
  PYTHON=<nonexistent>` deletes the working .venv, then fails (Error 127),
  leaving no environment. Base left .venv untouched (venv creation failed
  first). The repair's remove-before-validate order is the cause.
- F-s13-verify-02 (S20, pre-existing, base-identical traceback):
  `tools/validate.py` crashes with an uncaught TypeError (rules/references
  check, dict used as dict key) on a unit carrying a mixed-type list,
  instead of naming E SCHEMA. Reads fail closed; no write path reachable
  (snapshot unreadable). Same family as JF-20, different shape, unclaimed
  by the repairs.
- F-s13-verify-03 (S19, minor wart in improved code): the new GEN-JSON
  check reports a broken symlink at a view path as "a directory".
  Recovery advice still applies; base crashes with FileNotFoundError there.
- F-s13-verify-04 (S16, pre-existing, base-identical traceback):
  `ai-action-import-delivery` throws a raw traceback on an unparseable
  delivery.yaml instead of a DeliveryValidationError.

## Cross-cutting properties (all verified, no synthetic special-casing)

- Validator/projectability consistency: every unprojectable state probed
  (9 shapes across JF-08/09/10/11) is validator-flagged with its file; no
  validator-clean-but-unprojectable state found. Failing reads name the
  defect or the contract; failing writes name the defect.
- Persistence-before-validation gone: refused prepares persist nothing
  (19 cases); refused delivery imports leave deliveries/ and incoming/
  untouched (6 cases).
- Failed writes leave no poisoned state: zero orphan journal files across
  JF-11/JF-13/S17/S22; canonical intact after refusals; receipts only for
  commits.
- Transaction/read recovery consistency: single/batch/search/bootstrap
  agree post-kill (7/7); interrupt probe 20 trials pre-state/finished,
  zero PARTIAL; S22 30 racers serialize cleanly.
- TRACEPARENT no longer merges: per-process operation identity with
  parent linkage; ambient/malformed/empty/unset all isolated.
- Diagnostic semantics: settlement rule, conflict proof, reused-id
  explanations, unknown-id shape all as documented in §28.
- Byte-identical rebuilds: S19 20/20 raw-identical; clean-world
  projection bytes identical base-vs-tip (only the cross-revision
  fingerprint header differs).
- Crash/directory-shape handling: 8 shapes across generate/status/
  validate refuse or recover with named errors, zero tracebacks on tip
  (one pre-existing validator traceback on a non-shape input class:
  F-s13-verify-02).
- First-run/setup: half-built venv recovery, docs-only first capture,
  fresh-install suite green with zero spans (one minor repair-introduced
  footgun: F-s13-verify-01).

## Deferred surface (exactly as recorded)

- No ledger rebuild: replay consults ledgers only; post-loss replay
  denies the committed receipt; no rebuild code in the diff; replay paths
  untouched.
- No v16 records: manifest contract v15 both revisions, identical
  schema_sha256; records[] carries the same 12 types (no garden-note /
  inbox-item).
- JF-15 still one-directional: documented in OPERATOR; reverse edges
  require the note's own declaration (verified both directions).
- No Next-Action capability: 38 gateway commands, none advances a
  workspace aim; resume still shows the pre-write aim after progress.
- No JF-25: no capture-to-note or successor-note command exists.
- UI parity item still open: `gateway-v2.ts` absent; parity test skips
  by design (27 passed, 1 skipped); IDEMPOTENCY_CONFLICT addition owed.

## Branch audit (84bda98..7ffad84)

- 61 files, +2671/−133. Every file maps to a PATCH_LEDGER.md section
  (product diff reviewed in full, 2048 lines): Makefile (JF-01),
  AI-ACTIONS/OPERATOR/WORKFLOWS/README/capabilities.yaml/atlas schema
  (docs), ai_actions service/storage/support (JF-07/08), commands
  atlas/capability/operations/query/reads/resume/support (JF-11/19/14/
  17/21/23), atlas_question/payloads (JF-23), derived engine/store
  (S23), diagnostics context/conventions/resolver/store/tracer (JF-04/
  19), errors (JF-11), genout common/concepts/derived_generation/
  outputs/records_curriculum/resume_dossier (JF-18/09/node-bump/20/10/
  17), rules core/generated/projects (JF-08/20/13), transactions (JF-11),
  los.py (JF-14 CLI + JF-08 help), conftest (JF-03), 19 test files (pins
  + marks + fixes as claimed), PATCH_LEDGER.md itself.
- `tests/eval/` diff is PATCH_LEDGER.md only: harness, corpus, scenarios
  and prior runs untouched.
- Nothing beyond the ledger's claims. Replay/commit logic, manifest
  contract files, and record-type inventory untouched.

## Baselines (same-environment tip-vs-base)

- test_real_repo_manifest_replay: FAILS identically both revisions
  (FileNotFoundError, untracked ai-request-sad-l04-pilot bundle).
- test_every_pending_disposition_entry_is_still_on_disk: FAILS identically
  both revisions (original_research.txt assertion).
- The four unreadable-path boundary tests: PASS identically both
  revisions in this environment (the audit-harness chmod failures are
  environment-specific; behavior here is base==tip).

## S23 scale verdict: PARTIAL (defect not closed)

Direct measurement of the original ~10,116-note workload on the repaired
product (scale_bench.py, 3 reps, uptime-bracketed), with same-environment
base calibration that reproduces S08 within 4%:

| Notes | Path | S08 | Base (S13) | Tip (S13) | Spread (tip) |
|---|---|---|---|---|---|
| 2,116 | content cold | 11.688 | 11.978 | 8.706 | 8.606–8.855 |
| 2,116 | content warm | 8.846 | 9.044 | 2.467 | 2.438–2.501 |
| 10,116 | content cold | 227.833 | 234.802 | 153.984 | 152.443–154.015 |
| 10,116 | content warm | 169.318 | 175.579 | 11.236 | 11.165–11.331 |
| 10,116 | metadata | 4.678 | 4.929 | 4.833 | 4.809–4.911 |
| 10,116 | generate cold/warm | 5.014/4.851 | 5.212/5.127 | 5.189/5.149 | tight |

(All exits 0; every spread far below its median. Evidence:
`evidence/bench-*.json`, `evidence/uptime-*.log`.)

- The repair's warm-path extrapolation is CONFIRMED: 11.2s at 10k lands
  inside the predicted 12–15s linear remainder (15.7× better than base).
- The cold path is NOT fixed: 154s at 10k (1.5× better), still
  superlinear across sizes (8.7s → 154s for 4.8× notes). A back-to-back
  retest on a warm store answers in 11.8s then 9.5s with byte-identical
  answers, so the 154s is one-time cold-store fill, not per-search
  structure — but it is the cost every cold session pays, and the
  ledger's accepted residual (cold O(N²) writes/fill) is where it lives.
- The S23 SHOULD (≈2s interactive reads at 2,000 notes) is still missed
  on cold (8.7s) and marginally missed on warm (2.47s); warm ≈ cold
  generate is unchanged (5.19 vs 5.15s — the recorded no-incremental-
  benefit residual).
- Per the mandatory rule, the 10k extrapolation is accepted only for the
  warm path it named, and the scaling defect stays open.
