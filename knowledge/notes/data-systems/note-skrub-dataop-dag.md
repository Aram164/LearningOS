---
id: note-skrub-dataop-dag
type: note
title: "skrub DataOp DAG — Complete Reference"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-skrub]
sources: []
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Libraries/skrub/skrub-DataOp-DAG-Reference.md` (legacy tree).

# skrub DataOp DAG — Complete Reference

> Everything we've learned about how skrub builds and evaluates lazy computation graphs.
> This is the foundation Stratum builds upon — it intercepts these DAGs and compiles them
> instead of letting skrub's default evaluator walk them.

---

## 1. The Core Idea

skrub implements **lazy evaluation**. When you write operations on a DataOp (like `df.dropna()` or `df + 1`), nothing executes. Instead, each operation creates a **node** in a directed acyclic graph (DAG). The DAG records *what* to compute. Actual computation only happens later, when you explicitly evaluate the graph (via `.skb.eval()` or when a learner runs `fit`/`predict`).

This separation of "what to do" from "doing it" is exactly what makes optimization possible — Stratum can inspect and rewrite the DAG before execution.

---

## 2. The Two Core Classes

### `DataOp` — The User-Facing Proxy

**File:** `skrub/_data_ops/_data_ops.py`, line 549

`DataOp` is what the user interacts with. It's an **intentionally empty shell** — almost no methods or attributes live on it directly. This emptiness is deliberate: if `DataOp` had a real `.groupby` method, then `df.groupby()` would call that method instead of creating a DAG node. By keeping the class empty, all attribute accesses fall through to `__getattr__`, which creates graph nodes.

Key attributes:
- `_skrub_impl` — points to the actual `DataOpImpl` node (the graph node this DataOp wraps)
- `.skb` — a namespace providing skrub-specific methods (`.skb.eval()`, `.skb.apply()`, etc.)

### `DataOpImpl` — The Graph Node Base Class

**File:** `skrub/_data_ops/_data_ops.py`, line 189

Every node type in the DAG is a subclass of `DataOpImpl`. Each subclass defines:
- `_fields` — a list of attribute names (the node's inputs/children)
- `compute(self, e, mode, environment)` — how to produce this node's result once all children are resolved

`DataOpImpl` uses `__init_subclass__` (line 233) to automatically generate an `__init__` for each subclass based on its `_fields`. Subclasses must NOT define their own `__init__`.

---

## 3. Node Types (DataOpImpl Subclasses)

### `Var` (line 913)
```
_fields = ["name", "value"]
```
The entry point — a pipeline input variable. Created via `skrub.var("df", sample_data)`.
- `name`: string identifier (used as key in the environment dict at eval time)
- `value`: optional sample data (used for previews and tab-completion)

At eval time: looks up `name` in the environment dict and returns the real data.

### `GetAttr` (line 1524)
```
_fields = ["source_object", "attr_name"]
```
Represents attribute access: `x.something` where `something` is not called.
- `source_object`: the DataOp being accessed
- `attr_name`: string name of the attribute

At eval time: `getattr(evaluated_source, attr_name)`.

Note: GetAttr nodes rarely survive in the final DAG because `__call__` squashes them into `CallMethod` (see Section 4).

### `CallMethod` (line 1603)
```
_fields = ["obj", "method_name", "args", "kwargs"]
```
The most common node type. Represents `obj.method(args, kwargs)`.
- `obj`: the DataOp whose method is being called
- `method_name`: string name of the method
- `args`: tuple of positional arguments (may contain DataOps or plain values)
- `kwargs`: dict of keyword arguments (may contain DataOps or plain values)

At eval time: `getattr(evaluated_obj, method_name)(*evaluated_args, **evaluated_kwargs)`.

### `Call` (line 1550)
```
_fields = ["func", "args", "kwargs", "globals", "closure", "defaults", "kwdefaults"]
```
Represents a standalone function call: `f(x, y)`. Used when calling `@skrub.deferred` functions.
- `func`: the function object itself
- `args`, `kwargs`: arguments (may contain DataOps)
- `globals`, `closure`, `defaults`, `kwdefaults`: for `@deferred` functions that capture DataOps in their scope

At eval time: calls the function with evaluated arguments.

### `GetItem` (line 1537)
```
_fields = ["container", "key"]
```
Represents indexing: `x["column_name"]` or `x[0]`.

At eval time: `evaluated_container[evaluated_key]`.

### `BinOp` (line 1911)
```
_fields = ["left", "right", "op"]
```
Represents binary operations: `x + 1`, `x > 0`, `x & mask`.
- `left`, `right`: operands (either can be DataOps or plain values)
- `op`: a function from Python's `operator` module (e.g., `operator.__add__`)

At eval time: `op(evaluated_left, evaluated_right)`.

### `UnaryOp` (line 1922)
```
_fields = ["operand", "op"]
```
Represents unary operations: `-x`, `~x`, `abs(x)`.

At eval time: `op(evaluated_operand)`.

### `Value` (line 1165)
```
_fields = ["value"]
```
Wraps a constant value into the DAG (via `skrub.as_data_op(something)`).

At eval time: returns the value as-is.

---

## 4. How User Code Becomes DAG Nodes — The Interception Chain

### 4.1 Attribute Access → `__getattr__` (line 577)

When you write `df.dropna` (without parentheses), Python doesn't find `dropna` in DataOp's class dict, so it calls:

```python
DataOp.__getattr__(self, "dropna")
```

This creates and returns:
```python
DataOp(GetAttr(source_object=self, attr_name="dropna"))
```

### 4.2 Method Call → `__call__` squashes GetAttr + Call into CallMethod (line 603)

When you write `df.dropna()` (with parentheses), two things happen:
1. `df.dropna` → `__getattr__` → returns a DataOp wrapping `GetAttr`
2. `(...)` on that result → `__call__` runs on the GetAttr DataOp

Inside `__call__`:
```python
def __call__(self, *args, **kwargs):
    impl = self._skrub_impl
    if isinstance(impl, GetAttr):
        # SQUASH: merge GetAttr + Call into a single CallMethod node
        return DataOp(CallMethod(impl.source_object, impl.attr_name, args, kwargs))
    # If not a GetAttr (e.g., calling a DataOp that wraps a function):
    return DataOp(Call(self, args, kwargs, ...))
```

The squashing optimization keeps the DAG simpler — instead of two nodes (GetAttr → Call), you get one (CallMethod).

### 4.3 Operators → Dynamically Injected Dunder Methods (lines 759–793)

Python bypasses `__getattr__` for magic methods (`__add__`, `__eq__`, etc.). It only checks the class's `__dict__` directly. So these methods must be real class methods.

At module import time, a loop runs:
```python
def _make_bin_op(op_name):
    def op(self, right):
        return DataOp(BinOp(self, right, getattr(operator, op_name)))
    op.__name__ = op_name
    return checked_data_op_constructor(op)

for op_name in _BIN_OPS:  # ["__add__", "__eq__", "__gt__", ...]
    setattr(DataOp, op_name, _make_bin_op(op_name))
```

This injects ~30 operator methods into `DataOp.__dict__`. Each one creates a `BinOp` node.

**Why two nested `def`s (the factory pattern):** The outer function (`_make_bin_op`) is a factory that runs at import time. The inner function (`op`) is the product — the actual method, which runs later when the user writes `df + 1`. The factory creates a new scope that captures the correct `op_name` for each operator. Without the factory, all operators would share the last loop value due to Python's closure semantics.

**Why `self` and `right` work:** They're just parameter names in a function definition. They get their values later when the function is called (e.g., when Python executes `DataOp.__add__(df, 1)`).

### 4.4 Indexing → `__getitem__` (line 598)

```python
def __getitem__(self, key):
    return DataOp(GetItem(self, key))
```

`df["age"]` creates a `GetItem` node.

### 4.5 External Functions → `@skrub.deferred` (line 1640)

For functions that aren't methods on the data (like `np.log1p`), you wrap them with `@skrub.deferred`. When called with a DataOp argument, they create a `Call` node instead of executing immediately.

```python
@skrub.deferred
def transform(df):
    return np.log1p(df)

result = transform(x)  # creates Call(func=transform, args=(x,), ...)
```

### 4.6 Prevented Operations

Some operations are explicitly forbidden because they'd break the lazy model:
- `__setitem__` / `__setattr__` (line 643/658) → raise TypeError ("don't modify in-place")
- `__bool__` (line 668) → raise TypeError ("can't eagerly check boolean")
- `__iter__` (line 675) → raise TypeError ("can't eagerly iterate")
- `__contains__` (line 682) → raise TypeError ("can't eagerly test membership")

---

## 5. The `checked_data_op_constructor` Decorator (line 320)

Almost every method that creates a DataOp is wrapped with this decorator. It runs **eagerly** (immediately after node creation) and does two things:

1. **Validates** the new node:
   - Checks for duplicate variable names (`find_conflicts`)
   - Checks that raw DataFrames aren't passed where DataOps are expected (`_find_dataframe`)
   - Checks choice consistency (`check_choices_before_Xy`)

2. **Computes the preview**: calls `evaluate(data_op, mode="preview")` on the sample data. This gives immediate feedback — if your pipeline is broken, you find out right when you write the code, not later at eval time.

---

## 6. The `__init_subclass__` Mechanism (line 233)

When Python encounters a class like:
```python
class CallMethod(DataOpImpl):
    _fields = ["obj", "method_name", "args", "kwargs"]
```

`DataOpImpl.__init_subclass__()` fires and generates an `__init__` for `CallMethod`:
```python
def __init__(self, obj, method_name, args, kwargs):
    self.obj = obj
    self.method_name = method_name
    self.args = args
    self.kwargs = kwargs
    self.results = {}       # cache for computed results per mode
    self.errors = {}        # cache for errors per mode
    self.metadata = {}      # timing info, env key, etc.
    self._creation_stack_lines = ...  # where in user code this was created
```

This is why no subclass manually defines `__init__` — they all get one generated from `_fields`.

---

## 7. Parent/Child Terminology

In this DAG:
- **Child** = an input / dependency. "What I need before I can compute."
- **Parent** = a consumer. "Who uses my output."

Example for `df.dropna() + 1`:
```
BinOp(__add__)          ← root (no parents)
├── child: CallMethod("dropna")
│   └── child: Var("df")    ← leaf (no children)
└── child: 1 (plain value, not a node — no edge)
```

Evaluation happens **bottom-up**: leaves (Var) first, then their parents (CallMethod), then their parents (BinOp). Each node computes only after all its children have been resolved.

---

## 8. Evaluation — The `_evaluation.py` Module

### Architecture Split

| File | Role |
|------|------|
| `_data_ops.py` | Defines node types + `compute()` for each (what to do) |
| `_evaluation.py` | Traverses the DAG, orchestrates execution order (when to do it) |

### `_DataOpTraversal` (line 90) — The Traversal Engine

Uses a **non-recursive, stack-based DFS** with Python generators. Each node's handler is a generator that `yield`s children it needs evaluated, then gets the results sent back via `.send()`.

```python
def handle_data_op(self, data_op):
    impl = data_op._skrub_impl
    evaluated_attributes = {}
    for name in impl._fields:
        attr = getattr(impl, name)
        evaluated_attributes[name] = yield attr  # "evaluate this, give me the result"
    return self.compute_result(data_op, evaluated_attributes)
```

Why generators instead of recursion: avoids blowing the call stack on deep DAGs, and produces shorter tracebacks for users.

### `_Evaluator` (line 274) — The Concrete Evaluator

Subclass of `_DataOpTraversal` that actually computes results:
- Checks result cache first (avoids recomputing shared nodes)
- Handles environment lookups (for X, y, named variables)
- Calls `DataOpImpl.compute()` once all children are resolved
- Stores results in `node.results[mode]`

### Evaluation Modes

- `"preview"` — runs on sample data during DAG construction
- `"fit"` — training time
- `"predict"` — inference time
- `"fit_transform"` — fit + transform in one pass

---

## 9. Stratum's Graph Extraction — `build_graph()` 

**File:** `stratum/utils/_skrub_graph.py`

Stratum doesn't use skrub's generator-based traversal. It has its own simpler DFS that only extracts the DAG topology (no evaluation):

### `_collect_child_data_ops(value)` — Recursive Filter

Given any field value, yields only the DataOps inside it:
- If value IS a DataOp → yield it
- If value is a tuple/list/set/frozenset → recurse into each item
- If value is a dict → recurse into each value
- If value is a Choice → recurse into outcomes
- If value is a Match → recurse into choice + outcome_mapping
- Anything else (string, int, function, None) → yields nothing

Uses Python `yield` (generator) to produce DataOps one at a time without building intermediate lists. `yield from` delegates to recursive calls.

### `build_graph(data_op)` — Iterative DFS

1. Starts from root DataOp, pushes onto stack
2. Pops nodes, skips if visited (handles DAG sharing)
3. For each node: inspects `_fields`, calls `_collect_child_data_ops` on each field value
4. Records edges in both directions: `children[node] = [inputs]`, `parents[node] = [consumers]`
5. Pushes unvisited children onto stack
6. Renumbers all IDs from raw `id()` values to clean integers `0, 1, 2, ...`

Returns: `{"nodes": {id: DataOp}, "children": {id: [child_ids]}, "parents": {id: [parent_ids]}}`

This is what Stratum's optimizer consumes — a clean adjacency list of the computation graph.

---

## 10. The `_data_ops/` Package — File Map

| File | Purpose |
|------|---------|
| `_data_ops.py` | DataOp proxy, DataOpImpl base, all node types, dynamic method injection |
| `_evaluation.py` | Graph traversal engine, _Evaluator, clone, needs_eval |
| `_skrub_namespace.py` | The `.skb` namespace (eval, apply, preview, make_learner, etc.) |
| `_estimator.py` | sklearn-compatible fit/predict interface wrapping a DataOp plan |
| `_choosing.py` | Choice/Match for hyperparameter search |
| `_inspection.py` | Graph visualization and node reports |
| `_subsampling.py` | Subsampling logic for large data previews |
| `_utils.py` | Helper constants and functions (NULL sentinel, FITTED_PREDICTOR_METHODS) |

---

## 11. Connection to Stratum

Stratum intercepts the DAG **before** skrub's `_Evaluator` runs. The pipeline is:

```
User code → DataOp proxy → DAG of DataOpImpl nodes
                                    ↓
                        Stratum's build_graph() extracts topology
                                    ↓
                        Stratum IR (intermediate representation)
                                    ↓
                        Logical Optimizer:
                          - CSE (common subexpression elimination)
                          - Predicate pushdown
                          - Operator lowering (decompose TableVectorizer)
                          - Operator selection (choose Plans/Programming/rust/Rust/Polars/sklearn backend)
                                    ↓
                        Runtime:
                          - Parallelism planning
                          - Buffer pool + intermediate caching
                          - Rust kernels via PyO3
                                    ↓
                        Actual computed result
```

The node types from `_data_ops.py` are the "language" that both systems understand. skrub evaluates them naively (one at a time, in Python). Stratum compiles them into an optimized execution plan.
