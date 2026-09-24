# Statistical Learning — L05 Generative classifiers (slide text export)

Slide 8. The Bayes classifier: ŷ(x) = argmax_y p(y | x) minimizes the 0-1 risk.
Slide 9. By Bayes' rule, p(y | x) ∝ p(x | y) p(y). Modelling p(x | y) is density estimation.
Slide 12. For d binary features, p(x | y) has 2^d − 1 free parameters per class.
Slide 13. Naive assumption: p(x | y) = Π_j p(x_j | y). Parameters per class: d.
Slide 16. Multinomial event model for text: word counts, p(word | class) estimated by relative frequency.
Slide 18. Laplace smoothing: add α = 1 to every count.
Slide 27. Generative (model p(x, y)) versus discriminative (model p(y | x)).
Slide 31. Ng & Jordan (2002): Naive Bayes approaches its asymptotic error with O(log d) examples, logistic regression needs O(d).
Slide 35. Exam hint: be able to state the naive assumption precisely and name where it enters the derivation.
