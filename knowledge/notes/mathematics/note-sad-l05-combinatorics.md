---
id: note-sad-l05-combinatorics
type: note
title: "SaD Lecture 05 — Ultimate Reference: Classical Combinatorics"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-combinatorics]
sources: [source-sad-ss26-lectures, source-fahrmeir-statistik, source-blitzstein-hwang]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect05 combinatorics/SaD_L05_Ultimate_Reference.md` (legacy tree).

# SaD Lecture 05 — Ultimate Reference: Classical Combinatorics

*Synthesized from: SaD L05 (Leser, slides by W. Kössler, HU SoSe 2026) `Lecture-slides/05_combinatorics.pdf` (34 slides) + Blitzstein Ch 1 (counting, story proofs) + Fahrmeir Ch 4 (Kombinatorik). Provides the counting tools L04's Laplace/birthday problems assumed.*
*Created: KW 28 (Jul 2026) — fifth per-lecture SaD unit (3-file variant, no Mock Exam); last of the requested L01–L05 batch.*

---

## Table of Contents

1. [Why Combinatorics (the link to probability)](#1-why-combinatorics)
2. [The Decision Grid — pick the right case](#2-the-decision-grid)
3. [Permutations](#3-permutations)
4. [Variations (ordered selections)](#4-variations)
5. [Combinations (unordered selections)](#5-combinations)
6. [Combinations with Replacement — stars & bars](#6-combinations-with-replacement)
7. [The Six Formulas (memorize this)](#7-the-six-formulas)
8. [Worked Examples](#8-worked-examples)
9. [Hypergeometric Probability (L07 preview)](#9-hypergeometric-probability)
10. [Binomial Identities & Stirling](#10-binomial-identities--stirling)
11. [Summary and Cross-Wire Moments](#11-summary-and-cross-wire-moments)

---

## 1. Why Combinatorics

**[Source: SaD L05, slides 5–6]**

Combinatorics counts **how many combinations are possible** in discrete sets — permutations, variations, combinations, partitions. It is the engine of **probabilistic reasoning**: in a Laplace experiment P(A) = |A|/|Ω| (L04 §4), so you need to *count* the size of the event A and the sample space Ω. L04 already leaned on this (the birthday paradox's 365³² and the "all-distinct" product). Historically it grew out of gambling analysis (Pascal, Leibniz, 17th c.).

**The one question that selects the formula:** when you build a selection/arrangement, ask two things —

1. **Does order matter?** (is (A,B) different from (B,A)?)
2. **Are repetitions allowed?** (can the same element appear twice — "with replacement"?)

Those two yes/no answers pick exactly one of the six cases.

---

## 2. The Decision Grid

**[Source: SaD L05, slides 6–7, 27]**

Choosing **k** items from **n** distinct items:

| | **order matters** | **order doesn't matter** |
|---|---|---|
| **without replacement** (no repeats) | **Variation:** n!/(n−k)! | **Combination:** C(n,k) = n!/(k!(n−k)!) |
| **with replacement** (repeats allowed) | **Variation:** nᵏ | **Combination:** C(n+k−1, k) |

**Permutations** are the special case **k = n** (use *all* elements):

- all n **distinct** → **n!**
- with **indistinguishable groups** of sizes k₁,…,kₛ → **n! / (k₁!·…·kₛ!)** (multinomial).

**Reading the grid (mnemonics):**

- *Order matters* → you're building **tuples/sequences** (podium places, PINs). *Order doesn't* → **sets/hands** (lottery, committees).
- *Without replacement* shrinks the pool each pick (n, n−1, n−2, …). *With replacement* keeps it at n every pick.
- Combinations = variations with the k! redundant orderings **divided out**.

---

## 3. Permutations

**[Source: SaD L05, slides 8–14]**

**Without replacement (all distinct):** arrange n distinct objects in a row. n choices for the first slot, n−1 for the second, … → **n!**.

**With replacement / indistinguishable elements:** you have n objects but some are identical, in groups of sizes k₁,…,kₛ (Σkᵢ = n). Every rearrangement *within* a group is invisible, so divide n! by the internal orderings:
$$\frac{n!}{k_1!\,k_2!\cdots k_s!}\quad\text{(multinomial coefficient)}.$$
This is the "anagram" count and the **Skat deal** (§8). Special case s=2 gives the binomial coefficient.

---

## 4. Variations

**[Source: SaD L05, slides 15–19]** — *ordered selections of k out of n ("k-tuples").*

**Without replacement:** choose k distinct, order matters. n·(n−1)···(n−k+1) =
$$\frac{n!}{(n-k)!}.$$
It's a permutation that **stops after k** picks; for k = n it coincides with n!. *(Sprint top-3 of 8 → 8·7·6 = 336, §8.)*

**With replacement:** choose k, order matters, repeats allowed. Each of the k slots independently has n options →
$$n^k.$$
*(PIN codes: 10⁴ = 10,000; k letters: 26ᵏ.)*

---

## 5. Combinations

**[Source: SaD L05, slides 21–23]** — *unordered selections of k out of n ("k-subsets/hands").*

**Without replacement:** choose k distinct, order irrelevant. Start from the n!/(n−k)! variations, then divide by the **k!** orderings that don't matter → the **binomial coefficient**:
$$\binom{n}{k} = \frac{n!}{k!\,(n-k)!}.$$
*(Lotto "5 aus 49": C(49,5) ≈ 1.9 million, §8.)* Reads "n choose k."

---

## 6. Combinations with Replacement

**[Source: SaD L05, slides 24–26]** — *unordered, repeats allowed; the "stars & bars" case.*

$$\binom{n+k-1}{k} = \frac{(n+k-1)!}{k!\,(n-1)!}.$$

**Why (the Gummibärchen / stars-and-bars proof, slide 26).** You pack k candies choosing from n colours (0…k of each). Encode a pack as k **stars** (the candies) separated into n colour-groups by **n−1 bars**. Example n=4, k=3, "2 red, 0 green, 1 blue, 0 yellow" → `★★|·|★|·` → as a binary string `110010`. Every valid pack ↔ one arrangement of k stars and n−1 bars in n+k−1 positions; choosing which k of those positions are stars is a plain combination:
$$\binom{n+k-1}{k}.$$
*(n=4,k=3 → C(6,3) = 20 different packs.)*

**Urn intuition (slide 25):** with replacement the urn "grows" by the drawn element each time (except the last), so you effectively choose from n+k−1, and dividing by k! removes order.

---

## 7. The Six Formulas

**[Source: SaD L05, slide 27 — the "remember these" summary]**

| Case | Order? | Repeats? | Formula |
|---|---|---|---|
| **Permutation, distinct** | — (all n) | no | **n!** |
| **Permutation, groups** | — (all n) | identical items | **n! / (k₁!···kₛ!)** |
| **Variation w/o replacement** | yes | no | **n! / (n−k)!** |
| **Variation with replacement** | yes | yes | **nᵏ** |
| **Combination w/o replacement** | no | no | **C(n,k) = n!/(k!(n−k)!)** |
| **Combination with replacement** | no | yes | **C(n+k−1, k)** |

> **The 3-step exam reflex:** (1) *Am I using all elements (permutation) or choosing k?* (2) *Does order matter (variation) or not (combination)?* (3) *Repeats allowed (with replacement) or not?* Those three answers land you on exactly one row.

---

## 8. Worked Examples

**[Source: SaD L05, slides 13, 17, 23, 26, 29 — all verified]**

- **Skat deal (slide 13) — permutation with groups / multinomial.** 32 cards → 10 each to three players + 2 in the Skat. Count = how many ways to label the 32 cards by *destination*: $\frac{32!}{10!\,10!\,10!\,2!}$ = 2,753,294,408,504,640 (≈ 2.75 × 10¹⁵).
- **Sprint podium (slide 17) — variation without replacement.** Top-3 finishers among 8 starters: 8!/(8−3)! = 8·7·6 = **336**.
- **Lotto 5-subsets (slide 23) — combination without replacement.** Number of different 5-number picks from 49: C(49,5) = **1,906,884** (≈ 2 million).
- **Gummibärchen (slide 26) — combination with replacement.** k=3 candies, n=4 colours: C(4+3−1, 3) = C(6,3) = **20** packs.
- **PIN / letters — variation with replacement.** 4-digit PIN: 10⁴ = 10,000; 3 letters: 26³ = 17,576.
- **Seating (Example 1, slide 29) — Laplace via counting.** r students into n compartments: all events nʳ (each student any compartment, with replacement, ordered by student); "each in its own compartment" = n!/(n−r)! → P = [n!/(n−r)!]/nʳ. (This is the birthday-paradox structure from L04 §6.)

---

## 9. Hypergeometric Probability

**[Source: SaD L05, slides 30–32]** — *the combinatorics → probability payoff; previews the L07 hypergeometric distribution.*

Urn with **n** balls: **n₁** "black" (successes), **n − n₁** "white." Draw **k** without replacement. Probability of **exactly k₁** black:
$$P(A) = \frac{\dbinom{n_1}{k_1}\dbinom{n-n_1}{k-k_1}}{\dbinom{n}{k}}.$$

The logic is pure counting: *(ways to pick k₁ of the black) × (ways to pick the remaining k−k₁ of the white) ÷ (ways to pick any k)* — a Laplace ratio |A|/|Ω| built from combinations.

**Lotto "5 richtige" (6 aus 49).** n=49, n₁=6 winning numbers, draw k=6, want k₁=5:
$$P = \frac{\binom{6}{5}\binom{43}{1}}{\binom{49}{6}} = \frac{6\cdot 43}{13{,}983{,}816} = \frac{258}{13{,}983{,}816} \approx \textbf{1 in 54,201}.$$

This formula **is** the hypergeometric distribution — L07 gives it a name and studies its mean/variance and its relation to the binomial (draws *with* replacement → binomial).

---

## 10. Binomial Identities & Stirling

**[Source: SaD L05, slides 34–35]**

**Binomial coefficient facts** worth having:

- Symmetry: C(n,k) = C(n, n−k).
- Pascal's rule: C(n,k) = C(n−1, k−1) + C(n−1, k).
- Binomial theorem: (a+b)ⁿ = Σₖ C(n,k) aᵏ bⁿ⁻ᵏ (the source of the name; underlies the L07 Binomial distribution).
- Row sum: Σₖ C(n,k) = 2ⁿ (number of all subsets).

**Stirling's approximation** — turn factorials into something differentiable/analyzable:
$$n! \;\sim\; \sqrt{2\pi n}\,\Big(\frac{n}{e}\Big)^{n}.$$
Very handy for **algorithm-complexity analysis** over combinatorial quantities (e.g. showing C(2n,n) ≈ 4ⁿ/√(πn)) and for asymptotics of the distributions in L07–L08.

---

## 11. Summary and Cross-Wire Moments

### 11.1 Key takeaways

- Two questions — **order?** and **repeats?** — plus "all n vs choose k" select one of **six** counting formulas (§7).
- **Variation** = ordered (tuples); **Combination** = unordered (sets, = variation ÷ k!). With replacement: nᵏ (ordered) / C(n+k−1,k) (unordered, stars-and-bars).
- **Multinomial** n!/(k₁!···kₛ!) = permutations with indistinguishable groups (Skat, anagrams).
- Combinatorics feeds **Laplace probability**: P(A) = |A|/|Ω|, both counted with these formulas.
- **Hypergeometric** P = C(n₁,k₁)C(n−n₁,k−k₁)/C(n,k) is the draw-without-replacement success count → L07.

### 11.2 Cross-wires

1. **L04 → L05:** L04's Laplace definition and birthday paradox *used* counting; L05 supplies the formulas. Same **Block N2** exam cluster (probability & counting).
2. **L05 → L07 (Discrete Distributions):** the **binomial coefficient** powers the **Binomial** distribution (draws *with* replacement / independent trials); §9's **hypergeometric** is the *without-replacement* twin, formalized in L07 with mean/variance.
3. **L05 multinomial ↔ L04 NB / L14:** counting arrangements underlies multinomial Naïve Bayes (word-count models, L14).
4. **L05 Stirling → L06/L08 asymptotics + algorithm complexity:** factorial asymptotics recur in CLT-style approximations and in Algo-2 running-time analysis.

### 11.3 What's next (beyond this batch)

- **L06 (Random Variables):** RVs, E[X], Var, Chebyshev, LLN — the probability half proper. Its deep guide already exists: **`SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md`** (Sessions 1–5 cover L06–L10). Per the module plan, **L06–L10 use that deep plan as their unit layer** rather than separate per-lecture units.

---

*Document version 1.0 — KW 28 (Jul 2026). Verified: sprint 8P3=336; C(49,5)=1,906,884; C(49,6)=13,983,816; Lotto-5 ≈ 1 in 54,201; Gummibärchen C(6,3)=20; Skat 32!/(10!³·2!)=2,753,294,408,504,640.*
*Supports Block N2. SaD steps remain F.* in Chat1.*
