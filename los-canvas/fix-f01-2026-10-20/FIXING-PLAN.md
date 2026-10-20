# FIXING PLAN — LearningOS F-01 and neighbours

**For:** a fresh agent session.
**Written:** 2026-10-20, after a first implementation pass.
**Authority:** `~/los-canvas/reports/FIX-BRIEF-F01.md` (full brief) and
`~/los-canvas/reports/FINDINGS.md` (the report). Both were measured at Core
`1d32c918` / UI `66ca47aa`.
**Baseline to work from:** the certified pair — Core `40d8afe5028c3c811457ada1c81ac52fd42f8013`,
UI `66ca47aa7cf3eb2201a6af939e54a05471fa8594`.

> **Read the brief first.** Everything below is either (a) a correction to it,
> (b) work already done that must be kept, or (c) work still to do. Where the
> brief and this plan disagree, the reason is given.

---

## 0. Orientation

* **Core source of truth:** `LearningOS/repository` (the primary checkout).
  `LearningOS/materials` is the external materials tree; **`LearningOS/workbench/repaired-pair-gate-2026-10-19/repository`**
  is an isolated clone of the certified pair used for experiments.
* **The canvas** (`~/los-canvas`) is another agent's harness. Read it; do not
  mutate it. Its `canvas/probes/probe_scope_gap.py` is the per-part
  reproduction for F-01.
* **The UI** is `LearningOS/obsidian-ui`; the three pinned copies of the
  approval model are `system/contracts/capabilities.yaml`,
  `tools/learning_os/app/admission.py`, `obsidian-ui/scripts/check-contract.mjs`.

### The binding constraints (from the brief §5 and `system/OPERATOR.md`)

* The **operator path stays open** — Aram revises plans from the CLI with
  `--channel operator --approval-kind operator-approval`.
* The **`ui` channel stays** in `GATEWAY_CHANNELS` and in the app.
* The **warning baseline** must adopt any new signature in the same change.
* **`generated/` is never edited.**
* **Boundary 17:** `system/CRITIQUE-POINTS.md` is append-only; an open point is
  not a work item. If Part A turns out to be a settled judgement rather than a
  defect, append a point — do not act on one.
* **Do not** change a domain rule, a record shape, or a workflow's meaning
  while doing this.

---

## 1. What is true, measured, and corrected

| Finding | Status | Evidence |
|---|---|---|
| **F-01** — a stage can teach material its module never adopted, and the repo validates clean | **TRUE — reproduced** | `unit.map.import` exit 0, stage landed, `VALIDATE exit: 0`, 0 errors. A source registered globally but absent from the module's source map, at `"chapter 42"`, no `route_id`. |
| **F-02** — `los resume` labels the concept "Requirement" but the write path wants `requirement["id"]` | **TRUE** | `resume.py:775` printed `requirement["concept"]`; the IR schema requires `id` (`learning-requirement.schema.json`), and `resume.py:318` keys requirements by `req["id"]`. |
| **F-03** — a note body with its own frontmatter corrupts the published summary | **TRUE** | `notes.py:_render_exact_note` writes `front + body` verbatim; no check rejects a frontmatter-bearing body. |
| **F-04** — two resolvers disagree on `material://…#fragment` | **TRUE** | Write path (`canonical_material_uri`) preserves the fragment; the validator (`references.py:parse_reference_uri`, :31-36) does not strip it → the write is accepted and validation warns. |
| **F-05** — the promotion's "official-academic" evidence is asserted, never checked | **TRUE (canvas)** | A promotion landed carrying `https://nonexistent.invalid/probe/module-catalog`; nothing fetched it. **Not reproduced here** — the site is located in `app/admin/masters_planning.py:402-416`. |
| **F-06** — workflow 24's human acts are unreachable by construction | **POSITIVE (canvas)** | No capability retires a workspace or disposes of a garden seed. Nothing to fix. |

### Corrections to the brief's numbers (measured on the live corpus)

The brief says *"2,792 of 3,618 stage resources (77.2 %) carry no `route_id`"*.
True, but it counts one spelling only. The full picture:

```
stage resources                                   3618
  with route_id                                    826
  with material_ref.route_id                       862
  with NO route binding at all                    1930   (53.3 %, not 77.2 %)
    of those, resolvable by source_id+locator         2
    truly unbound (no route, no matching locator)  1928
      of those, kind: reference (pointers)           374
      of those, naming a source the module never adopted   21   (all module-skill-python)
```

Two consequences:

1. **The brief's rule is stricter than the defect.** It demands route- or
   locator-level resolution; only **21** resources are the actual
   "source the module never adopted" case. The other 1,907 are a *style*
   difference (descriptive locators like `"Ch 4 §Data Types pp. 105-109"`,
   and locator-only pointers like `"attachments/s4a-exercises.md"`).
2. **The brief's rule is also *under*-specified in one place:** it accepts
   `material_ref.route_id` as a binding — but **1,538 resources use that
   spelling and `references.py` never checks it**. A rule that trusts the
   spelling without resolving it is not a rule.

**On the error-level flip (the brief reserves it for Aram):** even the brief's
own rule would land as an error on 1,928 resources — 53 % of the corpus — and
one validation error blocks every canonical write. The *source-level* rule
would land on 21. That difference is the decision's real substance; it is
yours to make, not the fixer's.

---

## 2. What is already implemented (branch `fix/scope-authority-f01`)

Work done in an isolated clone at the certified baseline, committed as
`8be97a5` on branch `fix/scope-authority-f01` in
`LearningOS/workbench/repaired-pair-gate-2026-10-19/repository`
(working tree clean; **not pushed**).

| Item | Status | Where |
|---|---|---|
| **A** — scope warning | **Implemented, needs 2 corrections** | `derive/validation/plan_rigor.py` — new `RESOURCE-SCOPE-UNBOUND` warning, module-scoped resolution, archived modules skipped. Baseline adopted: 1,869 warnings / 40 signatures (the old baseline was empty). |
| **B** — CLI provenance | **Implemented, message must change** | `tools/seal_envelope.py` — refuses `--channel ui`, exit 2. |
| **C** — stop-and-ask | **Partly implemented** | `system/OPERATOR.md` boundary 18 ✓; `system/WORKFLOWS.md` §23 "Stop and ask first" ✓; **the "Start here" row is missing**. |
| **F-02** | **Implemented** | `app/handlers/resume.py` — prints the requirement id under "Requirement", the concept on its own labelled line. |
| **F-03** | **Implemented** | `app/handlers/notes.py` — `_precheck_note` refuses a frontmatter-bearing body (site `note.create.body-has-frontmatter`). |
| **F-04** | **Implemented in the wrong place — revert** | `store/materials/resolution.py` — `canonical_material_uri` now strips the fragment. |

### The corrections this pass needs

0. **NEW — the new refusal site must be *witnessed*.** This is the one
   obligation this pass created, and it is not optional.
   `tests/test_scenarios_zz_refusal_sites.py` scans every handler for
   `site="…"` literals; each one becomes a **declared site**, and
   `test_declared_site_is_witnessed_from_its_case` requires every declared
   site to be (a) *cased* — a scenario case in `tests/scenarios/cases/*.yaml`
   with `expect: {site: <site>}` — and (b) *witnessed in the session*.
   `note.create.body-has-frontmatter` is declared but not cased, so the gate
   fails with exactly that param id. Fix: add a case to
   `tests/scenarios/cases/note.create.yaml` beside the existing
   `expect: {site: note.create.empty-body}` (line 107) and
   `expect: {site: note.create.body-not-utf8}` (line 113) cases, sending a
   body that carries its own frontmatter.
   **General rule for this campaign: every new `site=` literal needs a
   witnessing case.** Part A adds a *warning*, not a refusal, and needs none;
   Part B's refusal is a CLI usage error (no `site=`), and needs none.

1. **A — close the `material_ref.route_id` hole.** The current rule returns
   early for *any* route-bearing resource, so a `material_ref.route_id` that
   names no route of the module passes unchecked. Resolve it against the
   module's own routes (1,538 resources use the spelling; **0** currently
   unbound, so this adds no warnings).
2. **A — decide the `reference` exemption.** The brief's risk table asks for
   it: *"that case is what `scope_triage: reference-only` and `kind: reference`
   exist for … exempt `reference` rows if the design intends them to point
   outside the map"*. Measured: **374** of the unbound rows are
   `kind: reference`. **Recommendation:** exempt `kind: reference` only
   (374 rows). Do **not** exempt on `scope_triage` alone — `deferred` /
   `reference-only` are flags the agent itself can set, which would turn the
   rule into an opt-out. If you prefer the strict reading, leave the
   exemption out; the warning set is 1,869 either way, only the meaning
   changes.
3. **B — align the message.** The brief's acceptance criterion expects the
   substring *"the 'ui' channel is the application's own provenance"*. The
   current message says "--channel ui is the app's own provenance and cannot
   be sealed from the command line". Use the brief's wording; keep exit 2.
4. **F-04 — revert and re-place.** The brief *prefers* the other option:
   *"strip the fragment in `parse_reference_uri` before the filesystem check,
   so both resolvers agree … Prefer the first: a fragment on a material ref
   is meaningful (the page to open), and the UI's `resource-target.ts`
   already understands page destinations."* My change made the **write path
   refuse** the fragment instead, which contradicts that and breaks
   page-destination support. **Revert `resolution.py`; strip the fragment in
   the validator's resolver** (`derive/validation/references.py`,
   `parse_reference_uri` / `_check_uri`) so the two agree. Then the write is
   accepted *and* validation is quiet — the world never ends in "write
   accepted, baseline gate broken".

### What is *not* implemented

* **F-05** (the promotion's unchecked verification) — see W7.
* **Every regression test** for the six items — see W8.
* **The "Start here" row** for Part C.

---

## 3. The work, item by item

Each item is independently shippable and independently testable. Ship A, B and C
separately, as the brief's risk table requires ("the canvas review was wrong
twice before").

### W1 — F-01 Part A: the scope rule

* **Site:** `tools/learning_os/derive/validation/plan_rigor.py`
  (`_module_scope_index`, `_check_row_scope`, called from
  `_check_stage_resource_rigor`).
  *Alternative:* `references.py` as the brief suggests — but that module owns
  the **error**-level reference checks; the rule is advisory, and `plan_rigor.py`
  already owns the advisory precedent the brief cites
  (`ANGLE-DIVERGES-FROM-ROUTE`). Keep it in `plan_rigor.py`.
* **Rule (as implemented):** a stage resource resolves when it names
  `route_id` / `material_ref.route_id` of one of the owning module's routes,
  or when `(source_id, locator)` matches one of that module's routes.
  Route-bound resources that fail to resolve are `references.py`'s business
  (unknown route → `REF-ROUTE`; wrong unit → `RESOURCE-ROUTE-OWNER`) — do not
  double-report them.
* **Corrections:** the two in §2 above (`material_ref` resolution; the
  `reference` exemption decision).
* **Baseline:** `tools/warning_baseline.py --update --note "…"` in the same
  change. The current baseline already holds 1,869 warnings / 40 signatures
  under `RESOURCE-SCOPE-UNBOUND`; re-run `--update` after any change to the
  rule.
* **Never** flip this to an error without Aram's decision, and do not
  "ratchet" it below the corpus without the migration path
  (`material_ref.route_id` with `inherit: [...]`,
  `tools/assemble_lecture_study_maps.py`).

### W2 — F-01 Part B: the CLI cannot mint the app's provenance

* **Site:** `tools/seal_envelope.py`, next to the existing channel check.
* **Change:** refuse `--channel ui`, exit 2, with the brief's wording
  (§2 correction 3). Do **not** touch `GATEWAY_CHANNELS`
  (`store/contracts/gateway.py:14`) and do **not** touch `admission.py`,
  `capabilities.yaml` or the UI's `check-contract.mjs` — the model does not
  move.
* **Why it is sufficient:** `admission.py:143-153` admits a
  `direct-user-gesture` only when the channel is `ui`, so refusing the
  channel in the CLI removes the amplifier completely (the gesture kind
  alone, on another channel, already fails closed).

### W3 — F-01 Part C: the stop-and-ask

* **Site:** `system/OPERATOR.md` (Hard boundaries — boundary 18 is **done**;
  the **"Start here" table row is missing**) and `system/WORKFLOWS.md` §23.
* **The decision the brief leaves open:** §23 has no transcript. The brief
  says: *"If a transcript exists for workflow 23, its first step must be the
  stop. If not, create the procedure as a stop-and-ask transcript."*
  **Recommendation: do not mint a transcript.** Creating
  `system/procedures/process-a-lecture.md` and pointing `INDEX.yaml` at it
  replaces the index cell "Untranscribable: …" with a transcript link — i.e.
  it makes an unimplementable workflow look executable, which is the opposite
  of the fix. Keep §23 declared untranscribable, keep the stop-and-ask in
  §23's own text (**done**), and add the boundary (**done**) plus the
  "Start here" row (to do). If you prefer the literal instruction, do it
  *and* keep the "Untranscribable" wording in the row's `untranscribable`
  field.
* **Optional, per the brief:** `admission.py:123-140` (`GESTURE_REFUSAL_RECOVERY`)
  could point `unit.map.import` / `module.plan.import` at the stop-and-ask
  rule rather than only at the operator path. This touches the *pinned*
  approval model — read the brief's "change one, change all three, or change
  none" before touching it.

### W4 — F-02: the resume label

* **Keep** the implementation (id under "Requirement", concept on its own
  line). The brief allows "print both". The `resume --json` payload must not
  change shape.
* **Add** the regression test (W8).

### W5 — F-03: the frontmatter refusal

* **Keep** the refusal; align the message with the brief's wording if you
  prefer: *"note body carries its own frontmatter; the writer owns the
  frontmatter — strip it and send the body only"*. The site name is free;
  `note.create.body-has-frontmatter` is in use now.
* **The check the brief asked for is done:** no canonical note carries a
  double frontmatter (0 of 145 in `knowledge/notes/`), and
  `system/procedures/create-durable-note.md` stages a body with **no**
  frontmatter (`# Triangulation memo …`).
* **Add** the regression test (W8).

### W6 — F-04: the two resolvers must agree

* **Revert** `store/materials/resolution.py`.
* **Implement** the brief's preferred option: strip the fragment in the
  validator's resolver (`derive/validation/references.py`,
  `parse_reference_uri` / `_check_uri`) so both sides resolve the same file.
* **Confirm** the corpus is unaffected: no canonical `material://` reference
  carries a fragment (checked — zero hits across `curriculum/`, `records/`,
  `sources/`, `knowledge/`, `work/`).
* **Add** the regression test (W8).

### W7 — F-05: the promotion's unchecked verification

**This one needs a decision, and it is a record-shape decision.**

The canvas measured a promotion landing on the strength of
`https://nonexistent.invalid/probe/module-catalog`: every other gate on that
path is real (catalog revision, candidate `selected`, source `deep-reviewed`,
checksum-bound candidate set, coverage-audit markers, six review checks,
two-pass package hash, expected revisions, warning-baseline gate, 30-day
evidence freshness, stale-verification refusal). The one thing missing is the
external fact.

The brief's options, in its own order of preference:

1. **Verify the evidence URL at write time** (strongest, most work).
2. **Require a named verifier** — the evidence carries the id of the review
   that checked the URL, so an unverifiable claim has no valid shape.
3. **Refuse an unresolvable host** (one-line shape check).

**Recommendation: option 2, and not option 1 or 3.** Both 1 and 3 require the
network inside a canonical write; the write path is offline-first today (the
30-day freshness rule is a *date* check, and `los validate --online` is a
separate, explicitly online audit). A network dependency in a write is a
domain-rule change and would need its own review.

Option 2 in practice: in `app/admin/masters_planning.py` (the
`verification` validation at :402-416), require each `verification.evidence[]`
to name a **local, content-bound verification artifact** — the way
`source.record.revise` carries a diff hash — so that "official-academic" is
verifiable by construction rather than asserted. A promotion whose evidence
carries no such artifact is refused, with a message naming the cause.

**This changes the accepted shape of the promotion package.** Per the brief's
§0 ("do not change a record shape") and boundary 17, that is a decision for
Aram, and possibly a compatibility review of its own. Present the three
options; do not implement option 2 without the answer.

### W8 — the regression tests (one per item, in the existing files)

| Item | Where | What it pins |
|---|---|---|
| A | `tests/test_plan_rigor.py` (or the nearest plan-rigor file) | a resource naming a source the module's map does not declare produces `RESOURCE-SCOPE-UNBOUND`; a resource bound to a module route does not |
| A | same | a `material_ref.route_id` naming a route of **another** module is flagged (the hole in §2) |
| B | the seal-envelope test file | `--channel ui` → exit 2 and the refusal text; `--channel operator` still seals |
| C | none needed (docs) | — |
| F-02 | the resume test file | the printed "Requirement" line carries the **id**, and that id is what `learner.observation.append` accepts |
| F-03 | `tests/test_note_create.py` | a body with frontmatter is refused by name; a body without one still writes |
| F-03 | `tests/scenarios/cases/note.create.yaml` | **the witnessing case for the new site** — without it the refusal-sites gate fails (see §2, correction 0) |
| F-04 | the materials test file | a `material://…#page=2` ref resolves identically in both resolvers, and the write stays accepted |

Adding tests is required by the brief's acceptance block ("each with a test").
Do not weaken or delete existing expectations.

---

## 4. Verification

```bash
# from a Core checkout that has its sibling UI and, where material-dependent
# scenarios run, the materials tree at ../materials
make check          # 0 errors
make warnings       # no new signature beyond the ones adopted in this change
make lint
make test           # the whole suite
make system-check   # the Core/UI release pair
```

Plus the brief's per-part criteria:

```bash
# 2. the CLI cannot mint the app's provenance
.venv/bin/python tools/seal_envelope.py --root . --capability garden.seed.create \
    --payload '{"text":"x"}' --key k --channel ui --out /tmp/e.json
#    expected: exit 2, "the 'ui' channel is the application's own provenance"

# 4. the operator path is untouched
.venv/bin/python tools/seal_envelope.py --root . --capability garden.seed.create \
    --payload '{"text":"x"}' --key k2 --channel operator --out /tmp/e2.json
#    expected: exit 0

# 1. the scope hole is closed (warning first)
#    los-canvas/canvas/probes/probe_scope_gap.py
#    before: validate exit 0, no warning; after: the new warning fires
```

### Environment requirements (learn this the hard way)

**The discriminator is `../materials`.** The isolated clone
(`workbench/repaired-pair-gate-2026-10-19/`) has **no materials tree**, and the
paired gate there reports **57 failures**:

* **56** are material-dependent scenario cases — `test_scenarios_effects`
  (`route.patch`, `module.plan.import`, `module.materials.compact`,
  `unit.plan.revise`, `session.end`, `status.read`, `resume.read`,
  `repository.validate`), `test_seal_guards_auto`, and
  `test_arch_suggestions::test_pointer_misses`. Their recorded expectation
  says the run changed canonical bytes and exited 0; without the material the
  run changes nothing, so the diff reads *"behaviour changed for
  route.patch/patch-success"*. They are **not** your change: the primary
  checkout, which has `LearningOS/materials`, passes them.
* **1** is caused by the new refusal site (§2, correction 0).

Two ways to be misled, both measured:

* Running a **subset** of the scenario corpus by node id fails even in a
  healthy tree: the corpus is a *sequence* (a base step, then its
  success/replay/refusal variants), so a case that expects its base to have
  run fails when it has not. `route.patch::patch-success` passes alone in the
  primary checkout and fails inside a hand-picked subset.
* `validate` reports `W MATERIALS-OFFLINE … 1519 inventoried file(s)
  unverified this run` in the clone without materials; the same warning is
  absent in the primary checkout. That warning is the cheap check.

**Therefore: run the authoritative suite in a tree whose sibling `materials`
tree is mounted** — the primary checkout (`LearningOS/repository`) or a clone
with the materials tree copied in (what the canvas did). The clone's 57 are
not evidence about your change.

* The UI needs `node_modules` (the `ajv` gap the canvas saw is exactly
  this); `npm ci --ignore-scripts` in `obsidian-ui/` fixes it.
* The UI gate harness needs a globally installed TypeScript; without it the
  operations-gate files error (the canvas's 10 errors).
* `make system-check` needs the sibling `obsidian-ui` at `../obsidian-ui`.

---

## 5. What must not change

* The operator path (`--channel operator --approval-kind operator-approval`).
* The `ui` channel in `GATEWAY_CHANNELS` and in the app.
* The three pinned copies of the approval model — change one, change all three,
  or change none.
* `generated/` (never edited).
* Any domain rule, record shape, or workflow meaning — beyond what the
  approved items above state explicitly.
* The warning baseline's meaning: a new signature is adopted **in the same
  change**, never left to fail the gate.
* `system/CRITIQUE-POINTS.md` is append-only, and an open point is not a work
  item.

---

## 6. Decisions for Aram (with a recommendation)

| # | Decision | Recommendation | Why it matters |
|---|---|---|---|
| 1 | **Error level for the scope rule** | **Warning, for now** | The route-level rule touches 1,928 resources (53 %); the source-level rule touches 21. One error blocks every canonical write. The flip is the *corpus migration*, and the migration path (`material_ref.route_id` + `assemble_lecture_study_maps.py`) has to exist first. |
| 2 | **Should `kind: reference` rows be exempt?** | **Yes — exempt `kind: reference` only** (374 rows). Exempting on `scope_triage` alone would let an agent opt out by flipping a flag it controls. |
| 3 | **Should the rule be unit-scoped or module-scoped?** | **Module-scoped** (as implemented) | Measured: 0 resources differ between the two readings on today's corpus. Unit-scoped would be stricter later, for no present difference. |
| 4 | **F-05: which option?** | **Option 2 (named, locally-bound verifier)** | Options 1 and 3 put the network in a canonical write; the write path is offline-first today. |
| 5 | **§23: mint a transcript or keep it untranscribable?** | **Keep it untranscribable** | A transcript link would make an unimplementable workflow look executable. The stop-and-ask lives in §23's text, in the boundary, and in a "Start here" row. |
| 6 | **The missing note-body view** (the canvas's reading-seam correction) | **Out of scope** | The UI *does* render a note's provenance bindings; the gap is the body (the projection carries 2.5 % of the corpus text). A separate piece of work, not a fix. |

---

## 7. Risks

| Risk | Why it is real | Mitigation |
|---|---|---|
| The scope rule lands as an error and bricks the repo | 1,928 route-less resources | warning first; baseline adopted in the same change; the flip is Aram's, after the migration |
| The rule flags legitimate pointers | `kind: reference` rows and descriptive locators | the exemption decision (above); the rule is advisory, so a false positive costs a warning, not a write |
| Part B breaks the app | the UI might use `seal_envelope.py` | it does not — it builds envelopes in process (`src/gateway-client.ts:465-480`); `make system-check` covers the boundary |
| Part B breaks a script | something may seal with `--channel ui` | grep for `--channel ui` before landing (the corpus is clean); the operator path is unchanged |
| Part C reads as a domain change | it adds a boundary and a row | it is two sentences of prose in the existing voice; no capability, schema or workflow change |
| F-04's fix lands on the wrong side | two plausible resolvers | the brief's option 1 is explicit: strip in the *validator*, keep the fragment meaningful |
| F-05 changes an accepted record shape | the promotion package's `verification` shape | decision before implementation; the alternative is to leave F-05 open and recorded |
| The fixes look like a refactor | the canvas review was wrong twice before | each item is independently shippable and independently testable; ship A, B, C separately |
| You trust a red suite that is only red for the environment | the materials tree | 56 of the clone's 57 failures are material-dependent scenario cases; reproduce in a tree that has `../materials` before believing them |
| A new refusal site is declared but unwitnessed | every `site=` literal is a declared site | the refusal-sites gate demands a witnessing case; ship the case with the refusal (§2, correction 0) |

---

## 8. Evidence index

* The brief: `~/los-canvas/reports/FIX-BRIEF-F01.md`; the report:
  `~/los-canvas/reports/FINDINGS.md`; the canvas probes:
  `~/los-canvas/canvas/probes/`.
* This pass's measurements and reproductions:
  `LearningOS/workbench/fix-f01-2026-10-20/` —
  `repro_part_a.py` (the F-01 reproduction: import succeeds, stage lands,
  validation clean), `evidence-system-check.txt` (the paired gate),
  plus the warning counts quoted in §1.
* The certified pair's own certification: hosted `release pair` run
  **39325973612** (success) and `validate` run **39325858381** (success) for
  Core `40d8afe`; the UI repository's own CI has never completed green on
  `66ca47aa` (three cancelled runs) — the pair is certified by Core's
  workflows, not by the UI's.
* Do not treat the *unverified review branch*
  `review/unverified-cleanup-2026-10-20` (Core, published earlier) as
  related work: it is a separate dead-code/documentation cleanup, and it is
  explicitly not certified.
