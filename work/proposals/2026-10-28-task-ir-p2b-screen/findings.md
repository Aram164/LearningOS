# Task IR P2b screening findings — 2026-10-28

Executed under the revised, cheapest-valid authorization: offline analysis,
one matched B/C pair, no automatic expansion. The 108-session campaign is
withdrawn. No dollar figure from any earlier estimate is used anywhere in
this record; the earlier Muse pricing estimate is explicitly not relied on.

## Phase 1 — offline analysis (zero model tokens)

Reusing the P2a traces and the three demonstration sessions:

1. **Model-call count, not per-call size, drives live cost.** Mean input per
   call was 30.0k (B) vs 36.3k (C) in the demonstrations; the totals differ
   mainly because C needed 8 calls to B's 5.
2. **C's extra calls were orientation, and the prompt caused part of it.**
   Arm C's demo agent listed the fixture tree, read a unit file, and searched
   the Core tools directory before writing its spec. Arm B's demo prompt
   contained an exact plan template; Arm C's contained prose. That is a
   scaffolding asymmetry, not intrinsic IR cost.
3. **One intrinsic C cost is real:** in the scripted P2-07 traces, C's apply
   returned 5,264 bytes, re-reporting operation outputs already delivered at
   preview (4,983 bytes). B's submit returned 1,606 bytes. Returned-context
   verbosity sits in the Task IR report shape, and only a result-projection
   change (the P3 hypothesis) addresses it.
4. Arm A's demo friction (help probes, repeated discovery reads) is real
   but does not bear on the B-versus-C decision, so Arm A was not rerun.

Prompt v2 therefore equalized scaffolding: identical common text and review
rule, an exact artifact template for each arm, fixture orientation, and a
fixed scratch location. Recorded as a protocol amendment before the pair ran.

## Phase 2 — one matched screening pair (P2-07, prompt v2)

Both sessions committed with oracle-clean state (only `angle` changed, stable
route id materialized, one receipt each, review step before apply in both).

| Measure | B — runner | C — Task IR |
|---|---|---|
| Model calls | 7 | 6 |
| Input tokens (incl. cached) | 209,829 | 178,869 |
| Non-cached input | 60,897 | 61,029 |
| Output tokens | 1,508 | 1,200 |
| Tool calls | 6 | 5 |
| Wall time | 46.1 s | 33.6 s |

Cumulative pair input: **388,698 tokens**, below the 1M pause threshold.
Session-log sums match the runner usage summaries, as in the demonstrations.

## Phase 3 — decision: stop here

Arm C was not substantially more expensive in this pair; it was marginally
cheaper in gross input and identical in non-cached input. But that edge is
smaller than ordinary run-to-run variance: Arm B alone has produced 149,782
and 209,829 input tokens on the same scenario under two prompt versions, a
40% swing. A 15% single-pair difference is not a plausible benefit signal,
and the expansion criterion (a credible C advantage) is therefore not met.

Per the sequential decision rule:

- **P2b stops.** This is a negative screening result for the efficiency
  hypothesis at current scope — not a statistically conclusive rejection,
  and not a safety finding (all live and scripted safety behaviour remains
  correct in both arms).
- The fair summary across all live evidence: after prompt normalization,
  typed orchestration costs about the same as the existing runner on the
  one workflow measured, with fewer, larger interactions. The runner is
  already good; P1's remaining case is reliability under harder tasks,
  which this screening did not test and further cheap trials would not
  settle quickly.
- **Next research question is P3, as a decision for Aram, not an automatic
  step:** does internal target resolution with compact, projected results
  (only `status`, `route_id`, `review_ref` returned; full outputs retained
  as artifacts) beat both arms? The apply-response verbosity measured above
  is the concrete cost such a slice would have to eliminate.
- PR #71 stays frozen either way. If P3 is not pursued, the standing
  recommendation from the P2a findings applies: simplify or retire the
  Task IR experiment and keep the runner, with this record as the evidence.

Artifacts: `frozen/prompt-v2-{B,C}.txt` and `frozen/screen-trials.json`
(prompt hashes, fixtures, session ids); analysis in
`results/demo/screen-analysis.json` and `results/demo/offline-analysis.json`.
