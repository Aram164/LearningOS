# External evaluation evidence — LearningOS F-01 fixing pass

**Branch:** `evidence/los-canvas-2026-10-20` (this branch)
**Base:** `fix/scope-authority-f01` at `6265f473` — the fixing agent's
production commits are inherited unchanged; this branch adds **only**
evidence.
**Produced:** 2026-10-20 by an independent agent that did not write the
fixes.

This directory is the external testing harness the fixing commits cite
(`los-canvas/reports/t05`, `los-canvas/canvas/probes/probe_scope_gap.py`).
It is published so a reviewer can independently assess not only *what* was
changed, but *whether the harness tested the right failure cases, used
representative fixtures, and produced sufficient evidence*.

---

## 1. What is here

```
los-canvas/
├── EVIDENCE.md                  this file
├── SHA256SUMS                   integrity manifest for every file below
├── canvas/                      the harness (sources only)
│   ├── lib/canvaslib.py         synthetic-world builder + gateway driver
│   ├── lib/runner.py            the small report runner
│   ├── t01_entry_points.py      every OPERATOR.md "Start here" row
│   ├── t02_filing_journey.py    one complete filing session, costed
│   ├── t03_adversarial.py       21 probes that try to make the system misbehave
│   ├── t04_consumption_seam.py  what a UI-only consumer can see
│   ├── t05_masters_promotion.py workflow 27: can an agent promote a module?
│   ├── t06_term_boundary.py     workflow 24: what can the agent do at a boundary?
│   ├── t07_ui_consumes_canvas.py the UI consuming a canvas world, at runtime
│   ├── probes/                  the exploratory scripts behind each finding
│   ├── bootstrap.sh             rebuild the clones, the venv and node_modules
│   ├── run-all.sh               run all seven suites
│   └── README.md                how the harness works and what it asserts
├── reports/                     the BASELINE run (Core 1d32c918, UI 66ca47a)
│   ├── FINDINGS.md              F-01 … F-06, the correction, the costs, the limits
│   ├── FIX-BRIEF-F01.md         the brief the fixing agent worked from
│   ├── t01/ … t07/              per-suite JSON + Markdown
│   ├── capability-schemas/      every write capability's payload schema
│   ├── canvas-final-run.txt     the scoreboard of the baseline run
│   ├── clone-test-suite.txt     the Core clone's own pytest run (7,919 passed)
│   ├── clone-failures-rerun.txt the five files re-run after the ajv gap
│   └── ui-test-suite.txt        the UI's own npm test (12,750 response cases)
├── after-fix/                   the SAME harness re-run against fix/scope-authority-f01
│   ├── t01/ … t07/              per-suite JSON + Markdown
│   └── canvas-run.txt           the scoreboard of the after-fix run
└── fix-f01-2026-10-20/          the fixing agent's own workbench documents
    ├── FIXING-PLAN.md           its plan
    ├── OUTCOME.md               its outcome report
    └── (its probe and measurement scripts)
```

## 2. How to reproduce

```bash
git clone --branch evidence/los-canvas-2026-10-20 <LearningOS remote>
cd LearningOS/los-canvas/canvas
./bootstrap.sh          # clones Core + UI, builds the venv, copies node_modules
./run-all.sh            # 78 cases across seven suites; writes ../reports/
```

`bootstrap.sh` writes only inside the canvas directory. It reads the
operator's Core and UI checkouts as sources and never modifies them.

## 3. Environment the measurements were taken in

| | |
|---|---|
| Core (baseline) | `1d32c918` — "Initial clean LearningOS Core snapshot" |
| Core (fixed) | `6265f473` — `fix/scope-authority-f01` |
| UI | `66ca47a` |
| Python | 3.14.4 (macOS arm64) |
| Worlds | the system's own characterization fixture (`rich_world`), plus synthetic content the suites add — no operator data |
| Writes | every canonical write went through `seal_envelope.py` → `los capability`; the only direct file edits were in the fail-closed probes, where corrupting a file *is* the adversarial act |
| Isolation | every world lives under `worlds/`; the operator's checkout was cloned, never built in |

## 4. The harness's own result

| Suite | Cases | Baseline | After the fix |
|---|---|---|---|
| T01 operator entry points | 19 | pass | pass |
| T02 filing journey | 16 | pass | pass |
| T03 adversarial | 21 | pass | pass |
| T04 consumption seam | 5 | pass | pass |
| T05 workflow 27 | 6 | pass | pass |
| T06 workflow 24 | 7 | pass | pass |
| T07 UI runtime | 4 | pass | pass |
| **Total** | **78** | **78/78** | **78/78** |

Plus the system's own suites, in the clone:
* Core `pytest -q` — **7,919 passed**, 5 failed, 10 errors. Both non-green
  sets were environment gaps (no `node_modules` → `Cannot find package
  'ajv'`; and a globally-resolved TypeScript), and each was re-run green
  after the gap was closed (**236 passed**, **10 passed**). No system
  failure.
* UI `npm test` — green: 125 source modules, 0 dependency cycles, 122
  module tests, 38 live-app-check tests, 12,750 response-differential
  cases over 13 endpoints.

## 5. Before and after, case by case

Same harness, same fixtures, same payloads. Only the tree differs.

| Finding | Case | Baseline | After the fix |
|---|---|---|---|
| **F-01 A** — a stage's scope is unbound | T03 `e1b` rung E (agent adds a stage of its own devising) | seal 0, apply 0, **stage installed** | seal 0, apply 0, stage installed — **but** the new rule fires |
| | probe case B (adopted source, locator `§9` no route declares) | `0 error(s), 10 warning(s)` — **silent** | `W RESOURCE-SCOPE-UNBOUND: … teaches source-demo-book at '§9' — the module's source map declares no route for it` |
| | warning-baseline gate for that world | pass | **fail** — "2 new or grown warning signature(s). Fix them, or adopt them deliberately" |
| **F-01 B** — the CLI mints the app's provenance | T03 `g1`, `ui` + `direct-user-gesture` | apply 0, **stage installed** | **apply 2, refused** |
| | T03 `g1`, `operator` + `operator-approval` | apply 0, installed | apply 0, installed (the operator path is unchanged, by design) |
| **F-02** — `resume` names the requirement wrongly | T02 world, `los resume` | `Requirement  knowledge-demo-expectation` (the write path rejects it) | `Requirement  req-demo-l01-demo` (the id the write path wants) |
| **F-03** — a note body carrying its own frontmatter | T03 `f1` | write **exit 0**, 3 frontmatter blocks, published summary = the stray YAML | write **exit 2**, 0 blocks |
| **F-04** — two resolvers disagree on a fragment URI | T03 `f2` | write accepted, warning-baseline gate **exit 1** | write accepted, warning-baseline gate **exit 0** |
| **F-05** — the promotion's verification is asserted | T05 `w27-4` (promotion with an unresolvable `https://nonexistent.invalid/…`) | seal 0, apply 0, **`module_promoted: true`** | seal 0, **apply 2, `module_promoted: false`** |

## 6. What this evidence does and does not establish

**Establishes.** That the harness exists, that its cases are reproducible
from this branch, and that five of the six findings have changed behaviour
in the fixed tree in the direction the brief asked for. It also establishes
one thing the reviewer should know precisely:

> **F-01 A closes the scope hole at the *warning* level, not the error
> level.** The agent's stage still lands in canonical state; what changed is
> that the repository now says so — `RESOURCE-SCOPE-UNBOUND` — and
> OPERATOR.md boundary 13's acceptance gate (no new warning signature)
> therefore *refuses to accept the change* until the warning is fixed or
> deliberately adopted. The error flip is Aram's, after the corpus
> migration; the fixing commit says the same thing and measures the debt
> at 1,462 live rows.

**Does not establish.** That a human's scope judgement is now impossible
to improvise. T03 `e1b` rung E still installs a stage of the agent's own
devising; what changed is that the repository now *reports* it and the
acceptance gate objects. The residual gap is the one the brief named: the
`ui` channel is closed at the CLI (F-01 B), but the *operator* path remains
open by design, because in this arrangement the agent is the operator.

**Not covered.**
* `los check:live` — the UI's live-Obsidian check needs a running Obsidian
  app; the script's own comment records that the Obsidian CLI is disabled
  on this machine. The UI was exercised headlessly and statically only.
* The materials tree was not mounted, so material-level evidence binding
  was exercised against the fixture's 3-file tree, not the real 1,519.
* Workflows 24 and 27 were driven to the point where the fixture's missing
  preconditions (a real term boundary, a quarantined catalogue) had to be
  synthesised; those syntheses are the harness's own construction, not
  real data.

## 7. Provenance of every number above

| Claim | Where it comes from |
|---|---|
| every before/after cell | `reports/t0*/…json` (baseline) and `after-fix/t0*/…json` (fixed) — machine-readable, per case |
| the 78/78 scoreboards | `reports/canvas-final-run.txt`, `after-fix/canvas-run.txt` |
| the Core suite result | `reports/clone-test-suite.txt` |
| the ajv re-run | `reports/clone-failures-rerun.txt` |
| the UI suite result | `reports/ui-test-suite.txt` |
| F-01 A's residual | `canvas/probes/probe_scope_fixing.py`, run on both trees |
| the findings themselves | `reports/FINDINGS.md` |
| the fix the agent worked from | `reports/FIX-BRIEF-F01.md` |
| the fixing agent's own account | `fix-f01-2026-10-20/OUTCOME.md`, `FIXING-PLAN.md` |
