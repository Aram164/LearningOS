# Session 1 — Polars on its own terms

**Companion drill set.** Verified against `polars 1.36.0`.

Session 1's two stages are about the *contract*: pinning versions, naming
divergence axes, building the parity harness. That framing is correct for the
job, and on its own it teaches Polars only as "the thing that is not pandas."
This sheet is the other half. **Nothing here references pandas.** If you find
yourself reaching for a translation, that is the signal to slow down.

Run everything with `Stratum/.venv/bin/python`.

---

## Drill 1 — Build a frame the way Polars wants one built

**Do.** Construct the same three-column frame five ways:

```python
pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})                      # from a dict
pl.DataFrame({"a": [1, 2]}, schema={"a": pl.Int32})               # declared schema
pl.DataFrame({"a": [1, 2], "b": ["x","y"]}, schema_overrides={"a": pl.UInt8})
pl.DataFrame([(1, "x"), (2, "y")], schema=["a", "b"], orient="row")
pl.DataFrame([pl.Series("a", [1, 2]), pl.Series("b", ["x", "y"])])
```

**Record.** The resulting schema of each, and which of the five let you state
the dtype without stating the data.

**Acceptance.** You can name the parameter that declares a full schema and the
one that adjusts a single column, and you can say why `orient` exists at all —
which is a question about ambiguity in the input, not about preference.

**Why it matters.** A frame whose dtypes you declared is a frame whose behaviour
you can predict. Inference is a convenience for exploration; a backend that
relies on it has outsourced its type contract to a heuristic.

## Drill 2 — Read a frame's physical shape, not just its values

**Do.**

```python
df = pl.DataFrame({"a": list(range(1000))})
df.estimated_size("kb")
df.schema
df.describe()
print(df.glimpse(return_type="string"))

two = pl.concat([pl.DataFrame({"a": [1]}), pl.DataFrame({"a": [2]})])
two.n_chunks()
two.rechunk().n_chunks()
```

**Predict.** `two.n_chunks()` before running.

**Acceptance.** You can say what a chunk is, why concatenation produces more than
one, and what `rechunk` costs. You do not need the full memory model yet —
Session 8 owns that — but you should leave this drill knowing that a Polars frame
has a *physical* representation you can inspect, and that two frames with equal
values can differ in it.

**Why it matters.** This is the first appearance of the idea that makes Polars
fast: the frame is a set of contiguous typed buffers, not a collection of rows.
Almost every performance question later reduces to it.

## Drill 3 — Learn the API by its namespaces, not by its functions

The Polars API is large and extremely regular. Memorizing calls is the slow
path; memorizing the *shape* is the fast one.

**Do.** For each namespace, list what lives there and name three operations you
would expect to find before you look:

```python
[m for m in dir(pl.col("x").str)    if not m.startswith("_")]
[m for m in dir(pl.col("x").dt)     if not m.startswith("_")]
[m for m in dir(pl.col("x").list)   if not m.startswith("_")]
[m for m in dir(pl.col("x").struct) if not m.startswith("_")]
[m for m in dir(pl.col("x").name)   if not m.startswith("_")]
[m for m in dir(pl.col("x").meta)   if not m.startswith("_")]
```

**Record.** For each namespace: how many members, and the *category* of thing it
holds.

**Acceptance.** Given an unfamiliar task — "extract the third capture group of a
regex", "get the last day of the month", "rename every field of a struct" — you
can name the namespace before searching. That is the fluency this drill buys:
not knowing the call, but knowing where it lives.

**Notice.** `struct` has five members and `name` has ten. Two of `name`'s are
`prefix_fields` and `suffix_fields` — renaming *inside* a struct. You have not
met structs yet; the API is telling you they exist and are first-class.

## Drill 4 — An expression is a value. Use it like one.

**Do.**

```python
total = pl.col("a").sum()

pl.DataFrame({"a": [1, 2]}).select(total)      # 3
pl.DataFrame({"a": [5, 5]}).select(total)      # 10

stats = {"sum": pl.col("a").sum(), "max": pl.col("a").max()}
df.select(**stats)

df.select([pl.col(c).alias(f"{c}_x") for c in df.columns])
```

Then build one programmatically: write `zscore(col)` returning an expression, and
apply it to three different columns of three different frames.

**Acceptance.** You have an expression stored in a variable, reused across two
frames, and one built by a function. You can state what this makes possible that
a method-call API does not — and you can connect it to `meta.root_names()` from
Session 2: an expression can be *inspected* because it is data.

**Why it matters.** This is the single deepest idea in the library, and it is
easy to use Polars for months without noticing it. Every later capability —
selectors, `over`, lazy optimization, the meta namespace — is a consequence of
expressions being values.

## Drill 5 — Predict, then check, without running

**Do.** For five expression chains of your own, use `collect_schema()` on a
LazyFrame to get the output schema, and predict it first.

**Acceptance.** Five predictions, five checks, and a note on any you got wrong.
The habit being built: *ask the plan, not the data*.

---

## Answer key

**Drill 1.** `schema=` declares the full schema; `schema_overrides=` adjusts named
columns and infers the rest. `orient` exists because a list of tuples is
ambiguous — `[(1, "x"), (2, "y")]` could be two rows of two columns or two
columns of two values, and Polars refuses to guess when it cannot tell.

**Drill 2.** `two.n_chunks()` → `2`. Concatenation does not copy data; it appends
buffers, so the frame is two chunks that behave as one. `rechunk()` → `1`,
copying into a single contiguous buffer. That copy is why it is a separate call
rather than automatic: it costs memory and time, and it pays off only when the
frame will be scanned many times afterwards.

**Drill 3.**

| namespace | holds | count in 1.36.0 |
|---|---|---|
| `.str` | string operations — regex, encoding, slicing, parsing | ~60 |
| `.dt` | temporal components, offsets, time zones, truncation | ~50 |
| `.list` | operations over a List column's elements, including `eval` | ~40 |
| `.struct` | `field`, `rename_fields`, `unnest`, `with_fields`, `json_encode` | 5 |
| `.name` | renaming, including inside structs | 10 |
| `.meta` | inspecting the expression itself | 15 |

`.meta` is the odd one out and the one worth knowing: it does not operate on
data at all. `root_names`, `output_name`, `tree_format`, `has_multiple_outputs`,
`is_literal` — these read the expression as a structure. A library that ships a
namespace for introspecting its own expressions is telling you that expressions
are the primary object.

**Drill 4.** `total` evaluated against two frames gives `3` and `10`. The
expression holds no data and no frame reference; it is a description applied
where it is placed. This is why a function can return one, a dict can hold one,
and a list comprehension can build a hundred.

---

## Where this goes next

Session 2 makes expressions the working language. Session 8 returns to Drill 2's
chunks with the full engine model. If you only take one thing from this sheet,
take Drill 4.
