# SaD Lecture 04 — Mini Learning Plan (Probability & Naïve Bayes)

> **📌 Supports Block N2 (probability & counting).** SaD steps stay **F.*** in Chat1 — log completions in `SESSION-LOG.md` + tick SEMESTER-STATUS §3. Fourth per-lecture SaD unit (3-file variant, no Mock Exam).

Sequenced path for L04: **concept → video → book → practice**. Practice in `SaD_L04_Exercise_Bank.md`; reference `SaD_L04_Ultimate_Reference.md` (same folder). This is a big lecture (59 slides) and a **heavy exam topic** — budget ~4 h. The two must-master exam skills: **4-Feldertafel + Bayes** and **Naïve Bayes by hand**.

**Book cites (gentle → rigorous):** OpenIntro Ch 3 🟢 (tree diagrams) · Tijms Ch 6 + Ch 8 🟢 (everyday Bayes) · Schaum's Ch 3–4 🧮 (drill) · Pitman Ch 1 (incl. 1.5 Bayes) 🟡 · Fahrmeir Ch 4 🟡🇩🇪 (exam notation) · Dekking Ch 2–3 🟡 · Ross Ch 2–3 🔴 · **Blitzstein Ch 1–2 🔴 (⭐ best *why* once it clicks)** · Kelleher Ch 6 (NB) · CS229 §4.2 (NB). *Full ladder + chapters: `SaD_Book-Difficulty-Map_L01-L15.md` → L04.* If Blitzstein feels hard, drop to OpenIntro/Tijms first.

---

## Step 1 — Event spaces, experiments, events  (~30 min)

Ω, random experiment, event vs outcome, set operations, secure/impossible/elementary/complement.

- 🎥 **Kurzes Tutorium Statistik (Bärtl, DE)** — Zufallsexperiment / Ereignisse / Mengenoperationen.
- 📖 **Blitzstein Ch 1** (sample spaces, naive definition) *or* Fahrmeir Ch 4.
- 📝 Reference §3.
- ✍️ No drill yet — fix the vocabulary.

## Step 2 — Probability, Laplace, Kolmogorov axioms  (~40 min)

Relative frequency → probability (frequentist limit); stationarity + small-n caution; Laplace experiments; the 3 axioms + complement/inclusion–exclusion corollaries.

- 🎥 **KTS / jbstatistics — "Probability basics / Laplace."**
- 📖 **Blitzstein Ch 1** (axioms, inclusion–exclusion) or Fahrmeir Ch 4.
- 📝 Reference §4–§5.
- ✍️ Exercise Bank **B1–B2** (inclusion–exclusion, Laplace counting).

## Step 3 — Counting & the complement (birthday paradox)  (~30 min)

Solve-the-complement technique; the birthday-paradox product (on-ramp to L05 combinatorics).

- 🎥 **Any "birthday paradox" explainer** (Vsauce/Numberphile).
- 📖 **Blitzstein Ch 1** (counting, sampling with/without replacement).
- 📝 Reference §6.
- ✍️ Exercise Bank **B9** (complement counting).

## Step 4 — Conditional probability & Bayes  (~1 h) ⭐ exam-critical

Definition + geometry; multiplication rule; total probability; **Bayes**; the medical-test worked example (note the slide-47 misprint: answer is 0.91, not 0.99).

- 🎥 ⭐ **3Blue1Brown — "The medical test paradox"** (https://www.youtube.com/watch?v=lG4VkPoG3ko) + **"Bayes theorem, geometry of changing beliefs"** (https://www.youtube.com/watch?v=HZGCoVF3YvM).
- 📖 ⭐ **Blitzstein Ch 2** (§2.1–2.3 conditioning + Bayes + total probability; §2.8 pitfalls) — the best treatment in print · gentle: OpenIntro Ch 3.
- 📝 Reference §7.
- ✍️ Exercise Bank **B3** (table) + **B5** (Bayes both ways) + the FAU 4-Feldertafel item.

## Step 5 — Independence & conditional independence  (~30 min)

The three equivalent independence conditions; conditional independence; the two "neither implies the other" counterexamples.

- 🎥 **StatQuest / KTS — "Independent events / conditional independence."**
- 📖 **Blitzstein Ch 2** (independence).
- 📝 Reference §8.
- ✍️ Exercise Bank **B4** (independence check).

## Step 6 — Naïve Bayes classifier  (~50 min) ⭐ exam-critical

The naïve assumption → factored joint → argmax P(c)∏P(xⱼ|c); worked SPAM examples; the zero-frequency trap → smoothing (L14); complexity O(m·n); generative vs discriminative.

- 🎥 ⭐ **StatQuest — "Naive Bayes, Clearly Explained"** (+ "Gaussian Naive Bayes" for the L14 link).
- 📖 **CS229 §4.2** (Naïve Bayes, event models) + Kelleher Ch 6 (forward-link) · Fahrmeir Ch 4.
- 📝 Reference §9–§10.
- ✍️ Exercise Bank **B6** (NB by hand) + **B7** (zero-frequency + smoothing flip) + **B8** (text NB).

## Step 7 — Practice & self-test  (→ exercise bank)

1. **UE3** → collect walked-through solutions in the Übung.
2. **B1–B9** → keys in the bank.
3. ⭐ **FAU 4-Feldertafel/Bayes** (timed) + **Master Wiring §2-C** NB-with-smoothing self-test.
4. **Blitzstein strategic practice** (Ch 1 counting, Ch 2 conditioning) for volume.

---

### Suggested schedule (~4 h)

| Session | Steps | Output |
|---|---|---|
| 1 | Steps 1–3 | event spaces, axioms, Laplace, complement; B1/B2/B9 |
| 2 | Steps 4–5 | ⭐ Bayes + independence cold; B3/B4/B5 + FAU Bayes |
| 3 | Step 6–7 | ⭐ Naïve Bayes + smoothing; B6/B7/B8 + Wiring §2-C |

Next unit: **L05 (Combinatorics)** — permutations, variations, combinations: the counting tools for |A| and |Ω| that L04's Laplace/birthday problems leaned on. Sources: Blitzstein Ch 1, Fahrmeir Ch 4.
