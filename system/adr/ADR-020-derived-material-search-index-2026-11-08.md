# ADR-020: derived material search index

Date: 2026-11-08. Status: accepted. Amends `system/ARCHITECTURE.md` §17 (Explicit
non-goals) to clarify that one disposable, rebuildable, read-only full-text
search index under `generated/material-search/` is permitted while preserving the
ban on any database or server as a canonical store of record.

## Decision

One derived, rebuildable, read-only SQLite FTS5 index under
`generated/material-search/index-<F[:16]>.sqlite3` is permitted to serve the
`material.search` query capability over the local PDF page-text cache
(`generated/text-cache/`). There is no canonical database, no server, and no
daemon, so `system/SEMANTIC-CONTRACT.md` and the plain-file source-of-truth
contract hold unchanged:

1. **Disposable derived artifact, never a store of record.** The index is built
   purely from validated `generated/text-cache/<sha256>/` page files and the
   checked-in `records/materials-manifest.yaml` inventory. Deleting
   `generated/material-search/` loses no canonical or learner data; queries
   degrade cleanly to `status: "unavailable", reason: "index_missing"` with the
   exact rebuild command until the index is rebuilt.
2. **Self-describing content identity.** The index filename and internal `meta`
   table record the text-cache fingerprint $F$ (SHA-256 over the sorted `(sha256,
   pages_sha256)` pairs of all valid cached documents), `schema_version`,
   `tokenizer` (`unicode61 remove_diacritics 2`), `extractor_id`, and `doc_count`.
   Canonical note or curriculum writes do not invalidate the index. At query time,
   `execute_search` resolves route bindings from the live `Repo`, verifies live
   material file bytes (`stat` first, `sha256` on mismatch), filters by `--unit`
   and `--module` inside SQL before `LIMIT`, and reports `freshness`
   (`matches_text_cache`, `changed_shas`) and `coverage` (`documents_without_text`,
   `excluded_cache_entries`, `unindexed_route_materials`, `scope_complete`) on
   every `ok` response.
3. **Why not a derived-store node.** The derived-state engine
   (`learning_os.derive.engine`) persists JSON artifacts that are serialized and
   read whole into memory. An inverted index over 71,120 textbook pages (~243 MB)
   requires paged random B-tree lookups (`mode=ro`) rather than whole-blob JSON
   deserialization.
4. **Precedent in projection publication.** The projection publisher
   (`learning_os.derive.projection.outputs`, `outputs.py:102-108`) already exempts
   sibling tool-maintained caches under `generated/` (`text-cache`,
   `material-slices`, `material-summaries`, and `reports`) via `_KEEP_TOP_DIRS`.
   `SEARCH_TOP_DIR = "material-search"` is declared in
   `learning_os.domain.validation.GENERATED_DIRECTORIES` and imported into
   `_KEEP_TOP_DIRS` so `write_outputs` preserves `generated/material-search/`
   across view rebuilds.

## Empirical evaluation (Phase 3)

On the rebuilt body-only `unicode61 remove_diacritics 2` index over the 512
validated text-cache entries (71,120 indexed pages, 1,079 pages without text):

- **Development regression set (`questions_v2.yaml`, 25 answerable queries + 2
  negative controls):** FTS5 achieved Strict R@1 = 0.12 (3/25), Strict R@3 =
  0.44 (11/25), Strict R@5 = 0.52 (13/25), Lenient R@5 = 0.56 (14/25), and
  MRR@5 = 0.2700, with 0/2 false positives on negative controls. In-process
  handler latency across the 27 queries measured p50 = 529.7 ms (p95 = 593.2 ms;
  122.0 ms p50 with a preloaded `Repo`), and SQL query execution measured p50 =
  43.3 ms.
- **Pre-registered held-out benchmark (`questions_heldout_v2.yaml`, 20 answerable
  queries + 4 negative controls, SHA-256
  `aab7d34bc258a643ffdbc157008e5e576e8173fe4142e5289dc38fe21f58a20a`):**
  - **FTS5 (`material.search`):** Strict R@1 = 0.25 (5/20), Strict R@3 = 0.40
    (8/20), Strict R@5 = 0.65 (13/20), Lenient R@5 = 0.70 (14/20), MRR@5 =
    0.3650, negative-control false positives = 0/4, SQL p50 = 43.33 ms,
    subprocess E2E p50 = 1,994.52 ms.
  - **Grep Scan (`generated/text-cache/`):** Strict R@1 = 0.10 (2/20), Strict
    R@3 = 0.20 (4/20), Strict R@5 = 0.35 (7/20), Lenient R@5 = 0.35 (7/20),
    MRR@5 = 0.1717, negative-control false positives = 0/4, E2E p50 =
    6,836.91 ms ($b = 7$ FTS5-only wins, $c = 1$ Scan-only win, exact two-sided
    McNemar $p = 0.0703$).
  - **Baseline A (`material.context`):** Strict R@1 = 0.00 (0/20), Strict R@3 =
    0.00 (0/20), Strict R@5 = 0.10 (2/20), MRR@5 = 0.0250 ($b = 11, c = 0$,
    exact two-sided McNemar $p = 0.0010$).

Both clauses of the pre-registered decision rule in
`workbench/material_search_eval/PREREGISTRATION.md` passed ($\text{Strict R@5} \ge
\text{Scan} - 2$ and $\text{p50} < \text{Scan p50}$). Because a helper subagent
wrote `questions_heldout_v2.yaml` after the development results were already
seen and the paired recall difference has $p = 0.0703$, the 13/20 vs 7/20 result
is treated only as satisfying the pre-registered non-inferiority gate (no more
than 2 worse on recall and faster), not as proof that FTS5 beats the scan on
recall.

## Residual corruption risk (D14) and review trigger

The builder acquires `generated/material-search/.build.lock` (`LOCK_EX | LOCK_NB`),
validates every cache entry via `material_text._index_valid`, decodes page files
with strict UTF-8, builds `.build-<pid>-<ns>.sqlite3`, runs `PRAGMA
integrity_check` and `INSERT INTO material_fts(material_fts) VALUES('integrity-check')`,
verifies row counts, `fsync`s the file and directory, and atomically publishes via
`os.replace` to `index-<F[:16]>.sqlite3` before pruning superseded files. The
reader opens the database in `mode=ro` with `PRAGMA query_only = ON`, `PRAGMA
mmap_size = 0`, `PRAGMA trusted_schema = OFF`, and a 20,000,000 VM-step progress
handler budget, catching `sqlite3.DatabaseError` around connect, metadata
validation, `MATCH`, and row iteration to return `status: "unavailable", reason:
"index_corrupt"`.

**Residual risk:** SQLite's C extension is not memory-safe against arbitrary
post-publication byte mutations on disk; a damaged B-tree or FTS5 shadow segment
can still trigger an upstream C assertion if SQLite is compiled with assertions
enabled. Disabling `mmap_size`, enforcing pre-publish integrity checks, and
keeping the index a disposable derived cache bound this risk.

**Review trigger:** If a future evaluation or corpus change shows a direct
page-cache scan tying or beating FTS5 within interactive latency bounds, or if
the post-landing headless-agent study evaluation does not meet its pre-registered
threshold, replace the FTS5 backend inside `execute_search` while keeping the
`material-search-v1` response contract unchanged.

## 2026-11-08: product answers

Aram answered the routing plan's two product questions on 2026-11-08; they
are recorded here because they bound what this index will ever cover.

**Q1 — no OCR now (D18).** The live text cache holds six scanned documents:
351/351, 118/118, 11/12, 8/8, 6/6 and 1/1 blank pages. Only the 11/12
document (a handwritten scan) is route-bound, and its locator already says
"scanned, weak text layer"; the rest are unrouted. OCR would make exactly
one routed document searchable, and that document is handwriting, which OCR
reads worst. Revisit trigger: a scanned PDF gains a route whose `role` is
not `reference`. OCR then becomes its own producer (`material_ocr`
writing `generated/ocr-cache/`), never part of `tools/material_text.py`
(N2). Until then, every route-bound document without text is disclosed in
the response under `coverage.unindexed_route_materials` (reason `no-text`)
with `scope_complete: false`.

**Q2 — only Aram's own notes (D19).** The notes under `knowledge/notes/`
(152 files, about 1.5 MB) are already searchable over their full bodies
with `search QUERY --type note --content` and already routed through the
`note-body-or-saved-reasoning` task. They are deliberately not added to
this FTS index: they are canonical records that change often, so a derived
index would serve them stale, and substring search over 1.5 MB is already
exact and fast. Video transcripts, notebooks, HTML and other non-PDF
materials stay unsearched; the coverage arithmetic ignores non-PDF
materials entirely.

**Disclosure over a response field (D21).** That coverage limit is stated
in the route docs, not added as a response field: the `material-search-v1`
schema closes its objects with `additionalProperties: false`, and a schema
bump for a gap one sentence can state is not warranted. Revisit trigger: a
discoverability transcript shows an agent reading a PDF-only result as
"the unit has nothing on this", or skipping the `material-span` cut-off
hint.

A search hit is retrieval evidence, not coverage evidence.

## 2026-11-12: section groups and concept names

Plan A step 1 (`outputs/learningos-agent-first/PLAN-A-retrieval-and-route-identity.md`
in the workspace) adds two read-side behaviours. Neither changes what the index is.

**Sections are a second disposable cache, not index rows.** Outline headings
come from each PDF's bookmarks and are keyed by file digest under
`generated/material-outlines/<sha256>.json`, written by
`tools/material_outline.py` from the exact bytes it hashed. The index stays
a pure function of the text cache (decision 1 above); a missing or damaged
outline entry only turns a group into an explicit unsectioned one
(`not-harvested`, `cache-invalid`). Encrypted PDFs get no outline, because
the shared PDF reader refuses encrypted bytes.

**A hit is a section group.** Candidate pages group by the section that owns
them; a document's pages without a section form one unsectioned group with
its reason. Each hit is one group at its best page, with the group's matched
pages and a `span_pages` range of at most 20 pages; `span_reference` still
opens the best page, so an excerpt stays inside `material-span`'s cut-off.
`limit` and `offset` count groups over one fixed scan of at most 1,000
candidate pages, so a group never moves between result pages;
`scan_truncated` reports a capped scan. Reason: an agent pays per distinct
place it reads, and a page list fills its limit with neighbouring pages of
one section. A slide deck that bookmarks every slide still yields one group
per slide, because the outline is the authority.

**A concept name is language-independent.** When the normalized query equals
a registered concept label or alias (`knowledge/concepts.yaml`), the phrase
and AND tiers also search the concept's other names, ranked together by
BM25, and the response reports them in `expansion`. Only an exact name
expands: a concept word inside a longer question does not. The OR tier stays
the query's own words.

