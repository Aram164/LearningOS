"""Assert the concatenation / reshaping answer key."""
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


X = pl.DataFrame({"a": [1], "b": [2]})
Y = pl.DataFrame({"b": [3], "c": [4]})

# A1 / B1 — the concat modes and the flipped default
check("A1 vertical refuses mismatched names",
      raises(lambda: pl.concat([X, Y], how="vertical")), "ShapeError")
check("A1 diagonal unions the columns",
      pl.concat([X, Y], how="diagonal").to_dict(as_series=False),
      {"a": [1, None], "b": [2, 3], "c": [None, 4]})
check("B1 pandas concat is the diagonal behaviour",
      pd.concat([X.to_pandas(), Y.to_pandas()]).shape, (2, 3))
check("A1 align joins on the common column",
      pl.concat([pl.DataFrame({"k": [1, 2], "a": [1, 2]}),
                 pl.DataFrame({"k": [2, 3], "b": [9, 9]})], how="align").to_dict(as_series=False),
      {"k": [1, 2, 3], "a": [1, 2, None], "b": [None, 9, 9]})

# B2 — dtype mismatch
i_f = [pl.DataFrame({"a": [1]}), pl.DataFrame({"a": [1.5]})]
check("B2 vertical refuses a dtype mismatch",
      raises(lambda: pl.concat(i_f, how="vertical")), "SchemaError")
check("B2 vertical_relaxed applies the supertype rule",
      pl.concat(i_f, how="vertical_relaxed").dtypes, [pl.Float64])
check("B2 pandas promotes silently",
      str(pd.concat([pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [1.5]})])["a"].dtype), "float64")

# B3 — horizontal padding (changes in 2.0)
check("B3 horizontal pads by position in 1.36",
      pl.concat([pl.DataFrame({"a": [1]}), pl.DataFrame({"b": [1, 2]})], how="horizontal")
        .to_dict(as_series=False), {"a": [1, None], "b": [1, 2]})
check("B3 pandas axis=1 aligns by label",
      pd.concat([pd.DataFrame({"a": [1, 2]}, index=[0, 1]),
                 pd.DataFrame({"b": [9]}, index=[1])], axis=1).shape, (2, 2))

# A2 / B4 — reshaping
W = pl.DataFrame({"i": ["x", "x", "y"], "c": ["p", "q", "p"], "v": [1, 2, 3]})
check("A2.1 pivot long to wide",
      W.pivot(on="c", index="i", values="v").to_dict(as_series=False),
      {"i": ["x", "y"], "p": [1, 3], "q": [2, None]})
dup = pl.DataFrame({"i": ["x", "x"], "c": ["p", "p"], "v": [1, 2]})
check("B4 pivot on repeated pairs needs an aggregate",
      raises(lambda: dup.pivot(on="c", index="i", values="v")), "ComputeError")
check("B4 with one it aggregates",
      dup.pivot(on="c", index="i", values="v", aggregate_function="sum").to_dict(as_series=False),
      {"i": ["x"], "p": [3]})
check("A2.5 explode a list column", pl.DataFrame({"a": [[1, 2], [3]]}).explode("a").height, 3)
check("A2.6 unnest a struct column",
      pl.DataFrame({"a": [1], "b": [2]}).select(pl.struct("a", "b").alias("s")).unnest("s").columns, ["a", "b"])
check("A2.8 partition_by returns one frame per key",
      sorted(pl.DataFrame({"k": ["x", "y", "x"], "v": [1, 2, 3]})
               .partition_by("k", as_dict=True).keys()), [("x",), ("y",)])

# A3 — pivot is a lazy boundary
check("A3 LazyFrame.pivot exists but needs the output columns declared",
      raises(lambda: W.lazy().pivot(on="c", index="i", values="v")), "TypeError")

# C1 — the deprecation, pinned
import warnings  # noqa: E402
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    W.melt(id_vars="i", value_vars="v")
check("C1 melt is deprecated in 1.36", any(w.category is DeprecationWarning for w in caught), True)
check("C1 and the warning names unpivot",
      any("unpivot" in str(w.message) for w in caught), True)

# C3 — the behaviour to pin, asserted by CONTENT rather than by column name
U = pl.DataFrame({"i": ["x", "y"], "p": [1, 3], "q": [2, 4]})
default = U.unpivot(index="i")
check("C3 default names are variable/value", default.columns, ["i", "variable", "value"])
check("C3 and the default column contents are as expected",
      default["variable"].to_list(), ["p", "p", "q", "q"])
custom = U.unpivot(index="i", variable_name="var", value_name="val")
check("C3 custom naming produces this column order", custom.columns, ["i", "val", "var"])
check("C3 the column NAMED 'val' holds the variable names", custom["val"].to_list(), ["p", "p", "q", "q"])
check("C3 the column NAMED 'var' holds the values", custom["var"].to_list(), [1, 3, 2, 4])
check("C3 pandas melt attaches the names the other way",
      U.to_pandas().melt(id_vars="i", var_name="var", value_name="val")["var"].tolist(),
      ["p", "p", "q", "q"])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
