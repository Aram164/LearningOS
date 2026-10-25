# C2 20% re-check (L1-234, 2026-10-24)

GLM-5.3 re-check of a sample of the C2 defects against the PDFs, per the
campaign. Same session as C1's verification pass (item L1-234); the C1 half
of this session's output is `../C1-VERIFY.md`.

- **Environment:** the C2 campaign clone `~/los-glm-C2-2026-10/repository`
  (branch `takeover/complete-and-install-2026-10-23` at `a2e2d49d`, clean),
  read-only; materials read in place through the campaign's
  `~/los-glm-C2-2026-10/materials` mount. Nothing pushed, nothing written.
- **Defect universe:** every module report's numbered defect findings.
  Zero-defect modules (betriebssysteme, icop, bachelor-thesis,
  ml-math-bridges, skill-python — confirmed: no `### F` sections, no defect
  claims) contribute nothing. The universe is **9 findings**: M2 F1–F3,
  AML F1–F2 (AML F3 is explicitly "no defect claim", excluded), job-git F1,
  job-polars F1–F2, job-engineering-tools F1. 20% of 9 is 1.8 → the floor
  is 2; I re-verified **7 of 9 (78%)** — every finding whose evidence is a
  local material, plus count-reconciliation of both warning-triage findings.
  The two not re-checked are the web-drift findings (job-polars F2 pandas
  docs, job-engineering-tools F1 FUSE URL): their evidence is a live
  website, not a PDF, so they are outside "re-verify against the PDF
  itself". They remain exactly as reported, unre-checked here.

## Verdicts

| Finding | Re-verified evidence | Verdict |
|---|---|---|
| M2 F1 broadcast blocks on ch03–ch07 stages | YAML stage counts + outline chapter starts | **CONFIRMED** |
| M2 F2 481 warnings all real | count reconciliation 86+69+129+127+61 = 472 no-source (+9 rehearsal, read) | **CONFIRMED** (arithmetic) |
| M2 F3 §2.4 "Maschinenzahlen" name drift | skript outline, verbatim | **CONFIRMED** |
| AML F1 printed-page anchors (−30) | pml1 outline + on-page printed headers, all 9 sub-anchors | **CONFIRMED** |
| AML F2 31 warnings, 46 unbound rows original design | count reconciliation 46 unbound rows | **CONFIRMED** (arithmetic) |
| job-git F1 Pro Git worktree half unsatisfiable | whole-PDF text scan + headings | **CONFIRMED** (one extra incidental page found; conclusion unchanged) |
| job-polars F1 notebook 03.01/03.02 misattribution | notebook headings | **CONFIRMED** |

## What I checked, per finding

### M2 F1 — broadcast chapter-resource blocks (CONFIRMED)

- YAML, live branch: `unit-m2-analysis-ch03` has 6 stages and the
  `§3.1 Folgen …` chapter locator is carried by **all 6**;
  `unit-m2-analysis-ch06` has 7 stages and the
  `Calculus 1 Lecture 2.1 … Calculus 2 Lecture 10.10 …` row by **all 7**;
  the `ana_inf_serie05.pdf … Türme von Hanoi …` row by **all 6** ch03
  stages. Matches the report's table exactly (spot-checked three of the
  five units).
- PDF side of "each locator is individually valid": outline of
  `unser skript.pdf` (258 pp) puts the five chapter starts at exactly the
  claimed PDF pages — Folgen und Konvergenz **51** (Kap. 3), Reihen **90**
  (Kap. 4), Differentialrechnung I **108** (Kap. 5), Differentialrechnung
  II **147** (Kap. 6), Integralrechnung **201** (Kap. 7) — the constant
  printed→PDF offset-10 structure the report describes. The defect is
  structural (same block on every sibling stage), as reported.
- Note: M2's CLAUDE-VERDICT (read, not re-derived here) reclassifies F1's
  *provenance* as original unmigrated design rather than the September
  repair damage; the current-state measurements above are what I verified,
  and they hold either way.

### M2 F3 — §2.4 section-name drift (CONFIRMED)

Outline of `unser skript.pdf`, verbatim: **"Ausflug – Darstellung reeller
Zahlen im Rechner" → PDF p. 36** and **"Maschinenzahlen" → PDF p. 38**.
Exactly the report's evidence: the locator's "§2.4 Ausflug –
Maschinenzahlen … (PDF p. 36)" compresses the section (p. 36) and its first
subsection (p. 38) into one title; page claim correct, name imprecise.
Minor, as reported.

### AML F1 — printed anchors in three exam-prep rows (CONFIRMED)

- Study map (live branch) carries all the claimed bare numbers
  (`p. 372`, `p. 380`, `pp. 277…`, `pp. 289…`, `pp. 298…`, `pp. 518…`,
  `pp. 526…`).
- `pml1.pdf` (860 pp) outline: §11.2.2 → **402**, §11.2.4 → **410**,
  §8.1.3 → **307**, §8.3 → **319**, §8.4.6 → **328**, §15.4 → **548**,
  §15.4.1 → **549**, §15.4.3 → **551**, §15.5 → **556**, 15.5.1–15.5.4 →
  **556/557/558/559**. Every claimed number is exactly 30 below the true
  PDF page.
- Printed headers on the target pages contain the claimed numbers:
  p402 prints "372", p410 "380", p307 "277", p319 "289", p328 "298",
  p548 "518", p549 "519", p556 "526". So each row anchors the book's
  *printed* number — the repository convention (PDF numbers, per the
  campaign pitfalls and the module's own `pdf pp.`-style routes) is
  violated. All nine sub-anchors verified; finding fully holds.

### job-git F1 — "worktrees" half of the Pro Git locator (CONFIRMED)

`ProGit_2ed.pdf` (501 pp): case-insensitive `worktree` appears on **453,
457, 478** — env-var documentation, trace output, and a JGit build example
respectively. **None inside chapter 7 (pp 224–341).** The report listed
453/457; my scan adds 478, equally incidental — conclusion unchanged: the
worktree half of "Pro Git worktrees and submodules Chs. 7.11, 7.13" is
unsatisfiable by the named book. Corroboration of the section identity:
"Replace" stands as a heading line on **p328** (report: 7.13 Replace p328);
the Submodules run begins **p304** within ch7 (report: 7.11 Submodules
p304; the earlier p294 hit is the chapter's tool-list intro).

### job-polars F1 — notebook 03.01/03.02 (CONFIRMED)

Materials, `PythonDataScienceHandbook/notebooks/`:
`03.01-Introducing-Pandas-Objects.ipynb` contains heading "The Pandas Index
Object" and **not** "Data Selection in Series";
`03.02-Data-Indexing-and-Selection.ipynb` contains "Data Selection in
Series" and not the former. Exactly as reported: the row's
`vault_path` points at 03.01 while quoting 03.02's section.

### Count reconciliation of the two triage findings (CONFIRMED)

- M2 F2: unbound non-reference stage-resource rows per unit — ch03 **86**,
  ch04 **69**, ch05 **129**, ch06 **127**, ch07 **61**; total **472**,
  equal to the report's no-source warning count and its own arithmetic.
- AML F2: `unit-aml-exam-prep/study-map.yaml` holds exactly **46** unbound
  rows, matching the report's 9 + 22 + 15 reconciliation base.

## The M2 section-check question (method note in AML REPORT §5)

The AML report's §5 claims the M2 sections-audit's "farm search silently
matched nothing on this machine" because `materials/.flat`'s source folders
are symlinks that `Path.rglob` does not descend. Verdict: **the claim about
the fallback is correct, and the honest summary is "partially" — the check
did search the materials for most routes, and silently skipped 80.**

Measured in the campaign clone with the M2 script's own logic
(`C2/module-hu-m2-statistik-analysis/scripts/c2_sections_audit.py`):

- **The fallback is dead, exactly as AML said.** `materials/.flat` has 100
  entries, all 100 symlinks; `(MATERIALS/".flat").rglob("*.pdf")` — the
  script's `find_pdf` — returns **0 files**, while the same file addressed
  directly (`.flat/source-analysis-skript/unser skript.pdf`) resolves fine.
- **But the script's primary path works.** `resolve()` builds the exact
  path from each route's `material://` vault_path (stat follows the symlink
  at the final component chain), and **318 of M2's 600 routes** resolved
  that way — for those, outline/page-text verification genuinely searched
  the materials. My own re-verification above (chapter starts, F3 outline)
  reproduces the report's PDF evidence exactly, so the by-hand outline work
  was real.
- **What was silently skipped:** 16 routes are URL-sources (skipped by
  design), 186 name no PDF — and **80 routes name a PDF but carry no
  resolvable vault_path**, so they fell to the dead `find_pdf`, got
  `path is None`, and hit the script's silent `continue`: not verified and
  *not counted as misses either*. The 80 are dominated by
  `source-sad-ss26-lectures` lecture decks (`lecture-slides/01_introduction.pdf`
  etc.) plus one skript route.
- Consequence for the M2 report: its check-C paragraph "claim-based
  verification of every (section, PDF page) pair" overstates coverage —
  the script verified the pairs it could resolve, and the 80
  fallback-dependent routes' section claims (§-refs into the SaD lecture
  decks) were never checked by the script. Nothing in the report's
  *positive* verifications is invalidated — every one I re-checked
  reproduces — but the "every" is wrong, and the misses list cannot contain
  defects hiding in those 80 routes. If Aram wants those closed, they need
  one pass with the AML session's symlink-aware locator.

## Assumptions and limits

- pypdf 6.x extraction (same as the C2 sessions); the two
  `statistik.pdf` pages over the stream-token limit were not touched (no
  sampled claim needs them).
- M2 F1's *mechanism* attribution remains the campaign text's assumption
  (this clone's history cannot date it); the re-check here covers
  current state only.
- The two web-drift findings were not re-checked (see sample note above).
- No fixes, no fix packages, no issues; clone and materials used read-only.
