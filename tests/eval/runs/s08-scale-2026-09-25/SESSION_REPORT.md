# Session report — s08-scale-2026-09-25

- Plan / role: P — scale-investigator
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fca (scale-0; see below for all four) · Eval revision: 3c30d03e2c2c2805b4d52288e3d69f0e6ebd4bd1
- Started / finished: 2026-09-25T14:32:50Z / 2026-09-25T15:14:01Z

## What I set out to do

Run plan P (scenario S23): build worlds at --scale 0/500/2000/10000 (116/616/2116/10116 notes),
run tools/scale_bench.py with 3 reps on each, bracket every series with uptime, and report
medians only where spread <= median.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S23 | PERFORMANCE_FAILURE | search --content median 227.8s at 10116 notes, superlinear across sizes; all other ops <= 5.5s, all exits 0 |

Median seconds by world size (all 44 medians reportable; spreads far below medians):

| op | 116 notes | 616 notes | 2116 notes | 10116 notes |
|---|---|---|---|---|
| generate_cold | 0.36 | 0.59 | 1.35 | 5.01 |
| generate_warm | 0.35 | 0.57 | 1.27 | 4.85 |
| validate | 0.27 | 0.43 | 0.88 | 3.29 |
| search_metadata | 0.38 | 0.59 | 1.25 | 4.68 |
| search_content | 0.36 | 1.77 | 11.69 | 227.83 |
| inspect_note | 0.38 | 0.59 | 1.26 | 4.67 |
| related_note | 0.38 | 0.59 | 1.25 | 4.68 |
| bootstrap_brief | 0.40 | 0.65 | 1.42 | 5.47 |
| resume | 0.24 | 0.36 | 0.76 | 2.85 |
| incremental_generate | 0.35 | 0.57 | 1.29 | 4.91 |
| incremental_search | 0.30 | 1.26 | 8.85 | 169.32 |

Full per-op min/max/samples/exit codes: evidence/scale-{0,500,2000,10000}.json.
Derived bytes: 1.3MB / 21.9MB / 83.8MB / 412.7MB.

## Failures (see failures.jsonl)

No failures.jsonl — every bench command exited 0 at every size. The PERFORMANCE_FAILURE
classification is the finding itself (content-search latency), not an execution failure.

## Friction that cost the most

None from the product: the harness path (build_world.py, scale_bench.py, observe.py) worked
exactly as documented, zero retries. Environment friction only: the managed shell sandbox
denied writes to ~/los-eval and the repo worktree, so seven commands ran with escalated
permission (one initial PermissionError, then escalated throughout). No file outside the
four world dirs, /tmp scratch, and tests/eval/runs/s08-scale-2026-09-25/ was touched.

## What the product made easy

Deterministic world builds with a recorded build manifest (EVAL-WORLD.json); a single
bench command covering all ordinary operations with machine-readable output; observer
snapshots that made the before/after check trivial.

## Behind the curtain

- No receipts, no inflight journals, no request ids: the bench issues no operator writes.
  The per-rep append-and-restore of note-cfs-fair-share left canonical_digest_changed=false
  in all four diffs; git_status stayed empty and all four world HEADs unchanged.
- Only change in any world: generated/ populated from empty (1.3–413MB, 140–10140 files).
- Warm generate ≈ cold generate at every size (e.g. 4.85s vs 5.01s at 10k), i.e. no
  incremental benefit — every generate looks like a full rebuild.
- Content search grows superlinearly (0.36 → 1.77 → 11.69 → 227.8s for 116 → 616 → 2116 →
  10116 notes) while metadata search stays linear-ish — consistent with an unindexed scan
  path. The 10k series ran under the lowest load of the day (1.8–2.7), so machine noise
  does not explain it.

## Uncertainties

- Shared-machine load varied across series; mitigated by 3 reps, tight spreads, and
  uptime bracketing (evidence/uptime-scale*.log). uptime stamps are machine-local (UTC+2).
- World HEADs: scale-0 13ad2fca, scale-500 bd7179af, scale-2000 53163d2c, scale-10000 cef2e239.

## Deviations from the protocol

See run.json → deviations (four sibling world dirs; escalated shell; scale-0 as primary
before/after state with all four snapshotted).

## NOT TESTED

Anything needing the Obsidian UI (none in this plan).
