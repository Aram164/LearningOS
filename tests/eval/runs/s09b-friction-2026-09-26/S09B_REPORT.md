# S09b — agent-friction verification on the landed system (Plan F rerun)

- Source revision (frozen): `8d1cc470d73a252bb7d87dc36c81e71e5db7c0d2`
- World revisions: `a62b39169269ba26e13b7fbda9e3ad56367b1ef9` x3 (identical)
- Eval revision: `3c30d03e2c2c2805b4d52288e3d69f0e6ebd4bd1` (corpus `ca9429af...`, seed 20260924, scale 0)
- Baseline: `supplemental-s09-friction-2026-09-26` (product `200a361`, world `13ad2fcc`)
- Blind: yes. Model: Muse Code powered by Meta Muse Spark. No repairs performed.

## Method

Three independent passes of Plan F (S02 with Q06/Q07/Q13/Q15/Q27, S10, S26),
each from a fresh world built with `--source-rev 8d1cc47...`; per-scenario
freshness via sanctioned `git reset --hard` + `clean -fd`, verified clean.
Each pass treated as a fresh consumer run: entry reads and product-facing
attempts repeated, never shortcut with earlier-pass knowledge. Tool calls =
consumer tool invocations (world commands + doc reads); harness excluded.
Per-pass records: `s09b-pass{1,2,3}-2026-09-26/` (run.json, results,
answers.jsonl, observations, SESSION_REPORT.md). Machine-readable aggregate:
`AGGREGATE.json`. Comparison: `COMPARISON.md`. Findings: `FINDINGS.md`.

## Results

| Scenario | p1 | p2 | p3 | Median (range) calls | Median (range) min | First route median |
|---|---|---|---|---|---|---|
| S02 | PWF 19/5.0 | PWF 18/2.9 | PWF 16/4.5 | 18 (16-19) | 4.5 (2.9-5.0) | ~99 s (setup-bound) |
| S10 | PWF 17/5.4 | PWF 13/3.5 | PWF 13/3.2 | 13 (13-17) | 3.5 (3.2-5.4) | 13 s |
| S26 | PASS 7/1.3 | PASS 6/1.2 | PASS 6/1.6 | 6 (6-7) | 1.3 (1.2-1.6) | 17 s |

Per-pass totals: 43 / 37 / 35 calls (median 37); 11.7 / 7.6 / 9.3 min.
9/9 scenario runs completed from product/operator docs alone. Zero
failures.jsonl entries. Zero implementation files read (see below).

## Friction (reproduced 3/3 unless noted)

| ID | Friction | Cause | Cost/run |
|---|---|---|---|
| F1 | milestone_ids advertised but not inspectable (baseline F-001) | doc | 1 call + 2 failed cmds |
| F2 | no inbox listing; `search inbox` workaround undocumented | doc | 2 calls |
| F3 | `make setup` 76-100 s per fresh world (network) | env+doc | dominates first contact |
| F4 | revision ledger file absent pre-write, 25c silent on it | doc | 1 failed read + inference |
| F5 | exact guard set per capability found only via refusal | doc | 1 refusal + reseal |
| F6 | envelope ceremony weight for small writes (no sealing helper) | doc | ~2-4 min cold |
| O1/O2 | own sandbox/quoting mistakes (one-offs) | agent | 1 + 3 calls |

## Implementation knowledge: NOT required

Explicit statement: no implementation file (`tools/**`, `tests/**`,
Makefile targets beyond documented use) was read in any of the 9 scenario
runs to complete a task. The write path (envelope recipe, intent hash,
guards, approval) was completed from WORKFLOWS 25c + capability schemas +
designed refusal messages. No undocumented repository knowledge and no hidden
protocol inference beyond the guard-set trial (F5, recovered via the refusal
text itself) was needed. Baseline needed 3 implementation reads.

## Before vs after (summary; full: COMPARISON.md)

Materially easier on the landed system: (1) writes completable with
receipts (baseline: blocked/AMBIGUOUS); (2) inbox product-readable
(`inbox-read`); (3) resume serves the stage excerpt; (4) due-dates in
2 calls; (5) zero implementation reads. Remaining: F1, F2, F4, F5, F6
(and setup cost F3). Newly observed neutral behavior: derived-state growth
on commits (+494062/+490051 B, byte-identical across passes; read-only S02
zero), same-status progress commits, resume.yaml unguarded. Baseline's open
uncertainties on gateway acceptance, guard sets, and capture channel are
resolved (yes; {unit} / {unit, study-map}; operator channel accepted).
Coverage caveats: workspace enumeration and literal-search limits from the
baseline were not exercised here; S26 goal 1 answered exams only while the
baseline also surfaced a workspace todo.

## Evidence integrity

`check_run`: 3/3 scenario results, 0 problems, in each of the three pass
dirs (see CHECK_RUN.txt). Observer diffs: S02 zero-change 3/3; S10 2
modified + 4 transaction files + 3 ops 3/3; S26 4 transaction/inbox files +
1 op 3/3. Working tree adds only `tests/eval/runs/s09b-*/`; HEAD stays on
`8d1cc47...` on branch `muse/s09b-friction-2026-09-26`; nothing pushed to
main. Worlds at /tmp/s09b-worlds (disposable); harness worktree detached at
the eval revision (removed after use).

## Uncertainties / deviations / NOT TESTED

- Idempotency-key reuse after refusal; generated/-refresh mechanics; resume
  guard model; Q27 routing and 3-week frame judgment calls (as in pass reports).
- Deviations: per-pass run dirs; 3 builds + resets; /tmp paths; setup once
  per pass; no failures.jsonl (nothing failure-class observed).
- NOT TESTED: Obsidian UI; repair/verify/judge phases; anything outside Plan F.

Phase 9b measurement complete — no repairs performed.
