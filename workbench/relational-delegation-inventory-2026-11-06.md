# Relational delegation — Stage 1 complexity inventory (2026-11-06)

Status: research deliverable on branch `research/relational-delegation-2026-11-06`
(base `main @ 60da966`). This document records measured findings and a ranking.
It proposes no production change and edits nothing outside `workbench/`.
Classification vocabulary: **relational-structural** (SQL candidate) /
**procedural-policy** (stays Python) / **diagnostic-formatting** (stays Python).

---

## 1. Understanding and method

The assignment asks which of LearningOS's custom relational bookkeeping could be
delegated to a mature embedded SQL engine — proven by evidence, with the real
objective being *retiring* Python machinery, not adding a parallel
implementation. This inventory measures all seven candidate subsystems, ranks
them by realistic net simplification, and answers the four open questions Q1–Q4.

Method: five parallel read-only investigations (one per slice) over the isolated
clone, each producing counted, command-reproducible numbers; then a synthesis
verification pass (§11) that re-ran the load-bearing commands. Counting
conventions:

- Line counts are `wc -l`. Diagnostic lines are the lines covered by
  `self.err(`/`self.warn(` call expressions, measured exactly with the
  stdlib `ast` module (`Call.lineno`–`Call.end_lineno`; the full runnable
  command and its output are in Appendix A). Extraction lines are lines
  outside those spans matching the extraction regex stated in Appendix A.
  The diag column is exact and machine-reproduced; the extract column is
  method-stated and reproduces within ±4 lines total (the boundary sits in
  three families' classifier). Emit sites and totals were independently
  re-verified (§11).
- Emit sites are `rg -n "self\.(err|warn)\(" <file> | wc -l`.
- Every counted number in this document is reproducible from a command stated
  here or in Appendix A. One figure is a design-stage estimate and is labelled
  as such wherever it appears: the Role-B *addition* side in §8/Q4 (machinery
  that would be written, not machinery that exists).

## 2. The candidates and their measured size

| # | Candidate | Files (wc -l, verified) | Role in the system |
|---|---|---|---|
| K1 | Reference validation | `derive/validation/references.py` **672**, `derive/validation/registries.py` **251** (adjacent) | every cross-record id/URI/link resolves |
| K2 | Semantic predicates | `derive/semantics/predicates.py` **949** | 27 registered judgment functions behind the semantic surface |
| K3 | Lineage / dependency analysis | `derive/semantics/lineage.py` **892** | claim assumptions, staleness, retraction, traversal over `operations/transactions/lineage.yaml` |
| K4 | Manifest projection | `derive/projection/manifest.py` **462** | atomic v2 manifest assembly (producer-owned published contract) |
| K5 | Derived-state bookkeeping | `store/derived/{engine 333, identity 398, model 122, store 308, __init__ 90}` = **1,251** | content-addressed disposable cache under `generated/derived-state/` |
| K6 | Ledger/receipt reconciliation | `store/evidence.py` **579**, `store/revisions.py` **74**, `store/session_ledger.py` **667** | committed-write evidence, revision counters, session write windows |
| K7 | Loading / snapshot | `store/loading/__init__.py` **124**, `domain/snapshot.py` **231** | the single full-model walk; `Repo` with `duplicate_ids` / `parse_failures` |

All seven brief line-count claims verified exactly. Corpus facts: 380 receipts
in `operations/transactions/` (65 × schema_version 1, 315 × v2); `revisions.yaml`
448 artifact rows; `lineage.yaml` 12,090 lines (not read in this inventory —
owner analysis done via `lineage.py` instead).

## 3. K1 reference validation — per-family counts and classification

90 diagnostic sites (86 `err` / 4 `warn`) through `core.py:70-75` helpers into
`Issue(severity, code, message, path)` (`domain/validation.py:274-283`).
Totals: **257/672 lines (38%) build diagnostics** (exact, reproduced by the
Appendix A command); **≈220/672 (33%) locate/normalize references** (219 by
the published command; 223 by the slice's classifier variant — the ±4 is a
classification boundary in three families); the remainder ≈195 is control
flow, comments, docstrings. The per-family extract values below come from the
slice's classifier; the Appendix command reproduces the diag column exactly.

| Family (lines) | Sites | diag | extract | Classification (evidence) |
|---|---|---|---|---|
| F0 shared parsers (19–60) | 0 | 0 | 7 | extraction (pure parsing) |
| F1 route identity (65–93) | 2 | 13 | 6 | duplicate detection relational-structural; v13 migration advisory procedural-policy |
| F1b solution exposure (613–642) | 2 | 12 | 5 | relational-structural (self-edge + dangling FK) |
| F2 material synthesis (94–173) | 9 | 54 | 20 | memberships + exactly-one resolution + guard trio relational-structural; message formatting stays |
| F3 note frontmatter (174–200) | 6 | 8 | 18 | memberships relational-structural; evidence scheme gate procedural |
| F4 workspace frontmatter (201–224) | 7 | 8 | 16 | relational-structural, pure — the most SQL-suited family (7/7 plain membership) |
| F5 module manifest (225–258) | 7 | 13 | 16 | memberships + UNIT-OWNER relational-structural; component set scoped per module |
| F6 unit payload (259–385) | 18 | 53 | 40 | mixed: memberships/guards/ownership relational-structural; working-note containment + is_file filesystem; legacy-selection advisory procedural-policy |
| F7 module source maps (386–418) | 5 | 9 | 16 | ownership + scoped REF-KNOWLEDGE relational-structural; polymorphic route extraction procedural |
| F8 study-map stages (419–460) | 6 | 23 | 12 | memberships + route owner/guard relational-structural |
| F9 resume pointer (461–472) | 4 | 4 | 7 | relational-structural, pure memberships (stage scoped to pointed map) |
| F10 learning paths (473–501) | 5 | 15 | 12 | relational-structural (required-field null semantics: missing workspace_id errors, no falsy skip) |
| F11 concepts/sources/topics (502–557) | 5 | 24 | 20 | memberships relational-structural; closed-vocabulary (ADR-009) and two-pass-intake policies documented in comments, membership itself delegable |
| F12 concept relations (558–569) | 4 | 4 | 6 | endpoint membership + self-edge relational-structural; polymorphic provenance (note or source); ordinal is the edge's only identity |
| F13 COORDINATION deps (570–580) | 2 | 4 | 4 | extraction procedural (regex prose mining); membership relational-structural; archived = policy attribute |
| F14 URI resolution (582–611) | 6 | 7 | 8 | registry schemes relational-structural; material/project existence filesystem + mounted-tree policy (noise-suppression docstring 601–604) |
| F15 Markdown links (644–672) | 2 | 6 | 10 | filesystem + prose extraction + path containment — procedural throughout |

**A3 verification.** Claim under test: "only ~48 of ~90 diagnostic sites are
plain membership tests." Counted result with stated tiers: **90 sites total;
50 strict plain membership (single container, truthy/type guards allowed)**
— lines 98, 141, 152, 160, 168, 178, 181, 187, 205, 208, 211, 214, 217, 220,
224, 229, 236, 250, 256, 283, 289, 304, 359, 364, 372, 375, 378, 393, 401, 414,
428, 460, 465, 467, 472, 478, 487, 493, 499, 505, 511, 521, 538, 553, 562, 564,
589, 592, 595, 637 — rising to **60** under the broadest existence-only
definition (dual-container +3 at 184, 569, 599; `.get is None` +5 at 242, 247,
383, 470, 576; empty-lookup +2 at 309, 433). The remaining **30 sites** are
equality/guard comparisons (17), multiplicity gates (3), falsy gate (1),
self-disjunction (1), scheme-prefix (1), filesystem (4), containment (2),
policy attribute (1). 60 + 30 = 90 ✓. **A3 confirmed in substance**; the exact
"48" is definition-dependent (50 strict / 60 broad).

**Malformed-input semantics (§6.3 contract).** Suppression is two-layered and
located: per-value, `id_list_items`/`list_items` (`domain/validation.py:142-149`)
return `()` for non-lists and drop non-str items, with explicit in-file guards
and rationale comments at `references.py:365-372` (unit `workspace_ids` — "Do
not iterate a string into misleading per-character reference errors"), 104–106,
148–149, 280–281, 300–302, 391, 426, 458; whole-pass crash containment at
`core.py:234-235, 267-283` (a crash on schema-invalid input becomes one
`SCHEMA-DEPENDENT` error; on schema-valid input it re-raises). Any extraction —
Python or SQL-exporter — must replicate `id_list_items`/`list_items` semantics
exactly.

**Fidelity requirements a relational reference model must carry** (each
verified in code): duplicate identities as diagnostics, not PK rejections
(`snapshot.py:224-230` keeps first record, appends `duplicate_ids` → `ID-DUP`;
ROUTE-ID-DUPLICATE; REL-DUP `registries.py:66-69`); origin provenance per
entity and edge (`_origin_for` partition files `core.py:165-171`;
`module_source_map_origins`, `unit_material_synthesis_origins`); occurrence
ordinal per edge (`relation[{i}]` via `enumerate`, 558–569); scoped targets
(component-in-module 237–258, knowledge-node-in-routed-unit 405–418,
stage-in-current-map 295–298, stage-in-pointed-map 471); polymorphic targets
(relation.source note-or-source 568, evidence URIs six schemes, `unit_routes`
string-or-route 394–403, artifacts scalar-or-list 360–364, contexts
active-or-quarantined 183–184); guard attributes compared (route
`unit_id`/`source_id`/`locator` × 17 equality sites across F2/F6/F8);
null/falsy semantics per family (optional pointers truthy-guarded ×11 sites;
learning-path `workspace_id` required 477; relations normalize missing
endpoints to `""` then error 559).

## 4. K2–K7 — what bookkeeping each owns

### K2 semantic predicates (949 L)
27 registered families (`rg -n '": _predicate\(' | wc -l` → 27); **0 diagnostic
sites** — pure judgment functions, diagnostics delegated to callers; one
`raise` (`evaluate`, line 948, fail-closed). 22 of 27 are relational-structural
*in form* (set membership, anti-joins, CHECKs) — including the two A9 families
`needs_study_map`/`needs_scope`, which stay Python by decision; 3 are
procedural-policy (`AllowedMutation` — segment-scope matcher semantics, not
string prefixes; `CritiquePointActionable` — session-scoped human
authorization; `RequiresHumanJudgment` — the automation boundary itself). The
registry duplicates the `SEMANTIC-CONTRACT.md` truth table deliberately, guarded
by the `DOC-BLOCK-STALE` check (`derive/validation/contract.py:283-291`).
Failures: every predicate is total, fallbacks fail-closed.

### K3 lineage (892 L)
42 `raise LineageError` sites; 2 coded diagnostics
(LINEAGE-ASSUMPTION-MISSING/CYCLE); 3 emit constructors (632, 663, 688).
Buckets: computation/extraction 675 L, serialization+schema 106 L, load 33 L.
The canonical store is the YAML sidecar `operations/transactions/lineage.yaml`
(schema-validated on every load), **not** a projection; records enter only with
a gateway admission binding; ledger text is minted only under
`current_gateway_request()`; `verify_plan_receipt.py:250-256` has a dedicated
`ledger_only` carve-out for exactly this file. `store/evidence.py` and
`store/session_ledger.py` are **not** lineage inputs (write-path machinery);
`store/revisions.py` is, via callers (`claim_status.py:33`,
`app/claim_admission.py`). Recursive blocks (SQL recursive-CTE candidates):
`retraction_impact` 549–577 (strongest — pure BFS closure), `effective_statuses`
+ `_assumption_order` 421–493 (Kahn topo sort + blocker propagation),
`check_assumptions` cycle DFS 822–841. The read-side graph machinery is six
functions ≈ 200 L, pure over records + revisions + hashes.

### K4 manifest projection (462 L)
Structural build ≈156 L + the 21 L `RECORD_SPLICE_ORDER` constant; policy ≈77 L
(quarantine-revision prefix filter, revision fallback, publishability refusal);
orchestration 115 L; **diagnostics 0 L**. Hand-maintained structures: the
16-name splice order ("part of the published file"), the 8-entry typed
collection map (a hand-written `GROUP BY type`), stage/semester unnests.
Record-group enumeration exists in three places (`RECORD_SPLICE_ORDER` keys,
`derive_manifest_collections` filters, the per-domain projectors that mint the
type strings). The production build is kept byte-identical to an incremental
shadow by a test (`tests/test_manifest_stages.py:139`). Adding a top-level key
is gated by `manifest-contract.yaml` + schema bump + **UI mirror in the same
release** (`changing-contracts.md:66-71`); 65 `additionalProperties: false`
blocks in `manifest-v16.schema.json` make unannounced record fields fail at
build time.

### K5 derived-state bookkeeping (1,251 L)
`store.py` is ~202 L of pure SQL-candidate persistence (read/verify/invalidate/
publish/GC over `state-v1.json` + content-addressed blobs) with hand-reasoned
invariants: five corruption→miss failure paths in `read_state` (109, 113, 115,
118, ~129), five in `lookup` (168, 172, 175, 177, 181), blobs-first/state-last
crash ordering, RMW merge, GC "crash-safe by construction" (265–308).
`engine.py` carries session caches that exist *only* to amortize JSON re-parsing
(`engine.py:147-148`: re-parsing per node made every N-node evaluation O(N²) —
"S23: 81% of a warm 2k-note content search"), deferred-index batching, and
staging/commit plumbing. `identity.py` (398 L) and `model.py`'s node-key
construction are extraction/identity policy that stays Python under any
delegation. The corruption doctrine, verbatim: engine.py:9–12 "Corrupt or
absent cached state is an ordinary miss"; store.py:98–104 "any corruption reads
as empty … never an error"; enforced by the `return {}`/`return None` paths.
`derived-store.md` invariant: "Stale or corrupt cache content is a miss, never
authority for current state."

### K6 ledger/receipt reconciliation (1,320 L)
`revisions.py` is the purest relational component in the repository: 448
`artifact → non-negative int` rows, monotone invariant, read-by-key only —
one table with a PK and a CHECK. Caveat: `dump_revisions`' canonical bytes are
hashed as *evidence* (`evidence.py:472-577`), so the serialization contract is
a design decision, not a free deletion. Idempotency rows: fixed 9-column
contract, strict shape validation → `TransactionFailure`. Receipts (380 files)
are append-only logs with two child collections (`writes[]`,
`artifact_revisions`) — natural child tables; 65 v1 receipts are historical,
not replayable (evidence.py requires schema_version 2). `evidence.py`'s
cross-binding choreography (trust binding, delegated-delivery hash
re-verification, revision floors) and `session_ledger.py`'s anchoring/identity/
refusal policy are procedural and stay.

### K7 loading/snapshot (355 L)
`load_repo` is the only place the 20-loader walk order is stated; no error
branch — failures accumulate as `repo.parse_failures` / `repo.duplicate_ids`
(verified fields, `snapshot.py:191-192`; `register` at 222–230 keeps the first
record). The malformed-input chain is verified end to end: `yamlio.py:1-9`
posture → per-file failure rows → `check_parse_failures` (`structure.py:22-28`)
emits `PARSE`/`ID-DUP` → handlers refuse only when failures bear on the answer
(`notes.py:1025-1041`). The snapshot accessor an ephemeral exporter would
consume is `ReadSession.repository()` (`app/read_session.py:80-93`) /
`OpContext.repo()` — the memoized `Repo`, never a second parse; exactly one
full-snapshot parse path exists (one partial-scope shortcut, `_note_collection`,
shares the same parser).

Measurement tooling (verified, not executed): six `tests/benchmark_*.py` scripts;
`benchmark_projection.py` (:110-143) and `benchmark_runtime.py` (:33-46) expose
named load/validate phases and are the fitting harnesses for a three-arm
comparison. S23 note verbatim (`notes.py:945-947`): cold-search scaling is
loader-dominated (145 notes 1.02 s cold; 725 notes 2.00 s; warm tracks cold —
"no index or rebuild work triggered"), which is the measurement that makes an
in-memory projection of the already-loaded snapshot interesting. Case-handling
caveat nearby: `derive/search/normalize.py:1-9` scopes `str.lower` to ASCII
where it coincides with `re.IGNORECASE`; `notes.py:1021` compiles verification
terms with `re.IGNORECASE` — any normalization change must revisit both.

## 5. Duplicated responsibilities (both places named)

1. **Route-guard equality** (`unit_id`/`source_id`/`locator` compared against
   the live route): F2 `references.py:118-138`, F6 `316-337`, F8 `441-456`, and
   the legacy matcher `derive/routes.py:64-88` — **four implementations** of one
   invariant. Family asymmetry to preserve: study-map resources have no locator
   guard (449–456).
2. **Stage-membership** (stage id inside a study map's stages): F6 `295-298`
   (`map_stage_ids`) and F9 `471` (comprehension).
3. **Dual-container workspace membership** (active ∪ quarantined): F3 `183-184`
   and F14 `598`.
4. **Ownership equalities**: UNIT-OWNER emitted from both sides (F5 `243-244`
   via unit_order, F6 `262-265` via unit payload); MAP-OWNER twice (`385`,
   `423`); SOURCE-MAP-OWNER (`389`), PATH-OWNER (`482`).
5. **Thematic-group membership**: F5 `228-229`, F11 `510-511`, and
   `registries.py:168-174` (collections).
6. **Scheme detection**: prefix loop in `parse_reference_uri` (44–45) vs
   `ref.startswith(EVIDENCE_SCHEMES)` at 196.
7. **Duplicate-identity semantics at three layers**: loader `register`
   (`snapshot.py:224-230`), ROUTE-ID-DUPLICATE (87), REL-DUP
   (`registries.py:66-69`).
8. **Polymorphic route shape parsed twice**: F7 `394-397` and
   `iter_route_references` (`routes.py:44-59`).
9. **Staleness comparison in two registers**: `claim_stale`
   (`predicates.py:381-407`, the delegated truth) vs per-key drift re-derivation
   `claim_status.py:95-102`.
10. **Manifest record-group enumeration ×3** (§ K4 above).
11. **Derived-store blob-path identity enforced twice** (parser ~129-133,
    reader ~163-166, `store.py`).
12. **Dossier freshness / scope authority each in two registers** (predicate vs
    lineage claim family, `predicates.py:611-629`/688–727 vs
    `lineage.py:688-707`/663–685).

## 6. Change propagation walks

- **One new note id-list reference field** (K1): `system/schema/note.schema.json`
  + the F3 loop in `references.py` + `manifest-v16.schema.json` mirror
  (945–985) + UI contract lock if projected → **3–4 places**.
- **One new entity family** (K1): schema + loader registration + `Repo` family
  field + validation loop + manifest projector + manifest schema + UI mirror →
  **6–7 places**.
- **One new predicate** (K2): function + constants + registry entry (+ possible
  `CONTRACT_VERSION` bump) + SEMANTIC-CONTRACT doc row (enforced) + re-export +
  a consumer + tests → **6–7 places**.
- **One new lineage claim kind** (K3): `CLAIM_KINDS` + schema enum + emit
  constructor + statement protocol + `claim_status.py` interpretation + a
  gateway write site (of four) + tests → **6–7 places**.
- **One new projected manifest field** (K4): projector + manifest schema
  (`additionalProperties: false` gate) + contract bump + UI mirror (+ shadow
  equality if stage assembly changes) → **3–5 places**.
- **One new reference field inside the derived store** (K5): producer list +
  node-key inputs — content-addressing absorbs it; **1–2 places**.

## 7. Q1 ranking — realistic net simplification

Scored as: bespoke code retireable + duplicated invariants eliminated + failure
modes removed + places-to-change reduced − integration cost honestly charged.

| Rank | Candidate | Verdict | Reason (evidence) |
|---|---|---|---|
| 1 | **Reference validation (K1)** | strongest first candidate | largest bespoke bookkeeping (672 L, 90 sites), most duplicated invariants (§5 items 1–8), 50–60/90 sites plain membership, wide change surface (§6); extraction is a hybrid: declarative field-path registry fits the membership families, route/scoped/guard families keep hand-written producers |
| 2 | **Derived-state persistence (K5, Role B)** | strongest evidenced SQL net-deletion case, separately staged | Q4 answered YES: the deletion side is **published as counted function spans (Appendix B)**; the addition side was **measured** by the Stage 2.5 spike. Measured correction: the same-API-boundary replacement is line-neutral (308 → 280 wc-l; 189 → 193 code lines) with parity 199/224 and zero behavioral failures — the net-deletion case rests on the engine-side ESTIMATE (≈ −40 L) plus the **measured** dimension-4 ownership transfer. The deletion concentrates precisely in hand-reasoned invariant machinery; Role B is design-only in this task per §4 of the brief |
| 3 | **Lineage read-side graph queries (K3, Role A)** | viable under the Q2 condition | ≈200 L of genuinely replaceable graph machinery (BFS closure, topo sort, cycle DFS); ledger, admission binding and gateway minting stay; net lines ≈ flat — the win is delegating recursion/cycles to the engine, so it must beat a refactor arm in its own later pilot |
| 4 | Ledger/receipt row storage (K6) | not first | purest tables, but the canonical-bytes digest contract is evidence, and the subsystem is gateway-coupled — integration risk outweighs the small deletion |
| 5 | **Manifest projection (K4) — recommended AGAINST** | argued rejection | diagnostics 0 L; the SQL-delegable part is view-shaped assembly, but the record shapes would then exist in JSON schema, SQL DDL, *and* the published contract — a new duplication; the contract/versioning/UI-mirror machinery is procedural-policy and stays; no failure mode is delegated |
| 6 | **Semantic predicates (K2) — recommended AGAINST** | argued rejection | 0 diagnostics and no machinery to retire — the predicates *are* the implementation; SQL would relocate 27 total functions behind an adapter, add a third copy of a truth table the `DOC-BLOCK-STALE` gate already pins, and A9 keeps two families Python regardless |
| 7 | Search | excluded (A10) | examined only: `build_postings` postings index is relational-structural and already declared disposable by `search.md` — a candidate for a later independent case |
| 8 | Loading (K7) | not a candidate | it is the exporter's input; `duplicate_ids`/`parse_failures` are diagnostics, not bookkeeping to delegate |

## 8. Q2, Q3, Q4 answers

- **Q2 (lineage)**: a SQL implementation can **replace the read-side query
  machinery** (≈200 L: `_assumption_order`, `effective_statuses`, `impacted`,
  `retraction_impact`, the withdraw cascade, the traversal half of
  `check_assumptions`) while merely *exposing*, never owning, the canonical
  ledger — `operations/transactions/lineage.yaml`, its on-load jsonschema
  validation, the admission binding, the four gateway write sites, and the
  `ledger_only` receipt carve-out all stay. Merely mirroring the YAML into
  ephemeral tables for ad-hoc queries deletes nothing. Condition: replace the
  queries, expose the ledger.
- **Q3 (declarative extraction)**: partially. The plain membership families
  (most of F3–F6, F9–F12) are expressible as a family → field-path registry
  (container, path, target family, alternative container, falsy semantics,
  code, message template). The route/scoped/guard families (F1, F1b, F2, F6
  selections/stages, F7, F8) need hand-written extraction producers —
  `iter_route_references` already is one. So extraction does not disappear in
  any arm; it changes representation. This is the pivot on which A4 (extraction
  is the major risk) turns, and it is quantified in Deliverable 2.
- **Q4 (Role B)**: **YES** — `store/derived/store.py` + the engine's
  persistence plumbing own enough hand-reasoned crash-safety/shape machinery
  that SQLite owning it deletes invariant code. **Deletion side published as
  counted spans in Appendix B** (reproducible AST command included): −202
  store.py deleted spans, −18 `_checked_store_dir` shrink, ≈ −40 engine-side
  ESTIMATE (untouched by the spike); the earlier headline “≈ −295” included
  ≈ −25 of `__init__` shrink that the same-API measurement corrects to ≈ 0.
  **Blob decision: content-addressed blobs move INTO SQLite** (a `blobs`
  table keyed by sha256), not paths-on-disk — this deletes the blob-file
  GC/symlink logic and the crash-ordering choreography; the alternative
  (SQLite stores paths) keeps most of `lookup`/`sweep` file logic and
  materially shrinks the deletion side. **Measured correction (Stage 2.5
  spike, `workbench/relational-delegation-spike-2026-11-06.md` §3): the
  same-API-boundary replacement is line-neutral (308 → 280 wc-l; 189 → 193
  code lines) with parity 199/224 and zero behavioral failures — the net
  ≈ −160 L ESTIMATE does not survive measurement; the case rests on the
  engine-side ESTIMATE plus the measured dimension-4 transfer (corruption→
  miss machinery → schema constraints + one transaction + PK upsert + one
  `DELETE … NOT IN`). Aram's caveat honored and measured: path safety, hash
  verification and identity binding remain ≈ 21 code lines of Python policy
  in the spike module. The doctrine "corrupt cache is a miss" must **not**
  be imported into validation (§6.4 of the brief) — a validator refuses; a
  cache misses, and rebuild **is** the miss path made atomic and explicit.

## 9. Friction and defect pointers (recorded, not fixed)

1. **B1 (`.inflight` predicate)** — pointer corrected during synthesis
   verification: the `.inflight` machinery **is present** in this clone
   (`app/lock.py:154 _has_armed_inflight`, used at `:262`;
   `store/transactions.py:1277 reconcile_inflight_transactions`; journal
   lifecycle `.inflight/.preparing-<id>/` at 1308–1331). An earlier slice
   reported "zero hits repo-wide"; that was wrong (search executed from the
   wrong working directory). The *defect statement* itself is not in this
   checkout — ASSUMPTION: it lives in the original reviewer reports. Not
   reproduced, not fixed, per §3.3.
2. **B3 (missing `maxLength` in the v16 manifest schema)** — verified:
   `maxLength` has **zero occurrences in `manifest-v16.schema.json` and in
   `manifest-v15.schema.json`**, while stored-record schemas use it
   (`sources.schema.json:125`, `concepts.schema.json`,
   `transaction-receipt.schema.json`, …). Most conspicuous unbounded strings:
   `$defs.gardenEntry` (id, path, revision, state, title, tags items;
   manifest-v16.schema.json:2558-2589) and `$defs.reviewItem` (3653-3670).
   Pointer only.
3. **Missing audit references**: `workbench/audits/synthetic-learner-2026-09-12`
   and `workbench/audits/repair-review-2026-09-13` are cited by the binding
   documents (`system/WORKFLOWS.md` ×5, `system/ARCHITECTURE.md` ×1 — invariant
   22b's audit citation) but **do not exist in this clone** (`ls workbench/audits`
   → No such file or directory). Most likely they live in the external session
   workbench tier (the two-tier convention `workbench/fix-f01-2026-10-20/README.md:19-26`
   describes) — but a binding document citing a path the checkout does not
   carry is a reference-integrity friction worth a deliberate home.
4. **Published-doc portability**: `workbench/architecture-hardening-2026-10-17/PLAN-REVIEW.md:7`
   links its plan by machine-specific absolute path into the live checkout.
5. **Naming drift** (cosmetic, record only): `predicates.py:7` names the
   producer `genout.projection`; the live producer is
   `derive/projection/projection/records_curriculum.py` — "genout" survives only
   in comments/docstrings.
6. Clone history is squashed to one commit ("Initial clean LearningOS Core
   snapshot") — a property of this research setup, noted so per-file history is
   not expected to answer questions here.

## 10. ASSUMPTION register (not verified in this inventory)

1. B1's precise defect statement exists in reviewer reports outside this
   checkout; only the machinery pointer above is verified.
2. Which specific v16 field B3 names — the unbounded-string shortlist above is
   the most conspicuous candidates, not a canonical answer.
3. `scope_matches` (`store/contracts/write_scopes.py`) matching internals were
   not read line-by-line; the `AllowedMutation` classification rests on the
   module contract.
4. `FACT_OWNERS` path templates duplicate nothing outside `store/layout.py`
   (searched; no match) — duplication in `domain/`/`derive/projection/` not
   exhaustively excluded.
5. The UI contract-lock mirror (`manifest-v<N>.lock.json`, `ManifestV<N>`,
   fixture vault) lives in the external UI repository; its state is unverified
   here.
6. Docstring performance figures ("244 ms at 328 receipts", "81% of a warm
   2k-note content search", "~265MB") are quoted as recorded claims, not
   re-measured.
7. All behavior statements are static code reads; nothing was executed (no
   venv exists in the clone). The `workbench/audits/*` interpretation (§9.3)
   assumes the external-session-workbench explanation.
8. `operations/transactions/lineage.yaml` content was not read; K3 analysis is
   via its owner module.

## 11. Verification and honesty notes

Independently re-verified during synthesis (commands against the clone):
all fifteen `wc -l` claims of §2 (exact matches); 86/4 err/warn and 90 total
sites in `references.py`; 27 predicate registry entries; 42 `raise LineageError`
and the three `emit_` constructors; B3's zero-`maxLength` result (exit 1) and
the stored-schema contrast; gate samples at `references.py` lines 98, 178, 204,
219, 244, 317, 442, 566 against the family table; the corrected B1 search (§9).
The Appendix A command reproduces the per-family diag column exactly and the
extract column within the stated ±4; the spot-checked gates and totals agree
with the family table.

An independent read-only review pass (2026-11-06) re-ran a sample of the
commands, verified ~20 file:line pointers across both deliverables, and found
one labelling defect — the Role-B addition side quoted as counted — corrected
in this revision together with a runnable reproduction command for the
per-family splits.

Not done, deliberately: no validation run, no benchmark execution, no
prototype code in the original Stage 1–2 pass (Stop gate 1's autonomous
clause: proceed to Stage 2 *design only*). The Stage 2.5 spike (authorized at
Gate 2) subsequently ran the oracle test suites in-process; its results live
in `workbench/relational-delegation-spike-2026-11-06.md`. Behavior claims in
§§2–8 are static reads on branch `research/relational-delegation-2026-11-06`;
counted numbers were taken at the commit that introduced them (commit-relative:
`git log --oneline main..HEAD`).

## Appendix A — key reproduction commands

```
cd /Users/aramaljanadi/los-sql-2026-11-06/repository
git branch --show-current                     # research/relational-delegation-2026-11-06
git log --oneline main..HEAD                  # the workbench deliverable, spike and fix commits on this branch
wc -l tools/learning_os/derive/validation/references.py \
      tools/learning_os/derive/validation/registries.py \
      tools/learning_os/derive/semantics/predicates.py \
      tools/learning_os/derive/semantics/lineage.py \
      tools/learning_os/derive/projection/manifest.py \
      tools/learning_os/store/derived/*.py \
      tools/learning_os/store/evidence.py tools/learning_os/store/revisions.py \
      tools/learning_os/store/session_ledger.py \
      tools/learning_os/store/loading/__init__.py \
      tools/learning_os/domain/snapshot.py
rg -c "self\.err\(" tools/learning_os/derive/validation/references.py    # 86
rg -c "self\.warn\(" tools/learning_os/derive/validation/references.py   # 4
rg -n '": _predicate\(' tools/learning_os/derive/semantics/predicates.py | wc -l  # 27
rg -c "raise LineageError" tools/learning_os/derive/semantics/lineage.py  # 42
rg -n "^def emit_" tools/learning_os/derive/semantics/lineage.py          # 632/663/688
rg -c "maxLength" system/contracts/manifest-v16.schema.json \
                 system/contracts/manifest-v15.schema.json               # no matches
rg -n "_has_armed_inflight" tools/learning_os/app/lock.py                 # 154, 262
grep -roh "workbench/audits/[a-z0-9.-]*" --include="*.md" system/ | sort -u
ls operations/transactions/transaction-*.yaml | wc -l                    # 380
wc -l operations/transactions/revisions.yaml                             # 451 (448 rows)
```

## Appendix B — Role-B deletion-side span ledger (reproducible)

The §8/Q4 deletion side, as counted function spans (`ast` `lineno`–
`end_lineno`, wc-l basis), with the classification under the **blob decision**
(blobs move into SQLite — see §8/Q4):

| Span | wc-l | Classification |
|---|---|---|
| `store.py:47-62` `_state_payload` | 16 | deleted (row serializer → schema) |
| `store.py:65-72` `derived_dir` / `state_path` | 6 | stays (path API parity) |
| `store.py:75-86` `canonical_bytes` | 12 | stays (feeds output digests) |
| `store.py:89-95` `_reject_duplicates` | 7 | deleted (PK uniqueness) |
| `store.py:98-135` `read_state` | 38 | deleted (SELECT + schema) |
| `store.py:138-151` `invalidate` | 14 | deleted (one `DELETE`) |
| `store.py:154-181` `lookup` | 28 | deleted; the hash-verify half is retained as policy |
| `store.py:184-205` `_checked_store_dir` | 22 | shrinks to one open-time guard (≈4) |
| `store.py:208-215` `_atomic_write` | 8 | deleted (journaling/transactions) |
| `store.py:218-233` `stage_node_blob` | 16 | deleted (INSERT) |
| `store.py:236-251` `publish_staged_states` | 16 | deleted (transaction upsert) |
| `store.py:254-262` `store_node` | 9 | stays (thin wrapper) |
| `store.py:265-308` `sweep_unreferenced_blobs` | 44 | deleted (one `DELETE … NOT IN`) |
| `engine.py` `_Session.states` cache + `_lookup` amortization | ≈12 | ESTIMATE (untouched by the spike) |
| `engine.py` `deferred_index` batching | ≈14 | ESTIMATE |
| `engine.py` `commit_staging` persistence half | ≈14 | ESTIMATE |
| `__init__.py` re-export shrink | ≈0 | measured correction (same API surface preserved) |

Counted store-side total: **−220** (−202 deleted spans − 18 shrink); with the
engine ESTIMATEs ≈ −260. The former “≈ −295” headline additionally counted
≈ −10 of store.py docstring/constants (retained in any rewrite of the same
surface) and ≈ −25 of `__init__` shrink the same-API measurement corrects to
≈ 0 — hence the measured correction in §8/Q4.

Command (spans are exact; run in the clone):

```python
python3 - <<'EOF'
import ast
for path in ("tools/learning_os/store/derived/store.py",
             "tools/learning_os/store/derived/engine.py"):
    src = open(path).read()
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            print(f"{path}:{node.lineno}-{node.end_lineno} {node.name} "
                  f"({node.end_lineno - node.lineno + 1}L)")
EOF
```

Measured counterpart (spike module replacing exactly this surface): 280 wc-l /
193 code lines, parity 199/224, zero behavioral failures —
`workbench/relational-delegation-spike-2026-11-06.md` §§1–3.

Per-family diag/extract reproduction (the §3 table; diag exact, extract ±4):

```python
python3 - <<'EOF'
import ast, re
FAM = [("F0-parsers",19,60),("F1-route",65,93),("F2-synthesis",94,173),
       ("F3-notes",174,200),("F4-workspaces",201,224),("F5-modules",225,258),
       ("F6-units",259,385),("F7-source-maps",386,418),("F8-study-maps",419,460),
       ("F9-resume",461,472),("F10-paths",473,501),("F11-concepts-sources-topics",502,557),
       ("F12-relations",558,569),("F13-coordination",570,580),("F14-uri",582,611),
       ("F1b-solution-exposure",613,642),("F15-links",644,672)]
path = "tools/learning_os/derive/validation/references.py"
lines = open(path).read().splitlines()
tree = ast.parse(open(path).read())
spans = set()
for node in ast.walk(tree):
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("err", "warn")):
        spans.update(range(node.lineno, node.end_lineno + 1))
EXTRACT = re.compile(r"\br\.[a-z_]+|\.get\(|id_list_items\(|list_items\(|"
    r"isinstance\(|startswith\(|\.split\(|\bstr\(|\bset\(|\.values\(\)|\.items\(\)|"
    r"enumerate\(|findall\(|resolve\(|is_relative_to|is_file|\.exists\(|"
    r"markdown_link_targets|classify_markdown_link|parse_reference_uri|"
    r"iter_route_references|routes_by_id|exact_selection_matches|"
    r"self\._(?:rel|origin_for)")
td = te = 0
for name, lo, hi in FAM:
    d = sum(1 for n in range(lo, hi+1) if n in spans)
    e = sum(1 for n in range(lo, hi+1) if n not in spans and EXTRACT.search(lines[n-1]))
    td += d; te += e
    print(f"{name:28s} diag {d:3d} extract {e:3d}")
print(f"{'TOTAL':28s} diag {td:3d} extract {te:3d} other {len(lines)-td-te}")
EOF
# Published output: diag column matches the §3 table exactly (Σ 257);
# extract Σ 219 by this regex vs 223 by the slice's variant — the four-line
# difference sits in F3/F8/F15's classifier boundary.
```
