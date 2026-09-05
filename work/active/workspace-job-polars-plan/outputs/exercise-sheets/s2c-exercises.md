# Session 2 · Stage 3 — Horizontal logic, folds, conditionals, and literals

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`. Several
results here are version-specific in a way that matters: one keyword the online
documentation may describe **does not exist** in 1.36.0, and `check.py` asserts
that too.

This is the stage that supplies the `dropna` predicate core for Session 3, so
the truth tables below are not academic — they become the lowering rule.

---

## Fixture F4 — the Kleene frame

Five rows, chosen to cover every pair a three-valued logic can produce:

```python
k = pl.DataFrame({
    "p": [True, True,  False, None,  None],
    "q": [True, None,  None,  False, None],
})
```

| row | `p` | `q` |
|---|---|---|
| 0 | T | T |
| 1 | T | null |
| 2 | F | null |
| 3 | null | F |
| 4 | null | null |

---

## Task 1 — The two truth tables

**Do.**

```python
k.select(pl.any_horizontal("p", "q"))
k.select(pl.all_horizontal("p", "q"))
```

**Predict.** Ten cells, before running. Rows 1 and 2 are the ones that separate
three-valued logic from "null means false": commit to both.

**Record.**

| row | `p` | `q` | `any_horizontal` | `all_horizontal` |
|---|---|---|---|---|
| 0 | T | T | | |
| 1 | T | null | | |
| 2 | F | null | | |
| 3 | null | F | | |
| 4 | null | null | | |

**Acceptance.** You can state both rules in the form *"the result is known when
…"*, and you can point at the two rows where a known result comes out of an
unknown input — which is the property that makes Kleene logic more than
null-propagation.

**Trap.** Expecting nulls to propagate everywhere. Row 1 of `any` and row 2 of
`all` both return a definite answer *despite* an unknown operand, because one
operand already decides the outcome. If your mental model is "null poisons
everything", both cells will be wrong.

---

## Task 2 — The keyword that is not there

**Do.**

```python
k.select(pl.any_horizontal("p", "q", ignore_nulls=False))
```

**Predict.** What this returns.

**Acceptance.** You have recorded the actual outcome and drawn the general
conclusion: a keyword you read about online is not a keyword this build has, and
the pinned environment is the authority. Then find where the null behaviour *is*
controllable and record the difference.

**Trap.** Reading the current online user guide and writing the lowering rule
from it. The live documentation may describe a release ahead of Stratum's
lockfile — this is the concrete instance of the rule the whole module states
abstractly.

---

## Task 3 — `fold` versus `sum_horizontal`, and the seed that types the result

**Do.** Same data, four calls:

```python
z = pl.DataFrame({"a": [1, None], "b": [2, 3]})
z.select(pl.sum_horizontal("a", "b"))
z.select(pl.fold(0,   lambda acc, x: acc + x, pl.all()).alias("f"))
pl.DataFrame({"a": [1], "b": [2]}).select(pl.fold(0,   lambda acc, x: acc + x, pl.all()).alias("f")).dtypes
pl.DataFrame({"a": [1], "b": [2]}).select(pl.fold(0.0, lambda acc, x: acc + x, pl.all()).alias("f")).dtypes
```

**Predict.** Row 1 of the first two calls (the row containing the null) — the
same arithmetic, the same data, and the two calls do not agree. And the dtype of
the last two: both inputs are `Int64`.

**Record.**

| call | row 0 | row 1 | dtype |
|---|---|---|---|
| `sum_horizontal` | | | |
| `fold(0, ...)` | | | |
| `fold(0.0, ...)` | — | — | |

**Acceptance.** You can say which of the two is the right primitive for a
`sum(skipna=True)` translation and which for `skipna=False`, with the row-1
result as your evidence. And you can state where a fold's output dtype comes
from.

**Trap.** The seed. `pl.fold(0, ...)` over two `Int64` columns does **not**
produce `Int64` — the literal `0` is not `Int64`, and the accumulator's type
wins. A translation that seeds with `0` silently narrows every horizontal sum it
emits, and narrowing is the kind of bug that only appears at scale.

---

## Task 4 — The empty subset

`dropna(subset=[...])` can be handed a subset that selects nothing. A horizontal
predicate over zero columns is the degenerate case, and it has to be handled
where the lowering happens, not discovered in production.

**Do.**

```python
pl.DataFrame({"a": [1]}).select(pl.any_horizontal())
pl.DataFrame({"a": [1]}).select(pl.all_horizontal())
```

**Predict.** For each: a value, or an exception? If a value, which — `any` over
nothing and `all` over nothing have conventional answers in logic (`False` and
`True`), so predict whether the library agrees with the convention.

**Acceptance.** You have the exception type and message, and you can explain the
*reason* it is an error rather than the conventional answer — the message names
it. Then write the guard your `dropna` lowering needs, with a decision recorded
for what an empty subset should mean at the operation boundary: all rows kept,
all rows dropped, or a raised error.

**Trap.** Assuming the identity elements. Both raise, and the reason has nothing
to do with logic: a fold over zero expressions cannot know its output height.

---

## Task 5 — Branch validity in `when/then/otherwise`

Polars requires every branch to be valid, not merely every *reachable* branch —
with one exception worth knowing.

**Do.** In order:

```python
w = pl.DataFrame({"a": [1, 2, 3], "s": ["x", "y", "z"]})

# 5a — a branch that is never selected, and is invalid
w.select(pl.when(pl.col("a") > 100).then(pl.col("s").cast(pl.Int64)).otherwise(0))

# 5b — the same, with a constant predicate
w.select(pl.when(pl.lit(True)).then(pl.col("a")).otherwise(pl.col("s").cast(pl.Int64)))

# 5c — non-strict cast
w.select(pl.when(pl.col("a") > 100).then(pl.col("s").cast(pl.Int64, strict=False)).otherwise(0))

# 5d — branches of different types, both valid
w.select(pl.when(pl.col("a") > 1).then(pl.col("a")).otherwise(pl.col("s")))

# 5e — no otherwise
w.select(pl.when(pl.col("a") > 1).then(pl.col("a")))

# 5f — types with no common supertype
w.select(pl.when(pl.col("a") > 1).then(pl.col("a")).otherwise(pl.lit([1, 2])))
```

**Predict.** Which of the six raise. Then, for 5d, predict the output **dtype** —
one branch is `Int64` and the other is `String`.

**Record.**

| case | outcome | dtype of result |
|---|---|---|
| 5a | | |
| 5b | | |
| 5c | | |
| 5d | | |
| 5e | | |
| 5f | | |

**Acceptance.** You can state the branch-validity rule *and* its exception, and
you can say why 5d is more dangerous than 5a even though 5a is the one that
raises.

**Trap.** 5d. There is no error: Polars finds a common supertype and coerces.
`Int64` and `String` have one — `String` — so a conditional over a numeric
column and a text column returns text, and the numbers arrive stringified.
Compare with pandas' `Series.where`, where the corresponding coercion goes to
`float64` via NaN, and note that both libraries silently changed the dtype in
different directions.

---

## Task 6 — Derive the `dropna` predicate core

The payload of the stage. Build the three predicates over a **dynamic** subset,
with no Python row loop:

| pandas | predicate to build |
|---|---|
| `dropna(how="any", subset=S)` | keep rows where no column in `S` is null |
| `dropna(how="all", subset=S)` | keep rows where not every column in `S` is null |
| `dropna(thresh=n, subset=S)` | keep rows with at least `n` non-null values in `S` |

**Do.** Implement all three as expressions parameterized by a selector, then
test each against: all-non-null rows, all-null rows, partially-null rows, a
`NaN` that is not a null (Session 1, Task 2), an empty subset (Task 4 above), and
`n = 0` and `n > len(S)` for `thresh`.

**Record.** For each of the three, on each of the six inputs: rows kept by
pandas, rows kept by your expression, and whether they agree.

**Acceptance.** All three agree with pandas on all six inputs, or a divergence is
recorded as a harness case with a reason. `thresh` is implemented as a count
comparison rather than as a chain of `any`/`all`, and the `NaN` row is the one
that proves your predicate distinguishes "missing" from "NaN" — or that it
does not, which is a decision you must have made rather than inherited.

**Trap.** Implementing `thresh` with `sum_horizontal` over `is_null()`. It works
until the seed-dtype problem from Task 3 bites, or until the subset is empty.
Count non-nulls, compare to `n`, and guard the empty case.

---

## Answer key

### Task 1

| row | `p` | `q` | `any_horizontal` | `all_horizontal` |
|---|---|---|---|---|
| 0 | T | T | `True` | `True` |
| 1 | T | null | `True` | `null` |
| 2 | F | null | `null` | `False` |
| 3 | null | F | `null` | `False` |
| 4 | null | null | `null` | `null` |

`any` is known as soon as one operand is `True`; `all` is known as soon as one
operand is `False`. Everything else with an unknown operand is unknown. Rows 1
and 2 are the two cells where a definite answer survives an unknown input.

### Task 2

```
pl.any_horizontal("p", "q", ignore_nulls=False)
→ TypeError: any_horizontal() got an unexpected keyword argument 'ignore_nulls'
```

`all_horizontal` behaves the same. The keyword is not part of this build's
signature, so any rule written from a page that documents it is untestable here.
Where null handling *is* controllable in 1.36.0: `Series.all`/`Series.any` take
`ignore_nulls`, and `GroupBy.first`/`last` take it with the opposite default —
which is a Session 6 finding, and a reminder that "the null keyword" is not one
uniform thing across the API.

### Task 3

| call | row 0 | row 1 | dtype |
|---|---|---|---|
| `sum_horizontal("a","b")` | `3` | `3` | Int64 |
| `fold(0, add, all())` | `3` | `null` | **Int32** |
| `fold(0.0, add, all())` | — | — | Float64 |

Same data, same arithmetic, different answers on row 1: `sum_horizontal`
skips the null, `fold` propagates it. So `sum_horizontal` is the
`skipna=True` primitive and `fold` is the `skipna=False` one — that is the
translation rule, and it is a *behavioural* difference rather than a stylistic
choice between two ways of adding columns.

The dtype comes from the **accumulator**, i.e. from the seed literal. Seeding an
integer fold with `0` yields `Int32` even though both inputs are `Int64`. Seed
with an explicitly typed literal — `pl.lit(0, dtype=pl.Int64)` — when the output
type is part of a contract.

### Task 4

Both raise:

```
ComputeError: cannot return empty fold because the number of output rows is unknown
```

Not a logic decision. A horizontal helper is a fold over its argument
expressions, and with zero arguments there is nothing to derive the output height
from — the frame's height is not implied. The conventional identities (`False`
for `any`, `True` for `all`) are therefore *your* decision to make at the
operation boundary, and the guard belongs in the lowering, before the expression
is built.

### Task 5

| case | outcome |
|---|---|
| 5a | raises `InvalidOperationError`: *conversion from `str` to `i64` failed in column 's' for 3 out of 3 values* — **even though the branch is never selected** |
| 5b | `[1, 2, 3]` — **no error**; the constant predicate is folded away and the invalid branch is eliminated before evaluation |
| 5c | `[0, 0, 0]` — `strict=False` turns the failed cast into nulls, so the branch is valid |
| 5d | `['x', '2', '3']`, dtype **String** — no error, silent stringification |
| 5e | `[null, 2, 3]` — a missing `otherwise` fills with null |
| 5f | raises `SchemaError`: *failed to determine supertype of i64 and list[i64]* |

The rule: every branch must be independently valid, because validity is checked
against the whole column and not against the selected rows. The exception is 5b —
a predicate that constant-folds lets the optimizer delete the branch first, so
the guarantee is about *evaluated* branches. Do not rely on that: it means a
plan that works with a literal predicate can start failing when the predicate
becomes data-dependent.

5d is the dangerous one precisely because it does not raise. For comparison,
pandas `pd.Series([1,2]).where(pd.Series([False,True]))` yields dtype `float64` —
promoting through NaN. Both libraries silently retype a conditional; they do it
in different directions, so this pair belongs in the harness.

### Task 6 — the divergence is the answer

The acceptance condition says "all three agree with pandas, **or** a divergence
is recorded". On this fixture it is the second. Using

```python
subset   = cs.by_name("a", "b")
non_null = pl.sum_horizontal(subset.is_not_null().cast(pl.Int64))
```

on

| row | `a` | `b` | non-nulls |
|---|---|---|---|
| 0 | 1.0 | 2.0 | 2 |
| 1 | null | 3.0 | 1 |
| 2 | null | null | 0 |
| 3 | 1.0 | **NaN** | 2 |
| 4 | null | null | 0 |

| predicate | Polars rows kept | pandas rows kept |
|---|---|---|
| `how="any"` | **2** (rows 0 and 3) | **1** (row 0) |
| `how="all"` | 3 | 3 |
| `thresh=2` | **2** | **1** |

Row 3 is the whole finding. Its `b` is a genuine floating-point `NaN`, not a
missing value: `is_null()` says `False`, so the Polars predicate keeps the row.
pandas has no way to agree — `to_pandas()` renders both null and NaN as `NaN`,
and `dropna` drops the row. The two implementations are each correct about their
own data model, and they return different row counts on the same frame.

So `dropna` is **not** a syntax-only translation. The lowering owes an explicit
decision recorded at the operation boundary: does `dropna` mean *drop missing*
(Polars `is_null`) or *drop missing-or-NaN* (pandas)? Whichever you choose,
`how="all"` will keep agreeing and hide the choice — which is why the harness
case must be the `how="any"` one.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
