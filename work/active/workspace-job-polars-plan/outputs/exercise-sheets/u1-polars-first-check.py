"""Assert the Session 1 Polars-first drill key.

    Stratum/.venv/bin/python check.py
"""
import sys

import polars as pl

if pl.__version__ != "1.36.0":
    sys.exit(f"FATAL: key asserts polars 1.36.0; you have {pl.__version__}.")

passed = failed = 0


def check(label, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {label}\n    got  {got!r}\n    want {want!r}")


# Drill 1 — five constructions
check("D1 declared schema", pl.DataFrame({"a": [1, 2]}, schema={"a": pl.Int32}).dtypes, [pl.Int32])
check("D1 schema_overrides adjusts one column",
      pl.DataFrame({"a": [1, 2], "b": ["x", "y"]}, schema_overrides={"a": pl.UInt8}).dtypes,
      [pl.UInt8, pl.String])
check("D1 orient='row' reads tuples as rows",
      pl.DataFrame([(1, "x"), (2, "y")], schema=["a", "b"], orient="row").to_dict(as_series=False),
      {"a": [1, 2], "b": ["x", "y"]})
check("D1 from Series keeps their names",
      pl.DataFrame([pl.Series("a", [1, 2]), pl.Series("b", ["x", "y"])]).columns, ["a", "b"])
check("D1 inference gives Int64 by default", pl.DataFrame({"a": [1, 2]}).dtypes, [pl.Int64])

# Drill 2 — physical shape
two = pl.concat([pl.DataFrame({"a": [1]}), pl.DataFrame({"a": [2]})])
check("D2 concat does not copy: two chunks", two.n_chunks(), 2)
check("D2 rechunk copies into one", two.rechunk().n_chunks(), 1)
check("D2 values are identical either way", two.to_series().to_list(), two.rechunk().to_series().to_list())
check("D2 estimated_size is inspectable", pl.DataFrame({"a": list(range(1000))}).estimated_size("b") > 0, True)
check("D2 describe returns a frame of statistics",
      pl.DataFrame({"a": [1, 2, 3]}).describe().columns, ["statistic", "a"])

# Drill 3 — the namespaces, and their shape
struct_ns = sorted(m for m in dir(pl.col("x").struct) if not m.startswith("_"))
check("D3 struct namespace is small and specific",
      struct_ns, ["field", "json_encode", "rename_fields", "unnest", "with_fields"])
name_ns = sorted(m for m in dir(pl.col("x").name) if not m.startswith("_"))
check("D3 name namespace reaches inside structs",
      "prefix_fields" in name_ns and "suffix_fields" in name_ns, True)
meta_ns = sorted(m for m in dir(pl.col("x").meta) if not m.startswith("_"))
for member in ("root_names", "output_name", "tree_format", "has_multiple_outputs", "is_literal"):
    check(f"D3 meta has {member}", member in meta_ns, True)
check("D3 str namespace is large", len([m for m in dir(pl.col("x").str) if not m.startswith("_")]) > 40, True)

# Drill 4 — an expression is a value
total = pl.col("a").sum()
check("D4 one expression, two frames (i)", pl.DataFrame({"a": [1, 2]}).select(total).item(), 3)
check("D4 one expression, two frames (ii)", pl.DataFrame({"a": [5, 5]}).select(total).item(), 10)
stats = {"sum": pl.col("a").sum(), "max": pl.col("a").max()}
check("D4 expressions stored in a dict",
      pl.DataFrame({"a": [1, 2, 3]}).select(**stats).to_dict(as_series=False), {"sum": [6], "max": [3]})
check("D4 expressions built by comprehension",
      pl.DataFrame({"a": [1], "b": [2]}).select([pl.col(c).alias(f"{c}_x") for c in ("a", "b")]).columns,
      ["a_x", "b_x"])


def zscore(col: str) -> pl.Expr:
    return (pl.col(col) - pl.col(col).mean()) / pl.col(col).std()


check("D4 a function returning an expression",
      isinstance(zscore("a"), pl.Expr), True)
check("D4 and it applies to any frame with that column",
      pl.DataFrame({"a": [1.0, 2.0, 3.0]}).select(zscore("a")).to_series().round(6).to_list(),
      [-1.0, 0.0, 1.0])

# Drill 5 — ask the plan, not the data
check("D5 collect_schema resolves without executing",
      dict(pl.DataFrame({"a": [1]}).lazy().select(pl.col("a").cast(pl.Float64)).collect_schema()),
      {"a": pl.Float64})

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
