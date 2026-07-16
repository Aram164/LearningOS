# MASTERS-ALGO-RESOURCES — Lernbibliothek für den ⚙️ Algorithms-Block

> **Stand:** 2026-06-11 · Phase 2, Teil 4 (Achse ⚙️ aus `MASTERS-MODULE-MENU.md`: alle 8 Module)
> **Modulprofile aus den offiziellen Lehrinhalten im 888-S.-Modulkatalog.** Konvention: 🎓 Vorlesung · 📚 Buch · 📄 Paper/Skript · 🛠 Hands-on, mit Einsatz-Timing.
> **Block-Eigenheit:** 5 der 8 Module (HA, CC, RandAlgo, ParamAlgo, ADS, AE II) verantwortet **Nichterlein** (AKT-Gruppe, Niedermeier-Schule) — Haus-Spezialität: parametrisierte Algorithmik, Kernelisierung/Datenreduktion. Diese Themen tauchen in *mehreren* Modulen wieder auf; entsprechende Ressourcen amortisieren sich mehrfach. Prüfungsmix: HA + ADS schriftlich · CC, RandAlgo, ParamAlgo mündlich · AE II, MTDA Portfolio.

---

## 1. Advanced Algorithmics / Höhere Algorithmik ([#40025](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40025&version=8), 9 LP, WiSe, **Klausur**, Nichterlein)

**Modulprofil (lt. Katalog):** Moderner Algorithmenentwurf mit Fokus **„Coping with Intractability"**: algorithmische Spieltheorie, Graphalgorithmen, **Approximations- & Online-Algorithmen**, Computational Geometry, **Computational Social Choice**, verteilte Algorithmen, **parametrisierte & exakte Algorithmen**, randomisierte Algorithmen, Universal Solvers. Ein Breiten-Survey — dein Algorithmik-Fundament im Default-Plan (M1).

- 📚 **Kleinberg/Tardos, „Algorithm Design"** — das beste Lehrbuch für genau diesen Zuschnitt: NP-Härte → was nun? (Approximation Kap. 11, Randomisierung Kap. 13, Local Search) — mit den lehrreichsten Übungsaufgaben des Genres. Einsatz: Hauptbuch; die Aufgaben sind klausurnah (Technik auf neues Problem anwenden).
- 🎓 **Stanford CS261 „A Second Course in Algorithms" (Roughgarden)** — [Notes + YouTube-Videos frei](https://timroughgarden.org/notes.html). Exakt die zweite Algorithmik-Vorlesung nach dem Bachelor: LP-Dualität, Approximation, Online-Algorithmen — Roughgardens Notes sind die beste freie Vorlesungsspur zum HA-Kernstoff. Einsatz: semesterbegleitend; auf derselben Seite liegen auch seine **„Twenty Lectures on Algorithmic Game Theory"** (Buch-PDF + CS364A-Videos) für den AGT-Block.
- 🎓 **MIT 6.854 „Advanced Algorithms" (Karger)** — Notes/Videos öffentlich auffindbar (OCW + YouTube). Graduate-Breite als Ergänzung, v. a. für randomisierte Techniken. Einsatz: punktuell pro Thema, nicht linear.
- 📚 **Jeff Erickson, „Algorithms"** — [komplett frei, jeffe.cs.illinois.edu/teaching/algorithms](https://jeffe.cs.illinois.edu/teaching/algorithms/). Hervorragende freie Kapitel inkl. Erweiterungsmaterial (Randomisierung, Approximation); berühmt für didaktische Klarheit. Einsatz: Zweitdarstellung + Aufgabenquelle.
- 📚 **de Berg/Cheong/van Kreveld/Overmars, „Computational Geometry: Algorithms and Applications"** — das Standardwerk für den Geometrie-Block (Sweep, Voronoi, Triangulierung). Einsatz: nur die in der Vorlesung behandelten Kapitel.
- 📚 **Brandt et al. (Hrsg.), „Handbook of Computational Social Choice"** — [frei als PDF (Cambridge-Open)](https://www.cambridge.org/core/books/handbook-of-computational-social-choice/35B58B6F0A11B0E7DC724BA4E5B33D6D). COMSOC ist eine Spezialität der Berliner AKT-Schule — wenn der Block drankommt, ist Kapitel 1 (Introduction) die richtige Dosis. Einsatz: nur bei Vorlesungsbedarf.
- 📚 **Cygan et al., „Parameterized Algorithms"** — [frei als PDF](https://www.mimuw.edu.pl/~malcin/book/parameterized-algorithms.pdf). Für den FPT-Block in HA reichen Kap. 1–3 — und das Buch wird in ParamAlgo (§4) zum Hauptwerk. Einsatz: Investition mit Doppelnutzen, s. u.

## 2. Computational Complexity ([#40379](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40379&version=9), 9 LP, WiSe+SoSe, **mündlich**, Nichterlein)

**Modulprofil (lt. Katalog):** Strukturelle Komplexitätstheorie: Komplexitätsklassen (Zeit/Platz), Reduktionen, **NP-Vollständigkeit & P-vs-NP**, **Hierarchiesätze & Polynomielle Hierarchie**, **interaktive Beweissysteme**.

- 📚 **Arora/Barak, „Computational Complexity: A Modern Approach"** — [Entwurfs-PDF frei (Princeton)](https://theory.cs.princeton.edu/complexity/book.pdf). Deckt das Modulprofil vollständig: Hierarchiesätze (Kap. 3), PH (Kap. 5), IP (Kap. 8). Einsatz: Hauptbuch; für die mündliche Prüfung die Beweis*ideen* (Diagonalisierung, Padding, Arithmetisierung bei IP=PSPACE) frei erzählen können.
- 🎓 **Ryan O'Donnell, CMU 15-855 „Graduate Computational Complexity"** — [komplette Vorlesung auf YouTube](https://www.youtube.com/playlist?list=PLm3J0oaFux3b8Gg1DdaJOzYNsaXYLAOKH). Die beste freie Video-Vorlesung zur strukturellen Komplexität — O'Donnell ist ein herausragender Erklärer. Einsatz: Video-Spur parallel zu Arora/Barak; mündliche Prüfungen profitieren enorm vom gehörten Argument.
- 📚 **Sipser, „Introduction to the Theory of Computation"** — Teil 3 (Zeit-/Platzkomplexität) als sanfter Einstieg, falls die HU-ToC-Grundlage Lücken hat. **Brücken-Ressource** — auch relevant für den R2-Zugangscheck (12 LP TheoInf!). Einsatz: Auffrischung vor Semesterstart.
- 📚 **Papadimitriou, „Computational Complexity"** — der elegante Klassiker; manche Themen (Orakel, PH) sind hier am schönsten erzählt. Einsatz: Zweitdarstellung nach Geschmack.
- 📄 **Originale für die Prüfungskür:** Cook (1971), Karp „Reducibility Among Combinatorial Problems" (1972), Shamir „IP = PSPACE" (1992). Einsatz: mindestens Karps 21 Probleme einmal gesehen haben — Reduktionsketten sind mündlicher Prüfungsstandard.

## 3. Randomized Algorithmics ([#40667](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40667&version=8), 6 LP, WiSe+SoSe, **mündlich**, Nichterlein)

**Modulprofil (lt. Katalog):** Ressource „Zufallsbits": randomisierte Algorithmen für Graph- und Geometrieprobleme, **probabilistische Methode**, randomisierte Komplexitätsklassen (RP/BPP/ZPP).

- 📚 **Mitzenmacher/Upfal, „Probability and Computing" (2. Aufl.)** — das moderne Standardwerk: Chernoff, Balls-into-Bins, Markov-Ketten, probabilistische Methode — didaktisch zugänglicher als Motwani/Raghavan. Einsatz: Hauptbuch; Kapitel 1–6 + 13 decken den Vorlesungskern.
- 📚 **Motwani/Raghavan, „Randomized Algorithms"** — der Klassiker, stärker bei randomisierten *Algorithmen* (Min-Cut/Karger, geometrische Algorithmen, RP/BPP-Theorie). Einsatz: für die Graph-/Geometrie-Beispiele, die Mitzenmacher/Upfal knapper hält.
- 📚 **Alon/Spencer, „The Probabilistic Method"** — die Referenz zum gleichnamigen Modulblock (Lovász Local Lemma, Alterationen, Second Moment). Einsatz: nur die in der Vorlesung berührten Kapitel — das Buch ist tief; für die mündliche Prüfung reichen die Grundtechniken mit je einem Vorzeige-Beweis.
- 🎓 **MIT 6.856 „Randomized Algorithms" (Karger)** — [OCW-Notes frei](https://ocw.mit.edu/courses/6-856j-randomized-algorithms-fall-2002/). Karger lehrt hier u. a. seinen eigenen Min-Cut — Vorlesungsnotizen mit Übungen als US-Spur. Einsatz: Aufgabenquelle.
- 📄 **Karger, „Global Min-Cuts in RNC..." (Min-Cut-Paper)** + **Aussagen-Set RP/BPP/ZPP aus Arora/Barak Kap. 7** — Einsatz: Min-Cut ist *das* kanonische Prüfungsbeispiel; die Klassen-Definitionen mit Amplifikations-Argument sicher beherrschen.

## 4. Parameterized Algorithmics ([#40627](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40627&version=8), 6 LP, WiSe+SoSe, **mündlich**, Nichterlein)

**Modulprofil (lt. Katalog):** Exaktes Lösen NP-schwerer Probleme via Parameter (Lösungsgröße, Struktur): **Datenreduktion/Kernelisierung, tiefenbeschränkte Suchbäume, Color Coding, Iterative Compression, Baumzerlegungen, parametrisierte Reduktionen** — auf Graphen, Netzwerken, Strings. **Das Heimspiel-Modul der AKT-Gruppe.**

- 📚 **Cygan/Fomin/Kowalik/Lokshtanov/Marx/Pilipczuk/Pilipczuk/Saurabh, „Parameterized Algorithms"** — [frei als PDF](https://www.mimuw.edu.pl/~malcin/book/parameterized-algorithms.pdf). Das Standardwerk, dessen Kapitelstruktur (Kernelization, Bounded Search Trees, Iterative Compression, **Color Coding**, Treewidth, W-Härte) die Modulthemen wörtlich abbildet. Einsatz: Hauptbuch — die Technik-Kapitel 2–7 mit je einem durchgerechneten Beispiel pro Technik sind die komplette mündliche Prüfung.
- 📚 **Niedermeier, „Invitation to Fixed-Parameter Algorithms"** — vom Begründer der Berliner FPT-Schule (Nichterleins Doktorvater). Sanfter und beispielgetriebener als Cygan et al.; die Denkweise *dieser* Gruppe. Einsatz: als Einstieg vor dem großen Buch — wer die „Invitation" kennt, versteht, wie am Lehrstuhl argumentiert wird.
- 📚 **Downey/Fellows, „Fundamentals of Parameterized Complexity"** — die Härte-Seite (W-Hierarchie) in voller Tiefe. Einsatz: Nachschlagewerk für parametrisierte Reduktionen; nicht linear lesen.
- 🛠 **PACE Challenge** — [pacechallenge.org](https://pacechallenge.org/). Jährlicher Implementierungswettbewerb für FPT-Probleme (Treewidth, Vertex Cover, …), an dem TU-Berlin-Gruppen traditionell teilnehmen. Einsatz: eine alte PACE-Instanz + Solver anschauen verbindet dieses Modul mit AE II (§6) und macht abstrakte Kernels konkret.
- 📄 **Alon/Yuster/Zwick, „Color-Coding" (JACM 1995)** — das Originalpaper zur elegantesten Technik des Felds. Einsatz: einmal im Original lesen; Standard-Prüfungsfrage („erklären Sie Color Coding für k-Path").

## 5. Algorithmics for Discrete Data Science ([#40913](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40913&version=4), 6 LP, WiSe+SoSe, **Klausur**, Nichterlein)

**Modulprofil (lt. Katalog):** Algorithmenentwurf in **alternativen Rechenmodellen** — RAM, **Memory Hierarchy**, **Online**, **Streaming** — angewandt auf **Netzwerk-, Sequenz- und Matrix-Analyse**. Die DSE+FC-Brücke des Blocks (doppelt gelistet!) und thematisch dein bestes ⚙️↔🔧-Scharnier.

- 🎓 **Stanford CS168 „The Modern Algorithmic Toolbox" (Roughgarden/Valiant)** — [alle Notes frei](https://web.stanford.edu/class/cs168/index.html). Sketching/Streaming, Hashing, Dimensionsreduktion, Matrix-Methoden (SVD/PCA-Sicht), Graph-Spektralmethoden — kein offener Kurs passt besser auf „Algorithmik für Data Science". Einsatz: Hauptspur; pro Modulthema die passende Note.
- 📚 **Leskovec/Rajaraman/Ullman, „Mining of Massive Datasets"** — [frei, mmds.org](http://www.mmds.org/) (+ Stanford-CS246-Videos). Kapitel 3 (LSH), 4 (Streaming!), 5 (PageRank/Netzwerke), 11 (Dimensionsreduktion) — du nutzt das Buch bereits für MDS; hier zahlt es erneut. Einsatz: Doppelnutzung 🔧↔⚙️.
- 📄 **Muthukrishnan, „Data Streams: Algorithms and Applications"** — [frei (Foundations & Trends)](https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/Muthu-Survey.pdf)-artig verfügbar über Autorenseite. Die kompakte Theorie-Referenz zu Streaming-Algorithmen (Count-Min, AMS-Sketches, Heavy Hitters). Einsatz: Vertiefung des Streaming-Blocks über MMDS-Niveau hinaus.
- 📄 **Demaine, „Cache-Oblivious Algorithms and Data Structures" (Survey)** — [frei (MIT)](https://erikdemaine.org/papers/BRICS2002/paper.pdf). Die Memory-Hierarchy-Hälfte: I/O-Modell, cache-oblivious B-Trees/Sorting. Einsatz: für den Memory-Hierarchy-Block — und konzeptionelle Brücke zu DMH (🔧/🚀), wo dieselben Ideen praktisch werden.
- 📚 **Gusfield, „Algorithms on Strings, Trees, and Sequences"** — das Referenzwerk für den Sequence-Analysis-Teil (Suffix-Strukturen, Alignment). Einsatz: nur die vorlesungsrelevanten Kapitel.
- 📚 **Easley/Kleinberg, „Networks, Crowds, and Markets"** — [frei als PDF (Cornell)](https://www.cs.cornell.edu/home/kleinber/networks-book/). Für den Network-Analysis-Teil (Zentralität, Communities, Kaskaden) die lesbarste Quelle. Einsatz: Auswahl-Kapitel.

## 6. Algorithm Engineering II ([#40320](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40320&version=13), 9 LP, **Turnus unregelmäßig ⚠**, **Portfolio**, Nichterlein, max 15)

**Modulprofil (lt. Katalog):** **Design–Analyse–Implementierung–Test-Zyklus** für (v. a. NP-schwere) Probleme: Beschleunigung durch Architektur-Ausnutzung, Problemmodellierung, DP/Suchbäume/**Datenreduktion**, exakt/approximativ/heuristisch, **LP-Solver-Einsatz**. Empirische Algorithmik = deine 📊-Achse in ⚙️-Gestalt.

- 📚 **Sanders/Mehlhorn/Dietzfelbinger/Dementiev, „Sequential and Parallel Algorithms and Data Structures: The Basic Toolbox"** — [frei als PDF (KIT/Autoren-Seite)](https://people.mpi-inf.mpg.de/~mehlhorn/Toolbox.html). Die Karlsruher AE-Schule in Buchform: Algorithmen *mit* Implementierungs- und Architekturblick (Caches, Parallelität). Einsatz: Haupttext für die Engineering-Denkweise.
- 📚 **McGeoch, „A Guide to Experimental Algorithmics"** — **die** Methodik-Referenz für saubere Algorithmen-Experimente: Instanzwahl, Messung, Varianzkontrolle, Reporting. Einsatz: vor dem Portfolio lesen — und wörtlich wiederverwendbar für CSB, ROC und deine Thesis-Evaluation (📊-Brücke!).
- 🛠 **PACE Challenge** (s. §4) + **DIMACS Implementation Challenges** — reale Benchmark-Instanzen + Vergleichs-Solver. Einsatz: Portfolio-Material; eine PACE-Aufgabe ist praktisch ein vorgefertigtes AE-II-Projekt.
- 🛠 **LP/ILP-Solver-Praxis:** Gurobi (akademische Gratis-Lizenz) oder HiGHS (Open Source) + die Modellierungs-Tutorials von Gurobi. Das Modulprofil nennt „etablierte Solver" explizit. Einsatz: ein NP-schweres Problem einmal als ILP modellieren und gegen eigene Heuristik benchmarken — genau der Portfolio-Dreiklang.
- 📚 **Bentley, „Programming Pearls"** — kurz, alt, unsterblich: die Engineering-Haltung (Messen! Back-of-envelope!) auf 200 Seiten. Einsatz: Wochenendlektüre vor Projektstart.
- ⚠ **Planungshinweis:** Turnus „unregelmäßig" — vor Einplanung per Moses-Link prüfen, ob das Modul im Zielsemester überhaupt läuft (Regel §4.6 im MODULE-MENU).

## 7. Logik, Spiele, Automaten ([#40545](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40545&version=3), 9 LP, WiSe+SoSe, **mündlich**, Kreutzer)

**Modulprofil (lt. Katalog):** Theoretische Grundlagen für Entwurf/**Verifikation reaktiver Systeme**: Automatentheorie (auf unendlichen Wörtern), logische Systeme, **unendliche Zwei-Personenspiele** — und ihre Zusammenhänge (Büchi/Parity/μ-Kalkül-Dreieck), mit algorithmischen Anwendungen im Systementwurf.

- 📚 **Grädel/Thomas/Wilke (Hrsg.), „Automata, Logics, and Infinite Games" (LNCS 2500)** — der kanonische Text, dessen Titel das Modul fast wörtlich trägt: Büchi-/Parity-Automaten, S1S, Spiele, Determinisierung (Safra). Einsatz: Hauptreferenz; Kreutzer kommt aus genau dieser (Grädel-)Schule.
- 📄 **Erich Grädel, Vorlesungsskripte „Automata, Games and Logic" / „Algorithmic Model Theory"** — [frei auf der RWTH-Logik-Seite](https://logic.rwth-aachen.de/Teaching/index.html.en). Druckreife deutsche/englische Skripte exakt zu diesem Vorlesungstyp. Einsatz: die beste freie Lernspur — kompakter als der LNCS-Band.
- 📚 **Baier/Katoen, „Principles of Model Checking"** — die Anwendungsseite (LTL/CTL, Model Checking reaktiver Systeme), auf die das Modulprofil zielt. Einsatz: für den Verifikations-Block; Kapitel zu LTL→Büchi ist der Scharnier-Stoff.
- 📄 **Thomas, „Languages, Automata, and Logic" (Handbook-Kapitel)** — das klassische 60-Seiten-Survey über die Logik↔Automaten-Korrespondenzen. Einsatz: Vorab-Landkarte; danach hat jeder Vorlesungsteil seinen Platz.
- 🛠 **Spot / owl (Automaten-Bibliotheken)** + **Parity-Game-Solver (z. B. Oink)** — Einsatz: optional; ein LTL→Büchi-Übersetzer einmal laufen lassen macht Safra & Co. greifbar.

## 8. Models and Theory of Distributed Algorithms ([#41225](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41225&version=1), 9 LP, WiSe, **Portfolio**, Nestmann, max 15)

**Modulprofil (lt. Katalog):** Projektförmig: Kapitel eines **bekannten Lehrbuchs über verteilte Algorithmen formalisieren** (bis hin zu theorembeweiser-prüfbaren Beweisen). Inhalte: synchrone/asynchrone Kommunikation, Prozess-/Fehlermodelle, **Leader Election, Consensus**.

- 📚 **Lynch, „Distributed Algorithms"** — *das* „bekannte Lehrbuch" des Felds (synchron/asynchron, Fehlermodelle, Leader Election, Consensus — die Modulliste ist ihre Kapitelfolge). Einsatz: Hauptbuch; die zu formalisierenden Kapitel kommen mit hoher Wahrscheinlichkeit hierher (Alternative: Attiya/Welch, „Distributed Computing").
- 📚 **Fokkink, „Distributed Algorithms: An Intuitive Approach" (MIT Press)** — kompakte, beweisfreundliche Zweitdarstellung derselben Algorithmen. Einsatz: wenn Lynch zu enzyklopädisch wird.
- 📄 **FLP: Fischer/Lynch/Paterson, „Impossibility of Distributed Consensus with One Faulty Process" (JACM 1985)** + **Lamport, „Time, Clocks, and the Ordering of Events" (CACM 1978)** + **Lamport, „Paxos Made Simple"** — die drei Texte, um die jedes Consensus-Kapitel kreist. Einsatz: vor dem Consensus-Teil; FLP-Beweisstruktur verstehen ist der Kern des Moduls.
- 🛠🎓 **TLA+ (Lamport)** — [Video-Kurs + Hyperbook frei](https://lamport.azurewebsites.net/video/videos.html). Spezifikation und maschinengeprüfte Argumente für verteilte Algorithmen — exakt die im Modulprofil angedeutete Theorembeweiser-Perspektive, vom Turing-Preisträger selbst gelehrt. Einsatz: Leader Election oder ein Consensus-Protokoll einmal in TLA+ spezifizieren — ideales Portfolio-Artefakt. (Nestmanns Gruppe arbeitet eher mit Isabelle — im Kurs klären, welches Werkzeug erwartet wird.)
- 🎓 **MIT 6.824 „Distributed Systems"** (s. `MASTERS-DATAENG-RESOURCES.md` §9) — die *praktische* Gegenwelt (Raft implementieren statt beweisen). Einsatz: optionaler Kontrast; verbindet dieses Theorie-Modul mit deiner Systems-Achse.

## 9. Algorithms for Distributed Systems ([#41127](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41127&version=3), 6 LP, SoSe, schriftlich, Schmid) / Algorithms for Networked Systems ([#41126](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41126&version=2), 6 LP, SoSe, schriftlich, Schmid)

**Modulprofil (lt. Katalog):** **#41127** — Modelle für Distributed Systems (Shared-Memory → Datacenter → Internet-scale), algorithmische Techniken (Shared-Memory + **verteilte Graph-Algorithmen**), Dezentralisierung. **#41126** — Netzwerk-Modelle (Datacenter/Sensor/Wireless/Mobile), **robuste Topologie (self-stabilizing/self-optimizing)**, Randomisierung, lokale Algorithmen. Schmids 3S-Gruppe; der **algorithmische Einstieg** in Distributed/Networked Systems (ergänzt MTDA §8, das eher Konsens-Theorie macht).

- 📚 **Lynch / Fokkink / Attiya-Welch** (s. §8) — die Grundlagenbücher tragen auch diese Module; der §8-Kanon (FLP, Lamport) deckt den Distributed-Systems-Teil von #41127. Einsatz: gemeinsame Basis.
- 📚 **Cachin/Guerraoui/Rodrigues, „Introduction to Reliable and Secure Distributed Programming"** — Broadcast/Consensus/Replication abstraktionsorientiert; die moderne Brücke Theorie ↔ System. Einsatz: für die Datacenter-/Internet-scale-Modelle von #41127.
- 📄 **Self-Stabilization:** Dijkstra, „Self-stabilizing Systems in Spite of Distributed Control" (CACM 1974) + Dolev, „Self-Stabilization" (MIT Press) — exakt der „self-stabilizing/self-optimizing networks"-Block von #41126. Einsatz: Pflicht für #41126.
- 📄 **Schmids Forschung (self-adjusting/demand-aware networks)** — seine SIGCOMM/INFOCOM-Arbeiten zu selbstoptimierenden Netzen. Einsatz: die Forschungsfront, aus der die #41126-Inhalte stammen — vom Dozenten.
- 📚 **Suomela, „Survey of Local Algorithms" (ACM CSUR 2013)** — der LOCAL/CONGEST-Einstieg (verteilte Graph-Algorithmen). Einsatz: für den Local-Algorithms-Teil.
- 🛠 **TLA+ / MIT 6.824** (s. §8) — Spezifikation bzw. Praxis (Raft), doppelt nutzbar.
- **Cross:** ergänzt **MTDA #41225 (§8)**; die Datacenter-Modelle berühren **Cloud Computing / Datacenter Networking** (DSN-Annex) und die 📊-Mess-Methodik (Schmids Internet-Measurement-Modul).

## 10. AKT-Forschungsmodule (Nichterlein): Current Research in Algorithms and Complexity ([#40394](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40394&version=8)) · Research Colloquium ([#40685](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40685&version=10))

**Modulprofil:** Betreute Literatur-/Forschungsarbeit bzw. Kolloquium der AKT-Gruppe — **kein fester Stoff**, sondern aktuelle Papers (Status benotet/unbenotet in MTS prüfen). Sinnvoll, wenn du Richtung algorithmische Forschung/PhD denkst.

- 📄 **Venues:** ESA, SODA, ICALP, STACS, **IPEC** (Parameterized) — die AKT-Publikationsorte; daraus Exposé/Vortragsthema wählen. Einsatz: ein aktuelles Paper der Nichterlein-Gruppe als Aufhänger.
- 🎓 **Paper-Reading:** Keshav, „How to Read a Paper" (s. `MASTERS-DATAENG-RESOURCES.md`) + die §1–§6-Bücher als Hintergrund. Einsatz: Vortragsvorbereitung.
- **Cross:** inhaltliche Fortsetzung von **HA/ParamAlgo/AE II** — gleiche Schule (Nichterlein prüft alle).

---

## Querverbindungen (so verzahnt sich der ⚙️-Block)

1. **AKT-Kanon zuerst:** Cygan et al. (frei) + Niedermeiers „Invitation" tragen ParamAlgo komplett, den FPT-Block von HA und die Datenreduktions-Denkweise von AE II — drei Module, zwei Bücher, eine Schule (Nichterlein prüft alle drei).
2. **ADS ist das Scharnier:** Streaming (→ MDS/MMDS, 🔧), Memory Hierarchy (→ DMH, 🚀), Matrix-Methoden (→ ML-Block) — als DSE+FC-doppelgelistetes Modul auch bucket-taktisch das flexibelste Stück der Achse.
3. **AE II + McGeoch = 📊-Vorschule:** experimentelle Algorithmik ist methodisch identisch mit CSB/ROC/Thesis-Evaluation. Einmal Messmethodik lernen, vierfach ernten.
4. **Theorie-Paar mit Nestmann/Kreutzer:** LSA (Spiele/Automaten) und MTDA (Formalisierung) sind die FC-lastigsten Wahlmöglichkeiten — beide belohnen Beweis-Sorgfalt, beide harmonieren mit TPS/Lambda-Kalkül (🚀-PL-Schiene) zur „formalen Säule" deines Profils.
5. **Mündlich-Cluster:** CC, RandAlgo, ParamAlgo (+ TPS, Lambda, MathML, FoSP, ADM) sind mündlich — gut stapelbar neben einer Klausur, aber nicht drei mündliche Theorie-Prüfungen in dieselbe Prüfungswoche legen.
6. **Kostenlos-Quote:** Cygan, Erickson, Roughgarden (Notes+AGT), Arora/Barak, O'Donnell-Videos, CS168, MMDS, Muthukrishnan, Demaine, Easley/Kleinberg, Sanders-Toolbox, Grädel-Skripte, TLA+-Kurs — der Block ist fast vollständig frei studierbar.

> **Pflege:** AE-II-Turnus („unregelmäßig") und CMU/Stanford-Jahrgangs-URLs vor Einplanung prüfen; tote Links hier korrigieren.

---

## Mega-Sweep-Nachtrag (2026-06-11): Übungen, Klausuren & Code-Repos

### Übungsblätter & Klausuren anderer Unis

- 📝 **MIT OCW 6.046J „Design and Analysis of Algorithms" (aus deinem Ultimate-Index)** — [ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2015](https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2015/): komplette Psets + **Exams mit Lösungen** — das beste freie HA-Klausurtraining (Randomisierung, Approximation, Flows). Dazu [6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) als Grundlagen-Sicherung.
- 📝 **O'Donnell 15-855: Homeworks** — auf der CMU-Kursseite zu den YouTube-Lectures liegen Problem Sets — Komplexitäts-Übungen auf genau dem CC-Prüfungsniveau.
- 📝 **Cygan et al.: Buchübungen + Hints** — das freie FPT-Buch enthält pro Kapitel Übungen mit Schwierigkeitsgraden und Hinweisen — die ParamAlgo-Übungsblätter sind faktisch mitgeliefert.
- 📝 **Kleinberg/Tardos „Solved Exercises"** — jedes Kapitel beginnt mit vollständig vorgerechneten Aufgaben — als Muster für die HA-Klausur-Argumentationsform („beschreibe Algorithmus, beweise Korrektheit, analysiere Laufzeit").
- 📝 **Stanford CS161/CS261-Psets (Roughgarden-Ökosystem)** — öffentlich auf [timroughgarden.org](https://timroughgarden.org/) verlinkt; CS261-Aufgaben decken Approximation/Online ab.

### Praxis-Training (aus deinem Ultimate-Index integriert)

- 🛠 **CP-Algorithms** — [cp-algorithms.com](https://cp-algorithms.com/): Implementierungs-Referenz für praktisch jeden HA-Algorithmus (Flows, Matching, Segment-Strukturen) mit Codebeispielen — die Brücke von Beweis zu Code.
- 🛠 **Open Data Structures** — [opendatastructures.org](https://opendatastructures.org/): freies Buch + Code; Auffrischung der Datenstruktur-Basis unter HA/ADS.
- 🛠 **Exercism + Project Euler** — Dauer-Fingerübungen; für ⚙️ besonders die Euler-Graphenprobleme.
- 🛠 **Codeforces/AtCoder (Ergänzung)** — wenn Wettkampf-Training motiviert: Div-2-Probleme sind HA-Klausuraufgaben unter Zeitdruck.

### Open-Source-Repos & Wettbewerbe

- 🛠 **PACE-Challenge-Siegersolver** — über [pacechallenge.org](https://pacechallenge.org/) je Jahr verlinkt (z. B. Treewidth-/Vertex-Cover-Solver): lesbarer FPT-Code im Wettbewerbszustand — verbindet ParamAlgo mit AE II.
- 🛠 **KaHIP / KaMIS (Karlsruhe)** — [github.com/KaHIP](https://github.com/KaHIP): Graphpartitionierung/Independent Sets in Algorithm-Engineering-Qualität — Vorzeige-Repos dafür, wie man Algorithmik-Code strukturiert, testet und benchmarkt (AE-II-Vorbild).
- 🛠 **NetworKit** — [github.com/networkit/networkit](https://github.com/networkit/networkit): skalierbare Netzwerkanalyse (ADS-Domäne „Network Analysis") — Algorithmen aus der Vorlesung im Produktionszustand.
- 🛠 **TLA+ Examples** — [github.com/tlaplus/Examples](https://github.com/tlaplus/Examples): spezifizierte verteilte Algorithmen (inkl. Paxos) als MTDA-Portfolio-Vorlagen.

> Einordnung Ultimate-Index: „Competitive Programmer's Core Skills" und Mines-Télécom-Graphenkurs sind unter HA-Niveau — übersprungen; 6.042J (Beweistechnik) ist in der 🧮-Datei verankert und trägt auch CC.
