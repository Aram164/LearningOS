# ADR-003 — External architecture review (2026-08-03)

**Status:** accepted — fixes applied 2026-08-03 (same day), Aram's approval:
"fix everything first." Implementation log at the bottom; push deliberately
held for Aram's review. · **Context:** Aram requested a software-architect
review of the whole system (safety, redundancy, separation, robustness,
workflow) plus a connector/plugin assessment and a formalized Job↔LearningOS
workflow. Evidence gathered 2026-08-03; `python tools/validate.py` passed
clean (0 errors, 0 warnings) at review time. Findings are ranked by severity;
each names its fix. Nothing here was applied without approval except the
explicitly commanded `Job/WORKFLOW.md`.

## Verdict in one paragraph

The core design is sound and unusually disciplined: single-owner facts
(`modules.yaml`, `COORDINATION.md`), a hard canonical/generated split,
schema validation with a pre-commit gate, plain-text longevity, and an
operator contract that survives operator loss. The failures found are not
design failures — they are **operational**: the safety guarantees all hang
off "a commit happens," and commits stopped happening two weeks ago. The
second theme is **residual duplication** across the legacy freeze and the
Job boundary — the exact drift disease v3 was built to kill, surviving in
the seams between the three trees.

## Findings

### S1 — Two weeks of canonical state exist on one disk only (CRITICAL)

Last repository commit: 2026-07-18 (pushed). Since then, uncommitted:
~1,255 changed lines across 10 files **including `records/modules.yaml` and
`work/COORDINATION.md`** (the two single-truth files), plus 4 untracked
items **including the entire `workspace-thesis-mle-medical/`** and three new
programming notes. The pre-commit validator, the post-commit view rebuild,
and the GitHub remote all protect only work that gets committed — right now
they protect nothing. A disk failure today loses the thesis workspace, the
2026-07-25 priority overhaul, and the modules re-verification.

**Fix:** commit + push now (validator already passes). Then adopt a
session-end ritual as a written workflow (proposed §15 below): `make check`
→ commit → push, every session that touched canonical files. Optionally a
weekly scheduled reminder.

### S2 — Generated views are stale and predate the current plan (HIGH)

`generated/coordination-view.md` says *Generated: 2026-07-18* — it does not
know the thesis workspace exists and still shows pre-Jul-25 priorities. The
README's human-fallback path ("what should I do next? → open
coordination-view.md") would today hand a human a two-week-old plan. The
operator rule (rebuild before answering) covers Claude, but the staleness
guard for humans is a timestamp they must notice. Root cause is S1: the
post-commit rebuild hook never fired because nothing was committed.

**Fix:** falls out of S1's ritual. Cheap hardening: have `generate.py`
print/embed a warning when any canonical input's mtime is newer than the
view (a one-function change to the generated-header logic).

### S3 — The frozen legacy tree is not frozen (HIGH)

Root repo `git status`: `legacy/Plans/Programming/python/Python-Intermediate-Roadmap.md`
and `legacy/Plans/Programming/rust/Rust-Learning-Plan.md` have 54 inserted
lines *after* the freeze, and `legacy/Plans/crosscutting/` is untracked-new.
Cause: live entry points still route into the frozen tree — the assistant's
own memory index cites `Plans/Programming/python/…` as the roadmap's home,
while the canonical successor `note-python-intermediate-roadmap.md` exists
in `knowledge/notes/programming/`. This is dual maintenance: the drift
disease, reborn.

**Fix:** (a) diff the legacy deltas into the canonical notes, then reset the
legacy files; (b) update every live pointer (assistant memories, any doc)
to the canonical note paths; (c) enforce the freeze mechanically — a root
repo check that fails when `legacy/` has modifications (or `chmod -R a-w legacy/`).

### S4 — The redirect layer is itself unmanaged (MEDIUM)

`HANDOFF.md` and `SEMESTER-STATUS.md` — the only thing the Cowork project
instructions point at — are **untracked** in the root repo, and the root
repo is 4 commits ahead of its remote, unpushed. The entry chain into the
whole system lives outside version control. The stubs themselves say they
should be deleted once project instructions point at `LearningOS/repository/`
directly — that update has been pending since 2026-07-17.

**Fix:** update the Cowork project instructions (replacement text at the
bottom of this ADR), delete both stubs, push the root repo. Decide the root
repo's remaining purpose: it now only tracks `legacy/` + README — arguably
it should be archived read-only once S3 is enforced.

### S5 — Zombie CI on the legacy repo; no CI on the live repo (MEDIUM)

`.github/workflows/weekly-hygiene.yml` (root repo) still link-checks the
frozen tree weekly against pre-v3 tooling (`TOOLING.md`, `check_system.py`)
— spending CI on dead docs. Meanwhile the live repository has **no** CI:
the validator only ever runs on Aram's machine.

**Fix:** retire the legacy workflow; add a minimal workflow to the
LearningOS repo that runs `pip install -r requirements-dev.txt && python
tools/validate.py` (and optionally `--online` weekly for URL rot, which the
sources registry already models).

### S6 — Job-boundary duplication and one registry leak (MEDIUM)

Three copies of the same learning plans coexist: legacy files (being edited,
see S3), snapshots in `Job/workspace-job-deem/inputs/` (Rust plan, OOP
repair plan, Toolbox bootcamp, Python level-up), and new canonical notes.
Also one boundary inconsistency: `concept-skrub` is registered in the canon
but all its notes are quarantined in `Job/` — the health report lists it as
"concept without notes," which is technically a job-knowledge trace inside
the registries.

**Fix:** `Job/WORKFLOW.md` (written, this review) makes the canonical home
unambiguous and demotes Job-side copies to labeled frozen snapshots or
pointers. For `concept-skrub`: either delete from the canon or keep with a
disambiguation line "notes quarantined in Job/" — decision Aram's; keeping
it with the marker is the least destructive.

### S7 — Authoritative doc drift (LOW, but on-principle)

`ARCHITECTURE.md` §3.1 still shows `legacy/` under `LearningOS/` (it lives
at the semestercontext root) and stratum under `projects/` (moved to `Job/`
2026-07-17). `README.md`'s materials line predates the same move. Harmless
today, but this file calls itself "the single authoritative architecture."

**Fix:** two-line correction to §3.1 + a pointer that the Job quarantine
(CLAUDE.md §13) supersedes the stratum placement note. Needs approval
(architecture doc).

### What is NOT wrong (checked and passed)

Validation clean; inbox empty; workspace count 6/8; no secrets or
credentials found in the tree; `.gitignore` layering correct (generated/,
venvs, heavy binaries); CLAUDE.md symlink chain intact (root and
`LearningOS/` both resolve to `system/CLAUDE.md`); repository pushed
through 2026-07-18; hooks present in `tools/hooks/`; Garden/inbox
separation clean; archived workspaces intact. The separation of concerns —
knowledge / records / work / sources / generated — is genuinely good and
should not be restructured.

## Connector & plugin assessment (2026-08-03)

Connected today: **Gmail**, **Google Calendar** — both useful (deadline
mail, exam-date events). Installed plugins: productivity, design,
cowork-plugin-management, anthropic-skills (incl. the custom
`lecture-unit-builder`). The design plugin and the nine unauthenticated
work-tool servers (Figma, Notion, Slack, Asana, Jira, …) serve nothing in
this system — leave unauthenticated or uninstall to cut noise. Notion/Roam
class tools were considered and **rejected on principle**: the system is
deliberately plain-file and local.

Worth adding (all serve the thesis workstream, the system's next primary
effort per Phase D):

1. **alphaXiv** — full-text arXiv search + agentic paper retrieval; directly
   serves the MLE-agents landscape survey. Highest value.
2. **Elicit** — structured paper search/report generation for the
   related-work sweep.
3. **bioRxiv/medRxiv** — the medical-preprint side of "MLE agents for
   medical use cases."
4. *(optional)* **Scite** — citation-grounded evidence checks when writing.
5. *(optional)* **Google Drive** — off-site copy of the ~10 GB
   `LearningOS/materials/` tree, which git deliberately excludes; skip if
   Time Machine/cloud backup already covers it — verify that it does.

Non-connector wins available now: a **scheduled task** guarding the
non-negotiable 2.-PZ Anmeldung window (2026-08-31 → 09-10, AML + M2) and a
weekly commit/push/`make views` hygiene reminder.

## Proposed changes requiring approval

1. **CLAUDE.md §13 addendum** (one sentence): *"The boundary workflow —
   reference, capture, and promotion across Job↔LearningOS — is formalized
   in `Job/WORKFLOW.md`; it operates within this quarantine, never against
   it."*
2. **New WORKFLOWS.md §15 — Session end:** *"Any session that touched
   canonical files ends with: `make check` → commit (message names the
   session's effort) → push. Views rebuild via the post-commit hook. A
   session is not closed while canonical changes sit uncommitted."*
3. **ARCHITECTURE.md §3.1 correction** per S7.
4. **Root repo disposition** per S3/S4: enforce freeze, delete stubs after
   project-instruction update, push, then archive.
5. **`concept-skrub` disposition** per S6.

## Implementation log (2026-08-03)

- **Root cause of S1 found during the fix:** stale `.git/index.lock` files
  (crashed git processes, Jul 18 root / Jul 19 repository) were silently
  blocking **all commits in both repos** — plus the root repo's pre-commit
  hook still invoked the deleted pre-v3 `check_system.py`, failing every
  root commit. So S1 was not lapsed discipline but *quiet mechanical
  failure*. Both locks removed; root hook replaced by a legacy-freeze guard
  (blocks commits touching `legacy/` unless `ALLOW_LEGACY=1`).
- **S3:** the 54 lines of post-freeze legacy edits were verified
  byte-duplicated elsewhere before reset (Python deltas already in
  `note-python-intermediate-roadmap.md`; Rust Job-track already in the Job
  copy, `diff -q` identical) — legacy reset lossless. The untracked
  `crosscutting/seminar/` tree (8 files, grade-pending module) was
  *preserved* by committing it into legacy. The **enforced** freeze is the
  root pre-commit hook (verified working: blocks any commit touching
  `legacy/` without `ALLOW_LEGACY=1`). A filesystem-level `chmod -R a-w
  legacy/` was attempted but is unverifiable through the Cowork sandbox
  mount (it normalizes modes) — Aram should run it once in his own terminal
  for the belt-and-suspenders lock.
- **S6:** `concept-skrub` kept, `description:` boundary-marker added.
  `Job/WORKFLOW.md` + `inputs/README.md` snapshot markers written; verified
  exception recorded: the Rust plan's live home is the Job copy (no
  canonical counterpart; carries the Stratum Job track).
- **S7:** ARCHITECTURE §3.1 corrected (dated correction block). CLAUDE.md
  §13 addendum applied. Session-end workflow landed as **WORKFLOWS.md §22**
  (this ADR's draft said "§15" — the file already had 21 sections).
- **S5:** root `weekly-hygiene.yml` retired; validator CI added to the
  LearningOS repository (`.github/workflows/validate.yml`).
- **S2/S1:** views rebuilt, validator clean, both repos committed.
  **Push pending Aram.** Project-instructions update + stub deletion also
  pending Aram (text below).

## Replacement project-instructions text (paste into Cowork project settings)

> Start at `LearningOS/repository/`: read `README.md`, then `CLAUDE.md`
> (the operating contract), then `work/COORDINATION.md` +
> `records/modules.yaml`. You are the operator for my semester.
> `Job/` is quarantined (CLAUDE.md §13); its boundary workflow is
> `Job/WORKFLOW.md`.
