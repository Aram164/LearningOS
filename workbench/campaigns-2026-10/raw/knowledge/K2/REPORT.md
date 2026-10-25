# K2 REPORT — navigation journeys over Aram's real data (2026-10-25)

Worker: GLM 5.8 Flash via ZCode, one operator chat for both phases.
STATUS.md said READY at start. Phase A (unaided cold-start navigation) is
recorded in `K2/COLDSTART.md`; this report covers phase B, the scripted
journeys and counts, and references phase A rather than repeating it.

## Base (recorded per Ground rules)

- Clone path: `/Users/aramaljanadi/los-glm-K2-2026-10/repository`
  (`--no-hardlinks` clone of the live Core, data base `7b713d84b5e8e48b7f8bdb6c88842c7ccbbda2ad`,
  clean; learner data preserved, nothing replaced).
- Core code/docs pin: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`
  (branch `codex/operator-developer-docs-20261025` fetched from
  https://github.com/Aram164/LearningOS.git, detached checkout, HEAD verified).
- UI pin f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94: not used — K2 exercises Core's
  CLI read surface only; no UI component was opened or needed.
- Materials sibling: `/Users/aramaljanadi/los-glm-K2-2026-10/materials` →
  `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials` (symlink,
  inspected before creation, nothing overwritten, tree read-only throughout).
- Environment: Python 3.14.4 `.venv`, `pip install -e '.[dev]'` — no setup
  failures. No `make setup`, no `make hooks`, no pushes, no CI dispatches, no
  live-vault edits, no writes to the repository (all reads).
- Data-base invariance: `git diff --stat 7b713d84…fb73b0f9 -- knowledge sources
  records work curriculum projects system/schema` → empty; the candidate
  changes no learner-data files relative to the snapshot.

**Reading route followed:** `LearningOS/repository/AGENTS.md` →
`system/OPERATOR.md` → `capabilities --compact --json` → focused
`capabilities NAME --json`. Phase B additionally read the law under test named
by CAMPAIGNS.md (`system/adr/ADR-016…` for the strict-relation definition,
`system/adr/ADR-017…` for the absence taxonomy and question-note family,
`system/ARCHITECTURE.md` §8 for the eight registry types) — binding system
docs, not learner YAML. Canonical YAML was never parsed.

## Journeys — all hops resolved; no failing hop, no proposed bug

Method note: every hop below is a public read via
`.venv/bin/python tools/los.py …`; command logs are in `K2/logs/`
(`k2-atlas-sweep.json`, `k2-relations-dedup.json`, `k2-related-sweep.json`,
`k2-note-coverage.json`, `k2-mockexam-targets.json`, `k2-unit-inspect.txt`).
Absences are reported as counts in the three ADR-017 categories, never as bugs.

### J1 — stage → concept tags → concept → atlas-context ✅

- `inspect stage-icop-l01-forms` → `"concepts":[]` (0 tags — count, not a bug).
- `inspect stage-icop-l01-geometry` → `"concepts":["concept-convexity"]` →
  `inspect concept-convexity` → resolved (title "Convexity", aliases
  `["Konvexität","PSD Hessian","convex optimization"]`) →
  `atlas-context concept-convexity` → 1 relation, 0 questions. Chain resolves.
- Cross-module repeat: `inspect stage-aml-l06-convexity` (module-hu-aml) →
  `"concepts":["concept-convexity"]` → same concept, same atlas read. Chain
  resolves from a second module.

### J2 — concept → carrying notes → note-read each ✅

`related concept-convexity` lists 6 notes via `backlink:concept_to_notes`;
`note-read` on each resolved 6/6, returning path + `content_sha256`:

| note | path | chars |
|---|---|---|
| note-aml-l06-exercise-bank | knowledge/notes/machine-learning/… | 4,755 |
| note-aml-l06-gradient-descent | knowledge/notes/machine-learning/… | 13,498 |
| note-aml-l06-mock-exam | knowledge/notes/machine-learning/… | 8,680 |
| note-aml-sad-master-wiring | knowledge/notes/cross-domain/… | 32,756 |
| note-icop-l01-exercise-bank | knowledge/notes/algorithms/… | 15,108 |
| note-icop-l01-mock-exam | knowledge/notes/algorithms/… | 12,579 |

### J3 — note → sources → one route per source → material-span → page exists ✅ (1 availability observation)

Leg 1 — `note-icop-l01-reference` (source `source-icop-hu-ws2627`, recorded
digest == live `76f3c809…`): route `route-icop-l01-deck-forms`,
`material-span unit-icop-l01-linear-programming route-icop-l01-deck-forms
--stage stage-icop-l01-forms --resource-index 1 --extract` →
`availability: local-observed`, `binding.resolution: resolved`, locator
`ico_linearprogramming.pdf, pdf pp. 1-23`, local page text extracted
(`--- PDF p.1 ---` deck title page of Kratsch's WS 2026/27 Linear Programming
deck; local file 767,086 bytes under the clone's materials link).

Leg 2 — `note-aml-l06-gradient-descent` (frontmatter sources:
`source-aml-ss26-lectures, source-murphy-pml1, source-cs229-notes, source-mml`),
one route per source via `material-span unit-aml-l06 <route> --extract`:

| source | route | availability | binding | digest match | page evidence |
|---|---|---|---|---|---|
| source-aml-ss26-lectures | route-446c1d8cfb60bd43f0315cdd | local-observed | resolved | yes | "PDF p.1" excerpt |
| source-murphy-pml1 | route-2859463c0a0acd4759eb3acb | local-observed | resolved | yes | "PDF p.307" excerpt |
| source-cs229-notes | route-f7a2035554358e7bdf8c0472 | local-observed | resolved | yes | "PDF p.10" excerpt |
| source-mml | route-6a75b1b8d8b317dabe077fb2 | **remote-unobserved** | none | n/a | none |

The `source-mml` leg is recorded in the failing-hop format although no
assertion failed: command as above; expected (per the journey) a resolvable
page; observed `remote-unobserved` with no binding and an empty extract — the
read reports availability honestly instead of pretending. Classified per the
Ground rules as the source's nature (no local copy), not a navigation bug and
not a missing mount: 3 of 4 sources resolved to real local pages.

### J4 — every question note → its target exists — honest absence, check path demonstrated

- Saved questions: `atlas-context` over **all 138 concepts** returned
  `"questions":[]` on every one — 0 saved questions in the atlas.
- Question notes (ADR-017 decision 4's `role: question` family): content search
  `search "role: question" --content --limit 100` → 10 candidates; `note-read`
  on each showed every candidate is `role: mock-exam` (viva drills mentioning
  the phrase in prose). **0 notes of 152 carry `role: question`.**
- Since no question note exists, the target check was demonstrated on the
  nearest existing family, clearly labeled as a substitution: frontmatter
  concept targets of `note-icop-l01-mock-exam` (`concept-convexity`) and
  `note-aml-l06-mock-exam` (`concept-gradient-descent`,
  `concept-adam-optimizer`, `concept-convexity`, `concept-feature-scaling`) —
  5/5 targets resolve via `inspect`. (Wrong turn recorded: my first ad-hoc
  frontmatter parser mishandled block-style lists and produced a false 0 for
  the ICOP note and a polluted 4th item for the AML note; fixed parser above,
  cross-checked against the system's own `related` backlinks. Counts elsewhere
  never relied on this parser.)

### J5 — every strict relation → both endpoints readable through atlas-context ✅

Strictness definition (the law under test): ADR-016 — **strict = `requires`
and `builds-on`**; ARCHITECTURE §8 fixes the registry at exactly eight types.
`atlas-context` was run on all 138 concepts (0 errors) and the printed relation
rows deduped by (from, type, to) — full rows in `logs/k2-relations-dedup.json`:

- 99 relation rows; strict subset 67 (requires 36 + builds-on 31);
  semantic 32 (applies-in 18, motivates 5, contrasts-with 5, derives 3,
  generalizes 1, equivalent-to 0 — the type is legal but unused: count).
- All 94 endpoint concepts are concept records; `atlas-context` succeeded on
  every one of them (the sweep itself), so both endpoints of all 67 strict
  relations are readable through `atlas-context`. 0 unknown endpoints.

## Measured counts vs historical baseline

Baseline = Claude's YAML measurement in the C2 clone at `a2e2d49d`, 2026-10-24
(historical, not refreshed). Mine = public-read projection measured today on
`fb73b0f9` over data base `7b713d84`. Methods differ (YAML vs read surface);
results:

| What | Baseline | K2 measured | Δ |
|---|---|---|---|
| concepts | 138 | 138 (`search "" --type concept`, paged) | 0 |
| relations | 99 | 99 (deduped `atlas-context` rows) | 0 |
| relations, strict | 67 | 67 (requires 36 + builds-on 31) | 0 |
| concepts in ≥1 relation | 94 | 94 | 0 |
| notes | 152 | 152 (`search "" --type note --page`, total field) | 0 |
| notes carrying concepts | 120 | 120 (distinct `backlink:concept_to_notes` targets) | 0 |
| concepts with ≥1 note | 119 | 119 | 0 |
| concepts with neither note nor relation | 19 | 19 (list in `logs/k2-note-coverage.json`) | 0 |
| unknown relation endpoints | 0 | 0 | 0 |

Every difference to explain is nil: the public-read projection and the YAML
measurement agree exactly, on every line. The 19 isolated concepts:
concept-activation-function, concept-bayesian-network, concept-chi-square-test,
concept-clustering, concept-conditional-independence, concept-distance-metrics,
concept-ensemble-methods, concept-k-means, concept-law-of-large-numbers,
concept-linear-algebra, concept-multiple-testing, concept-newton-method,
concept-nonparametric-tests, concept-sampling-bias, concept-similarity-search,
concept-simpsons-paradox, concept-supervised-learning,
concept-universal-approximation, concept-vanishing-gradients.

## Absence counts (ADR-017 decision 5 categories)

- **Missing authored connection:** 19 concepts with neither note nor relation;
  `stage-icop-l01-forms` carries 0 concept tags; `concept-convexity` is the
  endpoint of 0 `requires` relations (its single row is `applies-in`); the
  `equivalent-to` type has 0 rows. Counts, not bugs.
- **Missing linked evidence:** 1 source-availability observation — `source-mml`
  is `remote-unobserved` (no local bytes behind `route-6a75b1b8d8b317dabe077fb2`).
  All other checked links resolved with matching recorded/live digests.
- **Recorded question:** 0 saved questions (0/138 atlas) and 0 `role: question`
  notes (0/152). The store exists (`atlas-question-save` is a declared command)
  but is empty.

## Findings

**None.** No hop failed its assertion; nothing is proposed as a bug. All
non-resolutions observed are the three absence counts above.

## Untested scope (explicit)

- Alias resolution probed with one German alias on three surfaces only
  (`search`, `related`, `material-context`); other aliases and surfaces
  untested.
- Question-note enumeration relied on content search + per-candidate
  verification; a note whose role were spelled with quoting (e.g.
  `role: "question"`) would evade the literal substring and go uncounted
  (none observed among all candidates).
- Journeys exercised one concept deeply (`concept-convexity`), three stages,
  two notes' source sets, and the full relation/concept/note graph via the two
  138-call sweeps; other concepts' J1/J2/J3 chains were not individually walked.
- `material-span` page-existence checks read extracted text excerpts, not every
  page of every locator range.
- UI pins and the Obsidian atlas are out of K2's scope entirely (they are K3's).
- No writes were attempted anywhere, so no write-path behavior is covered.

## Protocol deviations

None material. Two disclosures: (1) phase B read the binding ADRs/ARCHITECTURE
§8 named as the law under test, to classify "strict" correctly — no learner
YAML parsed at any point; (2) phase A's COLDSTART.md was written before
CAMPAIGNS.md was opened, as required; the packet's per-batch chats are being
run by Aram as separate fresh chats, so this report is K2-only.
