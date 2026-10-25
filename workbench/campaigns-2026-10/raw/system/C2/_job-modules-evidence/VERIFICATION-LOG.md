# L2-12 verification log — the five `module-job-*` modules (2026-10-24)

Environment: clone `~/los-glm-C2-2026-10/repository` at `a2e2d49d`, branch
`takeover/complete-and-install-2026-10-23`, working tree clean; materials
symlink `~/los-glm-C2-2026-10/materials` → live tree. Validator on the whole
clone: **0 errors, 1468 warnings** (`tools/validate.py --compact`, 2.7 s).
Every number below was produced in this session by the commands shown or by
the equivalent pypdf/text checks described inline; anything not re-derivable
is marked ASSUMPTION in the module reports.

`collected.json` holds every stage-resource row (911) and source-map route
(29) of the five modules, dumped from the clone's YAML with the clone's venv.

## A-check — vault_path resolution

268 vault_paths checked (239 stage-resource rows + 29 routes): **all
resolve**. Two coordinate systems: repo-relative paths
(`curriculum/modules/...`, `knowledge/...`) resolved against the clone;
`material://source-<id>/…` URIs resolved through `materials/.flat/` with
NFC/NFD tolerance. One row intentionally resolves to a directory:
`resource-polars-02-05-local-material-contention-probes` →
`knowledge/attachments/note-pandas-polars-aggregation-contentions/` (an
attachment pin; the validator supports directory URIs and raised nothing).
Zero `MATERIAL-MISSING` / `MATERIAL-UNREGISTERED` errors tree-wide.

## B-check — page ranges against real page counts

Real page counts (pypdf): polars guide **591**, Pandas_cheatsheet **2**,
stratum paper **8**, Towards Scalable Dataframe Systems **19**, ProGit **501**,
HU-intro-to-git **26**, fluent-python **1011**, effective-python **469**.

All polars route ranges inside 591: 14-51, 74-102, 103-177, 122-143, 178-306,
279-326, 307-368, 327-368, 369-402, 387-390, 403-457, 503-591, 537-591.
Cheatsheet routes claim pp. 1-2 of a 2-page sheet (exact). Stratum routes
claim pp. 4-5 and 1-2 of 8. Scalable-dataframe routes claim pp. 5-7 and
10-12 of 19. No page claim anywhere exceeds its PDF.

Chapter ranges vs the polars guide's PDF outline (393 entries; pypdf
destination pages = PDF viewer pages):

| route | claim | outline evidence | verdict |
|---|---|---|---|
| s01 | Ch 1 = 14-51 | ch1 starts p14, ch2 starts p52 | ✓ |
| s01 | Ch 3 = 74-102 | ch3 starts p74, Part II divider p102 | ✓ |
| s02 | Ch 7-10 = 178-306 | ch7 starts p178, ch11 starts p307 | ✓ |
| s03 | Ch 10-11 = 279-326 | ch10 starts p279, ch12 starts p327 | ✓ |
| s04 | Ch 4-6 = 103-177 | ch4 starts p103, Part III divider p177 | ✓ |
| s04/s05 | Ch 12 = 327-368 | ch12 starts p327, ch13 starts p369 | ✓ |
| s05 | Ch 11-12 = 307-368 | ch11 starts p307, ch13 starts p369 | ✓ |
| s06 | Ch 13 = 369-402 | ch13 starts p369, ch14 starts p403 | ✓ |
| s07 | Ch 14-15 = 403-457 | ch14 starts p403, Part V divider p457 | ✓ |
| s08 | Ch 5 = 122-143 | ch5 starts p122, ch6 starts p144 | ✓ |
| s08 | Ch 17-18 = 503-591 | ch17 starts p503, doc ends p591 | ✓ |
| s10 | Ch 18 = 537-591 | ch18 starts p537, doc ends p591 | ✓ |

"pp." in the stage rows means PDF viewer pages: every section claim below
matches the PDF outline page numbers exactly, so the two coordinate systems
agree.

## C-check — polars guide section+page claims (17 distinct claims, 15 with §titles)

Each claim verified two ways: (a) the outline places the section exactly in
the claimed span; (b) the section title string appears in the extracted text
of the claimed first page (ligature/quote-normalized).

| claim | outline start (next section) | title in page text |
|---|---|---|
| Ch 3 §Concepts to Unlearn pp. 83-92 | 83 (93) | p83 ✓ |
| Ch 3 §Syntax to Forget pp. 93-98 | 93 (99) | p93 ✓ |
| Ch 4 §Data Types pp. 105-109 | 105 (110) | ✓ |
| Ch 4 §Data Type Conversion pp. 117-120 | 117 (121) | ✓ |
| Ch 4 §Missing Values pp. 112-116 | 112 (117) | ✓ |
| Ch 6 §Parsing Missing Values Correctly pp. 149-151 | 149 (152) | p149 ✓ |
| Ch 8 §Operations for Missing or Infinite Values pp. 219-221 | 219 (222) | ✓ |
| Ch 10 §Selecting Columns pp. 281-283 | 281 (283) | ✓ |
| Ch 10 §Introducing Selectors pp. 283-284 | 283 (284) | p283 ✓ |
| Ch 10 §Selecting Based on Data Type pp. 287-289 | 287 (290) | ✓ |
| Ch 10 §Combining Selectors pp. 291-293 | 291 (294) | ✓ |
| Ch 11 §Filtering Rows pp. 308-312 | 308 (313) | ✓ |
| Ch 11 §Related Row Operations pp. 319-324 | 319 (325) | ✓ |
| Ch 7 §The Definition of an Expression pp. 186-193 | 186 (194) | p186 ✓ |
| Ch 7 §Properties of Expressions pp. 190-193 | 190 (194) | ✓ |
| Ch 8 §Types of Operations pp. 209-212 | 209 (213) | ✓ |
| Ch 9 §Boolean Algebra Operations pp. 264-265 | 264 (266) | ✓ |
| Ch 9 §When, Then, Otherwise pp. 274-275 | 274 (276) | p274 ✓ |
| Ch 13 §Row-Wise Aggregations pp. 387-389 | 387 (390) | p387 ✓ |
| Ch 14 §Join Strategies pp. 404-408 | 404 (409) | p404 ✓ |
| Ch 14 §Joining on Multiple Columns pp. 409-410 | 409 (410) | ✓ |
| Ch 14 §Validation pp. 410-411 | 410 (412) | ✓ |
| Ch 14 §Inexact Joining pp. 412-420 | 412 (421) | p412 ✓ |
| Ch 14 §Vertical and Horizontal Concatenation pp. 421-431 | 421 (432) | ✓ |
| Ch 15 §Pivot pp. 437-442 ("Pivot to Wider DataFrame") | 437 (443) | ✓ |
| Ch 15 §Unpivot pp. 443-445 ("Unpivot to Longer DataFrame") | 443 (446) | ✓ |
| Ch 17 §Applying a Function to Elements/Series/Groups/Expression pp. 504-512 | 504/507/508/511 (512) | p508 ✓ |
| Ch 18 §Arrow pp. 539-541 | 539 (542) | ✓ |
| Ch 18 §The String Data Type in Memory pp. 543-544 | 543 (544) | ✓ |
| Ch 18 §ChunkedArrays in Series pp. 544-545 | 544 (545) | p544 ✓ |
| Ch 18 §Query Optimization pp. 545-550 | 545 (551) | ✓ |
| Ch 18 §Checking Your Expressions pp. 551-555 | 551 (556) | ✓ |
| Ch 18 §Profiling Polars pp. 556-558 | 556 (559) | ✓ |
| Ch 18 §Tests → 'Comparing DataFrames and Series' pp. 559-561 | 559 (562) | p559 ✓ |
| Ch 18 §Common Anti-patterns pp. 562-564 | 562 (564) | p562 ✓ |

The route-s03 "fold section" claim (pages 387-390) is real: pages 387-390
carry 14 `Expr.fold()`/`Expr.reduce()` mentions (extracted text, e.g. p387
"the Polars API are the Expr.reduce() and Expr.fold() methods", p389 "Figure
13-1. How a fold function is executed"). Chapter-only locators ('Ch. 12',
'Ch. 13', 'Chs. 9, 13', 'Revisit Chs. 3, 5, 14, 17, 18…') all name chapters
that exist in the outline.

## C-check — pydata notebooks (polars + engineering-tools rows)

16 pydata-backed rows in polars, each §-quoted title searched (normalized,
case-insensitive) in the FULL text of the exact notebook the row's
`vault_path` names, then in all 15 local notebooks:

- 13 claims hit their own file: 'The Pandas Index Object' (03.01),
  'Data Indexing and Selection' (03.01→own), 'Data Selection in DataFrame'
  (03.02), 'Index alignment in DataFrame' (03.03), 'Specification of the
  Merge Key' + 'Overlapping Column Names: the suffixes keyword' +
  'Example: US States Data' (03.07), 'Duplicate indices' + 'Concatenation
  with joins' (03.06), 'Pivot Table Syntax' (03.09), 'Trade-Offs in Missing
  Data Conventions' + 'Missing Data in Pandas' (03.04), 'Pandas Objects'
  (03.01), 'When to Use These Functions' (03.12, in-text).
- **F2 (misattribution):** stage-polars-01 row claims §'Data Selection in
  Series' against "(notebook 03.01)" with vault_path 03.01; the heading is
  in 03.02 (`# Data Selection in Series`). 03.01's actual headings enumerated
  (Introducing Pandas Objects … The Pandas Index Object, Index as Immutable
  Array, Index as Ordered Set — no selection section).
- Two title paraphrases, content present (noise, not defects): 03.03 local
  heading is `# Ufuncs: Operations Between DataFrames and Series` (row says
  'Operations between DataFrame and Series'); 03.12 local headings are
  `# pandas.eval for Efficient Operations` and `# The DataFrame.query Method`
  (row says 'pandas.eval() Function' and 'DataFrame.query() Method').
- engineering-tools: 'IPython shell-command notebook' →
  01.05-IPython-And-Shell-Commands.ipynb exists with matching heading ✓.

## C-check — ProGit (module-job-git)

Outline (123 entries) + page-text heading checks, all ✓ on the named pages:
Recording Changes p34 (2.2), Viewing the Commit History p46 (2.3), Undoing
Things p52 (2.4), Working with Remotes p56 (2.5), Tagging p61 (2.6), Branches
in a Nutshell p69 (3.1), Basic Branching p76 (3.2), Branch Management p85
(3.3), Remote Branches p91 (3.5), Rebasing p101 (3.6), Distributed Workflows
p132 (5.1), Contributing p135 (5.2), Maintaining p156 (5.3), Account Setup
p172 / Contributing p177 (6.1/6.2), Revision Selection p224 (7.1), Interactive
Staging p232 (7.2), Stashing and Cleaning p236 (7.3), Searching p245 (7.5),
Rewriting History p249 (7.6), Reset Demystified p257 (7.7), Advanced Merging
p277 (7.8), Debugging with Git p301 (7.10), Submodules p304 (7.11), Replace
p328 (7.13), Credential Storage p336 (7.14), Git Configuration p342 (8.1),
Git Attributes p352 (8.2), Git Hooks p360 (8.3), Plumbing and Porcelain p420
(10.1), Git Objects p421 (10.2), Git References p431 (10.3), Packfiles p435
(10.4), Maintenance and Data Recovery p446 (10.7).

**F1 (worktree):** regex `[Ww]orktree` over the whole 501-page PDF hits only
pp. 453 and 457, both incidental ("--work-tree, GIT_WORK_TREE or
core.worktree" env docs; "setup: worktree: /Users/ben/src/git" trace output).
Chapter 7 (pp224-341): **zero** mentions. So "Pro Git worktrees and
submodules Chs. 7.11, 7.13" (stage-git-15) names no worktree content; 7.11 =
Submodules, 7.13 = Replace. The stage's worktree need is otherwise covered
('MIT advanced Git worktree pointer', 'git-worktree and submodule model'
official-docs rows, both present in the stage).

git-handbook: index.html says "the 4 regions in one mental picture" with
WT/IDX/Open Local/Open Remote — 'Four-region visual map' locator ✓. The four
rows sharing the group label 'Stage/unstage/discard/rename pages' are four
DIFFERENT files (idx-stage, idx-unstage, wt-discard-unstaged,
wt-rename-delete) on one stage — a label for a page group, not duplicates.
HU-intro-to-git.pdf (26 pp): branch/remote/staging/index/commit/merge/clone/
push/pull all present in extracted text (worktree absent — no HU row claims
it).

## C-check — Rust book (module-job-rust-engineering)

`The-Rust-Programming-Language_print.html`, 112 h1 headings; chapter numbers
follow heading order: 1 Getting Started, 2 Programming a Guessing Game, 3
Common Programming Concepts, 4 Understanding Ownership (4.1 What is
Ownership?, 4.2 References and Borrowing, 4.3 The Slice Type), 5 Structs, 6
Enums and Pattern Matching, 7 Packages Crates and Modules, 8 Common
Collections, 9 Error Handling, 10 Generic Types Traits and Lifetimes (10.1
Generic Data Types, 10.2 Defining Shared Behavior with Traits, 10.3 Validating
References with Lifetimes), 11 Writing Automated Tests, 12 I/O Project, 13
Functional Language Features: Iterators and Closures, 14 More About Cargo and
Crates.io, 15 Smart Pointers, 16 Fearless Concurrency, 17 Fundamentals of
Asynchronous Programming: Async, Await, Futures, and Streams.

All 17 chapter/section claims in the module's locators match this structure,
including the two fine-grained ones verified inside the HTML body: 'Making
Useful Documentation Comments' (h3) sits between the h1s of §14.2 Publishing
a Crate to Crates.io and §14.3 Cargo Workspaces (byte offsets 982107 <
983068 < 1010504), so 'Chapter 11 and Chapter 14.2 — Tests and Documentation'
✓; 'Chapter 7 and Chapter 14.1–14.3' spans Release Profiles → Publishing →
Cargo Workspaces, and the workspaces material (14.3) is inside the claimed
span ✓. Ch 17's claim title 'Async and Await' is a short form of the actual
h1; content match ✓.

## C-check — papers and external docs (URL rows)

- arXiv 2603.03589 (8 pp, downloaded to /tmp/papers): §3 OUR VISION starts
  p3, §4 SYSTEM ARCHITECTURE p4, §4.1-4.2 p4, §4.3 Runtime Optimizations p5
  → "Sections 3 to 4.3 … pdf pp. 3-5" ✓; §5 CHALLENGES AND KEY DIRECTIONS
  starts p5, §6 starts p6 → "Section 5 … pdf pp. 5-6" ✓.
- SIGMOD'15 Spark SQL (12 pp, downloaded): §4 Catalyst Optimizer heading at
  the bottom of p4; §4.1 Trees p5, §4.2 Rules p5, §4.3 p5-6, §4.4 Extension
  Points p7 (+4.4.1/4.4.2 p7, ends before §5 on p8) → "Section 4 Catalyst
  Optimizer, 4.1 Trees through 4.4 Extension Points, pdf pp. 5-8" ✓.
- pandas user guide (fetched 2026-10-24, docs for pandas 3.1.x):
  indexing.html still has 'Boolean indexing' ✓ and 'Reindexing' (subsection)
  ✓. **Stale headings:** merging.html no longer has 'Brief primer on merge
  methods' (now 'Merge types') nor 'Checking for duplicate keys' (now 'Merge
  key uniqueness'); reshaping.html no longer has 'Reshaping by melt' (now
  'melt() and wide_to_long()') nor 'Pivot tables' (now 'pivot() and
  pivot_table()'); basics.html no longer has 'Nullable integer data type' /
  'Nullable Boolean data type' as headings at all (they moved to separate
  pages integer_na.html / boolean.html, only sidebar links remain). Content
  survives under the renamed headings — external drift, not internal damage.
- docs.pola.rs/user-guide/expressions/casting/: page exists, covers strict vs
  non-strict casting and overflow ✓.
- kernel.org FUSE: live row URL `…/filesystems/fuse/fuse` → **404**; the
  legacy-plan URL `…/filesystems/fuse.html` → **404**; current doc at
  `…/filesystems/fuse/index.html` → 200. The migration edited the URL but
  still landed on a dead page (stage-missing-semester-18, kind reference).

## C-check — polars session artifacts

SHELF.md contains '3a' + 'Testing' and '3c' + 'Performance' ✓ (routes s09/s10
claims); stage-8-interfaces-and-dispatch.md contains Q8.10 and Q8.11 ✓.
Pandas_cheatsheet.pdf (2 pp): all nine claimed panel titles present across
pp1-2 (creating DataFrames, tidy data, method chaining, subset observations,
subset variables, handling missing data, summarize data, combine data sets,
reshaping) ✓.

## D-check — duplicates

Sibling routes of one (unit, source_id) group: **no duplicate locators, no
duplicate angle_details, no unit with two routes from one source** (29 routes,
10 polars units, 6 sources). Identical locators across DIFFERENT units are by
design (stratum-paper route repeated on 4 units; scalable-dataframe on 3;
python-depth-drills s09/s10 pair) — not sibling duplicates.

Stage rows repeated within one (unit, source) group: template rows by design
— 'Exercise 1'-'Exercise 5' × 16 (git) and × 20 (engineering-tools); 'The
matching phase and step in the canonical Rust roadmap' × 19 (one per rust
stage, pointing at the per-stage step of the roadmap note); 'Complete guide
retained from the original monolithic plan' × 16 and 'Complete note' × 5
(polars). The only same-source repeated locator on one stage is the
git-handbook page-group label (four distinct files, see above). Nothing here
resembles the September (source_id, unit_id) broadcast.

## Validator warnings (695, all RESOURCE-SCOPE-UNBOUND)

Per module: engineering-tools 183, polars 212, git 168, python-engineering
67, rust-engineering 65. By reason: no-source 556 (row has no source_id —
template exercise rows, url-only reference/practise rows, knowledge-note
rows); no-disposition 101 (source declared in the module source-map, unit
records no disposition and no route matches: git 59, eng-tools 12, python 15,
rust 15); disposition-but-no-route 38 (all polars).

The 38 polars rows: every non-reference row carrying a source_id and a
vault_path (38 `read` rows), whose section-granularity locator (e.g. 'Ch.
13', "§'Index alignment in DataFrame' and §'Operations between DataFrame and
Series' (notebook 03.03)") differs from the unit route's chapter-range
locator (e.g. 'Chapter 13, PDF viewer pages 369-402'), so no (unit, source,
locator) route pair matches. Shape = binding debt (critique point 1), same
pattern the AML and M2 sessions found. One polars `practise` URL row
(resource-polars-01-book-repo, github.com book repo) has the same mismatch
shape but is not warned — the validator scope-checks rows that name local
material; ASSUMPTION: that is the intended filter (plan_rigor.py
_check_row_scope is reached only for material-bearing rows).

## Provenance

Git: each of the five module trees has exactly **one commit** — the initial
clean snapshot `1d32c918` (2026-10-19). Nothing inside the five modules was
modified after the snapshot, so no post-snapshot pass could have overwritten
anything; every shape below predates it.

- **module-job-git / -rust-engineering / -engineering-tools:** live
  study-maps are faithful migrations of `LearningOS/legacy/Job/plans/
  job-track-{git,rust,missing-semester}.yaml` (provenance
  `migrated-mini-plan`): same stage ids (16/19/20), same resource ids, zero
  field diffs except: one URL + label edit (FUSE row, see above) and one
  locator punctuation edit in rust ('—' vs ':'). Legacy vault paths
  (`LearningOS/materials/software/…`) were rewritten to id-based
  `material://` form.
- **module-job-python-engineering:** legacy job-track-python.yaml has 20
  stages; the live map has 10 (5 kept: 14-18; 15 dropped: mechanisms 01-13,
  19, 20; 5 new: 00-mechanism-diagnostic, repair-mechanism-gaps,
  optimizer-theory-and-rewrite-soundness, rewriter-tests-and-benchmark-
  evidence, contribution-loop). Shared stages carry identical resource ids
  and fields. Residue: 15 stage note directories for the dropped legacy
  stages remain on disk with well-formed working notes (no map entry, no
  row references them). Deliberate compression, not damage.
- **module-job-polars:** authored through
  `work/active/workspace-job-polars-plan/outputs/`. The operator package
  `polars-backend-session-migration.yaml`'s source_map (all 29 routes) is
  content-identical to live. Of the 10 unit study maps: 3 units
  (order-text-time, aggregation-windows, capstone-transition) match the
  package except the backfill-added `knowledge_node_id`; 6 units match the
  session's `map-drafts/` (the enriched successor of the package) except
  `knowledge_node_id`; backend-loop matches the package except
  `knowledge_node_id` plus 3 rows converted to `material_ref.route_id`
  binding with `angle_review` stamps ("refinement", "Codex under Aram
  cleanup authorization", 2026-09-30) — the same authorized route-binding
  pass pattern the AML session found (09-07 compact), plus the 09-20
  node-linkage backfill. Exercise-sheet attachments live in
  `outputs/exercise-sheets/` (s01…s8c + u1/u2 with check scripts). The
  suspect polars locators (F2) already appear verbatim in the map-drafts —
  original design of that session.

## Assumptions

- The pandas user-guide and kernel.org fetches reflect the sites as of
  2026-10-24; the pages are living documents.
- plan_rigor.py's exact row-filter for scope checks (why one practise URL
  row is not warned) was inferred from counts, not read line-by-line.
- ProGit/Rust section NUMBERS are canonical (the local artifacts carry no
  section numbers in their bookmarks); number→title mapping verified via
  heading order (Rust) and outline heading text (ProGit), with the TOC text
  of ProGit p3 lacking extractable numbers.
