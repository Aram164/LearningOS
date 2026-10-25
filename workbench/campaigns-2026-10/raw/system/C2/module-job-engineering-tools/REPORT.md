# C2 report — `module-job-engineering-tools` (item L2-12, evidence only, 2026-10-24)

Session: GLM-5.3-Flash. Clone `~/los-glm-C2-2026-10/repository` at `a2e2d49d`,
branch `takeover/complete-and-install-2026-10-23`, tree clean, never pushed.
Validator on the clone: **0 errors / 1468 warnings**. Full check tables:
[`../_job-modules-evidence/VERIFICATION-LOG.md`](../_job-modules-evidence/VERIFICATION-LOG.md).

Scope: 1 unit (`unit-job-engineering-tools-fluency`, the "missing semester"),
20 stages, 248 resources (60 read, 65 reference, 123 practise), no routes.
Mostly URL rows into MIT missing-semester lectures, man pages, standards
docs; 22 vault_path rows (pydata notebooks, git-handbook pages, knowledge
notes).

## Checks

- **A (vault_path):** 22 rows resolve ✓ (material:// into
  `source-pydata-handbook` notebooks 01.05/01.06/01.07/03.12 and
  git-handbook pages, plus repo-relative knowledge-note paths).
- **B (page ranges):** no local PDF carries a page claim; vacuous.
- **C (named sections vs text):** 'IPython shell-command notebook' →
  01.05-IPython-And-Shell-Commands.ipynb exists with matching heading ✓. The
  git-handbook and knowledge-note rows are prose locators verified at the
  file level by A. URL rows were spot-sampled, not exhaustively fetched
  (see Assumptions).
- **D (duplicates):** no routes; repeated locators are the 'Exercise 1-5' ×
  20 template rows and MIT-lecture labels reused by a reference row and a
  practise row of the same stage — by design.

## Provenance

One commit total (`1d32c918`). Faithful migration of
`LearningOS/legacy/Job/plans/job-track-missing-semester.yaml`: 20/20 stage
ids, all resource ids, zero stage-field diffs, exactly two row-level edits
both in stage-18's FUSE row (label 'www.kernel.org — fuse.html' → 'kernel.org
— FUSE overview'; URL `…/filesystems/fuse.html` → `…/filesystems/fuse/fuse`).
Verdict: **original design / unmigrated debt, no damage**.

## Findings

### F1 — stage-18 FUSE row points at a dead kernel.org URL (low, external drift; the legacy URL is dead too)

- Row: `resource-missing-semester-18-07-optional-depth-www-kernel-org-fuse-htm`,
  stage `stage-missing-semester-18-systems-potpourri-…`, `kind: reference`,
  url `https://www.kernel.org/doc/html/latest/filesystems/fuse/fuse`.
- Observed (fetched 2026-10-24): live URL → **HTTP 404**; the legacy-plan URL
  `…/filesystems/fuse.html` → **HTTP 404**; the current FUSE documentation
  lives at `…/filesystems/fuse/index.html` → HTTP 200.
- Expected: a reference row's URL should resolve to the named material.
- Origin: the migration already edited this row's URL and label (the only
  two field diffs against the legacy plan) but landed on another dead path —
  the kernel docs were restructured under it. External drift, not internal
  damage.
- Suggested fix (not applied): update the URL to
  `https://www.kernel.org/doc/html/latest/filesystems/fuse/index.html`.

## Validator warnings (183, all RESOURCE-SCOPE-UNBOUND)

- 171 `no-source`: the module is URL-heavy; template practise rows
  ('Exercise 1-5' × 20 stages) and url-only reference rows dominate.
- 12 `no-disposition`: declared sources (git-handbook-archive, hu-git-intro,
  progit, pydata-handbook, python-depth-drills) have no unit dispositions
  and no routes. Unmigrated critique-point-1 debt, not damage.

## Assumptions

- URL rows other than the FUSE row were not fetched this session (MIT
  missing-semester pages, man7.org, OWASP, NIST, RFC-style docs); their
  locators name no local text, so there was nothing to compare beyond
  reachability. The validator's own URL checks do not cover external
  reachability either.
- The pydata notebook claims verified here are the two this module actually
  makes (01.05 heading; 03.12 rows verified in the polars report share the
  same files).
