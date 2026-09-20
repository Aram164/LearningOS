# Incremental-manifest replay evidence

Manifest-phase proof on the live LearningOS tree: the full
`manifest.json` is computed both by `build_manifest()` and through the
derived-state graph, and must agree byte-for-byte while localized
mutations execute only their declared dependency closure.

Statuses: `hit`, `cold` (no previous output to compare),
`rebuilt-changed`, `rebuilt-pruned` (rebuilt with a byte-identical
output: downstream unaffected). `proof=X` is the validation-proof
node's verdict: `hit` (validation skipped), `rerun-changed`,
`rerun-same`, `cold`.

Produced by `test_real_repo_manifest_replay` in
`tests/test_manifest_replay.py`, which clones the live tree with its
git history to a disposable directory (working tree untouched; the copy
carries the real `tools/` bytes, so producer identities are genuine),
links the 2GB materials farm, warms the shadow cache, then applies one
cumulative mutation per scenario. Every scenario below re-proves
byte-exact manifest equality alongside the trace closure. Mutations are
cumulative, so each row's input state is the previous row's output
state. Shas are `manifest.json` bytes (legacy vs shadow) truncated to
12 hex chars. Run on 2026-09-20, branch
`dev/manifest-incremental-2026-09-20`.

| Scenario | Changed files | Rebuilt (changed) | Pruned (rebuilt, same) | Hit | Proof | Legacy | Shadow | Equal |
|---|---|---|---|---|---|---|---|---|
| R0 cold | — (empty cache) | all 36 | — | 0 | cold | 2793f70b3c93 | 2793f70b3c93 | yes |
| R1 warm | — | — | — | 36 | hit | 2793f70b3c93 | 2793f70b3c93 | yes |
| R2 note append | 1 note body (trailing prose) | — | notes, backlinks, counts | 32 | rerun-changed | 66585b6affdb | 66585b6affdb | yes |
| R3 note title | 1 note frontmatter title | notes, records, payload | backlinks, counts, indexes, typed-collections | 28 | rerun-changed | 50b1e7baada8 | 50b1e7baada8 | yes |
| R4 relation add | concept-relations.yaml +1 edge | relations, backlinks, counts, payload | — | 31 | rerun-changed | 3bed8dc2f13e | 3bed8dc2f13e | yes |
| R5 source title | 1 registry partition title | sources, records, payload | study-maps, source-maps, learning-paths, counts, indexes, typed-collections | 26 | rerun-changed | 7ece554f8cd4 | 7ece554f8cd4 | yes |
| R6 workspace append | 1 CONTEXT.md (trailing) | — | workspaces, backlinks, counts | 32 | rerun-changed | 1c1196adffe1 | 1c1196adffe1 | yes |
| R7 ledger bump | revisions.yaml unit-aml-l01 6→7 | revisions, units, records, typed-collections, payload | 17 (all other revision readers + downstream) | 13 | rerun-changed | 7243f0c758d0 | 7243f0c758d0 | yes |
| R8 inbox add | work/inbox +1 file | review-items, counts, payload | — | 32 | rerun-changed | 47c43d1d89f6 | 47c43d1d89f6 | yes |
| R9 garden add | knowledge/garden +1 seed | garden, ai-actions, counts, payload | — | 31 | rerun-changed | 814d020f4ac7 | 814d020f4ac7 | yes |
| R10 AI status | 1 request.yaml prepared→completed path | ai-actions, payload | counts | 32 | rerun-changed | d33d3a6d0bf5 | d33d3a6d0bf5 | yes |
| R11 stage status | 1 study-map stage active→complete | study-maps, stages, progress, counts, records, typed-collections, payload | backlinks, indexes, edges, review-items, semesters | 23 | rerun-changed | 4c456f60e49c | 4c456f60e49c | yes |
| R12 source-map why | 1 route rationale sentence | source-maps, records, typed-collections, payload | study-maps, syntheses, units, stages, progress, counts, +5 | 20 | rerun-changed | e8b110539f5f | e8b110539f5f | yes |
| R13 commit | — (git commit, no byte change) | — | counts | 34 | rerun-changed | 60a7687dcd75 | 60a7687dcd75 | yes |
| R14 corrupt | (records blob forged) | records (cold) | — | 35 | hit | 60a7687dcd75 | 60a7687dcd75 | yes |
| R14b healed | — | — | — | 36 | hit | 60a7687dcd75 | 60a7687dcd75 | yes |
| R15 delete state | (derived-state removed) | all 36 (cold) | — | 0 | cold | 60a7687dcd75 | 60a7687dcd75 | yes |

## What each scenario proves

- **R0/R1**: cold builds the complete 36-node graph once (6s incl. the
  legacy build); warm performs zero rebuilds.
- **R2/R6**: trailing prose moves no summary: the touched leaf prunes
  and the payload itself hits. Only the proof reruns (the fingerprint
  in `_generated` moved).
- **R3**: depth-2 pruning on real data — notes → records →
  pruned typed-collections → hit progress/stages/edges.
- **R4**: relations bypass records: records, indexes, and every typed
  view hit while only the relation readers rebuild.
- **R5**: source-title change prunes the entire route-resolution chain
  (source-maps, study-maps, learning-paths) because the material
  authority is untouched — and units hit through the pruned
  source-maps node.
- **R7**: one ledger row rebuilds every revision reader, but only the
  owning unit's output changes; 17 nodes prune.
- **R8–R10**: inbox/garden/AI mutations stay inside their subgraphs;
  garden growth correctly rebuilds AI actions (which embed garden
  rows) without touching records.
- **R11**: a stage flip propagates to progress and counts (completion
  tallies) while edges prune (evidence carries no status).
- **R12**: route-rationale prose rebuilds source-maps but prunes
  study-maps, syntheses, and units — the evidential projections
  exclude prose exactly as designed. Depth-2 pruning through two
  independent dependents.
- **R13**: committing with no byte change moves git dates: counts
  rebuilds on the notes-git input and prunes (no drift change), the
  proof reruns on the new source revision, everything else hits.
- **R14**: forging the records blob cold-misses exactly that node and
  self-heals; the proof hits because the manifest bytes are intact —
  validation is correctly NOT rerun for cache damage elsewhere.
- **R15**: deleting derived state restores clean-from-scratch
  execution with identical bytes.

## GO mapping (plan §5)

1. Legacy/shadow bytes identical on the live tree: every row, `Equal`.
2. Cold execution rebuilds the complete graph: R0 (36/36).
3. Warm execution performs zero rebuilds: R1, R14b (36/36 hits).
4. Every mutation rebuilds only its declared closure: R2–R13 rows.
5. Depth-1 pruning: R2, R6, R13 (leaf prunes, payload hits).
6. Depth-2+ pruning: R3 (collections→progress), R5 (source-maps→units
   hit), R12 (two independent depth-2 prunes).
7. Producer change invalidates the correct node: synthetic matrix
   (`test_producer_change_rebuilds_only_its_node`, lifecycle.py →
   modules only) and `test_validator_code_change_reruns_only_validation`.
8. Cache corruption self-heals: R14/R14b.
9. Deleting derived state restores clean execution: R15.
10. Contract/schema changes invalidate the proof: synthetic
    (`test_contract_comment…`, `test_registry_schema_change…`,
    `test_schema_change_fails_identically_on_both_sides`).
11. Proof reuse only for identical identity: R1/R14/R14b hits plus the
    enforce-spy suite (`tests/test_manifest_proof.py`).
12. `build_manifest()` remains production-authoritative: untouched
    call path; `generate_all()` diff-free (see below).
13. `generate_all()` unchanged: `git diff 16ffb37 --stat` shows no
    change to `tools/learning_os/genout/outputs.py`.
14. Full test/lint/system gates green: see commit trailer.
15. Real-repo replay proves exact equality: this document.
