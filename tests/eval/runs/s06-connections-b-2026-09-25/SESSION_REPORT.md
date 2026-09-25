# Session report — s06-connections-b-2026-09-25

- Plan / role: C — connection experiment B (independent repeat of plan C)
- Blind: yes · Product revision: 200a36185fd5c693b4464ce0bdff4be5b89ce584 · World HEAD: 13ad2fcaa0e478afddba6451e29376ca00f0bc8e · Eval revision: 658db28d0c389f7ac2e5cbf878d099d4d359ec67
- Started / finished: 2026-09-25T02:15:44Z / 2026-09-25T02:45:00Z

## What I set out to do

Act as the learner's operator on first contact and answer two read-only
connection requests. S03: for each of her 20 canon notes, what else she should
read next to it. S27: for each of the 30 new captures in `eval-drop/`, what
she already has that it connects to, without changing anything. I recorded
which candidates the product surfaced and which I found by reading.

## Scenario outcomes

| Scenario | Classification | One-line reason |
|---|---|---|
| S03 | PASS_WITH_FRICTION | 20/20 probes answered, 158 ranked candidates. 85 were first surfaced by product commands, 73 only by reading. `related` has no note→note edges, and every garden/inbox/stage target required direct file reads. |
| S27 | PASS_WITH_FRICTION | 30/30 arrivals answered before shelving, 185 candidates (115 product, 70 reading). The observer diff confirms the world is unchanged. No command accepts free text or a file, so every arrival needed hand-picked search terms. |

## Failures (see failures.jsonl)

**F-s06-connections-b-01 — USABILITY_FAILURE: garden seeds, inbox captures and stage working notes cannot be read or searched through any read command.**

- *Expected*: `system/OPERATOR.md` tells interfaces to use `list-*`, `inspect`,
  `search` and `related` for targeted reads, and not to reconstruct state by
  parsing canonical Markdown. `search --help` says it searches "the complete
  fresh projection". `status` and `bootstrap --brief` count 7 inbox items and
  9 garden entries.
- *Actual*: `search ""` returns 294 records of 12 types, none of them garden,
  inbox or stage. `search --content` covers durable notes only. `inspect
  garden:<file>`, `inspect inbox` and `note-read <garden-stem>` return "not
  found". `plan-edit-context --stage-id` returns the working-note path but not
  its text.
- *Reproduction*: `los status`; `los search "DAG" --content` misses
  `knowledge/garden/everything-is-a-dag.md`; `los inspect
  garden:everything-is-a-dag.md` returns "record not found".
- *Own error possible*: a command I did not find might expose them. I checked
  `los --help`, `intelligence-scan --brief`, `capture --help`,
  `material-context`, and grepped OPERATOR/WORKFLOWS/README for a listing
  command.

## Friction that cost the most

1. **No note→note or similarity lookup.** `related NOTE` returns only
   concepts, sources and sometimes workspaces. Notes are reached by hopping
   through concepts (precise but sparse: 28 concept relations in total) or
   sources (broad: the Statistical Learning slides link to 21 notes). The two
   concept-less probes (C03, C09) got zero note neighbours. Arrivals cannot be
   queried by content at all. Cost: 97 `related`/`atlas-context` calls and 130
   content searches in S03, 365 search/related calls in S27, and reading all
   116 note bodies to rank.
2. **Garden, inbox and stage notes are invisible (F-s06-connections-b-01).**
   23 S03 targets and 33 S27 targets came only from `ls`/`cat` of canonical
   files. These include the most useful ones: garden seeds that pose the
   probe's own question (C01, C07, C10, C19, A15) and inbox duplicates (A11,
   A29).
3. **Content search is not phrase search.** It ANDs whitespace tokens as
   case-insensitive substrings over the whole file, frontmatter included.
   `"System R"` returned 11 notes, none about System R. `"the log"` returned 23
   (e.g. "the" plus the "log" inside "topological"). Snippets repeat once per
   token. Title/id
   search is also plain substring (`NaN` → 21 records via "domiNANt",
   "provenaNce"…). Every hit list needed manual filtering.

Smaller: `los.py` fails until `make setup` is run, though the error names the
fix (2 calls). `material-context` sounds like a relevance search but only
covers saved analyses (none exist here). OPERATOR.md's "open the domain atlas
for the full map" names no command.

## What the product made easy

- `inspect` with up to 20 ids per call, one snapshot per batch: a full
  catalogue of 116 notes (title, summary, concepts, sources, state, contexts)
  in 6 calls.
- `search ""` lists all 294 projected records, a cheap map of what exists.
- `note-read` returns bounded, snapshot-guarded note bodies in stable JSON.
- `related CONCEPT` and `atlas-context` gave clean, typed same-topic
  neighbourhoods. Superseded/deprecated notes carry `state: deprecated`, so
  `p-values-first-take`, `virtual-memory-is-swap` and `adam-always-better`
  were easy to flag.
- Read commands never wrote canonical state. The snapshot id stayed
  `sha256:82bcffb7…` throughout.

## Behind the curtain

- No receipts, request ids, operations, diagnostics or AI actions in either
  scenario: both observer diffs show zero canonical change and HEAD unchanged.
- The first read materialized a derived-state cache:
  `generated/derived-state/state-v1.json` plus 117 blobs, 490,130 bytes,
  gitignored. S03's derived digest moved df97c873… → 50797f3c…. S27 reused it
  unchanged.
- `make setup` installs pre-commit, post-commit and pre-push hooks into the
  world's `.git/hooks`.
- Workspace membership shows up in `related` from one side only: a note listed
  by a workspace (naive Bayes in the retake workspace) does not show that
  workspace unless the note itself carries `contexts`.

## Uncertainties

- Rankings are my judgement of usefulness for her current goals (October
  exams, Tessera). Weak links are flagged `tentative`.
- In S27 the product/reading split depends on the search terms I chose; a
  different operator would shift it.
- A read path for garden/inbox/stage content may exist that I did not find
  (see the failure's own-error note).
- This session carried a memory index describing LearningOS internals (see
  deviations). It was not opened, and these read-only tasks did not need it.

## Deviations from the protocol

Recorded in full in `run.json`. In short:

- Harness venv on python3.12 (3.13 not installed).
- A LearningOS memory index was in the agent's context.
- Other sessions' branch names and a conductor `oracle` directory name were
  visible in listings; nothing was opened.
- S27's reset left gitignored `.venv`, hooks and the projection cache in place.
- S27 reused S03's reading.
- No approval values were needed.
- One operator error outside the product. An unquoted shell here-document
  executed backtick-quoted text, including `git reset --hard` and
  `git clean -fd`, in the operator's umbrella checkout. That deleted untracked
  files there. The world, the LearningOS repository and this run's evidence
  were unaffected; S27's diff was taken before it happened.

## NOT TESTED

The Obsidian interface (reading-room views, shelves/bases, any in-app
related-notes panel) is outside this environment, so connection discovery
through the UI is NOT TESTED. `make views` / `generated/reading-room.md` was
not generated or read.
