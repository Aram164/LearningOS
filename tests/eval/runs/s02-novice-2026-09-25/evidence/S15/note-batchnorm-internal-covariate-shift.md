---
id: note-batchnorm-internal-covariate-shift
type: note
title: Batch normalization
created: 2026-06-12
role: synthesis
state: evolving
authorship: user
concepts:
- concept-batch-normalization
sources:
- source-ioffe-batchnorm-2015
- source-santurkar-batchnorm-2018
---

For each feature in a layer, over the current minibatch:

    x̂ = (x − μ_B) / √(σ_B² + ε)      y = γ x̂ + β

γ and β are learned, so the layer can undo the normalization if that is
better.

Why it works (revised 2026-09-25 from note-batchnorm-why-it-works-contested):
the internal-covariate-shift story below is the original paper's
*motivation*, and later work disputes it. Santurkar et al. inject extra shift
after the batch-norm layers and training is still fast; and measured by their
own definition, batch norm does not even reduce the shift much. Their
alternative: batch norm makes the loss landscape smoother (gradients change
less abruptly between nearby points), so larger steps are safe. (I do not
fully follow their Lipschitz argument.) For the exam: know the mechanics
exactly, present the covariate-shift story as the *original motivation*, and
say that later work disputes it.

Original June explanation, kept as I wrote it (the paper's motivation, now
disputed):

Why it works: during training the distribution of each layer's inputs keeps
changing because the earlier layers keep changing ("internal covariate
shift"). Normalizing every batch removes this shift, so each layer sees a
stable input distribution and training can use much larger learning rates.

At test time use running averages of μ and σ² collected during training, not
the statistics of the test batch.
