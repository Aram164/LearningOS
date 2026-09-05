# Session 3 · Stage 3 — `drop_duplicates` versus `unique`

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Two libraries, two functions, four parameters that look like each other, and one
pair of identically-named methods that mean **different things**. The parameter
mapping is easy; the trap is the method next to it.

---

## Fixture F6 — adversarial duplicates

```python
df = pl.DataFrame({
    "k": ["a", "b", "a", "c", "b"],
    "v": [1, 2, 1, 3, 2],
    "w": [10, 20, 30, 40, 50],   # w is unique, so it labels the rows
})
```

`w` is a row label: quoting a result as a list of `w` values says exactly which
rows survived.

---

# Part A — Polars on its own terms

## Task A1 — Distinctness, natively

From intent:

1. The distinct rows, in the order they first appear.
2. The distinct values of `k`, order irrelevant, as fast as possible.
3. One row per `k` — the first.
4. One row per `k` — the last.
5. Only the rows whose `k` occurs exactly once.
6. A boolean column marking the *first* occurrence of each `k`.
7. A boolean column marking every row whose `k` occurs more than once.
8. The number of distinct `k`.
9. The distinct `(k, v)` pairs.
10. The `k` values that occur more than twice.

**Acceptance.** Ten expressions. #2 and #3 differ in a way worth naming: one has
no order requirement at all and Polars has a keyword for exactly that. #6 and #7
are two different predicates that people routinely conflate — and conflating
them is Part B's trap arriving early.

**Trap.** Solving #5 with a `group_by` and a filter on count, then joining back.
`is_unique()` over a partition, or `filter` on `len().over("k")`, keeps it in one
expression.

## Task A2 — What `unique()` promises about order

**Do.**

```python
df.unique()["w"].to_list()
df.unique()["w"].to_list()          # again
df.unique(maintain_order=True)["w"].to_list()
```

**Predict.** Whether the first two agree with each other.

**Acceptance.** You can state Polars' actual promise about the row order of
`unique()` — and you can say why the promise is *weaker* than what you observe,
and why relying on the observation is a bug waiting for a different machine.

**Trap.** Running it once, seeing a plausible order, and writing a test that
asserts it. The default is unordered; a run that comes out sorted proves nothing.

---

# Part B — The pandas contract

## Task B1 — The parameter mapping

**Do.** Fill in the table by execution, quoting results as `w` lists.

| pandas | polars | `w` kept (pandas) | `w` kept (polars) | agree? |
|---|---|---|---|---|
| `drop_duplicates()` | `unique(maintain_order=True)` | | | |
| `drop_duplicates(subset=["k"], keep="first")` | `unique(subset=["k"], keep="first", maintain_order=True)` | | | |
| `drop_duplicates(subset=["k"], keep="last")` | `unique(subset=["k"], keep="last", maintain_order=True)` | | | |
| `drop_duplicates(subset=["k"], keep=False)` | `unique(subset=["k"], keep=?, maintain_order=True)` | | | |
| — | `unique(subset=["k"], keep="any")` | | | |

**Predict.** The Polars spelling of `keep=False` before you look it up.

**Acceptance.** A complete mapping table, with `keep=False` resolved and
`keep="any"` identified as having **no pandas counterpart** — and a one-line
statement of what it buys, which is the reason it exists.

**Trap.** Omitting `maintain_order=True`. Every row of this table matches only
with it; without it the values agree and the order does not, and a test that
sorts before comparing will report a clean pass on a translation that has
silently dropped an ordering guarantee pandas makes.

## Task B2 — `duplicated()` and `is_duplicated()` are not the same function

**Do.**

```python
pdf.duplicated(subset=["k"]).tolist()
df.select(pl.struct("k").is_duplicated()).to_series().to_list()
df.select(pl.col("k").is_first_distinct()).to_series().to_list()
```

**Predict.** All three lists, five booleans each, before running.

**Record.**

| row | `k` | pandas `duplicated` | polars `is_duplicated` | polars `is_first_distinct` |
|---|---|---|---|---|

**Acceptance.** You can state the difference in one sentence, and you can say
which Polars call is the true counterpart of pandas `duplicated()` — it is not
the one with the matching name.

**Trap.** This is the stage's real finding. The names are near-identical, both
return a boolean mask of the right length, and on a frame with no duplicates
they agree perfectly. They differ on exactly the rows the operation is about.

## Task B3 — Nulls, NaNs, and the cases that are policy rather than behaviour

**Do.** Run the default dedup on each:

1. `["a", None, None]` — nulls in the key
2. `[1.0, float("nan"), float("nan")]` — NaNs in the key
3. an empty frame
4. a frame with a `List` column in the subset

**Record.** For each: rows kept on both sides, and whether it raised.

**Acceptance.** Cases 1 and 2 answered by execution. Case 4 recorded as a
**policy** entry — supported, unsupported, or version-sensitive — rather than
normalized away. Whatever it does, it is a limitation you have written down, and
Session 10's version-transition lab will re-check exactly this row.

---

# Part C — The lowering decision

## Task C1 — The mapping, unit-tested without a DataFrame

**Do.** Extract `map_drop_duplicates_params(subset, keep, ignore_index) ->
dict` and test it **without executing any frame operation**. Every pandas
argument combination in, either a valid Polars kwargs dict or a typed refusal
out.

**Acceptance.** The function is total over the pandas signature, `keep=False`
maps correctly, an unsupported combination raises at mapping time rather than
producing kwargs that fail later inside the engine, and the tests run in
milliseconds because they touch no data. This separation is the point: parameter
translation is a pure function and deserves to be tested like one.

**Trap.** Letting `ignore_index` quietly vanish. Polars has no row labels, so
there is no index to reset — but that means the pandas caller's request is
*already satisfied*, not that the parameter is unsupported. Record which of the
two it is; they are different answers to a reviewer.

---

## Answer key

### Task A2 / B1

`df.unique()` returned `[40, 30, 10, 50, 20]` on the run that produced this key —
**not** sorted, and not the input order. `unique(maintain_order=True)` gives
`[10, 20, 30, 40, 50]`. The default makes no ordering promise at all, so the
first result is one legal answer among many and must never be asserted.

| pandas | polars (with `maintain_order=True`) | `w` kept |
|---|---|---|
| `drop_duplicates()` | `unique()` | `[10, 20, 30, 40, 50]` (no full-row duplicates) |
| `subset=["k"], keep="first"` | `keep="first"` | `[10, 20, 40]` |
| `subset=["k"], keep="last"` | `keep="last"` | `[30, 40, 50]` |
| `subset=["k"], keep=False` | `keep="none"` | `[40]` |
| — | `keep="any"` | `{a, b, c}` in unspecified order |

`keep=False` → `keep="none"`. `keep="any"` has no pandas counterpart: it tells
the engine *"I do not care which representative you keep"*, which lets it skip
the bookkeeping that first/last require. It is the fastest option and it is only
correct when the non-subset columns genuinely do not matter — which, for a
translation of pandas semantics, is never, since pandas always promises first.

### Task B2 — the two masks

| row | `k` | pandas `duplicated()` | polars `is_duplicated()` | polars `is_first_distinct()` |
|---|---|---|---|---|
| 0 | a | `False` | `True` | `True` |
| 1 | b | `False` | `True` | `True` |
| 2 | a | `True` | `True` | `False` |
| 3 | c | `False` | `False` | `True` |
| 4 | b | `True` | `True` | `False` |

pandas `duplicated()` means *"this row is a repeat of an earlier one"* — it marks
the **2nd and later** occurrences. Polars `is_duplicated()` means *"this row's
value occurs more than once anywhere"* — it marks **all** occurrences, including
the first.

The counterpart of pandas `duplicated()` is `~is_first_distinct()`, not
`is_duplicated()`. On this fixture the two Polars masks differ on rows 0 and 1,
which is where the whole error lives: a filter written with the wrong one drops
the rows it was supposed to keep, and the code reads correctly.

### Task B3

Nulls are values for the purpose of dedup on both sides: `["a", None, None]`
reduces to two rows in both libraries. That agreement is worth having executed —
it is not the obvious answer, since nulls compare unequal to themselves in SQL,
and both libraries deliberately do not follow SQL here.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
