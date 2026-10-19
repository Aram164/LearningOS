# Session 7 · Stage 2 — Build a pandas↔Polars join compatibility layer

**Exercise sheet.** Verified against `pandas 3.0.2` / `polars 1.36.0`.

Stage 1 produced the divergence list. This stage builds the layer that survives
it, from blank, and then measures the result against a real implementation.

The deliverable is a standalone `JoinConfig` + two executors + a parity suite —
built in your own scratch space, importing nothing from Stratum.

---

# Part A — Polars on its own terms

## Task A1 — Write the joins you would actually want

Before building a compatibility layer, be sure you can write joins natively.
From intent, one expression each:

1. Left-join, keeping every left row, with the right frame's `w` renamed `w_ref`.
2. Rows of `L` whose key appears in `R` — without materializing a joined frame.
3. Rows of `L` whose key does **not** appear in `R`.
4. A join on two columns at once.
5. A join where the left key is `k` and the right key is `key`.
6. Join, then keep only the columns that came from the left plus one from the right.
7. A join that must fail if the right side has duplicate keys.
8. The most recent `R` row at or before each `L` timestamp.
9. A join on `L.t > R.t` — no equality anywhere.
10. Join three frames in one chain.

**Acceptance.** Ten expressions. #2 and #3 use `semi`/`anti` rather than a join
plus a filter, #7 uses `validate`, and #8/#9 use `join_asof`/`join_where`. You
can say which of the ten pandas cannot express without extra steps.

**Trap.** #6 written as a join followed by `select`. Correct, but check the plan:
does projection pushdown narrow the join's inputs, or did you build a wide
intermediate the optimizer then discarded? Use `explain()` to answer rather than
assuming either way.

---

# Part B — The compatibility layer

## Task B1 — `JoinConfig`, from blank

**Do.** In your own scratch file, define a `JoinConfig` carrying every field the
two libraries need, and two executors `pandas_exec(config, L, R)` and
`polars_exec(config, L, R)`. Import nothing from Stratum — the point is to
derive the field set, not to recognize it.

The fields must at minimum cover: join kind, left/right key specifications
(shared name, differing names, multiple keys), null-matching policy, suffix
policy, coalesce policy, validation, and output column ordering.

**Acceptance.** Each field exists because a Stage 1 finding demanded it, and you
can name that finding for each. A field you cannot justify from evidence is a
field you copied.

## Task B2 — Sixteen parity cases

**Do.** Build at least sixteen, covering:

| # | case |
|---|---|
| 1-2 | shared key name; differing key names |
| 3 | multiple keys |
| 4 | overlapping non-key column names |
| 5-6 | duplicate keys on the left; on the right; on both |
| 7 | null keys on both sides |
| 8 | no matches at all |
| 9 | empty left frame; empty right frame |
| 10 | key dtype mismatch (`Int64` left, `UInt64` right) |
| 11 | key dtype mismatch (`Int64` left, `String` right) |
| 12-16 | one per join kind, including `full` with and without coalesce |

**Predict.** Case 10 before running it. The Session 4 supertype rule applies —
what dtype does the join key become, and what does that do above 2^53?

**Acceptance.** Sixteen cases through the Session 1 harness, each reporting the
seven fields separately. Every divergence is either normalized by a *named*
config field or recorded as a deliberate non-parity boundary.

**Trap.** Case 9. An empty frame joined to a non-empty one has a schema but no
rows, and the two libraries can disagree about the *dtypes* of the result while
agreeing that it is empty. A comparison that short-circuits on row count misses
it entirely.

## Task B3 — The comparison helper, scoped

**Do.** Write the canonical comparison used by this suite. It sorts before
comparing **only** when the join kind promises no order, and normalizes column
names **only** through the config's declared suffix policy.

**Acceptance.** You can name the join kinds whose row order is contractual and
those whose is not, with evidence. A blanket sort is a failed version of this
task — it would hide the ordering half of every finding.

**Note on currency.** In Polars 2.0 the lazy engine defaults to streaming and
row order for joins is explicitly not guaranteed without `maintain_order`. Your
order policy should therefore be written as *"which kinds do we require an order
from"*, not *"which kinds happen to preserve it in 1.36"* — the second answer has
a known expiry date.

## Task B4 — The suffix and coalesce algorithm, closed-book

**Do.** Close every reference. Reproduce the algorithm that decides output
column names for: overlapping non-key columns, key columns under `full` with and
without coalesce, and a caller-supplied suffix that would itself collide.

Then diff against your Stage 1 findings.

**Acceptance.** The third case — a supplied suffix that collides with an
existing column — is handled explicitly. It is the case both libraries handle
differently and neither documents prominently, and a layer that does not consider
it will produce a duplicate column name and fail somewhere else.

---

# Part C — Boundaries

## Task C1 — Decide, in writing, what is out

**Do.** For each, decide **support / translate / explicit-unsupported**:

| feature | decision | reason |
|---|---|---|
| index joins (`left_index=True`) | | |
| `how="cross"` with a predicate | | |
| `indicator=True` | | |
| `validate=` | | |
| non-equi joins from pandas | | |
| key dtype mismatch | | |
| `sort=` on merge | | |

**Acceptance.** Seven decisions, no blanks. `indicator=True` and index joins in
particular get a stated answer, since both are common in captured code and
neither has a Polars analogue.

---

## Answer key

### Task B2 — case 10

An `Int64` left key against a `UInt64` right key resolves through the supertype
rule from Session 4: no integer type holds both ranges, so the comparison happens
in `Float64` and is exact only to 2^53. Keys above that can collide — two
distinct ids becoming one match. This is not a hypothetical for an id column
generated as an unsigned 64-bit value.

The right decision is almost certainly **explicit-unsupported** or a required
explicit cast at the boundary, not a silent join.

### Task B3 — order contracts

`semi` and `anti` return rows of the left frame and preserve its order. `cross`
has a defined nesting order. `inner`, `left`, `right` and `full` have no order
guarantee you should rely on — in 1.36 they often look stable, and in 2.0 the
streaming default makes the absence explicit.

So: never sort before comparing `semi`/`anti`/`cross`; always normalize order for
the other four, and record that as a *deliberate loss of test coverage* rather
than as a neutral convenience.

### Task B4

Polars suffixes only the right side's overlapping columns; pandas suffixes both.
Under `full`, Polars keeps `k` and `k_right` unless `coalesce=True`, and the
uncoalesced `k` is missing right-only keys — Stage 1, Task B3.

---

## Self-check

```bash
Stratum/.venv/bin/python check.py
```

The checker builds the sixteen-case corpus and asserts the divergences the layer
has to absorb, so you can compare your own suite against it after building yours
— not before.
