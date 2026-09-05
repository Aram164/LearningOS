"""Assert the type-promotion / coercion / strictness answer key."""
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


def supertype(a, b):
    f = pl.DataFrame([pl.Series("x", [1], dtype=a), pl.Series("y", [1], dtype=b)])
    return f.select(pl.col("x") + pl.col("y")).dtypes[0]


# Task A1 — the supertype rule and its edge
check("A1 Int8+Int64", supertype(pl.Int8, pl.Int64), pl.Int64)
check("A1 Int8+UInt8 widens one size", supertype(pl.Int8, pl.UInt8), pl.Int16)
check("A1 Int32+UInt32 widens one size", supertype(pl.Int32, pl.UInt32), pl.Int64)
check("A1 EDGE Int64+UInt64 falls to Float64", supertype(pl.Int64, pl.UInt64), pl.Float64)
check("A1 UInt8+Int64", supertype(pl.UInt8, pl.Int64), pl.Int64)
check("A1 Float32+Int64", supertype(pl.Float32, pl.Int64), pl.Float64)
check("A1 Float32+Float64", supertype(pl.Float32, pl.Float64), pl.Float64)
check("A1 Boolean+Int64 is allowed and numeric",
      pl.DataFrame({"b": [True, False], "i": [1, 2]}).select(pl.col("b") + pl.col("i")).dtypes, [pl.Int64])
check("A1 but any() still refuses an integer Series",
      raises(lambda: pl.Series([0, 1]).any()), "SchemaError")
check("A1 String+Int64 refused",
      raises(lambda: pl.DataFrame({"s": ["1"], "i": [1]}).select(pl.col("s") + pl.col("i"))),
      "InvalidOperationError")
# The edge, made concrete: above 2^53 the Float64 supertype is no longer exact.
check("A1 EDGE Float64 cannot tell 2^53 from 2^53+1", float(2 ** 53) == float(2 ** 53 + 1), True)
check("A1 EDGE and the promotion really goes through it",
      pl.DataFrame([pl.Series("a", [2 ** 53], dtype=pl.Int64),
                    pl.Series("b", [1], dtype=pl.UInt64)])
        .select((pl.col("a") + pl.col("b")).alias("s")).dtypes, [pl.Float64])

# Task A2 — strictness
check("A2 str->int strict raises", raises(lambda: pl.Series(["1", "x"]).cast(pl.Int64)), "InvalidOperationError")
check("A2 strict=False gives null", pl.Series(["1", "x"]).cast(pl.Int64, strict=False).to_list(), [1, None])
check("A2 overflow cast strict raises", raises(lambda: pl.Series([300]).cast(pl.Int8)), "InvalidOperationError")
check("A2 overflow cast non-strict gives null, not a wrapped value",
      pl.Series([300]).cast(pl.Int8, strict=False).to_list(), [None])
check("A2 float->int truncates toward zero", pl.Series([1.9, -1.9]).cast(pl.Int64).to_list(), [1, -1])

# Task B1 — the headline divergence
check("B1 pandas astype int8 returns the low byte", pd.Series([300]).astype("int8").tolist(), [44])
check("B1 and 44 is 300 mod 256", 300 % 256, 44)
check("B1 polars refuses the same conversion",
      raises(lambda: pl.Series([300]).cast(pl.Int8)), "InvalidOperationError")
check("B1 pandas float->int agrees with polars", pd.Series([1.9, -1.9]).astype("int64").tolist(), [1, -1])

# Task B2 / B3 — the agreements, on executed evidence
check("B2 polars true division", (pl.Series([5]) / pl.Series([2])).dtype, pl.Float64)
check("B2 polars floor division", (pl.Series([5]) // pl.Series([2])).dtype, pl.Int64)
check("B2 pandas true division", str((pd.Series([5]) / pd.Series([2])).dtype), "float64")
check("B2 pandas floor division", str((pd.Series([5]) // pd.Series([2])).dtype), "int64")
check("B3 polars int8 arithmetic wraps",
      (pl.Series([127], dtype=pl.Int8) + pl.Series([1], dtype=pl.Int8)).to_list(), [-128])
check("B3 pandas int8 arithmetic wraps identically",
      (pd.Series([127], dtype="int8") + pd.Series([1], dtype="int8")).tolist(), [-128])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
