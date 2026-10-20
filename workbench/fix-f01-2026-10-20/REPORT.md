# REPORT — the F-01 scope fixes, the F-05 wording, and the integration branch

**For:** Aram
**Date:** 2026-10-20
**Repositories:** `LearningOS/repository` (Core) and `LearningOS/obsidian-ui`
(the release pair). The base is the certified pair, Core `40d8afe` / UI
`66ca47aa`.

This report answers the three questions the review asked, states what the
warning set is actually made of, and names the two things that are
deliberately left open. Every number below was measured on the tree it
describes; the commands are in the companion documents.

---

## 1. The three answers

### (a) The 274 source-level cases — the rule is right, the message is not

**Answer: the rule asks the route question, and the system's own records ask a
different one. Both granularities are real, so the 274 are not a false-positive
class — but for 139 of them the rule's *message* is wrong.**

The full write-up is `GRANULARITY-274.md`. The short form:

* A **route** answers "where in this source does *this lecture's* material
  live?" (PLAN-CREATION-SOP.md: each rich `unit_routes` entry is one
  source-to-lecture edge).
* A **disposition** answers "did this unit adopt this source?" (OPERATOR.md
  boundary 14: selected, reference-only, or deferred with a reason — recorded
  in the unit's `source_selections` / `scope_sources`).

They are complementary, not competing. So the rule — which asks the route
question, correctly, for a stage resource that names a *place* in a source —
stays exactly as approved: a warning, on the corpus it was adopted against.

What the message gets wrong: one wording covers three different findings.
For 139 rows the module *did* adopt the source and the *unit* never disposed
of it; the message says "adopt the material in the module's map", which the
module already did. For 135 rows the unit *did* record the adoption and the
module's map simply declares no route to the place the stage teaches. For
1,101 rows the row names no source at all and the module's scope is not
implicated.

**No rule change was made, and none should be made as part of this pass.**
The fix is in the message, and it is a separate change (see §5.2).

### (b) F-05's guarantee, stated accurately, with the limitation explicit

**What F-05 guarantees: attribution, not truth.**

The promotion's `verification.evidence[]` must now name a named review and a
local document whose bytes are bound by a digest, and that document must name
the evidence URL. The guarantee that follows is that the claim is *traceable*:
the document exists, inside the repository's own boundaries, matching the
digest the promotion recorded, and naming the URL.

**What it does not guarantee:** that the document substantiates the claim, and
that the URL resolves against the world. A document whose only content is the
URL satisfies the check. That is now stated in three places, so the boundary
is a deliberate one and not a drift:

| where | what it says |
|---|---|
| `system/schema/master-planning-promotion.schema.json` (the `verifier` description) | the guarantee is attribution, not truth; it does not establish that the document substantiates the claim, and it does not resolve the URL |
| `tools/learning_os/app/admin/masters_planning.py` (`_require_content_bound_verifier`) | the same, and names the consequence: a document whose only content is the URL satisfies the check |
| `tests/test_master_promotion.py::test_the_verifier_attests_attribution_not_the_claim` | pins the boundary executably, so strengthening it later is a deliberate change |

The write path stays offline-first: the thirty-day rule is a date check, and
`los validate --online` remains the separate, explicitly online audit.

The promotion package's accepted shape changed with it, so the data contract
was bumped (**v56**; the schema bytes moved, so the world's canonical
fingerprint moved with it). That is the whole of the record-shape change.

### (c) One integration branch carrying both review branches, fully certified

`integration/scope-and-cleanup-2026-10-20` is built from the certified pair's
Core (`40d8afe`) and carries both review branches:

* `review/unverified-cleanup-2026-10-20` — 3 commits, 14 files, +45/−135,
  all in `tools/` and docs; it touches no canonical root, so it moves no
  fingerprint and needs no extra churn. It is **not** certified on its own.
* `fix/scope-authority-f01` — the 7 commits of §3, rebuilt so that each is
  green on its own.

The merge is clean (the two branches share no file), and the branch was then
certified as a pair on that exact revision — `make system-check`, which runs
lint, typecheck, the offline validator, the warning-baseline gate, the whole
pytest suite, the UI's own `npm run check`, and stamps the pair.

**Each of the seven commits is green on its own**, verified at that commit
and not only at the tip: the gate (check / warnings / lint / typecheck) at
every commit, the whole suite at the two commits that carry the churn, and
the suites each small commit touches at the other five.

---

## 2. The warning decomposition

The scope rule reports **1,462** rows on the live corpus (38 signatures, the
measured baseline). They are not one finding:

| rows | what the row is | what the records say |
|---|---|---|
| **1,101** | names no source at all | nothing to resolve against a map: 490 name a file, 546 name prose, 65 name nothing. The module's scope is not implicated; what it usually shows is a missing `source_id` on a row that names a file or a lecture |
| **135** | a source the module declared, with no rich route | the unit **did** record the adoption (133 `source_selections`, 2 `scope_sources`); the module's map has no route to the place the stage teaches |
| **139** | a source the module declared, with no rich route | **no unit disposition at all** — the four `module-job-*` modules and `module-skill-python` declare sources with no routes whatsoever, and the units never disposed of them |
| **69** | a source that has a rich route, at a locator matching none | the descriptive-locator style difference |
| **18** | a source **no module declared** | **the actual defect** — all in `module-skill-python`, in `unit-python-intermediate-roadmap` and `unit-python-oop-scope`; none of the units selects them |

The 274 in the reviewer's question are the 135 + 139: the "no rich route"
population. The 18 are the defect the rule was written to catch.

---

## 3. What shipped

| finding | change | where |
|---|---|---|
| **F-01 A** | `RESOURCE-SCOPE-UNBOUND`: a stage resource must resolve to material its own module's source map declares | `tools/learning_os/derive/validation/plan_rigor.py` |
| **F-01 B** | the CLI cannot mint the app's own provenance (`--channel ui` → exit 2) | `tools/seal_envelope.py` |
| **F-01 C** | workflows 23, 24 and 27 are a stop-and-ask (boundary 18 + a "Start here" row) | `system/OPERATOR.md`, `system/WORKFLOWS.md` |
| **F-02** | the resume screen names the requirement *id* the write path accepts | `tools/learning_os/app/handlers/resume.py` |
| **F-03** | a note body may not carry its own frontmatter | `tools/learning_os/app/handlers/notes.py` |
| **F-04** | the two material resolvers agree on a fragment | `tools/learning_os/derive/validation/references.py` |
| **F-05** | the promotion's verification must name a content-bound artifact | `system/schema/master-planning-promotion.schema.json`, `tools/learning_os/app/admin/masters_planning.py` |

---

## 4. A fourth finding, from the read-only review: the unit boundary

A read-only review of this branch asked a fourth question: does the scope
rule hold the **unit** boundary, or only the module's?

**It holds only the module's, in one of the two spellings.** A row that
names a route id is held to the unit's question — `references.py` reports
`RESOURCE-ROUTE-OWNER` as an error when the route belongs to another unit.
A row that names *material* (a source and a locator) is checked against the
**module's** routes, because that is the rule as approved: "the same source
at the same locator as one of the module's routes". So a unit can reach a
sibling unit's material by spelling it instead of naming its route.

**Measured on the live corpus: the gap is empty.** 685 rows take the
(source, locator) path, and all 685 are declared by the row's *own* unit
(`tools/unit_ownership.py`). Nothing is being missed today; the asymmetry
is a possibility, not a live defect.

**Not changed in this pass, and it is your call.** The rule's wording was
approved (the plan's W1), and the review's own instruction on the 274 was
*not* to change the rule. The closure is one condition — the pair must be
declared by a route of the row's own unit, not merely of the module's — and
because the gap is empty, it changes nothing measurable on today's corpus:
a zero-churn tightening, whenever you want it. It is a decision about the
ownership layers (boundary 8: source evaluation, module role, unit
selection and stage action are distinct), which is why it is yours and not
the fixer's.

## 5. The two residuals
### 4.1 The Master's Planning catalog's `fact_state` is deliberately untouched

The catalog records a candidate source's facts as
`{status, as_of, evidence: [<free strings>]}`, and the promotion's
`_require_current_fact_state` accepts any non-empty list of strings. That is
the same weakness one level down from F-05, and it is left open on purpose:

* closing it is a **second record-shape change**, in a schema that carries
  348 candidate sources, through a different write path
  (`masters-planning.catalog.update`);
* all 348 candidates are `unverified` today, so nothing in the corpus depends
  on it;
* F-05's own change was already a record-shape change and it moved the
  world's canonical fingerprint, the procedure transcripts, the scenario
  recordings and the scenario fixtures. A second one in the same pass would
  double that churn for no observable gain.

The mechanism, when you want it, is the same one: the catalog schema's
`factState.evidence` items would accept the same `verifier` object beside the
existing strings, and a `verified-current` row would have to carry one whose
artifact exists, hashes to the recorded digest, and names the row's URL.

### 4.2 The scope rule's *message*, not the rule, is what needs work

The rule was approved as a warning against the measured corpus, and it stays
as it is. What it needs is a message that says which of three things is
missing, because one wording covers three findings:

| the row | the message should say |
|---|---|
| names no source (1,101) | this row claims no material, so the module's scope is not implicated — what it usually shows is a missing `source_id` on a row that names a file or a lecture |
| the unit adopted it, no route exists (135) | the unit's disposition is recorded; the module's map declares no route to the place this stage teaches — a route-level authoring gap |
| no unit disposition (139) | the module's map declares this source, but this unit never recorded a disposition (boundary 14) |

The granularity-aware variant was measured and **not** taken: judging a
source the module declares at source level at source level silences all 274
and lands on 1,188 warnings — but it silences the 139 (a real missing
disposition) along with the 135 (a real missing route). Fix the message
first, then measure again.

---

## 6. The branch map

| branch | what it is | tip |
|---|---|---|
| `fix/scope-authority-f01` | the seven focused commits, one per finding, each green on its own | `9e762c3d` |
| `integration/scope-and-cleanup-2026-10-20` | the certified integration: the pair, both review branches, this documentation | the branch's tip |
| `evidence/los-canvas-2026-10-20` | the external evaluation harness and its reports (published by the independent agent) | `5c5ee017` |
| `origin/main` | untouched — merging is your call | `1d32c918` |

The fixing branch, in order:

```
c7e50300  F-02  the resume screen names the requirement the write path accepts
5f205fae  F-03  a note body may not carry its own frontmatter
0fd50412  F-04  the two material resolvers agree on a fragment
d0f9adff  B     the CLI cannot mint the app's own provenance
e14b1783  C     workflows 23, 24 and 27 are a stop-and-ask
8db9ffdf  A     a stage resource must resolve to material its module adopted
9e762c3d  F-05  the promotion's verification must name a content-bound artifact
```

**These are new commits.** The first pass shipped the same seven fixes at
`6265f473`; F-05's guarantee was then stated inaccurately, and correcting it
changed the promotion schema's bytes — so the world's canonical fingerprint
moved, and with it every transcript and recording that pins a digest. The
branch was rebuilt from the certified pair so that each commit is green on
its own. The rebuilt tip's tree is **byte-identical** to the tree the first
pass had reached: the rebuild changed the history, not the result.

## 7. What the harness measured, and against which tree

The external harness (`origin/evidence/los-canvas-2026-10-20`) was run by an
independent agent against `6265f473` — the first pass's tip, before F-05's
guarantee was restated. The delta between that tree and the shipped one is
exactly the F-05 correction (the schema's description, the code's
docstring, one new test, the data contract v55 → v56) plus the commit ids.
None of it changes what the harness asserts: the correction narrows a
*claim about the guarantee*, and the harness's cases are about the
promotion being refused, the CLI's channel, the resume label, the
frontmatter, the fragment and the scope hole.

The harness is **not** on the integration branch, and cannot be: at the
repository root, `los-canvas/` is one validation error (`TREE-UNDECLARED` —
measured), because the tree contract denies a directory it does not
declare. The same directory under `workbench/` is accepted, so if you want
the harness inside the certified tree, that is the one move that makes it
possible — at the cost of the commit messages' citations
(`los-canvas/reports/t05`) reading as `workbench/los-canvas/reports/t05`.
That is your call, not mine.

---

## 8. What was not done, and what is yours

* **The rule was not changed**, and the warning was not flipped to an error.
  The flip is yours, after the corpus migration (`material_ref.route_id` +
  `tools/assemble_lecture_study_maps.py`), which the plan records as its
  precondition.
* **The catalog's `fact_state` was not migrated** (§5.1).
* **The message was not rewritten** (§5.2) — that is a separate change, and
  it is yours to approve.
* **The harness was not re-run against the shipped tip.** The published
  evidence measures `6265f473`; the delta is the F-05 correction and the
  commit ids, and it changes nothing the harness asserts (§6). Re-running
  it is a half hour of machine time and one more branch, and it was not
  worth delaying the certification for. Say the word and it is a single
  command.
* **`origin/main` is untouched.**
