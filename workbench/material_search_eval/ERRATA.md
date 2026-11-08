# Errata for Historical Material Search Evaluation Reports (`STAGE_2_REPORT.md` – `STAGE_4_REPORT.md`)

**Date:** 2026-11-08  
**Superseding evaluation:** [`PREREGISTRATION.md`](PREREGISTRATION.md) and [`STAGE_5_REPORT.md`](STAGE_5_REPORT.md)

The earlier workbench reports (`STAGE_2_REPORT.md`, `STAGE_3A_REPORT.md`, `STAGE_3B_REPORT.md`, `STAGE_3C_REPORT.md`, and `STAGE_4_REPORT.md`) are retained unedited as historical artifacts. The 2026-11-08 adversarial audit identified the following factual and narrative errors in those reports:

1. **Per-query narrative tables in `STAGE_3B_REPORT.md` and `STAGE_3C_REPORT.md` do not match `questions_v2.yaml`.**  
   While the numeric aggregate metrics in the stored result JSON files reproduce (`37/37`), roughly 20 of the 27 development rows in the narrative prose tables of `STAGE_3B_REPORT.md` and `STAGE_3C_REPORT.md` describe fabricated or mismatched query topics that do not exist in `questions_v2.yaml` (for example, describing `DEV-06` as "SVD" when `DEV-06` in `questions_v2.yaml` is `"stochastic gradient descent"`).

2. **Held-out negative control ID misreported in `STAGE_4_REPORT.md`.**  
   `STAGE_4_REPORT.md` names `HELD-04` as the unanswerable negative control in `questions_heldout_v1.yaml`. In `questions_heldout_v1.yaml`, `HELD-04` is an answerable query (`"Gale-Shapley"`), and the actual negative control is `HELD-10`.

3. **False explanation of production vs. frozen ranking differences in `STAGE_4_REPORT.md` (Audit M4).**  
   `STAGE_4_REPORT.md` claimed that differences between the initial production index and the frozen Stage-3c spike index were caused by "identical BM25 scores" and SQLite `rowid` tie-breaking. In reality, BM25 scores differed across all `37/37` queries (`20/27` exact top-5 matches on dev, `10/10` on held-out), and adding an explicit `ORDER BY rank, sha256, page_no` tie-breaker changed `0/37` queries (ties occurred in the top 6 in only `2/37` queries). The actual causes of the score differences were:
   - indexing a filename-derived `title` column alongside `body` (shifting multi-column BM25 field weights and lengths);
   - dropping empty/whitespace pages (`71,120` indexed rows vs. `72,199` in the spike index, shifting corpus average document length);
   - omitting `remove_diacritics 2` from the `unicode61` tokenizer declaration; and
   - a diverged `STOPWORDS` set (`118` extra words in initial production while missing `dem`, `den`, `des`, `fur`, `of`, `uber` from the frozen spike set).
   All four divergences were fixed in Phase 3 (`search_index.py` and `build_material_search_index.py`), and `STAGE_5_REPORT.md` evaluates the exact production code path.

4. **Index size and build-time figures in `STAGE_3C_REPORT.md` and `STAGE_4_REPORT.md` (Audit L6).**  
   The reports stated an index size and build time of `"185 MB / ~45 s"`. Measured on the 512-entry text cache (`71,120` indexed pages), the initial generation was `269 MB` built in `11–22 s` (and the Phase 4 self-describing body-only index `index-4ed250ab63629926.sqlite3` is `242.6 MB` built in `~18 s`).

5. **"Ruff format clean" claim in `STAGE_4_REPORT.md` (Audit L6).**  
   `STAGE_4_REPORT.md` claimed the new files were `ruff format` clean when `ruff format --check` would have reformatted 1 new file.

6. **Mischaracterization of image-only scanned books as "blank pages" in `STAGE_4_REPORT.md` (Audit H2).**  
   `STAGE_4_REPORT.md` attributed the `1,079` unindexed pages across `generated/text-cache/` to "blank verso pages" (naming Rudin) and "blank transition slides" (naming Wirth). In reality, of the `1,079` pages without extracted text, `612` are image-only scanned content pages (including all `351` pages of Rudin's *Principles of Mathematical Analysis* — misnamed "Real and Complex Analysis" in the report — and `118` scanned pages of Wirth's *Compilerbau*), `465` have neither text nor embedded images, and `2` failed `pdftotext` extraction. In addition, `10` of the `522` PDFs in `records/materials-manifest.yaml` (`8` route-bound across `43` bindings) had no `generated/text-cache/` directory at the time of the audit. The v1 `material.search` contract now discloses `coverage.documents_without_text`, `coverage.excluded_cache_entries`, `coverage.unindexed_route_materials`, and `coverage.scope_complete` on every `ok` response.

7. **Post-hoc addition of `topical_targets` in `STAGE_3B_REPORT.md` (Audit H4).**  
   The `topical_targets` field was added to 10 development questions in `questions_v2.yaml` after `STAGE_2_REPORT.md` had already inspected and named the specific documents FTS5 surfaced (such as Ohlbach/Eisinger and MfNF), invalidating the "independence guarantee" claimed in `STAGE_3B_REPORT.md` for lenient/topical recall. The superseding evaluation in [`PREREGISTRATION.md`](PREREGISTRATION.md) and [`STAGE_5_REPORT.md`](STAGE_5_REPORT.md) uses a fresh held-out dataset (`questions_heldout_v2.yaml`, SHA-256 `aab7d34bc258a643ffdbc157008e5e576e8173fe4142e5289dc38fe21f58a20a`) authored from curriculum metadata and `material_toc.py` without running any search backend, and evaluates the pre-registered decision rule strictly on `Strict R@5`.
