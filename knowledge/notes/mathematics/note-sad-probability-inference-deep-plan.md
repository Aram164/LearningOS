---
id: note-sad-probability-inference-deep-plan
type: note
title: "SaD 6–10 — The Probability & Inference Core (Deep Study Plan)"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-random-variable, concept-expected-value, concept-variance, concept-discrete-distributions, concept-normal-distribution, concept-central-limit-theorem, concept-maximum-likelihood, concept-statistical-estimation, concept-hypothesis-testing]
sources: [source-sad-ss26-lectures, source-fahrmeir-statistik, source-blitzstein-hwang, source-mit-1805, source-sad-2025-recordings]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` (legacy tree).

# SaD 6–10 — The Probability & Inference Core (Deep Study Plan)

*The biggest, most exam-heavy block of SaD, done once and done properly.*
*Created KW 23 (Jun 2026) | Companion to `Regression_SaD-AML-ISLP_Bridge` and `AML_L02_Ultimate_Reference`*
*Main source: **Fahrmeir et al., Statistik – Der Weg zur Datenanalyse** (9. Auflage, `Plans/Math/sad/SaD/Books/Statistik.pdf`). Primary writing source: SaD lecture notes 06–10. Supplemented with vetted videos (EN + DE).*

> **KW-27 update (Jul 4):** exam final — **ONE combined M2 Klausur (SaD+Analysis), Mo 27.07 12–15h**; these five sessions ARE clusters N3+N4 of the merged prep track. **Drill layer expanded since this plan was written** (all local now): **Fahrmeir Arbeitsbuch** (solved twin, Ch 5–7/9/10–11 per session) · **Dekking** ~300 exercises w/ answers · **FAU Klausur ⭐** (`SaD/Klausuren-extern/` — N3/N4 tasks in German exam format; use in Session 4–5 + Block N) · UE walkthrough keys as collected (Open Loop #5). Source selector: `../../SaD_Source-Crosswalk_L01-L15.md`. Each session below: add 20–30 min from Arbeitsbuch/Dekking; the wire to Analysis (AN.A consistency, AN.G density↔CDF, AN.D log-laws in MLE) is now grade-critical — same Klausur.

---

## 0. Why do these five lectures together, now

SaD 06–10 are **one continuous argument**, not five separate topics. Read in order they answer a single chain of questions:

> **06** What is a random variable, and how do I summarise it? (E[X], Var) →
> **07** What are the standard *discrete* shapes it can take? (Binomial, Hypergeometric, Poisson) →
> **08** What is the one *continuous* shape that rules them all, and why? (Normal + CLT) →
> **09** Given data, how do I *estimate* an unknown parameter, and how sure am I? (point + interval estimation) →
> **10** How do I *decide* whether a claim about that parameter is true? (hypothesis tests)

This is **~40% of the SaD exam** and the entire "inductive statistics" half of the course. It's also the foundation that *everything downstream* silently assumes — the inference layer of regression (ISLP 3.1.2 that tripped you up), model evaluation in AML, and the probabilistic view of ML at large. Doing it now front-loads intuition for the whole semester. You were right.

### Source map (lecture ↔ book ↔ exercise ↔ media)

| SaD lecture | Slides | Fahrmeir chapter(s) | Exercise | Core question |
|---|---|---|---|---|
| **06 Random Variables** | 60 | **Ch 5** (Diskrete ZV) + **Ch 6** (Stetige ZV) + **Ch 7** (Mehr über ZV: E, Var, Tschebyscheff, Grenzwertsätze) | UE4 | "What is a RV; E[X], Var(X)?" |
| **07 Discrete Distributions** | 33 | **Ch 5** (spezielle diskrete Verteilungen) | UE4 | "Binomial / Hypergeometric / Poisson" |
| **08 Normal Distribution** | 38 | **Ch 6** (Normalverteilung) + **Ch 7** (ZGS/CLT, Gesetz der großen Zahlen) | UE5 | "Normal, z-scores, CLT, MLE" |
| **09 Estimation** | 45 | **Ch 9** (Parameterschätzung) | UE5 | "Point + interval estimates, CIs" |
| **10 Statistical Tests** | 65 | **Ch 10** (Testen von Hypothesen) + **Ch 11** (Spezielle Testprobleme) | UE6 | "Hypothesis tests, p-values, errors" |

*Background you already have:* probability basics & combinatorics = SaD 04/05 = Fahrmeir **Ch 4** (Wahrscheinlichkeitsrechnung). Keep Ch 4 handy as the prerequisite layer.

---

## 1. The golden threads (read this before the lectures)

Five connective ideas run through all of 6–10. If you hold these, the details hang together instead of being memorised in isolation.

1. **Sample ↔ Population.** Every sample quantity has a population twin: `x̄ ↔ µ = E[X]`, `s² ↔ σ² = Var(X)`. Descriptive stats (SaD 01–02) measure the sample; probability (06–08) models the population; inference (09–10) jumps from sample back to population. The whole block is about *that jump*.
2. **Variance shrinks with n.** `Var(X̄) = σ²/n`. One formula drives the Law of Large Numbers, the Central Limit Theorem, the standard error, and the width of every confidence interval. Internalise it.
3. **The Normal is the attractor.** The CLT says sums/means of *anything* (enough of it) become Normal. That's why one distribution dominates estimation and testing — and why z-scores are everywhere.
4. **Estimation and testing are the same coin.** A confidence interval and a two-sided hypothesis test use the *same* statistic and quantile; the CI is "all the null values you would *not* reject." SaD 10 says this explicitly ("Tests versus Confidence Intervals").
5. **MLE is the hidden engine.** Maximum Likelihood (introduced in 08) is *why* the sample mean estimates µ, *why* we minimise squared error in regression, and the conceptual seed of how ML models are trained. It connects this whole block to your AML regression notes.

---

## 2. Lecture-by-lecture deep dive

For each: the concepts to write out, the key formulas, where Fahrmeir goes deeper, the exam targets, the connections, and the videos. Watch the linked video *before* reading the slides for any subtopic that isn't already solid.

---

### SaD 06 — Random Variables  *(Fahrmeir Ch 5 + 6 + 7)*

**Concepts to write out**
- Random experiment, event space Ω; **random variable** `X: Ω → ℝ` (a rule turning outcomes into numbers).
- **Discrete vs continuous** RVs. Probability function `p(x)` (discrete) vs **density** `f(x)` (continuous).
- **Cumulative distribution function** `F(x) = P(X ≤ x)`; for continuous X, `f(x) = F'(x)`, and `P(X=x)=0`.
- **Expected value** `µ = E[X]` — the population analogue of `x̄`.
- **Variance** `σ² = Var(X)` and standard deviation `σ`.
- Rules / lemmata for E and Var (linearity; scaling).
- **Independence** of random variables; E and Var of independent variables.
- **Tschebyscheff inequality** — distribution-free bound on "how far from the mean."
- IID sampling; the sample mean as a random variable with **`Var(X̄)=σ²/n`** (→ precision grows with n).

**Key formulas**

```
E[X] = Σ xᵢ·p(xᵢ)        (discrete)   |   E[X] = ∫ x·f(x) dx   (continuous)
E[aX+b] = a·E[X] + b      E[X+Y] = E[X] + E[Y]
Var(X) = E[(X−µ)²] = E[X²] − µ²        Var(aX+b) = a²·Var(X)
Tschebyscheff:  P(|X−µ| ≥ c) ≤ σ²/c²
IID sample mean:  E[X̄]=µ,  Var(X̄)=σ²/n
```

**Fahrmeir:** Ch 5 (discrete RVs, p(x), F(x)), Ch 6 (continuous RVs, density), Ch 7 (expectation, variance, their rules, Tschebyscheff, and the limit theorems). Use Ch 7 as the rigorous home for E/Var.

**Exam targets (UE4):** compute E[X], Var(X) from a given probability table; apply E/Var rules to `aX+b`; apply Tschebyscheff to bound a tail probability.

**Connections:** `E[X]/Var(X)` are exactly the notation that made ISLP 3.1.2 hard — this is where they're defined. `Var(X̄)=σ²/n` is the seed of the standard error (09). Feeds *everything* after.

🎥 [Expected Values, Main Ideas — StatQuest](https://www.youtube.com/watch?v=KLs_7b7SKi4) · [Expected Values for Continuous Variables — StatQuest](https://www.youtube.com/watch?v=OSPr6G6Ka-U) · [The Main Ideas behind Probability Distributions — StatQuest](https://www.youtube.com/watch?v=oI3hZJqXJuc)

---

### SaD 07 — Discrete Distributions  *(Fahrmeir Ch 5)*

**Concepts to write out**
- **Binomial** `B(n,p)` — number of successes in n independent yes/no trials with fixed p. ("Why binomial": the `C(n,k)` counting term.)
- **Hypergeometric** `H(N,M,n)` — successes when drawing n *without replacement* from a finite pool of N (M of them "good"). Contrast with Binomial (with replacement / independent).
- **Poisson** `Po(λ)` — counts of rare events in a fixed interval; arises as the **limit of Binomial** when `n→∞, p→0, np=λ`.
- Outlook: Negative Binomial, Multinomial, Beta (just recognise them).
- Worked applications from the slides: defect/quality testing, Poisson approximation, even Erdős–Rényi random graphs.

**Key formulas**

```
Binomial:        P(X=k) = C(n,k) pᵏ (1−p)ⁿ⁻ᵏ      E=np,      Var=np(1−p)
Hypergeometric:  P(X=k) = C(M,k)·C(N−M, n−k) / C(N,n)
                 E = n·(M/N),   Var = n·(M/N)(1−M/N)·(N−n)/(N−1)
Poisson:         P(X=k) = λᵏ e⁻λ / k!             E = Var = λ
Poisson limit:   Binomial(n,p) ≈ Poisson(λ=np)  for large n, small p
```

**Fahrmeir:** Ch 5 — the named discrete distributions, each with derivation of E and Var.

**Exam targets (UE4):** identify *which* distribution a word problem describes (the classic trap: with vs without replacement → Binomial vs Hypergeometric); compute `P(X=k)`, `P(X≤k)`, E, Var; use the Poisson approximation; combine with Tschebyscheff for a tail bound (the slides do exactly this).

**Connections:** Binomial → Normal approximation is the bridge into 08. `E=Var=λ` for Poisson is a memorable exam fact. The "rare events" framing returns whenever you model counts.

🎥 [The Binomial Distribution in 30s — StatQuest](https://www.youtube.com/shorts/aH3mZjHkAbs) · [Sampling from a Distribution — StatQuest](https://www.youtube.com/watch?v=XLCWeSVzHUU) · [Introduction to the Poisson Distribution — Statistics 101 (Brandon Foltz)](https://www.youtube.com/watch?v=8px7xuk_7OU)

---

### SaD 08 — Normal Distribution  *(Fahrmeir Ch 6 + 7)*

**Concepts to write out**
- The **Normal distribution** `N(µ,σ²)`: the bell curve, its density, symmetry, the **68–95–99.7 rule**.
- **Standard normal** `N(0,1)`; **z-normalization** `Z=(X−µ)/σ`; the CDF `Φ(z)=P(Z≤z)` and table lookups; symmetry `Φ(−z)=1−Φ(z)`.
- **Quantiles** and how σ maps to probability mass.
- **Linear transform**: `Y=aX+b ⇒ N(aµ+b, a²σ²)`. **Sum of independent normals**: `Z=X+Y ⇒ N(µ_X+µ_Y, σ²_X+σ²_Y)`.
- ⭐ **Central Limit Theorem (no proof):** the mean/sum of many IID variables is approximately Normal, *whatever* their original distribution.
- **Normal approximations**: of the Binomial `≈ N(np, np(1−p))` (with continuity correction `+0.5`), and of the Poisson.
- **z-normalization in ML** = feature scaling / standardisation (the slides call this out explicitly).
- ⭐ **Normal errors → Maximum Likelihood → (the seed of) MSE.** Assume measurement errors are `N(0,σ²)`; the sample/parameters that maximise the likelihood of the observed data are the "best" ones. This is the MLE assumption stated on the slides.

**Key formulas**

```
Density:  f(x) = 1/(σ√(2π)) · exp( −(x−µ)²/(2σ²) )
z-score:  Z = (X−µ)/σ  ~ N(0,1)        P(a<X<b) = Φ((b−µ)/σ) − Φ((a−µ)/σ)
CLT:      X̄ ≈ N(µ, σ²/n)  for large n
Normal ≈ Binomial:  N(np, np(1−p)),  continuity correction ±0.5
MLE idea: maximise  L(θ)=∏ f(xᵢ|θ)  ⇔  maximise log L  ⇔ (Gaussian) minimise Σεᵢ²
```

**Fahrmeir:** Ch 6 (Normal and other continuous distributions); Ch 7 (Grenzwertsätze — Law of Large Numbers and the Central Limit Theorem). The CLT in Ch 7 is the theoretical keystone.

**Exam targets (UE5/UE6):** standardise to a z-score and look up probabilities (`what % of women are taller than…`); use the 68–95–99.7 rule; approximate a Binomial with a Normal (UE6 does this with continuity correction); state the CLT in one sentence.

**Connections:** This is the hinge of the whole block. CLT *justifies* using the Normal in 09–10. z-normalization = the feature scaling you do in the AMLS project. The **MLE→MSE** thread links straight to your regression bridge note (`Tier 3.3`) — same idea, here is where SaD states it.

🎥 [The Central Limit Theorem — StatQuest](https://www.youtube.com/watch?v=YAlJCEDH2uY) · [But what is the Central Limit Theorem? — 3Blue1Brown](https://www.youtube.com/watch?v=zeJD6dqJ5lo) · [Maximum Likelihood, clearly explained — StatQuest](https://www.youtube.com/watch?v=XepXtl9YKwc) · [Probability is not Likelihood — StatQuest](https://www.youtube.com/watch?v=pYxNSUDSFH4)

---

### SaD 09 — Estimation  *(Fahrmeir Ch 9)*

**Concepts to write out**
- The **estimation problem**: an unknown population parameter `θ` (e.g. µ, σ², p); a random sample `X₁…Xₙ` (IID); an **estimator** `T(X₁…Xₙ)` (itself a random variable).
- **Point vs interval** estimation.
- **Quality criteria for estimators**: **unbiased** `E[T]=θ`; **consistent** (`T→θ` as `n→∞`); **MSE-consistent** `lim E[(T−θ)²]=0`; **efficient** (smallest variance). Bias as a concept.
- The sample mean is an unbiased, consistent estimator of µ; estimating the variance (and why `n−1`).
- **Confidence interval** at level `1−α`: an interval that traps the true θ with probability `1−α`.
  - mean, **known** variance → uses z (standard normal).
  - mean, **unknown** variance → uses the **t-distribution** with `s` instead of σ.
  - mean of an arbitrary distribution, **large n** → CLT lets you use z anyway.
- Higher confidence ⇒ wider interval (the fundamental trade-off).
- **Resampling / bootstrap**: estimate the variability of *any* statistic by re-sampling — the slides' "estimate any property by resampling."
- Case study on the slides: the 2021 Delphi–Facebook COVID poll — **data quality beats data quantity** (a huge biased sample was worse than a small clean one). A real lesson about bias vs variance.

**Key formulas**

```
Estimator:  T = T(X₁,…,Xₙ)          Unbiased:  E[T]=θ
CI for mean, σ known:    x̄ ± z_{1−α/2} · σ/√n
CI for mean, σ unknown:  x̄ ± t_{n−1; 1−α/2} · s/√n
Standard error:          SE = σ/√n   (or s/√n)
```

**Fahrmeir:** Ch 9 (Parameterschätzung) — point estimators, their properties, and interval estimation, all here.

**Exam targets (UE5):** state whether an estimator is unbiased/consistent; construct a 95%/99% CI for a mean (choosing z vs t correctly based on whether σ is known); explain how the interval width responds to n, σ, and confidence level.

**Connections:** `SE=σ/√n` *is* `√(Var(X̄))` from 06. This is exactly the **standard error / CI machinery** behind ISLP 3.1.2 for regression coefficients — same story, `β̂` instead of `x̄` (see your regression bridge note, Tier 4). Estimators-as-random-variables is the conceptual leap that unlocks all of inference.

🎥 [The Standard Error — StatQuest](https://www.youtube.com/watch?v=XNgt7F6FqDU) · [Confidence Intervals — StatQuest](https://www.youtube.com/watch?v=TqOeMYtOc1w) · [Using Bootstrapping to Calculate p-values — StatQuest](https://www.youtube.com/watch?v=N4ZQQqyIf6k) · 🇩🇪 [Konfidenzintervall — Mathe by Daniel Jung](https://www.youtube.com/watch?v=l0qTTos-L0o)

---

### SaD 10 — Statistical Tests  *(Fahrmeir Ch 10 + 11)*

**Concepts to write out**
- The **general idea**: a claim about the population → collect data → ask "how surprising is this data *if the claim were true*?"
- **Null `H₀` vs alternative `H₁`** hypotheses; why we test against the null.
- **Test statistic**; compare against a tabulated reference distribution (standard normal, t, χ²).
- **Gauß-test (z-test)** for a mean with known variance; **t-test** when variance is unknown — the step-by-step procedure on the slides (formulate H₀/H₁ → compute statistic → look up quantile → decide).
- **One-tailed vs two-tailed** tests.
- **Error types**: **Type I** (reject a true H₀; probability `α`) and **Type II** (keep a false H₀; probability `β`); **power = 1−β**; the stronger the test, the higher the power.
- **p-value**: probability, *under H₀*, of a result at least as extreme as observed; reject when `p < α`.
- **Tests ↔ Confidence Intervals** duality (the slides make this point directly).
- **Non-parametric / other tests**: Pearson **χ² test** (independence in a contingency table / goodness of fit), **Wilcoxon rank-sum**, **permutation test**.
- The **multiple-testing trap** (the German slide example: test enough criteria and *something* will look "significant" by chance).

**Key formulas**

```
Gauß (z) test of H₀: µ=µ₀ (σ known):   z = (x̄ − µ₀)/(σ/√n)
t-test (σ unknown):                     t = (x̄ − µ₀)/(s/√n),  df = n−1
Reject (two-sided) if |statistic| > quantile_{1−α/2}
p-value = P(result this extreme | H₀);  reject if p < α
χ² test:  χ² = Σ (observed − expected)² / expected
```

**Fahrmeir:** Ch 10 (Testen von Hypothesen — the logic, z/t tests, errors, p-values); Ch 11 (Spezielle Testprobleme — χ², two-sample, non-parametric).

**Exam targets (UE6):** set up H₀/H₁; compute a z- or t-statistic; compare to the critical value and state the conclusion in words; explain Type I vs II with an example; interpret a p-value correctly; run a χ² independence test from a contingency table.

**Connections:** Same statistic + quantile as the CI in 09 (duality). Type I/II errors map onto the **false positive / false negative** table from your `AML_L02` note (precision/recall) — *literally the same 2×2 confusion matrix*, viewed inferentially. Comparing two models' accuracy is, underneath, a hypothesis test.

🎥 [Hypothesis Testing — StatQuest](https://www.youtube.com/watch?v=hGoTUyBnbxg) · [Null Hypothesis — StatQuest](https://www.youtube.com/watch?v=0oc49DyA3hU) · [p-values: what they are & how to interpret them — StatQuest](https://www.youtube.com/watch?v=vemZtEM63GY) · [How to calculate p-values — StatQuest](https://www.youtube.com/watch?v=JQc3yx0-Q9E) · [One or Two Tailed p-values — StatQuest](https://www.youtube.com/watch?v=bsZGt-caXO4) · 🇩🇪 [Hypothesentest — numiqo (ehem. DATAtab)](https://numiqo.de/tutorial/hypothesentest)

---

## 3. The ordered study sequence

Roughly five focused sessions (~3h each). The rule: **video → lecture slides → Fahrmeir section → exercise**. Do not skip the exercise — SaD is an exam of *computations*, not definitions.

**Session 1 — Random variables (SaD 06).** Watch Expected Values + Probability Distributions. Slides 06. Fahrmeir Ch 5–6 (skim densities), Ch 7 (E, Var, Tschebyscheff). Drill: compute E/Var from a table; one Tschebyscheff bound.
- ✅ Checkpoint: from a 5-row probability table, produce E[X], Var(X), and `Var(X̄)` for n=10 by hand.

**Session 2 — Discrete distributions (SaD 07).** Slides 07 + Fahrmeir Ch 5. Make a **one-page table** of Binomial / Hypergeometric / Poisson (formula, E, Var, "when to use"). Do UE4.
- ✅ Checkpoint: given three word problems, pick the right distribution and compute `P(X=k)` for each.

**Session 3 — Normal & CLT (SaD 08).** Watch CLT (StatQuest + 3B1B) and Maximum Likelihood. Slides 08. Fahrmeir Ch 6 (Normal), Ch 7 (CLT). Drill z-score lookups + one Normal-approx-to-Binomial.
- ✅ Checkpoint: standardise and look up a probability; state the CLT in one sentence; write the MLE→MSE chain in 5 steps.

**Session 4 — Estimation (SaD 09).** Watch Standard Error + Confidence Intervals. Slides 09. Fahrmeir Ch 9. Do UE5 (incl. Standardfehler & Konfidenzintervalle).
- ✅ Checkpoint: build a 95% CI with σ known (z) and a second with σ unknown (t); explain why the t-version is wider.

**Session 5 — Testing (SaD 10).** Watch Hypothesis Testing + p-values. Slides 10. Fahrmeir Ch 10 (+ skim Ch 11 for χ²). Do UE6.
- ✅ Checkpoint: run a full two-sided z-test end to end (H₀ → statistic → critical value → decision in words); state Type I/II for that test; interpret its p-value.

**Then:** you will have covered the entire probability+inference half of SaD and can revisit only via Block N (exam drill) later. This also retro-unlocks ISLP 3.1.2 for the regression note.

---

## 4. Comprehensive self-test (SaD exam format)

If you can do all of these cold, this block is exam-ready.

**Random variables (06)**
- [ ] Given a discrete probability table, compute `E[X]`, `Var(X)`, `σ`.
- [ ] If `E[X]=5, Var(X)=2`, give `E[3X+1]` and `Var(3X+1)`.
- [ ] Apply Tschebyscheff: at least what fraction of data lies within 2σ of µ?

**Discrete distributions (07)**
- [ ] `X~B(n=8, p=0.5)`: compute `P(X=3)` from the PMF.
- [ ] Urn: 5 red, 7 blue, draw 3 without replacement — `P(exactly 2 red)` (which distribution, and why?).
- [ ] `λ=3/hour`: compute `P(X=0)` and `P(X≥1)` (Poisson).
- [ ] State when you'd use Binomial vs Hypergeometric vs Poisson.

**Normal & CLT (08)**
- [ ] `X~N(100, 15²)`: compute `P(X>130)` via z-standardisation.
- [ ] State the 68–95–99.7 rule and sketch the curve.
- [ ] State the CLT in one sentence; explain why it lets you use the Normal for a sample mean.
- [ ] Walk the MLE→MSE derivation: normal errors → likelihood → log → drop constants → minimise `Σεᵢ²`.

**Estimation (09)**
- [ ] Define unbiased, consistent, efficient — one sentence each.
- [ ] `x̄=48, σ=12, n=36`: 95% CI for µ (use z=1.96).
- [ ] Same but σ unknown, `s=12, n=16`: which distribution, and why is the interval wider?

**Testing (10)**
- [ ] `H₀: µ=50` vs `H₁: µ≠50`, `x̄=47, σ=6, n=36, α=0.05`: compute z, compare to z_crit, conclude in words.
- [ ] Explain Type I and Type II error with the medical-test analogy; link to false positive / false negative.
- [ ] What does `p=0.03` mean, precisely?
- [ ] Run a χ² independence test from a 2×2 contingency table.

---

## 5. Curated media library (all verified)

**Random variables / E[X], Var (06)**
- [Expected Values, Main Ideas — StatQuest](https://www.youtube.com/watch?v=KLs_7b7SKi4)
- [Expected Values for Continuous Variables — StatQuest](https://www.youtube.com/watch?v=OSPr6G6Ka-U)
- [The Main Ideas behind Probability Distributions — StatQuest](https://www.youtube.com/watch?v=oI3hZJqXJuc)

**Discrete distributions (07)**
- [The Binomial Distribution in 30s — StatQuest](https://www.youtube.com/shorts/aH3mZjHkAbs)
- [Sampling from a Distribution — StatQuest](https://www.youtube.com/watch?v=XLCWeSVzHUU)
- [Introduction to the Poisson Distribution — Statistics 101](https://www.youtube.com/watch?v=8px7xuk_7OU)

**Normal & CLT + MLE (08)**
- [The Central Limit Theorem — StatQuest](https://www.youtube.com/watch?v=YAlJCEDH2uY)
- [But what is the Central Limit Theorem? — 3Blue1Brown](https://www.youtube.com/watch?v=zeJD6dqJ5lo)
- [Maximum Likelihood, clearly explained — StatQuest](https://www.youtube.com/watch?v=XepXtl9YKwc)
- [Probability is not Likelihood — StatQuest](https://www.youtube.com/watch?v=pYxNSUDSFH4)

**Estimation / CIs (09)**
- [The Standard Error — StatQuest](https://www.youtube.com/watch?v=XNgt7F6FqDU)
- [Confidence Intervals — StatQuest](https://www.youtube.com/watch?v=TqOeMYtOc1w)
- [Bootstrapping to calculate p-values — StatQuest](https://www.youtube.com/watch?v=N4ZQQqyIf6k)
- 🇩🇪 [Konfidenzintervall — Mathe by Daniel Jung](https://www.youtube.com/watch?v=l0qTTos-L0o)

**Testing (10)**
- [Hypothesis Testing — StatQuest](https://www.youtube.com/watch?v=hGoTUyBnbxg)
- [Null Hypothesis — StatQuest](https://www.youtube.com/watch?v=0oc49DyA3hU)
- [p-values: what they are & how to interpret them — StatQuest](https://www.youtube.com/watch?v=vemZtEM63GY)
- [How to calculate p-values — StatQuest](https://www.youtube.com/watch?v=JQc3yx0-Q9E)
- [One or Two Tailed p-values — StatQuest](https://www.youtube.com/watch?v=bsZGt-caXO4)
- 🇩🇪 [Hypothesentest — numiqo (ehem. DATAtab)](https://numiqo.de/tutorial/hypothesentest)
- 🇩🇪 [Statistik Grundkurs (playlist)](https://www.youtube.com/playlist?list=PL-p9JpwN5NNEdbUsMDCcuWe1HhyR9ebsq)

---

## 6. Optional rigorous track — MIT 18.650 *Statistics for Applications* (Rigollet)

A proof-based, English, undergraduate **mathematical statistics** course ([course home](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/) · [lecture videos](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/video_galleries/lecture-videos/) · [problem sets](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/pages/assignments/)). It is **not an AML companion** — it has no optimization, gradient descent, or neural nets. But it is almost exactly the *rigorous version of this SaD block* (MLE → estimation → testing → goodness of fit), plus regression-as-inference and GLMs. Treat it as an **optional depth layer** for masters/BIFOLD-grade foundations: pull the lecture that matches whatever SaD topic you want to go deeper on. Each MIT lecture has slides + video + a problem set.

| MIT 18.650 unit | Deepens (this plan) | Use it for | Priority |
|---|---|---|---|
| [L1–2 Introduction to Statistics](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-1-introduction/) | SaD 01–02 + § 1 golden threads | The population↔sample framing, done formally | optional |
| [L3 Parametric Inference](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-2-parametric-inference/) | **SaD 09** | The formal "statistical model + parameter" setup | medium |
| [L4–5 Maximum Likelihood Estimation](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-3-maximum-likelihood-estimation/) | **SaD 08 (MLE) + 09** | ⭐ The rigorous MLE — the engine behind "why MSE" and behind ML training. Highest ROI | **high** |
| [L6 The Method of Moments](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/mit18_650f16_method_of_moments_pdf/) | (extension) | An alternative way to build estimators; nice contrast to MLE | optional |
| [L7–10 Parametric Hypothesis Testing](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-5-parametric-hypothesis-testing/) | **SaD 10** | ⭐ The rigorous core of testing (Wald, likelihood-ratio, t/z). Directly strengthens UE6 | **high** |
| [L11–12 Testing Goodness of Fit](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-6-testing-goodness-of-fit/) | SaD 10 (χ²) | χ² and goodness-of-fit, properly derived | medium |
| [L13–16 Regression](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-7-regression/) | SaD 03 + `Regression_SaD-AML-ISLP_Bridge` (Tier 4) | ⭐ Regression **as inference**: standard errors and tests on coefficients — exactly the ISLP 3.1.2 layer you parked | **high** |
| [L17–18 Bayesian Statistics](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/mit18_650f16_bayesian_statistics_pdf/) | SaD 04 / 14 (Bayes, Naïve Bayes) | Bonus: the Bayesian view of estimation; pairs with regularization-as-a-prior | bonus |
| [L19–20 Principal Component Analysis](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-9-principal-component-analysis-pca/) | (beyond SaD core) | Bonus: dimensionality reduction; broadly useful for ML | bonus |
| [L21–24 Generalized Linear Models](https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/resources/lecture-10-generalized-linear-models-glms/) | SaD 14 + **AML L05 (logistic)** | Logistic & Poisson regression theory — the one place this course *does* reach into AML | medium |

**How to use it without it becoming a second course:** don't watch it linearly. When you finish a SaD session above and want more rigour, watch *only* the matching MIT lecture. For the SaD exam, the three high-ROI pulls are **L4–5 (MLE)**, **L7–10 (Testing)**, and **L13–16 (Regression inference)**. Everything else is masters-prep bonus. Skip the Method of Moments / PCA / Bayesian units unless you have spare time — they're enrichment, not SaD-exam material.

## 7. Optional rigorous track — HarvardX STAT110x *Introduction to Probability* (Blitzstein)

Joe Blitzstein's famous probability course ([edX landing page](https://www.edx.org/learn/probability/harvard-university-introduction-to-probability) · all lectures free on the [Harvard Stat 110 site](https://stat110.hsites.harvard.edu/) → [YouTube playlist](https://stat110.hsites.harvard.edu/youtube) · [handouts incl. the distribution cheat-sheet](https://stat110.hsites.harvard.edu/handouts) · free textbook *Blitzstein & Hwang*). Seven units, taught via "story proofs" — building distributions from the situations that generate them, which gives you intuition the SaD slides assume.

Where this differs from 18.650: **STAT110 is the *probability foundation* (the front half of SaD), 18.650 is the *inference layer* (the back half).** Together they cover the whole module rigorously:

> **STAT110x ≈ SaD 04–08** (probability, random variables, distributions, Normal, CLT) · **18.650 ≈ SaD 09–10** (estimation, testing, regression-as-inference).

Like 18.650, it is **not an AML course** — it's foundational probability. But probability *is* the language of ML, so it's high-value for the masters/BIFOLD goal. It's a full course, so **cherry-pick units 3–6** for this SaD block.

| STAT110x unit | Deepens (this plan) | Use it for | Priority |
|---|---|---|---|
| Unit 1 — Probability, Counting & Story Proofs | SaD 05 (combinatorics) + 04 | Sample spaces, counting, the "story" mindset | medium |
| Unit 2 — Conditional Probability & Bayes' Rule | SaD 04 → 14 (Naïve Bayes) | Bayes mastery (also feeds your classification block) | medium |
| Unit 3 — Random Variables & Their Distributions | **SaD 06 + 07** | ⭐ RVs, PMF/CDF, Bernoulli/Binomial/Hypergeometric | **high** |
| Unit 4 — Expectation (LOTUS, indicators, Poisson, Geometric, variance) | **SaD 06 (E/Var) + 07 (Poisson)** | ⭐ Expectation & variance done deeply; the indicator-RV trick is gold | **high** |
| Unit 5 — Continuous Random Variables (Uniform, Normal, Exponential) | **SaD 06 + 08 (Normal)** | ⭐ Densities, the Normal, standardisation | **high** |
| Unit 6 — Joint Distributions, Covariance/Correlation, LLN & CLT | **SaD 03 (cov/corr) + 06 + 08 (CLT)** | ⭐ Covariance/correlation *and* the CLT — ties back to your regression bridge | **high** |
| Unit 7 — Markov Chains | (beyond SaD) | Bonus: foundational for RL, sequence models, MCMC | bonus |

**How to use it:** for the SaD exam this block, Units **3, 4, 5, 6** are the high-ROI pulls — they cover exactly SaD 06–08 with far more intuition. Watch the matching Blitzstein lecture when a SaD topic feels mechanical rather than understood. Grab the **distribution cheat-sheet handout** early — it's the single best one-page summary of every distribution you'll meet in SaD 07–08. Units 1–2 are review (you've done SaD 04–05); Unit 7 is enrichment.

**The combined external track, at a glance:**

```
Probability foundation        Inference layer
   STAT110x                      18.650
   Units 3–6   ──────────────►   L4–5 (MLE) → L7–10 (Testing) → L13–16 (Regression)
   = SaD 06–08                   = SaD 09–10
```

---

*Sources: SaD lecture notes 06–10 (Akbik, HU SoSe 2025/26); Fahrmeir, Heumann, Künstler, Pigeot, Tutz — Statistik: Der Weg zur Datenanalyse, 9. Aufl. (Ch 5, 6, 7, 9, 10, 11); SaD Übungen UE4–UE6; MIT 18.650 Statistics for Applications (Rigollet, Fall 2016, MIT OCW); HarvardX STAT110x Introduction to Probability (Blitzstein). Maps to Foundations Blocks G (06–08) and J (09–10).*
