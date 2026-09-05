"""Assert the selection-and-projection answer key.

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


df = pl.DataFrame({"k": ["a", "b", "a", "c", "b"], "v": [1, 2, 1, 3, 2], "w": [10, 20, 30, 40, 50]})
pdf = df.to_pandas()

# Part A1 — the reference solutions all run and give these answers
check("A1.1 above own mean", df.filter(pl.col("v") > pl.col("v").mean())["w"].to_list(), [20, 40, 50])
check("A1.2 is_in", df.filter(pl.col("k").is_in(["a", "c"])).select("k", "w")["w"].to_list(), [10, 30, 40])
check("A1.3 name.suffix", df.select(cs.starts_with("w").name.suffix("_raw")).columns, ["w_raw"])
check("A1.4 top_k", sorted(df.top_k(2, by="w")["w"].to_list()), [40, 50])
# Compared with a tolerance, not for equality: the division is done in a
# different order than Python's, so the last row differs in the final bit.
# This is Session 1 seed case 8 turning up uninvited in an unrelated assertion.
check("A1.5 share of total",
      [round(x, 12) for x in df.select(pl.col("w") / pl.col("w").sum())["w"].to_list()],
      [round(n / 150, 12) for n in (10, 20, 30, 40, 50)])
check("A1.5 and exact equality would have failed",
      df.select(pl.col("w") / pl.col("w").sum())["w"].to_list()[-1] == 50 / 150, False)
check("A1.6 over() keeps height", df.filter(pl.col("w") > pl.col("w").mean().over("k"))["w"].to_list(), [30, 50])
check("A1.7 when/then band",
      df.with_columns(pl.when(pl.col("w") > 25).then(pl.lit("high")).otherwise(pl.lit("low")).alias("band"))
        ["band"].to_list(), ["low", "low", "high", "high", "high"])
check("A1.8 first per group in appearance order",
      df.group_by("k", maintain_order=True).first()["w"].to_list(), [10, 20, 40])
check("A1.9 selector used three times in one statement",
      df.with_columns((cs.numeric() - cs.numeric().mean()) / cs.numeric().std()).columns, ["k", "v", "w"])
check("A1.10 reorder without naming k", df.select("k", "w", "v").columns, ["k", "w", "v"])

# A1.6 the trap: the group-by-and-join route gives the same rows, by more work
joined = (df.join(df.group_by("k").agg(pl.col("w").mean().alias("m")), on="k")
            .filter(pl.col("w") > pl.col("m")).sort("w"))
check("A1.6 the pandas reflex reaches the same answer", joined["w"].to_list(), [30, 50])

# Part A2 — the optimizer passes are visible in explain()
plan2 = df.lazy().select("k", "v", "w").filter(pl.col("v") > 1).select("w").explain()
check("A2 projection pushdown: scan reads 2 of 3", "2/3 COLUMNS" in plan2, True)
check("A2 and k is not among them", '"v", "w"' in plan2, True)
plan3 = df.lazy().sort("v").head(2).explain()
check("A2 slice pushdown into the sort", "slice: (0, 2)" in plan3, True)
unopt = df.lazy().filter(pl.col("v") > 1).select("k", "w").explain(optimized=False)
check("A2 unoptimized plan still says SELECT", unopt.strip().startswith("SELECT"), True)
check("A2 streaming engine runs the same query",
      df.lazy().filter(pl.col("v") > 1).collect(engine="streaming").shape, (3, 3))

# Part A3 — four ways, and what differs
check("A3 frame-level filter then getitem is a Series",
      type(df.filter(pl.col("v") > 1)["w"]).__name__, "Series")
check("A3 frame-level filter then select is a DataFrame",
      type(df.filter(pl.col("v") > 1).select("w")).__name__, "DataFrame")
check("A3 expression-level filter gives the same values",
      df.select(pl.col("w").filter(pl.col("v") > 1))["w"].to_list(), [20, 40, 50])
check("A3 expression-level filter works inside an aggregation",
      df.group_by("k", maintain_order=True)
        .agg(pl.col("w").filter(pl.col("v") > 1).sum())["w"].to_list(), [0, 70, 40])

# Part B2 — the mask aligns by label
mask = pd.Series([True, False, True, False, True], index=[4, 3, 2, 1, 0])
import warnings  # noqa: E402
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    got = pdf[mask]["w"].tolist()
check("B2 pandas aligns the mask by label", got, [10, 30, 50])
check("B2 and pandas warns that it reindexed",
      any("reindexed" in str(w.message) for w in caught), True)
check("B2 polars takes a boolean list positionally",
      df.filter(pl.Series([True, False, True, False, True]))["w"].to_list(), [10, 30, 50])
check("B2 written order would have given a different set",
      [w for w, m in zip([10, 20, 30, 40, 50], [True, False, True, False, True]) if m], [10, 30, 50])

# Part B3 — exception classes
check("B3 pandas missing column", raises(lambda: pdf[["zz"]]), "KeyError")
check("B3 polars missing column", raises(lambda: df.select(["zz"])), "ColumnNotFoundError")

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
