"""Assert the drop_duplicates / unique answer key.

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


df = pl.DataFrame({"k": ["a", "b", "a", "c", "b"], "v": [1, 2, 1, 3, 2], "w": [10, 20, 30, 40, 50]})
pdf = df.to_pandas()

# Part B1 — the parameter mapping, quoted as w-lists
check("B1 full-row dedup pandas", pdf.drop_duplicates()["w"].tolist(), [10, 20, 30, 40, 50])
check("B1 full-row dedup polars", df.unique(maintain_order=True)["w"].to_list(), [10, 20, 30, 40, 50])
check("B1 keep=first pandas", pdf.drop_duplicates(subset=["k"], keep="first")["w"].tolist(), [10, 20, 40])
check("B1 keep=first polars",
      df.unique(subset=["k"], keep="first", maintain_order=True)["w"].to_list(), [10, 20, 40])
check("B1 keep=last pandas", pdf.drop_duplicates(subset=["k"], keep="last")["w"].tolist(), [30, 40, 50])
check("B1 keep=last polars",
      df.unique(subset=["k"], keep="last", maintain_order=True)["w"].to_list(), [30, 40, 50])
check("B1 keep=False pandas", pdf.drop_duplicates(subset=["k"], keep=False)["w"].tolist(), [40])
check("B1 keep=False maps to keep='none'",
      df.unique(subset=["k"], keep="none", maintain_order=True)["w"].to_list(), [40])
check("B1 keep='any' picks one of each, order unspecified",
      sorted(df.unique(subset=["k"], keep="any")["k"].to_list()), ["a", "b", "c"])

# Part A2 — the ordering promise
check("A2 maintain_order gives input order", df.unique(maintain_order=True)["w"].to_list(), [10, 20, 30, 40, 50])
check("A2 the default result is still a permutation of the same rows",
      sorted(df.unique()["w"].to_list()), [10, 20, 30, 40, 50])

# Part B2 — the stage's real finding: same name, different function
check("B2 pandas duplicated marks 2nd-and-later",
      pdf.duplicated(subset=["k"]).tolist(), [False, False, True, False, True])
check("B2 polars is_duplicated marks ALL occurrences",
      df.select(pl.struct("k").is_duplicated()).to_series().to_list(), [True, True, True, False, True])
check("B2 is_first_distinct is the real counterpart",
      df.select(pl.col("k").is_first_distinct()).to_series().to_list(), [True, True, False, True, False])
check("B2 ~is_first_distinct equals pandas duplicated",
      df.select(~pl.col("k").is_first_distinct()).to_series().to_list(),
      pdf.duplicated(subset=["k"]).tolist())
check("B2 and is_duplicated does NOT",
      df.select(pl.struct("k").is_duplicated()).to_series().to_list() == pdf.duplicated(subset=["k"]).tolist(),
      False)

# Part B3 — nulls are values for dedup on both sides
check("B3 nulls dedup pandas", pd.DataFrame({"k": ["a", None, None]}).drop_duplicates().shape, (2, 1))
check("B3 nulls dedup polars", pl.DataFrame({"k": ["a", None, None]}).unique().shape, (2, 1))
nan_pl = pl.DataFrame({"k": [1.0, float("nan"), float("nan")]})
check("B3 NaNs dedup polars", nan_pl.unique().height, 2)
check("B3 empty frame polars", pl.DataFrame({"k": pl.Series([], dtype=pl.Int64)}).unique().height, 0)

# Part A1 — the native forms
check("A1.5 rows whose key occurs once",
      df.filter(pl.len().over("k") == 1)["w"].to_list(), [40])
check("A1.8 count of distinct keys", df.select(pl.col("k").n_unique()).item(), 3)
check("A1.9 distinct pairs", df.unique(subset=["k", "v"], maintain_order=True).height, 3)
check("A1.10 keys occurring more than twice",
      df.filter(pl.len().over("k") > 2)["w"].to_list(), [])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
