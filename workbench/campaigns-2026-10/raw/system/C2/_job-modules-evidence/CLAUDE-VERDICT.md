# Claude's verdict on C2 for the five `module-job-*` modules (L2-12, 2026-10-24, overnight orchestrator)

**Verdict: the reports hold. There are four low findings, none of them
damage.** The 695 `RESOURCE-SCOPE-UNBOUND` warnings are unmigrated debt
under critique point 1, as GLM says. I did not re-run the validator.

## Spot checks (read-only)

1. **git F1, the worktree locator. CONFIRMED.**
   - `materials/software/tooling/progit/ProGit_2ed.pdf` has 501 pages.
   - p304 contains "Submodules" and p328 contains "Replace".
   - No page in pp.224–341 (chapter 7) mentions "worktree".
   - The locator "Pro Git worktrees and submodules Chs. 7.11, 7.13" is
     verbatim in `LearningOS/legacy/Job/plans/job-track-git.yaml`, so it is
     original design, carried over in the migration.
   - The stage on worktrees has no worktree material in this book. When the
     plan is next revised, it needs another source for worktrees, such as
     git-scm's `git-worktree` documentation.
2. **polars F1, the notebook misattribution. CONFIRMED.**
   - "Data Selection in Series" is a heading in
     `03.02-Data-Indexing-and-Selection.ipynb`, not in
     `03.01-Introducing-Pandas-Objects.ipynb`, which the row's `vault_path`
     names.
3. **engineering-tools F1, the FUSE URL. CONFIRMED.**
   - `https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse` returns
     404.
   - `…/filesystems/fuse/index.html` returns 200.
   - This is external drift.

Not checked: polars F2, the renamed pandas user-guide headings, also
external drift; and the 35/35 guide and 17/17 Rust chapter claims. Those are
GLM's measurements.

## For Aram

All four findings are fixes to plan data, which fall under critique point 1
and are reserved to you. None is a Core defect, so there is no issue draft.
The worktree gap is the only one that leaves a stage without real material.

## Correction and fix packages (conductor 2, Sun 2026-10-25 02:30)

**Correction: engineering-tools F1 (FUSE) is REFUTED. My verdict above was
wrong.**
- The live row carries `https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse.html`,
  which returns **200** (checked 2026-10-25).
- I had tested the truncated `…/fuse/fuse`, which returns 404.
- L2-17 caught this.

**The packages (L2-17):**
- polars F1 (the notebook attribution) passes `--check`;
- git F1 (`unit-map-import --replace`, full map: "Pro Git submodules and
  replace Chs. 7.11, 7.13") passes `--check`;
- its compact variant is refused, verbatim in the `.err` file. The
  full-map package is the one to use.

None is applied. They wait for the live-branch merge.
