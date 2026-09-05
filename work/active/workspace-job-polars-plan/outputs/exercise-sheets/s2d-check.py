"""Assert the assign-lowering answer key.

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


df = pl.DataFrame({"a": [1, 2, 3], "b": [1.5, 2.5, 3.5], "s": ["x", "y", "z"]})
pdf = pd.DataFrame({"a": [1, 2, 3], "b": [1.5, 2.5, 3.5], "s": ["x", "y", "z"]})

# Row 3 — independent entries share one layer
check("R3 independent entries in one context",
      df.with_columns(c=pl.col("a") * 2, d=pl.col("b") * 2)[["c", "d"]].to_dict(as_series=False),
      {"c": [2, 4, 6], "d": [3.0, 5.0, 7.0]})
check("R3 pandas agrees",
      pdf.assign(c=lambda t: t.a * 2, d=lambda t: t.b * 2)[["c", "d"]].to_dict("list"),
      {"c": [2, 4, 6], "d": [3.0, 5.0, 7.0]})

# Row 4 — sibling dependency raises when collapsed
check("R4 one context raises",
      raises(lambda: df.with_columns(z=pl.col("a") * 2, w=pl.col("z") + 1)), "ColumnNotFoundError")
check("R4 two contexts work",
      df.with_columns(z=pl.col("a") * 2).with_columns(w=pl.col("z") + 1)["w"].to_list(), [3, 5, 7])

# Row 5 — the silent wrong answer, which is the point of the stage
naive = df.with_columns(a=pl.col("a") * 10, b_wrong=pl.col("a") + 1)
staged = df.with_columns(a=pl.col("a") * 10).with_columns(b_right=pl.col("a") + 1)
check("R5 naive one-context reads the OLD a", naive["b_wrong"].to_list(), [2, 3, 4])
check("R5 staged reads the NEW a", staged["b_right"].to_list(), [11, 21, 31])
check("R5 pandas matches the staged form",
      pdf.assign(a=lambda t: t.a * 10, b=lambda t: t.a + 1)["b"].tolist(), [11, 21, 31])
check("R5 and the naive form raises nothing at all", raises(lambda: naive), None)

# Row 6 — Python rejects it before pandas sees it
check("R6 duplicate kwarg is a SyntaxError",
      raises(lambda: compile("f(a=1, a=2)", "<t>", "eval")), "SyntaxError")

# Row 7/8 — sequence constants
check("R7 right-length sequence", pdf.assign(c=[1, 2, 3])["c"].tolist(), [1, 2, 3])
check("R8 pandas length mismatch", raises(lambda: pdf.assign(c=[1, 2])), "ValueError")
check("R8 polars length mismatch", raises(lambda: df.with_columns(pl.Series("c", [1, 2]))), "ShapeError")

# Row 12 — broadcast agrees on non-empty, and the empty case is conditional
check("R12 polars broadcasts a reduction",
      df.with_columns(c=pl.col("a").sum())["c"].to_list(), [6, 6, 6])
check("R12 pandas broadcasts too", pdf.assign(c=lambda t: t.a.sum())["c"].tolist(), [6, 6, 6])
empty_pl = pl.DataFrame({"a": pl.Series([], dtype=pl.Float64)})
empty_pd = pd.DataFrame({"a": pd.Series([], dtype="float64")})
check("R12 empty sum agrees", empty_pl.select(pl.col("a").sum()).item(), float(empty_pd["a"].sum()))
check("R12 empty mean diverges: polars null", empty_pl.select(pl.col("a").mean()).item(), None)
check("R12 empty mean diverges: pandas NaN", empty_pd["a"].mean() != empty_pd["a"].mean(), True)

# Task 3 — root_names is exact on the Polars side
check("T3 root_names of a two-column expression",
      sorted((pl.col("a") + pl.col("b")).meta.root_names()), ["a", "b"])
check("T3 root_names sees through an alias",
      (pl.col("a") * 2).alias("z").meta.root_names(), ["a"])
check("T3 a literal reads nothing", pl.lit(5).meta.root_names(), [])

# Task 4 — the two surprises
check("T4.1 an element-wise python callable HAS a native home",
      df.with_columns(c=pl.col("a").map_elements(lambda v: v + 1, return_dtype=pl.Int64))["c"].to_list(),
      [2, 3, 4])
check("T4.5 astype('category') is metadata on both sides",
      df.with_columns(pl.col("s").cast(pl.Categorical)).dtypes[2], pl.Categorical)
check("T4.2 rolling mean has a native expression",
      df.with_columns(c=pl.col("a").rolling_mean(window_size=2))["c"].to_list(), [None, 1.5, 2.5])
check("T4.2 pandas rolling agrees on the defined rows",
      pdf.assign(c=lambda t: t.a.rolling(2).mean())["c"].tolist()[1:], [1.5, 2.5])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
