---
id: note-aml-l11-mock-exam
type: note
title: "AML L11 — Mock Exam (Transformers)"
created: "2026-08-15"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-transformer, concept-attention, concept-contextual-embedding,
  concept-embedding, concept-tokenization, concept-positional-encoding,
  concept-layer-normalization, concept-residual-connection,
  concept-language-modelling, concept-softmax]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from `VL 11-transformers.pdf`.
> Companion: `note-aml-l11-transformers` (§ refs in the key). `authorship: operator-drafted`
> — key operator-computed, **unverified by Aram**. Difficulty at or above the real
> exam by design.

# AML Lecture 11 — Mock Exam (Transformers)

**Topic:** language modelling and next-token prediction, tokenization, static vs
contextual embeddings, the embedding matrix, simplified and real attention,
multi-head attention, positional embeddings, O(n²) complexity, the transformer
block, stacking, the LM head, training and human feedback, and the bonus matrix
form with causal masking.
**Companion:** `note-aml-l11-transformers` (§ refs in the key).
**Suggested time:** 75 minutes, closed-book.

> **Scoring:** Part A = 20 (2 each) · Part B = 30 · Part C = 25 · Part D = 25.
> **Total 100.**
>
> ✍️ **Do this one with your A4 cheat sheet in hand** — the real exam allows one
> double-sided handwritten sheet (`Übung 10` sl. 2). Use this mock to find out
> what actually needs to be on it. My prediction: the six block equations,
> LayerNorm, the QKV shapes, and the masked-softmax formula. Verify that
> prediction rather than trusting it.
>
> ⚠️ **No RNN content is examined.** Encoder–decoder cross-attention, BERT-style
> masked LM, and sinusoidal/rotary position encodings are **not** in this deck —
> if you find yourself wanting them, you have drifted out of scope.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** State what a language model models, and give the deck's formula.

**A2.** Give the three major components of the transformer architecture.

**A3.** Why does word-level tokenization fail? Give two reasons and one number
from the corpus table.

**A4.** Define a contextual embedding, and give the minimal pair the deck uses to
motivate it.

**A5.** Name the three roles a single attention head assigns to tokens, and say
what each is *for*.

**A6.** Why must a positional embedding be added?

**A7.** What is the context window, and what range does the deck give?

**A8.** LayerNorm normalizes across *what*? Name the two learnable parameters.

**A9.** How many times is LayerNorm applied within one transformer block, and
where relative to the sublayers?

**A10.** Why is next-token prediction alone insufficient for a deployed
assistant?

---

## Part B — Attention by Hand (30 pts)

**B1 (12 pts).** Simplified attention over the prefix *"The quick brown"* with
one-hot embeddings.

(a) Write `score(xᵢ, xⱼ)` for one-hot inputs and state its three cases. **(3)**
(b) Compute the softmax weights for `t = 3` using `e¹ ≈ 2.718`, `e⁰ = 1`. **(4)**
(c) Compute `a₃` and state the result as percentages in words. **(3)**
(d) The deck calls the one-hot score a *problem*. Say why, and name the
mechanism in the real head that removes it. **(2)**

**B2 (10 pts).** The real single head.

(a) Write the four equations of the head: `qᵢ`, `kᵢ`, `vᵢ`, and `score`. **(4)**
(b) With `d = 512`, `d_k = d_v = 64`, give the shapes of `W_Q`, `W_V`, `W_O` and
of `aₜ`. **(4)**
(c) Why must `aₜ` come back out at width `d`? **(2)**

**B3 (8 pts).** Complexity.

(a) State the time/memory complexity of self-attention in the sequence length and
justify it in one sentence. **(3)**
(b) For `n = 100,000` and one head, compute the attention-matrix memory in FP32
and in FP16. **(4)**
(c) Name the architectural quantity that bounds `n` in practice. **(1)**

---

## Part C — The Block (25 pts)

**C1 (10 pts).** Write the six equations of the transformer block, in order,
labelling the two residual additions.

**C2 (5 pts).** Write `FFN(x)`. State which parameters are shared across token
positions and which are not, and why that matters for parameter count.

**C3 (5 pts).** Write `LayerNorm(x)` in full, including `μ` and `σ`.

**C4 (5 pts).** The deck says *"only the attention block takes information from
other streams."* Explain what that means operationally, and what it implies about
which sublayer you could compute independently per token.

---

## Part D — Language Modelling, Training, Bonus (25 pts)

**D1 (6 pts).** The language-modelling head. Which matrix is reused, what output
dimensionality does it produce, and what converts that output to probabilities?
Why is "reused" the interesting word?

**D2 (6 pts).** List the four steps of training a language model as the deck
gives them, and name the loss.

**D3 (5 pts).** Human feedback: why is it needed, and what share of final LLM
performance does the deck attribute to human intervention?

**D4 (8 pts) — bonus section.**
(a) Write the parallel attention formula `A = …` and name each factor. **(4)**
(b) Which triangle of `QKᵀ` is masked, with what value, and why that value rather
than 0? **(3)**
(c) Give the one-sentence reason training parallelizes but generation does not. **(1)**

---
---

# Solutions

## Part A

**A1.** A language model models the probability `p(x₁, …, xₙ)` of observing a
sequence of words. *(§1)*

**A2.** (1) Input encoding = embedding + positional encoding; (2) a stack of
transformer blocks; (3) the output head, i.e. the language-modelling head. *(§3)*

**A3.** Any two of: different forms (`run`/`runs`/`running`) are treated as
separate words; natural language is open-vocabulary so new words keep appearing;
the vocabulary explodes. Number: e.g. Google N-grams **13+ million types** over 1
trillion instances; COCA 2 million types / 440 million instances. *(§2)*

**A4.** A representation of a token that **depends on its surrounding words**,
rather than a single fixed vector per token. Minimal pair: *"The chicken didn't
cross the road because **it** was too **tired**"* (it = chicken) vs *"… too
**wide**"* (it = road). *(§4)*

**A5.** **Query** — the current element, compared against preceding inputs.
**Key** — a preceding input, used to determine the similarity weight.
**Value** — the value of a preceding element, summed into the output. *(§7)*

**A6.** Token embeddings carry no position and attention is a weighted sum, so
without a positional term the representation is invariant to permuting the
unmasked inputs — "dog bites man" and "man bites dog" would be identical. Fix:
`xₜ ← xₜ + pₜ`. *(§7)*

**A7.** The maximum number of tokens that can interact through attention. Deck
range: **N = 1k to 128k**. *(§8)*

**A8.** Across the **`d` features of a single token embedding** (not across the
batch, not across the sequence). Learnable parameters **γ** and **β**. *(§8)*

**A9.** **Twice**, and **before** each sublayer — pre-LN: once before multi-head
attention, once before the FFN. *(§8)*

**A10.** It only teaches imitation of the corpus's statistical patterns and does
not distinguish good from bad — it absorbs facts and styles but equally biases,
stereotypes, offensive language and misinformation. *(§10)*

## Part B

**B1.**
(a) `score(xᵢ,xⱼ) = xᵢᵀxⱼ = 1` if `i = j`, `0` if `i ≠ j` (and masked/`−∞` for
`j > i`). **(3)**
(b) Scores `(0,0,1)`; denominator `e⁰+e⁰+e¹ = 1+1+2.718 = 4.718`;
`α = (1/4.718, 1/4.718, 2.718/4.718) = (0.21, 0.21, 0.58)`. **(4)**
(c) `a₃ = 0.21·x_the + 0.21·x_quick + 0.58·x_brown = [0.21 0.21 0.58 0 … 0]` —
"brown" is **21% "the", 21% "quick", 58% "brown"**. **(3)**
(d) One-hot tokens are only similar to themselves, so the scores carry no
information about relatedness between different words. The learned projections
`W_Q`, `W_K` (`q = xW_Q`, `k = xW_K`) remove this: similarity is computed in a
learned space, not the identity space. **(2)** *(§5, §7)*

**B2.**
(a) `qᵢ = xᵢW_Q`, `kᵢ = xᵢW_K`, `vᵢ = xᵢW_V`,
`score(xₜ,xⱼ) = (qₜ·kⱼ)/√d_k`. **(4)**
(b) `W_Q ∈ ℝ^{512×64}`, `W_V ∈ ℝ^{512×64}`, `W_O ∈ ℝ^{64×512}`,
`aₜ ∈ ℝ^{512}`. **(4)**
(c) Because `aₜ` is added to `xᵢ` by the residual connection and passed to the
next block — the token stream must keep width `d` for the addition to be
defined. **(2)** *(§7, §8)*

**B3.**
(a) **O(n²)**: self-attention compares every token with every other token, so the
score matrix has `n²` entries. **(3)**
(b) `n×n = 10¹⁰` entries. FP32: `4×10¹⁰ B ≈ **37.4 GiB**`. FP16: `2×10¹⁰ B ≈
**18.6 GiB**`. **(4)**
(c) The **context window**. **(1)** *(§7, §8)*

## Part C

**C1 (10 pts).**
`t¹ᵢ = LayerNorm(xᵢ)`
`t²ᵢ = MultiHeadAttention(t¹ᵢ, t¹_{i−w+1}, …, t¹_{i−1})`
`t³ᵢ = t²ᵢ + xᵢ`  ← **residual 1** (around attention)
`t⁴ᵢ = LayerNorm(t³ᵢ)`
`t⁵ᵢ = FFN(t⁴ᵢ)`
`hᵢ = t⁵ᵢ + t³ᵢ`  ← **residual 2** (around the FFN)
*(§8)*

**C2 (5 pts).** `FFN(x) = W₂ ReLU(W₁x + b₁) + b₂`. **All four parameters are
shared across every token position** — nothing is position-specific. This is why
a block's FFN cost is independent of sequence length in parameters (though not in
compute), and why the parameter count scales with `d` and the hidden width, not
with `n`. *(§8)*

**C3 (5 pts).**
`μ = (1/d) Σᵢ₌₁ᵈ xᵢ`, `σ = sqrt((1/d) Σᵢ₌₁ᵈ (xᵢ − μ)²)`,
`LayerNorm(x) = γ·(x − μ)/σ + β`, with `γ, β` learnable. *(§8)*

**C4 (5 pts).** Each token has its own "stream" running up through the block;
only the attention sublayer reads from *neighbouring* streams (the `j ≤ t` terms).
LayerNorm, the FFN and both residual additions act on a single token's vector in
isolation — so the **FFN and both LayerNorms could be computed fully
independently per token**, and only attention requires the sequence. *(§8)*

## Part D

**D1 (6 pts).** The **embedding matrix `E`** is reused, projecting the final
representation back to vocabulary space to produce a vector of dimensionality
`1 × |V|`; **softmax** converts the `|V|` scores to probabilities. "Reused"
matters because the head therefore introduces **no new parameters** — the same
matrix serves as input lookup and output projection (weight tying). *(§9)*

**D2 (6 pts).** (1) Collect a large text corpus (books, Wikipedia, web pages,
code) and split the token stream into training sequences; (2) predict the next
token **at every position** in each sequence; (3) compute the **cross-entropy**
loss; (4) update the weights. *(§10)*

**D3 (5 pts).** Needed because pure next-token training cannot distinguish good
output (facts, style) from bad (bias, stereotypes, offensive language,
misinformation), while output must meet human quality standards — so humans are
integrated into training. Deck's figure: **about 10–20%** of final LLM
performance. *(§10)*

**D4 (8 pts).**
(a) `Q = XW_Q`, `K = XW_K`, `V = XW_V`;
`A = softmax(mask(QKᵀ/√d_k))V`. `QKᵀ` = pairwise query–key dot products;
`mask` blocks future positions; `softmax` normalizes row-wise; `V` supplies the
values being averaged. **(4)**
(b) The **upper triangle** (positions after the query), set to **`−∞`**, because
softmax maps `e^{−∞} ≈ 0`; using 0 before softmax would give `e⁰ = 1`, a large
weight — the opposite of what is wanted. Rationale: "guessing a next word becomes
simple, if you know it." **(3)**
(c) In training the whole sequence is known so all positions are processed
simultaneously; in generation each new token depends on the previously generated
one, forcing a pass per token. **(1)** *(§11)*

---

## Marking guidance

| Band | Total | Reading |
|---|---|---|
| Secure | ≥ 85 | Block equations and attention arithmetic are automatic — move to full-course mocks |
| Solid | 70–84 | Concepts hold; re-drill whichever of B1/B2/C1 lost points |
| Shaky | 50–69 | Redo §5 and §7 of the reference, then the whole of Part B cold |
| Not yet | < 50 | Reread the reference end to end before re-attempting; the deck is 81 slides and rewards one careful pass |

> **After this mock:** whatever you had to look up is what belongs on the A4
> sheet. Write the sheet *from your errors*, not from the slides.
