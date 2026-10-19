"""Assert the Stage 'expression grammar and contexts' answer key.

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


df = pl.DataFrame({"a": [1, 2, 3], "b": [1.5, 2.5, 3.5], "s": ["x", "y", "z"], "d": [None, 1, 2]})
ppdf = pd.DataFrame({"a": [1, 2, 3]})

# Task 1 — sibling visibility
check("T1.1 with_columns siblings are independent",
      raises(lambda: df.with_columns(z=pl.col("a") * 2, w=pl.col("z") + 1)), "ColumnNotFoundError")
check("T1.2 staged with_columns works",
      df.with_columns(z=pl.col("a") * 2).with_columns(w=pl.col("z") + 1)["w"].to_list(), [3, 5, 7])
check("T1.3 pandas assign is sequential",
      ppdf.assign(z=lambda t: t.a * 2, w=lambda t: t.z + 1)["w"].tolist(), [3, 5, 7])
overwritten = ppdf.assign(a=lambda t: t.a * 10, b=lambda t: t.a + 1)
check("T1.4 assign reads the overwritten name", overwritten["a"].tolist(), [10, 20, 30])
check("T1.4 assign b from the new a", overwritten["b"].tolist(), [11, 21, 31])
check("T1 non-callable sibling also works",
      ppdf.assign(z=ppdf.a * 2, w=lambda t: t.z + 1)["w"].tolist(), [3, 5, 7])

# Task 2 — contexts and shape
check("T2 select narrows", df.select(pl.col("a") * 2).shape, (3, 1))
check("T2 with_columns widens", df.with_columns(pl.col("a") * 2).shape, (3, 4))
check("T2 scalar broadcasts",
      df.select(pl.col("a"), pl.col("a").sum().alias("t"))["t"].to_list(), [6, 6, 6])
check("T2 non-unit length is refused",
      raises(lambda: df.select(pl.col("a"), pl.col("a").head(2).alias("h"))), "ShapeError")
check("T2 filter keeps width", df.filter(pl.col("a") > 1).shape, (2, 4))
check("T2 regex is multi-output", df.select(pl.col("^(a|s)$")).columns, ["a", "s"])
check("T2 alias cannot name two columns",
      raises(lambda: df.with_columns(pl.col("^(a|s)$").alias("q"))), "ComputeError")
check("T2 name.suffix can",
      df.with_columns(pl.col("a", "s").name.suffix("_2")).columns, ["a", "b", "s", "d", "a_2", "s_2"])

# Task 3 — reading the tree
e = (pl.col("a") * 2).alias("z")
check("T3 output_name", e.meta.output_name(), "z")
check("T3 root_names", e.meta.root_names(), ["a"])
check("T3 has_multiple_outputs", pl.col("^a.*$").meta.has_multiple_outputs(), True)
check("T3 tree_format renders", "binary: *" in e.meta.tree_format(return_as_string=True), True)
check("T3 collect_schema without data",
      dict(df.lazy().select(pl.col("a") * 2).collect_schema()), {"a": pl.Int64})
check("T3 lazy build of a bad column succeeds",
      type(df.lazy().select(pl.col("zz"))).__name__, "LazyFrame")
check("T3 the error arrives at collect",
      raises(lambda: df.lazy().select(pl.col("zz")).collect()), "ColumnNotFoundError")

# Task 4 — assign lowering rows
check("T4.1 pandas scalar broadcast", pd.DataFrame({"a": [1, 2]}).assign(c=5)["c"].tolist(), [5, 5])
check("T4.1 polars lit against Float64 promotes",
      df.select(pl.col("b") + pl.lit(1)).dtypes, [pl.Float64])
check("T4.6 pandas length mismatch",
      raises(lambda: pd.DataFrame({"a": [1, 2, 3]}).assign(c=[1, 2])), "ValueError")
check("T4.6 polars length mismatch",
      raises(lambda: df.with_columns(pl.Series("c", [1, 2]))), "ShapeError")
# Row 5 lowered naively to one context: no error, wrong answer.
naive = df.with_columns(a=pl.col("a") * 10, b_wrong=pl.col("a") + 1)
check("T4.5 one context silently reads the OLD a", naive["b_wrong"].to_list(), [2, 3, 4])
staged = df.with_columns(a=pl.col("a") * 10).with_columns(b_right=pl.col("a") + 1)
check("T4.5 staged reads the NEW a", staged["b_right"].to_list(), [11, 21, 31])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
