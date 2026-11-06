# Relational delegation — Stage 2 pilot design (2026-11-06)

Status: design-on-paper deliverable on branch
`research/relational-delegation-2026-11-06`. Per Stop gate 1's autonomous
clause ("proceed to Stage 2 *design only* … not to implementation"), no
prototype code was written; every arm below is a complete accounting, and the
numbers for arms (b)/(c) are labelled ESTIMATE with their derivation basis.
This is the final stop (Stop gate 2): Stage 3+ requires a separate assignment.
Companion document: `workbench/relational-delegation-inventory-2026-11-06.md`
(Stage 1 evidence; referenced as D1 below — not duplicated here).

---

## 1. The candidate and the slice boundary

Stage 1 ranked **reference validation (K1)** first. Slice: `tools/learning_os/
derive/validation/references.py` (672 L, 90 sites) — `check_references`,
`check_solution_exposure`, `check_links`/`_check_link`, `_check_uri`, and the
F0 shared parsers. Out of the slice, in every arm: `registries.py` (251 L;
REL-DUP/REL-TYPE/cycle/collection families — a later candidate), the schema
layer (`structure.py`, unchanged), the emit helpers and
`id_list_items`/`list_items` (`core.py`, `domain/validation.py` — consumed
identically by all arms, so they cancel out of every comparison).

Why this slice despite a likely non-SQL outcome: the brief requires the
database to beat the *table-driven refactor*, not the status quo (A5); the
three-arm comparison is the instrument that decides, so the strongest
candidate must be run through it honestly.

## 2. Arm (a) — current implementation (baseline and parity oracle)

Counted (D1 §3): 672 L = 223 extraction + 257 diagnostic + 192 control flow,
comments, docstrings. Output order is authored iteration order: dict
insertion order (= load order) for entity walks; `enumerate` ordinal for
relations; explicit `sorted()` where authored (route-duplicate owners 83–86,
sorted route loop 80, child-title keys 538). The recorded scenario outputs pin
diagnostic sequences. Twelve duplicated-responsibility sites (D1 §5), four
implementations of the route-guard invariant among them.

## 3. Arm (b) — table-driven Python refactor (the null hypothesis)

Design, complete accounting:

- **Spec registry.** One row per spec-driven site (53 sites: the 50 strict
  membership sites + 3 dual-container sites from D1 §3/A3), with the row
  grammar `(container, field_path, target_family, alt_container?, falsy ∈
  {skip-falsy, required, normalize-then-error}, scope ∈ {none, current-map,
  pointed-map, routed-unit, own-module}, code, severity, template_id)`.
  ≈ 130 L of declarative rows (ESTIMATE; 53 rows × ~2.5 L).
- **Generic engine.** ≈ 100 L: walk container → extract via the *existing*
  `id_list_items`/`list_items` (byte-identical malformed semantics, §6.3) →
  resolve scope set → evaluate membership → emit through the template layer.
  Includes the owner-equality spec kind (UNIT-OWNER/MAP-OWNER/
  SOURCE-MAP-OWNER/PATH-OWNER, 6 sites).
- **Route-guard helper.** One function ≈ 35 L + ~30 L of rows replacing the
  four guard implementations (`references.py:118-138, 316-337, 441-456` and
  `derive/routes.py:64-88`); the family asymmetry (study-map resources carry
  no locator guard) is a row flag.
- **Stage-membership helper.** ≈ 12 L replacing the two copies (295–298, 471).
- **Template layer.** ≈ 100–120 L: per-code template functions producing the
  *exact* current message text (the parity obligation); no message changes.
- **Hand-written stays** (≈ 370 L, unchanged in character): F0 parsers, F1
  route identity, F1b solution exposure, F2's traversal/cardinality half, F6's
  working-note containment + legacy-selection warn, F7 polymorphic route
  extraction, F13 regex prose mining, F14 scheme dispatch + filesystem,
  F15 links, and the policy-annotated F11 checks.
- **Tests added:** a registry-totality test (every spec's container/path
  resolves against the schema; every template id has an implementation),
  plus the shared parity harness (§6).

**Ledger-relevant estimate (single reconciled bottom-up derivation).** Arm (b)
keeps what no spec drives — complex-family code (extraction ≈103 L +
diagnostics ≈131 L at the same per-family split basis as D1 §3) plus control
flow/comments/docstrings ≈192 L — and collapses the duplicated invariants
(guard blocks ≈ −84 L replaced by a 35 L helper + 30 L rows; stage-membership
−10 L + 12 L helper; ownership −8 L into the engine; dual-container −4 L into
a spec field), then adds the declarative layer: spec rows ≈130 L + engine
≈100 L + templates ≈110 L. **Net ≈ 700–780 L ESTIMATE (baseline +30…+110)**;
`routes.py` sheds its fourth guard copy (−25 L). The increase is the price of
the declarative layer and is justified — if at all — by dimension 2 (one
implementation per invariant) and dimension 3 (change propagation), never by
line count (§9 of the brief).

## 4. Arm (c) — in-memory SQLite, Role A (complete accounting)

Stdlib `sqlite3` only; database exists for one operation, then discarded.

- **Exporter.** Consumes the memoized `Repo` from `ReadSession.repository()` /
  `OpContext.repo()` — never a second parse (D1 §K7). Per-family extraction is
  table-driven (the same spec rows as arm (b) drive INSERT generation), with
  hand-written producers for the route/scoped families. Captures, per row:
  `origin_path`, occurrence `ordinal` (relations, stages, route lists),
  `scope_kind`/`scope_id` where scoped, polymorphic alternatives as per-type
  nullable columns, guard columns (`unit_id`, `source_id`, `locator`) on
  route-consuming rows. Replicates `id_list_items`/`list_items` semantics
  exactly (non-list → zero rows; schema layer owns shape errors upstream).
  ≈ 120 L loop + rows (ESTIMATE).
- **Schema.** ≈ 20 per-family tables (notes, workspaces, units, modules,
  module_source_maps, routes, study_maps, stages, knowledge_nodes, concepts,
  sources, topics, thematic_groups, programs, projects, relations,
  unit_material_syntheses (+assessments), selections, resources,
  learning_paths (+stages)), DDL ≈ 130 L (ESTIMATE). **No foreign keys and no
  uniqueness constraints on ids** (§6.1: duplicates must survive as rows;
  malformed references load and report completely). A generic
  `entities`/`references` mega-abstraction was tested against the §6.6 list
  and **does not fit** (guard columns, ordinals, scoped and polymorphic
  targets differ per family) — that is a finding, per the brief: the families
  resist generalization exactly where they carry guard/routing semantics.
- **Queries.** ≈ 80 L: parameterized anti-join membership queries per
  (source family × target family) pair; exactly-one resolution via
  `GROUP BY route_id HAVING COUNT(*) != 1` with the four distinct message
  families (110, 349, 308/433, 87); guard comparisons as join + column
  compare; every user-visible result `ORDER BY source_ordinal,
  occurrence_ordinal` to reproduce the authored sequence.
- **Diagnostic mapping.** Query rows → `(code, template_id, params, path)` →
  the *same* template layer as arm (b) (≈ 110 L, shared).
- **Fail-closed machinery.** ≈ 50 L: model construction runs to completion
  from the admitted snapshot or the operation refuses naming why; one
  exception boundary converts `sqlite3.Error` into a structured diagnostic
  (never a skip); a completeness assertion verifies every registered family
  table was populated before any query result is treated as authoritative.
- **Determinism rules.** TEXT comparisons under the default BINARY collation
  (exact codepoint, matching Python `==` on NFC YAML strings); `NOCASE` and
  `LIKE` forbidden; no reliance on rowid iteration order for user-visible
  output — the ordinal columns are the authority.
- **Tests added:** schema/exporter unit tests, determinism tests
  (collation/ordering), the completeness/refusal paths — ≈ +15–25 cases over
  the shared corpus.

**Ledger-relevant estimate (structurally derived from arm (b)).** Arm (c) is
arm (b) with the Python engine replaced by persistence machinery: stays
≈ 330–350 L (complex code minus the guard/membership/ownership blocks that
become queries) + spec rows ≈130 L (exporter extraction) + exporter loop
≈120 L + DDL ≈130 L + queries ≈80 L + fail-closed boundary ≈50 L + templates
≈110 L. **Net ≈ 950–1030 L ESTIMATE (baseline +280…+360; ≈ arm (b) +250…+290).**

## 5. The complexity ledger (§9 of the brief)

Counted for arm (a); ESTIMATE ranges (derivation above) for (b)/(c), to be
replaced by spike measurements if the reviewer authorizes a Stage-2.5 spike.

| Dimension | (a) current | (b) refactor | (c) in-memory SQLite |
|---|---|---|---|
| 1 Bespoke implementation | **672 L** counted | ≈ 700–780 L ESTIMATE (+30…+110) | ≈ 950–1030 L ESTIMATE (+280…+360) |
| 2 Duplicated responsibility | 12 sites; guard invariant ×4; stage-membership ×2; dual-container ×2 | each invariant collapses to one implementation; **no new *code* duplication** — the spec registry is a declarative restatement of schema facts (the residual judgment call is Risk 2) | same collapses in SQL, **plus** record shapes declared a third time (JSON schema + SQL DDL + exporter mapping) |
| 3 Change propagation (one new note id-list field) | 3–4 places | **2 places** (schema + spec row) | 4–5 places (schema + spec row + DDL + exporter + query set) |
| 4 Failure modes owned | today's (crash containment exists) | fewer bug sites, no new class | **new classes**: build-failure refusal path, SQL-exception mapping, silent-skip risk needing a completeness assertion; SQLite delegates nothing the Python arms own (everything is ephemeral) |
| 5 Verification burden | recorded scenarios | shared parity/mutation corpus + registry-totality test | same corpus **+** schema/exporter/determinism/refusal tests (+15–25 cases) |
| 6 Operational overhead | none new | none new (stdlib only) | stdlib `sqlite3` (no new dependency) **but** SQL as a second language in the codebase and an in-memory build cost per validation run (unmeasured; S23 warns the loader already dominates cold runs) |

No dimension is won by (c) that (b) does not already win, and (c) loses
dimension 1, 2, 3, 4 and 5 outright. The unavoidable reason: Role A is
ephemeral, so the engine's transactional/constraint/durability strengths — the
only things that justify a database — have nothing here to own.

## 6. Parity and mutation test strategy (identical for arms b and c)

- **Oracle:** arm (a) output; recorded scenario outputs already pin sequences.
- **Harness:** run both arms over the mutation corpus; assert exact *ordered*
  equality of the issue list — severity, code, message text, attributed path,
  position (set comparison is insufficient, §6.2).
- **Mutation corpus, per family** (each mutation on a disposable scratch copy,
  following the `$TMPDIR` scratch pattern of `benchmark_projection.py`; never
  the live tree):
  1. unknown target ids, one per target family (concept, note, source, unit,
     module, program, project, workspace, stage, route, thematic group, topic);
  2. duplicate route id across two source maps; duplicate registry id
     (loader-level `ID-DUP` interaction);
  3. guard drift: `source_id`, `locator`, `unit_id` on a synthesis assessment,
     a unit selection, and a study-map resource (three families, one
     asymmetry: the resource locator guard must stay absent);
  4. self-edges: `REL-SELF`, `REF-ANSWER-NOTE` self, `ROUTE-SOLUTION-SELF`;
  5. quarantined-workspace context (F3/F14 dual container) and archived
     workspace `COORD-DEP`;
  6. malformed shapes: scalar/mapping `workspace_ids` (schema error only —
     **zero** per-character REF-WORKSPACE errors), non-str list items,
     non-dict assessments/groups (silently skipped);
  7. falsy/empty pointers (optional pointers skip; learning-path `workspace_id`
     must error; relation missing endpoint normalizes to `""` and errors);
  8. scoped misses: `covers` naming a node of another unit, selection stage not
     in the current map, component of another module, resume stage not in the
     pointed map;
  9. polymorphic legs: `relation.source` as note vs source, artifacts scalar
     vs list, `unit_routes` string vs dict;
  10. ordinal ordering: two broken relations — relative diagnostic order pinned;
  11. filesystem: broken internal link, repo-escaping link, missing working
     note, unmounted materials tree (URI-MATERIAL suppressed per-reference,
     reported once by `check_materials`);
  12. resume-pointer chain (each hop named separately).
- The corpus and harness live in the Stage-2.5 spike (`/tmp` or a labelled
  `workbench/` spike directory) until Stage 3 moves them under `tests/`.

## 7. Failure-contract compliance (§6 of the brief), itemized

| Contract | Arm (b) | Arm (c) as designed |
|---|---|---|
| 1 Complete diagnostics, no FK termination | no database layer exists; same helpers; nothing terminates early | no FK/PK constraints; duplicates preserved as rows; queries return complete result sets; `sqlite3.Error` mapped to a structured diagnostic, never a skip |
| 2 Exact parity, ordered | authored iteration order untouched; template layer byte-exact | ordinal columns + explicit `ORDER BY source_ordinal, occurrence_ordinal`; shared template layer |
| 3 Malformed-input semantics | `id_list_items`/`list_items` reused verbatim | exporter replicates their semantics exactly; non-list → zero rows; schema layer owns shape errors, unchanged upstream |
| 4 Fail-closed semantics | n/a (no database) | construction completes from the admitted snapshot or the operation refuses naming why; completeness assertion before any result is authoritative. Role B (design only): versioned schema + snapshot identity verified on open; corrupt/mismatched → rebuild-or-refuse; atomic publication build-to-temp/rename/verify — specified in D1 §8 (Q4), never built here; the derived-store "corrupt cache is a miss" doctrine is **not** imported |
| 5 Snapshot consistency | unchanged (same `Repo` discipline) | Role A makes this nearly free and it is stated: the model is built from one memoized `Repo` under `ReadSession`; no second snapshot can intervene mid-build |
| 6 Reference-graph fidelity | preserved by construction (no model) | carried by per-family tables: origin paths, ordinals, scope kind/id, polymorphic per-type columns, guard columns, per-family falsy semantics; the generic abstraction was tried and rejected — a finding |
| 7 Determinism | unchanged Python semantics | BINARY collation (= exact codepoint); `NOCASE`/`LIKE` forbidden; explicit ordering everywhere; no rowid-order dependence |

## 8. Expected-deletion list for a future Stage 4 (if arm (b) is adopted)

Named file-by-file (line ranges at `60da966`):

1. `references.py:118-138`, `316-337`, `441-456` — three guard blocks → one
   route-guard helper (+ rows).
2. `derive/routes.py:64-88` — legacy `exact_selection_matches` rewritten on
   the same helper (fourth copy eliminated).
3. `references.py:295-298`, `471` — two stage-membership constructions → one
   helper.
4. `references.py:183-184`, `598` — dual-container membership → spec
   `alt_container` field.
5. Ownership-equality sites `243-244`, `262-265`, `385`, `389`, `423`, `482`
   → owner-equality spec kind.

Estimated net ≈ −60…−90 L within the slice and **one implementation per
invariant**. Contract-level regression tests (recorded scenarios, the mutation
corpus) are retained, not deleted. If the reviewer instead adopts arm (c)
(against this document's recommendation), the same blocks delete *plus* the
membership loops, offset by DDL/exporter/query machinery — shown in the
ledger, not recommended.

## 9. Risks

1. **Parity drift** (most likely failure): 53 template rewrites must be
   byte-exact. Mitigation: the ordered-parity harness over the mutation corpus;
   any drift is a test failure, not a silent behavior change.
2. **A4 realized in arm (b)**: spec rows cost ≈ what the extraction they
   replaces cost (measured ≈1:1 in §3). The refactor's value is invariant
   dedup and change propagation, not line count. If a reviewer judges the spec
   registry itself to be a second implementation of the schemas, the honest
   fallback is to leave `references.py` unchanged: the status quo is
   defensible, and this document then records NO-GO for *any* change in this
   slice.
3. **Arm (c) performance** (only if pursued): in-memory build cost per
   validation run is unmeasured; S23 (D1 §K7) warns the loader already
   dominates cold runs, so an exporter adds post-load work on every run.
4. **Scope creep**: `registries.py` families (cycles, REL-DUP, collections)
   are adjacent and tempting; they are outside the slice boundary.
5. **Bundling**: B1/B3 repairs must stay a separate assignment (brief §3.3).

## 10. Recommendation

- **NO-GO — in-memory SQLite (and DuckDB) for the reference-validation
  slice.** The null-hypothesis arm (b) captures the available value (one
  implementation per invariant, 2-place change propagation) at lower bespoke
  cost than the SQL arm on every ledger dimension, at the price of a modest
  net line increase (+30…+110 ESTIMATE) justified only by the named
  dimension-2/3 wins — exactly the trade §9 of the brief permits; if the
  reviewer judges those wins insufficient, the fallback is no change at all
  (Risk 2). The ephemeral role gives SQLite no invariant to own.
- **GO-WITH-DIFFERENT-SLICE — the SQL program proceeds elsewhere**, in this
  order, each through its own pilot gates and separate assignments:
  1. **Role B: derived-state persistence** (`store/derived/store.py` + engine
     plumbing) — the strongest evidenced net-deletion case in the repository
     (D1 §8/Q4: ≈ −295 L deleted, counted from existing spans; ≈ +131 L new
     machinery, ESTIMATE; net ≈ −160 L ESTIMATE, range −110…−195; concentrated
     in hand-reasoned invariant machinery; corruption→miss becomes
     rebuild-or-refuse).
  2. **Role A: lineage read-side graph queries** (Stage 6), under the Q2
     condition "replace the queries, expose the ledger" (D1 §8): ≈200 L of
     BFS/topo/cycle machinery delegable; ledger, admission binding and
     gateway minting stay; it must beat its own refactor null arm.
- **DuckDB: no arm.** No named analytical/transformation property of this
  workload (nested JSON-ish records, no bulk columnar scans, no ledger-history
  analytics in the slice) deletes code the other arms cannot; nothing installed.

**Evidence that would change the NO-GO:** (i) a spike-measured ledger where
arm (c) beats arm (b) on dimension 1 while naming a dimensions-2–4 win unique
to SQL; (ii) a family whose exactly-one/cardinality message semantics resist
the table-driven helper (making (b) infeasible where a relational formulation
is not); (iii) a new requirement for cross-family joins over the whole snapshot
per operation (none found in Stage 1). **Evidence that would change the
GO-WITH-DIFFERENT-SLICE:** a failed parity/mutation demonstration on the
derived-store slice (rebuild-or-refuse not reproducible within the charged
line budget), or the reviewer rejecting the Q4 line accounting.

## 11. Performance constraint record (per §9 of the brief)

Unmeasured by design (no spike under the autonomous clause). Arm (a)'s
baseline numbers are producible today without any prototype code — both
harnesses are existing scripts; they need a `.venv`, which this task did not
create — and are recorded here as the spike's first deliverable rather than
run under the design-only clause. Harness named:
`tests/benchmark_projection.py` (named `seconds.load` /
`seconds.validate_loaded_repo` phases, mutation corpus on a scratch copy) and
`tests/benchmark_runtime.py` (named phases + an existing arm mechanism a SQL
arm could mirror). Cold/warm wall time on the live corpus; no material
regression permitted; the Stage 3 gate bound is the reviewer's to set from
spike numbers. Speed is not, and never becomes, the justification.

## 12. Verification and honesty notes

Counted in this document: all arm-(a) figures (from D1, re-verified during
synthesis: `wc -l`, 90 emit sites, gate samples). Everything marked ESTIMATE
(arms b/c line figures) is a design-stage derivation from those counted
figures — reproducible arithmetic, not measurement — and the spike plan (§6
corpus + harness, §11 benchmark arms) is specified so a Stage-2.5 spike can
replace the ranges with numbers before any Stage 3 gate. Nothing was executed;
no production file under `tools/` was touched; the only changes on this branch
are the two workbench deliverables.

An independent read-only review pass (2026-11-06) verified ~20 file:line
pointers and every counted figure; its findings are incorporated: the Role-B
addition side is labelled ESTIMATE in both documents, the arm-(b)/(c)
estimates were reconciled into single bottom-up derivations (the earlier
delta-style derivation double-counted the declarative layer's savings), the
dim-2 cell for arm (b) is reconciled with Risk 2, and D1's per-family counting
method is now a runnable Appendix command.

**What the reviewer is asked to decide:** (1) the Stage 1 ranking and the two
argued rejections (manifest projection, semantic predicates); (2) whether to
authorize a Stage-2.5 throwaway spike (arm (b) prototype + parity harness in
`/tmp`) to produce measured ledger numbers; (3) the next slice for a separate
assignment (Role B derived-store vs lineage Role A). Per Stop gate 2, no
further work happens without that assignment.

## Appendix — reproduction

```
cd /Users/aramaljanadi/los-sql-2026-11-06/repository
git log --oneline main..HEAD        # the two workbench deliverable commits
git status --porcelain              # clean except labelled spike, if any
sed -n '118,138p;316,337p;441,456p' tools/learning_os/derive/validation/references.py
sed -n '64,88p' tools/learning_os/derive/routes.py
rg -n "self\.(err|warn)\(" tools/learning_os/derive/validation/references.py | wc -l  # 90
# ESTIMATE derivations: arithmetic over D1 §3 per-family diag/extract counts;
# every input number reproduces from D1 Appendix A.
```
