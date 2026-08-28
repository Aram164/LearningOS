# Stage Working Notes

## Mental Models

### Pandas baseline

DataFrame/Series constructors, read_csv/read_parquet, dtype/usecols/parse_dates, inference, nullable dtypes, and index creation.

### Polars mirror

schema/schema_overrides, read_csv/read_parquet, scan_csv/scan_parquet, collect_schema, rechunking, and explicit casts. Distinguish eager reads from lazy scans.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/physical/_source_execs.py. Pair PandasReadCSV↔PolarsReadCSV, PandasReadParquet↔PolarsReadParquet, and PandasInMemoryFrame↔PolarsInMemoryFrame. Explain why the Polars source may rechunk and where that choice is bound.

## Component

- stratum/optimizer/physical/_source_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
