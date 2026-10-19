"""Assert the relational-joins answer key."""
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
pL, pR = L.to_pandas(), R.to_pandas()

# A1 — cardinality
for how, want in [("inner", 4), ("left", 5), ("right", 5), ("full", 6), ("semi", 3), ("anti", 1)]:
    check(f"A1 {how}", L.join(R, on="k", how=how).height, want)
check("A1 cross ignores keys", L.join(R, how="cross").height, 16)

# A2 — the Polars-only kinds are filters, not row combinations
check("A2 semi keeps only the left frame's columns", L.join(R, on="k", how="semi").columns, ["k", "lv"])
check("A2 anti is the complement", L.join(R, on="k", how="anti")["lv"].to_list(), [4])
a = pl.DataFrame({"t": [1, 5, 10], "v": ["a", "b", "c"]}).sort("t")
b = pl.DataFrame({"t": [2, 6], "w": ["x", "y"]}).sort("t")
check("A2 join_asof takes the nearest preceding row",
      b.join_asof(a, on="t", strategy="backward")["v"].to_list(), ["a", "b"])
check("A2 join_where does a non-equi join", a.join_where(b, pl.col("t") > pl.col("t_right")).height, 3)

# A3 — the join is visible in the plan
plan = L.lazy().join(R.lazy(), on="k", how="inner").explain()
check("A3 plan names the join", "INNER JOIN" in plan, True)
check("A3 and both sides' key expressions", "LEFT PLAN ON" in plan and "RIGHT PLAN ON" in plan, True)

# B1 — the null-key divergence
check("B1 polars does not match null keys", L.join(R, on="k", how="inner").height, 4)
check("B1 nulls_equal=True switches it", L.join(R, on="k", how="inner", nulls_equal=True).height, 5)
check("B1 pandas matches them by default", pL.merge(pR, on="k", how="inner").shape[0], 5)
# ...which contradicts pandas' own element-wise comparison, from Session 4:
check("B1 while pandas' comparison says they are NOT equal",
      (pd.Series([None]) == pd.Series([None])).tolist(), [False])

# B2 — suffixes
A = pl.DataFrame({"k": ["a"], "v": [1]})
B = pl.DataFrame({"k": ["a"], "v": [9]})
check("B2 polars suffixes only the right", A.join(B, on="k").columns, ["k", "v", "v_right"])
check("B2 custom suffix", A.join(B, on="k", suffix="_r").columns, ["k", "v", "v_r"])
check("B2 pandas suffixes both",
      A.to_pandas().merge(B.to_pandas(), on="k").columns.tolist(), ["k", "v_x", "v_y"])
check("B2 so 'v' exists on one side and not the other",
      "v" in A.join(B, on="k").columns and "v" not in A.to_pandas().merge(B.to_pandas(), on="k").columns,
      True)

# B3 — the full join that loses keys
A2 = pl.DataFrame({"k": ["a", "b"], "v": [1, 2]})
B2 = pl.DataFrame({"k": ["b", "c"], "w": [3, 4]})
full = A2.join(B2, on="k", how="full")
check("B3 full join keeps TWO key columns", full.columns, ["k", "v", "k_right", "w"])
check("B3 TRAP the k column is missing the right-only key",
      sorted(x for x in full["k"].to_list() if x is not None), ["a", "b"])
check("B3 and 'c' is only in k_right",
      sorted(x for x in full["k_right"].to_list() if x is not None), ["b", "c"])
check("B3 coalesce=True repairs it",
      sorted(A2.join(B2, on="k", how="full", coalesce=True)["k"].to_list()), ["a", "b", "c"])
check("B3 pandas outer coalesces by default",
      sorted(A2.to_pandas().merge(B2.to_pandas(), on="k", how="outer")["k"].tolist()), ["a", "b", "c"])

# B4 — validation
check("B4 polars validate raises ComputeError",
      raises(lambda: L.join(R, on="k", how="inner", validate="1:1")), "ComputeError")
check("B4 pandas validate raises MergeError",
      raises(lambda: pL.merge(pR, on="k", validate="1:1")), "MergeError")
check("B4 m:m is accepted", L.join(R, on="k", how="inner", validate="m:m").height, 4)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
