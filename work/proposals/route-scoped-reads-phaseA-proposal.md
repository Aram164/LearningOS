# Phase A proposal: route-scoped reads + stratified benchmark

Status: proposed. Authorizes nothing beyond this document until Aram approves
the benchmark protocol in section 4.

## 1. Goal

Prove that single-route audit verdicts reproduce from route-scoped reads at
a fraction of the context, and draw the explicit boundary where unit-level
reads remain mandatory. No canonical changes. No new architecture.

## 2. Key finding (verified 2026-09-08)

The route-scoped read **already exists**. `plan-edit-context UNIT_ID
--route-id ROUTE_ID` returns the full route row (angle, covers, locator,
detail, scope, source) plus `uses` (stage placements with triage and
overrides), `patch_fields`, snapshot, and artifact revisions — about 2 KB
against ~15 KB for the full unit context. Probed live on
`route-b574283601c1e7562e4f5071` (L09 MIT); output contract
`plan-edit-context`, `ok`.

Consequence: Phase A implementation is most likely **zero code**. The work
is measurement, a benchmark rule, and operator guidance — not a feature.

## 3. Measurement basis

L07/L08/L09 audits each pulled full unit contexts (18-24 routes) for
route-sized questions, at ~2 s full-repo load per `los.py` call and ~10-14
calls per audit. The labeled ground truth already exists and is frozen:

- L07: audit table + adjudication + transactions 20260908-045007/045026
- L08: audit table + adjudication + transactions 20260908-051053/051105
- L09: audit table, unaudited by second pass (candidate held-out set)

## 4. Benchmark protocol (needs approval)

Stratified, because three finding classes are irreducibly cross-route
(Leuphana same-pages L07/L08; unit-scope-vs-deck L07; stage-triage-vs-route
L07-geometric, L08 deck-in-stage-4). A benchmark that only tests
single-route verdicts would pass by shrinking the audit surface.

- **Set S (single-route, must reproduce exactly):** L07 Dekking swap,
  Schaum removals, MIT covers + R-prose, Arbeitsbuch narrowing, Leuphana
  angle; L08 Schaum removals, MIT additions, Dekking normal; L09 MIT
  bootstrap addition. Re-derive each verdict from the route-scoped read
  (+ unit knowledge-node summaries only where the verdict cites node
  meaning); record match/mismatch and input bytes.
- **Set C (cross-route, must stay unit-level):** the three classes above
  plus L09 data-bias single-source. For each, record the minimal read
  that reproduces it. This set defines the boundary; it is not a failure.
- **Acceptance:** 100% match on set S; set C documented with minimal
  reads; context-per-verdict reported before/after; no verdict in either
  set changes.
- **Held-out check:** run the protocol against L09 first (fresh eyes if
  available), since L09 has findings but no applied repair.

## 5. Deliverables on approval

1. Benchmark report (this file gets a results section, or a dated
   follow-up next to it).
2. One-paragraph operator guidance: route-scoped reads for single-route
   questions; named minimal reads per cross-route class.
3. Explicit non-goals: no `inspect` changes, no ID renaming, no detector,
   lineage, or cache work (Phases B-D, separate proposals).

## 6. Open questions

- Should knowledge-node summaries ride along in the route-scoped read,
  or is a second targeted read acceptable? The benchmark decides.
- Readable route IDs (`route-<unit>-<source>-<topic>`): separable,
  optional, not required for Phase A acceptance.
- Who runs the held-out L09 pass for independence credit.

## 7. Benchmark results (2026-09-08)

Method: all 11 Set-S verdicts re-derived from route-scoped reads only
(`plan-edit-context UNIT --route-id`), against the frozen L07-L09
adjudications. Post-repair state was verified to equal the adjudicated
end-state (covers present/absent per verdict, anchors present in
locator/angle/detail). One probe bug found and fixed in the check script
(case-sensitive anchor on the repaired Arbeitsbuch prose); no verdict
changed.

### Set S: 11/11 reproduce from route-scoped reads

Total context: 30,299 bytes over 11 calls, against 160,376 bytes over
3 full unit contexts (L07 58,255; L08 56,098; L09 46,023) — a 5.3x
reduction. Per-route reads measured 1,924-5,171 bytes. No verdict needed
knowledge-node summaries beyond the self-descriptive node IDs; open
question 1 is answered no, with the caveat that cryptic node IDs would
reopen it.

### Set C: minimal reads recorded

- C1 (Leuphana same-pages): 2 route reads, 2,186 + 2,025 bytes.
  Route-level after all.
- C2 (scope-vs-deck): unit inspect (3,946) + deck route (4,816).
  Unit-level read still required for scope text.
- C3a (triage placement, e.g. deck-in-geometric-stage): route read
  alone — the `uses` array carries per-stage triage plus overrides,
  and showed the repaired reference-only state. Route-level.
- C3b (stage flags: exam_critical, stage scope_triage): map inspect,
  127,203 bytes — the single most expensive read in the whole
  workflow, 2x a full unit context. A stage-scoped map read is the
  obvious follow-up micro-improvement.
- C4 (single-source proof, e.g. data-bias): full unit context,
  46,023 bytes. Negative claims need the universe; no narrower read
  can prove them.

### Latency honesty clause

Context fell 5.3x but wall time did not: `--route-id` takes one value,
so 11 calls pay ~11 full-repo loads (~22 s) against ~6 s for 3 full
contexts. Phase A as built saves context/tokens, not time. Converting
it into a time win needs batch reads (inspect-style, up to 20 IDs in
one load) — recommended as Phase A2, small and mechanical.

### Independence note

L09 was not held out in practice (same operator, post-audit). No
independence credit claimed; this run is verdict-reproduction against
frozen adjudications, which is what the protocol's acceptance required.

### Verdict on the proposal

Accepted with the latency clause above. Operator guidance stands:
route-scoped reads for single-route questions; unit inspect for scope;
map inspect (or future stage-scoped read) for stage flags; full context
only for negative/universe claims.
