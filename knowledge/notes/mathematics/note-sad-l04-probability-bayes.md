---
id: note-sad-l04-probability-bayes
type: note
title: "SaD Lecture 04 — Ultimate Reference: Probability Theory & the Naïve Bayes Classifier"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-probability, concept-conditional-probability, concept-bayes-theorem, concept-naive-bayes, concept-laplace-smoothing]
sources: [source-sad-ss26-lectures, source-fahrmeir-statistik, source-blitzstein-hwang, source-openintro-statistics]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect04 probability/SaD_L04_Ultimate_Reference.md` (legacy tree).

# SaD Lecture 04 — Ultimate Reference: Probability Theory & the Naïve Bayes Classifier

*Synthesized from: SaD L04 (Leser, HU SoSe 2026) `Lecture-slides/04_probability.pdf` (59 slides) + Blitzstein Ch 1–2 (the "why" layer, story proofs) + Fahrmeir Ch 4 + CS229 §4.2 (Naïve Bayes). The formal home of L01's medical-test example.*
*Created: KW 28 (Jul 2026) — fourth per-lecture SaD unit (3-file variant, no Mock Exam).*

> **⚠️ Slide-47 misprint (verified):** the worked Bayes example ("99% accurate test, 0.1% prevalence, P(healthy | positive)?") prints **~0.99**, but the correct value is **≈ 0.91** (equivalently P(ill | pos) ≈ **9%**). See §7.3 — this is the intended "rare-disease" punchline; 0.99 would break it. Double-check the slide, but the math is 0.91.

---

## Table of Contents

1. [The Framing Experiment (why we need this)](#1-the-framing-experiment)
2. [The SPAM Problem & the "accuracy" measure](#2-the-spam-problem)
3. [Event Spaces, Experiments, Events](#3-event-spaces-experiments-events)
4. [Relative Frequency vs Probability; Laplace](#4-relative-frequency-vs-probability-laplace)
5. [Kolmogorov Axioms & Corollaries](#5-kolmogorov-axioms--corollaries)
6. [The Birthday Paradox (counting via the complement)](#6-the-birthday-paradox)
7. [Conditional Probability & Bayes](#7-conditional-probability--bayes)
8. [Independence & Conditional Independence](#8-independence--conditional-independence)
9. [The Naïve Bayes Classifier](#9-the-naïve-bayes-classifier)
10. [Naïve Bayes for Text (Bag-of-Words)](#10-naïve-bayes-for-text)
11. [Summary and Cross-Wire Moments](#11-summary-and-cross-wire-moments)

---

## 1. The Framing Experiment

**[Source: SaD L04, slides 4–7]**

Kahneman & Tversky's "Asian disease" framing experiment. A disease will kill 600,000; two options, **expected survivors = 200,000 in every version**. When option 1 is framed as *survivors* ("200,000 saved for sure" vs "⅓ chance all saved"), people pick the **sure** option. When the *same* option 1 is framed as *casualties* ("400,000 will die" vs "30% chance none die"), people flip to the **gamble**. Conclusion: humans are **irrational and inconsistent** about probability → we need a formal calculus, not intuition. (Same moral as L01's "be careful with intuition.")

---

## 2. The SPAM Problem

**[Source: SaD L04, slides 9–17]**

The running example, an 8-row gold-standard training set. Each mail has 4 **nominal binary** features — Language (G/E), hasImage, knownSource, hasAttachment — and a label **Spam?** (Yes/No). Three observations that motivate everything:

- The mapping features → label is **indeterministic**: ⟨G,y,n,y⟩ appears once as spam, once not.
- **Not all combinations appear** (⟨g,n,n,n⟩ is missing) — but missing ≠ impossible.
- We want to classify **new** instances (9, 10, 11) whose exact feature combo was never seen.

### The "accuracy" agreement measure (slides 13–16)

Pearson (L03) needs continuous features; here everything is nominal, so Leser defines an **agreement measure** (he calls it "accuracy"):
$$\text{acc}(x,y) = \frac{1}{n}\sum_{i=1}^{n}\mathbb{1}(x_i, y_i),\quad \mathbb{1}(a,b)=1 \text{ if } a=b \text{ else } 0.$$

Range [0,1]; symmetric; best for nominal features (it ignores *degree* of deviation, so it's poor for ordinal/continuous). Example agreements with spam: image↔spam **3/8**, source↔spam **2/8**, attach↔spam **5/8**. **But agreement is a crude, ad-hoc "correlation"** — no clean way to combine per-feature signals into a prediction (slide 17). That failure motivates **conditional probability → Naïve Bayes** (§7, §9). *(Note: this "accuracy" is the agreement statistic; the classifier-quality "accuracy" of L01/L11 is the same formula applied to prediction-vs-truth.)*

---

## 3. Event Spaces, Experiments, Events

**[Source: SaD L04, slides 19–21]**

- **Event space** Ω (*Ergebnisraum*): the set of all possible outcomes of a **random experiment** (a repeatable process producing one element of Ω). Must be a **set** (no duplicates; outcomes disjoint). Dice: Ω={1..6}; urn of colours; assembly line {OK, defect}.
- **Event** (*Ereignis*) A ⊆ Ω: any subset. Distinguish from **outcome** (*Ergebnis*, a single element). "Odd" on a die = {2,4,6}... (Leser's slide writes the odd event as {2,4,6} — read as "the event of interest," a subset of Ω).
- Special events: **secure** A=Ω; **impossible** A=∅; **elementary** |A|=1; **complement** Ā = Ω∖A.
- Events combine with set operations: **intersection** A∩B (both), **union** A∪B (either); ordinary set algebra applies (distributive laws etc.). Dice example: A={2,4,6}, B={4,5,6} → A∩B={4,6}, A∪B={2,4,5,6}.

---

## 4. Relative Frequency vs Probability; Laplace

**[Source: SaD L04, slides 22–24]**

Repeat experiment n times → multiset of results R. For event A:

- **Frequency** h(A) = |{r ∈ R : r ∈ A}|; **relative frequency** h_r(A) = h(A)/n.
- **Probability** (frequentist): $P(A) = \lim_{n\to\infty} h_r(A)$ — the long-run relative frequency.
- **Classical definition:** $P(A) = |A|/|\Omega|$ (only valid when all outcomes are equally likely).

**Stationarity assumption:** results are produced one-by-one and their frequencies **don't drift over time**. A strong assumption — ignoring trends (T-shirt sales in summer ≠ winter) is a classic source of bias. If E is stationary and n is "large enough," h_r(A) ≈ P(A). **Always distrust small n** (slide 23's table shows h_r wandering — 1/1, 1/2, … — while the true P(A)=1/6 is constant).

**Laplace experiment (slide 24):** a *finite* event space where **all outcomes are equally likely**, P(r)=1/|Ω|. Then P(A)=|A|/|Ω| directly. Dice, roulette (P(red)=18/37) are Laplace; "days with rain," "patients with pneumonia" are **not** (outcomes not equiprobable) — for those you must estimate from data.

---

## 5. Kolmogorov Axioms & Corollaries

**[Source: SaD L04, slides 25–26]**

True probabilities are usually unknown (how fair is *your* die?), but we can still compute with them axiomatically. For a finite Ω and a function P, the **Kolmogorov axioms**:

1. **P(Ω) = 1** (something happens),
2. **0 ≤ P(A) ≤ 1**, P(A) ∈ ℝ (non-negativity + bounded),
3. **P(A∪B) = P(A)+P(B)** if A∩B=∅ (additivity for disjoint events).

Anything satisfying these is a **probability space**. **Corollaries (derivable, slide 26):**

- P(∅) = 0.
- **Complement:** P(Ā) = 1 − P(A). ← the workhorse (see the birthday paradox).
- **Inclusion–exclusion:** P(A∪B) = P(A) + P(B) − P(A∩B) (subtract the double-counted overlap). Proved by splitting B into (B∖A) and (A∩B).

*Worked SPAM check (slide 28):* with A = "Language G ∧ attach Y" (|A|=3/8) and B = "…∧ spam Y" style events, P(A∪B) = P(A)+P(B)−P(A∩B) = (3+2−3)/8 — inclusion–exclusion on real counts.

---

## 6. The Birthday Paradox

**[Source: SaD L04, slides 29–33]** — *the counting/"use the complement" technique.*

32 students, 365 days: P(at least two share a birthday)? Model as an **urn with 365 balls, 32 draws with replacement**; A = "some ball drawn ≥ twice."

**Technique — solve the complement.** Enumerating A directly is hard; its complement Ā = "all 32 birthdays distinct" is easy:
$$P(A) = 1 - P(\bar A) = 1 - \prod_{i=1}^{32}\frac{365-i+1}{365} = 1 - \frac{365!}{(365-32)!\,365^{32}}.$$
The product: 1st person free (365/365), 2nd must differ (364/365), 3rd (363/365), … **Result: P(32) ≈ 75.33%** (verified) — far higher than intuition ("guess 5/20/30/50%"). The lesson: **when the event is a messy union, compute 1 − P(complement).** This is the combinatorics on-ramp to L05.

---

## 7. Conditional Probability & Bayes

**[Source: SaD L04, slides 35–47]** · intuition depth: Blitzstein Ch 2; and L01 §5/§8

### 7.1 Definition

$$P(B\mid A) = \frac{P(A\cap B)}{P(A)}$$

"The relative frequency of B **among the instances of A**" — restrict the world to A, ask what fraction is also B. Geometrically (slide 36): P(B|A) = overlap area / A's area. *SPAM examples:* P(L=G | spam) = 2/3, P(L=G | ham) = 2/5, P(I=Y | spam) = 1/3.

**Why the naïve "P(class | full feature vector)" fails (slides 38–39):** most feature combinations were never seen → the conditional is **undefined (0/0)**; and for rare combos, relative frequency ≠ true probability. This is exactly what Naïve Bayes fixes by factoring the joint.

### 7.2 Multiplication rule & total probability

- **Multiplication rule:** P(A)·P(B|A) = P(A∩B) = P(B)·P(A|B). (Both equal the joint.)
- **Law of total probability:** if E₁,…,Eₙ **partition** Ω (disjoint, union = Ω), then
$$P(A) = \sum_i P(A\cap E_i) = \sum_i P(E_i)\,P(A\mid E_i).$$

### 7.3 Bayes' theorem

$$\boxed{\,P(E_i\mid A) = \frac{P(A\mid E_i)\,P(E_i)}{P(A)} = \frac{P(A\mid E_i)\,P(E_i)}{\sum_j P(E_j)\,P(A\mid E_j)}\,}$$

The denominator is total probability — it **flips the conditional** from the direction you know (P(evidence | cause)) to the one you want (P(cause | evidence)). Same structure as L01 §8.

> **Worked example (slide 47) — with the misprint corrected.** Test 99% accurate both ways, prevalence P(ill)=0.001. Then P(pos|healthy)=0.01, and
> $$P(\text{healthy}\mid\text{pos}) = \frac{0.01\cdot 0.999}{0.99\cdot 0.001 + 0.01\cdot 0.999} = \frac{0.00999}{0.01098} \approx \mathbf{0.91}.$$
> So a positive test on a **rare** disease still leaves you **~91% likely healthy** (P(ill|pos) ≈ 9%). The deck prints ~0.99 — a slip; the pedagogical point *is* the 0.91. This is the L01 base-rate lesson, more extreme because the prior is smaller (0.1% vs 2%).

**Secretary/hiring problem (slides 48–50, optional):** interview-then-hire strategy — reject the first j candidates, then take the first one better than all of them. Using Bayes, the optimal cutoff for n=12 is **j=4**, and as n→∞, **j ≈ 0.37n** (the "1/e" secretary problem; Leser rounds to 0.4n). Illustrative of Bayes on a non-medical problem; not a core exam target.

---

## 8. Independence & Conditional Independence

**[Source: SaD L04, slides 43–45, 52–53]**

**Independence:** A and B are independent iff any one (⇒ all) of:
$$P(B\mid A)=P(B),\quad P(A\mid B)=P(A),\quad P(A\cap B)=P(A)\,P(B).$$
Intuition: knowing B tells you nothing about A. *Practically important* — we often *know* two things are causally unrelated (two dice rolls; a student's grade vs another's), which makes joint probabilities factor into a simple product.

**Conditional independence (slide 52):** A and B are conditionally independent given C iff
$$P(A,B\mid C) = P(A\mid C)\,P(B\mid C).$$

> **⚠️ Independence ≠ conditional independence (slide 53, know both directions):**
> - *Independent but not conditionally:* two fair coins A, B; C = "both same." A,B independent, but given C, knowing A **determines** B.
> - *Conditionally independent but not independent:* two coins in a bag (one biased), draw one then flip twice. Flips A,B are dependent (first heads → probably the biased coin → second likely heads), but **given** which coin C was drawn, they're independent.

This distinction is the entire foundation of Naïve Bayes' "naïve" assumption.

---

## 9. The Naïve Bayes Classifier

**[Source: SaD L04, slides 52–58]**

**Goal:** compute P(class | features) and pick the best class. By Bayes:
$$P(c\mid X_i) = \frac{P(X_i\mid c)\,P(c)}{P(X_i)}.$$
The joint P(X_i | c) = P(x₁,…,xₙ | c) is unestimable (unseen combos). **The naïve assumption:** all features are **conditionally independent given the class**, so the joint factors:
$$P(X_i\mid c) = \prod_{j=1}^{n} P(x_j\mid c).$$
Since the denominator P(X_i) is the same for every class, **drop it** and take the argmax:
$$\boxed{\,c^* = \arg\max_{c\in C}\; P(c)\prod_{j=1}^{n} P(x_j\mid c)\,}$$

Each factor is a simple per-feature relative frequency estimated from the training counts (the **prior** P(c) and the **likelihoods** P(x_j|c)).

### Worked examples (slides 55–57, verified) — priors P(spam)=3/8, P(ham)=5/8

**Instance 9 = ⟨G, N, N, N⟩:**
$$P(\text{spam}\mid\cdot) \propto \tfrac{2}{3}\cdot\tfrac{2}{3}\cdot\tfrac{3}{3}\cdot\underbrace{\tfrac{0}{3}}_{\text{attach=N never in spam}}\cdot\tfrac{3}{8} = \mathbf{0}$$
$$P(\text{ham}\mid\cdot) \propto \tfrac{2}{5}\cdot\tfrac{2}{5}\cdot\tfrac{2}{5}\cdot\tfrac{2}{5}\cdot\tfrac{5}{8} = 0.016 > 0 \;\Rightarrow\; \textbf{Ham}$$

**Instance 10 = ⟨E, Y, N, Y⟩:**
$$P(\text{spam}\mid\cdot) \propto \tfrac{1}{3}\cdot\tfrac{1}{3}\cdot\tfrac{3}{3}\cdot\tfrac{3}{3}\cdot\tfrac{3}{8} = 0.041,\qquad P(\text{ham}\mid\cdot) \propto \tfrac{3}{5}\cdot\tfrac{3}{5}\cdot\tfrac{2}{5}\cdot\tfrac{3}{5}\cdot\tfrac{5}{8} = 0.054 \;\Rightarrow\; \textbf{Ham}$$

> **The zero-frequency problem (instance 9).** One unseen feature-value-in-class (attach=N never occurred among spam) makes a factor 0 and **zeroes the whole product**, even if every other feature screamed "spam." Fix = **smoothing** (add a pseudo-count, e.g. Laplace/add-one) — SaD L14 / CS229 §4.2.1. Flagged here, solved there.

### Complexity (slide 58) — why it's "simple"

Training = counting relative frequencies. With n instances, c classes, m features: input O(m·n); parameters needed O(c·m); one scan to estimate them O(m·n); prediction O(c·m) multiplications + one max. **Total: O(m·n) time and space.** Very cheap.

---

## 10. Naïve Bayes for Text

**[Source: SaD L04, slides 59–63]**

**Bag-of-Words (BoW):** represent a text as a **set** of words (drop duplicates and order; here, ignore stop-words and case). Ω = "all words we know," each feature = presence of a word. *Worked (slide 61):* query "klicke viel geld" →
$$P(\text{ham}\mid\cdot)\propto \tfrac{0}{2}\cdot\tfrac{0}{2}\cdot\tfrac{1}{2}\cdot\tfrac{2}{5}=0,\qquad P(\text{spam}\mid\cdot)\propto \tfrac{1}{3}\cdot\tfrac{1}{3}\cdot\tfrac{2}{3}\cdot\tfrac{3}{5}=0.044 \;\Rightarrow\;\textbf{Spam}.$$

**Two practical issues (slide 62):**

- **Huge vocabulary + unseen words** → zeros everywhere → must **smooth** (later).
- **Numerical underflow:** multiplying many tiny probabilities → work in **log space**, turning the product into a sum:
$$c^* = \arg\max_{c}\Big(\log P(c) + \sum_i \log P(x_i\mid c)\Big).$$

**Wrap-up (slide 63):** Naïve Bayes is a **(log-)linear classifier** (like MLR / logistic) and a **generative** method — it models P(X|c) and P(c), then inverts via Bayes; estimating the smaller "class space" is easier/more robust. **Discriminative** methods (logistic regression, max-entropy) model P(c|X) directly with extra assumptions. NB is "not quite state-of-the-art" for text (semantics-free) but astonishingly strong, fast, and language-agnostic (~<10% accuracy gap).

---

## 11. Summary and Cross-Wire Moments

### 11.1 Key takeaways

- **Probability** = long-run relative frequency (frequentist) or |A|/|Ω| (Laplace, equiprobable only).
- **Kolmogorov axioms** + the two workhorse corollaries: complement P(Ā)=1−P(A) and inclusion–exclusion.
- **Complement trick** (birthday paradox): 1 − P(all-distinct) ≈ 75% for 32 people.
- **Bayes** flips P(evidence|cause) → P(cause|evidence) via total probability; slide-47 answer is **0.91** (not 0.99).
- **Naïve Bayes:** assume conditional independence given the class → c* = argmax P(c)∏P(xⱼ|c). Watch the **zero-frequency** trap → smoothing. O(m·n), generative, log-space for text.

### 11.2 Cross-wires

1. **L01 ↔ L04:** L01's medical-test (counting + Bayes) is the informal preview; L04 gives the axioms, total probability, and the general Bayes theorem. Same **Block N2** cluster.
2. **L04 → L05 (Combinatorics):** the birthday paradox's counting is exactly what L05 formalizes (permutations/variations/combinations for computing |A| and |Ω|).
3. **L04 → L14 (Probability-Based Learning):** L14 is "Naïve Bayes revisited" — **smoothing** (Laplace/add-one), **Gaussian NB** (continuous features), **multinomial NB** (word counts, not just presence). The zero-frequency fix promised here lands there. Depth: CS229 §4.2 + Kelleher Ch 6 + Wiring §2-C self-test.
4. **L04 accuracy measure ↔ L01/L11 evaluation:** the same agreement formula is the classifier "accuracy" metric.
5. **L04 NB is log-linear ↔ L03 MLR / L15 logistic:** all are (log-)linear scorers; generative (NB) vs discriminative (logistic) is the axis.
6. **L04 conditional probability ↔ L06+ (random variables):** conditioning generalizes to conditional distributions and expectations.

### 11.3 What's next

- **L05 (Combinatorics):** permutations, variations, combinations — the tools to *count* |A| and |Ω| for non-trivial Laplace/probability problems (and to finish the birthday-style arguments). Sources: Blitzstein Ch 1, Fahrmeir Ch 4.

---

*Document version 1.0 — KW 28 (Jul 2026). Verified numerically: Bayes slide-47 = 0.91 (deck's 0.99 is a misprint); NB instance 9 → Ham (spam 0, ham 0.016); instance 10 ⟨E,Y,N,Y⟩ → Ham (0.041 vs 0.054); text NB → Spam (0 vs 0.044); birthday P(32)=75.33%.*
*Supports Block N2. SaD steps remain F.* in Chat1.*
