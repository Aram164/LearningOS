# Session report — s05-connections-a-2026-09-25

- Plan / role: C — connection experiment A
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: 658db28d0c389f7ac2e5cbf878d099d4d359ec67
- Started / finished: 2026-09-25T02:15:07Z / see `run.json` → `finished`. Active work ran 02:15–02:38 UTC (S03 11.5 min, S27 6.2 min, then records). The session then sat idle until about 10:50 UTC waiting for the operator's "continue", and finished the records, checks and commit after that. Treat the idle gap as not product time.

## What I set out to do

Plan C runs the two connection scenarios on fresh worlds. S03 finds, for each of the 20 canon notes, what else the learner has that she should read next to it. S27 does the same for each of the 30 arrivals in `eval-drop/`, before filing and without changing anything. I used the product's documented reads first. Where they could not reach something, I read the material myself and labelled every result with the product command that surfaced it, or `agent-reading`.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S03 | PASS_WITH_FRICTION | All 20 probes answered (161 results) from documented reads, world unchanged. `related NOTE` returns only concepts and sources, nothing is ranked, and Garden, inbox and stage items are unsearchable, so 75 results came from reading. |
| S27 | PASS_WITH_FRICTION | All 30 arrivals answered (176 results; A24 correctly empty), world verifiably unchanged. No product read takes an arrival as input, and inbox duplicates, Garden seeds and home stages were found only by reading. |

Provenance of results (full breakdown in `results/S03.json` and `results/S27.json` → `scenario_record`):

| | product:related | product:search | product:search-content | agent-reading |
|---|---|---|---|---|
| S03 (161) | 51 | 7 | 28 | 75 |
| S27 (176) | 67 | 24 | 10 | 75 |

Every Garden (23), inbox (14) and stage (22) result across both scenarios came from reading. No product read returned any of them.

## Failures (see failures.jsonl)

- **F-s05-garden-inbox-unreachable-01 — USABILITY_FAILURE.**
  - *Expected:* OPERATOR.md "Start here" says interfaces use `list-*`, `inspect`, `search` and `related` for targeted reads instead of parsing canonical Markdown. CLAUDE.md §2 says to use `inspect`/`search`/`related`/`note-read` for a named record.
  - *Happened:* `bootstrap --brief` counts 7 inbox items and 9 Garden entries, but `inspect`/`related` answer "record not found" for every id form I tried (`garden:<file>.md`, the bare stem, `inbox:<file>.md`, the bare inbox stem). `search` never returns either kind.
  - *Minimal reproduction:* `inspect garden:everything-is-a-dag.md`.
  - *Could be my mistake:* an id form or UI-only view I did not try might resolve them. I did not read code to find out.
- **F-s05-related-asymmetry-02 — AMBIGUOUS.**
  - *Happened:* `related workspace-statlearn-retake` lists `note-naive-bayes-spam-filter`, but `related note-naive-bayes-spam-filter` does not list the workspace. It does list a workspace when the note itself declares `contexts`.
  - *Could be my mistake:* `related` may be deliberately outgoing-only. No document states its direction.
- **F-s05-domain-atlas-missing-03 — AMBIGUOUS.**
  - *Expected:* CLAUDE.md §2 and its "Cross-domain reach" paragraph send cross-domain discovery to `generated/domain-atlas.md`.
  - *Happened:* the fresh world's `generated/` holds only `derived-state/`. The bootstrap glance reports 0 shelves and 0 crosswalks in every domain.
  - *Could be my mistake:* the file may appear after `los generate`, which I did not run because it writes derived files and S27 asked for no changes. The builder records `generate_exit 0`, so the builder may be responsible rather than the product.

## Friction that cost the most

1. **No ranked "read next to this" read, so the whole corpus had to be read.** `related NOTE` gives concepts and sources, and `related SOURCE` gives every note citing the same course (up to 21), all unranked. To rank honestly I listed all notes (`search "" --type note`) and read every one. That took 118 `note-read`, 6 batch `inspect` and 1 study-map `inspect` calls, plus 16 direct file reads for Garden and inbox: about 100 KB of text before any ranking.
2. **Candidate harvesting: 362 CLI calls** (169 in S03, 193 in S27; about 0.4 s cold start each). Substring matching inflated the sets. C05 got 35 candidates, most from content matches on "log". "prior" hits priority inversion, "CAP" hits "escape" in the annealing note, and "kernel" hits the SVM, CNN and KDE kernels.
3. **Looking for reads that do not exist: about 14 calls with no payoff.** Five "record not found" attempts for Garden and inbox. `bootstrap` ×3, `intelligence-scan`, `semantic --list` and `atlas-context` looking for a connection or Garden view. In S27, `material-context` ×2 (it searches only material-analysis notes, of which there are none) and `ai-action-list` (Garden shelving and unit material comparison only). Plus the missing domain atlas.

## What the product made easy

- `search "" --type note` enumerates every note. `inspect` takes 20 ids in one snapshot-consistent call.
- `note-read` returns the full body with a content hash and a continuation contract.
- `inspect study-map-…` carries each stage's working note inline (`notes_text`), so all 20 stage notes took one call.
- `related CONCEPT` gives clean concept neighbourhoods, including concept-to-concept relations. That produced most of the product-surfaced results.
- Errors were clear and actionable: the missing-dependency message names `make setup`, and "record not found" exits with code 2. `material-context` says its empty answer "never proves no source explains the topic".
- Read commands never touched canonical state.

## Behind the curtain

- In both scenarios: no receipts, no in-flight journals, no gateway requests, no AI-action bundles, no diagnostics, no new `los operations` entries. HEAD is `13ad2fc` before and after, and git status is clean.
- The first read materialises a git-ignored projection cache: `generated/derived-state/` goes from 0 to 490,130 bytes (state-v1.json plus 117 blobs). The derived digest `28a681fe…` is identical in both worlds, and every read reported the same `snapshot_id` `sha256:82bcffb7…`, so the projection is deterministic.
- OPERATOR.md calls `generated/manifest.json` "the stable read contract", but no such file exists before or after. The projection seems to live in `derived-state/`, which I did not open by hand.
- S27: `eval-drop/` stayed byte-identical (a sha256 over its 31 files matches the S03 world's drop).
- For the judge: at rank 1, 17/20 canon answers and 19/29 arrival answers are product-surfaced. The product's misses concentrate where the learner's own layers live (Garden, inbox, stages) and in cross-domain analogies that share neither a concept nor a word: Naive Bayes ↔ optimizer independence, Viterbi ↔ Selinger DP, softmax temperature ↔ KDE bandwidth, MAP ↔ lasso.

## Uncertainties

- Ranking is my own judgment; the product ranks nothing. 30 canon and 33 arrival results are flagged `tentative`.
- The 7 `arrival:` targets in S27 are other new captures, not "what she already has". I listed them last so they get filed together.
- S27 used my S03 reading of an identical world for note, Garden, inbox and stage contents.
- Whether F02 is intended behaviour, and whether F03 comes from the product or the world builder.

## Deviations from the protocol

All are listed in `run.json` → `deviations`: the scratchpad world location; an early `git show --stat` of the eval-package commit, which described the corpus design in general terms but contained no oracle content; the external venv; S27 reusing S03's reading; bulk helper scripts over the documented CLI; post-snapshot verification reads; a shell-quoting slip that ran a no-op `make setup` and a read-only `git show --stat` outside both repositories; and the approval authorisation, which went unused.

## NOT TESTED

- The Obsidian UI: any Garden or inbox view, the Review queue, and the Atlas connection editor (`concept.relations.change` over the `ui` channel), which might offer connection features the CLI lacks.
- `los generate` and the generated domain atlas.
- AI-assisted shelving (`garden.shelve`, `shelving-prepare`), which writes request bundles and was not asked for.
- Filing or capturing the arrivals, which the learner explicitly deferred.
