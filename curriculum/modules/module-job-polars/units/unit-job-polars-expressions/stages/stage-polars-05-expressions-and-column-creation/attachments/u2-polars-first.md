# Session 2 — Polars on its own terms

**Companion drill set.** Verified against `polars 1.36.0`. **No pandas appears
in this file.**

Session 2's stages build the expression language in order to lower `assign`.
This sheet builds it in order to *write Polars*. The difference shows up in one
place: here you are given intent and no source expression, so there is nothing to
translate and the only way through is to think in the language.

Fixture for every drill:

```python
df = pl.DataFrame({
    "region": ["north", "south", "north", "east", "south", "north"],
    "product": ["a", "b", "a", "c", "b", "b"],
    "units":   [10, 5, 8, 12, 7, 3],
    "price":   [2.5, 4.0, 2.5, 1.0, 4.0, 4.0],
    "note":    ["ok", None, "late", "ok", None, "late"],
})
```

---

## Drill set A — Single expressions from intent

Write each as one expression. No intermediate frames, no Python loops, no
`to_list()`.

1. Revenue: units × price.
2. Revenue, rounded to whole currency units.
3. The share of total units each row represents.
4. The share of its **region's** units each row represents.
5. Rank rows by revenue, highest first, ties sharing a rank.
6. The rank of each row *within its region*.
7. A flag: is this row's units above the overall median?
8. A flag: is this row's units the maximum **within its region**?
9. The running total of units in row order.
10. The running total of units within each region.
11. `note`, with missing values replaced by the string `"none"`.
12. The number of distinct products per region, as a column that keeps the frame's height.
13. The first non-null `note` in each region, broadcast to every row of that region.
14. Units, but only counting rows whose product is `"b"` — as a per-region sum.
15. A single column combining region and product as `"north/a"`.

**Acceptance.** Fifteen expressions that run. At least ten written without
looking anything up. For every one you looked up, write the *namespace or
function family* it came from — `over`, `cum_*`, `rank`, `fill_null`, `str`.

**The marker.** Drills 4, 6, 8, 10, 12, 13 and 14 all have the same shape: an
aggregation that must not collapse the frame. If you wrote `over` for all seven
without hesitating, you have the central idiom. If you reached for `group_by` and
a join on any of them, that is the reflex worth naming and retiring.

---

## Drill set B — Composition

16. Standardize every numeric column in one statement, without naming any.
17. Rename every column to upper case in one statement.
18. Add a `_pct` suffixed copy of every numeric column holding its share of that column's sum.
19. Filter to rows where **any** numeric column exceeds its own column mean.
20. Filter to rows where **every** string column is non-null.

**Acceptance.** Five statements, each of which still works after you add a
column to the fixture. Test that: add one and re-run. A statement that needed
editing was not composition, it was a name list.

---

## Drill set C — Conditionals and the shape of a query

21. A `band` column: `"high"` when revenue ≥ 30, `"mid"` when ≥ 15, else `"low"`.
    One chain, three branches.
22. The same, but `null` for rows whose `note` is missing — without a fourth branch.
23. Total revenue per region, as a frame of one row per region, sorted by revenue.
24. The same, but as a frame that also carries each region's best-selling product.
25. For each region: the number of rows, distinct products, and total revenue —
    three aggregations in one `agg`.

**Acceptance.** Five results. #22 tests whether you know what happens when a
`when` predicate is itself null. #24 is the first thing on this sheet that
genuinely needs a two-step query — recognizing *that* is the skill.

---

## Drill set D — Read the plan

26. Write drill 23 lazily and print `explain()`. Name every optimization visible.
27. Write a query that reads three columns, filters on one, and returns one.
    Confirm from the plan how many columns the scan touches.
28. Write two spellings of the same result — one with the filter before a
    `with_columns` and one after — and compare their optimized plans.

**Acceptance.** For #28, you can say whether the optimizer made them identical,
and if not, why not. This is the drill that tells you when hand-ordering a query
is worth your time.

---

## Answer key

### Drill set A — the seven that share one shape

```python
#  4  pl.col("units") / pl.col("units").sum().over("region")
#  6  pl.col("revenue").rank(descending=True).over("region")
#  8  pl.col("units") == pl.col("units").max().over("region")
# 10  pl.col("units").cum_sum().over("region")
# 12  pl.col("product").n_unique().over("region")
# 13  pl.col("note").drop_nulls().first().over("region")
# 14  pl.col("units").filter(pl.col("product") == "b").sum().over("region")
```

Every one is `<aggregation>.over(<partition>)`. `over` is the operator that turns
any aggregation into a window: the aggregation computes per partition, and the
result is broadcast back across the partition's rows so the frame keeps its
height. Once you see that these seven are one construction, the family stops
being seven things to remember.

Drill 14 is worth a second look: `filter` appears *inside* the expression, before
the aggregation and inside the window. That is the expression-level `filter` from
Session 3 — it is what lets a conditional aggregate exist without building a
separate filtered frame per condition.

Others:

```python
#  1  pl.col("units") * pl.col("price")
#  3  pl.col("units") / pl.col("units").sum()
#  5  pl.col("revenue").rank(method="min", descending=True)
#  9  pl.col("units").cum_sum()
# 11  pl.col("note").fill_null("none")
# 15  pl.concat_str([pl.col("region"), pl.col("product")], separator="/")
```

### Drill set B

```python
# 16  (cs.numeric() - cs.numeric().mean()) / cs.numeric().std()
# 17  pl.all().name.to_uppercase()
# 18  (cs.numeric() / cs.numeric().sum()).name.suffix("_pct")
# 19  pl.any_horizontal(cs.numeric() > cs.numeric().mean())
# 20  pl.all_horizontal(cs.string().is_not_null())
```

All five survive a new column, because none of them names one. That property —
not brevity — is what makes a selector worth using.

### Drill set C

```python
# 21  pl.when(rev >= 30).then(pl.lit("high")).when(rev >= 15).then(pl.lit("mid")).otherwise(pl.lit("low"))
# 23  df.group_by("region").agg((pl.col("units") * pl.col("price")).sum().alias("rev")).sort("rev", descending=True)
# 25  df.group_by("region").agg(pl.len(), pl.col("product").n_unique(), (pl.col("units")*pl.col("price")).sum())
```

**#22.** A `when` predicate that evaluates to null takes neither branch — the
result is null. So adding `pl.col("note").is_not_null() & (...)` to the *first*
predicate is not the answer; the answer is that a null predicate already produces
null, and you get the required behaviour by making the predicate depend on
`note`. Confirm it rather than trusting this paragraph: it is exactly the kind
of three-valued-logic claim Session 2's Kleene tables exist to make checkable.

**#24** needs two steps because "the region's best-selling product" is an
aggregation over a *different* grouping than the revenue total. Recognizing that
a single `agg` cannot express it — rather than fighting to make one — is the
judgment being trained.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
