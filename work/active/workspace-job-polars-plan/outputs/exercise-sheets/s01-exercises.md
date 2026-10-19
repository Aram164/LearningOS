# Session 1 · Stage 1 — Backend contract, version lock, and divergence axes

**Exercise sheet.** Every expected result below was executed against
`pandas 3.0.2` / `polars 1.36.0` — the versions Stratum pins in `pyproject.toml`
and resolves in `uv.lock`. If your interpreter reports anything else, stop: the
answer key is a claim about *these* builds and nothing here is transferable
until the versions match.

Run everything with Stratum's interpreter, not a system Python:

```bash
Stratum/.venv/bin/python -c "import pandas,polars;print(pandas.__version__,polars.__version__)"
# must print: 3.0.2 1.36.0
```

Work in a scratch file of your own choosing under `Stratum/` (a `scratch/`
or `tests/` path you pick). Nothing on this sheet edits Stratum's source.

---

## How to use this sheet

Each task has four parts, and skipping the third is what makes practice feel
productive while teaching nothing:

| Part | What it means |
|---|---|
| **Do** | The exact frames, calls, and arguments. No "explore" instructions. |
| **Predict** | Write the answer down *before* running. A prediction you did not record is not a prediction. |
| **Record** | The observation columns this task owes. Values, dtype/schema, cardinality, row order, missing-value behaviour, warnings, and exceptions are **separate columns** — collapsing them into "same/different" is the failure this whole session exists to prevent. |
| **Acceptance** | The checkable condition. When it holds, the task is done. |

The answer key is at the bottom. `check.py` next to this sheet asserts the key
against your environment: run it *after* you attempt, as a check on the sheet
as much as on you.

---

## Fixture F1 — the divergence frame

One frame, built the same way in both libraries, chosen so that four separate
axes fire on eight rows. Type it out; do not copy a variant.

```python
rows = {
    "k": ["a", "a", "b", "b", "c", "c", "d", "d"],   # duplicate keys
    "i": [1, 2, None, 4, 5, 6, 7, 8],                # integers with one missing
    "f": [1.0, float("nan"), 3.0, None, 5.0, 6.0, 7.0, 8.0],  # NaN *and* None
    "s": ["p", "q", None, "s", "t", "u", "v", "w"],  # strings with one missing
}
pdf = pd.DataFrame(rows)
ldf = pl.DataFrame(rows)
```

Column `f` is the important one: it carries a floating-point `NaN` at row 1 and
a missing value at row 3. Whether those are the same thing is the question the
fixture exists to ask.

---

## Task 1 — Constructor inference is not a shared contract

**Do.** Build F1 in both libraries. Print `pdf.dtypes` and `ldf.schema`. Then
print `pdf["i"].tolist()` and `ldf["i"].to_list()`.

**Predict.** For each of the four columns, write the dtype you expect on each
side — eight cells. Then write what you expect the *values* of `i` to be on
each side.

**Record.**

| column | pandas dtype | polars dtype | pandas values of `i` | polars values of `i` |
|---|---|---|---|---|

**Acceptance.** You can state, without looking, which column changed its
*values* — not merely its type — as a consequence of the constructor's dtype
choice, and why that is a storage decision rather than an API difference.

**Trap.** Reading `float64` and `Int64` as "the same numbers, typed
differently". One of the two libraries no longer has the integer 4 in that
column.

---

## Task 2 — `NaN` and null are two things in one library and one thing in the other

**Do.** On column `f` of F1, evaluate all three:

```python
pdf["f"].isna().tolist()
ldf["f"].is_null().to_list()
ldf["f"].is_nan().to_list()
```

**Predict.** Nine booleans: rows 1 and 3 for each of the three calls. Commit to
row 3 of `is_nan()` in particular before you run it.

**Record.**

| row | value written in F1 | `pdf.isna()` | `ldf.is_null()` | `ldf.is_nan()` |
|---|---|---|---|---|
| 1 | `float("nan")` | | | |
| 3 | `None` | | | |

**Acceptance.** You can write the truth table for the three predicates and
explain why one cell is neither `True` nor `False`. Then state the consequence
in one sentence: *what a parity comparison that treats "missing" as one concept
will silently pass.*

**Trap.** Assuming `is_nan()` is total. It is an ordinary expression, so it
propagates missingness like every other expression.

---

## Task 3 — Alignment: make the index observable

Index semantics are invisible until you force them to disagree. Three
sub-cases, in this order:

**3a — equal length, reversed labels.**

```python
a = pd.Series([1, 2, 3], index=[0, 1, 2])
b = pd.Series([10, 20, 30], index=[2, 1, 0])
(a + b).tolist()

pa = pl.Series([1, 2, 3])
pb = pl.Series([30, 20, 10])   # the same *storage* order as b
(pa + pb).to_list()
```

**3b — mismatched length.**

```python
c = pd.Series([1, 2, 3], index=[0, 1, 2])
d = pd.Series([10, 20], index=[1, 2])
c + d

pl.Series([1, 2, 3]) + pl.Series([10, 20])
```

**3c — duplicate labels, unequal multiplicity.**

```python
g = pd.Series([1, 2], index=["x", "x"])
h = pd.Series([10, 20, 30], index=["x", "x", "x"])
g + h            # record the length and the exact order of the result
```

**Predict.** For 3a, whether the two libraries agree. For 3b, the pandas result
including its dtype, and whether Polars returns or raises. For 3c, the output
**length** — one number — before you run it.

**Record.**

| case | pandas result | pandas dtype | polars result | which axis fired |
|---|---|---|---|---|
| 3a | | | | |
| 3b | | | | |
| 3c | | | n/a | |

**Acceptance.** 3a and 3b together let you state the trap in one sentence: the
case where the two libraries *agree* is the dangerous one, because it agrees for
the wrong reason. And you can say what 3c does to an output-size assumption in a
lowering rule.

**Trap.** Concluding from 3a that "alignment does not matter here". It mattered;
it just happened to produce the same answer as position.

---

## Task 4 — Derive the axes before you read them

This task is deliberately ordered before any reading of the axis list.

**Do.** Take three operations — `merge`, `groupby(...).agg(...)`, and `assign` —
and for each, write out every way the two libraries could differ. Do not
consult the axis list, the migration guide, or this sheet's key. Aim for at
least six distinct ways per operation; a way is distinct only if you can name
an observation that would detect it.

Then, and only then, read the eight axes. Produce a two-column reconciliation:

| axis | did I derive it? | the observation that would detect it |
|---|---|---|

**Predict.** Before reconciling, write down how many of the eight you expect to
have found.

**Acceptance.** Every axis you *missed* has a one-line explanation of why your
own derivation did not reach it. The missed ones are the output of this task —
the derived ones you already knew.

**Trap.** Reading the list first and then feeling that you would have derived
it. This task is unrepeatable, so spend it properly.

---

## Task 5 — Fifteen differences, classified, with the classification defended

**Do.** Assemble fifteen concrete API differences between the two libraries
drawn from your own work in Tasks 1–3 and from the migration guide. For each,
fill one row:

| # | pandas call | polars call | classification | detecting observation | axis |
|---|---|---|---|---|---|

Classification is exactly one of **syntax-only**, **semantic**,
**performance-only**, or **unsupported**.

**The rule that makes this exercise worth doing:** a row classified
`syntax-only` requires an executed pair showing identical values, dtypes,
cardinality, row order, and missing-value behaviour. Without that evidence the
row is `semantic` by default, because "looks equivalent" is how a wrong
translation gets shipped.

**Predict.** Before you start, guess how many of your fifteen will survive as
`syntax-only` once you actually run them.

**Acceptance.** Fifteen rows; every `syntax-only` row backed by an executed
comparison; every `semantic` row carrying the observation that reveals it. At
least one row must be a difference you originally believed was cosmetic.

**Trap.** `numeric_only`, `skipna`, `observed`, `as_index`, `sort` — every
pandas keyword with no Polars counterpart looks syntax-only until you ask what
happens when it is not the default.

---

## Task 6 — Backfill (do this after Stage 2 exists)

**Do.** Stage 2 builds the harness. When it exists, return here and commit one
named executable case per divergence recorded in Task 5, plus the truth table
from Task 2 and the length from Task 3c.

**Acceptance.** Every row of your Task 5 table has a harness case ID, and the
harness fails if any of those behaviours changes. A divergence living only in a
note is a divergence you will rediscover.

---

## Answer key

Open after attempting. Executed on `pandas 3.0.2` / `polars 1.36.0`.

### Task 1

| column | pandas | polars |
|---|---|---|
| `k` | `str` | `String` |
| `i` | `float64` | `Int64` |
| `f` | `float64` | `Float64` |
| `s` | `str` | `String` |

`pdf["i"].tolist()` → `[1.0, 2.0, nan, 4.0, 5.0, 6.0, 7.0, 8.0]`
`ldf["i"].to_list()` → `[1, 2, None, 4, 5, 6, 7, 8]`

A NumPy-backed `int64` array has no bit pattern reserved for "missing", so
pandas' constructor promotes the whole column to `float64` and represents the
gap as `NaN`. Polars keeps an `Int64` buffer and marks position 2 invalid in a
separate validity bitmap, so the dtype never moves. The pandas column no longer
contains integers at all. Note also that `k` and `s` are `str`, not `object`:
pandas 3.0 made a dedicated string dtype the default, so a pre-3.0 note claiming
`object` is describing a different library than the one you are targeting.

### Task 2

| row | written | `isna()` | `is_null()` | `is_nan()` |
|---|---|---|---|---|
| 1 | `float("nan")` | `True` | `False` | `True` |
| 3 | `None` | `True` | `True` | `None` |

pandas `isna()` answers one question — "is this the missing sentinel" — and on a
NumPy-backed float column `NaN` *is* that sentinel, so both rows are `True`.
Polars holds two orthogonal facts: the validity bitmap (row 3 invalid) and the
float payload (row 1 is the IEEE NaN value). `is_nan()` is an ordinary
expression over a value that is absent at row 3, so it returns null there — the
third truth value. A comparison layer with one `missing` concept maps
`{NaN, None} → missing` on both sides, and every divergence in this table
disappears from its report while remaining in the data.

### Task 3

| case | pandas | polars |
|---|---|---|
| 3a | `[31, 22, 13]` | `[31, 22, 13]` |
| 3b | `[nan, 12.0, 23.0]`, dtype `float64` | raises `InvalidOperationError`: *cannot do arithmetic operation on series of different lengths: got 3 and 2* |
| 3c | `[11, 21, 31, 12, 22, 32]`, length **6** | n/a — Polars has no labels to duplicate |

3a agrees, and that is the trap: pandas aligned on labels and Polars added by
position, and the fixture was built so the two orderings coincide. Nothing about
3a is evidence of shared semantics.

3b is the same mechanism made visible: pandas takes the *union* of the indexes,
fills the unmatched label with `NaN`, and promotes the result to `float64` —
three separate divergences (cardinality, missing value, dtype) from one
operation that Polars refuses outright.

3c is a cross join. Two `"x"` labels against three `"x"` labels produce 2×3 = 6
rows, ordered right-index-major within each left occurrence. Any lowering rule
that assumes `len(out) == len(left)` is wrong on duplicate keys — which is
exactly the assumption a join implementation makes by default. (`g + h` where
both sides carry two `"x"` labels returns length 2, not 4; equal multiplicity
is the special case, not the rule.)

### Task 5 — the row most people get wrong

`df.sort_values("v")` versus `df.sort("v")` reads syntax-only and is not: on a
column containing a missing value, pandas defaults to `na_position="last"` and
Polars defaults to `nulls_last=False`.

```
pd.Series([2, None, 1]).sort_values()   → [1.0, 2.0, nan]
pl.Series([2, None, 1]).sort()          → [None, 1, 2]
```

The values agree, the row order does not, and a comparison that sorts both sides
before comparing will call this pair equal.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```

`check.py` re-executes every claim in the answer key and exits non-zero on the
first mismatch. It fails loudly if the versions are not `3.0.2` / `1.36.0`,
because a passing run against other builds would prove nothing.
