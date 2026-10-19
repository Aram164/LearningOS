# Session 7 · Stage 1 — Relational joins and key cardinality

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Joins are where every axis fires at once: cardinality, null semantics, column
naming, row order, and dtype promotion all change in one call. Do the counting
before the coding.

---

## Fixture F8 — four rows, deliberately awkward

```python
L = pl.DataFrame({"k": ["a", "a", "b", None], "lv": [1, 2, 3, 4]})
R = pl.DataFrame({"k": ["a", "b", "b", None], "rv": [10, 20, 30, 40]})
```

Key `a` is 2×1, key `b` is 1×2, and both sides carry a null key. Every finding
below comes from those three facts.

---

# Part A — Polars on its own terms

## Task A1 — Count before you join

**Do.** On paper, for each `how`, predict the **row count**: `inner`, `left`,
`right`, `full`, `semi`, `anti`, `cross`. Then run them.

**Record.**

| how | predicted | actual | why |
|---|---|---|---|

**Acceptance.** Seven predictions. You can derive each count from key
multiplicity without executing, and you can explain `semi` and `anti` in one
sentence each — they are the two that are not row-combining operations at all.

**Trap.** `inner` is not 4 because of the two `a` rows plus the two `b` rows in
some simple way — work out the 2×1 and 1×2 products separately and notice that
they happen to sum to the same number a wrong method would give.

## Task A2 — The Polars-only join kinds

**Do.**

```python
L.join(R, on="k", how="semi")     # rows of L that have a match
L.join(R, on="k", how="anti")     # rows of L that do not
b.join_asof(a, on="t", strategy="backward")   # nearest-preceding match
a.join_where(b, pl.col("t") > pl.col("t_right"))   # non-equi join
```

**Acceptance.** Four results. You can say which of these pandas has no direct
equivalent for and how you would express each in pandas — and, having tried, why
`semi` written as a `merge` plus a dedup is not the same operation.

**Why it matters.** `semi`/`anti` are filters, not joins: the output has the
left frame's columns and no more. That makes them the right tool for existence
checks, and reaching for an inner join plus a `unique` there is both slower and
wrong when the right side has duplicates.

## Task A3 — Read a join plan

**Do.** `L.lazy().join(R.lazy(), on="k", how="inner").explain()`.

**Acceptance.** You can point at the `INNER JOIN:` node, the `LEFT PLAN ON:` and
`RIGHT PLAN ON:` sections, and say which columns each side's scan will read.
Then add a filter on `lv` after the join and check whether it moved.

---

# Part B — The pandas contract

## Task B1 — The null-key divergence

**Do.**

```python
L.join(R, on="k", how="inner").height
L.join(R, on="k", how="inner", nulls_equal=True).height
pL.merge(pR, on="k", how="inner").shape[0]
```

**Predict.** All three.

**Acceptance.** You can state each library's default answer to *"does a null key
match another null key?"* and name the Polars keyword that switches it.
Recorded as a harness case, class **semantic**, because it changes the row count
with no error.

**Trap.** pandas matches nulls to each other in a merge — which contradicts its
own `None == None → False` from Session 4. The merge does not use element
equality; it hashes the key, and the null hashes to itself. So "pandas says
missing values are unequal" is true of comparison and false of joining.

## Task B2 — Suffixes: the silent column rename

**Do.** Join two frames that both carry a column `v`, on `k`, in both libraries.

**Record.** The output column names on each side.

**Acceptance.** You can state both rules. Then answer the design question: a
compatibility layer must produce *pandas'* names or *Polars'*? Whichever you
choose, the other library's user is surprised, so write down which and why.

**Trap.** Polars suffixes only the **right** side; pandas suffixes **both**. So
after a join, one library has a column called `v` and the other does not have one
at all. A downstream `select("v")` works on one backend and raises on the other.

## Task B3 — The full join that loses keys

**Do.**

```python
A = pl.DataFrame({"k": ["a", "b"], "v": [1, 2]})
B = pl.DataFrame({"k": ["b", "c"], "w": [3, 4]})
A.join(B, on="k", how="full").columns
A.join(B, on="k", how="full")["k"].to_list()
A.join(B, on="k", how="full", coalesce=True)["k"].to_list()
A.to_pandas().merge(B.to_pandas(), on="k", how="outer")["k"].tolist()
```

**Predict.** The `k` values in the second line. The key `c` exists only on the
right — where does it appear?

**Acceptance.** You can explain why Polars' full join produces **two** key
columns by default, what `coalesce=True` does, and why the default is arguably
the more honest one. Recorded as a harness case.

**Trap.** This is the stage's most dangerous cell. Without `coalesce=True`, the
`k` column of a full join is **missing every right-only key** — it holds
`['a', 'b', None]` while the real key set is `{a, b, c}`. The value is in
`k_right`. Code that reads `k` after a full join silently drops right-only rows'
identity, and pandas' `merge(how="outer")` coalesces by default, so a translated
query changes meaning.

## Task B4 — Validation

**Do.** `validate="1:1"` on F8 in both libraries.

**Acceptance.** Both raise; you have both exception types and can say whether
your layer re-raises or translates.

---

# Part C — The lowering decision

## Task C1 — Eight merges to normalized fields

**Do.** Translate eight pandas `merge`/`join` calls into normalized `JoinOp`
field values **on paper** — no code. Include: `on=`, `left_on`/`right_on`,
`left_index=True`, `how="outer"`, custom `suffixes=`, `validate=`,
`indicator=True`, and a merge on columns of different dtypes.

**Acceptance.** Eight rows. Each unsupported feature is named as unsupported
rather than approximated — `indicator=True` and index joins in particular get an
explicit decision.

---

## Answer key

### Task A1

| how | rows | why |
|---|---|---|
| `inner` | **4** | `a`: 2×1 = 2, `b`: 1×2 = 2, nulls do not match |
| `left` | 5 | the 4 matched rows plus the unmatched null-key row |
| `right` | 5 | symmetric |
| `full` | 6 | 4 matched + 1 left-only + 1 right-only |
| `semi` | 3 | rows of `L` with a match: the two `a`s and the one `b` |
| `anti` | 1 | the null-key row |
| `cross` | 16 | 4 × 4, keys ignored entirely |

pandas' `inner` on the same data is **5**, not 4 — see Task B1.

### Task B1

| call | rows |
|---|---|
| `L.join(R, on="k", how="inner")` | 4 |
| `L.join(R, on="k", how="inner", nulls_equal=True)` | **5** |
| `pL.merge(pR, on="k", how="inner")` | **5** |

pandas' default is Polars' `nulls_equal=True`. Note the direction: the *default*
behaviours differ, so a translation that omits the keyword silently drops a row.

### Task B2

| | output columns |
|---|---|
| Polars `A.join(B, on="k")` | `['k', 'v', 'v_right']` |
| Polars with `suffix="_r"` | `['k', 'v', 'v_r']` |
| pandas `merge` | `['k', 'v_x', 'v_y']` |

### Task B3

```
A.join(B, on="k", how="full").columns   →  ['k', 'v', 'k_right', 'w']
                                 ["k"]  →  ['a', 'b', None]      ← 'c' is missing
with coalesce=True               ["k"]  →  ['a', 'b', 'c']
pandas merge(how="outer")        ["k"]  →  ['a', 'b', 'c']
```

Polars' default keeps both original key columns because a full join genuinely has
two of them, and they differ exactly on the unmatched rows. It is the more honest
representation and the more dangerous default, because `k` looks complete and is
not. pandas coalesces silently, which is friendlier and loses the information
about which side a key came from — recoverable there only with
`indicator=True`.

### Task B4

Polars: `ComputeError: join keys did not fulfill 1:1 validation`.
pandas: `MergeError: Merge keys are not unique in either left or right dataset;
not a one-to-one merge.` — with the duplicate keys listed.

Both refuse; pandas' message names the offending values, which is worth
preserving if your layer translates the error.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
