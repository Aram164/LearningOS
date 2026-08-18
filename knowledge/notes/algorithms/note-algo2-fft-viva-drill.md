---
id: note-algo2-fft-viva-drill
type: note
title: "Algo 2 T12 — Viva Drill: Schnelle Fourier-Transformation"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-fft, concept-complex-roots-of-unity, concept-fast-multiplication]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fastfouriertransform.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 12 — Viva Drill

> 🎯 **The best closing answer in the course.** T01 asked how fast integers
> multiply and got `O(n^{log₂3})`; T12 answers the same question better. If the
> examiner asks anything like "was war das Thema der Vorlesung?", this is the
> thread that ties twelve topics into one story.

---

## A. The five-minute summary

1. The problem is still multiplication — but polynomials are easier than integers
   because coefficients behave like digits **without carries**, and because they
   have **alternative representations**.
2. Coefficient form multiplies in `O(n²)`; point/value form multiplies in `O(n)`.
   So: **convert, multiply pointwise, convert back.**
3. Converting = evaluating at `n` points. The recursive split
   `p(x) = g(x²) + x·u(x²)` halves the work **if** the points come in ± pairs.
4. Over the reals that works once. Over the complex numbers, the **`n`-th roots of
   unity** regenerate the ± structure at every level.
5. FFT: `T(n) = 2T(n/2) + O(n)` = **`O(n log n)`**.
6. The inverse is the same algorithm with `ω⁻¹` and `1/n` — proved via the
   Vandermonde inverse and the summation lemma.
7. Hence polynomial multiplication in `O(n log n)`, and integer multiplication by
   encoding digits as coefficients and propagating carries.

---

## B. Follow-up trees

**B1. "Warum Polynome, wenn wir Zahlen multiplizieren wollen?"**
- → coefficients behave like digits but **without carries**
- → "Und was ist der eigentliche Vorteil?" → alternative representations
- → "Welche Darstellungen?" → coefficient, roots, point/value
- → "Wo ist die Multiplikation billig?" → point/value, `O(n)` pointwise
- → "Und was kostet sie in Koeffizientendarstellung?" → `O(n²)`

**B2. "Wie werten Sie ein Polynom an `n` Stellen aus?"**
- → the split `p(x) = g(x²) + x·u(x²)`
- → "Was bringt Ihnen das?" → two half-degree polynomials at the squared points
- → "Warum brauchen Sie ± Paare?" → `x` and `−x` give the same `x²`
- → "Warum reicht das über den reellen Zahlen nicht?" ⚠️ → squaring destroys the
  ± structure; positive reals aren't ± pairs
- → "Und über ℂ?" → the `n`-th roots of unity square to the `n/2`-th roots of
  unity, twice over — the structure regenerates

**B3. "Was ist eine primitive Einheitswurzel?"**
- → `ω^k = 1` and `ω^j ≠ 1` for `0 < j < k`
- → "Welche Stellen wählen Sie?" → `ω_n^0,…,ω_n^{n−1}` with `ω_n = e^{2πi/n}`,
  `n = 2^d`
- → "Nennen Sie das Summationslemma." → `Σ_k ω_n^{jk}` is `n` or `0`
- → "Beweisen Sie es." → geometric series; `z^n = 1` kills the numerator
- → "Wo brauchen Sie es?" ⚠️ → to invert the Vandermonde matrix

**B4. "Schreiben Sie die FFT auf."**
- → the pseudocode
- → "Laufzeit?" → `T(n) = 2T(n/2) + O(n)` = `O(n log n)`
- → "Beweisen Sie die Korrektheit des Kombinationsschritts."
- → "Warum `k = j mod n/2`?" → because `ω_n^{2j} = ω_{n/2}^{j mod (n/2)}`

**B5. "Und die Rücktransformation?"**
- → DFT as `aV = y` with the Vandermonde matrix
- → "Wie sieht `V⁻¹` aus?" → entries `ω_n^{−jk}/n`
- → "Wie zeigen Sie das?" → the summation lemma
- → "Und wie schnell?" → same algorithm, `ω⁻¹` and `1/n` → `O(n log n)`

**B6. "Wie multiplizieren Sie damit zwei Polynome?"**
- → FFT both, multiply pointwise, inverse FFT
- → "Wie wählen Sie `n`?" → minimal `2^d` with `n ≥ s + t`
- → "Warum `s + t`?" ⚠️ → the product has degree `s+t−2`, needing `s+t−1` values
- → "Und ganze Zahlen?" → encode digits as coefficients, multiply, **carry**
- → "Wie verhält sich das zu Karatsuba?" 🎯 *the bookend*

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | `p(x) = g(x²) + x·u(x²)` with an example split | 45 s |
| C2 | The 8th roots of unity, and what squaring does | 45 s |
| C3 | The summation lemma with its geometric-series proof | 60 s |
| C4 | FFT pseudocode | 60 s |
| C5 | The Vandermonde matrix and `V⁻¹`'s entries | 45 s |
| C6 | The four-step multiplication pipeline | 30 s |

---

## D. Traps

**D1.** *"Die FFT multipliziert Polynome?"* — It **transforms**. The multiplication
is the trivial pointwise step in between; the FFT does the conversion. Saying it
loosely suggests you don't know which part is hard.

**D2.** *"Reelle Stützstellen würden auch gehen?"* — No. `z^n = 1` has only `1`
and `−1` in the reals, so the halving structure is unavailable after the first
level. This is stated as a *Fakt* on sl. 58 and is the reason complex numbers
enter at all.

**D3.** *"`n` ist einfach der Grad?"* — `n = 2^d` minimal with `n ≥ s + t`, because
the product's degree demands that many sample points.

**D4.** *"Das Summationslemma ist eine Definition?"* — It is a lemma with a
one-line geometric-series proof, and it is what makes the inverse transform work.

**D5.** *"Die inverse DFT braucht einen anderen Algorithmus?"* — The same one, with
`ω_n^{−1}` and a factor `1/n`.

**D6.** *"Man braucht zwingend komplexe Zahlen?"* — No — the deck's §8 shows
primitive roots of unity exist modulo suitable numbers, which also avoids
floating-point error.

---

## E. Two-minute version

> "Ziel ist wieder schnelle Multiplikation, diesmal über Polynome — deren
> Koeffizienten verhalten sich wie Ziffern, nur ohne Überträge, und vor allem
> haben Polynome verschiedene Darstellungen. In Koeffizientendarstellung kostet
> die Multiplikation `O(n²)`, in Punkt/Wert-Darstellung nur `O(n)`, weil man
> punktweise multipliziert. Die Idee ist also: hin transformieren, punktweise
> multiplizieren, zurück transformieren. Auswerten an `n` Stellen macht man
> rekursiv über `p(x) = g(x²) + x·u(x²)`; das halbiert die Arbeit, sofern die
> Stellen in ± Paaren vorliegen, denn dann fallen je zwei auf dasselbe `x²`. Über
> den reellen Zahlen klappt das genau einmal — deshalb nimmt man die komplexen
> `n`-ten Einheitswurzeln `ω_n^j` mit `ω_n = e^{2πi/n}`: quadriert man sie,
> erhält man genau die `n/2`-ten Einheitswurzeln, jede doppelt. Die FFT hat damit
> die Rekurrenz `2T(n/2) + O(n)`, also `O(n log n)`. Die Rücktransformation ist
> dieselbe Rechnung mit `ω⁻¹` und Faktor `1/n`; das zeigt man, indem man die
> Vandermonde-Matrix invertiert, wofür man das Summationslemma braucht. Damit
> multipliziert man Polynome in `O(n log n)` — und ganze Zahlen, indem man die
> Ziffern als Koeffizienten auffasst und am Ende die Überträge verarbeitet."

**~105 seconds.**

---

## F. The closing answer

If asked to summarize the **course**, use the bookend:

> "Die Vorlesung beginnt und endet bei derselben Frage — wie schnell kann man
> multiplizieren. Lecture 1 kommt über Karatsuba auf `O(n^{log₂3})`, indem sie
> vier Teilmultiplikationen auf drei drückt. Lecture 12 kommt über Polynome,
> Darstellungswechsel und die FFT auf `O(n log n)`. Dazwischen liegen
> Datenstrukturen und Graphenalgorithmen, aber das methodische Motiv ist überall
> dasselbe: eine Rekurrenz aufstellen und den Verzweigungsfaktor senken, oder die
> Repräsentation wechseln, bis die teure Operation billig wird."
