"""P2 — exact locators for every AML route backed by registered local bytes.

Pages are PDF pages, not printed folios.  The two books without usable PDF
outlines (CSC411 and Zacharski) were located by Poppler text extraction; the
remaining book pages come from their embedded outlines and were spot-verified.
"""

AML = "material://source-aml-ss26-lectures"
GERON = "material://source-geron-handson/geron-copy2.pdf"
SAD = "material://source-sad-ss26-lectures/lecture-slides/15_neural_networks.pdf"
ZACH = (
    "material://source-zacharski-data-mining/"
    "Zacharski_Programmers-Guide-to-Data-Mining.pdf"
)

EDITS = {
    # Course exercise decks — slide ranges were read from the local PDFs.
    "route-60bc74e346dcfde204afeba3": {
        "locator": "exercise-slides/Übung 02 .pdf, slides 3-17 (CLIP), 19-33 (Blatt 1 k-NN exercise), and 35-43 (NumPy refresher)",
        "vault_path": f"{AML}/exercise-slides/Übung 02 .pdf",
    },
    "route-57a9e25c00310eb54bc52039": {
        "locator": "exercise-slides/Übung 06 .pdf, slides 3-10 (logistic model, loss, and gradient), 16-21 (sigmoid and overfitting), and 23-27 (decision-boundary exercise)",
        "vault_path": f"{AML}/exercise-slides/Übung 06 .pdf",
    },
    "route-bef5d1b1bd52e5ddd842c0f7": {
        "locator": "exercise-slides/Übung 06 .pdf, slides 12-14 (gradient descent) and 16-21 (sigmoid saturation and overfitting)",
        "vault_path": f"{AML}/exercise-slides/Übung 06 .pdf",
    },

    # ISLP.
    "route-21f9795d5af805470f6b7aa8": {
        "locator": "islp.pdf §2.1 What Is Statistical Learning?, pdf pp. 25-36; §2.2 Assessing Model Accuracy, pdf pp. 37-48 (bias-variance §2.2.2 p. 41; classification setting §2.2.3 p. 44)",
    },
    "route-d3bb781518afd9298b86e667": {
        "locator": "islp.pdf §3.1 Simple Linear Regression, pdf pp. 79-88; §3.2 Multiple Linear Regression, pdf pp. 89-99",
    },
    "route-9b7338b2096b7f03eef6d176": {
        "locator": "islp.pdf §3.2 Multiple Linear Regression, pdf pp. 89-99; §2.2.2 The Bias-Variance Trade-Off, pdf pp. 41-43; §§6.2.1-6.2.2 Ridge Regression and the Lasso, pdf pp. 248-259; §7.1 Polynomial Regression and Step Functions, pdf pp. 298-313",
    },
    "route-b5479427410717e42df4b6af": {
        "locator": "islp.pdf §4.3 Logistic Regression, pdf pp. 147-155 (logistic model §4.3.1 p. 148; multiple logistic regression §4.3.4 p. 151)",
    },
    "route-f0ccf205ed8c7df0ef0c8687": {
        "locator": "islp.pdf §10.7 Fitting a Neural Network, pdf pp. 434-438 (backpropagation §10.7.1 p. 435; regularization and SGD §10.7.2 p. 436)",
    },
    "route-250a1234665348201198e7ef": {
        "locator": "islp.pdf §9.4.2 Support Vector Machines with More than Two Classes, pdf p. 391; optional context only: §9.3.2 Support Vector Classifiers with Non-Linear Boundaries, pdf p. 384",
    },
    "route-987303d08d29f8315ce9a8e6": {
        "locator": "islp.pdf §10.1 Single Layer Neural Networks, pdf pp. 407-408; §10.2 Multilayer Neural Networks, pdf pp. 409-412",
    },
    "route-9479853098e251427bc92b4a": {
        "locator": "islp.pdf §10.7 Fitting a Neural Network, pdf pp. 434-438; §10.8 Interpolation and Double Descent, pdf pp. 439-441",
    },

    # ESL.
    "route-0c5b2516f89b5265bb3c86e2": {
        "locator": "esl.pdf §3.2 Linear Regression Models and Least Squares, pdf pp. 63-75",
    },
    "route-387627946adffa7177aebbb4": {
        "locator": "esl.pdf §3.4.1 Ridge Regression, pdf pp. 80-86; §3.4.2 The Lasso, pdf p. 87; §3.4.3 Discussion, pdf pp. 88-91 (stop before §3.4.4 Least Angle Regression p. 92)",
    },
    "route-da6e469fc665bfad1ee8045c": {
        "locator": "esl.pdf §4.4 Logistic Regression, pdf pp. 138-147 (fitting by Newton-Raphson/IRLS §4.4.1 p. 139; L1-regularized logistic regression §4.4.4 p. 144)",
    },
    "route-f9bae648830b68b38885701f": {
        "locator": "esl.pdf §4.5.1 Rosenblatt's Perceptron Learning Algorithm, pdf pp. 149-150 (stop before optimal separating hyperplanes §4.5.2 p. 151)",
    },
    "route-48d3ff104dc9cf8297be28ca": {
        "locator": "esl.pdf §11.3 Neural Networks, pdf pp. 411-413; §11.4 Fitting Neural Networks, pdf pp. 414-415; §11.5 Some Issues in Training Neural Networks, pdf pp. 416-422",
    },
    "route-5537c790ee855af15adac484": {
        "locator": "esl.pdf §11.4 Fitting Neural Networks, pdf pp. 414-415; §11.5 Some Issues in Training Neural Networks, pdf pp. 416-422",
    },
    "route-ff147162ccc891125fca6e2c": {
        "locator": "esl.pdf §11.7 Example: A Convolutional Neural Network for Digit Classification, pdf pp. 423-425",
    },

    # Murphy PML1.
    "route-7414f700392cabbc7991a6c6": {
        "locator": "pml1.pdf §16.1 K nearest neighbor (KNN) classification, pdf pp. 577-580 (curse of dimensionality §16.1.2 p. 578); §4.7.6 The bias-variance tradeoff, pdf pp. 189-193",
    },
    "route-773bc4e5073c9add77b9f2d8": {
        "locator": "pml1.pdf §11.2 Least squares linear regression, pdf pp. 401-410",
    },
    "route-edfd22e1d584f506b0efdd2c": {
        "locator": "pml1.pdf §11.2 Least squares linear regression, pdf pp. 401-410; §11.3 Ridge regression, pdf pp. 411-414; §11.4 Lasso regression, pdf pp. 415-428",
    },
    "route-37104c3c217b32519e132f1f": {
        "locator": "pml1.pdf §10.2.3 Maximum likelihood estimation, pdf pp. 372-374; §10.2.4 Stochastic gradient descent, pdf p. 375; §10.2.5 Perceptron algorithm, pdf p. 376",
    },
    "route-2859463c0a0acd4759eb3acb": {
        "locator": "pml1.pdf §8.1.3 Convex vs nonconvex optimization, pdf pp. 307-310; §8.2.4 Momentum, pdf pp. 317-318; §8.3 Second-order methods, pdf pp. 319-321; §8.4.6 Preconditioned SGD, pdf pp. 328-331",
    },
    "route-cd7615636cab19837678f3bc": {
        "locator": "pml1.pdf §10.2.5 Perceptron algorithm, pdf p. 376; §17.1 Mercer kernels, pdf pp. 597-603 (§17.1.1 Mercer's theorem p. 598; §17.1.2 popular kernels p. 599)",
    },
    "route-c1a26eea429baf963f8f3ed4": {
        "locator": "pml1.pdf §13.2 Multilayer perceptrons, pdf pp. 456-467 (XOR §13.2.1 p. 457; activation functions §13.2.3 p. 458)",
    },
    "route-e25d9a6869ecc1aabd95b158": {
        "locator": "pml1.pdf §13.3 Backpropagation, pdf pp. 468-475; §13.4 Training neural networks, pdf pp. 476-484; §13.5 Regularization, pdf pp. 485-489",
    },
    "route-4d9bdcdef94d579ed5bc99c8": {
        "locator": "pml1.pdf §14.1 Introduction, pdf p. 497; §14.2 Common layers, pdf pp. 498-508 (convolution §14.2.1 p. 498; pooling §14.2.2 p. 505); §14.3 Common architectures, pdf pp. 509-515",
    },
    "route-c16dd407fb2579c179f20a8a": {
        "locator": "solutions-public.pdf 'Gradient and Hessian of log-likelihood for multinomial logistic regression' (exercise 10.1), pdf p. 25",
        "vault_path": "material://source-murphy-pml1/solutions-public.pdf",
    },

    # CSC411.  This PDF has no outline; printed folios are offset by +5.
    "route-be209f0a3a6bc848da75f184": {
        "locator": "csc411.pdf §3.4 K-Nearest Neighbors regression, pdf pp. 20-21; §8.4 K-Nearest Neighbors Classification, pdf pp. 51-52",
    },
    "route-d644dc77c149abc299b420c9": {
        "locator": "csc411.pdf §3.1 Basis function regression, pdf pp. 14-15; §3.2 Overfitting and Regularization, pdf pp. 16-18",
        "covers": ["knowledge-aml-l04-basis", "knowledge-aml-l04-overfitting", "knowledge-aml-l04-ridge"],
    },
    "route-7523f3a6574bcd59ec9049dc": {
        "locator": "csc411.pdf §8.2 Logistic Regression, pdf pp. 49-50; §8.6 Classification by LS Regression, pdf pp. 53-54",
        "covers": ["knowledge-aml-l05-classification", "knowledge-aml-l05-boundary", "knowledge-aml-l05-sigmoid"],
    },
    "route-9a435fb743f7e6a7298b2ff1": {
        "locator": "csc411.pdf §9 Gradient Descent, pdf pp. 58-59; §9.1 Finite differences, pdf pp. 60-61",
        "covers": ["knowledge-aml-l06-gradient", "knowledge-aml-l06-batch-gd"],
    },
    "route-3a57aca9cbff2316a93e4e6e": {
        "locator": "csc411.pdf §17.1 Maximizing the margin, pdf pp. 120-121; §17.3 Loss Functions, pdf pp. 123-124 (perceptron mentioned, not taught); §17.4 The Lagrangian and the Kernel Trick, pdf pp. 125-126",
        "covers": ["knowledge-aml-l07-linear-geometry", "knowledge-aml-l07-kernels"],
    },
    "route-0a14c0a2625dad335f7469e3": {
        "locator": "csc411.pdf §3.3 Artificial Neural Networks for regression, pdf pp. 18-20; §8.3 Artificial Neural Networks for classification, pdf p. 51",
        "covers": ["knowledge-aml-l08-forward", "knowledge-aml-l08-activations", "knowledge-aml-l08-output"],
    },
    "route-cc1692a36cdffbe573dd3279": {
        "title": "CSC411 finite-difference gradient check",
        "angle": "A compact numerical-gradient check and optimization note; it mentions backpropagation but does not derive it.",
        "locator": "csc411.pdf §9.1 Finite differences, pdf pp. 60-61 (backpropagation is identified as efficient derivative computation, not developed)",
        "covers": ["knowledge-aml-l09-gradient-health"],
    },

    # Kroese et al.
    "route-add32fc5153a4c50969e540d": {
        "locator": "kroese.pdf Statistical Learning, pdf pp. 37-76 (training/test loss p. 41; tradeoffs p. 49; cross-validation p. 55); Classification Metrics, pdf pp. 271-274",
    },
    "route-214b495f9a3e48dae5e1dbb2": {
        "locator": "kroese.pdf Cross-Validation, pdf pp. 55-57; K-Nearest Neighbors Classification, pdf pp. 285-286",
    },
    "route-350570d160a9c93e8e15c31b": {
        "locator": "kroese.pdf Regression, pdf pp. 185-232; Linear Regression, pdf pp. 187-205",
    },
    "route-fa5c8cd2be60115843c542e9": {
        "locator": "kroese.pdf Linear Regression, pdf pp. 187-205; Nonlinear Regression Models, pdf pp. 206-208; Regularization, pdf pp. 234-238",
    },
    "route-cba6b8ab6cc94afb1e892c0f": {
        "locator": "kroese.pdf Logistic Regression and Softmax Classification, pdf p. 284",
    },
    "route-d87a2b230c35407d76c77688": {
        "locator": "kroese.pdf Classification Metrics, pdf pp. 271-274; Feed-Forward Neural Networks, pdf pp. 344-348",
    },
    "route-207185556058e90371302703": {
        "locator": "kroese.pdf Back-Propagation, pdf pp. 349-351; Methods for Training, pdf pp. 352-358",
    },
    "route-08a08216d5d79326650ef693": {
        "locator": "kroese.pdf Deep Learning subsection 'convolution neural network', pdf pp. 348-349; §9.5.2 Image Classification, pdf pp. 363-366",
    },

    # CS229 notes.
    "route-eadacb35cc80b4a95220b6e7": {
        "locator": "cs229-notes.pdf pdf pp. 106-111 ('Bias-variance tradeoff'); pdf pp. 130-132 (cross-validation heading)",
    },
    "route-8ec3da0114ef9468d3f63a51": {
        "locator": "cs229-notes.pdf 'LMS algorithm', pdf pp. 10-13; 'The normal equations', pdf pp. 14-15; 'Probabilistic interpretation', pdf pp. 16-17",
    },
    "route-645d8b43b56e2e686b72e717": {
        "locator": "cs229-notes.pdf 'Feature maps', pdf p. 50; 'LMS with features' and 'LMS with the kernel trick', pdf pp. 51-54; 'Regularization', pdf pp. 126-127",
    },
    "route-bd9f3f470427052f4909004e": {
        "locator": "cs229-notes.pdf 'Logistic regression', pdf pp. 21-23; 'Another algorithm for maximizing l(theta)' (Newton), pdf pp. 25-26; 'Constructing GLMs', pdf pp. 29-35",
    },
    "route-f7a2035554358e7bdf8c0472": {
        "locator": "cs229-notes.pdf 'LMS algorithm' batch and stochastic gradient updates, pdf pp. 10-13; 'Regularization', pdf pp. 126-127; cross-validation heading, pdf pp. 130-132",
    },
    "route-7c963103098bcf54f78b7c94": {
        "locator": "cs229-notes.pdf 'Supervised learning with non-linear models', pdf pp. 82-83; 'Neural networks', pdf pp. 84-92; 'Vectorization over training examples', pdf pp. 100-102",
    },
    "route-034d7a304227e9ea24516e86": {
        "locator": "cs229-notes.pdf 'Backpropagation', pdf pp. 93-100; 'The double descent phenomenon', pdf pp. 112-116; 'Regularization', pdf pp. 126-127",
    },

    # Géron, third edition local copy.
    "route-832a42bb1f63ec6ea43fa373": {
        "locator": "geron-copy2.pdf Ch 2 End-to-End Machine Learning Project, pdf pp. 70-155 (Frame the Problem p. 73; Create a Test Set p. 92; cross-validation p. 138; final test p. 147)",
        "vault_path": GERON,
    },
    "route-21d8ed20ec2a60ffd4fabe71": {
        "locator": "geron-copy2.pdf Ch 4 'Linear Regression', pdf pp. 197-203; 'Gradient Descent', pdf pp. 204-215; Exercises, pdf pp. 243-244",
        "vault_path": GERON,
    },
    "route-33a411ac067444cf1a290747": {
        "locator": "geron-copy2.pdf Ch 4 'Polynomial Regression', pdf pp. 216-217; 'Learning Curves', pdf pp. 218-222; 'Regularized Linear Models', pdf pp. 223-231",
        "vault_path": GERON,
    },
    "route-760cfc6e64bcdad0cfffaa15": {
        "locator": "geron-copy2.pdf Ch 4 'Logistic Regression', pdf pp. 232-242 (training and cost p. 234; decision boundaries p. 235; softmax p. 238)",
        "vault_path": GERON,
    },
    "route-be37c217e550b50efbf0cfd3": {
        "locator": "geron-copy2.pdf Ch 4 'Gradient Descent', pdf pp. 204-215 (batch p. 208; stochastic p. 211; mini-batch p. 214)",
        "vault_path": GERON,
    },
    "route-4973b76c89eb8da1abe050fe": {
        "locator": "geron-copy2.pdf Ch 10, 'The Perceptron', pdf pp. 384-390; 'The Multilayer Perceptron and Backpropagation', pdf pp. 391-401; Keras forward models, pdf pp. 402-449",
        "vault_path": GERON,
    },
    "route-f94d721af516f6854fdf31e8": {
        "locator": "geron-copy2.pdf Ch 11 Training Deep Neural Networks, pdf pp. 456-518 (unstable gradients pp. 457-475; optimizers pp. 485-495; regularization pp. 502-514)",
        "vault_path": GERON,
    },
    "route-515ab334a05432e324931153": {
        "locator": "geron-copy2.pdf Ch 14 Deep Computer Vision Using CNNs, pdf pp. 619-698 (visual cortex p. 620; convolution pp. 621-633; pooling pp. 634-639; architectures pp. 640-667; exercises p. 694)",
        "vault_path": GERON,
    },

    # Cornell CS4780 local problem/solution pairs.
    "route-2bae8945210ddd977b807773": {
        "locator": "2018Fall/HW1/hw1_2018.tex and hw1_2018_solution.tex: Problems 1-3 (train/test splits; k-nearest neighbors; curse of dimensionality)",
    },
    "route-3a4b6feb419487c260abc90c": {
        "locator": "2018Fall/HW6/hw6.tex and hw6_solution.tex: Problem 1 'Regularization Mitigates Overfitting' (ridge) and Problem 2 'Bias and Variance in KNN'",
    },
    "route-2637137a9003dac44a7db244": {
        "locator": "2018Fall/HW2/hw2_2018.tex and hw2_2018_solution.tex: Problems 1-4 (perceptron); 2018Fall/HW7/hw7.tex and hw7_solution.tex: Problems 1-2 (kernelized perceptron; constructing kernels), excluding Problem 3 Gaussian processes",
    },
    "route-62bb1d35141bbcdf47a06b0c": {
        "locator": "2018Fall/HW9/hw9.tex and hw9_sol.tex: Problem 3 'RELU-network', parts (a)-(c) (forward pass, boundary, and loss gradient)",
    },
    "route-366bca385def5fe993e5ea6a": {
        "locator": "2018Fall/HW9/hw9.tex and hw9_sol.tex: Problem 3 'RELU-network', part (c) (cross-entropy gradients for W and V)",
    },

    # Kelleher et al.
    "route-b7ad49a27ce531882edd8afe": {
        "locator": "kelleher.pdf Ch 1 Machine Learning for Predictive Data Analytics, pdf pp. 36-56 (§1.2 What Is Machine Learning? p. 39; §1.4 What Can Go Wrong? p. 46)",
    },
    "route-8b24329d3d132e44d2db2bad": {
        "locator": "kelleher.pdf Ch 7 Error-based Learning, pdf pp. 351-413 (§7.2.1 simple linear regression p. 354; §7.2.3 error surfaces p. 360; §7.3 gradient descent p. 362)",
    },
    "route-af0dec1a20a6184eaf0ca273": {
        "locator": "kelleher.pdf Ch 7 Error-based Learning, pdf pp. 351-413 (§7.3.2 gradient descent p. 365; §7.3.3 learning rates p. 371; §7.4.2 weight decay p. 379)",
    },

    # SaD's shared L15 deck.
    "route-2b133f42c89b800e823d83c2": {
        "locator": "lecture-slides/15_neural_networks.pdf, slides 5-9 (one-layer ANN), 10-13 (linear-model restriction and AI winter), and 20 (MLP)",
        "vault_path": SAD,
    },
    "route-b907809826ba756aa1d65f9d": {
        "locator": "lecture-slides/15_neural_networks.pdf, slides 26 (gradient descent) and 30 (training a multilayer perceptron/backpropagation overview)",
        "vault_path": SAD,
    },

    # Zacharski has no outline; these PDF pages were found by exact heading scan.
    "route-142725fc373154de7ce46773": {
        "locator": "Zacharski_Programmers-Guide-to-Data-Mining.pdf Ch 2: 'Manhattan Distance' pdf p. 23; 'Euclidean Distance' pdf p. 24; 'A generalization' (Minkowski) pdf pp. 31-34; nearest-neighbor recommendation code, pdf pp. 35-39",
        "vault_path": ZACH,
    },
}


SPLITS = {
    "route-296d58fc7c7c51f9dc02c203": [
        {
            "id": None,
            "title": "ESL flexibility spectrum: least squares to k-NN",
            "angle": "Places least squares and k-NN on one flexibility axis, making the L02-to-L03 bridge explicit.",
            "angle_detail": "Read this when the apparent opposition between parametric regression and instance-based prediction is still fuzzy. ESL uses the two methods as endpoints of a flexibility spectrum and makes their inductive assumptions comparable; it is mathematical context, not an implementation recipe or the 2026 lecturer's scope authority.",
            "covers": ["knowledge-aml-l02-algorithm", "knowledge-aml-l02-dimensionality"],
            "locator": "esl.pdf §2.3.2 Nearest-Neighbor Methods, pdf pp. 33-34; §2.3.3 From Least Squares to Nearest Neighbors, pdf p. 35",
        },
        {
            "id": None,
            "title": "ESL k-NN variance term",
            "angle": "Derives the k-NN variance term sigma-squared over k instead of leaving the bias-variance claim qualitative.",
            "angle_detail": "This fragment earns its own route because it supplies the formula behind the lecture's qualitative statement that increasing k reduces variance. Use it to reproduce the sigma-squared-over-k argument; move to the separate ESL decomposition route for the full MSE identity and to the course deck for examined notation.",
            "covers": ["knowledge-aml-l02-bias-variance"],
            "locator": "esl.pdf §2.9 Model Selection and the Bias-Variance Tradeoff, pdf pp. 56-57",
        },
        {
            "id": None,
            "title": "ESL bias-variance decomposition",
            "angle": "Gives the rigorous MSE decomposition and a worked comparison of k-NN with linear regression.",
            "angle_detail": "This is the proof-depth route for Bias squared plus Variance plus irreducible noise, with k-NN and linear regression compared inside the same framework. It assumes comfort with expectations and squared error, goes beyond the deck's derivation depth, and does not teach the k-NN search algorithm.",
            "covers": ["knowledge-aml-l02-bias-variance"],
            "locator": "esl.pdf §7.2 Bias, Variance, and Model Complexity, pdf pp. 238-241; §7.3 The Bias-Variance Decomposition, pdf pp. 242-247 (§7.3.1 example p. 245)",
        },
        {
            "id": None,
            "title": "ESL cross-validation rationale",
            "angle": "Explains why k-fold cross-validation estimates generalization error, complementing procedural sources.",
            "angle_detail": "Use this after you can run a train-validation-test split but cannot justify why cross-validation is a reasonable estimator. ESL emphasizes the statistical rationale and its bias, complementing procedural code sources; it is not the place to memorize the lecturer's workflow or choose a library API.",
            "covers": ["knowledge-aml-l02-validation"],
            "locator": "esl.pdf §7.10 Cross-Validation, pdf pp. 260-264",
        },
        {
            "id": None,
            "title": "ESL applied nearest-neighbour classification",
            "angle": "Shows prototype and nearest-neighbour classifiers with decision-boundary examples.",
            "angle_detail": "This later chapter turns nearest neighbours into a classifier with visible decision regions and prototype comparisons. It is useful for geometric intuition after the L02 algorithm is known, but its broader classification setting and notation extend beyond what the current k-NN deck examines.",
            "covers": ["knowledge-aml-l02-algorithm", "knowledge-aml-l02-dimensionality"],
            "locator": "esl.pdf §13.3 Prototypes and Nearest-Neighbors, pdf pp. 482-491",
        },
    ],
    "route-6fb1231d5d6cf9a542e91137": [
        {
            "id": None,
            "title": "ISLP bias-variance and classification setting",
            "angle": "The gentlest entry to the U-shaped test-error curve and its regression/classification distinction.",
            "angle_detail": "Start here when the U-shaped test-error curve is not yet intuitive. ISLP separates regression from classification and explains the flexibility trade-off with lighter algebra than ESL; it prepares the lecture but does not provide the exact L02 algorithm trace or course notation.",
            "covers": ["knowledge-aml-l02-bias-variance"],
            "locator": "islp.pdf §2.2.2 The Bias-Variance Trade-Off, pdf pp. 41-43; §2.2.3 The Classification Setting, pdf pp. 44-48",
        },
        {
            "id": None,
            "title": "ISLP linear regression versus k-NN",
            "angle": "Compares the parametric linear fit and flexible k-NN directly on the same prediction problem.",
            "angle_detail": "This short comparison is the cleanest bridge from L02 to L03: the same prediction setting exposes where a rigid linear model or a flexible neighbourhood model wins. Use it to explain model assumptions, not as a source for implementation details, distance scaling, or validation procedure.",
            "covers": ["knowledge-aml-l02-algorithm", "knowledge-aml-l02-bias-variance"],
            "locator": "islp.pdf §3.5 Comparison of Linear Regression with K-Nearest Neighbors, pdf pp. 120-124",
        },
        {
            "id": None,
            "title": "ISLP k-NN implementation lab",
            "format": "code",
            "angle": "Turns the classifier into an executable lab and makes the decision rule observable in code.",
            "angle_detail": "Run this lab when you want to see the classification rule operate on real data and compare predicted classes. Its value is executable feedback rather than additional theory; the lab's Python workflow is complementary and may not match the lecturer's exact variable names or exam presentation.",
            "depth": "implementation",
            "covers": ["knowledge-aml-l02-algorithm"],
            "locator": "islp.pdf §4.7.6 K-Nearest Neighbors, pdf pp. 192-195",
        },
        {
            "id": None,
            "title": "ISLP validation for choosing k",
            "angle": "Provides the resampling machinery needed to choose k without touching the test set.",
            "angle_detail": "Use these sections to turn the lecture's validation warning into an actual selection protocol for k. They distinguish validation-set, leave-one-out, and k-fold estimates and discuss their bias-variance behavior; the route is broader than the exam's required procedure and should not replace the course deck's split discipline.",
            "covers": ["knowledge-aml-l02-validation"],
            "locator": "islp.pdf §5.1 Cross-Validation, pdf pp. 210-219 (§5.1.3 k-fold p. 214; §5.1.4 bias-variance p. 216)",
        },
    ],
}


# Both local documents were searched in full.  Neither contains a CNN section;
# keeping either route would make its locator and coverage necessarily false.
REMOVE = {
    "route-6d31131942fa99c15b4da015",  # CS229 notes -> L10
    "route-7093e25725cfab05e05ac643",  # CSC411 notes -> L10
}

REBUILD_UNITS = {"unit-aml-l10"}
