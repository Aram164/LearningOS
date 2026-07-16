---
id: note-sad-l04-exercise-bank
type: note
title: "SaD Lecture 04 — Exercise Bank (Probability & Naïve Bayes)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-probability, concept-conditional-probability, concept-bayes-theorem, concept-naive-bayes, concept-laplace-smoothing]
sources: [source-sad-ss26-lectures, source-sad-uebungen, source-mit-1805]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect04 probability/SaD_L04_Exercise_Bank.md` (legacy tree).

# SaD Lecture 04 — Exercise Bank (Probability & Naïve Bayes)

Practice for L04: axioms & set-probability, Laplace counting, conditional probability, independence, Bayes, and Naïve Bayes by hand (including the zero-frequency/smoothing trap). Self-grading keys throughout. Gaps → `SaD_L04_Ultimate_Reference.md` (same folder).

> 3-file unit — **no Mock Exam** (per build request). Feeds Klausur cluster **N2 (probability & counting)**. This is a heavy exam topic — **4-Feldertafel + Bayes** and **Naïve Bayes by hand** are near-certain exam tasks.

---

## 1. Local material (in your repo)

| File / path | What it is | Use |
|---|---|---|
| `SaD_L04_Ultimate_Reference.md` | Full topic reference (slide-cited) | read / recall source |
| `SaD/SaD-2025/UE3.pdf` + `Exercise-slides/Übung-3.pdf` | SaD sheet 3 (probability half) | ⭐ solve first — course notation |
| **Blitzstein & Hwang Ch 1–2** (`SaD/Books/Introduction to Probability…`) | the best conditioning/Bayes intuition in print (story proofs) + strategic-practice problems | ⭐ depth + volume |
| `SaD/Books/Modern_intro_…Dekking05.pdf` — Ch 3 | ~conditional-probability/Bayes exercises, answers in back | volume |
| `SaD/Klausuren-extern/FAU-…_mit-Loesungen.pdf` | ⭐ the **4-Feldertafel + Bayes** item, fully solved | exam-format Bayes |
| `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` §2-C | **NB-with-smoothing by-hand self-test** (4-feature table) ⭐ | the L14 forward-link drill |

---

## 2. Warm-up drills (by hand)

**B1 — axioms / inclusion–exclusion.** In a group, P(coffee)=0.6, P(tea)=0.3, P(both)=0.2. Find P(coffee or tea) and P(neither).
<details><summary>answer</summary> P(A∪B)=0.6+0.3−0.2=0.7; P(neither)=1−0.7=0.3. (Inclusion–exclusion + complement.)</details>

**B2 — Laplace counting.** One card from a 52-card deck. P(King)? P(Heart)? P(King or Heart)? Are "King" and "Heart" independent?
<details><summary>answer</summary> P(K)=4/52=1/13; P(♥)=13/52=1/4; P(K∪♥)=4/52+13/52−1/52=16/52=4/13. Independent? P(K∩♥)=1/52 = (1/13)(1/4) ✓ → **yes, independent**.</details>

**B3 — conditional probability from a table.** 100 people: 40 smoke; of smokers 20 have a cough, of non-smokers 12 have a cough. Find P(cough | smoker), P(smoker | cough).
<details><summary>answer</summary> P(cough|smoker)=20/40=0.5. Total cough=20+12=32 → P(smoker|cough)=20/32=0.625. (Note the flip — that's Bayes.)</details>

**B4 — independence check.** Roll two dice. A="first is even", B="sum is 7". Independent?
<details><summary>answer</summary> P(A)=1/2, P(B)=6/36=1/6, P(A∩B): even-first sums-to-7 pairs = (2,5)(4,3)(6,1) = 3/36=1/12. Compare P(A)P(B)=1/12. Equal → **independent**.</details>

**B5 — Bayes by hand.** Disease prevalence 5%; test sensitivity 90%, specificity 80% (so FPR 20%). You test positive — P(disease)? Do it via the formula and via a 10,000-person table.
<details><summary>answer</summary> Formula: (0.9·0.05)/(0.9·0.05+0.20·0.95)=0.045/0.235=**0.1915 ≈ 19%**. Table of 10,000: 500 ill → 450 TP; 9,500 well → 1,900 FP; P=450/(450+1900)=450/2350=0.1915. Same. Base-rate lesson again.</details>

**B6 — Naïve Bayes by hand.** Using the L04 SPAM table (priors P(spam)=3/8, P(ham)=5/8), classify **instance 11 = ⟨G, Y, N, Y⟩** (lang G, image Y, source N, attach Y).
<details><summary>answer</summary> spam ∝ (2/3)(1/3)(3/3)(3/3)(3/8)=**0.083**; ham ∝ (2/5)(3/5)(2/5)(3/5)(5/8)=**0.036** → **Spam**. (Unlike instances 9/10, here nothing zeroes out and spam wins clearly.)</details>

**B7 — the zero-frequency trap + smoothing.** Instance 9 = ⟨G,N,N,N⟩ gave spam ∝ 0 (attach=N never seen in spam) → classified Ham. Recompute **with add-one (Laplace) smoothing**, k=2 values per feature: P(xⱼ|c) = (count+1)/(N_c+2).
<details><summary>answer</summary> spam ∝ (3/5)(3/5)(4/5)(1/5)(3/8)=**0.0216**; ham ∝ (3/7)⁴(5/8)=**0.0211** → **Spam** — the decision *flips*, because smoothing removes the artificial 0. This is exactly why L14 introduces smoothing. (Numbers verified.)</details>

**B8 — Bag-of-Words text NB.** Train: "gratis geld" (Spam), "geld gewinnen" (Spam), "meeting morgen" (Ham), "morgen bericht" (Ham). Classify "geld morgen" (presence BoW). Priors P(spam)=P(ham)=1/2.
<details><summary>answer</summary> spam ∝ P(geld|sp)·P(morgen|sp)·P(sp) = (2/2)·(0/2)·(1/2)=0; ham ∝ (0/2)·(2/2)·(1/2)=0 → **both 0** → tie/undefined ⇒ must **smooth**. With add-one (vocab size V=6): spam ∝ (3/8)(1/8)(1/2)=0.0234; ham ∝ (1/8)(3/8)(1/2)=0.0234 → genuinely tied here (symmetric data). Lesson: unseen words zero everything; smoothing is mandatory for text.</details>

**B9 — the complement trick.** In a class of 25, P(at least two share a birthday)? Set up the product (no need to fully evaluate).
<details><summary>answer</summary> 1 − (365/365)(364/365)…(341/365) = 1 − 365!/((340!)·365²⁵) ≈ **0.569** (56.9%). Compute via the complement, never by enumerating collisions. (For n=32 it's 75.3%, slide 33.)</details>

---

## 3. Exam-format practice (timed, self-graded)

- ⭐ **FAU Erlangen WS14/15** — the **4-Feldertafel + Bayes** item + the independence check, fully solved. ~25 min.
- ⭐ **Master Wiring §2-C** — Naïve Bayes with smoothing by hand on a 4-feature table (the L14 target, but great L04 practice now).
- **UE3** — the SaD probability sheet; collect walked-through solutions in the Übung.
- **Blitzstein Strategic Practice** (Ch 1 counting, Ch 2 conditioning/Bayes) — free official problem sets with full solutions (see `LEARNING-RESOURCES.md` §6 / Stat 110).

---

## 4. Concept self-checks (external, solution-backed)

- ⭐ **3Blue1Brown — "The medical test paradox"** (https://www.youtube.com/watch?v=lG4VkPoG3ko) + **"Bayes theorem, geometry of changing beliefs"** (https://www.youtube.com/watch?v=HZGCoVF3YvM) — the intuition for §7.
- ⭐ **StatQuest — "Naive Bayes, Clearly Explained"** + **"Gaussian Naive Bayes"** — §9 + the L14 forward-link.
- **Blitzstein Ch 1–2** (local) — story proofs; the *why* behind every formula here.
- **OpenIntro Ch 3** (local) — tree diagrams for conditional probability/Bayes.

---

## 5. Suggested sequence (~4 h — this is a big lecture)

1. **B1–B2** (axioms, Laplace counting) — foundations.
2. **B3–B4** (conditional probability + independence from tables).
3. ⭐ **B5** (Bayes both ways) + the FAU 4-Feldertafel item — the exam-classic.
4. ⭐ **B6–B7** (Naïve Bayes by hand + the smoothing flip) — the other exam-classic.
5. **B8–B9** (text NB + complement counting).
6. Master Wiring §2-C self-test (timed) → then Blitzstein strategic practice for volume.

Anything you miss → reread the cited § in `SaD_L04_Ultimate_Reference.md`.

---

*No HU SaD Altklausuren are public (Moodle/Fachschaft only). Above = SaD sheet + Blitzstein/Dekking + solved FAU Klausur + Wiring self-test. All keys verified numerically.*
