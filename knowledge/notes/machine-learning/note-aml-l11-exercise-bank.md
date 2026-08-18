---
id: note-aml-l11-exercise-bank
type: note
title: "AML L11 — Exercise Bank (Transformers)"
created: "2026-08-15"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-transformer, concept-attention, concept-contextual-embedding,
  concept-embedding, concept-tokenization, concept-positional-encoding,
  concept-layer-normalization, concept-residual-connection,
  concept-language-modelling, concept-softmax]
sources: [source-aml-ss26-lectures, source-jurafsky-slp3, source-d2l, source-eecs498]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from `VL 11-transformers.pdf`.
> Companions: `note-aml-l11-transformers` (reference), `note-aml-l11-mock-exam`.
> `authorship: operator-drafted` — solutions operator-computed, **unverified by Aram**.
> Where a solution disagrees with the deck, the deck wins.

# AML Lecture 11 — Exercise Bank (Transformers)

**Reading-scope rule:** language modelling and next-token prediction,
tokenization and vocabulary, static vs contextual embeddings, the embedding
matrix, simplified attention, the QKV attention head, multi-head attention,
positional embeddings, O(n²) complexity, the transformer block (MHA + FFN +
residual + LayerNorm), stacking, the language-modelling head, training by
cross-entropy, human feedback, and — as bonus — the matrix form with causal
masking.

> 🚨 **This is the only AML lecture with no Übung.** Every other lecture has a
> lecturer-worked Besprechung; L11 has none. There is no official worked
> transformer problem anywhere in the course. **Section 2 is therefore empty by
> necessity, and Section 3 is the whole bank** — that is a deliberate structural
> difference from L02–L10, not an omission.
>
> ⚠️ **RNNs are out of scope.** External "sequence models" problem sets are
> dominated by RNN/LSTM/BPTT. Take only the attention and transformer parts.
> Likewise, external transformer sets are dominated by encoder–decoder
> cross-attention, BERT-style masked LM, and rotary/relative position schemes —
> **none of that is in this deck.** The deck is decoder-style causal attention
> with additive positional embeddings, full stop.

---

## 1. Local material

| File | What it is | Where |
|---|---|---|
| `note-aml-l11-transformers` | Full page-anchored reference | this vault |
| `note-aml-l11-mock-exam` | 100-pt mock, worked key | this vault |
| `note-aml-l08-feedforward-networks` | The FFN inside every block; softmax output layer | this vault |
| `note-aml-l10-cnn` | Residual connections, introduced there, reused here | this vault |
| `note-aml-l05-logistic-regression` | MLE → cross-entropy, the training loss | this vault |
| `VL 11-transformers.pdf` | The deck itself, 81 sl. | `material://source-aml-ss26-lectures/lecture-slides` |
| `Übung 10.pdf` sl. 2–3 | Exam format + the 11 Themen | `material://source-aml-ss26-lectures/exercise-slides` |

## 2. Course sheets to solve

**None exist.** The Übung series ends at Übung 11 (CNNs, 2026-07-14); this deck
is dated 2026-07-17. No Übungsblatt and no Bonusblatt touches transformers.

*Practical consequence:* the exam's transformer question cannot be predicted from
past sheet style the way L02–L10 questions can. Expect it to sit close to the
slides — the deck's own worked examples (sl. 32–34, 43–44) are the most likely
templates, which is why §3.A drills them numerically rather than conceptually.

## 3. Drills

Solved items give the answer inline. Unsolved items are marked **[open]** — do
them cold, then check against the reference section named in brackets.

### A. The deck's own worked examples — do these first

**A1.** With one-hot encodings, show that `score(xᵢ, xⱼ) = xᵢᵀxⱼ` equals 1 when
`i = j` and 0 otherwise. Why does the deck call this a *problem*?

<details><summary>Solution</summary>

One-hot vectors have a single 1 at the token's vocabulary index. The dot product
of two one-hot vectors counts matching positions: 1 if the same index, 0
otherwise. **Problem (sl. 32): one-hot tokens are only similar to themselves** —
so simplified attention on one-hot inputs can express nothing about relatedness
between *different* words. Learned `W_Q`/`W_K` projections in the real head fix
exactly this. *(Ref §5.)*
</details>

**A2.** For the prefix *"The quick"*, compute the softmax attention weights by
hand using `e¹ ≈ 2.718`, `e⁰ = 1`.

<details><summary>Solution</summary>

Row for `t = 2`, scores `(0, 1)` for (the, quick):
`α_{2,the} = e⁰/(e⁰+e¹) = 1/3.718 = 0.27`,
`α_{2,quick} = e¹/3.718 = 0.73`.
The deck prints the 0.27 (sl. 33). Weights sum to 1. *(Ref §5.)*
</details>

**A3.** For *"The quick brown"*, compute the three weights, then the attention
output `a₃` under simplified attention. State the result as percentages.

<details><summary>Solution</summary>

Scores for `t = 3` are `(0, 0, 1)`. Denominator `e⁰+e⁰+e¹ = 4.718`.
`α = (1/4.718, 1/4.718, 2.718/4.718) = (0.21, 0.21, 0.58)`.

`a₃ = 0.21·x_the + 0.21·x_quick + 0.58·x_brown = [0.21 0.21 0.58 0 … 0]`.

In words: the representation of "brown" is **21% "the", 21% "quick", 58%
"brown"** (sl. 34). *(Ref §5.)*
</details>

**A4.** The real head on the same sentence gives `a₃ = 0.10·v₁ + 0.19·v₂ +
0.71·v₃`. Name every difference from A3's `0.21 / 0.21 / 0.58` and explain the
sharpening.

<details><summary>Solution</summary>

Four differences: (1) scores use learned projections `q₃·kⱼ` instead of raw
`x₃·xⱼ`; (2) scores are scaled by `1/√d_k`; (3) the sum is over **values** `vⱼ`,
not raw `xⱼ`; (4) an output projection `W_O` follows. The distribution sharpens
(0.58 → 0.71) because `W_Q`/`W_K` are trained to make relevant pairs score high —
under one-hot inputs the only "relevant" pair was self-identity, so the weight
mass was forced to spread. *(Ref §7.)*
</details>

**A5.** Compute the memory for one attention head at `n = 100,000` tokens in FP32
and FP16.

<details><summary>Solution</summary>

Matrix is `n × n = 10¹⁰` entries.
FP32: `10¹⁰ × 4 B = 4×10¹⁰ B = 4×10¹⁰ / 2³⁰ GiB ≈ **37.4 GiB**`.
FP16: half → **≈ 18.6 GiB**. Root cause: self-attention compares every token with
every other → **O(n²)** in time and memory (sl. 49). *(Ref §7.)*
</details>

**A6. [open]** Redo A3 for a 4-token prefix where the scores are `(0, 0, 0, 1)`.
Then redo it for scores `(1, 0, 1, 1)`. Which token dominates in each case?
*(Ref §5.)*

**A7. [open]** GPT-4 maps ~750 words to ~1,000 tokens. Estimate the token count
of a 3,000-word document, and explain why the ratio exceeds 1. *(Ref §2.)*

### B. Shapes and parameter counting

**B1.** With the deck defaults `d = 512`, `d_k = d_v = 64`, give the shapes of
`W_Q`, `W_K`, `W_V`, `W_O`, and of `qᵢ`, `kᵢ`, `vᵢ`, `headₜ`, `aₜ`.

<details><summary>Solution</summary>

`W_Q, W_K ∈ ℝ^{512×64}`; `W_V ∈ ℝ^{512×64}`; `W_O ∈ ℝ^{64×512}`.
`qᵢ, kᵢ ∈ ℝ^{64}`; `vᵢ ∈ ℝ^{64}`; `headₜ ∈ ℝ^{64}`; `aₜ = headₜW_O ∈ ℝ^{512}`.
The head's job is to leave the token stream at width `d` so residual addition
works. *(Ref §7.)*
</details>

**B2.** Count the parameters of one attention head with those defaults (ignore
biases). Then for `A = 8` heads.

<details><summary>Solution</summary>

Per head: `W_Q + W_K + W_V = 3 × (512×64) = 98,304`. Plus `W_O = 64×512 = 32,768`
→ **131,072** with the output matrix, 98,304 without.
For 8 heads with per-head `W_Q^c, W_K^c, W_V^c`: `8 × 98,304 = 786,432`, plus the
output projection. *(Ref §7.)*
</details>

**B3.** Give the shape of the embedding matrix `E` and of a one-hot input batch
of `N` tokens. Show the multiplication produces the right shape.

<details><summary>Solution</summary>

`E ∈ ℝ^{|V|×d}`; one-hot batch `X ∈ ℝ^{N×|V|}`; `XE ∈ ℝ^{N×d}`. Each row selects
one row of `E` — a lookup implemented as a matrix product (sl. 36–38). *(Ref §6.)*
</details>

**B4. [open]** The LM head reuses `E` to map `ℝ^d → ℝ^{|V|}`. What shape must it
be used in, and how many *new* parameters does the head introduce? *(Ref §9.)*

**B5. [open]** For `|V| = 50,000` and `d = 512`, how many parameters does `E`
hold? Compare to the 131,072 of one attention head — what does that tell you
about where a small LLM's parameters actually live? *(Ref §6, §9.)*

### C. The block

**C1.** Write the six equations of the transformer block from memory, then check
the ordering of LayerNorm and the two residual additions.

<details><summary>Solution</summary>

`t¹ᵢ = LayerNorm(xᵢ)` · `t²ᵢ = MultiHeadAttention(t¹ᵢ, t¹_{i−w+1}, …, t¹_{i−1})` ·
`t³ᵢ = t²ᵢ + xᵢ` · `t⁴ᵢ = LayerNorm(t³ᵢ)` · `t⁵ᵢ = FFN(t⁴ᵢ)` · `hᵢ = t⁵ᵢ + t³ᵢ`.

LayerNorm is applied **before** each sublayer (pre-LN) and **twice** per block.
The residual adds are lines 3 (`+xᵢ`, around attention) and 6 (`+t³ᵢ`, around the
FFN). *(Ref §8.)*
</details>

**C2.** Write `FFN(x)`. Which of its parameters differ between token positions?

<details><summary>Solution</summary>

`FFN(x) = W₂ ReLU(W₁x + b₁) + b₂`. **None differ** — the same `W₁, W₂, b₁, b₂`
are used at every position (sl. 53). Only the attention sublayer moves
information *between* positions. *(Ref §8.)*
</details>

**C3.** Write LayerNorm and say precisely what it normalizes over.

<details><summary>Solution</summary>

`LayerNorm(x) = γ (x−μ)/σ + β`, with `μ = (1/d)Σᵢxᵢ` and
`σ = sqrt((1/d)Σᵢ(xᵢ−μ)²)` — statistics taken **across the `d` features of a
single token embedding**, not across the batch and not across the sequence.
`γ, β` learnable. *(Ref §8.)*
</details>

**C4. [open]** GPT-3 has 175B parameters in 96 blocks. Roughly how many
parameters per block? What does the deck's model table (sl. 58) suggest about the
relationship between parameter count and block count — is it linear? *(Ref §8.)*

**C5. [open]** DeepSeek-V3 is listed as "671B (37B active)". The deck does not
explain the parenthesis. Flag it as an open question rather than inventing an
answer, and note what you'd need to check. *(Ref §8.)*

### D. Conceptual short answers

**D1.** Why do we need contextual embeddings? Answer in the deck's own form.

<details><summary>Solution</summary>

Static embeddings are context-independent: one word → one fixed vector. Use the
deck's minimal pair (sl. 21–22): *"The chicken didn't cross the road because it
was too **tired**"* vs *"… too **wide**"* — *it* refers to the chicken in one and
the road in the other, but a static embedding gives *it* the same vector both
times. A representation that varies with surrounding words is required. *(Ref §4.)*
</details>

**D2.** Why is a positional embedding necessary?

<details><summary>Solution</summary>

Token embeddings carry no position, and attention is a weighted **sum** — so
permuting the unmasked inputs permutes nothing in the output representation.
Without position, "dog bites man" and "man bites dog" are indistinguishable. Fix:
`xₜ ← xₜ + pₜ` (sl. 48). *(Ref §7.)*
</details>

**D3.** Give the three major components of the transformer architecture.

<details><summary>Solution</summary>

1. Input encoding (embedding + positional encoding); 2. a stack of transformer
blocks; 3. the output head (language-modelling head). *(Ref §3.)*
</details>

**D4.** Why is next-token prediction alone insufficient to produce a usable
assistant?

<details><summary>Solution</summary>

It teaches the model to imitate the corpus's statistical patterns without
distinguishing good from bad — it absorbs factual knowledge and writing styles,
but equally biases, stereotypes, offensive language and misinformation. Human
review is therefore integrated into training; the deck attributes **~10–20% of
final LLM performance** to human intervention (sl. 65). *(Ref §10.)*
</details>

**D5. [open]** Explain "context window" and give the deck's typical range. Why is
it bounded rather than unlimited? *(Ref §8, and tie to the O(n²) argument in §7.)*

**D6. [open]** The deck says the same prompt can yield different continuations.
Which property of the sampling step makes this true, and what would have to
change for the output to become deterministic? *(Ref §1 — and note the deck does
not cover temperature/greedy decoding, so answer only from what it does say.)*

**D7. [open]** Explain, in three sentences, how analysing phrase frequency
("delve", "tapestry", …) supports conclusions about AI use. *(Ref §10.)*

### E. Bonus — matrix form and masking

**E1.** Write the parallel attention formula and name each factor.

<details><summary>Solution</summary>

`Q = XW_Q`, `K = XW_K`, `V = XW_V`, then
`A = softmax(mask(QKᵀ/√d_k))V`. `QKᵀ` is the matrix of pairwise dot products
between query and key vectors; the mask blocks future positions; softmax
normalizes row-wise; `V` supplies the summed values. *(Ref §11.)*
</details>

**E2.** Why is the mask `−∞` rather than `0`, and which triangle gets it?

<details><summary>Solution</summary>

The **upper** triangle (positions after the query). It must be `−∞` *before*
softmax so that `e^{−∞} ≈ 0` after softmax — writing 0 before softmax would give
`e⁰ = 1`, a *large* weight, exactly backwards. Rationale for masking at all:
"guessing a next word becomes simple, if you know it" (sl. 80). *(Ref §11.)*
</details>

**E3. [open]** Why is training highly parallelizable while generation is not?
Give the one-sentence reason for each. *(Ref §11.)*

**E4. [open]** Write the 4×4 masked score matrix for a 4-token sequence, marking
which entries are `−∞`. *(Ref §11.)*

### F. Cross-wiring drills

**F1. [open]** The FFN inside a block is the L08 MLP. Restate `FFN(x)` in L08's
notation and identify what L08 calls `W₁`/`W₂`. *(Ref §12; use
`note-aml-l08-feedforward-networks`.)*

**F2. [open]** The training loss is cross-entropy. Redo the L05 MLE →
cross-entropy derivation, but for a categorical output over `|V|` tokens instead
of Bernoulli. Where exactly does the derivation change? *(Ref §10; use
`note-aml-l05-logistic-regression`.)*

**F3. [open]** Residual connections appear in L10 (ResNet) and L11 (per block).
State the motivation given in each lecture — are they the same motivation?
*(Ref §12; use `note-aml-l10-cnn`.)*

**F4. [open]** Softmax appears in L08 (output layer) and L11 (attention weights).
Same function, different jobs — state each job in one sentence. *(Ref §12.)*

---

## 4. External practice — use with the scope filter

| Source | Take | Avoid |
|---|---|---|
| `source-jurafsky-slp3` Ch. 8 | **First choice.** The deck's own further reading; same notation, fills in every stated-but-unproven step | later chapters on fine-tuning/prompting — beyond deck scope |
| `source-d2l` | Runnable PyTorch for attention and the block — best for *checking* your shape arithmetic in B1–B3 | its encoder–decoder machine-translation framing |
| `source-eecs498` | Lecture on attention/transformers with clean diagrams | its RNN lectures (out of scope) and vision-transformer material |

**The scope filter, stated once:** this deck is **decoder-style causal
self-attention, additive learned positional embeddings, pre-LN blocks, weight-tied
LM head**. If external material introduces encoder–decoder cross-attention,
masked-LM/BERT pretraining, rotary or sinusoidal position encodings, KV-caching,
or RNN comparison beyond one sentence, it has left the lecture — read it for
interest, not for the exam.
