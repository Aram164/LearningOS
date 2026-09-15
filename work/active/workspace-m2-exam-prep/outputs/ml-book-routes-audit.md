# ML book-routes audit — L11–L15 firsthand reads

## L12 Trees (verify-only, no changes)

Read in full: Kelleher Ch4 (PDF pp. 156–214 = printed, Guess Who → entropy/IG
→ ID3 + vegetation worked example → Gini/CART → continuous features →
regression trees/variance → pruning pre/post + reduced-error worked →
boosting/bagging/RF; NO stacking), ISLP §8.1–8.2 (PDF pp. 338–372; recursive
binary splitting/RSS, cost-complexity pruning + CV, Gini/entropy,
bagging/OOB/RF/boosting/BART; NO stacking), Geron Ch6–7 (PDF pp. 203–240;
CART/gini/regularization/χ² pruning/regression/instability + voting,
bagging/pasting, OOB 63.2%, RF/Extra-Trees, AdaBoost/SAMME, GBM, stacking
blender; sub-page cites in route-4e866ff69e5d5dde2aa2d6ba all land on printed
pages), ESL §8.8 (PDF pp. 307–310; Bayesian averaging, CV-prediction
stacking) + §9.2 (PDF pp. 324–332+; CART, greedy (j,s), weakest-link pruning,
Gini/deviance, surrogates, instability), Ch10 AdaBoost/exponential-loss
passage (PDF p. 376) + Ch15 RF-variance passage (PDF pp. 604–612) targeted.
Spot-verified: Marsland Ch12 ID3/entropy present at cited pages; Kroese Ch8
decision-tree + bagging/boosting present at cited pages.
Result: all five book routes (Kelleher/ISLP/Geron×2/ESL) confirmed as written.
All 16 non-video L12 routes are referenced by stages; the 5 unsurfaced routes
are StatQuest videos, reference-only by decision. No import needed.

## L11 Workflow (one locator fix)

Read: Geron Ch2 (test-set discipline, scaling, pipelines, CV — all anchors
land), Ch3 (confusion/ROC/precision-recall/AUC/multiclass/multilabel all
present; ROC sub-cite said p. 117, actual PDF pp. 125–126 — patched via
route.patch, receipt transaction-20260916-010341-001), Ch1 (supervised/
unsupervised/overfitting/exercises anchors land), Ch4 (log-loss Eq 4-17,
softmax, cross-entropy Eq 4-22 all present); Kelleher Ch1 (CRISP-DM,
ill-posed/generalization), Ch2 fraud case, Ch8 (hold-out/peeking/confusion);
ISLP §2.1–2.2 (train/test MSE, U-curve, bias-variance decomposition);
Kroese Ch1–2 (risk, Bayes-optimal predictor, training-vs-test loss §2.3).
All 22 mapped L11 routes referenced by stages. No import needed.

## L14 Probabilistic learning (verify-only, no changes)

Read: Kelleher Ch6 in full (recap/MAP, NB fraud worked, Laplace smoothing
with k, PDFs incl. Gaussian/student-t/binning, Bayes nets/CPTs/Markov
blanket/structure learning); Murphy §9.3–9.4 (NB/MLE, add-one smoothing,
NB–logreg connection, generative-vs-discriminative); ISLP §4.4.4 (NB
assumption, Gaussian/histogram/categorical options, bias-variance framing);
Zacharski Ch6 (m-estimate smoothing worked on votes) + Ch7 (text NB,
log-space); Kroese Ch7 + Marsland Ch16 + ISLP lab at anchor level.
Bishop/Jurafsky/MIT routes unopened (not local); videos reference-only.
All 7 nodes carry verified book routes; 20/21 mapped routes referenced by
stages (lone gap: one StatQuest video, by decision). No import needed.
