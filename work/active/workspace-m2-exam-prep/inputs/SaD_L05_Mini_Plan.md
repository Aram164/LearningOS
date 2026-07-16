# SaD Lecture 05 — Mini Learning Plan (Combinatorics)

> **📌 Supports Block N2 (probability & counting).** SaD steps stay **F.*** in Chat1 — log completions in `SESSION-LOG.md` + tick SEMESTER-STATUS §3. Fifth per-lecture SaD unit (3-file variant, no Mock Exam); last of the L01–L05 batch.

Sequenced path for L05: **concept → video → book → practice**. Practice in `SaD_L05_Exercise_Bank.md`; reference `SaD_L05_Ultimate_Reference.md` (same folder). Budget ~2.5–3 h — L05 is short but the **case-recognition** skill is the whole game.

**Book cites (gentle → rigorous):** Schaum's Ch 2 🧮 (⭐ drills the 6-case grid) · Fahrmeir Ch 4 🟡🇩🇪 (exam notation, 6-case table) · **Blitzstein Ch 1 🟡 (⭐ clearest *why* — here Blitzstein is easy, not hard)** · Ross Ch 1 🔴 (thorough/dense) · Pitman Ch 1–2.5 🟡 (counting woven in). *OpenIntro/Tijms are weak on formal counting.* One or two is enough — full ladder: `SaD_Book-Difficulty-Map_L01-L15.md` → L05.

---

## Step 1 — The decision grid (the core skill)  (~40 min)

The two questions — **order?** and **repeats?** — plus "all n vs choose k" → one of six cases. Get this reflexive before any arithmetic.

- 🎥 ⭐ **jbstatistics — "Permutations and Combinations"** (or KTS, DE).
- 📖 **Blitzstein Ch 1** (naive definition, multiplication rule, sampling table) or Fahrmeir Ch 4.
- 📝 Reference §2 (the grid) + §7 (the six-formula table).
- ✍️ Exercise Bank **C1** (classify each scenario) — repeat until instant.

## Step 2 — Permutations & variations  (~40 min)

n! (all distinct); multinomial n!/(k₁!···kₛ!) (indistinguishable groups); variation without replacement n!/(n−k); variation with replacement nᵏ.

- 🎥 **jbstatistics / KTS — permutations & the multiplication principle.**
- 📖 **Blitzstein Ch 1** (permutations, sampling with/without replacement).
- 📝 Reference §3–§4.
- ✍️ Exercise Bank **C2** (multinomial), **C3** (variation w/o repl), **C4** (variation w/ repl).

## Step 3 — Combinations (both kinds) + stars & bars  (~40 min)

C(n,k) = variations ÷ k!; combination with replacement C(n+k−1,k) via the stars-and-bars / Gummibärchen proof.

- 🎥 **jbstatistics — "Combinations"**; a "stars and bars" explainer for the with-replacement case.
- 📖 **Blitzstein Ch 1** (binomial coefficient, Bose–Einstein / stars-and-bars).
- 📝 Reference §5–§6.
- ✍️ Exercise Bank **C5** (choose k) + **C6** (stars & bars).

## Step 4 — Counting → probability: Laplace + hypergeometric  (~40 min)

P(A)=|A|/|Ω| built from counts; the hypergeometric formula C(n₁,k₁)C(n−n₁,k−k₁)/C(n,k) (draw without replacement) — previews L07.

- 🎥 **StatQuest — "Hypergeometric Distribution"** (forward-link to L07).
- 📖 **Blitzstein Ch 1** (probability via counting) / Fahrmeir Ch 4.
- 📝 Reference §8–§9.
- ✍️ Exercise Bank **C7** (poker/Laplace) + **C8** (quality control) + **C9** (Lotto) + **C10** (birthday link).

## Step 5 — Binomial identities & Stirling  (~15 min, light)

C(n,k)=C(n,n−k), Pascal's rule, Σ C(n,k)=2ⁿ, binomial theorem; Stirling n! ~ √(2πn)(n/e)ⁿ for asymptotics/complexity.

- 📝 Reference §10. No drill — just recognition (recurs in L07 Binomial + Algo-2 complexity).

## Step 6 — Practice & self-test  (→ exercise bank)

1. **UE3** (counting half) → collect walked-through solutions in the Übung.
2. **C1–C10** → keys in the bank.
3. **FAU** Binomial/counting items (timed) → then Blitzstein Ch 1 strategic practice for volume.

---

### Suggested schedule (~2.5–3 h)

| Session | Steps | Output |
|---|---|---|
| 1 | Steps 1–3 | the six cases + formulas cold; C1–C6 |
| 2 | Steps 4–6 | counting→probability + hypergeometric; C7–C10 + FAU |

---

### 🎓 End of the L01–L05 batch

That completes the requested per-lecture units for **L01–L05** (descriptive → correlation/regression → probability/Bayes → combinatorics). **L06–L10** (random variables → distributions → normal/CLT → estimation → testing) are covered by the existing **`SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md`** (its 5 sessions are the unit layer for that half). **L11–L15** (the ML methods) are served by the L11 Reference, the AML L02 unit (k-NN/L13), and the crosswalk rows for trees/NB/NN. Say the word if you want per-lecture units built for any of those too.
