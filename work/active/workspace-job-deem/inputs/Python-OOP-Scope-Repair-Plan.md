# Python OOP & Scope Repair Plan — KW 24

> **Why this exists:** You read FP Ch 14 (PY.08 ✅) and built the §8 resource list in LEARNING-RESOURCES.md, but scope/classes/inheritance/super() still feel shaky in mlprov and job work. Diagnosis: reading without drilling. This plan is **practice-first** — every session ends with you writing code from memory, not just reading.
>
> **Total:** 5 sessions × ~1.5h. Sessions 1–3 this weekend (they unblock mlprov work NOW). Sessions 4–5 after Jun 18.

## Rules of the game (do this or the plan fails)

1. **Predict → run → explain.** Before running any snippet, write down what it prints. Run it. If wrong, figure out why before moving on.
2. **Close the tab, rebuild.** After each reading, close it and reconstruct the core example from memory in a real `.py` file. Can't? Re-read once, try again. That rebuild IS the session.
3. **Type, never paste.** Including drill snippets below.
4. Keep a `python-drills/` folder. One file per session.

---

## Session 1 — Names, values, scope (the root of everything)

Your C++ intuition (variables are boxes holding values) is the bug. In Python, variables are **labels pointing at objects**.

**Read (~70 min):**
1. [Ned Batchelder — Facts and myths about Python names and values](https://nedbatchelder.com/text/names.html) (~40 min) — or the [PyCon talk](https://nedbatchelder.com/text/names1.html)
2. [Real Python — LEGB Rule](https://realpython.com/python-scope-legb-rule/) — only §"Python Scope vs Namespace" and §"functions"; skim the rest

**Drill (~20 min):** paste each into [pythontutor.com](https://pythontutor.com), predict first:

```python
# D1: two names, one object (the mlprov provenance bug pattern)
a = [1, 2, 3]
b = a
b.append(4)
print(a)        # ?

# D2: rebinding is not mutation
a = [1, 2, 3]
b = a
b = b + [4]
print(a)        # ?

# D3: function args are assignments
def f(lst):
    lst.append(99)   # mutates caller's object?
    lst = [0]        # affects caller?
def g():
    x = 10
    def h():
        print(x)     # works? (E in LEGB)
    h()

# D4: the C++ trap — assignment makes a name LOCAL
count = 0
def inc():
    count = count + 1   # UnboundLocalError — why?
```

**Done when:** you can explain in one sentence why passing `X.provenance` around in mlprov shares ONE DataFrame across objects.

---

## Session 2 — Class mechanics: self, instance vs class attributes

**Watch + code along (~60 min):** [Corey Schafer OOP playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc) videos #2 (class variables) and #3 (classmethods/staticmethods). His code: [github.com/CoreyMSchafer/code_snippets → Object-Oriented](https://github.com/CoreyMSchafer/code_snippets/tree/master/Object-Oriented).

**Key reframe:** `obj.method(x)` is just `Class.method(obj, x)`. `self` is not magic — it's an ordinary first argument. A class is a dict of names; attribute lookup goes instance `__dict__` → class → parent classes.

**Drill (~30 min):** from scratch, no reference:

```python
class Module:
    sws_per_lp = 0.75               # class attr — shared
    def __init__(self, name, lp):
        self.name = name            # instance attrs
        self.lp = lp
    def workload(self):
        return self.lp * 30
```

Then predict: what does `Module.workload(m)` do vs `m.workload()`? What happens if you set `m.sws_per_lp = 2` — does it change the class attr? Verify with `m.__dict__` and `Module.__dict__`.

---

## Session 3 — Inheritance + super() (the headache session)

**The one mental model that kills the headache:**
`super()` does NOT mean "my parent." It means **"the next class after me in this object's MRO (method resolution order)."** In single inheritance the next class IS the parent, so the simple intuition usually works — until multiple inheritance (mixins, like `PandasProvenanceMixin`), where the MRO is a single linear sequence through ALL classes and `super()` just moves one step along it. Print it: `ClassName.__mro__`.

**Watch first (~25 min):** Corey Schafer #4 (inheritance) — the gentle version.

**Then read (~45 min):** [Hettinger — Python's super() considered super!](https://rhettinger.wordpress.com/2011/05/26/super-considered-super/) — slowly. His opening example:

```python
class LoggingDict(dict):
    def __setitem__(self, key, value):
        print(f'Setting {key}')
        super().__setitem__(key, value)   # delegate UP the MRO
```

This is *structurally identical* to `ProvDataFrame.__getitem__`: intercept, do your thing (log / record provenance), delegate the real work via `super()`.

**Drill (~20 min):**
1. Close the article. Rebuild `LoggingDict` from memory. Then build `LoggingList(list)` that logs `append`.
2. Build the diamond: `A`, `B(A)`, `C(A)`, `D(B, C)`, each `__init__` printing its name and calling `super().__init__()`. Predict the print order for `D()`. Check against `D.__mro__`.
3. Open `ProvDataFrame` in mlprov and annotate every `super()` call: which class actually gets hit next? (Check `ProvDataFrame.__mro__`.)

**Done when:** drill 2's output stops surprising you.

---

## Session 4 — Subclassing real libraries (mlprov-shaped) — *post-Jun 18*

**Do (~60 min):** [TU Python-for-ML Sheet 2](https://github.com/mahmutoezmen/Python-for-ML-Course) — the inheritance/NumPy exercises. Real exercises with code, already mapped to mlprov/job in HANDOFF.

**Read (~30 min):** [numpy subclassing guide](https://numpy.org/doc/stable/user/basics.subclassing.html) + [pandas subclassing guide](https://pandas.pydata.org/docs/development/extending.html#subclassing-pandas-data-structures) — now Hettinger has given you the model these assume. Explains `__array_finalize__` (why ndarray can't just use `__init__`) and `_metadata`/`_constructor` (how provenance survives pandas ops).

**Drill:** pick one mlprov sklearn skeleton class and explain every line out loud (or to Chat 4). Note the adapter pattern Hettinger describes — that's why the skeletons call `orig_tree.DecisionTreeClassifier.predict(self, X)` explicitly: sklearn classes aren't cooperative super() citizens.

---

## Session 5 — The interpreter, demystified — *post-Jun 18 (light), post-Jul 15 (deep)*

**Light version now (~30 min):** the "interpreter" mystery mostly dissolves with three facts:

1. Everything is an object created at runtime — `def` and `class` are *statements that execute*, not declarations.
2. Every function call creates a **frame**; local scope IS the frame. When the frame dies, locals die.
3. See it physically: `import dis; dis.dis(your_function)` — `LOAD_FAST` = local lookup, `LOAD_GLOBAL` = global lookup. Scope made visible.

**Deep version (post-Jul 15, ~1.5h):** [Allison Kaptur — A Python Interpreter Written in Python](https://aosabook.org/en/500L/a-python-interpreter-written-in-python.html). Your C++ background is an asset here. Optional after: Philip Guo's CPython lectures L1/L3/L8 (see LEARNING-RESOURCES.md §8 Tier 3).

---

## super() cheat card

| Confusion | Resolution |
|---|---|
| "super() calls the parent" | It calls the **next class in the instance's MRO**. Often the parent; not always. |
| "Whose MRO?" | The MRO of the *instance's actual class* (`type(self).__mro__`), not the class where the code is written. That's how mixins work. |
| Why `super().__init__(**kwargs)` chains | Each class strips the kwargs it owns, passes the rest up. Hettinger §"practical advice." |
| When NOT to use super() | Non-cooperative parents (sklearn). Call explicitly: `Parent.method(self, args)` — the adapter pattern. |
| Debug move | `print(Cls.__mro__)` answers 90% of super() questions. |

---

*Created KW 24 (Jun 13). Complements LEARNING-RESOURCES.md §8 — same resources, now ordered into drill sessions. Sessions 1–3 before Jun 18 are justified: they unblock mlprov sprint + job work.*
