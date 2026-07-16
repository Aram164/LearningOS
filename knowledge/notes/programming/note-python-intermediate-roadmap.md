---
id: note-python-intermediate-roadmap
type: note
title: "Python Intermediate Roadmap — Reference & Repair Map"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-python]
sources: [source-fluent-python]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Programming/python/Python-Intermediate-Roadmap.md` (legacy tree).

# Python Intermediate Roadmap — Reference & Repair Map

> **Purpose:** Complete map from "knows basics" to confident intermediate + Stratum-level Python. **Usage model: lookup file, not a linear course.** When something feels shaky, find the symptom in the index, jump to that step, work its materials.
>
> **Skeleton:** Fluent Python 2nd ed. (local: `Plans/Programming/python/Python/`). All FP chapter code: [fluentpython/example-code-2e](https://github.com/fluentpython/example-code-2e) — clone once, retype don't paste.
>
> **Related docs:** `Plans/Programming/python/Python-OOP-Scope-Repair-Plan.md` (drill sessions for Steps 2, 7, 8), `LEARNING-RESOURCES.md` §8, `Programming-Toolbox-Bootcamp.md` (shell/git/pytest/Docker).
>
> **Stratum-specific steps:** Steps 22–27 are derived from reading the Stratum repo directly (optimizer IR, buffer pool, monkey-patching, Rust backend). These are not intermediate-level — they're what you need for that job.
>
> *Created KW 24 (Jun 13, 2026). Extended KW 24 with Stratum analysis. Links verified.*

---

## Diagnostic index — symptom → step

| You feel weak when... | Go to |
|---|---|
| "Why did changing `b` also change `a`?" / copies vs references / mutation | **Step 2** |
| `UnboundLocalError`, `global`/`nonlocal`, "where does this name come from?" | **Step 3** |
| `__repr__`, `__len__`, `__getitem__`, "why does `len(x)` work on my class?" | **Step 4** |
| Slicing, sorting, dict/set behavior, comprehensions, choosing container | **Step 5** |
| Encoding errors, `str` vs `bytes`, f-string formatting | **Step 6** |
| `self`, instance vs class attrs, `@classmethod` vs `@staticmethod` | **Step 7** |
| `super()`, MRO, mixins, subclassing built-ins/pandas/sklearn | **Step 8** |
| `@dataclass`, `NamedTuple`, `__post_init__`, `field()` | **Step 9** |
| Duck typing, ABCs, protocols, "what interface does this expect?" | **Step 10** |
| Decorators, closures, `functools.wraps`, decorator factories | **Step 11** |
| Generators, `yield`, iterators, lazy pipelines | **Step 12** |
| `with`, context managers, `match`, loop `else` | **Step 13** |
| Exceptions: what to catch, when to raise, custom exceptions | **Step 14** |
| Type hints, mypy, generics, `Optional`, `TypeVar` | **Step 15** |
| Imports failing, `__init__.py`, circular imports, venvs, `sys.path` | **Step 16** |
| Reinventing things `collections`/`itertools`/`functools`/`pathlib` already do | **Step 17** |
| Code works but reads like C++ | **Step 18** |
| Threads, processes, async, the GIL, `concurrent.futures` | **Step 19** |
| "What does the interpreter actually do?" — frames, bytecode, `dis` | **Step 20** |
| `@property`, descriptors, `__getattr__`, metaclasses | **Step 21** |
| `getattr`/`setattr`, `type()`, `vars()`, `inspect`, reading object guts at runtime | **Step 22** |
| `importlib`, `sys.modules`, monkey-patching modules at runtime | **Step 23** |
| `gen.send()`, `throw()`, `StopIteration.value`, generator-coroutines | **Step 24** |
| Python ↔ Rust/C: PyO3, maturin, `.so` files, `ctypes` | **Step 25** |
| Building DAGs, optimizer passes, tree-walking patterns in Python | **Step 26** |
| `__slots__`, `__init_subclass__`, `weakref`, memory layout | **Step 27** |

**FP reading order (from HANDOFF):** 1→6→2→3→7→17→11→14→5→9→13→8→15→18. Done so far: Ch 1, 5, 6, 11, 14.

---

## Step 1 — Baseline: syntax & core mechanics

*You're past this. Listed for gap-fills only.*

- **Book:** *Automate the Boring Stuff* — dip back in for any syntax hole.
- **Reference:** [Official Python Tutorial](https://docs.python.org/3/tutorial/) ch. 3–5 — skim; small revelations hide here.
- **Bridge:** *Beyond the Basic Stuff with Python* (Sweigart, [free online](https://inventwithpython.com/beyond/)) — ch. 4 (common Python gotchas) is a 30-min pass worth doing once.

---

## Step 2 — Names, objects, references, mutability

*The single most important mental-model fix from C++. Everything else builds on it.*

**Symptoms:** aliasing surprises, mutable default arguments, shallow vs deep copy confusion, "is `=` a copy?"

- **Core:** FP **Ch 6** — PY.02 ✅. Re-read §"Identity, Equality, Aliases" + §"Function Parameters as References."
- **Core:** [Ned Batchelder — Facts and myths about Python names and values](https://nedbatchelder.com/text/names.html) ⭐ (~40 min), or the [PyCon talk](https://nedbatchelder.com/text/names1.html).
- **Tool:** [Python Tutor](https://pythontutor.com) — visualize every snippet you don't trust.
- **Reference:** `is` vs `==`, `copy.copy` vs `copy.deepcopy` ([copy module docs](https://docs.python.org/3/library/copy.html)).
- **Going deeper:** `sys.getrefcount(obj)` — see CPython's reference count live; `id(obj)` — the memory address, which is what `is` compares. [weakref module](https://docs.python.org/3/library/weakref.html) — references that don't prevent garbage collection; important for cache / buffer pool patterns like Stratum's `BufferPool`.
- **Stratum anchor:** `BufferPool.live_variable_map` holds `(size, data)` tuples keyed by `Op` objects. The `pin`/`unpin`/`remove` pattern is a manual reference-counting cache. Understanding object identity (`is` vs `==`) is essential to see why `Op` objects can safely be dict keys.
- **Drills:** Repair Plan **Session 1** (D1–D4); then explain the classic `def f(x, lst=[])` mutable-default bug from memory.
- **Done when:** you can predict, without running, what any mix of rebinding vs mutation prints.

---

## Step 3 — Scope, namespaces, functions as objects

**Symptoms:** `UnboundLocalError`, confusion about what a function "sees", `global`/`nonlocal`, passing functions around.

- **Core:** [Real Python — LEGB Rule](https://realpython.com/python-scope-legb-rule/) — §LEGB + §functions.
- **Core:** FP **Ch 7** (Functions as First-Class Objects) — PY.05 ⬜. Functions are objects with attributes; `def` executes at runtime, not at parse time.
- **Key fact:** scope is *decided at compile time* per function — any assignment anywhere in a function body makes that name local for the entire function, even lines above the assignment.
- **Going deeper:** `inspect.currentframe()`, `locals()`, `globals()` — expose the current scope as a live dict. Used in Stratum's logging and debugging.
- **Video:** any Hettinger talk — watch how he passes functions as values without ceremony.
- **Drills:** Repair Plan Session 1 D3/D4; then write `make_counter()` returning a closure — first without `nonlocal` (watch it fail), then with.
- **Done when:** you can explain why `nonlocal` exists and what problem it solves.

---

## Step 4 — The data model & dunder methods

*The "grand unified theory" of Python: `len()`, operators, `for` loops, `with` — all just call dunders.*

**Symptoms:** dunders feel magic; you don't know which to implement; `print(obj)` shows `<object at 0x...>`.

- **Core:** FP **Ch 1** (Data Model) — PY.01 ✅; FP **Ch 11** (A Pythonic Object) — PY.07 ✅. Re-read Ch 11 §`__repr__`/`__str__`, §hashable objects, §`__format__`.
- **Going further:** FP **Ch 16** (Operator Overloading) — when you need `+`/`==` on your own classes.
- **Reference:** [Data model chapter of the language reference](https://docs.python.org/3/reference/datamodel.html) — the authoritative dunder list; bookmark, don't read linearly.
- **Video:** [James Powell — "So you want to be a Python expert?"](https://www.youtube.com/watch?v=cKPlPJyQrt4) — first 25 min is the best live demo of the data model's logic.
- **Code:** FP example-code-2e `01-data-model/` (FrenchDeck, Vector) — retype FrenchDeck from memory.
- **Stratum anchor:** `Op.__repr__`, `Op.__str__` in `_ops.py` are your live examples of well-crafted dunders on a class hierarchy; `PlaceHolder.__repr__` is the minimal case.
- **Done when:** given "I want `len(x)` / `x[i]` / `for item in x` / `x == y` to work," you name the dunder instantly.

---

## Step 5 — Built-in containers & comprehensions

**Symptoms:** misusing lists where sets/dicts fit, slice confusion, sort vs sorted, clunky loops that should be comprehensions.

- **Core:** FP **Ch 2** (Sequences) — PY.03 ⬜ — slicing, unpacking, `sort` vs `sorted`, when lists are wrong.
- **Core:** FP **Ch 3** (Dicts and Sets) — PY.04 ⬜ — hashing, dict views, `setdefault`/`defaultdict`, set algebra, dict ordering (insertion-order since 3.7).
- **Article:** [Real Python — List Comprehensions](https://realpython.com/list-comprehension-python/) — incl. when *not* to use them.
- **Reference:** [Sorting HOWTO](https://docs.python.org/3/howto/sorting.html) — `key=` functions; the idiom that replaces C++ comparators.
- **Code:** example-code-2e `02-array-seq/`, `03-dict-set/`; rewrite three of your own mlprov/job loops as comprehensions.
- **Stratum anchor:** `indegree = {n: len(children.get(n, [])) for n in nodes}` in `_optimize.py` is the pattern — dict comprehension over a node set, `.get()` with default to avoid KeyError.
- **Done when:** you reflexively reach for set/dict for membership tests, and `key=lambda` is muscle memory.

---

## Step 6 — Strings, bytes, and formatting

**Symptoms:** `UnicodeDecodeError`, `b'...'` confusion, ugly string building.

- **Core:** FP **Ch 4** (Unicode Text vs Bytes) — §"Character Issues" + §"Basic Encoders/Decoders" + §"Handling Text Files" (the "Unicode sandwich"); skim the rest.
- **Article:** [Real Python — f-strings / string formatting](https://realpython.com/python-string-formatting/) — format-spec mini-language (`f"{x:.3f}"`, `{x!r}`).
- **Key model:** `str` = text (Unicode code points); `bytes` = raw data. Encode on the way out, decode on the way in, never mix.
- **Done when:** a `UnicodeDecodeError` tells you exactly where the sandwich broke.

---

## Step 7 — Classes I: mechanics

**Symptoms:** `self` feels magic, instance vs class attributes blur, `@classmethod` vs `@staticmethod` unclear.

- **Core:** [Official tutorial ch. 9 (Classes)](https://docs.python.org/3/tutorial/classes.html) §9.1–9.4 — classes are namespaces; attribute lookup is dict lookup.
- **Video + code:** [Corey Schafer OOP playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc) #1–3, code at [CoreyMSchafer/code_snippets](https://github.com/CoreyMSchafer/code_snippets/tree/master/Object-Oriented).
- **Article:** [Real Python — Instance, Class, and Static Methods Demystified](https://realpython.com/instance-class-and-static-methods-demystified/).
- **Going deeper:** `__slots__` — replaces `__dict__` with a fixed-layout tuple of named slots; eliminates per-instance dict overhead; important for classes created in hot loops (like Op nodes in Stratum's large DAGs). [Real Python — `__slots__`](https://realpython.com/python-slots/). Also see Step 27.
- **`__init_subclass__`** — a hook called on the base class every time a subclass is defined; used in frameworks to auto-register subclasses. [Docs](https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__). Stratum's `Op` hierarchy could use this; understanding it helps you read framework code.
- **Key reframe:** `obj.method(x)` ≡ `Class.method(obj, x)`. `self` is an ordinary first argument.
- **Drills:** Repair Plan **Session 2**.
- **Done when:** you can predict `m.__dict__` vs `Module.__dict__` contents and explain attribute shadowing.

---

## Step 8 — Classes II: inheritance, super(), MRO, mixins

*Your named headache. The repair plan's Sessions 3–4 are the drill version of this step.*

**Symptoms:** super() confusion, mixin `__init__` chains, subclassing pandas/numpy/sklearn, diamond inheritance.

- **Core:** [Hettinger — Python's super() considered super!](https://rhettinger.wordpress.com/2011/05/26/super-considered-super/) ⭐ — THE mental model: super() = next in MRO.
- **Core:** FP **Ch 14** (Inheritance) — PY.08 ✅. Re-read §"Multiple Inheritance and MRO" + §"Mixin Classes" + §"Subclassing Built-In Types Is Tricky."
- **Article:** [Real Python — Supercharge Your Classes With super()](https://realpython.com/python-super/).
- **Reference:** [Official MRO write-up](https://docs.python.org/3/howto/mro.html) — C3 linearization; read after Hettinger.
- **Practical:** [numpy subclassing guide](https://numpy.org/doc/stable/user/basics.subclassing.html) + [pandas subclassing guide](https://pandas.pydata.org/docs/development/extending.html#subclassing-pandas-data-structures) — your mlprov reality.
- **`__init_subclass__`:** (see Step 7) — used in abstract base classes where you want to enforce constraints on every concrete subclass at *class-definition time*, not at instantiation.
- **Stratum anchor:** `Op` base class defines `clone()` using a class-level `fields` list — a manual version of what `__init_subclass__` + descriptors could auto-generate. `ImplOp.clone()` and `BaseEstimatorOp.clone()` override this because their internal state is more complex. Read these and annotate every `super()` call.
- **Drills:** Repair Plan **Sessions 3–4** (LoggingDict rebuild, diamond drill, ProvDataFrame MRO annotation).
- **Done when:** `print(Cls.__mro__)` is your reflex.

---

## Step 9 — Data class builders

**Symptoms:** writing boilerplate `__init__`/`__repr__`/`__eq__` by hand.

- **Core:** FP **Ch 5** (Data Class Builders) — PY.09 ✅. Re-read §"Main Features" comparison table.
- **Article:** [Real Python — Data Classes](https://realpython.com/python-data-classes/) — `field(default_factory=...)`, `frozen=True`, `__post_init__`.
- **Going deeper:** `@dataclass(slots=True)` (3.10+) — auto-generates `__slots__`; eliminates `__dict__` per instance. Use when you have many short-lived instances.
- **Rule of thumb:** records of data → `@dataclass`; immutable / tuple-compatible → `NamedTuple`; behavior-heavy → plain class.
- **Done when:** you stop hand-writing `__init__` for pure data containers.

---

## Step 10 — Duck typing, ABCs, protocols

**Symptoms:** "what type does this function accept?", `isinstance` overuse, designing interfaces.

- **Core:** FP **Ch 13** (Interfaces, Protocols, ABCs) — PY.11 ⬜ — the four interface mechanisms: duck typing, goose typing (ABCs), static protocols, static duck typing.
- **Reference:** [collections.abc table](https://docs.python.org/3/library/collections.abc.html) — which dunders give you which "free" methods.
- **Going deeper:** `@runtime_checkable` on a `Protocol` — lets you use `isinstance(x, MyProtocol)` at runtime (normally protocols are static-only). `TypeVar` + `Generic` for parameterized protocols. [Docs](https://docs.python.org/3/library/typing.html#typing.Protocol).
- **Code:** example-code-2e `13-protocol-abc/`.
- **Stratum anchor:** Stratum's `Op.process()` is an abstract method pattern without ABCs (raises `NotImplementedError`). The sklearn fit/predict contract is pure duck typing — anything with `.fit/.predict` is an estimator.
- **Done when:** you can say *why* an ABC's `abstractmethod` is better than just `raise NotImplementedError` (ABC raises at *instantiation*, not at *call time*).

---

## Step 11 — Closures & decorators

**Symptoms:** `@something` syntax feels magic, can't write a decorator with arguments, losing function metadata.

- **Prerequisite:** Steps 3 and 2.
- **Core:** FP **Ch 9** (Decorators and Closures) — PY.10 ⬜ — registration decorators, `functools.wraps`, `lru_cache`, `singledispatch`.
- **Article:** [Real Python — Primer on Python Decorators](https://realpython.com/primer-on-python-decorators/) ⭐ — do this FIRST, then FP Ch 9.
- **Video:** [Corey Schafer — Decorators](https://www.youtube.com/watch?v=FsAPt_9Bf3U).
- **Mental model:** `@dec` is just `f = dec(f)`. Nothing else.
- **Going deeper:** `functools.singledispatch` — dispatch table by first argument type; used extensively in optimizer/rewrite passes like Stratum's `extract_dataframe_op`. [Docs](https://docs.python.org/3/library/functools.html#functools.singledispatch). `functools.cache` (3.9+, alias for `lru_cache(maxsize=None)`) — zero-arg version, fastest.
- **Drills:** from memory: `@timer`, `@logged`, then `@retry(n=3)` (decorator factory). Verify `__name__` survives via `@wraps`.
- **Done when:** decorator factories don't scare you.

---

## Step 12 — Iterators, generators, lazy pipelines

**Symptoms:** `yield` confusion, iterator-exhausted-once surprises, memory blowups from loading whole files.

- **Core:** FP **Ch 17** (Iterators, Generators, Classic Coroutines) — PY.06 ⬜ — read the generators section first; the coroutines section is Step 24.
- **Article:** [Trey Hunner — The Iterator Protocol: How for Loops Work](https://treyhunner.com/2016/12/python-iterator-protocol-how-for-loops-work/).
- **Classic:** [David Beazley — Generator Tricks for Systems Programmers](https://www.dabeaz.com/generators/) ⭐ — generator pipelines over logs; career-grade for data engineering.
- **Article:** [Real Python — Introduction to Generators](https://realpython.com/introduction-to-python-generators/).
- **`yield from`:** delegates to a sub-iterator; essential in recursive generator traversals (like Stratum's DAG walkers). `yield from inner` is shorthand for `for x in inner: yield x` but also proxies `.send()` and `.throw()`. [PEP 380](https://peps.python.org/pep-0380/).
- **Hierarchy:** iterable (has `__iter__`) ⊃ iterator (also has `__next__`, exhausts) ⊃ generator (iterator written with `yield`).
- **Stratum anchor:** `topological_iterator` in `_op_utils.py` is a generator that walks the Op DAG — read it once you know generators. The `for op in topological_iterator(root):` pattern throughout the optimizer is the canonical lazy DAG traversal.
- **Drills:** (1) manual `__iter__`/`__next__` → rewrite with generator; (2) 3-stage lazy CSV pipeline; (3) write a topological sort of a toy DAG as a generator.
- **Done when:** you reach for genexps instead of lists and `yield from` for recursive traversal feels natural.

---

## Step 13 — Context managers, with / else / match

**Symptoms:** `with` feels like ritual, can't write your own, `try/else` semantics unclear.

- **Core:** FP **Ch 18** (with, match, else) — PY.14 ⬜.
- **Article:** [Real Python — Context Managers and the with Statement](https://realpython.com/python-with-statement/).
- **Two ways to write one:** class with `__enter__`/`__exit__`, or `@contextlib.contextmanager` + one `yield` ([contextlib docs](https://docs.python.org/3/library/contextlib.html)).
- **Stratum anchor:** `DummyConfigManager` in `_ops.py` is a minimal do-nothing context manager — shows the interface in its simplest form. `estimator_parallel_config()` returns either a real one or the dummy depending on config.
- **Drill:** write a `timer()` context manager both ways; wrap an mlprov test.
- **Done when:** you know `with` is exactly `try/finally` with syntactic sugar, and you use it for every resource that needs cleanup.

---

## Step 14 — Exceptions & error handling

**Symptoms:** bare `except:`, unsure what to catch, when to define custom exceptions.

- **Core:** [Official tutorial ch. 8](https://docs.python.org/3/tutorial/errors.html) — `else`, `finally`, exception chaining (`raise X from Y`).
- **Article:** [Real Python — Python Exceptions](https://realpython.com/python-exceptions/).
- **Reference:** [Built-in exception hierarchy](https://docs.python.org/3/library/exceptions.html#exception-hierarchy) — catch the most specific class.
- **Going deeper:** `ExceptionGroup` (3.11+) and `except*` — handle multiple concurrent exceptions (asyncio context). `traceback` module — format and log exceptions programmatically.
- **Idiom:** EAFP ("easier to ask forgiveness") — `try: d[k] except KeyError:` over `if k in d:`.
- **Stratum anchor:** `Scheduler.process_op()` wraps every op execution in `try/except Exception as e: raise RuntimeError(...)` — the pattern of catching broad exceptions and re-raising with more context. Note `RuntimeError(f"[{self.mode}] Error processing '{op}': {e}")` — the string interpolation preserves context without losing the traceback (prefer `raise ... from e` in your own code).
- **Rules of thumb:** never bare `except:`; custom exceptions = one class per library (`class StratumError(Exception): pass`) subclassed per error type.
- **Done when:** your `except` clauses name specific exceptions and your libraries raise typed ones.

---

## Step 15 — Type hints

**Symptoms:** reading hinted signatures in skrub/sklearn/Stratum, `Optional`, generics, mypy errors.

- **Core:** FP **Ch 8** (Type Hints in Functions) — PY.12 ⬜; FP **Ch 15** (more types) — PY.13 ⬜.
- **Article:** [Real Python — Python Type Checking](https://realpython.com/python-type-checking/) — practical mypy setup.
- **Reference:** [mypy cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) ⭐ — fastest on-ramp; start here.
- **Going deeper:**
  - `TypeVar` + `Generic[T]` — parameterized containers (`class Stack(Generic[T]): ...`). [Real Python — generics](https://realpython.com/python-type-hints-multiple-dispatch/).
  - `from __future__ import annotations` (PEP 563) — makes ALL annotations lazy strings; enables forward references (`def f() -> "MyClass":` becomes just `def f() -> MyClass:`). Used at the top of every Stratum file. Becoming default in future Python versions.
  - `overload` decorator — multiple signatures for one function (typing-only; the runtime version catches the rest).
  - `Callable[[ArgType], ReturnType]` — type hint for functions.
- **Stratum anchor:** `_ops.py` is full of `list[Op]`, `dict[Hashable, Any]`, `tuple[list[Op], int | None, list[Op]]` — modern Python 3.10+ union syntax. `from __future__ import annotations` at the top of every file makes all these work even on older Python.
- **Drill:** annotate one mlprov module fully, run `mypy`, fix every complaint.
- **Done when:** you write hints by default and can read any Stratum/sklearn signature fluently.

---

## Step 16 — Modules, imports, packages, environments

**Symptoms:** `ModuleNotFoundError`, `__init__.py` mystery, circular imports, "works in IDE not terminal."

- **Core:** [Real Python — Python Modules and Packages](https://realpython.com/python-modules-packages/).
- **Deeper:** [Real Python — Python import: Advanced Techniques](https://realpython.com/python-import/) — §basics + §circular imports + §the import system.
- **Key model:** a module executes *once* on first import and is cached in `sys.modules`; subsequent imports return the cached object. `sys.path` determines where Python looks; it depends on *how you launched Python*. `python -m pkg.module` from project root fixes most "works here not there" bugs.
- **Going deeper:** `importlib.import_module("pkg.mod")` — programmatic import; returns the module object. `importlib.reload(mod)` — re-execute a module (rarely needed; hot-reload scenarios). Essential for Step 23 (monkey-patching).
- **Layout reference:** how mlprov is structured (`pyproject.toml` + package dir + `tests/`) is your live example.
- **Done when:** an import error makes you check `sys.path` and launch directory, not shuffle files.

---

## Step 17 — Standard library power tools

**Symptoms:** writing 10 lines for what stdlib does in 1; manual path surgery; nested loops that should be `itertools`.

- **collections:** [docs](https://docs.python.org/3/library/collections.html) — `Counter`, `defaultdict`, `deque`, `namedtuple`, `UserDict` (the Step-8 subclassing fix), `ChainMap`.
- **itertools:** [Real Python guide](https://realpython.com/python-itertools/) + [docs recipes](https://docs.python.org/3/library/itertools.html#itertools-recipes) — the recipes are goldmine idiomatic code.
- **functools:** [docs](https://docs.python.org/3/library/functools.html) — `lru_cache`/`cache`, `partial`, `reduce`, `cached_property`, `singledispatch`.
- **pathlib:** [Real Python — pathlib](https://realpython.com/python-pathlib/) — replace every `os.path` + string concat habit.
- **abc:** [docs](https://docs.python.org/3/library/abc.html) — `ABC`, `abstractmethod`, `ABCMeta` — the formal way to define abstract interfaces (vs. just `raise NotImplementedError`).
- **inspect:** [docs](https://docs.python.org/3/library/inspect.html) — `getmembers`, `signature`, `isclass`, `isfunction`, `currentframe` — introspects live objects; essential for Step 22.
- **logging:** [Real Python — logging](https://realpython.com/python-logging/) — Stratum uses `logging` everywhere (`logger = logging.getLogger(__name__)`); know how to configure it.
- **Browsing resource:** [PyMOTW-3](https://pymotw.com/3/) — one worked article per stdlib module.
- **Done when:** "stdlib probably has this" is your first thought.

---

## Step 18 — Pythonic style & idioms

**Symptoms:** code works but reads like translated C++.

- **Video:** [Hettinger — Transforming Code into Beautiful, Idiomatic Python](https://www.youtube.com/watch?v=OSGv2VnC0go) ⭐ (~50 min) — the single highest-value hour in this file.
- **Reference:** [PEP 8](https://peps.python.org/pep-0008/) — skim once; let `ruff` enforce it.
- **Patterns:** [python-patterns.guide](https://python-patterns.guide/) (Brandon Rhodes) — read "Composition Over Inheritance" first.
- **Idiom checklist:** unpacking over indexing; `enumerate`/`zip` over index loops; comprehensions; `key=` functions; EAFP; context managers for resources; flat over nested.
- **Done when:** you can shrink 20 lines of KW-19 code meaningfully without losing clarity.

---

## Advanced tier — pull-based only

---

## Step 19 — Concurrency & the GIL

*Relevant for AMLS parallelism + job perf work.*

- **Orientation:** [Real Python — Speed Up Your Python Program With Concurrency](https://realpython.com/python-concurrency/) — the threading vs multiprocessing vs asyncio decision map.
- **The GIL:** [Real Python — What Is the GIL?](https://realpython.com/python-gil/) + [Beazley — Understanding the GIL (slides)](https://www.dabeaz.com/python/UnderstandingGIL.pdf).
- **Threading primitives:** `threading.RLock` (reentrant lock — the same thread can acquire it multiple times without deadlock), `threading.Lock`, `threading.Event`. [Official docs](https://docs.python.org/3/library/threading.html). Used in Stratum's `_patching.py` (`_LOCK = threading.RLock()`) to make the monkey-patching idempotent across threads.
- **`concurrent.futures`:** [Real Python — concurrent.futures](https://realpython.com/python-concurrency/#using-concurrentfutures) — `ThreadPoolExecutor` for I/O-bound, `ProcessPoolExecutor` for CPU-bound; cleaner API than raw `threading`/`multiprocessing`.
- **Video:** [Beazley — Python Concurrency From the Ground Up: LIVE!](https://www.youtube.com/watch?v=MCs5OvhV9S4) ⭐ — builds a concurrent server from scratch on stage.
- **asyncio basics:** [Real Python — Async IO in Python](https://realpython.com/async-io-python/) — `async def`, `await`, `asyncio.run()`. Know the model; don't need to write it for Stratum work.
- **Book:** FP **Ch 19–21** — read only if needed after the above.
- **Job tie-in:** [Brandon Rohrer's Making Python Faster series](https://brandonrohrer.com/code_optimization.html).

---

## Step 20 — Interpreter internals

*The "how does it actually work" itch. Your C++ background is an asset here.*

- **Appetizer (15 min):** `import dis; dis.dis(f)` — see `LOAD_FAST` (local) vs `LOAD_GLOBAL` (global) — scope made physical. `dis.dis` on Stratum's `process_op` and compare with `LOAD_ATTR`, `CALL_FUNCTION`.
- **Bytecode module:** `opcode` — the full list of bytecode instructions. `compile(source, "<string>", "exec")` returns a `code` object; inspect its `co_consts`, `co_varnames`, `co_code`.
- **Core:** [Allison Kaptur — A Python Interpreter Written in Python](https://aosabook.org/en/500L/a-python-interpreter-written-in-python.html) ⭐ (~1.5h) — Byterun: working bytecode VM in 500 lines; frames, value stack, why scope IS the frame structure.
- **Foundations alternative:** [Composing Programs](https://www.composingprograms.com/) ch. 1.6 & 3 (Berkeley CS61A) — environments/frames diagrams done formally.
- **Deep:** [Philip Guo — CPython internals lectures](https://pgbovine.net/cpython-internals.htm) — cherry-pick L1 (overview), L3 (frames/scope), L8 (classes). Old (Py 2.7) but architecture stands.
- **Modern alternative:** [CPython internals book](https://realpython.com/products/cpython-internals-book/) (Real Python, paid) or the free [devguide.python.org](https://devguide.python.org/) — the official contributor guide explains the C source layout.
- **`eval()`/`exec()`:** [Real Python — eval and exec](https://realpython.com/python-eval-function/) — run Python code from strings; understand why this is powerful and dangerous.

---

## Step 21 — Attribute magic: properties, descriptors, metaclasses, module `__getattr__`

*Read to understand libraries; you will write `@property` often, descriptors occasionally, metaclasses almost never.*

- **Properties:** FP **Ch 22** (Dynamic Attributes and Properties) — `@property` is the 95%-case; turns `get_x()` habits into plain attribute access. `@property` + `@x.setter` + `@x.deleter` trio.
- **Descriptors:** [Official Descriptor HOWTO](https://docs.python.org/3/howto/descriptor.html) (Hettinger) ⭐ — explains how `@property`, `@classmethod`, methods themselves ALL work underneath via the descriptor protocol (`__get__`, `__set__`, `__delete__`). [Real Python — descriptors](https://realpython.com/python-descriptors/) as a gentler alternative.
- **`__getattr__` vs `__getattribute__`:** `__getattr__` is called only when normal lookup *fails* (fallback); `__getattribute__` intercepts *every* attribute access. FP Ch 22 §"Using a Property for Attribute Validation." Use `__getattr__` for lazy attributes and proxy objects.
- **Module-level `__getattr__` (PEP 562):** defining `def __getattr__(name):` at *module level* (not inside a class) intercepts attribute access on the module object itself — `stratum._rust_backend` uses this exact pattern to lazily read config flags: `USE_RUST = __getattr__("USE_RUST")`. [PEP 562](https://peps.python.org/pep-0562/). Key insight: modules ARE objects in Python; they have `__dict__` and can have `__getattr__`.
- **`__class_getitem__`:** makes `MyClass[int]` work (generic syntax). Needed if you're writing parameterizable containers.
- **Metaclasses:** FP **Ch 24** — skim only. FP's own advice: "if you're not sure you need them, you don't." The one pattern worth knowing: `type(obj)` is its metaclass; `type` itself is a metaclass; classes are instances of `type`.
- **Done when:** `obj.attr` triggering code is no longer magic — you know the lookup chain: data descriptor → instance `__dict__` → non-data descriptor/class attribute → `__getattr__`.

---

## Stratum-specific steps

*The following steps are derived from reading the Stratum codebase directly. They target what you need for the job.*

---

## Step 22 — Runtime introspection & reflection

*Used pervasively in Stratum: `isinstance`, `getattr`, `hasattr`, `type`, `vars`, `inspect`.*

**Symptoms:** confused by code that reads/modifies objects without knowing their type at write-time; `isinstance` chains; `getattr(obj, name, default)` calls.

- **Core:** [Real Python — Python's `isinstance` and `issubclass`](https://realpython.com/python-isinstance/) — when to use it, when duck typing is better.
- **Core:** [Official docs — Built-in functions: `getattr`, `setattr`, `hasattr`, `delattr`](https://docs.python.org/3/library/functions.html) — the reflection quad. `getattr(obj, name, default)` is the safe form; `setattr(mod, name, value)` patches attributes on anything, including modules (Step 23).
- **`type()` and `vars()`:** `type(obj)` returns the class; `vars(obj)` returns the `__dict__`. `type(obj).__name__`, `type(obj).__module__` tell you the class string — used in `estm_supports_polars()` in Stratum (`estimator.__class__.__module__.startswith("sklearn.")`).
- **`inspect` module:** [Real Python — inspect](https://realpython.com/python-inspect-module/) — `inspect.signature(f)`, `inspect.getmembers(obj)`, `inspect.isclass`, `inspect.isfunction`, `inspect.getmro(cls)` (same as `cls.__mro__`). Used for framework code, plugins, and any "I need to know what this object has" scenario.
- **`__class__.__name__` idiom:** the pattern `self.__class__.__name__` in `Op.__str__` — works correctly in subclasses (returns the subclass name, not `Op`).
- **Stratum anchor:** `_ops.py` is full of this. `isinstance(value, DataOp)`, `isinstance(value, (list, tuple))`, `isinstance(impl, Value)` etc. in `as_op()` and `replace_dataop()`. `hasattr(self.skrub_impl, "eval")` in `ImplOp.process` — checking for an optional method before calling it (duck typing via reflection).
- **Drill:** write a function `describe(obj)` that prints the class name, all public attributes (excluding dunders), and which are callable vs data; use only `type()`, `dir()`, `getattr()`, `callable()`.
- **Done when:** `getattr(obj, name, None)` and `hasattr(obj, name)` are your reflex for "does this object have X."

---

## Step 23 — Import machinery & monkey-patching

*Stratum's `patching/_patching.py` is a full monkey-patching system. Understanding it requires knowing how Python's import system works.*

**Symptoms:** `importlib.import_module` looks foreign; `setattr(module, "ClassName", MyClass)` seems wrong; "why would you replace a class inside another module?"

- **Core — the import system:** [Real Python — Python import: Advanced Techniques](https://realpython.com/python-import/) — §"The Python import system," §"`sys.modules`," §"Reloading modules."
- **`sys.modules`:** a plain dict mapping module names to module objects. First `import foo` executes `foo.py` and stores the result in `sys.modules["foo"]`. Every subsequent `import foo` just returns `sys.modules["foo"]`. Monkey-patching works because ALL code that does `from foo import Bar` later gets the patched `Bar` (if patched before they import).
- **`importlib.import_module(name)`:** programmatic equivalent of `import name`; returns the module object. If the module is already in `sys.modules`, returns the cached object without re-executing. Used in `_patching.py`'s `_import_module()`.
- **`setattr(module, "ClassName", ReplacementClass)`:** replaces the name `ClassName` in `module.__dict__`. Any code in that module that uses `ClassName` after the patch sees the new class. Code that already did `from module import ClassName` and stored a local binding is NOT affected — order matters.
- **Article:** [Real Python — Monkey Patching in Python](https://realpython.com/python-mock-patch/) — the `unittest.mock.patch` context manager does exactly this; understanding it demystifies Stratum's manual version.
- **Idempotence pattern:** Stratum uses `_PATCH_SENTINEL_NAME = "_STRATUM_PATCHED"` + `threading.RLock` to ensure patching runs exactly once even across threads. Classic sentinel + lock pattern. [threading.RLock docs](https://docs.python.org/3/library/threading.html#threading.RLock).
- **`from __future__ import annotations` interaction:** patching at import time must happen before any module that uses the patched names is imported. `_patching.py` imports and patches during its own module execution, so `import stratum.patching` triggers it; the `__init__.py` that does `from .patching import ...` controls timing.
- **Stratum anchor:** read `_patching.py` in full after this step. It is a clean, well-commented example of: `importlib.import_module`, `setattr`, `threading.RLock`, module-level patching, and idempotent initialization — all patterns you'll use.
- **Drill:** write a toy `patch_module.py` that (1) imports `math`, (2) replaces `math.sqrt` with a version that prints before delegating, (3) verifies that `import math; math.sqrt(9)` in another file sees the patched version if `patch_module` is imported first.
- **Done when:** you can explain the timing issue ("already bound names are not affected") and the sentinel pattern.

---

## Step 24 — Generator coroutines: `send()`, `throw()`, `StopIteration.value`

*Used in `ImplOp.process()` in Stratum to fuse a generator-based evaluation protocol with regular function calls.*

**Symptoms:** `gen.send(value)` looks wrong; confused by `StopIteration as e: return e.value`; difference between a generator and a coroutine is unclear.

- **Core:** FP **Ch 17** — the coroutines section (after the generators section). Specifically: §"Using a Generator as a Coroutine," §"`send()`, `throw()`, `close()`."
- **The protocol in full:**
  - `gen = f()` — creates the generator object, executes nothing yet.
  - `next(gen)` or `gen.send(None)` — advance to the first `yield`; both do the same thing (must be `None` on first call).
  - `gen.send(value)` — resumes the generator, and the `yield` expression *evaluates to `value`*.
  - `gen.throw(ExcType, val)` — injects an exception at the `yield` point.
  - `StopIteration` — raised when the generator returns; `.value` is the return value.
- **Article:** [Real Python — Generators and Coroutines](https://realpython.com/introduction-to-python-generators/#using-advanced-generator-methods) — §"Advanced Generator Methods."
- **PEP 342:** [PEP 342 — Coroutines via Enhanced Generators](https://peps.python.org/pep-0342/) — the spec; readable.
- **Stratum anchor:** `ImplOp.process()` uses the full protocol — `gen = self.skrub_impl.eval(mode=mode, environment=environment)`, then `while True: last_yield = gen.send(last_yield)`, catching `StopIteration as e: return e.value`. The generator yields `DataOp` objects (requesting inputs), the scheduler sends back computed values. This is a cooperative computation pattern — the generator drives its own input requests. Read this method after doing the drill below.
- **Drill:** write a `compute_steps()` generator that yields strings requesting inputs and uses `send()` to receive answers:
  ```python
  def compute_steps():
      a = yield "give me a"
      b = yield "give me b"
      return a + b
  
  gen = compute_steps()
  print(next(gen))           # "give me a"
  print(gen.send(10))        # "give me b"
  try:
      gen.send(20)
  except StopIteration as e:
      print(e.value)         # 30
  ```
  Then write a driver that runs it in a loop (exactly like Stratum's `while True: gen.send(...)`).
- **Done when:** `gen.send()` feels like a natural two-way communication channel, not magic.

---

## Step 25 — Python ↔ Rust/C FFI: PyO3, maturin, C extensions

*Stratum has a Rust backend (`_rust_backend_native`) compiled with PyO3/maturin. This is what "developing microkernels underneath Python" means.*

**Symptoms:** `.so`/`.pyd` import fails or succeeds mysteriously; `from . import _rust_backend_native` looks like magic; unsure how to write and build a Rust function callable from Python.

### How Python loads compiled extensions

- Python treats `.so` (Linux/macOS) and `.pyd` (Windows) files as importable modules — it calls `dlopen()` on the file and looks for an entry point `PyInit_<modname>`.
- `try: from . import _rust_backend_native; HAVE_RUST = True except: HAVE_RUST = False` — the standard "optional compiled extension" pattern in Stratum. The `HAVE_RUST` flag gates all Rust feature usage.
- **Reference:** [Python C extension docs](https://docs.python.org/3/extending/extending.html) — the C version; read §1 (structure of an extension) to understand what PyO3 generates automatically.

### PyO3 — the Rust↔Python bridge

- **Core:** [PyO3 user guide](https://pyo3.rs/latest/) ⭐ — start with "Getting started" + "Python classes" + "Calling Python from Rust." This is the primary resource; it's well-written.
- **What it does:** `#[pyfunction]`, `#[pyclass]`, `#[pymethods]` — Rust macros that generate the C API glue. `#[pymodule]` — the entry point Python calls on `import`.
- **Key concept:** PyO3 manages the GIL via `Python<'py>` lifetime tokens — you must hold a GIL token to call Python APIs from Rust. `py.allow_threads(|| { ... })` releases the GIL during pure Rust work (e.g., compute-heavy operations).

### maturin — the build tool

- **Core:** [maturin docs](https://www.maturin.rs/) — `maturin develop` builds and installs the extension in-place (like `pip install -e .`). `maturin build` produces a wheel.
- **Project layout:** `Cargo.toml` + `src/lib.rs` (Rust) + `pyproject.toml` (Python). The `[lib] crate-type = ["cdylib"]` line tells Rust to compile as a C-compatible dynamic library.
- **Stratum anchor:** `_rust_backend.py` imports `_rust_backend_native` — the compiled `.so` built by maturin. `hashing_tfidf_fit = getattr(native, "hashing_tfidf_csr", None)` — `getattr` with `None` default gracefully handles missing functions (version skew between Rust and Python).
- **Practical:** [Real Python — Build a Python C Extension Module](https://realpython.com/build-python-c-extension-module/) — C version; read for mental model, then prefer PyO3 in practice.

### Data marshaling

- **NumPy ↔ Rust:** PyO3 + `numpy` crate — zero-copy array sharing via buffer protocol. [pyo3-numpy docs](https://docs.rs/numpy/latest/numpy/). The `csr_to_dense` and TF-IDF functions in Stratum all work on sparse matrices, converted via this bridge.
- **Buffer protocol:** [Python buffer protocol](https://docs.python.org/3/c-api/buffer.html) — the general mechanism for zero-copy memory sharing between Python objects and native code. `memoryview` is the Python-level interface.
- **`ctypes`:** [Official docs](https://docs.python.org/3/library/ctypes.html) + [Real Python — ctypes](https://realpython.com/python-bindings-overview/#ctypes) — call existing shared libraries without writing any C/Rust. Useful for quick prototypes; not used in Stratum (they use PyO3 instead).
- **Overview of alternatives:** [Real Python — Python Bindings Overview](https://realpython.com/python-bindings-overview/) — ctypes, CFFI, PyO3, Cython, pybind11 — comparison of all approaches; read once to orient.
- **Cython:** [Cython docs](https://cython.readthedocs.io/en/latest/) — "Python with types" that compiles to C. Used in NumPy, sklearn. Know it exists; PyO3 is preferred for new Rust-based work.

### Practical workflow

1. `cargo new --lib mykernel` → add `pyo3` to `Cargo.toml` → write `#[pyfunction]` + `#[pymodule]`
2. `maturin develop` → `.so` installed in current venv
3. `from mykernel import my_function` → call from Python

- **Drill:** write a minimal PyO3 extension with one function `def add(a: i64, b: i64) -> i64`, build it with maturin, call it from Python. Then add a function that accepts a NumPy array (read-only) and returns its sum.
- **Done when:** you can trace the path from a Rust `#[pyfunction]` through the `.so` to a Python `import` and understand what PyO3 generates in between.

---

## Step 26 — DAG / IR patterns in Python

*Stratum's entire optimizer is a DAG transformation pipeline in Python. These patterns come from compiler design — PL theory applied in Python.*

**Symptoms:** code that builds and transforms graph structures feels ad-hoc; unclear how to visit all nodes, replace nodes, maintain input/output edges consistently.

### Core graph representation

- **Node + edge list:** `Op` in Stratum uses explicit `inputs: list[Op]` and `outputs: list[Op]` on each node — a doubly-linked representation. Enables O(1) parent and child lookup at the cost of keeping both sides in sync.
- **Topological sort:** Kahn's algorithm (`deque` + indegree dict) in `_optimize.py`'s `topological_traverse`. DFS-based in `_linearization.py`'s `linearize_dag`. Know both.
- **Article:** [Real Python — Python Graphs](https://realpython.com/python-graphs/) — adjacency list, DFS/BFS in Python.
- **Book:** CLRS §22 (Graph algorithms, already in your Algo2 plan) — the formal version; the Stratum code is direct applied CLRS.

### Node replacement (rewrite rules)

- **Pattern:** find a node matching a pattern → create a new node → rewire inputs/outputs of neighbors. `replace_op_in_outputs(op, replacement)` and `op.replace_input(old, new)` in `_op_utils.py` are the two primitives. Every optimizer pass uses these.
- **Visitor pattern:** iterating `topological_iterator(root)` and applying a transform to each node — this is the visitor design pattern. Python's `singledispatch` makes it clean: dispatch by node type.
- **Reference:** [python-patterns.guide — Visitor](https://python-patterns.guide/) — Brandon Rhodes' treatment; read after Step 21.

### CSE (Common Subexpression Elimination)

- **Concept:** if two subtrees are identical (same op type + same inputs), compute once, reuse the result. Stratum's `_cse.py` implements this.
- **Python implementation:** hash-cons — assign each node a hash based on its type + the hashes of its inputs; equal hashes → candidate for merging. Requires `__hash__` and `__eq__` on node types (or an external hash table keyed on structural equality).
- **Article:** [Wikipedia — Common subexpression elimination](https://en.wikipedia.org/wiki/Common_subexpression_elimination) — concept overview; then read `_cse.py`.

### Linearization / scheduling

- **Topological order = valid execution order.** Post-order DFS on a DAG = reverse topological order (output last).
- **Stratum's split invariant:** all ops before `split_pos` are pre-split (fit phase), all after are post-split (predict phase). The deferred-pop logic in `linearize_dag` enforces this.
- **Buffer pool / liveness analysis:** after linearization, for each op compute the last point where each of its inputs is needed (`remove_after` list in `_input_removal_planning.py`). This is register allocation / liveness analysis from compiler theory.

### Immutable IR vs mutable IR

- Stratum uses mutable IR (nodes have mutable `inputs`/`outputs` lists, in-place rewriting). This is simpler but requires careful bookkeeping. Alternative: immutable IR where rewrites return new nodes (functional style, easier to debug). Know the trade-off.

### Resources

- **Book:** *Crafting Interpreters* (Nystrom, [free online](https://craftinginterpreters.com/)) — the best accessible intro to IR design, AST walking, and optimization passes. Not Python-specific but your C++ background makes Part II very readable.
- **Book:** *Engineering a Compiler* (Cooper & Torczon, 3rd ed.) — the textbook for compiler middle-end (IR, optimization, register allocation). Graduate-level; dip in when you hit a specific Stratum concept.
- **Python AST as a worked example:** `import ast; tree = ast.parse("x + 1"); ast.dump(tree)` — Python's own IR for source code. `ast.NodeVisitor` and `ast.NodeTransformer` are the visitor and rewriter patterns in stdlib form. [Green Tree Snakes — the missing Python AST docs](https://greentreesnakes.readthedocs.io/).
- **Stratum anchor:** read `_optimize.py` top-to-bottom as a complete compiler middle-end pipeline: parse (skrub → Op IR), optimize (CSE, rewrites, choice unrolling), legalize (algebraic rewrites), lower (linearize), schedule.
- **Drill:** build a minimal expression DAG in Python: nodes are `Add(left, right)`, `Mul(left, right)`, `Const(value)`. Write a topological sort, a simple constant-folding pass (replace `Add(Const(1), Const(2))` with `Const(3)`), and an evaluator that walks the DAG.
- **Done when:** you can read an optimizer pass in `_algebraic_rewrites.py` and explain what invariant it maintains and what it transforms.

---

## Step 27 — `__slots__`, `weakref`, memory layout

*For performance-sensitive code; relevant when Op DAGs get large.*

**Symptoms:** high memory usage from many small objects; `weakref` appearing in buffer pool code; `__slots__` in scikit-learn internals.

- **`__slots__`:** [Real Python — `__slots__`](https://realpython.com/python-slots/) — replaces per-instance `__dict__` with a fixed C array of named slots. Memory reduction: ~40-60% per instance. Trade-off: no dynamic attributes, harder to pickle (need `__getstate__`/`__setstate__`). Use when you create millions of small instances (e.g., AST/IR nodes).
- **`weakref`:** [Official docs](https://docs.python.org/3/library/weakref.html) — a reference that doesn't prevent garbage collection. `weakref.ref(obj)` returns a callable that returns `obj` or `None` if collected. `weakref.WeakValueDictionary` — a dict that drops entries when values are garbage-collected; perfect for caches (like a buffer pool that shouldn't keep objects alive). Stratum's `BufferPool` uses a plain dict now (strong refs) — a `WeakValueDictionary` variant would auto-evict on GC.
- **Memory profiling:** `tracemalloc` (stdlib) + [memray](https://github.com/bloomberg/memray) (Bloomberg's profiler, highly recommended) — identify which objects are using the most memory.
- **`sys.getsizeof(obj)`:** returns *shallow* size of one object (doesn't recurse into attributes). Stratum's `_object_size.py` wraps this. For true deep size: `pympler` library or `objgraph`.
- **Done when:** you can profile an Op-heavy run, identify the hot objects, and evaluate whether `__slots__` is worth adding.

---

## Practice grounds (cross-step)

| Resource | What for |
|---|---|
| [Exercism Python track](https://exercism.org/tracks/python) (free) | Small exercises with mentor feedback; filter by concept to drill one step at a time. |
| [TU Python-for-ML course](https://github.com/mahmutoezmen/Python-for-ML-Course) | Sheets 2 (inheritance/NumPy), 5 (autograd/Numba) — mapped to your modules. |
| [fluentpython/example-code-2e](https://github.com/fluentpython/example-code-2e) | Runnable code for every FP chapter; retype, don't read. |
| [Python Morsels](https://www.pythonmorsels.com/) (Trey Hunner; some free) | Weekly intermediate exercises, exactly this skill band. |
| [norvig/pytudes](https://github.com/norvig/pytudes) | Beautiful idiomatic notebooks — style calibration for Step 18. |
| [Crafting Interpreters](https://craftinginterpreters.com/) (Nystrom, free) | The accessible book on IR/compiler design; Step 26 backbone. |
| **Stratum repo** (`Plans/crosscutting/job/Job/repo/stratum/`) | The real practice ground for Steps 22–27. Read one file per session, annotate every pattern. |
| **mlprov repo, AMLS project, Stratum** | All real work. Every step above names a concrete drill against them. |

---

## Two meta-rules

1. **Always drill, never just read.** Predict → run → explain; close the source and rebuild the core example from memory. This is why it sticks.
2. **One step at a time, symptom-driven.** Feeling weak → diagnostic index → one step → "done when" check → back to real work.
