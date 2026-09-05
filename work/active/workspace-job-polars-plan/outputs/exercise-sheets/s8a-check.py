"""Assert the lazy-plans / optimizer-literacy answer key."""
import sys

import polars as pl

if pl.__version__ != "1.36.0":
    sys.exit(f"FATAL: key asserts polars 1.36.0; you have {pl.__version__}.")

passed = failed = 0


def check(label, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {label}\n    got  {got!r}\n    want {want!r}")


df = pl.DataFrame({"a": list(range(10)), "b": list(range(10)), "k": ["x", "y"] * 5})
sub = pl.col("a") + pl.col("b")

# A1 — projection pushdown
plan_proj = df.lazy().select("a", "b", "k").filter(pl.col("a") > 3).select("b").explain()
check("A1 projection pushdown narrows the scan", "2/3 COLUMNS" in plan_proj, True)
check("A1 and k is not read", '"k"' not in plan_proj.split("PROJECT")[1].split("\n")[0], True)

# A1 — common subexpression elimination
plan_cse = df.lazy().with_columns(s1=sub, s2=sub * 2).explain()
check("A1 CSE hoists the shared subtree", "__POLARS_CSER" in plan_cse, True)
check("A1 and the addition appears once", plan_cse.count("(col(\"a\")) + (col(\"b\"))"), 1)

# A1 — predicate pushdown through with_columns
plan_pred = df.lazy().with_columns(c=pl.col("a") * 2).filter(pl.col("a") > 3).explain()
check("A1 the filter sits below the column creation",
      plan_pred.index("FILTER") > plan_pred.index("WITH_COLUMNS"), True)

# A1 — slice pushdown
check("A1 slice pushdown reaches the sort",
      "slice: (0, 2)" in df.lazy().sort("a").head(2).explain(), True)

# A1 — the pass that disappoints
check("A1 simplify_expression does NOT remove + 0",
      "(col(\"a\")) + (0)" in df.lazy().select((pl.col("a") + 0).alias("z")).explain(), True)

# A2 — turning a pass off changes the plan
off = pl.QueryOptFlags(comm_subexpr_elim=False)
plan_off = df.lazy().with_columns(s1=sub, s2=sub * 2).explain(optimizations=off)
check("A2 with CSE off the hoisted node is gone", "__POLARS_CSER" in plan_off, False)
check("A2 and the addition now appears twice", plan_off.count("(col(\"a\")) + (col(\"b\"))"), 2)
flags = [f for f in dir(pl.QueryOptFlags()) if not f.startswith("_")]
for f in ("predicate_pushdown", "projection_pushdown", "slice_pushdown",
          "comm_subexpr_elim", "comm_subplan_elim", "simplify_expression"):
    check(f"A2 QueryOptFlags exposes {f}", f in flags, True)
check("A2 there are TWO CSE flags where the docs list one",
      "comm_subexpr_elim" in flags and "comm_subplan_elim" in flags, True)

# A3 — profiling
result, profile = df.lazy().filter(pl.col("a") > 3).group_by("k").agg(pl.col("a").sum()).profile()
check("A3 profile returns a node timing frame", profile.columns, ["node", "start", "end"])
check("A3 and the query still returns its result", result.height, 2)

# A4 — two engines, same answer
q = df.lazy().filter(pl.col("a") > 3)
check("A4 in-memory engine", q.collect(engine="in-memory").height, 6)
check("A4 streaming engine agrees", q.collect(engine="streaming").height, 6)

# B1 — the unoptimized plan is what you wrote; the optimized one is what runs
unopt = df.lazy().select("a", "b", "k").filter(pl.col("a") > 3).select("b").explain(optimized=False)
check("B1 unoptimized plan reads all columns", "*/3 COLUMNS" in unopt, True)
check("B1 optimized plan does not", "*/3 COLUMNS" in plan_proj, False)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
