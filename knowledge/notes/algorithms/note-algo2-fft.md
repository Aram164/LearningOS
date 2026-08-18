---
id: note-algo2-fft
type: note
title: "Algo 2 T12 — Reference: Schnelle Fourier-Transformation"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-fft, concept-complex-roots-of-unity, concept-fast-multiplication,
  concept-recurrences-master-theorem]
sources: [source-algo2-hu-materials, source-ottmann-widmayer]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fastfouriertransform.pdf`
> (67 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 12 — Schnelle Fourier-Transformation

*Lectures: 6. Juli `[1-14]`, 8. Juli `[15-end]` — **the final lecture of the
course.***
***Literatur:** Ottmann/Widmayer Abschnitt 1.2. **Leseempfehlung:** von zur
Gathen & Gerhard, *Modern Computer Algebra* (3rd ed., 2013).*

**Agenda (sl. 2):** polynomials — operations and representations · choice of
**Stützstellen** · the FFT · the fast inverse FFT · fast multiplication of
polynomials **and integers** · an alternative to complex roots of unity ·
DFT/FFT of sequences.

> ⚠️ **Scope caution.** The lecture schedule gives the second session as
> `[15-end]` — **53 slides in one sitting**, against 6–21 for every other session
> in the course. Either that lecture was unusually long, or later material was not
> delivered. **Confirm before treating all 67 slides as examinable.**

> 🔗 **This is the bookend of T01.** Lecture 1 asked how fast two integers can be
> multiplied and reached `O(n^{log₂3})`. This lecture returns to the same question
> through polynomials and does better. Saying so is the cleanest possible answer
> to "what did this course do?"

---

## 1. Why polynomials (sl. 4–9)

**The question (sl. 4):** we want to multiply *integers* — why polynomials?

**Answer:** polynomials in one variable share many properties with the integers;
the **coefficients play the role of digits**, but they can be chosen more freely
and **there are no carries**. Crucially, polynomials admit **alternative
representations** that integers do not.

**Sl. 5** shows the parallel explicitly: `2024 · 137` written out in powers of 10
is exactly a polynomial product, except that digits must be carried.

**Formally (sl. 6–7).** A polynomial of degree `n` in `x` over a commutative ring
`R` is `p = a_n x^n + … + a₁x + a₀`. For `t ∈ R`, `p(t)` denotes the value
obtained by substituting; `p(x)` denotes the function `t ↦ p(t)`.

**Addition (sl. 8):** coefficientwise, `c_j = a_j + b_j`.
**Multiplication (sl. 9):** convolution, `c_j = Σ_{s+t=j} a_s b_t`.

---

## 2. Representations (sl. 11–19) — *the heart of the lecture*

> **Three representations of the same polynomial (sl. 11):**
> 1. **Koeffizientendarstellung** — the coefficient list;
> 2. **Nullstellendarstellung** — leading coefficient plus roots;
> 3. **Punkt/Wertdarstellung** — the values at `n` chosen points (**Stützstellen**).

**The point (sl. 12):** different operations are cheap in different
representations.

| Representation | Addition | Multiplication | Evaluation |
|---|---|---|---|
| **Coefficient** (sl. 13) | `O(n)` | **`O(n²)`** (convolution) | fast (Horner) |
| **Roots** (sl. 14) | hard | easy (concatenate roots) | easy |
| **Point/value** (sl. 15–16) | `O(n)` | **`O(n)`** (pointwise!) | needs interpolation |

> **Trade-off (sl. 17).** Coefficient form is the most natural — fast addition and
> evaluation, **slow multiplication**. Point/value form multiplies in linear time
> but is awkward otherwise.

> **The idea (sl. 18–19).** Can we **change representation** fast enough to profit
> from the cheaper operation? Given `p` and `q` of degree `< n` in coefficient
> form: evaluate both at `n` points, multiply the values **pointwise** in `O(n)`,
> then interpolate back. Everything hinges on doing the two conversions fast.

---

## 3. Choosing the Stützstellen (sl. 21–25)

**Recursive approach (sl. 22).** Split `p` by parity of the coefficient index:

$$p(x) = g(y) + x \cdot u(y), \qquad y = x^2$$

where `g` collects the even-indexed coefficients and `u` the odd-indexed ones.
Evaluating `p` at `n` points now reduces to evaluating **two half-degree
polynomials** — but at the points `x²`.

**Why that helps (sl. 23):** if the evaluation points come in **± pairs**, then
`x` and `−x` give the *same* `y = x²`, so the `n` points collapse to `n/2` points
for the subproblems. That halving is the whole recursion.

**Example (sl. 24):** evaluate `p = 2x³ − 5x² + 7x + 11` at the 8 points
`−4,−3,−2,−1,0,1,2,3`.

> **The obstacle (sl. 25):** the ± trick works **once** — squaring a ± pair gives a
> positive number, and positive reals do not come in ± pairs, so the second level
> of recursion has nothing to collapse. **More possibilities exist over the
> complex numbers.**

---

## 4. Complex roots of unity (sl. 27–31) — Phase 0.7

> **Definition (sl. 27).** For `k ∈ ℕ⁺`, a complex number `ω` is a **`k`-th root
> of unity** if `ω^k = 1`. It is **primitive** if additionally `ω^j ≠ 1` for all
> `0 < j < k`.

> **Choice of Stützstellen (sl. 28).** For `n = 2^d` points, use
> `ω_n^0, ω_n^1, …, ω_n^{n−1}` where `ω_n = e^{2πi/n}`.

These are exactly closed under the halving: squaring the `n`-th roots of unity
gives the `n/2`-th roots of unity, **each hit twice**. That is the ± trick,
available at *every* level.

> **The summation lemma (sl. 29–31).**
> $$\sum_{0 \le k < n} \omega_n^{jk} = \begin{cases} n & \text{if } j \equiv 0 \bmod n \\ 0 & \text{otherwise}\end{cases}$$
>
> **Proof.** If `j ≡ 0 mod n` then `ω_n^{jk} = 1` for every `k`, so the sum is `n`.
> Otherwise `z := ω_n^j ≠ 1`, and the geometric sum gives
> `Σ_k z^k = (z^n − 1)/(z − 1) = 0`, since `z^n = (ω_n^n)^j = 1`.

**This lemma is what makes the inverse transform work** — it is used in §6.

---

## 5. The FFT (sl. 33–41)

> **DFT (sl. 33).** For `p` given by coefficients `a = (a₀,…,a_{n−1})`, the
> **discrete Fourier transform** is the vector of values
> `y_j = p(ω_n^j)` for `j = 0,…,n−1`.

> **FFT (sl. 34).** An efficient algorithm for the DFT — **`O(n log n)`** instead
> of the naive `O(n²)`.

```
FFT(a, n)      // n = 2^d, ω_n = e^{2πi/n}
1  if n = 1 then y[0] ← a[0]                        // base case
2  else
3      for j := 0 to n/2 − 1 do
4          g[j] := a[2j]                            // even coefficients
5          u[j] := a[2j+1]                          // odd coefficients
6      y1 ← FFT(g, n/2)
7      y2 ← FFT(u, n/2)
8      for j := 0 to n − 1 do
9          k := j mod (n/2)
10         y[j] := y1[k] + ω_n^j · y2[k]
11 return y
```

> **Runtime (sl. 36).** Two recursive calls on half the input plus `O(n)` work:
> `T(n) = 2T(n/2) + O(n)` = **`O(n log n)`** by the master theorem.

**Correctness (sl. 37–40).** By induction. The identity being exploited (sl. 39):

$$p(x) = a_0 + a_1x + \dots + a_{n-1}x^{n-1} = g(x^2) + x\cdot u(x^2)$$

so `y[j] = p(ω_n^j) = g(ω_n^{2j}) + ω_n^j u(ω_n^{2j})`, and `ω_n^{2j} =
ω_{n/2}^{j mod (n/2)}` — which is exactly `y1[k] + ω_n^j y2[k]` with
`k = j mod (n/2)`.

> 🔗 **T01 cross-wire:** the recurrence `2T(n/2) + O(n)` is the same shape as
> Karatsuba's `3T(n/2) + O(n)`. Here the branching factor is **2**, giving
> `n log n` instead of `n^{log₂3}` — the clearest illustration in the course of
> why the factor is what matters.

---

## 6. The inverse DFT (sl. 43–48)

**Question (sl. 43):** what does the inverse look like, and can it be computed
fast?

**DFT as a linear map (sl. 44).** The transform is a vector–matrix product
`a·V = y` with the **Vandermonde matrix**

$$V = \begin{pmatrix} 1 & 1 & 1 & \cdots & 1 \\ 1 & \omega_n & \omega_n^2 & \cdots & \omega_n^{n-1} \\ 1 & \omega_n^2 & \omega_n^4 & \cdots & \omega_n^{2(n-1)} \\ \vdots & & & \ddots & \vdots \\ 1 & \omega_n^{n-1} & \omega_n^{2(n-1)} & \cdots & \omega_n^{(n-1)^2}\end{pmatrix}$$

> **The inverse (sl. 45–46).** `V⁻¹` has entries `ω_n^{−jk}/n` — **proved using the
> summation lemma of §4**, which makes `V·V⁻¹ = I` fall out. Since `aV = y` iff
> `yV⁻¹ = a`, this gives a formula for recovering the coefficients.

> **Fast inverse (sl. 47).** Computing `a` from `y` is **identical to a DFT up to
> the factor `1/n` and replacing `ω_n` by `ω_n^{−1}`.** So the same `O(n log n)`
> algorithm computes the inverse.

**Summary (sl. 48):** starting from the differing efficiency of polynomial
operations across representations, we now have both conversions in `O(n log n)`.

---

## 7. Fast multiplication (sl. 50–55)

### Polynomials (sl. 50–52)

Given `p` of degree `< s` and `q` of degree `< t` in coefficient form:

1. choose `n = 2^d` **minimal with `n ≥ s + t`** (so `n ≤ 4·max{s,t}`);
2. compute the DFT of both via FFT — `O(n log n)`;
3. multiply the value vectors **pointwise** — `O(n)`;
4. apply the inverse FFT — `O(n log n)`.

> **Theorem (sl. 52).** Two polynomials of degree at most `n−1` with complex
> coefficients can be multiplied in **`O(n log n)`**.

**Why `n ≥ s + t`:** the product has degree `s + t − 2`, so it needs at least
`s + t − 1` values to be determined uniquely.

### Integers (sl. 54–55)

Encode `a` and `b` (given in `s`- and `t`-digit representation to some base) as the
polynomials `p(x) = a₀ + a₁x + … + a_{s−1}x^{s−1}` and likewise `q`; multiply the
polynomials; then **evaluate at the base** and propagate carries.

**Leseempfehlung (sl. 56):** Schönhage & Strassen [1971], *"Schnelle
Multiplikation großer Zahlen"*.

---

## 8. An alternative to complex roots of unity (sl. 58–60)

> **Fact (sl. 58).** Within the **reals**, `z^n = 1` has only the solutions `1`
> and (for even `n`) `−1`. So there are not enough real roots of unity — which is
> precisely why §3's trick stalled and complex numbers were needed.

**Sl. 59:** the addition and multiplication tables of `(ℤ₅, +, ·)` are shown —
and primitive roots of unity **do** exist there.

> **Sl. 60:** computing **modulo suitable numbers** also provides (primitive) roots
> of unity, giving an alternative to the complex numbers — and one that avoids
> floating-point error. *(This is the number-theoretic transform.)*

---

## 9. DFT/FFT of sequences (sl. 62–64)

**Sl. 62:** the definition usually given for "discrete Fourier transform" is in
terms of a **sequence** of complex numbers rather than a polynomial's
coefficients — but it is the same computation.

> **Lemma (sl. 63) and Theorem (sl. 64).** The DFT and inverse DFT of sequences of
> complex numbers can be computed in **`O(n log n)`**.

---

## 10. Überblick and Ausblick (sl. 66–67)

**Überblick.** Polynomials: representations and operations · coefficient vs
point/value form · complex (primitive) `n`-th roots of unity · the FFT and its
inverse · fast multiplication of polynomials and integers.

**Ausblick (sl. 67).** Various theoretical and practical improvements of the FFT ·
**multidimensional DFT/FFT** · the **Hadamard transform** (a special
multidimensional case).

---

## 11. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Why polynomials — digits without carries, alternative representations | sl. 4–5 |
| The three representations and which operation is cheap in each | sl. 11–17 |
| **Coefficient: `O(n²)` multiply · point/value: `O(n)` multiply** | sl. 13, 15 |
| The strategy: convert → multiply pointwise → convert back | sl. 19 |
| `p(x) = g(x²) + x·u(x²)` | sl. 22, 39 |
| Why the ± trick needs complex numbers to repeat | sl. 25 |
| Root of unity, **primitive** root of unity | sl. 27 |
| The choice `ω_n^j`, `ω_n = e^{2πi/n}`, `n = 2^d` | sl. 28 |
| **The summation lemma and its geometric-series proof** | sl. 29–31 |
| FFT pseudocode and `T(n) = 2T(n/2) + O(n)` = `O(n log n)` | sl. 35–36 |
| DFT as `aV = y` with the Vandermonde matrix | sl. 44 |
| `V⁻¹` entries `ω_n^{−jk}/n`, proved via the lemma | sl. 45–46 |
| Inverse = DFT with `ω_n^{−1}` and `1/n` | sl. 47 |
| Multiplication in `O(n log n)`; **why `n ≥ s + t`** | sl. 51–52 |
| Integer multiplication via polynomial encoding + carries | sl. 54–55 |
| Roots of unity exist modulo suitable numbers | sl. 58–60 |

**Traps:** saying the FFT "multiplies polynomials" — it *transforms*; the
multiplication is the trivial pointwise step; forgetting the `n ≥ s + t` sizing
and the reason for it; being unable to prove the summation lemma (it is a
geometric series); claiming real roots of unity suffice; not connecting back to
T01 when asked what the course achieved.
