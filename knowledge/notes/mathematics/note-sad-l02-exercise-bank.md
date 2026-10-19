---
id: note-sad-l02-exercise-bank
type: note
title: "SaD L02 — Exercise Bank (Basic Concepts)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-descriptive-statistics, concept-variance]
sources: [source-sad-ss26-lectures, source-fahrmeir-arbeitsbuch]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect02 basics/SaD_L02_Exercise_Bank.md` (legacy tree). Feeds Klausur cluster N1 (descriptive); gaps route to `note-sad-l02-descriptive-basics`.

# SaD Lecture 02 — Exercise Bank (Basic Concepts)

Practice for L02: scale-type classification, frequencies/histograms, location (mean/median/mode/quantiles/boxplot), dispersion (range/MAD/variance/SD, both divisors), Simpson's paradox, and sampling-bias reasoning. Every drill has a self-grading key. Gaps → `SaD_L02_Ultimate_Reference.md` (same folder).

*3-file unit — **no Mock Exam** (per build request). The timed items in §3 stand in for it. L02 feeds Klausur cluster **N1 (descriptive)**.*

---

## 1. Local material (in your repo)

| File / path | What it is | Use |
|---|---|---|
| `SaD_L02_Ultimate_Reference.md` | Full topic reference (slide-cited) | read / recall source |
| `SaD/SaD-2025/UE1.pdf`, `UE2.pdf` + `Exercise-slides/` (`Blatt1`, `blatt-02`) | SaD exercise sheets 1–2 (descriptive + scale types) | ⭐ solve first — course notation |
| `SaD/Books/Arbeitsbuch Statistik.pdf` — **Ch 2** | Fahrmeir *Arbeitsbuch*: descriptive drills **with solutions** | ⭐ volume for mean/median/quantile/variance |
| `SaD/Klausuren-extern/FAU-…_mit-Loesungen.pdf` | Two solved German Klausuren | descriptive items (median/quartiles/Spannweite/skewness) in exam format |
| `SaD/Klausuren-extern/` (Köln, Regensburg, HS-Harz, Leuphana) | Four more solved exams | extra descriptive items |

---

## 2. Warm-up drills (by hand)

Solutions in the collapsibles — attempt first.

**E1 — location + dispersion, full pass.** For `4 8 6 5 3 9 7 7 10`: mean, median, mode, range, sample variance s² (÷(n−1)) and SD.
<details><summary>answer</summary> n=9, sum=59 → mean=6.556; sorted 3,4,5,6,7,7,8,9,10 → median=7 (5th); mode=7; range=10−3=7; s²=5.278, s=2.297. (Population ÷n: 4.691 / 2.166.)</details>

**E2 — scale types.** Classify: (a) blood type A/B/AB/0; (b) Amazon star rating 1–5; (c) body temperature °C; (d) number of siblings; (e) postal code.
<details><summary>answer</summary> (a) nominal; (b) ordinal; (c) continuous; (d) discrete; (e) nominal (it's a label, not a quantity — averaging postal codes is meaningless). Reflex: unordered→nominal, ordered categories→ordinal, counts→discrete, measured continuum→continuous.</details>

**E3 — which measures are legal?** For each of E2's features, say whether mean, median, and mode are meaningful.
<details><summary>answer</summary> nominal (a,e): mode only. ordinal (b): mode + median (+ quantiles); mean is dubious (common in practice but not strictly justified). continuous (c) & discrete (d): all three. Rule: mean needs quantitative; median needs at least ordinal; mode always works.</details>

**E4 — quartiles & boxplot.** For `2 4 4 4 5 5 7 9`: give min, Q0.25, median, Q0.75, max, IQR, and sketch the boxplot five-number summary.
<details><summary>answer</summary> min=2, max=9, median=(4+5)/2=4.5. Using linear interpolation: Q0.25=4, Q0.75=5.5 → IQR=1.5. (Different quantile conventions shift Q slightly — state which you use.) Box 4→5.5, median line at 4.5, whiskers to 2 and 9.</details>

**E5 — variance divisor.** For `2 4 4 4 5 5 7 9`, compute the variance both ways and say which is the "empirical/sample" variance.
<details><summary>answer</summary> mean=5. ÷n (population): Σ(xᵢ−5)²/8 = 32/8 = 4 → SD 2. ÷(n−1) (empirical/sample): 32/7 = 4.571 → SD 2.138. The **sample/empirical** variance is ÷(n−1) (Bessel, unbiased) — the course default (Reference §9). Note L02's slide 31 numbers used ÷n.</details>

**E6 — outlier robustness.** Take `20 21 19 20 18 22 20 21 19`; then replace the last 19 with 135. Report how mean and median change.
<details><summary>answer</summary> mean 20 → 32.9 (moves a lot); median 20 → 20 (unchanged). Mean not robust, median robust (Reference §6).</details>

**E7 — Simpson's paradox.** Two treatments for kidney stones. Treatment A: small stones 81/87 success (93%), large 192/263 (73%). Treatment B: small 234/270 (87%), large 55/80 (69%). Which is better per stone-size? Which looks better overall? Explain.
<details><summary>answer</summary> Per size, **A wins both** (93>87 small; 73>69 large). Overall: A = 273/350 = 78%; B = 289/350 = 83% → **B looks better overall**. Reversal because A was mostly given the *hard* large-stone cases and B the easy small ones; unequal group sizes make the pooled rates non-additive. Classic Simpson (Reference §5). [Real Charig et al. 1986 data.]</details>

**E8 — spot the sampling bias.** A university emails a "how stressed are you?" survey; 8% respond. The results look mild. Why might they mislead?
<details><summary>answer</summary> Self-selection / non-response bias: the most stressed students are least likely to have time/energy to answer, so respondents aren't representative. Fix: random targeted sampling + follow-up, or stratify by known confounders (year, program). Reference §10.</details>

---

## 3. Exam-format practice (timed, self-graded)

- ⭐ **FAU Erlangen WS14/15** (`SaD/Klausuren-extern/FAU-…`) — the descriptive block: median, quartiles, Spannweite (range), skewness, plus a scale-type/frequency item. ~25 min, self-grade with the printed Lösung.
- **Fahrmeir *Arbeitsbuch* Ch 2** — a full set of descriptive problems with worked solutions; best fluency builder before L03.
- **UE1 / UE2** — the SaD sheets; collect walked-through solutions in the Übung (Open Loop #5).
- The other four German Klausuren — extra descriptive items where you missed something.

---

## 4. Concept self-checks (external, solution-backed)

- ⭐ **jbstatistics — descriptive-statistics playlist** (mean/median/mode, variance/SD, quartiles/boxplots) — short, calculation-exact; crosswalk L02 🎥 primary.
- **Kurzes Tutorium Statistik (Bärtl, DE)** — Lage- & Streumaße, German exam vocabulary.
- **StatQuest — "Boxplots, Clearly Explained"** + **"Population vs Sample Variance"** — nails the n vs n−1 distinction (Reference §9).
- **OpenIntro Statistics Ch 2** (local `SaD/Books/2019.openintro.statistics.pdf`) — end-of-section exercises with a solutions appendix; gentle EN.
- **Simpson's paradox** — Minute Physics / any explainer, then re-derive E7 without pausing.

---

## 5. Suggested sequence (~3 h)

1. **E2–E3** (scale types → legal measures) — fast, high exam value.
2. **E1, E4, E5** (location + dispersion + the divisor) — the computational core.
3. **E6** (robustness) + **E7** (Simpson) + **E8** (bias) — the "explain why" items.
4. **FAU descriptive block** timed → self-grade.
5. Thin spots → Arbeitsbuch Ch 2 for volume.

Anything you miss → reread the cited § in `SaD_L02_Ultimate_Reference.md`.

---

*No HU SaD Altklausuren are public (Moodle/Fachschaft only — `LEARNING-RESOURCES.md` §6). Above = SaD sheets + solved external German exams + matched concept material. All keys verified numerically.*
