---
id: note-skrub-evaluation-engine
type: note
title: "skrub Evaluation Engine — Complete Reference"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-skrub]
sources: []
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Libraries/skrub/skrub-Evaluation-Engine-Reference.md` (legacy tree).

# skrub Evaluation Engine — Complete Reference

> How skrub's `_DataOpTraversal` and `_Evaluator` turn a lazy DAG of DataOp nodes
> into actual computed results. This is the execution engine that Stratum replaces
> with its own compiler + optimizer + Rust runtime.
>
> **Source file:** `skrub/_data_ops/_evaluation.py`
>
> **Prerequisite reading:** `Plans/Libraries/skrub/skrub-DataOp-DAG-Reference.md` (covers how the DAG is built)

---

## 1. The Problem Being Solved

You have a DAG of nodes. Each node holds **references to other nodes** (DataOps), not
actual data. At evaluation time, you need to turn those references into real values
and compute results bottom-up.

The challenge: a node's fields can hold DataOps directly, or DataOps buried inside
tuples, dicts, sklearn estimators, or even nested combinations of all of these.
The evaluator must recursively dig through everything, resolve all DataOps to real
values, and then let each node compute its result using only real values.

---

## 2. The Architecture: Three Layers

The engine cleanly separates three concerns:

| Layer | Responsibility | Where |
|-------|---------------|-------|
| **Engine** (`run` loop) | Drives the stack, dispatches by type, pipes results between generators | `_DataOpTraversal.run()` |
| **Handlers** (generators) | Know how to process one type of thing (DataOp, tuple, dict, plain value) | `handle_data_op`, `handle_seq`, `handle_mapping`, `handle_value`, etc. |
| **Node logic** (`compute`) | Knows how to produce a result given fully resolved inputs | `DataOpImpl.compute(e, mode, environment)` — lives in `_data_ops.py` |

The engine never knows what a node does. The node never knows about the graph structure.
The handlers are the bridge — they know which fields a node has, but delegate the actual
resolution to the engine via `yield`.

---

## 3. The `e` Variable — Separating Graph from Data

Every node's `compute()` method receives an argument `e` which is a `SimpleNamespace`.
It contains the **already-evaluated** values for every field of that node.

Example for a `CallMethod(obj=Var("df"), method_name="dropna", args=(), kwargs={})` node:

```
self.obj         = DataOp(Var("df"))     ← graph reference (unevaluated)
self.method_name = "dropna"               ← already a plain value
self.args        = ()                     ← might contain DataOps in other cases
self.kwargs      = {}                     ← might contain DataOps in other cases

e.obj            = <real pandas DataFrame> ← evaluated
e.method_name    = "dropna"                ← unchanged (was already plain)
e.args           = ()                      ← all DataOps inside resolved
e.kwargs         = {}                      ← all DataOps inside resolved
```

**`self` holds the recipe (the DAG structure). `e` holds the ingredients (real values).**

`compute()` only sees `e`. It never touches the graph. This means:
- Node logic is simple — just do the computation with real Python objects
- Graph traversal logic lives in one place — the evaluator
- No duplication — every node type doesn't need to know how to resolve DataOps

### How `e` is constructed

1. `handle_data_op` loops over `_fields`, yielding each raw field value to the engine
2. The engine recursively processes each value (resolving DataOps, digging into tuples/dicts)
3. Each resolved value is sent back to the generator via `.send()`
4. After all fields are done, `evaluated_attributes` dict is complete
5. `compute_result` wraps it: `e = SimpleNamespace(**evaluated_attributes)`
6. `e` is passed to `node.compute(e, mode, environment)`

---

## 4. The `yield` Mechanism — A Request-Response Protocol

`yield` in this codebase is NOT about producing a stream of values. It's a
**question-answer protocol** between a generator (handler) and the engine.

```
Generator:  yield some_value     →  "Engine, what does this evaluate to?"
                                     Engine goes away, processes it
Engine:     .send(result)        →  "It evaluates to this."
Generator:  resumes, uses result
```

Each `yield` is a request. The generator pauses, the engine processes the yielded
thing (possibly starting more generators for children), and eventually sends the
answer back. The generator resumes exactly where it left off.

### `yield` vs `return` in handlers

- **`yield X`** means: "I need X evaluated before I can continue. Pause me, go evaluate it, come back with the answer."
- **`return X`** means: "I'm done. X is my final result. Send it to whoever was waiting for me."

When a generator returns, Python raises `StopIteration` with the return value in
`.value`. The engine catches this and uses the value as `last_result`.

---

## 5. Helper Classes

### `_Computation` (line 51)

```python
class _Computation:
    def __init__(self, target_id, generator):
        self.target_id = target_id
        self.generator = generator
```

A wrapper that pairs a **handler generator** with the **identity of what it's
processing** (`id()` of the original object). Lives on the stack.

**Purpose:**
- Lets the engine distinguish "a paused generator" from "a raw value needing processing"
- Enables cycle detection: if `target_id` appears twice in `running`, there's a circular reference
- Enables per-node timing via `node_durations[target_id]`

### `_CurrentNodeDuration` (line 74)

A sentinel object. When a generator yields this, it's asking "how much time have I
spent so far?" The engine looks up the answer in `node_durations` and sends it back.
Used for profiling — not part of the core evaluation logic.

### `CircularReferenceError` (line 70)

Raised when the engine detects a cycle (same node is a descendant of itself).
Prevents infinite loops.

---

## 6. The Engine: `run()` (line 118)

### State

```python
stack = [data_op]                       # things waiting to be processed
last_result = None                      # most recently computed result
running = set()                         # target_ids of active _Computations
node_durations = defaultdict(float)     # time spent per node
```

The stack holds a mix of:
- **Raw values** (DataOps, tuples, dicts, strings, ints) — need processing
- **`_Computation` objects** — paused generators, mid-processing, waiting for a child

### Inner Functions

#### `push_computation(handler)` (line 130)

"Start processing the top-of-stack item by creating a handler generator for it."

```python
def push_computation(handler):
    top = pop()                              # remove raw item from stack
    top_id = id(top)
    if top_id in running:                    # already processing this → cycle!
        raise CircularReferenceError(...)
    generator = handler(top)                 # call handler → creates generator
    stack.append(_Computation(top_id, generator))  # push generator onto stack
    running.add(top_id)                      # mark as actively processing
```

Flow: raw item on stack → pop it off → create a handler generator for it → push
the generator (wrapped in `_Computation`) back onto the stack. Next loop iteration,
the engine will see a `_Computation` on top and call `step()` to run the generator.

#### `pop()` (line 147)

"Remove top item from stack. Clean up cycle tracking if it's a `_Computation`."

```python
def pop():
    top = stack.pop()
    if isinstance(top, _Computation):
        running.remove(top.target_id)    # no longer actively processing
    return top
```

#### `step()` (line 154)

"Resume the generator on top of the stack by sending it the last computed result."

This is the most important function — it implements the `yield`/`.send()` protocol:

```python
def step():
    nonlocal last_result
    top = stack[-1]                                 # current _Computation
    try:
        new_top = top.generator.send(last_result)   # resume generator, give it the answer
    except StopIteration as e:
        # Generator hit 'return' — it's done
        last_result = e.value                       # return value becomes last_result
        pop()                                       # remove finished _Computation
    else:
        # Generator hit 'yield' — it needs something evaluated
        stack.append(new_top)                       # push yielded thing onto stack
        last_result = None                          # clear (will be set when child finishes)
```

**Two outcomes:**

1. **Generator yielded** (`else` branch): The generator is asking "evaluate this for me."
   The yielded thing is pushed onto the stack. The generator stays on the stack (frozen).
   Next iteration, the engine processes the yielded thing. Eventually that produces
   `last_result`, and the engine will call `step()` again on the waiting generator.

2. **Generator returned** (`except StopIteration` branch): The generator is finished.
   Its return value becomes `last_result`. The `_Computation` is popped. The generator
   below it on the stack (the one that was waiting for this result) will receive
   `last_result` on the next `step()` call via `.send()`.

### The Main Loop (line 176)

```python
while stack:
    top = stack[-1]
    if isinstance(top, _Computation):
        step()                                   # resume paused generator
    elif isinstance(top, _CurrentNodeDuration):
        pop()
        last_result = node_durations[stack[-1].target_id]
    elif isinstance(top, DataOp):
        push_computation(self.handle_data_op)    # start evaluating this DataOp
    elif type(top) in _BUILTIN_MAP:
        push_computation(self.handle_mapping)    # dig into dict values
    elif type(top) in _BUILTIN_SEQ:
        push_computation(self.handle_seq)        # dig into tuple/list items
    elif type(top) is slice:
        push_computation(self.handle_slice)      # evaluate slice components
    elif isinstance(top, _choosing.BaseChoice):
        push_computation(self.handle_choice)     # handle hyperparameter choices
    elif isinstance(top, _choosing.Match):
        push_computation(self.handle_choice_match)
    elif isinstance(top, BaseEstimator):
        push_computation(self.handle_estimator)  # handle sklearn estimator params
    else:
        push_computation(self.handle_value)      # plain value — return as-is
```

This is a **type-based router**. Each iteration:
1. Look at top of stack
2. If it's a `_Computation` → there's a generator waiting. Resume it.
3. If it's a raw value → determine its type, start the appropriate handler.

When the stack is empty, `last_result` holds the final answer. Return it.

---

## 7. The Handlers

All handlers are **generator functions**. They receive a raw value, `yield` anything
they need evaluated, and `return` the final processed result.

### `handle_data_op(self, data_op)` (line 207) — DAG Nodes

```python
def handle_data_op(self, data_op):
    impl = data_op._skrub_impl
    evaluated_attributes = {}
    for name in impl._fields:
        attr = getattr(impl, name)
        evaluated_attributes[name] = yield attr
    return self.compute_result(data_op, evaluated_attributes)
```

**What it does:** Iterates over the node's declared fields. For each field, yields
its raw value to the engine. The engine processes it (recursively — the field might
be a DataOp, a tuple containing DataOps, a dict, anything) and sends back the
evaluated result. After all fields are resolved, calls `compute_result`.

**This is the generator that builds `e`.** The `evaluated_attributes` dict it
accumulates becomes `SimpleNamespace(**evaluated_attributes)` inside `compute_result`.

### `handle_seq(self, seq)` (line 244) — Tuples, Lists, Sets, Frozensets

```python
def handle_seq(self, seq):
    new_seq = []
    for item in seq:
        value = yield item
        new_seq.append(value)
    return type(seq)(new_seq)
```

**What it does:** Iterates over items. Yields each one to the engine for evaluation.
Collects resolved values. Reconstructs the same container type (`tuple(...)`,
`list(...)`, etc.).

**Why it exists:** A node's `args` field is a tuple that might contain DataOps mixed
with plain values, like `(DataOp(Var("x")), 5, "hello")`. This handler ensures every
DataOp inside gets resolved while plain values pass through unchanged.

### `handle_mapping(self, mapping)` (line 256) — Dicts

```python
def handle_mapping(self, mapping):
    new_mapping = {}
    for k, v in mapping.items():
        new_mapping[k] = yield v
    return type(mapping)(new_mapping)
```

**What it does:** Same concept as `handle_seq` but for dict values. Keys are NOT
yielded — DataOps aren't hashable so they can never be dict keys. Only values need
evaluation.

**Why it exists:** A node's `kwargs` field is a dict like `{"on": DataOp(Var("col"))}`.
The DataOp value needs to be resolved to a real string or object.

### `handle_value(self, value)` (line 240) — Plain Values

```python
@_as_gen
def handle_value(self, value):
    return value
```

**What it does:** Nothing. Returns the value unchanged. The `@_as_gen` decorator turns
this regular function into a generator (the engine protocol requires all handlers to
be generators compatible with `.send()`).

**When it triggers:** For strings, ints, floats, function objects, None — anything that
doesn't need recursive evaluation. These are leaves in the type-dispatch tree.

### `handle_estimator(self, estimator)` (line 220) — sklearn Estimators

```python
def handle_estimator(self, estimator):
    params = yield estimator.get_params()
    estimator = skl_clone(estimator)
    estimator.set_params(**params)
    return estimator
```

**What it does:** sklearn estimators can contain DataOps or Choices in their params
(e.g., a hyperparameter set to `skrub.choose_from([0.01, 0.1])`). This extracts all
params as a dict, yields it (the engine processes it as a dict via `handle_mapping`,
resolving any DataOps inside), then creates a fresh clone with the resolved params.

### `handle_slice(self, s)` (line 270) — Slices

```python
def handle_slice(self, s):
    return slice((yield s.start), (yield s.stop), (yield s.step))
```

**What it does:** A slice's start/stop/step might be DataOps. Yields each component,
gets the resolved values, returns a new slice with real values.

### `handle_choice` / `handle_choice_match` (lines 226–238)

Handle skrub's hyperparameter selection system. A `Choice` holds multiple possible
outcomes; a `Match` maps a choice to different branches. These handlers yield the
relevant parts for evaluation and reconstruct the resolved versions.

---

## 8. The Extension Point: `compute_result` (line 215)

```python
# Base class — does nothing:
def compute_result(self, data_op, evaluated_attributes):
    return data_op

# _Evaluator subclass (line 365) — actually computes:
def compute_result(self, data_op, evaluated_attributes):
    return data_op._skrub_impl.compute(
        SimpleNamespace(**evaluated_attributes),
        mode=self.mode,
        environment=self.environment,
    )
```

The base `_DataOpTraversal` class is designed for **structural operations** on the graph
(like cloning). Its `compute_result` just returns the DataOp unchanged.

The `_Evaluator` subclass overrides it to **actually compute** results. It packs
`evaluated_attributes` into a `SimpleNamespace` (creating `e`) and passes it to the
node's `compute()` method.

This is the only method subclasses need to override to change what "traversal" means —
clone vs evaluate vs inspect vs anything else.

---

## 9. Complete Walkthrough: Evaluating `df.merge(other, on="id")`

**DAG structure:**
```
CallMethod(obj=Var("df"), method_name="merge", args=(Var("other"),), kwargs={"on": "id"})
```

**Environment:** `{"df": real_df, "other": real_other}`

### Stack trace (simplified, showing only key moments):

```
STACK                                           ACTION
─────                                           ──────
[CallMethod_DataOp]                             top is DataOp → push handle_data_op
[_Comp(CM_gen)]                                 top is _Comp → step(), .send(None)
  CM_gen starts, yields self.obj (Var("df") DataOp)
[_Comp(CM_gen), Var_df_DataOp]                  top is DataOp → push handle_data_op
[_Comp(CM_gen), _Comp(Var_gen)]                 top is _Comp → step(), .send(None)
  Var_gen starts, yields "df" (string)
[_Comp(CM_gen), _Comp(Var_gen), "df"]           top is string → push handle_value
[_Comp(CM_gen), _Comp(Var_gen), _Comp(val_gen)] step → val_gen returns "df"
  last_result = "df"
[_Comp(CM_gen), _Comp(Var_gen)]                 step → .send("df") into Var_gen
  Var_gen yields sample_df
  ... handle_value returns sample_df ...
  Var_gen has all fields → compute_result → Var.compute():
    looks up "df" in environment → returns real_df
  last_result = real_df
[_Comp(CM_gen)]                                 step → .send(real_df) into CM_gen
  CM_gen: evaluated_attributes["obj"] = real_df ✓
  CM_gen yields "merge" (string)
[_Comp(CM_gen), "merge"]                        handle_value → returns "merge"
  last_result = "merge"
[_Comp(CM_gen)]                                 step → .send("merge") into CM_gen
  CM_gen: evaluated_attributes["method_name"] = "merge" ✓
  CM_gen yields (Var("other") DataOp,) — a tuple
[_Comp(CM_gen), (Var_other_DataOp,)]            top is tuple → push handle_seq
[_Comp(CM_gen), _Comp(seq_gen)]                 step → seq_gen yields Var_other DataOp
[_Comp(CM_gen), _Comp(seq_gen), Var_other_DO]   push handle_data_op for Var("other")
  ... Var("other") evaluates to real_other ...
  last_result = real_other
[_Comp(CM_gen), _Comp(seq_gen)]                 step → .send(real_other) into seq_gen
  seq_gen: new_seq = [real_other], no more items
  seq_gen returns (real_other,)     ← reconstructed tuple
  last_result = (real_other,)
[_Comp(CM_gen)]                                 step → .send((real_other,)) into CM_gen
  CM_gen: evaluated_attributes["args"] = (real_other,) ✓
  CM_gen yields {"on": "id"} — a dict
[_Comp(CM_gen), {"on": "id"}]                   push handle_mapping
  ... handle_mapping yields "id" → handle_value → "id" ...
  handle_mapping returns {"on": "id"}
  last_result = {"on": "id"}
[_Comp(CM_gen)]                                 step → .send({"on": "id"}) into CM_gen
  CM_gen: evaluated_attributes["kwargs"] = {"on": "id"} ✓
  All fields done. CM_gen calls compute_result:
    e = SimpleNamespace(
        obj=real_df, method_name="merge",
        args=(real_other,), kwargs={"on": "id"}
    )
    CallMethod.compute(e):
        method = getattr(real_df, "merge")
        return method(real_other, on="id")
    → returns merged DataFrame
  last_result = merged_DataFrame
[]                                              stack empty → return last_result
```

**Result:** the actual merged pandas DataFrame.

---

## 10. The `_Evaluator` Subclass (line 274)

`_Evaluator` extends `_DataOpTraversal` with evaluation-specific behavior:

### Overridden `handle_data_op` (line 294)

```python
def handle_data_op(self, data_op):
    impl = data_op._skrub_impl
    # Check cache first
    try:
        return impl.results[self.mode]
    except KeyError:
        pass
    # Handle environment lookups (X, y, named variables)
    # ... environment lookup logic ...
    # If not found in cache or environment, evaluate normally
    result = yield from self._eval_data_op(data_op)
    # Store result in cache
    self._store(data_op, result, duration=..., env_key=...)
    return result
```

Additions over base class:
- **Result caching:** checks `impl.results[mode]` before evaluating. If the same node
  is referenced by multiple parents, it's only computed once.
- **Environment lookups:** for Var nodes and named nodes, checks the environment dict
  for pre-supplied values.
- **Error handling:** stores errors in `impl.errors[mode]`, adds stack trace info.
- **Callbacks:** notifies registered callbacks after each node is evaluated.

### Overridden `compute_result` (line 365)

```python
def compute_result(self, data_op, evaluated_attributes):
    return data_op._skrub_impl.compute(
        SimpleNamespace(**evaluated_attributes),
        mode=self.mode,
        environment=self.environment,
    )
```

This is where `e` is created and passed to the node's `compute()` method.

### Evaluation Modes

The `mode` parameter propagates through the entire evaluation:
- `"preview"` — runs on sample data during DAG construction (eager feedback)
- `"fit"` — training time
- `"predict"` — inference time
- `"fit_transform"` — fit + transform in one pass

Nodes can use `mode` in their `compute()` to behave differently (e.g., a Var node
looks up data differently in preview mode vs fit mode).

---

## 11. Why Not Simple Recursion?

The comment at line 93 explains: recursion causes deep call stacks, which produce
**confusing tracebacks** for users when something fails. The generator+stack approach
keeps the call stack shallow — the Python call stack never grows beyond a few frames
regardless of DAG depth.

The technique comes from "The Python Cookbook" by Beazley & Jones (3rd edition,
chapter 8.22: "Implementing the Visitor Pattern Without Recursion").

The `yield`/`.send()` protocol effectively simulates recursion: yielding is like
making a recursive call, and receiving the `.send()` value is like getting the
recursive call's return value. But the actual Python call stack stays flat.

---

## 12. Connection to Stratum

Stratum **does not use** `_DataOpTraversal` or `_Evaluator`. It has its own
`build_graph()` function (in `stratum/utils/_skrub_graph.py`) that extracts the DAG
topology using a simple iterative DFS — no generators, no evaluation.

Stratum's pipeline replaces the evaluation layer:

```
skrub's _Evaluator:
  DAG → walk nodes → compute each → return result

Stratum:
  DAG → build_graph() extracts topology
      → convert to IR (intermediate representation)
      → logical optimizer (CSE, pushdown, lowering, selection)
      → runtime (parallelism, buffering, Rust kernels)
      → return result
```

The node types and their `_fields` are shared vocabulary. skrub's evaluator walks
them and computes naively. Stratum reads them and compiles an optimized plan.
The `compute()` methods on nodes are only used by skrub's evaluator — Stratum
replaces them with its own operator implementations.
