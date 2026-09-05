"""Assert every claim in the Stage 1 answer key against the pinned environment.

    Stratum/.venv/bin/python check.py

Exits non-zero on the first mismatch. A pass means the sheet's key describes the
library you are actually running; it says nothing about whether you attempted
the tasks.
"""
import math
import sys

import pandas as pd
import polars as pl

if (pd.__version__, pl.__version__) != ("3.0.2", "1.36.0"):
    sys.exit(
        f"FATAL: this key asserts behaviour of pandas 3.0.2 / polars 1.36.0; you have "
        f"{pd.__version__} / {pl.__version__}. A passing run would prove nothing. "
        f"Use Stratum/.venv/bin/python."
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


ROWS = {
    "k": ["a", "a", "b", "b", "c", "c", "d", "d"],
    "i": [1, 2, None, 4, 5, 6, 7, 8],
    "f": [1.0, float("nan"), 3.0, None, 5.0, 6.0, 7.0, 8.0],
    "s": ["p", "q", None, "s", "t", "u", "v", "w"],
}
pdf = pd.DataFrame(ROWS)
ldf = pl.DataFrame(ROWS)

# --- Task 1: constructor inference -----------------------------------------
check("T1 pandas dtypes", [str(d) for d in pdf.dtypes], ["str", "float64", "float64", "str"])
check("T1 polars schema", [str(t) for t in ldf.schema.values()], ["String", "Int64", "Float64", "String"])
check("T1 polars i values", ldf["i"].to_list(), [1, 2, None, 4, 5, 6, 7, 8])

pandas_i = pdf["i"].tolist()
check("T1 pandas i is float-typed", pdf["i"].dtype.name, "float64")
check("T1 pandas i row 2 is NaN not None", math.isnan(pandas_i[2]), True)
check("T1 pandas i lost integer identity", pandas_i[0] == 1 and isinstance(pandas_i[0], float), True)

# --- Task 2: the three-valued truth table ----------------------------------
isna = pdf["f"].isna().tolist()
is_null = ldf["f"].is_null().to_list()
is_nan = ldf["f"].is_nan().to_list()
check("T2 pandas isna rows 1,3", [isna[1], isna[3]], [True, True])
check("T2 polars is_null rows 1,3", [is_null[1], is_null[3]], [False, True])
check("T2 polars is_nan rows 1,3", [is_nan[1], is_nan[3]], [True, None])

# --- Task 3a: alignment that coincides with position -----------------------
a = pd.Series([1, 2, 3], index=[0, 1, 2])
b = pd.Series([10, 20, 30], index=[2, 1, 0])
check("T3a pandas label-aligned add", (a + b).tolist(), [31, 22, 13])
check("T3a polars positional add", (pl.Series([1, 2, 3]) + pl.Series([30, 20, 10])).to_list(), [31, 22, 13])

# --- Task 3b: mismatched length --------------------------------------------
c = pd.Series([1, 2, 3], index=[0, 1, 2])
d = pd.Series([10, 20], index=[1, 2])
cd = c + d
check("T3b pandas union length", len(cd), 3)
check("T3b pandas row 0 is NaN", math.isnan(cd.iloc[0]), True)
check("T3b pandas tail values", cd.iloc[1:].tolist(), [12.0, 23.0])
check("T3b pandas promoted dtype", cd.dtype.name, "float64")
try:
    pl.Series([1, 2, 3]) + pl.Series([10, 20])
    check("T3b polars raises", "no exception", "InvalidOperationError")
except Exception as exc:  # noqa: BLE001 - the type is the assertion
    check("T3b polars raises", type(exc).__name__, "InvalidOperationError")

# --- Task 3c: duplicate labels cross-join ----------------------------------
g = pd.Series([1, 2], index=["x", "x"])
h = pd.Series([10, 20, 30], index=["x", "x", "x"])
gh = g + h
check("T3c cross-join length", len(gh), 6)
check("T3c cross-join order", gh.tolist(), [11, 21, 31, 12, 22, 32])
equal_mult = pd.Series([1, 2], index=["x", "x"]) + pd.Series([10, 20], index=["x", "x"])
check("T3c equal multiplicity is the special case", equal_mult.tolist(), [11, 22])

# --- Task 5: the sort row --------------------------------------------------
sorted_pd = pd.Series([2, None, 1]).sort_values().tolist()
check("T5 pandas nulls last by default", [sorted_pd[0], sorted_pd[1], math.isnan(sorted_pd[2])], [1.0, 2.0, True])
check("T5 polars nulls first by default", pl.Series([2, None, 1]).sort().to_list(), [None, 1, 2])
check("T5 polars nulls_last=True", pl.Series([2, None, 1]).sort(nulls_last=True).to_list(), [1, 2, None])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
