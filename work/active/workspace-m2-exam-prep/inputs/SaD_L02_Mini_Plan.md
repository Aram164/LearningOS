# SaD Lecture 02 — Mini Learning Plan (Basic Concepts)

> **📌 Supports Block N1 (descriptive).** SaD steps stay **F.*** in Chat1 — log completions in `SESSION-LOG.md` + tick SEMESTER-STATUS §3. Second per-lecture SaD unit (3-file variant, no Mock Exam).

Sequenced path for L02: **concept → video → book → practice**. Practice lives in `SaD_L02_Exercise_Bank.md`; reference is `SaD_L02_Ultimate_Reference.md` (same folder).

**Primary course material:** `Lecture-slides/02_basics.pdf` (39 slides) + SaD sheets **UE1/UE2** (`Exercise-slides/Blatt1.pdf`, `blatt-02.pdf`). Book cites: **Teschl & Teschl** (official) / **Fahrmeir Ch 2** (notation-matched) / **OpenIntro Ch 2** (gentle) — pick one per step. Budget ~3 h; this closes the descriptive cluster with L01.

---

## Step 1 — Statistics types + core vocabulary  (~30 min)

Descriptive vs inferential vs exploratory; population/sample/instance/feature; why we sample.

- 🎥 **Kurzes Tutorium Statistik (Bärtl, DE)** — Grundbegriffe (Grundgesamtheit/Stichprobe/Merkmal).
- 📖 **Fahrmeir Ch 2 §intro** *or* **OpenIntro Ch 1.2–1.3** (population/sample, sampling).
- 📝 Reference §1–§2.
- ✍️ No drill — just fix the vocabulary; it underpins everything.

## Step 2 — Scale types (Skalenniveaus)  (~30 min)

Nominal / ordinal / discrete / continuous; qualitative vs quantitative; discretization. **High exam value — the "classify each feature" task.**

- 🎥 **KTS / jbstatistics — "Types of data / levels of measurement."**
- 📖 **Fahrmeir Ch 2** (Merkmalstypen) or OpenIntro Ch 1.2.
- 📝 Reference §3.
- ✍️ Exercise Bank **E2–E3** (classify + which measures are legal).

## Step 3 — Frequencies, histograms, Simpson's paradox  (~40 min)

Absolute/relative frequency; binning (equi-width vs equi-depth); why rates don't add.

- 🎥 **jbstatistics — frequency distributions / histograms**; any **Simpson's paradox** explainer (Minute Physics).
- 📖 OpenIntro Ch 2.1 (distributions/histograms).
- 📝 Reference §4–§5.
- ✍️ Exercise Bank **E7** (Simpson by hand).

## Step 4 — Location: mean, median, mode, quantiles, boxplots  (~45 min)

Formal definitions + properties (robustness, ordinal/nominal legality); quartiles, IQR, boxplot, violin.

- 🎥 ⭐ **jbstatistics — mean/median/mode** + **"Boxplots, Clearly Explained" (StatQuest)**.
- 📖 **Fahrmeir Ch 2** (Lagemaße, Quantile) or OpenIntro Ch 2.1.
- 📝 Reference §6–§7.
- ✍️ Exercise Bank **E4** (quartiles/boxplot) + **E6** (robustness).

## Step 5 — Dispersion + the n vs n−1 divisor  (~45 min)

Range, MAD, variance, SD, variance coefficient; **the ÷(n−1) vs ÷n distinction** (Bessel) — L02's slide inconsistency.

- 🎥 ⭐ **StatQuest — "Population vs Sample Variance"** (settles n vs n−1) + jbstatistics variance/SD.
- 📖 **Fahrmeir Ch 2** (Streumaße); the *why n−1* is completed in **L09** — don't chase it now.
- 📝 Reference §8–§9.
- ✍️ Exercise Bank **E1** (full pass) + **E5** (both divisors).

## Step 6 — Mind the sample  (~20 min, skim)

Sampling bias, stratified sampling, confounders; the mammal-size and St. Louis case studies; "models."

- 📝 Reference §10 (+ the two case studies).
- ✍️ Exercise Bank **E8** (spot the bias). No video needed.

## Step 7 — Practice & self-test  (→ exercise bank)

1. **UE1/UE2** → collect walked-through solutions in the Übung.
2. **E1–E8** → keys in the bank.
3. **FAU descriptive block** (median/quartiles/range/skewness) timed ~25 min → self-grade with the Lösung.

---

### Suggested schedule (~3 h)

| Session | Steps | Output |
|---|---|---|
| 1 | Steps 1–3 | vocabulary + scale types + frequencies solid; E2/E3/E7 |
| 2 | Steps 4–5 | location + dispersion + divisor cold; E1/E4/E5/E6 |
| 3 | Steps 6–7 | bias skimmed; UE + FAU descriptive timed |

Next unit: **L03 (Correlation & Regression)** — but note L03's authoritative doc is the **Regression Bridge** (`Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`); the L03 unit will point there rather than duplicate.
