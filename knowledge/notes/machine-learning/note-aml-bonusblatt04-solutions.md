---
id: note-aml-bonusblatt04-solutions
type: note
title: "AML Bonusblatt 04 — Worked Solutions (L07 perceptron / L08 preview)"
created: "2026-07-01"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-perceptron, concept-xor-problem, concept-neural-network]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect07 linear classifiers/AML_BonusSheet04_Solution.md` (legacy tree). Companions in v3: `note-aml-l07-exercise-bank` (bank cites these Aufgaben). The step hook (F.K2) and the Mini Plan are operational and live in
> `work/active/workspace-aml-exam-prep/`.

# Bonusblatt 4 — Worked Solutions (Perceptron, Separability, Single-Layer NN, MLP)

*Sheet: `…/SoSe 2026/Bonus-exercises/zusatz-blatt04.pdf` (dated 23.06.2026; besprochen in den Übungen ab 07.07.). Aufgaben 1–2 = **AML L07** scope; Aufgaben 3–4 = **AML L08** scope (single neuron as gate, MLP design) — solved here for completeness, revisit them in the L08 unit.*
*All numerics computer-verified (NumPy). Convention from the sheet: `sign(0) = 1`; step `g(z) = 1 iff z ≥ 0`.*

---

## Aufgabe 1 (Perceptron)

**Data (a):** P1 ([0,1], +1) · P2 ([1,0], +1) · P3 ([0,0], −1) · P4 ([1,1], −1).

**a)** Plot the four corners of the unit square: the positives sit on one diagonal, the negatives on the other — this is exactly the **XOR pattern** (labels ±1 instead of 0/1). **D is not linearly separable**: no line can put (0,1) and (1,0) on one side and (0,0), (1,1) on the other (proof: the 4-inequality contradiction, Reference §10).

**b)** **No.** The perceptron converges **iff** the data is linearly separable [VL07 slide 27]. On D there is always ≥1 misclassified point, so the update loop never terminates — the boundary jiggles forever.

**c)** Any linear boundary classifies **at most 3 of the 4** XOR points correctly (computer-verified over a weight grid), so the best achievable training error is **1/4 = 25 %** — reached at some intermediate iterate, never held (the algorithm keeps updating).

**d)** Data: P1 ([0,1], +1) · P2 ([1,0], −1) · P3 ([0,0], +1) · P4 ([1,1], −1). *(Separable: label = +1 ⟺ x₁ = 0.)* Init `w = [0,0,0]`, augmented `x = [1, x₁, x₂]`, order P1→P4, `sign(0)=1`:

| i | x⁽ⁱ⁾ | y_true | w·x | ŷ | update? | w after |
|---|---|---|---|---|---|---|
| 1 | [1,0,1] | +1 | 0 | **Sign(0)=+1** ✓ | no | [0, 0, 0] |
| 2 | [1,1,0] | −1 | 0 | +1 ✗ | w += (−1)·x | **[−1, −1, 0]** |
| 3 | [1,0,0] | +1 | −1 | −1 ✗ | w += (+1)·x | **[0, −1, 0]** |
| 4 | [1,1,1] | −1 | −1 | −1 ✓ | no | [0, −1, 0] |
| 1 | [1,0,1] | +1 | 0 | +1 ✓ | no | [0, −1, 0] |
| 2 | [1,1,0] | −1 | −1 | −1 ✓ | no | [0, −1, 0] |
| 3 | [1,0,0] | +1 | 0 | +1 ✓ | no | [0, −1, 0] |
| 4 | [1,1,1] | −1 | −1 | −1 ✓ | no | [0, −1, 0] |

Second pass is clean → converged after **2 updates**:  **w = [w₀, w₁, w₂] = [0, −1, 0]**.

**e)** Boundary: `w·x = −x₁ = 0` → the **vertical line x₁ = 0** (the x₂-axis). Points with x₁ = 0 lie *on* the boundary and are predicted **+1** via `sign(0)=1` (P1, P3 ✓); x₁ = 1 gives z = −1 → **−1** (P2, P4 ✓). *(Plot: positives on the x₂-axis, negatives at x₁=1, boundary = the axis itself.)*

> Dual-form check (Reference §7): updates hit P2 once (α₂=1, y=−1) and P3 once (α₃=1, y=+1): `w = −[1,1,0] + [1,0,0] = [0,−1,0]` ✓.

---

## Aufgabe 2 (Lineare Trennbarkeit)

**Data:** x₁ ∈ {−3,−2,−1,0,1,2,3}, y = (−1,−1,+1,+1,+1,−1,−1).

**a)** On the 1-D number line the +1 class sits **in the middle** (|x₁| ≤ 1) with −1 on both flanks (|x₁| ≥ 2). A single threshold splits the line into two half-lines only → **not linearly separable** in 1-D.

**b)** Mapping `Φ(x) = (x, x²)`:

| x₁ | y | x₁² |
|---|---|---|
| −3 | −1 | 9 |
| −2 | −1 | 4 |
| −1 | +1 | 1 |
| 0 | +1 | 0 |
| 1 | +1 | 1 |
| 2 | −1 | 4 |
| 3 | −1 | 9 |

**c)** In the (x, x²) plane the classes separate **horizontally**: all +1 have x² ≤ 1, all −1 have x² ≥ 4. Any horizontal line x² = c with 1 < c < 4 works, e.g. **x² = 2.5**. As weights on augmented `(1, x, x²)`:

```
w = (w₀, w₁, w₂) = (2.5, 0, −1)      z = 2.5 − x²  ≥ 0  ⟺  x² ≤ 2.5  →  +1
```

Check: x=0 → z=2.5 → +1 ✓ · x=±1 → 1.5 → +1 ✓ · x=±2 → −1.5 → −1 ✓ · x=±3 → −6.5 → −1 ✓.

> This is VL07 slides 44–45 as an exercise: non-separable in x-space, separable after a quadratic feature map — the seed of the kernel idea.

---

## Aufgabe 3 (Single-Layer NN — step activation) *(L08 scope)*

Network: `a = g(w₀ + w₁x₁ + w₂x₂)`, `g(z) = 1 iff z ≥ 0`.

**a)** `w₀ = −15, w₁ = w₂ = 10`:

| Input | z | a |
|---|---|---|
| (0,0) | −15 | 0 |
| (0,1) | −5 | 0 |
| (1,0) | −5 | 0 |
| (1,1) | +5 | 1 |

**b)** Fires only when *both* inputs are 1 → **AND** (x₁ ∧ x₂).

**c)** `w₀ = −5`:

| Input | z | a |
|---|---|---|
| (0,0) | −5 | 0 |
| (0,1) | +5 | 1 |
| (1,0) | +5 | 1 |
| (1,1) | +15 | 1 |

**d)** Fires when *at least one* input is 1 → **OR** (x₁ ∨ x₂).

> Moral (→ L08): the **same architecture** computes different logical functions purely by shifting the bias — weights are the program.

---

## Aufgabe 4 (FNN: "is the list of length 4 strictly ascending?") *(L08 scope)*

Want `y = 1` iff `x₁ < x₂ < x₃ < x₄` (inputs real; equality counts as *not* ascending). Architecture: `h = g(W⁽¹⁾x + b⁽¹⁾)` (3 hidden units), `y = g(w⁽²⁾·h + b⁽²⁾)`, step g.

**a)** Neuron `h₁ = 1 iff x₁ ≥ x₂`: `z = x₁ − x₂ ≥ 0 ⟺ x₁ ≥ x₂`, so

```
1) w₁ = 1     2) w₂ = −1     3) b = 0
```

**b)** Let each hidden unit detect one **violation** `xᵢ ≥ xᵢ₊₁`:

```
        ⎡ 1  −1   0   0 ⎤
W⁽¹⁾ =  ⎢ 0   1  −1   0 ⎥        b⁽¹⁾ = (0, 0, 0)
        ⎣ 0   0   1  −1 ⎦
```

`hᵢ = 1` ⟺ violation between position i and i+1. The list is strictly ascending ⟺ **no violation** ⟺ h = (0,0,0). Output must fire exactly then:

```
w⁽²⁾ = (−1, −1, −1)        b⁽²⁾ = 0.5
```

Check: h = (0,0,0) → z = 0.5 ≥ 0 → **y = 1** ✓; any hᵢ = 1 → z ≤ −0.5 < 0 → **y = 0** ✓. Equal neighbours give z = 0 in the hidden unit → g(0) = 1 → violation → y = 0 ✓ (strictness handled).

> Any positive b⁽²⁾ < 1 works (e.g. 0.5); scalings of the rows of W⁽¹⁾ too — step networks are scale-invariant, same lesson as the perceptron.

---

*Cross-refs: Reference §§6–11 (`AML_L07_Ultimate_Reference.md`); Aufgaben 3–4 forward-link to the L08 unit (forward pass, gates → XOR by stacking).*
