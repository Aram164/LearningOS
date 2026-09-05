"""Assert the selectors-and-expansion answer key.

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


narrow = pl.DataFrame({"a": [1], "s": ["x"]})
wide = pl.DataFrame({"a": [1], "b": [1.5], "c": [2], "s": ["x"], "t": ["y"]})
changed = pl.DataFrame({"a": [1.0], "s": ["x"], "n": [2]})
f2 = pl.DataFrame({"a": [1, 2, 3], "b": [1.5, 2.5, 3.5], "s": ["x", "y", "z"], "d": [None, 1, 2]})

# Task 1 — set algebra
check("T1 numeric", cs.expand_selector(wide, cs.numeric()), ("a", "b", "c"))
check("T1 by_dtype String", cs.expand_selector(wide, cs.by_dtype(pl.String)), ("s", "t"))
check("T1 union", cs.expand_selector(wide, cs.numeric() | cs.string()), ("a", "b", "c", "s", "t"))
check("T1 difference", cs.expand_selector(wide, cs.numeric() - cs.by_name("a")), ("b", "c"))
check("T1 intersection", cs.expand_selector(wide, cs.numeric() & cs.by_name("a", "s")), ("a",))
check("T1 complement", cs.expand_selector(wide, ~cs.numeric()), ("s", "t"))
check("T1 exclude", cs.expand_selector(wide, cs.all().exclude("s")), ("a", "b", "c", "t"))

# Task 1 — the operator-ambiguity trap: `- 1` is arithmetic, not set difference
check("T1 TRAP minus scalar is arithmetic",
      f2.select(cs.numeric() - 1).to_dict(as_series=False),
      {"a": [0, 1, 2], "b": [0.5, 1.5, 2.5], "d": [None, 0, 1]})
check("T1 TRAP it selected, not filtered", f2.select(cs.numeric() - 1).columns, ["a", "b", "d"])

# Task 2 — schema drift
sel = cs.numeric() - cs.by_name("a")
check("T2 narrow expands to nothing", cs.expand_selector(narrow, sel), ())
check("T2 wide expands to two", cs.expand_selector(wide, sel), ("b", "c"))
check("T2 changed: a is Float64 so still excluded by name", cs.expand_selector(changed, sel), ("n",))
check("T2 empty selection in select yields a (0, 0) frame", narrow.select(sel).shape, (0, 0))
check("T2 empty selection in with_columns is a no-op", narrow.with_columns(sel).columns, ["a", "s"])
check("T2 dtype selector follows the schema change",
      cs.expand_selector(changed, cs.numeric()), ("a", "n"))

# Task 3 — strictness
check("T3 by_name strict raises", raises(lambda: wide.select(cs.by_name("zz"))), "ColumnNotFoundError")
check("T3 require_all=False selects nothing", wide.select(cs.by_name("zz", require_all=False)).columns, [])
check("T3 pandas select_dtypes",
      pd.DataFrame({"a": [1], "b": [1.0], "s": ["x"]}).select_dtypes("number").columns.tolist(), ["a", "b"])

# Task 4 — the boolean/categorical class question, answered rather than assumed
mixed = pl.DataFrame({"i": [1], "f": [1.0], "bo": [True], "ca": pl.Series(["x"], dtype=pl.Categorical)})
check("T4 polars numeric excludes Boolean", cs.expand_selector(mixed, cs.numeric()), ("i", "f"))
check("T4 polars numeric excludes Categorical", "ca" in cs.expand_selector(mixed, cs.numeric()), False)
pd_mixed = pd.DataFrame({"i": [1], "f": [1.0], "bo": [True], "ca": pd.Categorical(["x"])})
check("T4 pandas 'number' also excludes bool",
      pd_mixed.select_dtypes("number").columns.tolist(), ["i", "f"])

# The property the stage exists for: a materialized name list does NOT survive drift.
materialized = [n for n, t in wide.schema.items() if t.is_numeric() and n != "a"]
check("T4 TRAP materialized list is stale on a new schema",
      [n for n in materialized if n in changed.columns], [])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
