# C2 report — `module-job-polars` (item L2-12, evidence only, 2026-10-24)

Session: GLM-5.3-Flash. Clone `~/los-glm-C2-2026-10/repository` at `a2e2d49d`,
branch `takeover/complete-and-install-2026-10-23`, tree clean, never pushed.
Validator on the clone: **0 errors / 1468 warnings**. Full check tables:
[`../_job-modules-evidence/VERIFICATION-LOG.md`](../_job-modules-evidence/VERIFICATION-LOG.md).

Scope: the largest of the five — 10 units, 31 stages, 290 resources (101
read, 72 reference, 115 practise, 2 watch) plus **29 source-map routes** from
6 sources (polars-definitive-guide 9, pydata-handbook 8, stratum-paper 4,
scalable-dataframe-systems-paper 4, python-cheatsheets 3, python-depth-drills
2). 114 vault_path rows.

## Checks

- **A (vault_path):** 114 rows + 29 routes = 143 paths, all resolve ✓
  (material:// URIs through the `.flat` farm — the guide PDF, pydata
  notebooks, cheatsheet, stratum/scalable papers, depth-drills files — plus
  repo-relative attachment/note paths; one row intentionally pins an
  attachment directory).
- **B (page ranges):** every route range is inside its PDF's real page count
  (guide 591 pp, cheatsheet 2, stratum 8, scalable 19). The 12 distinct
  guide ranges (14-51 … 537-591) all match the chapter boundaries in the
  PDF's own outline — table in the verification log. The route's "fold
  section" (pp. 387-390) is real: those pages carry 14 `Expr.fold()` /
  `Expr.reduce()` mentions (p387 "the Polars API are the Expr.reduce() and
  Expr.fold() methods", p389 "Figure 13-1. How a fold function is
  executed").
- **C (section claims vs text):** all 35 distinct section+page claims on the
  guide verified exactly against the PDF outline AND the section title
  string found in the claimed page's extracted text (e.g. §Concepts to
  Unlearn p83 with next section p93, claimed 83-92). "pp." provably means
  PDF viewer pages (claims match outline pages exactly). pydata notebook
  claims: 13/16 hit the named file's text; two are title paraphrases with
  content present (03.03's actual heading 'Ufuncs: Operations Between
  DataFrames and Series'; 03.12's 'pandas.eval for Efficient Operations' /
  'The DataFrame.query Method'); one misattribution found (F1). Cheatsheet:
  all nine claimed panel titles on pp1-2 ✓. SHELF.md 3a 'Testing' / 3c
  'Performance' and stage-8 Q8.10/Q8.11 ✓. External-docs drift: F2.
- **D (duplicates):** clean — no unit has two routes from one source; no
  same-unit duplicate route locators or angle_details; identical locators
  across different units (stratum paper × 4 units, scalable paper × 3,
  drills s09/s10) are deliberate per-unit background routes, not sibling
  duplicates; repeated stage-row locators are template rows ('Complete guide
  retained from the original monolithic plan' × 16, 'Complete note' × 5).

## Provenance (settled, no damage)

One commit total (`1d32c918`, 2026-10-19 snapshot): nothing in the module
changed after the snapshot. The module was authored through
`work/active/workspace-job-polars-plan/outputs/`:
- The operator package `polars-backend-session-migration.yaml`'s source_map
  (all 29 routes) is **content-identical** to live (runtime keys stripped).
- 3 units (order-text-time, aggregation-windows, capstone-transition) match
  the package except the backfill-added `knowledge_node_id`.
- 6 units match the session's `map-drafts/` (the enriched successor of the
  package: sharper locators, exercise-sheet attachments, expanded
  done_when) except `knowledge_node_id`.
- `backend-loop` matches the package except `knowledge_node_id` plus 3 rows
  converted to `material_ref.route_id` binding with `angle_review` stamps
  ("refinement", "Codex under Aram cleanup authorization", 2026-09-30) —
  the same authorized route-binding pass pattern the AML session dated to
  the 09-07 compact, plus the 09-20 node-linkage backfill.

Every divergence from the ancestors is (a) an authorized, stamped pass or
(b) the session's own drafted refinement. The F1 misattribution already
appears verbatim in the map-drafts — original design of that session.

## Findings

### F1 — stage-polars-01 attributes a 03.02 notebook section to notebook 03.01 (low, original design)

- Row: `resource-pydata-01-…` in stage
  `stage-polars-01-two-data-models-and-the-eight-divergence-axes`,
  `source_id: source-pydata-handbook`,
  `vault_path: material://source-pydata-handbook/PythonDataScienceHandbook/notebooks/03.01-Introducing-Pandas-Objects.ipynb`.
- Locator (verbatim): **"§'The Pandas Index Object' and §'Data Selection in
  Series' (notebook 03.01)"**.
- Observed: notebook 03.01's headings are Introducing Pandas Objects / The
  Pandas Series Object / … / The Pandas Index Object / Index as Immutable
  Array / Index as Ordered Set — no selection section. `# Data Selection in
  Series` is a heading of **03.02-Data-Indexing-and-Selection.ipynb**; the
  string appears in no other local notebook. The locator even names "notebook
  03.01" explicitly, doubling the misdirection.
- Expected: a §-quoted section claim should exist in the file the row points
  at (system contract: locator ↔ named material; validator
  RESOURCE-SCOPE-UNBOUND only covers route binding, not this).
- Origin: verbatim in `map-drafts/unit-job-polars-pandas-fluency-study-map.yaml`
  — the polars session's own draft, not a later overwrite.
- Suggested fix (not applied): point the section half at notebook 03.02
  (split the row or re-mention "(notebook 03.02) for selection").

### F2 — five reference rows cite pandas user-guide headings that pandas has since renamed or moved (low, external drift)

Fetched 2026-10-24 (pandas 3.1.x docs):
- `user_guide/merging.html`: 'Brief primer on merge methods' is now **'Merge
  types'**; 'Checking for duplicate keys' is now **'Merge key uniqueness'**
  (rows on stage-polars-12, stage-polars-14).
- `user_guide/reshaping.html`: 'Reshaping by melt' → **'melt() and
  wide_to_long()'**; 'Pivot tables' → **'pivot() and pivot_table()'**
  (stage-polars-14).
- `user_guide/basics.html#dtypes`: 'Nullable integer data type' and
  'Nullable Boolean data type' are no longer headings on that page at all —
  they moved to separate pages (`integer_na.html`, `boolean.html`); only
  sidebar links remain (stage-polars-06, stage-polars-07).
- Still valid: `indexing.html` 'Boolean indexing' ✓ + 'Reindexing'
  (subsection) ✓; `docs.pola.rs/.../casting/` ✓.
- Content survives under the renamed headings; this is drift of an external
  living reference, not internal damage. Suggested fix (not applied):
  re-point the four stale locators to the renamed headings/pages.

## Validator warnings (212, all RESOURCE-SCOPE-UNBOUND)

- 174 `no-source`: template practise rows, url-only reference rows (pola.rs
  API pages, pandas docs, polars 2.0 upgrade notes), and knowledge-note rows.
- 38 `disposition-but-no-route`: every non-reference row that carries both a
  `source_id` and a `vault_path` (38 `read` rows). Their locators are
  section-granular ('Ch. 13', "§'Index alignment in DataFrame'… (notebook
  03.03)") while the unit's route locator is chapter-range-granular
  ('Chapter 13, PDF viewer pages 369-402'), so no (unit, source_id, locator)
  route pair matches. Real under the validator's rule; shape = binding debt
  of critique point 1, the same pattern the AML (31) and M2 (481) sessions
  found — the material is the route's own material, the route pair just
  doesn't string-match. One practise URL row (book-repo) has the same shape
  but is not warned (the validator scope-checks material-bearing rows;
  ASSUMPTION: intended filter).
- 0 `undeclared-source`: all six sources the rows name are declared in the
  module source-map.

## Assumptions

- The pandas/kernel.org pages are living documents; fetches reflect
  2026-10-24.
- plan_rigor.py's material-row filter inferred from counts, not read
  line-by-line.
- The guide's early-release status (the routes' own angle_detail warns
  "confirm examples against Polars 1.36.0 because the local book is an
  early-release edition") means page drift is expected by the authors; all
  claims nonetheless verified against THIS copy.
