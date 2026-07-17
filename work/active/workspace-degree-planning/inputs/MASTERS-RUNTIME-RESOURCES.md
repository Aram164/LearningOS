# MASTERS-RUNTIME-RESOURCES — Lernbibliothek für den 🚀 Runtime/Optimizer/PL-Block

> **Stand:** 2026-06-11 · Phase 2, Teil 5 (Achse 🚀 aus `MASTERS-MODULE-MENU.md`: TPS, Compiling Techniques, Compiler Design, Lambda-Kalkül; Cross-Tags DBTLAB/DMH/MLMMI → bereits in `MASTERS-DATAENG-RESOURCES.md`)
> **Modulprofile aus den offiziellen Lehrinhalten im 888-S.-Modulkatalog.** Konvention: 🎓 Vorlesung · 📚 Buch · 📄 Paper/Skript · 🛠 Hands-on, mit Einsatz-Timing.
> **Warum diese Achse deine wichtigste ist:** Stratum = Rewrites über DAG-IRs + symbolische Selektoren. Compiler-IRs, Rewrite-Systeme und Typdisziplin sind die akademische Sprache deiner Job-Arbeit — und Steuwer (TPS + Compiling Techniques) forscht **exakt** an Rewrite-basierten Compilern. Diese Achse verbindet Vorlesung, Job und Thesis enger als jede andere.

---

## 1. TPS — Types and Programming Languages ([#41202](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41202&version=1), 6 LP, WiSe, **mündlich**, Steuwer, max 24)

**Modulprofil (lt. Katalog):** **Lambda-Kalkül** (Syntax, operationale Semantik), **einfach getypter & polymorpher Lambda-Kalkül (Lambda-Würfel)**, algebraische Datentypen (Summen-/Produkttypen), **Curry-Howard-Korrespondenz**, Anwendung von Typsystemen; fortgeschritten ggf. **dependent/linear/row types**.

- 📚 **Pierce, „Types and Programming Languages" (TAPL)** — **das Modul trägt den Buchtitel.** Operationale Semantik, STLC, System F, ADTs, Subtyping — die mündliche Prüfung wird in TAPL-Notation geführt werden. Einsatz: Hauptbuch; Kapitel 3–11 + 23 (System F) gründlich, mit Progress/Preservation-Beweisen zum Selbst-Erzählen.
- 📚🛠 **Pierce et al., „Software Foundations" (Band 1–2)** — [komplett frei](https://softwarefoundations.cis.upenn.edu/). TAPL-Stoff als interaktive Coq-Skripte — jeder Beweis wird maschinell geprüft, Fehler fliegen sofort auf. Einsatz: parallel zu TAPL; eine Stunde Coq pro Woche verankert Typregeln tiefer als jedes Wiederholungslesen.
- 📚🛠 **Wadler/Kokke/Siek, „Programming Language Foundations in Agda" (PLFA)** — [frei, plfa.github.io](https://plfa.github.io/). Dieselbe Theorie in Agda — moderner, schlanker als Coq; und Agda ist die im Schwestermodul (§4) explizit genannte Sprache. Einsatz: Alternative zu Software Foundations nach Geschmack; eines von beiden reicht.
- 📄 **Wadler, „Propositions as Types" (CACM 2015)** — [frei (Autoren-Seite)](https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf) + sein berühmter Vortrag dazu (YouTube). Curry-Howard als Erzählung — die schönste Vorbereitung auf die entsprechende Prüfungsfrage. Einsatz: ein Abend, bleibender Eindruck.
- 🎓 **OPLSS — Oregon Programming Languages Summer School** — [Videoarchiv frei](https://www.cs.uoregon.edu/research/summerschool/archives.html). Jahrzehnte an Vorlesungsreihen zu Typtheorie, Curry-Howard, dependent types von den Größen des Felds (Pierce, Harper, Wadler …). Einsatz: à la carte für die Advanced Topics (dependent/linear types).
- 📄 **Steuwers eigene Forschung als Kontext:** „RISE & Shine" / **„Achieving High-Performance the Functional Way" (ELEVATE, ICFP 2020)** — funktionale IRs + **Rewrite-Strategien** für Performance-Compiler ([Publikationsliste](https://steuwer.info/)). **Das ist konzeptionell Stratum in PL-Gestalt.** Einsatz: vor der mündlichen Prüfung lesen — du kannst das Gespräch auf das Forschungsgebiet des Prüfers lenken und hast mit deiner DEEM-Arbeit echtes Material dafür.

## 2. Compiling Techniques ([#41162](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41162&version=1), 6 LP, SoSe, **Portfolio**, Steuwer)

**Modulprofil (lt. Katalog):** **Kompletten Compiler from scratch bauen** (Kursprojekt, reale Zielarchitektur ARM/MIPS/RISC-V): Lexing, Parsing (LR), AST, semantische Analyse, **Zwischendarstellungen + SSA**, **Liveness/Datenflussgleichungen**, Befehlsauswahl, **Registerallokation (Colouring by Simplification, Coalescing)**; fortgeschritten: automatische Parallelisierung, GCC/LLVM/**MLIR**. Steuwers SoSe-Komplement zu TPS.

- 📚 **Appel, „Modern Compiler Implementation in ML" (bzw. Java/C)** — die Modulgliederung folgt diesem Buch fast wörtlich („colouring by simplification", „coalescing" sind Appels Kapitelvokabular — er hat Compiling Techniques in Edinburgh geprägt, wo Steuwer den Kurs übernahm). Einsatz: Hauptbuch zum Projekt; pro Compiler-Phase das Kapitel **vor** dem Implementieren lesen.
- 🎓 **Cornell CS 6120 „Advanced Compilers" (Adrian Sampson)** — [komplett frei als Self-Guided Course mit Videos](https://www.cs.cornell.edu/courses/cs6120/2020fa/self-guided/). SSA, Datenflussanalyse, LLVM — moderne, praxisnahe Behandlung exakt der zweiten Modulhälfte; mit Übungs-Ökosystem (Bril-IR). Einsatz: begleitend ab IR/SSA-Phase; die beste freie Quelle für Datenfluss-Intuition.
- 🛠 **LLVM „Kaleidoscope"-Tutorial + MLIR „Toy"-Tutorial** — [llvm.org/docs/tutorial](https://llvm.org/docs/tutorial/) · [mlir.llvm.org/docs/Tutorials/Toy](https://mlir.llvm.org/docs/Tutorials/Toy/). Einen Mini-Compiler auf realer Infrastruktur bauen; **MLIR ist das Industrie-Gegenstück zu Stratums Multi-Level-DAG-Rewriting** (Dialekte, Pattern-Rewrites, Lowering). Einsatz: das Toy-Tutorial komplett — es ist die direkteste Brücke zwischen diesem Modul und deiner Job-Arbeit.
- 📚 **Cooper/Torczon, „Engineering a Compiler" (3. Aufl.)** — die modernere Alternative zum Drachenbuch: stark bei SSA, Instruction Selection, Registerallokation. Einsatz: Zweitreferenz, wenn Appel zu ML-lastig ist.
- 📚 **Nystrom, „Crafting Interpreters"** — [komplett frei, craftinginterpreters.com](https://craftinginterpreters.com/). Lexer→Parser→Bytecode-VM in zwei Durchgängen, herausragend geschrieben. Einsatz: Warm-up **vor** Semesterstart, falls du noch nie einen Parser gebaut hast — danach fühlt sich das Kursprojekt halb so groß an.
- 📄 **Cytron et al., „Efficiently Computing Static Single Assignment Form…" (TOPLAS 1991)** + **Chaitin, „Register Allocation & Spilling via Graph Coloring" (1982)** — die zwei Originale hinter den zwei schwersten Projektphasen. Einsatz: jeweils vor der Phase; Portfolio-Berichte gewinnen durch Originalzitate.

## 3. Compiler Design ([#40197](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40197&version=3), 6 LP, WiSe, **Portfolio**, Juurlink, max 40, ESCA)

**Modulprofil (lt. Katalog):** Compiler-Phasen klassisch (Lexing, Parsing, Typen/Typprüfung, Zwischensprachen, **Datenflussanalyse, Programmoptimierung**, Codegenerierung, **Runtime-Systeme**) **+ parallelisierende Compiler** und aktuelle Entwicklungen. Juurlink ist Rechnerarchitekt (AES/Embedded) — der Kurs denkt von der Maschine her; die WiSe-Alternative, falls Compiling Techniques (SoSe) nicht in den Plan passt.

- 📚 **Aho/Lam/Sethi/Ullman, „Compilers: Principles, Techniques, and Tools" (Drachenbuch, 2. Aufl.)** — für *diesen* klassisch geschnittenen Kurs die passende Referenz; die Lam-Kapitel (11–12) zu Parallelisierung/Lokalität decken den besonderen Modulfokus. Einsatz: Referenz pro Phase; Kapitel 9 (Datenfluss) und 11 (parallelisierende Compiler) sind hier die wichtigsten.
- 📚 **Allen/Kennedy, „Optimizing Compilers for Modern Architectures"** — *das* Buch zu **parallelisierenden Compilern** (Dependence Analysis, Loop-Transformationen, Vektorisierung) — exakt das Alleinstellungsmerkmal dieses Moduls gegenüber §2. Einsatz: für den Parallelisierungs-Block; verbindet direkt zu DMH (SIMD!) aus dem 🔧/🚀-Cross-Tag.
- 📚 **Muchnick, „Advanced Compiler Design and Implementation"** — Tiefenreferenz für klassische Optimierungen (SSA-Optimierungen, Scheduling). Einsatz: Nachschlagen bei Portfolio-Optimierungsaufgaben.
- 🎓 **Cornell CS 6120** (s. §2) — trägt auch hier; identischer Stoffkern. Einsatz: Video-Spur.
- 📄 **Lattner/Adve, „LLVM: A Compilation Framework…" (CGO 2004)** + **Lattner et al., „MLIR: Scaling Compiler Infrastructure for Domain Specific Computation" (CGO 2021)** — die zwei Infrastruktur-Papers, die „recent advances" im Modulprofil konkret machen. Einsatz: fürs Portfolio-Diskussionskapitel; MLIR erneut = Stratum-Brücke.

## 4. Lambda-Kalkül und Typ-Systeme ([#40826](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40826&version=5), 6 LP, WiSe, **mündlich**, Nestmann, max 25)

**Modulprofil (lt. Katalog):** Lambda-Kalkül als Berechnungsmodell (Syntax, Konversion, Auswertung), **einfach getypter & polymorpher LK, abhängige Typen, Lambda-Würfel, Curry-Howard**; optional abstrakte Maschinen, **Haskell/Agda**-Anwendungen. ⚠ **Starke Überschneidung mit TPS (§1)** — gleiche Theorie, formaler/logischer Zuschnitt (Nestmann) statt PL/Compiler-Zuschnitt (Steuwer). Beide WiSe, beide mündlich: **eines wählen**, nicht beide.

- 📄 **Selinger, „Lecture Notes on the Lambda Calculus"** — [frei auf arXiv](https://arxiv.org/abs/0804.3434). ~100 Seiten druckreifes Skript: Konversion, Konfluenz (Church-Rosser), Typisierung — exakt der Vorlesungskern, kostenlos. Einsatz: Erstlektüre; die Church-Rosser-Beweisskizze mündlich erzählen können.
- 📚 **Pierce, TAPL** (s. §1) — trägt auch dieses Modul (STLC, System F, Lambda-Würfel-Einordnung). Einsatz: gemeinsame Investition für §1/§4 — ein Buch, zwei Modulkandidaten.
- 📚 **Sørensen/Urzyczyn, „Lectures on the Curry-Howard Isomorphism"** — die Tiefenreferenz zum Herzstück des Moduls (Logik ↔ Berechnung, bis zu abhängigen Typen und Lambda-Würfel). Einsatz: für den Curry-Howard-/Lambda-Kubus-Block; formaler als TAPL, passend zum Nestmann-Stil.
- 📄 **Barendregt, „Lambda Calculi with Types" (Handbook-Kapitel)** — frei auffindbares Standard-Survey; der Lambda-Würfel stammt von Barendregt selbst. Einsatz: Originalquelle für die Würfel-Prüfungsfrage.
- 🛠 **Haskell + Agda praktisch:** Hutton, „Programming in Haskell" (kompakt) bzw. [Learn You a Haskell (frei)](https://learnyouahaskell.github.io/) · Agda über **PLFA** (s. §1). Das Modulprofil nennt beide Sprachen. Einsatz: kleine Beispiele selbst tippen (ADTs, Polymorphie, ein dependent-typed Vektor in Agda) — mündliche Prüfungen lieben „zeigen Sie an einem Beispiel".

## 5. GPU Computing ([#41201](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41201&version=2), 6 LP, WiSe+SoSe, Portfolio, Steuwer, max 30)

**Modulprofil (lt. Katalog):** Modernes GPU-Computing für rechenintensive/datenparallele Probleme: moderne GPU-Hardware, **Throughput- vs. Latency-oriented Computing**, Schreiben von High-Performance-GPU-Software (CUDA). Das **dritte Steuwer-Modul** (TPS → Compiling Techniques → GPU) — die Accelerator-Seite der Stratum-IR-Achse.

- 📚 **Kirk/Hwu, „Programming Massively Parallel Processors (PMPP)" (4. Aufl.)** — das Standardbuch für CUDA/GPU-Programmierung: Speicherhierarchie, Parallelitätsmuster, Performance-Tuning. Einsatz: Hauptbuch.
- 🎓 **GPU MODE Lecture Series** — [github.com/gpu-mode/lectures](https://github.com/gpu-mode/lectures) + YouTube — moderne Kernel-/Performance-Vorträge (Triton, FlashAttention, Profiling). Einsatz: semesterbegleitend; direkte Brücke zu deiner ML-Systems-Achse.
- 📄 **NVIDIA CUDA C++ Programming Guide + Best Practices Guide** — die Primärreferenz. Einsatz: Nachschlagewerk fürs Portfolio-Projekt.
- 🛠 **Triton** ([triton-lang.org](https://triton-lang.org/)) — GPU-Kernel in Python; **direkter Steuwer/MLIR-Bezug** (ELEVATE/RISE-Linie → Kernel-Generierung). Einsatz: der Brückenschlag GPU ↔ Compiler (TPS/CT) ↔ Stratum.
- 📄 **Horace He, „Making Deep Learning Go Brrrr From First Principles"** — Memory- vs. Compute-bound, Operator-Fusion intuitiv. Einsatz: das „throughput vs. latency"-Mentalmodell des Moduls verankern.
- **Cross:** überlappt mit **DMH** (Hardware-Performance), **MLMMI** (Inference-Runtime) und dem **Frontier-Lab-Delta** (GPU/Kernel-Pfad, unten) — einmal lernen, mehrfach nutzen.

## 6. Intro into Interactive Theorem Proving ([#40416](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40416&version=4), 3 LP, SoSe, mündlich, Nestmann, Blockveranstaltung, max 20)

**Modulprofil (lt. Katalog):** **Higher-Order Logic (HOL)**, Isabelle-Syntax, Beweisstrategien, **Induktion/Co-Induktion**, Theorien in Isabelle/HOL, **deep vs. shallow Embeddings**. Nestmanns Werkzeug-Modul — die maschinengeprüfte Ergänzung zu Lambda-Kalkül (§4); für Stratum relevant als Korrektheitsbeweis von IR-Transformationen.

- 📚 **Nipkow/Klein, „Concrete Semantics with Isabelle/HOL"** — [frei: concrete-semantics.org](http://concrete-semantics.org/) — DAS Isabelle-Lehrbuch (vom Isabelle-Mitentwickler Nipkow); Teil I lehrt Isabelle/HOL genau auf Modulniveau, Teil II wendet es auf Programmiersprachen-Semantik an. Einsatz: Hauptbuch — Teil I komplett vor der Blockveranstaltung durcharbeiten.
- 🎓 **Isabelle-Tutorials** ([isabelle.in.tum.de](https://isabelle.in.tum.de/) — „Prog-Prove" + „Tutorial on Isabelle/HOL") — Einsatz: Hands-on parallel; die mündliche Prüfung verlangt Beweise live.
- 📄 **deep vs. shallow embeddings** — Nipkows Embedding-Notizen / Standard-Survey. Einsatz: für den im Profil explizit genannten Embedding-Block.
- 🛠 **Alternativ-Beweiser zum Querlesen:** „Software Foundations" (Coq) + „Theorem Proving in Lean 4" — dieselben Ideen in anderer Syntax. Einsatz: optional; Isabelle bleibt Pflicht (Nestmanns Werkzeug).
- **Cross:** direkt an **Lambda-Kalkül (§4)** (Curry-Howard) und an **MTDA** (`MASTERS-ALGO-RESOURCES.md` §8, TLA+/Isabelle-Beweise verteilter Algorithmen) angebunden.

---

## Querverbindungen (so verzahnt sich der 🚀-Block)

1. **Die Steuwer-Linie ist deine Thesis-Rampe:** TPS (WiSe, Theorie) → Compiling Techniques (SoSe, Praxis) → ELEVATE/RISE-Papers → MLIR-Tutorial → Stratum-Rewrites. Kein anderer Modulpfad zahlt so direkt auf deine DEEM-Arbeit und das Thesis-Framing („rule-based optimizer infrastructure") ein.
2. **TPS vs. Lambda-Kalkül entscheiden:** ~70 % Stoffüberlappung, beide WiSe/mündlich. Default: **TPS** (Steuwer-Beziehung + Anwendungsfokus + Stratum-Fit). Lambda-Kalkül nur, wenn der Termin kollidiert oder du die Logik-Seite (Curry-Howard formal, Agda) bevorzugst — dann trägt TAPL trotzdem.
3. **Compiler Design vs. Compiling Techniques:** CD (WiSe, Juurlink, architektur-/parallelisierungslastig) ist die Ausweichoption, CT (SoSe, Steuwer, from-scratch-Projekt) die profilbildende Wahl. Wer beide nimmt, lernt einmal Phasen-Theorie und einmal Engineering — vertretbar, aber 12 LP für einen Themenkreis.
4. **Cross-Tags einsammeln:** DBTLAB (Query-Engine = Compiler für Anfragepläne), DMH (SIMD/Lokalität = das, was parallelisierende Compiler erzeugen), MLMMI/AMLS Lecture 03–04 (Rewrites, Operator Fusion = Compiler-Optimierung über ML-DAGs) — die 🚀-Achse ist der theoretische Unterbau von allem dreien.
5. **Werkzeug-Investition:** Coq *oder* Agda (eines reicht), dazu einmal MLIR-Toy — zusammen ~3 Wochenenden, Ertrag in 4+ Modulen und der Thesis.

> **Pflege:** Steuwers TU-Kursseiten ([Fachgebiet COMPL](https://www.tu.berlin/en/compl)) bei Modulstart auf veröffentlichte Materialien prüfen (sein Edinburgh-Vorgängerkurs hatte öffentliche Traditionen); LLVM/MLIR-Tutorial-URLs sind stabil.

---

## Mega-Sweep-Nachtrag (2026-06-11): Übungen, Klausuren & Code-Repos

### Übungsblätter, Projekte & Klausurersatz anderer Unis

- 📝 **Software Foundations = maschinengeprüfte Übungsblätter** — (s. §1) jedes Kapitel besteht aus Coq-Übungen mit automatischer Korrektur — für TPS/Lambda gibt es kein besseres „Übungsblatt mit Lösung", weil der Beweisassistent die Lösung verifiziert.
- 📝 **Stanford CS143: Assignments (Cool-Compiler)** — [web.stanford.edu/class/cs143](https://web.stanford.edu/class/cs143/): vier Programmierprojekte (Lexer→Parser→Semant→Codegen) mit Skeleton + Tests, dazu Midterm/Final-Archive **mit Lösungen** auf den Jahrgangsseiten — Klausur- und Projekttraining für Compiling Techniques/Compiler Design.
- 📝 **MIT OCW 6.035 „Computer Language Engineering"** — komplette Projektspezifikationen (Decaf-Compiler) + Quizzes — die amerikanische Vollversion des CT-Kursprojekts.
- 📝 **Cornell CS 6120: Tasks** — (s. §2) die „Lessons" enthalten Implementierungsaufgaben auf der Bril-IR mit Community-Lösungen im Repo — Datenfluss/SSA-Übungen mit Vergleichsmaterial.

### Open-Source-Repos zum Architektur-Lernen (build-your-own-x: „Build your own Programming Language")

- 🛠 **rui314/chibicc** — [github.com/rui314/chibicc](https://github.com/rui314/chibicc): C-Compiler in ~700 Commits, **jeder Commit ein lehrbuchartiger Schritt** — das beste „Read the history"-Repo des Felds. Einsatz: vor/während CT als Implementierungs-Vorbild.
- 🛠 **munificent/craftinginterpreters** — [github.com/munificent/craftinginterpreters](https://github.com/munificent/craftinginterpreters): der komplette Code zum Buch (s. §2), Java + C.
- 🛠 **andrejbauer/plzoo** — [github.com/andrejbauer/plzoo](https://github.com/andrejbauer/plzoo): Mini-Implementierungen von ~10 Sprachparadigmen (typisiert, lazy, OO …) in OCaml — TPS-Konzepte als lauffähige 300-Zeilen-Sprachen.
- 🛠 **Stephen Diehl, „Write You a Haskell"** — [dev.stephendiehl.com/fun](https://dev.stephendiehl.com/fun/): Lambda-Kalkül → Hindley-Milner → Core in Haskell — die Brücke von §1/§4-Theorie zu Code.
- 🛠 **QBE** — [c9x.me/compile](https://c9x.me/compile/): Backend in ~10k Zeilen C (SSA, RegAlloc) — zeigt, wie klein ein echtes Optimizer-Backend sein kann; Kontrast zum LLVM-Studium.
- 🛠 **egraphs-good/egg + egglog** — [github.com/egraphs-good/egg](https://github.com/egraphs-good/egg): **Equality Saturation / E-Graph-Rewriting in Rust — das für Stratum relevanteste Repo dieser gesamten Bibliothek.** Term-Rewriting ohne Phase-Ordering-Problem; das egg-Paper (POPL 2021) gehört in deine Thesis-Literaturliste. Einsatz: Paper + Tutorial durcharbeiten, dann gegen Stratums Rewrite-Ansatz spiegeln.
- 🛠 **rise-lang / elevate** — [github.com/rise-lang](https://github.com/rise-lang): Steuwers eigene IR + Rewrite-Strategie-Sprache als Code — vor der TPS-Prüfung und vor DEEM-Designdiskussionen gleichermaßen wertvoll.
- 🛠 **MLIR-Beispiele im LLVM-Monorepo** — (s. §2 Toy-Tutorial) plus produktive Dialekte (linalg, affine) — Industrie-Referenz für Multi-Level-Rewriting.

### Generalfundament (aus deinem Ultimate-Index übernommen)

- 📚 **Nand2Tetris** ([nand2tetris.org](https://www.nand2tetris.org/)) — Teil II baut VM-Translator + Compiler für eine einfache Sprache: sanfter CT-Vorlauf, falls du vor M2/M4 Grundlagen-Sicherheit willst.
- 📚 **OSTEP** — Runtime-Systeme-Hälfte von Compiler Design (Speicher, Prozesse, Threads) — Kapitel gezielt, mit den mitgelieferten Homework-Simulatoren.
- 🎓 **MIT 6.1810/6.828 (OS Engineering, OCW)** — aus deinem Index; xv6-Labs als tiefste Runtime-Systems-Schule — nur bei echtem Zeitbudget, eher Zusatz als Pflicht.

---

## Frontier-Lab-Delta (2026-06-11): Was kein TU-Modul lehrt — Selbststudien-Pfad Richtung ML-Systems-Engineer (Anthropic-Klasse)

> Drei Themenfelder, die für Frontier-Lab-Rollen erwartet werden, aber in keinem Modulkatalog stehen. Kein Semesterdruck — das hier läuft parallel über die Masterjahre, andockend an GPU Computing, MLMMI und AMLS. Reihenfolge innerhalb jedes Felds = Lernreihenfolge.

### A. Large-Scale-Training-Systeme (Verteiltes Training)

- 📚 **Hugging Face „Ultra-Scale Playbook"** — [huggingface.co/spaces/nanotron/ultrascale-playbook](https://huggingface.co/spaces/nanotron/ultrascale-playbook) (frei, 2025). Der erste zusammenhängende Text, der Training auf GPU-Clustern end-to-end lehrt: Daten-/Tensor-/Pipeline-/Context-Parallelismus, ZeRO, Overlap von Compute und Kommunikation — mit Messungen statt Folklore. Einsatz: Haupttext für dieses Feld; einmal komplett, danach als Referenz.
- 📚 **Stas Bekman, „Machine Learning Engineering Open Book"** — [github.com/stas00/ml-engineering](https://github.com/stas00/ml-engineering) (frei, vom BLOOM-Training-Lead). Die Praxis-Seite: Debugging auf Multi-Node, NCCL, Storage/IO fürs Training, Fehlertoleranz — das, was zwischen den Papers steht. Einsatz: parallel zum Playbook als „so ist es wirklich"-Korrektiv.
- 📄 **Paper-Kette (chronologisch lesen):** Micikevicius et al., „Mixed Precision Training" (2018) → Shoeybi et al., **„Megatron-LM"** (2019, Tensor-Parallelismus) → Huang et al., „GPipe" + Narayanan et al., „PipeDream" (Pipeline-Parallelismus) → Rajbhandari et al., **„ZeRO" (SC 2020)** → Narayanan et al., „Efficient Large-Scale LM Training" (SC 2021, Megatron-Kombination) → PyTorch-FSDP-Paper (2023). Einsatz: ~ein Paper pro Woche neben M-Semestern; danach kannst du jedes Trainings-Infra-Gespräch führen.
- 🛠 **Code dazu:** [NVIDIA/Megatron-LM](https://github.com/NVIDIA/Megatron-LM) und [huggingface/nanotron](https://github.com/huggingface/nanotron) (klein genug zum Lesen) — Parallelismus-Strategien im Quelltext statt im Diagramm.

### B. GPU-/Kernel-Tiefe (über das GPU-Computing-Modul hinaus)

- 🎓 **GPU MODE (ehem. CUDA MODE) Lecture Series** — [github.com/gpu-mode/lectures](https://github.com/gpu-mode/lectures) + YouTube. Die De-facto-Community-Uni für Kernel-Engineering (Profiling, Occupancy, Triton, CUTLASS), von Praktikern aus genau den Ziel-Firmen. Einsatz: als Begleitspur zum GPU-Computing-Modul (M2/M4) — Modul liefert Grundlagen, GPU MODE die Frontier-Praxis.
- 📚 **Kirk/Hwu, „Programming Massively Parallel Processors" (4. Aufl., PMPP)** — das Lehrbuch zu CUDA-Grundmustern (Tiling, Memory Coalescing, Reduktionen). Einsatz: Referenz neben den Lectures; Kapitel zu Matmul-Optimierung ist Pflicht.
- 📄 **Horace He, „Making Deep Learning Go Brrrr From First Principles"** — [horace.io/brrr_intro.html](https://horace.io/brrr_intro.html). Das mentale Modell (compute-bound vs. memory-bound vs. overhead-bound), mit dem man jede DL-Performance-Frage sortiert. Einsatz: ein Abend; danach DMH/AMLS/MLMMI-Stoff neu einsortieren.
- 📄 **Dao et al., „FlashAttention" (2022)** + 🛠 **OpenAI Triton-Tutorials** ([triton-lang.org](https://triton-lang.org/)) — IO-Awareness als Optimierungsprinzip + Kernel schreiben in Python-Syntax. **Triton ist zugleich ein Compiler über einer Tile-IR — die direkteste Frontier-Verlängerung deiner Stratum/MLIR-Schiene.** Einsatz: Tutorials 1–3 durcharbeiten, einen eigenen Fused-Kernel bauen.

### C. Inference im Frontier-Maßstab

- 📄 **Pope et al., „Efficiently Scaling Transformer Inference" (MLSys 2023)** — das Grundlagen-Paper für Serving-Ökonomie (Batching, KV-Cache, Parallelismus-Trade-offs). → direkt MLMMI-anschlussfähig.
- 📄 **Kwon et al., „Efficient Memory Management for LLM Serving with PagedAttention" (SOSP 2023)** — das vLLM-Paper: OS-Konzepte (Paging!) auf ML-Serving übertragen — konzeptionell die schönste Systems×ML-Arbeit der letzten Jahre; Repo bereits im ML-Nachtrag. Dazu: Leviathan et al., „Speculative Decoding" (2023).
- 🛠 **Praxis:** ein kleines Modell einmal selbst quantisieren + servieren (llama.cpp → vLLM → Profiling mit GPU-MODE-Methodik) und die Latenz-/Durchsatz-Kurven nach CSB-/Gil-Tene-Regeln messen. **Dieses eine Wochenendprojekt verbindet vier Achsen (🚀🤖📊🔧) und ist ein CV-fähiges Artefakt.**

> **Einordnung:** Schicht 1 (TU-Module) ✓ erfasst · Schicht 2 (Stratum/DEEM + Thesis) ✓ geplant · Schicht 3 = dieser Abschnitt, bewusst klein gehalten: 2 freie Bücher, ~10 Papers, 2 Lecture-Serien, 1 Wochenendprojekt. Mehr braucht es nicht — der Rest ist Job-Erfahrung.
