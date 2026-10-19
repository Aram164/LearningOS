"""Assert the horizontal-logic / folds / conditionals answer key.

    Stratum/.venv/bin/python check.py
"""
import sys

import pandas as pd
import polars as pl

if (pd.__version__, pl.__version__) != ("3.0.2", "1.36.0"):
    sys.exit(f"FATAL: key asserts pandas 3.0.2 / polars 1.36.0; you have {pd.__version__} / {pl.__version__}.")

passed = failed = 0


def check(label, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {label}\n    got  {got!r}\n    want {want!r}")


def raises(fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__
    return None


k = pl.DataFrame({"p": [True, True, False, None, None], "q": [True, None, None, False, None]})

# Task 1 — the Kleene truth tables
check("T1 any_horizontal", k.select(pl.any_horizontal("p", "q")).to_series().to_list(),
      [True, True, None, None, None])
check("T1 all_horizontal", k.select(pl.all_horizontal("p", "q")).to_series().to_list(),
      [True, None, False, False, None])

# Task 2 — the keyword that is not in this build
check("T2 any_horizontal has no ignore_nulls",
      raises(lambda: k.select(pl.any_horizontal("p", "q", ignore_nulls=False))), "TypeError")
check("T2 all_horizontal has no ignore_nulls",
      raises(lambda: k.select(pl.all_horizontal("p", "q", ignore_nulls=False))), "TypeError")
# Where it does exist in 1.36.0:
check("T2 Series.any(ignore_nulls=False) is Kleene", pl.Series([False, None]).any(ignore_nulls=False), None)
check("T2 Series.any default treats null as absent", pl.Series([False, None]).any(), False)
check("T2 Series.all(ignore_nulls=False) is Kleene", pl.Series([True, None]).all(ignore_nulls=False), None)
check("T2 Series.all default treats null as absent", pl.Series([True, None]).all(), True)

# Task 3 — fold vs sum_horizontal, and the seed dtype
z = pl.DataFrame({"a": [1, None], "b": [2, 3]})
check("T3 sum_horizontal skips the null", z.select(pl.sum_horizontal("a", "b")).to_series().to_list(), [3, 3])
check("T3 fold propagates the null",
      z.select(pl.fold(0, lambda acc, x: acc + x, pl.all()).alias("f")).to_series().to_list(), [3, None])
ints = pl.DataFrame({"a": [1], "b": [2]})
check("T3 int seed narrows to Int32",
      ints.select(pl.fold(0, lambda acc, x: acc + x, pl.all()).alias("f")).dtypes, [pl.Int32])
check("T3 float seed gives Float64",
      ints.select(pl.fold(0.0, lambda acc, x: acc + x, pl.all()).alias("f")).dtypes, [pl.Float64])
check("T3 typed seed keeps Int64",
      ints.select(pl.fold(pl.lit(0, dtype=pl.Int64), lambda acc, x: acc + x, pl.all()).alias("f")).dtypes,
      [pl.Int64])

# Task 4 — the empty subset
check("T4 any_horizontal() over nothing raises",
      raises(lambda: pl.DataFrame({"a": [1]}).select(pl.any_horizontal())), "ComputeError")
check("T4 all_horizontal() over nothing raises",
      raises(lambda: pl.DataFrame({"a": [1]}).select(pl.all_horizontal())), "ComputeError")

# Task 5 — branch validity
w = pl.DataFrame({"a": [1, 2, 3], "s": ["x", "y", "z"]})
check("T5a unselected invalid branch still raises",
      raises(lambda: w.select(pl.when(pl.col("a") > 100).then(pl.col("s").cast(pl.Int64)).otherwise(0))),
      "InvalidOperationError")
check("T5b constant predicate folds the branch away",
      w.select(pl.when(pl.lit(True)).then(pl.col("a")).otherwise(pl.col("s").cast(pl.Int64)))
       .to_series().to_list(), [1, 2, 3])
check("T5c strict=False makes the branch valid",
      w.select(pl.when(pl.col("a") > 100)
                 .then(pl.col("s").cast(pl.Int64, strict=False)).otherwise(0)).to_series().to_list(),
      [0, 0, 0])
mixed = w.select(pl.when(pl.col("a") > 1).then(pl.col("a")).otherwise(pl.col("s")))
check("T5d Int64/String supertype is String, silently", mixed.to_series().to_list(), ["x", "2", "3"])
check("T5d and the dtype confirms it", mixed.dtypes, [pl.String])
check("T5e no otherwise fills null",
      w.select(pl.when(pl.col("a") > 1).then(pl.col("a"))).to_series().to_list(), [None, 2, 3])
check("T5f no supertype raises",
      raises(lambda: w.select(pl.when(pl.col("a") > 1).then(pl.col("a")).otherwise(pl.lit([1, 2])))),
      "SchemaError")
check("T5 pandas where promotes through NaN instead",
      str(pd.Series([1, 2]).where(pd.Series([False, True])).dtype), "float64")

# Task 6 — the dropna predicate core, built the way the sheet prescribes
import polars.selectors as cs  # noqa: E402

frame = pl.DataFrame({
    "a": pl.Series([1.0, None, None, 1.0, None], dtype=pl.Float64),
    "b": pl.Series([2.0, 3.0, None, float("nan"), None], dtype=pl.Float64),
})
subset = cs.by_name("a", "b")
non_null = pl.sum_horizontal(subset.is_not_null().cast(pl.Int64))

how_any = frame.filter(~pl.any_horizontal(subset.is_null()))
how_all = frame.filter(~pl.all_horizontal(subset.is_null()))
thresh_2 = frame.filter(non_null >= 2)

check("T6 non-null counts per row", frame.select(non_null.alias("n"))["n"].to_list(), [2, 1, 0, 2, 0])
check("T6 how='any' keeps two rows in Polars", how_any.height, 2)
check("T6 how='all' keeps three", how_all.height, 3)
check("T6 thresh=2 keeps two in Polars", thresh_2.height, 2)
check("T6 the NaN row is one of them", how_any["b"].to_list()[1] != how_any["b"].to_list()[1], True)

# The divergence this task exists to find: a round-trip through pandas cannot
# preserve the null/NaN distinction, so the same three predicates disagree.
p = frame.to_pandas()
check("T6 pandas how='any' keeps only one", len(p.dropna(how="any", subset=["a", "b"])), 1)
check("T6 pandas how='all' agrees", len(p.dropna(how="all", subset=["a", "b"])), 3)
check("T6 pandas thresh=2 keeps only one", len(p.dropna(thresh=2, subset=["a", "b"])), 1)
check("T6 how='any' diverges by exactly the NaN row",
      how_any.height - len(p.dropna(how="any", subset=["a", "b"])), 1)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
