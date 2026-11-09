# Coverage audit — module-job-git / module-job-polars fix packages (L2-17, 2026-10-24)

Prepared in the C2 clone (`~/los-glm-C2-2026-10/repository`, branch
`takeover/complete-and-install-2026-10-23` at `a2e2d49d`) under Aram's
authorization to act on critique point 1 by preparing `module-plan-import
--check` packages only — nothing here is applied. Evidence base:
`C2/module-job-git/REPORT.md`, `C2/module-job-polars/REPORT.md`,
`C2/module-job-engineering-tools/REPORT.md` (L2-12) as confirmed by
`C2/_job-modules-evidence/CLAUDE-VERDICT.md` and `L1-234-CLAUDE-VERDICT.md`.

## Local

Scope of the packages — one study-map row per module, nothing else:

- `package-git-f1-progit-locator.yaml` (compact `module-plan-import` shape)
  — full resources array (11 rows) of
  `stage-git-15-worktrees-parallel-tickets-and-advanced-repository-lay` in
  `curriculum/modules/module-job-git/units/unit-job-git-fluency/study-map.yaml`.
  Only row `resource-git-15-01-required-core-progit-2ed-pdf` changes, its
  `locator`: "Pro Git worktrees and submodules Chs. 7.11, 7.13" →
  "Pro Git submodules and replace Chs. 7.11, 7.13". The dropped "worktrees"
  half is the confirmed defect: the 501-page `ProGit_2ed.pdf` carries no
  worktree teaching content (whole-PDF mentions: pp. 453 and 457, both
  incidental env-var/trace output; chapter 7, pp. 224–341, has none —
  re-verified in this clone on 2026-10-24 with the clone's pypdf). The kept
  section claims are verified: the 7.11 heading "Submodules" is on p. 304 and
  the 7.13 heading "Replace" is on p. 328. The stage's worktree need stays
  carried by the rows that do hold it: `resource-git-15-02` (git-scm
  `git-worktree` docs) and `resource-git-15-05` (MIT advanced Git worktree
  pointer), untouched. Locator phrasing follows the module's house style
  ("Pro Git searching and debugging", "Pro Git revision selection").
- `package-polars-f1-notebook-attribution.yaml` — full resources array
  (14 rows) of `stage-polars-01-two-data-models-and-the-eight-divergence-axes`
  in `curriculum/modules/module-job-polars/units/unit-job-polars-pandas-fluency/study-map.yaml`.
  Only row `resource-polars-01-03-local-material-03-01-introducing-panda`
  changes, its `locator`: "§'The Pandas Index Object' and §'Data Selection in
  Series' (notebook 03.01)" → "§'The Pandas Index Object' (notebook 03.01)".
  The dropped half is the confirmed misattribution: "Data Selection in Series"
  is a heading of `03.02-Data-Indexing-and-Selection.ipynb`, not of 03.01
  (re-verified from both notebooks' markdown headings in this clone on
  2026-10-24; 03.01's full heading list carries no selection section). The
  kept half is verified: "The Pandas Index Object" is a 03.01 heading, and the
  row's own angle is entirely about the index, so the kept locator covers the
  row's full declared purpose. The dropped section's material stays carried by
  `unit-job-polars-selection-backend`'s 03.02 row and the module source-map's
  03.02 route, untouched. Re-mentioning "(notebook 03.02) for selection" in
  this row was rejected: it would leave the locator naming a notebook the
  row's `vault_path` does not carry, the exact locator↔named-material
  ambiguity C2 exists to catch. Splitting the row was rejected as a structural
  change (new resource id, changed placement count) beyond the confirmed
  defect.

Both compact packages were generated programmatically from the live maps with
assertions: the old locator hits exactly one row (the target), exactly one row
differs from live and only in its `locator`, and the staged row id order
equals the live order. Build script: `build_packages.py` beside this audit.

**Git compact package is hard-blocked by the module's own routing debt.** Its
`--check` refuses with `module plan routing preflight failed`: "unit-job-git-fluency
uses source-git-handbook-archive / source-hu-git-intro / source-progit, but
its source-map unit_routes omit the unit" (`plan_import.py::module_plan_routing_problems`
reads the LIVE unit and map, so no one-row patch can avoid it; the refusal is
saved as `check-git-f1-progit-locator.err`). This is the same unmigrated
critique-point-1 routing debt the verdicts recorded as the git module's 168
warnings — a module whose three declared sources carry empty `unit_routes`
cannot import ANY plan revision, not even this one-line fix. Unblocking it
means authoring routes or dispositions, new plan content that needs Aram's
critique-point-1 decision and that no verdict confirms.

**The checked path for git F1 today is `package-git-f1-full-study-map.yaml`**
(`build_git_fullmap.py` beside this audit): the complete
`unit-job-git-fluency/study-map.yaml` (16 stages) with only that one locator
changed, checked through the procedure's directed single-unit path
`unit-map-import unit-job-git-fluency --file … --replace --check --json`.
`--replace` is required because the unit already has a current map; the merge
carries learner state forward (the check reports all 16 stages' state
preserved, `relative_order_changed: false`, no stages added or retired,
`content_changes` = exactly the one stage-15 resources change,
`canonical_files_written: 0`). It is heavier than the compact patch (a
replacement transaction with Git as prior-version archive), so the landing
session should prefer the compact package once the routing debt is resolved,
and use the full-map package only if the debt stays unresolved when the fix
lands.

## Linked

Materials read in place, read-only, through the clone's mounted materials
symlink (`~/los-glm-C2-2026-10/materials` → the live materials tree); nothing
wrote to the materials tree:

- `material://source-progit/ProGit_2ed.pdf` (501 pp.) — pages 304 and 328
  opened and text-extracted; chapter 7 (pp. 224–341) swept for "worktree".
- `material://source-pydata-handbook/PythonDataScienceHandbook/notebooks/03.01-Introducing-Pandas-Objects.ipynb`
  and `…/03.02-Data-Indexing-and-Selection.ipynb` — markdown headings listed
  in full and searched.

Web pages verified 2026-10-24 (external drift check, no package):

- `https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html` → HTTP
  200, page title "1. FUSE Overview — The Linux Kernel documentation". This is
  the live URL of the engineering-tools FUSE row and it satisfies that row's
  label ("FUSE overview") and locator ("FUSE project documentation").
- `https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse` → HTTP 404.
  This URL is NOT in any live row; the L2-12 report and verdict quoted it as
  "the live row URL" in error (L2-12's own `collected.json` records the live
  row's URL as `…/fuse/fuse.html`). See Completeness.

## Completeness

Disposition of the L2-12 findings against this item's authorization ("fix
only the defects that the verdicts confirm"):

- **git F1 — fixed by both git packages.** Confirmed by both verdicts;
  locator retitle is the report's first suggested form, narrowed to keep the
  two verified section claims rather than dropping the 7.13 mention, because
  7.13 Replace is real, verified, in-scope content and the confirmed defect is
  only the worktree half. Compact package prepared and blocked by the module's
  routing debt (above); full-map package checked clean (`ok: true,
  canonical_files_written: 0`).
- **polars F1 — fixed by `package-polars-f1-notebook-attribution.yaml`.**
  Confirmed by both verdicts; the false half is dropped (reasoning above).
- **engineering-tools F1 — refuted as a live defect; no package.** The
  verdicts' measurement ("`…/fuse/fuse` returns 404") is true of the URL they
  quote, but the live row has carried `…/fuse/fuse.html` since the initial
  snapshot commit `1d32c918`, and that URL returns HTTP 200 with the exact
  page the row names. The suggested fix (re-pointing to `…/fuse/index.html`,
  the section TOC titled "FUSE Technical Documentation") would move a working
  row away from the page its label names, on the strength of a 404 that row
  never had. Left byte-identical.
- **polars F2 (five pandas user-guide heading renames) — no package.** The
  job-modules verdict explicitly lists it under "Not checked", so it is not
  confirmed; content survives under the renamed headings per the L2-12 report.
  Re-pointing the four stale locators stays Aram's call.
- **The 695 `RESOURCE-SCOPE-UNBOUND` warnings (eng-tools 183, polars 212,
  git 168, python 67, rust 65) — no package.** Both verdicts classify them as
  unmigrated critique-point-1 debt, not damage, and neither names a confirmed
  binding defect or a reviewed binding source to port (unlike AML's unapplied
  r2 plan, which gave L2-15 its 17 bindings). Inventing ~550 route bindings
  with no reviewed source would author new plan content, not fix a confirmed
  defect. They stay as recorded debt for Aram.
- `module-job-python-engineering` and `module-job-rust-engineering` had 0
  defects in both verdicts — no packages.

The six checks are attested on the L2-12 measurements re-verified for the
touched rows in this clone: local/linked inventories above (both packages
touch one row each; both target materials opened today); materials content
checked (ProGit headings and worktree absence, notebook heading lists — all
re-verified today); current and prior scope reconciled (both locators are
verbatim legacy/map-draft originals — original design, no later overwrite;
nothing else in either stage diverges from the 2026-10-19 snapshot);
duplicates and numbering checked (0 sibling-route duplicates, L2-12 check D;
each package's one-row change cannot create one); exclusions and unresolved
gaps recorded (the three no-package dispositions above).
