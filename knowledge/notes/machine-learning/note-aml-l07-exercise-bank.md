---
id: note-aml-l07-exercise-bank
type: note
title: "AML L07 — Exercise Bank (Perceptron, Kernel Trick, Multi-Class)"
created: "2026-07-01"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-perceptron, concept-kernel-trick, concept-xor-problem]
sources: [source-aml-ss26-lectures, source-cs4780-homeworks, source-mit-6034-quizzes,
  source-mit-6036]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect07 linear classifiers/AML_L07_Exercise_Bank.md` (legacy tree). Companions in v3: `note-aml-l07-linear-classifiers` (reference), `note-aml-l07-mock-exam`. The step hook (F.K2) and the Mini Plan are operational and live in
> `work/active/workspace-aml-exam-prep/`.

# AML Lecture 07 — Exercise Bank (Perceptron, Kernel Trick, Multi-Class)

All practice for L07 in one place. Everything here has **solutions** to self-check against.

**Reading-scope rule:** practice matched to what AML L07 covers — **perceptron (primal/dual), separability/XOR, kernel trick, polynomial + RBF kernels, One-vs-Rest + multiclass perceptron**. ⚠️ **No SVM in this lecture** — skip margin/support-vector problems (they dominate most external "kernel" problem sets; take only the kernel-computation parts).

---

## 1. Local material

| File | What it is | Where |
|------|-----------|-------|
| `AML_L07_Ultimate_Reference.md` | Full topic reference (TOC + self-test) | this folder |
| `AML_L07_Mock_Exam.md` | 100-pt mock exam (perceptron trace, kernel checks, RBF, multi-class), verified key | this folder |
| `AML_L07_Mini_Plan.md` | Sequenced study path (videos + readings) | this folder |
| `AML_BonusSheet04_Solution.md` | Worked key to **Bonusblatt 4** (Aufg. 1–2 = L07; Aufg. 3–4 = L08 preview) | this folder |

## 2. Source sheets to solve (in the repo)

- **Bonusblatt 4** (`…/SoSe 2026/Bonus-exercises/zusatz-blatt04.pdf`, dated 23.06.2026, discussed in Übungen ab 07.07.):
  - **Aufgabe 1 (Perceptron)** — XOR-labelled data: convergence? best achievable error? + a full **algorithm trace** with `sign(0)=1` and the boundary plot. *The main L07 drill.*
  - **Aufgabe 2 (Lineare Trennbarkeit)** — 1-D non-separable data → mapping `Φ(x) = (x, x²)` → separable; give w. *Slides 44–45 as an exercise.*
  - Aufgaben 3–4 (single-neuron gates, MLP design) — **L08 scope**; fine as preview.
  - ✓ all solved in `AML_BonusSheet04_Solution.md`.
- **Tutorial deck** `…/Exercise slides/Übung 07.pdf` — perceptron worked example + Besprechung (the "more in the tutorials" of slide 62). Work through the perceptron example before peeking at its resolution.

## 3. External practice — solution-checked, matched to L07

- ✓ **CS4780 HW2 (local)** ⭐ — `…/CS4780-homeworks/2017Spring/hw2/` (perceptron algorithm problems, images `perceptronalg*.jpg`, full solutions `4780_HW2_solutions*.pdf`) + `2018Spring/HW2` / `2018Fall/HW2` variants. The perceptron trace + convergence reasoning in exam format.
- ✓ **CS4780 HW7 — kernel parts only** — `…/CS4780-homeworks/*/HW7/` (kernels; ⚠️ skip the Gaussian-process and SVM sub-parts — beyond L07).
- ✓ **MIT 6.034 past quizzes (with solutions)** ⭐ — the *neural nets / perceptron* sections regularly ask for hand-run perceptron updates and Boolean-gate weights — the closest published match to this lecture's exam format (see LEARNING-RESOURCES §6).
- **MIT 6.036 (OLL)** — auto-graded perceptron unit (implementation + margin-free theory).
- ⚠️ **Skip:** CS4780 HW5 (SVM), Caltech LFD SVM problems, ISLP Ch 9 conceptual exercises on margins — all SVM-scope.

## 4. Books (scoped to L07)

- **CS229 notes Ch 5** (p.49–58) ⭐ — after reading, redo §5.3's kernelized-LMS derivation with the perceptron update instead (that's slide 62). Local: `…/Bücher/CS229 Lecture Notes.pdf`.
- **ESL §4.5.1** (p.130) — reproduce the perceptron-criterion loss and connect it to the lecture's "amount wrong" loss (identical object).
- **Murphy §17.1.2** (p.569) — kernel reference card; check you can state why RBF's implicit dimension is infinite.

---

## 5. Suggested sequence

1. **By-hand trace** — Bonusblatt 4 Aufgabe 1(d) table (`sign(0)=1`!) → final `w = (0, −1, 0)`.
2. **Bonusblatt 4 Aufgabe 2** (Φ-mapping) + gate tables (Aufgabe 3 as L08 preview).
3. **Kernel drills** — `(x·z)²` vs `φ(x)·φ(z)` by hand; one RBF value table for σ² ∈ {0.5, 1, 3}.
4. **`AML_L07_Mock_Exam.md`** (75 min, timed) → self-grade.
5. **CS4780 HW2** (perceptron) + 6.034 quiz sections; HW7 kernel parts if time.

Anything you miss → reread the cited § in `AML_L07_Ultimate_Reference.md`.

---

*No HU AML Altklausuren are public (see `LEARNING-RESOURCES.md` §6). The above is matched, solution-bearing practice, scoped to the lecture.*
