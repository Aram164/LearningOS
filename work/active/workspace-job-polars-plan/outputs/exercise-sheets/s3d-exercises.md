# Session 3 · Stage 4 — `DROPNA` from selectors and horizontal expressions

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

`drop_nulls` is not `dropna`. The names match, the common case matches, and the
difference is a whole class of rows. This stage builds the real implementation.

Session 2's horizontal stage derived the predicates; here you make one
implementation that covers `how`, `thresh`, `subset`, runtime operands, and the
failure boundary.

---

## Fixture F7 — the frame that separates null from NaN

```python
df = pl.DataFrame({
    "a": pl.Series([1.0, None, 3.0, float("nan")], dtype=pl.Float64),
    "b": ["x", None, "z", "w"],
    "c": [1, 2, 3, 4],          # row labels
})
```

Row 4 (`c = 4`) carries a real floating-point `NaN` in `a` and nothing missing
anywhere. Whether it survives a `dropna` is the entire question.

---

# Part A — Polars on its own terms

## Task A1 — The missing-value toolkit

Polars' answer to missing data is a small set of orthogonal tools rather than one
overloaded function. Learn the shape of it:

1. Count the missing values per column, in one call.
2. Count the NaNs in `a` — which is a different number.
3. Drop rows with any missing value.
4. Drop rows where `a` specifically is missing.
5. Drop rows where any *numeric* column is missing, without naming one.
6. Replace missing values in `a` with `0`.
7. Carry the previous value forward into missing positions.
8. Turn every `NaN` in `a` into a null.
9. Replace missing values with the column mean.
10. Keep only rows where `b` is missing.

**Predict.** For #6: what happens to the `NaN` at row 4?

**Record.** For each, the call and its result on F7.

**Acceptance.** You can state the design principle: **`null` and `NaN` are
different things and each has its own verb**. `fill_null` and `fill_nan` are not
variants of one function, and knowing which you need is knowing what your data
means. Then say what that buys you that pandas' single `fillna` does not.

**Trap.** #6. `fill_null(0)` leaves the `NaN` untouched, because a `NaN` is not
missing — it is a present value that happens to be Not-a-Number. If you expected
it to be filled, your model is still pandas'.

## Task A2 — The normalization sandwich

**Do.** Produce a frame where every `NaN` has become a null, then drop rows with
any null.

**Acceptance.** Two calls, in the right order, and you can say why the order is
not reversible. This composition — `fill_nan(None)` then `drop_nulls()` — is the
**exact** pandas semantics of `dropna()`, expressed in Polars' own vocabulary.
Notice what that means: pandas' behaviour is a *composition* of two Polars
concepts, which is why one call cannot be the translation of the other.

---

# Part B — The pandas contract

## Task B1 — Where `drop_nulls` and `dropna` part company

**Do.**

```python
df.drop_nulls()["c"].to_list()
pdf.dropna()["c"].tolist()
```

**Predict.** Both lists.

**Acceptance.** You can name the row that differs and say why, without
re-reading Session 1. Then record the two-call composition from Task A2 as the
correct translation and verify it matches pandas exactly.

## Task B2 — The full argument surface

**Do.** Map every `dropna` argument. For each, decide **native**, **adapt**
(expressible as a composition), or **unsupported**, with evidence:

| pandas argument | meaning | polars | class |
|---|---|---|---|
| `how="any"` | | | |
| `how="all"` | | | |
| `thresh=n` | | | |
| `subset=[...]` | | | |
| `axis=1` | drop **columns**, not rows | | |
| `ignore_index` | | | |
| `inplace` | | | |

**Acceptance.** Seven rows. `axis=1` in particular gets a real answer — it is a
different operation, not a flag, and the Polars form is not a `drop_nulls` call
at all.

**Trap.** Calling `axis=1` unsupported and moving on. It is expressible; it is
just not expressible with the same function, which is a different classification
with a different consequence for the caller.

## Task B3 — Invalid combinations, and where they must fail

**Do.**

```python
pdf.dropna(how="any", thresh=2)
pdf.dropna(subset=["zz"])
df.drop_nulls(subset="zz")
```

**Predict.** Which raise, and with what type.

**Acceptance.** Three exception types recorded. You can state which of these
your implementation must reproduce and which it must *improve on*, and you have
decided where in your own code each is raised — at argument validation, or at
execution. Reproducing pandas' error at pandas' boundary is a deliberate choice;
so is refusing earlier with a better message. Make it once, in writing.

**Trap.** Letting the invalid `how` + `thresh` combination through because
Polars, given the composed expression, will happily evaluate something. pandas
rejects it as meaningless; if your layer does not, you have invented semantics.

---

# Part C — The implementation

## Task C1 — One implementation, all paths

**Do.** Write `lower_dropna(how, thresh, subset, axis, ...)` producing a Polars
expression or frame operation, where `subset` may be a literal list **or** a
runtime operand resolved during execution.

It must handle:

| input | requirement |
|---|---|
| `how="any"` / `how="all"` | the Session 2 predicates |
| `thresh=n` | a non-null count compared to `n`, not a chain of any/all |
| `subset` as a selector | resolved at execution, so schema drift is followed |
| `subset` resolving to nothing | the decision you recorded in Session 2 |
| `subset` naming a missing column | the exception class from Task B3, at your chosen boundary |
| `thresh=0`, `thresh > len(subset)` | no special-casing needed, or explain why |
| mixed dtypes in the subset | strings and datetimes have nulls but no NaN |
| the `NaN` policy | applied consistently, from a single named constant |

**Acceptance.** One function, no branch that exists only to make a test pass.
Every dropna case from Task B2 routes through it. The NaN policy appears exactly
once in the source — if it appears twice, they will disagree eventually.

**Trap.** Special-casing `thresh` when the subset is empty *and* separately when
`thresh=0`. Both fall out of a correct count comparison; if you needed two
special cases, the count is being computed wrongly.

## Task C2 — Rebuild it closed-book

**Do.** Close every reference including the attached `_selection_execs.py`.
Derive the whole thing from the pandas contract and your Session 2 predicates.
Then diff against the attached implementation.

**Record.** Every difference, classified: *mine is wrong*, *theirs is wrong*,
*both correct, different policy*.

**Acceptance.** The diff exists and each entry has a classification. This is the
only exercise in the module whose value is destroyed by looking first.

---

## Answer key

### Task A1 / A2

| # | call | result on F7 |
|---|---|---|
| 1 | `df.null_count()` | `{'a': 1, 'b': 1, 'c': 0}` |
| 2 | `pl.col("a").is_nan().sum()` | `1` — a different row than #1 counted |
| 3 | `df.drop_nulls()` | rows `c = [1, 3, 4]` |
| 6 | `pl.col("a").fill_null(0)` | `[1.0, 0.0, 3.0, nan]` — **the NaN is untouched** |
| 7 | `fill_null(strategy="forward")` | `[1.0, 1.0, 3.0, nan]` |
| 8 | `pl.col("a").fill_nan(None)` | `[1.0, None, 3.0, None]` |

The normalization sandwich:

```python
df.with_columns(cs.float().fill_nan(None)).drop_nulls()
```

`fill_nan(None)` first, then `drop_nulls()`. The reverse order drops the null
row and leaves the NaN row, which is `drop_nulls()`'s own semantics — so
reversing does not produce a different answer to the same question, it answers a
different question.

### Task B1

```
df.drop_nulls()  →  c = [1, 3, 4]
pdf.dropna()     →  c = [1, 3]
```

Row 4. Polars keeps it because nothing in it is *missing*: `a` holds a NaN, a
present floating-point value. pandas drops it because on a NumPy-backed float
column `NaN` **is** the missing sentinel — the same fact as Session 1 Task 2,
now deciding a row count.

### Task B2

| pandas argument | polars | class |
|---|---|---|
| `how="any"` | `~any_horizontal(subset.is_null())`, or `drop_nulls(subset)` | native |
| `how="all"` | `~all_horizontal(subset.is_null())` | native |
| `thresh=n` | `sum_horizontal(subset.is_not_null().cast(Int64)) >= n` | native |
| `subset=[...]` | selector or column list | native |
| `axis=1` | not a `drop_nulls` call: select the columns whose `null_count()` is 0 | **adapt** |
| `ignore_index` | no row labels exist, so the request is already satisfied | native (vacuously) |
| `inplace` | no in-place frame mutation; return the new frame | adapt |

`axis=1` on F7 keeps only `c` — and the Polars form,
`[col for col in df.columns if df[col].null_count() == 0]`, gives the same answer
while making it obvious that this is a *schema* operation and not a row filter.

### Task B3

```
pdf.dropna(how="any", thresh=2)  →  TypeError: You cannot set both the how and
                                    thresh arguments at the same time.
pdf.dropna(subset=["zz"])        →  KeyError: ['zz']
df.drop_nulls(subset="zz")       →  ColumnNotFoundError: "zz" not found
```

The `TypeError` is the interesting one: pandas is refusing a *combination*, not a
value, and there is nothing in Polars to inherit that refusal from. It belongs in
your argument validation, before any expression is built — which means your layer
has a validation stage whether or not you planned one.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
