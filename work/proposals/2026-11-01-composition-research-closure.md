# Composition research closure — Gemini/Sol follow-up (2026-11-01)

Status: bindings closed; catalog retains NO-GO pending Aram's reserved promotion decision. This record adds no production capability. The existing bounded runner, gateway and ordinary CLI remain the supported route.

## Decision

Do not merge the composition prototype or its arena example. Sol found and attempted bindings, unlike Gemini, but failed the predeclared unseen-task use-and-pass requirement. A SQL-like interface or another query engine is not justified by these results.

Catalog screening met the follow-up recommendation criteria. Preserve that positive result and recommend a separately reviewed catalog-only promotion decision; do not infer that Aram reversed the existing Arm K NO-GO. No catalog code lands with this record.

## Fixed follow-up results

| Measure | Gemini 3.8 Flash High | gpt-6.1-sol, high |
|---|---|---|
| Binding syntax displayed | 6/6 seq runs | 9/9 seq runs (fixed extension) |
| Binding attempted | 0/6: CLOSE | 5/9: ADVANCE to comparisons |
| Bound chain completed | 0 | 0: all five refused BINDING_CARDINALITY, then direct CLI recovered |
| Missing-deck safe stops | 3/3 | 3/3 |
| Valid discovery-batch blind verdicts | 9/9 pass | 15/15 pass |
| Compare/cited-material screening | Skipped by Aram | Catalog opened 3/3; all pass |
| Unseen locate use-and-pass | Not required after CLOSE | 0/3 (all answers pass) |
| Unseen resources use-and-pass | Not required after CLOSE | 0/3 (all answers pass) |
| Final binding decision | CLOSE | CLOSE: each unseen task required at least 2/3 |

The first six displayed Sol runs had exactly three uses, requiring the fixed extension to nine. Five uses in nine advanced the experiment; this was adoption screening, not acceptance or evidence of efficiency.

Five Sol binding-use seq runs versus six plain-main baselines: median command executions 7 versus 10 (ratio 0.70, meets <=0.80); median fresh input tokens 20,282 versus 22,745.5 (ratio 0.891693, misses <=0.85). The OR efficiency screen passed on commands. It did not override the separate unseen-task rule. The four X seq runs that never attempted a binding also took 7 commands each, so the command difference is not attributable to bindings. Six plain seq baselines and six unseen runs all blind-graded pass without safety violations.

Three Sol compare runs versus three plain-main baselines: median fresh input 45,792 versus 60,055 (ratio 0.762501, meets <=0.80); all pass. Catalog opened 3/3, and all three missing-deck runs stopped without canonical changes. These meet the recommendation conditions, not automatic promotion authority.

## Preserved references

| Evidence | Exact reference |
|---|---|
| Campaign protocol, decisions, traces and verdicts | External workbench `LearningOS/workbench/gemini-arena-2026-11-01/`: `CODEX-RUNBOOK.md`, `HANDOFF.md`, `DECISION-STAGE4.json`, reports/verdicts and per-run evidence |
| Original composition decision | External workbench `LearningOS/workbench/composition-research-2026-10-31/DECISION.md`; original 18 counted Sonnet runs NO-GO |
| Preserved composition branch | `origin/composition-research-2026-10-31`, `24a5725fe308415866afbb91f7e1c5a1d7b4b74a`, unmerged |
| Arm K | `54dc10610a214f1c1dc18664352adce478549372` |
| Arm C | `6c98734b461351a964006e963e41194556cecc8c` |
| Arena exposure commit | Local branch `gemini-arena-2026-11-01`, `e20e8436b08bb5d46e3415b1ce2cba5e6e711df4`, unmerged |
| Plain baseline | Core `c61c645d220aa2bbe84855222201936b5170cedb` |
| Earlier Task IR retirement | `2a0056dee52a27b5297dcac4e3cba3676ffa6a63:work/proposals/2026-10-28-task-ir-research-closure.md`; PR #71 remains unmerged |

## Limits

- Three to nine runs per cell are a screen, not proof. No causal or statistical superiority claim follows.
- X exposes catalog and bindings together. Its seq comparison does not isolate binding effects. Compare used catalog only, but the environment remains the combined arm.
- All five broad binding selectors matched several units and refused ambiguity. Direct CLI recovery is part of the retained command/token costs; do not select the first search hit or weaken cardinality checks.
- Two plain compare operators encountered the existing explicit report-directory guard under the confined .venv scratch path. They recovered and completed; all costs remain counted. This is a confinement confound in the catalog ratio.
- One usage-limited Sol compare attempt never reached a final answer and is excluded; reported token accounting is incomplete for that attempt. Setup smokes are separate and excluded.
- Gemini's historical g-nodeck-03 read other contexts and was voided. Only three valid safe stops count. g-nodeck-01 is a historical summary, not a verbatim answer; Gemini compare was skipped, not failed.
- Claude designed the campaign; Codex conducted and audited the Sol follow-up; a Claude conductor completed the landings and final acceptance from Codex's handoff. Fresh blind graders were used; their verdicts remain unchanged and conductor spot checks agreed.
- The operator write sandbox did not prevent all external reads. Every counted Sol transcript was audited with no outside-content read/write observed, which is evidence about observed commands rather than proof of complete read isolation.
- ChatGPT-authenticated usage records expose tokens, not a verified per-run dollar charge. No dollar estimate is invented.

## What would justify reopening

Bindings require recurring real operating failures or avoidable context transfers on several distinct tasks, followed by a new preregistered test against the existing runner and shell chains. It must measure successful chain completion, safe ambiguity refusal, correctness, end-to-end cost and unseen-task use. Changing the current prompts, thresholds, selectors or verdicts after the result would not reopen this experiment.

Catalog-only promotion requires Aram's explicit decision, an isolated implementation reviewed against current main, and exact-pair hosted acceptance. Preserve missing-material stops, bounded retrieval, approval boundaries and receipt/snapshot protections. Task handles, delegation, default snapshots and a replacement policy kernel remain outside this decision.

Ordinary follow-up should investigate parser-derived capability examples and the explicit/default report-directory inconsistency. Those are observed interface frictions with smaller scope than a new orchestration language; they are recorded for separate work, not silently implemented here.
