# MASTERS-MATH-RESOURCES — Lernbibliothek für den 🧮 Mathe-Block

> **Stand:** 2026-06-11 · Phase 2, Teil 3 (Achse 🧮 aus `MASTERS-MODULE-MENU.md`: alle 5 Module)
> **Modulprofile aus den offiziellen Lehrinhalten im 888-S.-Modulkatalog.** Konvention: 🎓 Vorlesung · 📚 Buch · 📄 Paper/Skript · 🛠 Hands-on, mit Einsatz-Timing.
> **Achsen-Hinweis:** Alle 5 Module werden **mündlich** geprüft außer Optimization Algorithms (schriftlich). Mündliche Mathe-Prüfungen belohnen Herleitungs-Souveränität statt Rechen-Tempo — die Ressourcen unten sind danach ausgesucht. Erinnerung: Es gibt kein Bayesian/Monte-Carlo-Modul im Studiengang; diese Achse *ist* der Mathe-Unterbau deines Profils.

---

## 1. Mathematics of Machine Learning ([#40894](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40894&version=3), 6 LP, WiSe+SoSe, **mündlich**, Stanczak)

**Modulprofil (lt. Katalog):** Statistische Lerntheorie komplett: Lernmodell, **Lernen via uniformer Konvergenz, Bias-Complexity-Tradeoff, Konzentrationsungleichungen, Suprema empirischer Prozesse, VC-Dimension, Nonuniform Learning, Runtime of Learning**, Hilberträume & Projektionsmethoden, **Kernel-/Multi-Kernel-Methoden**, Regularisierung, Dimensionsreduktion, **Compressive Sensing**.

- 📚 **Shalev-Shwartz/Ben-David, „Understanding Machine Learning: From Theory to Algorithms"** — [frei als PDF (Autoren-Seite)](https://www.cs.huji.ac.il/~shais/UnderstandingMachineLearning/). **Die Themenliste des Moduls liest sich fast wie das Inhaltsverzeichnis dieses Buchs** („Learning via Uniform Convergence", „Bias-Complexity Tradeoff", „Nonuniform Learnability", „The Runtime of Learning" sind wörtlich Kapiteltitel). Mit hoher Wahrscheinlichkeit das Rückgrat der Vorlesung. Einsatz: Hauptbuch; Kapitel 2–7 vor der Semestermitte, die Beweise aktiv nachrechnen — genau die werden mündlich abgefragt.
- 📚 **Mohri/Rostamizadeh/Talwalkar, „Foundations of Machine Learning" (2. Aufl.)** — [frei als PDF](https://cs.nyu.edu/~mohri/mlbook/). Die Rademacher-Komplexitäts-Perspektive, die SSBD knapper behandelt; sauberste Darstellung von Generalisierungsschranken für Kernmethoden. Einsatz: Zweitquelle pro Thema; wenn Stanczak Rademacher-Argumente bringt, ist das hier die Referenz.
- 🎓 **Stanford CS229M / STATS214 „Machine Learning Theory" (Tengyu Ma)** — [Vorlesungsnotizen frei](https://web.stanford.edu/class/stats214/) (+ Videos auf YouTube). Moderner Kursdurchgang durch uniforme Konvergenz, Konzentration, VC, Margin-Theorie — gut als Video-Spur neben den Büchern. Einsatz: semesterbegleitend zum Hör-Lernen; mündliche Prüfungen profitieren davon, Argumente einmal *gehört* statt nur gelesen zu haben.
- 📚 **Vershynin, „High-Dimensional Probability: An Introduction with Applications in Data Science"** — [frei als PDF (Autoren-Seite)](https://www.math.uci.edu/~rvershyn/papers/HDP-book/HDP-book.html). **Der** Text für Konzentrationsungleichungen und Suprema empirischer Prozesse (Sub-Gaussian, Bernstein, Chaining) — und Kapitel 10 deckt Compressive Sensing ab, womit zwei Modulblöcke aus einer Quelle kommen. Einsatz: für den Konzentrations-Block; anspruchsvoll, aber exakt das Niveau des Moduls.
- 📚 **Wainwright, „High-Dimensional Statistics: A Non-Asymptotic Viewpoint"** — die schwerere Alternative zu Vershynin (empirische Prozesse, Metrik-Entropie). Einsatz: nur bei echtem Theorie-Appetit oder wenn die Vorlesung Chaining-Argumente formal führt.
- 📄 **Candès/Wakin, „An Introduction to Compressive Sampling" (IEEE SPM 2008)** — das Standard-Tutorial zu Compressive Sensing (~20 Seiten), genau richtig für den CS-Schlussblock des Moduls; Stanczak ist Signalverarbeiter, der Block hat bei ihm Gewicht. Einsatz: vor dem CS-Teil; danach ggf. Foucart/Rauhut als Buchreferenz.
- 🎓 **Caltech „Learning from Data"** (s. `MASTERS-ML-RESOURCES.md`, MI I) — **Brücken-Ressource:** falls VC-Dimension/Generalisation neu sind, ist Abu-Mostafa der sanfte Einstieg, *bevor* SSBD formal wird. Einsatz: Vorsemester-Warm-up; doppelt nutzbar für MI I.

## 2. Foundations of Stochastic Processes ([#40256](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40256&version=3), 6 LP, WiSe, **mündlich**, Caire)

**Modulprofil (lt. Katalog):** Axiomatische Wahrscheinlichkeit, diskrete/stetige Zufallsvariablen, Zufallsvektoren, **multivariate Gauß-Verteilungen**, Maßwechsel, Transformationsmethoden (PGF/CF/MGF), **Gesetz der großen Zahlen, ZGS, Large Deviations**, **MMSE-Schätzung & Orthogonalitätsprinzip**, stochastische Konvergenz, **Markov-Ketten**, **WSS-Prozesse & Spektraldarstellung**. Caire ist Informationstheoretiker — das Modul trägt eine klare EE/Kommunikationstheorie-Handschrift.

- 📚 **Papoulis/Pillai, „Probability, Random Variables and Stochastic Processes" (4. Aufl.)** — der EE-Klassiker, dessen Kapitelfolge (RVs → Vektoren → MMSE/Orthogonalität → WSS/Spektraldichte) der Modulgliederung entspricht; MMSE + Orthogonalitätsprinzip + Spektraldarstellung sind *Papoulis-Kernland*. Einsatz: Hauptreferenz; für die mündliche Prüfung die Herleitungen von MMSE-Schätzer und Wiener-Khinchin sicher beherrschen.
- 📚🎓 **Gallager, „Stochastic Processes: Theory for Applications"** + **MIT 6.262 „Discrete Stochastic Processes"** — [OCW-Kurs mit Videos](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/). Gallager (Informationstheorie-Legende, fachlich Caires Schule) behandelt Markov-Ketten, Large Deviations und Konvergenzbegriffe mit genau der Mischung aus Strenge und Intuition, die mündliche Prüfungen verlangen. Einsatz: Markov-/Konvergenz-Block; die OCW-Videos sind die beste freie Vorlesungsspur zum Modul.
- 📚 **Grimmett/Stirzaker, „Probability and Random Processes"** — die Mathematik-Seite: sauber bei Maßwechsel, Konvergenzarten, erzeugenden Funktionen; Tausende Übungsaufgaben (+ Lösungsband „One Thousand Exercises"). Einsatz: Zweitbuch und Aufgabenquelle — mündliche Prüfungen bei Theoretikern fragen gern die Abgrenzung der Konvergenzbegriffe, die hier am klarsten steht.
- 📚🎓 **Bertsekas/Tsitsiklis, „Introduction to Probability"** + **MIT 6.041 auf OCW** (Videos). **Brücken-Ressource:** falls die axiomatische Grundlage aus dem HU-Bachelor wackelt (relevant: dein Mathe-2-Kontext), ist das der gründlichste sanfte Unterbau — bis ZGS und Markov-Ketten. Einsatz: Sommer-Vorbereitung; zahlt nebenbei auf SaD-/Statistik-Festigkeit ein.
- 📚 **Norris, „Markov Chains"** — [Kapitel frei auf der Autoren-Seite](https://www.statslab.cam.ac.uk/~james/Markov/). Das Standardwerk nur für Markov-Ketten (diskret/stetig, Rekurrenz, Stationarität). Einsatz: Vertiefung des Markov-Blocks, der in der mündlichen Prüfung fast sicher drankommt.

## 3. Optimization Algorithms ([#41016](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41016&version=2), 6 LP, WiSe, **schriftlich**, Toussaint)

**Modulprofil (lt. Katalog):** Kontinuierliche, v. a. restringierte Optimierung. Teil 1: Gradientenabstieg, Backtracking, **Wolfe-Bedingungen**, Newton/Quasi-Newton/**BFGS**; Teil 2: **KKT, Log-Barrier, Augmented Lagrangian, primal-duales Newton**, konvexe Programme; Teil 3 (variiert): SGD für NNs, **Bayes'sche/globale Optimierung**, Black-Box-/evolutionäre Verfahren, Software (CERES). Direkt ML-relevant (Training = Optimierung) und die formale Heimat deiner ML-2-X-Dualitätslücken.

- 🎓📄 **Toussaints eigenes Vorlesungsskript — komplett öffentlich:** [Lecture-Optimization.pdf](https://www.user.tu-berlin.de/mtoussai/teaching/Lecture-Optimization.pdf) (alle Folien + Übungen als ein indexiertes Skript, explizit „to help prepare for exams") · [Kursseite WS 20/21 mit Einzelfolien](https://www.user.tu-berlin.de/mtoussai/teaching/20-Optimization/) · [LaTeX-Quellen auf GitHub](https://github.com/MarcToussaint). **Das Modul ist damit vollständig im Voraus studierbar** — Skript inkl. Spezialthemen wie [No Free Lunch](https://www.user.tu-berlin.de/mtoussai/teaching/Optimization/16-noFreeLunch.pdf) und [Bayesian Optimization](https://www.user.tu-berlin.de/mtoussai/teaching/Optimization/17-bayesOpt.pdf). Einsatz: Primärquelle vor und während des Semesters; die enthaltenen Übungen sind das Klausurtraining.
- 📚 **Nocedal/Wright, „Numerical Optimization" (2. Aufl.)** — das Standardwerk, dessen Kapitel (Line Search/Wolfe, Newton, **BFGS**, KKT, Penalty/**Augmented Lagrangian**, Interior Point) Teil 1+2 des Moduls 1:1 abdecken. Einsatz: wo Toussaints Folien zu kompakt sind, liefert Nocedal/Wright die ausgeschriebene Herleitung samt Konvergenzbeweis.
- 📚🎓 **Boyd/Vandenberghe, „Convex Optimization"** — [frei + EE364a-Videos](https://web.stanford.edu/~boyd/cvxbook/). Für den Konvexitäts-/Dualitäts-Unterbau (KKT sauber verstanden = halbe Klausur) — und dieselbe Investition trägt die SVM-Dualität in ML 2-X. Einsatz: Kapitel 4–5 und 9–11 gezielt.
- 📚 **Kochenderfer/Wheeler, „Algorithms for Optimization" (MIT Press)** — [frei als PDF (algorithmsbook.com/optimization)](https://algorithmsbook.com/optimization/). Jeder Algorithmus als lauffähiger Code + Visualisierung; deckt auch Teil 3 (stochastisch, evolutionär, Bayes-Optimierung) ab. Einsatz: Implementierungs-Spur — einen Optimierer selbst zu coden verankert Wolfe-Bedingungen besser als jede Folie.
- 📚 **Garnett, „Bayesian Optimization"** — [frei, bayesoptbook.com](https://bayesoptbook.com/). Das Referenzbuch zum variierenden Teil-3-Thema; baut auf Gaußprozessen auf (→ Rasmussen/Williams aus `MASTERS-ML-RESOURCES.md` §8). Einsatz: nur wenn Teil 3 im Jahrgang Bayes-Optimierung bringt.
- 🛠 **CERES Solver / scipy.optimize / JAXopt-Tutorials** — das Modul nennt CERES explizit. Einsatz: ein kleines Curve-Fitting-Problem einmal mit CERES (C++) oder scipy (Python) durchziehen; Klausuren fragen gern, *welcher* Solver-Typ zu welchem Problem passt.

## 4. Diskrete Optimierung (ADM II) ([#20088](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=20088&version=1), **10 LP**, SoSe, **mündlich 30min**, Skutella, Mathe-Fakultät)

**Modulprofil (lt. Katalog):** **Simplex** (revidiert, dual, Pivotregeln, exponentielle Beispiele), **Polyedertheorie**, primal-duale Algorithmen auf Graphen/Netzwerken, **Ellipsoid-Methode, Innere-Punkte-Verfahren**; **ganzzahlige Optimierung** (Branch & Bound, Lagrange-Relaxation, Schnittebenen), Zuordnungsprobleme/**Matchings/Matroide**; Einstieg Approximation (Gütegarantien, MAX-SNP). ⚠ Setzt ADM-I-Stoff voraus (LP-Grundlagen) und ist mit 10 LP + Mathe-Fakultäts-Niveau der schwerste Brocken der Achse — wähle ihn nur mit echtem Theorie-Commitment.

- 📚 **Bertsimas/Tsitsiklis, „Introduction to Linear Optimization"** — der Standard für die erste Modulhälfte: Simplex-Varianten, Degeneration, Polyedergeometrie, Dualität, Ellipsoid, Interior Point — mit der geometrischen Intuition, die in mündlichen Prüfungen Punkte bringt. Einsatz: Hauptbuch für den LP-Teil.
- 📚 **Korte/Vygen, „Combinatorial Optimization: Theory and Algorithms"** — die „Bonner Bibel": Matchings, Matroide, Netzwerkflüsse, ganzzahlige Programme — deckt die zweite Modulhälfte vollständig und auf deutschem Lehrstuhl-Niveau ab (deutsche Ausgabe existiert). Einsatz: Referenz für Matching-/Matroid-Theorie; Beweisstruktur passt zur Skutella-Schule (COGA).
- 📄 **Lex Schrijver, „A Course in Combinatorial Optimization"** — [frei als PDF (CWI)](https://homepages.cwi.nl/~lex/files/dict.pdf). ~250 Seiten kondensierte Vorlesungsnotizen vom Großmeister: LP-Dualität, Matchings, Matroide, TUM-Matrizen. Einsatz: kompakte Zweitdarstellung — ideal zum Wiederholen vor der mündlichen Prüfung.
- 🎓 **MIT 18.433/6.251 (Goemans-Notizen, frei)** + **MIT OCW „Integer Programming and Combinatorial Optimization"** — amerikanische Vorlesungsspur zu Polyedern, Branch & Bound, Schnittebenen. Einsatz: wenn du eine Videoquelle willst; sonst reichen die Bücher.
- 📚 **Matoušek/Gärtner, „Understanding and Using Linear Programming"** — **Brücken-Ressource:** schlank, geometrisch, der schnellste Weg, ADM-I-Lücken (LP-Basics, Dualität) zu schließen, bevor ADM II startet. Einsatz: Sommer davor.
- 📚 **Wolsey, „Integer Programming"** — fokussierte Referenz nur für den ILP-Block (B&B, Cuts, Lagrange-Relaxation). Einsatz: gezielt zur zweiten Semesterhälfte.

## 5. Approximationsalgorithmen (ADM III) ([#20091](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=20091&version=1), **10 LP**, WiSe+SoSe, **mündlich 30min**, Skutella, Mathe-Fakultät)

**Modulprofil (lt. Katalog):** (Nicht-)Approximierbarkeit, **PTAS**, **LP-Runden** (randomisiert/deterministisch/iteriert), **Dual Fitting (Set Cover)**, **primal-duales Schema, Local-Ratio-Methode**, Netzwerkdesign, **SDP-Relaxationen am Beispiel MAX CUT**, **PCP-Theorem (ohne Beweis)**, lückenerzeugende/-bewahrende Reduktionen, MAX-SNP. Die ⚙️-affinste Wahl der Achse — und thematisch näher an deinem Algorithmik-Profil als ADM II.

- 📚 **Williamson/Shmoys, „The Design of Approximation Algorithms"** — [komplett frei, designofapproxalgs.com](https://www.designofapproxalgs.com/). **Nahezu deckungsgleich mit dem Modulprofil:** LP-Rounding in allen Varianten, primal-dual, Local Ratio, SDP/**MAX CUT (Goemans-Williamson — Williamson ist Co-Autor!)**, Hardness. Einsatz: Hauptbuch; pro Vorlesungswoche das passende Kapitel.
- 📚 **Vazirani, „Approximation Algorithms"** — der kompaktere Klassiker; **Dual Fitting wird hier am Beispiel Set Cover eingeführt — exakt wie im Modulprofil**. Einsatz: Zweitdarstellung; Vaziranis kurze, beweis-zentrierte Kapitel sind ideales Material für 30-minütige mündliche Prüfungen („erklären Sie Technik X an Beispiel Y").
- 📄 **Goemans/Williamson, „Improved Approximation Algorithms for Maximum Cut and Satisfiability Problems Using Semidefinite Programming" (JACM 1995)** — das Original zum SDP-Block; eines der schönsten Papers der theoretischen Informatik. Einsatz: vor dem SDP-Teil lesen — die 0.878-Rundungsanalyse einmal selbst nachgerechnet zu haben ist die beste Prüfungsversicherung.
- 📚 **Arora/Barak, „Computational Complexity: A Modern Approach"** (Kapitel zu PCP & Hardness of Approximation; Entwurf frei online) — fürs PCP-Theorem und Gap-Reduktionen die zugänglichste Darstellung. Einsatz: nur den PCP-Block (im Modul „ohne Beweis" — Verständnis der Aussage + Konsequenzen genügt).
- 🎓 **Anupam Gupta / Ryan O'Donnell (CMU) „Approximation Algorithms"-Vorlesungsnotizen** (frei auf den CMU-Seiten) — moderne Kursdurchgänge mit Übungen als US-Spur. Einsatz: Aufgabenquelle; mündliche Prüfungen bei Skutella verlangen Technik-Transfer auf neue Probleme — genau das trainieren diese Problem Sets.
- 📚 **Korte/Vygen** (s. ADM II) — die Approximationskapitel verbinden ADM II und III; bei Belegung beider Module ist das Buch die gemeinsame Klammer.

## 6. Foundations of Statistical Inference, Detection & Estimation ([#41105](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41105&version=2), 6 LP, SoSe, Portfolio, Caire)

**Modulprofil (lt. Katalog):** Hypothesentests (**MAP, Neyman-Pearson, Minimax**); Signalerkennung (un-/codierte Modulation, ISI-Kanäle, **Viterbi, BCJR**); Parameterschätzung (**Fisher-Information & Cramér-Rao-Grenze, MVU, Maximum-Likelihood, Least Squares, Bayes**); Bayessche Inferenz, **Sum-Product/Belief Propagation, Approximated Message Passing (AMP)**. Das **SoSe-Statistik-Gegenstück zu FoSP**, gleiche Caire/EE-Schule. Brücke: Estimation/Detection ist die formale Basis unter ML 2-X (MLE), MI II (Schätztheorie) und der Uncertainty-Achse.

- 📚 **Kay, „Fundamentals of Statistical Signal Processing", Vol. I (Estimation) + Vol. II (Detection)** — DER kanonische Detektions-/Schätzungstext; Cramér-Rao, MVU, MLE, Neyman-Pearson stehen 1:1 im Modulprofil. Einsatz: Hauptbuch — Vol. I für den Schätz-, Vol. II für den Detektionsteil.
- 📚 **Poor, „An Introduction to Signal Detection and Estimation" (Springer)** — kompakter, mathematisch elegant; ideal für die Hypothesentests-/Detektionstheorie. Einsatz: Zweitquelle für die Beweisseite.
- 📄 **Kschischang/Frey/Loeliger, „Factor Graphs and the Sum-Product Algorithm" (IEEE IT 2001)** — der kanonische Faktorgraphen/BP-Artikel; deckt den Sum-Product/Belief-Propagation-Block. Einsatz: Pflicht für den Message-Passing-Teil.
- 📚 **Bishop, PRML** — Kap. 8 (Graphical Models / Sum-Product = Belief Propagation) + Kap. 2 (MLE/Bayes). Einsatz: didaktische Brücke zu ML 2-X/MI II (du nutzt Bishop ohnehin als Hauptbuch).
- 📄 **Donoho/Maleki/Montanari, „Message-Passing Algorithms for Compressed Sensing" (PNAS 2009)** — der AMP-Ursprung. Einsatz: nur für den (exotischen) AMP-Block, den kaum ein Lehrbuch abdeckt.
- **Cross:** MLE/Cramér-Rao = exakt der Schätztheorie-Teil von **MI II** (ML-Resources §6); BP/Faktorgraphen = die graphischen Modelle aus **ML 2-X** (ML-Resources §1). Gleiche Caire-Notation wie **FoSP** (§2).

## 7. Information Theory and Applications ([#40981](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40981&version=1), 6 LP, SoSe, Portfolio, Caire)

**Modulprofil (lt. Katalog):** **Entropie, Cross-Entropy (Information Divergence), Mutual Information**; fundamentale Grenzen der Datenkompression; **Kanalkapazität** & Datenübertragung; **Rate-Distortion-Theorie**; Multiple-Access-/Broadcast-Kanäle (Uplink/Downlink), Interferenz, Relaying; Projektarbeit. ML-Bezug: Entropie/KL/Mutual Information sind das Vokabular von Loss-Funktionen, VAEs und dem Information Bottleneck.

- 📚 **Cover & Thomas, „Elements of Information Theory" (2. Aufl., Wiley)** — das kanonische IT-Lehrbuch; Entropie, Kanalkapazität, Rate-Distortion 1:1 zum Profil. Einsatz: Hauptbuch.
- 📚 **MacKay, „Information Theory, Inference, and Learning Algorithms"** — [frei: inference.org.uk/mackay/itila](https://www.inference.org.uk/mackay/itila/). Verbindet IT direkt mit ML/Inferenz — für dich die ideale Brücke (gleiche Sprache wie FoSIDE/ML). Einsatz: parallel; die Inferenz-/ML-Kapitel doppelt nutzbar.
- 🎓 **Stanford EE376A „Information Theory" (Weissman)** — Notes + Übungen frei. Einsatz: semesterbegleitende Video-/Aufgabenspur.
- 📄 **Tishby/Pereira/Bialek, „The Information Bottleneck Method" (1999)** + **Alemi et al., „Deep Variational Information Bottleneck" (ICLR 2017)** — der direkte IT↔Deep-Learning-Brückenschlag. Einsatz: für den Projektteil bzw. um den ML-Bezug sauber zu zeigen.
- **Cross:** KL-Divergenz/Cross-Entropy = die Loss-Funktionen aus **DL1/DL2**; Rate-Distortion ↔ VAE/Kompression (**DL2**, ML-Resources §3).

---

## Querverbindungen (so verzahnt sich der Mathe-Block)

1. **Zwei Teilachsen:** *Stochastik/Lerntheorie* (MathML + FoSP) vs. *Optimierung* (OptAlgos + ADM II/III). Für dein Profil (Optimizer/Runtime!) hat die Optimierungsschiene Priorität; MathML ist die theorieseitige Absicherung deiner ML-Module.
2. **Buch-Synergien:** SSBD trägt MathML *und* MI I (Lerntheorie-Teil); Boyd trägt OptAlgos *und* die SVM-Dualität in ML 2-X; Rasmussen/Williams (ML-RESOURCES §8) trägt Gaußprozesse *und* Garnetts Bayes-Optimierung.
3. **Kostenlos-Quote:** Fast die gesamte Achse ist legal frei verfügbar — SSBD, Mohri, Vershynin, Toussaint-Skript, Kochenderfer, Garnett, Schrijver, Williamson/Shmoys, Boyd. Nur Papoulis, Nocedal/Wright, Korte/Vygen und Bertsimas/Tsitsiklis brauchen die Bibliothek.
4. **ADM-Warnung:** ADM II/III sind 10-LP-Module der Mathe-Fakultät mit mündlicher Prüfung bei Skutella — hohes Niveau, hoher Ertrag fürs ⚙️-Profil, aber nicht neben einem Implementierungs-Brocken (DBTLAB/BDSPRO) ins selbe Semester legen (Regel §4.2 im MODULE-MENU).
5. **Mathe-2-Dividende:** Bertsekas/Tsitsiklis (FoSP-Brücke) und Matoušek/Gärtner (ADM-Brücke) sind gleichzeitig solide Wiederholungsarbeit für den Bachelor-Drittversuch — Sommer-Investition mit Doppelnutzen.

> **Pflege:** Toussaint-/Stanford-/MIT-Links beim Modulstart auf aktuelle Jahrgänge prüfen; tote Links hier korrigieren.

---

## Mega-Sweep-Nachtrag (2026-06-11): Übungen, Klausuren & Code-Repos

### Übungsblätter & Klausuren anderer Unis

- 📝 **MIT OCW 18.657 „Mathematics of Machine Learning" (Rigollet)** — [ocw.mit.edu/courses/18-657-mathematics-of-machine-learning-fall-2015](https://ocw.mit.edu/courses/18-657-mathematics-of-machine-learning-fall-2015/) — **aus deinem Ultimate-Index, namensgleich mit dem TU-Modul!** Vollständige Lecture Notes + Problem Sets zu VC, uniformer Konvergenz, Konzentration. Einsatz: die MIT-Psets als MathML-Übungsblätter — es gibt kein passenderes fremdes Material.
- 📝 **Stanford EE364a (Boyd): Homework + Final-Archiv** — die Kursseite veröffentlicht Psets und alte Finals (mit Lösungen); zusätzlich das offizielle Boyd/Vandenberghe-Buch „Additional Exercises" mit Lösungs-Repo. Rechentraining für KKT/Dualität (OptAlgos + ML-2-X-Doppelnutzen).
- 📝 **Toussaints eigene Übungen** — bereits im Komplett-Skript (s. §3) enthalten — das *ist* das Klausurtraining für OptAlgos; nicht doppelt suchen.
- 📝 **MIT OCW 6.262 „Discrete Stochastic Processes"** — neben den Videos liegen dort Psets + Quizzes **mit Lösungen** — die FoSP-Übungsschiene (Markov-Ketten, Konvergenz).
- 📝 **Grimmett/Stirzaker: „One Thousand Exercises in Probability"** — der offizielle Lösungsband zum FoSP-Zweitbuch; mündliche Prüfungen bei Caire mit 20–30 durchgerechneten Aufgaben betreten ist ein anderes Spiel.
- 📝 **MIT OCW 6.042J (aus deinem Ultimate-Index)** — Mathematics for CS mit kompletten Psets/Exams + Lösungen: kein Master-Stoff, aber das ideale **TheoInf-/Beweis-Auffrischtraining** parallel zum Mathe-2-Drittversuch und für den R2-Zugangscheck.
- 📝 **ADM-Übungsersatz:** MIT OCW [18.433 Combinatorial Optimization / 6.251 Intro to Mathematical Programming] — Psets mit Lösungen als Ersatz für die internen COGA-Blätter; dazu Schrijvers Skript-Übungen (s. §4).

### Code & Hands-on

- 🛠 **CVXPY** — [cvxpy.org](https://www.cvxpy.org/) (+ Beispielgalerie): konvexe Programme deklarativ lösen; jede EE364a-Aufgabe lässt sich damit gegenprüfen. Einsatz: Selbstkontrolle beim Dualitäts-Lernen.
- 🛠 **Toussaints LaTeX/Code-Repos** — [github.com/MarcToussaint](https://github.com/MarcToussaint): Skriptquellen + Robotik/Optimierungs-Code des Dozenten.
- 🛠 **Project Euler + Exercism (aus deinem Ultimate-Index)** — mathematische Programmierprobleme als Dauer-Fingerübung; Euler-Probleme 1–100 sind diskrete-Mathe-Kondition für ADM-Niveau.
- 🛠 **MML-Buch-Notebooks** — [github.com/mml-book/mml-book.github.io](https://github.com/mml-book/mml-book.github.io): Übungen + Jupyter-Begleitcode zur Mathe-Brücke (Deisenroth).

> Einordnung Ultimate-Index: 18.01/18.02/18.06/18.100A (Calculus/LinAlg/Analysis auf OCW) sind als Bachelor-Auffrischung katalogisiert — fürs Master-Niveau dieser Achse nur bei konkreten Lücken anzapfen; 18.06 (Strang) bleibt die beste LinAlg-Notfall-Ressource vor MathML/MI II.
