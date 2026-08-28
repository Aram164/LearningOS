---
id: note-pandas-groupby-signatures
type: note
title: "pandas Series / DataFrame / GroupBy signatures — Stratum flag-model reference"
created: "2026-08-18"
role: reference
state: evolving
authorship: user
concepts: [concept-dataframe-ops, concept-aggregation, concept-dataframe-semantics]
sources: []
# Companion to note-pandas-polars-aggregation-contentions: the per-method flag
# surface that extraction and lowering have to preserve. Targets pandas 3.0.2,
# the version Stratum pins.
---

# pandas Series / DataFrame / GroupBy method signatures — Stratum design reference

**Target pandas version:** 3.0.2 (the version pinned by Stratum)  
**Primary purpose:** design a clean flag model for Stratum's grouped operations, especially `GroupByAggregateOp` / `AggregateOp`.

---

## 0. Why this document exists

The problem is not merely that pandas exposes many methods with the same names. The important implementation fact is:

> `Series`, `DataFrame`, `SeriesGroupBy`, and `DataFrameGroupBy` often expose the same conceptual operation through **different signatures**, and some methods only exist in the grouped API.

For Stratum this means that normalizing a direct call such as:

```python
grouped.sum(min_count=2, skipna=False)
```

to only the string `"sum"` is not enough. The method-specific flags are part of the semantics and need to survive extraction/lowering.

The current Stratum `AggregateOp` stores:

```text
grouping_attributes
aggregations
groupby_kwargs
```

and direct aggregation calls are normalized to their method name. This reference is intended to make it obvious which **aggregation-call kwargs** need their own storage and which can be shared structurally.

---

## 1. Colour legend

The signatures are stacked in this order whenever the method exists:

1. `Series`
2. `DataFrame`
3. `SeriesGroupBy`
4. `DataFrameGroupBy`

Colour meaning:

- <span style="background-color:#fff2a8;padding:1px 3px;border-radius:3px">YELLOW</span> — the same parameter exists in multiple variants but its **default value differs**.
- <span style="color:#c62828;font-weight:700">RED</span> — the parameter is **not shared by all variants being compared**; it exists only on a subset of implementations.
- uncoloured — structurally shared with the same default.
- <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">YELLOW + RED</span> — both conditions apply: the field is not universal **and** the variants that have it use different defaults.

### Important TypedDict warning

A `TypedDict` expresses **key names and value types**, not runtime defaults. Therefore:

```python
class SumKwargs(TypedDict, total=False):
    numeric_only: bool
    min_count: int
    skipna: bool
```

can express that these keys are valid, but it does **not** encode that `min_count` defaults to `0`.

That distinction matters for Stratum:

- if you store **only explicitly supplied kwargs**, use `total=False` and let each backend supply its native default;
- if Stratum wants **backend-independent normalized semantics**, defaults must be materialized separately (e.g. a defaults table, dataclass metadata, or canonicalized effective kwargs).

---

# PART I — aggregation / reduction methods

## 2. `sum`

### Signatures

<code>Series.sum(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=None</span>, skipna=True, numeric_only=False, min_count=0, **kwargs)</code>  
<code>DataFrame.sum(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=0</span>, skipna=True, numeric_only=False, min_count=0, **kwargs)</code>  
<code>SeriesGroupBy.sum(numeric_only=False, min_count=0, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>  
<code>DataFrameGroupBy.sum(numeric_only=False, min_count=0, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>

### Difference

- Plain objects reduce along an axis; GroupBy reduces independently inside each group.
- `axis` therefore disappears from GroupBy.
- GroupBy adds `engine` / `engine_kwargs`.
- `numeric_only`, `min_count`, and `skipna` are the useful shared semantic flags.

### TypedDict implication

```python
class NumericSkipnaKwargs(TypedDict, total=False):
    numeric_only: bool
    skipna: bool

class MinCountKwargs(TypedDict, total=False):
    min_count: int

class EngineKwargs(TypedDict, total=False):
    engine: str | None
    engine_kwargs: dict[str, object] | None

class SumKwargs(NumericSkipnaKwargs, MinCountKwargs, EngineKwargs):
    pass
```

---

## 3. `prod`

### Signatures

<code>Series.prod(*, axis=None, skipna=True, numeric_only=False, min_count=0, **kwargs)</code>  
<code>DataFrame.prod(*, axis=0, skipna=True, numeric_only=False, min_count=0, **kwargs)</code>  
<code>SeriesGroupBy.prod(numeric_only=False, min_count=0, skipna=True)</code>  
<code>DataFrameGroupBy.prod(numeric_only=False, min_count=0, skipna=True)</code>

### Difference

For grouped execution the semantic kwargs are exactly the compact shared set:

```text
numeric_only
min_count
skipna
```

Unlike `sum`, GroupBy `prod` has no `engine` / `engine_kwargs` parameters.

### TypedDict implication

```python
class ProdKwargs(NumericSkipnaKwargs, MinCountKwargs):
    pass
```

---

## 4. `mean`

### Signatures

<code>Series.mean(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrame.mean(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.mean(numeric_only=False, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>  
<code>DataFrameGroupBy.mean(numeric_only=False, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>

### TypedDict implication

```python
class MeanKwargs(NumericSkipnaKwargs, EngineKwargs):
    pass
```

---

## 5. `min` / `max`

### Signatures

<code>Series.min(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrame.min(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.min(numeric_only=False, <span style="color:#c62828;font-weight:700">min_count=-1</span>, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>  
<code>DataFrameGroupBy.min(numeric_only=False, <span style="color:#c62828;font-weight:700">min_count=-1</span>, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>

`max` has the same shape:

<code>Series.max(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrame.max(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.max(numeric_only=False, <span style="color:#c62828;font-weight:700">min_count=-1</span>, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>  
<code>DataFrameGroupBy.max(numeric_only=False, <span style="color:#c62828;font-weight:700">min_count=-1</span>, skipna=True, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>)</code>

### Important difference

`min_count` exists on the grouped variant but not on the plain `Series.min` / `DataFrame.min` API.

Also note the default difference relative to `sum` / `prod`:

```text
sum/prod: min_count = 0
min/max:  min_count = -1
```

This difference is **not representable by TypedDict inheritance alone**.

### TypedDict implication

```python
class MinMaxKwargs(NumericSkipnaKwargs, MinCountKwargs, EngineKwargs):
    pass
```

with a separate defaults mapping if Stratum canonicalizes defaults.

---

## 6. `median`

### Signatures

<code>Series.median(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrame.median(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.median(numeric_only=False, skipna=True)</code>  
<code>DataFrameGroupBy.median(numeric_only=False, skipna=True)</code>

### TypedDict implication

Grouped `median` needs only the shared numeric/missing-value bundle:

```python
class MedianKwargs(NumericSkipnaKwargs):
    pass
```

---

## 7. `std` / `var`

### Signatures

<code>Series.std(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=None</span>, skipna=True, ddof=1, numeric_only=False, **kwargs)</code>  
<code>DataFrame.std(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=0</span>, skipna=True, ddof=1, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.std(ddof=1, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, numeric_only=False, skipna=True)</code>  
<code>DataFrameGroupBy.std(ddof=1, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, numeric_only=False, skipna=True)</code>

`var` follows the same grouped flag shape:

<code>Series.var(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=None</span>, skipna=True, ddof=1, numeric_only=False, **kwargs)</code>  
<code>DataFrame.var(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=0</span>, skipna=True, ddof=1, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.var(ddof=1, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, numeric_only=False, skipna=True)</code>  
<code>DataFrameGroupBy.var(ddof=1, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, numeric_only=False, skipna=True)</code>

### TypedDict implication

```python
class DdofKwargs(TypedDict, total=False):
    ddof: int

class StdVarKwargs(NumericSkipnaKwargs, DdofKwargs, EngineKwargs):
    pass
```

---

## 8. `sem`

### Signatures

<code>Series.sem(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=None</span>, skipna=True, ddof=1, numeric_only=False, **kwargs)</code>  
<code>DataFrame.sem(*, <span style="background-color:#fff2a8;color:#c62828;font-weight:700;padding:1px 3px;border-radius:3px">axis=0</span>, skipna=True, ddof=1, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.sem(ddof=1, numeric_only=False, skipna=True)</code>  
<code>DataFrameGroupBy.sem(ddof=1, numeric_only=False, skipna=True)</code>

### TypedDict implication

```python
class SemKwargs(NumericSkipnaKwargs, DdofKwargs):
    pass
```

No GroupBy engine flags here.

---

## 9. `count`

### Signatures

<code>Series.count()</code>  
<code>DataFrame.count(<span style="color:#c62828;font-weight:700">axis=0</span>, <span style="color:#c62828;font-weight:700">numeric_only=False</span>)</code>  
<code>SeriesGroupBy.count()</code>  
<code>DataFrameGroupBy.count()</code>

### Difference

The grouped count API has **no method kwargs**. It counts non-missing values per group.

### TypedDict implication

No aggregation-call kwargs need to be stored for GroupBy `count()`.

---

## 10. `nunique`

### Signatures

<code>Series.nunique(dropna=True)</code>  
<code>DataFrame.nunique(<span style="color:#c62828;font-weight:700">axis=0</span>, dropna=True)</code>  
<code>SeriesGroupBy.nunique(dropna=True)</code>  
<code>DataFrameGroupBy.nunique(dropna=True)</code>

### TypedDict implication

```python
class DropnaKwargs(TypedDict, total=False):
    dropna: bool

class NuniqueKwargs(DropnaKwargs):
    pass
```

Do **not** conflate `dropna` with `skipna`; pandas uses different parameter names and semantics.

---

## 11. `first` / `last` — GroupBy-specific reducers

### Signatures

<code>Series: — no current plain reducer counterpart —</code>  
<code>DataFrame: — no current plain reducer counterpart —</code>  
<code>SeriesGroupBy.first(numeric_only=False, min_count=-1, skipna=True)</code>  
<code>DataFrameGroupBy.first(numeric_only=False, min_count=-1, skipna=True)</code>

`last`:

<code>Series: — no current plain reducer counterpart —</code>  
<code>DataFrame: — no current plain reducer counterpart —</code>  
<code>SeriesGroupBy.last(numeric_only=False, min_count=-1, skipna=True)</code>  
<code>DataFrameGroupBy.last(numeric_only=False, min_count=-1, skipna=True)</code>

### Difference

These are genuine GroupBy reducers: first/last qualifying values are computed **inside each group**.

### TypedDict implication

```python
class FirstLastKwargs(NumericSkipnaKwargs, MinCountKwargs):
    pass
```

The `min_count` default is `-1`.

---

## 12. `size` — GroupBy-specific reducer

### Signatures

<code>Series.size -> property</code>  
<code>DataFrame.size -> property</code>  
<code>SeriesGroupBy.size()</code>  
<code>DataFrameGroupBy.size()</code>

### Difference

This is an important same-name/different-concept case:

- plain `.size` is an **attribute** containing total element count;
- grouped `.size()` is a **method** returning the size of each group.

### TypedDict implication

No aggregation-call kwargs.

---

## 13. `all` / `any`

### Signatures

<code>Series.all(*, <span style="color:#c62828;font-weight:700">axis=0</span>, <span style="color:#c62828;font-weight:700">bool_only=False</span>, skipna=True, **kwargs)</code>  
<code>DataFrame.all(*, <span style="color:#c62828;font-weight:700">axis=0</span>, <span style="color:#c62828;font-weight:700">bool_only=False</span>, skipna=True, **kwargs)</code>  
<code>SeriesGroupBy.all(skipna=True)</code>  
<code>DataFrameGroupBy.all(skipna=True)</code>

`any` has the same signature pattern.

### TypedDict implication

```python
class SkipnaKwargs(TypedDict, total=False):
    skipna: bool

class AllAnyKwargs(SkipnaKwargs):
    pass
```

These are useful candidates if Stratum expands `_AGG_METHODS`.

---

## 14. `skew` / `kurt`

### Signatures

<code>Series.skew(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrame.skew(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.skew(skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrameGroupBy.skew(skipna=True, numeric_only=False, **kwargs)</code>

`kurt` follows the same shape:

<code>Series.kurt(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrame.kurt(*, <span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, numeric_only=False, **kwargs)</code>  
<code>SeriesGroupBy.kurt(skipna=True, numeric_only=False, **kwargs)</code>  
<code>DataFrameGroupBy.kurt(skipna=True, numeric_only=False, **kwargs)</code>

### TypedDict implication

Grouped core:

```python
class SkewKurtKwargs(NumericSkipnaKwargs):
    pass
```

The public signature also accepts `**kwargs`; whether Stratum should preserve arbitrary pass-through kwargs is a separate policy decision.

---

## 15. `quantile`

### Signatures

<code>Series.quantile(q=0.5, interpolation='linear')</code>  
<code>DataFrame.quantile(q=0.5, <span style="color:#c62828;font-weight:700">axis=0</span>, <span style="color:#c62828;font-weight:700">numeric_only=False</span>, interpolation='linear', <span style="color:#c62828;font-weight:700">method='single'</span>)</code>  
<code>SeriesGroupBy.quantile(q=0.5, interpolation='linear', <span style="color:#c62828;font-weight:700">numeric_only=False</span>)</code>  
<code>DataFrameGroupBy.quantile(q=0.5, interpolation='linear', <span style="color:#c62828;font-weight:700">numeric_only=False</span>)</code>

### Difference

- `q` and `interpolation` are conceptually shared.
- DataFrame has axis and cross-column quantile method machinery.
- GroupBy computes the requested quantile separately per group.

### TypedDict implication

```python
class QuantileKwargs(TypedDict, total=False):
    q: float | list[float]
    interpolation: str
    numeric_only: bool
```

---

## 16. `idxmin` / `idxmax`

### Signatures

<code>Series.idxmin(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, *args, **kwargs)</code>  
<code>DataFrame.idxmin(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, <span style="color:#c62828;font-weight:700">numeric_only=False</span>)</code>  
<code>SeriesGroupBy.idxmin(skipna=True)</code>  
<code>DataFrameGroupBy.idxmin(skipna=True, <span style="color:#c62828;font-weight:700">numeric_only=False</span>)</code>

`idxmax` follows the same pattern.

### TypedDict implication

SeriesGroupBy and DataFrameGroupBy differ:

```python
class IdxSeriesKwargs(SkipnaKwargs):
    pass

class IdxFrameKwargs(NumericSkipnaKwargs):
    pass
```

This is a concrete example where a SeriesGroupBy/DataFrameGroupBy split may be justified.

---

## 17. `agg` / `aggregate`

### Signatures

<code>Series.agg(func=None, <span style="color:#c62828;font-weight:700">axis=0</span>, *args, **kwargs)</code>  
<code>DataFrame.agg(func=None, <span style="color:#c62828;font-weight:700">axis=0</span>, *args, **kwargs)</code>  
<code>SeriesGroupBy.agg(func=None, *args, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, **kwargs)</code>  
<code>DataFrameGroupBy.agg(func=None, *args, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, **kwargs)</code>

`aggregate` is an alias of `agg` with the same public semantics.

### Difference

For GroupBy this is the generic aggregation dispatcher. `func` can be a callable/string/list, and DataFrameGroupBy also supports dict-shaped aggregation specs and named aggregation.

### Stratum implication

This is different from a direct method call:

```python
g.groupby("k").sum(min_count=2)
```

versus:

```python
g.groupby("k").agg("sum")
```

The logical representation should preserve whether it is representing:

1. a generic aggregation specification, or
2. a direct reducer plus reducer-specific kwargs,

unless Stratum has a proven normalization that preserves every kwarg and return-shape rule.

---

# PART II — frequently used methods that are NOT ordinary aggregations

These methods are important precisely because they should **not automatically be folded into `GroupByAggregateOp`** simply because they are methods on GroupBy.

---

## 18. `head`

**Category:** selection / filtration; not a reduction.

### Signatures

<code>Series.head(n=5)</code>  
<code>DataFrame.head(n=5)</code>  
<code>SeriesGroupBy.head(n=5)</code>  
<code>DataFrameGroupBy.head(n=5)</code>

### Difference

Same signature, different semantic scope:

- plain object: first `n` rows of the whole object;
- GroupBy: first `n` rows **of every group**, then concatenate while preserving original row order/index.

### Stratum implication

The signature gives no warning that semantics differ. Method name + caller family matters. This belongs in a selection/grouped-selection op, not an aggregation op.

---

## 19. `tail`

**Category:** selection / filtration.

### Signatures

<code>Series.tail(n=5)</code>  
<code>DataFrame.tail(n=5)</code>  
<code>SeriesGroupBy.tail(n=5)</code>  
<code>DataFrameGroupBy.tail(n=5)</code>

Same structural lesson as `head`: identical flags, group-scoped execution.

---

## 20. `nth`

**Category:** GroupBy positional selection.

### Signatures

<code>Series: — no plain `nth` method —</code>  
<code>DataFrame: — no plain `nth` method —</code>  
<code>SeriesGroupBy.nth -> property/indexer supporting nth(n, dropna=...)</code>  
<code>DataFrameGroupBy.nth -> property/indexer supporting nth(n, dropna=...)</code>

### Important API peculiarity

`nth` is exposed as a GroupBy indexer/property and supports both call and index syntax, e.g. conceptually:

```python
g.nth(0)
g.nth([0, 1])
g.nth[:-1]
```

`dropna` is available in call form but not index notation.

### Stratum implication

Do not model this as a normal reducer-method signature. It is structurally closer to an indexing operation.

---

## 21. `take`

**Category:** positional selection.

### GroupBy signatures

<code>SeriesGroupBy.take(indices, **kwargs)</code>  
<code>DataFrameGroupBy.take(indices, **kwargs)</code>

### Difference from `nth`

`take()` is strict positional selection and can raise when a requested position does not exist in a group; `nth()` is the more group-aware selection API and can simply omit missing positions.

### Typed flag shape

```python
class TakeKwargs(TypedDict, total=False):
    # public GroupBy signature exposes arbitrary compatibility kwargs
    pass
```

`indices` is a required operand, not a flag.

---

## 22. `get_group`

**Category:** GroupBy-only group selection.

### Signatures

<code>Series: — absent —</code>  
<code>DataFrame: — absent —</code>  
<code>SeriesGroupBy.get_group(name)</code>  
<code>DataFrameGroupBy.get_group(name)</code>

`name` is the group key to retrieve. This is not an aggregation.

---

## 23. `sample`

**Category:** selection; random sampling.

### Signatures

<code>Series.sample(n=None, frac=None, replace=False, weights=None, random_state=None, <span style="color:#c62828;font-weight:700">axis=None</span>, <span style="color:#c62828;font-weight:700">ignore_index=False</span>)</code>  
<code>DataFrame.sample(n=None, frac=None, replace=False, weights=None, random_state=None, <span style="color:#c62828;font-weight:700">axis=None</span>, <span style="color:#c62828;font-weight:700">ignore_index=False</span>)</code>  
<code>SeriesGroupBy.sample(n=None, frac=None, replace=False, weights=None, random_state=None)</code>  
<code>DataFrameGroupBy.sample(n=None, frac=None, replace=False, weights=None, random_state=None)</code>

### Difference

The core sampling flags are shared, but GroupBy performs the sample independently per group and does not expose the plain-object `axis` / `ignore_index` flags in this method.

---

## 24. `nlargest` / `nsmallest`

**Category:** value-based selection.

### Signatures

<code>Series.nlargest(n=5, keep='first')</code>  
<code>DataFrame: different API (`DataFrame.nlargest(n, columns, keep=...)`)</code>  
<code>SeriesGroupBy.nlargest(n=5, keep='first')</code>  
<code>DataFrameGroupBy: — no direct `nlargest` counterpart —</code>

and:

<code>Series.nsmallest(n=5, keep='first')</code>  
<code>DataFrame: different API (`DataFrame.nsmallest(n, columns, keep=...)`)</code>  
<code>SeriesGroupBy.nsmallest(n=5, keep='first')</code>  
<code>DataFrameGroupBy: — no direct `nsmallest` counterpart —</code>

### Stratum implication

This is a strong example of why a method-name registry cannot assume SeriesGroupBy and DataFrameGroupBy expose identical method sets.

---

# PART III — same-shape transformations

These operations generally return one output value for each input row/value rather than collapsing each group.

## 25. `cumsum`

### Signatures

<code>Series.cumsum(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, *args, **kwargs)</code>  
<code>DataFrame.cumsum(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, <span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>  
<code>SeriesGroupBy.cumsum(<span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>  
<code>DataFrameGroupBy.cumsum(<span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>

### Difference

GroupBy resets the cumulative state at each group boundary. It does **not** reduce each group to one row.

---

## 26. `cumprod`

### Signatures

<code>Series.cumprod(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, *args, **kwargs)</code>  
<code>DataFrame.cumprod(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, <span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>  
<code>SeriesGroupBy.cumprod(<span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>  
<code>DataFrameGroupBy.cumprod(<span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>

Same architectural category as `cumsum`.

---

## 27. `cummin` / `cummax`

### Signatures

<code>Series.cummin(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, *args, **kwargs)</code>  
<code>DataFrame.cummin(<span style="color:#c62828;font-weight:700">axis=0</span>, skipna=True, <span style="color:#c62828;font-weight:700">numeric_only=False</span>, *args, **kwargs)</code>  
<code>SeriesGroupBy.cummin(<span style="color:#c62828;font-weight:700">numeric_only=False</span>, **kwargs)</code>  
<code>DataFrameGroupBy.cummin(<span style="color:#c62828;font-weight:700">numeric_only=False</span>, **kwargs)</code>

`cummax` follows the same grouped shape.

### Stratum implication

Although names contain `min`/`max`, these are **transformations**, not reducers. They should not share the `GroupByAggregateOp` family merely because the scalar reducer names are related.

---

## 28. `cumcount`

**Category:** GroupBy-only transformation.

### Signatures

<code>Series: — absent —</code>  
<code>DataFrame: — absent —</code>  
<code>SeriesGroupBy.cumcount(ascending=True)</code>  
<code>DataFrameGroupBy.cumcount(ascending=True)</code>

It numbers rows inside each group from `0` upward (or downward when `ascending=False`).

---

## 29. `ngroup`

**Category:** GroupBy-only transformation / group labelling.

### Signatures

<code>Series: — absent —</code>  
<code>DataFrame: — absent —</code>  
<code>SeriesGroupBy.ngroup(ascending=True)</code>  
<code>DataFrameGroupBy.ngroup(ascending=True)</code>

Difference from `cumcount`:

```text
cumcount -> number rows WITHIN each group
ngroup   -> number the GROUPS themselves
```

---

## 30. `rank`

**Category:** transformation.

### Signatures

<code>Series.rank(<span style="color:#c62828;font-weight:700">axis=0</span>, method='average', <span style="color:#c62828;font-weight:700">numeric_only=False</span>, na_option='keep', ascending=True, pct=False)</code>  
<code>DataFrame.rank(<span style="color:#c62828;font-weight:700">axis=0</span>, method='average', <span style="color:#c62828;font-weight:700">numeric_only=False</span>, na_option='keep', ascending=True, pct=False)</code>  
<code>SeriesGroupBy.rank(method='average', ascending=True, na_option='keep', pct=False)</code>  
<code>DataFrameGroupBy.rank(method='average', ascending=True, na_option='keep', pct=False)</code>

### Difference

The actual ranking-policy flags are perfectly shared:

```text
method
ascending
na_option
pct
```

Plain Series/DataFrame add `axis` and `numeric_only`; GroupBy ranks independently within each group.

### TypedDict implication

```python
class RankKwargs(TypedDict, total=False):
    method: str
    ascending: bool
    na_option: str
    pct: bool
```

---

## 31. `shift`

**Category:** transformation.

### Signatures

<code>Series.shift(periods=1, freq=None, <span style="color:#c62828;font-weight:700">axis=0</span>, fill_value=&lt;no_default&gt;, <span style="color:#c62828;font-weight:700">suffix=None</span>)</code>  
<code>DataFrame.shift(periods=1, freq=None, <span style="color:#c62828;font-weight:700">axis=0</span>, fill_value=&lt;no_default&gt;, suffix=None)</code>  
<code>SeriesGroupBy.shift(periods=1, freq=None, fill_value=&lt;no_default&gt;, suffix=None)</code>  
<code>DataFrameGroupBy.shift(periods=1, freq=None, fill_value=&lt;no_default&gt;, suffix=None)</code>

### Difference

GroupBy shifts independently within each group and no longer exposes an `axis` parameter in pandas 3.0.2.

### TypedDict implication

```python
class GroupShiftKwargs(TypedDict, total=False):
    periods: int | list[int]
    freq: object | None
    fill_value: object
    suffix: str | None
```

---

## 32. `diff`

**Category:** transformation.

### Signatures

<code>Series.diff(periods=1)</code>  
<code>DataFrame.diff(periods=1, <span style="color:#c62828;font-weight:700">axis=0</span>)</code>  
<code>SeriesGroupBy.diff(periods=1)</code>  
<code>DataFrameGroupBy.diff(periods=1)</code>

### Difference

The GroupBy operation resets the comparison at each group boundary. `DataFrame.diff` exposes axis choice; grouped diff is row-wise within each group.

---

## 33. `pct_change`

**Category:** transformation.

### Signatures

<code>Series.pct_change(periods=1, fill_method=None, freq=None, **kwargs)</code>  
<code>DataFrame.pct_change(periods=1, fill_method=None, freq=None, **kwargs)</code>  
<code>SeriesGroupBy.pct_change(periods=1, fill_method=None, freq=None)</code>  
<code>DataFrameGroupBy.pct_change(periods=1, fill_method=None, freq=None)</code>

### Important pandas 3.0 note

`fill_method` must be `None` and is retained only as transitional API surface; older fill behaviour should be performed explicitly before `pct_change`.

---

## 34. `ffill` / `bfill`

**Category:** missing-value transformation.

### Signatures

Plain objects expose a broader API:

<code>Series.ffill(*, <span style="color:#c62828;font-weight:700">axis=None</span>, <span style="color:#c62828;font-weight:700">inplace=False</span>, limit=None, <span style="color:#c62828;font-weight:700">limit_area=None</span>)</code>  
<code>DataFrame.ffill(*, <span style="color:#c62828;font-weight:700">axis=None</span>, <span style="color:#c62828;font-weight:700">inplace=False</span>, limit=None, <span style="color:#c62828;font-weight:700">limit_area=None</span>)</code>  
<code>SeriesGroupBy.ffill(limit=None)</code>  
<code>DataFrameGroupBy.ffill(limit=None)</code>

`bfill` has the analogous grouped signature:

<code>SeriesGroupBy.bfill(limit=None)</code>  
<code>DataFrameGroupBy.bfill(limit=None)</code>

### Difference

GroupBy filling is constrained to group boundaries and exposes only `limit` at the grouped method level.

---

# PART IV — function-application methods

## 35. `transform`

**Category:** same-shape function application.

### Signatures

<code>Series.transform(func, <span style="color:#c62828;font-weight:700">axis=0</span>, *args, **kwargs)</code>  
<code>DataFrame.transform(func, <span style="color:#c62828;font-weight:700">axis=0</span>, *args, **kwargs)</code>  
<code>SeriesGroupBy.transform(func, *args, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, **kwargs)</code>  
<code>DataFrameGroupBy.transform(func, *args, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, **kwargs)</code>

### Semantic contract

For GroupBy, the result is aligned back to the original grouped rows: this is fundamentally different from an aggregation that produces one row/value per group.

### Stratum implication

A separate `GroupByTransformOp` family would make the shape contract explicit.

---

## 36. `apply`

**Category:** generic function application; output shape is not fixed.

### Signatures

<code>Series.apply(func, args=(), *, <span style="color:#c62828;font-weight:700">by_row='compat'</span>, **kwargs)</code>  
<code>DataFrame.apply(func, <span style="color:#c62828;font-weight:700">axis=0</span>, <span style="color:#c62828;font-weight:700">raw=False</span>, <span style="color:#c62828;font-weight:700">result_type=None</span>, args=(), <span style="color:#c62828;font-weight:700">by_row='compat'</span>, <span style="color:#c62828;font-weight:700">engine=None</span>, <span style="color:#c62828;font-weight:700">engine_kwargs=None</span>, **kwargs)</code>  
<code>SeriesGroupBy.apply(func, *args, **kwargs)</code>  
<code>DataFrameGroupBy.apply(func, *args, <span style="color:#c62828;font-weight:700">include_groups=False</span>, **kwargs)</code>

### Difference

This is one of the least uniform same-name APIs in pandas.

- `Series.apply` normally applies to Series values.
- `DataFrame.apply` works along an axis and has substantial execution/result-shape controls.
- `SeriesGroupBy.apply` calls the function group-wise.
- `DataFrameGroupBy.apply` calls it on sub-DataFrames and has `include_groups` semantics.

### Stratum implication

Do not try to squeeze `apply` into the same flag hierarchy as reducers. Its output type is dynamic and its callable semantics differ substantially.

---

## 37. `filter` — same name, radically different semantics

### Signatures

<code>Series.filter(<span style="color:#c62828;font-weight:700">items=None</span>, <span style="color:#c62828;font-weight:700">like=None</span>, <span style="color:#c62828;font-weight:700">regex=None</span>, <span style="color:#c62828;font-weight:700">axis=None</span>)</code>  
<code>DataFrame.filter(<span style="color:#c62828;font-weight:700">items=None</span>, <span style="color:#c62828;font-weight:700">like=None</span>, <span style="color:#c62828;font-weight:700">regex=None</span>, <span style="color:#c62828;font-weight:700">axis=None</span>)</code>  
<code>SeriesGroupBy.filter(<span style="color:#c62828;font-weight:700">func</span>, <span style="color:#c62828;font-weight:700">dropna=True</span>, *args, **kwargs)</code>  
<code>DataFrameGroupBy.filter(<span style="color:#c62828;font-weight:700">func</span>, <span style="color:#c62828;font-weight:700">dropna=True</span>, *args, **kwargs)</code>

### Critical difference

These are not variants of the same operation:

- plain `.filter(...)` filters **axis labels**;
- GroupBy `.filter(func, ...)` evaluates a predicate on **whole groups** and keeps/drops groups.

For an IR, method name alone is insufficient; caller family is semantically essential.

---

## 38. `pipe`

**Category:** chaining helper.

### Signatures

<code>Series.pipe(func, *args, **kwargs)</code>  
<code>DataFrame.pipe(func, *args, **kwargs)</code>  
<code>SeriesGroupBy.pipe(func, *args, **kwargs)</code>  
<code>DataFrameGroupBy.pipe(func, *args, **kwargs)</code>

Same signature shape, but GroupBy passes the **whole GroupBy object** to `func`; this is not group-wise reduction.

---

# PART V — additional GroupBy computations worth recognizing

## 39. `unique`

**Category:** SeriesGroupBy-only per-group collection result.

<code>Series.unique()</code>  
<code>DataFrame: — no equivalent `unique()` method —</code>  
<code>SeriesGroupBy.unique()</code>  
<code>DataFrameGroupBy: — no direct counterpart —</code>

The grouped result is one collection of unique values per group, not a scalar reducer in the narrow sense.

---

## 40. `ohlc`

**Category:** GroupBy summary; multi-output reduction.

<code>Series: — absent —</code>  
<code>DataFrame: — absent —</code>  
<code>SeriesGroupBy.ohlc()</code>  
<code>DataFrameGroupBy.ohlc()</code>

It produces four outputs per grouped value (`open`, `high`, `low`, `close`). It is summary-like but does not obey the ordinary “one scalar per input column” reducer shape.

---

## 41. `describe`

**Category:** descriptive summary; multi-statistic output.

Typical grouped signature:

<code>SeriesGroupBy.describe(percentiles=None, include=None, exclude=None)</code>  
<code>DataFrameGroupBy.describe(percentiles=None, include=None, exclude=None)</code>

This produces many statistics at once, so it should not be treated as an ordinary single reducer in the IR.

---

# PART VI — recommended Stratum decomposition

## 42. Do not make `GroupByAggregateOp` mean “any method after groupby”

A clean architecture is to classify by **shape/semantic contract**:

| Family | Examples | Result-shape idea |
|---|---|---|
| `GroupByAggregateOp` | `sum`, `mean`, `min`, `max`, `std`, `var`, `count`, `nunique`, `first`, `last`, `prod`, `sem`, `all`, `any`, `quantile`, `skew`, `kurt`, `idxmin`, `idxmax` | one reduced result per group/column (with known exceptions such as multi-q quantile) |
| `GroupBySelectionOp` | `head`, `tail`, `nth`, `take`, `get_group`, `sample`, `nlargest`, `nsmallest` | subset/reordering of original rows/values |
| `GroupByTransformOp` | `cumsum`, `cumprod`, `cummin`, `cummax`, `cumcount`, `ngroup`, `rank`, `shift`, `diff`, `pct_change`, `ffill`, `bfill`, `transform` | generally aligned/same-length result |
| `GroupByApplyOp` | `apply`, `filter`, possibly `pipe` | callable-driven / dynamic result contract |
| specialised summary | `ohlc`, `describe`, `value_counts`, `unique` | collection or multi-statistic result |

This makes backend lowering far easier because each logical family advertises a much stronger output contract.

---

## 43. Recommended aggregation flag bundles

Rather than one enormous `TypedDict`, use small reusable bundles and compose method-specific dictionaries.

```python
from typing import TypedDict


class NumericOnlyKwargs(TypedDict, total=False):
    numeric_only: bool


class SkipnaKwargs(TypedDict, total=False):
    skipna: bool


class DropnaKwargs(TypedDict, total=False):
    dropna: bool


class MinCountKwargs(TypedDict, total=False):
    min_count: int


class DdofKwargs(TypedDict, total=False):
    ddof: int


class EngineKwargs(TypedDict, total=False):
    engine: str | None
    engine_kwargs: dict[str, object] | None


class NumericSkipnaKwargs(NumericOnlyKwargs, SkipnaKwargs):
    pass
```

Then method families:

```python
class SumKwargs(NumericSkipnaKwargs, MinCountKwargs, EngineKwargs):
    pass


class ProdKwargs(NumericSkipnaKwargs, MinCountKwargs):
    pass


class MinMaxKwargs(NumericSkipnaKwargs, MinCountKwargs, EngineKwargs):
    pass


class MeanKwargs(NumericSkipnaKwargs, EngineKwargs):
    pass


class MedianKwargs(NumericSkipnaKwargs):
    pass


class StdVarKwargs(NumericSkipnaKwargs, DdofKwargs, EngineKwargs):
    pass


class SemKwargs(NumericSkipnaKwargs, DdofKwargs):
    pass


class FirstLastKwargs(NumericSkipnaKwargs, MinCountKwargs):
    pass


class NuniqueKwargs(DropnaKwargs):
    pass


class AllAnyKwargs(SkipnaKwargs):
    pass
```

### Why bundles are better than a single base class

There is no single nontrivial flag that is valid for every aggregation:

```text
count()      -> no kwargs
size()       -> no kwargs
nunique()    -> dropna
all()/any()  -> skipna
median()     -> numeric_only + skipna
sum()        -> numeric_only + skipna + min_count + engine
std()/var()  -> numeric_only + skipna + ddof + engine
```

So a giant base such as:

```python
class AggregateKwargs(TypedDict, total=False):
    numeric_only: bool
    skipna: bool
    min_count: int
    ddof: int
    engine: str | None
    engine_kwargs: dict[str, object] | None
    dropna: bool
```

would be easy to implement but **too permissive**: it would type-check invalid combinations such as `count(ddof=1)` or `nunique(min_count=2)`.

Small orthogonal bundles + method-specific composition give stronger static constraints without excessive duplication.

---

## 44. Defaults should be metadata, not TypedDict inheritance

Because defaults differ even when the key type is identical:

```text
sum.min_count   = 0
prod.min_count  = 0
min.min_count   = -1
max.min_count   = -1
first.min_count = -1
last.min_count  = -1
```

A clean canonical defaults table would look conceptually like:

```python
PANDAS_GROUPBY_DEFAULTS = {
    "sum": {"numeric_only": False, "min_count": 0, "skipna": True,
            "engine": None, "engine_kwargs": None},
    "prod": {"numeric_only": False, "min_count": 0, "skipna": True},
    "min": {"numeric_only": False, "min_count": -1, "skipna": True,
            "engine": None, "engine_kwargs": None},
    "max": {"numeric_only": False, "min_count": -1, "skipna": True,
            "engine": None, "engine_kwargs": None},
    "mean": {"numeric_only": False, "skipna": True,
             "engine": None, "engine_kwargs": None},
    "std": {"ddof": 1, "numeric_only": False, "skipna": True,
            "engine": None, "engine_kwargs": None},
    "var": {"ddof": 1, "numeric_only": False, "skipna": True,
            "engine": None, "engine_kwargs": None},
    "sem": {"ddof": 1, "numeric_only": False, "skipna": True},
    "first": {"numeric_only": False, "min_count": -1, "skipna": True},
    "last": {"numeric_only": False, "min_count": -1, "skipna": True},
    "nunique": {"dropna": True},
    "all": {"skipna": True},
    "any": {"skipna": True},
}
```

Whether Stratum actually materializes this table depends on the semantic goal:

### Option A — preserve only explicit user kwargs

Store:

```python
method="sum"
method_kwargs={"min_count": 2}
```

and let the backend supply all omitted defaults.

**Advantage:** lean representation; mirrors source program closely.  
**Risk:** pandas and polars defaults/semantics can differ, so omitted flags may not be backend-independent.

### Option B — canonicalize effective semantics

Store:

```python
method="sum"
method_kwargs={
    "numeric_only": False,
    "min_count": 2,
    "skipna": True,
    "engine": None,
    "engine_kwargs": None,
}
```

**Advantage:** the logical IR fully captures pandas semantics before backend lowering.  
**Risk:** more coupling to pandas API/version and more translation work for other backends.

For Stratum's goal of reproducing pandas semantics on alternative backends, **Option B is semantically stronger**, but a hybrid is possible: retain explicit kwargs plus a semantic-versioned defaults policy in the lowering layer.

---

## 45. What the current Stratum representation is missing

Current direct-call extraction conceptually does:

```python
# grouped.sum(min_count=2, skipna=False)
aggregations = "sum"
```

but the physical pandas implementation ultimately executes conceptually:

```python
obj.groupby(grouping, **groupby_kwargs).agg(aggregations)
```

Therefore the direct method's own args/kwargs are not represented by the current `AggregateOp` fields.

A minimally complete logical representation needs something equivalent to:

```python
method: str | None
aggregation_spec: ... | None
aggregation_kwargs: Mapping[str, object]
```

or a discriminated representation such as:

```python
class DirectAggregation(TypedDict):
    method: str
    kwargs: Mapping[str, object]


class GenericAggregation(TypedDict):
    spec: object
    args: tuple[object, ...]
    kwargs: Mapping[str, object]
```

The important design point is the distinction between:

```text
groupby construction kwargs
        versus
direct aggregation-method kwargs
        versus
generic .agg(...) specification/kwargs
```

These are three different layers of state.

---

# PART VII — practical method registry for Stratum

## 46. Current direct reducer set in Stratum

The current repository snapshot recognizes:

```python
{
    "sum", "mean", "count", "min", "max", "median", "std", "var",
    "first", "last", "prod", "size", "nunique", "sem",
}
```

These naturally remain in `GroupByAggregateOp`.

## 47. Strong candidates for later reducer coverage

```python
{
    "all", "any", "skew", "kurt", "quantile", "idxmin", "idxmax",
}
```

Potentially also `cov` / `corr`, but those deserve separate review because their result shape and Series-vs-DataFrame contracts are more complicated than the ordinary one-scalar-per-column reducers.

## 48. Methods that should NOT be added to `_AGG_METHODS`

```python
{
    "head", "tail", "nth", "take", "get_group", "sample",
    "nlargest", "nsmallest",
    "cumsum", "cumprod", "cummin", "cummax", "cumcount", "ngroup",
    "rank", "shift", "diff", "pct_change", "ffill", "bfill",
    "transform", "apply", "filter", "pipe",
}
```

They are useful GroupBy methods, but they have different shape/semantic contracts.

---

# PART VIII — concise implementation takeaway

For the specific TypedDict problem, the cleanest mental model is:

```text
GroupBy method call
│
├── groupby_kwargs
│     by / level / sort / observed / dropna / ...
│
└── operation
      │
      ├── reducer
      │     method = "sum" | "mean" | ...
      │     method_kwargs = method-specific TypedDict
      │
      ├── generic agg
      │     spec
      │     args
      │     kwargs
      │
      ├── selection
      │     head / tail / nth / ...
      │
      ├── transform
      │     cumsum / rank / shift / transform / ...
      │
      └── apply-like
            apply / filter / pipe
```

The most important implementation rule is:

> **Share parameter bundles only where pandas actually shares the parameter contract. Do not create one permissive “all aggregate kwargs” TypedDict.**

And the second is:

> **Do not use TypedDict inheritance to model defaults. Use it to model valid keys/types; model defaults separately if Stratum needs canonical backend-independent semantics.**

---

## Source basis

This document was prepared against the pandas 3.0.x API surface and has now been aligned specifically to pandas 3.0.2, the version pinned by Stratum and the current `Aram164/stratum` `feature/fold-missing-masks` snapshot of `stratum/optimizer/ir/_aggregation_ops.py` inspected on 2026-08-18.


## Legacy Job provenance

### status

current
