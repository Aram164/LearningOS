# module-job-polars plan coverage audit — 2026-11-02

Plan package: built by `LearningOS/workbench/polars-plan-2026-11-02/build/build_package.py`.

Scope authority: Aram's request of 2026-11-02 (fluent Polars; aware of pandas differences; ML-pipeline
operations; no signature memorisation; no internals), and Stratum's lockfile for versions (Polars 2.0.0,
pandas 3.0.2, skrub 0.11.0, scikit-learn 1.8). Stratum was read, never changed.

Review boundary: every source and URL already in this module; local book PDF; candidate materials named below.

## Local material inventory

| Locator | Version/year | Opened evidence | Disposition | Reason |
|---|---|---|---|---|
| `material://source-polars-definitive-guide/python-polars-the-definitive-guide.pdf` | Early Release 8, 2024-12-03, Polars 1.13.1 | text extracted, chapter starts and 33 section locators checked by page | current, selected chapters | best long-form text; read with the errata page; Ch 16 and Ch 18 off the path |
| source-pydata-handbook notebooks | 2016 | named notebooks in routes | prior-year, reference-only | predates pandas 3.0; replaced by pandas docs and Modern Polars |
| `material://source-python-cheatsheets/Pandas_cheatsheet.pdf` | 2017 | route locators | prior-year, reference-only | recall only, never an authority |
| source-python-depth-drills | current | route locators | deferred with the backend stages | Python technique; lives with the deferred stages |
| `material://source-stratum-paper/stratum-paper.pdf` | current | route locators | helpful-now in Session 10 | architectural intent only |
| source-scalable-dataframe-systems-paper | 2020 | route locators | complementary, unplaced | theory, reachable on the menu |
| stage attachments, 1.36 sheets and checks | 2026-09 | all run under 2.0 | superseded by `-p2` copies; originals retained | hard version guard stopped them all under Stratum's current lock |

## Linked web material inventory

All 81 URLs already in the module were requested on 2026-11-02 and returned HTTP 200 without moving.
New links, each requested on 2026-11-02:

| URL | Verified | Disposition | Unit |
|---|---|---|---|
| https://docs.pola.rs/user-guide/getting-started/ | 200 | current | Session 1 |
| https://pola.rs/posts/release-polars-2 | 200, read | current | Session 1 |
| https://docs.pola.rs/releases/upgrade/2/ | 200, read | current | Sessions 1, 7 |
| https://kevinheavey.github.io/modern-polars/ and chapters | 200, read | current | Sessions 1, 2, 5, 7, 8 |
| https://narwhals-dev.github.io/narwhals/concepts/ pages | 200 | complementary | Sessions 1, 3, 5 |
| https://pandas.pydata.org/docs/whatsnew/v3.0.0.html | 200, read | current | Session 1 |
| https://github.com/pola-rs/polars-benchmark | queries read | current | Sessions 6, 7, 11 |
| https://github.com/jeroenjanssens/python-polars-the-definitive-guide (crash course) | notebook read | helpful | Session 1 |
| https://skrub-data.org/stable/ pages | 200, read | current | Session 9 |
| https://scikit-learn.org/stable/modules/df_output_transform.html, compose, cross_validation, common_pitfalls | 200 | current | Session 9 |
| https://docs.pola.rs user guide time-series and categorical pages | 200 | current | Session 9 |

## Current/prior and duplicate reconciliation

The book (Polars 1.13.1) and the current user guide disagree where 2.0 changed behaviour; the user guide
governs, and the errata page lists the book's passages. The pandas stable docs now show 3.1 while Stratum
pins 3.0.2; the 3.0 release notes are named explicitly. Modern Polars targets 1.41.2 and polars-benchmark
1.41.2 with pandas 2.3.3; both predate Polars 2.0 and each route says so.

## Explicit exclusions and unresolved gaps

| Material | Disposition | Reason | Revisit |
|---|---|---|---|
| Talk Python 'Polars for Power Users' | out-of-scope | paid, Polars 1.24 | a 2.0 edition |
| Udemy 'Data Analysis with Polars' | out-of-scope | paid, last stated version 1.30 | a 2.0 edition |
| DataCamp Polars courses | out-of-scope | beginner level, and the free material above covers them | |
| Effective Polars (Harrison) | out-of-scope | code repo last pushed 2024-04 | a new edition |
| Polars Cookbook | reference-only | Polars 1.x; retained where already placed | |
| Final printed edition of the Definitive Guide | not required | the local Early Release is close to final; the concepts hold | |
| Stratum as a material | not registered | OPERATOR boundary 3: read-only paths named in stages | |
| Pre-2.0 claims in the 1.36 stage guides (`notes.md`) | deferred | old guides stay reachable and off the path | |
| Stale Stratum notes (SelectionOp, MissingMaskOp) | gap | describe classes no longer in the code; the stages now point at the code; the notes need Aram's review to change | a note revision |
| pandas↔Polars aggregation contention note | gap | its probes are pinned to 1.36 and were not re-verified on 2.0 | a note revision |
| Practice gap | recorded | ML stages have short tasks without an answer key, by Aram's priority of materials over exercises | |

## Completeness

Every source already on the module stays on the source map, with its routes. Nothing was deleted. Nine
stages moved to deferred with the reason in their objective; they keep rows, attachments and notes.
