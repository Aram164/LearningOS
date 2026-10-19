# Handoff to Codex — intelligence gaps: what Muse did, what's missing (2026-09-28)

Read `AGENTS.md` at the `semestercontext/` root first (your role), then the
repair-branch `AGENTS.md` + `system/OPERATOR.md` before touching Core. This
file is a status handoff, not a plan: the planning is yours.

## Where things stand

Branch `muse/intelligence-gaps-2026-09-28`, local, clean, unmerged, two commits
on top of `main` (`6148580`, the merged H5 candidate):

- `37092bf` — ephemeral session counts + scan feed wiring (`--feed`),
  detector precedence in `rank_clusters`, PCC coverage ranking, work record
  (heartbeat decision, ratification draft), contract wording. Full suite green
  at commit time: 2538 passed / 1 skipped / 1 deselected (`not live_install`).
- `c68a400` — adversarial fixes: duplicate feed sets refuse, noted inspection
  files dedupe, full precedence order pinned, fed-scan-writes-nothing test.
  Synthesis group 555 + `make check` + warning baseline + `make lint` green.
  Full suite was NOT re-run on `c68a400` (touches only the new module + tests).

Earlier this session (done, verified): H5 repair branches merged to `main` in
both repos (Core `6148580`, UI `1548fb9`); tag `eval-h5-d059320` on `d059320`;
`PATCH_LEDGER.md` consolidated. No push anywhere (standing rule).

## What Muse verified (on disk, this session)

- Feed validation fails closed (33-case fuzz, zero tracebacks); empty feed ==
  no feed (300 randomized inputs); four mutations caught red and reverted.
- Live-operator session: scan emits 545 goals / 77 groups (493 "due" before
  the 2026-09-30 AML exam); resume pointer missing; 0/449 stages complete,
  0 feedback records, 0 reviewed notes; local extraction works (ESL pp. 56–57);
  remote routes return `spans: []` silently; `material-context` returns 0/27
  (all unreviewed).
- Data hygiene: placeholder URL `oldSol-randomstringfdsafsa` in 7 live routes
  (`curriculum/modules/module-hu-aml/source-map.yaml` ~L5334–5431).

## What's missing for the end product

1. **Merge the branch.** Needs Aram's word + full suite re-run on HEAD first.
2. **Four operator fixes** (Muse's explanation to Aram, this session; suggested
   order): (a) bulk goal triage — `--detector` / `--tier-below` deferral flags
   plus `revisit_on` ledger expiry (schema has no expiry today; deferred
   suppresses forever); (b) study mode for resume — "open X at locator" for
   the nearest-exam current stage, assembly only; (c) micro-capture — one-tap
   session log (UI work) or agent "log:" convention (zero code); (d) remote
   routes fail loudly — print fetch→`make inventory`→re-span directive instead
   of empty `spans`. Design details and rejected alternatives are in Muse's
   session; re-derive, don't assume.
3. **Amendment ratification.** Draft one-liner sits in
   `work/proposals/intelligence-gaps-2026-09-28-record.md` — it becomes binding
   only in Aram's own words.
4. **CS229 URL.** True URL or route removal — Aram's call; source-map edits go
   through the plan capabilities, never hand edits.
5. **Recorded follow-ups** (same record file): runtime VOQ/dossier coverage
   source; `unit.plan.revise` Phase B extension + dossier-publish lineage
   question (`pcc-coverage-ranking-2026-09-28.md` items 1–2); VOQ coverage for
   new predicates.
6. **Push / paired CI.** Standing no-push; remote gates unproven on current
   code. Aram's decision like any push.

## Pointers (reference, don't copy)

- Code: `tools/learning_os/semantics/session_counts.py`, `scan.py`
  (`ScanInput`, `intelligence_scan`), `goals.py` (`DETECTOR_PRECEDENCE`,
  `rank_clusters`), `commands/intelligence.py` (`--feed`), `tools/los.py`.
- Tests: `tests/test_session_counts.py` (28), `tests/group_map.py` (synthesis).
- Docs: `system/SEMANTIC-CONTRACT.md` (feed + precedence wording),
  `work/proposals/pcc-coverage-ranking-2026-09-28.md`,
  `work/proposals/intelligence-gaps-2026-09-28-record.md`.
- Probes (throwaway, `/tmp`, not committed): `/tmp/feed_fuzz.py`,
  `/tmp/parity_probe.py`.
