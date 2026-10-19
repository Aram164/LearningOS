# Session 2 · Stage 2 — Selectors and expression expansion

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

The goal is a selection that survives a schema change. `select_dtypes` returns a
*list of names computed now*; a Polars selector is a *rule resolved at
execution*. Anything that materializes names into Python defeats the point, and
this stage is about noticing when you have done that by accident.

---

## Fixture F3 — three schemas, one expression

```python
narrow = pl.DataFrame({"a": [1], "s": ["x"]})
wide   = pl.DataFrame({"a": [1], "b": [1.5], "c": [2], "s": ["x"], "t": ["y"]})
changed = pl.DataFrame({"a": [1.0], "s": ["x"], "n": [2]})      # a is now Float64; n is new
```

Every task's expression must be written **once** and applied to all three.

---

## Task 1 — Set algebra over selectors

**Do.** With `import polars.selectors as cs`, evaluate each against `wide` using
`cs.expand_selector(wide, <sel>)` — which answers "which columns would this
pick?" without executing anything:

```python
cs.numeric()
cs.by_dtype(pl.String)
cs.numeric() | cs.string()
cs.numeric() - cs.by_name("a")
cs.numeric() & cs.by_name("a", "s")
~cs.numeric()
cs.all().exclude("s")
```

**Predict.** Write the expected column tuple for each of the seven before
running. Then the important one:

```python
wide.select(cs.numeric() - 1)      # what does this return?
```

**Record.**

| selector | expanded columns | is `-` set difference or arithmetic here? |
|---|---|---|

**Acceptance.** You can state the rule that decides what `-` means, and you can
say what the same ambiguity does to `|` and `&`. Then write down the defensive
habit that makes it a non-issue.

**Trap.** This is the whole task. `cs.numeric() - cs.by_name("a")` is a set
difference; `cs.numeric() - 1` is **element-wise subtraction applied to every
numeric column**. Both are legal, neither warns, and the second one silently
becomes a *computation* where you meant a *selection*. The operator is
overloaded on the type of its right operand.

---

## Task 2 — Schema drift: the test that must pass without editing the expression

**Do.** Write one expression that "selects every numeric column, excluding
`a`, and sums each". Apply it to `narrow`, `wide`, and `changed`. Then apply it
to a fourth schema of your own with *no* numeric columns at all.

**Predict.** For each of the four: the output columns, and whether it raises.
Commit to the no-numeric case in particular.

**Record.**

| schema | expanded columns | output | raised? |
|---|---|---|---|
| `narrow` | | | |
| `wide` | | | |
| `changed` | | | |
| no-numeric | | | |

**Acceptance.** The same expression string works on all four, and you can
explain what `changed` proves that `wide` does not: `a` becomes `Float64` there,
so a selector keyed on dtype picks a *different set* than it did before, with no
error. That is the intended behaviour and also the risk — state which of your
selections want it and which do not.

**Trap.** Writing `cs.numeric() - cs.by_name("a")` and calling the task done. On
`narrow` there is exactly one numeric column and it is excluded, so the result is
an empty selection — check what that does inside `select` versus inside
`with_columns` before assuming it is harmless.

---

## Task 3 — Strictness: a name that is not there

**Do.**

```python
wide.select(cs.by_name("zz"))
wide.select(cs.by_name("zz", require_all=False))
pd.DataFrame({"a": [1], "b": [1.0], "s": ["x"]}).select_dtypes("number")
```

**Predict.** Which of the first two raises, and what the third returns.

**Acceptance.** You can name the pandas equivalent of `require_all=False` — and
having looked, you can say why there is not really one, which is itself the
finding: `select_dtypes` cannot fail on a missing name because it never takes a
name.

**Trap.** Choosing `require_all=False` as the default because it "won't break".
A selection that silently picks nothing is how a whole projection disappears
from a plan without an error. Default to strict; opt out per call with a reason.

---

## Task 4 — Implement the `select_dtypes` translation properly

**Do.** Write `translate_select_dtypes(include, exclude) -> selector` covering
the pandas argument forms you actually have to support: a single dtype, a list, a
string alias like `"number"`, and both `include` and `exclude` given together.

Then test it against all three fixtures **plus** a schema containing `Boolean`
and `Categorical`, because those are where the dtype *classes* stop matching:
pandas' `"number"` and Polars' `cs.numeric()` do not have to agree about
booleans, and you need the answer as evidence rather than as an assumption.

**Record.** For each pandas argument form: the selector produced, the expanded
columns on each fixture, and a native / adapt / unsupported classification.

**Acceptance.** The function is total over the forms you listed, every
`unsupported` form raises a clear error rather than silently selecting nothing,
and the boolean/categorical question is answered with an executed result.

**Trap.** Building the selector by materializing `df.schema` into a Python list
of names. It passes every test in this task and fails the one property the
stage exists for — apply it to `changed` and it selects the old set.

---

## Answer key

### Task 1

| selector | expanded on `wide` |
|---|---|
| `cs.numeric()` | `('a', 'b', 'c')` |
| `cs.by_dtype(pl.String)` | `('s', 't')` |
| `cs.numeric() | cs.string()` | `('a', 'b', 'c', 's', 't')` |
| `cs.numeric() - cs.by_name("a")` | `('b', 'c')` |
| `cs.numeric() & cs.by_name("a", "s")` | `('a',)` |
| `~cs.numeric()` | `('s', 't')` |
| `cs.all().exclude("s")` | `('a', 'b', 'c', 't')` |

And the trap, on fixture F2 from the previous stage (`a`, `b`, `d` numeric):

```
df.select(cs.numeric() - 1)
→ {'a': [0, 1, 2], 'b': [0.5, 1.5, 2.5], 'd': [None, 0, 1]}
```

`-` dispatches on the right operand: a selector on the right makes it set
difference, a scalar makes it arithmetic broadcast over every selected column.
`|` and `&` carry the same hazard against boolean expressions. The defensive
habit: keep selector algebra and value arithmetic in separate expressions, and
call `cs.expand_selector` on anything you are unsure about — it answers with
column names, so a selector that has quietly become a computation shows up
immediately.

### Task 3

`cs.by_name("zz")` raises `ColumnNotFoundError`: *"zz" not found*.
`cs.by_name("zz", require_all=False)` expands to `[]` — no error, nothing
selected. pandas `select_dtypes("number")` → `['a', 'b']`.

### Task 2 — the empty selection

An empty selection inside `select` yields a frame of shape `(0, 0)` — zero
columns *and* zero rows, because there is nothing left to give the frame a
height. Inside
`with_columns` it is a no-op. Neither raises, which is why the no-numeric
schema belongs in the test: the failure it would otherwise produce is not an
exception but a silently missing projection downstream.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
