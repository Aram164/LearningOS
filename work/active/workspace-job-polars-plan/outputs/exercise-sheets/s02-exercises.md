# Session 1 · Stage 2 — Build the cumulative differential parity harness

**Exercise sheet.** Every divergence tabulated below was executed against
`pandas 3.0.2` / `polars 1.36.0`. The twelve seed cases are not illustrative
examples: they are the twelve the harness must classify correctly on day one,
and `check.py` asserts each one still behaves as recorded.

```bash
Stratum/.venv/bin/python -c "import pandas,polars;print(pandas.__version__,polars.__version__)"
# must print: 3.0.2 1.36.0
```

This stage produces the one artifact every later session deposits into. Build it
badly and nine sessions of evidence go into a file that reports `False` and
tells you nothing.

---

## The design constraint, stated once

**A comparison that returns a boolean has thrown away the finding.** When a
pandas call and a Polars call disagree, the useful question is never *whether*
they disagree — it is which of seven independent things differ:

| # | Dimension | Why it is separate |
|---|---|---|
| 1 | **values** | Can match while everything else diverges. |
| 2 | **dtype / schema** | `float64` vs `Int64` on equal values is a real finding (Stage 1, Task 1). |
| 3 | **cardinality** | A cross join and a length-preserving op both "worked". |
| 4 | **row order** | Only meaningful where the operation promises one. |
| 5 | **missing-value representation** | `NaN` vs null vs three-valued (Stage 1, Task 2). |
| 6 | **warnings** | pandas signals deprecations here; Polars mostly does not. |
| 7 | **exceptions** | Type *and* whether one side raised at all. |

Seven fields, reported independently. Every task on this sheet exists to defend
that shape against the pressure to collapse it.

---

## Task 1 — The comparison helper, and the report it returns

**Do.** Write `compare(pandas_fn, polars_fn, case) -> Report` where `Report`
carries the seven fields above as *separate* attributes, plus the case ID. Both
callables take the case's input spec and return a frame, a series, or a scalar.

Required behaviour, each independently testable:

1. If exactly one side raises, that is a finding — not a crash of the harness.
   Record which side, the exception type, and the message.
2. If both raise, record both types. Different exception types on the same
   input is a finding (see seed case 12).
3. Warnings are captured with `warnings.catch_warnings(record=True)` on both
   sides and reported per side. A pandas `FutureWarning` that Polars has no
   analogue for is a finding, not noise.
4. `Report` has no `__bool__`. Make it a `TypeError` to use one in an `if`.
   This is the constraint, expressed as code rather than as discipline.

**Predict.** Before writing it: which of the seven fields will you be tempted to
merge first? Write it down. It is almost always 2 into 1, or 5 into 1.

**Acceptance.** `Report` cannot be reduced to a boolean by accident, one side
raising produces a populated report rather than a traceback, and you can point
at the line that captures warnings on each side.

**Trap.** Reaching for `polars.testing.assert_frame_equal` or
`pandas.testing.assert_frame_equal` as the comparison. Both are *assertions*:
they raise on the first difference and throw away the rest. They belong inside
one field of your report, never as the whole of it.

---

## Task 2 — The null policy, written before it is coded

**Do.** Answer one question in prose, in the file, as a comment block: **is a
pandas `NaN` equal to a Polars null for comparison purposes?**

Then encode your answer, and make the encoding a *named policy* rather than a
default:

```python
class NullPolicy(Enum):
    DISTINCT = auto()   # NaN != null; every Stage 1 Task 2 row is a finding
    UNIFIED  = auto()   # both map to MISSING before comparing
```

The justification must cover all three of these cases, because a single rule
that handles all three does not exist:

| case | the question it forces |
|---|---|
| `pd.Series([1.0, nan]).sum()` = `1.0` vs Polars sum of `[1.0, NaN]` = `NaN` | Is this a value finding, or a representation artifact? |
| pandas `mean()` of an all-null column → `nan`; Polars → `null` | Same value class, different type. Finding? |
| Polars `is_nan()` on a null row → `null` (three-valued) | A boolean comparator has no cell for this. |

**Predict.** Commit to one of `DISTINCT` / `UNIFIED` as your default *before*
working through the table, then see whether the table changes your mind.

**Acceptance.** The policy is a named value passed into `compare`, not a hidden
default. Every entry above has a one-line justification recorded next to it.
And you can state the specific class of divergence your chosen default will hide
— every choice hides one, and the deliverable is knowing which.

**Trap.** `UNIFIED` feels like the pragmatic engineering choice, and it silently
erases the *entire* Stage 1 Task 2 finding — the one the whole missing-value
axis exists for. If you choose it, the finding has to be recovered by an
explicit representation field.

---

## Task 3 — The order policy, scoped per operation

**Do.** Row order may be normalized **only** where the operation genuinely
promises no order. Build the list of which operations those are, as data:

```python
ORDER_PROMISE = {
    "group_by.agg":      Order.NONE,      # normalize before comparing
    "sort":              Order.TOTAL,     # never normalize
    "join":              ...,             # ← you decide, with evidence
    "unique":            ...,
    "filter":            Order.PRESERVED,
    "concat":            ...,
}
```

For each entry you fill in, the evidence is an executed pair, not the
documentation's wording.

**Predict.** For `join` and `unique`, predict whether each library promises an
order, then check. Guess before you look: which of the two libraries makes
*fewer* promises?

**Record.**

| operation | pandas promise | polars promise | shared promise | normalize? |
|---|---|---|---|---|

**Acceptance.** `compare` refuses to normalize row order unless the case names
an operation whose entry is `Order.NONE`. A blanket `sort_before_compare=True`
switch is a failed version of this task, because it makes case 12 of Stage 1
(the `sort_values` / `sort` null-placement divergence) unreachable.

**Trap.** `group_by.agg` promises no order in Polars, and pandas `groupby`
defaults to `sort=True`. The *shared* promise is the weaker one — but that means
your harness cannot detect a change in pandas' key ordering, so the pandas
ordering needs its own case with `Order.TOTAL`.

---

## Task 4 — The twelve seed cases

**Do.** Implement all twelve. For each: predict the outcome, write the
prediction as a comment in the file, then run it. **Keep the wrong predictions
in the file.** They are the record of what your model of these libraries got
wrong, and they are worth more than the passing cases.

| # | case | the call to compare |
|---|---|---|
| 1 | empty frame, dtype survival | filter to zero rows, then read the column dtype |
| 2 | all-null column, sum | `sum()` on `[None, None]` float |
| 3 | all-null column, mean/min/max | `mean()`, `min()`, `max()` on the same |
| 4 | all-null column, the three counters | pandas `count`/`size`/`nunique` vs Polars `count`/`len`/`n_unique` |
| 5 | mixed-type column construction | `Series([1, "a", 2.0])` |
| 6 | string reduction | `sum()` on `["a", "b"]` |
| 7 | truthiness reduction | `any()` on `[0, 1]` **typed as integers** |
| 8 | float summation order | `sum()` of `[0.1] * 10` |
| 9 | duplicate column names | build a frame with two columns named `a` |
| 10 | datetime resolution | parse `"2026-01-01"` and read the unit |
| 11 | duplicate keys, unequal multiplicity | Stage 1 Task 3c, as a harness case |
| 12 | missing-column exception class | select column `"zz"` from a frame without it |

**Acceptance.** Twelve cases run. Each produces a populated seven-field report,
including the ones where one side raises. At least four are classified
`semantic` rather than `syntax-only` — if you got fewer, a normalization is
hiding something.

**Trap.** Case 8 is the one people delete as "floating-point noise". It is the
reason the harness needs a *declared tolerance per case* rather than a global
`atol`: the two libraries sum in a different order, so on this input they return
genuinely different floats. A global tolerance that hides case 8 also hides real
accumulation bugs in your own lowering.

---

## Task 5 — Break the harness on purpose

**Do.** Construct a pair that is **semantically different** and make your
harness report no finding. Then fix the check that let it through.

Three that work, in ascending difficulty:

1. A pair differing only in dtype, compared with a helper that reads `.tolist()`
   on both sides before comparing.
2. A pair differing only in row order, on an operation you mis-declared as
   `Order.NONE`.
3. A pair differing only in *missing-value representation*, under
   `NullPolicy.UNIFIED`.

**Predict.** Which of the three does your current implementation already let
through? Answer before testing.

**Acceptance.** Each of the three, once found, has a regression case in the
harness asserting that the finding is now *reported*. The harness now tests
itself, which is the property that keeps it trustworthy across nine more
sessions of additions.

**Trap.** Fixing the check without adding the regression case. The next
refactor re-introduces it, and this time nothing notices.

---

## Task 6 — The deposit protocol

**Do.** Write down, in the harness's own README or docstring, the three-line
protocol every later stage follows:

1. A divergence discovered in a session becomes a named case **that session**.
2. The case name records the axis and the stage that found it.
3. The whole harness runs at the end of every stage, not only the new case.

**Acceptance.** Stage 1's Task 5 table is fully backfilled through this
protocol, and running the harness reproduces every Stage 1 finding.

---

## Answer key — the seed case divergences

Executed on `pandas 3.0.2` / `polars 1.36.0`.

| # | pandas | polars | class |
|---|---|---|---|
| 1 | dtype `int64` survives an empty filter; shape `(0, 1)` | dtype `Int64` survives; shape `(0, 1)` | **syntax-only** (naming aside) |
| 2 | `sum()` → `0.0` | `sum()` → `0.0` | **syntax-only** — the empty sum agrees |
| 3 | `mean()` → `nan`, `min()` → `nan`, `max()` → `nan` | all three → `None` | **semantic** (representation) |
| 4 | `count()` → `0`, `size` → `2`, `nunique()` → `0` | `count()` → `0`, `len()` → `2`, `n_unique()` → **`1`** | **semantic** |
| 5 | `Series([1, "a", 2.0])` → dtype `object` | raises `TypeError` (`strict=False` would coerce) | **unsupported** |
| 6 | `Series(["a","b"]).sum()` → `'ab'` | raises `InvalidOperationError` | **semantic**, and the dangerous direction |
| 7 | `Series([0,1]).any()` → `True` | raises `SchemaError`: expected `Boolean`, got `i64` | **unsupported** |
| 8 | `Series([0.1]*10).sum()` → `1.0` | → `0.9999999999999999` | **semantic** (accumulation order) |
| 9 | two columns named `a` is legal; shape `(1, 2)` | raises `DuplicateError` | **unsupported** |
| 10 | `to_datetime` → `datetime64[us]` | `str.to_datetime` → `Datetime(time_unit='us')` | **syntax-only** — but see below |
| 11 | 2 labels × 3 labels → length **6**, `[11,21,31,12,22,32]` | no labels; length mismatch raises | **semantic** |
| 12 | `KeyError: 'zz'` | `ColumnNotFoundError` | **semantic** for any caller that catches by type |

### The three cells worth reading twice

**Case 4.** `n_unique()` counts null as a distinct value; `nunique()` does not.
Two counters with the same name, off by one, on every column containing a
missing value. This one reaches production as an off-by-one in a
cardinality-based optimizer decision.

**Case 6.** pandas concatenates strings under `sum` — no error, no warning, a
plausible-looking result. Polars refuses. If a plan can be routed to either
backend, a string column silently *changes the answer* on one path and fails
loudly on the other. Failing loudly is the better behaviour, which means a
translation that "fixes" the Polars error by falling back to pandas has made
things worse.

**Case 8.** Both are correct floating-point sums. They differ because the two
libraries accumulate in a different order. There is no version of this harness
in which a single global tolerance is right: the tolerance is a property of the
case, and it must be declared where the case is defined.

**Case 10** is marked syntax-only because both landed on microseconds *here*.
`datetime64[us]` is pandas 3.0's inferred unit; pandas can also carry `[ns]`,
`[ms]` and `[s]`, and Polars' `Datetime` time_unit is one of `us`/`ns`/`ms`. The
agreement is between two defaults, not two contracts, so the case belongs in the
harness precisely so that a change in either default is caught.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```

Asserts all twelve seed divergences plus the null-policy table. A failure means
either your environment is not the pinned one or one of the libraries changed
behaviour — both of which invalidate every parity conclusion downstream, so fix
it before continuing.
