# Before vs after — Plan F on the pre-landing vs landed product

Baseline: `supplemental-s09-friction-2026-09-26` (product `200a361`, world
`13ad2fcc`). This run: S09b (product `8d1cc47`, world `a62b391`).
Corpus, seed (20260924), scale (0), counts (133 commits / 116 notes /
30 arrivals) and build validation (0 errors, 3 warnings) are identical;
only the product revision changed.

## Methodology deltas (read first)

| | Baseline | S09b |
|---|---|---|
| Passes 2-3 | warm (docs not re-read) | fresh by task design (entry + attempts repeated) |
| Worlds | 9 fresh builds (1 per scenario run) | 3 fresh builds (1 per pass) + sanctioned resets, verified clean |
| Answers | pass-1 only in answers.jsonl | per-pass answers.jsonl in each pass dir (deviation: check_run forbids duplicate question ids) |
| Agent-env refusals | YES (write path blocked, S10/S26 AMBIGUOUS) | none (all writes submitted) |
| Setup cost | ~5 s (cached) | 76-100 s (network pip install; environment delta) |

Only baseline-r1 (cold) is directly comparable to S09b passes.

## Per scenario, cold vs S09b

| Scenario | Baseline cold | S09b p1 / p2 / p3 | Verdict |
|---|---|---|---|
| S02 | PWF, 21 calls, 4.5 min, 1 impl read | PWF x3; 19/18/16 calls; 5.0/2.9/4.5 min; 0 impl | same class, similar cost, no impl reads |
| S10 | AMBIGUOUS, 16 calls, 5.2 min, write never submitted | PWF x3; 17/13/13 calls; 5.4/3.5/3.2 min; 2 receipted writes x3 | materially easier: completable |
| S26 | AMBIGUOUS, 11 calls, 1.8 min, goal 2 blocked | PASS x3; 7/6/6 calls; 1.3/1.2/1.6 min; all goals x3 | materially easier: completable |

Answers agree on all five questions (Q06/Q07/Q13/Q15/Q27 identical facts).

## Materially easier on the landed system

1. **Writes are completable from docs.** Baseline never submitted an
   envelope (agent-env refusal + intent hash only in gateway.py). S09b
   committed 9/9 writes with receipts, zero implementation reads:
   WORKFLOWS 25c now carries the complete sealing recipe.
2. **Inbox is product-readable.** Baseline read inbox + working note as
   files; landed `inbox-read` + `search inbox` serve all 7 items (listing
   still via workaround — see F2).
3. **Resume serves the stage excerpt.** "Stopped at step 4" + NEXT line
   arrive via `resume --json`; baseline found them only in files.
4. **Due-dates path is short.** S26 goal 1 in 2 calls (brief + module
   inspect) vs baseline's 6-call workspace hunt. Caveat: S09b did not
   enumerate workspace-level dues (mock-exam todo), so coverage differs.
5. **No implementation reads anywhere.** Baseline: Makefile + gateway.py
   (ikn=true for S10/S26). S09b: 0 files, ikn=false in all 9 runs.

## Remaining reproducible friction (also FINDINGS.md)

- F1 milestone ids uninspectable (baseline F-001, still open, 3/3).
- F2 no inbox list command (baseline, still open, 3/3).
- F4 ledger file absent pre-write (doc gap, 3/3).
- F5 guard sets discoverable only by refusal (3/3).
- F6 envelope ceremony weight for small writes (3/3).
- F3 setup cost per fresh world (environment-dependent).

## Newly observed on the landed system (neutral, needs owner reading)

- Derived-state growth coincides with commits (+494062 B in S10, +490051 B
  in S26, byte-identical across passes); read-only S02 grows zero. Baseline
  saw a read-side 490130 B write from content search. Behavior changed sides.
- Same-status progress updates commit (revisions bump); resume.yaml changes
  without requiring a guard. Observed 3/3.
- Derived cache accumulates across reset scenarios (gitignored files survive
  `clean -fd`); canonical state unaffected, reads stayed fresh.

## Baseline uncertainties resolved by S09b

- Gateway accepts S10 envelopes (operator channel, operator-approval): yes.
- Guard sets: stage.note.write {unit}, stage.progress.update {unit,
  study-map}; module guard not needed (baseline guessed module+study-map+unit).
- Capture on operator channel + capture-request guard: accepted 3/3
  (baseline guessed direct-user-gesture).
- Still open: idempotency-key reuse after a refused attempt; whether
  milestones should be records; generated/-refresh mechanics post-commit.

## Coverage caveats

- Workspace enumeration (`search '' --type workspace`) and literal-search
  limits (caching/cache, aliases) were baseline frictions S09b did not
  exercise; neither confirmed fixed nor confirmed remaining.
- S09b S26 goal 1 answered registered exams only; baseline additionally
  surfaced the workspace mock-exam todo. Same question, different depth.
