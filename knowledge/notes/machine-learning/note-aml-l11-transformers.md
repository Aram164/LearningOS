---
id: note-aml-l11-transformers
type: note
title: "AML L11 — Ultimate Reference: Transformers (Embeddings, Attention, Language Modelling)"
created: "2026-08-15"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-transformer, concept-attention, concept-contextual-embedding,
  concept-embedding, concept-tokenization, concept-positional-encoding,
  concept-layer-normalization, concept-residual-connection,
  concept-language-modelling, concept-softmax]
sources: [source-aml-ss26-lectures, source-jurafsky-slp3]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator directly from the current
> 2026 deck `lecture-slides/VL 11-transformers.pdf` (81 pages), page-anchored
> throughout. Companions: `note-aml-l11-exercise-bank`, `note-aml-l11-mock-exam`.
> `authorship: operator-drafted` — **not yet Aram's synthesis**; becomes `mixed` when he
> works it. Slide-traceable but unverified-by-learner.

# AML Lecture 11 — Ultimate Reference: Transformers

*Built from `VL 11-transformers.pdf`, 81 pages.*

> ⚠️ **Scope correction (slide-verified 2026-08-15).** This deck was missing from
> the local archive until today, and the repository recorded L11 as *"not
> buildable, no current 2026 deck, must not become exam scope."* Both halves of
> that are now wrong:
>
> 1. **L11 is confirmed exam scope.** `exercise-slides/Übung 10.pdf` sl. 3 gives
>    the lecturer's own Themen list, 11 items, ending **"11. Transformers."**
> 2. **L11 is Transformers, not RNNs.** The prior-year
>    `older-lecture-slides/11-rnn_*.pdf` has been *replaced*, not supplemented.
>    There is **no RNN/LSTM/GRU content in the 2026 course.** Do not study the
>    old deck for this exam.
>
> 🚨 **This lecture has zero tutorial coverage.** The Übung series ends at
> Übung 11 (CNNs, 2026-07-14); this deck is dated 2026-07-17. Every other lecture
> was drilled in a Besprechung — this one never was. There are no lecturer-worked
> transformer problems anywhere in the course materials, which is exactly why
> `note-aml-l11-exercise-bank` and `note-aml-l11-mock-exam` matter more here than
> for any other lecture.
>
> 📐 **Two-pass construction.** The deck builds attention *twice*: a deliberately
> simplified version (sl. 27–34) and then the real QKV head (sl. 40–44), using
> **the same running example** so the two can be compared line by line. Learn it
> in that order — the simplification is not a throwaway, it is the scaffold.

---

## 1. Why sequences — the language-modelling frame (sl. 2–11)

A **language model** models the probability `p(x₁, …, xₙ)` of observing a
sequence of words (sl. 4). The deck's motivating contrast (sl. 5):

| Sequence | Probability |
|---|---|
| "today is a great day" | likely |
| "great day today is a" | unlikely |
| "today a great day is" | unlikely |

**Key move:** a model that knows which word sequences are likely can *also
predict the next word*. That converts modelling into prediction.

**Next-token prediction (sl. 6).** Goal: find `h_θ(x_{<t})` such that

$$h_\theta(x_{<t}) = p(x_t \mid x_1, \ldots, x_{t-1})$$

i.e. observe all words up to `t−1`, predict `x_t`. The deck's running example is
the prefix *"Adidas Evo 3"* (sl. 6–8), with a vocabulary of ~10,000–100,000
tokens and a next-token distribution like `steht` 80%, `ist` 5%, `wurde` 4%,
`kombiniert` 1%, … `explodiert` 0.00001%. Extend the prefix to *"Adidas Evo 3
steht"* and the distribution shifts (`für` 35%, …) — **the next token is chosen
depending on the prefix** (sl. 8).

**Consequences the deck states explicitly (sl. 9):** the process is
**non-deterministic** — the same prompt can yield different continuations.
ChatGPT is presented as exactly this: a large language model applying next-token
prediction (sl. 10).

**Scale (sl. 11).** Modern networks are transformers with thousands of billions
of weights — Mistral 7B (7.3B, 2023), Llama 3.1 (405B, 2024), etc.

---

## 2. Words vs tokens (sl. 13–15)

**Tokenization** splits text into units; the **vocabulary** assigns each unit a
unique integer ID (sl. 13).

**Why word-level fails (sl. 13–14):**

- different forms (`run`, `runs`, `running`) become separate words;
- natural language has an open vocabulary — new words keep appearing;
- the vocabulary simply explodes.

The corpus table (sl. 14, from Jurafsky & Martin):

| Corpus | Types \|V\| | Instances N |
|---|---|---|
| Shakespeare | 31 thousand | 884,000 |
| Brown Corpus | 38 thousand | 1 million |
| Switchboard conversations | 20 thousand | 2.4 million |
| COCA | 2 million | 440 million |
| Google N-grams | 13+ million | 1 trillion |

- **Types |V|** = vocabulary size · **Instances N** = number of used words.

**Solution: subwords / tokens** (sl. 15). Far fewer unique subwords are needed to
build all words. Calibration number: **GPT-4 — a 750-word input ≈ 1,000 tokens.**

---

## 3. Architecture overview (sl. 17–18)

The transformer is *the* default architecture for LLMs, built on
**self-attention** (a.k.a. multi-head attention), which lets the model learn how
tokens relate to one another (sl. 17).

**Three major components (sl. 18) — memorize this triple:**

1. **Input encoding** — embedding + positional encoding
2. **(Stack of) transformer blocks** — the multilayer network
3. **Output head** — i.e. the language-modelling head

---

## 4. Embeddings: static → contextual (sl. 19–22)

**Embedding (sl. 19).** A vector representation of an object — maps an object
(image, word, token) to a high-dimensional vector `x ∈ ℝ^d`, typically
**100–1,000+ dimensions**. Embeddings let us *compute* with objects (the deck's
picture: Adidas / Puma / NIKE landing near each other).

**One-hot encoding (sl. 20)** — the simplest embedding: each token has a fixed
position in the vocabulary; set that index to 1, everything else 0.

**The problem (sl. 21): embeddings are static.** Context-independent — `chicken`
always maps to the same fixed vector. Consider:

> The chicken didn't cross the road because **it** …

What does *it* refer to? Unanswerable from a static vector.

**Contextual embedding (sl. 22).** Now compare two completions:

1. The chicken didn't cross the road because **it** was too **tired**. → *it* = chicken
2. The chicken didn't cross the road because **it** was too **wide**. → *it* = road

Same word, same static embedding, different referent. **Goal: a word should have
a different vector representation depending on its surrounding words.**

> 🎯 This slide pair is the single best exam-answer template for *"why do we need
> contextual embeddings?"* — one sentence, two completions, different referents.

---

## 5. Attention, pass 1 — the simplified version (sl. 24–34)

**Definition (sl. 24).** Attention is the mechanism that relates
(contextualizes) tokens to one another by **weighting and combining their
representations**.

- **Input:** token embeddings `x₁, …, x_t`
- **Output:** contextualized representations `a₁, …, a_t`

**The simplified mechanism (sl. 28–29).** Given `x_j ∈ ℝ^d`, produce `a_t ∈ ℝ^d`
as a weighted sum over all `j ≤ t`:

$$\text{score}(x_t, x_j) = x_t^{\mathsf T} x_j
\qquad
\alpha_{tj} = \operatorname{softmax}\big(\text{score}(x_t, x_j)\big)\ \forall j \le t
\qquad
a_t = \sum_{j \le t} \alpha_{tj}\, x_j$$

with `α_tj ∈ [0…1]` a scalar weight.

> ⚠️ The deck flags this as **"not the actual attention mechanism"** (sl. 27) — a
> simplification that gets extended in §7. Two things are already true and stay
> true: similarity is a **dot product**, weights are **softmax-normalized**, and
> the sum runs over `j ≤ t` only (**never the future**).

**Step 1 — similarity by dot product (sl. 30):** larger dot product = more
similar.

**Step 2 — softmax normalization (sl. 30):** makes all weights positive and sum
to 1.

### The worked example — "The quick brown …" (sl. 32–34)

Using **one-hot encodings**, `x_the = [1 0 0 …]`, `x_quick = [0 1 0 …]`,
`x_brown = [0 0 1 0 …]`, the score has a degenerate form (sl. 32):

$$\text{score}(x_i, x_j) = x_i^{\mathsf T} x_j = \begin{cases} 1 & i = j \\ 0 & i \ne j \\ -\infty\ (\text{masked}) & j > i \end{cases}$$

**Problem the deck names explicitly:** one-hot tokens are only similar to
themselves. (This is precisely what the learned `W_Q`/`W_K` fix in pass 2.)

**Softmax is computed row-wise** (sl. 33), with `e¹ ≈ 2.718` and `e⁰ = 1`:

- Row for the 2-token prefix *"The quick"*:
  `softmax = e¹ / (e⁰ + e¹) = 2.718 / 3.718 = 0.27`
- Row for the 3-token prefix *"The quick brown"*:
  `e⁰ / (e⁰ + e⁰ + e¹) = 1 / 4.718 = 0.21` and
  `e¹ / 4.718 = 0.58`

**Output for "brown" (sl. 34):**

$$a_3 = \sum_{j \le 3} \alpha_{3j} x_j = 0.21\,x_{\text{the}} + 0.21\,x_{\text{quick}} + 0.58\,x_{\text{brown}} = [0.21\ 0.21\ 0.58\ 0\ \ldots]$$

> 💡 Read the output in words, the way the deck does: *the representation of
> "brown" is composed of **21%** information from "the", **21%** from "quick",
> and **58%** from "brown."* That sentence is the whole idea of attention.

---

## 6. The embedding matrix (sl. 36–38)

- Input tokens become one-hot vectors of shape `ℝ^{N×|V|}`.
- **Embedding matrix `E`** maps each token to its embedding; shape `ℝ^{|V|×d}`
  for output dimension `d`.
- Multiplying the one-hot vector by `E` is a **lookup** implemented as a
  matrix–vector product (sl. 37, example token *"Thanks"*).
- For an N-token sequence, the same product runs row-wise (sl. 38).

> 🔗 Remember `E` — it comes back at sl. 61 as the *language-modelling head*, and
> the reuse is the exam-worthy detail.

---

## 7. Attention, pass 2 — the real single head (sl. 40–44)

**Three roles per token (sl. 40):**

| Role | Meaning |
|---|---|
| **Query** | the current element, compared to preceding inputs |
| **Key** | a preceding input, used to determine the similarity weight |
| **Value** | the value of a preceding element, summed into the output |

**Projections (sl. 41–42).** Each token vector `x_i ∈ ℝ^{1×d}` is projected into
its three roles:

$$q_i = x_i W_Q \in \mathbb{R}^{d_k}
\qquad
k_i = x_i W_K \in \mathbb{R}^{d_k}
\qquad
v_i = x_i W_V \in \mathbb{R}^{d_v}$$

with `W_Q, W_K ∈ ℝ^{d×d_k}`, `W_V ∈ ℝ^{d×d_v}`, and an **output matrix**
`W_O ∈ ℝ^{d_v×d}`.

**Deck defaults (sl. 42): `d = 512`, `d_k = d_v = 64`.**

**The head (sl. 42):**

$$\text{score}(x_t, x_j) = \frac{q_t \cdot k_j}{\sqrt{d_k}}
\qquad
\alpha_{tj} = \operatorname{softmax}\big(\text{score}(x_t,x_j)\big)\ \forall j \le t$$
$$\text{head}_t = \sum_{j \le t} \alpha_{tj}\, v_j
\qquad
a_t = \text{head}_t\, W_O$$

This is **self-attention**.

**What changed from pass 1 — the four differences worth stating in an exam:**

1. similarity is computed between **learned projections** `q_t · k_j`, not raw `x_t · x_j`;
2. the score is **scaled by `1/√d_k`**;
3. the weighted sum runs over **values `v_j`**, not raw `x_j`;
4. an **output projection `W_O`** maps `d_v` back to `d`.

**Same example, real head (sl. 43–44):** attention output for *"brown"* becomes

$$a_3 = 0.10\,v_1 + 0.19\,v_2 + 0.71\,v_3$$

— 10% from "the", 19% from "quick", 71% from "brown". Compare to `0.21 / 0.21 /
0.58` in pass 1: **the learned projections sharpen the distribution.**

### Multi-head attention (sl. 46)

Use `A` many heads. Heads may specialize to different linguistic relationships.
Each head `c` has its **own** matrices `W_Q^c, W_K^c, W_V^c`:

$$q_i^c = x_i W_Q^c, \quad k_i^c = x_i W_K^c, \quad v_i^c = x_i W_V^c \qquad \forall\, 1 \le c \le A$$

Attention is computed per head and the results combined.

### Positional embeddings (sl. 48)

**Token embeddings are not position-dependent.** Fix: add an embedding of the
position. With `x_t ∈ ℝ^d` the token embedding at position `t` and `p_t ∈ ℝ^d` a
positional embedding:

$$x_t \leftarrow x_t + p_t$$

> ⚠️ Common exam trap: attention as defined is **permutation-invariant over the
> unmasked positions** — without `p_t`, "dog bites man" and "man bites dog" have
> identical representations. Say *why* the addition is needed, not just that it
> happens.

### Complexity (sl. 49) — a favourite exam number

Self-attention compares **every token with every other token**, so computation
and memory grow **quadratically in sequence length: O(n²)**.

Worked example, `n = 100,000` tokens, **one** attention head:

- matrix size `n × n = 100,000²` = 10¹⁰ entries
- **FP32 (4 bytes): 37.4 GiB**
- **FP16 (2 bytes): 18.6 GiB**

### Key takeaways (sl. 50 — near-verbatim)

- Attention enriches token representations with contextual information by
  computing a weighted sum of the representations of other relevant tokens.
- Attention weights determine how much each token contributes to the
  representation of the current token.
- The resulting token embedding becomes **context-dependent**.
- Transformers use **multi-head self-attention** to model relationships between
  all tokens in a sequence.

---

## 8. The transformer block (sl. 52–58)

**Three layers (sl. 52):**

1. multi-head self-attention
2. feedforward layer
3. residual connections and layer normalization

Each component updates the token representation while **preserving information
via residual connections**.

**Feedforward layer (sl. 53)** — a fully-connected 2-layer network (one hidden +
one output layer):

$$\mathrm{FFN}(x) = W_2\,\mathrm{ReLU}(W_1 x + b_1) + b_2$$

`W₁, W₂, b₁, b₂` are learnable, and — the detail that gets asked — **the same
weights are used for all token positions.**

**Layer normalization (sl. 54).** For each token embedding `x ∈ ℝ^d`, normalize
**across its `d` features**:

$$\mu = \frac{1}{d}\sum_{i=1}^{d} x_i
\qquad
\sigma = \sqrt{\frac{1}{d}\sum_{i=1}^{d}(x_i - \mu)^2}
\qquad
\mathrm{LayerNorm}(x) = \gamma\,\frac{x - \mu}{\sigma} + \beta$$

`γ` and `β` are learnable. **LayerNorm is applied twice within a block.**

**The block, combined (sl. 55)** — memorize the six lines:

$$\begin{aligned}
t^1_i &= \mathrm{LayerNorm}(x_i) \\
t^2_i &= \mathrm{MultiHeadAttention}(t^1_i,\, t^1_{i-w+1}, \ldots, t^1_{i-1}) \\
t^3_i &= t^2_i + x_i \\
t^4_i &= \mathrm{LayerNorm}(t^3_i) \\
t^5_i &= \mathrm{FFN}(t^4_i) \\
h_i &= t^5_i + t^3_i
\end{aligned}$$

with `w` the window size. **Only the attention block takes information from
other streams** — everything else is per-token.

> 📌 Note the ordering: LayerNorm comes **before** each sublayer (pre-LN), and
> lines 3 and 6 are the two residual additions. Both are easy marks and easy to
> get backwards.

**Context window (sl. 56).** Attention heads move information between
neighbouring token streams; the maximum number of tokens that can interact
through attention is the **context window**. Common values **N = 1k to 128k**.

**Stacking (sl. 57–58).** A transformer is a stack of *identical* blocks.
**GPT-3 (175B) = 96 sequential transformer blocks.** Stacking is what enables
complex language understanding. Reference table (sl. 58):

| Model | Year | Parameters | Blocks |
|---|---|---|---|
| GPT-3 | 2020 | 175B | 96 |
| Llama 2 70B | 2023 | 70B | 80 |
| Llama 3.1 70B | 2024 | 70B | 80 |
| Llama 3.1 405B | 2024 | 405B | 126 |
| Mistral Large 2 | 2024 | 123B | 88 |
| DeepSeek-V3 | 2024 | 671B (37B active) | 61 |
| Llama 4 Maverick | 2025 | 400B (17B active) | 48 |

---

## 9. Language modelling head (sl. 60–62)

**Training objective:** predict the next token given previous tokens — learn
`h_θ(x_{<t}) ≈ p(x_t | x₁,…,x_{t−1})` (sl. 60).

Input pipeline: **tokenization** (text → token IDs) → **embedding lookup**
(IDs → vectors) → blocks.

**The head (sl. 61–62):** the **same weight matrix `E`** used for the input
embedding is **reused** to project the final output representation back into
vocabulary space, producing a vector of dimensionality `1 × |V|`. One score per
vocabulary token; **softmax** converts scores to probabilities.

> 🔗 **Weight tying.** `E` is used twice — once as lookup (`|V| → d`), once
> transposed as the output projection (`d → |V|`). If asked "how many parameters
> does the output head add?", the answer is *none beyond `E`*.

---

## 10. Training (sl. 64–69)

**Conceptually (sl. 64):**

1. Collect a large text corpus (books, Wikipedia, web pages, code); split the
   token stream into training sequences.
2. Predict the next token **at every position** in each sequence.
3. Compute the **cross-entropy loss**.
4. Update the weights.

> 🔗 **Cross-wire to L05.** This is the same cross-entropy derived from maximum
> likelihood in the logistic-regression lecture — Bernoulli there, categorical
> over `|V|` here. Same engine, wider output.

**Role of human feedback (sl. 65).** Training only by next-token prediction makes
the model imitate the corpus's statistical patterns; it **does not differentiate
good from bad**:

- *Good:* factual knowledge, different writing styles
- *Bad:* biases, stereotypes, offensive language, misinformation

So humans are integrated into the training process. The deck's number:
**about 10–20% of final LLM performance is attributed to human intervention.**

**Crowdworkers (sl. 66–69).** Content review and evaluation is done by crowd- and
clickworkers (the deck links the TIME report on Kenyan workers). A knock-on
effect: African click workers prefer certain phrasings, which the models then
overuse — *"delve", "explore", "captivate", "tapestry", "leverage", "embrace",
"resonate", "dynamic"*. Analysing phrase frequency therefore lets you infer AI
use (sl. 69, the MP/ChatGPT analysis).

> This is the deck's ethics/society segment. It is short, concrete, and exactly
> the kind of material that shows up as a 2–4 point short-answer question.

**Conclusion (sl. 70).** Attention lets networks focus on the most relevant parts
of the input · transformers use self-attention for context-dependent
representations · pre-training via next-token prediction learns language from
massive corpora · fine-tuning/human feedback follows.

**Further reading (sl. 72):** Jurafsky & Martin, *Speech and Language
Processing*, **Chapter 8: Transformers** — `source-jurafsky-slp3`.

---

## 11. BONUS — parallelization (sl. 73–81)

> ⚠️ **Scope status ambiguous.** The agenda labels this section **"Bonus"**, yet
> it contains the canonical matrix formulation and causal masking that most
> courses examine directly. Treat as **learn-anyway, low-cost** — it is four
> formulas and one picture, and it makes §5/§7 easier to hold, not harder.

**Training vs inference (sl. 74):**

| | Behaviour |
|---|---|
| **Training** | entire input sequence known → all token embeddings processed simultaneously → highly parallelizable on GPUs |
| **Inference (generation)** | future tokens must be generated one at a time; each new token requires another pass |

**Matrix form (sl. 76–77).** Compute three matrices at once:

$$Q = XW_Q, \qquad K = XW_K, \qquad V = XW_V$$

then

$$A = \operatorname{softmax}\!\left(\operatorname{mask}\!\left(\frac{QK^{\mathsf T}}{\sqrt{d_k}}\right)\right) V$$

`QKᵀ` is the matrix of pairwise dot products between query and key vectors.

**Masking the future (sl. 79–80).** Add `−∞` to the cells in the **upper
triangle**; softmax turns these into `e^{−∞} ≈ 0`:

$$\begin{pmatrix}
q_1^{\mathsf T}k_1 & -\infty & -\infty & -\infty \\
q_2^{\mathsf T}k_1 & q_2^{\mathsf T}k_2 & -\infty & -\infty \\
q_3^{\mathsf T}k_1 & q_3^{\mathsf T}k_2 & q_3^{\mathsf T}k_3 & -\infty \\
q_4^{\mathsf T}k_1 & q_4^{\mathsf T}k_2 & q_4^{\mathsf T}k_3 & q_4^{\mathsf T}k_4
\end{pmatrix}$$

**Why mask?** `QKᵀ` contains dot products for tokens that *follow* the query, but
only preceding tokens are allowed. The deck's rationale, worth quoting:
**"guessing a next word becomes simple, if you know it."**

Attention remains quadratic in sequence length and bounded by the context window
(sl. 79).

---

## 12. Cross-wires into the rest of the course

| From L11 | Wires to | The connection |
|---|---|---|
| Softmax over attention scores | **L08** | same softmax as the classification output layer |
| FFN inside the block | **L08** | it *is* the two-layer MLP, weights shared across positions |
| Residual connections | **L10** | L10 closes on residuals (ResNet); L11 reuses them per block |
| Cross-entropy training loss | **L05** | same MLE→cross-entropy engine, categorical instead of Bernoulli |
| Training by gradient updates | **L06/L09** | Adam + backprop through the stack |
| Sequence modelling | **prior-year L11 (RNN)** | *superseded* — contrast only, not scope |
| Embeddings / vector similarity | **Übung 02** | k-NN search with vector embeddings — the same `ℝ^d` similarity idea |

---

## 13. Exam-format facts (from `exercise-slides/Übung 10.pdf`, sl. 2)

Recorded here because this Übung is the only place the lecturer states them.

- **Zulassung:** 21 points (50% of 42 possible across the 4 Übungsblätter)
- **Allowed aids:** one **double-sided handwritten A4 sheet**, calculator (stated
  as not necessary), pen, possibly a ruler for drawing decision boundaries
- **Bring:** official photo ID, CampusCard
- **1. Termin was:** Mi 22.07., ESZ 0'115, entry 15:00, start 15:20, **120 minutes**

> ⚠️ These are the **1. Termin** figures. The 2. Termin sitting is recorded in
> `curriculum/modules/module-hu-aml/module.yaml` and its listed slot is longer
> than 120 minutes — **do not assume the duration carries over.** The cheat-sheet
> rule is the one worth acting on now: build the A4 sheet as you study, not the
> night before.

---

## 14. The eleven Themen (Übung 10 sl. 3, verbatim order)

> "Themen (without Claim to Completeness)"

1. Introduction: What is ML
2. Nearest Neighbour, Bias, Variance and Generalization
3. Linear Regression with one Predictor Variable
4. (Non-Linear) Regression, Regularization
5. Logistic Regression
6. Gradient Descent, Adam
7. Linear Classifiers (Perceptron, Kernel-Perceptron)
8. Fully Connected (Feed Forward) Neural Networks
9. Training (Backpropagation)
10. Convolutional Neural Networks
11. **Transformers**

**One lecture, one Thema, one unit note — the mapping is exact.** The repository
now has a reference note, exercise bank and mock exam for L02–L11, i.e. Themen
2–11. Thema 1 (Introduction) has no unit and needs none.
