# C2 fix packages — the five `module-job-*` modules (item L2-17, 2026-10-24)

Prepared under Aram's authorization to act on critique point 1 by preparing
`--check` fix packages only. **Nothing was applied, nothing was pushed**: both
passing checks report `canonical_files_written: 0`, and the clone's git tree
carries only the new untracked workspace folder (no commits).

Scope discipline: only the defects `C2/_job-modules-evidence/CLAUDE-VERDICT.md`
and `L1-234-CLAUDE-VERDICT.md` confirm. Of L2-12's four findings, that is
**git F1 and polars F1** (confirmed by both verdicts). The other two are not
packaged, one for each possible reason:

- **engineering-tools F1 — REFUTED as a live defect** (details below). The
  verdicts confirmed a 404 measurement that is true of the URL they quote,
  but that URL is not the one the live row carries.
- **polars F2 (pandas user-guide heading renames) — not confirmed.** The
  job-modules verdict lists it explicitly under "Not checked"; content
  survives under the renamed headings. Re-pointing the four stale locators
  stays Aram's call.

## Where

Prepared in the C2 clone `~/los-glm-C2-2026-10/repository` (branch
`takeover/complete-and-install-2026-10-23` at `a2e2d49d`, clean, never
pushed), in `work/active/workspace-job-modules-l2-17-2026-10-24/`, and copied
here to `packages/`:

| file | what it is | `--check` result |
|---|---|---|
| `package-polars-f1-notebook-attribution.yaml` | polars F1, compact `module-plan-import` shape | **ok=true**, 0 writes |
| `package-git-f1-full-study-map.yaml` | git F1, full `unit-job-git-fluency` map for `unit-map-import --replace` | **ok=true**, 0 writes |
| `package-git-f1-progit-locator.yaml` | git F1, compact `module-plan-import` shape | refused (exit 1), see below |
| `check-polars-f1-notebook-attribution.json` | polars check output | |
| `check-git-f1-full-study-map.json` | git full-map check output | |
| `check-git-f1-progit-locator.err` | git compact refusal, verbatim | |
| `coverage-audit-l2-17.md` | the `plan_contract.coverage_audit` document | |

Package hashes (sha256, first 16 hex): polars compact `00e015e4391831ae`, git
full-map `8b9ccc2562e9948a`, git compact `1cf3708da573511e`. The polars check
also reports `package_sha256: sha256:57ce85482057733b4b9210f178900241cfa2ab9f79bc047c569625db63ae89b7`.

## The two confirmed fixes

Both packages were generated programmatically from the live maps with
assertions (old locator hits exactly one row, the target; exactly one row
differs from live and only in its `locator`; staged row ids equal live order);
build scripts and the full audit live beside the packages in the clone.

### git F1 — stage-git-15 ProGit row (confirmed by both verdicts)

- Row `resource-git-15-01-required-core-progit-2ed-pdf` in
  `curriculum/modules/module-job-git/units/unit-job-git-fluency/study-map.yaml`.
- Locator: "Pro Git worktrees and submodules Chs. 7.11, 7.13" →
  **"Pro Git submodules and replace Chs. 7.11, 7.13"**.
- Evidence re-verified in the clone on 2026-10-24 with the clone's pypdf
  against `ProGit_2ed.pdf` (501 pp.): the 7.11 heading "Submodules" is on
  p. 304, the 7.13 heading "Replace" is on p. 328, `[Ww]orktree` appears
  nowhere in chapter 7 (pp. 224–341) and only at pp. 453/457 in the whole PDF
  (env-var docs and trace output — no teaching content). The dropped
  "worktrees" half was the confirmed defect; the kept claims are the verified
  ones. The stage's worktree need stays carried by the untouched rows that
  hold it (git-scm `git-worktree` docs, MIT worktree pointer).
- Decision, recorded: the L2-12 report suggested "Pro Git submodules
  Ch. 7.11"; this package keeps the 7.13 mention as well, because 7.13 Replace
  is real, verified content the original locator pointed at, and the confirmed
  defect is only the worktree half. Locator phrasing matches the module's
  house style ("Pro Git searching and debugging", "Pro Git revision
  selection").

### polars F1 — stage-polars-01 notebook attribution (confirmed by both verdicts)

- Row `resource-polars-01-03-local-material-03-01-introducing-panda` in
  `curriculum/modules/module-job-polars/units/unit-job-polars-pandas-fluency/study-map.yaml`.
- Locator: "§'The Pandas Index Object' and §'Data Selection in Series'
  (notebook 03.01)" → **"§'The Pandas Index Object' (notebook 03.01)"**.
- Evidence re-verified from both notebooks' markdown headings in the clone on
  2026-10-24: "The Pandas Index Object" is a heading of
  `03.01-Introducing-Pandas-Objects.ipynb` (kept claim); "Data Selection in
  Series" is a heading of `03.02-Data-Indexing-and-Selection.ipynb` and of no
  03.01 cell (the misattribution).
- Decision, recorded: the report offered "split the row" or "re-mention
  (notebook 03.02)". The false half is dropped instead. The row's own `angle`
  is entirely about the index, so the kept locator covers its full declared
  purpose; 03.02's selection material stays carried where it belongs
  (`unit-job-polars-selection-backend`'s 03.02 row and the module source-map's
  03.02 route, untouched). Re-mentioning 03.02 here would leave the locator
  naming a notebook the row's `vault_path` does not carry — the exact
  locator↔named-material ambiguity C2 exists to catch; a split would add a
  fresh resource id and change the placement count, more than the confirmed
  defect requires.

### Check results, in full

- **polars** (`module-plan-import module-job-polars --file … --check`):
  `ok=true, mode=check, canonical_files_written=0`; one affected file
  (`…/unit-job-polars-pandas-fluency/study-map.yaml`); routes 29→29, sources
  6→6, placements 23→23, triage unchanged, `resource_learner_changes: []`,
  no route changes.
- **git, full map** (`unit-map-import unit-job-git-fluency --file … --replace
  --check --json`): `ok=true, mode=check, canonical_files_written=0`;
  `content_changes` is exactly one entry (stage-git-15, field `resources`);
  `relative_order_changed: false`; no stages added or retired; all 16 stages'
  learner state preserved; `map_changes: []`.

## Why the git compact package is refused, and what unblocks it

`module-plan-import module-job-git --file package-git-f1-progit-locator.yaml
--check` refuses with `module plan routing preflight failed`, because

- unit-job-git-fluency uses source-git-handbook-archive, but its source-map unit_routes omit the unit
- unit-job-git-fluency uses source-hu-git-intro, but its source-map unit_routes omit the unit
- unit-job-git-fluency uses source-progit, but its source-map unit_routes omit the unit

`plan_import.py::module_plan_routing_problems` reads the LIVE unit and map, so
no one-row patch can avoid the check: **a module whose three declared sources
all carry empty `unit_routes` cannot import any plan revision at all.** This
is the same unmigrated critique-point-1 routing debt the verdicts recorded as
the git module's 168 warnings — the preflight turns that debt into a hard
block the moment anyone tries to land a fix. Unblocking it means authoring
routes or dispositions for the three sources: new plan content that needs
Aram's critique-point-1 decision and that no verdict confirms, so this item
does not make it.

That is why git F1 ships as two artifacts: the compact package is the right
vehicle once routing lands, and the full-map package (checked clean, above)
is the applyable path today — heavier, because `--replace` is a replacement
transaction with Git as prior-version archive. The landing session should
prefer the compact one when the debt is resolved.

## engineering-tools F1 — refuted (no package)

The verdict's spot-check: "`https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse`
returns 404. `…/filesystems/fuse/index.html` returns 200." Both measurements
reproduce (re-fetched 2026-10-24). But **neither URL is the live row's URL.**
The live row `resource-missing-semester-18-07-optional-depth-www-kernel-org-fuse-htm`
carries `https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html`,
which:

- is in the clone's map at line 1599, byte-identical since the initial
  snapshot commit `1d32c918` (the module tree has no later commit), and
  identical in the live checkout and in L2-12's own `collected.json`;
- returned **HTTP 200** on 2026-10-24 (re-fetched twice), serving the page
  titled **"1. FUSE Overview — The Linux Kernel documentation"** — exactly
  the row's label ("FUSE overview") and locator ("FUSE project
  documentation").

The L2-12 report and verification log misquoted the live URL as `…/fuse/fuse`
(no `.html`); the verdict spot-checked that misquote; L1-234 confirmed the
verdict's measurement of it. Each step's measurement was accurate; the error
entered between collection (correct in `collected.json`) and reporting. The
suggested fix — re-pointing to `…/fuse/index.html` — would move a working row
away from the exact page its label names, onto the section TOC ("FUSE
Technical Documentation"), on the strength of a 404 that row never had. The
row is left byte-identical, and this refutation is the deliverable for it.

## Everything else, and why no package exists for it

- **polars F2** — not confirmed (verdict: "Not checked"); four stale
  locators to pandas-renamed headings, content survives. Aram's call.
- **The 695 `RESOURCE-SCOPE-UNBOUND` warnings** (eng-tools 183, polars 212,
  git 168, python 67, rust 65) — both verdicts classify them as unmigrated
  critique-point-1 debt, not damage, and neither names a confirmed binding
  defect nor a reviewed binding source to port (unlike AML's unapplied r2
  plan, which gave L2-15 its 17 bindings). Inventing ~550 route bindings with
  no reviewed source would author new plan content, not fix a confirmed
  defect. They stay recorded debt for Aram.
- **python-engineering and rust-engineering** — 0 defects in both verdicts;
  no packages.

## Assumptions

- kernel.org was fetched 2026-10-24 (three times within the hour: status of
  all three URL variants, then headers, then page titles — same results); it
  is a living document.
- The polars check's revision guard (`expected_revisions:
  {"unit-job-polars-pandas-fluency": 12}`) and the git full-map check's
  (`{"unit-job-git-fluency": 1, "study-map-job-git-fluency": 1}`) are
  snapshot-state facts of the clone at `a2e2d49d`; a landing session applying
  against a moved base re-runs `--check` first.
- The git routing refusal was not probed further (e.g. whether
  `source_joins` could mask it) — masking a routing preflight would defeat
  the check that refuses, which is not this item's call.
