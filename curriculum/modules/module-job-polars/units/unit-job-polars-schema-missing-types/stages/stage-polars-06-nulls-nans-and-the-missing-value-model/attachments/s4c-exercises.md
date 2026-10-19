# Session 4 · Stage 3 — Nulls, NaNs, and the missing-value model

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Session 1 established that `null` and `NaN` are different things. Session 2
turned that into predicates. This stage settles the whole model: what missing
does to comparison, to grouping, to membership, and to sorting — and where the
two libraries make *opposite default choices*.

---

# Part A — Polars on its own terms

## Task A1 — Three-valued logic, all the way down

**Do.** Predict every result, then run:

```python
d = pl.DataFrame({"a": [1, None]})
d.select(pl.col("a") + 1)                       # arithmetic
d.select(pl.col("a") > 0)                       # comparison
d.select(pl.col("a") == pl.col("a"))            # a null compared to itself
d.select(pl.col("a").eq_missing(pl.col("a")))   # the other equality
d.filter(pl.col("a") > 0)                       # how many rows survive?
d.select(pl.col("a").is_in([1, 2]))
d.select(pl.col("a").is_in([1, None]))
```

**Record.**

| expression | row 0 | row 1 |
|---|---|---|

**Acceptance.** You can state the general rule — *an operation on an unknown
value produces an unknown result* — and you can name the two calls on this list
that deliberately break it, and why each exists.

**Trap.** `null == null` is `null`, not `True`. That is correct three-valued
logic and it is why `eq_missing` exists: sometimes you want to ask "are these the
same, treating missing as a value", and ordinary equality cannot answer it.
Every join key comparison and every dedup depends on which of the two you mean.

## Task A2 — Where Polars decides missing *is* a value

Three-valued logic is not applied everywhere. Find where it stops.

**Do.**

```python
pl.DataFrame({"k": [None, "a", None]}).group_by("k").len()
pl.DataFrame({"k": [None, "a", None]}).unique()
pl.Series([2, None, 1]).sort()
pl.Series([None, None]).n_unique()
```

**Acceptance.** Four answers. You can state, for each, whether missing was
treated as a value or as unknown — and you can say why an engine has no choice
about grouping and sorting, even though it does about comparison.

**Trap.** These are not inconsistencies. A group-by must put every row
somewhere and a sort must put every row in an order; "unknown" is not a
placement. The three-valued rule governs *computed answers*, and grouping and
ordering are *placements*.

## Task A3 — The verbs

**Do.** On `[1.0, None, 3.0, NaN]`:

```python
.null_count()        .is_null()      .is_not_null()
.is_nan()            .is_not_nan()
.fill_null(0)        .fill_null(strategy="forward")   .fill_null(strategy="mean")
.fill_nan(None)      .drop_nulls()
.interpolate()
```

**Acceptance.** You can complete this sentence without hedging: *"To make my
data match pandas' idea of missing, I …"* — one call, from this list.

---

# Part B — The pandas contract

## Task B1 — The default that flips

**Do.**

```python
pl.DataFrame({"k": [None, "a", None], "v": [1, 1, 1]}).group_by("k").agg(pl.col("v").sum())
pd.DataFrame({"k": [None, "a", None], "v": [1, 1, 1]}).groupby("k")["v"].sum()
pd.DataFrame({"k": [None, "a", None], "v": [1, 1, 1]}).groupby("k", dropna=False)["v"].sum()
```

**Predict.** How many groups each returns.

**Record.**

| call | groups | null group present? |
|---|---|---|

**Acceptance.** Recorded as a harness case, class **semantic**, with the
translation rule stated: which pandas argument corresponds to Polars' behaviour,
and what a translation must emit when that argument is *absent* from the captured
call.

**Trap.** pandas defaults to `dropna=True` and therefore **discards rows** whose
key is missing. Polars keeps them as a null group. A `groupby` translated
literally does not lose an error — it loses rows, and the totals still look
plausible.

## Task B2 — Sorting: the other flipped default

**Do.** `sort` a Series containing a null in both libraries, with defaults.

**Acceptance.** You can state both defaults and both opt-outs
(`na_position=`, `nulls_last=`). Session 1 recorded this; here you attach it to
the missing-value model rather than to the sort operation, because it is the same
question: does missing come before or after everything else?

## Task B3 — Comparison and the identity question

**Do.** `pd.Series([None]) == pd.Series([None])` and the Polars equivalents from
Task A1.

**Acceptance.** Three results — pandas `False`, Polars `null`, Polars
`eq_missing` `True` — and a statement of which one a *join* should use. Then
check what your join actually does, in Session 7.

---

# Part C — The lowering decision

## Task C1 — One missing-value policy, stated once

**Do.** Write the policy as a document with five entries. For each, the pandas
behaviour, the Polars behaviour, the chosen Stratum semantics, and the mechanism:

1. Comparison of two missing values.
2. Grouping by a column containing missing values.
3. Sorting placement.
4. Membership (`is_in` / `isin`).
5. `NaN` in a float column that is not missing.

**Acceptance.** Five entries. Each names a *mechanism* — a keyword, a
normalization call, or an explicit refusal — not just an intention. Entry 5
refers back to the `fill_nan(None)` sandwich from Session 3 and states where in
the pipeline it is applied, because applying it in two places is how the policy
starts disagreeing with itself.

---

## Answer key

### Task A1

| expression | row 0 | row 1 |
|---|---|---|
| `a + 1` | `2` | `null` |
| `a > 0` | `True` | `null` |
| `a == a` | `True` | **`null`** |
| `a.eq_missing(a)` | `True` | **`True`** |
| `filter(a > 0)` | 1 row survives (of 2) | |
| `a.is_in([1, 2])` | `True` | `null` |
| `a.is_in([1, None])` | `True` | **`null`** |

The last row is the one people get wrong: putting `None` in the list does *not*
make the null row match. Membership is a comparison, and comparing to unknown is
unknown. `eq_missing` is the deliberate exception — it is the "treat missing as a
value" equality, and it is the one a dedup or a null-matching join needs.

`filter` keeps only rows where the predicate is `True`; `null` is not `True`, so
the unknown row is dropped. pandas does the same with `NaN`, so this one agrees.

### Task A2

| call | result | missing treated as |
|---|---|---|
| `group_by("k").len()` | two groups: `a` → 1, `null` → 2 | **a value** |
| `unique()` | 2 rows | **a value** |
| `Series([2, None, 1]).sort()` | `[None, 1, 2]` | **a value**, ordered first |
| `Series([None, None]).n_unique()` | `1` | **a value** |

A placement operation must place every row. Only *computed answers* follow
three-valued logic.

### Task B1

| call | groups |
|---|---|
| Polars `group_by("k")` | 2 — including a `null` group with sum 2 |
| pandas `groupby("k")` | **1** — `{'a': 1}`; the two null-key rows are gone |
| pandas `groupby("k", dropna=False)` | 2 — `{'a': 1, nan: 2}` |

The translation rule: Polars' behaviour corresponds to pandas
`dropna=False`. A captured `groupby` that does *not* mention `dropna` is
therefore requesting `dropna=True`, which Polars has no keyword for — it must be
emitted as an explicit filter before the grouping. Getting this wrong does not
raise; it silently includes rows pandas would have discarded, and the group
totals stay plausible.

### Task B2 / B3

`pd.Series([2,None,1]).sort_values()` → `[1.0, 2.0, nan]` (`na_position="last"`).
`pl.Series([2,None,1]).sort()` → `[None, 1, 2]` (`nulls_last=False`).

`pd.Series([None]) == pd.Series([None])` → `False`. pandas' comparison gives a
definite *wrong* answer where Polars gives `null` and `eq_missing` gives `True`.
Three libraries' worth of behaviour from one question, which is why the join
stage needs this settled before it starts.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
