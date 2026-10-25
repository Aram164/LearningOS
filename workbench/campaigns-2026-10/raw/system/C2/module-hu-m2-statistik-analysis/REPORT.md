# C2 report — module-hu-m2-statistik-analysis

Campaign: GLM C2, 2026-10-24. Evidence only — no fixes, no fix packages
(`module-plan-import --check` included), no issues filed. Verified by
GLM-5.3-Flash in one session; a 20% re-check against the PDFs by GLM-5.3 is a
separate later session.

## 1. What was run

- Clone: `~/los-glm-C2-2026-10/repository`, cloned `--no-hardlinks` from the
  live checkout, branch `takeover/complete-and-install-2026-10-23` at
  `a2e2d49d3e4978849c270d55a9583897a2fadbad`, clean tree. Never pushed.
- Venv: `python3.14`, `pip install -e '.[dev]'` per Ground rules. No
  `make setup`, no `make hooks`.
- Materials tree read in place, read-only, via
  `~/los-glm-C2-2026-10/materials -> <workspace>/LearningOS/materials` (the
  validator expects it mounted there; the mount is a symlink outside the
  workspace, and nothing wrote to the materials tree).
- Validator: `.venv/bin/python tools/validate.py --compact` — **0 errors,
  1468 warnings** with materials mounted (1471 before the mount: 2
  ANGLE-REVIEW-UNVERIFIED for this module's study maps plus MATERIALS-OFFLINE
  disappeared once the tree was reachable — the angle reviews verified clean).
- Re-run scripts are in `scripts/` next to this report (`c2_route_audit.py`,
  `c2_pages_audit.py`, `c2_sections_audit.py`, `c2_claims_audit.py`), run with
  the clone's venv python. PDF work used pypdf 6.21.2 directly and
  `tools/material_toc.py`-style outline/page-text reads; ligatures
  (ﬀ ﬁ ﬂ ﬃ), quotes (′ ’ ‘ “ ”) and whitespace normalised before every string
  comparison; misses confirmed against the whole document, never one page;
  page numbers treated as PDF page numbers throughout.

## 2. Findings

### F1 — the known route damage, measured: chapter-resource blocks broadcast onto sibling stages (units ch03–ch07)

The proven case in CAMPAIGNS.md C2 ("a repair keyed on `(source_id, unit_id)`
broadcast one route's locator onto five siblings") is present and wider than
one unit. In the five Analysis chapter units, most of each unit's stage
resources are unbound rows (no `route_id`, no `source_id`) carrying raw
locators, and the same locator strings reappear on sibling stages that cover
different topics:

| unit | stages | distinct unbound locators | carried by ≥2 stages | carried by every stage |
|---|---|---|---|---|
| unit-m2-analysis-ch03 | 6 | 25 | 23 | 3 |
| unit-m2-analysis-ch04 | 4 | 23 | 21 | 5 |
| unit-m2-analysis-ch05 | 7 | 24 | 23 | 12 |
| unit-m2-analysis-ch06 | 7 | 21 | 21 | 14 |
| unit-m2-analysis-ch07 | 3 | 22 | 20 | 19 |

Evidence, verbatim:

- `unser skript.pdf Kapitel 3, printed p. 41 (PDF p. 51)–printed p. 79 (PDF
  p. 89); §3.1 Folgen printed p. 42 (PDF p. 52), …` — carried as a `read`
  resource by **all six** ch03 stages: `stage-m2-analysis-ch03-folgen`,
  `-rekursionen`, `-konvergenzkriterien`, `-rechenregeln`,
  `-bestimmt-divergenz`, `-quadratwurzel`. A whole-chapter menu sits on a
  stage whose topic is a three-page Ausflug (Quadratwurzel, PDF p. 84).
- `Calculus 1 Lecture 2.1: 'An Introduction to the Derivative'; Calculus 2
  Lecture 10.10: 'Taylor and Maclaurin Series'` — a `watch` resource carried
  by **all seven** ch06 stages, from Differenzierbarkeit through
  Trigonometrie and Interpolation.
- `ana_inf_serie05.pdf: 5.1 Türme von Hanoi (recursion → §3.3), 5.2 limits
  from Definition 3.19 …` — a `practise` resource on all six ch03 stages,
  including the stages whose topics are Konvergenzkriterien and Bestimmt
  divergente Folgen.

Contrast, same module: the sibling units unit-m2-analysis-ch01 and -ch02, and
all fifteen `unit-m2-sad-l*` units, bind their stage resources through
`material_ref.route_id` to declared routes; they produce **zero**
RESOURCE-SCOPE-UNBOUND warnings. The source map already declares per-chapter
routes for every damaged unit (`route-an-ch03-analysisskript` …
`route-an-ch07-analysisskript`, all verified against the PDFs below), so the
unbound rows duplicate material those routes already address.

Why `make check` stays clean: every broadcast locator is *individually valid*.
The chapter-range locators verify exactly against the skript's own outline —
Kapitel 3 → PDF pp. 51–89 (outline: "Folgen und Konvergenz" p. 51, "Reihen"
p. 90), Kapitel 4 → 90–107, Kapitel 5 → 108–146, Kapitel 6 → 147–200,
Kapitel 7 → 201–235, all with the skript's constant printed→PDF offset 10.
The defect is structural (same block on every sibling stage, no source
binding), not a bad locator, so no error fires.

ASSUMPTION (mechanism, not state): the (source_id, unit_id)-keyed repair as
the cause is taken from CAMPAIGNS.md; the clone's history cannot date it —
`git log --follow` on `units/unit-m2-analysis-ch03/study-map.yaml` shows only
"Initial clean LearningOS Core snapshot" in this branch's 62 commits. The
current-state measurements above are verified, not assumed.

### F2 — validator warnings for this module: all 481 are real, in exactly two families

Triage of every RESOURCE-SCOPE-UNBOUND warning naming this module
(`generated/reports/validation-report.md` in the clone):

- **472 × "teaches material without a source … no source_id is named"** —
  one per unbound non-`reference` stage resource in ch03–ch07. Counts
  reconcile exactly with the YAML: 86 + 69 + 129 + 127 + 61 = 472. Real
  defects: each is a stage resource teaching material with no source binding,
  and (F1) most are broadcast copies on topic-mismatched sibling stages.
- **9 × "the unit's source disposition is recorded, but no route for this unit
  matches this source and locator"** — all in unit-m2-combined-exam-rehearsal
  (stage-m2-joint-blueprint/-mock-one/-mock-two/-repair). These rows do name a
  `source_id`; their locators are prose placeholders such as "L01-L15 deck
  contents and the SaD.X error ledger" and "Unused scope-matched German
  questions with solutions", which no route can match. The unit has declared
  routes (e.g. `route-686945337831d30097efd0a5`, locator "unser skript.pdf
  Kapitel 1-7 (Stand 04.02.2025), the course contract pp. iv-vii, …") that
  these rows re-describe in other words instead of binding to. Real defects of
  the same unbound family, mechanically repairable.
- **0 noise** among this module's warnings. (Elsewhere in the clone: 5
  ATTACH-LOCAL-ABSENT are local-only handwritten-attachment pins absent by
  design in a fresh clone; 1 HYGIENE-VIEWS is the disposable generated/ view
  set — both noise, both self-explained by the validator. The other 981
  RESOURCE-SCOPE-UNBOUND warnings belong to other modules — job-* ~735,
  skill-python 120, hu-amls 135 (skipped module) — other C2 sessions' scope.)

Per the campaign and boundary 17 these 481 are the deferred debt of critique
point 1; this report records evidence only.

### F3 — minor: section-name drift in one route locator

`route-an-ch02-analysisskript` (source-map.yaml) locator ends
"§2.4 Ausflug – Maschinenzahlen printed p. 26 (PDF p. 36)". The skript's own
outline titles §2.4 "Ausflug – Darstellung reeller Zahlen im Rechner" (PDF
p. 36), with "Maschinenzahlen" as its first subsection (PDF p. 38). The page
claim is correct (p. 36, offset 10 consistent); the section name compresses
the section and its subsection into one title. Cosmetic locator imprecision,
no addressing consequence. Evidence: outline dump of `unser skript.pdf`
(258 pp), entries "Ausflug – Darstellung reeller Zahlen im Rechner -> p 36",
"Maschinenzahlen -> p 38".

### F4 — non-defects worth recording (checked, explained)

- **Route-level duplicates (check D on routes):** exactly three
  `angle_detail` strings are shared by sibling route pairs
  (source-sad-uebungen in units l10, l11, l15 — the "This is the current
  worked tutorial…" template), each pair on **different files and slide
  ranges** (UE6 vs UE7). Deliberate template prose; not the broadcast. No
  duplicated `locator` strings exist among sibling routes anywhere in the
  source map.
- **statistik.pdf (source-fahrmeir-statistik, 9th ed., 665 pp) has a
  non-uniform printed→PDF offset** — 14 in chapter 4 (printed 216 = PDF 230),
  10 in chapter 12 (printed 509 = PDF 519). Both locators verify: the book's
  own Inhaltsverzeichnis gives §4.7 → printed 216 and §12.2.3 → printed 509;
  the PDF bookmarks place them at pp. 230/519; the page text matches (Bayes
  content on 230–231, matrix-notation regression on 519). Not a defect; it
  does mean per-file offset consistency checks cannot assume one offset for
  this file.
- **URL-only sources:** routes of source-mit-1805, source-mit-6034-quizzes,
  source-cs229-problem-sets and source-mmds-book name PDFs
  (`mit18_05_s22_exam_final.pdf`, `MIT6_034F10_quiz3_2010.pdf`,
  `ps2-sol.pdf`, `ch3.pdf`) that exist only online; their page/section claims
  are unverifiable on this machine. Recorded as unverifiable-locally, not
  defects. source-sad-uebungen is an alias source (material →
  `source-sad-ss26-lectures/exercise-slides`); all its named files exist
  there, including `Übung-3.pdf`.
- **All 318 `vault_path` values in the source map resolve** through the
  `.flat` id farm, and every locator that names a local file names the file
  its `vault_path` points at (0 mismatches after normalising name variants
  such as "skript.pdf" for "unser skript.pdf", "guide_ch02.pdf" for
  "mitres_18_001_f17_guide_ch02.pdf").

## 3. Check-by-check results (routes: 600 across 97 sources; resources: 1420 stage rows, 783 route-bound)

- **A — vault_path / material:// vs locator file:** 318/318 vault_paths
  resolve; 0 file mismatches. 27 stage-resource "unresolved URI" hits in the
  script output were a regex artifact (URIs contain a space:
  `material://source-analysis-skript/unser skript.pdf` — raw YAML verified).
- **B — page ranges vs real page counts:** 0 out-of-range across every
  `PDF p. N` mention on routes and stage resources (2020 items scanned).
  Offset conflicts: one (statistik.pdf, explained above). Printed→PDF pairs
  in the skript locators are constant at offset 10 across all seven chapters.
- **C — named sections against the material:** claim-based verification of
  every (section, PDF page) pair: 44 verified via outline/page text, 23
  script "unverified" all traced to extractor artifacts and then verified by
  hand (all seven skript chapter-start pages agree with the outline;
  "Exkurs – Landau-Notation" p. 56, "Ausflug – Lineare Rekursionsgleichungen"
  p. 57, "Ausflug – Berechnung der Quadratwurzel" p. 84, "Ausflug –
  Umordnungen" p. 102, "Ausflug – Sinus-, Kosinus- und Tangensfunktion"
  p. 158, "Ausflug – Einblick in die numerische Interpolation" p. 184; Lebl
  realanal.pdf Series p. 87 / More on series p. 100 / The Derivative p. 155 /
  MVT p. 162 / Taylor p. 171 / IFT p. 176; Labs-Schreyer 'Reihen' p. 113 with
  subsections p. 115/120; MIT 18.100A lectures p. 69/72/76). Blitzstein
  exercises verified with printed footers: Ex 2.3.9 → PDF 73 (footer "56",
  offset 17), Ex 2.8.3 → PDF 93 (footer "76"), Hibbert on pp. 93–95. The two
  script "REFUTED" hits were extractor artifacts (trailing-comma title;
  "Maschinenzahlen" paired with the §2.4 start page — see F3). 8
  route-title-vs-locator number disagreements all resolved as benign
  cross-book references or sub-section refinements (e.g. Murphy §11.2.2 vs
  11.2.2.1).
- **D — duplicates among sibling routes of one (source_id, unit_id) group:**
  3 template angle_detail pairs (F4); 0 locator duplicates among routes. The
  real duplication lives one level down, on stage resources (F1).

## 4. Assumptions and limits

- ASSUMPTION: the broadcast *mechanism* ((source_id, unit_id)-keyed repair)
  is from CAMPAIGNS.md; not datable from this clone's git history (F1).
- pypdf text extraction; two statistik.pdf pages exceed pypdf's stream-token
  limit and were skipped in whole-document scans (both outside any claim
  checked). The `.md` transcript files under source-3b1b-essence-of-calculus
  matched by a loose `.pdf` glob were excluded (not PDFs).
- URL-only-source claims (F4) and the 5 local-only attachment pins were not
  verifiable on this machine.
- The shared-kernel pattern could in principle be intended "chapter backdrop"
  on some stages (e.g. quadratwurzel's Forster/Wessoly §§4–6 genuinely covers
  Wurzeln); the report states which locators are shared where and leaves the
  per-row keep/bind/split judgment to the fix owner.

## 5. Out of scope (per kickoff: evidence only)

No fixes, no `module-plan-import --check` packages, no GitHub issues, no
edits to any canonical file; the clone and the materials mount were used
read-only. The 20% GLM-5.3 re-check against the PDFs, any repair, and any
issue filing belong to Aram or Claude per CAMPAIGNS.md.
