# K1 — Core projections against the ADRs (REPORT)

**Result: 0 findings.** All seven invariants held under fixture attack. 25
probe tests across 7 files, every one green on the pinned base; the four
original focused test files re-ran green afterwards. One boundary observation
recorded under invariant 7 (not a finding — see below).

## Base

- Clone: `/Users/aramaljanadi/los-glm-K1-2026-10/repository` (full clone from
  `https://github.com/Aram164/LearningOS.git`, private branch `glm/K1-2026-10-25`).
- Core pin: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` (branch
  `codex/operator-developer-docs-20261025`), HEAD verified after checkout:
  `git rev-parse HEAD` → `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`
  (`fb73b0f9… "Refresh AI-delivery request hashes after corpus contract change"`).
- UI pin `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94` — recorded because
  STATUS.md names the exact candidate pair; K1 is Core-only and never loaded it.
- venv: `python3.14 -m venv .venv && .venv/bin/pip install -e '.[dev]'`
  (exit 0; log `/tmp/k1-venv-install.log`). `make setup` / `make hooks` not run,
  per the 2026-10-24 environment rules.
- Working-tree footprint in the clone (nothing committed, nothing pushed):
  7 untracked probe files `tests/test_k1_*.py`, plus test registration:
  `tests/group_map.py` (+7 lines, group `generation`) and
  `.github/shard-manifest.json` (+7 lines, leg `rest-0`). `git diff --stat`
  shows exactly those two files, 14 insertions, 0 deletions.
- No pushes, no CI dispatches, no `system/contracts/` edits, no live-tree
  edits, no production fixes. One pytest process at a time, one focused file
  per process, throughout.

## Reading route (completed before probing)

Core `AGENTS.md` → `system/OPERATOR.md` (hard boundaries) →
`system/DEVELOPER.md` (read-in-order route; task row "Add a test file" names
the registration rules) → `system/developer/CODEMAP.md` →
`system/developer/components/projection.md` → focused reading:

- The four files the batch names: `tests/test_module_concept_atlas.py`,
  `tests/test_atlas_authoring.py`,
  `tests/test_thematic_navigation_projection.py`,
  `tests/test_semantic_contract.py`.
- Projection code the batch names: `tools/learning_os/derive/projection/projection/atlas.py`
  and `indexes.py`, plus the surfaces the seven invariants live on:
  `projection/canvas.py`, `projection/atlas.py` (domain atlas),
  `projection/concepts.py`, `projection/outputs.py`, `projection/manifest.py`
  (call site), `derive/validation/registries.py` (`_prerequisite_cycle`),
  `domain/vocabulary.py` (type vocabularies), `app/handlers/notes.py`
  (`search`, content + metadata paths), `app/handlers/materials.py`
  (`material_context`, `_resolve_concept`).
- Law: ADR-005 decision 1, ADR-015 decisions 1–4 (5 retired by ADR-016),
  ADR-016 decisions 2–5 and 8, ADR-017 decisions 1–5;
  `ARCHITECTURE.md` §6 (bilingual policy) and §8 (eight relation types);
  capability entries for `atlas.context`, `atlas.question.save`,
  `concept.relations.change`, `semantic.query`, `note.search`,
  `material.context`, `material.span` via
  `.venv/bin/python tools/los.py capabilities <name> --json`.
- Test-registration rules (`tests/conftest.py::pytest_collection_modifyitems`
  asserts `group_map.check_map()`): a `test_*.py` on disk but in no group
  fails EVERY collection. Probe files are therefore registered in
  `tests/group_map.py` (group `generation` — the group that owns
  `test_module_concept_atlas.py` and `test_thematic_navigation_projection.py`)
  and in `.github/shard-manifest.json` leg `rest-0` (the leg carrying
  `test_thematic_navigation_projection.py`; all legs kept sorted).
  I also re-ran `test_material_context.py`'s alias test shape (read, not
  modified) to model invariant 7's fixture.

## Results per invariant

Every probe builds a synthetic fixture (the suite's own `mini_repo` +
`repo_builders`), projects it through `generate_all` (or the named function,
or the real CLI), and asserts. Probe copies: `probes/test_k1_*.py`; exact
pytest commands and full output: `logs/*.out`.

| # | Invariant (law) | Probe file | Result |
|---|---|---|---|
| 1 | Edge evidence exists and resolves (ADR-015 d2) | `test_k1_1_edge_evidence.py` | **HELD** — 3/3 |
| 2 | No inferred edges (ADR-015 d2) | `test_k1_2_no_inferred_edges.py` | **HELD** — 3/3 |
| 3 | One computation: indexes = pivots of edges (ADR-015 d3) | `test_k1_3_index_pivots.py` | **HELD** — 2/2 |
| 4 | Strict cycle refused, deterministic path; semantic cycle passes (ADR-016 d4) | `test_k1_4_prereq_cycles.py` | **HELD** — 6/6 |
| 5 | Canvas draws strict edges prerequisite → dependent (ADR-016 d3) | `test_k1_5_canvas_direction.py` | **HELD** — 4/4 |
| 6 | Domain atlas drops no shelf; canonical descriptions (ADR-005 d1) | `test_k1_6_domain_atlas.py` | **HELD** — 3/3 |
| 7 | German alias reaches the concept id (ARCHITECTURE §6) | `test_k1_7_alias_resolution.py` | **HELD** — 4/4 |

What each probe actually attacked:

1. **Edge evidence** — a fixture whose stage tags `concept-expected-value` and
   whose knowledge-map node tags `concept-variance`, projected through
   `generate_all`. Every published edge row carries ≥1 evidence item; every
   `stage-concept` item resolves to a study-map stage whose authored
   `concepts` tag carries the edge's concept; every `knowledge-node` item
   resolves to a knowledge-map node whose `concept_ids` carries it; every
   identity resolves through the manifest's own `units`/`study_maps`/`stages`
   rows (the consumer's drill-in surface); stage + node on one concept merge
   into one edge with both rows.
2. **No inferred edges** — `concept-kernels` registered in the concept
   registry (so absence can only come from the licensing rule, never from
   unknown-id dropping), then named ONLY in: unit title/scope, node
   title/summary, study-map stage objective, module title, a note's
   `concepts` + body, and a source evaluation's `concepts`. Pipeline output:
   zero edges, while the concept is still projected everywhere else. One
   licensed stage tag alongside all that prose yields exactly one edge. A
   second probe plants `concepts` on the module record, on the unit, and on a
   node (non-canonical shapes ADR-015 explicitly rejects) directly against
   `build_module_concept_edges`: no edge.
3. **One computation** — a fixture with two stages carrying one concept and
   two nodes carrying another (duplicate pivots to collapse). All four
   indexes (`unit_to_concepts`, `concept_to_units`, `module_to_concepts`,
   `concept_to_modules`) equal the pivots of the published edges exactly,
   duplicates collapsed; edges empty ⇒ all four tables `{}` (the repaired-
   tables regression from ADR-015's context).
4. **Cycles** — strict 2-cycles in mixed strict types, a self-loop, and a
   semantic 2-cycle (`motivates`/`derives`), plus a mixed graph where a
   `contrasts-with` cycle coexists with a strict one. `REL-PREREQ-CYCLE`
   fires exactly once, names a closed walk over strict edges only, is
   byte-identical across two validations, and is identical when the relation
   file lists the same edges in reversed order (the walk's determinism is
   sorted-start + sorted-neighbours, not file order). The semantic cycle
   validates clean.
5. **Canvas direction** — `variance builds-on expected-value` renders
   `fromNode=concept-expected-value → toNode=concept-variance` (prerequisite →
   dependent) with sides right/left and label `prerequisite for (builds-on)`,
   while the edge id keeps the canonical `from--type--to` spelling; the
   `motivates` edge keeps canonical direction and bare label; the
   prerequisite's card sits further left (x = prerequisite depth); and the
   Mermaid concept map draws the same strict edge the same direction
   (dotted) while excluding the semantic edge — the two projections agree.
6. **Domain atlas** — three collections (one mapped to `mathematics`, one to
   `machine-learning`, one the view-level map has never heard of). All three
   are linked exactly once; the unlisted one lands under `cross-domain` (the
   fallback ADR-005 decision 1 requires); the printed description is the
   canonical `description:` field verbatim (compacted, prefix-verified for
   the >220-char case, never authored by the view); a domain without shelves
   says "Shelves: none yet" instead of going silent; all seven known domains
   publish even when empty.
7. **German alias** — through the real CLI on a fixture whose note text never
   mentions the alias: `material-context --concept Erwartungswert` and
   `--concept concept-expected-value` return the identical item set, and the
   response names the resolved canonical id in `match.concept`;
   `erwartungswert` (case-folded) behaves the same; an undeclared term
   refuses with exit 2 ("matches no id or declared alias"); and
   `search --type concept Erwartungswert` returns the concept row
   `concept-expected-value` (concept manifest rows publish `aliases`, so
   metadata search reaches the id from the German term).

## Boundary observation (recorded, NOT a finding)

**Content-mode note search does not expand declared aliases.**
`search --content Erwartungswert` returns 0 hits while
`search --content concept-expected-value` returns the two notes carrying that
id in frontmatter (`test_k1_7_alias_resolution.py::test_content_search_boundary_recorded`,
log `logs/test_k1_7_alias_resolution.out`). Invariant 7 still holds through
the two declared paths the batch names: material-context's concept filter
(explicitly promises "concept filter resolves declared ids and aliases" in its
capability entry) and note search reaching the concept id via the concept
record's published aliases. `note.search`'s capability entry declares only
"content mode searches complete registered durable notes and returns bounded
line snippets" — no alias expansion is promised, so there is no violated
contract line, and I am not proposing one. Recorded so the absence is a
counted fact rather than a surprise: a learner who searches the German term
in content mode finds notes only when the notes themselves use the German
word. Whether the Atlas should bridge that is an authoring/product decision
that belongs to Aram (ADR-017 decision 2).

## Probe-authoring notes (for the verifier)

- Three of my first probe drafts failed on fixture mistakes, not on Core
  behavior; each was corrected and the final runs are what the logs hold:
  probe 1 asserted a stale concept set after retagging its own fixture;
  probe 3's synthetic second stage used `working_note: None`, which the
  manifest shape lock correctly refused (`ManifestContractError`, fail-closed
  on a schema-invalid stage — the right behavior, and a usable reminder that
  the shape lock guards every fixture probe); probe 6 used list-membership
  where substring matching was needed. No Core behavior changed between any
  of those runs.
- `run_los` CLI invocations used: `material-context <q> --concept …`,
  `search <term> --type concept`, `search <term> --content` (the note.search
  verb is `search`).

## Logs

- `logs/test_k1_1_edge_evidence.out` … `logs/test_k1_7_alias_resolution.out` —
  one file per probe, each produced by
  `.venv/bin/pytest tests/<file> -v` from the clone root (exact command
  visible in each file's header line), final passing runs.
- `logs/original-focused-tests-after-probes.out` — the four files the batch
  named, re-run after the probes landed in `tests/`:
  `test_module_concept_atlas.py` 16 passed, `test_thematic_navigation_projection.py`
  4 passed, `test_atlas_authoring.py` 6 passed, `test_semantic_contract.py`
  99 passed.
