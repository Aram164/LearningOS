---
id: note-sad-l05-exercise-bank
type: note
title: "SaD Lecture 05 — Exercise Bank (Combinatorics)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-combinatorics]
sources: [source-sad-ss26-lectures, source-sad-uebungen]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect05 combinatorics/SaD_L05_Exercise_Bank.md` (legacy tree).

# SaD Lecture 05 — Exercise Bank (Combinatorics)

Practice for L05: picking the right counting case, applying each of the six formulas, Laplace probability via counting, and the hypergeometric distribution. Self-grading keys throughout. Gaps → `SaD_L05_Ultimate_Reference.md` (same folder).

> 3-file unit — **no Mock Exam** (per build request). Feeds Klausur cluster **N2 (probability & counting)**. The exam skill here is **recognizing which of the six cases applies**, then plugging in — practice classification as much as arithmetic.

---

## 1. Local material (in your repo)

| File / path | What it is | Use |
|---|---|---|
| `SaD_L05_Ultimate_Reference.md` | Full topic reference + the decision grid | read / recall source |
| `SaD/SaD-2025/UE3.pdf` + `Exercise-slides/Übung-3.pdf` | SaD sheet 3 (counting half) | ⭐ solve first — course notation |
| **Blitzstein & Hwang Ch 1** (`SaD/Books/Introduction to Probability…`) | the clearest counting treatment, story proofs + strategic-practice problems | ⭐ depth + volume |
| `SaD/Books/Modern_intro_…Dekking05.pdf` — Ch 2 | combinatorial-probability exercises, answers in back | volume |
| `SaD/Klausuren-extern/FAU-…_mit-Loesungen.pdf` | solved German Klausur | counting + Binomial items |

---

## 2. Warm-up drills (by hand)

**C1 — classify the case (the key skill).** For each, name which of the six cases applies (order? repeats? all-n or choose-k): (a) rankings of 5 finishers; (b) a 4-digit PIN; (c) a 6-number lottery pick; (d) ways to split 3 identical cakes among 5 people; (e) anagrams of "OTTO".
<details><summary>answer</summary> (a) permutation of all distinct → 5!; (b) variation *with* replacement → 10⁴; (c) combination *without* replacement → C(49,6); (d) combination *with* replacement (stars & bars) → C(3+5−1,3)=C(7,3); (e) permutation with groups (O²T²) → 4!/(2!2!)=6.</details>

**C2 — multinomial (permutation with groups).** How many distinct arrangements of the letters in **MISSISSIPPI**?
<details><summary>answer</summary> 11 letters: M1, I4, S4, P2 → 11!/(1!·4!·4!·2!) = **34,650**.</details>

**C3 — variation without replacement.** A club of 10 elects a president, vice-president, and treasurer (distinct people, roles ordered). How many outcomes?
<details><summary>answer</summary> 10·9·8 = 10!/7! = **720**.</details>

**C4 — variation with replacement.** How many 3-letter strings over the 26-letter alphabet (repeats allowed)?
<details><summary>answer</summary> 26³ = **17,576**. (Each of 3 slots independently 26 options.)</details>

**C5 — combination without replacement.** From 10 people, how many 3-person committees (roles don't matter)?
<details><summary>answer</summary> C(10,3) = 10!/(3!7!) = **120**. (= C3's 720 divided by 3! = 6, the orderings that don't count.)</details>

**C6 — combination with replacement (stars & bars).** Distribute 10 identical candies among 4 children (a child may get 0)?
<details><summary>answer</summary> C(10+4−1, 10) = C(13, 10) = C(13,3) = **286**. (10 stars, 3 bars → choose positions of the 3 bars among 13.)</details>

**C7 — Laplace probability via counting.** Draw a 5-card poker hand from 52. P(exactly two Kings)?
<details><summary>answer</summary> hypergeometric: C(4,2)·C(48,3)/C(52,5) = 6·17,296/2,598,960 = **0.0399** (≈ 4%).</details>

**C8 — hypergeometric (quality control).** A batch of 20 has 4 defective. You sample 5 without replacement. (a) P(exactly 1 defective)? (b) P(none defective)?
<details><summary>answer</summary> (a) C(4,1)·C(16,4)/C(20,5) = 4·1,820/15,504 = **0.470**. (b) C(16,5)/C(20,5) = 4,368/15,504 = **0.282**.</details>

**C9 — Lotto payoff.** In 6-aus-49, P(exactly 5 correct)?
<details><summary>answer</summary> C(6,5)·C(43,1)/C(49,6) = 6·43/13,983,816 = 258/13,983,816 ≈ **1 in 54,201**. (Reference §9.)</details>

**C10 — the birthday connection.** Redo L04's seating from a counting view: r=4 people, n=12 months, all birthdays in distinct months? Give the count ratio.
<details><summary>answer</summary> P(all distinct) = [12·11·10·9]/12⁴ = (12!/8!)/12⁴ = 11,880/20,736 = **0.573**. So P(at least one shared month) ≈ 0.427. Variation-without-replacement / variation-with-replacement — the birthday structure (Reference §8, L04 §6).</details>

---

## 3. Exam-format practice (timed, self-graded)

- ⭐ **FAU Erlangen WS14/15** — the Binomial / counting items, fully solved.
- **UE3** (counting half) — the SaD sheet; collect walked-through solutions in the Übung.
- **Blitzstein Ch 1 Strategic Practice** — free official counting problem sets with full solutions (Stat 110; see `LEARNING-RESOURCES.md` §6).
- **Dekking Ch 2** — extra combinatorial-probability items with back-of-book answers.

---

## 4. Concept self-checks (external, solution-backed)

- ⭐ **jbstatistics — "Counting / Permutations and Combinations"** — short, exam-exact.
- **Stat 110 (Blitzstein) L1–L2** — the counting lectures (story-proof style); pick per gap.
- **3Blue1Brown — "Pascal's triangle / binomials"** (optional) for the C(n,k) identities (§10).
- **StatQuest — "The Hypergeometric Distribution"** (forward-link to L07) for §9.

---

## 5. Suggested sequence (~2.5–3 h)

1. ⭐ **C1** (classify the case) — do this until it's instant; it's the whole exam skill.
2. **C2–C6** — one drill per formula (multinomial, both variations, both combinations).
3. **C7–C9** (Laplace + hypergeometric) — the probability payoff.
4. **C10** (birthday connection back to L04).
5. **FAU counting items** timed → then Blitzstein Ch 1 strategic practice for volume.

Anything you miss → reread the cited § (esp. the §2 decision grid) in `SaD_L05_Ultimate_Reference.md`.

---

*No HU SaD Altklausuren are public (Moodle/Fachschaft only). Above = SaD sheet + Blitzstein/Dekking + solved FAU Klausur. All keys verified numerically.*
