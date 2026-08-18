---
id: note-algo2-fft-exercise-bank
type: note
title: "Algo 2 T12 — Exercise Bank: Schnelle Fourier-Transformation"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-fft, concept-complex-roots-of-unity, concept-fast-multiplication]
sources: [source-algo2-hu-materials, source-ottmann-widmayer, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fastfouriertransform.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 12 — Exercise Bank

**Scope:** polynomial representations and operation costs, the recursive
evaluation split, complex roots of unity and the summation lemma, the FFT,
the inverse via the Vandermonde matrix, fast multiplication of polynomials and
integers, modular alternatives.

> ⚠️ **Phase 0.7 first.** If roots of unity are shaky this topic is unreadable.
> The diagnostic is in `note-algo2-phase0-prerequisites`.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-fft` | Reference (§ refs below) | this vault |
| `note-algo2-fft-viva-drill` | Oral drill | this vault |
| `note-algo2-fast-multiplication` | T01 — the problem this closes | this vault |
| Ottmann/Widmayer 1.2 | **Assigned reading** | `material://source-ottmann-widmayer/ow.pdf` |

## 2. Drills

### A. Representations

**A1.** Name the three representations and the cost of multiplication in each.

<details><summary>Solution</summary>

**Coefficient** — `O(n²)` (convolution). **Roots** — easy (concatenate).
**Point/value** — **`O(n)`**, pointwise. *(Ref §2, sl. 13–17.)*
</details>

**A2.** State the overall strategy in one sentence.

<details><summary>Solution</summary>

Convert both polynomials from coefficient to point/value form, multiply the value
vectors pointwise in `O(n)`, convert back — provided both conversions are fast
enough. *(Ref §2, sl. 19.)*
</details>

**A3. [open]** Multiply `p = 1 + 2x` and `q = 3 + x` by convolution, then again by
evaluating at 3 points and interpolating. Check the answers agree.

**A4. [open]** Why can't the roots representation be used for the fast-multiply
trick, even though multiplication is easy there? *(Think about the conversion.)*

### B. The recursive split

**B1.** Write the parity split and say what it buys.

<details><summary>Solution</summary>

`p(x) = g(x²) + x·u(x²)`, with `g` the even-indexed and `u` the odd-indexed
coefficients. Evaluating `p` at `n` points reduces to evaluating two half-degree
polynomials at the squared points. *(Ref §3, sl. 22; §5, sl. 39.)*
</details>

**B2.** Why does the trick stall over the reals?

<details><summary>Solution</summary>

It needs the evaluation points to come in **± pairs**, so that `x` and `−x` share
a value of `y = x²`. Squaring a ± pair yields a positive number, and positive
reals do not form ± pairs — so the collapse happens only at the first level.
*(Ref §3, sl. 25; §8, sl. 58.)*
</details>

**B3. [open]** Do the deck's example (sl. 24): evaluate `p = 2x³ − 5x² + 7x + 11`
at `−4,−3,−2,−1,0,1,2,3` using the recursive approach. Show where the halving
occurs and where it stops.

### C. Roots of unity

**C1.** Define root of unity and primitive root of unity.

<details><summary>Solution</summary>

`ω` is a `k`-th root of unity if `ω^k = 1`; it is **primitive** if additionally
`ω^j ≠ 1` for all `0 < j < k`. *(Ref §4, sl. 27.)*
</details>

**C2.** Why do the `n`-th roots of unity make the recursion work at every level?

<details><summary>Solution</summary>

Squaring the `n`-th roots of unity gives exactly the `n/2`-th roots of unity, each
attained twice — the ± structure regenerates at every level, which is what the
reals could not do. *(Ref §4, sl. 28.)*
</details>

**C3.** State and prove the summation lemma.

<details><summary>Solution</summary>

`Σ_{0≤k<n} ω_n^{jk} = n` if `j ≡ 0 mod n`, else `0`. If `j ≡ 0 mod n` each term is
1. Otherwise `z := ω_n^j ≠ 1` and the geometric series gives
`Σ_k z^k = (z^n − 1)/(z − 1)`; since `z^n = (ω_n^n)^j = 1`, the numerator is 0.
*(Ref §4, sl. 29–31.)*
</details>

**C4. [open]** Draw the 8th roots of unity on the unit circle and mark what
squaring does to them.

**C5. [open]** Verify the summation lemma numerically for `n = 4`, `j = 0,1,2,3`.

### D. The algorithm

**D1.** Write the FFT and give its recurrence.

<details><summary>Solution</summary>

See reference §5. Split into even/odd coefficient lists, recurse on each of size
`n/2`, then combine `y[j] = y1[k] + ω_n^j·y2[k]` with `k = j mod (n/2)`.
`T(n) = 2T(n/2) + O(n)` = `O(n log n)`. *(Ref §5, sl. 35–36.)*
</details>

**D2.** Prove the combination step is correct.

<details><summary>Solution</summary>

`p(x) = g(x²) + x·u(x²)`, so `y[j] = p(ω_n^j) = g(ω_n^{2j}) + ω_n^j·u(ω_n^{2j})`.
And `ω_n^{2j} = ω_{n/2}^{j mod (n/2)}`, so `g(ω_n^{2j}) = y1[k]` and
`u(ω_n^{2j}) = y2[k]` with `k = j mod (n/2)`. *(Ref §5, sl. 39–40.)*
</details>

**D3. [open]** Run FFT by hand on `a = (1,2,3,4)` with `n = 4`, `ω₄ = i`. Verify
against direct evaluation at `1, i, −1, −i`.

**D4. [open]** Compare `T(n) = 2T(n/2) + O(n)` with Karatsuba's
`T(n) = 3T(n/2) + O(n)` (T01). Solve both with the master theorem and say in one
sentence what the comparison shows. *(Ref §5 — the deck's own bookend.)*

### E. The inverse

**E1.** Express the DFT as a matrix product and give `V⁻¹`.

<details><summary>Solution</summary>

`a·V = y` with `V` the Vandermonde matrix `V_{jk} = ω_n^{jk}`. Its inverse has
entries `ω_n^{−jk}/n`, which is verified using the summation lemma. *(Ref §6,
sl. 44–46.)*
</details>

**E2.** Why is the inverse computable by the *same* algorithm?

<details><summary>Solution</summary>

Recovering `a` from `y` is identical to a DFT except for the factor `1/n` and
using `ω_n^{−1}` in place of `ω_n`. So the same `O(n log n)` routine applies.
*(Ref §6, sl. 47.)*
</details>

**E3. [open]** Show `V·V⁻¹ = I` explicitly using the summation lemma — this is the
one place the lemma does real work.

### F. Multiplication

**F1.** Give the four steps and the theorem.

<details><summary>Solution</summary>

Pick `n = 2^d` minimal with `n ≥ s + t`; FFT both polynomials; multiply values
pointwise; inverse FFT. **Theorem (sl. 52):** two polynomials of degree ≤ `n−1`
with complex coefficients multiply in `O(n log n)`. *(Ref §7.)*
</details>

**F2.** Why must `n ≥ s + t`?

<details><summary>Solution</summary>

The product has degree `s + t − 2`, so `s + t − 1` values are needed to determine
it uniquely; fewer points would alias. *(Ref §7, sl. 51.)*
</details>

**F3. [open]** Describe integer multiplication via this route, including what has
to happen **after** the polynomial multiplication. *(Ref §7, sl. 54–55 — the
carries.)*

**F4. [open]** Compare the resulting integer-multiplication bound with T01's
`O(n^{log₂3})`. Which wins, and from roughly what size?

### G. Alternatives and extensions

**G1. [open]** Why is there an interest in avoiding complex numbers? Look at the
`(ℤ₅,+,·)` tables on sl. 59 and find a primitive 4th root of unity. *(Ref §8.)*

**G2. [open]** What is the DFT of a *sequence*, and how does it relate to the
polynomial version? *(Ref §9, sl. 62.)*

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| O/W 1.2 | **Assigned reading** | — |
| von zur Gathen & Gerhard | Leseempfehlung; suitable sections only | the bulk of the book |
| Schönhage & Strassen 1971 | Named in T01/T12 as context | its analysis |
| Frankfurt Klausuren | FFT items as explain-aloud drill | written framing |

**Filter:** in scope are representations, the recursive split, roots of unity, the
FFT and inverse, and multiplication of polynomials and integers. The
**Ausblick items — multidimensional DFT and the Hadamard transform — are names
only.** Signal-processing applications, windowing, and FFTW-style implementation
concerns are outside the course.

> ⚠️ **Open scope question:** the second lecture session covers `[15-end]` = 53
> slides, far more than any other session. Confirm with the lecturer or a
> classmate how far the course actually got before treating §8–§9 (alternatives,
> sequences) as examinable.
