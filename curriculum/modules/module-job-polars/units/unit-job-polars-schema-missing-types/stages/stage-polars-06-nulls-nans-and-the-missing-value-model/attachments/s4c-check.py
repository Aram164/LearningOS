"""Assert the nulls / NaNs / missing-value-model answer key."""
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


d = pl.DataFrame({"a": [1, None]})

# Task A1 — three-valued logic
check("A1 arithmetic propagates", d.select(pl.col("a") + 1).to_series().to_list(), [2, None])
check("A1 comparison propagates", d.select(pl.col("a") > 0).to_series().to_list(), [True, None])
check("A1 null == null is null", d.select(pl.col("a") == pl.col("a")).to_series().to_list(), [True, None])
check("A1 eq_missing treats missing as a value",
      d.select(pl.col("a").eq_missing(pl.col("a"))).to_series().to_list(), [True, True])
check("A1 filter keeps only True", d.filter(pl.col("a") > 0).height, 1)
check("A1 is_in propagates", d.select(pl.col("a").is_in([1, 2])).to_series().to_list(), [True, None])
check("A1 TRAP None in the list does not make null match",
      d.select(pl.col("a").is_in([1, None])).to_series().to_list(), [True, None])

# Task A2 — placement operations treat missing as a value
g = pl.DataFrame({"k": [None, "a", None]}).group_by("k").len().sort("k", nulls_last=True)
check("A2 group_by keeps a null group", g.to_dict(as_series=False), {"k": ["a", None], "len": [1, 2]})
check("A2 unique keeps null as a value", pl.DataFrame({"k": [None, "a", None]}).unique().height, 2)
check("A2 sort places nulls first by default", pl.Series([2, None, 1]).sort().to_list(), [None, 1, 2])
check("A2 n_unique counts null as one value", pl.Series([None, None]).n_unique(), 1)

# Task A3 — the verbs
s = pl.Series([1.0, None, 3.0, float("nan")])
check("A3 null_count counts only nulls", s.null_count(), 1)
check("A3 is_null", s.is_null().to_list(), [False, True, False, False])
check("A3 is_nan is three-valued", s.is_nan().to_list(), [False, None, False, True])
filled = s.fill_null(0).to_list()
check("A3 fill_null does not touch NaN", filled[:3], [1.0, 0.0, 3.0])
check("A3 fill_nan(None) is the bridge to pandas' model",
      s.fill_nan(None).is_null().to_list(), [False, True, False, True])
check("A3 forward fill", s.fill_null(strategy="forward").to_list()[:3], [1.0, 1.0, 3.0])

# Task B1 — the flipped grouping default
frame = {"k": [None, "a", None], "v": [1, 1, 1]}
pl_groups = pl.DataFrame(frame).group_by("k").agg(pl.col("v").sum())
check("B1 polars keeps the null group", pl_groups.height, 2)
check("B1 polars null group sums to 2",
      pl_groups.filter(pl.col("k").is_null())["v"].to_list(), [2])
pd_default = pd.DataFrame(frame).groupby("k")["v"].sum()
check("B1 pandas DROPS the null-key rows by default", len(pd_default), 1)
check("B1 and the two rows are simply gone", int(pd_default.sum()), 1)
pd_keep = pd.DataFrame(frame).groupby("k", dropna=False)["v"].sum()
check("B1 dropna=False matches polars", len(pd_keep), 2)
check("B1 and then the totals agree", int(pd_keep.sum()), int(pl_groups["v"].sum()))

# Task B2 / B3
sorted_pd = pd.Series([2, None, 1]).sort_values().tolist()
check("B2 pandas puts nulls last", [sorted_pd[0], sorted_pd[1]], [1.0, 2.0])
check("B2 polars puts nulls first", pl.Series([2, None, 1]).sort().to_list(), [None, 1, 2])
check("B3 pandas says two missing values are NOT equal",
      (pd.Series([None]) == pd.Series([None])).tolist(), [False])
check("B3 polars says unknown", pl.DataFrame({"a": [None]}).select(pl.col("a") == pl.col("a")).to_series().to_list(),
      [None])
check("B3 and eq_missing says equal",
      pl.DataFrame({"a": [None]}).select(pl.col("a").eq_missing(pl.col("a"))).to_series().to_list(), [True])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
