"""Assert the HEAD / TAIL / SAMPLE answer key.

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


def raises(fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__
    return None


df = pl.DataFrame({"k": ["a", "b", "a", "c", "b"], "v": [1, 2, 1, 3, 2], "w": [10, 20, 30, 40, 50]})
pdf = df.to_pandas()

# Part B1 — head/tail agree on every edge, which is itself the finding
for n, want in [(2, [10, 20]), (-1, [10, 20, 30, 40])]:
    check(f"B1 head({n}) pandas", pdf.head(n)["w"].tolist(), want)
    check(f"B1 head({n}) polars", df.head(n)["w"].to_list(), want)
check("B1 head(0) pandas", pdf.head(0).shape, (0, 3))
check("B1 head(0) polars", df.head(0).shape, (0, 3))
check("B1 head(99) pandas", pdf.head(99).shape, (5, 3))
check("B1 head(99) polars", df.head(99).shape, (5, 3))
check("B1 tail(-1) pandas", pdf.tail(-1)["w"].tolist(), [20, 30, 40, 50])
check("B1 tail(-1) polars", df.tail(-1)["w"].to_list(), [20, 30, 40, 50])
check("B1 head(None) escapes a Python TypeError", raises(lambda: df.head(None)), "TypeError")

# Part B2 — SAMPLE, and the divergence a spot check misses
check("B2.2 pandas sample(frac=1) permutes",
      pdf.sample(frac=1, random_state=0)["w"].tolist() != [10, 20, 30, 40, 50], True)
check("B2.2 polars sample(fraction=1.0) does NOT reorder",
      df.sample(fraction=1.0, seed=0)["w"].to_list(), [10, 20, 30, 40, 50])
check("B2.3 shuffle=True is the opt-in",
      df.sample(n=5, seed=0, shuffle=True)["w"].to_list() != [10, 20, 30, 40, 50], True)
check("B2.4 pandas oversample raises ValueError",
      raises(lambda: pdf.sample(n=99, random_state=0)), "ValueError")
check("B2.4 polars oversample raises ShapeError",
      raises(lambda: df.sample(n=99, seed=0)), "ShapeError")
check("B2.5 pandas frac>1 raises ValueError",
      raises(lambda: pdf.sample(frac=1.5, random_state=0)), "ValueError")
check("B2.5 polars fraction>1 raises ShapeError too",
      raises(lambda: df.sample(fraction=1.5, seed=0)), "ShapeError")
check("B2.6 polars has no weights", raises(lambda: df.sample(n=2, seed=0, weights=[1, 1, 1, 1, 5])), "TypeError")

# Part C2 — the randomness contract, stated as properties
check("C2.1 same seed is reproducible",
      df.sample(n=3, seed=7)["w"].to_list(), df.sample(n=3, seed=7)["w"].to_list())
check("C2.3 n gives exactly n rows", df.sample(n=3, seed=0).height, 3)
check("C2.3 fraction rounds to this", df.sample(fraction=0.4, seed=0).height, 2)
check("C2.4 every row came from the input",
      set(df.sample(n=3, seed=0)["w"].to_list()) <= {10, 20, 30, 40, 50}, True)
check("C2.5 without replacement there are no repeats",
      len(set(df.sample(n=5, seed=0)["w"].to_list())), 5)
check("C2.6 with replacement n may exceed height",
      df.sample(n=7, with_replacement=True, seed=0).height, 7)

# Part A — native row-limiting, and the plan
check("A1.6 top_k", sorted(df.top_k(3, by="w")["w"].to_list()), [30, 40, 50])
check("A1.7 head on a GroupBy",
      df.group_by("k", maintain_order=True).head(1)["w"].to_list(), [10, 20, 40])
check("A1.9 gather_every", df.gather_every(2)["w"].to_list(), [10, 30, 50])
check("A2 slice pushdown into sort", "slice: (0, 2)" in df.lazy().sort("v").head(2).explain(), True)
check("A2 head-then-sort is a different query",
      "slice: (0, 2)" in df.lazy().head(2).sort("v").explain(), False)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
