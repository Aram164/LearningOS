Durable notes — machine learning.

=== note-naive-bayes-spam-filter
domain: machine-learning
title: Naive Bayes for the spam exercise
created: 2026-05-07
role: synthesis
state: evolving
authorship: user
concepts: [concept-naive-bayes]
sources: [source-tuh-statlearn-slides, source-murphy-pml1]
evidence:
  - {type: implementation, ref: "github://noor-haddad/ml-exercises/sheet05/spam_nb.py"}
---
Goal: P(spam | words in the mail).

Bayes: P(spam | w_1, …, w_n) ∝ P(spam) · P(w_1, …, w_n | spam).

The second factor is hopeless to estimate directly — there are more word
combinations than emails. The trick: pretend that, once you already know
whether a mail is spam or ham, seeing one word tells you nothing more about
whether another word appears. Then the big probability breaks into one factor
per word:

    P(spam | w_1..w_n) ∝ P(spam) · Π_i P(w_i | spam)

and each P(w_i | spam) is just a count: in how many spam mails does w_i show
up. Same for ham, then compare the two scores (in log space, otherwise the
product underflows to 0.0 after a few hundred words).

This assumption is obviously false ("free" and "viagra" come together) but the
classifier still works well, because we only need the *ranking* of spam vs ham
to be right, not the probabilities.

Laplace smoothing: add 1 to every count so a word never seen in spam does not
zero out the whole product. Without it my classifier called every mail with
the word "Havelberg" ham, because it never appeared in training spam.

Accuracy on the exercise data: 96.8% with smoothing, 91% without.

=== note-generative-vs-discriminative
domain: machine-learning
title: Generative versus discriminative classifiers
created: 2026-05-14
role: synthesis
state: rough
authorship: user
concepts: [concept-generative-vs-discriminative, concept-naive-bayes, concept-logistic-regression]
sources: [source-tuh-statlearn-slides]
---
Generative: model how the data is produced, p(x | y) p(y), then get p(y | x)
by Bayes. Naive Bayes, Gaussian discriminant analysis.

Discriminative: model p(y | x) directly. Logistic regression.

Lecture claim (Ng & Jordan): with little data the generative model reaches its
(worse) asymptotic error faster; with lots of data the discriminative one wins.

Half-understood: why "modelling more" (the features too) helps with little
data. My guess is that the extra assumptions act like a prior.

TODO for the stage: same features, both models, learning curves.

=== note-logistic-regression-cross-entropy
domain: machine-learning
title: Logistic regression and where cross-entropy comes from
created: 2026-05-20
role: derivation
state: evolving
authorship: user
concepts: [concept-logistic-regression, concept-cross-entropy]
sources: [source-tuh-statlearn-slides, source-bishop-prml]
evidence:
  - {type: derivation, ref: "github://noor-haddad/ml-exercises/sheet05/ex3_logreg.pdf"}
---
Model: p_i = σ(wᵀx_i) with σ(z) = 1 / (1 + e^(−z)), labels y_i ∈ {0, 1}.

Each label is a Bernoulli draw with success probability p_i, so the
probability of the observed labels is

    Π_i p_i^(y_i) (1 − p_i)^(1 − y_i)

Take −log and average:

    J(w) = −(1/n) Σ_i [ y_i log p_i + (1 − y_i) log(1 − p_i) ]

That is the binary cross-entropy loss. Nice fact: ∇J = (1/n) Σ (p_i − y_i) x_i
— the same shape as the linear regression gradient.

Why not squared error? With a sigmoid inside, squared error is non-convex in w
and its gradient vanishes when the prediction is confidently wrong. The
cross-entropy gradient stays large exactly then.

No closed form — you have to iterate.

=== note-gradient-descent-from-scratch
domain: machine-learning
title: Gradient descent from scratch (housing exercise)
created: 2026-04-24
updated: 2026-05-19
role: implementation
state: evolving
authorship: user
concepts: [concept-gradient-descent, concept-linear-regression]
sources: [source-tuh-statlearn-slides]
evidence:
  - {type: implementation, ref: "github://noor-haddad/ml-exercises/sheet02/gd_housing.py"}
---
Update rule: w ← w − η ∇L(w), with L the mean squared error.

Housing exercise (living area in m², rooms, age → price):

- On the raw features, η = 0.1 made the loss explode to inf within 12 steps.
- η = 0.001 converged but painfully slowly (40,000 iterations).
- η = 0.01 was the best compromise on raw features.

Update 2026-05-19: the real problem was scaling. The area feature is in the
hundreds and the rooms feature is 1–6, so the loss surface is a very long thin
valley and any step size that is safe along one axis is useless along the
other. After standardizing every feature (subtract mean, divide by standard
deviation) η = 0.1 converges in under 200 iterations. Lesson: before blaming
the learning rate, look at the feature scales.

Stopping rule: stop when the relative change in loss is below 1e-6.

=== note-gradient-descent-from-scratch @2026-04-24
created: 2026-04-24
---
Update rule: w ← w − η ∇L(w), with L the mean squared error.

Housing exercise (living area in m², rooms, age → price):

- η = 0.1 made the loss explode to inf within 12 steps. No idea why yet.
- η = 0.001 converged but painfully slowly (40,000 iterations).
- η = 0.01 was the best compromise.

Stopping rule: stop when the relative change in loss is below 1e-6.

=== note-linear-regression-normal-equation
domain: machine-learning
title: Linear regression — the normal equation
created: 2026-04-23
role: derivation
state: evolving
authorship: user
concepts: [concept-linear-regression, concept-normal-equation]
sources: [source-tuh-statlearn-slides]
---
Minimize ‖y − Xw‖². Gradient: −2Xᵀ(y − Xw) = 0 ⇒ XᵀX w = Xᵀy ⇒

    w = (XᵀX)⁻¹ Xᵀ y

when XᵀX is invertible (full column rank). Geometrically: Xw is the
orthogonal projection of y onto the column space of X; the residual is
perpendicular to every column.

Cost: forming XᵀX is O(n d²), inverting it O(d³). Fine for d in the hundreds,
bad for d = 100,000 — which is why the iterative version exists.

If two features are collinear, XᵀX is singular and the formula breaks. The
lecture said "we fix this in L07".

=== note-sgd-momentum-nn-training
domain: machine-learning
title: Training a small MLP — minibatches and momentum
created: 2026-07-10
role: implementation
state: rough
authorship: user
concepts: [concept-stochastic-gradient-descent]
sources: [source-goodfellow-dl]
---
Trained a 2-layer MLP on Fashion-MNIST in plain numpy.

Full-batch updates were slow; minibatches of 64 made each step cheap and
noisy, and the noise did not hurt — if anything the loss curve was better.

Momentum as a heavy ball: v ← βv − η g; θ ← θ + v with β = 0.9. It keeps
going in directions where the gradients agree and cancels the zig-zag across
the narrow directions.

Numbers: plain minibatch updates reached 84% test accuracy after 10 epochs,
with momentum 87%.

The update rule is the same one from the housing exercise, just with a
gradient estimated from 64 examples and a velocity term.

=== note-adam-always-better
domain: machine-learning
title: Adam is just better
created: 2026-06-05
role: synthesis
state: deprecated
authorship: user
concepts: [concept-adaptive-optimizers]
sources: []
---
Adam adapts the step size per parameter (running averages of the gradient and
of its square) and needs almost no tuning. Everyone in the forum says just use
Adam with lr = 3e-4. There is no reason to use plain SGD anymore.

=== note-adam-vs-sgd-revisited
domain: machine-learning
title: Adam versus SGD, revisited
created: 2026-08-20
role: synthesis
state: evolving
authorship: user
concepts: [concept-adaptive-optimizers, concept-stochastic-gradient-descent]
sources: [source-wilson-adaptive-2017, source-goodfellow-dl]
---
In June I wrote that Adam is "just better". Too strong.

What is true: Adam usually drives the training loss down faster and is less
sensitive to the initial learning rate.

What I missed: Wilson et al. find that on several image-classification tasks,
well-tuned SGD with momentum *generalizes* better — lower test error — even
when Adam's training loss is lower. Their explanation involves the adaptive
methods finding different solutions, not just the same solution faster.

My own run: same MLP as in July, Adam reached 86% test accuracy in 4 epochs
but plateaued; SGD + momentum with a decaying learning rate reached 88% after
15 epochs.

Current take: Adam for fast iteration and for models where SGD is hard to
tune (transformers); SGD + momentum is still worth trying when the last
percent of test accuracy matters. Not a law either way.

=== note-backprop-as-bookkeeping
domain: machine-learning
title: Backpropagation is careful bookkeeping
created: 2026-07-08
role: synthesis
state: rough
authorship: user
concepts: [concept-backpropagation, concept-chain-rule]
sources: [source-goodfellow-dl]
---
Forward pass: compute every intermediate value layer by layer and *keep
them*. Backward pass: start from ∂L/∂L = 1 at the loss and walk the graph in
reverse, multiplying by each node's local derivative; a node used by several
later nodes adds up the contributions.

Why store the forward activations: the local derivative of a layer usually
needs its input (for y = Wx, ∂L/∂W = (∂L/∂y) xᵀ). Memory use therefore grows
with depth × batch size — that is the memory wall people talk about.

Cost: one backward pass ≈ 2–3× the forward pass, for *all* parameters at
once. Computing each partial derivative separately would cost one forward
pass per parameter.

Still unclear to me: how frameworks decide which intermediates to keep.

=== note-batchnorm-internal-covariate-shift
domain: machine-learning
title: Batch normalization
created: 2026-06-12
role: synthesis
state: evolving
authorship: user
concepts: [concept-batch-normalization]
sources: [source-ioffe-batchnorm-2015]
---
For each feature in a layer, over the current minibatch:

    x̂ = (x − μ_B) / √(σ_B² + ε)      y = γ x̂ + β

γ and β are learned, so the layer can undo the normalization if that is
better.

Why it works: during training the distribution of each layer's inputs keeps
changing because the earlier layers keep changing ("internal covariate
shift"). Normalizing every batch removes this shift, so each layer sees a
stable input distribution and training can use much larger learning rates.

At test time use running averages of μ and σ² collected during training, not
the statistics of the test batch.

=== note-batchnorm-why-it-works-contested
domain: machine-learning
title: Why batch norm works is contested
created: 2026-08-28
role: synthesis
state: rough
authorship: user
concepts: [concept-batch-normalization, concept-stochastic-gradient-descent]
sources: [source-santurkar-batchnorm-2018]
---
The June note repeats the original paper's explanation (internal covariate
shift). Santurkar et al. test it directly: they *inject* extra shift after the
batch-norm layers and training is still fast; and measured by their own
definition, batch norm does not even reduce the shift much.

Their alternative: batch norm makes the loss landscape smoother (gradients
change less abruptly between nearby points), so larger steps are safe.

I do not fully follow their Lipschitz argument. What I take away for the
exam: know the mechanics exactly, present the covariate-shift story as the
*original motivation*, and say that later work disputes it.

=== note-ridge-regression-penalty
domain: machine-learning
title: Ridge regression
created: 2026-06-01
role: derivation
state: evolving
authorship: user
concepts: [concept-regularization, concept-linear-regression]
sources: [source-tuh-statlearn-slides]
---
Add a penalty on the weight size:

    L(w) = ‖y − Xw‖² + λ‖w‖²

Gradient to zero: −2Xᵀ(y − Xw) + 2λw = 0 ⇒

    w = (XᵀX + λI)⁻¹ Xᵀ y

XᵀX + λI is always invertible for λ > 0 (its eigenvalues are shifted up by
λ), which also fixes the collinearity problem from the normal-equation note.

Effect: all weights shrink towards zero, none becomes exactly zero. Large λ →
more bias, less variance.

Open questions:

- Why is there a neat closed form here while the lasso needs special solvers?
- Where does λ come from — is it just a knob you tune by cross-validation, or
  does it mean something?

=== note-lasso-sparsity-geometry
domain: machine-learning
title: Why the lasso sets weights exactly to zero
created: 2026-06-03
role: synthesis
state: evolving
authorship: user
concepts: [concept-regularization]
sources: [source-esl]
---
Lasso: minimize ‖y − Xw‖² + λ Σ_j |w_j|.

Constrained form: minimize the squared error subject to Σ|w_j| ≤ t. In 2-D the
allowed region is a diamond with corners on the axes; for ridge (Σ w_j² ≤ t)
it is a disc.

The error contours are ellipses around the unconstrained solution. Grow them
until they first touch the allowed region: a disc gets touched at a generic
point (both weights non-zero), a diamond very often at a corner — where one
weight is exactly zero. ESL figure 3.11 is the whole argument in one picture.

So lasso does feature selection for free. With highly correlated features it
picks one of them somewhat arbitrarily.

=== note-overfitting-polynomial-degree
domain: machine-learning
title: Overfitting — polynomial degree experiment
created: 2026-05-27
role: implementation
state: evolving
authorship: user
concepts: [concept-overfitting, concept-bias-variance-tradeoff]
sources: [source-tuh-statlearn-slides]
evidence:
  - {type: implementation, ref: "github://noor-haddad/ml-exercises/l07/poly_fit.ipynb"}
---
20 noisy points from sin(2πx), fit polynomials of degree 1, 3, 9, 15.

| degree | train MSE | test MSE |
|---|---|---|
| 1 | 0.21 | 0.24 |
| 3 | 0.05 | 0.07 |
| 9 | 0.01 | 0.19 |
| 15 | 0.000 | 4.8 |

Degree 15 passes through every training point and oscillates wildly between
them. Degree 1 is wrong everywhere in the same way.

With 200 points instead of 20, degree 9 behaves fine — more data reduces the
wiggle.

=== note-cross-validation-kfold
domain: machine-learning
title: k-fold cross-validation
created: 2026-06-16
role: synthesis
state: evolving
authorship: user
concepts: [concept-cross-validation]
sources: [source-esl]
---
Split the training data into k folds; train on k−1, validate on the held-out
one, rotate, average the k validation scores. k = 5 or 10 in practice.

Use it to choose hyperparameters (λ, polynomial degree). Then retrain on all
training data with the chosen value and report the score on the untouched
test set once.

ESL §7.10.2 "the wrong and the right way to do cross-validation": if you pick
the features using all the data *before* splitting into folds, the CV error is
wildly optimistic. Every step that looks at the labels has to happen inside the
fold.

Nested CV if you also want an honest estimate of the tuned model.

=== note-data-leakage-scaler
domain: machine-learning
title: The scaler leak
created: 2026-06-19
role: synthesis
state: evolving
authorship: user
concepts: [concept-data-leakage, concept-cross-validation]
sources: [source-huyen-dmls]
---
My L07 notebook reported 94% validation accuracy. The mistake: I fit the
StandardScaler on the whole dataset *before* the train/validation split, so
the mean and standard deviation used to scale the training data already
contained information from the validation rows.

Here it only moved the score by about a point, but with target encoding it
would have been catastrophic.

Fix: put the scaler and the model into one sklearn Pipeline and pass the
Pipeline to cross_val_score — then fit() on each training fold refits the
scaler on that fold only.

General rule for myself: anything that is *fit* (scalers, imputers, feature
selection, encoders) is part of the model.

=== note-pca-by-hand
domain: machine-learning
title: PCA by hand on a 2-D toy dataset
created: 2026-06-09
role: implementation
state: evolving
authorship: user
concepts: [concept-pca, concept-covariance-matrix, concept-eigendecomposition]
sources: [source-tuh-statlearn-slides]
evidence:
  - {type: exercise, ref: "github://noor-haddad/ml-exercises/l09/pca_by_hand.ipynb"}
---
Data: 6 points in 2-D, centred. Covariance

    Σ = [[2.0, 1.2], [1.2, 1.0]]

Characteristic polynomial λ² − 3λ + 0.56 = 0 → λ₁ ≈ 2.79, λ₂ ≈ 0.21.
First eigenvector ≈ (0.84, 0.55). Explained variance of PC1 = 2.79 / 3.0 = 93%.

Projecting each point onto PC1 gives a 1-D dataset keeping 93% of the
variance. Checked against numpy.linalg.eigh — same up to sign.

Steps: centre → covariance → eigenvectors sorted by eigenvalue → project.
Standardize first if the features have different units.

=== note-svm-kernel-trick
domain: machine-learning
title: SVMs and the kernel trick
created: 2026-06-23
role: synthesis
state: rough
authorship: user
concepts: [concept-svm]
sources: [source-tuh-statlearn-slides]
---
Maximum-margin separating hyperplane; only the support vectors (points on the
margin) determine it. Soft margin with slack variables and a penalty C.

The dual problem only uses the data through inner products x_iᵀx_j. Replace
every inner product by a kernel k(x_i, x_j) = φ(x_i)ᵀφ(x_j) and you get a
linear separator in the feature space of φ without ever computing φ.

RBF kernel: k(x, x') = exp(−γ‖x − x'‖²) — an infinite-dimensional φ.

A function is a valid kernel iff every kernel matrix it produces is positive
semi-definite (Mercer).

Out of exam scope beyond the definition (workspace deferral).

=== note-cnn-convolution-kernels
domain: machine-learning
title: Convolutions in CNNs
created: 2026-07-14
role: synthesis
state: rough
authorship: user
concepts: [concept-convolutional-networks]
sources: [source-goodfellow-dl]
---
A convolutional layer slides a small kernel (say 3×3) over the image and takes
a weighted sum at every position. The same weights are used everywhere —
weight sharing — so a detector learned in one corner works in every corner.

The classic hand-made filter [[−1, 0, 1], [−2, 0, 2], [−1, 0, 1]] (Sobel)
detects vertical edges; a CNN learns its own filters instead.

Output size: (W − K + 2P)/S + 1. Pooling shrinks the feature map and adds a
bit of translation invariance.

Parameters: 3×3×64×128 = 73,728 for a layer from 64 to 128 channels, far fewer
than a dense layer on the same input.

=== note-softmax-temperature
domain: machine-learning
title: Softmax and temperature
created: 2026-08-12
role: synthesis
state: rough
authorship: user
concepts: [concept-softmax]
sources: [source-goodfellow-dl]
---
softmax(z)_i = exp(z_i / T) / Σ_j exp(z_j / T)

T = 1 is the normal softmax. Large T flattens the distribution towards
uniform; small T sharpens it; T → 0 puts all the mass on the largest logit.

Where it shows up: sampling from language models (temperature 0.7 vs 1.2),
knowledge distillation (a high T exposes how the teacher ranks the wrong
classes), and calibration (fit one T on the validation set so the confidences
match the accuracy).

Numerical detail: subtract max(z) before exponentiating.

=== note-hmm-viterbi
domain: machine-learning
title: HMMs and the Viterbi algorithm
created: 2026-07-03
role: synthesis
state: evolving
authorship: user
concepts: [concept-hidden-markov-models]
sources: [source-bishop-prml]
---
Hidden states z_1..z_T form a Markov chain; each state emits an observation
x_t. Parameters: initial distribution, transition matrix A, emission
probabilities.

Most likely hidden sequence given the observations: brute force is K^T
sequences. Viterbi instead fills a table: for every time step t and every
state k, the best score of any path that ends in state k at time t,

    δ_t(k) = max_j [ δ_{t−1}(j) · A_jk ] · p(x_t | k)

plus a backpointer to the j that achieved the max. At the end, take the best
final state and follow the backpointers. Cost O(T K²).

Works because the best path into (t, k) must consist of a best path into some
(t−1, j) followed by one step — you never need to remember the worse ones.

Use logs so the products become sums.

=== note-matrix-factorization-recommenders
domain: machine-learning
title: Matrix factorization for recommendations
created: 2026-08-25
role: synthesis
state: rough
authorship: user
concepts: [concept-matrix-factorization]
sources: []
---
Ratings matrix R (users × items), 99% missing. Model every user by a vector
p_u ∈ ℝ^k and every item by q_i ∈ ℝ^k with k ≈ 20–100, predict r̂_ui = p_uᵀq_i.

Fit by minimizing the squared error *only over the observed ratings*, plus a
penalty λ(‖p_u‖² + ‖q_i‖²). Alternating least squares: fix Q, each p_u is a
small least-squares problem; then fix P; repeat. Or plain SGD over the observed
entries.

So the missing entries are never needed — you only fit the ones you have, and
the product PQᵀ fills in everything else. That is the "Netflix prize" idea.

k is the number of hidden taste dimensions; nobody labels them, they fall out
of the fit.

=== note-regression-metrics
domain: machine-learning
title: Regression metrics
created: 2026-05-22
role: reference
state: evolving
authorship: user
concepts: [concept-regression-metrics]
sources: [source-tuh-statlearn-slides]
---
- MAE = mean |y − ŷ| — robust to outliers, same units as y.
- RMSE = √(mean (y − ŷ)²) — punishes large errors more.
- R² = 1 − SS_res / SS_tot — fraction of variance explained; can be negative
  on test data if the model is worse than predicting the mean.

For the housing regression: MAE 21k €, RMSE 34k €, R² 0.81 on the test split.

Report more than one; R² alone hides the scale of the errors.

=== note-decision-trees-entropy
domain: machine-learning
title: Decision trees and information gain
created: 2026-05-29
role: synthesis
state: evolving
authorship: user
concepts: [concept-decision-trees]
sources: [source-tuh-statlearn-slides]
---
Entropy of a node with class proportions p_k: H = −Σ_k p_k log₂ p_k.
Information gain of a split = H(parent) − weighted average H(children).
Greedy: at each node pick the split with the largest gain.

Gini impurity 1 − Σ p_k² behaves almost the same and is cheaper.

Deep trees overfit; limit depth or prune. Random forests average many trees
trained on bootstrap samples with random feature subsets.

=== note-statlearn-mock-exam-september
domain: machine-learning
title: Statistical Learning — mock exam 1
created: 2026-09-01
role: mock-exam
state: rough
authorship: operator-drafted
concepts: [concept-naive-bayes, concept-regularization, concept-bias-variance-tradeoff, concept-pca, concept-maximum-likelihood]
sources: [source-tuh-statlearn-slides]
contexts: [workspace-statlearn-retake]
---
Drafted from the lecture slides in the exam format (90 minutes, no aids). Not
yet attempted.

1. (12 P) Derive the MLE of θ for n Bernoulli(θ) observations. When is it a
   poor estimate?
2. (15 P) A spam filter uses Naive Bayes over a 5-word vocabulary. Given the
   count table, classify the mail "free money now". State the assumption you
   used and one reason it is violated in practice.
3. (15 P) Derive the ridge estimator. Explain why it exists even when XᵀX is
   singular.
4. (10 P) Sketch training and test error against model complexity; label bias
   and variance.
5. (18 P) Compute the first principal component of the given 2-D covariance
   matrix and the fraction of variance it explains.
6. (10 P) Explain why fitting a scaler before the train/test split is a
   mistake.
