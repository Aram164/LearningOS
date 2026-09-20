# Incremental-generation replay evidence

Shadow-phase proof on the live LearningOS tree: the three shadow
artifacts (`backlinks.json`, `concept-map.md`, `dependency-report.md`)
are computed both the legacy way and through the derived-state graph,
and must agree byte-for-byte while localized mutations execute only
their declared dependency closure.

Statuses: `hit`, `rebuilt (cold)` (no previous output to compare),
`rebuilt-changed`, `rebuilt-pruned` (rebuilt with a byte-identical
output: downstream unaffected).

Produced by `test_real_repo_replay_scenarios` in
`tests/test_incremental_generation.py`, which copies the live tree to a
disposable directory (working tree untouched; the copy carries the real
`tools/` bytes, so producer identities are genuine), warms the shadow
cache, then applies one mutation per scenario with byte-restore between
scenarios. Every scenario below re-proves artifact equality alongside
the trace closure. | Scenario | Changed canonical files | backlinks.semantic | concept-map.body | dependency-report.body | Bytes equal |
|---|---|---|---|---|---|
| A cold | — (empty cache) | rebuilt (cold) | rebuilt (cold) | rebuilt (cold) | yes |
| A warm | — | hit | hit | hit | yes |
| B note prose | 1 note body (links kept) | rebuilt-pruned | hit | hit | yes |
| B restore | (bytes restored) | rebuilt-pruned | hit | hit | yes |
| C note concepts | 1 note frontmatter | rebuilt-changed | hit | rebuilt-pruned | yes |
| C restore | (bytes restored) | rebuilt-changed | hit | rebuilt-pruned | yes |
| D requires edge | concept-relations.yaml +1 edge | rebuilt-changed | rebuilt-changed | rebuilt-changed | yes |
| D restore | (bytes restored) | rebuilt-changed | rebuilt-changed | rebuilt-changed | yes |
| E workspace prose | 1 CONTEXT.md body | rebuilt-pruned | hit | rebuilt-pruned | yes |
| E restore | (bytes restored) | rebuilt-pruned | hit | rebuilt-pruned | yes |
| F source title | 1 registry partition title | hit | hit | hit | yes |
| F restore | (bytes restored) | hit | hit | hit | yes |

## What each scenario proves

- **A**: cold builds everything once; warm performs zero semantic work.
- **B**: a prose edit that keeps note links rebuilds backlinks but prunes
  it and both downstream nodes — the first change-pruning proof on real
  generation.
- **C**: a concept-metadata edit propagates through backlinks, then
  prunes at the report (which reads only `module_to_workspaces`) —
  pruning at depth two.
- **D**: a semantic relation edit rebuilds the full dependent closure.
- **E**: a workspace prose edit prunes backlinks (concept lists and
  module links untouched) while the report rebuilds-pruned on its
  direct workspace input.
- **F**: source-record edits are outside every declared input: full
  locality across domains.
- **Restores**: reverting bytes rebuilds exactly the affected nodes
  again, with the same pruning verdicts — reuse tracks content, not
  history.
