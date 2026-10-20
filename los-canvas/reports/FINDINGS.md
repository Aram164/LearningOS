# LearningOS Testing Canvas — Operator-Perspective Findings

**Date:** 2026-10-20
**Subject:** LearningOS Core v3.2.0 (`1d32c918`) + Obsidian UI (`66ca47a`)
**Method:** isolated clone, synthetic worlds, gateway-only writes, adversarial probes
**Canvas root:** `/private/var/folders/tx/dcz7b0nn2_n8kv3439vkggc80000gn/T/opencode/los-canvas/`

---

## 1. What was built, and why it cannot have touched the real tree

```
los-canvas/
├── LearningOS/repository/      isolated clone of the Core repo (+ its own .venv)
├── LearningOS/obsidian-ui/     isolated clone of the UI repo
├── canvas/                     the harness (4 suites + the exploratory probes)
├── worlds/                     every synthetic world the suite built
└── reports/                    machine + human reports for every run
```

* Both repositories were cloned from the working copies with `git clone` (local,
  hardlinked objects). The operator's tree was never written to; `git status`
  in `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository` is
  clean at `1d32c918` after the whole exercise.
* The clone's own `.venv` was built with `make setup` (Python 3.14.4, pytest,
  ruff, scrut). The clone validates with **0 errors** and 9 warnings, all of
  them the expected fresh-clone ones (5 local-only attachments absent, 1519
  uninventoried materials, 2 angle reviews unverified, views not yet built).
* The synthetic worlds are the system's own characterization fixture
  (`rich_world`, built by `tests/scenario_fixtures.py`): demo book, demo
  module, two units, two workspaces, inbox drops, a garden seed, paths,
  abilities, goals. **No operator data is in the canvas.**
* Every write in the canvas went through the sanctioned path
  (`seal_envelope.py` → `los capability`), never a direct file edit — with one
  deliberate exception in the fail-closed probes, where the adversarial act
  *is* corrupting a canonical file.

## 2. What was run

| Suite | Cases | Question it answers |
|---|---|---|
| **T01** entry points | 19 | Does every row of OPERATOR.md's "Start here" table work, and what does it cost? |
| **T02** filing journey | 16 | Can the librarian file material end to end, and what does one session cost? |
| **T03** adversarial | 21 | Can the system be made to write twice, write wrong, write out of scope, or write unattended? |
| **T04** consumption seam | 5 | What can a UI-only consumer actually see of the durable-note corpus? |
| **T05** workflow 27 | 6 | Can an agent promote a Master's module unattended, and on what evidence? |
| **T06** workflow 24 | 7 | What can an agent do at a term boundary, and what can it not? |
| **T07** UI runtime | 4 | Does the UI consume a canvas world, and what does it reach of a note? |
| **Total** | **78** | All 78 green — the suite asserts the system's *behaviour*, including its refusals. |

Plus the clone's own suite (`pytest -q`, 7,919 passed) and the UI's own suite
(`npm test`, 12,750 response-differential cases) for faithfulness — see §7.

---

## 3. Findings

### F-01 — HIGH. An agent can author the scope authority that workflow 23 says a human must supply

The previous review named this as the single biggest operational risk of
agent-as-librarian: *"an agent under task pressure will try to 'process a
lecture' and improvise the scope authority the system deliberately left
undefined — and here there is no gate that can refuse it."*

**The canvas measured it. The claim is correct.**

The probe walked the ladder from "no plan" to "an agent's own stage,
installed", each rung in its own fresh world:

| Rung | What the agent did | Result |
|---|---|---|
| A | hand-wrote a study map with no `plan_template_version` | **refused** — creation contract |
| B | used the canonical `los plan-template` output, placeholder left in place | **refused** — `source_plan.path is still the template placeholder` |
| C | v1-conforming map that *replaces* the existing one, retirement undeclared | **refused** — `this revision removes existing stages … declare each with --retire-stage` |
| D | same, with every retirement declared and a reason string | **refused** — `E REF-STAGE: resume pointer references an unknown stage` |
| E | **kept the map and added one stage of the agent's own devising** | **ACCEPTED** — seal 0, apply 0, stage installed, validation clean, receipt written |

Rung E is the minimal move and needs no retirement, no reason string, and no
human. The agent wrote its own `objective`, its own `done_when`, and a
resource locator into a book section that was never assigned (`§9`), and the
gateway installed it.

Every guard the system raised is **structural**: a template version, a named
plan, a declared retirement, one active stage, a live resume pointer. None is
a *provenance* gate. Nothing in the canonical record says who wrote the stage
— `study-map.yaml` has no authorship field, and the receipt records only the
**caller-declared** channel (`"channel": "operator"`), which the caller chose.

**The mechanism, measured.** The system *does* have a reviewed-UI gate for
plan revisions, and it works exactly as designed:

| channel | approval kind | apply | agent's stage installed |
|---|---|---|---|
| `codex` | `direct-user-gesture` | **2 — refused** | no |
| `ui` | `direct-user-gesture` | 0 | **yes** |
| `operator` | `operator-approval` | 0 | **yes** |

The codex-channel refusal is precise and actionable:

> `unit.map.import is authorized by a reviewed action in the LearningOS app,
> not by a codex-channel request: apply it from the screen that shows the
> exact change, **or send it through the approved operator path**`

That last clause is the whole finding. The system offers the *operator path*
as the alternative — and under agent-as-librarian the agent **is** the
operator, so the gate is satisfied without a human ever being present. Worse,
the CLI can declare `--channel ui` itself, so the "reviewed action in the app"
door is open to it as well.

The system's own source already states the limit, in
`tools/learning_os/app/admission.py`:

> *"The restriction to `channel == "ui"` is what keeps this from widening
> agent authority … **The channel label is provenance inside this trusted
> local application, not cryptographic proof that a human was present, and it
> is not treated as more than that.**"*

So this is not a bug in the system's own terms. It assumes the operator is a
trusted party; the arrangement makes the agent that party. What the system
does protect: the **shape** of the scope. What it cannot protect: **whose**
scope it is. The previous review's conclusion stands exactly — **the refusal
has to come from the agent having read the manual.**

**And the scope itself is unbound.** The sharpest form of the defect does
not need any impersonation at all. A source registered globally but never
adopted by the module's source map, placed on a stage with a locator no
route declares:

```
source registered: True
module-demo declares: ['source-demo-book']
probe source in module map: False
map import: 0
stage landed: True
VALIDATE exit: 0 | errors: []
```

The module's source map — the reviewed statement of what the module covers —
does not constrain what a stage may teach. `references.py:404-435` checks
that a resource's `source_id` is *registered* and that a `route_id`, *if
present*, exists; but `route_id` is optional in the resource schema, and a
route-less resource is never checked against the module's map. Even a
*dangling* `route_id` is not an error: `plan_rigor.py:362,464` return
silently when the route does not resolve. This is the defect to fix — the
approval matrix above is only the amplifier.

The fix brief is in `reports/FIX-BRIEF-F01.md`: it is written for another
agent to execute in the real tree.

### F-02 — LOW-MEDIUM. The resume screen names the requirement twice, and the label "Requirement" carries the value the write path rejects

`los resume --json` carries the requirement correctly:

```json
"requirement": { "id": "req-demo-l01-demo",
                 "concept": "knowledge-demo-expectation", … }
```

`los resume` (the text form OPERATOR.md's entry table names) prints the
**concept** under the label `Requirement`:

```
  Requirement  knowledge-demo-expectation
               capability: {"kind": "explain", "operands": ["expectation"]}
```

`learner.observation.append` requires the **requirement id**. Feeding the
value from the "Requirement" line produces:

```
seal_envelope: unknown requirement: knowledge-demo-expectation; fix the payload and seal again
```

**What I first wrote here was wrong, and the correction matters:** the id
*is* on the same screen, eight lines down, under a different label —

```
  Next         los observe req-demo-l01-demo --activity <what-you-did> --result <correct|incorrect|partial|abandoned>
```

So this is not a dead end; the value is reachable and the resume screen even
prints the command that uses it. The defect is narrower: **one screen names
the same object twice under two labels, and the label that says "Requirement"
holds the value the write path refuses** — and the refusal does not name the
id it wants. Source: `resume.py:775` prints `requirement.get("concept", "")`
where `requirement["id"]` was available.

Fix: print the id under the "Requirement" label (or print both). One line.

### F-03 — MEDIUM-LOW. A note body that carries its own frontmatter silently corrupts the published summary

`note.create` takes a `body_file` and prepends its own canonical frontmatter.
Nothing stops the body from carrying one too. The result is a file with two
frontmatter blocks, which validates cleanly (0 errors) and publishes the
**stray YAML block as the note's summary**:

```
SUMMARY: 'id: note-f1-duplicate type: note title: "Body with its own frontmatter"'
```

The real prose sits one heading further down, and the UI would show the YAML
as the note's abstract. The body-file contract never says "body only".

### F-04 — LOW. Two resolvers disagree on a `material://…#fragment` reference

| Stage | `material://source-demo-book/lecture-01.pdf#page=2` |
|---|---|
| write (`note.evidence.add`) | **accepted** (exit 0) |
| validate | **warns** `URI-MATERIAL: … does not resolve on disk` |
| warning-baseline gate | **fails** — `NEW URI-MATERIAL … 0 → 1` |

The seal-time materials check strips the fragment; the general validator
(`parse_reference_uri`) does not. So a write the system accepts can break the
acceptance gate that OPERATOR.md rule 13 makes mandatory. Note that no
canonical record uses a fragment today, so this is a latent edge rather than
a live defect.

### F-05 — HIGH (new, from T05). Workflow 27's "official-academic" verification is asserted, never checked

The canvas built the precondition workflow 27 declares missing — a
prospective catalog, a comparison, a promotion package — and then walked the
path as the agent.

**The path is heavily gated.** Every one of these refusals was real and
specific:

```
catalog revision must be 0; got 1
candidate-source-probe-book is selected and must be deep-reviewed
source_assessments/0: 'contribution' is a required property
source_assessments/0/evidence: [] should be non-empty
candidate comparison was prepared against a stale catalog
candidate-module-probe-masters must be selected before promotion
candidate-module-probe-masters must be verified-current
a promoted prospective module must enter canonical state as planned
promoted planned unit unit-probe-masters-01 may not enter an active/completed state
plan_contract.coverage_audit is not a safe repository file
coverage audit lacks required section marker: ## Linked
recorded_at cannot be in the future
verification.evidence[0].verified_on is stale (49 days old; maximum is 30)
live promotion requires the exact package_sha256 returned by --check
promotion expected revisions must match the complete checked bundle
W NEW-OR-GROWN-WARNING: LOCATOR-VAGUE … 0 → 1 (introduced by this plan)
```

**And then it landed.** With those satisfied, the agent promoted a Master's
module into the live curriculum:

```
check_exit: 0   package_sha256: sha256:5560c224…
seal_exit: 0    apply_exit: 0    module_promoted: true
```

The verification evidence it rested on was:

```json
{"authority": "official-academic",
 "url": "https://nonexistent.invalid/probe/module-catalog",
 "claim": "The module is offered by the programme.",
 "verified_on": "2026-10-20"}
```

**That URL cannot resolve, and nothing fetched it.** The verification is a
*shape* check — `^https://`, a date ordering, and a 30-day freshness
window — plus the catalog's own `fact_state.status: verified-current`, whose
`evidence` is a list of free strings. The agent asserted both.

The honest part: the quarantine keeps the promotion's provenance record
verbatim, so the URL survives into `curriculum/quarantine/masters-planning/
promotions/<id>.yaml` and an auditor can check it. The record is not
falsified; it is simply *unverified*, and nothing at write time says so.

**The fix is small and does not touch a domain rule:** make the promotion
verify the evidence URL it accepts — either by fetching it, or by refusing
a promotion whose evidence has not been verified by a named party. The
`los validate --online` URL audit already exists; the promotion path could
require its verdict.

### F-06 — POSITIVE (new, from T06). Workflow 24's human steps are enforced by *absence of capability*

The previous review worried that an agent would sweep the Garden at a term
boundary. It cannot — and the reason is stronger than a refusal.

**What the agent can do at a boundary** (all measured, all through the
gateway):

| Step | Result |
|---|---|
| record the attempt | ✅ `module.attempt.record` → `result: passed` |
| close the module | ✅ `module.plan.import` → status `enrolled` → `completed`, via the reviewed-plan path with the plan contract and a coverage audit carrying its required `## Local` / `## Linked` / `## Completeness` markers |
| commit and push | ✅ `session-end --commit-message --push` → `committed: true`, `pushed: true`, `session_closed: true`, validation clean — and the commit reached the bare remote |

**What the agent cannot do, at all:**

| Step | Why |
|---|---|
| retire a workspace | **no capability exists.** The only workspace capability is `workspace.next-action.update`, which moves text. |
| dispose of a garden seed | **no capability exists.** `garden.seed.create` only creates; there is no resolve, shelve or discard. |

So the Garden judgment and the workspace lifecycle are *outside the agent's
reach by construction* — not gated, not refused, simply absent from the
capability surface. That is the strongest form this system has of the
"human-only" steps, and it is exactly what workflow 24 needs.

**The contrast with workflow 23 is the finding.** Where a human's judgement
is expressed as a *record* (a plan file, a catalog, a promotion package),
the agent can author the record and the system accepts it. Where it is
expressed as an *act on a file* (move the seed, archive the workspace),
there is no capability, and the agent is stopped by the absence of a door.

### F-05 — INFORMATIONAL. The CLI has no `warnings` command

`los` exposes `validate` and `generate` but not the warning-baseline gate,
which OPERATOR.md rule 13 names as a raw tool invocation
(`.venv/bin/python tools/warning_baseline.py --check`). Not a defect — the
contract names the exact command — but the machine surface is one command
short of the acceptance rule.

### CORRECTION to the previous review — the UI *does* expose the bindings

The previous review said: *"If a note's provenance binding is wrong, you
would only learn it from the agent, not from the interface you actually
use."* **That is wrong about the bindings.** The Obsidian UI's Atlas surface
renders, for every note: authorship, lifecycle, semantic-review state,
recorded sources (linked), the `material_analysis` provenance (material,
observed range, analysis resolution, analysis source) and every recorded
evidence ref (`src/features/atlas/domains.ts:160-185`).

What the UI cannot show is the note's **body**. Measured on the real corpus
(145 notes, 1,421,939 characters of body text):

| | |
|---|---|
| Body characters in the corpus | 1,421,939 |
| Summary characters in the projection | 35,144 |
| **Share of corpus text the UI can show** | **2.5 %** (median note: 3.2 %) |

**Measured at runtime (T07).** The UI's own "real projection" pass —
`tests/test-library-finder.js`, which reads `../repository/generated/
manifest.json` — was pointed at a canvas world's projection instead. It
consumed it:

```
library-finder: core projection OK — 1 sources, all reachable across 8 folders
```

(the real checkout's projection was restored afterwards). And a sentinel
sentence placed past the note's first paragraph is **absent** from the
projection while its summary is present — so the seam is confirmed at
runtime, not only by reading the source. The UI's own suite passes in the
clone: 125 source modules, 0 dependency cycles, 122 module tests, 38
live-app-check tests, 12,750 response-differential cases over 13 endpoints.

And the UI never names a note-reading command. Its whole read surface is 7
CLI verbs — `ability-context`, `health-report`, `legacy-archive-status`,
`masters-planning-dashboard`, `material-span`, `operations`, `plan-template`
— plus the projection, plus 17 write capabilities. `note-read` and
`note.search` are absent from all 125 of its TypeScript source files. The seam is therefore
**narrower and sharper than claimed**: it is a *reading* seam (97.5 % of the
librarian's reasoning is invisible from the app), not an *auditing* seam
(the bindings are auditable from the app). The one thing the UI does not do
is *resolve* an evidence ref against the corpus — it shows the ref string.

---

## 4. What held up — measured, not assumed

Every one of these is an executed probe, not an inspection.

**Double-writes are impossible.** Resubmitting the same sealed envelope
replays the receipt (`"replayed": true`), the canonical fingerprint is
unchanged, and no second receipt appears. Re-sealing under a used key is
refused at apply time with `IDEMPOTENCY_CONFLICT`. `--replay-only` verifies a
committed receipt without re-running the handler.

**Concurrency is honest.** A write sealed against a stale snapshot is refused
with exit 3, `STALE_SNAPSHOT`, and both hashes. Two writers against one
snapshot produce exactly one success (0) and one conflict (3). In every
refusal the canonical fingerprint was byte-identical before and after.

**Authority is enforced.** A bare write command refuses by design. A write
naming a stage that does not exist refuses. Shelving refuses an empty
selection and a bogus selection with the same message. `note.revise` without
approval refuses.

**Fail-closed is real.** Corrupting one canonical unit file produced 13
validation errors; every subsequent canonical write was refused, and the
refusal named the file and the schema errors. The reads refused too, rather
than silently omitting the broken record.

**Refusals are specific.** Across the whole exercise the system never once
answered "no". Every refusal named a site and a reason, and the reasons were
*specific* rather than generic:

```
role 'reference' keeps its dedicated capability; use note.analysis.save
source-canvas-synthetic: 'type' must be one of ['book', 'conversation', …]
source-canvas-synthetic: create needs 'discovery' provenance
unknown requirement: knowledge-demo-expectation
every selected ID must exist in the current proposal
E REF-STAGE: resume pointer references an unknown stage [curriculum/resume.yaml]
E SCHEMA: unit: 'artifacts' is a required property (at root) […/unit.yaml]
```

**The write path pre-validates by construction.** The seal-time dry run
catches invalid content before it can land — which is why F-04 (a *warning*-
level disagreement) was the only way to make the world and the gate disagree.

**The review queue cannot be spammed.** After the filing journey wrote a
note, a relation, a garden seed, a question, a source, feedback, an
observation and a stage note, the review queue held **4 items — all of them
unrouted inbox captures**, each naming its path. Nothing the system produced
on its own entered the queue. The membership rule is real.

**Reads are bounded.** `note-read --limit 100000` is refused
(`limit between 1 and 16000`); the default read returns at most 16,000
characters and reports `total_characters` so the caller knows what is left.

---

## 5. What the operator loop costs — measured

Read costs (approximate tokens, bytes ÷ 4):

| Entry read | Tokens |
|---|---|
| `status` | 144 |
| `related NOTE` | 75 |
| `program-list` | 74 |
| `inspect WORKSPACE` | 109 |
| `inbox-list` | 113 |
| `note-read NOTE` | 303 |
| `ability-context` (horizon) | 303 |
| `resume` | 283 |
| `material-context` | 358 |
| `plan-edit-context --route-id` | 360 |
| `plan-edit-context --stage-id` | 410 |
| `material-span` | 393 |
| `intelligence-scan --brief` | 493 |
| `capabilities --compact --json` | 534 |
| `bootstrap --brief` | 932 |
| `plan-edit-context --brief` | 1,154 |
| `semantic --list` | 1,337 |
| **`bootstrap` (no `--brief`)** | **10,898** |

The contract's context-discipline claim holds in practice: a routine lookup
costs 75–500 tokens. The one trap is the one the contract warns about —
`bootstrap` without `--brief` is **11.7×** the brief form.

One complete filing session (capture → read → note → evidence → relation →
garden → question → source → feedback → observation → stage note → shelving →
session end) cost:

| | |
|---|---|
| Steps | 14 |
| Writes | 11 |
| Reads | 3 |
| Write tokens (seal + apply) | 2,775 |
| Read tokens | 621 |
| **Total** | **3,396** |

So "the governance cost is paid in tokens and steps" is measurable and
bounded: **roughly 3.4 k tokens and 14 steps per filing session** — under
half of one unbounded `bootstrap`.

---

## 6. Limitations — what this does not establish

* The canvas ran against **synthetic worlds**, not Aram's live curriculum. The
  live tree was never opened by the harness.
* The materials tree was not mounted, so material-level evidence binding was
  exercised against the fixture's 3-file tree, not the real 1,519-file one.
* F-01 was demonstrated on one unit of the fixture. Whether an agent would
  *actually* take that path under real task pressure is a behavioural
  question this canvas cannot answer.
* The `masters-planning` (workflow 27) and "turn the semester" (workflow 24)
  surfaces were mapped but not driven end to end: the fixture has no
  quarantined catalogue and no remote, which is exactly why the contract
  declares those workflows untranscribable.
* Token counts are bytes ÷ 4 — a proxy, not a tokenizer.
* The UI was analysed **statically** (its client's reachable surface and the
  surfaces it renders). The Obsidian app was not launched against a canvas
  world; the UI's own test suite was not run.

## 7. Clone faithfulness

The clone validates at **0 errors / 9 warnings** (8 after `make views`) with
no new warning-baseline signature, and `tools/generate.py` rebuilds all 36
projections from scratch. `los capabilities --compact --json` is byte-identical
between the clone and the operator's checkout.

`pytest -q` in the clone produced **5 failures**, all of them in the Core↔UI
contract-mirror area (`test_contract_differential`, `test_contract_bundle`,
`test_contract_register`, `test_ops_pipeline`, `test_plan_rigor`). After
copying the UI's `node_modules` into the clone, those five files re-run
**236 passed, 0 failed** (`reports/clone-failures-rerun.txt`). The cause
was an artifact of isolation, not a defect:

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'ajv' imported from
  …/obsidian-ui/scripts/ajv-options.mjs
```

Those tests shell out to **Node + Ajv** against the *sibling UI checkout* to
prove that Core's schema and the UI's Ajv validator agree on the same seeds.
`node_modules` is gitignored, so the isolated UI clone had none. Copying the
original's 35 MB `node_modules` into the clone (read-only on the source) and
re-running exactly those files is the check — see
`reports/clone-failures-rerun.txt`.

**Verdict: the clone is faithful. The system has no test-suite failures.**
Every non-green result was re-run green after the missing dependency was
supplied:

| Suite result | Cause | Re-run |
|---|---|---|
| 5 failed | `Cannot find package 'ajv'` — the isolated UI clone had no `node_modules` | **236 passed** (the five files) |
| 10 errors | `Cannot find module '/opt/homebrew/lib/node_modules/typescript/lib/typescript.js'` — the UI gate harness resolves TypeScript globally | **10 passed** (`test_operations_gate.py`) |

Full clone run: **7,919 passed, 5 failed, 10 errors, 5 skipped, 2 xfailed**
in 51:47. With both environment gaps closed, the green count is the whole
suite.

The UI's own suite is likewise green in the clone (`npm test`): 125 source
modules with 0 dependency cycles, 122 module tests, 38 live-app-check
tests, and 12,750 response-differential cases across 13 endpoints.

The lesson for the canvas, recorded in `canvas/README.md`: an isolated clone
of the UI needs `node_modules` copied in, or the paired contract tests fail
for a reason that has nothing to do with the system.

---

## 8. Recommendation

F-01 is the one finding that changes what should happen. The two cheap
changes the previous review proposed remain right; this canvas adds a third
and revises one:

1. **Close the `ui` channel at the CLI, and route plan revisions through the
   app.** The system already has the right shape — a plan revision wants a
   `direct-user-gesture` from the `ui` channel, and the codex channel is
   refused. Two small changes make that shape bite:
   * `seal_envelope.py` refuses `--channel ui`. The CLI is not the app; only
     the app's own client should be able to claim a user gesture. (Today an
     agent can mint the app's provenance with one flag.)
   * `unit.map.import` and `module.plan.import` are admitted **only** from
     the reviewed-UI path, so a plan revision is a deliberate Save in the app
     rather than an operator request — and the refusal message that already
     exists stops offering the operator path as an alternative.

   This touches no domain rule and no data shape; it moves one admission
   decision and one flag.
2. **Give the human a read path to the durable notes** (`note.content`,
   `note.search` as UI views) — the previous review's proposal, now with a
   measured size: the UI would need to surface the 97.5 % of corpus text it
   currently cannot show. The bindings are already there; only the body is
   missing.
3. **Make workflows 23, 24 and 27 a hard stop for agents** — the previous
   review's proposal, now with a measurement attached: the *structural* gates
   (rungs A–D) all fired correctly and would catch a clumsy improvisation, but
   rung E walked straight through them. A stop-and-ask rule is the only
   thing that catches rung E.
4. **Revised, not new:** the previous review's worry that provenance bindings
   are unauditable from the UI is **not** the case — they are rendered. The
   real gap is that the UI shows an evidence ref without resolving it, and
   shows no body at all. A `note.content` view closes both.
