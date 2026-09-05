"""Assert the DROPNA answer key.

    Stratum/.venv/bin/python check.py
"""
import sys

import pandas as pd
import polars as pl
import polars.selectors as cs

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


df = pl.DataFrame({
    "a": pl.Series([1.0, None, 3.0, float("nan")], dtype=pl.Float64),
    "b": ["x", None, "z", "w"],
    "c": [1, 2, 3, 4],
})
pdf = df.to_pandas()

# Part A — the toolkit
check("A1.1 null_count", df.null_count().to_dict(as_series=False), {"a": [1], "b": [1], "c": [0]})
check("A1.2 nan count is a different row", df.select(pl.col("a").is_nan().sum()).item(), 1)
check("A1.3 drop_nulls keeps the NaN row", df.drop_nulls()["c"].to_list(), [1, 3, 4])
check("A1.4 subset=a", df.drop_nulls(subset="a")["c"].to_list(), [1, 3, 4])
check("A1.5 selector subset", df.drop_nulls(cs.numeric())["c"].to_list(), [1, 3, 4])
filled = df["a"].fill_null(0).to_list()
check("A1.6 fill_null leaves NaN alone", [filled[0], filled[1], filled[2]], [1.0, 0.0, 3.0])
check("A1.6 and row 3 is still NaN", filled[3] != filled[3], True)
check("A1.7 forward fill", df["a"].fill_null(strategy="forward").to_list()[:3], [1.0, 1.0, 3.0])
check("A1.8 fill_nan(None) makes it missing", df["a"].fill_nan(None).to_list(), [1.0, None, 3.0, None])
check("A1.10 keep rows where b is missing", df.filter(pl.col("b").is_null())["c"].to_list(), [2])

# Part A2 — the normalization sandwich IS pandas' dropna
sandwich = df.with_columns(cs.float().fill_nan(None)).drop_nulls()
check("A2 sandwich reproduces pandas dropna", sandwich["c"].to_list(), pdf.dropna()["c"].tolist())
check("A2 and the reverse order does not",
      df.drop_nulls().with_columns(cs.float().fill_nan(None))["c"].to_list(), [1, 3, 4])

# Part B1 — the divergence on the primary API
check("B1 polars drop_nulls", df.drop_nulls()["c"].to_list(), [1, 3, 4])
check("B1 pandas dropna", pdf.dropna()["c"].tolist(), [1, 3])
check("B1 they differ by exactly the NaN row",
      set(df.drop_nulls()["c"].to_list()) - set(pdf.dropna()["c"].tolist()), {4})

# Part B2 — how/thresh/axis
subset = cs.by_name("a", "b")
check("B2 how='all' polars",
      df.filter(~pl.all_horizontal(subset.is_null()))["c"].to_list(), [1, 3, 4])
check("B2 how='all' pandas", pdf.dropna(how="all")["c"].tolist(), [1, 2, 3, 4])
check("B2 thresh=2 polars",
      df.filter(pl.sum_horizontal(subset.is_not_null().cast(pl.Int64)) >= 2)["c"].to_list(), [1, 3, 4])
check("B2 axis=1 pandas keeps only c", pdf.dropna(axis=1).columns.tolist(), ["c"])
check("B2 axis=1 polars form agrees",
      [c for c in df.columns if df[c].null_count() == 0], ["c"])

# Part B3 — the failure boundary
check("B3 pandas refuses how+thresh together",
      raises(lambda: pdf.dropna(how="any", thresh=2)), "TypeError")
check("B3 pandas missing subset column", raises(lambda: pdf.dropna(subset=["zz"])), "KeyError")
check("B3 polars missing subset column", raises(lambda: df.drop_nulls(subset="zz")), "ColumnNotFoundError")

# Part C — thresh edges fall out of the count, with no special cases
counts = df.select(pl.sum_horizontal(subset.is_not_null().cast(pl.Int64)).alias("n"))["n"].to_list()
check("C1 non-null counts per row", counts, [2, 0, 2, 2])
check("C1 thresh=0 keeps everything",
      df.filter(pl.sum_horizontal(subset.is_not_null().cast(pl.Int64)) >= 0).height, 4)
check("C1 thresh above the subset size keeps nothing",
      df.filter(pl.sum_horizontal(subset.is_not_null().cast(pl.Int64)) >= 3).height, 0)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
