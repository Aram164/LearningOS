---
id: note-sad-l01-exercise-bank
type: note
title: "SaD Lecture 01 — Exercise Bank (Descriptive Stats · Confusion Matrix · Bayes)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-descriptive-statistics, concept-classification-metrics]
sources: [source-sad-ss26-lectures, source-fau-klausur-ws1415]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect01 introduction/SaD_L01_Exercise_Bank.md` (legacy tree).

# SaD Lecture 01 — Exercise Bank (Descriptive Stats · Confusion Matrix · Bayes)

All practice for L01 in one place: descriptive measures (mean/median/mode, robustness), the confusion matrix (precision/recall/specificity/sensitivity), and Bayes-by-hand. Every item has a solution to self-grade against. Reference for any gap: `SaD_L01_Ultimate_Reference.md` (same folder).

*Per user's build request this unit has **no Mock Exam** — the timed self-test rows below stand in for it. Focus L01 practice on Klausur clusters **N1** (descriptive) and **N2** (probability/Bayes).*

---

## 1. Local material (in your repo)

| File / path | What it is | Use |
|---|---|---|
| `SaD_L01_Ultimate_Reference.md` | Full topic reference (slide-cited) | read / recall source |
| `SaD/SaD-2025/UE1.pdf` + `Exercise-slides/Blatt1.pdf` | The **SaD exercise sheet 1** (descriptive stats) | ⭐ solve first — matches course notation exactly |
| `SaD/Books/Arbeitsbuch Statistik.pdf` — **Ch 2** | Fahrmeir *Arbeitsbuch*: worked descriptive problems **with solutions** | volume drill for mean/median/mode/quantiles |
| `SaD/Books/Modern_intro_probability_statistics_Dekking05.pdf` | Dekking — ~300 exercises, short answers in the back | conditional-probability / Bayes drills (Ch 3) |
| `SaD/Klausuren-extern/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf` | ⭐ Two full German Klausuren, fully solved | the **4-Feldertafel + Bayes** task and descriptive tasks = L01 in exam format |
| `SaD/Klausuren-extern/` (Köln, Regensburg-Löh, HS-Harz, Leuphana) | Four more solved German exams | extra descriptive + Bayes items |

> ⚠️ The SaD exercise sheets live in `SaD/SaD-2025/UE*.pdf` and `SaD/Exercise-slides/` (the top-level `execise slides/` is empty). UE1 is the descriptive-stats sheet; do it closed-book, then check in the exercise session (collect the walked-through solution — Open Loop #5).

---

## 2. Warm-up drills (by hand, ~30 min) — build from the reference

Solutions in the collapsible keys. Do them before looking.

**D1 — the three centers.** For `4 4 5 6 6 6 9 10 12`, compute mean, median, mode.
<details><summary>answer</summary> n = 9, sum = 62 → mean = 6.89; sorted middle (5th) = 6 → median = 6; most frequent = 6 → mode = 6.</details>

**D2 — even n median.** For `3 7 7 8 10 14`, compute the median.
<details><summary>answer</summary> n = 6 → average of 3rd & 4th = (7+8)/2 = 7.5.</details>

**D3 — robustness.** Take D1's data and change the 12 to 120. Which of mean/median/mode changes, and to what?
<details><summary>answer</summary> mean jumps 6.89 → (62−12+120)/9 = 18.9; median and mode stay 6. Point: mean not robust, median/mode robust (Reference §3).</details>

**D4 — reproduce the lecture.** From the 20-student list (Reference §2), verify mean = 9.1, median = 8, mode = 7; then trim top/bottom-1 and confirm mean = 8.9, median = 8, mode = 7.
<details><summary>answer</summary> sum 182/20 = 9.1; sorted 10th=11th=8 → 8; 7 occurs 5× → 7. Trim drop 5 & 17: 160/18 = 8.89; median 8; mode 7.</details>

**D5 — build the confusion matrix.** A spam filter is tested on 1,000 emails: 200 are truly spam. It flags 250 emails; of those, 180 are truly spam. Fill TP/FP/FN/TN and compute precision, recall, specificity, accuracy.
<details><summary>answer</summary> TP = 180, FP = 250−180 = 70, FN = 200−180 = 20, TN = 800−70 = 730. precision = 180/250 = 0.72; recall = 180/200 = 0.90; specificity = 730/800 = 0.9125; accuracy = (180+730)/1000 = 0.91.</details>

**D6 — Bayes by hand (fresh numbers).** A disease has prevalence 1%. A test is 95% sensitive and 90% specific (i.e. false-positive rate 10%). You test positive — probability you're ill? Do it *both* ways: (a) count out of 10,000; (b) Bayes formula.
<details><summary>answer</summary> (a) 10,000 → 100 ill, 9,900 healthy; TP = 95, FP = 0.10·9,900 = 990; P(ill|pos) = 95/(95+990) = 95/1085 ≈ 0.0876 ≈ 8.8%. (b) (0.95·0.01)/(0.95·0.01 + 0.10·0.99) = 0.0095/0.1085 ≈ 0.088. Same. Base-rate neglect again — feels much higher than it is.</details>

**D7 — precision = posterior.** In the L01 medical example, show precision (TP/(TP+FP)) equals the Bayes p(ill|pos) numerically, and say which given quantity recall equals.
<details><summary>answer</summary> precision = 1,980/11,780 = 0.168 = p(ill|pos). recall = 1,980/2,000 = 0.99 = the given sensitivity p(pos|ill). (Reference §7.2.)</details>

---

## 3. Exam-format practice (the real thing)

### ⭐ FAU Erlangen WS14/15 — `SaD/Klausuren-extern/FAU-…_mit-Loesungen.pdf`
Two complete exams, fully solved. For L01 do the **descriptive** items (median/quartiles/Spannweite/skewness) and the **4-Feldertafel + Bayes** item. This is the single closest match to how L01 content appears on a German Klausur. Do closed-book, self-grade with the printed Lösung.

### Dekking Ch 3 (Conditional probability) — `SaD/Books/Modern_intro_…Dekking05.pdf`
Work the conditional-probability / Bayes exercises; short answers in the back. Good volume for the "flip the conditional" reflex (Reference §8).

### Fahrmeir *Arbeitsbuch* Ch 2 — `SaD/Books/Arbeitsbuch Statistik.pdf`
Descriptive-stat drills with full solutions, in course notation. Best for mean/median/mode/quantile fluency ahead of L02.

### The other four German Klausuren (`SaD/Klausuren-extern/`)
Köln, Regensburg-Löh, HS-Harz, Leuphana — each has descriptive and/or Bayes items with solutions. Use for extra reps only where you missed something above.

---

## 4. Concept self-checks (external, solution-backed)

- ⭐ **StatQuest — "The Confusion Matrix"** and **"Sensitivity and Specificity"** (YouTube, Josh Starmer). Watch, then re-derive precision/recall/specificity for D5 and the L01 example without pausing. The crosswalk names these as the L01 🎥 primary.
- **StatQuest — "Naive Bayes, Clearly Explained"** — optional forward-link; confirms the precision↔posterior idea before L04/L14.
- **OpenIntro Statistics Ch 3** (local, `SaD/Books/2019.openintro.statistics.pdf`) — end-of-section exercises on conditional probability & Bayes with a solutions appendix; the gentle tree-diagram version of §8.

---

## 5. Suggested sequence (~2.5–3 h)

1. **D1–D4** (descriptive + robustness) closed-book → check keys.
2. **UE1 / Blatt1** (the SaD sheet) → collect the walked-through solution in the Übung.
3. **D5–D7** (confusion matrix + precision/recall + the posterior bridge) → check keys.
4. **D6 + FAU 4-Feldertafel/Bayes item** (both-ways Bayes) → self-grade with FAU Lösung.
5. Thin spots only: Arbeitsbuch Ch 2 (descriptive volume) or Dekking Ch 3 (Bayes volume).

Anything you miss → reread the cited § in `SaD_L01_Ultimate_Reference.md`.

---

*No HU SaD Altklausuren are public (Moodle/Fachschaft only — see `LEARNING-RESOURCES.md` §6). Everything above is the SaD exercise sheets + solved external German Klausuren + matched concept material, not HU past papers. Numerics in all keys verified.*
