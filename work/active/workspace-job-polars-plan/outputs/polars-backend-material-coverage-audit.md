# Polars backend plan - complete material coverage audit

Verified: 2026-09-03. Target environment: pandas 3.0.2 and Polars 1.36.0 from the current Stratum `pyproject.toml` and `uv.lock`.

## Local inventory

- **Existing learning map:** all 18 pending stages, 251 stage resources, and 18 authored working guides were inspected. Every stage/resource is preserved in the session migration. Session 1 retains its original paths; moved stages link back to the original authored guide while receiving a new owning-session working note.
- **Python Polars: The Definitive Guide:** 591-page early-release PDF opened and visually checked. Exact chapter starts were verified in viewer pages: Ch. 1 p.14, Ch. 2 p.52, Ch. 3 p.74, Ch. 4 p.103, Ch. 5 p.122, Ch. 6 p.144, Ch. 7 p.178, Ch. 8 p.208, Ch. 9 p.254, Ch. 10 p.279, Ch. 11 p.307, Ch. 12 p.327, Ch. 13 p.369, Ch. 14 p.403, Ch. 15 p.434, Ch. 16 p.458, Ch. 17 p.503, Ch. 18 p.537. Expression, selector, aggregation, join, lazy, extension, and Arrow routes use viewer-page ranges.
- **Python Data Science Handbook notebooks:** every pandas notebook 03.00-03.12 was enumerated and its markdown headings inspected. They cover objects/indexes, selection, alignment, missing values, concat, joins, grouping, pivots, strings, time series, and eval/query. Disposition: useful executable prompt corpus, but prior-version material; pandas 3.0.2 docs and probes remain authority.
- **Pandas cheat sheet:** both viewer pages visually inspected. Disposition: operation-recall index only; it is dated 2017 and cannot establish current semantics.
- **Python Depth Drills:** Stage 8 interfaces/dispatch and SHELF sections 3a testing and 3c performance inspected. Disposition: complementary implementation practice, not dataframe semantic authority.
- **stratum paper:** all eight pages available; architecture sections 4.1-4.3 on viewer pages 4-5 visually checked. Disposition: architecture authority for declarative DAGs, lowering, and physical selection; checkout remains authority for implemented details.
- **Towards Scalable Dataframe Systems:** 19-page PDF; dataframe model/algebra on viewer pages 5-7 and schema/order/metadata challenges on pages 10-12 inspected, including a visual check of Section 4.3. Disposition: derivation/mental-model depth.
- **User-authored notes:** `note-stratum-extract-dataframe-op`, SelectionOp, ColumnSelectorOp, MissingMaskOp, AssignMapOp/AssignOp, AggregateOp, JoinOp, pandas GroupBy signatures, and the executable pandas-Polars aggregation contention map are explicitly routed into the applicable stages.
- **Attached case study:** `/Users/aramaljanadi/Downloads/_selection_execs.py` was compared with the current Stratum selection implementation before redesign; SAMPLE, duplicate mapping, DROPNA expression construction, and OperandRef resolution drive Session 3.

## Linked inventory

Official pages were opened or checked on 2026-09-03 and routed by exact section, not by homepage: Polars expressions and contexts; migration from pandas; expression expansion/selectors; folds; `when`; missing data; casting and schemas; head/tail/sample/unique/drop_nulls; aggregation; windows; joins; lazy usage/optimizations/query plans; UDF guidance; testing/parametric strategies; pandas 3.0 release notes; and the corresponding pandas 3.0.2 operation/testing references.

The live Polars documentation may describe a release newer than Stratum's Polars 1.36.0. Every linked behavior therefore carries an explicit pinned-environment verification rule. The Polars 2.0 upgrade guide is deferred to Session 10 and cannot define the current backend contract.

The official `pola-rs/polars-benchmark` paired pandas/Polars queries are retained as an advanced capstone corpus by link, not copied, because some benchmark inputs are license-governed and the plan needs only selected translation exercises.

## Completeness sign-off

- The redesign preserves all existing learning/exercise resources and adds missing expression, selector, horizontal/fold, real SelectionOp, cross-family implementation-loop, and generated-testing exercises.
- No fixed stage durations were retained or invented. Sessions are bounded by outcomes and contain two to four stages each.
- pandas is an operation-level observable oracle, not a demand to reproduce every incidental quirk. Each backend case ends in native, adapted, fallback, unsupported, or intentional-divergence policy.
- The cumulative harness is owned by Session 1 and used in every later done-when. A new first-class LearningOS project/workspace was deliberately not created in this migration because project creation does not create a joined workspace atomically; that extra write would delay today's usable curriculum. Exercise code belongs in a learner-chosen Stratum scratch/test file and can be attached to the stage without modifying Stratum automatically.
- Existing stages were all pending, so no completion evidence is moved or rewritten. Original moved-stage guides remain at their old paths as migration evidence and are linked from the new owning stage.
- Excluded as non-fitting: plotting/visualization chapters, unrelated NumPy/Matplotlib/ML notebooks, generic Python drills outside testing/dispatch/performance, and copying third-party benchmark data.
- Unresolved but visible: live official docs can drift; every behavior must be probed in the pinned environment. Polars 2.0 remains a deferred transition exercise until Stratum changes its dependency.
