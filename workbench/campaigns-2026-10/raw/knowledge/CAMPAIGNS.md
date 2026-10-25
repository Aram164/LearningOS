# Knowledge-layer campaign: GLM 5.8 Flash workers, Codex verification

**For:** the atlas, concept relations and navigation. Updated 2026-10-25.
**Roles assigned by Aram:** Aram pastes the prompts; GLM 5.8 Flash runs K1–K4;
Codex verifies the completed reports. No worker launches or messages other chats.
**Start condition:** STATUS.md must say READY. Aram requested the handoff before
the final upstream checks finish; the packet pins the completed review candidate
and records that release acceptance and main landing remain pending.
This file supersedes the Claude draft in Documents/claude-drafts/C6-knowledge-campaign;
that draft is historical reference for this run.

Each batch runs in its own fresh chat. Read **Ground rules** first, then
only your own batch. All four worker batches use GLM 5.8 Flash.

## Why

The 2026-10-24 campaign tested three things:
- C1: whether commands keep data safe;
- C2: whether study plans point at the right material;
- C3: CI speed.

Nothing tested whether the knowledge layer is right or navigable:
- whether the atlas shows what the authored data says;
- whether each hop from a stage to a concept, a note and a material page
  resolves;
- whether the Obsidian atlas renders Core's projection faithfully.

C1-C touched the atlas, relation and semantic capabilities only for
write-path safety, and mostly by reading code. See
`LearningOS/workbench/glm-campaigns-2026-10-24/C1-C/REPORT.md`, "Attacked
and held".

**The law under test:**
- the binding ADRs in `system/adr/`: ADR-005 (domain atlas), ADR-015 (module
  × concept edges), ADR-016 (focused atlas navigation) and ADR-017 (atlas
  authoring);
- `system/ARCHITECTURE.md` §6 (concepts) and §8 (concept relations);
- the entries in `system/contracts/capabilities.yaml` for `atlas.context`,
  `atlas.question.save`, `concept.relations.change`, `semantic.query`,
  `note.search`, `material.context` and `material.span`.

## Ground rules

Use the earlier campaign's **Your own copies** environment setup (except K2's
live-data clone), **The laptop**, **Public repos**, and **Reporting** evidence
rules at `LearningOS/workbench/glm-campaigns-2026-10-24/CAMPAIGNS.md`.
This packet owns the base, model, role, reporting destination and finish signal.
Do not use the earlier packet's model/budget claims, CI/push authorization,
Claude orchestration or signal directory. This campaign does not authorize any
push or CI dispatch.

**Clones and base:**
- **Full clones from GitHub,** at `/Users/aramaljanadi/los-glm-K1-2026-10/`, `/Users/aramaljanadi/los-glm-K2-2026-10/`,
  `/Users/aramaljanadi/los-glm-K3-2026-10/` or `/Users/aramaljanadi/los-glm-K4-2026-10/`,
  with `repository` and (when needed) `obsidian-ui` children.
  K2 is the exception: like C2, it needs Aram's live data.
- **Base:** the exact Core/UI candidate pair named in STATUS.md. Record both SHAs
  and the clone path in the report. Do not silently advance a base mid-batch.

**Reading route:** K2 operates learner records and follows AGENTS.md → OPERATOR.md
and the focused capabilities. K1 and K4 follow Core's DEVELOPER.md route before
the specific code/tests named here. K3 reads the UI's CLAUDE.md, README.md and
ARCHITECTURE.md, plus Core's DEVELOPER.md for the producer boundary. The UI has
no separate DEVELOPER.md entry at its pinned revision.
Repository rules and the current task assignment govern both routes.

**Checkpoint:** write REPORT.md as you work, with completed/untested items and
exact commands. Keep command logs beside it. Resume from that record after an
interruption. Do not claim a test ran merely because its file was written.

**Never:**
- push, open a branch on GitHub, or dispatch a workflow. Every proof runs
  locally, one pytest file or one node test file at a time;
- edit `system/contracts/` in Core or `contracts/` in the UI.

**Absence is not a defect.** ADR-017 decision 5 separates three things:
- a missing authored connection;
- missing linked evidence;
- a recorded question.

None of them is evidence of the others. Report absences as counts in those
three categories.

**Never propose a concept, a relation or a tag as a fix.** Aram authors the
graph (ADR-017 decision 2).

Temporary reproduction files must follow the clone's test-registration rules.
A collection failure, broken fixture or unavailable environment is a setup gap;
a proposed bug must reach and fail the assertion for the stated behavior.

**A finding counts only with proof:**
- a failing test: pytest in Core, a node test in the UI;
- for K2, a re-runnable CLI command with its output.

**Signal and report:**
- The finish signal is as before, but its folder is
  `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-knowledge-campaign/signals/`.
- Reports go to `LearningOS/workbench/glm-knowledge-campaign/<batch>/`.

## K1: Core projections against the ADRs (GLM 5.8 Flash)

**Data:** fixtures only, the test suite's own; no live data.

**Read first, so you don't duplicate them:**
- `tests/test_module_concept_atlas.py`, `tests/test_atlas_authoring.py`,
  `tests/test_thematic_navigation_projection.py` and
  `tests/test_semantic_contract.py`;
- the projection code in `tools/learning_os/derive/projection/projection/atlas.py`
  and `indexes.py`.

**Attack each invariant** with a pytest that builds a fixture, projects it,
and checks:
1. **Edge evidence:** every `module_concept_edges` row has at least one
   evidence item. Each item resolves to the stage or knowledge node that
   carries that concept tag (ADR-015 decision 2).
2. **No inferred edges:** a concept named only in a title, a note body, a
   source evaluation or prose produces no edge (ADR-015 decision 2).
3. **One computation:** `unit_to_concepts`, `concept_to_units`,
   `module_to_concepts` and `concept_to_modules` equal pivots of
   `module_concept_edges` (ADR-015 decision 3).
4. **Cycles:**
   - a cycle among `requires` / `builds-on` fails validation with
     `REL-PREREQ-CYCLE` and one deterministic path;
   - the same cycle among semantic types passes (ADR-016 decision 4). The
     check lives in `tools/learning_os/derive/validation/registries.py`.
5. **Direction:** the generated Canvas draws every strict edge
   prerequisite → dependent (ADR-016 decision 3).
6. **Domain atlas:** `generated/domain-atlas.md` drops no shelf (the
   `cross-domain` fallback), and it harvests its descriptions from the
   canonical `description:` fields (ADR-005 decision 1).
7. **Aliases:** a German alias in `knowledge/concepts.yaml` reaches the same
   concept id through `material-context`'s concept filter and through note
   search (ARCHITECTURE §6).

**Output:** `K1/REPORT.md`, and each finding as
`K1/<slug>/{test_<slug>.py,finding.md}`, in C1's format.

## K2: navigation journeys over Aram's real data (GLM 5.8 Flash)

**Cold-start pass first.** Read only the operator route and public capability
help before inspecting implementation or parsing canonical YAML. Use natural
questions about the current stage, its prerequisites, existing explanations,
relation evidence, a German concept alias and a saved question. Choose the
exact existing stage/concept IDs through public reads. Record the question,
commands in order, wrong turns, files read, outcome and supporting record IDs.
Do not receive or fabricate a golden answer. Codex adjudicates the evidence.
Then run the scripted journeys below. This separates unaided route discovery
from checking that a known sequence of read commands resolves.


**Input:** like C2, a `--no-hardlinks` clone of the live branch, read-only
and never pushed.

Ensure the private clone uses the pinned code/docs revision in STATUS.md while
preserving its learner-data snapshot. Its sibling `materials` path must resolve
to `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials` through a
symlink, so public material reads can reach the real PDFs. Inspect an existing
path before creating the link; never overwrite it. The materials tree is
read-only for this campaign. A missing mount is a setup gap, not a navigation bug.

**Navigate through the system's own read commands** in `tools/los.py`:
`atlas-context`, `inspect`, `note-read`, `material-context` and
`material-span`. Never parse the YAML for this. The question is whether the
system navigates, not whether the data exists.

**Journeys.** Every hop must resolve:
1. a stage → its concept tags → the concept (`inspect`) → `atlas-context`
   for that concept;
2. a concept → the notes that carry it → `note-read` on each;
3. a note → its sources → one of each source's routes → `material-span` →
   the PDF page exists;
4. every question note → its target concept or relation exists;
5. every strict relation → both endpoints readable through `atlas-context`.

**For each failing hop,** record:
- the exact command;
- its output;
- what you expected, and what you observed.

Absences go into the three counts, not into findings.

**Historical baseline, not refreshed for this run.** Claude measured the YAML
in the C2 clone at `a2e2d49d` on 2026-10-24. Reconcile your measured public-read
counts with these; explain differences and never force them to match:

| What | Count |
|---|---|
| concepts | 138 |
| relations | 99 (67 of them strict) |
| concepts in at least one relation | 94 |
| notes | 152 |
| notes carrying concepts | 120 |
| concepts with at least one note | 119 |
| concepts with neither a note nor a relation | 19 |
| unknown relation endpoints | 0 |

Report your own numbers beside these, and explain every difference.

**Output:** `K2/REPORT.md`.

## K3: the Obsidian atlas against Core's projection (GLM 5.8 Flash)

**Setup:**
- the UI clone, and fixture data only (`fixture-vault/` and the tests' own
  fixtures);
- never Aram's vault, never the Obsidian app.

**Write node tests** in the style of `tests/test-atlas-graph.js`, using the
source-module loader, against `src/features/atlas/` and
`src/views/atlas-view.ts`:
1. **Route state** (ADR-016 decision 8): an unknown concept, lens or depth
   value falls back to the default and never throws. `lens` is one field.
2. **Focused graph** (decision 1): depth 1 by default. Whatever a depth bound
   excludes is counted and named.
3. **Layers** (decision 2): only `requires` / `builds-on` order anything.
   Semantic edges never reorder the path lens.
4. **Direction** (decision 3): every strict arrow points prerequisite →
   dependent. The inspector carries both sentences of one row.
5. **Modules are lenses** (decision 5): a module chip opens the exact
   evidence. No edge comes from shared module membership.
6. **Authoring** (ADR-017 decisions 1 and 3). The relation editor:
   - builds a `concept.relations.change` payload with exact old rows for
     replace and remove;
   - works with no AI provider configured;
   - surfaces Core's refusals (duplicate, unknown endpoint, cycle) instead of
     swallowing them.
7. **Questions** (ADR-017 decision 4): saving a question on a concept or a
   relation creates a question note, and never touches note `state`.

**If the loader cannot load a module** because it depends on the Obsidian
API, report that as a coverage gap, not as a finding.

**Output:** `K3/REPORT.md`, with the failing tests in `K3/<slug>/`.

## K4: the authoring path, probed (GLM 5.8 Flash)

C1-C mostly read these capabilities. K4 drives them through the real V2
gateway, in a fixture repository.
- **Skip** anything C1-C's "Attacked and held" marks as **probed**.
- **Re-attack** what it marks as **read**.

**`concept.relations.change`:**
- replace or remove with a stale old row;
- a cycle introduced by a replace, not an add;
- 50 operations, then 51;
- an operation that names an alias instead of an id;
- two sessions changing different rows under one snapshot.

**`atlas.question.save`:**
- a question on a relation rather than a concept;
- a target that `concept.relations.change` later removes;
- the same wording saved twice.

**Note-to-concept links:** a note names a concept id that is then removed.
Does validation name the note?

**Findings need a failing pytest,** as in C1.

**Output:** `K4/REPORT.md`, and each finding in `K4/<slug>/`.

## Verification after K1–K4: Codex

Aram will return when the workers finish. Codex re-runs every proposed bug's
reproduction on its recorded base, reads the cited contract and code, and
tries to refute the diagnosis. Findings become CONFIRMED, REFUTED or UNSURE
with reasons. Navigation failures are re-run with their exact commands; absence
and untested coverage remain separate. A worker's own judgment is provisional.
No worker performs K5 or declares the overall campaign accepted.

## Run order

Start K2 and K3 in two fresh chats after STATUS.md becomes READY. When K2
finishes, run K1 in a fresh chat; run K4 after K1. At most two worker chats
may be active, with one pytest process at a time. K2 uses read commands; K3
uses focused node tests. K1 and K4 run sequentially. Aram pastes every prompt.

The existing campaign cutoff remains: launch nothing after Sunday 2026-10-25
22:00 Europe/Berlin; the recorded free-credit deadline is Monday 02:00.
Read the actual provider balance before launching a later batch; no estimate
here assumes how cached input is counted.
