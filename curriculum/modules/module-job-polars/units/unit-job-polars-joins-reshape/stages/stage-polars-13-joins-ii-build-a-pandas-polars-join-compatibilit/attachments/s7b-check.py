"""Assert the join-compatibility-layer corpus findings."""
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


L = pl.DataFrame({"k": ["a", "a", "b", None], "lv": [1, 2, 3, 4]})
R = pl.DataFrame({"k": ["a", "b", "b", None], "rv": [10, 20, 30, 40]})

# A1 — native forms
check("A1.2 semi is an existence filter", L.join(R, on="k", how="semi").columns, ["k", "lv"])
check("A1.5 differing key names",
      L.join(R.rename({"k": "key"}), left_on="k", right_on="key", how="inner").height, 4)
check("A1.7 validate refuses duplicate right keys",
      raises(lambda: L.join(R, on="k", how="left", validate="m:1")), "ComputeError")
multi = pl.DataFrame({"a": [1, 1], "b": ["x", "y"], "v": [1, 2]})
check("A1.4 join on two columns",
      multi.join(pl.DataFrame({"a": [1], "b": ["x"], "w": [9]}), on=["a", "b"], how="inner").height, 1)

# B2 case 9 — empty frames keep a schema
empty = pl.DataFrame({"k": pl.Series([], dtype=pl.String), "rv": pl.Series([], dtype=pl.Int64)})
joined_empty = L.join(empty, on="k", how="inner")
check("B2.9 empty join has no rows", joined_empty.height, 0)
check("B2.9 but it still has a schema", joined_empty.columns, ["k", "lv", "rv"])
check("B2.9 with the right dtypes", joined_empty.dtypes, [pl.String, pl.Int64, pl.Int64])
check("B2.9 left join against an empty right keeps every left row",
      L.join(empty, on="k", how="left").height, 4)

# B2 case 10 — the supertype rule reaches the join key
i64 = pl.DataFrame({"k": pl.Series([1], dtype=pl.Int64), "v": [1]})
u64 = pl.DataFrame({"k": pl.Series([1], dtype=pl.UInt64), "w": [2]})
check("B2.10 an Int64/UInt64 key join is accepted", i64.join(u64, on="k", how="inner").height, 1)
check("B2.10 and Float64 cannot separate 2^53 from 2^53+1",
      float(2 ** 53) == float(2 ** 53 + 1), True)

# B2 case 11 — incompatible key dtypes
s_key = pl.DataFrame({"k": ["1"], "w": [2]})
check("B2.11 Int64 against String key is refused",
      raises(lambda: i64.join(s_key, on="k", how="inner")), "SchemaError")

# B2 case 4 — overlapping non-key columns
ov_l = pl.DataFrame({"k": ["a"], "v": [1]})
ov_r = pl.DataFrame({"k": ["a"], "v": [9]})
check("B2.4 polars renames only the right", ov_l.join(ov_r, on="k").columns, ["k", "v", "v_right"])
check("B2.4 pandas renames both",
      ov_l.to_pandas().merge(ov_r.to_pandas(), on="k").columns.tolist(), ["k", "v_x", "v_y"])

# B3 — which kinds preserve the left frame's order
check("B3 semi preserves left order", L.join(R, on="k", how="semi")["lv"].to_list(), [1, 2, 3])
check("B3 anti preserves left order", L.join(R, on="k", how="anti")["lv"].to_list(), [4])
check("B3 cross has a defined nesting order",
      pl.DataFrame({"a": [1, 2]}).join(pl.DataFrame({"b": [10, 20]}), how="cross").to_dict(as_series=False),
      {"a": [1, 1, 2, 2], "b": [10, 20, 10, 20]})
# maintain_order is the explicit request; it exists because the default is not a promise
check("B3 maintain_order='left' is available on join",
      L.join(R, on="k", how="inner", maintain_order="left")["lv"].to_list(), [1, 2, 3, 3])

# B4 — a supplied suffix that itself collides
coll_l = pl.DataFrame({"k": ["a"], "v": [1], "v_r": [7]})
coll_r = pl.DataFrame({"k": ["a"], "v": [9]})
check("B4 a colliding suffix produces a duplicate-name error",
      raises(lambda: coll_l.join(coll_r, on="k", suffix="_r")), "DuplicateError")
check("B4 pandas raises on the same collision",
      raises(lambda: coll_l.to_pandas().merge(coll_r.to_pandas(), on="k", suffixes=("", "_r"))),
      "MergeError")

# C1 — indicator has no Polars analogue; this is what you would have to build
ind = (L.join(R, on="k", how="full", coalesce=True)
        .with_columns(_merge=pl.when(pl.col("lv").is_not_null() & pl.col("rv").is_not_null())
                                .then(pl.lit("both"))
                                .when(pl.col("lv").is_not_null()).then(pl.lit("left_only"))
                                .otherwise(pl.lit("right_only"))))
check("C1 an indicator column is expressible, not built in",
      sorted(set(ind["_merge"].to_list())), ["both", "left_only", "right_only"])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
