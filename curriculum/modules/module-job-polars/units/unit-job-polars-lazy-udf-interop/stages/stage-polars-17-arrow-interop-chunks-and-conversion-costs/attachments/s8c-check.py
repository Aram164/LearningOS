"""Assert the Arrow-interop / conversion-cost answer key."""
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


d = pl.DataFrame({
    "n": pl.Series([1, 2, None], dtype=pl.Int64),
    "s": ["a", None, "c"],
    "c": pl.Series(["x", "y", "x"], dtype=pl.Categorical),
    "l": [[1, 2], [3], []],
    "st": [{"a": 1}, {"a": 2}, {"a": 3}],
})

# A1 — a Polars frame is Arrow data
arrow_types = [str(f.type) for f in d.to_arrow().schema]
check("A1 int64", arrow_types[0], "int64")
check("A1 strings are large_string (64-bit offsets)", arrow_types[1], "large_string")
check("A1 categorical is a dictionary with uint32 indices",
      "dictionary" in arrow_types[2] and "indices=uint32" in arrow_types[2], True)
check("A1 lists are large_list", arrow_types[3], "large_list<item: int64>")
check("A1 struct", arrow_types[4], "struct<a: int64>")
check("A1 the arrow round trip is exact", pl.from_arrow(d.to_arrow()).schema == d.schema, True)

# A2 — chunks cross the boundary
three = pl.concat([pl.DataFrame({"a": [1]})] * 3)
check("A2 three chunks in polars", three.n_chunks(), 3)
check("A2 and three chunks in arrow", three.to_arrow()["a"].num_chunks, 3)
check("A2 rechunk collapses them", three.rechunk().to_arrow()["a"].num_chunks, 1)

# A4 — zero-copy, as an assertion rather than a claim
check("A4 a null-free Int64 converts without copying",
      pl.Series("x", [1, 2, 3]).to_numpy(allow_copy=False).tolist(), [1, 2, 3])
check("A4 one null makes that impossible",
      raises(lambda: pl.Series("x", [1, None, 3]).to_numpy(allow_copy=False)), "RuntimeError")
check("A4 and the unguarded conversion promotes to float64",
      str(pl.Series("x", [1, None, 3]).to_numpy().dtype), "float64")

# B1 — the conversion that changes your schema
default_dtypes = d.to_pandas().dtypes.astype(str).to_dict()
check("B1 TRAP Int64 with a null becomes float64", default_dtypes["n"], "float64")
check("B1 TRAP a List column becomes object", default_dtypes["l"], "object")
check("B1 TRAP a Struct column becomes object", default_dtypes["st"], "object")
check("B1 the default round trip does NOT preserve the schema",
      pl.from_pandas(d.to_pandas()).schema == d.schema, False)

pa_dtypes = d.to_pandas(use_pyarrow_extension_array=True).dtypes.astype(str).to_dict()
check("B1 pyarrow-backed keeps the integer", pa_dtypes["n"], "int64[pyarrow]")
check("B1 pyarrow-backed keeps the list", pa_dtypes["l"], "large_list<item: int64>[pyarrow]")
check("B1 and that round trip DOES preserve the schema",
      pl.from_pandas(d.to_pandas(use_pyarrow_extension_array=True)).schema == d.schema, True)
check("B1 but the categorical index width still changes",
      "indices=int64" in pa_dtypes["c"], True)

# A3 — the ranking is the finding; assert the ordering, not absolute times
import time  # noqa: E402


def median_ms(fn, n=5):
    times = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t) * 1000)
    return sorted(times)[n // 2]


big = pl.DataFrame({"n": list(range(1_000_000))})
t_arrow = median_ms(big.to_arrow)
t_pandas = median_ms(big.to_pandas)
check("A3 default to_pandas is the slowest of the two", t_pandas > t_arrow, True)
check("A3 and to_arrow is sub-millisecond on 1e6 rows", t_arrow < 1.0, True)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)
