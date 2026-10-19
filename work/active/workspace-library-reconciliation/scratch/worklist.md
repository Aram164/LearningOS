# Library reconciliation worklist (disposable; regenerate with `suggest`)


## lr — legacy/LEARNING-RESOURCES.md

L32: ✓ local: root/relative/path.pdf | file lives in the owning module's material folder | path validated by Masters-Planning/tools/check_system.py
    lr:32:p1 [path] root/relative/path.pdf  -> no material match
    lr:32:p2 [path] Masters-Planning/tools/check_system.py  -> no material match
L40: Canonical material-folder layout (enforced 2026-07-10, every module): Lecture-slides/ (course decks) · Buecher//Books/ (books & long texts) · Klausuren-extern/ (solved exams from other unis) · papers/ · exercises keep their course folder (CS4780-homeworks/, B…
    lr:40:p1 [path] Lecture-slides/  -> no material match
    lr:40:p2 [path] Buecher/  -> no material match
    lr:40:p3 [path] Books/  -> no material match
    lr:40:p4 [path] Klausuren-extern/  -> no material match
    lr:40:p5 [path] papers/  -> no material match
    lr:40:p6 [path] CS4780-homeworks/  -> no material match
    lr:40:p7 [path] Bonus-exercises/  -> no material match
    lr:40:p8 [path] Drill-Loesungen/  -> no material match
    lr:40:p9 [path] notes/  -> no material match
    lr:40:p10 [path] SaD-2025/  -> no material match
    lr:40:p11 [path] Masters-Planning/MASTERS-*-RESOURCES.md  -> no material match
L50: [Brandon Rohrer's blog] (https://brandonrohrer.com/blog.html) ⭐ added KW 24 | Visual, from-scratch ML explainers organized as free "book projects." His Under the Hood of Machine Learning series mirrors the AML lecture sequence almost 1:1 — see the mapping tabl…
    lr:50:u1 [url] https://brandonrohrer.com/blog.html  «Brandon Rohrer's blog»  -> title ~ source-rohrer-e2eml (1.00)
L53: [CS231n notes — ConvNets] (https://cs231n.github.io/convolutional-networks/) + [Understanding/Visualizing CNNs] (https://cs231n.github.io/understanding-cnn/) | The standard written CNN reference; covers exactly Task 1.4's methods (saliency, occlusion) + paramet…
    lr:53:u1 [url] https://cs231n.github.io/convolutional-networks/  «CS231n notes — ConvNets»  -> title ~ source-cs231n-notes (1.00)
    lr:53:u2 [url] https://cs231n.github.io/understanding-cnn/  «Understanding/Visualizing CNNs»  -> title ~ source-zeiler-fergus-occlusion (0.67)
L56: [scikit-learn — Underfitting vs. Overfitting] (https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html) + [Ridge/Lasso user guide] (https://scikit-learn.org/stable/modules/linear_model.html) added KW 25 | The degree 1/4/…
    lr:56:u1 [url] https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html  «scikit-learn — Underfitting vs. Overfitting»  -> title ~ source-calmcode-sklearn (0.50), source-data-school-sklearn (0.50), source-python-cheatsheets (0.50)
    lr:56:u2 [url] https://scikit-learn.org/stable/modules/linear_model.html  «Ridge/Lasso user guide»  -> title ~ source-sklearn-user-guide (0.50)
L59: [CS231n notes — Image Classification (k-NN + cross-validation)] (https://cs231n.github.io/classification/) + [Optimization / SGD] (https://cs231n.github.io/optimization-1/) added KW 26 | Course-quality written notes: the k-NN + validation/CV module mirrors L02…
    lr:59:u1 [url] https://cs231n.github.io/classification/  «CS231n notes — Image Classification (k-NN + cross-validation)»
    lr:59:u2 [url] https://cs231n.github.io/optimization-1/  «Optimization / SGD»
L67: [Ch 3: Choosing a loss function] (https://brandonrohrer.com/how_modeling_works_3.html) + [Ch 4: Splitting the data] (https://brandonrohrer.com/how_modeling_works_4.html) | Block D (loss, train/val/test) | AML SaD
    lr:67:u1 [url] https://brandonrohrer.com/how_modeling_works_3.html  «Ch 3: Choosing a loss function»
    lr:67:u2 [url] https://brandonrohrer.com/how_modeling_works_4.html  «Ch 4: Splitting the data»
L68: [Ch 6–9: Optimization methods] (https://brandonrohrer.com/how_optimization_works_1.html) (4 parts, through linear + complex models) | SaD 03 GD → AML L06 | AML SaD
    lr:68:u1 [url] https://brandonrohrer.com/how_optimization_works_1.html  «Ch 6–9: Optimization methods»
L69: [Ch 10: How backpropagation works] (https://brandonrohrer.com/how_backpropagation_works.html) | AML L09 / Block L | AML DL1
    lr:69:u1 [url] https://brandonrohrer.com/how_backpropagation_works.html  «Ch 10: How backpropagation works»
L70: [Ch 11: Decision trees] (https://brandonrohrer.com/how_decision_trees_work.html) | SaD 12 / Block K | SaD
    lr:70:u1 [url] https://brandonrohrer.com/how_decision_trees_work.html  «Ch 11: Decision trees»
L71: [Ch 16: Bayesian inference] (https://brandonrohrer.com/how_bayesian_inference_works.html) | SaD 04/14 / Blocks F+I | SaD
    lr:71:u1 [url] https://brandonrohrer.com/how_bayesian_inference_works.html  «Ch 16: Bayesian inference»
L72: [Ch 17: Fully connected neural networks] (https://brandonrohrer.com/how_neural_networks_work.html) | AML L08 / SaD 15 / Block L | AML SaD
    lr:72:u1 [url] https://brandonrohrer.com/how_neural_networks_work.html  «Ch 17: Fully connected neural networks»  -> title ~ source-3b1b-neural-networks (0.50), source-hinton-nnml (0.50), source-mit-ocw-nn-training (0.50)
L73: [Ch 18: Regularization] (https://brandonrohrer.com/regularization.html) | AML L04 (Ridge/Lasso) + L09 / Blocks H+L | AML
    lr:73:u1 [url] https://brandonrohrer.com/regularization.html  «Ch 18: Regularization»
L74: [Ch 19: Softmax] (https://brandonrohrer.com/softmax.html) | SaD 15 "differentiable argmax" / Block L (Wiring cross-wire #6) | AML SaD
    lr:74:u1 [url] https://brandonrohrer.com/softmax.html  «Ch 19: Softmax»
L75: [Ch 20: Batch normalization] (https://brandonrohrer.com/batch_normalization.html) | AML L09 / CNN training | AML P DL1
    lr:75:u1 [url] https://brandonrohrer.com/batch_normalization.html  «Ch 20: Batch normalization»
L76: [Ch 22: How CNNs work] (https://brandonrohrer.com/how_convolutional_neural_networks_work.html) + [Ch 23: CNNs in depth (video)] (https://youtu.be/JB8T_zN7ZC0) | AML L10 / Block M / Task 1.3-1.4 — the in-depth video is DL.P1.A2 in the DL plan | AML P DL1
    lr:76:u1 [url] https://brandonrohrer.com/how_convolutional_neural_networks_work.html  «Ch 22: How CNNs work»
    lr:76:u2 [url] https://youtu.be/JB8T_zN7ZC0  «Ch 23: CNNs in depth (video)»
L77: [Ch 24: RNNs and LSTM] (https://brandonrohrer.com/how_rnns_lstm_work.html) | AML L11 / Block M | AML
    lr:77:u1 [url] https://brandonrohrer.com/how_rnns_lstm_work.html  «Ch 24: RNNs and LSTM»
L78: [Ch 25: Transformers from scratch] (https://brandonrohrer.com/transformers.html) | AMLS L07 (LLM systems) background + DL 1 | AMLS DL1
    lr:78:u1 [url] https://brandonrohrer.com/transformers.html  «Ch 25: Transformers from scratch»
L79: [Ch 14: 1D convolution] (https://brandonrohrer.com/convolution_one_d.html) + [2D convolution (video)] (https://youtu.be/B-M5q51U8SM) | Convolution arithmetic before AML L10 | AML P
    lr:79:u1 [url] https://brandonrohrer.com/convolution_one_d.html  «Ch 14: 1D convolution»
    lr:79:u2 [url] https://youtu.be/B-M5q51U8SM  «2D convolution (video)»
L80: [Ch 31: CIFAR-10 case study] (https://brandonrohrer.com/cifar) | Same task family as the AMLS project CNN | P
    lr:80:u1 [url] https://brandonrohrer.com/cifar  «Ch 31: CIFAR-10 case study»
L81: [Making Python Faster series] (https://brandonrohrer.com/code_optimization.html) ([multiprocessing] (https://brandonrohrer.com/multiprocessing.html), [threading] (https://brandonrohrer.com/threading.html)) | AMLS parallelism intuition + Stratum/job perf work | A…
    lr:81:u1 [url] https://brandonrohrer.com/code_optimization.html  «Making Python Faster series»
    lr:81:u2 [url] https://brandonrohrer.com/multiprocessing.html  «multiprocessing»
    lr:81:u3 [url] https://brandonrohrer.com/threading.html  «threading»
L82: [How to slice and index pandas DataFrames] (https://brandonrohrer.com/dataframe_indexing.html) | mlprov _getitem_ work + pandas internals | M JK
    lr:82:u1 [url] https://brandonrohrer.com/dataframe_indexing.html  «How to slice and index pandas DataFrames»
L83: Resource lists: [Linear Algebra] (https://brandonrohrer.com/linear_algebra_resources.html) · [Calculus] (https://brandonrohrer.com/calculus_resources.html) · [Statistics] (https://brandonrohrer.com/stats_resources.html) · [NumPy] (https://brandonrohrer.com/numpy_…
    lr:83:u1 [url] https://brandonrohrer.com/linear_algebra_resources.html  «Linear Algebra»  -> title ~ source-3b1b-linear-algebra (1.00), source-mit-1806 (1.00)
    lr:83:u2 [url] https://brandonrohrer.com/calculus_resources.html  «Calculus»
    lr:83:u3 [url] https://brandonrohrer.com/stats_resources.html  «Statistics»
    lr:83:u4 [url] https://brandonrohrer.com/numpy_resources.html  «NumPy»
    lr:83:u5 [url] https://brandonrohrer.com/cpp_resources.html  «C++»
    lr:83:u6 [url] https://brandonrohrer.com/git_resources.html  «Git»
L84: [Matplotlib guides] (https://brandonrohrer.com/matplotlib_just_plot_it.html) | Report figures (AMLS + mlprov experiments) | P M PY
    lr:84:u1 [url] https://brandonrohrer.com/matplotlib_just_plot_it.html  «Matplotlib guides»
L96: [HarvardX STAT110x (Blitzstein)] (https://stat110.hsites.harvard.edu/) · [handouts] (https://stat110.hsites.harvard.edu/handouts) | Rigorous twin of SaD 04–08. High-ROI: Units 3–6. Grab the distribution cheat-sheet early. Mapping in SaD_06-10_DeepPlan §7. | SaD
    lr:96:u1 [url] https://stat110.hsites.harvard.edu/  «HarvardX STAT110x (Blitzstein)»
    lr:96:u2 [url] https://stat110.hsites.harvard.edu/handouts  «handouts»
L97: [Karpathy — Neural Networks: Zero to Hero] (https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ) (micrograd, ~2.5h) | Build autograd from scratch; loss.backward() stops being magic. DL plan Phase 2B. | AML DL1
    lr:97:u1 [url] https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ  «Karpathy — Neural Networks: Zero to Hero»
L98: MIT OCW — Intro to NNs / Training Deep NNs (Aram's playlist #11) | Training dynamics depth (init, vanishing gradients, batch norm). DL plan Phase 2D. | DL1 AML
    lr:98:e1 [entry] MIT OCW — Intro to NNs / Training Deep NNs (Aram's playlist #11)  -> title ~ source-mit-ocw-nn-training (1.00)
L114: ⭐ [Stanford CS229 — Machine Learning (Spring 2022, Tengyu Ma & Chris Ré)] (https://www.youtube.com/playlist?list=PLoROMvodv4rNyWOpJg_Yh4NSqI4Z4vOYy) ([Ng's Autumn-2018 run] (https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU) · [notes] (htt…
    lr:114:u2 [url] https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU  «Ng's Autumn-2018 run»  -> same line as ['source-cs229-2022-videos']
    lr:114:u3 [url] https://cs229.stanford.edu/main_notes.pdf  «notes»  -> same line as ['source-cs229-2022-videos']
L115: ⭐ [MIT 6.036 — Introduction to Machine Learning (Open Learning Library, 2019)] (https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/) — AML spine | Full applied ML course with auto-graded exercises: k-NN, perceptron, features, logist…
    lr:115:u1 [url] https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/  «MIT 6.036 — Introduction to Machine Learning (Open Learning Library, 2019)»  -> title ~ source-mit-6036 (1.00), source-google-ml-crash-course (0.50), source-mit-6s191 (0.50)
L116: [Andrew Ng — Machine Learning (Stanford/Coursera 2011, full 103-video mirror)] (https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX) ([materials] (https://github.com/blitz70/ML)) added KW 25 | Linear regression + GD + normal equation → E (A…
    lr:116:u1 [url] https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX  «Andrew Ng — Machine Learning (Stanford/Coursera 2011, full 103-video mirror)»  -> same line as ['source-ng-coursera']; title ~ source-ng-coursera (1.00), source-cs229-notes (0.50), source-google-ml-crash-course (0.50)
L119: [Kurzes Tutorium Statistik (Mathias Bärtl, HS Offenburg)] (https://www.youtube.com/channel/UCtBEklAtHHji2V1TsaTzZXw) ⭐ added KW 27 | Playlists: deskriptive Statistik → SaD 01–02; Wahrscheinlichkeitsrechnung → 04–05; Parameterschätzung → 09; Testtheorie → 10 |…
    lr:119:u1 [url] https://www.youtube.com/channel/UCtBEklAtHHji2V1TsaTzZXw  «Kurzes Tutorium Statistik (Mathias Bärtl, HS Offenburg)»  -> title ~ source-baertl-statistik-buch (0.75), source-kurzes-tutorium-statistik (0.67)
L122: [UMich EECS 498-007 — Deep Learning for Computer Vision (Justin Johnson)] (https://www.youtube.com/playlist?list=PL5-TkQAfAZFbzxjBHtzdVCWE0Zbhomg7r) ([course site] (https://web.eecs.umich.edu/~justincj/teaching/eecs498/FA2020/)) | L5 Neural Networks + L6 Backpr…
    lr:122:u2 [url] https://web.eecs.umich.edu/~justincj/teaching/eecs498/FA2020/  «course site»  -> same line as ['source-eecs498']
L124: [CMU 10-414/714 — Deep Learning Systems (Tianqi Chen, Zico Kolter)] (https://dlsyscourse.org/lectures/) ([YouTube] (https://www.youtube.com/playlist?list=PLGzYMymX8amNyGPuJ35YWdq59eQ5jYCZ1)) ⭐ | Autodiff/computation graphs → S.B + AML L09; hardware acceleration…
    lr:124:u1 [url] https://dlsyscourse.org/lectures/  «CMU 10-414/714 — Deep Learning Systems (Tianqi Chen, Zico Kolter)»  -> title ~ source-cmu-10414 (1.00), source-mit-6s191 (0.50), source-mlc-book (0.50)
    lr:124:u2 [url] https://www.youtube.com/playlist?list=PLGzYMymX8amNyGPuJ35YWdq59eQ5jYCZ1  «YouTube»
L129: [MIT 18.100A — Real Analysis (Casey Rodriguez, F2020)] (https://www.youtube.com/watch?v=LY7YmuDbuW0&list=PLUl4u3cNGP61O7HkcF7UImpM0cR_L2gSw) ([notes: Plans/Math/analysis/Analysis/Buecher/mit18_100af20_lec_full2.pdf, local]) ⭐ added KW 24 | Rigor layer for the…
    lr:129:u1 [url] https://www.youtube.com/watch?v=LY7YmuDbuW0&list=PLUl4u3cNGP61O7HkcF7UImpM0cR_L2gSw  «MIT 18.100A — Real Analysis (Casey Rodriguez, F2020)»  -> title ~ source-mit-18100a (0.67)
L131: Daniel Jung + MathePeter (YouTube, DE) added KW 27 | 5-min German single-topic explainers (ε-N, Konvergenzkriterien, l'Hospital, partielle Integration) — quick unblocks in Klausur vocabulary, not systematic study. | AN
    lr:131:e1 [entry] Daniel Jung + MathePeter (YouTube, DE) added KW 27  -> title ~ source-daniel-jung (0.60)
L138: Pagh [2006] Cuckoo Hashing for Undergraduates + Sleator/Tarjan [1985] (both on Algo2-Moodle, also public) | THE primary texts for AL.F and AL.E2 per the course itself — short, readable originals. | AL
    lr:138:e1 [entry] Pagh [2006] Cuckoo Hashing for Undergraduates + Sleator/Tarjan [1985] (both on Algo2-Moodle, also public)  -> title ~ source-pagh-cuckoo-hashing (0.80)
L142: Saved per Aram's request from MIT Open Learning's ["7 free online MIT courses to grasp machine learning"] (https://medium.com/open-learning/7-free-online-mit-courses-to-grasp-machine-learning-3ef5d819bbd8). These are for later / general ML depth & the job, not…
    lr:142:u1 [url] https://medium.com/open-learning/7-free-online-mit-courses-to-grasp-machine-learning-3ef5d819bbd8  «"7 free online MIT courses to grasp machine learning"»  -> title ~ source-rohrer-e2eml (0.60), source-google-ml-crash-course (0.50), source-ng-coursera (0.50)
L146: [Introduction to Machine Learning] (https://learn.mit.edu/search?resource=16193) | The OCW/MITx catalog entry for MIT 6.036 — i.e. the AML-spine course above (principles, over-fitting, generalization, supervised + RL). Listed for completeness; you're already u…
    lr:146:u1 [url] https://learn.mit.edu/search?resource=16193  «Introduction to Machine Learning»  -> title ~ source-mit-6036 (1.00), source-mlsysbook-vol1 (1.00), source-murphy-pml1 (1.00)
L162: ISLP — Introduction to Statistical Learning (Python) | The textbook spine of Chat1; chapter map lives in Chat1 + Master Wiring §1, and the per-concept map in the L02–L10 crosswalk above. Also SaD 12 (trees: §8.1–8.2 verified) + SaD 14 (NB: §4.4.4 p.158). | AM…
    lr:162:e1 [entry] ISLP — Introduction to Statistical Learning (Python)  -> title ~ source-islp (0.80), source-mit-6s191 (0.50)
L164: Blitzstein & Hwang — Introduction to Probability (2nd ed.) ✓ on Aram's Drive ([file] (https://drive.google.com/file/d/1VmkAAGOYCTORq1wxSQqy255qLJjTNvBI/edit); [official source] (https://projects.iq.harvard.edu/stat110/home)) — drop a copy into SaD/Books/ for of…
    lr:164:u1 [url] https://drive.google.com/file/d/1VmkAAGOYCTORq1wxSQqy255qLJjTNvBI/edit  «file»
    lr:164:u2 [url] https://projects.iq.harvard.edu/stat110/home  «official source»
    lr:164:p1 [path] SaD/Books/  -> no material match
L166: Dekking, Kraaikamp, Lopuhaä & Meester — A Modern Introduction to Probability and Statistics (Springer) ⭐ added KW 27 | The full SaD-stats arc in ONE book (probability → RVs → distributions → LLN/CLT → estimation → testing → regression), Informatiker-friendly…
    lr:166:e1 [entry] Dekking, Kraaikamp, Lopuhaä & Meester — A Modern Introduction to Probability and Statistics (Springer) ⭐ added KW 27  -> title ~ source-dekking-mips (0.80), source-mit-1805 (0.75)
L167: Henze — Stochastik für Einsteiger (Springer, DE) added KW 27 | German rigor alternative for the probability half (SaD 04–08) with exercises + Lösungen; same Springer-license route. Use if Fahrmeir's probability chapters feel thin. | SaD
    lr:167:e1 [entry] Henze — Stochastik für Einsteiger (Springer, DE) added KW 27  -> title ~ source-henze-stochastik (0.80)
L169: Tijms — Understanding Probability (2nd ed.) (Cambridge, 2007) ✓ local (Plans/Math/sad/SaD/Books/Tijms - Understanding Probability…(Cambridge, 2007).pdf) added KW 29 (Jul 14) | The most narrative, least formula-heavy of the set — builds intuition through every…
    lr:169:p1 [path] Plans/Math/sad/SaD/Books/Tijms - Understanding Probability…(Cambridge, 2007).pdf  -> no material match
L172: Grinstead & Snell — Introduction to Probability (AMS, free/open-access) ❌ NOT yet local — the one missing from the Jul 14 batch (recommended KW 29, download never landed) | The gentle, computation-flavored free book — lots of worked examples + simulation. Fre…
    lr:172:p1 [path] SaD/Books/  -> no material match
L173: [Nielsen — Neural Networks and Deep Learning] (http://neuralnetworksanddeeplearning.com/chap1.html) (free) | Ch 1–3 + 6 phased in DL-AMLS-Learning-Plan; Ch 2 = backprop rigor for AML L09. | AML P DL1
    lr:173:u1 [url] http://neuralnetworksanddeeplearning.com/chap1.html  «Nielsen — Neural Networks and Deep Learning»  -> title ~ source-nielsen-nndl (1.00), source-hinton-nnml (0.60), source-mit-ocw-nn-training (0.60)
L174: Ramalho — Fluent Python (Plans/Programming/python/Python/, local) | The PY track; reading order in HANDOFF. | PY M
    lr:174:p1 [path] Plans/Programming/python/Python/  -> no material match
L176: Murphy — Probabilistic Machine Learning: An Introduction (MIT Press 2022, local: Plans/ML/foundations/AML/Bücher/probabilistic ML.pdf, 860 pp) + solutions (…/Bücher/Probabilistic-ML-solutions-public.pdf) · [book source] (https://github.com/probml/pml-book/rele…
    lr:176:u1 [url] https://github.com/probml/pml-book/releases/latest/download/book1.pdf  «book source»
    lr:176:u2 [url] https://probml.github.io/pml-book/solns-public.pdf  «solutions source»
    lr:176:p2 [path] …/Bücher/Probabilistic-ML-solutions-public.pdf  -> no material match
L178: Toronto CSC411 — Machine Learning and Data Mining lecture notes | local: Plans/ML/foundations/AML/Bücher/Machine Learning and Data Mining Lecture Notes CSC 411…pdf. Concise notes on k-NN, linear/logistic regression, NNs — compact second telling of the AML L02…
    lr:178:p1 [path] Plans/ML/foundations/AML/Bücher/Machine Learning and Data Mining Lecture Notes CSC 411…pdf  -> no material match
L181: CLRS — Introduction to Algorithms (Cormen et al.; DE 4. Aufl. = EN 3rd ed.) | local: Plans/CS-Theory/algo2/Algo2/Buecher/Algo-Buch.pdf (DE 4.A.) + …/Introduction_to_algorithms-3rd Edition…pdf (EN 3rd). The HU AlgoDat II base text. | AL
    lr:181:p2 [path] …/Introduction_to_algorithms-3rd Edition…pdf  -> no material match
L182: DMS — Dietzfelbinger, Mehlhorn & Sanders, Algorithmen u. Datenstrukturen: Die Grundwerkzeuge (eXamen.press) · OW — Ottmann & Widmayer, Algorithmen und Datenstrukturen | local: …/algo2/Algo2/Buecher/AlgoBuch 2.pdf (DMS) + …/Algorithmen und Datenstrukturen.pdf…
    lr:182:p1 [path] …/algo2/Algo2/Buecher/AlgoBuch 2.pdf  -> no material match
    lr:182:p2 [path] …/Algorithmen und Datenstrukturen.pdf  -> no material match
L187: ✓ local: Plans/ML/foundations/AML/Bücher/Sutton-Barto_Reinforcement-Learning_2ed.pdf (548pp) · [Sutton & Barto — Reinforcement Learning: An Introduction (2nd ed.)] (http://incompleteideas.net/book/RLbook2018trimmed.pdf) added KW 29 (Stony Brook ML page) | The…
    lr:187:u1 [url] http://incompleteideas.net/book/RLbook2018trimmed.pdf  «Sutton & Barto — Reinforcement Learning: An Introduction (2nd ed.)»  -> title ~ source-sutton-barto-rl (1.00), source-mit-6s191 (0.50)
L188: ✓ local (notebooks): Plans/Programming/python/Python/PythonDataScienceHandbook/notebooks/ (67 .ipynb) · [prose web book] (https://jakevdp.github.io/PythonDataScienceHandbook/) — VanderPlas Python Data Science Handbook · added KW 29 (Stony Brook ML page) | NumP…
    lr:188:u1 [url] https://jakevdp.github.io/PythonDataScienceHandbook/  «prose web book»
    lr:188:p1 [path] Plans/Programming/python/Python/PythonDataScienceHandbook/notebooks/  -> no material match
L200: Géron — Hands-On ML with Scikit-Learn, Keras & TensorFlow (3rd ed., O'Reilly) | ✓ local: Plans/Programming/python/Python/Geron_Hands-On-ML_Scikit-Learn-Keras-TensorFlow.pdf (+ copy in AMLS learningcontent/) | Best practical bridge across three of your tracks…
    lr:200:p2 [path] learningcontent/  -> no material match
L202: ⭐ Boehm, Kumar & Yang — Data Management in ML Systems (Synthesis Lectures 2019, ~173pp) added KW 27 | 🏛️ Springer campus license (same route as Forster/Abbott) — pull it | The AMLS lecturer's own book — rewrites, op selection/fusion, parallel execution, param…
    lr:202:e1 [entry] ⭐ Boehm, Kumar & Yang — Data Management in ML Systems (Synthesis Lectures 2019, ~173pp) added KW 27  -> title ~ source-dmmls-boehm (0.60)
L203: ⭐ MLSysBook Vol 1 + Vol 2 (Reddi, MIT Press 2026/2027) added KW 27 | ✓ local: Plans/ML/systems/AMLS/learningcontent/Buecher/MLSysBook-Vol1-2026.pdf (1036pp) + MLSysBook-Vol2-AtScale-2026.pdf (1170pp) — 🆓 [mlsysbook.ai] (https://mlsysbook.ai/book/) | The single…
    lr:203:u1 [url] https://mlsysbook.ai/book/  «mlsysbook.ai»
L205: 🆓 MLC — Machine Learning Compilation (Tianqi Chen, [book.mlc.ai] (https://mlc.ai/courses.html)) added KW 27 | free, executable Jupyter chapters | Compilation lectures (AMLS 03–04) as runnable notebooks (TVM): rewrites, fusion, automatic optimization — the "do"…
    lr:205:u1 [url] https://mlc.ai/courses.html  «book.mlc.ai»
L206: Huyen — AI Engineering (O'Reilly 2025) added KW 27 | 💰/🏛️ O'Reilly | LLM inference-optimization + serving chapters only (AMLS 07/13) — optional depth, job-relevant, not exam-critical. | AMLS JK
    lr:206:e1 [entry] Huyen — AI Engineering (O'Reilly 2025) added KW 27  -> title ~ source-huyen-ai-engineering (0.80)
L207: Kelleher, Mac Namee & D'Arcy — FMLPDA ✓ OWNED, local (Plans/Math/sad/SaD/Books/Fundamentals of Machine Learning…(2015).pdf, Jul 2) | Hypothesis CONFIRMED from the book's TOC: Ch 4–7 (information/similarity/probability/error-based) = SaD 12–15 one-to-one — it…
    lr:207:p1 [path] Plans/Math/sad/SaD/Books/Fundamentals of Machine Learning…(2015).pdf  -> no material match
L208: Freedman, Pisani & Purves — Statistics (Norton, 4th ed., ~€60 / used cheap) added KW 27 | the classic intuition-first statistics book — box models, chance errors, tests explained in words before formulas | The famous "different aspect": where Fahrmeir gives t…
    lr:208:e1 [entry] Freedman, Pisani & Purves — Statistics (Norton, 4th ed., ~€60 / used cheap) added KW 27  -> title ~ source-fpp-statistics (0.67)
L209: Bärtl — Statistik Schritt für Schritt (~€20) added KW 27 | the companion book to the Kurzes Tutorium Statistik channel (§2) | Cheap German written twin of the DE video layer — same everyday-problem style, Klausur vocabulary. | SaD
    lr:209:e1 [entry] Bärtl — Statistik Schritt für Schritt (~€20) added KW 27  -> title ~ source-baertl-statistik-buch (0.75), source-kurzes-tutorium-statistik (0.50)
L210: Bishop — PRML (Murphy & ESL now have their own rows in §3 above) | €0 | Not a paid recommendation — this classic has a legal free PDF (Microsoft). Listed so nobody buys it by accident. | AML DL1
    lr:210:e1 [entry] Bishop — PRML (Murphy & ESL now have their own rows in §3 above)
L221: [sklearn Getting Started] (https://scikit-learn.org/stable/getting_started.html) + [Developing estimators] (https://scikit-learn.org/stable/developers/develop.html) + [compose guide] (https://scikit-learn.org/stable/modules/compose.html) + [mixed-types CT exampl…
    lr:221:u1 [url] https://scikit-learn.org/stable/getting_started.html  «sklearn Getting Started»
    lr:221:u2 [url] https://scikit-learn.org/stable/developers/develop.html  «Developing estimators»
    lr:221:u3 [url] https://scikit-learn.org/stable/modules/compose.html  «compose guide»
    lr:221:u4 [url] https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html  «mixed-types CT example»
L224: [skrub] (https://github.com/skrub-data/skrub) + local refs Plans/Libraries/skrub/skrub-DataOp-DAG-Reference.md, Plans/Libraries/skrub/skrub-Evaluation-Engine-Reference.md | Job: DataOps DAG + evaluation engine references. | JK
    lr:224:u1 [url] https://github.com/skrub-data/skrub  «skrub»
L225: Stratum repo (Plans/crosscutting/job/Job/repo/stratum/, local) + paper | Job onboarding core. | JK
    lr:225:p1 [path] Plans/crosscutting/job/Job/repo/stratum/  -> no material match
L227: 🔧 [scikit-learn algorithm cheat-sheet (estimator map)] (https://scikit-learn.org/stable/tutorial/machine_learning_map/index.html) added KW 29 (Stony Brook ML page) | The "which estimator?" flowchart — quick model-selection reference for mlprov + AML. | M AML
    lr:227:u1 [url] https://scikit-learn.org/stable/tutorial/machine_learning_map/index.html  «scikit-learn algorithm cheat-sheet (estimator map)»  -> title ~ source-calmcode-sklearn (0.50)
L228: ✓ local: Plans/Programming/python/Python/cheatsheets/ — sgfin cheat-sheets (NumPy · Pandas · Scikit-Learn · Keras · Graphic-Design) added KW 29 (Stony Brook ML page) | One-page API references for the daily Python-ML stack; the graphic-design one is for clean…
    lr:228:p1 [path] Plans/Programming/python/Python/cheatsheets/  -> no material match
L229: 🔧 [scikit-learn — full User Guide] (https://scikit-learn.org/stable/user_guide.html) + [examples gallery] (https://scikit-learn.org/stable/auto_examples/index.html) + [docs PDF] (https://scikit-learn.org/stable/downloads/scikit-learn-docs.pdf) added KW 29 (Stony…
    lr:229:u3 [url] https://scikit-learn.org/stable/_downloads/scikit-learn-docs.pdf  «docs PDF»  -> same line as ['source-sklearn-user-guide']
L231: 🔧 [Stanford CS229 project archive] (http://cs229.stanford.edu/projects.html) + [CS230 past projects] (https://cs230.stanford.edu/past-projects/) added KW 29 (Stony Brook ML page) | Hundreds of short project reports — idea/scoping bank for the AMLS project and t…
    lr:231:u1 [url] http://cs229.stanford.edu/projects.html  «Stanford CS229 project archive»  -> same line as ['source-cs229-project-archive']; title ~ source-cs229-project-archive (1.00), source-cs229-2022-videos (0.50), source-cs229-notes (0.50)
L246: Zeiler & Fergus 2014 (occlusion) — skim figures | Origin of occlusion analysis; one good figure for the report. | P
    lr:246:e1 [entry] Zeiler & Fergus 2014 (occlusion) — skim figures  -> title ~ source-zeiler-fergus-occlusion (0.50)
L249: Belkin et al. 2019 — double descent (PNAS) | Cited in AML L09; the modern correction to the bias-variance U-curve. | AML DL1
    lr:249:e1 [entry] Belkin et al. 2019 — double descent (PNAS)  -> title ~ source-belkin-double-descent (0.60)
L250: Buneman, Khanna & Tan 2001 — Why and Where: A Characterization of Data Provenance | local: Plans/ML/mlprov/PPDS ML Data Provenance/( Paper 2 )Buneman_WhyAndWhere_Provenance_paper.pdf (dup copy Why and Where…pdf). Foundational why/where-provenance paper — the…
    lr:250:p1 [path] Plans/ML/mlprov/PPDS ML Data Provenance/( Paper 2 )Buneman_WhyAndWhere_Provenance_paper.pdf  -> no material match
L251: Data Distribution Debugging in Machine Learning Pipelines (mlinspect-family) | local: Plans/ML/mlprov/PPDS ML Data Provenance/(Paper 1 ) Data distribution debugging in machine learning pipelines.pdf. Motivation paper for instrumenting ML pipelines — directly…
    lr:251:p1 [path] Plans/ML/mlprov/PPDS ML Data Provenance/(Paper 1 ) Data distribution debugging in machine learning pipelines.pdf  -> no material match
L261: [Harvard Stat 110 — Strategic Practice + Homework with solutions] (https://stat110.hsites.harvard.edu/strategic-practice-problems) | Official, free, topic-organized problem sets, each with full solutions (Blitzstein). Conditioning, Bayes, Binomial, joint/condi…
    lr:261:u1 [url] https://stat110.hsites.harvard.edu/strategic-practice-problems  «Harvard Stat 110 — Strategic Practice + Homework with solutions»  -> title ~ source-stat110 (0.60)
L263: [MIT 6.034 Artificial Intelligence — past exams (OCW)] (https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/pages/exams/) (also [Spring 2005 set] (https://ocw.mit.edu/courses/6-034-artificial-intelligence-spring-2005/pages/exams/)) | Years of qu…
    lr:263:u1 [url] https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/pages/exams/  «MIT 6.034 Artificial Intelligence — past exams (OCW)»  -> title ~ source-mit-6034-quizzes (0.75)
    lr:263:u2 [url] https://ocw.mit.edu/courses/6-034-artificial-intelligence-spring-2005/pages/exams/  «Spring 2005 set»
    lr:263:u3 [url] https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/4a2ea7a8b0ab11a40e0f1a0093a78865_MIT6_034F10_quiz3_2010.pdf  «PDF»
    lr:263:u4 [url] https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/5c0e73c065cc8ae4c2a1899e4d4417f7_MIT6_034F10_quiz3_2007.pdf  «PDF»
L266: Cornell CS4780 (Weinberger) — local homework set ⭐ added KW 25 ([source notes] (https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/index.html)) | Plans/ML/foundations/AML/CS4780-homeworks/ — 3 semesters (2017Spring HW1–6, 2018Fall + 2018Spring HW1–9), e…
    lr:266:p2 [path] README.md  -> material candidates: source-cs4780-homeworks, source-pydata-handbook, source-python-depth-drills
L268: [MIT 6.036/6.390 — Intro to ML, Open Learning Library] (https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/) — auto-graded ⭐ added KW 25 | Free interactive course with auto-graded homework (immediate feedback — best self-check forma…
    lr:268:u1 [url] https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/  «MIT 6.036/6.390 — Intro to ML, Open Learning Library»  -> same line as ['source-mit-6036']; title ~ source-mit-6036 (0.67)
L273: 1. AML + SaD Moodle — check for Probeklausur/Altklausur uploads as the exam approaches; UE solutions are usually walked through in the Übung — collect them there.
    lr:273:e1 [entry] AML + SaD Moodle
L274: 2. Ask the Fachschaft Informatik (HU) for AML/SaD Gedächtnisprotokolle/Altklausuren — student councils typically keep an exam archive that never appears on Google.
    lr:274:e1 [entry] Ask the Fachschaft Informatik (HU)
L275: 3. Ask Abdalla/teammates and last-year students — the SaD-2025 materials in this folder came from somewhere; the same source may have the 2025 exams.
    lr:275:e1 [entry] Ask Abdalla/teammates and last-year students — the SaD-2025 materials in this folder came from somewhere; the same sour…
L283: ✅📁 FAU Erlangen — Klausur Statistik WS14/15, Aufgaben UND Lösung — local Jul 2: Plans/Math/sad/SaD/Klausuren-extern/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf ([source] (https://www.statistik.rw.fau.de/files/2019/10/WS_14_15.pdf)) ⭐ | Two complet…
    lr:283:p2 [path] …/files/…  -> no material match
L284: ✅📁 Uni Köln — Musterlösung Klausur — local Jul 2: …SaD/Klausuren-extern/Koeln_Statistik-Klausur_Musterloesung.pdf ([source] (https://wisostat.uni-koeln.de/fileadmin/sites/statistik/pdf/MustLoesStatBSS13.pdf)) | Solved Klausur (WiSo-Statistik) | N2–N4 | SaD
    lr:284:u1 [url] https://wisostat.uni-koeln.de/fileadmin/sites/statistik/pdf/MustLoesStatBSS13.pdf  «source»
L285: ✅📁 Regensburg (Löh) — Klausur W-Theorie & Statistik, solved — local Jul 2: …SaD/Klausuren-extern/Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf ([source] (https://loeh.app.uni-regensburg.de/teaching/probthy_ss12/klausur_solv.pdf)) | Solved exam f…
    lr:285:u1 [url] https://loeh.app.uni-regensburg.de/teaching/probthy_ss12/klausur_solv.pdf  «source»
L289: Also testing-bearing (from §3): Dekking ⭐ (~300 exercises w/ answers) · Fahrmeir Arbeitsbuch (Open Loop #4) · Schaum's Outline of Probability (solved-problem bank, local KW 29) · Ross — First Course (worked-example heavy, local KW 29) · plus the existing 18.0…
    lr:289:p1 [path] Plans/Math/sad/SaD/Klausuren-extern/  -> no material match
L293: Same logic as above: no public HU ana_inf Altklausuren (the serie sheets + kleine_beweise.pdf in Plans/Math/analysis/Analysis/ are the HU-internal material). The bank below is solved exam material from other German unis + MIT, matched to the AN blocks. ✅ = fe…
    lr:293:p2 [path] Plans/Math/analysis/Analysis/  -> no material match
L297: ✅📁 Marburg — 3 komplette Analysis-I-Klausuren mit Lösungen — downloaded KW 24: Plans/Math/analysis/Analysis/Klausuren-extern/Marburg_Analysis-I_3-Klausuren-mit-Loesungen.pdf ([source] (https://www.mathematik.uni-marburg.de/~portenier/Analyse/Uebungen/klau-i.pd…
    lr:297:u1 [url] https://www.mathematik.uni-marburg.de/~portenier/Analyse/Uebungen/klau-i.pdf  «source»
L298: ✅📁 Regensburg — Analysis I Klausur mit Lösungen + „Häufige Fehler" — downloaded KW 24: Plans/Math/analysis/Analysis/Klausuren-extern/Regensburg_Analysis-I_Klausur-mit-Loesungen-und-Haeufige-Fehler.pdf ([source] (https://loeh.app.uni-regensburg.de/teaching/anal…
    lr:298:u1 [url] https://loeh.app.uni-regensburg.de/teaching/analysis1_ss11/klausur_solv.pdf  «source»
L299: ✅📁 MIT 18.100C F12 exam set — local Jul 2 in …analysis/Analysis/Klausuren-extern/ (MIT18100C_Final.pdf + Final-Solutions + Practice-Final + Practice-Midterm1/2 + Midterm2; [psets] (https://ocw.mit.edu/courses/18-100c-real-analysis-fall-2012/pages/assignments/)…
    lr:299:u1 [url] https://ocw.mit.edu/courses/18-100c-real-analysis-fall-2012/pages/assignments/  «psets»
    lr:299:u2 [url] https://ocw.mit.edu/courses/18-100c-real-analysis-fall-2012/resources/mit18_100cf12_final/  «solved practice final»
    lr:299:p1 [path] …analysis/Analysis/Klausuren-extern/  -> no material match
L300: [MIT 18.100A F20 — assignments page (OCW)] (https://ocw.mit.edu/courses/18-100a-real-analysis-fall-2020/pages/assignments-and-exams/) | The psets matching Rodriguez's lectures (the ones mapped in the AN plan). Solutions not posted → use as extra problems, chec…
    lr:300:u1 [url] https://ocw.mit.edu/courses/18-100a-real-analysis-fall-2020/pages/assignments-and-exams/  «MIT 18.100A F20 — assignments page (OCW)»
    lr:300:u2 [url] https://github.com/dkaysin/MIT-18.100B-Analysis-I-solutions  «community 18.100B solutions repo»  -> title ~ source-islp-community-solutions (0.50)
L307: Mapping into the plan: Marburg ⭐ feeds AN.A4/B3/C3 drill; Regensburg ⭐ feeds AN.E4/G4 and is the model for AN.X4's self-assembled mock; the rest are backup volume. ✅ Both ⭐ PDFs downloaded into Plans/Math/analysis/Analysis/ (KW 24) — link rot no longer a risk.
    lr:307:p1 [path] Plans/Math/analysis/Analysis/  -> no material match
L317: ✅📁 Goethe Frankfurt B-ALGO-2 — ALL Klausuren 2021–2024 with Lösungsvorschläge — local KW 24: Plans/CS-Theory/algo2/Algo2/Frankfurt-Klausuren/ (8 PDFs, each = full Klausur with embedded Lösungsskizze) ([source] (https://files.tcs.uni-frankfurt.de/algo2/exams/))…
    lr:317:u1 [url] https://files.tcs.uni-frankfurt.de/algo2/exams/  «source»  -> same line as ['source-frankfurt-algo2-course']
L320: [Frankfurt ALGO2 Übungsblätter] (https://goethe-tcs.github.io/algo2-exercises/ALGO2-Blatt-02-Netzwerkfluss-I.pdf) (Blatt 1 APSP · [2] (https://goethe-tcs.github.io/algo2-exercises/ALGO2-Blatt-02-Netzwerkfluss-I.pdf)+[3] (https://goethe-tcs.github.io/algo2-exerci…
    lr:320:u1 [url] https://goethe-tcs.github.io/algo2-exercises/ALGO2-Blatt-02-Netzwerkfluss-I.pdf  «Frankfurt ALGO2 Übungsblätter»  -> title ~ source-frankfurt-algo2-course (1.00)
    lr:320:u2 [url] https://goethe-tcs.github.io/algo2-exercises/ALGO2-Blatt-02-Netzwerkfluss-I.pdf  «2»
    lr:320:u3 [url] https://goethe-tcs.github.io/algo2-exercises/ALGO2-Blatt-03-Netzwerkfluss-II.pdf  «3»
    lr:320:u4 [url] https://goethe-tcs.github.io/algo2-exercises/ALGO2-Blatt-04-Amortisierte-Analyse.pdf  «4»
L327: [KIT Algorithmen 2 — Sanders, WS17/18 (YouTube, German)] (https://www.youtube.com/playlist?list=PLfk0Dfh13pBNyD4E0lUbTe3o4nvRwexRv) ⭐ ([course page] (https://ae.iti.kit.edu/english/4046.php)) | Flows & matchings → AL.H/I; computational geometry (convex hull, ra…
    lr:327:u2 [url] https://ae.iti.kit.edu/english/4046.php  «course page»  -> same line as ['source-kit-algorithmen2']
L329: [CMU 15-451 — splay tree lecture notes] (https://www.cs.cmu.edu/~15451-f23/lectures/lecture08-splay-trees.pdf) ([older full notes] (http://www.cs.cmu.edu/afs/cs/academic/class/15451-s16/www/lectures/451-spring16.pdf)) | AL.E (access lemma proof, written by Slea…
    lr:329:u2 [url] http://www.cs.cmu.edu/afs/cs/academic/class/15451-s16/www/lectures/451-spring16.pdf  «older full notes»  -> same line as ['source-cmu-15451-splay-notes']
L340: ✅ [MIT 6.172 Performance Engineering — 4 practice quizzes WITH solutions (OCW)] (https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/pages/quizzes/) ⭐ | Real exam-style questions w/ answer keys: caching/locality, ILP/vectori…
    lr:340:u1 [url] https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/pages/quizzes/  «MIT 6.172 Performance Engineering — 4 practice quizzes WITH solutions (OCW)»  -> title ~ source-mit-6172 (0.60)
L343: [MLSysBook.ai (Harvard CS249r book)] (https://mlsysbook.ai) — built-in SocratiQ quizzes · ✓ local PDFs (updated KW 27): Plans/ML/systems/AMLS/learningcontent/Buecher/MLSysBook-Vol1-2026.pdf + MLSysBook-Vol2-AtScale-2026.pdf (old Intro-Machine-Learning-Systems.…
    lr:343:u1 [url] https://mlsysbook.ai  «MLSysBook.ai (Harvard CS249r book)»
    lr:343:p3 [path] Intro-Machine-Learning-Systems.pdf  -> no material match
L344: Boehm SS23 lecture recordings (see §2 ⭐ entry) | Not solved material, but enables the strongest S.X drill: watch a lecture section → pause → re-explain aloud → compare. | all 12 | AMLS
    lr:344:e1 [entry] Boehm SS23 lecture recordings (see §2 ⭐ entry)
L353: Seminar Moodle + topic list (links in HANDOFF) | Course logistics. | SE
    lr:353:e1 [entry] Seminar Moodle + topic list (links in HANDOFF)
L381: [Philip Guo — CPython internals, 10h lecture series] (https://pgbovine.net/cpython-internals.htm) | Line-by-line C walkthrough of CPython. Cherry-pick L1 (overview), L3 (frames/calls/scope), L8 (user-defined classes). Old (Py 2.7) but the architecture stands.…
    lr:381:u1 [url] https://pgbovine.net/cpython-internals.htm  «Philip Guo — CPython internals, 10h lecture series»  -> title ~ source-guo-cpython-internals (0.83)
L385: Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md §7, Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md §5–7, Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md §2/§5, Plans/ML/systems/DL-AMLS-Learning-Plan.md, and links…
    lr:385:p5 [path] ML-Semester-Master-Plan copy 2.md  -> no material match

## m-algo — repository/curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning/inputs/MASTERS-ALGO-RESOURCES.md

L13: 📚 Kleinberg/Tardos, „Algorithm Design" — das beste Lehrbuch für genau diesen Zuschnitt: NP-Härte → was nun? (Approximation Kap. 11, Randomisierung Kap. 13, Local Search) — mit den lehrreichsten Übungsaufgaben des Genres. Einsatz: Hauptbuch; die Aufgaben sind…
    m-algo:13:e1 [entry] Kleinberg/Tardos, „Algorithm Design"  -> title ~ source-kleinberg-tardos (1.00), source-wayne-kt-slides (0.50)
L14: 🎓 Stanford CS261 „A Second Course in Algorithms" (Roughgarden) — [Notes + YouTube-Videos frei] (https://timroughgarden.org/notes.html). Exakt die zweite Algorithmik-Vorlesung nach dem Bachelor: LP-Dualität, Approximation, Online-Algorithmen — Roughgardens Note…
    m-algo:14:u1 [url] https://timroughgarden.org/notes.html  «Notes + YouTube-Videos frei»
L15: 🎓 MIT 6.854 „Advanced Algorithms" (Karger) — Notes/Videos öffentlich auffindbar (OCW + YouTube). Graduate-Breite als Ergänzung, v. a. für randomisierte Techniken. Einsatz: punktuell pro Thema, nicht linear.
    m-algo:15:e1 [entry] MIT 6.854 „Advanced Algorithms" (Karger)
L17: 📚 de Berg/Cheong/van Kreveld/Overmars, „Computational Geometry: Algorithms and Applications" — das Standardwerk für den Geometrie-Block (Sweep, Voronoi, Triangulierung). Einsatz: nur die in der Vorlesung behandelten Kapitel.
    m-algo:17:e1 [entry] de Berg/Cheong/van Kreveld/Overmars, „Computational Geometry: Algorithms and Applications"
L18: 📚 Brandt et al. (Hrsg.), „Handbook of Computational Social Choice" — [frei als PDF (Cambridge-Open)] (https://www.cambridge.org/core/books/handbook-of-computational-social-choice/35B58B6F0A11B0E7DC724BA4E5B33D6D). COMSOC ist eine Spezialität der Berliner AKT-S…
    m-algo:18:u1 [url] https://www.cambridge.org/core/books/handbook-of-computational-social-choice/35B58B6F0A11B0E7DC724BA4E5B33D6D  «frei als PDF (Cambridge-Open)»
L25: 📚 Arora/Barak, „Computational Complexity: A Modern Approach" — [Entwurfs-PDF frei (Princeton)] (https://theory.cs.princeton.edu/complexity/book.pdf). Deckt das Modulprofil vollständig: Hierarchiesätze (Kap. 3), PH (Kap. 5), IP (Kap. 8). Einsatz: Hauptbuch; für…
    m-algo:25:u1 [url] https://theory.cs.princeton.edu/complexity/book.pdf  «Entwurfs-PDF frei (Princeton)»
L26: 🎓 Ryan O'Donnell, CMU 15-855 „Graduate Computational Complexity" — [komplette Vorlesung auf YouTube] (https://www.youtube.com/playlist?list=PLm3J0oaFux3b8Gg1DdaJOzYNsaXYLAOKH). Die beste freie Video-Vorlesung zur strukturellen Komplexität — O'Donnell ist ein h…
    m-algo:26:u1 [url] https://www.youtube.com/playlist?list=PLm3J0oaFux3b8Gg1DdaJOzYNsaXYLAOKH  «komplette Vorlesung auf YouTube»
L27: 📚 Sipser, „Introduction to the Theory of Computation" — Teil 3 (Zeit-/Platzkomplexität) als sanfter Einstieg, falls die HU-ToC-Grundlage Lücken hat. Brücken-Ressource — auch relevant für den R2-Zugangscheck (12 LP TheoInf!). Einsatz: Auffrischung vor Semester…
    m-algo:27:e1 [entry] Sipser, „Introduction to the Theory of Computation"
L28: 📚 Papadimitriou, „Computational Complexity" — der elegante Klassiker; manche Themen (Orakel, PH) sind hier am schönsten erzählt. Einsatz: Zweitdarstellung nach Geschmack.
    m-algo:28:e1 [entry] Papadimitriou, „Computational Complexity"  -> title ~ source-arora-barak (0.67)
L29: 📄 Originale für die Prüfungskür: Cook (1971), Karp „Reducibility Among Combinatorial Problems" (1972), Shamir „IP = PSPACE" (1992). Einsatz: mindestens Karps 21 Probleme einmal gesehen haben — Reduktionsketten sind mündlicher Prüfungsstandard.
    m-algo:29:e1 [entry] Originale für die Prüfungskür
L35: 📚 Mitzenmacher/Upfal, „Probability and Computing" (2. Aufl.) — das moderne Standardwerk: Chernoff, Balls-into-Bins, Markov-Ketten, probabilistische Methode — didaktisch zugänglicher als Motwani/Raghavan. Einsatz: Hauptbuch; Kapitel 1–6 + 13 decken den Vorlesu…
    m-algo:35:e1 [entry] Mitzenmacher/Upfal, „Probability and Computing" (2. Aufl.)  -> title ~ source-mitzenmacher-upfal (0.80)
L36: 📚 Motwani/Raghavan, „Randomized Algorithms" — der Klassiker, stärker bei randomisierten Algorithmen (Min-Cut/Karger, geometrische Algorithmen, RP/BPP-Theorie). Einsatz: für die Graph-/Geometrie-Beispiele, die Mitzenmacher/Upfal knapper hält.
    m-algo:36:e1 [entry] Motwani/Raghavan, „Randomized Algorithms"
L37: 📚 Alon/Spencer, „The Probabilistic Method" — die Referenz zum gleichnamigen Modulblock (Lovász Local Lemma, Alterationen, Second Moment). Einsatz: nur die in der Vorlesung berührten Kapitel — das Buch ist tief; für die mündliche Prüfung reichen die Grundtechn…
    m-algo:37:e1 [entry] Alon/Spencer, „The Probabilistic Method"
L38: 🎓 MIT 6.856 „Randomized Algorithms" (Karger) — [OCW-Notes frei] (https://ocw.mit.edu/courses/6-856j-randomized-algorithms-fall-2002/). Karger lehrt hier u. a. seinen eigenen Min-Cut — Vorlesungsnotizen mit Übungen als US-Spur. Einsatz: Aufgabenquelle.
    m-algo:38:u1 [url] https://ocw.mit.edu/courses/6-856j-randomized-algorithms-fall-2002/  «OCW-Notes frei»
L39: 📄 Karger, „Global Min-Cuts in RNC..." (Min-Cut-Paper) + Aussagen-Set RP/BPP/ZPP aus Arora/Barak Kap. 7 — Einsatz: Min-Cut ist das kanonische Prüfungsbeispiel; die Klassen-Definitionen mit Amplifikations-Argument sicher beherrschen.
    m-algo:39:e1 [entry] Karger, „Global Min-Cuts in RNC..." (Min-Cut-Paper)
L46: 📚 Niedermeier, „Invitation to Fixed-Parameter Algorithms" — vom Begründer der Berliner FPT-Schule (Nichterleins Doktorvater). Sanfter und beispielgetriebener als Cygan et al.; die Denkweise dieser Gruppe. Einsatz: als Einstieg vor dem großen Buch — wer die „I…
    m-algo:46:e1 [entry] Niedermeier, „Invitation to Fixed-Parameter Algorithms"
L47: 📚 Downey/Fellows, „Fundamentals of Parameterized Complexity" — die Härte-Seite (W-Hierarchie) in voller Tiefe. Einsatz: Nachschlagewerk für parametrisierte Reduktionen; nicht linear lesen.
    m-algo:47:e1 [entry] Downey/Fellows, „Fundamentals of Parameterized Complexity"
L48: 🛠 PACE Challenge — [pacechallenge.org] (https://pacechallenge.org/). Jährlicher Implementierungswettbewerb für FPT-Probleme (Treewidth, Vertex Cover, …), an dem TU-Berlin-Gruppen traditionell teilnehmen. Einsatz: eine alte PACE-Instanz + Solver anschauen verbi…
    m-algo:48:u1 [url] https://pacechallenge.org/  «pacechallenge.org»
L49: 📄 Alon/Yuster/Zwick, „Color-Coding" (JACM 1995) — das Originalpaper zur elegantesten Technik des Felds. Einsatz: einmal im Original lesen; Standard-Prüfungsfrage („erklären Sie Color Coding für k-Path").
    m-algo:49:e1 [entry] Alon/Yuster/Zwick, „Color-Coding" (JACM 1995)
L55: 🎓 Stanford CS168 „The Modern Algorithmic Toolbox" (Roughgarden/Valiant) — [alle Notes frei] (https://web.stanford.edu/class/cs168/index.html). Sketching/Streaming, Hashing, Dimensionsreduktion, Matrix-Methoden (SVD/PCA-Sicht), Graph-Spektralmethoden — kein off…
    m-algo:55:u1 [url] https://web.stanford.edu/class/cs168/index.html  «alle Notes frei»
L57: 📄 Muthukrishnan, „Data Streams: Algorithms and Applications" — [frei (Foundations & Trends)] (https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/Muthu-Survey.pdf)-artig verfügbar über Autorenseite. Die kompakte Theorie-Referenz zu Streaming-Algorit…
    m-algo:57:u1 [url] https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/Muthu-Survey.pdf  «frei (Foundations & Trends)»
L58: 📄 Demaine, „Cache-Oblivious Algorithms and Data Structures" (Survey) — [frei (MIT)] (https://erikdemaine.org/papers/BRICS2002/paper.pdf). Die Memory-Hierarchy-Hälfte: I/O-Modell, cache-oblivious B-Trees/Sorting. Einsatz: für den Memory-Hierarchy-Block — und ko…
    m-algo:58:u1 [url] https://erikdemaine.org/papers/BRICS2002/paper.pdf  «frei (MIT)»
L59: 📚 Gusfield, „Algorithms on Strings, Trees, and Sequences" — das Referenzwerk für den Sequence-Analysis-Teil (Suffix-Strukturen, Alignment). Einsatz: nur die vorlesungsrelevanten Kapitel.
    m-algo:59:e1 [entry] Gusfield, „Algorithms on Strings, Trees, and Sequences"
L60: 📚 Easley/Kleinberg, „Networks, Crowds, and Markets" — [frei als PDF (Cornell)] (https://www.cs.cornell.edu/home/kleinber/networks-book/). Für den Network-Analysis-Teil (Zentralität, Communities, Kaskaden) die lesbarste Quelle. Einsatz: Auswahl-Kapitel.
    m-algo:60:u1 [url] https://www.cs.cornell.edu/home/kleinber/networks-book/  «frei als PDF (Cornell)»
L66: 📚 Sanders/Mehlhorn/Dietzfelbinger/Dementiev, „Sequential and Parallel Algorithms and Data Structures: The Basic Toolbox" — [frei als PDF (KIT/Autoren-Seite)] (https://people.mpi-inf.mpg.de/~mehlhorn/Toolbox.html). Die Karlsruher AE-Schule in Buchform: Algorith…
    m-algo:66:u1 [url] https://people.mpi-inf.mpg.de/~mehlhorn/Toolbox.html  «frei als PDF (KIT/Autoren-Seite)»
L67: 📚 McGeoch, „A Guide to Experimental Algorithmics" — die Methodik-Referenz für saubere Algorithmen-Experimente: Instanzwahl, Messung, Varianzkontrolle, Reporting. Einsatz: vor dem Portfolio lesen — und wörtlich wiederverwendbar für CSB, ROC und deine Thesis-Ev…
    m-algo:67:e1 [entry] McGeoch, „A Guide to Experimental Algorithmics"  -> title ~ source-mcgeoch-experimental-algorithmics (1.00)
L68: 🛠 PACE Challenge (s. §4) + DIMACS Implementation Challenges — reale Benchmark-Instanzen + Vergleichs-Solver. Einsatz: Portfolio-Material; eine PACE-Aufgabe ist praktisch ein vorgefertigtes AE-II-Projekt.
    m-algo:68:e1 [entry] PACE Challenge
L69: 🛠 LP/ILP-Solver-Praxis: Gurobi (akademische Gratis-Lizenz) oder HiGHS (Open Source) + die Modellierungs-Tutorials von Gurobi. Das Modulprofil nennt „etablierte Solver" explizit. Einsatz: ein NP-schweres Problem einmal als ILP modellieren und gegen eigene Heur…
    m-algo:69:e1 [entry] LP/ILP-Solver-Praxis
L70: 📚 Bentley, „Programming Pearls" — kurz, alt, unsterblich: die Engineering-Haltung (Messen! Back-of-envelope!) auf 200 Seiten. Einsatz: Wochenendlektüre vor Projektstart.
    m-algo:70:e1 [entry] Bentley, „Programming Pearls"
L71: ⚠ Planungshinweis: Turnus „unregelmäßig" — vor Einplanung per Moses-Link prüfen, ob das Modul im Zielsemester überhaupt läuft (Regel §4.6 im MODULE-MENU).
    m-algo:71:e1 [entry] Planungshinweis
L77: 📚 Grädel/Thomas/Wilke (Hrsg.), „Automata, Logics, and Infinite Games" (LNCS 2500) — der kanonische Text, dessen Titel das Modul fast wörtlich trägt: Büchi-/Parity-Automaten, S1S, Spiele, Determinisierung (Safra). Einsatz: Hauptreferenz; Kreutzer kommt aus gen…
    m-algo:77:e1 [entry] Grädel/Thomas/Wilke (Hrsg.), „Automata, Logics, and Infinite Games" (LNCS 2500)
L78: 📄 Erich Grädel, Vorlesungsskripte „Automata, Games and Logic" / „Algorithmic Model Theory" — [frei auf der RWTH-Logik-Seite] (https://logic.rwth-aachen.de/Teaching/index.html.en). Druckreife deutsche/englische Skripte exakt zu diesem Vorlesungstyp. Einsatz: di…
    m-algo:78:u1 [url] https://logic.rwth-aachen.de/Teaching/index.html.en  «frei auf der RWTH-Logik-Seite»
L79: 📚 Baier/Katoen, „Principles of Model Checking" — die Anwendungsseite (LTL/CTL, Model Checking reaktiver Systeme), auf die das Modulprofil zielt. Einsatz: für den Verifikations-Block; Kapitel zu LTL→Büchi ist der Scharnier-Stoff.
    m-algo:79:e1 [entry] Baier/Katoen, „Principles of Model Checking"
L80: 📄 Thomas, „Languages, Automata, and Logic" (Handbook-Kapitel) — das klassische 60-Seiten-Survey über die Logik↔Automaten-Korrespondenzen. Einsatz: Vorab-Landkarte; danach hat jeder Vorlesungsteil seinen Platz.
    m-algo:80:e1 [entry] Thomas, „Languages, Automata, and Logic" (Handbook-Kapitel)
L81: 🛠 Spot / owl (Automaten-Bibliotheken) + Parity-Game-Solver (z. B. Oink) — Einsatz: optional; ein LTL→Büchi-Übersetzer einmal laufen lassen macht Safra & Co. greifbar.
    m-algo:81:e1 [entry] Spot / owl (Automaten-Bibliotheken)
L87: 📚 Lynch, „Distributed Algorithms" — das „bekannte Lehrbuch" des Felds (synchron/asynchron, Fehlermodelle, Leader Election, Consensus — die Modulliste ist ihre Kapitelfolge). Einsatz: Hauptbuch; die zu formalisierenden Kapitel kommen mit hoher Wahrscheinlichke…
    m-algo:87:e1 [entry] Lynch, „Distributed Algorithms"
L88: 📚 Fokkink, „Distributed Algorithms: An Intuitive Approach" (MIT Press) — kompakte, beweisfreundliche Zweitdarstellung derselben Algorithmen. Einsatz: wenn Lynch zu enzyklopädisch wird.
    m-algo:88:e1 [entry] Fokkink, „Distributed Algorithms: An Intuitive Approach" (MIT Press)
L89: 📄 FLP: Fischer/Lynch/Paterson, „Impossibility of Distributed Consensus with One Faulty Process" (JACM 1985) + Lamport, „Time, Clocks, and the Ordering of Events" (CACM 1978) + Lamport, „Paxos Made Simple" — die drei Texte, um die jedes Consensus-Kapitel kreis…
    m-algo:89:e1 [entry] FLP: Fischer/Lynch/Paterson, „Impossibility of Distributed Consensus with One Faulty Process" (JACM 1985)
L90: 🛠🎓 TLA+ (Lamport) — [Video-Kurs + Hyperbook frei] (https://lamport.azurewebsites.net/video/videos.html). Spezifikation und maschinengeprüfte Argumente für verteilte Algorithmen — exakt die im Modulprofil angedeutete Theorembeweiser-Perspektive, vom Turing-Prei…
    m-algo:90:u1 [url] https://lamport.azurewebsites.net/video/videos.html  «Video-Kurs + Hyperbook frei»
L97: 📚 Lynch / Fokkink / Attiya-Welch (s. §8) — die Grundlagenbücher tragen auch diese Module; der §8-Kanon (FLP, Lamport) deckt den Distributed-Systems-Teil von #41127. Einsatz: gemeinsame Basis.
    m-algo:97:e1 [entry] Lynch / Fokkink / Attiya-Welch
L98: 📚 Cachin/Guerraoui/Rodrigues, „Introduction to Reliable and Secure Distributed Programming" — Broadcast/Consensus/Replication abstraktionsorientiert; die moderne Brücke Theorie ↔ System. Einsatz: für die Datacenter-/Internet-scale-Modelle von #41127.
    m-algo:98:e1 [entry] Cachin/Guerraoui/Rodrigues, „Introduction to Reliable and Secure Distributed Programming"
L99: 📄 Self-Stabilization: Dijkstra, „Self-stabilizing Systems in Spite of Distributed Control" (CACM 1974) + Dolev, „Self-Stabilization" (MIT Press) — exakt der „self-stabilizing/self-optimizing networks"-Block von #41126. Einsatz: Pflicht für #41126.
    m-algo:99:e1 [entry] Self-Stabilization
L100: 📄 Schmids Forschung (self-adjusting/demand-aware networks) — seine SIGCOMM/INFOCOM-Arbeiten zu selbstoptimierenden Netzen. Einsatz: die Forschungsfront, aus der die #41126-Inhalte stammen — vom Dozenten.
    m-algo:100:e1 [entry] Schmids Forschung (self-adjusting/demand-aware networks)
L101: 📚 Suomela, „Survey of Local Algorithms" (ACM CSUR 2013) — der LOCAL/CONGEST-Einstieg (verteilte Graph-Algorithmen). Einsatz: für den Local-Algorithms-Teil.
    m-algo:101:e1 [entry] Suomela, „Survey of Local Algorithms" (ACM CSUR 2013)  -> title ~ source-pouyanfar-dl-survey (0.57)
L102: 🛠 TLA+ / MIT 6.824 (s. §8) — Spezifikation bzw. Praxis (Raft), doppelt nutzbar.
    m-algo:102:e1 [entry] TLA+ / MIT 6.824
L103: Cross: ergänzt MTDA #41225 (§8); die Datacenter-Modelle berühren Cloud Computing / Datacenter Networking (DSN-Annex) und die 📊-Mess-Methodik (Schmids Internet-Measurement-Modul).
    m-algo:103:e1 [entry] Cross
L109: 📄 Venues: ESA, SODA, ICALP, STACS, IPEC (Parameterized) — die AKT-Publikationsorte; daraus Exposé/Vortragsthema wählen. Einsatz: ein aktuelles Paper der Nichterlein-Gruppe als Aufhänger.
    m-algo:109:e1 [entry] Venues
L111: Cross: inhaltliche Fortsetzung von HA/ParamAlgo/AE II — gleiche Schule (Nichterlein prüft alle).
    m-algo:111:e1 [entry] Cross
L117: 1. AKT-Kanon zuerst: Cygan et al. (frei) + Niedermeiers „Invitation" tragen ParamAlgo komplett, den FPT-Block von HA und die Datenreduktions-Denkweise von AE II — drei Module, zwei Bücher, eine Schule (Nichterlein prüft alle drei).
    m-algo:117:e1 [entry] AKT-Kanon zuerst
L118: 2. ADS ist das Scharnier: Streaming (→ MDS/MMDS, 🔧), Memory Hierarchy (→ DMH, 🚀), Matrix-Methoden (→ ML-Block) — als DSE+FC-doppelgelistetes Modul auch bucket-taktisch das flexibelste Stück der Achse.
    m-algo:118:e1 [entry] ADS ist das Scharnier
L119: 3. AE II + McGeoch = 📊-Vorschule: experimentelle Algorithmik ist methodisch identisch mit CSB/ROC/Thesis-Evaluation. Einmal Messmethodik lernen, vierfach ernten.
    m-algo:119:e1 [entry] AE II + McGeoch = 📊-Vorschule
L120: 4. Theorie-Paar mit Nestmann/Kreutzer: LSA (Spiele/Automaten) und MTDA (Formalisierung) sind die FC-lastigsten Wahlmöglichkeiten — beide belohnen Beweis-Sorgfalt, beide harmonieren mit TPS/Lambda-Kalkül (🚀-PL-Schiene) zur „formalen Säule" deines Profils.
    m-algo:120:e1 [entry] Theorie-Paar mit Nestmann/Kreutzer
L121: 5. Mündlich-Cluster: CC, RandAlgo, ParamAlgo (+ TPS, Lambda, MathML, FoSP, ADM) sind mündlich — gut stapelbar neben einer Klausur, aber nicht drei mündliche Theorie-Prüfungen in dieselbe Prüfungswoche legen.
    m-algo:121:e1 [entry] Mündlich-Cluster
L122: 6. Kostenlos-Quote: Cygan, Erickson, Roughgarden (Notes+AGT), Arora/Barak, O'Donnell-Videos, CS168, MMDS, Muthukrishnan, Demaine, Easley/Kleinberg, Sanders-Toolbox, Grädel-Skripte, TLA+-Kurs — der Block ist fast vollständig frei studierbar.
    m-algo:122:e1 [entry] Kostenlos-Quote
L133: 📝 O'Donnell 15-855: Homeworks — auf der CMU-Kursseite zu den YouTube-Lectures liegen Problem Sets — Komplexitäts-Übungen auf genau dem CC-Prüfungsniveau.
    m-algo:133:e1 [entry] O'Donnell 15-855: Homeworks
L134: 📝 Cygan et al.: Buchübungen + Hints — das freie FPT-Buch enthält pro Kapitel Übungen mit Schwierigkeitsgraden und Hinweisen — die ParamAlgo-Übungsblätter sind faktisch mitgeliefert.
    m-algo:134:e1 [entry] Cygan et al.: Buchübungen + Hints
L135: 📝 Kleinberg/Tardos „Solved Exercises" — jedes Kapitel beginnt mit vollständig vorgerechneten Aufgaben — als Muster für die HA-Klausur-Argumentationsform („beschreibe Algorithmus, beweise Korrektheit, analysiere Laufzeit").
    m-algo:135:e1 [entry] Kleinberg/Tardos „Solved Exercises"  -> title ~ source-kleinberg-tardos (0.50), source-wayne-kt-slides (0.50)
L136: 📝 Stanford CS161/CS261-Psets (Roughgarden-Ökosystem) — öffentlich auf [timroughgarden.org] (https://timroughgarden.org/) verlinkt; CS261-Aufgaben decken Approximation/Online ab.
    m-algo:136:u1 [url] https://timroughgarden.org/  «timroughgarden.org»
L140: 🛠 CP-Algorithms — [cp-algorithms.com] (https://cp-algorithms.com/): Implementierungs-Referenz für praktisch jeden HA-Algorithmus (Flows, Matching, Segment-Strukturen) mit Codebeispielen — die Brücke von Beweis zu Code.
    m-algo:140:u1 [url] https://cp-algorithms.com/  «cp-algorithms.com»
L142: 🛠 Exercism + Project Euler — Dauer-Fingerübungen; für ⚙️ besonders die Euler-Graphenprobleme.
    m-algo:142:e1 [entry] Exercism + Project Euler
L143: 🛠 Codeforces/AtCoder (Ergänzung) — wenn Wettkampf-Training motiviert: Div-2-Probleme sind HA-Klausuraufgaben unter Zeitdruck.
    m-algo:143:e1 [entry] Codeforces/AtCoder (Ergänzung)
L147: 🛠 PACE-Challenge-Siegersolver — über [pacechallenge.org] (https://pacechallenge.org/) je Jahr verlinkt (z. B. Treewidth-/Vertex-Cover-Solver): lesbarer FPT-Code im Wettbewerbszustand — verbindet ParamAlgo mit AE II.
    m-algo:147:u1 [url] https://pacechallenge.org/  «pacechallenge.org»
L148: 🛠 KaHIP / KaMIS (Karlsruhe) — [github.com/KaHIP] (https://github.com/KaHIP): Graphpartitionierung/Independent Sets in Algorithm-Engineering-Qualität — Vorzeige-Repos dafür, wie man Algorithmik-Code strukturiert, testet und benchmarkt (AE-II-Vorbild).
    m-algo:148:u1 [url] https://github.com/KaHIP  «github.com/KaHIP»
L149: 🛠 NetworKit — [github.com/networkit/networkit] (https://github.com/networkit/networkit): skalierbare Netzwerkanalyse (ADS-Domäne „Network Analysis") — Algorithmen aus der Vorlesung im Produktionszustand.
    m-algo:149:u1 [url] https://github.com/networkit/networkit  «github.com/networkit/networkit»
L150: 🛠 TLA+ Examples — [github.com/tlaplus/Examples] (https://github.com/tlaplus/Examples): spezifizierte verteilte Algorithmen (inkl. Paxos) als MTDA-Portfolio-Vorlagen.
    m-algo:150:u1 [url] https://github.com/tlaplus/Examples  «github.com/tlaplus/Examples»

## m-bench — repository/curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning/inputs/MASTERS-BENCHMARKING-RESOURCES.md

L11: Modulprofil (lt. Katalog): Grundlagen + gesamter Benchmarking-Lifecycle, als Flipped Classroom über ein Buch + individuelles Benchmarking-Projekt. Der Modultext verlinkt die Buch-Website selbst: [cloudservicebenchmarking.github.io] (https://cloudservicebenchma…
    m-bench:11:u1 [url] https://cloudservicebenchmarking.github.io/  «cloudservicebenchmarking.github.io»
L13: 📚 Bermbach/Wittern/Tai, „Cloud Service Benchmarking: Measuring Quality of Cloud Services from a Client Perspective" (Springer) — das Kursbuch, vom Dozenten, explizit im Modultext genannt ([Begleit-Website] (https://cloudservicebenchmarking.github.io/)). Benchm…
    m-bench:13:u1 [url] https://cloudservicebenchmarking.github.io/  «Begleit-Website»
L14: 📚 Raj Jain, „The Art of Computer Systems Performance Analysis" — die zeitlose Methodik-Bibel: Metrikwahl, Workload-Charakterisierung, experimentelles Design (Faktorenanalyse), häufige Benchmarking-Fehler („common mistakes" — als Checkliste Gold wert). Einsatz…
    m-bench:14:e1 [entry] Raj Jain, „The Art of Computer Systems Performance Analysis"  -> title ~ source-jain-performance-analysis (1.00)
L15: 📄 Methodik-Papers mit Biss: Georges et al., „Statistically Rigorous Java Performance Evaluation" (OOPSLA 2007) · Kalibera/Jones, „Rigorous Benchmarking in Reasonable Time" · Huppler, „The Art of Building a Good Benchmark" (TPCTC 2009) · Hoefler/Belli, „Scient…
    m-bench:15:e1 [entry] Methodik-Papers mit Biss
L16: 🛠 YCSB ([github.com/brianfrankcooper/YCSB] (https://github.com/brianfrankcooper/YCSB)) + TPC-Benchmarks ([tpc.org] (https://www.tpc.org/)) — der Standard-Workload-Generator für Cloud-/Storage-Dienste (Original-Paper: Cooper et al., SoCC 2010) und die DB-Industr…
    m-bench:16:u1 [url] https://github.com/brianfrankcooper/YCSB  «github.com/brianfrankcooper/YCSB»
    m-bench:16:u2 [url] https://www.tpc.org/  «tpc.org»
L23: 📄 AWS Builders' Library — [aws.amazon.com/builders-library] (https://aws.amazon.com/builders-library/) (frei). Essays von Amazon-Principal-Engineers zu exakt den Modul-Patterns: „Timeouts, Retries, and Backoff with Jitter", „Reliability, Constant Work, and a G…
    m-bench:23:u1 [url] https://aws.amazon.com/builders-library/  «aws.amazon.com/builders-library»
L24: 📚 Nygard, „Release It! (2. Aufl.)" — der Patterns-Katalog für Stabilität unter Last: Circuit Breaker, Bulkheads, Backpressure, Retry-Strategien. Einsatz: die Stability-Patterns-Kapitel; Portfolio-Diskussionen („warum kippt System X?") argumentieren in genau d…
    m-bench:24:e1 [entry] Nygard, „Release It! (2. Aufl.)"
L27: 📄 Zwei Denk-Papers: Fox/Brewer, „Harvest, Yield, and Scalable Tolerant Systems" (1999) und McSherry/Isard/Murray, „Scalability! But at what COST?" (HotOS 2015) — Letzteres misst, wann „skalierbare" Systeme langsamer sind als ein Laptop-Thread: die perfekte Br…
    m-bench:27:e1 [entry] Zwei Denk-Papers
L28: 🛠 Case-Study-Fundus: Architektur-Postmortems und „How X scales"-Artikel ([highscalability.com] (http://highscalability.com/)-Archiv, Engineering-Blogs von Netflix/Cloudflare/Discord). Einsatz: Material für den Case-Study-Teil des Moduls — eine fremde Architekt…
    m-bench:28:u1 [url] http://highscalability.com/  «highscalability.com»
L34: 🎓 Green Software Foundation, „Green Software Practitioner" — [learn.greensoftware.foundation] (https://learn.greensoftware.foundation/) (frei, ~6h) + die SCI-Spezifikation (Software Carbon Intensity). Die Industrie-Begriffsbasis für Carbon Accounting von Softw…
    m-bench:34:u1 [url] https://learn.greensoftware.foundation/  «learn.greensoftware.foundation»
L35: 📚 Currie/Hsu/Bergman, „Building Green Software" (O'Reilly 2024) — das praxisnahe Buch zu energiebewusster Architektur, Carbon-Aware-Scheduling, Messung — deckt die Architektur-/Redesign-Hälfte des Moduls. Einsatz: Hauptbegleitbuch.
    m-bench:35:e1 [entry] Currie/Hsu/Bergman, „Building Green Software" (O'Reilly 2024)
L36: 📄 Forschungskanon fürs Seminar: Gupta et al., „Chasing Carbon: The Elusive Environmental Footprint of Computing" (HPCA 2021) — das Paper, das embodied vs. operational Carbon etabliert hat · Patterson et al., „Carbon Emissions and Large Neural Network Training…
    m-bench:36:e1 [entry] Forschungskanon fürs Seminar
L37: 📄 HotCarbon Workshop — [hotcarbon.org] (https://hotcarbon.org/) (Proceedings frei). Die aktuelle Forschungsfront kompakt (Carbon-Aware-Scheduling, Energie-Messung, Wasserverbrauch). Einsatz: Themenquelle für den Seminarteil — ein frisches HotCarbon-Paper refer…
    m-bench:37:u1 [url] https://hotcarbon.org/  «hotcarbon.org»
L38: 🛠 Messwerkzeuge: Intel RAPL (via perf/powercap) für systemnahe Energiemessung · CodeCarbon ([codecarbon.io] (https://codecarbon.io/)) für ML-Workload-Tracking · Cloud-Carbon-Footprint-Tools (cloudcarbonfootprint.org). Einsatz: fürs Portfolio einmal real messen…
    m-bench:38:u1 [url] https://codecarbon.io/  «codecarbon.io»
L39: ⚠ Einordnung: Tai (ISE-Lehrstuhl, Bermbach-Orbit) — methodisch dieselbe Mess-Schule wie CSB; wer beide nimmt, recycelt das halbe Methodik-Toolkit.
    m-bench:39:e1 [entry] Einordnung
L45: 📄 Handwerks-Trio fürs CRM-Modul: Keshav, „How to Read a Paper" (s. MASTERS-DATAENG-RESOURCES.md §10) · Simon Peyton Jones, „How to Write a Great Research Paper" ([Talk + Folien frei, Microsoft-Research-Seite] (https://simon.peytonjones.org/great-research-paper…
    m-bench:45:u1 [url] https://simon.peytonjones.org/great-research-paper/  «Talk + Folien frei, Microsoft-Research-Seite»
L47: 📄 Themen-Anker für die Lesezyklen: Hellerstein et al., „Architecture of a Database System" (s. DBT) · Pavlo et al., „Self-Driving Database Management Systems" (CIDR 2017) — Self-Tuning/adaptive Methoden · Chaudhuri/Narasayya, „Self-Tuning Database Systems: A…
    m-bench:47:e1 [entry] Themen-Anker für die Lesezyklen
L48: 📄 Experimentelles Design & Reproduzierbarkeit: McGeoch, „A Guide to Experimental Algorithmics" (s. MASTERS-ALGO-RESOURCES.md §6) · ACM-Artifact-Badging / SIGMOD Availability & Reproducibility Initiative ([sigmod.org/sigmod-reproducibility] (https://reproducibi…
    m-bench:48:u1 [url] https://reproducibility.sigmod.org/  «sigmod.org/sigmod-reproducibility»
L49: ⚠ Kapazität max 8 + WiSe + 9 LP: ROC konkurriert im Plan mit DBTLAB um den M3-Brocken-Slot (Regel: nie zwei Implementierungs-Brocken). Es ist der DIMA-Weg zur Thesis — dein Default bleibt der DEEM-Weg (EDML → RDE-Projekt); ROC ist die Markl-Alternative, falls…
    m-bench:49:e1 [entry] Kapazität max 8 + WiSe + 9 LP
L55: 📚 Crovella/Krishnamurthy, „Internet Measurement: Infrastructure, Traffic and Applications" (Wiley) — das Standardlehrbuch zur Internet-Messung. Einsatz: Hauptbuch.
    m-bench:55:e1 [entry] Crovella/Krishnamurthy, „Internet Measurement: Infrastructure, Traffic and Applications" (Wiley)
L56: 📄 Paxson, „Strategies for Sound Internet Measurement" (IMC 2004) — wie man messmethodisch sauber arbeitet (Kalibrierung, systematische Fehler, Fallstricke). Einsatz: Pflicht — das methodische Rückgrat, exakt dein 📊-Profilziel.
    m-bench:56:e1 [entry] Paxson, „Strategies for Sound Internet Measurement" (IMC 2004)
L57: 🛠 Mess-Infrastruktur: RIPE Atlas + CAIDA-Datensätze/Tools — reale Messung statt Theorie. Einsatz: für den praktischen Teil/das Portfolio.
    m-bench:57:e1 [entry] Mess-Infrastruktur
L58: 📄 Coordinated Omission (Gil Tene) (s. Mega-Sweep unten) — Latenz-Messfehler, der auch Netzwerk-Benchmarks betrifft. Einsatz: Querbezug zur restlichen 📊-Methodik.
    m-bench:58:e1 [entry] Coordinated Omission (Gil Tene)
L65: 📚 Basis = ScalEng/CSB-Ressourcen (§1–§2) — selbes Lehrstuhl-Orbit; AWS Builders' Library, Nygard „Release It!". Einsatz: Hintergrund für die Themenwahl.
    m-bench:65:e1 [entry] Basis = ScalEng/CSB-Ressourcen (§1–§2)
L66: 📄 Venues: SoCC, Middleware, ICDCS — daraus zieht das Seminar; pro Thema das Quellpaper. Einsatz: Vortragsvorbereitung.
    m-bench:66:e1 [entry] Venues
L67: Cross: Mini-Vertiefung neben CSB/ScalEng; Gegenstück zu „Hot Topics in Scalable Software Systems" (§1b).
    m-bench:67:e1 [entry] Cross
L73: 1. Die Bermbach-Schiene: CSB (WiSe/SoSe) → Scalability Engineering (SoSe) → Sustainable Computing (Tai, WiSe) teilen Mess-Methodik, Cloud-Kontext und Lehrstuhl-Orbit — Methodik-Toolkit einmal aufbauen, dreimal ernten.
    m-bench:73:e1 [entry] Die Bermbach-Schiene
L74: 2. Der Methodik-Kanon der gesamten Achse (Jain · McGeoch · Hoefler/Belli · Georges · COST) ist identisch mit dem Handwerk deines Thesis-Evaluationskapitels: Benchmark-Suite, Baselines, Varianzkontrolle, ehrliche Limitierungen. Diese Achse ist die Thesis-Vorsc…
    m-bench:74:e1 [entry] Der Methodik-Kanon der gesamten Achse
L75: 3. Cross-Tag-Einlösung: AE II (⚙️, McGeoch) = experimentelle Algorithmik · DMH (🔧, Gregg/perf) = Mikro-Messung · Adversarial ML (🤖, Carlini/Rieck) = Evaluations-Ehrlichkeit · ROC = wissenschaftliche Verpackung. Vier Achsen, ein Skill.
    m-bench:75:e1 [entry] Cross-Tag-Einlösung
L76: 4. ROC vs. DEEM-Pipeline: beide führen zur Thesis — ROC über Markl/DIMA (max 8!), EDML+RDE-Projekt über Schelter/DEEM (Default). Nicht beide einplanen; ROC als dokumentierter Fallback.
    m-bench:76:e1 [entry] ROC vs. DEEM-Pipeline
L77: 5. Serie komplett: 🔧 🤖 🧮 ⚙️ 🚀 📊 — alle sechs Achsen-Bibliotheken liegen in Masters-Planning/. Einstieg immer über MASTERS-MODULE-MENU.md → Achsen-Datei → Modul.
    m-bench:77:p1 [path] Masters-Planning/  -> no material match
L89: 🛠 cmu-db/benchbase — [github.com/cmu-db/benchbase] (https://github.com/cmu-db/benchbase): das CMU-Multi-DBMS-Benchmark-Framework (TPC-C, YCSB, 20+ Workloads gegen beliebige JDBC-DBs). Das beste Lese-Repo dafür, wie man ein Benchmark-Harness architektonisch bau…
    m-bench:89:u1 [url] https://github.com/cmu-db/benchbase  «github.com/cmu-db/benchbase»
L90: 🛠 giltene/wrk2 — [github.com/giltene/wrk2] (https://github.com/giltene/wrk2): Lastgenerator mit korrekter Latenz-Messung; dazu Gil Tenes Vortrag „How NOT to Measure Latency" (YouTube) — Coordinated Omission ist der häufigste Benchmarking-Fehler überhaupt und g…
    m-bench:90:u1 [url] https://github.com/giltene/wrk2  «github.com/giltene/wrk2»
L91: 🛠 Microbenchmark-Harnesses: JMH (Java — Pflicht, wenn du DBTLAB-Komponenten misst) · google/benchmark (C++) · criterion.rs (Rust) · hyperfine (CLI). Einsatz: je Sprache das Harness einmal beherrschen; sie kodifizieren Warmup/Statistik aus Georges et al. (s. §…
    m-bench:91:e1 [entry] Microbenchmark-Harnesses
L92: 🛠 brendangregg/FlameGraph + perf-Beispiele — [github.com/brendangregg/FlameGraph] (https://github.com/brendangregg/FlameGraph): Profiling-Visualisierung als Standard-Artefakt für Portfolio-Berichte und Thesis-Plots.
    m-bench:92:u1 [url] https://github.com/brendangregg/FlameGraph  «github.com/brendangregg/FlameGraph»
L93: 🛠 MLPerf (MLCommons) — [mlcommons.org] (https://mlcommons.org/): die Industrie-Benchmarks für Training/Inference inkl. öffentlicher Regeln + Submissions-Repos — die ML-Systems-Seite des Benchmarking (dein Profil-Schnittpunkt 📊×🤖); MLPerf-Methodik (Ergebnis-Nor…
    m-bench:93:u1 [url] https://mlcommons.org/  «mlcommons.org»
L94: 🛠 TPC-Kits + DuckDB-tpch/tpcds-Extensions — TPC-H/DS-Datengeneratoren praktisch nutzen (DuckDB hat beide eingebaut — CALL dbgen(sf=1)): in Minuten reproduzierbare Analytics-Benchmarks für eigene Experimente.
    m-bench:94:e1 [entry] TPC-Kits + DuckDB-tpch/tpcds-Extensions
L98: 🛠 ACM/SIGMOD-Artefakt-Praxis als Übung: ein eigenes Mini-Experiment nach [SIGMOD-Reproducibility-Regeln] (https://reproducibility.sigmod.org/) verpacken (Dockerfile, Seeds, run_all.sh, README mit Hardware-Angabe) — einmal durchgespielt, ist das Thesis-Artefakt…
    m-bench:98:u1 [url] https://reproducibility.sigmod.org/  «SIGMOD-Reproducibility-Regeln»
L99: 🛠 CodeCarbon / Scaphandre / Kepler — Energie-Mess-Stack für SustComp-Portfolios: [codecarbon] (https://github.com/mlco2/codecarbon) (ML-Workloads), [hubblo-org/scaphandre] (https://github.com/hubblo-org/scaphandre) (RAPL-Agent), [sustainable-computing-io/kepler…
    m-bench:99:u1 [url] https://github.com/mlco2/codecarbon  «codecarbon»
    m-bench:99:u2 [url] https://github.com/hubblo-org/scaphandre  «hubblo-org/scaphandre»
    m-bench:99:u3 [url] https://github.com/sustainable-computing-io/kepler  «sustainable-computing-io/kepler»
L100: 📄 SPEC-Methodik-Dokumente ([spec.org] (https://www.spec.org/)) — Run-and-Reporting-Rules der SPEC-Benchmarks als Vorbild dafür, wie man Messregeln spezifiziert — ROC-/Thesis-relevant.
    m-bench:100:u1 [url] https://www.spec.org/  «spec.org»
L104: 🎓 MIT Missing Semester — Shell/Tooling-Übungen: die Voraussetzung, um Messpipelines (tmux, ssh, Skripting) überhaupt sauber zu fahren; bereits in der 🔧-Datei, gilt hier doppelt.
    m-bench:104:e1 [entry] MIT Missing Semester
L105: 📚 OSTEP-Homeworks — die Simulator-Übungen zu Scheduling/Memory erklären, was man bei Systemmessungen eigentlich sieht (Context-Switch-Kosten, Cache-Effekte).
    m-bench:105:e1 [entry] OSTEP-Homeworks

## m-dataeng — repository/curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning/inputs/MASTERS-DATAENG-RESOURCES.md

L13: 🎓 CMU 15-445/645 „Intro to Database Systems" (Andy Pavlo) — [15445.courses.cs.cmu.edu] (https://15445.courses.cs.cmu.edu/) · [Kursübersicht der CMU DB Group] (https://db.cs.cmu.edu/courses/) · alle Vorlesungen auf YouTube. Die Referenzvorlesung für genau den DB…
    m-dataeng:13:u2 [url] https://db.cs.cmu.edu/courses/  «Kursübersicht der CMU DB Group»  -> same line as ['source-cmu-15445']
L14: 🎓 UC Berkeley CS186 „Introduction to Database Systems" — [cs186berkeley.net] (https://cs186berkeley.net/) · [Videos auf YouTube] (https://github.com/PKUFlyingPig/CS186) · [Projekt-Spezifikationen] (https://cs186.gitbook.io/project). Gleicher Stoff, etwas SQL-/an…
    m-dataeng:14:u1 [url] https://cs186berkeley.net/  «cs186berkeley.net»
    m-dataeng:14:u2 [url] https://github.com/PKUFlyingPig/CS186  «Videos auf YouTube»
    m-dataeng:14:u3 [url] https://cs186.gitbook.io/project  «Projekt-Spezifikationen»
L15: 🎓 MIT 6.5830 „Database Systems" — [dsg.csail.mit.edu/6.5830] (https://dsg.csail.mit.edu/6.5830/) · [Notes + Assignments] (https://dsg.csail.mit.edu/6.5830/assign.php). Graduate-Niveau, paperbasierter: liest Originalarbeiten (System R, ARIES) parallel zur Vorles…
    m-dataeng:15:u1 [url] https://dsg.csail.mit.edu/6.5830/  «dsg.csail.mit.edu/6.5830»
    m-dataeng:15:u2 [url] https://dsg.csail.mit.edu/6.5830/assign.php  «Notes + Assignments»
L16: 📚 Silberschatz/Korth/Sudarshan, „Database System Concepts" (7. Aufl.) — [db-book.com] (https://www.db-book.com/) (Slides + Übungen frei). Das Standard-Lehrbuch; Kapitel 12–19 (Storage, Indexing, Query Processing/Optimization, Transactions, Concurrency, Recover…
    m-dataeng:16:u1 [url] https://www.db-book.com/  «db-book.com»
L17: 📚 Garcia-Molina/Ullman/Widom, „Database Systems — The Complete Book" — steht in der offiziellen DBT-Literaturliste (siehe Moses-Link). Stärker formal bei Anfrageverarbeitung/Optimierung (relationale Algebra-Umformungen, Kostenabschätzung). Einsatz: gezielt di…
    m-dataeng:17:e1 [entry] Garcia-Molina/Ullman/Widom, „Database Systems — The Complete Book"
L18: 📄 Hellerstein/Stonebraker/Hamilton, „Architecture of a Database System" — [frei als PDF (Foundations & Trends)] (https://dsf.berkeley.edu/papers/fntdb07-architecture.pdf). ~80 Seiten, die beste Gesamtschau, wie die DBT-Einzelthemen in echten Systemen zusammenh…
    m-dataeng:18:u1 [url] https://dsf.berkeley.edu/papers/fntdb07-architecture.pdf  «frei als PDF (Foundations & Trends)»
L19: 🛠 CMU BusTub — [github.com/cmu-db/bustub] (https://github.com/cmu-db/bustub). Das 15-445-Übungs-DBMS (C++): Buffer Pool, B+Tree, Query Execution selbst bauen. Einsatz: optional vor dem Semester als Warm-up für die DBT-Programmieraufgabe — wer einen Buffer Pool…
    m-dataeng:19:u1 [url] https://github.com/cmu-db/bustub  «github.com/cmu-db/bustub»
L25: 🛠🎓 Berkeley RookieDB (CS186-Projekte) — [github.com/berkeley-cs186] (https://github.com/berkeley-cs186) · [Spezifikationen] (https://cs186.gitbook.io/project). In Java! Du implementierst B+Tree-Indizes, Join-Algorithmen, Query Optimization, Locking und Recovery…
    m-dataeng:25:u1 [url] https://github.com/berkeley-cs186  «github.com/berkeley-cs186»
    m-dataeng:25:u2 [url] https://cs186.gitbook.io/project  «Spezifikationen»
L26: 🛠🎓 MIT SimpleDB / GoDB (6.830/6.5830-Labs) — [historische Java-Labs auf OCW] (https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/pages/assignments/) · [aktuelle Go-Variante] (https://dsg.csail.mit.edu/6.5830/assign.php). SimpleDB (Java) lässt dich meh…
    m-dataeng:26:u1 [url] https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/pages/assignments/  «historische Java-Labs auf OCW»
    m-dataeng:26:u2 [url] https://dsg.csail.mit.edu/6.5830/assign.php  «aktuelle Go-Variante»
L27: 🎓 CMU 15-721 „Advanced Database Systems" — [15721.courses.cs.cmu.edu] (https://15721.courses.cs.cmu.edu/) (Videos + Reading List öffentlich). Wie moderne Engines wirklich gebaut werden: Vectorized Execution, Query Compilation, Parallel Join-Implementierungen,…
    m-dataeng:27:u1 [url] https://15721.courses.cs.cmu.edu/  «15721.courses.cs.cmu.edu»
L28: 📚 Alex Petrov, „Database Internals" (O'Reilly) — Teil 1 (Storage Engines: B-Trees, LSM, File Formats, Buffer Management) ist die lesbarste moderne Darstellung der IO-Schicht. Einsatz: begleitend zum ersten Deliverable (IO Handling).
    m-dataeng:28:e1 [entry] Alex Petrov, „Database Internals" (O'Reilly)
L29: 📚 Andy Grove, „How Query Engines Work" — [howqueryengineswork.com] (https://howqueryengineswork.com/) (frei online). Baut Schritt für Schritt eine Query Engine (logische/physische Pläne, Operatoren, Planner, Optimizer-Rules) — vom DataFusion-Erfinder. Einsatz:…
    m-dataeng:29:u1 [url] https://howqueryengineswork.com/  «howqueryengineswork.com»
L30: 📚 Joshua Bloch, „Effective Java" (3. Aufl.) — DBTLAB verlangt explizit „very good (!!) command of Java". Einsatz: die Items zu Generics, Collections, equals/hashCode und Ressourcen-Management vor Semesterstart auffrischen — die Korrektoren lesen Code-Qualität…
    m-dataeng:30:e1 [entry] Joshua Bloch, „Effective Java" (3. Aufl.)
L31: 📄 Goetz Graefe, „Volcano — An Extensible and Parallel Query Evaluation System" + „The Cascades Framework for Query Optimization" — die zwei Papers, auf denen praktisch jeder Executor (Iterator-Modell) und Optimizer (Cascades) basiert. Einsatz: jeweils vor Del…
    m-dataeng:31:e1 [entry] Goetz Graefe, „Volcano — An Extensible and Parallel Query Evaluation System"
L37: 🎓 TUM „Data Processing on Modern Hardware" (Jana Giceva) — [db.in.tum.de/teaching/ss21/dataprocessingonmodernhardware] (https://db.in.tum.de/teaching/ss21/dataprocessingonmodernhardware/?lang=en) (alle Foliensätze frei: Hardware Trends, Cache Awareness, Execut…
    m-dataeng:37:u1 [url] https://db.in.tum.de/teaching/ss21/dataprocessingonmodernhardware/?lang=en  «db.in.tum.de/teaching/ss21/dataprocessingonmodernhardware»
L38: 🎓 CMU 15-721 (s. o.) — die Lectures zu In-Memory-Architekturen, Vectorization vs. Compilation und Parallel Joins überschneiden sich stark mit DMH. Einsatz: pro DMH-Thema die passende 15-721-Lecture als Video-Ergänzung.
    m-dataeng:38:e1 [entry] CMU 15-721
L39: 📄 Ulrich Drepper, „What Every Programmer Should Know About Memory" — [frei als PDF] (https://people.freebsd.org/~lstewart/articles/cpumemory.pdf). Der Klassiker über Cache-Hierarchien, TLBs, Prefetching, NUMA — ~100 Seiten, davon die ersten 50 Pflicht. Einsatz…
    m-dataeng:39:u1 [url] https://people.freebsd.org/~lstewart/articles/cpumemory.pdf  «frei als PDF»
L40: 📄 Boncz/Zukowski/Nes, „MonetDB/X100: Hyper-Pipelining Query Execution" (CIDR 2005) und Neumann, „Efficiently Compiling Efficient Query Plans for Modern Hardware" (VLDB 2011) — die zwei Papers, die Vectorized Execution bzw. Query Compilation begründet haben; K…
    m-dataeng:40:e1 [entry] Boncz/Zukowski/Nes, „MonetDB/X100: Hyper-Pipelining Query Execution" (CIDR 2005)
L41: 📚 Brendan Gregg, „Systems Performance" (2. Aufl.) — Methodik des Performance-Engineerings (USE-Methode, Profiling, Flame Graphs, perf). Einsatz: fürs Portfolio-Messen — sauberes Benchmarking-Handwerk, das dir auch bei CSB und in der Thesis-Evaluation wieder b…
    m-dataeng:41:e1 [entry] Brendan Gregg, „Systems Performance" (2. Aufl.)
L42: 🛠 Agner Fog, Optimization Manuals ([agner.org/optimize] (https://www.agner.org/optimize/)) + perf/VTune-Tutorials — wenn das Portfolio Mikro-Benchmarks verlangt (Cache-Misses zählen, SIMD-Speedups messen), sind das die Referenzwerkzeuge. Einsatz: punktuell bei…
    m-dataeng:42:u1 [url] https://www.agner.org/optimize/  «agner.org/optimize»
L48: 📚 Akidau/Chernyak/Lax, „Streaming Systems" (O'Reilly) — das Buch zur Semantik: Watermarks, Trigger, Accumulation, Exactly-Once, Streams↔Tables-Dualität. Geschrieben von den Google-Dataflow-Architekten, deren Modell Flink übernommen hat. Einsatz: Hauptbegleitl…
    m-dataeng:48:e1 [entry] Akidau/Chernyak/Lax, „Streaming Systems" (O'Reilly)
L49: 📄 Tyler Akidau, „Streaming 101" + „Streaming 102" — [oreilly.com/radar/the-world-beyond-batch-streaming-101] (https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (frei). Die Kurzfassung des Buchs als zwei Essays. Einsatz: vor Semesterstart — i…
    m-dataeng:49:u1 [url] https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/  «oreilly.com/radar/the-world-beyond-batch-streaming-101»
L50: 📄 Carbone et al., „Apache Flink: Stream and Batch Processing in a Single Engine" + „Lightweight Asynchronous Snapshots for Distributed Dataflows" (Chandy-Lamport-Variante hinter Flinks Checkpointing) — Papers direkt aus dem TU-Berlin-Umfeld. Einsatz: Pflichtl…
    m-dataeng:50:e1 [entry] Carbone et al., „Apache Flink: Stream and Batch Processing in a Single Engine"
L51: 🎓 Stanford CS246 „Mining of Massive Datasets" — [web.stanford.edu/class/cs246] (https://web.stanford.edu/class/cs246/) · Buch frei auf [mmds.org] (http://www.mmds.org/). Kapitel 4 (Mining Data Streams) liefert die Algorithmen-Seite: Sampling, Bloom Filter, Coun…
    m-dataeng:51:u1 [url] https://web.stanford.edu/class/cs246/  «web.stanford.edu/class/cs246»  -> same line as ['source-mmds-book']
L52: 🛠 Apache Flink Training & Docs — [nightlies.apache.org/flink] (https://nightlies.apache.org/flink/flink-docs-stable/) (Learn-Flink-Tutorials: DataStream API, Event Time, State, Checkpointing). Einsatz: Hands-on parallel zur Vorlesung — ein kleines Event-Time-W…
    m-dataeng:52:u1 [url] https://nightlies.apache.org/flink/flink-docs-stable/  «nightlies.apache.org/flink»
L53: 📚 Kleppmann, „Designing Data-Intensive Applications", Kapitel 11 (Stream Processing) — die beste Einbettung von Streams ins Gesamtbild verteilter Datensysteme (Logs, Kafka, CDC, Exactly-Once-Mythen). Einsatz: Wiederholungslektüre vor der Prüfung; verbindet MD…
    m-dataeng:53:e1 [entry] Kleppmann, „Designing Data-Intensive Applications"  -> title ~ source-kleppmann-ddia (1.00)
L59: 🎓 Böhms eigene Kursseiten (TU Graz → TU Berlin), alle Folien frei — [aktuelle Ausgabe WiSe 25/26] (https://mboehm7.github.io/teaching/ws2526_dia/index.htm) · [WS 21/22 mit allen PDFs] (https://mboehm7.github.io/teaching/ws2122_dia/index.htm) · [Übersicht auf mb…
    m-dataeng:59:u1 [url] https://mboehm7.github.io/teaching/ws2526_dia/index.htm  «aktuelle Ausgabe WiSe 25/26»
    m-dataeng:59:u2 [url] https://mboehm7.github.io/teaching/ws2122_dia/index.htm  «WS 21/22 mit allen PDFs»
    m-dataeng:59:u3 [url] https://mboehm7.github.io/  «Übersicht auf mboehm7.github.io»
    m-dataeng:59:u4 [url] https://philipportner.github.io/DIA-Notes/  «Studenten-Mitschrift DIA-Notes»
L60: 📚 Doan/Halevy/Ives, „Principles of Data Integration" — das Standardwerk zur Integrationstheorie: Schema Matching, Mappings (GAV/LAV), Entity Resolution, Datenaustausch. Einsatz: Vertiefung der ersten Semesterhälfte; die formalen Mapping-Kapitel sind klausurre…
    m-dataeng:60:e1 [entry] Doan/Halevy/Ives, „Principles of Data Integration"
L61: 📚 Ilyas/Chu, „Data Cleaning" (ACM Books) — systematische Abdeckung von Fehlererkennung, Constraint-basiertem Cleaning, Deduplizierung, ML-gestütztem Cleaning. Einsatz: für den Cleaning-Block; gleichzeitig EDML-Vorinvestition (Überschneidung der beiden Module!…
    m-dataeng:61:e1 [entry] Ilyas/Chu, „Data Cleaning" (ACM Books)
L62: 🛠 Apache SystemDS — [systemds.apache.org] (https://systemds.apache.org/) — Böhms eigenes System (er ist Gründungs-Committer); die DIA-Programmierprojekte in Graz liefen auf SystemDS/DAPHNE. Einsatz: Codebasis anschauen, bevor du in seine Sprechstunde gehst — u…
    m-dataeng:62:u1 [url] https://systemds.apache.org/  «systemds.apache.org»
L63: 📄 Stonebraker et al., „Data Curation at Scale: The Data Tamer System" (CIDR 2013) + Konda et al., „Magellan: Toward Building Entity Matching Management Systems" (VLDB 2016) — zwei Systeme-Papers, die Integration end-to-end denken. Einsatz: Zusatzstoff für Tra…
    m-dataeng:63:e1 [entry] Stonebraker et al., „Data Curation at Scale: The Data Tamer System" (CIDR 2013)
L69: 📚 Abedjan/Golab/Naumann/Papenbrock, „Data Profiling" (Synthesis Lectures) — vom Modulverantwortlichen selbst. Unique Column Combinations, funktionale/Inklusions-Abhängigkeiten, Discovery-Algorithmen (TANE & Co.). Einsatz: Hauptlektüre — wer das Buch des Prüfe…
    m-dataeng:69:e1 [entry] Abedjan/Golab/Naumann/Papenbrock, „Data Profiling" (Synthesis Lectures)  -> title ~ source-abedjan-data-profiling (1.00)
L70: 🎓 HPI-Vorlesungen (Naumann-Gruppe): „Data Profiling" + „Information Integration" — [hpi.de Data-Profiling-Kursseite] (https://hpi.de/en/naumann/teaching/course-archive.html); Folien und teils Videos öffentlich (tele-Task/openHPI). Abedjans wissenschaftliche He…
    m-dataeng:70:u1 [url] https://hpi.de/en/naumann/teaching/course-archive.html  «hpi.de Data-Profiling-Kursseite»  -> title ~ source-abedjan-data-profiling (0.50)
    m-dataeng:70:u2 [url] https://open.hpi.de/courses/data-engineering2020  «z. B. „Data Engineering und Data Science"»  -> title ~ source-kroese-dsml (0.67), source-pydata-handbook (0.67), source-vershynin-hdp (0.67)
L71: 📄 Naumann/Herschel, „An Introduction to Duplicate Detection" (Synthesis Lectures) + Papadakis et al., „Blocking and Filtering Techniques for Entity Resolution: A Survey" (ACM CSUR 2020) — Duplikaterkennung von Grundlagen bis State of the Art. Einsatz: für den…
    m-dataeng:71:e1 [entry] Naumann/Herschel, „An Introduction to Duplicate Detection"
L72: 📚 Doan/Halevy/Ives (s. DILA) — doppelt nutzbar; die beiden Module teilen sich das theoretische Fundament, unterscheiden sich aber in Tiefe (Abedjan: Algorithmen) vs. Breite (Böhm: Systeme).
    m-dataeng:72:e1 [entry] Doan/Halevy/Ives
L78: 📄 Schelters eigene Papers — Pflichtprogramm: „Automating Large-Scale Data Quality Verification" (VLDB 2018, das Deequ-Paper) · „mlinspect: Lightweight Inspection of Native ML Pipelines" (CIDR 2021 — Provenance/Inspection über Pipeline-DAGs, konzeptioneller St…
    m-dataeng:78:e1 [entry] Schelters eigene Papers — Pflichtprogramm
L79: 🎓 MIT „Introduction to Data-Centric AI" — [dcai.csail.mit.edu] (https://dcai.csail.mit.edu/) · [Videos auf YouTube] (https://www.youtube.com/@dcai-course) · [Labs auf GitHub] (https://github.com/dcai-course/dcai-course). Der einzige offene Kurs, der EDMLs Kernth…
    m-dataeng:79:u1 [url] https://dcai.csail.mit.edu/  «dcai.csail.mit.edu»
    m-dataeng:79:u2 [url] https://www.youtube.com/@dcai-course  «Videos auf YouTube»
    m-dataeng:79:u3 [url] https://github.com/dcai-course/dcai-course  «Labs auf GitHub»
L80: 🎓 Stanford CS329S „Machine Learning Systems Design" (Chip Huyen) — [stanford-cs329s.github.io] (https://stanford-cs329s.github.io/) (Notes öffentlich) + 📚 Huyen, „Designing Machine Learning Systems" (O'Reilly). Kapitel zu Training Data, Feature Engineering, Da…
    m-dataeng:80:u1 [url] https://stanford-cs329s.github.io/  «stanford-cs329s.github.io»
L81: 🛠 Deequ / Great Expectations / TFX Data Validation — [github.com/awslabs/deequ] (https://github.com/awslabs/deequ) (Schelters System aus seiner Amazon-Zeit!), [greatexpectations.io] (https://greatexpectations.io/), TFDV-Tutorials. Einsatz: eines davon im Portfo…
    m-dataeng:81:u1 [url] https://github.com/awslabs/deequ  «github.com/awslabs/deequ»
    m-dataeng:81:u2 [url] https://greatexpectations.io/  «greatexpectations.io»
L82: 📚 Ilyas/Chu, „Data Cleaning" (s. DILA) — die wissenschaftliche Tiefe hinter dem Cleaning-Teil. Doppelnutzung DILA↔EDML im selben WiSe ist ein echter Synergie-Gewinn.
    m-dataeng:82:e1 [entry] Ilyas/Chu, „Data Cleaning"
L88: 🎓 CMU 10-414/714 „Deep Learning Systems" (Chen/Kolter) — [dlsyscourse.org] (https://dlsyscourse.org/) · [Lectures] (https://dlsyscourse.org/lectures/) · [YouTube-Playlist] (https://www.youtube.com/playlist?list=PLGzYMymX8amNyGPuJ35YWdq59eQ5jYCZ1). Du baust „Need…
    m-dataeng:88:u2 [url] https://dlsyscourse.org/lectures/  «Lectures»  -> same line as ['source-cmu-10414']
    m-dataeng:88:u3 [url] https://www.youtube.com/playlist?list=PLGzYMymX8amNyGPuJ35YWdq59eQ5jYCZ1  «YouTube-Playlist»  -> same line as ['source-cmu-10414']
L89: 🎓 Stanford MLSys Seminar (CS528) — [mlsys.stanford.edu] (https://mlsys.stanford.edu/) · [YouTube-Kanal] (https://www.youtube.com/c/StanfordMLSysSeminars). 100+ Talks von Praktikern (Serving, Feature Stores, Model Management, LLM-Inference). Einsatz: à la carte…
    m-dataeng:89:u1 [url] https://mlsys.stanford.edu/  «mlsys.stanford.edu»
    m-dataeng:89:u2 [url] https://www.youtube.com/c/StanfordMLSysSeminars  «YouTube-Kanal»
L90: 📚 „Machine Learning Systems" (Vijay Janapa Reddi, Harvard) — [mlsysbook.ai] (https://mlsysbook.ai/) (frei, lebendes Lehrbuch). Kapitel zu Model Optimization, Serving, MLOps, Monitoring — das fehlende Lehrbuch zwischen Huyens Praxisbuch und Systems-Papers. Eins…
    m-dataeng:90:u1 [url] https://mlsysbook.ai/  «mlsysbook.ai»
L91: 📄 Papers: „TFX: A TensorFlow-Based Production-Scale ML Platform" (KDD 2017) · „Hidden Technical Debt" (s. o.) · „Clipper: A Low-Latency Online Prediction Serving System" (NSDI 2017) · „Model Cards for Model Reporting" (FAT 2019 — Schelter-nahe Responsibility-…
    m-dataeng:91:e1 [entry] Papers
L92: 🛠 MLflow + Weights&Biases (Tracking) · TorchServe/Triton/ONNX Runtime (Serving) — offizielle Tutorials. Einsatz: ein Mini-Projekt „Modell trainieren → registrieren → servieren → überwachen" einmal end-to-end bauen; genau dieses Skelett verlangen MLMMI-Portfol…
    m-dataeng:92:e1 [entry] MLflow + Weights&Biases (Tracking) · TorchServe/Triton/ONNX Runtime (Serving)
L98: 📚 Kleppmann, „Designing Data-Intensive Applications" — falls du nur ein Buch für verteilte Datensysteme liest, dann dieses: Replikation, Partitionierung, Konsistenz, Batch (MapReduce/Spark), Streams. Einsatz: komplett; DDIA ist außerdem die gemeinsame Wissens…
    m-dataeng:98:e1 [entry] Kleppmann, „Designing Data-Intensive Applications"  -> title ~ source-kleppmann-ddia (1.00)
L100: 📄 Klassiker-Papers: „MapReduce" (OSDI 2004) · „Resilient Distributed Datasets" (Spark, NSDI 2012) · „Dremel" (VLDB 2010) · „The Google File System" (SOSP 2003) · dazu Böhms „SystemDS: A Declarative ML System" (CIDR 2020). Einsatz: Reading-Grundstock; das Syst…
    m-dataeng:100:e1 [entry] Klassiker-Papers
L101: 🛠 Spark- und Flink-Doku/Tutorials + Fundamentals of Data Engineering (Reis/Housley, O'Reilly) als Praxis-Rahmenbuch über Pipelines, Orchestrierung, Storage-Formate (Parquet/Iceberg). Einsatz: begleitend zur Projektarbeit.
    m-dataeng:101:e1 [entry] Spark- und Flink-Doku/Tutorials
L107: 📄 Venues, aus denen die Paper kommen: CIDR ([cidrdb.org] (https://www.cidrdb.org/) — alle Papers frei), SIGMOD, VLDB ([vldb.org/pvldb] (https://www.vldb.org/pvldb/) — frei), MLSys ([mlsys.org] (https://mlsys.org/)). Einsatz: vorab je ein, zwei aktuelle Jahrgänge…
    m-dataeng:107:u1 [url] https://www.cidrdb.org/  «cidrdb.org»
    m-dataeng:107:u2 [url] https://www.vldb.org/pvldb/  «vldb.org/pvldb»
    m-dataeng:107:u3 [url] https://mlsys.org/  «mlsys.org»
L108: 📄 Einstiegs-Surveys: „Machine Learning for Databases" bzw. learned-components-Literatur (z. B. „The Case for Learned Index Structures", SIGMOD 2018) für die eine Richtung; „A Survey on Deep Learning Data Systems"-artige Überblicke und Schelters/Böhms eigene Ü…
    m-dataeng:108:e1 [entry] Einstiegs-Surveys
L109: 📄 S. Keshav, „How to Read a Paper" — [frei als PDF] (https://web.stanford.edu/class/ee384m/Handouts/HowtoReadPaper.pdf). Drei-Pass-Methode; 2 Seiten. Einsatz: einmal lesen, dauerhaft anwenden — auch für Research Seminar DEEM und die Thesis-Literaturphase.
    m-dataeng:109:u1 [url] https://web.stanford.edu/class/ee384m/Handouts/HowtoReadPaper.pdf  «frei als PDF»
L110: 🎓 Stanford MLSys Seminar (s. MLMMI) + CMU DB Group „Vaccination Database Tech Talks" ([db.cs.cmu.edu] (https://db.cs.cmu.edu/) → Seminars, alle auf YouTube) — laufende Talk-Reihen, in denen Paper-Autoren ihre Systeme selbst vorstellen. Einsatz: zum gewählten R…
    m-dataeng:110:u1 [url] https://db.cs.cmu.edu/  «db.cs.cmu.edu»
L116: 📚 Hogan et al., „Knowledge Graphs" (ACM Computing Surveys 2021) — [frei: aidanhogan.com] (https://aidanhogan.com/docs/knowledge-graphs-computing-surveys.pdf) / [arXiv 2003.02320] (https://arxiv.org/abs/2003.02320); auch als Buch (Synthesis Lectures). Deckt Bloc…
    m-dataeng:116:u2 [url] https://arxiv.org/abs/2003.02320  «arXiv 2003.02320»  -> same line as ['source-hogan-knowledge-graphs']
L117: 🎓 Stanford CS520 „Knowledge Graphs" — [web.stanford.edu/class/cs520] (https://web.stanford.edu/class/cs520/) (Seminar, Videos öffentlich). Einsatz: semesterbegleitend, besonders für den Aufbau-/LLM-Teil (Block II).
    m-dataeng:117:u1 [url] https://web.stanford.edu/class/cs520/  «web.stanford.edu/class/cs520»
L118: 📄 W3C RDF/SPARQL + Property Graphs/Cypher — die Abfragesprachen aus Block I. Einsatz: Hands-on mit einem Triple-Store (Apache Jena) oder Neo4j.
    m-dataeng:118:e1 [entry] W3C RDF/SPARQL + Property Graphs/Cypher
L119: 📄 KG-Embeddings: Bordes et al., „Translating Embeddings (TransE)" (NeurIPS 2013) + Wang et al., „Knowledge Graph Embedding: A Survey" (IEEE TKDE 2017). Einsatz: für den Embedding-Block.
    m-dataeng:119:e1 [entry] KG-Embeddings
L120: 🛠 PyKEEN ([github.com/pykeen/pykeen] (https://github.com/pykeen/pykeen)) + Neo4j / Apache Jena — Embedding-Library bzw. Storage/Query. Einsatz: Portfolio-Projekt.
    m-dataeng:120:u1 [url] https://github.com/pykeen/pykeen  «github.com/pykeen/pykeen»
L121: Cross: KG-Aufbau (Anreicherung/Angleichung) = Entity Resolution/Schema Matching aus DI:AS (§6) — gleiche Algorithmen, andere Verpackung.
    m-dataeng:121:e1 [entry] Cross
L127: 📄 Wilkinson et al., „The FAIR Guiding Principles for scientific data management and stewardship" (Scientific Data 2016) — das Gründungspaper der FAIR-Bewegung; Kern des Datenqualitäts-/FAIRness-Teils. Einsatz: Pflicht, zuerst lesen.
    m-dataeng:127:e1 [entry] Wilkinson et al., „The FAIR Guiding Principles for scientific data management and stewardship" (Scientific Data 2016)
L128: 🌐 NFDI / NFDI4DataScience — [nfdi.de] (https://www.nfdi.de/) — Schimmlers Konsortium; Research Knowledge Graphs + FAIR Digital Objects als Infrastruktur. Einsatz: der konkrete Anwendungskontext des Moduls.
    m-dataeng:128:u1 [url] https://www.nfdi.de/  «nfdi.de»
L129: 📚 Hogan et al., „Knowledge Graphs" (s. §11) — die KG-Hälfte, doppelt nutzbar. Einsatz: Überschneidung mit KG&AI gezielt ausnutzen.
    m-dataeng:129:e1 [entry] Hogan et al., „Knowledge Graphs"  -> title ~ source-hogan-knowledge-graphs (1.00)
L130: 🌐 Open Research Knowledge Graph (ORKG) — [orkg.org] (https://orkg.org/) + GO-FAIR/RDM-Grundlagen. Einsatz: konkretes Beispiel eines Research-KG für Exposé/Projekt.
    m-dataeng:130:u1 [url] https://orkg.org/  «orkg.org»
L131: Cross: überlappt mit Schelters Responsible-DE-Linie (Datenqualität, Reproduzierbarkeit) und mit KG&AI (§11). Hinweis: Themen variieren semesterweise → beim Modulstart das aktuelle Programm prüfen.
    m-dataeng:131:e1 [entry] Cross
L138: 📚 Newman, „Building Microservices" (2. Aufl., O'Reilly) — Service-Decomposition, Deployment, Resilienz. Einsatz: für den Microservices-/Architektur-Teil.
    m-dataeng:138:e1 [entry] Newman, „Building Microservices" (2. Aufl., O'Reilly)
L139: 🌐 CNCF / Kubernetes-Doku + AWS Well-Architected Framework — Praxis-Referenz zu Container-Orchestrierung & Serverless. Einsatz: semesterbegleitend.
    m-dataeng:139:e1 [entry] CNCF / Kubernetes-Doku + AWS Well-Architected Framework
L140: 📄 „Twelve-Factor App" ([12factor.net] (https://12factor.net/)) + Fowler/Lewis, „Microservices" — die Architektur-Prinzipien kompakt. Einsatz: schneller Einstieg.
    m-dataeng:140:u1 [url] https://12factor.net/  «12factor.net»
L141: Cross: Skalierbarkeit/Resilienz überlappt mit Scalability Engineering & CSB (📊-Block); Patterns ähneln der AWS Builders' Library.
    m-dataeng:141:e1 [entry] Cross
L147: 🛠 AWS Free Tier + AWS Well-Architected Labs — [wellarchitectedlabs.com] (https://wellarchitectedlabs.com/) — Hands-on mit echten Services. Einsatz: Pflicht — das Modul lebt vom Bauen.
    m-dataeng:147:u1 [url] https://wellarchitectedlabs.com/  «wellarchitectedlabs.com»
L148: 🛠 Infrastructure as Code: Terraform + AWS CDK + Serverless Framework — reproduzierbare Deployments. Einsatz: für saubere, bewertbare Prototypen.
    m-dataeng:148:e1 [entry] Infrastructure as Code
L149: 📚 Cloud Native (§13) als theoretischer Unterbau — gleiche Tai-Linie. Einsatz: Architekturentscheidungen begründen.
    m-dataeng:149:e1 [entry] Cloud Native (§13)
L150: Cross: „quality-driven assessment" = Benchmarking-Methodik (CSB/📊); dokumentiere Messungen nach Bermbach-Regeln, dann ist das Projekt thesis-zitierfähig.
    m-dataeng:150:e1 [entry] Cross
L156: 📚 Abedjan/Golab/Naumann/Papenbrock, „Data Profiling" (Synthesis Lectures) — wie bei DI:AS (§6): vom Seminarleiter, die thematische Grundlage. Einsatz: Hauptlektüre.
    m-dataeng:156:e1 [entry] Abedjan/Golab/Naumann/Papenbrock, „Data Profiling" (Synthesis Lectures)  -> title ~ source-abedjan-data-profiling (1.00)
L157: 📄 Aktuelle Venues für die Paper-Auswahl: VLDB, SIGMOD, ICDE (Data Integration / Preparation / Cleaning Tracks). Einsatz: das Exposé an einem aktuellen Paper dieser Konferenzen aufhängen.
    m-dataeng:157:e1 [entry] Aktuelle Venues für die Paper-Auswahl
L158: 🛠 Praxis-Tools: Deequ/PyDeequ (Datenqualität, Schelter), skrub, OpenRefine — passend zum Datenaufbereitungs-Fokus. Einsatz: für den praktischen Teil/die begleitete Thesis.
    m-dataeng:158:e1 [entry] Praxis-Tools
L159: 🎓 Paper-Reading-Methodik: Keshav, „How to Read a Paper" (s. ML&DMS §10) + HPI-Naumann-Folien (s. DI:AS §6). Einsatz: für Exposé und Präsentation.
    m-dataeng:159:e1 [entry] Paper-Reading-Methodik
L160: Cross: identisches Fundament wie DI:AS (§6) — wer DI:AS belegt, hat das Seminar inhaltlich halb erledigt. Hinweis: explizit thesis-begleitend → an deine DEEM/DAMS-Thesis koppeln.
    m-dataeng:160:e1 [entry] Cross
L166: 1. Engine-Linie: DBT (Theorie) → DBTLAB (selbst bauen) → DMH (schnell machen) → Thesis. RookieDB/BusTub im Sommer vor M3 ist die Investition mit dem höchsten Return.
    m-dataeng:166:e1 [entry] Engine-Linie
L167: 2. Integrations-Linie: DILA (Böhm, Breite) ↔ DI:AS (Abedjan, Algorithmen-Tiefe) teilen sich Doan/Halevy/Ives und das Cleaning-Buch — im selben WiSe belegen spart real Lesezeit.
    m-dataeng:167:e1 [entry] Integrations-Linie
L168: 3. DEEM-Linie: EDML → MLMMI → RDE-Projekt → Thesis. Gemeinsamer Kanon: Schelter-Papers (Deequ, mlinspect), Hidden Technical Debt, DCAI-Kurs, Huyen-Buch. mlinspect lesen = Stratum verstehen.
    m-dataeng:168:e1 [entry] DEEM-Linie
L169: 4. Evaluations-Handwerk (Gregg, Benchmarking-Methodik) zieht sich von DMH über CSB bis zur Thesis-Evaluation — einmal lernen, vierfach nutzen.
    m-dataeng:169:e1 [entry] Evaluations-Handwerk
L177: > Ergänzung auf Arams Wunsch: Übungsmaterial mit Lösungen, fremde Klausurarchive, Open-Source-Repos zum Architektur-Lernen. Quellen u. a. [build-your-own-x] (https://github.com/codecrafters-io/build-your-own-x) („Build your own Database") und Arams Ultimate-In…
    m-dataeng:177:u1 [url] https://github.com/codecrafters-io/build-your-own-x  «build-your-own-x»
L182: 📝 Berkeley CS186: Discussion Worksheets + Exam-Archiv — die Kursseiten je Semester ([cs186berkeley.net] (https://cs186berkeley.net/)) veröffentlichen Worksheets mit Lösungen und Altklausuren; zusätzlich führt das Berkeley-HKN-Archiv ältere CS186-Klausuren. Bes…
    m-dataeng:182:u1 [url] https://cs186berkeley.net/  «cs186berkeley.net»
L183: 📝 MIT 6.5830: Practice Quizzes — auf der [Assignments-Seite] (https://dsg.csail.mit.edu/6.5830/assign.php) liegen Übungs-Quizzes + ältere Quizzes mit Lösungen; zusätzlich [6.830 Fall 2010 auf OCW] (https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/)…
    m-dataeng:183:u1 [url] https://dsg.csail.mit.edu/6.5830/assign.php  «Assignments-Seite»
    m-dataeng:183:u2 [url] https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/  «6.830 Fall 2010 auf OCW»
L184: 📝 Flink Training Exercises — [github.com/apache/flink-training] (https://github.com/apache/flink-training): offizielle Übungsaufgaben mit Lösungs-Branches (Event Time, Windows, State). Das praktische MDS-Pflichttraining.
    m-dataeng:184:u1 [url] https://github.com/apache/flink-training  «github.com/apache/flink-training»
L188: 🛠 cstack/db_tutorial — [github.com/cstack/db_tutorial] (https://github.com/cstack/db_tutorial): „Let's Build a Simple Database" (SQLite-Klon in C, Schritt für Schritt — der build-your-own-x-Klassiker). Einsatz: Wochenend-Warm-up vor DBTLAB; B-Tree + Pager from…
    m-dataeng:188:u1 [url] https://github.com/cstack/db_tutorial  «github.com/cstack/db_tutorial»
L189: 🛠 skyzh/mini-lsm — [github.com/skyzh/mini-lsm] (https://github.com/skyzh/mini-lsm): geführtes Tutorial, eine LSM-Storage-Engine in Rust zu bauen (vom BusTub-TA). Moderne Storage-Seite, die RookieDB nicht abdeckt.
    m-dataeng:189:u1 [url] https://github.com/skyzh/mini-lsm  «github.com/skyzh/mini-lsm»
L190: 🛠 erikgrinaker/toydb — [github.com/erikgrinaker/toydb] (https://github.com/erikgrinaker/toydb): verteilte SQL-DB in Rust mit exzellent dokumentierter Architektur (Parser→Planner→Optimizer→Executor→Raft) — als Lese-Repo ideal, um eine komplette Engine-Pipeline…
    m-dataeng:190:u1 [url] https://github.com/erikgrinaker/toydb  «github.com/erikgrinaker/toydb»
L191: 🛠 risinglightdb/risinglight — [github.com/risinglightdb/risinglight] (https://github.com/risinglightdb/risinglight): educational OLAP-DB in Rust (vektorisierte Execution!) — die DMH-Konzepte (Spaltenlayout, Vektorisierung) in lesbarem Code.
    m-dataeng:191:u1 [url] https://github.com/risinglightdb/risinglight  «github.com/risinglightdb/risinglight»
L192: 🛠 Apache Calcite — [github.com/apache/calcite] (https://github.com/apache/calcite): der Industrie-Standard-Query-Optimizer in Java (regelbasiert + Cascades-artig). Für Stratum das wichtigste Lese-Repo dieser Liste: so sieht produktionsreife Rewrite-Infrastrukt…
    m-dataeng:192:u1 [url] https://github.com/apache/calcite  «github.com/apache/calcite»
L193: 🛠 DuckDB — [github.com/duckdb/duckdb] (https://github.com/duckdb/duckdb): moderne In-Process-OLAP-Engine; Optimizer- und Vektorisierungs-Code kompakt genug zum Studieren; dazu der lesenswerte [DuckDB-Blog] (https://duckdb.org/news/) (Pushdown, Out-of-Core-Joins…
    m-dataeng:193:u1 [url] https://github.com/duckdb/duckdb  «github.com/duckdb/duckdb»
    m-dataeng:193:u2 [url] https://duckdb.org/news/  «DuckDB-Blog»
L194: 🛠 DataFusion — [github.com/apache/datafusion] (https://github.com/apache/datafusion): Andy Groves Buch (s. o.) als reales Projekt — logische/physische Pläne + Optimizer-Rules in Rust.
    m-dataeng:194:u1 [url] https://github.com/apache/datafusion  «github.com/apache/datafusion»
L198: 🛠 stefan-grafberger/mlinspect — [github.com/stefan-grafberger/mlinspect] (https://github.com/stefan-grafberger/mlinspect): der Code zum mlinspect-Paper (DAG-Extraktion aus nativen ML-Pipelines) — das architektonisch Stratum-ähnlichste öffentliche Repo; lesen,…
    m-dataeng:198:u1 [url] https://github.com/stefan-grafberger/mlinspect  «github.com/stefan-grafberger/mlinspect»
L199: 🛠 awslabs/deequ (+ python-deequ) — Schelters Data-Quality-System im Produktionszustand; Test-Suite zeigt, wie man Datenqualitäts-Checks API-fähig macht.
    m-dataeng:199:e1 [entry] awslabs/deequ
L200: 🛠 skrub-data/skrub — [github.com/skrub-data/skrub] (https://github.com/skrub-data/skrub): kennst du aus dem Job — hier als Lern-Referenz gelistet, wie sklearn-kompatible Pipeline-APIs designt werden.
    m-dataeng:200:u1 [url] https://github.com/skrub-data/skrub  «github.com/skrub-data/skrub»
L204: 🎓 MIT 6.824 (OCW + aktuelle pdos-Seite) — bereits in §9 verankert; dein Index bestätigt die OCW-Edition als Einstieg.
    m-dataeng:204:e1 [entry] MIT 6.824 (OCW + aktuelle pdos-Seite)
L205: 📚 OSTEP ([pages.cs.wisc.edu/~remzi/OSTEP] (https://pages.cs.wisc.edu/~remzi/OSTEP/)) — OS-Grundlagen (Scheduling, Memory, Concurrency, Persistence) mit Übungs-Homeworks + Simulatoren im Repo; das fehlende Fundament unter DBT-Buffer-Management und DMH. Einsatz:…
    m-dataeng:205:u1 [url] https://pages.cs.wisc.edu/~remzi/OSTEP/  «pages.cs.wisc.edu/~remzi/OSTEP»
L206: 🎓 MIT Missing Semester ([missing.csail.mit.edu] (https://missing.csail.mit.edu/)) — Shell/Git/Debugging-Handwerk mit Übungen; vor DBTLAB-Semestern als Werkzeug-Check.
    m-dataeng:206:u1 [url] https://missing.csail.mit.edu/  «missing.csail.mit.edu»

## m-math — repository/curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning/inputs/MASTERS-MATH-RESOURCES.md

L15: 🎓 Stanford CS229M / STATS214 „Machine Learning Theory" (Tengyu Ma) — [Vorlesungsnotizen frei] (https://web.stanford.edu/class/stats214/) (+ Videos auf YouTube). Moderner Kursdurchgang durch uniforme Konvergenz, Konzentration, VC, Margin-Theorie — gut als Video…
    m-math:15:u1 [url] https://web.stanford.edu/class/stats214/  «Vorlesungsnotizen frei»
L17: 📚 Wainwright, „High-Dimensional Statistics: A Non-Asymptotic Viewpoint" — die schwerere Alternative zu Vershynin (empirische Prozesse, Metrik-Entropie). Einsatz: nur bei echtem Theorie-Appetit oder wenn die Vorlesung Chaining-Argumente formal führt.
    m-math:17:e1 [entry] Wainwright, „High-Dimensional Statistics: A Non-Asymptotic Viewpoint"
L18: 📄 Candès/Wakin, „An Introduction to Compressive Sampling" (IEEE SPM 2008) — das Standard-Tutorial zu Compressive Sensing (~20 Seiten), genau richtig für den CS-Schlussblock des Moduls; Stanczak ist Signalverarbeiter, der Block hat bei ihm Gewicht. Einsatz: vo…
    m-math:18:e1 [entry] Candès/Wakin, „An Introduction to Compressive Sampling" (IEEE SPM 2008)
L25: 📚 Papoulis/Pillai, „Probability, Random Variables and Stochastic Processes" (4. Aufl.) — der EE-Klassiker, dessen Kapitelfolge (RVs → Vektoren → MMSE/Orthogonalität → WSS/Spektraldichte) der Modulgliederung entspricht; MMSE + Orthogonalitätsprinzip + Spektral…
    m-math:25:e1 [entry] Papoulis/Pillai, „Probability, Random Variables and Stochastic Processes" (4. Aufl.)  -> title ~ source-papoulis-pillai (0.88)
L27: 📚 Grimmett/Stirzaker, „Probability and Random Processes" — die Mathematik-Seite: sauber bei Maßwechsel, Konvergenzarten, erzeugenden Funktionen; Tausende Übungsaufgaben (+ Lösungsband „One Thousand Exercises"). Einsatz: Zweitbuch und Aufgabenquelle — mündlich…
    m-math:27:e1 [entry] Grimmett/Stirzaker, „Probability and Random Processes"  -> title ~ source-papoulis-pillai (0.60)
L28: 📚🎓 Bertsekas/Tsitsiklis, „Introduction to Probability" + MIT 6.041 auf OCW (Videos). Brücken-Ressource: falls die axiomatische Grundlage aus dem HU-Bachelor wackelt (relevant: dein Mathe-2-Kontext), ist das der gründlichste sanfte Unterbau — bis ZGS und Marko…
    m-math:28:e1 [entry] Bertsekas/Tsitsiklis, „Introduction to Probability"  -> title ~ source-mit-res6012 (0.75), source-bertsimas-tsitsiklis-lp (0.50), source-blitzstein-hwang (0.50)
L29: 📚 Norris, „Markov Chains" — [Kapitel frei auf der Autoren-Seite] (https://www.statslab.cam.ac.uk/~james/Markov/). Das Standardwerk nur für Markov-Ketten (diskret/stetig, Rekurrenz, Stationarität). Einsatz: Vertiefung des Markov-Blocks, der in der mündlichen Pr…
    m-math:29:u1 [url] https://www.statslab.cam.ac.uk/~james/Markov/  «Kapitel frei auf der Autoren-Seite»
L35: 🎓📄 Toussaints eigenes Vorlesungsskript — komplett öffentlich: [Lecture-Optimization.pdf] (https://www.user.tu-berlin.de/mtoussai/teaching/Lecture-Optimization.pdf) (alle Folien + Übungen als ein indexiertes Skript, explizit „to help prepare for exams") · [Kurs…
    m-math:35:u2 [url] https://www.user.tu-berlin.de/mtoussai/teaching/20-Optimization/  «Kursseite WS 20/21 mit Einzelfolien»  -> same line as ['source-toussaint-optimization-script']
    m-math:35:u3 [url] https://github.com/MarcToussaint  «LaTeX-Quellen auf GitHub»  -> same line as ['source-toussaint-optimization-script']
    m-math:35:u4 [url] https://www.user.tu-berlin.de/mtoussai/teaching/Optimization/16-noFreeLunch.pdf  «No Free Lunch»  -> same line as ['source-toussaint-optimization-script']
    m-math:35:u5 [url] https://www.user.tu-berlin.de/mtoussai/teaching/Optimization/17-bayesOpt.pdf  «Bayesian Optimization»  -> same line as ['source-toussaint-optimization-script']
L36: 📚 Nocedal/Wright, „Numerical Optimization" (2. Aufl.) — das Standardwerk, dessen Kapitel (Line Search/Wolfe, Newton, BFGS, KKT, Penalty/Augmented Lagrangian, Interior Point) Teil 1+2 des Moduls 1:1 abdecken. Einsatz: wo Toussaints Folien zu kompakt sind, lief…
    m-math:36:e1 [entry] Nocedal/Wright, „Numerical Optimization" (2. Aufl.)  -> title ~ source-nocedal-wright (0.80)
L38: 📚 Kochenderfer/Wheeler, „Algorithms for Optimization" (MIT Press) — [frei als PDF (algorithmsbook.com/optimization)] (https://algorithmsbook.com/optimization/). Jeder Algorithmus als lauffähiger Code + Visualisierung; deckt auch Teil 3 (stochastisch, evolution…
    m-math:38:u1 [url] https://algorithmsbook.com/optimization/  «frei als PDF (algorithmsbook.com/optimization)»
L39: 📚 Garnett, „Bayesian Optimization" — [frei, bayesoptbook.com] (https://bayesoptbook.com/). Das Referenzbuch zum variierenden Teil-3-Thema; baut auf Gaußprozessen auf (→ Rasmussen/Williams aus MASTERS-ML-RESOURCES.md §8). Einsatz: nur wenn Teil 3 im Jahrgang Ba…
    m-math:39:u1 [url] https://bayesoptbook.com/  «frei, bayesoptbook.com»
L40: 🛠 CERES Solver / scipy.optimize / JAXopt-Tutorials — das Modul nennt CERES explizit. Einsatz: ein kleines Curve-Fitting-Problem einmal mit CERES (C++) oder scipy (Python) durchziehen; Klausuren fragen gern, welcher Solver-Typ zu welchem Problem passt.
    m-math:40:e1 [entry] CERES Solver / scipy.optimize / JAXopt-Tutorials
L46: 📚 Bertsimas/Tsitsiklis, „Introduction to Linear Optimization" — der Standard für die erste Modulhälfte: Simplex-Varianten, Degeneration, Polyedergeometrie, Dualität, Ellipsoid, Interior Point — mit der geometrischen Intuition, die in mündlichen Prüfungen Punk…
    m-math:46:e1 [entry] Bertsimas/Tsitsiklis, „Introduction to Linear Optimization"  -> title ~ source-bertsimas-tsitsiklis-lp (1.00)
L47: 📚 Korte/Vygen, „Combinatorial Optimization: Theory and Algorithms" — die „Bonner Bibel": Matchings, Matroide, Netzwerkflüsse, ganzzahlige Programme — deckt die zweite Modulhälfte vollständig und auf deutschem Lehrstuhl-Niveau ab (deutsche Ausgabe existiert).…
    m-math:47:e1 [entry] Korte/Vygen, „Combinatorial Optimization: Theory and Algorithms"  -> title ~ source-korte-vygen (1.00), source-schrijver-combinatorial-notes (0.50)
L49: 🎓 MIT 18.433/6.251 (Goemans-Notizen, frei) + MIT OCW „Integer Programming and Combinatorial Optimization" — amerikanische Vorlesungsspur zu Polyedern, Branch & Bound, Schnittebenen. Einsatz: wenn du eine Videoquelle willst; sonst reichen die Bücher.
    m-math:49:e1 [entry] MIT 18.433/6.251 (Goemans-Notizen, frei)
L50: 📚 Matoušek/Gärtner, „Understanding and Using Linear Programming" — Brücken-Ressource: schlank, geometrisch, der schnellste Weg, ADM-I-Lücken (LP-Basics, Dualität) zu schließen, bevor ADM II startet. Einsatz: Sommer davor.
    m-math:50:e1 [entry] Matoušek/Gärtner, „Understanding and Using Linear Programming"
L51: 📚 Wolsey, „Integer Programming" — fokussierte Referenz nur für den ILP-Block (B&B, Cuts, Lagrange-Relaxation). Einsatz: gezielt zur zweiten Semesterhälfte.
    m-math:51:e1 [entry] Wolsey, „Integer Programming"
L58: 📚 Vazirani, „Approximation Algorithms" — der kompaktere Klassiker; Dual Fitting wird hier am Beispiel Set Cover eingeführt — exakt wie im Modulprofil. Einsatz: Zweitdarstellung; Vaziranis kurze, beweis-zentrierte Kapitel sind ideales Material für 30-minütige…
    m-math:58:e1 [entry] Vazirani, „Approximation Algorithms"  -> title ~ source-williamson-shmoys (0.67)
L59: 📄 Goemans/Williamson, „Improved Approximation Algorithms for Maximum Cut and Satisfiability Problems Using Semidefinite Programming" (JACM 1995) — das Original zum SDP-Block; eines der schönsten Papers der theoretischen Informatik. Einsatz: vor dem SDP-Teil l…
    m-math:59:e1 [entry] Goemans/Williamson, „Improved Approximation Algorithms for Maximum Cut and Satisfiability Problems Using Semidefinite P…  -> title ~ source-williamson-shmoys (0.50)
L60: 📚 Arora/Barak, „Computational Complexity: A Modern Approach" (Kapitel zu PCP & Hardness of Approximation; Entwurf frei online) — fürs PCP-Theorem und Gap-Reduktionen die zugänglichste Darstellung. Einsatz: nur den PCP-Block (im Modul „ohne Beweis" — Verständn…
    m-math:60:e1 [entry] Arora/Barak, „Computational Complexity: A Modern Approach"  -> title ~ source-arora-barak (1.00)
L61: 🎓 Anupam Gupta / Ryan O'Donnell (CMU) „Approximation Algorithms"-Vorlesungsnotizen (frei auf den CMU-Seiten) — moderne Kursdurchgänge mit Übungen als US-Spur. Einsatz: Aufgabenquelle; mündliche Prüfungen bei Skutella verlangen Technik-Transfer auf neue Proble…
    m-math:61:e1 [entry] Anupam Gupta / Ryan O'Donnell (CMU) „Approximation Algorithms"-Vorlesungsnotizen
L62: 📚 Korte/Vygen (s. ADM II) — die Approximationskapitel verbinden ADM II und III; bei Belegung beider Module ist das Buch die gemeinsame Klammer.
    m-math:62:e1 [entry] Korte/Vygen  -> title ~ source-korte-vygen (1.00)
L68: 📚 Kay, „Fundamentals of Statistical Signal Processing", Vol. I (Estimation) + Vol. II (Detection) — DER kanonische Detektions-/Schätzungstext; Cramér-Rao, MVU, MLE, Neyman-Pearson stehen 1:1 im Modulprofil. Einsatz: Hauptbuch — Vol. I für den Schätz-, Vol. II…
    m-math:68:e1 [entry] Kay, „Fundamentals of Statistical Signal Processing", Vol. I (Estimation) + Vol. II (Detection)
L69: 📚 Poor, „An Introduction to Signal Detection and Estimation" (Springer) — kompakter, mathematisch elegant; ideal für die Hypothesentests-/Detektionstheorie. Einsatz: Zweitquelle für die Beweisseite.
    m-math:69:e1 [entry] Poor, „An Introduction to Signal Detection and Estimation" (Springer)
L70: 📄 Kschischang/Frey/Loeliger, „Factor Graphs and the Sum-Product Algorithm" (IEEE IT 2001) — der kanonische Faktorgraphen/BP-Artikel; deckt den Sum-Product/Belief-Propagation-Block. Einsatz: Pflicht für den Message-Passing-Teil.
    m-math:70:e1 [entry] Kschischang/Frey/Loeliger, „Factor Graphs and the Sum-Product Algorithm" (IEEE IT 2001)
L71: 📚 Bishop, PRML — Kap. 8 (Graphical Models / Sum-Product = Belief Propagation) + Kap. 2 (MLE/Bayes). Einsatz: didaktische Brücke zu ML 2-X/MI II (du nutzt Bishop ohnehin als Hauptbuch).
    m-math:71:e1 [entry] Bishop, PRML  -> title ~ source-bishop-prml (1.00)
L72: 📄 Donoho/Maleki/Montanari, „Message-Passing Algorithms for Compressed Sensing" (PNAS 2009) — der AMP-Ursprung. Einsatz: nur für den (exotischen) AMP-Block, den kaum ein Lehrbuch abdeckt.
    m-math:72:e1 [entry] Donoho/Maleki/Montanari, „Message-Passing Algorithms for Compressed Sensing" (PNAS 2009)
L73: Cross: MLE/Cramér-Rao = exakt der Schätztheorie-Teil von MI II (ML-Resources §6); BP/Faktorgraphen = die graphischen Modelle aus ML 2-X (ML-Resources §1). Gleiche Caire-Notation wie FoSP (§2).
    m-math:73:e1 [entry] Cross
L79: 📚 Cover & Thomas, „Elements of Information Theory" (2. Aufl., Wiley) — das kanonische IT-Lehrbuch; Entropie, Kanalkapazität, Rate-Distortion 1:1 zum Profil. Einsatz: Hauptbuch.
    m-math:79:e1 [entry] Cover & Thomas, „Elements of Information Theory" (2. Aufl., Wiley)
L80: 📚 MacKay, „Information Theory, Inference, and Learning Algorithms" — [frei: inference.org.uk/mackay/itila] (https://www.inference.org.uk/mackay/itila/). Verbindet IT direkt mit ML/Inferenz — für dich die ideale Brücke (gleiche Sprache wie FoSIDE/ML). Einsatz:…
    m-math:80:u1 [url] https://www.inference.org.uk/mackay/itila/  «frei: inference.org.uk/mackay/itila»
L81: 🎓 Stanford EE376A „Information Theory" (Weissman) — Notes + Übungen frei. Einsatz: semesterbegleitende Video-/Aufgabenspur.
    m-math:81:e1 [entry] Stanford EE376A „Information Theory" (Weissman)
L82: 📄 Tishby/Pereira/Bialek, „The Information Bottleneck Method" (1999) + Alemi et al., „Deep Variational Information Bottleneck" (ICLR 2017) — der direkte IT↔Deep-Learning-Brückenschlag. Einsatz: für den Projektteil bzw. um den ML-Bezug sauber zu zeigen.
    m-math:82:e1 [entry] Tishby/Pereira/Bialek, „The Information Bottleneck Method" (1999)
L83: Cross: KL-Divergenz/Cross-Entropy = die Loss-Funktionen aus DL1/DL2; Rate-Distortion ↔ VAE/Kompression (DL2, ML-Resources §3).
    m-math:83:e1 [entry] Cross
L89: 1. Zwei Teilachsen: Stochastik/Lerntheorie (MathML + FoSP) vs. Optimierung (OptAlgos + ADM II/III). Für dein Profil (Optimizer/Runtime!) hat die Optimierungsschiene Priorität; MathML ist die theorieseitige Absicherung deiner ML-Module.
    m-math:89:e1 [entry] Zwei Teilachsen
L90: 2. Buch-Synergien: SSBD trägt MathML und MI I (Lerntheorie-Teil); Boyd trägt OptAlgos und die SVM-Dualität in ML 2-X; Rasmussen/Williams (ML-RESOURCES §8) trägt Gaußprozesse und Garnetts Bayes-Optimierung.
    m-math:90:e1 [entry] Buch-Synergien
L91: 3. Kostenlos-Quote: Fast die gesamte Achse ist legal frei verfügbar — SSBD, Mohri, Vershynin, Toussaint-Skript, Kochenderfer, Garnett, Schrijver, Williamson/Shmoys, Boyd. Nur Papoulis, Nocedal/Wright, Korte/Vygen und Bertsimas/Tsitsiklis brauchen die Biblioth…
    m-math:91:e1 [entry] Kostenlos-Quote
L92: 4. ADM-Warnung: ADM II/III sind 10-LP-Module der Mathe-Fakultät mit mündlicher Prüfung bei Skutella — hohes Niveau, hoher Ertrag fürs ⚙️-Profil, aber nicht neben einem Implementierungs-Brocken (DBTLAB/BDSPRO) ins selbe Semester legen (Regel §4.2 im MODULE-MEN…
    m-math:92:e1 [entry] ADM-Warnung
L93: 5. Mathe-2-Dividende: Bertsekas/Tsitsiklis (FoSP-Brücke) und Matoušek/Gärtner (ADM-Brücke) sind gleichzeitig solide Wiederholungsarbeit für den Bachelor-Drittversuch — Sommer-Investition mit Doppelnutzen.
    m-math:93:e1 [entry] Mathe-2-Dividende
L104: 📝 Stanford EE364a (Boyd): Homework + Final-Archiv — die Kursseite veröffentlicht Psets und alte Finals (mit Lösungen); zusätzlich das offizielle Boyd/Vandenberghe-Buch „Additional Exercises" mit Lösungs-Repo. Rechentraining für KKT/Dualität (OptAlgos + ML-2-X…
    m-math:104:e1 [entry] Stanford EE364a (Boyd): Homework + Final-Archiv
L105: 📝 Toussaints eigene Übungen — bereits im Komplett-Skript (s. §3) enthalten — das ist das Klausurtraining für OptAlgos; nicht doppelt suchen.
    m-math:105:e1 [entry] Toussaints eigene Übungen
L106: 📝 MIT OCW 6.262 „Discrete Stochastic Processes" — neben den Videos liegen dort Psets + Quizzes mit Lösungen — die FoSP-Übungsschiene (Markov-Ketten, Konvergenz).
    m-math:106:e1 [entry] MIT OCW 6.262 „Discrete Stochastic Processes"  -> title ~ source-gallager-stochastic-processes (0.80)
L107: 📝 Grimmett/Stirzaker: „One Thousand Exercises in Probability" — der offizielle Lösungsband zum FoSP-Zweitbuch; mündliche Prüfungen bei Caire mit 20–30 durchgerechneten Aufgaben betreten ist ein anderes Spiel.
    m-math:107:e1 [entry] Grimmett/Stirzaker: „One Thousand Exercises in Probability"
L108: 📝 MIT OCW 6.042J (aus deinem Ultimate-Index) — Mathematics for CS mit kompletten Psets/Exams + Lösungen: kein Master-Stoff, aber das ideale TheoInf-/Beweis-Auffrischtraining parallel zum Mathe-2-Drittversuch und für den R2-Zugangscheck.
    m-math:108:e1 [entry] MIT OCW 6.042J (aus deinem Ultimate-Index)
L109: 📝 ADM-Übungsersatz: MIT OCW [18.433 Combinatorial Optimization / 6.251 Intro to Mathematical Programming] — Psets mit Lösungen als Ersatz für die internen COGA-Blätter; dazu Schrijvers Skript-Übungen (s. §4).
    m-math:109:e1 [entry] ADM-Übungsersatz
L113: 🛠 CVXPY — [cvxpy.org] (https://www.cvxpy.org/) (+ Beispielgalerie): konvexe Programme deklarativ lösen; jede EE364a-Aufgabe lässt sich damit gegenprüfen. Einsatz: Selbstkontrolle beim Dualitäts-Lernen.
    m-math:113:u1 [url] https://www.cvxpy.org/  «cvxpy.org»
L114: 🛠 Toussaints LaTeX/Code-Repos — [github.com/MarcToussaint] (https://github.com/MarcToussaint): Skriptquellen + Robotik/Optimierungs-Code des Dozenten.
    m-math:114:u1 [url] https://github.com/MarcToussaint  «github.com/MarcToussaint»
L115: 🛠 Project Euler + Exercism (aus deinem Ultimate-Index) — mathematische Programmierprobleme als Dauer-Fingerübung; Euler-Probleme 1–100 sind diskrete-Mathe-Kondition für ADM-Niveau.
    m-math:115:e1 [entry] Project Euler + Exercism (aus deinem Ultimate-Index)
L116: 🛠 MML-Buch-Notebooks — [github.com/mml-book/mml-book.github.io] (https://github.com/mml-book/mml-book.github.io): Übungen + Jupyter-Begleitcode zur Mathe-Brücke (Deisenroth).
    m-math:116:u1 [url] https://github.com/mml-book/mml-book.github.io  «github.com/mml-book/mml-book.github.io»

## m-ml — repository/curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning/inputs/MASTERS-ML-RESOURCES.md

L14: 📄 Müller/Mika/Rätsch/Tsuda/Schölkopf, „An Introduction to Kernel-Based Learning Algorithms" (IEEE TNN 2001) — vom Prüfer selbst, das kanonische Kernel-Tutorial seiner Gruppe (SVM, Kernel-PCA, Fisher-Diskriminante). Einsatz: vor Semesterstart lesen; die Notati…
    m-ml:14:e1 [entry] Müller/Mika/Rätsch/Tsuda/Schölkopf, „An Introduction to Kernel-Based Learning Algorithms" (IEEE TNN 2001)  -> title ~ source-mueller-kernel-tutorial (1.00), source-mit-6s191 (0.50)
L15: 📚 Schölkopf/Smola, „Learning with Kernels" (MIT Press) — die Vollversion der Kernel-Theorie: RKHS, Repräsenter-Theorem, Kernels für Strings/Graphen (= „strukturierte Daten" aus dem Modulprofil). Einsatz: Vertiefung parallel zum Kernel-Block; Kapitel zu strukt…
    m-ml:15:e1 [entry] Schölkopf/Smola, „Learning with Kernels" (MIT Press)  -> title ~ source-schoelkopf-smola-lwk (1.00)
L17: 📚 Hastie/Tibshirani/Friedman, „The Elements of Statistical Learning" — [frei als PDF] (https://hastie.su.domains/ElemStatLearn/). Kapitel 10 (Boosting/AdaBoost als additive Modellierung) und 12 (SVMs) liefern die statistische Sicht, die Müllers Vorlesung mit d…
    m-ml:17:u1 [url] https://hastie.su.domains/ElemStatLearn/  «frei als PDF»
L18: 🎓 Stanford CS228 „Probabilistic Graphical Models" — [Kursnotizen frei] (https://ermongroup.github.io/cs228-notes/) (Ermon-Gruppe). Kompakter als Koller/Friedman, deckt Repräsentation/Inferenz/Lernen graphischer Modelle ab. Einsatz: wenn der PGM-Teil der Vorles…
    m-ml:18:u1 [url] https://ermongroup.github.io/cs228-notes/  «Kursnotizen frei»
L19: 📚 Chapelle/Schölkopf/Zien (Hrsg.), „Semi-Supervised Learning" (MIT Press) — das Referenzwerk zum SSL-Block (Self-Training, Co-Training, graphbasierte Verfahren, transduktive SVMs), aus dem Max-Planck-Umfeld der Müller-Schule. Einsatz: gezielt die Einführungsk…
    m-ml:19:e1 [entry] Chapelle/Schölkopf/Zien (Hrsg.), „Semi-Supervised Learning" (MIT Press)
L27: 🎓 Stanford CS231n „Deep Learning for Computer Vision" — [cs231n.stanford.edu] (https://cs231n.stanford.edu/) · Notes + ältere Vorlesungsvideos frei. Die Backprop-Notes (computational graphs, Gradienten von Hand) sind das beste Klausurtraining für den Kern des…
    m-ml:27:u1 [url] https://cs231n.stanford.edu/  «cs231n.stanford.edu»  -> title ~ source-cs231n-2017-videos (0.67), source-cs231n-notes (0.67)
L28: 🛠🎓 Andrej Karpathy, „Neural Networks: Zero to Hero" — [karpathy.ai/zero-to-hero.html] (https://karpathy.ai/zero-to-hero.html) (YouTube-Serie). Baut Backprop (micrograd) und Sprachmodelle from scratch — nichts verankert das Verständnis von Autodiff tiefer. Eins…
    m-ml:28:u1 [url] https://karpathy.ai/zero-to-hero.html  «karpathy.ai/zero-to-hero.html»
L32: 🛠 UvA Deep Learning Notebooks — [uvadlc-notebooks.readthedocs.io] (https://uvadlc-notebooks.readthedocs.io/) (Universiteit van Amsterdam, frei). Saubere PyTorch-(Lightning-)Implementierungen aller DL1-Architekturen inkl. Autoencoder und RNNs. Einsatz: Referenz…
    m-ml:32:u1 [url] https://uvadlc-notebooks.readthedocs.io/  «uvadlc-notebooks.readthedocs.io»
L38: 📚 Prince, „Understanding Deep Learning" (s. o.) — die zweite Buchhälfte ist exakt DL2: Transformers, GANs, Normalizing Flows, Diffusion, Graph-Netze. Einsatz: Hauptbuch auch hier — ein Buch trägt beide Module.
    m-ml:38:e1 [entry] Prince, „Understanding Deep Learning"  -> title ~ source-prince-udl (1.00), source-cmu-10414 (0.50), source-d2l (0.50)
L39: 🎓 Stanford CS236 „Deep Generative Models" — [deepgenerativemodels.github.io] (https://deepgenerativemodels.github.io/) (Notes + Folien frei). Die sauberste Behandlung von autoregressiven Modellen, Flows, GANs, VAEs als ein zusammenhängendes Likelihood-Gerüst —…
    m-ml:39:u1 [url] https://deepgenerativemodels.github.io/  «deepgenerativemodels.github.io»
L40: 🎓 Stanford CS25 „Transformers United" — [web.stanford.edu/class/cs25] (https://web.stanford.edu/class/cs25/) (Videos öffentlich). Self-Attention von Grundlagen bis aktuelle Varianten. Einsatz: für den Attention-Block; ergänzend Karpathys „Let's build GPT" aus…
    m-ml:40:u1 [url] https://web.stanford.edu/class/cs25/  «web.stanford.edu/class/cs25»
L41: 📄 Lilian Weng, lil'log — [lilianweng.github.io] (https://lilianweng.github.io/). Die besten Übersichtsartikel zu Normalizing Flows, Self-Supervised Learning, Diffusion, Quantisierung — jeweils mit vollständiger Mathematik. Einsatz: pro Vorlesungsthema der pass…
    m-ml:41:u1 [url] https://lilianweng.github.io/  «lilianweng.github.io»
L42: 📄 Schlüssel-Papers (klausur- und thesis-zitierfähig): „Attention Is All You Need" (2017) · Chen et al., „Neural Ordinary Differential Equations" (NeurIPS 2018) · Bai et al., „Deep Equilibrium Models" (NeurIPS 2019) · Rezende/Mohamed, „Variational Inference wi…
    m-ml:42:e1 [entry] Schlüssel-Papers (klausur- und thesis-zitierfähig)
L50: 📚 James/Witten/Hastie/Tibshirani/Taylor, „An Introduction to Statistical Learning with Python (ISLP)" — [statlearning.com] (https://www.statlearning.com/) (frei, mit Python-Labs). Du kennst ISLP aus dem SoSe-26-Foundations-Plan — hier wird es zum Lab-Begleiter…
    m-ml:50:u1 [url] https://www.statlearning.com/  «statlearning.com»
L51: 📚 Raschka/Liu/Mirjalili, „Machine Learning with PyTorch and Scikit-Learn" — das beste Brückenbuch zwischen klassischem ML (sklearn) und DL (PyTorch) mit sauberem Evaluations-Handwerk. Einsatz: Nachschlagen für Implementierungsdetails, die sklearn-Doku zu knap…
    m-ml:51:e1 [entry] Raschka/Liu/Mirjalili, „Machine Learning with PyTorch and Scikit-Learn"  -> title ~ source-calmcode-sklearn (0.50), source-data-school-sklearn (0.50), source-google-ml-crash-course (0.50)
L52: 📚 Abhishek Thakur, „Approaching (Almost) Any Machine Learning Problem" — [frei auf GitHub] (https://github.com/abhishekkrthakur/approachingalmost). Pragmatischer Workflow: Validierungsstrategien, Feature Engineering, Hyperparameter-Suche — vom 4-fachen Kaggle-…
    m-ml:52:u1 [url] https://github.com/abhishekkrthakur/approachingalmost  «frei auf GitHub»
L53: 📄 Pedregosa et al., „Scikit-learn: Machine Learning in Python" (JMLR 2011) + Varma/Simon, „Bias in Error Estimation when Using Cross-Validation for Model Selection" — Letzteres ist der Klassiker zu nested CV, dem häufigsten Praktikums-Stolperstein (und einer…
    m-ml:53:e1 [entry] Pedregosa et al., „Scikit-learn: Machine Learning in Python" (JMLR 2011)  -> title ~ source-data-school-sklearn (0.62), source-calmcode-sklearn (0.50), source-google-ml-crash-course (0.50)
L59: 🎓 Caltech „Learning from Data" (Abu-Mostafa) — [work.caltech.edu/telecourse.html] (https://work.caltech.edu/telecourse.html) (18 Vorlesungen frei). Die Lehrveranstaltung zu Generalisierung: VC-Dimension, Bias-Variance, Regularisierung, Validation — exakt der E…
    m-ml:59:u1 [url] https://work.caltech.edu/telecourse.html  «work.caltech.edu/telecourse.html»
L60: 📚 Bishop, PRML (s. o.) — deckt mit Kapiteln 3–5 (Bayes lineare Modelle, NNs), 7 (SVM), 8 (PGM) fast das gesamte Modul ab. Einsatz: Hauptbuch; MI I ist das bishop-förmigste Modul im ganzen Katalog.
    m-ml:60:e1 [entry] Bishop, PRML  -> title ~ source-bishop-prml (1.00)
L63: 📚 Hertz/Krogh/Palmer, „Introduction to the Theory of Neural Computation" — der Klassiker der konnektionistischen Schule (RBF-Netze, rekurrente Netze aus physikalischer Sicht), aus der Obermayers Gruppe stammt. Einsatz: optional für die NN-Kapitel, deren Stil…
    m-ml:63:e1 [entry] Hertz/Krogh/Palmer, „Introduction to the Theory of Neural Computation"
L69: 📚 Bishop, PRML — Kapitel 9 (Mixture Models & EM), 12 (PCA, Kernel-PCA, probabilistische PCA), 13 (HMMs, sequenzielle Modelle) sind eine fast vollständige Abdeckung des Moduls in einem Buch. Einsatz: Hauptbuch; die EM-Herleitung in Kap. 9 ist die, die in Klaus…
    m-ml:69:e1 [entry] Bishop, PRML  -> title ~ source-bishop-prml (1.00)
L70: 📄 Hyvärinen/Oja, „Independent Component Analysis: Algorithms and Applications" (Neural Networks 2000) — [frei verfügbar] (https://www.cs.helsinki.fi/u/ahyvarin/papers/NN00new.pdf). Das Standard-Tutorial zu ICA/FastICA von den Erfindern — der ICA-Block ist das…
    m-ml:70:u1 [url] https://www.cs.helsinki.fi/u/ahyvarin/papers/NN00new.pdf  «frei verfügbar»
L71: 📚 Murphy, „Probabilistic Machine Learning" (Book 1 + 2) — [probml.github.io/pml-book] (https://probml.github.io/pml-book/) (beide Bände frei). Moderne, einheitlich-probabilistische Behandlung von Schätztheorie, Mischmodellen, Embeddings; Book 2 vertieft, wo Bi…
    m-ml:71:u1 [url] https://probml.github.io/pml-book/  «probml.github.io/pml-book»
L72: 📚 ESL (s. o.), Kapitel 14 (Unsupervised: Clustering, SOM, PCA-Varianten, spektrale Methoden) — die statistische Gegenperspektive inkl. Praxis-Caveats. Einsatz: Wiederholung vor der Klausur.
    m-ml:72:e1 [entry] ESL
L73: 🎓 MIT DCAI / Müller-Schule-Querbezug: Kernel-PCA stammt aus der TU-Berlin/MPI-Linie (Schölkopf/Smola/Müller, „Nonlinear Component Analysis as a Kernel Eigenvalue Problem", 1998). Einsatz: das Originalpaper lesen — verbindet MI II direkt mit dem ML-2-X-Kernels…
    m-ml:73:e1 [entry] MIT DCAI / Müller-Schule-Querbezug
L79: 🎓📚 Kolter/Madry, „Adversarial Robustness — Theory and Practice" — [adversarial-ml-tutorial.org] (https://adversarial-ml-tutorial.org/) (freies Tutorial-Buch mit Code, aus dem NeurIPS-Tutorial). Baut Angriffe (FGSM, PGD) und Verteidigungen (Adversarial Training…
    m-ml:79:u1 [url] https://adversarial-ml-tutorial.org/  «adversarial-ml-tutorial.org»
L80: 📄 Biggio/Roli, „Wild Patterns: Ten Years After the Rise of Adversarial Machine Learning" (Pattern Recognition 2018) — der Übersichtsartikel des Felds, aus der europäischen Security-Schule, mit der Rieck kollaboriert; systematisiert Threat Models und Poisoning…
    m-ml:80:e1 [entry] Biggio/Roli, „Wild Patterns: Ten Years After the Rise of Adversarial Machine Learning" (Pattern Recognition 2018)  -> title ~ source-bishop-prml (0.57), source-google-ml-crash-course (0.50), source-ng-coursera (0.50)
L81: 📄 Schlüssel-Papers entlang der Modulgliederung: Szegedy et al., „Intriguing Properties of Neural Networks" (2014) + Goodfellow et al., „Explaining and Harnessing Adversarial Examples" (2015) — Geburt des Felds · Madry et al., „Towards Deep Learning Models Res…
    m-ml:81:e1 [entry] Schlüssel-Papers entlang der Modulgliederung
L82: 📄 Nicholas Carlini — [nicholas.carlini.com] (https://nicholas.carlini.com/) (u. a. „A Complete List of All Adversarial Example Papers" und kritische Evaluations-Essays wie „On Evaluating Adversarial Robustness"). Einsatz: die Evaluations-Checkliste daraus ist…
    m-ml:82:u1 [url] https://nicholas.carlini.com/  «nicholas.carlini.com»
L83: 🛠 RobustBench ([robustbench.github.io] (https://robustbench.github.io/)) + Adversarial Robustness Toolbox (ART) ([github.com/Trusted-AI/adversarial-robustness-toolbox] (https://github.com/Trusted-AI/adversarial-robustness-toolbox)) — standardisierte Benchmarks…
    m-ml:83:u1 [url] https://robustbench.github.io/  «robustbench.github.io»
    m-ml:83:u2 [url] https://github.com/Trusted-AI/adversarial-robustness-toolbox  «github.com/Trusted-AI/adversarial-robustness-toolbox»
L92: 📚 Bishop, PRML (s. o.) — Kapitel 1–4 (Wahrscheinlichkeit, Verteilungen, lineare Regression/Klassifikation inkl. LDA, Ridge), 6.4 (Gaußprozesse), 9 (EM), 12 (PCA). Praktisch eine 1:1-Abdeckung des Modulprofils in einem Buch. Einsatz: gezielte Kapitel je Lücke.
    m-ml:92:e1 [entry] Bishop, PRML  -> title ~ source-bishop-prml (1.00)
L93: 📚 Rasmussen/Williams, „Gaussian Processes for Machine Learning" — [frei als PDF, gaussianprocess.org/gpml] (https://gaussianprocess.org/gpml/). Gaußprozesse sind das ML-1-Thema, das Standard-Einführungen am häufigsten auslassen — hier das Referenzwerk der Erfi…
    m-ml:93:u1 [url] https://gaussianprocess.org/gpml/  «frei als PDF, gaussianprocess.org/gpml»
L94: 📚 ISLP (s. ML Lab) — du arbeitest es im SoSe 26 ohnehin durch; Kapitel 4 (LDA!), 5 (CV), 6 (Ridge/Lasso), 12 (PCA/Clustering) sind exakt ML-1-X-Stoff. Einsatz: deine laufende Foundations-Arbeit ist bereits ML-1-X-Vorbereitung — kein Doppelaufwand nötig.
    m-ml:94:e1 [entry] ISLP
L95: 📚 Deisenroth, „Mathematics for ML" (s. ML 2-X) — die Schätztheorie-/Linear-Algebra-Brücke, falls MLE/EM-Herleitungen haken. Einsatz: Sommer-Auffrischung.
    m-ml:95:e1 [entry] Deisenroth, „Mathematics for ML"  -> title ~ source-mml (1.00)
L101: 🎓 Böhms eigene AMLS-Kursseiten — alle Folien öffentlich, alle Jahrgänge — [SS25] (https://mboehm7.github.io/teaching/ss25_amls/index.htm) · [SS23] (https://mboehm7.github.io/teaching/ss23_amls/index.htm) · [Archiv ab SS19 auf mboehm7.github.io] (https://mboehm7.…
    m-ml:101:u1 [url] https://mboehm7.github.io/teaching/ss25_amls/index.htm  «SS25»  -> same line as ['source-amls-prior-archives']
    m-ml:101:u3 [url] https://mboehm7.github.io/  «Archiv ab SS19 auf mboehm7.github.io»  -> same line as ['source-amls-prior-archives']
L102: 📚 Boehm/Kumar/Yang, „Data Management in Machine Learning Systems" (Morgan & Claypool Synthesis Lectures) — das Buch des Dozenten zum Modul: deklarative ML-Systeme, Rewrites/Optimierung, daten-parallele Ausführung, Lifecycle. Einsatz: die ausformulierte Prosa-…
    m-ml:102:e1 [entry] Boehm/Kumar/Yang, „Data Management in Machine Learning Systems" (Morgan & Claypool Synthesis Lectures)  -> title ~ source-dmmls-boehm (0.73), source-google-ml-crash-course (0.50), source-huyen-dmls (0.50)
L103: 📄 Papers entlang des Vorlesungskalenders: „SystemDS: A Declarative ML System for the End-to-End Data Science Lifecycle" (CIDR 2020, Böhm) · „SystemML: Declarative Machine Learning on Spark" (VLDB 2016) + „Compressed Linear Algebra for Large-Scale ML" (VLDB 20…
    m-ml:103:e1 [entry] Papers entlang des Vorlesungskalenders
L104: 🎓 CMU 10-714 (s. MLMMI) — die Lectures zu Operator Fusion, Compilation und GPU-Execution sind die Hands-on-Ergänzung zu AMLS Teil A. Einsatz: wo AMLS konzeptionell bleibt, zeigt 10-714 den Code; gleiche Investition zahlt später auf MLMMI ein.
    m-ml:104:e1 [entry] CMU 10-714  -> title ~ source-cmu-10414 (1.00)
L105: 📄 Stratum-Querbezug (dein Jobvorteil): AMLS Lecture 03 (Size Inference, Rewrites, Operator Selection) beschreibt genau die Klasse von Optimierungen, die du bei DEEM an DAG-Rewrites baust — SystemMLs Rewrite-Katalog ist die akademische Blaupause dafür. Einsatz…
    m-ml:105:e1 [entry] Stratum-Querbezug (dein Jobvorteil)
L114: 🎓 Stanford CS224N „NLP with Deep Learning" (Manning) — [web.stanford.edu/class/cs224n] (https://web.stanford.edu/class/cs224n/) + YouTube. Der Standard-Graduate-Kurs: Word-Vektoren → Transformer → LLMs. Einsatz: semesterbegleitend; Assignments als Portfolio-Üb…
    m-ml:114:u1 [url] https://web.stanford.edu/class/cs224n/  «web.stanford.edu/class/cs224n»
L115: 🎓 CMU CS11-711 „Advanced NLP" (Neubig) — [phontron.com/class/anlp] (https://phontron.com/class/anlp2024/) + YouTube. LLM-Ära: Pretraining, Fine-Tuning, Prompting, RAG, RLHF — exakt das #41270-Profil. Einsatz: Hauptspur für Advanced NLP.
    m-ml:115:u1 [url] https://phontron.com/class/anlp2024/  «phontron.com/class/anlp»
L116: 🛠 Hugging Face „LLM/NLP Course" — [huggingface.co/learn] (https://huggingface.co/learn). Transformer, Fine-Tuning, RAG mit lauffähigem Code. Einsatz: die praktische Projektarbeit (#41047/#41269-Portfolio) — schnellster Weg zu einer sauberen Pipeline.
    m-ml:116:u1 [url] https://huggingface.co/learn  «huggingface.co/learn»
L117: 📄 Schlüssel-Papers entlang der Modulgliederung: Vaswani et al., „Attention Is All You Need" (2017) · Devlin et al., „BERT" (2019) · Brown et al., „Language Models are Few-Shot Learners" (GPT-3, 2020) · Ouyang et al., „InstructGPT/RLHF" (2022) · Lewis et al.,…
    m-ml:117:e1 [entry] Schlüssel-Papers entlang der Modulgliederung
L118: 🛠 spaCy + NLTK — produktionsnahe NLP-Pipelines (Tokenisierung, NER, Vektorisierung). Einsatz: für die angewandte Variante #41269.
    m-ml:118:e1 [entry] spaCy + NLTK
L119: Cross: Attention/Transformer überlappt direkt mit DL2 §3 (CS25, Karpathys „Let's build GPT") — einmal lernen, in NLP und DL2 ernten.
    m-ml:119:e1 [entry] Cross
L125: 📚 Samek/Montavon/Vedaldi/Hansen/Müller (Hrsg.), „Explainable AI: Interpreting, Explaining and Visualizing Deep Learning" (Springer LNCS 11700, 2019) — vom Dozenten herausgegeben, praktisch das Modul als Buch (Methoden, Bewertung, Anwendungen, Software). Einsa…
    m-ml:125:e1 [entry] Samek/Montavon/Vedaldi/Hansen/Müller (Hrsg.), „Explainable AI: Interpreting, Explaining and Visualizing Deep Learning"  -> title ~ source-mit-6s191 (0.50)
L126: 📚 Holzinger/.../Samek/Müller (Hrsg.), „xxAI – Beyond Explainable AI" (Springer 2022, Open Access) — [link.springer.com/book/10.1007/978-3-031-04083-2] (https://link.springer.com/book/10.1007/978-3-031-04083-2). Einsatz: die aktuelle, frei verfügbare Erweiterun…
    m-ml:126:u1 [url] https://link.springer.com/book/10.1007/978-3-031-04083-2  «link.springer.com/book/10.1007/978-3-031-04083-2»
L127: 📄 LRP-Kanon: Bach et al., „On Pixel-Wise Explanations… by Layer-Wise Relevance Propagation" (PLoS ONE 2015, das LRP-Originalpaper) + Montavon/Binder/Lapuschkin/Samek/Müller, „Layer-Wise Relevance Propagation: An Overview" (2019). Einsatz: Pflicht — LRP ist Sa…
    m-ml:127:e1 [entry] LRP-Kanon
L128: 📄 Achtibat et al. (Samek-Gruppe), „From Attribution Maps to Human-Understandable Explanations through Concept Relevance Propagation (CRP)" (Nature Machine Intelligence 2023) — die aktuelle Linie der Gruppe. Einsatz: zeigt die Forschungsfront; gut für Portfoli…
    m-ml:128:e1 [entry] Achtibat et al. (Samek-Gruppe), „From Attribution Maps to Human-Understandable Explanations through Concept Relevance P…
L129: 📚 Christoph Molnar, „Interpretable Machine Learning" — [christophm.github.io/interpretable-ml-book] (https://christophm.github.io/interpretable-ml-book/) (frei). Die Methodenlandkarte (LIME, SHAP, PDP, Permutation Importance) als Komplement zu LRP. Einsatz: Üb…
    m-ml:129:u1 [url] https://christophm.github.io/interpretable-ml-book/  «christophm.github.io/interpretable-ml-book»
L130: 📚 Barocas/Hardt/Narayanan, „Fairness and Machine Learning" — [fairmlbook.org] (https://fairmlbook.org/) (frei). Der Fairness-/Verantwortungs-Teil jenseits der Erklärbarkeit. Einsatz: für die „responsible"-Themen (Bias, Fairness-Metriken) — überlappt mit FAccT/…
    m-ml:130:u1 [url] https://fairmlbook.org/  «fairmlbook.org»
L131: 🛠 Captum ([captum.ai] (https://captum.ai/), PyTorch) + Zennit ([github.com/chr5tphr/zennit] (https://github.com/chr5tphr/zennit), LRP/CRP). Einsatz: Portfolio — LRP/IG/SHAP auf ein eigenes Modell anwenden und vergleichen.
    m-ml:131:u1 [url] https://captum.ai/  «captum.ai»
    m-ml:131:u2 [url] https://github.com/chr5tphr/zennit  «github.com/chr5tphr/zennit»
L132: Cross: FAccT in ML #40994 + Responsible-DE-Project (Schelter) = dieselbe Linie; XAI/Robustheit sind direkt thesis-relevant für DEEM-Daten-Pipelines.
    m-ml:132:e1 [entry] Cross
L138: 📄 Raissi/Perdikaris/Karniadakis, „Physics-Informed Neural Networks" (J. Computational Physics 2019) — das Gründungspaper; PINNs für Vorwärts- und Inverse-PDE-Probleme (PDE-Residuum als Loss-Term). Einsatz: Pflicht — das ganze Modul baut hierauf auf.
    m-ml:138:e1 [entry] Raissi/Perdikaris/Karniadakis, „Physics-Informed Neural Networks" (J. Computational Physics 2019)
L139: 📄 Karniadakis et al., „Physics-informed machine learning" (Nature Reviews Physics 2021) — die kanonische Übersicht des Felds. Einsatz: als Landkarte vor Semesterstart lesen.
    m-ml:139:e1 [entry] Karniadakis et al., „Physics-informed machine learning" (Nature Reviews Physics 2021)  -> title ~ source-google-ml-crash-course (0.50), source-ng-coursera (0.50)
L140: 🎓📚 Steve Brunton, „Physics-Informed Machine Learning" (YouTube-Serie) + Brunton/Kutz, „Data-Driven Science and Engineering" ([databookuw.com] (https://databookuw.com/), 1. Aufl. frei) — die didaktisch beste Einführung in PIML/SINDy/Operator-Learning. Einsatz:…
    m-ml:140:u1 [url] https://databookuw.com/  «databookuw.com»
L141: 🛠 DeepXDE ([deepxde.readthedocs.io] (https://deepxde.readthedocs.io/), Lu Lu) + maziarraissi/PINNs ([github.com/maziarraissi/PINNs] (https://github.com/maziarraissi/PINNs)) — Referenz-Implementierungen. Einsatz: Portfolio — eine PDE (z. B. Burgers/Wärmeleitung)…
    m-ml:141:u1 [url] https://deepxde.readthedocs.io/  «deepxde.readthedocs.io»
    m-ml:141:u2 [url] https://github.com/maziarraissi/PINNs  «github.com/maziarraissi/PINNs»
L142: Cross: Die Kernel-Seite knüpft an den ML-2-X-Kernelstoff (§1) an; die Optimierungs-/PDE-Mathematik an Optimization Algorithms (Toussaint, 🧮).
    m-ml:142:e1 [entry] Cross
L148: 📄 Müllers eigene „ML in the Sciences"-Linie: Schütt et al., „SchNet — A continuous-filter CNN for modeling quantum interactions" (NeurIPS 2017 / JCP 2018) — das Vorzeige-Beispiel der Müller-Gruppe. Einsatz: als roter Faden, weil Müller-Anwendungen erfahrungsg…
    m-ml:148:e1 [entry] Müllers eigene „ML in the Sciences"-Linie
L149: 📄 Übersichten: „Machine learning for molecular and materials science" (Nature 2018) + von Lilienfeld/Müller/Tkatchenko, Reviews zu Quantum Machine Learning. Einsatz: Hintergrund vor den Gastvorträgen.
    m-ml:149:e1 [entry] Übersichten
L150: 🌐 TU Berlin Machine Learning Group — Publications — [web.ml.tu-berlin.de/publication] (https://web.ml.tu-berlin.de/publication/). Einsatz: vor der mündlichen Prüfung 2–3 aktuelle Anwendungs-Papers der Gruppe kennen — die mündliche Prüfung honoriert konkrete Be…
    m-ml:150:u1 [url] https://web.ml.tu-berlin.de/publication/  «web.ml.tu-berlin.de/publication»
L151: Hinweis: Vortragsformat → keine Buchgrundlage; pro Thema die Gast-Slides + ein Anwendungspaper. 3 LP/mündlich = geringer Aufwand, idealer Klein-Slot neben einem großen Klausurmodul.
    m-ml:151:e1 [entry] Hinweis
L157: 🌐 BIFOLD Research Workgroups — [bifold.berlin/research/workgroups] (https://bifold.berlin/research/workgroups). Die offizielle Themenquelle; deine DEEM/Schelter- und Böhm-Gruppen sind hier gelistet. Einsatz: Projekt direkt an Stratum/Thesis ausrichten.
    m-ml:157:u1 [url] https://bifold.berlin/research/workgroups  «bifold.berlin/research/workgroups»
L158: 📄 Forschungs- & Reproduzierbarkeits-Handwerk: Joelle Pineau, „ML Reproducibility Checklist" + Papers with Code ([paperswithcode.com] (https://paperswithcode.com/)). Einsatz: saubere Projektdurchführung und Eval.
    m-ml:158:u1 [url] https://paperswithcode.com/  «paperswithcode.com»
L159: Cross: Dein methodischer Kanon (Jain/McGeoch/Hoefler/COST) aus den 📊-Ressourcen = der Evaluations-Werkzeugkasten; Research Seminar DEEM #41279 + Responsible-DE-Project #41242 sind die thematischen Nachbarn. Hinweis: 6 LP je, stapelbar (I→II→III) — füllt Wahlb…
    m-ml:159:e1 [entry] Cross
L165: 📚 Luciano Ramalho, „Fluent Python" (2. Aufl.) — deckt exakt die „advanced functional/OO patterns, Dunder, Decorators" aus dem Profil. Einsatz: gezielt die Kapitel zu Dunder-Methoden/Decorators/Iteratoren — der Rest sitzt bei dir schon.
    m-ml:165:e1 [entry] Luciano Ramalho, „Fluent Python" (2. Aufl.)  -> title ~ source-fluent-python (0.80)
L166: 📚 Jake VanderPlas, „Python Data Science Handbook" — [jakevdp.github.io/PythonDataScienceHandbook] (https://jakevdp.github.io/PythonDataScienceHandbook/) (frei). NumPy/Pandas/Matplotlib als Nachschlagewerk. Einsatz: punktuell.
    m-ml:166:u1 [url] https://jakevdp.github.io/PythonDataScienceHandbook/  «jakevdp.github.io/PythonDataScienceHandbook»
L167: 🛠 NumPy- + PyTorch-Tutorials (offiziell) — die „Beschleunigungs-Frameworks" aus dem Profil. Einsatz: für die ML-Implementierungsaufgaben der Klausur/Übung.
    m-ml:167:e1 [entry] NumPy- + PyTorch-Tutorials (offiziell)  -> title ~ source-pytorch-tutorials (0.67), source-captum (0.50)
L168: Hinweis: grade-safe; nur belegen, wenn ein 6-LP-Slot oder ein Notenpolster (§8-Streichregel) gebraucht wird.
    m-ml:168:e1 [entry] Hinweis
L174: 1. Ein Buch, vier Module: Bishop PRML trägt ML 2-X (PGM/SVM), MI I (Lerntheorie/NN) und MI II (EM/PCA/HMM); Prince UDL trägt DL1 und DL2. Erst kaufen/laden, dann modulweise ernten.
    m-ml:174:e1 [entry] Ein Buch, vier Module
L175: 2. Müller-Schule als roter Faden: Kernel-Tutorial (2001) → Kernel-PCA-Paper (1998) → ML 2-X → MI II — dieselbe Denkschule, dieselbe Notation, dieselben Prüfungs-Idiome. Wer die zwei Papers kennt, liest die TU-Folien wie Muttersprache.
    m-ml:175:e1 [entry] Müller-Schule als roter Faden
L176: 3. DL2-Deployment-Teil (Distillation/Quantisierung) = MLMMI/10-714-Vorstoff — die 🚀-Brücke; einmal lernen, in beiden Klausur-/Portfolio-Kontexten verwenden.
    m-ml:176:e1 [entry] DL2-Deployment-Teil (Distillation/Quantisierung) = MLMMI/10-714-Vorstoff
L177: 4. Adversarial ML × Benchmarking: Carlinis Evaluations-Essays + Riecks „Dos and Don'ts" sind methodisch dasselbe Anliegen wie CSB/ROC — reproduzierbare, ehrliche Evaluation. Direkt auf die Thesis-Evaluation übertragbar.
    m-ml:177:e1 [entry] Adversarial ML × Benchmarking
L178: 5. Klausur-Cluster beachten: ML 2-X, DL1/2, MI I/II sind alle schriftlich — nie mehr als zwei davon in dasselbe Semester legen (Regel §4.3 im MODULE-MENU bleibt bindend).
    m-ml:178:e1 [entry] Klausur-Cluster beachten
L193: 📝 MIT 6.036 (Open Learning Library, aus deinem Ultimate-Index-Umfeld) — Intro-ML mit auto-gegradeten Übungen; als Lücken-Diagnose vor ML 2-X.
    m-ml:193:e1 [entry] MIT 6.036 (Open Learning Library, aus deinem Ultimate-Index-Umfeld)  -> title ~ source-mit-6036 (0.67)
L194: 🎓 Tübingen „Probabilistic Machine Learning" (Hennig) — komplette Vorlesung + Übungen auf YouTube/GitHub; die deutsche graduate-Perspektive auf den probabilistischen Stoff von MI II.
    m-ml:194:e1 [entry] Tübingen „Probabilistic Machine Learning" (Hennig)  -> title ~ source-murphy-pml1 (0.60), source-google-ml-crash-course (0.50), source-ng-coursera (0.50)
L198: 🛠 karpathy/micrograd + nanoGPT — [github.com/karpathy/micrograd] (https://github.com/karpathy/micrograd) · [nanoGPT] (https://github.com/karpathy/nanoGPT): Autodiff in 100 Zeilen bzw. GPT in lesbarem PyTorch — die Code-Seite von DL1/DL2 (Zero-to-Hero-Begleitrep…
    m-ml:198:u1 [url] https://github.com/karpathy/micrograd  «github.com/karpathy/micrograd»  -> title ~ source-karpathy-micrograd (0.50)
    m-ml:198:u2 [url] https://github.com/karpathy/nanoGPT  «nanoGPT»
L199: 🛠 tinygrad — [github.com/tinygrad/tinygrad] (https://github.com/tinygrad/tinygrad): vollständiges DL-Framework, klein genug zum Komplett-Lesen — Operator-Graphen, Lazy Evaluation, Kernel-Fusion: die Brücke DL ↔ AMLS/MLMMI in einem Repo.
    m-ml:199:u1 [url] https://github.com/tinygrad/tinygrad  «github.com/tinygrad/tinygrad»
L200: 🛠 NYU Deep Learning (LeCun/Canziani) — [github.com/Atcold/NYU-DLSP21] (https://github.com/Atcold/NYU-DLSP21): komplette Vorlesung + Notebooks (auch zu Energy-Based Models, die DL2-exotisch sind).
    m-ml:200:u1 [url] https://github.com/Atcold/NYU-DLSP21  «github.com/Atcold/NYU-DLSP21»
L201: 🛠 fast.ai ([course.fast.ai] (https://course.fast.ai/), aus deinem Ultimate-Index) + Kaggle Learn — Praxis-Spur fürs ML Lab: schnelle, saubere Baselines bauen; danach sklearn/ISLP für die Methodik-Tiefe.
    m-ml:201:u1 [url] https://course.fast.ai/  «course.fast.ai»
L202: 🛠 Adversarial-ML-Praxis: [Trusted-AI/adversarial-robustness-toolbox] (https://github.com/Trusted-AI/adversarial-robustness-toolbox) (bereits §7) + [cleverhans] (https://github.com/cleverhans-lab/cleverhans) Tutorials + [MadryLab robustness] (https://github.com/M…
    m-ml:202:u1 [url] https://github.com/Trusted-AI/adversarial-robustness-toolbox  «Trusted-AI/adversarial-robustness-toolbox»
    m-ml:202:u2 [url] https://github.com/cleverhans-lab/cleverhans  «cleverhans»
    m-ml:202:u3 [url] https://github.com/MadryLab/robustness  «MadryLab robustness»
L203: 🛠 MLMMI/Serving-Lese-Repos: [vllm-project/vllm] (https://github.com/vllm-project/vllm) (PagedAttention — Inference-Runtime-Engineering vom Feinsten), [ggml-org/llama.cpp] (https://github.com/ggml-org/llama.cpp) (Quantisierung praktisch), [mlflow/mlflow] (https:/…
    m-ml:203:u1 [url] https://github.com/vllm-project/vllm  «vllm-project/vllm»
    m-ml:203:u2 [url] https://github.com/ggml-org/llama.cpp  «ggml-org/llama.cpp»
    m-ml:203:u3 [url] https://github.com/mlflow/mlflow  «mlflow/mlflow»

## m-runtime — repository/curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning/inputs/MASTERS-RUNTIME-RESOURCES.md

L13: 📚 Pierce, „Types and Programming Languages" (TAPL) — das Modul trägt den Buchtitel. Operationale Semantik, STLC, System F, ADTs, Subtyping — die mündliche Prüfung wird in TAPL-Notation geführt werden. Einsatz: Hauptbuch; Kapitel 3–11 + 23 (System F) gründlich…
    m-runtime:13:e1 [entry] Pierce, „Types and Programming Languages" (TAPL)  -> title ~ source-pierce-tapl (1.00)
L15: 📚🛠 Wadler/Kokke/Siek, „Programming Language Foundations in Agda" (PLFA) — [frei, plfa.github.io] (https://plfa.github.io/). Dieselbe Theorie in Agda — moderner, schlanker als Coq; und Agda ist die im Schwestermodul (§4) explizit genannte Sprache. Einsatz: Alte…
    m-runtime:15:u1 [url] https://plfa.github.io/  «frei, plfa.github.io»
L16: 📄 Wadler, „Propositions as Types" (CACM 2015) — [frei (Autoren-Seite)] (https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf) + sein berühmter Vortrag dazu (YouTube). Curry-Howard als Erzählung — die schönste Vorbereitun…
    m-runtime:16:u1 [url] https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf  «frei (Autoren-Seite)»
L17: 🎓 OPLSS — Oregon Programming Languages Summer School — [Videoarchiv frei] (https://www.cs.uoregon.edu/research/summerschool/archives.html). Jahrzehnte an Vorlesungsreihen zu Typtheorie, Curry-Howard, dependent types von den Größen des Felds (Pierce, Harper, Wa…
    m-runtime:17:u1 [url] https://www.cs.uoregon.edu/research/summerschool/archives.html  «Videoarchiv frei»
L18: 📄 Steuwers eigene Forschung als Kontext: „RISE & Shine" / „Achieving High-Performance the Functional Way" (ELEVATE, ICFP 2020) — funktionale IRs + Rewrite-Strategien für Performance-Compiler ([Publikationsliste] (https://steuwer.info/)). Das ist konzeptionell…
    m-runtime:18:u1 [url] https://steuwer.info/  «Publikationsliste»
L24: 📚 Appel, „Modern Compiler Implementation in ML" (bzw. Java/C) — die Modulgliederung folgt diesem Buch fast wörtlich („colouring by simplification", „coalescing" sind Appels Kapitelvokabular — er hat Compiling Techniques in Edinburgh geprägt, wo Steuwer den Ku…
    m-runtime:24:e1 [entry] Appel, „Modern Compiler Implementation in ML" (bzw. Java/C)
L26: 🛠 LLVM „Kaleidoscope"-Tutorial + MLIR „Toy"-Tutorial — [llvm.org/docs/tutorial] (https://llvm.org/docs/tutorial/) · [mlir.llvm.org/docs/Tutorials/Toy] (https://mlir.llvm.org/docs/Tutorials/Toy/). Einen Mini-Compiler auf realer Infrastruktur bauen; MLIR ist das…
    m-runtime:26:u1 [url] https://llvm.org/docs/tutorial/  «llvm.org/docs/tutorial»  -> title ~ source-python-docs-classes-mro (0.50)
    m-runtime:26:u2 [url] https://mlir.llvm.org/docs/Tutorials/Toy/  «mlir.llvm.org/docs/Tutorials/Toy»
L27: 📚 Cooper/Torczon, „Engineering a Compiler" (3. Aufl.) — die modernere Alternative zum Drachenbuch: stark bei SSA, Instruction Selection, Registerallokation. Einsatz: Zweitreferenz, wenn Appel zu ML-lastig ist.
    m-runtime:27:e1 [entry] Cooper/Torczon, „Engineering a Compiler" (3. Aufl.)
L28: 📚 Nystrom, „Crafting Interpreters" — [komplett frei, craftinginterpreters.com] (https://craftinginterpreters.com/). Lexer→Parser→Bytecode-VM in zwei Durchgängen, herausragend geschrieben. Einsatz: Warm-up vor Semesterstart, falls du noch nie einen Parser gebau…
    m-runtime:28:u1 [url] https://craftinginterpreters.com/  «komplett frei, craftinginterpreters.com»
L29: 📄 Cytron et al., „Efficiently Computing Static Single Assignment Form…" (TOPLAS 1991) + Chaitin, „Register Allocation & Spilling via Graph Coloring" (1982) — die zwei Originale hinter den zwei schwersten Projektphasen. Einsatz: jeweils vor der Phase; Portfoli…
    m-runtime:29:e1 [entry] Cytron et al., „Efficiently Computing Static Single Assignment Form…" (TOPLAS 1991)
L35: 📚 Aho/Lam/Sethi/Ullman, „Compilers: Principles, Techniques, and Tools" (Drachenbuch, 2. Aufl.) — für diesen klassisch geschnittenen Kurs die passende Referenz; die Lam-Kapitel (11–12) zu Parallelisierung/Lokalität decken den besonderen Modulfokus. Einsatz: Re…
    m-runtime:35:e1 [entry] Aho/Lam/Sethi/Ullman, „Compilers: Principles, Techniques, and Tools" (Drachenbuch, 2. Aufl.)
L36: 📚 Allen/Kennedy, „Optimizing Compilers for Modern Architectures" — das Buch zu parallelisierenden Compilern (Dependence Analysis, Loop-Transformationen, Vektorisierung) — exakt das Alleinstellungsmerkmal dieses Moduls gegenüber §2. Einsatz: für den Parallelis…
    m-runtime:36:e1 [entry] Allen/Kennedy, „Optimizing Compilers for Modern Architectures"
L37: 📚 Muchnick, „Advanced Compiler Design and Implementation" — Tiefenreferenz für klassische Optimierungen (SSA-Optimierungen, Scheduling). Einsatz: Nachschlagen bei Portfolio-Optimierungsaufgaben.
    m-runtime:37:e1 [entry] Muchnick, „Advanced Compiler Design and Implementation"
L38: 🎓 Cornell CS 6120 (s. §2) — trägt auch hier; identischer Stoffkern. Einsatz: Video-Spur.
    m-runtime:38:e1 [entry] Cornell CS 6120  -> title ~ source-cornell-cs6120 (1.00)
L39: 📄 Lattner/Adve, „LLVM: A Compilation Framework…" (CGO 2004) + Lattner et al., „MLIR: Scaling Compiler Infrastructure for Domain Specific Computation" (CGO 2021) — die zwei Infrastruktur-Papers, die „recent advances" im Modulprofil konkret machen. Einsatz: für…
    m-runtime:39:e1 [entry] Lattner/Adve, „LLVM: A Compilation Framework…" (CGO 2004)
L45: 📄 Selinger, „Lecture Notes on the Lambda Calculus" — [frei auf arXiv] (https://arxiv.org/abs/0804.3434). ~100 Seiten druckreifes Skript: Konversion, Konfluenz (Church-Rosser), Typisierung — exakt der Vorlesungskern, kostenlos. Einsatz: Erstlektüre; die Church-…
    m-runtime:45:u1 [url] https://arxiv.org/abs/0804.3434  «frei auf arXiv»
L46: 📚 Pierce, TAPL (s. §1) — trägt auch dieses Modul (STLC, System F, Lambda-Würfel-Einordnung). Einsatz: gemeinsame Investition für §1/§4 — ein Buch, zwei Modulkandidaten.
    m-runtime:46:e1 [entry] Pierce, TAPL  -> title ~ source-pierce-tapl (1.00)
L47: 📚 Sørensen/Urzyczyn, „Lectures on the Curry-Howard Isomorphism" — die Tiefenreferenz zum Herzstück des Moduls (Logik ↔ Berechnung, bis zu abhängigen Typen und Lambda-Würfel). Einsatz: für den Curry-Howard-/Lambda-Kubus-Block; formaler als TAPL, passend zum Ne…
    m-runtime:47:e1 [entry] Sørensen/Urzyczyn, „Lectures on the Curry-Howard Isomorphism"
L48: 📄 Barendregt, „Lambda Calculi with Types" (Handbook-Kapitel) — frei auffindbares Standard-Survey; der Lambda-Würfel stammt von Barendregt selbst. Einsatz: Originalquelle für die Würfel-Prüfungsfrage.
    m-runtime:48:e1 [entry] Barendregt, „Lambda Calculi with Types" (Handbook-Kapitel)
L49: 🛠 Haskell + Agda praktisch: Hutton, „Programming in Haskell" (kompakt) bzw. [Learn You a Haskell (frei)] (https://learnyouahaskell.github.io/) · Agda über PLFA (s. §1). Das Modulprofil nennt beide Sprachen. Einsatz: kleine Beispiele selbst tippen (ADTs, Polymo…
    m-runtime:49:u1 [url] https://learnyouahaskell.github.io/  «Learn You a Haskell (frei)»
L55: 📚 Kirk/Hwu, „Programming Massively Parallel Processors (PMPP)" (4. Aufl.) — das Standardbuch für CUDA/GPU-Programmierung: Speicherhierarchie, Parallelitätsmuster, Performance-Tuning. Einsatz: Hauptbuch.
    m-runtime:55:e1 [entry] Kirk/Hwu, „Programming Massively Parallel Processors (PMPP)" (4. Aufl.)  -> title ~ source-kirk-hwu-pmpp (0.75)
L57: 📄 NVIDIA CUDA C++ Programming Guide + Best Practices Guide — die Primärreferenz. Einsatz: Nachschlagewerk fürs Portfolio-Projekt.
    m-runtime:57:e1 [entry] NVIDIA CUDA C++ Programming Guide + Best Practices Guide
L58: 🛠 Triton ([triton-lang.org] (https://triton-lang.org/)) — GPU-Kernel in Python; direkter Steuwer/MLIR-Bezug (ELEVATE/RISE-Linie → Kernel-Generierung). Einsatz: der Brückenschlag GPU ↔ Compiler (TPS/CT) ↔ Stratum.
    m-runtime:58:u1 [url] https://triton-lang.org/  «triton-lang.org»
L59: 📄 Horace He, „Making Deep Learning Go Brrrr From First Principles" — Memory- vs. Compute-bound, Operator-Fusion intuitiv. Einsatz: das „throughput vs. latency"-Mentalmodell des Moduls verankern.
    m-runtime:59:e1 [entry] Horace He, „Making Deep Learning Go Brrrr From First Principles"  -> title ~ source-mit-6s191 (0.50)
L60: Cross: überlappt mit DMH (Hardware-Performance), MLMMI (Inference-Runtime) und dem Frontier-Lab-Delta (GPU/Kernel-Pfad, unten) — einmal lernen, mehrfach nutzen.
    m-runtime:60:e1 [entry] Cross
L66: 📚 Nipkow/Klein, „Concrete Semantics with Isabelle/HOL" — [frei: concrete-semantics.org] (http://concrete-semantics.org/) — DAS Isabelle-Lehrbuch (vom Isabelle-Mitentwickler Nipkow); Teil I lehrt Isabelle/HOL genau auf Modulniveau, Teil II wendet es auf Program…
    m-runtime:66:u1 [url] http://concrete-semantics.org/  «frei: concrete-semantics.org»
L67: 🎓 Isabelle-Tutorials ([isabelle.in.tum.de] (https://isabelle.in.tum.de/) — „Prog-Prove" + „Tutorial on Isabelle/HOL") — Einsatz: Hands-on parallel; die mündliche Prüfung verlangt Beweise live.
    m-runtime:67:u1 [url] https://isabelle.in.tum.de/  «isabelle.in.tum.de»
L68: 📄 deep vs. shallow embeddings — Nipkows Embedding-Notizen / Standard-Survey. Einsatz: für den im Profil explizit genannten Embedding-Block.
    m-runtime:68:e1 [entry] deep vs. shallow embeddings
L69: 🛠 Alternativ-Beweiser zum Querlesen: „Software Foundations" (Coq) + „Theorem Proving in Lean 4" — dieselben Ideen in anderer Syntax. Einsatz: optional; Isabelle bleibt Pflicht (Nestmanns Werkzeug).
    m-runtime:69:e1 [entry] Alternativ-Beweiser zum Querlesen
L76: 1. Die Steuwer-Linie ist deine Thesis-Rampe: TPS (WiSe, Theorie) → Compiling Techniques (SoSe, Praxis) → ELEVATE/RISE-Papers → MLIR-Tutorial → Stratum-Rewrites. Kein anderer Modulpfad zahlt so direkt auf deine DEEM-Arbeit und das Thesis-Framing („rule-based o…
    m-runtime:76:e1 [entry] Die Steuwer-Linie ist deine Thesis-Rampe
L77: 2. TPS vs. Lambda-Kalkül entscheiden: ~70 % Stoffüberlappung, beide WiSe/mündlich. Default: TPS (Steuwer-Beziehung + Anwendungsfokus + Stratum-Fit). Lambda-Kalkül nur, wenn der Termin kollidiert oder du die Logik-Seite (Curry-Howard formal, Agda) bevorzugst —…
    m-runtime:77:e1 [entry] TPS vs. Lambda-Kalkül entscheiden
L78: 3. Compiler Design vs. Compiling Techniques: CD (WiSe, Juurlink, architektur-/parallelisierungslastig) ist die Ausweichoption, CT (SoSe, Steuwer, from-scratch-Projekt) die profilbildende Wahl. Wer beide nimmt, lernt einmal Phasen-Theorie und einmal Engineerin…
    m-runtime:78:e1 [entry] Compiler Design vs. Compiling Techniques
L79: 4. Cross-Tags einsammeln: DBTLAB (Query-Engine = Compiler für Anfragepläne), DMH (SIMD/Lokalität = das, was parallelisierende Compiler erzeugen), MLMMI/AMLS Lecture 03–04 (Rewrites, Operator Fusion = Compiler-Optimierung über ML-DAGs) — die 🚀-Achse ist der th…
    m-runtime:79:e1 [entry] Cross-Tags einsammeln
L80: 5. Werkzeug-Investition: Coq oder Agda (eines reicht), dazu einmal MLIR-Toy — zusammen ~3 Wochenenden, Ertrag in 4+ Modulen und der Thesis.
    m-runtime:80:e1 [entry] Werkzeug-Investition
L82: > Pflege: Steuwers TU-Kursseiten ([Fachgebiet COMPL] (https://www.tu.berlin/en/compl)) bei Modulstart auf veröffentlichte Materialien prüfen (sein Edinburgh-Vorgängerkurs hatte öffentliche Traditionen); LLVM/MLIR-Tutorial-URLs sind stabil.
    m-runtime:82:u1 [url] https://www.tu.berlin/en/compl  «Fachgebiet COMPL»
L90: 📝 Software Foundations = maschinengeprüfte Übungsblätter — (s. §1) jedes Kapitel besteht aus Coq-Übungen mit automatischer Korrektur — für TPS/Lambda gibt es kein besseres „Übungsblatt mit Lösung", weil der Beweisassistent die Lösung verifiziert.
    m-runtime:90:e1 [entry] Software Foundations = maschinengeprüfte Übungsblätter  -> title ~ source-software-foundations (0.50)
L91: 📝 Stanford CS143: Assignments (Cool-Compiler) — [web.stanford.edu/class/cs143] (https://web.stanford.edu/class/cs143/): vier Programmierprojekte (Lexer→Parser→Semant→Codegen) mit Skeleton + Tests, dazu Midterm/Final-Archive mit Lösungen auf den Jahrgangsseiten…
    m-runtime:91:u1 [url] https://web.stanford.edu/class/cs143/  «web.stanford.edu/class/cs143»
L92: 📝 MIT OCW 6.035 „Computer Language Engineering" — komplette Projektspezifikationen (Decaf-Compiler) + Quizzes — die amerikanische Vollversion des CT-Kursprojekts.
    m-runtime:92:e1 [entry] MIT OCW 6.035 „Computer Language Engineering"
L93: 📝 Cornell CS 6120: Tasks — (s. §2) die „Lessons" enthalten Implementierungsaufgaben auf der Bril-IR mit Community-Lösungen im Repo — Datenfluss/SSA-Übungen mit Vergleichsmaterial.
    m-runtime:93:e1 [entry] Cornell CS 6120: Tasks  -> title ~ source-cornell-cs6120 (0.67)
L97: 🛠 rui314/chibicc — [github.com/rui314/chibicc] (https://github.com/rui314/chibicc): C-Compiler in ~700 Commits, jeder Commit ein lehrbuchartiger Schritt — das beste „Read the history"-Repo des Felds. Einsatz: vor/während CT als Implementierungs-Vorbild.
    m-runtime:97:u1 [url] https://github.com/rui314/chibicc  «github.com/rui314/chibicc»
L98: 🛠 munificent/craftinginterpreters — [github.com/munificent/craftinginterpreters] (https://github.com/munificent/craftinginterpreters): der komplette Code zum Buch (s. §2), Java + C.
    m-runtime:98:u1 [url] https://github.com/munificent/craftinginterpreters  «github.com/munificent/craftinginterpreters»
L99: 🛠 andrejbauer/plzoo — [github.com/andrejbauer/plzoo] (https://github.com/andrejbauer/plzoo): Mini-Implementierungen von ~10 Sprachparadigmen (typisiert, lazy, OO …) in OCaml — TPS-Konzepte als lauffähige 300-Zeilen-Sprachen.
    m-runtime:99:u1 [url] https://github.com/andrejbauer/plzoo  «github.com/andrejbauer/plzoo»
L100: 🛠 Stephen Diehl, „Write You a Haskell" — [dev.stephendiehl.com/fun] (https://dev.stephendiehl.com/fun/): Lambda-Kalkül → Hindley-Milner → Core in Haskell — die Brücke von §1/§4-Theorie zu Code.
    m-runtime:100:u1 [url] https://dev.stephendiehl.com/fun/  «dev.stephendiehl.com/fun»
L101: 🛠 QBE — [c9x.me/compile] (https://c9x.me/compile/): Backend in ~10k Zeilen C (SSA, RegAlloc) — zeigt, wie klein ein echtes Optimizer-Backend sein kann; Kontrast zum LLVM-Studium.
    m-runtime:101:u1 [url] https://c9x.me/compile/  «c9x.me/compile»
L102: 🛠 egraphs-good/egg + egglog — [github.com/egraphs-good/egg] (https://github.com/egraphs-good/egg): Equality Saturation / E-Graph-Rewriting in Rust — das für Stratum relevanteste Repo dieser gesamten Bibliothek. Term-Rewriting ohne Phase-Ordering-Problem; das e…
    m-runtime:102:u1 [url] https://github.com/egraphs-good/egg  «github.com/egraphs-good/egg»
L103: 🛠 rise-lang / elevate — [github.com/rise-lang] (https://github.com/rise-lang): Steuwers eigene IR + Rewrite-Strategie-Sprache als Code — vor der TPS-Prüfung und vor DEEM-Designdiskussionen gleichermaßen wertvoll.
    m-runtime:103:u1 [url] https://github.com/rise-lang  «github.com/rise-lang»
L104: 🛠 MLIR-Beispiele im LLVM-Monorepo — (s. §2 Toy-Tutorial) plus produktive Dialekte (linalg, affine) — Industrie-Referenz für Multi-Level-Rewriting.
    m-runtime:104:e1 [entry] MLIR-Beispiele im LLVM-Monorepo
L108: 📚 Nand2Tetris ([nand2tetris.org] (https://www.nand2tetris.org/)) — Teil II baut VM-Translator + Compiler für eine einfache Sprache: sanfter CT-Vorlauf, falls du vor M2/M4 Grundlagen-Sicherheit willst.
    m-runtime:108:u1 [url] https://www.nand2tetris.org/  «nand2tetris.org»
L109: 📚 OSTEP — Runtime-Systeme-Hälfte von Compiler Design (Speicher, Prozesse, Threads) — Kapitel gezielt, mit den mitgelieferten Homework-Simulatoren.
    m-runtime:109:e1 [entry] OSTEP
L110: 🎓 MIT 6.1810/6.828 (OS Engineering, OCW) — aus deinem Index; xv6-Labs als tiefste Runtime-Systems-Schule — nur bei echtem Zeitbudget, eher Zusatz als Pflicht.
    m-runtime:110:e1 [entry] MIT 6.1810/6.828 (OS Engineering, OCW)
L121: 📚 Stas Bekman, „Machine Learning Engineering Open Book" — [github.com/stas00/ml-engineering] (https://github.com/stas00/ml-engineering) (frei, vom BLOOM-Training-Lead). Die Praxis-Seite: Debugging auf Multi-Node, NCCL, Storage/IO fürs Training, Fehlertoleranz…
    m-runtime:121:u1 [url] https://github.com/stas00/ml-engineering  «github.com/stas00/ml-engineering»
L122: 📄 Paper-Kette (chronologisch lesen): Micikevicius et al., „Mixed Precision Training" (2018) → Shoeybi et al., „Megatron-LM" (2019, Tensor-Parallelismus) → Huang et al., „GPipe" + Narayanan et al., „PipeDream" (Pipeline-Parallelismus) → Rajbhandari et al., „Ze…
    m-runtime:122:e1 [entry] Paper-Kette (chronologisch lesen)
L123: 🛠 Code dazu: [NVIDIA/Megatron-LM] (https://github.com/NVIDIA/Megatron-LM) und [huggingface/nanotron] (https://github.com/huggingface/nanotron) (klein genug zum Lesen) — Parallelismus-Strategien im Quelltext statt im Diagramm.
    m-runtime:123:u1 [url] https://github.com/NVIDIA/Megatron-LM  «NVIDIA/Megatron-LM»
    m-runtime:123:u2 [url] https://github.com/huggingface/nanotron  «huggingface/nanotron»
L128: 📚 Kirk/Hwu, „Programming Massively Parallel Processors" (4. Aufl., PMPP) — das Lehrbuch zu CUDA-Grundmustern (Tiling, Memory Coalescing, Reduktionen). Einsatz: Referenz neben den Lectures; Kapitel zu Matmul-Optimierung ist Pflicht.
    m-runtime:128:e1 [entry] Kirk/Hwu, „Programming Massively Parallel Processors" (4. Aufl., PMPP)  -> title ~ source-kirk-hwu-pmpp (0.75)
L129: 📄 Horace He, „Making Deep Learning Go Brrrr From First Principles" — [horace.io/brrr_intro.html] (https://horace.io/brrr_intro.html). Das mentale Modell (compute-bound vs. memory-bound vs. overhead-bound), mit dem man jede DL-Performance-Frage sortiert. Einsat…
    m-runtime:129:u1 [url] https://horace.io/brrr_intro.html  «horace.io/brrr_intro.html»
L130: 📄 Dao et al., „FlashAttention" (2022) + 🛠 OpenAI Triton-Tutorials ([triton-lang.org] (https://triton-lang.org/)) — IO-Awareness als Optimierungsprinzip + Kernel schreiben in Python-Syntax. Triton ist zugleich ein Compiler über einer Tile-IR — die direkteste Fr…
    m-runtime:130:u1 [url] https://triton-lang.org/  «triton-lang.org»
L134: 📄 Pope et al., „Efficiently Scaling Transformer Inference" (MLSys 2023) — das Grundlagen-Paper für Serving-Ökonomie (Batching, KV-Cache, Parallelismus-Trade-offs). → direkt MLMMI-anschlussfähig.
    m-runtime:134:e1 [entry] Pope et al., „Efficiently Scaling Transformer Inference" (MLSys 2023)
L135: 📄 Kwon et al., „Efficient Memory Management for LLM Serving with PagedAttention" (SOSP 2023) — das vLLM-Paper: OS-Konzepte (Paging!) auf ML-Serving übertragen — konzeptionell die schönste Systems×ML-Arbeit der letzten Jahre; Repo bereits im ML-Nachtrag. Dazu:…
    m-runtime:135:e1 [entry] Kwon et al., „Efficient Memory Management for LLM Serving with PagedAttention" (SOSP 2023)
L136: 🛠 Praxis: ein kleines Modell einmal selbst quantisieren + servieren (llama.cpp → vLLM → Profiling mit GPU-MODE-Methodik) und die Latenz-/Durchsatz-Kurven nach CSB-/Gil-Tene-Regeln messen. Dieses eine Wochenendprojekt verbindet vier Achsen (🚀🤖📊🔧) und ist ein C…
    m-runtime:136:e1 [entry] Praxis

## ws-algo2-chat9 — repository/work/active/workspace-algo2-exam-prep/inputs/Chat9_Algo2_Plan.md

L32: 2. The course texts (exam-defining) | CLRS „Algorithmen: Eine Einführung", 4. Aufl. Deutsch (= EN 3rd ed; Plans/CS-Theory/algo2/Algo2/Buecher/Algo-Buch.pdf, EN parallel: Introduction_to_algorithms-3rd Edition.pdf) · DMS = Dietzfelbinger/Mehlhorn/Sanders (Algo…
    ws-algo2-chat9:32:p2 [path] Introduction_to_algorithms-3rd Edition.pdf  -> no material match
    ws-algo2-chat9:32:p3 [path] AlgoBuch 2.pdf  -> no material match
L39: Solved-practice bank (added KW 24 — full table in LEARNING-RESOURCES §6 → "Algo 2 (AL)"): ⭐ Goethe Frankfurt B-ALGO-2: 8 complete Klausuren 2021–2024, each with a solutions PDF ([directory] (https://files.tcs.uni-frankfurt.de/algo2/exams/) — flows, matching, a…
    ws-algo2-chat9:39:u1 [url] https://files.tcs.uni-frankfurt.de/algo2/exams/  «directory»

## ws-aml-dl-amls — repository/work/active/workspace-aml-exam-prep/inputs/DL-AMLS-Learning-Plan.md

L19: Given: [NNDL Ch. 1] (http://neuralnetworksanddeeplearning.com/chap1.html) (Nielsen) — free book, chapters 1–6.
    ws-aml-dl-amls:19:u1 [url] http://neuralnetworksanddeeplearning.com/chap1.html  «NNDL Ch. 1»
L25: [CS231n notes: ConvNets] (https://cs231n.github.io/convolutional-networks/) + [Understanding/Visualizing] (https://cs231n.github.io/understanding-cnn/) | The standard written reference for exactly your Task 1.4 methods (saliency, occlusion) — readable in under…
    ws-aml-dl-amls:25:u1 [url] https://cs231n.github.io/convolutional-networks/  «CS231n notes: ConvNets»  -> title ~ source-cs231n-notes (1.00)
    ws-aml-dl-amls:25:u2 [url] https://cs231n.github.io/understanding-cnn/  «Understanding/Visualizing»  -> title ~ source-zeiler-fergus-occlusion (1.00)
L53: DL.P1.A1 | Read AMLS L11 slides 4–13 (on disk). This is the literal playbook: geometric transforms, color jitter, cutout, AutoAugment. | 30m | List of 4–6 candidate augmentations matched to validation_augmented/ degradations
    ws-aml-dl-amls:53:p1 [path] validation_augmented/  -> no material match

## ws-m2-an-index — repository/work/active/workspace-m2-exam-prep/inputs/AN_Node_Plans_INDEX.md

L3: Written 2026-08-15 to workspace-m2-exam-prep/inputs/. Operational, not
    ws-m2-an-index:3:p1 [path] workspace-m2-exam-prep/inputs/  -> no material match
L14: curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml, not invented.
    ws-m2-an-index:14:p1 [path] curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml  -> no material match
L33: 0 | Proof reading & presentation | [AN_00_proof_presentation.md] (AN_00_proof_presentation.md) | calibrate | 60 min | contract + kleine_beweise
    ws-m2-an-index:33:p1 [path] AN_00_proof_presentation.md  -> no material match
L34: 1 | Foundations & the real numbers | [AN_01_foundations.md] (AN_01_foundations.md) | an0 | 210 min | Ch 1–2
    ws-m2-an-index:34:p1 [path] AN_01_foundations.md  -> no material match
L35: 2 | Sequences & convergence | [AN_02_sequences.md] (AN_02_sequences.md) | ana | 360 min | Ch 3
    ws-m2-an-index:35:p1 [path] AN_02_sequences.md  -> no material match
L36: 3 | Series & convergence criteria | [AN_03_series.md] (AN_03_series.md) | anb | 270 min | Ch 4
    ws-m2-an-index:36:p1 [path] AN_03_series.md  -> no material match
L37: 4 | Function limits & continuity | [AN_04_limits_continuity.md] (AN_04_limits_continuity.md) | anc | 300 min | §5.1–5.5
    ws-m2-an-index:37:p1 [path] AN_04_limits_continuity.md  -> no material match
L38: 5 | Exp/log & uniform convergence | [AN_05_exp_log_uniform.md] (AN_05_exp_log_uniform.md) | and | 150 min | §5.6–5.7
    ws-m2-an-index:38:p1 [path] AN_05_exp_log_uniform.md  -> no material match
L39: 6 | Differentiation & mean-value theorems | [AN_06_differentiation.md] (AN_06_differentiation.md) | ane | 330 min | Ch 6
    ws-m2-an-index:39:p1 [path] AN_06_differentiation.md  -> no material match
L40: 7 | Taylor approximation | [AN_07_taylor.md] (AN_07_taylor.md) | anf | 210 min | §6.8
    ws-m2-an-index:40:p1 [path] AN_07_taylor.md  -> no material match
L41: 8 | Riemann integration | [AN_08_integration.md] (AN_08_integration.md) | ang | 330 min | §7.1–7.3
    ws-m2-an-index:41:p1 [path] AN_08_integration.md  -> no material match
L42: 9 | Retrieval, mixed practice, combined mocks | [AN_09_exam_transfer.md] (AN_09_exam_transfer.md) | anx | 540 min | all
    ws-m2-an-index:42:p1 [path] AN_09_exam_transfer.md  -> no material match

## ws-m2-chat1 — repository/work/active/workspace-m2-exam-prep/inputs/Chat1_Foundations_AML_SaD_Plan.md

L18: > 📌 The single-study-script rule (KW 27): once a lecture has a complete unit in AML/my notes/lectNN …/, its Mini Plan is the ONLY study script for that lecture — the block tables below are just the step-ID ledger, and the Wiring §5 sequences are superseded fo…
    ws-m2-chat1:18:p1 [path] AML/my notes/lectNN …/  -> no material match
L275: > Optional supplement: [TU Python-for-ML Sheet 4] (https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/4.%20Sheet) — hands-on linear algebra exercises in Python. Do alongside or after F.E to practice the matrix operations behind β̂ = (XᵀX)⁻¹Xᵀy.
    ws-m2-chat1:275:u1 [url] https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/4.%20Sheet  «TU Python-for-ML Sheet 4»
L444: > 📚 Complete unit (KW 27): Plans/ML/foundations/AML/my notes/lect07 linear classifiers/ — Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam + Blatt-4 solution. Use the Mini Plan as the K2 study script.
    ws-m2-chat1:444:p1 [path] Plans/ML/foundations/AML/my notes/lect07 linear classifiers/  -> no material match
L473: > 🎬 Start here before the slides: [3Blue1Brown — Neural Networks] (https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi) (4 videos, ~1.5h): "What is a NN?", "Gradient Descent", "Backpropagation", "Backprop Calculus". Watch all 4 BEFORE L1–L…
    ws-m2-chat1:473:u2 [url] https://ki-campus.org/en/learning-opportunities/videos/neural-networks  «they build exactly the right intuition. Also on KI-Campus»  -> same line as ['source-3b1b-neural-networks']
L477: > Optional supplement: [TU Python-for-ML Sheet 5] (https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/5.%20Sheet) — automatic differentiation (autograd), Numba, Cython. Autograd is exactly what PyTorch's loss.backward() does. Do during or after Blo…
    ws-m2-chat1:477:u1 [url] https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/5.%20Sheet  «TU Python-for-ML Sheet 5»

## ws-m2-chat8 — repository/work/active/workspace-m2-exam-prep/inputs/Chat8_Analysis_SaD_Plan.md

L23: 3. The folder is rich but unordered. Plans/Math/analysis/Analysis/ holds the skript, 6 HU exercise sheets, ~8 solved problem collections, MIT lecture notes, Rudin, and Strang — with no sequence. This plan turns the pile into an ordered path.
    ws-m2-chat8:23:p1 [path] Plans/Math/analysis/Analysis/  -> no material match
L33: 2b. Drill companion | Forster/Wessoly — Übungsbuch zur Analysis (Analysis/Buecher/, downloaded KW 24 via HU Springer license) + Fritzsche Trainingsbuch zur Analysis 1 and Deitmar Übungsbuch zur Analysis (both Buecher/, triaged Jul 4 — chapter map in the cross…
    ws-m2-chat8:33:p1 [path] Analysis/Buecher/  -> no material match
    ws-m2-chat8:33:p2 [path] Buecher/  -> no material match
L34: 3. Rigor / proof technique | MIT 18.100A Real Analysis (Casey Rodriguez, Fall 2020) — [playlist] (https://www.youtube.com/watch?v=LY7YmuDbuW0&list=PLUl4u3cNGP61O7HkcF7UImpM0cR_L2gSw) + full lecture notes mit18_100af20_lec_full2.pdf (92 pp, same numbering as th…
    ws-m2-chat8:34:u1 [url] https://www.youtube.com/watch?v=LY7YmuDbuW0&list=PLUl4u3cNGP61O7HkcF7UImpM0cR_L2gSw  «playlist»
L35: (optional rigor track) | Rudin Principles_of_Mathematical_Analysis-Rudin.pdf, realanal.pdf/realanal2.pdf | Same pattern as 18.650/STAT110x for SaD: only if a proof in the skript feels unmotivated and you have spare appetite. NOT exam-required.
    ws-m2-chat8:35:p1 [path] Principles_of_Mathematical_Analysis-Rudin.pdf  -> no material match
L40: Solved-problem bank in Plans/Math/analysis/Analysis/ (mapped to blocks below)
    ws-m2-chat8:40:p1 [path] Plans/Math/analysis/Analysis/  -> no material match
L42: > 🗂️ Folder tidied KW 27 (Jul 2): the flat pile is now sorted — Skript+HU/ (unser skript, kleine_beweise ⭐, ana_inf serie05–09 + WV), Buecher/ (all books+notes — incl. 8 NEWLY SURFACED from a nested duplicate folder, all 5 unknowns triaged Jul 4 — see the cro…
    ws-m2-chat8:42:p1 [path] Skript+HU/  -> no material match
    ws-m2-chat8:42:p2 [path] Buecher/  -> no material match
    ws-m2-chat8:42:p3 [path] Drill-Loesungen/  -> no material match
    ws-m2-chat8:42:p4 [path] Klausuren-extern/  -> no material match
L46: Mengen und Abbildungen ( sehr hilfreich !).pdf, Relationen .pdf | Sets, maps, relations | AN.0
    ws-m2-chat8:46:p1 [path] Mengen und Abbildungen ( sehr hilfreich !).pdf  -> no material match
    ws-m2-chat8:46:p2 [path] Relationen .pdf  -> no material match
L49: Grenzwert von folgen.pdf, loesungen4.pdf, auf_2_2_Folgen_loesungen.pdf (30 pp Folgen-Katalog w/ solutions — was also present as duplicate 'gute Aufgaben mit lösungen.pdf', deleted KW 27), bestimmt..pdf | Solved sequence-convergence practice | AN.A
    ws-m2-chat8:49:p1 [path] Grenzwert von folgen.pdf  -> no material match
    ws-m2-chat8:49:p3 [path] auf_2_2_Folgen_loesungen.pdf  -> no material match
    ws-m2-chat8:49:p4 [path] bestimmt..pdf  -> no material match
L51: KIT blatt zu Reihen .pdf, Tutorium-Musterloesung-Reihen.pdf, auf_2_3_Reihen_loesungen.pdf | Solved series practice | AN.B
    ws-m2-chat8:51:p1 [path] KIT blatt zu Reihen .pdf  -> no material match
    ws-m2-chat8:51:p3 [path] auf_2_3_Reihen_loesungen.pdf  -> no material match
L53: Proofs in calculus.pdf | Limits/series proof patterns (EN) | AN.A–C
    ws-m2-chat8:53:p1 [path] Proofs in calculus.pdf  -> no material match
L54: u10_L.pdf (solved Blatt 10, TU Darmstadt), IngMath_2_aufgaben.pdf (312 pp solved, Voß) | Derivative/Taylor/integral drill — pull by topic | AN.E–G
    ws-m2-chat8:54:p1 [path] u10_L.pdf  -> no material match
    ws-m2-chat8:54:p2 [path] IngMath_2_aufgaben.pdf  -> no material match
L55: Aufgabensammlung_M1__Loesung.pdf, AS-Ana1.pdf (53 pp themed Aufgabensammlung) | Mixed Klausur-style collections | AN.X
    ws-m2-chat8:55:p1 [path] Aufgabensammlung_M1__Loesung.pdf  -> no material match
L114: AN.A3 (1h) — Skript pp. 79–84: bestimmte Divergenz (→ ±∞), Standardgrenzwerte (qⁿ, ⁿ√n, (1+x/n)ⁿ → eˣ). bestimmt..pdf for drill.
    ws-m2-chat8:114:p1 [path] bestimmt..pdf  -> no material match
L115: AN.A4 (2.5h) — Drill block (this is where the exam points live): serie06, serie07, auf_2_2_Folgen_loesungen.pdf (work ≥10 of the 30 pp), loesungen4.pdf (the "find N(ε)" type — a classic Klausur opener), auf_2_2_Folgen_loesungen.pdf. Target fluency: given a se…
    ws-m2-chat8:115:p1 [path] auf_2_2_Folgen_loesungen.pdf  -> no material match
    ws-m2-chat8:115:p3 [path] auf_2_2_Folgen_loesungen.pdf  -> no material match
L133: AN.C3 (1.5h) — Drill: serie09 (exactly this topic), Proofs in calculus.pdf continuity sections.
    ws-m2-chat8:133:p1 [path] Proofs in calculus.pdf  -> no material match
L151: AN.E4 (1h) — Drill: pull derivative/MVT/l'Hospital tasks from IngMath_2_aufgaben.pdf + AS-Ana1.pdf.
    ws-m2-chat8:151:p1 [path] IngMath_2_aufgaben.pdf  -> no material match

## ws-thesis-brief — repository/work/active/workspace-thesis-mle-medical/inputs/original-thesis-brief.md

L14: > https://www.kaggle.com/code/sudalairajkumar/winning-solutions-of-kaggle-competitions
    ws-thesis-brief:14:u1 [url] https://www.kaggle.com/code/sudalairajkumar/winning-solutions-of-kaggle-competitions  «>»
