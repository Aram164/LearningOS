# Session 2 · Stage 1 — Expression grammar, contexts, aliases, and sibling visibility

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`. Run
`check.py` after attempting; it re-executes every expected value here.

The one idea this stage installs: **an expression is a value, not a statement.**
`pl.col("a") * 2` builds a tree and executes nothing. Where you put that tree —
`select`, `with_columns`, `filter`, `group_by().agg()` — decides its output
width, its output height, and what other columns it can see. Everything below is
a consequence.

---

## Fixture F2

```python
df = pl.DataFrame({
    "a": [1, 2, 3],       # Int64
    "b": [1.5, 2.5, 3.5], # Float64
    "s": ["x", "y", "z"], # String
    "d": [None, 1, 2],    # Int64 with a null
})
```

---

## Task 1 — Sibling visibility: the rule that decides how `assign` lowers

This is the single most consequential divergence in the session, and it is worth
discovering by making it fail.

**Do.** Run all four:

```python
# 1
df.with_columns(z=pl.col("a") * 2, w=pl.col("z") + 1)
# 2
df.with_columns(z=pl.col("a") * 2).with_columns(w=pl.col("z") + 1)
# 3
pd.DataFrame({"a": [1, 2, 3]}).assign(z=lambda t: t.a * 2, w=lambda t: t.z + 1)
# 4
pd.DataFrame({"a": [1, 2, 3]}).assign(a=lambda t: t.a * 10, b=lambda t: t.a + 1)
```

**Predict.** For (1), whether it succeeds. For (4), whether `b` is computed from
the *old* `a` or the *new* one — the answer determines whether an overwrite in
the middle of an assign chain can be reordered by a lowering pass.

**Record.**

| # | outcome | what it proves about the context |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |

**Acceptance.** You can state the rule in one sentence each way — what
`with_columns` evaluates its expressions against, and what `assign` evaluates
its kwargs against — and name the consequence for a lowering pass: which pandas
assign chains collapse into **one** `with_columns` call and which must be
**staged** into several.

**Trap.** Concluding "Polars needs two calls, fine". The real finding is that
pandas' `assign` is *sequential*, so the assign entries form a dependency chain,
and a translator must compute that chain rather than emit the entries in order
and hope.

---

## Task 2 — Contexts change shape, not just syntax

**Do.** For each row, predict the output **shape** before running:

```python
df.select(pl.col("a") * 2)                                  # (?, ?)
df.with_columns(pl.col("a") * 2)                            # (?, ?)
df.select(pl.col("a"), pl.col("a").sum().alias("t"))        # (?, ?)
df.select(pl.col("a"), pl.col("a").head(2).alias("h"))      # (?, ?)
df.filter(pl.col("a") > 1)                                  # (?, ?)
df.select(pl.col("^(a|s)$"))                                # which columns?
df.with_columns(pl.col("^(a|s)$").alias("q"))               # ?
df.with_columns(pl.col("a", "s").name.suffix("_2"))         # which columns?
```

**Record.** A table of expression → context → output width → output height, plus
the two rows that raise and the exception type for each.

**Acceptance.** You can predict output width and height for an unseen expression
in each of the four contexts, and you can state the rule that separates the
`sum()` row from the `head(2)` row — both return fewer than three values, and
only one of them is legal.

**Trap.** `alias` on a multi-output expression. `pl.col("^(a|s)$")` produces two
columns; one `alias` cannot name both, and the error you get names duplication
rather than arity, which sends people looking in the wrong place.

---

## Task 3 — Read the tree instead of guessing at it

The migrated version of this stage said "build and print an Expr tree" without
saying how. Here is how.

**Do.**

```python
e = (pl.col("a") * 2).alias("z")
e.meta.output_name()             # what column will this produce?
e.meta.root_names()              # which input columns does it read?
print(e.meta.tree_format(return_as_string=True))
pl.col("^a.*$").meta.has_multiple_outputs()
```

Then, on the lazy side:

```python
df.lazy().select(pl.col("a") * 2).collect_schema()   # schema without executing
df.lazy().select(pl.col("zz"))                       # builds fine
df.lazy().select(pl.col("zz")).collect()             # now it fails
```

**Predict.** At which of the last two lines does the missing column become an
error?

**Record.** For three expressions of your own — one single-output, one
multi-output, one containing an aggregation — the four `meta` answers and the
`collect_schema()` result.

**Acceptance.** You can answer "what columns will this produce, and from what
inputs" for an expression **without executing it**, using `meta` and
`collect_schema`. This is the capability a lowering pass needs, since it must
decide the output schema before any data exists.

**Trap.** Treating a `LazyFrame` construction error as impossible. Building is
lazy, so a wrong column name survives until `collect()` — and the error then
arrives with a *resolved plan* attached, which is more informative than the eager
error and is the reason to prefer lazy while developing a translation.

---

## Task 4 — Eight `assign` pipelines, lowered

**Do.** Translate each into Polars, then run both sides and compare with the
Stage 2 harness (Session 1). One row per pipeline:

| # | pandas | the question it asks |
|---|---|---|
| 1 | `assign(c=5)` | scalar broadcast |
| 2 | `assign(c=lambda t: t.a + t.b)` | two-column arithmetic, and the result dtype |
| 3 | `assign(a=lambda t: t.a * 10)` | overwrite in place |
| 4 | `assign(z=lambda t: t.a * 2, w=lambda t: t.z + 1)` | sibling dependency → how many contexts? |
| 5 | `assign(a=lambda t: t.a * 10, b=lambda t: t.a + 1)` | overwrite *then* read the overwritten name |
| 6 | `assign(c=[1, 2])` on three rows | length mismatch: which error, which side |
| 7 | `assign(c=lambda t: t.s.str.upper())` | namespace translation |
| 8 | `assign(c=lambda t: t.a.map(some_python_fn))` | the opaque case |
| | | |

**Predict.** Before translating: how many of the eight need more than one
`with_columns` context? Write the number down.

**Record.** For each: the Polars expression, the number of contexts required, the
classification — **native**, **staged** (needs more than one context), or
**fallback** (cannot be expressed as an expression tree) — and the observed
dtype on both sides.

**Acceptance.** Eight rows, each with a classification and an executed
comparison. Row 5 and row 4 are classified differently, and you can say why in
one sentence. Row 8 is identified as fallback *before* you try to make it work.

**Trap.** Row 2's dtype. `a` is `Int64` and `b` is `Float64`; check what each
library produces and whether they agree, then check row 1 (`pl.lit(1)` against a
`Float64` column) for the same question in the other direction.

---

## Task 5 — Closed-book translation table

**Do.** Without references, classify twenty operations you have used this stage
as **projection** (produces columns from columns), **map** (element-wise),
**metadata** (renames/reorders/retypes without computing values), or
**fallback**. Then check each against the library.

**Acceptance.** Twenty rows; every misclassification kept in the file with a
note on what you had assumed. The misclassifications are the deliverable —
they are the operations whose lowering you would have got wrong.

---

## Answer key

### Task 1

| # | result |
|---|---|
| 1 | raises `ColumnNotFoundError`: *unable to find column "z"; valid columns: ["a", "b", "s", "d"]* |
| 2 | `w = [3, 5, 7]` |
| 3 | `w = [3, 5, 7]` |
| 4 | `a = [10, 20, 30]`, `b = [11, 21, 31]` |

`with_columns` evaluates **every** expression against the frame as it was on
entry — the expressions are independent and may run in parallel, so a sibling
created in the same call does not exist yet. `assign` evaluates its kwargs
**in order against the frame accumulated so far**, which is why (4) computes `b`
from the *new* `a`.

The lowering consequence: an assign chain collapses into one `with_columns` only
when no entry reads a name written by an earlier entry in the same chain. Build
the dependency graph over the entries, then emit one context per layer. Row (4)
shows that an overwrite counts as a write for this purpose, so the graph is over
*names*, not over new columns.

### Task 2

| expression | context | shape / columns |
|---|---|---|
| `pl.col("a")*2` | `select` | `(3, 1)` |
| `pl.col("a")*2` | `with_columns` | `(3, 4)` |
| `col("a"), col("a").sum().alias("t")` | `select` | `(3, 2)`, `t = [6, 6, 6]` |
| `col("a"), col("a").head(2).alias("h")` | `select` | raises `ShapeError`: *Series length 2 doesn't match the DataFrame height of 3* |
| `filter(col("a") > 1)` | `filter` | `(2, 4)` |
| `select(col("^(a|s)$"))` | `select` | `['a', 's']` |
| `with_columns(col("^(a|s)$").alias("q"))` | `with_columns` | raises `ComputeError`: *the name 'q' … is duplicate* |
| `with_columns(col("a","s").name.suffix("_2"))` | `with_columns` | `['a', 's', 'a_2', 's_2']` |

The rule separating `sum()` from `head(2)`: a **scalar** broadcasts to the
frame's height, any other length must equal it. `sum()` returns one value and is
stretched; `head(2)` returns two and is refused. So "returns fewer rows" is not
one category — length 1 is special.

### Task 3

`meta.output_name()` → `'z'`; `meta.root_names()` → `['a']`;
`tree_format` prints the binary `*` node with its two children;
`pl.col("^a.*$").meta.has_multiple_outputs()` → `True`.

`collect_schema()` on `select(col("a")*2)` → `Schema({'a': Int64})` — resolved
without touching data. `df.lazy().select(pl.col("zz"))` **builds**; the
`ColumnNotFoundError` arrives at `collect()`, together with the resolved plan and
a `---> FAILED HERE RESOLVING 'sink' <---` marker.

### Task 4 — the two rows to check twice

**Row 6.** pandas raises `ValueError`: *Length of values (2) does not match
length of index (3)*. The Polars analogue — adding a two-element `pl.Series` to a
three-row frame — raises `ShapeError`: *unable to add a column of length 2 to a
DataFrame of height 3*. Same finding, different exception type, which is a
harness case (Session 1, seed case 12's pattern).

**Rows 4 vs 5.** Both need two contexts, and for different reasons: row 4
because `w` reads a name created in the same call, row 5 because `b` must read
the *overwritten* `a`. Emitting row 5 as a single `with_columns` does not raise —
it silently computes `b` from the original `a`. A wrong answer with no error is
worse than row 4's exception, and it is the case a naive translator gets wrong.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
