"""Assert the UDF / native-rewrite answer key."""
import sys
import warnings

import numpy as np
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fn()
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__
    return None


s = pl.DataFrame({"a": [1, 2, 3]})
warnings.simplefilter("ignore", pl.exceptions.PolarsInefficientMapWarning)

# A1 — the five rungs
check("A1 rung 1 native", s.select(pl.col("a") + 1).to_series().to_list(), [2, 3, 4])
check("A1 rung 2 numpy ufunc", np.sqrt(s.to_series()).to_list()[:2], [1.0, 2 ** 0.5])
check("A1 rung 3 map_batches", s.select(pl.col("a").map_batches(lambda x: x * 2)).to_series().to_list(),
      [2, 4, 6])
check("A1 rung 4 map_elements",
      s.select(pl.col("a").map_elements(lambda v: v + 1, return_dtype=pl.Int64)).to_series().to_list(),
      [2, 3, 4])
check("A1 rung 5 struct row UDF",
      pl.DataFrame({"a": [1], "b": [2]})
        .select(pl.struct("a", "b").map_elements(lambda r: r["a"] + r["b"], return_dtype=pl.Int64))
        .to_series().to_list(), [3])

# A1 TRAP — map_batches returning a different length silently reshapes
check("A1 TRAP map_batches may change the frame height",
      s.select(pl.col("a").map_batches(lambda x: x.head(1))).height, 1)
check("A1 TRAP and it does not raise",
      raises(lambda: s.select(pl.col("a").map_batches(lambda x: x.head(1)))), None)

# A2 — the library grades your work
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    s.select(pl.col("a").map_elements(lambda v: v + 1, return_dtype=pl.Int64))
check("A2 emits PolarsInefficientMapWarning",
      any(w.category.__name__ == "PolarsInefficientMapWarning" for w in caught), True)
check("A2 and prints the native rewrite",
      any('pl.col("a") + 1' in str(w.message) for w in caught), True)

# A3 — return_dtype
check("A3 dtype inferred when omitted",
      s.select(pl.col("a").map_elements(lambda v: v + 1)).dtypes, [pl.Int64])
check("A3 a declared dtype the value contradicts raises",
      raises(lambda: s.select(pl.col("a").map_elements(lambda v: str(v), return_dtype=pl.Int64))),
      "SchemaError")

# A4 — does a UDF blind projection pushdown?
wide = pl.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3], "c": [1, 2, 3]})
native_plan = wide.lazy().select((pl.col("a") + 1).alias("z")).explain()
udf_plan = wide.lazy().select(
    pl.col("a").map_elements(lambda v: v + 1, return_dtype=pl.Int64).alias("z")).explain()
check("A4 native selection reads one column of three", "1/3 COLUMNS" in native_plan, True)
check("A4 the UDF version still reads one column",
      "1/3 COLUMNS" in udf_plan, True)
# ...but the expression itself is opaque: the plan shows a python function node
check("A4 while the expression is opaque in the plan",
      "python_udf" in udf_plan or "map" in udf_plan.lower(), True)

# B1 — the five native forms
big = pl.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40], "k": ["x", "x", "y", "y"]})
check("B1.2 row-wise apply is a plain expression",
      big.select(pl.col("a") + pl.col("b")).to_series().to_list(), [11, 22, 33, 44])
lookup = {1: "one", 2: "two", 3: "three", 4: "four"}
check("B1.3 dictionary lookup is replace_strict",
      big.select(pl.col("a").replace_strict(lookup)).to_series().to_list(),
      ["one", "two", "three", "four"])
check("B1.5 grouped apply is an over() window",
      big.select((pl.col("a").max() - pl.col("a").min()).over("k")).to_series().to_list(), [1, 1, 1, 1])
check("B1.5 and pandas agrees on the values",
      big.to_pandas().groupby("k")["a"].apply(lambda x: x.max() - x.min()).tolist(), [1, 1])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
