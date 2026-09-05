# Session 3 · Stage 1 — Selection and projection contracts

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Three parts, and they are not interchangeable:

- **Part A — Polars on its own terms.** Stated as intent, with no pandas
  original. This is the fluency half: if you can only reach a Polars query by
  translating one you already have, you are not fluent yet, you are bilingual by
  dictionary.
- **Part B — The pandas contract.** Where the two disagree, and how you find out.
- **Part C — The lowering decision.** What Stratum has to do about it.

---

## Fixture F5

```python
df = pl.DataFrame({
    "k": ["a", "b", "a", "c", "b"],
    "v": [1, 2, 1, 3, 2],
    "w": [10, 20, 30, 40, 50],
})
```

---

# Part A — Polars on its own terms

## Task A1 — Ten queries from intent

Write each as a single Polars expression chain. **Do not write the pandas
version first**, and do not look up a translation table. If you cannot express
one, write down what you reached for and could not find — that gap is the
finding.

1. The rows where `v` is above its own mean.
2. `k` and `w`, for rows where `k` is one of `{"a", "c"}`.
3. Every column whose name starts with `w`, renamed with a `_raw` suffix.
4. The two rows with the largest `w`, without sorting the whole frame in your head first.
5. `w` as a fraction of the total `w`.
6. Rows where `w` is above the mean **of its own `k` group**.
7. A column that is `"high"` when `w > 25` and `"low"` otherwise.
8. The first row of each `k`, in the order the groups first appear.
9. Every numeric column, standardized (subtract mean, divide by std), all in one statement.
10. The frame with `v` and `w` swapped in position, without naming any other column.

**Record.** For each: your expression, whether you reached it without a pandas
detour, and which namespace or function you had to look up.

**Acceptance.** Ten expressions that run. At least six written without consulting
anything. For the ones you looked up, you can now say *where in the API* they
live — `pl.col(...).over(...)`, `pl.when`, `cs.numeric()`, `.name.suffix`,
`top_k`, `.first()` — because the API's shape is the thing worth memorizing, not
the individual calls.

**Trap.** Solving #6 with a `group_by` and a join back. That is the pandas
reflex. `over` exists precisely so that a grouped computation can stay in a
row-preserving context, and reaching for it is the single clearest marker of
thinking in Polars rather than in translation.

## Task A2 — Read the plan the engine actually runs

Fluency includes knowing what the query becomes.

**Do.**

```python
lf = df.lazy().filter(pl.col("v") > 1).select("k", "w")
print(lf.explain(optimized=False))
print(lf.explain())
```

Then a second one, where you added a column you do not use:

```python
df.lazy().select("k", "v", "w").filter(pl.col("v") > 1).select("w").explain()
```

And a third:

```python
df.lazy().sort("v").head(2).explain()
```

**Predict.** For query 2: how many of the three columns will the scan read? For
query 3: will the engine sort all five rows?

**Record.** The three plans, and for each, the optimizer pass you can name from
reading it.

**Acceptance.** You can point at the line in each plan that proves an
optimization happened, and name it: **projection pushdown**, **predicate
pushdown**, **slice pushdown**. And you can state what that means for how you
should write queries — specifically, whether selecting columns early is worth
doing by hand.

**Trap.** Assuming the optimizer is a black box you cannot inspect. `explain()`
is the primary tool for understanding Polars, and reading plans is a skill that
compounds: every later session's performance question is answered here first.

## Task A3 — Idiom: the same result, four ways

**Do.** Get column `w` where `v > 1`, four ways:

```python
df.filter(pl.col("v") > 1)["w"]
df.filter(pl.col("v") > 1).select("w")
df.select(pl.col("w").filter(pl.col("v") > 1))
df.lazy().filter(pl.col("v") > 1).select("w").collect()
```

**Record.** Return type, shape, and — using `explain()` where it applies —
whether they produce the same plan.

**Acceptance.** You can say which of the four is idiomatic and why, and you can
state the rule about `[]` on a DataFrame that the library's own anti-patterns
section gives. Note that `filter` appears in two different positions and means
something subtly different in each.

**Trap.** Thinking this is a style question. `pl.col("w").filter(...)` is an
*expression-level* filter — it can appear inside an aggregation where a
frame-level filter cannot, which is the whole reason it exists.

---

# Part B — The pandas contract

## Task B1 — Ten paired prompts, shape predicted first

**Do.** Take prompts 1, 2, 4, 6, 7 and 8 from Task A1. Write the pandas version
now. For each, **predict Series versus DataFrame** before running.

**Record.**

| # | pandas call | returns | polars call | returns | agree on values? | agree on type? |
|---|---|---|---|---|---|---|

**Acceptance.** Six rows. Every "agree" backed by an executed comparison through
the Session 1 harness, not by inspection.

*(A note from writing this sheet's own checker: asserting prompt 5 —
`w / w.sum()` — against Python's `50/150` fails on the last row. Polars divides
in a different order and the final bit differs. Seed case 8 is not a curiosity;
it turns up in ordinary assertions, which is why the harness needs a per-case
tolerance rather than a habit of rounding when something looks close.)*

**Trap.** `df["w"]` gives a Series in both libraries and `df[["w"]]` a frame in
both — so the easy rows agree. The row that does not is #6: pandas needs
`groupby(...).transform(...)`, whose result is index-aligned back onto the
original frame, and the alignment is the part with no Polars analogue.

## Task B2 — The mask with a shuffled index

**Do.** Build a boolean mask whose index is shuffled relative to the frame, then
apply it in pandas. Apply a same-length boolean list in Polars.

```python
mask = pd.Series([True, False, True, False, True], index=[4, 3, 2, 1, 0])
pdf[mask]
```

**Predict.** Which rows survive: the ones at *positions* where the mask is
`True`, or the ones whose *labels* the mask marks `True`?

**Acceptance.** You can state which one pandas does, and you can produce the
Polars behaviour that corresponds — then say why no amount of care makes them
the same operation. This is Session 1 Task 3 arriving in a place where it
changes which rows a filter returns.

## Task B3 — Missing columns and exception classes

**Do.** `pdf[["zz"]]` and `df.select(["zz"])`.

**Record.** Both exception types and both messages.

**Acceptance.** Recorded as a harness case. A caller that catches `KeyError`
will not catch `ColumnNotFoundError`, so this is a contract difference and not a
cosmetic one.

---

# Part C — The lowering decision

## Task C1 — Six GetItem shapes, classified without running Stratum

**Do.** For each of the six argument shapes a captured `__getitem__` can carry —
scalar, list of names, boolean mask, slice, callable, tuple — decide the Polars
lowering path and the failure mode:

| shape | example | polars path | fails how |
|---|---|---|---|

**Acceptance.** Six rows, each naming a concrete expression or an explicit
`unsupported`. The boolean-mask row must record the shuffled-index finding from
Task B2 as a precondition, because a mask that arrived with an index is not the
same operand as a mask that arrived as a list.

---

## Answer key

### Task A1 — the six that reveal fluency

```python
# 1
df.filter(pl.col("v") > pl.col("v").mean())
# 4
df.top_k(2, by="w")
# 5
df.select(pl.col("w") / pl.col("w").sum())
# 6   ← the one that separates translation from fluency
df.filter(pl.col("w") > pl.col("w").mean().over("k"))
# 7
df.with_columns(pl.when(pl.col("w") > 25).then(pl.lit("high")).otherwise(pl.lit("low")).alias("band"))
# 8
df.group_by("k", maintain_order=True).first()
# 9
df.with_columns((cs.numeric() - cs.numeric().mean()) / cs.numeric().std())
# 10
df.select("k", "w", "v")     # or cs-based, without naming k
```

`#6` in one expression, with no join and no intermediate frame, is the marker.
`over` turns any aggregation into a window over a partition while keeping the
frame's height — it is the single most load-bearing piece of Polars idiom, and
Session 6 is where it gets its own stage.

`#9` is worth staring at: a selector appears three times in one expression and
resolves to the same column set each time, so the whole standardization is one
statement that survives a schema change.

### Task A2 — the three plans

```
# 1, unoptimized                     # 1, optimized
SELECT [col("k"), col("w")]          simple π 2/2 ["k", "w"]
  FILTER [(col("v")) > (1)]            FILTER [(col("v")) > (1)]
  FROM                                 FROM
    DF; PROJECT */3 COLUMNS              DF; PROJECT["k", "w", "v"] 3/3 COLUMNS
```

```
# 2 — the scan reads two of three columns
simple π 1/1 ["w"]
  FILTER [(col("v")) > (1)]
  FROM
    DF ["k", "v", "w"]; PROJECT["v", "w"] 2/3 COLUMNS
```

```
# 3 — the sort is told it only needs two rows
SORT BY [slice: (0, 2)] [col("v")]
  DF ["k", "v", "w"]; PROJECT */3 COLUMNS
```

Query 2 is the one to keep: you asked for three columns and the scan reads two,
because `k` is used by nothing downstream. That is **projection pushdown**, and
it is the reason hand-optimizing your column list is usually wasted effort — and
the reason a UDF that hides which columns it touches is expensive in a way that
has nothing to do with Python's speed. Query 3 is **slice pushdown**: a sort
followed by a head becomes a top-k, not a full sort.

### Task B2

pandas aligns the mask **by label**, not by position. The mask above has index
`[4, 3, 2, 1, 0]` with values `[True, False, True, False, True]`, so it marks
labels 4, 2 and 0 — and the surviving rows are positions 0, 2 and 4. pandas
emits a `UserWarning` while doing it (*"Boolean Series key will be reindexed to
match DataFrame index"*), which is worth catching in the harness: it is the
library telling you an alignment happened, and it is the only signal you get.
Polars has no
labels, so a boolean list is positional and there is nothing to align. The two
operations coincide only when the mask's index is already the frame's index in
the same order.

### Task B3

`pdf[["zz"]]` → `KeyError: "None of [Index(['zz'], dtype='str')] are in the [columns]"`
`df.select(["zz"])` → `ColumnNotFoundError: unable to find column "zz"; valid columns: ["k", "v", "w"]`

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
