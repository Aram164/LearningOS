# C2 report — `module-job-git` (item L2-12, evidence only, 2026-10-24)

Session: GLM-5.3-Flash. Clone `~/los-glm-C2-2026-10/repository` at `a2e2d49d`,
branch `takeover/complete-and-install-2026-10-23`, tree clean, never pushed.
Validator on the clone: **0 errors / 1468 warnings**. Full check tables and
reproduction commands: [`../_job-modules-evidence/VERIFICATION-LOG.md`](../_job-modules-evidence/VERIFICATION-LOG.md).

Scope: 1 unit (`unit-job-git-fluency`), 16 stages, 215 resources (70 read,
47 reference, 98 practise), no routes (the module's `source-map.yaml` declares
3 sources with empty `unit_routes`; all binding lives in stage resources).

## Checks

- **A (vault_path):** 59 resource vault_paths resolve — `material://` URIs
  through the `.flat` farm (ProGit_2ed.pdf, HU-intro-to-git.pdf, 41
  git-handbook `intentions/*.html` pages), repo-relative none. 59/59 ✓.
- **B (page ranges):** the only local PDF is ProGit_2ed.pdf (501 pp); no row
  claims pages, only chapter/section numbers, so B is vacuous here. The HU
  PDF (26 pp) has no page claims either.
- **C (named sections vs text):** every ProGit section named in the locators
  verified against the PDF outline and the page text of the section's start
  page — 34 headings checked, all present (e.g. 2.2 Recording Changes p34,
  7.11 Submodules p304, 10.4 Packfiles p435). The git-handbook index page
  says "the 4 regions in one mental picture" (WT/IDX/Open Local/Open
  Remote), grounding the 'Four-region visual map' locator. HU-intro-to-git
  text contains every topic a HU row names (branch, remote, staging, index,
  merge, clone, push/pull). One finding below.
- **D (sibling duplicates):** no routes, so vacuous; repeated stage-row
  locators are template rows ('Exercise 1'-'Exercise 5' × 16 stages) and one
  page-group label ('Stage/unstage/discard/rename pages') shared by four rows
  that point at four different intention pages on one stage — by design.

## Provenance

One commit total (`1d32c918`, the 2026-10-19 snapshot): nothing in the module
was modified after the snapshot. The study-map is a faithful migration of
`LearningOS/legacy/Job/plans/job-track-git.yaml` (provenance
`migrated-mini-plan`): 16/16 stage ids, all resource ids, zero field diffs;
legacy `LearningOS/materials/software/…` vault paths were rewritten to
id-based `material://` form. Verdict: **original design / unmigrated debt,
no damage**.

## Findings

### F1 — stage-git-15 Pro Git row names worktree chapters the book does not have (low, original design)

- Row: `resource-git-15-…` in stage
  `stage-git-15-worktrees-parallel-tickets-and-advanced-repository-lay`,
  `source_id: source-progit`, `vault_path: material://source-progit/ProGit_2ed.pdf`.
- Locator (verbatim): **"Pro Git worktrees and submodules Chs. 7.11, 7.13"**.
- Observed: `[Ww]orktree` appears **nowhere in chapter 7 (PDF pp224-341)**;
  the whole 501-page PDF mentions it only at pp453/457, both incidental
  ("--work-tree, GIT_WORK_TREE or core.worktree is specified" env-var docs;
  "setup: worktree: /Users/ben/src/git" trace output). In this book 7.11 =
  Submodules (heading on p304) and 7.13 = Replace (heading on p328). The
  worktree half of the locator is unsatisfiable by the named material; the
  submodule half is correct.
- Expected: a locator that names worktree content should point at material
  containing it (the stage's other rows do: 'MIT advanced Git worktree
  pointer' and the git-worktree/submodule official-docs rows).
- Origin: verbatim from `LearningOS/legacy/Job/plans/job-track-git.yaml`
  line 1719 — pre-migration debt carried through the migration, not
  broadcast damage (the campaign's September pattern does not apply).
- Suggested fix (for Aram/Claude, not applied): retitle the locator to
  "Pro Git submodules Ch. 7.11" and let the existing git-worktree docs row
  carry worktrees, or point the worktree half at the official docs row.

## Validator warnings (168, all RESOURCE-SCOPE-UNBOUND)

All real under the validator's rule; shape is the legacy plan's design, not
damage:
- 109 `no-source`: template practise rows ('Exercise 1-5'), url-only
  reference rows (git-scm docs, MIT list), and rows pointing at knowledge
  notes — no `source_id`, so module adoption cannot be checked.
- 59 `no-disposition`: the three declared sources have no unit
  `source_selections`/`scope_sources` rows and the map declares no routes.
  Unmigrated critique-point-1 debt (same shape as AML/M2).

## Assumptions

- ProGit section numbers are canonical 2nd-edition numbering (the PDF's
  bookmarks carry no numbers); mapping verified via heading text at outline
  pages, not via a numbered TOC.
- The 109/59 warning split is from the generated report's message text, not
  a re-run of plan_rigor in isolation.
