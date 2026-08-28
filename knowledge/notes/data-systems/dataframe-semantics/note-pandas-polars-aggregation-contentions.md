---
id: note-pandas-polars-aggregation-contentions
type: note
title: "pandas ↔ polars aggregation contentions — semantic divergence map"
created: "2026-08-16"
role: reference
state: evolving
authorship: user
concepts: [concept-dataframe-ops, concept-aggregation, concept-dataframe-semantics]
sources: []
# Reference material for Stratum's GroupByAggregateOp / AggregateOp design.
# Not a Stratum source note: it describes pandas and polars behaviour, so it
# carries no `component:` and drift is not computed against the checkout.
# Regenerate the executable claims with probes/check_all.py.

attachments: [knowledge/attachments/note-pandas-polars-aggregation-contentions/audit_doc.py, knowledge/attachments/note-pandas-polars-aggregation-contentions/audit_tables.py,
  knowledge/attachments/note-pandas-polars-aggregation-contentions/check_all.py, knowledge/attachments/note-pandas-polars-aggregation-contentions/gen_tables.py,
  knowledge/attachments/note-pandas-polars-aggregation-contentions/probe.py, knowledge/attachments/note-pandas-polars-aggregation-contentions/semantics.py,
  knowledge/attachments/note-pandas-polars-aggregation-contentions/semantics2.py,
  knowledge/attachments/note-pandas-polars-aggregation-contentions/verify.py]
---

# pandas ↔ polars aggregation contention map

**Verified against `pandas 3.0.2` and `polars 1.36.0`.** `pyproject.toml` pins
`pandas==3.0.2` but lists `polars` unpinned; the `1.36.0` comes from `uv.lock`. The
worked examples and presence matrices are executable against the pinned environment;
the interpretation and architecture sections are design decisions, not test results.

> In polars 1.36.0, the API is `DataFrame.group_by`; `DataFrame.groupby` does not exist.
> `GroupBy.count` is deprecated and its docstring directs callers to `GroupBy.len`.
>
> *Every version statement in this document is one the installed packages assert about
> themselves. Claims about which release introduced a change are not made, because they
> cannot be checked from the pinned environment.*
>
Fixture used throughout unless stated otherwise:

```
g    x     y
a    1     10
a    null  20
a    3     20
b    4     40
```

---

## The graph

The hierarchy includes node [**(0)**](#0-system-wide) for contentions that sit above
the whole tree because they belong to the data models rather than to any aggregation.

```
                    AGGREGATION
                         |
                    (0) SYSTEM-WIDE ......................  5 contentions
                         |
        +----------------+----------------+
        |                                 |
   (1) AGG_METHODS ...... 3          (2) AGG_FUNCS ....... 2
        |                                 |
   +----+----+                       +----+----+
   |         |                       |         |
(3) DF/Ser  (4) GroupBy           (5) DF/Ser  (6) GroupBy
    ...7        ...9                  ...3        ...6
```

**DFS visit order — and the order of this document:**

```
(0) ──▶ (1) ──▶ (3) ──▶ (4) ──▶ (2) ──▶ (5) ──▶ (6)
 5       3       7       9       2       3       6      =  35
```

Every contention has an immutable `node.n` identifier. The prefix records its filing
category when this catalogue was established — for example, [`4.3`](#43-all-implodes-into-lists-instead-of-reducing) was filed under
`AGG_METHODS → GroupBy` — but it is an identifier, not a graph position to recompute if
the catalogue is later reorganised. Tests and disposition records key off these stable IDs.

### The one thing that is *not* a contention: `P`, the index premise

"pandas has an index, polars doesn't" is labelled **[`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise)** and is **not counted among the
35**, because it fails the test for membership at [(0)](#0-system-wide).

**The membership test for node [(0)](#0-system-wide):** does it show up on a `Series → scalar` reduction —
the smallest possible aggregation, where no container survives? If yes, it's a property
of the data models and belongs at [(0)](#0-system-wide). If no, it's a property of some *container*, and
belongs wherever that container is produced.

```
pd.Series([1,2,3]).sum()  →  6      pl.Series([1,2,3]).sum()  →  6     no index anywhere
pd.Series([1,None]).sum() →  1.0    pl.Series([1,None]).sum() →  1     0.1 / 0.2 visible
pd.Series(['a','b']).sum()→ 'ab'    pl.Series(['a','b']).sum()→ raises 0.3 visible
```

[`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap)–[`0.5`](#05-configurable-reducers-vs-nullary-reducers) all survive that test. The index does not — both sides return a bare scalar.
A pandas `GroupBy` does not expose a result `.index` before aggregation, but it does retain
the indexed source and index-dependent grouping intent. That is why [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) affects both
`GroupingSpec` and `OutputLayout` without becoming a scalar value-policy contention.

So [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) is a **premise**, not a contention: a background fact about pandas' containers
that *generates* five contentions, each with its own separate fix.

| where [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) surfaces | as | fix |
|---|---|---|
| [(3)](#3-agg_methods--dataframe--series) ungrouped reduction | [`3.1`](#31-series-vs-one-row-dataframe) Series vs one-row DataFrame | rank normalisation |
| [(4)](#4-agg_methods--groupby) grouped reduction | [`4.5`](#45-group-keys-index-vs-ordinary-columns) keys in index vs columns | key placement |
| [(4)](#4-agg_methods--groupby) single-column path | [`4.6`](#46-seriesgroupby-has-no-polars-analogue) SeriesGroupBy has no analogue | container choice |
| [(6)](#6-agg_funcs--groupby) list spec | [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce) MultiIndex columns can't be produced | output-label normalisation |
| [(6)](#6-agg_funcs--groupby) named agg | [`6.5`](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence) alias may collide with a key | namespace merge |

Fixing [`3.1`](#31-series-vs-one-row-dataframe) does not fix [`4.5`](#45-group-keys-index-vs-ordinary-columns). Listing [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) as a contention would double-count all five
and imply a single fix that does not exist.

### `P` is not purely an output concern

The index is not merely a property of what `AggregateOp` produces. It also determines
grouping intent before any aggregation happens:

```
d.groupby(level=0)          # group BY the index, not by a column
d.groupby(external_series)  # aligned by index LABEL, not by position
d.groupby(lambda k: ...)    # callable evaluated against index keys
d.groupby(pd.Grouper(...))  # DatetimeIndex resampling
```

Verified: an external `pd.Series` grouper with deliberately reversed labels pairs rows by
label, not position. polars can accept an external `Series` as a positional grouping
expression, but it does not reproduce pandas' index-label alignment. Index levels,
callable index groupers, and `pd.Grouper` likewise require distinct `GroupingSpec`
variants and explicit plan rewrites rather than a direct `group_by` argument passthrough.

**So the correct statement is:** `GroupbyOp` never has to *materialise* an index, but it
must **preserve index-dependent grouping intent and alignment semantics**. That is a
`GroupingSpec` concern, not an `OutputLayout` one, and it is the strongest argument that
the two need to be separate contracts rather than one node with a flag.

### How to read the graph

The DFS sequence is a **filing and reading order**, not an implementation dependency
order. It keeps each contention in one place, but several decisions cut horizontally
across the tree:

- `ValuePolicy` affects every reducer surface.
- Reducer semantics established at [(1)](#1-agg_methods)/(3) also constrain expression lowering at [(4)](#4-agg_methods--groupby)/(6).
- Grouping configuration from [(4)](#4-agg_methods--groupby) applies equally when aggregation is expressed through
  `.agg()` at [(6)](#6-agg_funcs--groupby).
- The index premise [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) affects grouping intent as well as output rank, key placement,
  labels, and alias collisions ([`3.1`](#31-series-vs-one-row-dataframe), [`4.5`](#45-group-keys-index-vs-ordinary-columns), [`4.6`](#46-seriesgroupby-has-no-polars-analogue), [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce), [`6.5`](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence)).

The normative dependency order is therefore a separate DAG, defined in
[§ Implementation order](#implementation-order). Adding an edge to that DAG does not
require duplicating a contention in this taxonomy.

### Contention index, in DFS order

| # | Contention |
|---|---|
| *([`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise))* | *index premise — not a contention; generates [`3.1`](#31-series-vs-one-row-dataframe) [`4.5`](#45-group-keys-index-vs-ordinary-columns) [`4.6`](#46-seriesgroupby-has-no-polars-analogue) [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce) [`6.5`](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence)* |
| [**0.1**](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap) | NumPy-backed pandas `NaN` semantics vs polars' null bitmap |
| [**0.2**](#02-inferred-numpy-backed-integer-data-promotes-to-float-under-nulls) | Inferred NumPy-backed integer data promotes to float under nulls |
| [**0.3**](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) | Reducer dtype domains vary by reducer and execution surface |
| [**0.4**](#04-numeric_only-has-no-polars-parameter) | `numeric_only` has no polars parameter |
| [**0.5**](#05-configurable-reducers-vs-nullary-reducers) | Configurable reducers vs nullary reducers |
| [**1.1**](#11-renames-hide-semantic-changes) | Renames hide semantic changes (and matching names can too) |
| [**1.2**](#12-no-passthrough-argument-surface-despite-a-small-overlap) | No passthrough argument surface despite a small overlap |
| [**1.3**](#13-the-direct-method-set-is-not-closed) | The direct-method set is not closed |
| [**3.1**](#31-series-vs-one-row-dataframe) | Series vs one-row DataFrame |
| [**3.2**](#32-nunique-counts-different-units-and-nulls) | `nunique` counts different units *and* nulls |
| [**3.3**](#33-size-is-a-property-and-it-counts-cells) | `size` is a property, and counts cells |
| [**3.4**](#34-quantile-interpolation-default-differs-and-so-does-q-arity) | `quantile`: interpolation default differs; `q`-arity differs |
| [**3.5**](#35-describe-differs-in-shape-and-row-set) | `describe` differs in shape and row set |
| [**3.6**](#36-firstlast-three-way-absence-asymmetry) | `first`/`last`: three-way absence asymmetry |
| [**3.7**](#37-skew-and-kurtosis-use-different-bias-conventions) | `skew`/`kurtosis` use different bias conventions |
| [**4.1**](#41-count-names-a-different-operation) | `count` names a different operation |
| [**4.2**](#42-size--len-series-vs-dataframe) | `size`/`value_counts` rank depends on `as_index` |
| [**4.3**](#43-all-implodes-into-lists-instead-of-reducing) | `all` implodes into lists instead of reducing |
| [**4.4**](#44-firstlast-null-contract-is-inverted) | `first`/`last` null contract is inverted |
| [**4.5**](#45-group-keys-index-vs-ordinary-columns) | Group keys: index vs ordinary columns |
| [**4.6**](#46-seriesgroupby-has-no-polars-analogue) | `SeriesGroupBy` has no polars analogue |
| [**4.7**](#47-sort-and-maintain_order-are-not-the-same-knob) | `sort` and `maintain_order` are not the same knob |
| [**4.8**](#48-pandas-silently-drops-rows-with-null-keys) | pandas silently drops rows with null keys |
| [**4.9**](#49-unobserved-categorical-groups) | Unobserved categorical groups |
| [**2.1**](#21-aggregate-does-not-exist-in-polars) | `aggregate` does not exist in polars |
| [**2.2**](#22-a-specification-is-not-an-expression) | A specification is not an expression |
| [**5.1**](#51-the-node-does-not-exist-in-polars-at-all) | The node does not exist in polars at all |
| [**5.2**](#52-the-specs-value-controls-the-result-type) | The spec's *value* controls the result *type* |
| [**5.3**](#53-axis-is-method-specific-on-ungrouped-calls-and-absent-from-grouping) | `axis` is surface-specific and absent from grouping |
| [**6.1**](#61-a-bare-string-names-a-column-not-a-function) | A bare string names a column, not a function |
| [**6.2**](#62-list-specs-need-a-multiindex-polars-cant-produce) | List specs need a MultiIndex polars can't produce |
| [**6.3**](#63-dict-specs-are-rejected-outright) | Dict specs are rejected outright |
| [**6.4**](#64-a-bare-callable-is-not-an-expression--but-callables-can-be-embedded) | Bare Python callables require explicit UDF expressions |
| [**6.5**](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence) | Named aggregation: syntactic alignment, semantic divergence |
| [**6.6**](#66-seriesgroupby-accepts-a-different-spec-grammar-from-dataframegroupby) | `SeriesGroupBy` accepts a different spec grammar |

This index is navigational. Detectability, backend disposition, output effects, and test
coverage are separate fields in the normative disposition matrix; they are not collapsed
into one “severity” score.

---

# (0) SYSTEM-WIDE

*Cross-cutting contentions that can affect every branch of the aggregation tree. They are
listed once here rather than repeated for every reducer and surface.*

> Premise [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) is defined once above. Its grouping-input effects belong to `GroupingSpec`;
> its five result manifestations belong to `OutputLayout`. It is not counted in node [(0)](#0-system-wide).

## 0.1 NumPy-backed pandas `NaN` semantics vs polars' null bitmap

**What happens.** A group of only missing values reduces to `NaN` under pandas `mean()`
and `null` under polars `mean()`. They look similar in a repr; they are not the same
thing.

**Why.** On a NumPy-backed pandas float column, `NaN` is both a floating-point value and
the conventional missing sentinel. Nullable extension and Arrow-backed pandas dtypes can
represent missingness separately, so this is not universal to every pandas dtype. polars
uses a validity bitmap: `null` (absent) and `NaN` (a present floating-point value) are
orthogonal and can both occur in one column.

**Consequence.** *Most* pandas reducers take `skipna=`, but `count`, `size`, `nunique`,
`quantile`, `describe`, and `value_counts` do not on `DataFrameGroupBy`. Polars has no
general `skipna` reducer keyword. `skipna=True` is equivalent only after a declared input
policy maps pandas-missing `NaN` values to polars `null`, or after the generated expression
filters both representations as required. Otherwise, for example,
`pd.Series([1.0, NaN]).sum()` is `1.0` while the corresponding polars sum is `NaN`.

`skipna=False` is still expressible: generate a conditional aggregate that returns the
canonical missing value when any relevant missing value is present and otherwise evaluates
the reducer. It is an expression rewrite, not an unsupported capability.

Specific polars reducers do expose a null-control parameter: `pl.Series.all`,
`pl.Series.any`, `GroupBy.first`, and `GroupBy.last` all expose `ignore_nulls`. The two
sets barely overlap, the polars parameter is spelled
differently, and that on `first`/`last` it defaults the opposite way — see [`4.4`](#44-firstlast-null-contract-is-inverted).
`pl.GroupBy.all` notably does *not* take it.

## 0.2 Inferred NumPy-backed integer data promotes to float under nulls

**What happens.** Group `a` has `x = [1, null, 3]`. pandas grouped `sum()` returns `4.0`
typed `float64`; polars returns `4` typed `Int64`. Counters diverge too — pandas
`count()` gives `int64`, polars `len()` gives `UInt32`.

**Why.** This is [`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap) showing up in the type system — but only on the *default*
storage path. A NumPy-backed `int64` column has no NaN bit pattern, so when the
constructor infers dtype from data containing `None` it promotes to `float64`. polars
keeps the values in an `Int64` array and marks position 1 invalid in the bitmap, so the
dtype never changes. `UInt32` is the index dtype of this Polars build
(`pl.get_index_type()`); a big-index build may use `UInt64`.

**Important scope limit.** This is *not* a law about pandas. pandas' nullable extension
dtypes hold missing values without promoting:

```
pd.Series([1,None,3])                    grouped sum → 4.0   float64   (inferred)
pd.Series([1,None,3], dtype="Int64")     grouped sum → 4     Int64     (nullable)
```

So the contention is between polars and *NumPy-backed pandas*, which is what you get by
default. If Stratum can require nullable/Arrow-backed dtypes at the boundary, this one
mostly dissolves — which makes it a storage-policy decision rather than a translation
rule.

**Consequence.** Reducer-name translation alone does not fix this divergence. It requires
an explicit dtype policy and, where necessary, input or output casting.

## 0.3 Reducer dtype domains vary by reducer and execution surface

Unsupported- and coercible-dtype behaviour is not one pandas policy versus one Polars
policy. It is a matrix of reducer × dtype × execution surface. Representative string
results on the pinned fixture are:

| call on a string column | pandas | polars |
|---|---|---|
| eager `DataFrame.sum()` | concatenates → `'aaab'` | returns `null` |
| `Series.sum()` | concatenates | raises `InvalidOperationError` |
| expression `select(col.sum())` | n/a | raises `InvalidOperationError` |
| grouped `sum()` / grouped sum expression | concatenates → `'pq'` | raises `InvalidOperationError` |
| eager `DataFrame.mean()` | raises `TypeError` | returns `null` |
| `Series.mean()` | raises `TypeError` | returns `None` |
| expression `select(col.mean())` | n/a | raises `InvalidOperationError` |
| grouped `mean()` / grouped mean expression | raises `TypeError` | returns `null` |

These are observed API contracts, not evidence for one universal dispatch mechanism.
In particular, Polars' eager `DataFrame` method cannot predict the behaviour of the
expression emitted by the spec→expression compiler. Backend capability must therefore be
recorded per reducer, dtype class, and lowering surface.

The same contention is visible outside strings. pandas `Series.any()`/`all()` accept
numeric truthiness, whereas Polars requires a Boolean Series and raises `SchemaError` on
an integer Series. Reducer presence alone therefore does not establish a shared dtype
domain.

**The dangerous cell** is pandas `sum` concatenating strings: no error, no warning, a
plausible-looking result. If Stratum routes a plan to the pandas backend, a string
column changes the answer rather than failing.

## 0.4 `numeric_only` has no polars parameter

**What happens.** pandas offers `mean(numeric_only=True)` to sidestep [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) — it drops
non-numeric columns instead of raising. polars has no such parameter on any reducer.

**Why.** In polars the equivalent is schema-aware measure selection, expressed either as
a projection on an ungrouped frame or inside the generated aggregation expressions.

**Consequence for the split.** On a grouped path, a pre-projection must preserve grouping
keys; the safer lowering is usually to retain the keys and generate expressions only for
eligible measure columns. pandas includes Boolean columns in common `numeric_only=True`
reductions, while `polars.selectors.numeric()` excludes Boolean, so the selector policy
must include Boolean explicitly when pandas compatibility is required. This contention
owns *which columns participate*; [`0.5`](#05-configurable-reducers-vs-nullary-reducers) owns reducer configuration semantics and [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap)
owns the backend signature mapping.

## 0.5 Configurable reducers vs nullary reducers

**What happens.** pandas reducers are configurable objects with a wide keyword surface:
`skipna`, `min_count`, `numeric_only`, `ddof`, `engine`, `engine_kwargs`. polars
reducers are almost all **nullary** — `GroupBy.sum()` takes no arguments at all.

**Why.** Two philosophies about where configuration lives. In pandas, one method name
covers a family of behaviours selected by keyword. In polars, configuration means
*choosing a different expression* — you compose a different tree rather than passing a
flag.

**Consequence.** No general passthrough strategy exists. Each pandas keyword
becomes a plan rewrite (`numeric_only` → measure selection), a different expression
(`min_count` → a conditional), or an explicit `NotImplementedError`. See [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap).

> **Closing [(0)](#0-system-wide).** [`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap) + [`0.2`](#02-inferred-numpy-backed-integer-data-promotes-to-float-under-nulls) together mean two physical impls of the same logical op
> cannot be expected to return equal *values or dtypes*, independently of any container
> question. These policies must be declared before backend lowering. The container and
> label contract generated by [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) is owned separately by `GroupingSpec` and
> `OutputLayout`.

---

# (1) AGG_METHODS

*Is `_AGG_METHODS` a well-formed abstraction? These three contentions test whether one
shared direct-method abstraction can cover the tracked reducers and surfaces.*

## 1.1 Renames hide semantic changes

Three of the fourteen `_AGG_METHODS` names require renaming: `prod`, `size`, and
`nunique`. Nearby reducers add `kurt`, `idxmin`, and `idxmax`; `skew` keeps its spelling
but changes semantics, and `sem` has no direct Polars method.

| pandas | polars | note |
|---|---|---|
| `prod` | `product` | operation identity agrees for supported numeric inputs after `ValuePolicy` |
| `skew` | `skew` | *same name*, different bias convention ([`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions)) |
| `nunique` | `n_unique` | rename **and** semantic divergence ([`3.2`](#32-nunique-counts-different-units-and-nulls)) |
| `size` | `len` | rename **and** different unit **and** different container ([`3.3`](#33-size-is-a-property-and-it-counts-cells), [`4.2`](#42-size--len-series-vs-dataframe)) |
| `kurt` | `kurtosis` | rename **and** different bias convention ([`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions)) |
| `idxmin` / `idxmax` | `arg_min` / `arg_max` | rename **and** label-vs-position divergence |
| `sem` | *(none)* | no direct polars method; lower to an explicit formula |

**Why the renames aren't harmless.** Only `prod → product` is a name-only mapping once
the shared value policy has handled nulls, `NaN`, and dtypes. `nunique → n_unique`,
`size → len`, `kurt → kurtosis`, and `idxmin`/`idxmax → arg_min`/`arg_max` all require
additional semantic or layout handling. `idxmin`, for example, returns an index label in
pandas while `arg_min` returns a positional integer.

**The rule:** a name-mapping table is necessary but never sufficient. Every entry needs
a semantic flag beside the new name — and `skew` shows the converse failure: an
*identical* name whose semantics diverge ([`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions)). Neither matching nor mismatching names
carry information on their own.

## 1.2 No passthrough argument surface despite a small overlap

The same reducer on the grouped surface:

```
pandas  GroupBy.sum(numeric_only=False, min_count=0, skipna=True,
                    engine=None, engine_kwargs=None)
polars  GroupBy.sum()
```

Some keyword names overlap, but their domains, defaults, and output effects still need
per-reducer rules:

| shared keyword | where | note |
|---|---|---|
| `ddof` | `std`, `var` — DF/Series direct methods | no direct polars `GroupBy.std/var`; grouped expressions support both |
| `interpolation` | `quantile` — DF/Series and GroupBy | shared name; defaults and accepted value sets differ ([`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity)) |
| `percentiles` | `DataFrame.describe`, `Series.describe` | shared name; the result contract still differs ([`3.5`](#35-describe-differs-in-shape-and-row-set)) |
| `normalize`, `sort` | `Series.value_counts` | shared names; defaults, null handling, and result containers differ |

Everything else must be translated or rejected. Although `interpolation` is shared by
name, the quantile-value parameter is not: pandas calls it `q` and accepts a scalar or
vector, while Polars calls it `quantile`, accepts one scalar, and raises `TypeError` on a
list. This loud failure is part of [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity).

The one place polars *does* expose a control it disagrees twice over: polars
`first(ignore_nulls=False)` vs pandas `first(skipna=True)` — different name, **opposite
default**. See [`4.4`](#44-firstlast-null-contract-is-inverted).

**Consequence.** The `AggregateOp` field carrying aggregation arguments cannot be a
passthrough dict; every key needs an explicit translation rule or explicit rejection.

## 1.3 The direct-method set is not closed

`_AGG_METHODS` is written as if there were a shared universal set of reducer names both
libraries expose. There isn't. Of the 24 aggregation concepts tracked in the tables
below, pandas' `DataFrameGroupBy` exposes **23** and polars' `GroupBy` exposes **12**.
The intersection is smaller than either — and per [`4.1`](#41-count-names-a-different-operation) and [`4.3`](#43-all-implodes-into-lists-instead-of-reducing), **membership in the
intersection does not imply agreement**, because two shared names denote different
operations.

**Practical consequence.** `_AGG_METHODS` is doing two jobs: recognising a call during IR
construction, and implying it can be executed on any backend. Separate them. Recognition
can stay permissive; executability must be a per-backend property checked at plan time.

---

# (3) AGG_METHODS → DataFrame / Series

*Direct reducers on an ungrouped frame or series. First child of [(1)](#1-agg_methods).*

## Presence table

Legend: `M` callable method · `attr` property (not callable) · `.` absent · **bold** = present in only one library on that surface.
The **gap** column names the surface where the method is *missing*, not where it exists:
"absent on pl.DF" means pandas has it on `DataFrame` and polars does not.

| concept | pandas | polars | pd.DF | pd.Ser | pl.DF | pl.Ser | gap | name≠ | sig≠ | semantic≠ |
|---|---|---|---|---|---|---|---|---|---|---|
| sum | `sum` | `sum` | M | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| mean | `mean` | `mean` | M | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| min | `min` | `min` | M | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | — |
| max | `max` | `max` | M | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | — |
| median | `median` | `median` | M | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| std | `std` | `std` | M | M | M | M | — | — | partial (`ddof`) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| var | `var` | `var` | M | M | M | M | — | — | partial (`ddof`) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| count | `count` | `count` | M | M | M | M | — | — | ✔ | ✔ [`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap) for genuine `NaN` unless normalised |
| prod | `prod` | `product` | M | M | M | M | — | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| nunique | `nunique` | `n_unique` | M | M | M | M | — | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ **[`3.2`](#32-nunique-counts-different-units-and-nulls)** |
| size | `size` | `len` | **attr** | **attr** | **.** | M | ✔ [`3.3`](#33-size-is-a-property-and-it-counts-cells) | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ **[`3.3`](#33-size-is-a-property-and-it-counts-cells)** |
| quantile | `quantile` | `quantile` | M | M | M | M | — | — | ✔ | ✔ **[`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity)** |
| describe | `describe` | `describe` | M | M | M | M | — | — | ✔ | ✔ **[`3.5`](#35-describe-differs-in-shape-and-row-set)** |
| first | `first` | `first` | **.** | **.** | **.** | **M** | ✔ [`3.6`](#36-firstlast-three-way-absence-asymmetry) | — | — | n/a |
| last | `last` | `last` | **.** | **.** | **.** | **M** | ✔ [`3.6`](#36-firstlast-three-way-absence-asymmetry) | — | — | n/a |
| sem | `sem` | — | **M** | **M** | **.** | **.** | ✔ pandas-only | ✔ no name | n/a | n/a |
| any | `any` | `any` | **M** | M | **.** | M | ✔ absent on pl.DF | — | ✔ | ✔ dtype domain ([`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface)) |
| all | `all` | `all` | **M** | M | **.** | M | ✔ absent on pl.DF | — | ✔ | ✔ dtype domain ([`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface)) |
| skew | `skew` | `skew` | **M** | M | **.** | M | ✔ absent on pl.DF | — | ✔ | ✔ **[`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions)** |
| kurt | `kurt` | `kurtosis` | **M** | M | **.** | M | ✔ absent on pl.DF | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ **[`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions)** |
| idxmin | `idxmin` | `arg_min` | **M** | M | **.** | M | ✔ absent on pl.DF | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ label vs position |
| idxmax | `idxmax` | `arg_max` | **M** | M | **.** | M | ✔ absent on pl.DF | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ label vs position |
| mode | `mode` | `mode` | **M** | M | **.** | M | ✔ absent on pl.DF | — | ✔ | ✔ padding/null defaults |
| value_counts | `value_counts` | `value_counts` | **M** | M | **.** | M | ✔ absent on pl.DF | — | ✔ | ✔ row tuples/container/defaults |

**The shape of this table.** The `pl.DF` direct-method surface is narrower than the
pandas DataFrame surface, and method presence does not imply a common output rank
(`describe` is multi-row). Most missing DataFrame methods still exist on `pl.Series`,
but `sem` does not; pandas also lacks the pinned `first`/`last` methods and exposes
`size` as a property. The exact nine-method DataFrame gap and its distinct lowerings are
listed next.

**Nine concepts are present on `pandas.DataFrame` and absent on `pl.DataFrame`** —
`sem`, `any`, `all`, `skew`, `kurt`, `idxmin`, `idxmax`, `mode`, `value_counts`. Eight
still exist on `pl.Series`; only `sem` is missing from both polars surfaces.

They do not share one lowering. `sem`, `any`, `all`, `skew`, `kurt`, `idxmin`, and
`idxmax` can be built from schema-aware expressions and the declared value policy.
`DataFrame.mode()` additionally requires padding unequal per-column mode counts; a naive
`select(pl.all().mode())` can raise `ShapeError`. `DataFrame.value_counts()` counts
complete row tuples, not values independently per column, so its structural lowering is
`group_by(all payload columns).len()` plus pandas-compatible sorting, null, naming, and
output-layout rules.

## 3.1 Series vs one-row DataFrame

**What happens.** pandas `DataFrame.sum()` → `Series` shape `(3,)`. polars
`DataFrame.sum()` → `DataFrame` shape `(1, 3)`. But pandas `Series.sum()` → scalar, and
polars `Series.sum()` → scalar too.

**The point:** the *Series* leg matches and the *DataFrame* leg does not. Direct
consequence of [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) — pandas can express "one value per column" as a `Series` indexed
by column name because it has an index to put names in. polars' direct DataFrame reducer
keeps those names as columns, so its native result is a one-row frame.

**Consequence.** One operation produces results of different *rank* across backends:
pandas drops a dimension, polars keeps it. Any downstream op that indexes into the
result has to branch.

## 3.2 `nunique` counts different units *and* nulls

Two independent divergences behind one rename, which is why this is easy to get wrong.

**Divergence 1 — the unit, at DataFrame level.**

```
pdf.nunique()      →  g: 2, x: 3, y: 3      # distinct values PER COLUMN, a Series
pldf.n_unique()    →  4                     # distinct ROWS, a scalar
```

Not the same operation with a different output shape — they count different things.
`DataFrame.nunique()` is a column-wise reduction; `DataFrame.n_unique()` is whole-table
cardinality (polars' `len(df.unique())`). The pandas equivalent of polars' behaviour is
`len(df.drop_duplicates())`.

**Divergence 2 — missing-value handling, at Series level.**

```
pd.Series([1, None, 1]).nunique()   →  1     # dropna=True by default
pl.Series([1, None, 1]).n_unique()  →  2     # null counted as a distinct value
```

Here the *unit* agrees but the treatment of missing does not. pandas defaults
`dropna=True`; polars has no such parameter and counts `null` as a distinct value. The
same policy decision is needed for a present floating-point `NaN`: pandas drops it by
default, while polars counts it as a value unless the boundary normalises it.

**Consequence.** To reproduce pandas' Series default in polars, filter the missing
representations selected by `ValuePolicy` before `n_unique`; to reproduce polars in
pandas, use `dropna=False` after deciding how `NaN` and `null` correspond. At DataFrame
level the two methods count different units regardless of missing-value policy.

## 3.3 `size` is a property, and it counts cells

Three problems stacked on one name.

**It isn't callable.** `pd.DataFrame.size` is a **property**. `pdf.size` works;
`pdf.size()` raises `TypeError: 'int' object is not callable`. But on the *grouped*
surface `gb.size()` **is** a method — so `size` is a property on one surface and a
method on another, within pandas itself. Since `_AGG_METHODS` is consumed by
`MethodCallOp` matching, a `size` entry only ever matches the grouped case; the
DF/Series case never arrives as a method call at all.

**It counts a different unit.** `pdf.size` is `rows × cols` = `12` on our fixture,
inherited from NumPy's `ndarray.size`; grouped `size()` counts rows per group.

**polars has no `DataFrame.len()` at all.** `hasattr(pl.DataFrame, 'len')` is `False`.
Row count is `df.height` or `len(df)`. Only `pl.Series.len()` exists as a method, and it
returns `3` for `[1, None, 3]` — it counts nulls, unlike `Series.count()` which returns
`2`.

**Net effect.** There is no direct method-to-method mapping on this surface. pandas
`DataFrame.size` lowers structurally to `height × width`; pandas `Series.size` lowers to
`len(series)`. It should not share the grouped `size → len` rule merely because the name
is the same.

## 3.4 `quantile`: interpolation default differs, and so does `q`-arity

```
pd.Series([1,2,3,4]).quantile(0.5)            →  2.5    # interpolation='linear'
pl.Series([1,2,3,4]).quantile(0.5)            →  3.0    # interpolation='nearest'
pl.Series([1,2,3,4]).quantile(0.5, 'linear')  →  2.5    # agrees once forced
```

**Why it's dangerous.** Both signatures have an `interpolation` parameter, but their
defaults and accepted value sets differ. The common values include `linear`, `lower`,
`higher`, `midpoint`, and `nearest`; pandas 3.0.2 additionally accepts methods such as
`hazen`, while polars additionally accepts `equiprobable`. On the default call there is
no error or warning and both answers look plausible.

**Second divergence, this one loud.** The arity of `q` also differs:

```
pd.Series([1,2,3,4]).quantile([0.25, 0.75])  →  Series of two values
pl.Series([1,2,3,4]).quantile([0.25, 0.75])  →  TypeError
```

pandas accepts a vector and changes its return rank accordingly — another instance of
[`5.2`](#52-the-specs-value-controls-the-result-type), and further evidence that direct-reducer output typing depends on *arguments*, not
just the method name. Polars takes one float. This cannot be passed through directly: the
lowerer must expand it into scalar quantile expressions and reconstruct the requested
layout, or reject it when that contract cannot be reproduced.

**Disposition.** Force an explicit common interpolation value when the source omitted
one. A source-only value requires a proven rewrite or an explicit capability error; it
cannot be passed through by name.

## 3.5 `describe` differs in shape and row set

| | pandas | polars |
|---|---|---|
| shape on our fixture | `(8, 2)` | `(9, 4)` |
| statistic names live in | the **index** | a `statistic` **column** |
| columns included | numeric only | **all**, including strings |
| extra rows | — | `null_count` |
| percentile method | linear ([`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity)) | nearest ([`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity)) |

**Why it remains a separate regression case.** Statistic placement is [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise), string-column
inclusion is [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface), and percentile values are [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity); `describe` composes those policies
into one public output contract. Polars also documents the result of `DataFrame.describe`
as unstable and unsuitable as a programmatic schema contract. Treat [`3.5`](#35-describe-differs-in-shape-and-row-set) as a compound
conformance scenario, not an independent root cause.

## 3.6 `first`/`last`: three-way absence asymmetry

```
hasattr(pd.DataFrame, 'first')   →  False
hasattr(pd.Series,    'first')   →  False
hasattr(pl.DataFrame, 'first')   →  False
hasattr(pl.Series,    'first')   →  True
```

**What this means.** In pandas 3.0.2 there is nothing to translate *from* on this
surface: neither `DataFrame.first` nor `Series.first` exists. polars' `Series.first()` is
a positional reducer with no pandas counterpart here, and polars has no
`DataFrame.first` either.

**Consequence.** The only translation question on this surface is what to do with
polars' `Series.first()`, which has no direct pandas counterpart in the pinned version.

## 3.7 `skew` and `kurtosis` use different bias conventions

**What happens.** Same data, same method, no error, different number:

```
v = [1, 2, 3, 4, 10]

pandas  pd.Series(v).skew()   →  1.697        polars  pl.Series(v).skew()      →  1.138
pandas  pd.Series(v).kurt()   →  3.152        polars  pl.Series(v).kurtosis()  → -0.212

polars  pl.Series(v).skew(bias=False)      →  1.697   ← matches pandas
polars  pl.Series(v).kurtosis(bias=False)  →  3.152   ← matches pandas
```

**Why.** polars defaults `bias=True` (the raw sample moment). pandas applies the
bias-corrected estimator and exposes no `bias` parameter. To reproduce pandas defaults,
emit `skew(bias=False)` and `kurtosis(fisher=True, bias=False)` in polars. Non-default
Polars requests for `bias` or `fisher` cannot be passed through to pandas by keyword.

**Why it belongs here and not at [`1.1`](#11-renames-hide-semantic-changes).** `kurt`→`kurtosis` looks like a rename and
`skew`→`skew` looks like an exact match; both are wrong in the same way, and the shared
root cause is the bias convention, not the spelling. Treating it as a rename problem
would have produced a name table that silently returns wrong numbers.

**Scope check.** The divergence does *not* extend to `std`/`var` on this fixture: both
default to `ddof=1` and agree. Polars has no direct `GroupBy.skew()` or
`GroupBy.kurtosis()` methods, but grouped forms work through expressions such as
`group_by(...).agg(pl.col("x").skew(bias=False))`. The same correction is therefore
required when lowering grouped pandas reducers.

---

# (4) AGG_METHODS → GroupBy

*Direct reducers on a grouped object. This is a sibling of [(3)](#3-agg_methods--dataframe--series) in the filing taxonomy,
but it consumes the same reducer and value policies during implementation.*

**polars `GroupBy` exposes exactly 17 public members:**

```
agg  all  count(deprecated)  first  having  head  last  len
map_groups  max  mean  median  min  n_unique  quantile  sum  tail
```

That's the entire surface — 17 members, of which 12 are reducers (`agg`, `having`,
`head`, `map_groups`, `tail` are not). pandas' `DataFrameGroupBy` exposes **23** of the
24 concepts in the table below, plus a large transform/window surface on top.

## Presence table

| concept | pandas | polars | pd.DFGroupBy | pd.SeriesGroupBy | pl.GroupBy | gap | name≠ | sig≠ | semantic≠ |
|---|---|---|---|---|---|---|---|---|---|
| sum | `sum` | `sum` | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| mean | `mean` | `mean` | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| min | `min` | `min` | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | — |
| max | `max` | `max` | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | — |
| median | `median` | `median` | M | M | M | — | — | ✔ [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | ✔ [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) |
| **count** | `count` | `count` | M | M | **M (deprecated)** | — | ✔ | ✔ | ✔ **[`4.1`](#41-count-names-a-different-operation)** — *different operation* |
| **size** | `size` | `len` | M | M | M | — | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ (`name=`) | ✔ **[`4.2`](#42-size--len-series-vs-dataframe)** |
| **all** | `all` | `all` | M | M | M | — | — | ✔ | ✔ **[`4.3`](#43-all-implodes-into-lists-instead-of-reducing)** — *different operation* |
| **first** | `first` | `first` | M | M | M | — | — | ✔ | ✔ **[`4.4`](#44-firstlast-null-contract-is-inverted)** |
| **last** | `last` | `last` | M | M | M | — | — | ✔ | ✔ **[`4.4`](#44-firstlast-null-contract-is-inverted)** |
| nunique | `nunique` | `n_unique` | M | M | M | — | ✔ [`1.1`](#11-renames-hide-semantic-changes) | ✔ | ✔ [`3.2`](#32-nunique-counts-different-units-and-nulls) |
| quantile | `quantile` | `quantile` | M | M | M | — | — | ✔ | ✔ [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity) |
| **std** | `std` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| **var** | `var` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| **prod** | `prod` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| **sem** | `sem` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| any | `any` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| skew | `skew` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| kurt | `kurt` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| idxmin | `idxmin` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| idxmax | `idxmax` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| value_counts | `value_counts` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| describe | `describe` | — | M | M | **.** | ✔ pandas-only | — | n/a | n/a |
| mode | — | — | **.** | **.** | **.** | absent both | — | — | — |

**Coverage of the 14 names in `_AGG_METHODS`:**

| bucket | names | n |
|---|---|---|
| direct method, same reducer concept; `ValuePolicy`/defaults still apply | `sum mean min max median first last` | 7 |
| direct method, renamed and/or semantically off | `size`→`len` ([`4.2`](#42-size--len-series-vs-dataframe)), `nunique`→`n_unique` ([`3.2`](#32-nunique-counts-different-units-and-nulls)) | 2 |
| **same name, different operation** — the trap | `count` ([`4.1`](#41-count-names-a-different-operation)) | 1 |
| no direct method — lower to `agg(pl.col(c).<op>())` | `std var prod sem` | 4 |

The last four aren't *impossible* — `pl.col("x").std()` is a fine expression. They just
have no **direct `GroupBy` method**, so they can't be translated by a name table; they
force the grouped-reducer path to fall through to the `.agg()` path. A control-flow
difference in your impl, not a lookup difference.

## 4.1 `count` names a different operation

```
pandas   gb.count()   →   x  y          # one column per input column
                       a  2  3          # non-null values in each
                       b  1  1

polars   gb.count()   →   g   count     # ONE column
                       a   3            # rows in each group
                       b   1
```

Plus polars emits `DeprecationWarning: GroupBy.count was renamed; use GroupBy.len`.

**Why this is the sharpest example in the document.** The same name across surfaces:

| | pandas | polars |
|---|---|---|
| `Series.count()` | excludes pandas-missing `NaN` | excludes `null`, but counts present `NaN` — agree only after missing-value normalisation |
| `DataFrame.count()` | same pandas rule per column | same polars rule per column — same qualification |
| `GroupBy.count()` | non-null **per column** | **rows** per group ❌ **disagree** |

**polars flips the meaning of its own method between surfaces.** That's why this cannot
be resolved up at node [(1)](#1-agg_methods) — the correct translation depends on which surface you're on,
which is exactly the argument for splitting the node.

**And there's no direct replacement.** No polars `GroupBy` method reproduces pandas'
per-column non-null count; you must lower to `agg(pl.col(c).count() for c in cols)`. So
`count`, despite sitting in the "present on both" bucket, really belongs with
`std`/`var`/`prod`/`sem`.

## 4.2 `size` → `len`, Series vs DataFrame

**What happens.** pandas `gb.size()` returns a **`Series`** when `as_index=True` (the
default), because the result is one number per group with no column dimension left.
polars `gb.len()` returns a `DataFrame` with the key column plus a `len` column,
renameable via `len(name="...")`.

**Two qualifications that matter.** `size` is *not* the only Series-returning grouped
reducer, and its return type is *not* fixed:

```
gb.size()                        → Series        gb.value_counts()                → Series
gb.size()   as_index=False       → DataFrame     gb.value_counts() as_index=False → DataFrame
```

So the rule is not "`size` is special"; it is **"container rank on the pandas side is a
function of `as_index` and of which reducer collapses the column dimension."** That is a
property of `OutputLayout`, not of the method name — which is why [`4.5`](#45-group-keys-index-vs-ordinary-columns) and this
contention have to be decided together.

**Why it matters.** Any code assuming "grouped reducer → `DataFrame`" on the pandas side
breaks on `size` and `value_counts`. And the polars side needs a decision your pandas
call never had to make: what to call the output column.

## 4.3 `all` implodes into lists instead of reducing

**The most dangerous single entry in the map**, because it fails silently.

```
input:   g=a, b=[True, False]

pandas   gb.all()   →   b
                     a  False              # boolean AND per column

polars   gb.all()   →   g   b
                     a   [true, false]     # list[bool] — every value, imploded
```

**Why.** In polars, `GroupBy.all()` means "aggregate **all the values** of each group
into a list" — the identity aggregation, collecting rather than reducing. The collision
with boolean-AND is an accident of English. polars' boolean AND exists, but as an
expression: `agg(pl.col("b").all())`.

**Why it's worse than a missing method.** A missing method raises immediately. This
returns a well-formed `DataFrame` with the expected row count and column name; only the
dtype changes, `Boolean` → `List(Boolean)`. If nothing downstream type-checks, the wrong
answer propagates. Note `pl.Series.all()` **is** the boolean reducer — so like `count`,
polars flips this name's meaning between its own surfaces.

## 4.4 `first`/`last` null contract is inverted

```
group a, x = [null, 10, 20, null]

pandas   gb.first()                    →  10      # skipna=True by default
polars   gb.first()                    →  null    # ignore_nulls=False by default
polars   gb.first(ignore_nulls=True)   →  10      # agrees once forced
```

**Why.** pandas and polars choose different defaults. The parameters have the same
polarity — `skipna=True` and `ignore_nulls=True` both mean "ignore missing values" — but
pandas defaults to `True` while polars defaults to `False`.

**Status.** **Bridgeable** — polars 1.36.0 exposes `ignore_nulls` on `GroupBy.first`
and `GroupBy.last`. This is a translation rule rather than a capability gap. Because an
omitted argument maps to different defaults, the generated argument must be explicit.

## 4.5 Group keys: index vs ordinary columns

```
pandas   m_pd.groupby("g").max().columns    →  ['s', 'v']        # key removed
         m_pd.groupby("g").max().index.name →  'g'               # key is the index

polars   m_pl.group_by("g").max().columns   →  ['g', 's', 'v']   # key retained
```

With two keys, pandas produces a **`MultiIndex`**:

```
pandas   df.groupby(["c","t"]).sum()          polars  df.group_by(["c","t"]).sum()
                             v                        ┌─────┬─────┬─────┐
         c   t                                        │ c   ┆ t   ┆ v   │
         DE  B               10                       ╞═════╪═════╪═════╡
             H                7                       │ DE  ┆ B   ┆ 10  │
         FR  P               12                       │ ...
```

**Why.** Direct consequence of [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise). pandas has an index, so keys go in it; polars has
none, so keys stay as columns.

**`as_index=False` does close this gap.** Verified, for ordinary reductions including
multi-key:

```
pd  d.groupby("g", as_index=False).sum().columns        → ['g', 'x', 'y']
pl  d.group_by("g").sum().columns                       → ['g', 'x', 'y']     identical

pd  mk.groupby(["c","t"], as_index=False).sum().columns → ['c', 't', 'v']     no MultiIndex
```

`group_keys` does **not** affect ordinary `.sum()`/`.agg()` output; it primarily controls
key insertion for `apply`. The equality claim is covered for both `.sum()` and `.agg()`
by the probe suite.
`MultiIndex` *columns* are a separate matter belonging to [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce), not here.

Within this key-layout issue, what remains after `as_index=False` is **row order**, which
is [`4.7`](#47-sort-and-maintain_order-are-not-the-same-knob) and only [`4.7`](#47-sort-and-maintain_order-are-not-the-same-knob). Keeping those two axes separate is what stops this from being
double-counted: key *placement* is solved by a pandas flag; key *ordering* is not.

**Ownership.** `GroupingSpec` records `as_index` intent; `OutputLayout` owns key
placement in the realised result. The aggregate lowerer consumes both contracts.

## 4.6 `SeriesGroupBy` has no polars analogue

```
pandas   pdf.groupby("g")["x"].sum()                 →  Series, name='x', indexed by g
polars   pldf.group_by("g").agg(pl.col("x").sum())   →  DataFrame(g, x)
```

**Why.** pandas has a whole separate class — `SeriesGroupBy` — for the case where you
select one column before aggregating, returning a `Series`. polars has no such thing;
`group_by` returns one `GroupBy` type and every grouped result is a `DataFrame`.

**Why this is directly relevant to your task.** Today `_is_aggregation` refuses to fuse
when anything sits between `groupby` and the reducer, so `groupby("g")["x"].sum()` — a
`GetItem` in between — is simply *not recognised*. Splitting into two nodes is exactly
what makes that pattern representable. This case moves from **unsupported** (not your
problem) to **must be handled** (your problem). The split creates this work rather than
resolving it.

## 4.7 `sort` and `maintain_order` are not the same knob

```
input keys: [b, a, b, a]

pandas  default (sort=True)            →  a, b       # sorted by key
pandas  sort=False                     →  b, a       # first-appearance order
polars  default (maintain_order=False) →  unspecified — do not rely on it
polars  maintain_order=True            →  b, a       # first-appearance order
```

**The trap.** They look like the same knob. pandas' `sort=True` gives **sorted-by-key**
order; polars' `maintain_order=True` gives **input** order. **No polars flag reproduces
pandas' default** — matching it needs `maintain_order=True` plus an explicit sort, or
just an explicit sort.

With `maintain_order=False`, output group order is unspecified and must not be relied
upon. `GroupingSpec` owns the requested ordering semantics; `OutputLayout` records and
the lowerer realises the resulting row order.

## 4.8 pandas silently drops rows with null keys

```
input keys: ['a', null, 'a']

pandas  default (dropna=True)  →  1 group   # rows with null keys are DROPPED
pandas  dropna=False           →  2 groups  # null becomes a group
polars  (no parameter)         →  2 groups  # always keeps the null group
```

**Why it's significant.** pandas' default **silently discards data**. If the key column
has any nulls the two backends aggregate over different row sets, so *every* aggregate
value can differ — not just the group count. And there's no polars parameter to opt into
pandas' behaviour; you'd have to filter nulls explicitly before grouping.

**Ownership.** `GroupingSpec` owns the null-key policy; `GroupbyOp` carries it.

## 4.9 Unobserved categorical groups

```
pandas  observed=True   (3.0.2 default) →  only groups present in the data
pandas  observed=False                 →  extra rows for unused categories,
                                          filled with the reducer's identity (sum→0)
polars  Enum / Categorical             →  only observed groups, no parameter
```

**Why it's low-priority but real.** In pandas 3.0.2 the `observed` default is `True`
(read off the live signature), which matches polars, so out of the box they agree. But
`observed=False` is still available with no direct polars flag — and it doesn't just add
empty rows, it fills them according to reducer semantics (`0` for sum, `NaN` for mean).
A rewrite can materialise the category domain, aggregate observed groups, then join and
fill according to `ValuePolicy`; otherwise the capability must be rejected explicitly.

**Ownership.** `GroupingSpec` owns the requested group domain. `ValuePolicy` owns the
reducer-specific value for an unobserved group, and the backend lowerer realises both.

> **Filing transition.** Nodes [(3)](#3-agg_methods--dataframe--series) and [(4)](#4-agg_methods--groupby) finish the direct-method catalogue. Node [(2)](#2-agg_funcs)
> begins the `.agg()` grammar catalogue; implementation follows the separate dependency
> DAG rather than this reading order.

---

# (2) AGG_FUNCS

*What kind of thing may be passed to `.agg()`. Second child of the root.*

## 2.1 `aggregate` does not exist in polars

pandas exposes `agg` and `aggregate` as **the same function object**:

```
pd.DataFrame.agg is pd.DataFrame.aggregate            →  True
pd.Series.agg    is pd.Series.aggregate               →  True
DataFrameGroupBy.agg is DataFrameGroupBy.aggregate    →  True
```

Among the tracked eager `DataFrame`/`Series`/`GroupBy` surfaces, Polars exposes `agg`
only on `GroupBy`:

```
hasattr(pl...GroupBy, 'aggregate')  →  False
```

**Consequence.** `_AGG_FUNCS = {"agg", "aggregate"}` is a 2→1 mapping. Harmless — just
normalise both to one canonical name during IR construction — but do it deliberately so
the physical impls only ever see one spelling.

## 2.2 A specification is not an expression

This distinction explains most grammar and lowering differences at [(5)](#5-agg_funcs--dataframe--series) and [(6)](#6-agg_funcs--groupby). It does
not explain method-specific arguments such as `axis`, callable execution contracts, or
output namespace/layout collisions; those retain their own contentions.

```
pandas   gb.agg({"x": "sum"})           # a SPECIFICATION describing what to do
polars   gb.agg(pl.col("x").sum())      # an EXPRESSION that already encodes it
```

In pandas, strings, lists, dicts, and named-aggregation tuples are declarative specs that
pandas parses at call time; pandas also accepts callable reducers under a separate
contract. In polars the grouped API expects expressions that already encode the selected
columns and operations. A pandas spec must therefore be parsed before it can become a
polars expression tree.

**Why no name table can fix this.** There is no string you can pass to polars that means
"sum". `"sum"` isn't a name polars looks up — it's parsed as a column reference ([`6.1`](#61-a-bare-string-names-a-column-not-a-function)).
Translating pandas specs requires an actual **lowering pass**: walk the spec, and for
each `(column, function)` pair emit `pl.col(column).<function>()`. A compiler, not a
lookup — and it must handle the six contentions and distinct source grammars at [(6)](#6-agg_funcs--groupby).

---

# (5) AGG_FUNCS → DataFrame / Series

*`.agg(spec)` on an ungrouped object. First child of [(2)](#2-agg_funcs).*

## 5.1 The node does not exist in polars at all

```
hasattr(pl.DataFrame, 'agg')  →  False
hasattr(pl.Series,    'agg')  →  False
```

**The only one of the four leaf nodes with zero polars surface.** There is no generic
aggregation entry point on ordinary polars objects. `df.agg("sum")` and
`s.agg(["sum","mean"])` therefore have no direct method target; they lower to explicit
expressions or direct reducer calls according to the spec and output contract.

**Lowering.** In polars 1.36.0, generic ungrouped aggregation is represented by explicit
expressions or direct reducer methods rather than a `.agg()` entry point. For compatible
numeric columns, `df.select(pl.all().sum())` is a structural lowering of
`df.agg("sum")`; it is not a result-contract equivalent because it returns a one-row
DataFrame rather than a Series and inherits the expression-specific dtype policy from
[`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface). `OutputLayout` and `ValuePolicy` must be applied around the lowering.

## 5.2 The spec's *value* controls the result *type*

```
s = pdf["x"]
df = pdf[["x", "y"]]

s.agg("sum")                →  8.0                    scalar
s.agg(["sum","mean"])       →  Series                 indexed by function name
df.agg("sum")               →  Series                 indexed by column name
df.agg(["sum","mean"])      →  DataFrame              functions × columns
```

**Why it matters for an IR.** Output rank is not knowable from the operation class or
method name alone; a literal `AggSpec` makes it statically derivable, while a deferred
`OperandRef` also defers `OutputLayout`. The planner must not assume scalar, Series, or
DataFrame rank until the relevant spec is resolved.

The current code sets `self.output_type = OutputType.FRAME` unconditionally. For three of
the four cases above, that's wrong.

## 5.3 `axis` is method-specific on ungrouped calls and absent from grouping

```
pd.DataFrame.aggregate(func=None, axis=0, *args, **kwargs)     # axis IS a parameter
pdf[["x","y"]].agg("sum", axis=1)  →  per-row sums, length 4

pd.DataFrame.groupby(...)          # axis is NOT a parameter in pandas 3.0.2
pdf.groupby(level=0, axis=1)       →  TypeError: unexpected keyword argument 'axis'
```

`axis` is not unique to `.agg()`. Many direct DataFrame reducers take it —
`DataFrame.sum` is one example — but the property is method-specific rather than a
property of the entire node:

| surface | `axis`? |
|---|---|
| ungrouped `.agg()` (node 5) | **yes** |
| ungrouped direct reducers (node 3) | **method-dependent**; present on `sum`, `mean`, `count`, … but absent on `size`, `describe`, and `value_counts` |
| `DataFrame.groupby(...)` | **no** in pandas 3.0.2; passing it raises `TypeError` |
| tracked polars aggregation surfaces | **no** — use `*_horizontal` for row-wise reduction |

**Why this matters for the split.** `AggregateOp` carries an `axis` field and
`make_aggregate_op` parses it. That field is meaningful on both *ungrouped* paths and
meaningless on the grouped one. It belongs in `AggSpec` only for source methods that
accept it. Together with [`5.2`](#52-the-specs-value-controls-the-result-type), this shows that output layout cannot be inferred from a
method name alone: `sum(axis=0)` and `sum(axis=1)` are both Series, but their index domain
and interpretation differ.

The tracked polars aggregation surfaces have no `axis` parameter; row-wise reduction is
the separate `*_horizontal` family (`pl.sum_horizontal`, `pl.mean_horizontal`, …) — a
different function, not a parameter.

---

# (6) AGG_FUNCS → GroupBy

*`.agg(spec)` on a grouped object. Last node in the traversal. These six cover spec
grammar, callable execution, and output-layout consequences.*

```
pandas  DataFrameGroupBy.aggregate(func=None, *args, engine=None,
                                   engine_kwargs=None, **kwargs)
polars  GroupBy.agg(*aggs: IntoExpr | Iterable[IntoExpr],
                    **named_aggs: IntoExpr) -> DataFrame
```

pandas takes **one positional spec**; polars takes **varargs of expressions**. Even the
arity differs.

## 6.1 A bare string names a column, not a function

```
pandas   gb.agg("sum")   →  applies the sum reducer to every column
polars   gb.agg("sum")   →  ColumnNotFoundError: unable to find column "sum"
polars   gb.agg("x")     →  a: [1, null, 3], b: [4] — SILENTLY implodes each group
```

**Why.** polars' `IntoExpr` protocol converts a bare string via `pl.col(str)` — a string
is always a **column reference**, never a function name. So `agg("sum")` looks for a
column called `sum`. And a bare `pl.col("x")` in grouped context with no reducer applied
produces the list of all values in the group.

**The failure mode depends on your data.** If the string doesn't match a column name you
get a clean `ColumnNotFoundError`. If it *does* — and `"count"`, `"min"`, `"max"`,
`"sum"`, `"mean"` are entirely plausible column names in real data — you get a silently
wrong result. That asymmetry makes it hard to catch: it works fine until someone's frame
has a column named `count`.

## 6.2 List specs need a MultiIndex polars can't produce

```
pandas   gb.agg(["sum","mean"])   →  MultiIndex columns: (x,sum) (x,mean) (y,sum) (y,mean)
polars   gb.agg(["sum","mean"])   →  ColumnNotFoundError
```

**Why there's no equivalent.** Beyond the string-parsing issue from [`6.1`](#61-a-bare-string-names-a-column-not-a-function), the pandas
result has **`MultiIndex` columns** — a two-level structure pairing each input column
with each function. polars has no native `MultiIndex`. Under source-semantic preservation,
`OutputLayout` retains ordered tuple-label metadata and the result materialiser must
reconstruct a source-compatible labelled result; if the executor cannot carry that
metadata, the plan is rejected. Flattening to `x_sum`, `x_mean` is permitted only under
an explicitly selected normalised compatibility profile.

## 6.3 Dict specs are rejected outright

```
pandas   gb.agg({"x": "sum"})               →  works
pandas   gb.agg({"x": ["sum","mean"]})      →  works, MultiIndex columns
polars   gb.agg({"x": "sum"})               →  TypeError: specifying aggregations
                                               as a dictionary is not supported
```

polars raises explicitly and suggests keyword syntax. The single-function form
`{"x": "sum"}` can be parsed into an `AggEntry` and lowered syntactically to
`agg(x=pl.col("x").sum())`, after applying reducer semantics and output-layout policy.
The list-valued form also inherits [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce)'s hierarchical-label problem.

## 6.4 A bare callable is not an expression — but callables *can* be embedded

```
pandas   gb.agg(lambda s: s.max() - s.min())   →  works, per group per column
polars   gb.agg(lambda s: s.max() - s.min())   →  TypeError: cannot create expression
                                                  literal for value of type function
```

**Why.** The failure is about the *protocol*, not the capability. `IntoExpr` has no
conversion for a raw function object, so a bare lambda is rejected. polars can absolutely
run Python per group — it just requires an explicit wrapper:

```python
# works, and returns a proper scalar column (Int64):
gb.agg(pl.map_groups(["x"], lambda s: s[0].max() - s[0].min(),
                     return_dtype=pl.Int64, returns_scalar=True))
gb.agg(pl.col("x").map_batches(lambda s: s.max() - s.min(),
                               return_dtype=pl.Int64, returns_scalar=True))
```

**Two contracts must be explicit:**

- With the default `returns_scalar=False`, a Python-scalar callback raises `TypeError`.
  A callback returning a length-one Series succeeds but produces `List(Int64)` in grouped
  context. Set `returns_scalar=True` when the declared UDF output is scalar.
- `return_dtype` is optional in polars 1.36.0 and is inferred successfully for this
  scalar fixture. Supplying it remains advisable because inference can fail or infer an
  unintended dtype; omission does not unconditionally raise.

**On `GroupBy.map_groups`** — it exists, but it is *not* the closest analogue to
`agg(lambda)`: it receives a whole sub-`DataFrame` per group, whereas pandas' `agg`
callable receives one Series per selected column. Top-level `pl.map_groups` and
`pl.col(...).map_batches` are closer expression-level building blocks.

**So the real contention is narrower than "no callables":** it is that the pandas spec
grammar admits a bare function where polars requires an explicit UDF wrapper and an
output contract. Lowering is valid only when the callable's supported input/output
semantics are known; an arbitrary pandas callable is not automatically equivalent.
Python UDF paths also forfeit native vectorisation, which an optimiser should surface.

## 6.5 Named aggregation: syntactic alignment, semantic and layout divergence

```
pandas   gb.agg(x_sum=("x", "sum"))            # value is a (column, funcname) TUPLE
polars   gb.agg(x_sum=pl.col("x").sum())       # value is an EXPRESSION
```

**The alignment is real but only syntactic.** Both use `**kwargs` with the output name
as key, so the keyword *shape* matches and the pandas tuple `(col, func)` maps
mechanically onto `pl.col(col).func()`. That makes this the cleanest *surface* mapping in
the document.

**It is not semantically clean**, on three counts:

1. **It inherits every reducer divergence.** `x=("v","kurt")` still hits [`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions);
   `x=("v","nunique")` still hits [`3.2`](#32-nunique-counts-different-units-and-nulls). The wrapper is clean; the payload is not.
2. **Alias collisions diverge.** pandas permits an output name equal to a grouping key
   (it lives in the index, so there is no clash); polars raises:
   ```
   pd  d.groupby("g").agg(g=("x","sum"))   →  column 'g', index name 'g'   OK
   pl  d.group_by("g").agg(g=pl.col("x").sum())  →  DuplicateError
   ```
   This is [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise) again: pandas has two namespaces (index and columns), polars has one.
3. **`SeriesGroupBy` uses a different grammar entirely** — see [`6.6`](#66-seriesgroupby-accepts-a-different-spec-grammar-from-dataframegroupby).

**Consequence for the IR.** Named aggregation is one source grammar and can be one
physical lowering form when aliases do not collide. It is not the canonical internal
representation; the ordered `AggSpec` defined below preserves the information it loses.

## 6.6 `SeriesGroupBy` accepts a different spec grammar from `DataFrameGroupBy`

The presence tables carry a `pd.SeriesGroupBy` column, but presence is where the
similarity stops. Once you select a column before aggregating, **the grammar changes**:

| spec form | `DataFrameGroupBy` | `SeriesGroupBy` |
|---|---|---|
| `.agg(["sum","mean"])` | `MultiIndex` columns `(x,sum)…` | **flat** columns `['sum','mean']` |
| named agg | `x_sum=("x","sum")` | `x_sum="sum"` — the tuple form raises `TypeError` |
| dict spec | `{"x":"sum"}` works | `SpecificationError: nested renamer is not supported` |
| `as_index=False` | keys become columns | **result becomes a `DataFrame`** again |

All four verified. The consequences for the split are concrete:

- [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce)'s hierarchical-column problem **does not exist** on the `SeriesGroupBy` path —
  the same list spec requires a different `OutputLayout` depending on source surface.
- Source parsers must dispatch on `DataFrameGroupBy` versus `SeriesGroupBy` because
  `("x","sum")` is valid on one and a `TypeError` on the other. Both parsers can then
  emit the unified ordered `AggSpec` consumed by one backend lowering compiler.
- Since `groupby("g")["x"]` is exactly the `GetItem`-in-between case from [`4.6`](#46-seriesgroupby-has-no-polars-analogue), **the
  node split is what makes this path representable at all** — and therefore what makes
  this contention Stratum's problem rather than an unsupported pattern.

**Recommendation:** the implementation capability registry must use separate rows for
the two grouped input surfaces. Treating `pd.SeriesGroupBy` as
"`DataFrameGroupBy` with one column" is wrong in all four cells above. The contention
matrix below keeps one row per immutable contention ID; it must not be mistaken for that
surface-level capability registry.

## Not repeated here

[`4.5`](#45-group-keys-index-vs-ordinary-columns)–[`4.9`](#49-unobserved-categorical-groups) apply to this node too and are recorded once at [(4)](#4-agg_methods--groupby) because they are grouping
and grouped-layout rules. [`3.2`](#32-nunique-counts-different-units-and-nulls), [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity), [`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions), and other reducer semantics are recorded
once under the reducer surface. Swapping `.sum()` for `.agg({"x":"sum"})` does not create
a second contention.

Recording these shared grouping and layout rules once avoids duplicating them under both
direct reducers and `.agg()`.

---

# Normative contracts and ownership

The canonical rule is **source-semantic preservation**: capture the meaning and output
contract of the source call, then require every backend to reproduce it through a native
operation, a rewrite, or result normalisation. If a backend cannot do so, validation must
reject the plan before execution. A target backend's native default must never silently
replace the captured source semantics.

The normative execution checklist in this document defines the **pandas-compatible
profile** used by the current task: pandas-style `groupby`/aggregation calls are captured
once and may execute on either the pandas or Polars backend without changing their
observable contract. The factual catalogue is bidirectional, but the disposition matrix
is deliberately not a claim that native Polars calls have pandas semantics. A native
Polars `group_by(...).count()`, `all()`, `n_unique()`, or bare-column aggregation retains
its Polars meaning and belongs to a separate `polars-compatible` profile.

For an operation created directly in Stratum, the caller must select a compatibility
profile explicitly. Adding native Polars call capture requires a separate profile matrix;
the pandas-compatible rows below must not be reused in reverse.

Every field has one logical owner. Backend lowerers choose the mechanism used to honour
the contract; they do not redefine it.

## `ValuePolicy`

Owns cross-backend value semantics:

- `null` versus `NaN`, including which representations count as missing;
- nullable dtype and promotion rules;
- non-numeric and Boolean-column participation;
- canonical defaults for `skipna`, `min_count`, interpolation, `ddof`, bias, and
  other reducer controls.

The requested arguments remain in `AggSpec`; `ValuePolicy` defines what supplied and
omitted values mean. It is the primary owner of [`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap)–[`0.5`](#05-configurable-reducers-vs-nullary-reducers).

## `GroupingSpec` and `GroupbyOp`

Owns how groups are formed, without computing aggregate values:

```text
GroupingSpec:
    keys
    key_source:
        column | expression | positional_external | aligned_external
        | index_level | callable | Grouper
    requested_group_order
    null_key_policy
    categorical_domain_policy
    as_index_intent
    group_keys
```

`by`, `level`, aligned external Series, callable groupers, and `pd.Grouper` are
different key-source variants. They must not be collapsed into one string/list field.
`GroupingSpec` owns [`4.7`](#47-sort-and-maintain_order-are-not-the-same-knob)–[`4.9`](#49-unobserved-categorical-groups) and the grouping-input part of [`P`](#the-one-thing-that-is-not-a-contention-p-the-index-premise). It records
`as_index`, but `OutputLayout` owns how that intent is realised.

| pandas input | polars mechanism | disposition |
|---|---|---|
| ordinary column/expression `by` | `*by`, `**named_by` | native after expression translation |
| external Series | external expression | native only for positional semantics; pandas label alignment requires an explicit align/materialise rewrite |
| `sort=True` | explicit result sort | rewrite; `maintain_order` is not the same setting |
| `dropna=False` | default null-key grouping | native semantic match |
| `dropna=True` | filter rows with null grouping keys | rewrite |
| `observed=True` | observed groups | native semantic match |
| `observed=False` | materialise category domain, join, and reducer-specific fill | rewrite or reject |
| `as_index` | no native index | capture here; realise in `OutputLayout` |
| `group_keys` | no aggregation effect | preserve for provenance; relevant only to other grouped operations |
| `level`, callable, `Grouper` | explicit derived grouping columns or specialised plan | rewrite or reject |

## `AggSpec` and `AggregateOp`

Owns what is reduced and how:

```text
AggSpec:
    input_surface: DataFrame | Series | DataFrameGroupBy | SeriesGroupBy
    entries: ordered AggEntry[] | DeferredAggSpec(OperandRef)
    source_form
    axis

AggEntry:
    input_selector
    reducer_id
    reducer_arguments
    output_label
    ordinal
```

The ordered representation preserves bare reducers over all payload columns, duplicate
functions, arguments, source ordering, callable-derived labels, DataFrameGroupBy versus
SeriesGroupBy grammar, and deferred `OperandRef` specifications. `axis` is valid only
when the captured source method accepts it.

Named aggregation is one source grammar and one possible backend lowering form. It is not
the canonical IR.

## `OutputLayout`

Owns the observable result contract:

```text
OutputLayout:
    rank: scalar | series | frame | deferred
    key_placement: index | columns | absent
    key_names
    column_label_depth
    column_labels
    column_order
    alias_collision_policy
    row_order
```

It is derived from the input kind, `GroupingSpec`, `AggSpec`, and compatibility
profile. It owns rank and schema decisions in [`3.1`](#31-series-vs-one-row-dataframe), [`4.2`](#42-size--len-series-vs-dataframe), [`4.5`](#45-group-keys-index-vs-ordinary-columns), [`4.6`](#46-seriesgroupby-has-no-polars-analogue),
[`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce), and the alias/layout part of [`6.5`](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence). If an aggregation spec is deferred through
`OperandRef`, layout is deferred too; shape-dependent optimiser rules must wait until
resolution.

`OutputLayout` is backend-neutral metadata attached to the logical result. It can
represent Series rank, index keys, and hierarchical labels even when the physical
calculation uses a polars DataFrame. A result materialiser reconstructs the requested
source-compatible container. If the current execution boundary can expose only a native
backend container, any unrepresentable source layout is `reject`, not silently flattened.

Every concern has a logical owner. A value can be configured by one contract and realised
by another without leaving ownership ambiguous.

---

# Implementation order

The taxonomy's DFS order is not this dependency order:

```text
             source call / explicit compatibility profile
                                  |
              +-------------------+-------------------+
              |                   |                   |
         ValuePolicy         GroupingSpec          AggSpec
              \                   |                   /
               +------------------+------------------+
                                  |
                            OutputLayout
                                  |
                     capability + disposition
                           /             \
                   pandas lowering   polars lowering
                           \             /
                            normalisation
                                  |
                         conformance tests
```

1. Declare the compatibility profile and `ValuePolicy`.
2. Implement independent parsers for grouping forms and aggregation forms, both retaining
   source surface and grammar.
3. Build the versioned reducer catalogue. Record semantic identity separately from direct
   backend-method availability.
4. Derive `OutputLayout` from the normalised specs; never infer rank from a method name
   alone.
5. Resolve every backend/reducer/surface combination through the disposition algorithm
   below; do not choose a fallback ad hoc.
6. Lower grouped pairs as one physical operation and ungrouped aggregates through the
   appropriate direct method or expression plan.
7. Test each contention by source surface, disposition, value result, dtype, and output
   layout.

# Normative disposition matrix

This is the execution checklist. “Specified” means the design decision is closed in this
map; it does not claim the corresponding Stratum implementation is complete.

Disposition is deterministic under the active compatibility profile. First resolve any
`OperandRef`; until then, the plan is in a **deferred planning state**, not a backend
disposition. Then look up the tuple `(profile, target backend, input surface, reducer,
dtype class, arguments, requested layout)` in the versioned capability registry:

1. `native` applies only when the backend operation already satisfies all four contracts.
2. `normalize` applies when an input/output value, dtype, rank, or label adapter is enough
   and the reduction itself is semantically identical.
3. `rewrite` applies when a proven expression, filter, expansion, join, or formula is
   required.
4. `reject` applies when neither an exact native path nor a proven adapter/rewrite exists.
5. `out-of-scope` means the source operation does not exist in the active profile.

A slash in the table is this ordered conditional route, not an unresolved menu. For
example, `native/rewrite/reject` means exact native support when the capability predicate
passes, otherwise the documented rewrite when its preconditions pass, otherwise rejection.

| ID | Primary owner | pandas path | polars path | Disposition | Observable / probe |
|---|---|---|---|---|---|
| [`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap) | `ValuePolicy` | preserve declared pandas missing semantics | normalise `NaN`/`null`; conditional aggregate for strict propagation | normalize/rewrite | silent value/dtype · `U2`, [`0.1`](#01-numpy-backed-pandas-nan-semantics-vs-polars-null-bitmap) |
| [`0.2`](#02-inferred-numpy-backed-integer-data-promotes-to-float-under-nulls) | `ValuePolicy` | choose nullable dtype or cast | preserve integer then cast to contract | normalize | dtype · `U3`, [`0.2`](#02-inferred-numpy-backed-integer-data-promotes-to-float-under-nulls) |
| [`0.3`](#03-reducer-dtype-domains-vary-by-reducer-and-execution-surface) | `ValuePolicy` | apply reducer×dtype policy | choose correct direct/expression path or reject | rewrite/reject | value/error/schema · `U4` |
| [`0.4`](#04-numeric_only-has-no-polars-parameter) | `ValuePolicy` | native `numeric_only` | select eligible measures inside aggregation; include Boolean when required | rewrite | participating columns · `U5` |
| [`0.5`](#05-configurable-reducers-vs-nullary-reducers) | `ValuePolicy` | parse reducer kwargs | emit conditional/configured expressions or reject | rewrite/reject | values/errors · signature probes |
| [`1.1`](#11-renames-hide-semantic-changes) | `AggSpec` | canonical reducer ID | name mapping plus semantic flags | normalize | silent values/labels · `M1`, [`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions) |
| [`1.2`](#12-no-passthrough-argument-surface-despite-a-small-overlap) | `AggSpec` | retain arguments | translate by reducer/domain or reject | rewrite/reject | values/rank · `M2`, [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity) |
| [`1.3`](#13-the-direct-method-set-is-not-closed) | `AggSpec` | native method where supported | direct method, expression, formula, or rejection | native/rewrite/reject | capability · inventories |
| [`3.1`](#31-series-vs-one-row-dataframe) | `OutputLayout` | native Series | one-row frame plus labelled-result materialisation | normalize | rank/labels · `U1`, `DS1` |
| [`3.2`](#32-nunique-counts-different-units-and-nulls) | `AggSpec` | per-column `nunique` | per-column expression with missing filter; never DataFrame `n_unique` | rewrite | silent unit/value · `DS2` |
| [`3.3`](#33-size-is-a-property-and-it-counts-cells) | `AggSpec` | property (`rows × cols`) | `height × width`; Series uses `len` | rewrite | scalar/unit · `DS3` |
| [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity) | `AggSpec` | force common interpolation; vector `q` native | force common interpolation; expand vector or reject | rewrite/reject | silent scalar value / loud arity · `DS4`, [`3.4`](#34-quantile-interpolation-default-differs-and-so-does-q-arity) |
| [`3.5`](#35-describe-differs-in-shape-and-row-set) | `OutputLayout` | native summary contract | build and materialise compatible summary or reject | normalize/rewrite/reject | compound schema · `DS5` |
| [`3.6`](#36-firstlast-three-way-absence-asymmetry) | `AggSpec` | no source method in the pinned pandas profile | Series direct method belongs to a separate Polars profile | out-of-scope | capability · `DS6` |
| [`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions) | `AggSpec` | native corrected estimator | `bias=False`; `fisher=True` for kurtosis | rewrite | silent value · [`3.7`](#37-skew-and-kurtosis-use-different-bias-conventions) |
| [`4.1`](#41-count-names-a-different-operation) | `AggSpec` | native per-column non-missing count | `agg(col.count())`, never `GroupBy.count()` | rewrite | silent value/schema · `GB1` |
| [`4.2`](#42-size--len-series-vs-dataframe) | `OutputLayout` | rank from reducer and `as_index` | `len`/row counts plus materialisation and naming | normalize | rank/name · `GB2`, [`4.2`](#42-size--len-series-vs-dataframe) |
| [`4.3`](#43-all-implodes-into-lists-instead-of-reducing) | `AggSpec` | Boolean AND | `agg(col.all())`, never `GroupBy.all()` | rewrite | silent value/dtype · `GB3` |
| [`4.4`](#44-firstlast-null-contract-is-inverted) | `ValuePolicy` | explicit `skipna` semantics | explicit `ignore_nulls` | rewrite | silent default value · `GB4` |
| [`4.5`](#45-group-keys-index-vs-ordinary-columns) | `OutputLayout` | native `as_index` layout | columns plus index/key metadata or reject | normalize/reject | key placement · `GB5`, [`4.5`](#45-group-keys-index-vs-ordinary-columns) |
| [`4.6`](#46-seriesgroupby-has-no-polars-analogue) | `OutputLayout` | native `SeriesGroupBy` result | selected `AggSpec` plus Series materialisation | normalize | rank/name · `GB6` |
| [`4.7`](#47-sort-and-maintain_order-are-not-the-same-knob) | `GroupingSpec` | `sort` semantics | `maintain_order` for input order; explicit key sort otherwise | rewrite | silent row order · `GB7` |
| [`4.8`](#48-pandas-silently-drops-rows-with-null-keys) | `GroupingSpec` | native `dropna` | native keep-null or pre-filter grouping keys | native/rewrite | silent group membership · `GB8` |
| [`4.9`](#49-unobserved-categorical-groups) | `GroupingSpec` | native categorical domain | observed native; materialise/join/fill or reject | native/rewrite/reject | rows/values · `GB9` |
| [`2.1`](#21-aggregate-does-not-exist-in-polars) | `AggSpec` | normalise `agg`/`aggregate` alias | emit `agg` | normalize | spelling only · `F1` |
| [`2.2`](#22-a-specification-is-not-an-expression) | `AggSpec` | parse declarative grammar/callable contract | compile ordered entries to expressions | rewrite | values/schema · `F`, `FG` |
| [`5.1`](#51-the-node-does-not-exist-in-polars-at-all) | `AggSpec` | native `.agg()` | direct reducer or explicit `select` expressions | rewrite | rank/schema · `FD1` |
| [`5.2`](#52-the-specs-value-controls-the-result-type) | `OutputLayout` | derive from literal spec | derive/materialise; remain in planning state while `OperandRef` is unresolved | normalize | rank · `FD2` |
| [`5.3`](#53-axis-is-method-specific-on-ungrouped-calls-and-absent-from-grouping) | `AggSpec` | retain `axis` only where accepted | horizontal expression on ungrouped path; reject grouped axis | rewrite/reject | index domain · `FD3` |
| [`6.1`](#61-a-bare-string-names-a-column-not-a-function) | `AggSpec` | parse string as reducer | compile reducer expression; never pass function string | rewrite | silent list/value or clean error · `FG1` |
| [`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce) | `OutputLayout` | native hierarchical labels | retain tuple-label metadata and materialise, else reject | normalize/reject | label depth · `FG2` |
| [`6.3`](#63-dict-specs-are-rejected-outright) | `AggSpec` | parse dict | ordered expressions from parsed entries | rewrite | labels/schema · `FG3` |
| [`6.4`](#64-a-bare-callable-is-not-an-expression--but-callables-can-be-embedded) | `AggSpec` | native callable contract | explicit UDF wrapper when contract is known, else reject | rewrite/reject | dtype/value/performance · `FG4`, [`6.4`](#64-a-bare-callable-is-not-an-expression--but-callables-can-be-embedded) |
| [`6.5`](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence) | `OutputLayout` | native named aggregation | named expression when collision-free; apply collision policy | normalize/rewrite/reject | alias namespace · `FG5` |
| [`6.6`](#66-seriesgroupby-accepts-a-different-spec-grammar-from-dataframegroupby) | `AggSpec` | surface-specific parser | unified ordered spec plus surface-specific layout | rewrite | rank/labels · [`6.6`](#66-seriesgroupby-accepts-a-different-spec-grammar-from-dataframegroupby) |

Every row specifies a contention-level route for the pandas-compatible profile.
Implementation expands these rules into capability rows keyed by target backend,
`AggSpec.input_surface`, reducer, dtype, arguments, and layout. In particular,
`DataFrameGroupBy` and `SeriesGroupBy` require different rows there for [`4.2`](#42-size--len-series-vs-dataframe), [`4.6`](#46-seriesgroupby-has-no-polars-analogue),
[`6.2`](#62-list-specs-need-a-multiindex-polars-cant-produce), [`6.5`](#65-named-aggregation-syntactic-alignment-semantic-and-layout-divergence), and [`6.6`](#66-seriesgroupby-accepts-a-different-spec-grammar-from-dataframegroupby). Implementation tracking should also add a separate status
field linked to the corresponding Stratum issue or test; it must not infer completion
from this document.

---

# Execution model for the node split

`GroupbyOp` and `AggregateOp` are separate logical nodes but one fused physical grouped
aggregation.

```text
Frame
  |
  v
GroupbyOp(GroupingSpec)                 OutputType.GROUPED
  |
  v
AggregateOp(AggSpec, OutputLayout)
```

`OutputType.GROUPED` is a logical semantic edge, not a tabular runtime value. pandas and
polars GroupBy builders are returnable Python objects, but they are backend-specific and
opaque to a backend-neutral optimiser. This design therefore does not place either
builder in the runtime buffer pool.

The backend lowerer must match `GroupbyOp → AggregateOp` and emit one executable
operation carrying all four contracts:

```text
FusedGroupAggregateExec(
    grouping_spec,
    agg_spec,
    value_policy,
    output_layout,
)
```

The pandas implementation emits the appropriate `groupby(...).<reducer>()` or
`groupby(...).agg(...)` call. The polars implementation emits
`group_by(...).agg(expressions)` plus any required null-key filter, payload selection,
explicit key sort, reducer emulation, and result-layout normalisation.

A logical `GroupbyOp` may feed more than one supported `AggregateOp`. The correctness
rule is to form one independent `FusedGroupAggregateExec` per consumer, each carrying the
same immutable `GroupingSpec` and its own `AggSpec`/`OutputLayout`; no opaque backend
GroupBy object is shared. A backend optimiser may coalesce compatible consumers into one
physical grouping and project separate results only after proving that value policies,
ordering, aliases, and layouts remain independent. Fan-out is therefore supported by
cloning the logical grouping contract, while physical sharing is an optional optimisation.

A grouped selection such as `df.groupby("g")["x"].sum()` is absorbed into
`AggSpec.input_surface` and `AggEntry.input_selector`; it is not scheduled as a
runtime `GetItemOp` over a backend GroupBy object.

The rewrite is valid only when the grouped path terminates in a supported grouped
operation. Support validation must happen before replacing the original call chain, or
the rewrite must be transactional and reversible. An unsupported consumer therefore
keeps its original opaque chain on a backend that supports it or raises a capability
error during planning. The executor must never discover at runtime that mandatory fusion
was impossible.

---

# Reproducing this

Scripts live in `agg_contention_probes/`. Run `python check_all.py` for all of it.

**Exploration** — how the findings were produced:

```bash
python probe.py       # presence + signature matrix
python semantics.py   # semantic probes on the shared fixture
python semantics2.py  # edge cases: nulls, dtypes, ordering, categoricals
python gen_tables.py  # regenerates the presence tables at (3) and (4)
```

**Verification** — three independent layers, all must pass:

| script | checks | what it proves |
|---|---|---|
| `verify.py` | **263** | the listed worked examples and targeted semantic assertions reproduce on the pinned fixture |
| `audit_tables.py` | **254** | all **168 presence cells** in the two tables match live introspection, and every method name in them exists on some surface |
| `audit_doc.py` | **57** | declared counts, numbering, reading order, cross-references, selected live inventory claims, and literal no-op checks remain consistent |
| **total** | **574** | |

Current status: **574 checks passed, 0 failed.**

### What this claim actually covers

- **Covered:** the explicit assertions in `verify.py`, all 168 presence cells, declared
  inventory/count claims, cross-references, and the documented exception types exercised
  by the suite.
- **Not covered:** every sentence of prose, warning absence unless a test captures it,
  semantic annotations that are not named by an assertion, other dtypes, empty frames,
  broader multi-key cases, and all lazy-plan combinations.
- **Design claims:** severity, ownership, compatibility policy, and the node-split
  architecture require review in addition to executable tests.

Re-run after bumping either library; pin `pandas==3.0.2` and `polars==1.36.0` to
reproduce these exact results.


## Legacy Job provenance

### status

current
