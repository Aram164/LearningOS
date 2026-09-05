# Session 4 · Stage 1 — Construction, I/O, schema, and chunks

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

A schema is a contract. This stage is about who writes it — you, or an inference
heuristic reading the first N rows of a file.

---

# Part A — Polars on its own terms

## Task A1 — Declare, don't infer

**Do.** Build the same frame six ways and record the resulting schema:

```python
pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
pl.DataFrame({"a": [1, 2], "b": ["x", "y"]}, schema={"a": pl.Int32, "b": pl.String})
pl.DataFrame({"a": [1, 2], "b": ["x", "y"]}, schema_overrides={"a": pl.UInt8})
pl.DataFrame([(1, "x"), (2, "y")], schema=["a", "b"], orient="row")
pl.DataFrame({"a": [1, 2]}, schema={"a": pl.Float64})          # coercion on construction
pl.DataFrame({"a": [1, "x"]})                                  # mixed, no schema
```

**Predict.** Which one raises, and which one silently changes the values you
handed it.

**Acceptance.** You can state the three ways a schema gets decided — declared in
full, adjusted per column, or inferred — and you can name the one input where
Polars refuses to guess rather than picking something. Then write the rule you
will follow in Stratum: where does the schema come from at the operation
boundary?

**Trap.** `schema={"a": pl.Float64}` on integer input does not fail; it casts.
Declaring a schema is therefore also a *cast instruction*, and a wrong
declaration converts data rather than rejecting it.

## Task A2 — Lazy scans and the schema you get before reading

**Do.**

```python
lf = pl.scan_csv("some.csv")
lf.collect_schema()          # schema without reading the data
lf.explain()
pl.read_csv("some.csv").schema
```

**Acceptance.** You can say what `scan_*` gives you that `read_*` does not, and
you can point at the plan line that shows the scan being narrowed by a later
`select`. Connect this to Session 3's projection pushdown: with `read_csv` the
file is already in memory before any pushdown can help.

**Why it matters.** `scan_` + lazy is the idiomatic Polars entry point. A
pipeline that starts with `read_csv` has thrown away the optimizer's best
opportunity before the first expression is written.

## Task A3 — Chunks

**Do.**

```python
two = pl.concat([pl.DataFrame({"a": [1]}), pl.DataFrame({"a": [2]})])
two.n_chunks()
two.rechunk().n_chunks()
two.estimated_size("b")
```

Then build a frame by appending in a loop 100 times and measure `n_chunks()` and
the time of a subsequent `sum()` before and after `rechunk()`.

**Acceptance.** A measurement, not an opinion. You can say when `rechunk` pays
for itself and when it is wasted, and you can name the anti-pattern the loop
demonstrates.

---

# Part B — The pandas contract

## Task B1 — CSV inference is not the same heuristic

**Do.** On the same three files:

```python
a,b,c
1,x,2026-01-01
2,y,2026-01-02
```

```python
pl.read_csv(csv).schema
pl.read_csv(csv, try_parse_dates=True).schema
pd.read_csv(csv).dtypes
```

Then a column that changes type partway down:

```
a
1
2
x
```

And a file with `NA`:

```
a
1
NA
```

**Predict.** Whether the date column is parsed by default on either side, and
what each library does with the `NA`.

**Record.**

| file | pandas | polars | class |
|---|---|---|---|

**Acceptance.** Three rows. You can state each library's default answer to
"is this text a date?" and "is this text missing?", and you can say which of the
two defaults is more dangerous for a backend and why.

**Trap.** The `NA` row. pandas has a built-in list of strings it treats as
missing and applies it without being asked, which also promotes the column to
`float64`. Polars treats `NA` as text unless you pass `null_values`. Same file,
different dtype, different values, no warning on either side.

## Task B2 — Where inference gives up

**Do.** Take the mixed-type file above and add a variant where the type change
happens at row 200, then read it with `infer_schema_length` set to 100 and to
`None`.

**Predict.** With defaults, does Polars read it wrongly, or refuse?

**Acceptance.** You have the answer, and it is not the one most people guess.
Record the setting you would use at the Stratum boundary and the reason, plus
what `ignore_errors=True` does instead and why it is the worse of the two
escapes.

---

# Part C — The lowering decision

## Task C1 — The schema contract at the boundary

**Do.** Write down, as a decision record:

1. Does an operation receive its input schema, or infer it?
2. When a captured pandas call produced a frame by inference, is that schema part
   of the contract or an implementation detail?
3. What happens when the schema Stratum expects and the schema Polars produces
   disagree — raise, cast, or record a divergence?

**Acceptance.** Three answers, each with the case from Part A or B that
motivated it.

---

## Answer key

### Task A1

| construction | schema | note |
|---|---|---|
| inferred | `{a: Int64, b: String}` | |
| `schema=` | `{a: Int32, b: String}` | declared in full |
| `schema_overrides=` | `{a: UInt8, b: String}` | one column adjusted, rest inferred |
| `orient="row"` | `{a: Int64, b: String}` | |
| `schema={"a": Float64}` on ints | `{a: Float64}` | **cast, not rejected** |
| `{"a": [1, "x"]}` | raises `TypeError` | refuses to guess; `strict=False` coerces to String |

### Task B1

| file | pandas | polars |
|---|---|---|
| dates | `c` is `str` | `c` is `String`; `try_parse_dates=True` gives `Date` |
| mixed `1,2,x` | `a` is `str` | `a` is `String` — both widen to text |
| `NA` | `a` is `float64`, values `[1.0, nan]` | `a` is `String`, values `["1", "NA"]` |

Neither library parses dates by default, which is the safe choice and worth
knowing because it is the opposite of what people expect.

### Task B2 — the late type change

A file whose column turns from integers to text at row 201, with default
settings:

| | result |
|---|---|
| `pd.read_csv` | succeeds; dtype `str`; pandas read the whole file |
| `pl.read_csv` | **raises** `ComputeError`: *could not parse `x` as dtype `i64`* |
| `pl.scan_csv(...).collect()` | raises the same |
| `pl.read_csv(infer_schema_length=None)` | `String` |
| `pl.read_csv(ignore_errors=True)` | `Int64`, and the offending row becomes **null** |

This is the opposite of the usual direction. Polars' inference window is 100 rows
by default, and rather than mis-typing the column it *fails loudly* with an error
that lists the four ways out. pandas quietly reads the whole file, which is
correct here and gets slower as files grow — the two libraries made different
trades between speed and surprise, and neither is wrong.

The row worth arguing about is the last one. `ignore_errors=True` makes the read
succeed by turning unparseable values into nulls — it converts a schema error
into missing data, silently, and every downstream null-policy decision you made
in Session 2 now applies to values that were never missing. Prefer
`infer_schema_length=None` or an explicit `schema_overrides` at the boundary.

The `NA` row is the finding. pandas applies a default missing-string list
(`NA`, `N/A`, `null`, `NaN`, and a dozen more) and, having created a missing
value in an integer column, promotes to `float64`. Polars applies no such list:
`NA` is the two-character string `"NA"`, and the column is text. One file, two
dtypes, two value sets, no diagnostic from either. For a backend this is the more
dangerous default in pandas' direction — it invents missingness from data — but
the practical hazard is that a round trip through the two libraries does not
return the frame you started with.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
