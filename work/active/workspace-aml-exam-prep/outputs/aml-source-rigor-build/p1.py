# P1 — page-convention corrections, artifact clearing, dispositions.
# Every PDF page below was derived on 2026-08-30 from the file's own outline
# (tools/material_toc.py --toc) and re-checked with --verify.

M = "material://source-murphy-pml1/pml1.pdf"

EDITS = {
    # ---- Murphy: printed pages -> PDF pages (offset +30, outline-derived) ----
    "route-c67a99b0cdc7f85ce29bece8": {
        "locator": "pml1.pdf §11.2.2 Least squares estimation, pdf pp. 402-405; "
                   "§11.2.4 Measuring goodness of fit, pdf p. 410",
        "vault_path": M,
    },
    "route-09ae79cd78e352276370c8d0": {
        "locator": "pml1.pdf §8.1.3 Convex vs nonconvex optimization, pdf pp. 307-310 "
                   "(convex sets and functions p. 307, the Hessian positive-definite test p. 310)",
        "vault_path": M,
    },
    "route-d2797d2723a780a4c3715a01": {
        "locator": "pml1.pdf §8.3 Second-order methods, pdf pp. 319-321 "
                   "(Newton's method p. 319, BFGS and quasi-Newton p. 320, trust region p. 321)",
        "vault_path": M,
    },
    "route-c446c7532bc169a9759f14ce": {
        "locator": "pml1.pdf §8.4.6 Preconditioned SGD, pdf pp. 328-331 "
                   "(AdaGrad p. 329, RMSProp and AdaDelta pp. 329-330, Adam p. 330, "
                   "issues with adaptive learning rates p. 331); "
                   "momentum and Nesterov in §8.2.4, pdf pp. 317-318",
        "vault_path": M,
    },
    "route-3224d420145c8529499ae635": {
        "locator": "pml1.pdf §15.4 Attention, pdf pp. 548-555 "
                   "(attention as soft dictionary lookup p. 549, parametric attention p. 551)",
        "vault_path": M,
    },
    "route-2c65706e0f943446ed4f5f28": {
        "locator": "pml1.pdf §15.5 Transformers, pdf pp. 556-562 "
                   "(self-attention p. 556, multi-headed attention p. 557, positional encoding p. 558, "
                   "putting it all together p. 559, comparing transformers, CNNs and RNNs p. 561)",
        "vault_path": M,
    },
    "route-480b485364dfde6ba7eba3ca": {
        "locator": "pml1.pdf §15.7 Language models and unsupervised representation learning, "
                   "pdf pp. 567-576 (non-generative models p. 568, generative causal LLMs p. 572)",
        "vault_path": M,
    },
    "route-b4767511bb52dcb8e0cdd2d0": {
        "locator": "pml1.pdf §20.5 Word embeddings, pdf pp. 735-742 "
                   "(latent semantic analysis p. 735, word2vec p. 737, GloVe p. 740, word analogies p. 740)",
        "vault_path": M,
    },
    "route-f426a3cf4e1b48b8f1c408d3": {
        "locator": "pml1.pdf §8.1.3 pdf pp. 307-310, §8.3 pdf pp. 319-321, §8.4.6 pdf pp. 328-331; "
                   "§15.4 pdf pp. 548-555, §15.5 pdf pp. 556-562; "
                   "solutions-public.pdf 'Gradient and Hessian of log-likelihood for multinomial "
                   "logistic regression' pdf p. 25 and 'Backpropagation for a 1 layer MLP' pdf p. 30",
        "vault_path": M,
    },
    # ---- ISLP: printed pages -> PDF pages (offset +7, outline-derived) ----
    "route-96b3bc3586d74e35b541bcb5": {
        "locator": "islp.pdf §10.3 Convolutional Neural Networks, pdf pp. 413-419 "
                   "(§10.3.1 convolution layers p. 414, §10.3.2 pooling p. 417, "
                   "§10.3.3 architecture p. 417, §10.3.4 data augmentation p. 418)",
        "vault_path": "material://source-islp/islp.pdf",
    },
    # ---- Artifact clearing: the address was already precise, the form was not ----
    "route-2457956085b5ea6e7a400110": {
        "locator": "Chapter 11, sections 11.1 'Queries, Keys, and Values'; "
                   "11.3 'Attention Scoring Functions'; 11.5 'Multi-Head Attention'; "
                   "11.6 'Self-Attention and Positional Encoding'; "
                   "11.7 'The Transformer Architecture' — each ending in an Exercises subsection. "
                   "Section 11.4 (Bahdanau attention) is RNN-era and 11.8-11.9 (vision, large-scale "
                   "pretraining) are outside the 2026 scope. Verified 2026-08-22.",
    },
}

SOURCE_EDITS = {
    "source-sutton-barto-rl": {
        "role": "reference",
        "why": "Reference-only, deliberately unrouted (2026-08-30). Reinforcement learning appears "
               "nowhere in the current L01-L11 decks or in the Themen list on Uebung 10 slide 3, so no "
               "lecture route can honestly claim it. The record is kept rather than dropped so the "
               "decision stays visible: revisit only if a future deck adds RL.",
    },
}
