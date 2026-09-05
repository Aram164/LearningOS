# Session 3 · Stage 2 — HEAD, TAIL, and SAMPLE runtime operands

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

The interesting thing about this stage is that two of the three operations
**agree completely** and the third does not agree at all — and the one that does
not is the one whose divergence is invisible in a spot check.

---

# Part A — Polars on its own terms

## Task A1 — Row-limiting, natively

Write each from intent, without a pandas original:

1. The first three rows.
2. The last three rows.
3. All but the last row.
4. Rows 2 through 4 inclusive, by position.
5. Three rows chosen at random, reproducibly.
6. The three rows with the largest `w` — not "sort then head".
7. The first two rows *of each group* of `k`.
8. A random 40% of the frame.
9. Every second row.
10. The frame in a random order, reproducibly.

**Acceptance.** Ten expressions. #6 uses `top_k`, #7 uses `group_by(...).head(2)`
— note that `head` exists on a `GroupBy` as well as on a frame — and #10 is the
one that needs a keyword you will not guess. Which one it is, is Task B2.

**Trap.** Solving #9 with a Python range and a `take`. `pl.col(...).gather_every`
and `df.gather_every(2)` exist; reaching for Python row indices is the reflex
this whole module is trying to replace.

## Task A2 — Where `head` sits in a lazy plan

**Do.**

```python
df.lazy().sort("v").head(2).explain()
df.lazy().head(2).sort("v").explain()
```

**Predict.** Whether the two produce the same plan, and whether either avoids
sorting all the rows.

**Acceptance.** You can explain what **slice pushdown** did to the first one, and
why it cannot do the same to the second. This also settles a design question you
will meet in Session 8: `sort().head(n)` is not a wasteful way to write
`top_k(n)` — the optimizer already knows.

---

# Part B — The pandas contract

## Task B1 — HEAD and TAIL: the agreement, established rather than assumed

**Do.** For `n` in `2, 0, -1, 99` and on both a five-row frame and an empty
frame, run `head(n)` and `tail(n)` in both libraries.

**Predict.** Which cells disagree. Commit to a number before running.

**Record.** A 4 × 2 × 2 table of shapes and row contents.

**Acceptance.** You can state the answer for negative `n` in both libraries —
which is not "error" — and you have an executed record that these two operations
are **syntax-only**. That record is worth as much as a divergence: it is a
translation you may now make without a per-case check, and Session 1's evidence
rule says you may only say that once you have run it.

**Trap.** `head(None)`. pandas accepts it; Polars raises a `TypeError` from
Python's comparison machinery rather than a Polars error, which is a different
failure surface — and a runtime operand that resolves to `None` is exactly how
that reaches you.

## Task B2 — SAMPLE: the divergence you will not see in a spot check

**Do.** In order:

```python
# 1 — same seed, both libraries
pdf.sample(n=3, random_state=0)
df.sample(n=3, seed=0)

# 2 — sample the whole frame
pdf.sample(frac=1, random_state=0)["w"].tolist()
df.sample(fraction=1.0, seed=0)["w"].to_list()

# 3 — the same, asked differently
df.sample(n=5, seed=0, shuffle=True)["w"].to_list()

# 4 — oversampling without replacement
pdf.sample(n=99, random_state=0)
df.sample(n=99, seed=0)

# 5 — fraction above 1 without replacement
pdf.sample(frac=1.5, random_state=0)
df.sample(fraction=1.5, seed=0)

# 6 — weighted sampling
pdf.sample(n=2, weights=[1, 1, 1, 1, 5], random_state=0)
df.sample(n=2, seed=0, weights=[1, 1, 1, 1, 5])
```

**Predict.** For case 2, whether the two return the same *rows* (they will not —
different generators) and whether they return them in the same *order*. The
second question is the one that matters.

**Record.**

| case | pandas | polars | class |
|---|---|---|---|

**Acceptance.** You can state the randomness contract each library actually
offers, and your test asserts that contract rather than asserting equal rows.
Case 2 is recorded as a **semantic** divergence with a one-line statement of what
breaks if you assume otherwise.

**Trap.** Case 2, and it is the whole task. Sampling three of five rows looks
random on both sides, so a spot check passes. Sample *all* the rows and pandas
returns a permutation while Polars returns them in the original order — because
Polars' `shuffle` defaults to `False` and shuffling is a separate concern from
selecting. Any code that used `sample(frac=1)` as a shuffle silently stops
shuffling.

---

# Part C — The lowering decision

## Task C1 — Thirty cases through both operand paths

`n` may be a literal known at planning time or an `OperandRef` resolved during
execution. Both paths must produce the same behaviour, including the failures.

**Do.** Build the matrix: `{head, tail, sample} × {default, zero, negative,
oversized, empty frame, runtime ref}`, each through a literal and through a
resolved reference.

**Record.** For each cell: the resolved value, the outcome, the exception class
if any, and whether the literal and runtime paths agree.

**Acceptance.** Thirty cells. Every failure raises at the **same boundary** on
both paths — a runtime ref that resolves to something invalid must fail the way
the literal does, not later and not with a different type. The `None` case from
Task B1 is present, because a reference can resolve to `None`.

**Trap.** Testing only the literal path because it is easier to write. The
runtime path is the one with a resolution step in front of it, so it is the one
that can fail in a new way.

## Task C2 — The randomness contract, as a test

**Do.** Write the assertions for `SAMPLE` that do **not** require the two
libraries to return the same rows:

1. Same seed, same library, twice → identical.
2. Different seed → different (with a stated probability of false failure).
3. Output cardinality is exactly `n`, or exactly `ceil/floor(fraction × height)`
   — determine which, and record it.
4. Every returned row is a row of the input.
5. Without replacement, no row appears twice.
6. With replacement, the output may contain repeats and `n > height` is legal.

**Acceptance.** Six properties, each a test. Property 3 is answered by execution
rather than by reading, and you can say what it does at a fraction that lands
exactly between two rows.

---

## Answer key

### Task B1 — HEAD/TAIL agree, including the negative case

| `n` | pandas `head` | polars `head` |
|---|---|---|
| 2 | `[10, 20]` | `[10, 20]` |
| 0 | shape `(0, 3)` | shape `(0, 3)` |
| −1 | `[10, 20, 30, 40]` | `[10, 20, 30, 40]` |
| 99 | shape `(5, 3)` | shape `(5, 3)` |

`tail(-1)` gives `[20, 30, 40, 50]` on both. Negative `n` means "all but the
last/first `n`" in both libraries — a genuine agreement, and one worth having
executed rather than assumed, because it is the kind of edge that documentation
often leaves to the reader.

`head(None)`: Polars raises `TypeError: '<' not supported between instances of
'NoneType' and 'int'` — a Python-level error escaping from inside, not a Polars
diagnostic.

### Task B2 — SAMPLE

| case | pandas | polars | class |
|---|---|---|---|
| 1 | `[30, 10, 20]` | `[10, 50, 20]` | expected: different generators |
| 2 | `[30, 10, 20, 40, 50]` — a permutation | `[10, 20, 30, 40, 50]` — **original order** | **semantic** |
| 3 | — | `[40, 10, 20, 50, 30]` with `shuffle=True` | the opt-in |
| 4 | `ValueError`: *Cannot take a larger sample than population when 'replace=False'* | `ShapeError`: *cannot take a larger sample than the total population when `with_replacement=false`* | different exception class |
| 5 | `ValueError`: *Replace has to be set to `True` when upsampling the population `frac` > 1.* | `ShapeError` — **the same message as case 4** | different exception class *and* different diagnostic granularity |
| 6 | works | `TypeError`: unexpected keyword argument `'weights'` | **unsupported** |

Case 2 is the finding. Polars' `sample` selects rows; it does not reorder them
unless asked. `sample(fraction=1.0)` is therefore an identity operation on row
order, while `sample(frac=1)` is the standard pandas idiom for *shuffling a
frame*. Translating one to the other silently removes the shuffle, and no test
that samples a strict subset will ever notice.

Case 5 deserves a second look for a different reason: pandas distinguishes
"oversampling by count" from "oversampling by fraction" and gives a message
naming the parameter you got wrong. Polars gives one message for both. When a
lowering re-raises the backend's error, the caller loses that distinction —
which is an argument for translating the exception at the boundary rather than
passing it through.

### Task A2

```
df.lazy().sort("v").head(2)         →   SORT BY [slice: (0, 2)] [col("v")]
df.lazy().head(2).sort("v")         →   SORT BY [col("v")]  over a 2-row input
```

The first is a top-k: the slice is pushed into the sort, so the engine never
orders all five rows. The second cannot be — the head happens first and changes
which rows exist — and it is a *different query*, not a slower spelling of the
same one.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
