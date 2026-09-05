"""Assert the construction / IO / schema answer key."""
import io
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


# Task A1 — three ways a schema is decided
check("A1 inferred", pl.DataFrame({"a": [1, 2], "b": ["x", "y"]}).dtypes, [pl.Int64, pl.String])
check("A1 declared in full",
      pl.DataFrame({"a": [1, 2], "b": ["x", "y"]}, schema={"a": pl.Int32, "b": pl.String}).dtypes,
      [pl.Int32, pl.String])
check("A1 adjusted per column",
      pl.DataFrame({"a": [1, 2], "b": ["x", "y"]}, schema_overrides={"a": pl.UInt8}).dtypes,
      [pl.UInt8, pl.String])
check("A1 orient=row", pl.DataFrame([(1, "x"), (2, "y")], schema=["a", "b"], orient="row").dtypes,
      [pl.Int64, pl.String])
# The trap: declaring a schema is also a cast instruction.
check("A1 TRAP declared Float64 casts rather than rejects",
      pl.DataFrame({"a": [1, 2]}, schema={"a": pl.Float64}).to_series().to_list(), [1.0, 2.0])
check("A1 mixed input is refused, not guessed", raises(lambda: pl.DataFrame({"a": [1, "x"]})), "TypeError")
check("A1 strict=False coerces to text",
      pl.Series([1, "x"], strict=False).to_list(), ["1", "x"])

# Task A3 — chunks
two = pl.concat([pl.DataFrame({"a": [1]}), pl.DataFrame({"a": [2]})])
check("A3 concat leaves two chunks", two.n_chunks(), 2)
check("A3 rechunk makes one", two.rechunk().n_chunks(), 1)
check("A3 values unchanged", two.rechunk().to_series().to_list(), [1, 2])

# Task B1 — CSV inference
csv = "a,b,c\n1,x,2026-01-01\n2,y,2026-01-02\n"
check("B1 polars does not parse dates by default",
      [str(t) for t in pl.read_csv(io.StringIO(csv)).dtypes], ["Int64", "String", "String"])
check("B1 try_parse_dates opts in",
      [str(t) for t in pl.read_csv(io.StringIO(csv), try_parse_dates=True).dtypes],
      ["Int64", "String", "Date"])
check("B1 pandas does not either",
      str(pd.read_csv(io.StringIO(csv)).dtypes["c"]), "str")

mixed = "a\n1\n2\nx\n"
check("B1 polars widens a mixed column to text", str(pl.read_csv(io.StringIO(mixed)).dtypes[0]), "String")
check("B1 pandas widens too", str(pd.read_csv(io.StringIO(mixed)).dtypes["a"]), "str")

na = "a\n1\nNA\n"
pd_na = pd.read_csv(io.StringIO(na))["a"]
pl_na = pl.read_csv(io.StringIO(na)).to_series()
check("B1 TRAP pandas invents a missing value from 'NA'", pd_na.isna().tolist(), [False, True])
check("B1 TRAP and promotes the column to float", str(pd_na.dtype), "float64")
check("B1 polars keeps 'NA' as text", pl_na.to_list(), ["1", "NA"])
check("B1 opting in gives pandas' reading",
      pl.read_csv(io.StringIO(na), null_values=["NA"]).to_series().to_list(), [1, None])

# Task B2 — where inference gives up
late = "a\n" + "1\n" * 200 + "x\n"
check("B2 pandas reads the whole file and widens silently",
      str(pd.read_csv(io.StringIO(late)).dtypes["a"]), "str")
check("B2 polars REFUSES with default inference length",
      raises(lambda: pl.read_csv(io.StringIO(late))), "ComputeError")
check("B2 and so does the lazy scan",
      raises(lambda: pl.scan_csv(io.BytesIO(late.encode())).collect()), "ComputeError")
check("B2 infer_schema_length=None resolves it",
      str(pl.read_csv(io.StringIO(late), infer_schema_length=None).dtypes[0]), "String")
check("B2 a large window resolves it too",
      str(pl.read_csv(io.StringIO(late), infer_schema_length=10000).dtypes[0]), "String")
check("B2 ignore_errors nulls the offending row instead",
      pl.read_csv(io.StringIO(late), ignore_errors=True).to_series().to_list()[-1], None)

# Task A2 — scan gives a schema without reading
lf = pl.scan_csv(io.BytesIO(csv.encode()))
check("A2 collect_schema without collecting",
      [str(t) for t in dict(lf.collect_schema()).values()], ["Int64", "String", "String"])

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
