# FIX BRIEF — F-01 and neighbours

**For:** another agent working in `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository`
**From:** the LearningOS testing canvas, 2026-10-20
**Evidence:** `los-canvas/reports/FINDINGS.md`, `los-canvas/reports/t03/`, `los-canvas/canvas/probes/`

Every claim below was measured against commit `1d32c918` (Core) and `66ca47a`
(UI) in an isolated clone. Paths and line numbers are from those commits.

---

## 0. Read first

* `system/OPERATOR.md` — the operator contract. Hard boundaries 1, 2, 12, 13,
  16, 17.
* `tools/learning_os/app/admission.py` — the approval model (read the
  comments; they explain the intent precisely).
* `system/contracts/capabilities.yaml` — the contract mirror of that model.
* `tests/test_observation_gesture.py` — what pins the model.

**Do not** change a domain rule, a record shape, or a workflow's meaning while
doing this. The fixes below are admission decisions, one validation rule, one
refusal, and two one-line label fixes.

---

## 1. F-01 in one paragraph

An AI agent acting as the librarian can install **its own scope authority**
into the curriculum — a stage that names material the module never adopted
and a locator no reviewed route ever declared — and the system validates it
with **zero errors**. The plan-revision path (`unit.map.import`) is
sanctioned for the operator, and under agent-as-librarian the agent *is* the
operator, so nothing distinguishes "the operator applied a reviewed plan" from
"the operator applied a plan it wrote three seconds earlier".

---

## 2. The measured evidence

### 2.1 The ladder (canvas case `e1b`, `reports/t03/`)

Each rung ran in its own fresh synthetic world. Writes went through
`seal_envelope.py` → `los capability`, exactly as the contract requires.

| Rung | What the agent did | Result |
|---|---|---|
| A | hand-wrote a study map with no `plan_template_version` | refused — creation contract |
| B | used `los plan-template` output, placeholder left in place | refused — `source_plan.path is still the template placeholder` |
| C | v1-conforming map that *replaces* the existing one, retirement undeclared | refused — `this revision removes existing stages and their recorded evidence: stage-demo, stage-demo-pending — declare each with --retire-stage` |
| D | same, with every retirement declared and a reason string | refused — `E REF-STAGE: resume pointer references an unknown stage [curriculum/resume.yaml]` |
| E | **kept the map, added one stage of its own devising** | **ACCEPTED — seal 0, apply 0, stage installed, validation clean, receipt written** |

Rung E needs no retirement, no reason string, and no human. The agent wrote
its own `objective`, its own `done_when`, and a resource locator into a book
section that was never assigned.

### 2.2 The approval matrix (canvas case `g1`)

| channel | approval kind | apply | agent's stage installed |
|---|---|---|---|
| `codex` | `direct-user-gesture` | **2 — refused** | no |
| `ui` | `direct-user-gesture` | 0 | **yes** |
| `operator` | `operator-approval` | 0 | **yes** |

The `codex` refusal text (`tools/learning_os/app/admission.py:160-165`):

> `unit.map.import is authorized by a reviewed action in the LearningOS app,
> not by a codex-channel request: apply it from the screen that shows the
> exact change, or send it through the approved operator path`

That last clause is the hole: the operator path is offered as an alternative,
and the agent takes it.

### 2.3 The scope gap (canvas probe `probes/probe_scope_gap.py`) — **the sharpest form**

A source registered globally but **never adopted by the module's source map**,
placed on a stage with a locator no route declares:

```
source registered: True
module-demo declares: ['source-demo-book']
probe source in module map: False
map import: 0
stage landed: True
VALIDATE exit: 0 | errors: []
```

So the agent does not need to fake a gesture, impersonate the UI, or even
name a plausible locator. It can point a stage at a book the module never
listed, at "chapter 42", and the repository stays clean.

**Why this is a defect and not a design choice.** The system already defines
scope precisely and enforces it elsewhere:

* `system/OPERATOR.md` boundary 14: *every learning source named by an
  authoritative template, bibliography, plan or course artifact must remain
  reachable and be explicitly selected, reference-only, or deferred with a
  reason* — and a module's source map is the record of that decision.
* `system/OPERATOR.md` boundary 6: *a knowledge map and a complete material
  menu say what a lecture covers and what may be used*.
* `tools/learning_os/derive/validation/references.py:300-310` already checks
  a **unit's source selection** against the module's routes
  (`RESOURCE-SOURCE-GUARD`).

What is missing is the same check for a **stage's resource**. In
`references.py:404-435` the validator checks:

* `REF-SOURCE` — the resource's `source_id` is a registered source;
* `REF-ROUTE` — *if* the resource names a `route_id`, that route exists;
* `RESOURCE-ROUTE-OWNER` / `RESOURCE-SOURCE-GUARD` — route/unit/source agree.

**But a resource is not required to name a route at all.** `route_id` is
optional in `system/schema/learning-plan.schema.json` (`resource` requires
only `kind`), and a route-less resource is never checked against the module's
source map. In `plan_rigor.py:358-405` and `:457-470` the rules `return`
silently when the route does not resolve — so even a *dangling* `route_id`
on a stage resource is not an error.

The result: the module's source map — the reviewed statement of what the
module covers — does not constrain what a stage may teach.

---

## 3. The fix, in three independent parts

### Part A — bind a stage's scope to the module's reviewed source map **(recommended; this is the real defect)**

**Rule to add:** a curriculum stage's resource must resolve to a route the
unit's module source map declares. Concretely, for a stage resource in a
curriculum study map, require one of:

* `route_id` naming an existing route of that module (`routes_by_id`), **or**
* `material_ref.route_id` naming one, **or**
* `source_id` that the module's source map declares for that unit, **and** a
  `locator` that matches one of that source's routes.

The machinery already exists: `iter_route_references(r)` builds
`routes_by_id` (`references.py:53-66`), and
`tools/learning_os/domain/material_refs.py` already resolves a resource's
`material_ref` to a route. The new rule is a *requirement*, not new
resolution code.

**Where to put it:** `tools/learning_os/derive/validation/references.py`, in
the same `for smid, study_map in r.study_maps.items():` loop that already
walks `stage["resources"]` (line 400ff). Use the existing `self.err(...)`
machinery and the existing `routes_by_id` index.

**Severity — read this before you write it.** In the live corpus, **2,792 of
3,618 stage resources (77.2 %) carry no `route_id`**:

```
stage resources in the live corpus: 3618
  with route_id: 826  (22.8%)
  WITHOUT route_id: 2792  (77.2%)
```

Making this an **error** would turn the live repository into 2,792 errors and
block every canonical write (boundary: *"one validation error anywhere blocks
every canonical write"*). So:

1. Land it as a **warning** with a new code, e.g.
   `STAGE-SCOPE-OFF-MAP`, and adopt the baseline in the same change:
   `.venv/bin/python tools/warning_baseline.py --update --note "stage scope off the module map (new rule)"`.
   Then `make warnings` stays green.
2. Follow the pattern `plan_rigor.py` already documents for
   `ANGLE-DIVERGES-FROM-ROUTE`: *"A warning, not an error, and deliberately
   not yet in the baseline: each row is either a legitimate per-placement
   refinement or an unrecorded correction, and only a human reading both can
   say which."*
3. Then ratchet: the migration path is `material_ref.route_id` with
   `inherit: [label, source_id, locator, angle, angle_detail, url, vault_path]`
   (see `system/schema/learning-plan.schema.json`, `resource.material_ref`).
   `tools/assemble_lecture_study_maps.py` is the documented structural
   regeneration path; consider whether it can bind the route-less rows.
4. Only after the corpus is bound should it become an error — and that is
   Aram's call, not this change's.

**What this does and does not stop.** It stops the agent from *inventing
scope*: to put "chapter 42" on a stage, the source would first have to be a
route in the module's source map, and adding that route is
`module.plan.import` — a different capability with its own preflight, plan
hash and receipt. It does not stop the agent from extending a study map with
real, declared routes — which is legitimate librarian work and must keep
working.

### Part B — stop the CLI from minting the app's provenance **(the amplifier; cheap)**

**Change:** `tools/seal_envelope.py` refuses `--channel ui`.

```python
# tools/seal_envelope.py, next to the existing channel check (~line 425)
if args.channel == "ui":
    print("seal_envelope: the 'ui' channel is the application's own "
          "provenance; the CLI cannot claim it", file=sys.stderr)
    return 2
```

**Why this is safe:** the Obsidian UI does **not** use `seal_envelope.py` — it
builds its envelope in-process (`src/gateway-client.ts:465-480`, `channel:
'ui'`, `approval.kind: 'direct-user-gesture'`). Verified: no reference to
`seal_envelope` anywhere in `obsidian-ui/src/` or `obsidian-ui/scripts/`.

**Why it matters:** the `ui` channel is the system's only expression of
*"a human pressed a button"*. `tools/learning_os/app/admission.py:81-89` says
so honestly:

> *"The restriction to `channel == "ui"` is what keeps this from widening
> agent authority: a codex- or system-task-origin envelope claiming a
> gesture for these still fails closed. The channel label is provenance
> inside this trusted local application, not cryptographic proof that a human
> was present, and it is not treated as more than that."*

Making the CLI unable to claim `ui` restores exactly the property that
sentence claims. It is one guard in one tool.

**Do not** remove `"ui"` from `GATEWAY_CHANNELS`
(`tools/learning_os/store/contracts/gateway.py:14`) — the app needs it.
Only the *CLI's* ability to mint it goes away.

### Part C — make workflows 23, 24 and 27 a stop-and-ask **(the procedure gap)**

Workflows 23, 24 and 27 are declared untranscribable in the OPERATOR.md
procedure index, and the index is *index*. An agent that has read the manual
knows to stop; an agent under task pressure may not.

**Change (two places, no code logic):**

1. `system/OPERATOR.md` — the "Start here" table gains a row, and the
   "Hard boundaries" list gains one numbered boundary in the same voice as
   the existing seventeen. Something like: *23, 24 and 27 have no
   executable path; an agent that reaches one stops and asks, because the
   scope authority they need does not exist yet.*
2. `system/procedures/process-a-lecture.md` — does it exist? If a transcript
   exists for workflow 23, its first step must be the stop. If not, create
   the procedure as a stop-and-ask transcript.

**Also consider:** `tools/learning_os/app/admission.py:123-140`
(`GESTURE_REFUSAL_RECOVERY`) already carries per-capability advice for
refusals. `unit.map.import` and `module.plan.import` could carry a line
that points at the stop-and-ask rule rather than only at the operator path.

---

## 3b. F-05 (found while building T05) — the promotion's "official-academic" claim is never checked

**This is a separate defect and a separate fix.** Workflow 27's promotion
package carries:

```json
"verification": {"policy": "official-academic-30d-v1",
                  "status": "verified-current",
                  "as_of": "2026-10-20",
                  "evidence": [{"authority": "official-academic",
                                "url": "https://nonexistent.invalid/probe/module-catalog",
                                "claim": "…", "verified_on": "2026-10-20"}]}
```

The canvas promoted a Master's module with exactly that, and it **landed**
(`module_promoted: true`, seal 0, apply 0). The URL cannot resolve; nothing
fetched it. The catalog's own `fact_state.status: verified-current` — whose
`evidence` is a list of free strings — is equally self-asserted.

Every other gate on that path is real (catalog revision, candidate
`selected`, source `deep-reviewed`, checksum-bound candidate set,
coverage-audit file with required section markers, six review checks, the
two-pass package hash, the expected revisions, the warning-baseline gate on
the introduced plan, the 30-day evidence freshness, and the refusal of
stale verification). The one thing missing is the external fact.

**Fix, in order of preference:**

1. **Verify the evidence at write time.** `los validate --online` already
   audits external URLs; the promotion path could require that verdict for
   every `verification.evidence[].url` (and refuse a promotion whose
   evidence does not resolve). This is the strongest fix and the most work.
2. **Require a named verifier.** `verification.evidence[]` could carry the
   id of the review that checked the URL, the way `source.record.revise`
   carries a diff hash — so an unverifiable claim has no valid shape.
3. **At minimum, refuse an unresolvable host.** A promotion whose evidence
   points at a host that cannot resolve is not "verified-current" in any
   useful sense; refusing it is a one-line shape check and still catches the
   agent-written case.

Whatever is chosen, the *record* already keeps the claim verbatim
(`curriculum/quarantine/masters-planning/promotions/<id>.yaml`), so the
audit trail is honest — it is the acceptance that is unchecked.

## 4. The three smaller findings (cheap, independent, ship them too)

### F-02 — `los resume` names the requirement twice under two labels

`tools/learning_os/app/handlers/resume.py:775` prints

```python
lines.append(f"  Requirement  {concept}")
```

where `concept = requirement.get("concept", "")`. The requirement's **id**
(`requirement["id"]`) is what `learner.observation.append` requires. The same
screen prints the id eight lines down, under a different label:

```
  Requirement  knowledge-demo-expectation
  ...
  Next         los observe req-demo-l01-demo --activity <what-you-did> --result ...
```

Feeding the value from the "Requirement" line into the write path gives:

```
seal_envelope: unknown requirement: knowledge-demo-expectation; fix the payload and seal again
```

**Fix:** print the id under the "Requirement" label (e.g.
`Requirement  req-demo-l01-demo  (knowledge-demo-expectation)`), or print
both. One line in `resume.py`, plus the matching line in the `resume --json`
payload if it changes shape (it must not).

### F-03 — a note body carrying its own frontmatter silently corrupts the note

`note.create` prepends its own frontmatter
(`tools/learning_os/app/handlers/notes.py:46-53`, `_render_frontmatter`) to
the bytes of `body_file`. Nothing stops the body from carrying a second
frontmatter block. The result validates with **0 errors**, and the published
summary becomes the stray YAML:

```
SUMMARY: 'id: note-f1-duplicate type: note title: "Body with its own frontmatter"'
```

**Fix:** in `_precheck_note` (`notes.py:328-370`, which already checks the
body is non-empty and valid UTF-8), refuse a body that begins with a
frontmatter block — e.g. `body.lstrip().startswith("---")` followed by a
closing `---` — with a refusal that names the cause:

> `note body carries its own frontmatter; the writer owns the frontmatter —
> strip it and send the body only`

Use the existing `WriteRefused(..., site="note.create.…")` machinery.

**Check first:** does any procedure or test legitimately send a body *with*
frontmatter? `system/procedures/create-durable-note.md` stages a body file;
confirm what it contains before refusing.

### F-04 — two resolvers disagree on a `material://…#fragment` reference

| stage | `material://source-demo-book/lecture-01.pdf#page=2` |
|---|---|
| write (`note.evidence.add`) | **accepted** (exit 0) |
| validate | **warns** `URI-MATERIAL: … does not resolve on disk` |
| warning-baseline gate | **fails** — `NEW URI-MATERIAL … 0 → 1` |

The seal-time materials check strips the fragment;
`tools/learning_os/derive/validation/references.py:562-590` (`_check_uri`,
via `parse_reference_uri` at `:31-36`) does not. So a write the system
accepts can break the acceptance gate that OPERATOR.md boundary 13 makes
mandatory.

**Fix (pick one):**
* strip the fragment in `parse_reference_uri` before the filesystem check, so
  both resolvers agree; **or**
* make the evidence `ref` grammar reject fragments, so the write path and the
  validator agree by refusing.

Note that **no canonical record uses a fragment today** — `material://` refs
in the corpus are bare paths — so either fix is behaviour-preserving for the
live corpus. Prefer the first: a fragment on a material ref is meaningful
(the page to open), and the UI's `resource-target.ts` already understands
page destinations.

---

## 5. What must not change

* **The operator path must keep working.** Aram revises plans from the CLI
  with `--channel operator --approval-kind operator-approval`. Do not close
  that; the defect is that *scope* is unbound, not that the path exists.
* **The `ui` channel stays** in `GATEWAY_CHANNELS` and in the app.
* **The capability catalog mirror stays in sync.**
  `system/contracts/capabilities.yaml` is the contract; `admission.py` is
  pinned to it by `tests/test_observation_gesture.py:206-234`
  (`test_allowlist_matches_the_capability_contract`) and by
  `tests/test_observation_gesture.py:255-265`
  (`test_a_reviewed_workflow_is_admitted_only_over_the_ui_channel`). The UI's
  producer-side copy is pinned by `obsidian-ui/scripts/check-contract.mjs`.
  Change one, change all three, or change none.
* **The warning baseline.** A new warning signature must be adopted in the
  same change (`tools/warning_baseline.py --update --note "…"`), or the
  `make warnings` gate fails by design (OPERATOR.md, "What 'clean' means").
* **`generated/` is never edited.** Change authored input, validate,
  regenerate.
* **Boundary 17:** `system/CRITIQUE-POINTS.md` is append-only and its open
  points are not work items. If Part A turns out to be a settled judgement
  rather than a defect, that is Aram's call — append a point, do not act on
  one.

---

## 6. Acceptance criteria

```bash
# 1. The scope hole is closed (as a warning first, per Part A step 1).
#    Synthetic world: a stage naming a source the module map does not declare.
#    Before: validate exit 0, no warning.  After: the new warning fires.
#    Reproduce with: los-canvas/canvas/probes/probe_scope_gap.py

# 2. The CLI can no longer mint the app's provenance.
.venv/bin/python tools/seal_envelope.py --root . --capability garden.seed.create \
    --payload '{"text":"x"}' --key k --channel ui --out /tmp/e.json
#    expected: exit 2, "the 'ui' channel is the application's own provenance"

# 3. The app still can. (The UI's envelopes are built in-process; nothing to
#    run here, but `make test-paired` must stay green.)

# 4. The operator path is untouched.
.venv/bin/python tools/seal_envelope.py --root . --capability garden.seed.create \
    --payload '{"text":"x"}' --key k2 --channel operator --out /tmp/e2.json
#    expected: exit 0.

# 5. Everything else is green.
make check          # 0 errors
make warnings       # no new signature beyond the ones adopted in this change
make lint
make test           # the whole suite
make system-check   # the Core/UI release pair
```

Plus the two label fixes and the resolver fix, each with a test:

* `resume` prints the requirement id under the "Requirement" label; the
  value it prints is accepted by `learner.observation.append`.
* `note.create` refuses a body carrying frontmatter; the refusal names the
  cause; a body without one still writes.
* a `material://…#page=2` ref is either resolved identically by both
  resolvers, or refused by the write path — the world never ends in "write
  accepted, baseline gate broken".

---

## 7. Risks

| Risk | Why it is real | Mitigation |
|---|---|---|
| Part A lands as an error and bricks the repo | 2,792 route-less resources in the live corpus | land as a warning first; adopt the baseline in the same change; ratchet later, with Aram |
| Part B breaks the UI | the UI might use `seal_envelope.py` | verified: it does not — it builds envelopes in-process at `src/gateway-client.ts:465-480` |
| Part B breaks a script | a script may seal with `--channel ui` | grep the tree for `--channel ui` before changing; the `make system-check` paired gate covers the UI boundary |
| Part C is read as a domain change | it adds a boundary to OPERATOR.md | keep it to a stop-and-ask sentence in the same voice; no capability, schema or workflow changes |
| The fixes look like a refactor | the canvas review was wrong twice before | each part is independently shippable and independently testable; ship A, B and C separately |
| The scope rule is wrong | maybe a stage legitimately names material outside the module map (a reference-only pointer) | that case is what `scope_triage: reference-only` and `kind: reference` exist for — check the triage before requiring a route, and exempt `reference` rows if the design intends them to point outside the map |

---

## 8. What was NOT found (so the fixer does not chase it)

* **Double-writes are impossible.** Replay, `IDEMPOTENCY_CONFLICT`, no
  canonical byte moved, no second receipt. Verified.
* **Stale snapshots refuse** with exit 3 and both hashes; two writers give
  exactly one winner. Verified.
* **Fail-closed works.** One corrupt canonical file → 13 validation errors →
  every write and every read refused, naming the file. Verified.
* **The review queue cannot be spammed.** After a session that wrote a note,
  a relation, a garden seed, a question, a source, feedback, an observation
  and a stage note, the queue held 4 items — all unrouted inbox captures.
* **The clone's own suite is green.** The 5 failures seen in the isolated
  clone were `Cannot find package 'ajv'` — the isolated UI clone had no
  `node_modules`. After copying it in, those five files re-run
  **236 passed**. The system has no test-suite failures.
* **The UI *does* render a note's provenance bindings** (authorship, sources,
  `material_analysis`, evidence refs — `src/features/atlas/domains.ts:160-185`).
  A missing note-body view is a real gap (the projection carries 2.5 % of
  the corpus text), but it is a *reading* gap, not an auditing one.
