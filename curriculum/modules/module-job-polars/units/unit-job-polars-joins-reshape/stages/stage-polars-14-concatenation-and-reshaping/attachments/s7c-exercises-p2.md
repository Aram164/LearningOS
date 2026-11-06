# Session 7 · Stage 3 — Concatenation and reshaping

> **Retargeted 2026-11-02 to `polars 2.0.0` / `pandas 3.0.2`**, the versions in Stratum's
> `uv.lock`. Run with `Stratum/.venv/bin/python`. Read for behaviour, not signatures: look
> arguments up whenever you need them. Where this sheet says "record as a harness case",
> add a row to your differences sheet instead; the harness is now optional.

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 2.0.0`.

Concatenation is where the two libraries' *defaults* diverge most sharply:
Polars refuses what pandas silently unions. Reshaping is where the API is
currently moving, so this stage carries an explicit currency section.

---

# Part A — Polars on its own terms

## Task A1 — The five concat modes

Polars has more concat modes than pandas has arguments. Learn them as a set.

**Do.** With

```python
X = pl.DataFrame({"a": [1], "b": [2]})
Y = pl.DataFrame({"b": [3], "c": [4]})
```

run `pl.concat([X, Y], how=...)` for `vertical`, `vertical_relaxed`,
`diagonal`, `horizontal`, and `align`. Then run `align` on two frames sharing a
key column.

**Predict.** Which of the five raise on `X`/`Y`, and what `align` does that none
of the others do.

**Record.**

| how | result | what it is for |
|---|---|---|

**Acceptance.** Five rows. You can say which one is the equivalent of pandas'
`concat(axis=0)`, and — the more useful answer — why Polars made the strict
version the default and gave the permissive one a different name.

**Trap.** `align` is not a concatenation at all in the usual sense: it joins on
the common columns and unions the rest. It has no pandas argument equivalent,
and it is often what someone actually wanted when they reached for `axis=1`.

## Task A2 — Reshaping, natively

From intent:

1. Long to wide: one row per `i`, one column per value of `c`.
2. The same, when `(i, c)` pairs repeat.
3. Wide to long.
4. Wide to long with your own names for the two produced columns.
5. Turn a `List` column into one row per element.
6. Turn a `Struct` column into one column per field.
7. Transpose a small frame.
8. Split one frame into a dict of frames, one per value of `k`.

**Acceptance.** Eight expressions. #2 needs something #1 does not; find out what
by letting #1 fail on repeated pairs. #6 and #8 are the two most people do not
know exist — `unnest` and `partition_by`.

## Task A3 — Where reshaping stops being lazy

**Do.** Try `pivot` on a `LazyFrame`.

**Acceptance.** You can state why a pivot is a boundary for a lazy engine: the
*output schema depends on the data*, so the plan cannot be resolved without
reading. Note that `LazyFrame.pivot` exists in 2.0 with a different signature
requiring the output columns to be declared up front — which is the same fact
stated as an API.

---

# Part B — The pandas contract

## Task B1 — The concat default that flips

**Do.**

```python
pl.concat([X, Y], how="vertical")
pd.concat([X.to_pandas(), Y.to_pandas()])
```

**Predict.** Both.

**Acceptance.** Recorded as a harness case. You can name the Polars mode that
reproduces pandas' behaviour, and state which default you would want at a backend
boundary — with a reason that is about failure modes, not preference.

**Trap.** pandas unions the columns and fills the gaps with `NaN`, producing a
3-column frame from two 2-column frames without a word. If the mismatch was a
typo in a column name, pandas gives you a wider frame full of missing values and
Polars gives you a `ShapeError` naming the two columns.

## Task B2 — dtype mismatch on vertical concat

**Do.** Concatenate an `Int64` column with a `Float64` one, `how="vertical"`
then `how="vertical_relaxed"`; and the pandas equivalent.

**Acceptance.** Three results. `vertical_relaxed` applies the Session 3
supertype rule; `vertical` refuses. You can say which one pandas is.

## Task B3 — Horizontal concat and length

**Do.** `pl.concat([X, pl.DataFrame({"z": [1, 2]})], how="horizontal")` and
`pd.concat([...], axis=1)` on frames with different indexes.

**Acceptance.** Both results, and the two different mechanisms: Polars pads by
**position**, pandas aligns by **label**. Then read the currency note below,
because this specific behaviour changes in the next major version.

## Task B4 — `pivot` on repeated pairs

**Do.** Pivot a frame where `(index, on)` repeats, with and without
`aggregate_function`, in both libraries.

**Acceptance.** You can map `pivot`/`pivot_table` onto Polars' single `pivot`
with its `aggregate_function` argument, and you know what each does when the
argument is missing.

---

# Part C — What 2.0 changed here

Older tutorials, including the book, still show the pre-2.0 forms. Learn to spot them.

## Task C1 — `melt` is gone

**Do.** Run `W.melt(id_vars="i", value_vars="v")`, read the error, then rewrite it with
`unpivot`. pandas keeps `melt`, so this is a name that differs between the libraries.

## Task C2 — Two defaults that moved

**Do.** Read the [2.0 upgrade guide](https://docs.pola.rs/releases/upgrade/2/) entries for
horizontal `concat` and for the default lazy engine. Say in one sentence each what old code
would now do.

**Acceptance.** You can say why relying on incidental row order after a lazy `group_by` or
join is now wrong, and you ask for `maintain_order` or sort instead.

## Task C3 — A behaviour to pin with a test

**Do.**

```python
W = pl.DataFrame({"i": ["x", "y"], "p": [1, 3], "q": [2, 4]})
W.unpivot(index="i", variable_name="var", value_name="val")
W.to_pandas().melt(id_vars="i", var_name="var", value_name="val")
```

**Predict.** For each: which produced column holds the *names* `p`/`q`, and
which holds the *values* `1,3,2,4`?

**Acceptance.** You have both results side by side and can state exactly what
differs. Then write the harness case, and re-run it when you move off 2.0.0 —
see the key.

---

## Answer key

### Task A1 / B1

| how | on `X`/`Y` |
|---|---|
| `vertical` | raises `ShapeError`: *unable to vstack, column names don't match: "a" and "b"* |
| `vertical_relaxed` | same name check; relaxes **dtypes**, not names |
| `diagonal` | `{'a': [1, None], 'b': [2, 3], 'c': [None, 4]}` — the pandas equivalent |
| `horizontal` | side-by-side, padding the shorter with nulls |
| `align` | joins on common columns and unions the rest |

`pd.concat([X, Y])` → shape `(2, 3)`, i.e. Polars' `diagonal`. Polars made the
strict version the default because the overwhelmingly common cause of a column
mismatch is a mistake; `diagonal` is available for when it is not.

`align` on two frames sharing `k`:
`{'k': [1, 2, 3], 'a': [1, 2, None], 'b': [None, 9, 9]}`.

### Task B2

`pl.concat([Int64, Float64], how="vertical")` → `SchemaError: type Float64 is
incompatible with expected type Int64`.
`how="vertical_relaxed"` → `Float64`, by the Session 3 supertype rule.
pandas is `vertical_relaxed`: it promotes silently.

### Task B3

`pl.concat([one_row, two_rows], how="horizontal")` raises `ShapeError` in 2.0.
`how="horizontal_extend"` gives `{'a': [1, None], 'b': [1, 2]}`, padded by position.
pandas `concat(axis=1)` aligns by index label and produces the union of the
indexes.


### Task B4

Polars `pivot` with repeated `(index, on)` pairs and no `aggregate_function`
raises `ComputeError: aggregation 'item' expected no or a single value, got 2
values`. With `aggregate_function="sum"` it aggregates. So Polars' single
`pivot` covers both of pandas' `pivot` (raises on duplicates) and `pivot_table`
(aggregates), selected by one argument.

### Task C3 — the result to pin

In 2.0 both calls attach the names the way the parameters say:
`W.unpivot(index="i", variable_name="var", value_name="val").columns` is
`['i', 'var', 'val']`, with `p`/`q` in `var` and `1, 3, 2, 4` in `val`. pandas `melt` agrees.
Polars 1.36 had these two columns swapped, so old examples may show that.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
