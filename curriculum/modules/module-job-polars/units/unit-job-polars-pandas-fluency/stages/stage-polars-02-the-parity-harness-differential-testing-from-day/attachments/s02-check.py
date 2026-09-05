"""Assert the twelve seed-case divergences of Stage 2 against the pinned environment.

    Stratum/.venv/bin/python check.py

A failure means either you are not on pandas 3.0.2 / polars 1.36.0, or one of
the libraries changed behaviour. Both invalidate every downstream parity
conclusion, so resolve it before adding cases.
"""
import math
import sys

import pandas as pd
import polars as pl

if (pd.__version__, pl.__version__) != ("3.0.2", "1.36.0"):
    sys.exit(
        f"FATAL: the seed table asserts pandas 3.0.2 / polars 1.36.0; you have "
        f"{pd.__version__} / {pl.__version__}. Use Stratum/.venv/bin/python."
    )

passed = 0
failed = 0


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
    except Exception as exc:  # noqa: BLE001 - the type is the assertion
        return type(exc).__name__
    return None


NULL_F_PD = pd.Series([None, None], dtype="float64")
NULL_F_PL = pl.Series([None, None], dtype=pl.Float64)

# 1 — dtype survives an empty result
check("1 pandas empty dtype", str(pd.DataFrame({"v": [1, 2]}).query("v > 5")["v"].dtype), "int64")
check("1 polars empty dtype", str(pl.DataFrame({"v": [1, 2]}).filter(pl.col("v") > 5)["v"].dtype), "Int64")
check("1 pandas empty shape", pd.DataFrame({"v": [1, 2]}).query("v > 5").shape, (0, 1))
check("1 polars empty shape", pl.DataFrame({"v": [1, 2]}).filter(pl.col("v") > 5).shape, (0, 1))

# 2 — the empty sum agrees
check("2 pandas all-null sum", float(NULL_F_PD.sum()), 0.0)
check("2 polars all-null sum", NULL_F_PL.sum(), 0.0)

# 3 — mean/min/max diverge in representation
check("3 pandas all-null mean is NaN", math.isnan(NULL_F_PD.mean()), True)
check("3 pandas all-null min is NaN", math.isnan(NULL_F_PD.min()), True)
check("3 pandas all-null max is NaN", math.isnan(NULL_F_PD.max()), True)
check("3 polars all-null mean", NULL_F_PL.mean(), None)
check("3 polars all-null min", NULL_F_PL.min(), None)
check("3 polars all-null max", NULL_F_PL.max(), None)

# 4 — the counters, and n_unique counting null as a value
check("4 pandas count", int(NULL_F_PD.count()), 0)
check("4 pandas size", NULL_F_PD.size, 2)
check("4 pandas nunique", NULL_F_PD.nunique(), 0)
check("4 polars count", NULL_F_PL.count(), 0)
check("4 polars len", NULL_F_PL.len(), 2)
check("4 polars n_unique counts null", NULL_F_PL.n_unique(), 1)

# 5 — mixed-type construction
check("5 pandas mixed dtype", str(pd.Series([1, "a", 2.0]).dtype), "object")
check("5 polars mixed raises", raises(lambda: pl.Series([1, "a", 2.0])), "TypeError")
check("5 polars strict=False coerces", pl.Series([1, "a", 2.0], strict=False).to_list(), ["1", "a", "2.0"])

# 6 — the dangerous cell
check("6 pandas string sum concatenates", pd.Series(["a", "b"]).sum(), "ab")
check("6 polars string sum raises", raises(lambda: pl.Series(["a", "b"]).sum()), "InvalidOperationError")

# 7 — truthiness
check("7 pandas any on ints", bool(pd.Series([0, 1]).any()), True)
check("7 polars any on ints raises", raises(lambda: pl.Series([0, 1]).any()), "SchemaError")

# 8 — accumulation order: no global tolerance is correct here
check("8 pandas sum of ten 0.1", float(pd.Series([0.1] * 10).sum()), 1.0)
check("8 polars sum of ten 0.1", pl.Series([0.1] * 10).sum(), 0.9999999999999999)
check("8 the two really differ", pd.Series([0.1] * 10).sum() == pl.Series([0.1] * 10).sum(), False)

# 9 — duplicate column names
check("9 pandas allows duplicate names", pd.DataFrame([[1, 2]], columns=["a", "a"]).shape, (1, 2))
check(
    "9 polars refuses duplicate names",
    raises(lambda: pl.DataFrame([pl.Series("a", [1]), pl.Series("a", [2])])),
    "DuplicateError",
)

# 10 — two defaults that agree, not two contracts
check("10 pandas datetime unit", str(pd.to_datetime(pd.Series(["2026-01-01"])).dtype), "datetime64[us]")
check("10 polars datetime unit", pl.Series(["2026-01-01"]).str.to_datetime().dtype.time_unit, "us")

# 11 — duplicate-label cross join, as a harness case
gh = pd.Series([1, 2], index=["x", "x"]) + pd.Series([10, 20, 30], index=["x", "x", "x"])
check("11 cross-join length", len(gh), 6)
check("11 cross-join order", gh.tolist(), [11, 21, 31, 12, 22, 32])
check(
    "11 polars length mismatch raises",
    raises(lambda: pl.Series([1, 2]) + pl.Series([10, 20, 30])),
    "InvalidOperationError",
)

# 12 — exception class is part of the contract
check("12 pandas missing column", raises(lambda: pd.DataFrame({"a": [1]})["zz"]), "KeyError")
check("12 polars missing column", raises(lambda: pl.DataFrame({"a": [1]})["zz"]), "ColumnNotFoundError")
check(
    "12 polars missing column in an expression",
    raises(lambda: pl.DataFrame({"a": [1]}).select(pl.col("zz"))),
    "ColumnNotFoundError",
)

# Task 2 — the null-policy table
check("T2 pandas skips NaN in sum", float(pd.Series([1.0, float("nan")]).sum()), 1.0)
check("T2 polars NaN poisons the sum", math.isnan(pl.Series([1.0, float("nan")]).sum()), True)
check("T2 polars NaN sum is not 1.0", pl.Series([1.0, float("nan")]).sum() == 1.0, False)
check("T2 polars null sum skips", pl.Series([1.0, None]).sum(), 1.0)
check("T2 polars is_nan on a null row", pl.Series([1.0, None]).is_nan().to_list(), [False, None])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
