---
id: note-python-depth-drills
type: note
title: "Python Depth Drills — the nine-stage ladder"
created: "2026-08-02"
role: reference
state: evolving
authorship: mixed
concepts: [concept-python]
sources: [source-python-depth-drills, source-fluent-python, source-slatkin-effective-python]
---

# Python Depth Drills — the nine-stage ladder

**Where it lives:** `material://source-python-depth-drills` →
`LearningOS/materials/Programming/python/python-depth-drills/`. Start at its `README.md`.

**What it is:** nine stages through the middle of the language — the band between "knows the
syntax" and "reads an unfamiliar OOP codebase without friction". Each stage is one markdown
guide (claim under test → prerequisites → ranked reading → drills → done-when → traps checklist)
and one Jupyter notebook (~20 predict-then-run questions with folded solutions). 165 questions
total, all code cells verified to execute.

Stages 1–5 are the split-and-extended form of an earlier single notebook; Stages 0, 6, 7
and 8 are new.

---

## Why it exists beside the other Python documents

Four Python documents now sit in this repository, and they answer different questions. Keeping
that distinction is the point — the material was consolidated here specifically so Python
wouldn't fragment across the job tree and the learning tree.

| Document | Question it answers | Shape |
|---|---|---|
| [[note-python-intermediate-roadmap]] | *"Something feels shaky and I don't know what it's called."* | Symptom → step lookup, 27 steps, Fluent-Python-skeletoned |
| [[note-python-oop-scope-repair-plan]] | *"I read it and it still doesn't stick."* | Five practice-first drill sessions |
| **This** | *"I want to close the gap in order, and know when a stage has landed."* | Ordered, gated ladder with a self-test per stage |
| [[note-programming-toolbox-bootcamp]] | *"How do I run the thing at all?"* | Tooling: shell, Git, venv, VS Code, pytest, Docker (historical; the tools half is still the only copy) |

> **Fragmentation closed.** All four Python planning documents now live in this
> repository. [[note-python-oop-scope-repair-plan]] and [[note-programming-toolbox-bootcamp]]
> were the last two — both were still only in `Plans/Programming/python/` (legacy, frozen), and
> the depth-drill guides cite Repair Plan sessions by number, so those citations pointed outside
> the canon. Bodies migrated verbatim. The Bootcamp is kept for its **tools** half (shell / Git /
> venv / VS Code / pytest / Docker), which nothing else here covers; its Python half is
> superseded by this ladder.

---

## Why nine stages and not five

The earlier plan had five: functions as objects, scope & closures, decorators, classes as
objects, imports & registration. Checked against the competency map in the Level-Up document,
four gaps rated *needs 4–5 / currently 2–3* had no stage covering them:

| Gap | Rating | Stage added |
|---|---|---|
| Identity, mutation, aliasing, invariants | **needs 5, currently 2** — the widest gap on the map | **Stage 0** |
| Data model / dunders (`__slots__`, `__eq__`, `__hash__`, `__repr__`) | needs 4, currently 2–3, "copied shape" | **Stage 6** |
| Generators / iterators | needs 4, currently 3 | **Stage 7** |
| ABCs / Protocols / interfaces | needs 4, currently 2, "implements an implicit interface, never declares one" | **Stage 8** |

Stage 0 is the structurally important one. Stages 2, 4 and 5 each restate the same
rebinding-vs-mutation rule in a different costume — closures capture names, class attributes are
shared objects, `from x import y` copies a binding. Without Stage 0 underneath them they read as
three unrelated mysteries rather than one rule seen three times.

Stage 8 also gave a home to the *tag-dispatch vs subclass polymorphism* comparison, which was in
the Level-Up session list but had nowhere to sit in a five-stage plan.

---

## The ladder

| # | Stage | Q | Unlocks |
|---|---|---:|---|
| 0 | Names, identity & mutation | 20 | everything |
| 1 | Functions as first-class objects | 19 | 2, 3, 8 |
| 2 | Scope & closures | 19 | 3 |
| 3 | Decorators | 20 | 5 |
| 4 | Classes as objects | 20 | 6, 8 |
| 5 | Imports & registration | 17 | registry/plugin code |
| 6 | The data model & dunders | 18 | 7, 8 |
| 7 | Generators & iterators | 15 | tree/graph traversal code |
| 8 | Interfaces & dispatch | 14 | design reviews |

Full order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → capstone. Two shorter paths:
**0 → 1 → 2 → 3 → 5** for anything registry- or plugin-shaped; **0 → 4 → 6 → 7** for anything
tree- or IR-shaped. Stage 8 sits last deliberately — it is the only stage that is mostly
judgement, and judgement needs the other eight underneath it.

---

## The shelf it added

`SHELF.md` inside the material is the companion to the per-stage reading lists. It holds two
things the stages don't own:

- **Books worth adding**, with a per-stage mapping so a new book slots into the ladder:
  [[source-slatkin-effective-python]] (the closest complement to Fluent Python at this band),
  [[source-cosmicpython-architecture-patterns]] (free; Stage 8's design half),
  [[source-viafore-robust-python]], [[source-beazley-python-distilled]].

  > **2026-08-05 — the mapping paid off.** [[source-slatkin-effective-python]] arrived and moved
  > from "worth adding" to the shelf (`SHELF.md` §1a). Two files, one record: the **full text is
  > the 2nd ed. (90 items)**, and an 80-page **3rd-ed publisher sample** carries the complete
  > 125-item contents but no item bodies. Citations throughout use **3rd-ed numbering** — the
  > edition the guides were drafted against — with a 3e→2e crosswalk in §1a so the numbers stay
  > usable against the readable copy.
  >
  > The renumbering was not bookkeeping. It surfaced items the 2nd ed. simply doesn't have and
  > the ladder had been arguing for on its own: **3e Item 49, "Prefer Object-Oriented
  > Polymorphism over `functools.singledispatch`"** is Stage 8's expression-problem judgement
  > stated outright; **Item 30** ("Know That Function Arguments Can Be Mutated") is Stage 0's
  > whole claim in one rule; **Items 46 and 89** are Stage 7's one-shot-iterator fix rather than
  > just its hazard. `SHELF.md` §3a/3b/3c also gained their first coverage of testing, debugging
  > and profiling — and §3c now hands off to the Rust track through 3e Items 94–96, which are
  > the decision procedure for *whether* to leave Python that [[note-rust-learning-plan]]
  > otherwise assumes already happened.
- **Cross-cutting topics no stage owns** — testing ([[source-pytest-docs]],
  [[source-hypothesis-docs]]), debugging (`pdb`, PDSH `01.06`), performance
  (PDSH `01.07`, `cProfile`, `tracemalloc`), style. Each was a genuine hole: the plan's method is
  *rebuild-blind*, and nothing in it tested the rebuilds.

Newly registered online sources these stages lean on: [[source-beazley-generator-tricks]],
[[source-hunner-iterator-protocol]], [[source-coghlan-import-traps]],
[[source-rhodes-python-patterns]], [[source-powell-python-expert]],
[[source-hettinger-class-toolkit]]. The Python sources already registered from the legacy §8
intake (Batchelder, LEGB, Python Tutor, Schafer's OOP playlist, the MRO docs, Kaptur, Guo) are
cited by ID rather than re-registered.

---

## Job boundary

Questions tagged `[Stratum]` are anchored to the BIFOLD/DEEM query optimizer. They are
deliberately renamed and re-shaped, and are answerable with no access to that repository — a
concrete system makes the abstract question sharp, that's all.

The **file-level** anchors — which real files to open per stage, which of Aram's own merged
commits to read back — were split out into `Job/python-drills/STRATUM-ANCHORS.md` and stay
outside this tree under the job-quarantine rule (`CLAUDE.md` §13). Nothing in this material
depends on that file; open it alongside the guides only when working the job track.

---

## Verification trail

Not a mastery claim — a record of what was checked when the material was built:

- All 157 code cells across the ten notebooks execute with zero unhandled errors
  (`_build/verify.py`, kept in the material so it can be re-run after any edit).
- Actual cell output was captured and diffed against the claimed output in every newly written
  solution; **19 mismatches were found and corrected** — among them
  `partial` rather than `functools` as a printed type name, `__init_subclass__` reporting as
  `method` rather than `builtin_function_or_method`, and `deepcopy`'s memo printing twice rather
  than four times.
- One infinite-loop hazard removed before shipping (a `__getitem__` that never raises
  `IndexError`, which would have hung the kernel on `list()`).
- Links: the mCoding video URLs could not be verified, so those citations point at the channel
  plus a search term rather than risking dead links. Everything else was either inherited from
  the already-verified Roadmap or spot-checked.

**No stage has been worked yet** — the material was built, not consumed. Evidence of working
through it belongs here as it accumulates.
