# Session 4 · Stage 2 — Type promotion, coercion, and strictness

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Two questions, and they have different answers: *what type results when two types
meet* (promotion) and *what happens when a value will not fit* (strictness). One
library answers the second question with an exception and the other with a
number.

---

# Part A — Polars on its own terms

## Task A1 — Derive the supertype rule

**Do.** For each pair, add two one-element Series of those dtypes and record the
result dtype. Predict each before running.

| left | right | predicted | actual |
|---|---|---|---|
| `Int8` | `Int64` | | |
| `Int8` | `UInt8` | | |
| `Int32` | `UInt32` | | |
| `Int64` | `UInt64` | | |
| `UInt8` | `Int64` | | |
| `Float32` | `Int64` | | |
| `Float32` | `Float64` | | |
| `Boolean` | `Int64` | | |
| `String` | `Int64` | | |
| `Date` | `Datetime` | | |

**Acceptance.** You can state the rule in one sentence, and you can explain the
`Int64` + `UInt64` row from it — that row is the rule's edge, and it is where the
rule stops being lossless.

**Trap.** Assuming signed-plus-unsigned always widens to a bigger integer. It
does for `Int8`+`UInt8` and `Int32`+`UInt32`. It cannot for `Int64`+`UInt64`,
because no integer type in the system holds both ranges — so the supertype is
`Float64`, and every value above 2^53 silently loses exactness. A join key of
`UInt64` compared against an `Int64` column goes through this.

## Task A2 — Strictness is a parameter, and it has a default

**Do.**

```python
pl.Series(["1", "x"]).cast(pl.Int64)
pl.Series(["1", "x"]).cast(pl.Int64, strict=False)
pl.Series([300]).cast(pl.Int8)
pl.Series([300]).cast(pl.Int8, strict=False)
pl.Series([1.9, -1.9]).cast(pl.Int64)
```

**Predict.** All five.

**Acceptance.** You can state Polars' default (`strict=True`) and what
`strict=False` produces — which is not a clamped value. And you can say what the
float-to-int rule is: truncation toward zero, not rounding.

## Task A3 — Overflow in arithmetic is a different question from overflow in a cast

**Do.**

```python
pl.Series([127], dtype=pl.Int8) + pl.Series([1], dtype=pl.Int8)   # arithmetic
pl.Series([300]).cast(pl.Int8)                                     # cast
```

**Acceptance.** Two different behaviours from the same library, and you can say
why they differ. One is a hardware-level operation on a fixed-width integer; the
other is a conversion Polars chose to police.

---

# Part B — The pandas contract

## Task B1 — The cast that lies

**Do.**

```python
pl.Series([300]).cast(pl.Int8)
pd.Series([300]).astype("int8")
```

**Predict.** Both.

**Acceptance.** Recorded as a harness case with the class **semantic**, and you
can state which direction is dangerous. Then decide the Stratum policy: when a
captured `astype` cannot be represented, does the backend reproduce pandas'
answer, raise, or record a divergence? Write the decision down.

**Trap.** This is the stage's headline. pandas returns `44` — the low byte of
300 — with no error and no warning. Polars raises. A translation that "fixes"
the Polars error by falling back to pandas produces a plausible wrong number
where it previously produced a loud failure.

## Task B2 — Division, and the types it produces

**Do.** `5 / 2` and `5 // 2` on integer Series in both libraries; record result
dtype in each case.

**Acceptance.** Four cells. The agreement here is worth recording as
syntax-only, on executed evidence.

## Task B3 — Arithmetic overflow: the rare full agreement

**Do.** `int8` 127 + 1 in both libraries.

**Acceptance.** Both wrap to `-128`. Record it as syntax-only — and note that
this makes the Task B1 divergence stranger, not less important: the two
libraries agree on silent wraparound in arithmetic and disagree completely on
casts.

---

# Part C — The lowering decision

## Task C1 — A coercion policy, written once

**Do.** Produce a table with one row per pandas `astype` target you must
support. Columns: pandas result on an out-of-range value, Polars result, chosen
Stratum behaviour, and the reason.

**Acceptance.** Every row's chosen behaviour is one of **reproduce pandas**,
**raise**, or **raise with a translated message**. No row is left as "depends".
The `Int64`/`UInt64` supertype row from Task A1 appears, because a join or
comparison triggers it without any `astype` being captured at all.

---

## Answer key

### Task A1

| left | right | supertype |
|---|---|---|
| `Int8` | `Int64` | `Int64` |
| `Int8` | `UInt8` | `Int16` |
| `Int32` | `UInt32` | `Int64` |
| `Int64` | `UInt64` | **`Float64`** |
| `UInt8` | `Int64` | `Int64` |
| `Float32` | `Int64` | `Float64` |
| `Float32` | `Float64` | `Float64` |
| `Boolean` | `Int64` | `Int64` |
| `String` | `Int64` | raises `InvalidOperationError`: *arithmetic on string and numeric not allowed, try an explicit cast first* |
| `Date` | `Datetime` | raises `InvalidOperationError`: *+ not allowed on date and datetime[μs]* |

**The rule:** the supertype is the smallest type in the system that holds both
operands' ranges exactly. Mixing signed and unsigned widens to a signed type one
size up — `Int8`+`UInt8` → `Int16`, `Int32`+`UInt32` → `Int64`. At 64 bits there
is nothing to widen *to*, so the system falls back to `Float64`, which holds both
ranges approximately and is exact only up to 2^53. That is the one place the
promotion rule stops being lossless, and it is reachable from an ordinary join
between a `UInt64` id column and an `Int64` one.

Note that `Boolean` + `Int64` works and gives `Int64` — booleans are numeric
under arithmetic here, which is the opposite of the Session 1 finding that
`Series.any()` refuses an integer Series. Numeric-to-boolean is refused;
boolean-to-numeric is not.

### Task A2 / B1

| call | result |
|---|---|
| `pl.Series(["1","x"]).cast(Int64)` | raises `InvalidOperationError`: *conversion from `str` to `i64` failed … for 1 out of 2 values: ["x"]* |
| `.cast(Int64, strict=False)` | `[1, None]` |
| `pl.Series([300]).cast(Int8)` | raises `InvalidOperationError`: *conversion from `i64` to `i8` failed … for 1 out of 1 values: [300]* |
| `.cast(Int8, strict=False)` | `[None]` — null, not a clamped or wrapped value |
| `pl.Series([1.9, -1.9]).cast(Int64)` | `[1, -1]` — truncation toward zero |
| `pd.Series([1.9,-1.9]).astype("int64")` | `[1, -1]` — agrees |
| **`pd.Series([300]).astype("int8")`** | **`44`** |

`44` is `300 mod 256`. pandas performs the C-level narrowing conversion and
returns the low byte; there is no error, no warning, and the number looks
ordinary. Polars refuses the same conversion. `strict=False` gives you null —
Polars' position is that a value which does not fit is *missing*, not
*wrapped*, which is at least a defensible answer and is never 44.

### Task B2 / B3

| operation | pandas | polars |
|---|---|---|
| `5 / 2` on ints | `float64` | `Float64` |
| `5 // 2` on ints | `int64` | `Int64` |
| `int8` 127 + 1 | `-128` | `-128` |

Arithmetic overflow wraps identically on both sides. So the two libraries share
the hardware's behaviour where the hardware decides, and diverge completely where
the library decides. That is the sentence to keep: **the divergences are in the
policy layer, not the arithmetic.**

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```
