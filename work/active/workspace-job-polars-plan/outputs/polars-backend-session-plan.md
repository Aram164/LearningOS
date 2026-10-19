# Polars backend engineering - session plan

Purpose: become fluent enough in Polars expressions and semantics to implement and verify logical dataframe operations in Stratum's Polars physical backend, while using pandas 3.0.2 as an explicit operation-level oracle.

Start today with Session 1, then Session 2 before returning to the `_selection_execs.py` clinic in Session 3. The order is intentional: the expression language and parity harness are prerequisites for solving DROPNA, selector, and runtime-operand problems without copying an answer.

## Session 1 - Backend contracts and parity harness

Specify observable pandas behavior at the operation boundary, target Polars 1.36.0, and create the cumulative executable harness used by every later session.

  1. Backend contract, version lock, and divergence axes
  2. Build the cumulative differential parity harness

## Session 2 - Polars expression fluency

Build and compose Polars expressions from intent, with explicit context, shape, schema, dependency, and failure reasoning before any backend operator clinic.

  1. Expression grammar, contexts, aliases, and sibling visibility
  2. Selectors and expression expansion
  3. Horizontal logic, folds, conditionals, and literals
  4. Translate pandas assign into native expression trees

## Session 3 - Selection backend clinic

Use the attached SelectionOp implementation as a real backend clinic: resolve runtime operands, translate parameters, compose native Polars expressions, and make fallbacks and unsupported behavior explicit.

  1. Selection and projection contracts
  2. HEAD, TAIL, and SAMPLE runtime operands
  3. DROP_DUPLICATES versus unique
  4. DROPNA from selectors and horizontal expressions

## Session 4 - Schema, dtypes, and missing values

Predict and preserve schema, coercion, null/NaN, construction, I/O, and failure behavior across the pinned backends.

  1. Construction, I/O, schema, and chunks
  2. Type promotion, coercion, and strictness
  3. Nulls, NaNs, and the missing-value model

## Session 5 - Ordering, text, and temporal operations

Make row order and determinism explicit, then translate string and temporal namespace operations without assuming pandas accessor names or calendar conventions carry over.

  1. Ordering, sorting, and determinism
  2. Strings, datetimes, and namespace translation

## Session 6 - Aggregation and windows

Implement grouped reductions and same-cardinality window transforms while preserving flags, shape, order, and missing-value semantics.

  1. GroupBy aggregation, counting, and de-duplication
  2. Aggregation signature and flag contract
  3. Windows and per-group transformations

## Session 7 - Joins, concatenation, and reshaping

Specify key cardinality, null matching, suffixes, coalescing, output order, and shape before lowering joins, concatenation, and reshape operations.

  1. Relational joins and key cardinality
  2. Build a pandas-Polars join compatibility layer
  3. Concatenation and reshaping

## Session 8 - Lazy plans, UDF boundaries, and Arrow interop

Read optimized plans, keep transformations expression-native, and recognize materialization, UDF, Arrow, chunk, and conversion boundaries that affect a physical backend.

  1. Lazy plans and optimizer literacy
  2. UDF fallbacks and native expression rewrites
  3. Arrow interop, chunks, and conversion costs

## Session 9 - Repeated Stratum backend implementation loop

Repeat the full logical-to-physical workflow across Selection, Map/Projection, Aggregation, and Join so the skill transfers to new ML-pipeline operations rather than remaining tied to one file.

  1. Trace capture, logical rewrite, selection, and execution
  2. Apply the backend implementation decision loop
  3. Transfer the loop across four logical families
  4. Failure policy and regression gate

## Session 10 - Capstone and controlled version transition

Implement one mirrored backend operation end to end, prove its contract with adversarial and generated tests, and keep future Polars-version assessment isolated from today's production baseline.

  1. Capstone - specify, implement, and prove a mirrored operation
  2. Property and adversarial stress pass
  3. Version transition lab - 1.36 baseline versus newer Polars
