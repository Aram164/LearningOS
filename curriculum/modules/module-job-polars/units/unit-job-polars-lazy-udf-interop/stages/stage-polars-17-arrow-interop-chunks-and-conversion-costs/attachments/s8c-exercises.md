# Session 8 · Stage 3 — Arrow interop, chunks, and conversion costs

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0` /
`pyarrow`.

"Zero-copy" is a claim about specific dtypes under specific conditions. This
stage replaces the claim with measurements, and finds the conversion that
silently changes your schema.

---

## Fixture F9 — one column per interesting representation

```python
d = pl.DataFrame({
    "n":  pl.Series([1, 2, None], dtype=pl.Int64),
    "s":  ["a", None, "c"],
    "c":  pl.Series(["x", "y", "x"], dtype=pl.Categorical),
    "l":  [[1, 2], [3], []],
    "st": [{"a": 1}, {"a": 2}, {"a": 3}],
})
```

Int64-with-null, String-with-null, Categorical, List, Struct — the five that
behave differently at a boundary.

---

# Part A — Polars on its own terms

## Task A1 — What a Polars frame actually is, in Arrow terms

**Do.** `[str(f.type) for f in d.to_arrow().schema]`.

**Predict.** The Arrow type of each of the five columns. Guess the string one in
particular.

**Acceptance.** Five Arrow types recorded. You can say what `large_string` and
`large_list` mean and why Polars uses them, and you can read the Categorical's
Arrow type well enough to name its index width.

**Why it matters.** A Polars frame *is* Arrow data. Once you can read the Arrow
schema, "conversion cost" becomes a question you can answer per column rather
than per frame.

## Task A2 — Chunks survive the boundary

**Do.**

```python
three = pl.concat([pl.DataFrame({"a": [1]})] * 3)
three.n_chunks()
three.to_arrow()["a"].num_chunks
```

**Acceptance.** You can state the relationship, and say what that implies about
`rechunk()` before an export.

## Task A3 — Measure, do not assume

**Do.** On a one-million-row single-column frame, time `to_arrow()`,
`to_numpy()`, `to_pandas()`, and `to_pandas(use_pyarrow_extension_array=True)`.

**Record.** Four timings, and the ratio of the slowest to the fastest.

**Acceptance.** Numbers, from your machine. You can rank the four and explain
the ranking from what each has to build — not from what you expected.

## Task A4 — Prove zero-copy rather than asserting it

Polars gives you a switch that turns the claim into a test.

**Do.**

```python
pl.Series("x", [1, 2, 3]).to_numpy(allow_copy=False)
pl.Series("x", [1, None, 3]).to_numpy(allow_copy=False)
```

**Predict.** Which raises.

**Acceptance.** You can state the exact condition under which an Int64 column
converts to NumPy without copying, and what a single null does to it. Then use
`allow_copy=False` as the assertion in your own interop tests — it is the only
honest way to test a zero-copy claim.

---

# Part B — The pandas contract

## Task B1 — The conversion that changes your schema

**Do.**

```python
d.to_pandas().dtypes
pl.from_pandas(d.to_pandas()).schema == d.schema
d.to_pandas(use_pyarrow_extension_array=True).dtypes
pl.from_pandas(d.to_pandas(use_pyarrow_extension_array=True)).schema == d.schema
```

**Predict.** Both round-trip results, and the dtype of `n` after the default
`to_pandas()`.

**Record.**

| column | polars | to_pandas() default | to_pandas(pyarrow) |
|---|---|---|---|

**Acceptance.** Recorded as a harness case, class **semantic**. You can name the
three columns the default conversion degrades and say why each one degrades.

**Trap.** This is the stage's headline. `n` is `Int64` with one null, and the
default `to_pandas()` returns **`float64`** — the Session 1 promotion, arriving
through a conversion rather than a constructor. `l` and `st` become `object`,
which is not a type so much as the absence of one. The default round trip does
**not** preserve the schema; the pyarrow-backed one does.

## Task B2 — Where a backend boundary costs you

**Do.** Find three places in the read-only Stratum checkout where a
pandas↔Polars conversion happens. For each: which direction, which dtypes cross,
and whether the default or the pyarrow-backed path is used.

**Acceptance.** Three locations with a one-line assessment each. At least one
should be assessed as *"this is where a schema could silently degrade"* or
explicitly cleared. Read only — do not edit Stratum.

## Task B3 — Separate compute from conversion

**Do.** Design a microbenchmark where the *same* operation is timed (a) entirely
within Polars, (b) within Polars but with a pandas frame converted in, and (c)
within Polars with the result converted back out.

**Acceptance.** Three numbers that let you attribute time to compute versus
boundary crossing. You can state the frame size at which the conversion stops
mattering, for your machine — which is the number that should decide whether a
fallback is acceptable.

**Trap.** Timing a conversion once. These operations are fast enough that
interpreter warm-up and allocator behaviour dominate a single run; use repeated
timing and report a median.

---

# Part C — The lowering decision

## Task C1 — The boundary map

**Do.** Draw where data crosses between representations in a Stratum query, and
annotate each crossing with: direction, dtypes at risk, measured cost, and
whether it is avoidable.

**Acceptance.** Every crossing has a measured cost, not an estimate. Crossings
that exist only because of a UDF fallback (previous stage) are marked as such,
which is what connects the two stages: a fallback's real price is a boundary
crossing plus the optimizer passes it disabled, not the Python loop.

---

## Answer key

### Task A1

| column | polars | arrow |
|---|---|---|
| `n` | `Int64` | `int64` |
| `s` | `String` | `large_string` |
| `c` | `Categorical` | `dictionary<values=large_string, indices=uint32, ordered=0>` |
| `l` | `List(Int64)` | `large_list<item: int64>` |
| `st` | `Struct({'a': Int64})` | `struct<a: int64>` |

`large_string` and `large_list` use 64-bit offsets rather than 32-bit, so a
single column can exceed 2 GB. Polars uses them throughout. Note the
Categorical's index width — `uint32` — and compare it with what a pandas
`category` produces after conversion.

`pl.from_arrow(d.to_arrow())` reproduces the schema exactly.

### Task A2

`n_chunks()` → 3, and `to_arrow()["a"].num_chunks` → 3. Chunking is preserved
across the Arrow boundary, so a fragmented frame exports as a fragmented
`ChunkedArray`. If the consumer wants one contiguous buffer, `rechunk()` before
exporting — and pay that cost knowingly rather than having the consumer pay it
invisibly.

### Task A3 — measured on 1e6 rows

| conversion | time |
|---|---|
| `to_arrow()` | ~0.1 ms |
| `to_numpy()` | ~0.1 ms |
| `to_pandas(use_pyarrow_extension_array=True)` | ~0.1 ms |
| `to_pandas()` (default) | ~0.9 ms |

Your numbers will differ; the *ranking* is the finding. The default
`to_pandas()` is the outlier because it is the only one that has to build a
different representation — NumPy-backed columns with a pandas index — rather than
hand over buffers.

### Task A4

```
pl.Series("x", [1, 2, 3]).to_numpy(allow_copy=False)      → works
pl.Series("x", [1, None, 3]).to_numpy(allow_copy=False)   → RuntimeError:
    copy not allowed: cannot convert to a NumPy array without copying data
```

And without the guard, `pl.Series([1, None, 3]).to_numpy()` returns dtype
**`float64`** — the null forced a promotion, silently, because NumPy has no
integer representation for missing.

So: an Int64 column converts to NumPy without copying **only when it contains no
nulls**. `allow_copy=False` turns that from a claim into an assertion, and it
belongs in any test that says "this path is zero-copy".

### Task B1

| column | polars | `to_pandas()` | `to_pandas(pyarrow)` |
|---|---|---|---|
| `n` | `Int64` | **`float64`** | `int64[pyarrow]` |
| `s` | `String` | `str` | `large_string[pyarrow]` |
| `c` | `Categorical` | `category` | `dictionary<… indices=int64 …>[pyarrow]` |
| `l` | `List(Int64)` | **`object`** | `large_list<item: int64>[pyarrow]` |
| `st` | `Struct` | **`object`** | `struct<a: int64>[pyarrow]` |

```
pl.from_pandas(d.to_pandas()).schema == d.schema                       → False
pl.from_pandas(d.to_pandas(use_pyarrow_extension_array=True)).schema   → True
```

Three degradations: the integer column loses its type to a null, and the two
nested columns become `object` — Python objects in a NumPy array, which is the
worst available representation and the one most likely to be slow later.

Note also that the Categorical's index width changes from `uint32` to `int64`
through the pandas boundary. Even the round trip that "works" is not byte-identical.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
