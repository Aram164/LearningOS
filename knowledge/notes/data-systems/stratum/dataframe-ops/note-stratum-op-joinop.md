---
id: note-stratum-op-joinop
type: note
title: "JoinOp — binary df.merge/df.join"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-join-family]
sources: []
---

# JoinOp

> A binary relational join (`df.merge(...)` / `df.join(...)`). Family `"Join"`.

**Created by** — MethodCallOp `method ∈ {join, merge}` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), via
`make_join_op`.

## Node shape
- `JoinOp(Op)`, `logical_family = "Join"`.
- `fields = ["how", "left_on", "right_on", "left_index", "right_index", "suffixes"]`.
- `output_type = FRAME`; `name = ""` (the family label renders cleanly on its own).

## How it's built (`make_join_op`)
- The first positional arg is the right/other frame (already in `op.inputs`).
- Normalizes the two pandas conventions into `JoinOp` fields:
  - **merge**: positional order `_MERGE_POSITIONAL`; a bare `on` → both `left_on`
    and `right_on`; default `suffixes = ("_x", "_y")`.
  - **join**: positional order `_JOIN_POSITIONAL`; defaults `how="left"`, index-based;
    `on` → `left_on` + `right_index=True`; `lsuffix`/`rsuffix` → `suffixes`; default
    `suffixes = ("", "")`.
- `sort=True` → `NotImplementedError`; unknown kwargs → `NotImplementedError`.
- Single join: `JoinOp(**join_kwargs, inputs=op.inputs, outputs=op.outputs)` +
  `replace_output_of_inputs`.

## Chained joins
`df.join([df2, df3, ...])` (or `len(op.inputs) > 2`) → `_make_chained_join_op`
unrolls into a **chain of binary JoinOps** (`inputs=[prev, right]` each), returning
the final one; only the last carries `op.outputs`. Chained links are always
index-based. Duplicate right-hand frames raise `ValueError`.

## Gotchas
- `merge` vs `join` differ in default `how`, index vs key matching, and suffix
  spelling — all reconciled inside `make_join_op`.


## Legacy Job provenance

### component

stratum/optimizer/ir/_join_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
