# K2 Phase A — Cold-start operator navigation (2026-10-25)

Worker: GLM 5.8 Flash via ZCode, fresh operator chat. STATUS.md said READY at
start. All navigation below is in the private clone
`/Users/aramaljanadi/los-glm-K2-2026-10/repository` at Core pin
`fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` over data base `7b713d84b5e8e48b7f8bdb6c88842c7ccbbda2ad`.
Every answer comes from public system reads (`.venv/bin/python tools/los.py …`).
No canonical YAML parsed, no implementation/test code opened, no writes to the
repository or live tree, nothing pushed. CAMPAIGNS.md had not been opened when
this file was written.

## Setup record (recorded separately from navigation failures)

1. Read `STATUS.md` → READY; read `K2-COLDSTART.md`; operator reading route:
   `LearningOS/repository/AGENTS.md` then `LearningOS/repository/system/OPERATOR.md`.
2. Live Core pre-check (read-only):
   `git -C <live> rev-parse HEAD` → `7b713d84b5e8e48b7f8bdb6c88842c7ccbbda2ad`
   (matches the recorded data base exactly); `git status --porcelain` → empty.
   No uncommitted learner changes, no reconciliation stop.
3. `git clone --no-hardlinks <live> /Users/aramaljanadi/los-glm-K2-2026-10/repository`
   → clone HEAD `7b713d84…`. Target path did not exist beforehand; nothing overwritten.
4. Materials sibling link:
   `ln -s /Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials /Users/aramaljanadi/los-glm-K2-2026-10/materials`
   (resolves to the real materials tree; read-only for this task).
5. `git -C <clone> fetch https://github.com/Aram164/LearningOS.git codex/operator-developer-docs-20261025`;
   `git checkout --detach fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`.
   Verified HEAD: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` ("Refresh AI-delivery
   request hashes after corpus contract change").
6. Data-base invariance check:
   `git diff --stat 7b713d84b5e8e48b7f8bdb6c88842c7ccbbda2ad HEAD -- knowledge sources records work curriculum projects system/schema`
   → empty output (exit 0). Working tree clean.
7. `python3.14 -m venv .venv` (Python 3.14.4);
   `.venv/bin/python -m pip install -e '.[dev]'` → success (`learningos-core 3.2.0`).
   No `make setup`, no `make hooks`, live venv not reused, live checkout untouched.
   **No setup failures.**

Discovery: `.venv/bin/python tools/los.py capabilities --compact --json` →
contract_version 2, cli_protocol 6, gateway `tools/los.py`, 20 queries, 50
commands; `capabilities NAME --json` used for `resume`, `material.context`,
`atlas.context`, `semantic.query`, `search`, `related`, `inspect`.

## Q1 — From a recorded study context: a concept's prerequisites and one existing explanation

Selected IDs: stage `stage-icop-l01-forms` (recorded study context), unit
`unit-icop-l01-linear-programming`, prerequisite knowledge node
`knowledge-icop-l01-forms`, dependent node `knowledge-icop-l01-geometry`,
stage `stage-icop-l01-geometry`, concept `concept-convexity`, note
`note-icop-l01-reference`.

Commands in order, with results:

1. `los.py resume --study` → **refused**: "no upcoming exam is recorded for an
   enrolled module; `status` shows the recorded exam spine". Wrong turn,
   recorded; consistent with `resume` later reporting "no upcoming sitting
   recorded" for ICOP.
2. `los.py resume` → recorded study context:
   `Introduction to Combinatorial Optimization (ICOP) · ICOP Chapter 1 — Linear
   Programming · stage-icop-l01-forms (via recently touched stage (resume
   pointer missing or stale))`. Requirement
   `req-icop-l01-linear-programming-icop-l01-forms`, concept label
   `knowledge-icop-l01-forms`, evidence "none recorded yet".
3. `los.py inspect knowledge-icop-l01-forms` → INVALID_REQUEST "record not
   found (did you mean: stage-icop-l01-forms, stage-icop-l01-pivots?)";
   `los.py related knowledge-icop-l01-forms` → same. Wrong turns, recorded:
   knowledge-map node labels are not record IDs.
4. `los.py plan-edit-context unit-icop-l01-linear-programming --brief` →
   snapshot `sha256:297576615e7d0b893c45b7ab34a140b39cfdab7b575a308931becfe5cf43d959`;
   9 stages, 53 routes, 58 placements; `stage-icop-l01-forms` triage
   required-now 1 / helpful-now 1 / reference-only 3.
5. `los.py plan-edit-context unit-icop-l01-linear-programming --stage-id stage-icop-l01-forms`
   → stage record; `"concepts":[]` (this stage carries no durable concept — a
   count, not a bug).
6. `los.py inspect unit-icop-l01-linear-programming` → knowledge map:
   `knowledge-icop-l01-geometry` has `"builds_on": ["knowledge-icop-l01-forms"]`
   and carries `"concept_ids": ["concept-convexity"]`. The chain continues
   geometry→bases→pivots→phase-one→standard-duality→general-duality→slackness→oral-review.
7. `los.py inspect concept-convexity` →
   `{"aliases":["Konvexität","PSD Hessian","convex optimization"], "id":"concept-convexity",
   "path":"knowledge/concepts.yaml", "title":"Convexity", "type":"concept"}`.
8. `los.py plan-edit-context unit-icop-l01-linear-programming --stage-id stage-icop-l01-geometry`
   → stage record `"concepts": ['concept-convexity']` — the stage↔concept link
   confirmed from the stage record itself.
9. `los.py material-context --concept concept-convexity` → exactly 1 item:
   `analysis-note note-icop-l01-reference` ("ICOP Chapter 1 — Linear Programming
   reference"), `concept_via: ["stage:stage-icop-l01-geometry"]`, source
   `algorithms/structures/icop-hu-ws2627/ico_linearprogramming.pdf` pp. 1–129,
   `freshness: current`, `resolution: resolved`, `semantic_review: unreviewed`.
10. `los.py note-read note-icop-l01-reference` → note exists (16,960 chars);
    frontmatter `material_analysis.resolution: resolved`, `source_id:
    source-icop-hu-ws2627`, `recorded_source_digest == live_source_digest`
    (`76f3c809e569606b1d7422867ec0887f062aab814e6abeda31f2c990e15f45d1`).

Result: from the recorded study context, the prerequisite structure is the
knowledge-map edge `knowledge-icop-l01-geometry` builds on `knowledge-icop-l01-forms`
(the stage-1 node the resume pointer names), and the dependent stage
`stage-icop-l01-geometry` carries concept `concept-convexity`, for which one
existing explanation is `note-icop-l01-reference` with a current, resolved
digest binding. Concept-level prerequisite relations exist elsewhere in the
atlas (see Q2), but for `concept-convexity` itself the atlas records no
`requires` relation — an honest count, not a bug.

## Q2 — An explicitly authored concept connection: recording row and linked evidence

Selected connection: `concept-convexity` —`applies-in`→ `concept-gradient-descent`.

Commands and results:

1. `los.py related concept-convexity` → includes
   `{"id":"concept-gradient-descent","type":"concept","path":"knowledge/concepts.yaml","via":["relation"]}`,
   plus backlinked notes (`note-aml-l06-gradient-descent`,
   `note-aml-sad-master-wiring`, `note-icop-l01-exercise-bank`,
   `note-icop-l01-mock-exam`, …) via `backlink:concept_to_notes`, and units via
   `stage-concept:…`.
2. `los.py atlas-context concept-convexity` → the row, printed by the public read:
   ```json
   {"relation_revision":0,
    "relations":[{"from":"concept-convexity","type":"applies-in",
      "to":"concept-gradient-descent",
      "context":"∇²L = (1/m)XᵀX is PSD ⟹ MSE convex; logistic loss convex — GD cannot get trapped (cross-wire #11)",
      "source":"note-aml-sad-master-wiring"}],
    "questions":[]}
   ```
3. `los.py atlas-context concept-gradient-descent` → 5 further rows, types
   `requires` (concept-data-parallelism → GD; context "legacy hard prerequisite
   F.J→S.C: data-parallel SGD needs the SGD concept first", source
   `note-amls-source-crosswalk`), `builds-on` (Adam → GD), `motivates`
   (logistic regression → GD), `applies-in` (convexity, feature scaling → GD).
4. `los.py atlas-context concept-logistic-regression` → `requires`
   concept-sigmoid and concept-conditional-probability; `builds-on`
   concept-linear-regression; `contrasts-with` concept-naive-bayes; etc.
5. `los.py atlas-context concept-adt-priority-queue` →
   `concept-fibonacci-heaps` —`requires`→ `concept-adt-priority-queue`, context
   in German ("'Erinnerung an ADT Priority Queue und Umsetzung mittels Heap';
   sl. 6 compares binary/binomial/Fibonacci bounds (sl. 2, 6)"), source
   `note-algo2-fibonacci-heaps`.
6. Linked-evidence existence checks (public reads):
   `los.py note-read note-aml-sad-master-wiring` → exists (32,756 chars, role
   crosswalk); `los.py note-read note-amls-source-crosswalk` → exists
   (`knowledge/notes/systems/…`); `los.py note-read note-algo2-fibonacci-heaps`
   → exists (`knowledge/notes/algorithms/…`); target concepts exist per the
   metadata search (`concept-gradient-descent`, `concept-sigmoid`,
   `concept-adt-priority-queue`).

Result: the connection is recorded in a typed row (`from`/`type`/`to`/
`context`/`source`, `relation_revision: 0`) that the public read
`atlas-context` prints; every row names its authored source note, and all three
source notes checked are present and readable. Linked evidence actually
available for the selected row: the source note, both endpoint concepts, and
the backlinked notes from `related`. Recorded limits: `related` shows only
`via:["relation"]` without the type; no public read found that prints relation
rows outside the per-concept `atlas-context` view. ASSUMPTION (mechanism, not
verified — implementation code not opened): the atlas derives these rows from
authored concept data whose canonical home is `knowledge/concepts.yaml` (the
path the concept records themselves publish), with the authored prose living in
the named source notes.

## Q3 — Reach a concept through a German alias published by the system

Alias discovered through a public read: `los.py inspect concept-convexity`
publishes `"aliases":["Konvexität","PSD Hessian","convex optimization"]`.

Wrong turns (recorded):
- `los.py search "Konvexität" --type concept` → empty (metadata search does not
  match alias fields).
- `los.py related Konvexität` → INVALID_REQUEST "record not found: Konvexität"
  (its help mentions resolution "through project aliases", which did not
  resolve concept aliases).

Success: `los.py material-context --concept Konvexität` → the resolved filter is
reported as `"concept":"concept-convexity"` in the response (`searched` block)
and the same explanation item as Q1 is returned (matched via
`stage:stage-icop-l01-geometry`). The German alias reaches its concept through
the `material-context` concept filter, which resolves declared ids and aliases.

Limit recorded: alias discovery is per-record via `inspect`; there is no
alias→record lookup in `search` or `related`; only the `material-context`
concept filter resolved the alias.

## Q4 — A saved question and its target

Honest absence. Scope chosen: the complete concept atlas.

Evidence: all 138 concept records were enumerated through the public read
(`los.py search "" --type concept --limit 100`, then `--offset 100`) and each
was passed through `los.py atlas-context <concept_id>` (138 calls, scripted,
read-only). Every response returned `"questions":[]`; 0 of 138 concepts carry a
saved question. The write command `atlas-question-save` exists in the
capability index, so the store is real but empty. Cross-check:
`los.py bootstrap --brief` lists recorded workspaces with next-actions
(`workspace-aml-exam-prep`, `workspace-bs-foundations`, `workspace-m2-exam-prep`, …)
— these are coordination records, not saved questions; the capability index
exposes no other saved-question query. The target-existence check is therefore
moot; the absence is a count, not a bug.

## Q5 — Follow a learning-material connection to an exact local page

Selected connection: stage resource `resource-icop-l01-forms-deck-forms`
(route `route-icop-l01-deck-forms`) on `stage-icop-l01-forms`, discovered via
`los.py plan-edit-context unit-icop-l01-linear-programming --stage-id
stage-icop-l01-forms` (locator `ico_linearprogramming.pdf, pdf pp. 1-23`,
`vault_path: material://source-icop-hu-ws2627/ico_linearprogramming.pdf`,
resource index 1 in the stage's canonical resource order).

Command: `los.py material-span unit-icop-l01-linear-programming
route-icop-l01-deck-forms --stage stage-icop-l01-forms --resource-index 1 --extract`.

Result (bounded output preserved in session log):
- Source identity preserved: `source_id: source-icop-hu-ws2627`;
  `material_uri: material://source-icop-hu-ws2627/ico_linearprogramming.pdf`;
  `binding.resolution: resolved`; `recorded_source_digest` ==
  `live_source_digest` == `76f3c809e569606b1d7422867ec0887f062aab814e6abeda31f2c990e15f45d1`;
  `file_sha256: sha256:76f3c809…`.
- Resolved locator: `"ico_linearprogramming.pdf, pdf pp. 1-23"`, availability
  `local-observed`, `extraction: range-truncated`.
- Exact local pages read: the extract prints `--- PDF p.1 ---` (deck title
  "Introduction to Combinatorial Optimization / Linear programming, Stefan
  Kratsch, Humboldt-Universität zu Berlin, Winter term 2026/27") through p.4+.
- Local file existence confirmed read-only:
  `/Users/aramaljanadi/los-glm-K2-2026-10/materials/algorithms/structures/icop-hu-ws2627/ico_linearprogramming.pdf`
  → 767,086 bytes (via the clone's own materials link; the live tree untouched).
- The same span names its analysis note (`note-icop-l01-reference`, resolved,
  current), tying Q5 back to Q1's explanation.

## Wrong turns and limits (consolidated)

- `resume --study` refused (no upcoming exam for an enrolled module) — plain
  `resume` is the working entry.
- Knowledge-map node labels (`knowledge-icop-l01-forms`) are not record IDs —
  `inspect`/`related` refuse them with suggestions.
- `search` does not match alias fields; `related` does not resolve concept
  aliases (only `material-context --concept` does).
- `related` does not print relation types; `atlas-context` does.
- An attempt to read `generated/manifest.json` directly found no such file in
  the clone (the projection is computed by the CLI, not committed) — abandoned;
  all reads stayed on CLI verbs.
- The public read surface exposes no saved-question count outside per-concept
  `atlas-context`; the 138-concept sweep was needed to establish the absence.

## Protocol notes

- No deviation to declare: CAMPAIGNS.md and implementation/test code were not
  opened before this file was written. No canonical YAML parsed. All commands
  read-only against the private clone; the live tree was only read for the
  pre-check and clone source.
- Distinguish throughout: no authored connection (Q1: no `requires` relation on
  `concept-convexity`; empty `concepts` on stage-icop-l01-forms), no linked
  evidence (none observed — all cited rows had their evidence present), and no
  saved question (Q4: 0/138). Missing content was counted, never classified as
  a bug; nothing was inferred, invented, or repaired.
- Untested scope: only concept-keyed atlas questions were swept (the atlas read
  is concept-keyed; no other saved-question store is exposed). Alias resolution
  was probed with one alias on three surfaces, not exhaustively. Knowledge-map
  chains beyond unit-icop-l01 and relation types beyond the five observed
  (`requires`, `builds-on`, `applies-in`, `motivates`, `contrasts-with`) were
  not enumerated.
