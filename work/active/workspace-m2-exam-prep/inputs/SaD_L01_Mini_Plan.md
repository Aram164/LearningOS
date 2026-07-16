# SaD Lecture 01 — Mini Learning Plan (Introduction)

> **📌 Supports Block N1 (descriptive) + N2 (probability/Bayes).** SaD steps stay **F.*** in Chat1 — log completions in `SESSION-LOG.md` + tick SEMESTER-STATUS §3. This is the first per-lecture SaD unit (built on request; extends the "no-unit for 01–02" default in `SaD-Module-Overview.md`).

A sequenced path for L01, mapped to the crosswalk. Each step: **concept → video → book section → practice**. Practice lives in `SaD_L01_Exercise_Bank.md`; the topic reference is `SaD_L01_Ultimate_Reference.md` (same folder).

**Primary course material:** `Lecture-slides/01_introduction.pdf` (42 slides) + SaD exercise sheet **UE1 / `Exercise-slides/Blatt1.pdf`**. Everything below *supplements* those. Book cites: **Teschl & Teschl *Mathematik für Informatiker*** is the officially-named stats text (slide 40); **Fahrmeir / OpenIntro / Blitzstein** are the notation-matched / gentle / depth alternatives — pick per taste, don't read all.

> L01 is a light, motivational lecture. Budget ~3–4 h total; most of the payoff is in Steps 2–3 (metrics + Bayes), which recur on the exam. Descriptive detail is finished properly in L02.

---

## Step 1 — Describing data: mean, median, mode, robustness  (~45 min)

The three "centers", the histogram, and why the mean isn't robust to outliers.

- 🎥 **Kurzes Tutorium Statistik (Bärtl, DE)** — Lagemaße (Mittelwert/Median/Modus) + Streuung; German, same vocab as the Klausur. *(crosswalk L01–02 primary channel)*
- 🎥 alt: **Brandon Foltz — "Statistics 101: Measures of Central Tendency"** (slow, every step written out).
- 📖 **Teschl & Teschl** (descriptive-stats section) *or* **Fahrmeir Ch 2** (course notation) *or* **OpenIntro Ch 1–2** (gentle EN). One is enough.
- 📝 Reference §2–§3.
- ✍️ Practice: Exercise Bank **D1–D4** + skim **UE1**.

## Step 2 — The confusion matrix + precision/recall  (~45 min)

TP/FP/FN/TN; precision vs recall; specificity/sensitivity; why accuracy misleads on rare classes. **Exam-relevant.**

- 🎥 ⭐ **StatQuest — "The Confusion Matrix"** then **"Sensitivity and Specificity"** (Starmer) — the crosswalk L01 🎥 primary; short and exact.
- 📖 **Kroese §7.2 (p.253)** — the metrics, compactly (in the AML/ML shelf) · or OpenIntro's classification-metrics section.
- 📝 Reference §6–§7 — **read the §7.1 slide-wording decode** (Leser's "Type-1/Type-2 error" labels for precision/recall are a loose mnemonic, *not* the standard Type I/II from testing — don't write them as definitions).
- ✍️ Practice: Exercise Bank **D5** (build a matrix from counts) + **D7** (precision = posterior).

## Step 3 — Base-rate neglect & Bayes (counting + formula)  (~1 h)

The medical-test paradox two ways: the 100,000-person table, then Bayes' theorem; the precision↔posterior bridge. **The heart of the lecture and exam-relevant.**

- 🎥 ⭐ **3Blue1Brown — "The medical test paradox, and redesigning Bayes' rule"** (https://www.youtube.com/watch?v=lG4VkPoG3ko) — literally slide 23–24's example.
- 🎥 ⭐ **3Blue1Brown — "Bayes theorem, the geometry of changing beliefs"** (https://www.youtube.com/watch?v=HZGCoVF3YvM) — the representative-population / areas intuition; core message: *don't memorize, draw the diagram.*
- 📖 **Blitzstein Ch 2** (§2.1 thinking conditionally, §2.2 definition & intuition, §2.3 Bayes + total probability, §2.7 conditioning as a tool, §2.8 pitfalls) — local, the best written intuition · gentle alt: **OpenIntro Ch 3** (tree diagrams).
- 📝 Reference §5 (counting) + §8 (formula derivation + recognition trigger).
- ✍️ Practice: Exercise Bank **D6** (Bayes both ways, fresh numbers) + the **FAU 4-Feldertafel/Bayes** item.
- ➡️ Forward-link: this is the informal version of **L04** (axioms → conditional P → Bayes → Naïve Bayes). Don't go deep now — L04 owns it.

## Step 4 — Context: the "same distribution?" question + case study  (~20 min, skim)

Why one sample isn't enough; a glimpse of the ML half. Non-examinable — read once for the map.

- 📝 Reference §4 (samples → distributions → the seeds of estimation/testing) + §9 (oncology case study: PCA, Random Forest + 10-fold CV, Cox regression — all later lectures).
- No practice; just note which later lecture each named method belongs to.

## Step 5 — Practice & self-test  (→ exercise bank)

Closed-book, then self-grade. Details in `SaD_L01_Exercise_Bank.md`:

1. **UE1 / Blatt1** (descriptive) → collect walked-through solution in the Übung.
2. **D1–D7** warm-ups → keys in the bank.
3. **FAU Erlangen** descriptive + 4-Feldertafel/Bayes items (timed ~30 min) → self-grade with the printed Lösung.

---

### Suggested schedule (~3–4 h total)

| Session | Steps | Output |
|---|---|---|
| 1 | Steps 1–2 | mean/median/mode + confusion matrix solid; D1–D5 done |
| 2 | Step 3 | Bayes both ways cold; D6–D7 + FAU Bayes item self-graded |
| 3 | Steps 4–5 | context skimmed; UE1 + FAU descriptive timed |

Pull a supplement only where a slide feels thin — don't read every source linearly. Next unit: **L02 (Basic Concepts)** — population/sample, x̄, s², quantiles, boxplots.
