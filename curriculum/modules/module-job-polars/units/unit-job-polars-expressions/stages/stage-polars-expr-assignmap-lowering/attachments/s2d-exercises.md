# Session 2 · Stage 4 — Translate pandas `assign` into native expression trees

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Stage 1 of this session established the rule: `assign` is **sequential**,
`with_columns` is **parallel**. This stage turns that observation into a
lowering algorithm and finds its boundaries — the cases where the algorithm must
stage, and the cases where it must give up and say so.

The output is a decision procedure you can apply to an `assign` call you have
never seen, plus a twelve-row matrix of evidence.

---

## The algorithm, stated so you can attack it

For an assign chain of entries `e₁ … eₙ`, each writing a name and reading a set
of names:

1. Build a dependency graph over **names**, not over new columns — an overwrite
   is a write.
2. Any entry reading a name written by an earlier entry depends on it.
3. Partition into layers by longest path.
4. Emit one `with_columns` context per layer.
5. An entry that cannot be expressed as an `Expr` tree at all breaks the chain:
   everything from that entry onward is **fallback**.

Your job on this sheet is to find the inputs where each numbered step is wrong
or incomplete.

---

## Task 1 — The twelve-case translation matrix

**Do.** For each case: predict the layer count, write the Polars translation, run
both sides, and classify.

| # | pandas `assign(...)` | what it probes |
|---|---|---|
| 1 | `c=5` | scalar broadcast |
| 2 | `c=lambda t: t.a + t.b` | two-column arithmetic; result dtype |
| 3 | `c=lambda t: t.a * 2, d=lambda t: t.b * 2` | independent entries → one layer? |
| 4 | `z=lambda t: t.a * 2, w=lambda t: t.z + 1` | sibling dependency |
| 5 | `a=lambda t: t.a * 10, b=lambda t: t.a + 1` | overwrite, then read the overwritten name |
| 6 | `a=lambda t: t.a * 10, a=lambda t: t.a + 1` | the same name twice — is it even legal Python? |
| 7 | `c=[1, 2, 3]` | a sequence constant of the right length |
| 8 | `c=[1, 2]` on three rows | length mismatch |
| 9 | `c=lambda t: t.s.str.upper()` | namespace translation |
| 10 | `c=lambda t: t.a.map(python_fn)` | opaque callable |
| 11 | `c=other_series` where `other_series` has a different index | an external operand |
| 12 | `c=lambda t: t.a.sum()` | an aggregation inside an element-wise context |

Classification is exactly one of **native** (one context), **staged** (n
contexts, n recorded), **fallback** (no expression tree), or **rejected** (must
raise at translation time rather than produce a wrong answer).

**Record.**

| # | layers | polars translation | class | pandas result | polars result | agree? |
|---|---|---|---|---|---|---|

**Acceptance.** Twelve rows. Every `native` row has an executed comparison
proving values *and* dtype agree. Every `fallback` row names what specifically
cannot be expressed. Row 6 has a definite answer about what Python does before
pandas ever sees it.

**Trap.** Row 12. `t.a.sum()` is a scalar in pandas and broadcasts; in Polars
`pl.col("a").sum()` inside `with_columns` also broadcasts. They agree — so the
row is `native` — but check the dtype and check what happens when the frame is
**empty**, because the broadcast of a reduction over zero rows is where the two
stop agreeing.

---

## Task 2 — Prove step 5 with a wrong answer, not an exception

The dangerous failure of this lowering is not a crash.

**Do.** Take case 5 and deliberately lower it wrongly, as a single context:

```python
df.with_columns(a=pl.col("a") * 10, b_wrong=pl.col("a") + 1)
```

against the correct staging:

```python
df.with_columns(a=pl.col("a") * 10).with_columns(b_right=pl.col("a") + 1)
```

**Predict.** Both values, before running.

**Acceptance.** You have both results side by side, and you can state why this is
worse than case 4 — where the same mistake raises `ColumnNotFoundError`. Then
write the property your translator must assert so that this can never ship: name
it, and say where it is checked.

**Trap.** Concluding "so always stage every entry". That is correct and it is
also a performance decision you have just made silently: `n` entries become `n`
contexts and the optimizer loses the chance to fuse them. The right answer is to
stage by dependency layer, which requires actually building the graph.

---

## Task 3 — The reads-set is harder than it looks

Step 1 needs, for each entry, the set of names it reads. In Polars that is
`expr.meta.root_names()`. In pandas it is whatever the lambda touches.

**Do.** For each of these, determine the read set:

```python
lambda t: t.a + t.b                 # easy
lambda t: t["a"] + t["b"]           # same names, different syntax
lambda t: t[cols]                   # cols is a Python variable
lambda t: t.filter(like="x").sum(1) # names not known until runtime
lambda t: t.a + EXTERNAL            # EXTERNAL is a module-level constant
```

**Predict.** For which of the five can the read set be determined **without
executing the lambda**?

**Acceptance.** You can state the boundary of static analysis here in one
sentence, and you can say what a translator should do on the far side of it —
which is not "guess". Compare with the Polars side, where `root_names()` gives
an exact answer for any `Expr`, and note why that difference exists.

**Trap.** Assuming the read set is recoverable by inspecting the lambda's
bytecode or signature. It is recoverable for the first two and not for the rest,
and a translator that is right most of the time here produces silently wrong
column ordering the rest of the time.

---

## Task 4 — Where the fallback boundary actually sits

**Do.** For each of the following, decide **native / staged / fallback** and
then verify by attempting a native translation:

1. `t.a.map(lambda v: v + 1)` — an element-wise Python callable
2. `t.a.rolling(2).mean()` — a window with an equivalent Polars expression
3. `t.a.apply(some_c_extension)` — an opaque call
4. `t.groupby(t.k).transform("sum")` — a grouped transform inside assign
5. `t.a.astype("category")` — a metadata operation
6. `t.a.pipe(user_fn)` — a user function taking and returning a Series

**Acceptance.** Each has a classification with evidence. At least one of these
that *looks* like fallback has a native expression (find it), and at least one
that looks native does not survive contact with the pinned version (find that
too). Record both.

**Trap.** Treating "a Python callable appears" as sufficient for fallback. Case 1
has a native form; case 3 does not. The distinguishing question is not whether
Python code appears in the source but whether the *operation* has an expression
equivalent — and `map_elements` exists precisely to keep case 1 inside the
expression system, at a cost you should measure rather than assume. Polars will
tell you so itself: running case 1 emits a `PolarsInefficientMapWarning` that
prints the native rewrite. Read that warning as data — it is the library
classifying your own translation for you, and Session 8 returns to when the
warning should be believed and when the native rewrite changes semantics.

---

## Task 5 — The staged-vs-fallback closing decision

**Do.** Write the decision procedure as runnable code:
`classify(assign_entries) -> list[Layer] | Fallback`, where a `Layer` is a list
of entries safe to emit in one `with_columns`.

Feed it all twelve cases from Task 1 and the six from Task 4.

**Acceptance.** The procedure returns the layer counts you recorded by hand, and
it *refuses* rather than guesses on the Task 3 cases whose read set is not
statically determinable. A procedure that silently assumes an empty read set for
an opaque lambda is the specific bug this task exists to prevent — assert
against it.

---

## Answer key

### Task 1 — the rows that decide the design

**Row 3** is one layer: two entries, neither reads the other's name. This is the
case that justifies building the graph rather than staging everything.

**Row 4** is two layers, and lowering it as one raises `ColumnNotFoundError`.

**Row 5** is two layers, and lowering it as one **does not raise**:

```
one context   → a = [10, 20, 30], b_wrong = [2, 3, 4]     ← read the OLD a
staged        → a = [10, 20, 30], b_right = [11, 21, 31]  ← read the NEW a
```

pandas gives `[11, 21, 31]`. So the naive lowering produces a plausible frame
with wrong numbers and no diagnostic. This row, not row 4, is the reason the
dependency graph is over *names*.

**Row 6** never reaches pandas: `assign(a=..., a=...)` is a duplicate keyword
argument and Python raises `SyntaxError` at compile time. It is worth one line in
the matrix because it tells you the entry list can be treated as having unique
keys per call — a real simplification, and one you should record as an
assumption rather than assume.

**Row 8** raises on both sides with different types: pandas `ValueError`
(*Length of values (2) does not match length of index (3)*), Polars `ShapeError`
(*unable to add a column of length 2 to a DataFrame of height 3*).

**Row 12** broadcasts on both sides and agrees on non-empty input. On an *empty*
frame the reduction has no rows to reduce, and Session 1's seed case 3 already
recorded that pandas returns `NaN` where Polars returns `null` for `mean` while
both give `0.0` for `sum` — so whether row 12 stays `native` depends on which
reduction it contains. Record it as native-with-a-condition, not native.

### Task 3

Read sets are statically determinable for `t.a + t.b` and `t["a"] + t["b"]`
only. `t[cols]` depends on a runtime value; `t.filter(like="x")` depends on the
schema; `t.a + EXTERNAL` reads a name outside the frame that a column-level graph
does not model at all.

The asymmetry with Polars is structural rather than incidental: `pl.col("a")`
*is* a data structure recording the name, so `root_names()` is a read of stored
information. A pandas lambda is opaque Python whose column references only exist
once it runs. This is the same distinction as Session 1's "expression is a value,
not a statement", arriving as a practical limit on what a translator can know.

The correct behaviour past the boundary is to refuse: mark the entry
non-analyzable and fall back from that entry onward. An assumed-empty read set
turns an unknown dependency into a declared independence, which is exactly the
row-5 failure again.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
