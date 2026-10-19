# Session 8 · Stage 1 — Lazy plans and optimizer literacy

**Exercise sheet.** Verified against `polars 1.36.0`.

This is the stage that makes you fluent rather than merely correct. Everything
before it was about what a query *means*; this is about what it *becomes*.

The tool is `explain()`, and the skill is reading it.

---

# Part A — Polars on its own terms

## Task A1 — The eight passes, found in plans you wrote

Polars documents **eight** optimizations. Most people can name three.

| pass | what it does |
|---|---|
| predicate pushdown | move filters toward the scan |
| projection pushdown | read only the columns needed |
| slice pushdown | push a head/limit into the operation below |
| common subplan elimination | compute a repeated subtree once |
| simplify expressions | rewrite expressions into cheaper equivalents |
| join ordering | reorder multi-way joins |
| type coercion | insert casts once, at plan time |
| cardinality estimation | inform the choices above |

**Do.** Construct **one query per pass** that makes it visible in `explain()`,
and record the line that proves it. Two are given so you can see what "proves it"
means; find the rest yourself.

```python
# projection pushdown — the scan reads fewer columns than the frame has
df.lazy().select("a", "b", "k").filter(pl.col("a") > 3).select("b").explain()
#   → DF ["a","b","k"]; PROJECT["a","b"] 2/3 COLUMNS

# common subexpression elimination — a shared subtree is hoisted
sub = pl.col("a") + pl.col("b")
df.lazy().with_columns(s1=sub, s2=sub * 2).explain()
#   → WITH_COLUMNS: [col("__POLARS_CSER_0x…").alias("s1"), …]
#     WITH_COLUMNS: [[(col("a")) + (col("b"))].alias("__POLARS_CSER_0x…")]
```

**Acceptance.** At least five of the eight demonstrated with a plan line you can
point at. For any you cannot make visible, say what you tried and why the plan
did not change — a pass that does not fire on your query is a finding about the
pass's preconditions, not a failure of the exercise.

**Trap.** Assuming a pass fired because the result was correct. The *only*
evidence is the plan text. `simplify expressions` in particular does less than
people expect — check whether `pl.col("a") + 0` is actually removed before
claiming it.

## Task A2 — Turn a pass off and watch the plan change

The strongest way to see a pass is to remove it.

**Do.**

```python
flags = pl.QueryOptFlags(comm_subexpr_elim=False)
df.lazy().with_columns(s1=sub, s2=sub * 2).explain(optimizations=flags)
df.lazy().with_columns(s1=sub, s2=sub * 2).explain()          # for comparison
```

Then explore `pl.QueryOptFlags()` — list its fields.

**Acceptance.** Two plans side by side, differing exactly by the hoisted
`__POLARS_CSER_…` node. You can list the flag names and say which correspond to
the eight documented passes and which are extra.

**Currency note.** `collect(no_optimization=True)` is **deprecated since
1.30.0**. The current API is the `optimizations=` parameter taking a
`QueryOptFlags`. If you find `no_optimization` in a tutorial, the tutorial
predates this.

## Task A3 — Where the time actually goes

**Do.** `lf.profile()` on a query with a filter, a group-by and a join.

**Acceptance.** You can read the returned profile frame (`node`, `start`,
`end`), name the most expensive node, and say whether it is the one you would
have guessed. Then change the query to make a *different* node dominate.

**Why it matters.** This is the honest answer to "is Polars fast here". A
backend decision justified by a benchmark you did not profile is a guess with a
number attached.

## Task A4 — Two engines

**Do.** Run the same lazy query with `collect(engine="in-memory")` and
`collect(engine="streaming")`.

**Acceptance.** Same result. You can state what streaming does differently and
what it gives up — and you have read the currency note below, because the
default changes in the next major version.

**Currency.** In Polars 2.0, `collect()` defaults to the **streaming** engine.
Streaming does not guarantee row order for operations that do not inherently
require one — `group_by`, joins, `unpivot`. Any correctness your code currently
gets from incidental ordering will stop arriving. The fix is `maintain_order`
where the operation supports it, or an explicit `sort` — not a re-sorted
expectation in a test.

---

# Part B — The pandas contract

## Task B1 — There is no plan to compare

pandas has no query planner. That makes this stage's parity question different
from every other stage's: there is nothing to be *equal* to.

**Do.** Build an eager pandas pipeline and its lazy Polars mirror over the same
CSV: read, filter, add a column, group, aggregate, sort.

**Record.** For each: what pandas materializes at each step, and what Polars
does instead — read the plan to answer, not the docs.

**Acceptance.** You can state the number of full-column materializations each
performs, and identify at least one intermediate pandas creates that Polars never
does. That difference, not a benchmark, is the argument for the lazy API.

## Task B2 — `eval`/`query` are not a planner

**Do.** Read pandas' `eval`/`query` and its `scale.html` guidance. Try the same
pipeline with `df.query(...)`.

**Acceptance.** You can say what `eval` actually does (expression-level
evaluation, avoiding some temporaries) and what it does not (reorder, prune
columns, or defer). It is a different kind of optimization from a plan, and
conflating them is the usual mistake in comparisons of the two libraries.

---

# Part C — The lowering decision

## Task C1 — Where Stratum's optimizer and Polars' meet

**Do.** Write the two-layer diagram: Stratum's logical plan and rewrites above,
Polars' plan and passes below. For each of the eight Polars passes, decide
whether Stratum should (a) rely on it, (b) duplicate it, or (c) actively avoid
interfering with it.

**Acceptance.** Eight decisions. At least one is (c): a rewrite that materializes
early, or hides which columns an operation touches, prevents a Polars pass from
firing — and the biggest single example of that is the subject of the next stage.

---

## Answer key

### Task A1 — the two given passes, verified

**Projection pushdown.** Selecting three columns, filtering on one, returning
one:

```
simple π 1/1 ["b"]
  FILTER [(col("a")) > (3)]
  FROM
    DF ["a", "b", "k"]; PROJECT["a", "b"] 2/3 COLUMNS
```

`2/3 COLUMNS`, and `k` is not among them.

**Common subexpression elimination.** A shared subtree becomes a hoisted node
with a generated name:

```
WITH_COLUMNS:
[col("__POLARS_CSER_0x…").alias("s1"), [(col("__POLARS_CSER_0x…")) * (2)].alias("s2")]
  WITH_COLUMNS:
  [[(col("a")) + (col("b"))].alias("__POLARS_CSER_0x…")]
```

The addition appears **once**. That is the pass that should change your habits:
naming an intermediate to "avoid recomputing it" is work the optimizer already
did, and a repeated subexpression is not a performance problem.

**Predicate pushdown through `with_columns`:**

```
WITH_COLUMNS: [[(col("a")) * (2)].alias("c")]
  FILTER [(col("a")) > (3)]
  FROM
    DF …
```

The filter is now *below* the column creation, so the new column is computed for
fewer rows.

**Slice pushdown** (Session 3): `sort("v").head(2)` → `SORT BY [slice: (0, 2)]`.

**The one that disappoints:** `select((pl.col("a") + 0))` still shows
`[(col("a")) + (0)]` in the optimized plan. `simplify expressions` did not remove
the identity. Do not report a pass as firing on the strength of its name.

### Task A2

`pl.QueryOptFlags()` exposes: `check_order_observe`, `cluster_with_columns`,
`comm_subexpr_elim`, `comm_subplan_elim`, `fast_projection`,
`predicate_pushdown`, `projection_pushdown`, `simplify_expression`,
`slice_pushdown`, plus `none()` and `no_optimizations`.

Note there are two CSE flags — `comm_subexpr_elim` (within an expression) and
`comm_subplan_elim` (across subplans) — where the documentation lists one
"common subplan elimination". The flag list is the finer-grained truth.

With `comm_subexpr_elim=False` the `__POLARS_CSER_…` node disappears and the
addition appears twice.

### Task A3

`profile()` returns `(result, profile_frame)` where the profile frame has
`node`, `start`, `end` in microseconds.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
