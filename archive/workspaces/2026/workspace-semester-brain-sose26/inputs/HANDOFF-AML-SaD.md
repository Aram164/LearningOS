# Handoff — AML + SaD Foundations (Chat 1)

> **Created:** 2026-06-25 (KW 26) · **Scope:** AML (Angewandtes ML, Schäfer) + SaD (Statistik & Data Science, Akbik), HU SoSe 2026.
> **Purpose:** boot a fresh AML+SaD chat without re-deriving everything. Read order: **this file → `../../../SEMESTER-STATUS.md` (the brain, for dates/priorities) → `Chat1_Foundations_AML_SaD_Plan.md` (the block plan, step prefix `F`)**.
> Authoritative for *dates/status* is SEMESTER-STATUS.md; authoritative for *what study material exists* is this file.

---

## 1. Context

**Aram** — MSc ML×DE, HU+TU Berlin; near-zero ML at semester start, ambitious pacing, prefers concise/direct, dislikes hand-holding. BIFOLD/DEEM job ahead.

**The two modules and how they relate:**
- **AML** (Schäfer) — applied/loss-first ML. Lecture sequence: L01 intro, **L02 k-NN, L03 linear regression, L04 non-linear regression + regularization, L05 logistic regression, L06 gradient descent**, L07 perceptron/linear classifiers (⚠️ **no SVM** — slide-verified), L08–L09 neural nets, L10 CNNs, L11 RNNs.
- **SaD** (Akbik) — stats-first → ML. Probability/inference half = lectures **06–10** (has its own deep plan); ML half overlaps AML: **L11 instance-based (= k-NN, supports AML L02)**, L12 clustering, L13 similarity/trees, L14–15 neural nets.
- **SaD is a Kombimodul with Analysis (M2.1, one grade).** AML + SaD written exams are in the **1. Termin (late July)** block — confirm exact dates in SEMESTER-STATUS.md.
- Cross-module wiring is documented in `reference/AML-SaD_Master_Wiring.md`.

---

## 2. Where everything lives

| Thing | Path |
|---|---|
| **AML lecture slides** | `AML/SoSe 2026/lecture slides/VL 0X-*.pdf` |
| **AML exercise/tutorial decks** | `AML/SoSe 2026/Exercise slides/` — ⚠️ filenames ≠ sheet order (see gotchas) |
| **AML bonus sheets** | `AML/SoSe 2026/Bonus-exercises/zusatz-blatt0X.pdf` |
| **AML per-lecture study units** | `AML/my notes/lectNN <topic>/` (L02–L06) |
| **AML book↔concept crosswalk (L02–L10)** | `AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md` |
| **AML books (local)** | `AML/Bücher/` — ISLP, ESL, Murphy PML1 (+solutions), Kroese (Data Science & ML), Toronto CSC411, **CS229 Lecture Notes** |
| **CS4780 solved homeworks** | `AML/CS4780-homeworks/` (see its README for the topic map) |
| **SaD slides (2026)** | `Plans/Math/sad/SaD/Lecture-slides/` · **SaD 2025 slides** `Plans/Math/sad/SaD/SaD-2025/` *(moved out of ML/foundations KW 27 — SaD is a Math/Kombimodul subject)* |
| **SaD notes** | `Plans/Math/sad/SaD/notes/` — incl. `lect11 instance-based/SaD_L11_Reference.md` and the `SaD_06-10_Probability-Inference_DeepPlan.md` |
| **Cross-module bridges** | `reference/Regression_SaD-AML-ISLP_Bridge.md`, `reference/AML-SaD_Master_Wiring.md` |
| **Master resource index** | `../../../LEARNING-RESOURCES.md` (repo root) — all external + local material, tagged |

---

## 3. The "complete unit" template (the per-lecture standard)

Each finished AML lecture folder (`AML/my notes/lectNN …/`) contains, modeled on the user-praised **L02** set:

1. **`AML_L0X_Ultimate_Reference.md`** — detailed, **numbered TOC**, per-section `[Source: VL0X slide N]` citations, worked examples, ASCII diagrams, self-test.
2. **`AML_L0X_Mini_Plan.md`** — study path **in lecture order**: concept → lecture video → reading → practice; with a **"Reading scope" note**.
3. **`AML_L0X_Exercise_Bank.md`** — consolidated: local material → source sheets (incl. the graded Übungsblatt task-by-task) → external solution-checked practice → key scoped ISLP exercises → suggested sequence.
4. **`AML_L0X_Mock_Exam.md`** — 100 pts (Part A conceptual / B numerical / C true-false / D synthesis) **with full answer key in the same file**; all numerics computer-verified.
5. **Bonus-sheet solution(s)** — `AML_BonusSheetNN_Solution.md` (worked key).

**SaD lectures get their own sheets** under `Plans/Math/sad/SaD/notes/lectNN …/` (mirrors AML), and AML cross-links to them rather than absorbing SaD scope.

---

## 4. Conventions / rules (follow these)

- **Reading-scope rule (user-mandated):** match every reading to the lecture's *actual* scope **and** the student's prior-lecture prerequisites. Never keyword-match to advanced chapters (ISLP Ch 7 ≠ L04). Mark beyond-scope material `skip`/`optional depth`. Pull *named sections*, not whole chapters. Memory: `reading-suggestions-scope-to-lecture`.
- **Verify all numerics** with Python (NumPy/fractions) before writing them into references/keys. This has caught real slide typos (e.g. SaD L11 SPAM F-score is **0.50**, not the deck's 0.37).
- **Verify book section numbers** against the local PDF TOCs (`pdftotext`), don't trust memory.
- **Course video/course spine (Aram's pick):** **Stanford CS229 2022** (⚠️ Spring-2022 playlist = **Ma & Ré**; Ng-taught = the 2018 mirror — corrected KW 27) + **MIT 6.036 (Open Learning Library)**. The **CS229 Lecture Notes** in `Bücher/` are the *written companion* to that spine; the verified lecture⇄AML map is in the crosswalk's 🎥 layer. Andrew Ng's gentler **Coursera ML** mirror is the closest level-match for L03–L05 and is still cited per-lecture. **CS4780 (Weinberger)** is *general ML / for-later* (different, probability-first angle) — use its written notes as targeted refs, not the full video series.
- **Ask before large multi-file builds**; present finished files via the file cards; keep responses concise.
- **Binary downloads aren't possible** in-session — the user places PDFs in `Bücher/` etc. manually; then they get read/mapped.

---

## 5. Current state

### AML — lectures L02–L07 are **complete units** ✅
Each has all five components (reference + mini-plan + exercise bank + mock exam + bonus solution), scoped and prerequisite-aware, with the graded Übungsblätter folded in.

| Lecture | Topic | Notes |
|---|---|---|
| **L02** | k-NN, bias-variance, cross-validation | Reference §8 has the bias-variance deep-dive (§8.1.1 wording, §8.1.2 retraining-intuition). **Trimmed to AML scope** — SaD-only material (vectorization, eval toolkit, ML-families taxonomy) moved to the SaD L11 sheet + cross-linked. |
| **L03** | linear regression (1 predictor) + linear algebra/vectorization | — |
| **L04** | non-linear: multivariate, normal equation, polynomial, Ridge/Lasso | Reference §6 has a **"through-line" intuition box** (curves → overfit → regularize). StatQuest regularization trilogy + CS229 §9.1 pinned. |
| **L05** | logistic regression | sigmoid → decision boundary → cross-entropy from MLE → gradient → regularized LR |
| **L06** | gradient descent | the optimizer for L03–L05; CS229 §1.1 (LMS) is the on-scope GD source |
| **L07** | perceptron, kernel trick, multi-class | Built KW 27. **No SVM** (slide-verified). Bonus solution = Blatt 4 (Aufg. 1–2 = L07; Aufg. 3–4 = L08 preview, already solved). Kernel book layer = CS229 Ch 5 (only kernels-without-SVM source). |

**Not yet built:** **L01** (intro — mostly ML-setup material already woven into L02) and **L08–L11** (NNs, CNNs, RNNs). No mock exams/exercise banks for those yet — but the book layer for all of them is already in the L02–L10 crosswalk, and Blatt-4 Aufg. 3–4 (L08 scope) are pre-solved in the L07 folder.

### SaD
- **L11 (instance-based / k-NN)** — **full standalone reference** built: `Plans/Math/sad/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` (covers the whole 126-slide lecture: stats→ML, four ML families, k-NN, *Vektorisierung*, similarity/distance measures, scaling, over/underfitting, the full evaluation toolkit; + self-test + scope-split map to AML L02). **No mock exam / exercise bank yet** (offered, not done).
- **Probability/inference half (06–10)** — has `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md`. No per-lecture unit sheets yet.
- **L12–L15** (clustering, trees/similarity, neural nets) — not built.

### Cross-cutting (done)
- **`AML_Book-Concept-Crosswalk_L02-L10.md`** — every L02–L10 concept → exact section/page in **7 sources** (ISLP, ESL, Murphy, Toronto, Kroese, MML, **CS229 notes**), with in-scope / optional-depth / beyond-scope flags. **Extended to L07–L10 in KW 27** (slide decks pdftotext-verified; L11 preliminary map included). Key findings: real **GD** sources are only Murphy Ch 8, MML Ch 7, CS229 §1.1; **kernels-without-SVM only in CS229 Ch 5**; **double descent only in ISLP §10.8 + CS229 §8.2**; **computation graphs only in Murphy §13.3.4**; **CNNs only in ISLP §10.3 + Murphy Ch 14**.
- **`LEARNING-RESOURCES.md`** — fully reconciled with local material; AML course spine declared; famous blogs (Domingos, Fortmann-Roe, CS231n, distill, Setosa) added; CS4780 + 7 MIT "grasp ML" courses saved as general-ML/for-later; CS229 notes added.

---

## 6. Gotchas (real mistakes already made & fixed — don't repeat)

- **AML exercise filenames ≠ sheet order.** `Übung 06 .pdf` contains the **3rd** Übungsblatt (Logistic Regression); `Übung 02` = sheet 1 (k-NN); `Übung 04` = sheet 2 (Linear/Non-linear/Regularization). Confirm by opening, not by filename number.
- **SaD L11 = `Plans/Math/sad/SaD/SaD-2025/11_instance-based.pdf` (126 pp)** — NOT the misleadingly-named `Lecture-slides/13_similarity_based.pdf` (32 pp, a different/shorter deck).
- **MIT 6.034 quizzes are question-only** (no answer keys on OCW).
- **CS4780 videos can't be cherry-picked** (linear regression is lecture ~17, built on MLE/MAP) — use its self-contained *written notes* instead.
- Always re-read a mini-plan/reference section before editing (file-state), and keep the per-section `[Source: …]` citations intact.

---

## 7. Open threads / offered-but-not-done (good next steps)

- **SaD L11**: build a mock exam + exercise bank (to match the AML unit treatment) for the SaD Klausur.
- **AML L01**: decide whether it needs its own unit or stays folded into L02.
- ~~**AML L07**~~ ✅ **done KW 27** (`AML/my notes/lect07 linear classifiers/` — full 5-doc unit incl. Blatt-4 solution). **Next: L08 → L09 → L10** at the same depth (user decision KW 27: full 4-doc template for all). L08 can reuse Blatt-4 Aufg. 3–4 solutions from the L07 folder.
- ~~**Crosswalk**: extend `AML_Book-Concept-Crosswalk` to L07+~~ ✅ **done KW 27** (`AML_Book-Concept-Crosswalk_L02-L10.md`; old L02-L06 file is a redirect stub). Finalize the L11 map when the 2026 RNN deck is posted.
- ~~**CS229 2022 lecture numbering**~~ ✅ **resolved KW 27 (Jul 2):** full verified lecture⇄AML map lives in the crosswalk's 🎥 video layer (L2 LMS→L03/L06, L3 logistic→L05, L4 GLM→L05, L7 kernels→L07, L8/L9 NN→L08/L09, L10 bias-var/reg→L02/L04/L09). ⚠️ Also corrected: the 2022 playlist = **Ma & Ré**, not Ng (Ng = 2018 mirror). Mini-plans may still cite Coursera titles — fine, they're Ng-taught and verified by title.
- **SaD per-lecture sheets**: give SaD 06–10 and L12+ the same own-sheet treatment as L11 if desired.

---

## 8. Memory pointers (persistent context already saved)

`aram-profile`, `semester-brain-workflow`, `semester-key-deadlines`, `aml-sad-master-wiring`, `foundations-bridge-docs`, `reading-suggestions-scope-to-lecture`, `sad-l11-instance-based-split`. The MEMORY index loads these each session.
