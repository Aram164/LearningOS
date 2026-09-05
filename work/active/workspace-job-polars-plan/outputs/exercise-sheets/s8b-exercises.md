# Session 8 · Stage 2 — UDF fallbacks and native expression rewrites

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

A UDF is not a performance problem because Python is slow. It is a problem
because it is **opaque to the optimizer**: the passes from the previous stage
cannot see which columns it reads or what it produces, so several of them stop
firing. This stage builds the ladder from "works" to "native".

---

# Part A — Polars on its own terms

## Task A1 — The five rungs

Polars offers several ways to run your own logic. They are not interchangeable.

| rung | form | granularity |
|---|---|---|
| 1 | native expression | whole column, vectorized |
| 2 | NumPy ufunc on an expression | whole column, vectorized |
| 3 | `map_batches` | whole Series at once |
| 4 | `map_elements` | one value at a time |
| 5 | `map_elements` over a `struct` | one row at a time |

**Do.** Implement the same operation — "add one" — at every rung. Then implement
"concatenate two columns with a separator" at rungs 1, 3, and 5.

**Acceptance.** You can state what each rung costs and what it buys, and you can
name the rung for an unfamiliar task. Rung 5 is the one people reach for first
and should reach for last: it is how you write a row loop without noticing.

**Trap.** `map_batches` receiving a Series and returning something of a
different length. Try it: return `x.head(1)` from a `map_batches` on a 3-row
frame and look at the output height. It does **not** raise.

## Task A2 — Let the library grade your work

**Do.** Run a `map_elements` with an obvious native equivalent and read the
warning.

**Acceptance.** You have the warning class and the suggested rewrite. Polars
prints the native expression it thinks you meant.

**How to use it.** Treat `PolarsInefficientMapWarning` as a linter, not noise —
but verify the suggestion rather than pasting it. The rewrite is derived from
your lambda's bytecode and is a suggestion about *shape*, not a proof of
semantic equivalence, particularly around nulls: a native expression propagates
missingness where a Python lambda may have been called with `None` and returned
something.

## Task A3 — `return_dtype`, and what happens without it

**Do.**

```python
s.select(pl.col("a").map_elements(lambda v: v + 1))                      # no dtype
s.select(pl.col("a").map_elements(lambda v: v + 1, return_dtype=pl.Int64))
s.select(pl.col("a").map_elements(lambda v: str(v), return_dtype=pl.Int64))
```

**Acceptance.** You can say what Polars does when `return_dtype` is missing (it
infers from the first non-null result) and what happens when the declared dtype
and the returned value disagree. The third line's failure mode is the one to
remember.

## Task A4 — Show that a UDF blinds the optimizer

**Do.** Build two lazy queries that select one column from a three-column frame:
one where the selection is a native expression, one where it goes through
`map_elements`. Compare the `PROJECT n/3 COLUMNS` line in each plan.

**Acceptance.** A measured statement about what the optimizer can still do
either side of a UDF boundary — this is the concrete version of the claim in the
stage's opening paragraph, and you should verify it rather than repeat it.

---

# Part B — The pandas contract

## Task B1 — Five `apply`/`map` tasks, three ways each

**Do.** Write five pandas tasks using `apply` or `map`. For each produce: the
literal Polars UDF translation, and the idiomatic native expression.

Suggested five, chosen so the answers differ:

1. `df.a.map(lambda v: v * 2)` — trivially native
2. `df.apply(lambda r: r.a + r.b, axis=1)` — row-wise
3. `df.a.apply(lambda v: my_lookup[v])` — dictionary lookup
4. `df.a.apply(lambda v: expensive_io(v))` — genuinely opaque
5. `df.groupby("k").a.apply(lambda s: s.max() - s.min())` — grouped

**Record.** For each: literal translation, native form, and a timing of both on
a frame of ~1e6 rows.

**Acceptance.** Five rows with measurements. #3 has a native form most people do
not know (`replace_strict`), #5 has an obvious one, and #4 is the honest
fallback — name it as such rather than forcing it.

**Trap.** `df.apply(..., axis=1)` is the pandas idiom with the worst translation.
Its literal form is rung 5, and its native form is usually a plain expression
over the two columns. If a captured pipeline is full of `axis=1`, that is where
the backend's advantage is being thrown away.

## Task B2 — The elimination ledger

**Do.** For every UDF you translated, record: before, after, both timings, and
whether the semantics are identical or merely equivalent on the tested data.

**Acceptance.** A ledger with a *semantics* column, not just a speed column. A
rewrite that is faster and subtly different is a bug you have optimized into
production.

---

# Part C — The lowering decision

## Task C1 — Classify ten captured functions

**Do.** Ten functions from real captured code. Assign each to one rung, or to
**unsupported**.

**Acceptance.** Ten assignments with a stated reason. The rule to apply: the
question is not whether Python code appears, it is whether the *operation* has an
expression equivalent.

## Task C2 — When a fallback is correct and still wrong

**Do.** Write the paragraph, for your own design notes, explaining when a
fallback preserves semantics but destroys the reason for having the backend.
Include the optimizer consequence from Task A4.

**Acceptance.** A statement your future self can act on: the condition under
which the lowering should *refuse* rather than fall back, and who decides.

---

## Answer key

### Task A1 / A3

| call | result |
|---|---|
| `map_elements(lambda v: v + 1)` | works; dtype `Int64` inferred |
| `map_elements(..., return_dtype=pl.Int64)` | same, no inference, no warning about the dtype |
| `map_elements(lambda v: str(v), return_dtype=pl.Int64)` | raises `SchemaError: unexpected value while building Series of type Int64; found value of type String: "1"` |
| `map_batches(lambda x: x * 2)` | `[2, 4, 6]` |
| `map_batches(lambda x: x.head(1))` on 3 rows | **height 1** — no error |
| `np.sqrt(series)` | works directly; ufuncs are rung 2 |
| `pl.struct("a","b").map_elements(lambda r: r["a"] + r["b"], return_dtype=pl.Int64)` | `[3]` — the row-wise rung |

The `map_batches` length case is the one to remember: returning a
differently-sized Series silently changes the frame's height. There is no
contract enforced on the returned length, so a `map_batches` that filters is a
`map_batches` that reshapes the frame.

### Task A2

The warning is `PolarsInefficientMapWarning`, and it prints the rewrite:

```
Expr.map_elements is significantly slower than the native expressions API.
Only use if you absolutely CANNOT implement your logic otherwise.
Replace this expression...
  - pl.col("a").map_elements(lambda v: ...)
with this one instead:
  + pl.col("a") + 1
```

It even handles `str(v)` → `pl.col("a").cast(pl.String)`. Useful, and derived
from bytecode — so check it against nulls before adopting it.

### Task B1 — the five, with their native forms

```python
# 1  pl.col("a") * 2
# 2  pl.col("a") + pl.col("b")                     ← not a row UDF
# 3  pl.col("a").replace_strict(my_lookup)          ← the one people miss
# 4  no native form — rung 3 or 4, and say so
# 5  (pl.col("a").max() - pl.col("a").min()).over("k")
```

`#5` is a Session 6 `over` in disguise, which is worth noticing: a grouped
`apply` in pandas is almost always a window expression in Polars, and translating
it as a UDF preserves the answer while discarding the entire reason to use the
backend.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
