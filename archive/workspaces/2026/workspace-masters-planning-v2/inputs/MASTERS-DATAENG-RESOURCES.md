# MASTERS-DATAENG-RESOURCES — Lernbibliothek für den 🔧 Data-Engineering-Block

> **Stand:** 2026-06-11 · Phase 2, Teil 1 (Achse 🔧 aus `MASTERS-MODULE-MENU.md`)
> **Zweck:** Pro Modul die besten externen Lerninhalte — offene Vorlesungen anderer Unis (mit Videos), Bücher, Papers, Hands-on-Material — mit Erklärung, was es ist und **wann im Studienverlauf du es einsetzt** (Vorbereitung / semesterbegleitend / Prüfungsphase).
> **Konvention:** 🎓 = offene Uni-Vorlesung · 📚 = Buch · 📄 = Paper/Skript · 🛠 = Hands-on/Code. Web-Links Stand Juni 2026 — Kurs-Seiten wandern gelegentlich pro Semester (Jahrgang in der URL beachten).

---

## 1. DBT — Database Technology ([#40405](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40405&version=13), 6 LP, WiSe, Klausur 90min)

**Modulprofil:** DBMS-Interna single-node: Architektur, File-/Buffer-Management, Datenlayouts, Caching, Indexstrukturen, Anfrageverarbeitung, **Anfrageoptimierung**, Locking, Recovery, Transaktionen. Mit Programmier-Vorleistung (~25h) und Theorieaufgaben. Das ist dein Fundament-Modul — und inhaltlich fast deckungsgleich mit den berühmtesten offenen DB-Kursen der Welt.

- 🎓 **CMU 15-445/645 „Intro to Database Systems" (Andy Pavlo)** — [15445.courses.cs.cmu.edu](https://15445.courses.cs.cmu.edu/) · [Kursübersicht der CMU DB Group](https://db.cs.cmu.edu/courses/) · alle Vorlesungen auf YouTube. **Die** Referenzvorlesung für genau den DBT-Stoff: Storage, Buffer Pool, B+Trees, Hash Tables, Sorting/Aggregation, Joins, Query Execution, Optimierung, Concurrency Control, Recovery (ARIES). Pavlo ist didaktisch herausragend und die Themenreihenfolge passt nahezu 1:1 auf die DBT-Gliederung. Einsatz: semesterbegleitend als Zweitperspektive — nach jeder DBT-Vorlesung die passende 15-445-Lecture schauen; vor der Klausur die Lecture Notes (öffentlich, sehr kondensiert) als Wiederholung.
- 🎓 **UC Berkeley CS186 „Introduction to Database Systems"** — [cs186berkeley.net](https://cs186berkeley.net/) · [Videos auf YouTube](https://github.com/PKUFlyingPig/CS186) · [Projekt-Spezifikationen](https://cs186.gitbook.io/project). Gleicher Stoff, etwas SQL-/anwendungslastiger als CMU, mit exzellenten Notes zu Query Optimization (Selinger-Stil — genau das, was in der DBT-Klausur als Rechenaufgabe kommt: Kostenmodelle, Join-Ordering, Selektivitäten). Einsatz: als Alternative, wenn dir Pavlos Tempo zu hoch ist; die CS186-Discussion-Worksheets sind ideales Klausurtraining.
- 🎓 **MIT 6.5830 „Database Systems"** — [dsg.csail.mit.edu/6.5830](https://dsg.csail.mit.edu/6.5830/) · [Notes + Assignments](https://dsg.csail.mit.edu/6.5830/assign.php). Graduate-Niveau, paperbasierter: liest Originalarbeiten (System R, ARIES) parallel zur Vorlesung. Einsatz: punktuell für Tiefe bei Optimizer und Recovery — die System-R-Lecture erklärt die Optimizer-Grundideen, die Markl (selbst Optimizer-Forscher, IBM-Vergangenheit) in DBT vertieft.
- 📚 **Silberschatz/Korth/Sudarshan, „Database System Concepts" (7. Aufl.)** — [db-book.com](https://www.db-book.com/) (Slides + Übungen frei). Das Standard-Lehrbuch; Kapitel 12–19 (Storage, Indexing, Query Processing/Optimization, Transactions, Concurrency, Recovery) decken die DBT-Klausurthemen vollständig ab. Einsatz: Nachschlagewerk, wenn eine Vorlesungsfolie zu knapp ist; die Übungsaufgaben mit Lösungen sind Klausur-Simulationsmaterial.
- 📚 **Garcia-Molina/Ullman/Widom, „Database Systems — The Complete Book"** — steht in der offiziellen DBT-Literaturliste (siehe Moses-Link). Stärker formal bei Anfrageverarbeitung/Optimierung (relationale Algebra-Umformungen, Kostenabschätzung). Einsatz: gezielt die Kapitel 15–16 für die Optimierungs-Theorieaufgaben.
- 📄 **Hellerstein/Stonebraker/Hamilton, „Architecture of a Database System"** — [frei als PDF (Foundations & Trends)](https://dsf.berkeley.edu/papers/fntdb07-architecture.pdf). ~80 Seiten, die beste Gesamtschau, wie die DBT-Einzelthemen in echten Systemen zusammenhängen (Prozessmodelle, Parser→Rewriter→Optimizer→Executor, Storage). Einsatz: einmal **vor** Semesterstart lesen — danach hat jede DBT-Vorlesung einen Platz im Gesamtbild.
- 🛠 **CMU BusTub** — [github.com/cmu-db/bustub](https://github.com/cmu-db/bustub). Das 15-445-Übungs-DBMS (C++): Buffer Pool, B+Tree, Query Execution selbst bauen. Einsatz: optional vor dem Semester als Warm-up für die DBT-Programmieraufgabe — wer einen Buffer Pool einmal implementiert hat, besteht die Vorleistung entspannt.

## 2. DBTLAB — Database Technology Lab ([#40037](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40037&version=10), 6 LP, WiSe, Portfolio, 150h Implementierung, **sehr gutes Java verlangt**)

**Modulprofil:** Komponenten eines relationalen DBMS in Java selbst implementieren — IO/Storage, Query Execution, Query Optimization (die drei Deliverables). Das ist die praktische Zwillingshälfte zu DBT und dein wichtigstes Engine-Bau-Modul vor der Thesis.

- 🛠🎓 **Berkeley RookieDB (CS186-Projekte)** — [github.com/berkeley-cs186](https://github.com/berkeley-cs186) · [Spezifikationen](https://cs186.gitbook.io/project). **In Java!** Du implementierst B+Tree-Indizes, Join-Algorithmen, Query Optimization, Locking und Recovery in ein vorgegebenes Java-DBMS-Skelett — strukturell das exakte Trainingsprogramm für die drei DBTLAB-Deliverables, inklusive Test-Suites. Einsatz: im Sommer vor M3 durcharbeiten (mindestens die Projekte zu Joins/Optimizer); das ist die beste DBTLAB-Generalprobe, die es gibt.
- 🛠🎓 **MIT SimpleDB / GoDB (6.830/6.5830-Labs)** — [historische Java-Labs auf OCW](https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/pages/assignments/) · [aktuelle Go-Variante](https://dsg.csail.mit.edu/6.5830/assign.php). SimpleDB (Java) lässt dich mehr von Grund auf bauen als RookieDB (weniger Gerüst, mehr Eigenverantwortung) — näher am DBTLAB-Gefühl. Einsatz: Alternative/Ergänzung zu RookieDB, wenn du das Architektur-Design selbst treffen willst.
- 🎓 **CMU 15-721 „Advanced Database Systems"** — [15721.courses.cs.cmu.edu](https://15721.courses.cs.cmu.edu/) (Videos + Reading List öffentlich). Wie moderne Engines wirklich gebaut werden: Vectorized Execution, Query Compilation, Parallel Join-Implementierungen, moderne Optimizer (Cascades!). Einsatz: selektiv während DBTLAB — besonders die Optimizer-Lectures, wenn das dritte Deliverable (Query Optimization) ansteht; gleichzeitig Thesis-relevante Optimizer-Literatur.
- 📚 **Alex Petrov, „Database Internals" (O'Reilly)** — Teil 1 (Storage Engines: B-Trees, LSM, File Formats, Buffer Management) ist die lesbarste moderne Darstellung der IO-Schicht. Einsatz: begleitend zum ersten Deliverable (IO Handling).
- 📚 **Andy Grove, „How Query Engines Work"** — [howqueryengineswork.com](https://howqueryengineswork.com/) (frei online). Baut Schritt für Schritt eine Query Engine (logische/physische Pläne, Operatoren, Planner, Optimizer-Rules) — vom DataFusion-Erfinder. Einsatz: vor/während Deliverable 2+3; konzeptionell die Brücke zwischen DBTLAB und deiner Stratum-Arbeit (logische Pläne + Rewrites!).
- 📚 **Joshua Bloch, „Effective Java" (3. Aufl.)** — DBTLAB verlangt explizit „very good (!!) command of Java". Einsatz: die Items zu Generics, Collections, equals/hashCode und Ressourcen-Management vor Semesterstart auffrischen — die Korrektoren lesen Code-Qualität mit.
- 📄 **Goetz Graefe, „Volcano — An Extensible and Parallel Query Evaluation System"** + **„The Cascades Framework for Query Optimization"** — die zwei Papers, auf denen praktisch jeder Executor (Iterator-Modell) und Optimizer (Cascades) basiert. Einsatz: jeweils vor Deliverable 2 bzw. 3 lesen; Cascades ist zusätzlich Stratum-Thesis-Hintergrund.

## 3. DMH — Data Management on Modern Hardware ([#40804](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40804&version=6), 6 LP, SoSe, Portfolio)

**Modulprofil:** Datenverarbeitung im Spannungsfeld moderner Hardware: Cache-Hierarchien, NUMA, SIMD, Multicore-Parallelität, ggf. GPUs/Beschleuniger — Performance-Engineering für Datensysteme. Deine 🚀/📊-Brücke.

- 🎓 **TUM „Data Processing on Modern Hardware" (Jana Giceva)** — [db.in.tum.de/teaching/ss21/dataprocessingonmodernhardware](https://db.in.tum.de/teaching/ss21/dataprocessingonmodernhardware/?lang=en) (alle Foliensätze frei: Hardware Trends, Cache Awareness, Execution Models, SIMD, Multicore, Synchronisation). Das deutsche Schwester-Modul von der stärksten DB-Systems-Gruppe Europas (HyPer/Umbra). Einsatz: semesterbegleitend als zweite Foliensicht; die Cache-/SIMD-Kapitel sind ausführlicher als die meisten Vorlesungen.
- 🎓 **CMU 15-721** (s. o.) — die Lectures zu In-Memory-Architekturen, Vectorization vs. Compilation und Parallel Joins überschneiden sich stark mit DMH. Einsatz: pro DMH-Thema die passende 15-721-Lecture als Video-Ergänzung.
- 📄 **Ulrich Drepper, „What Every Programmer Should Know About Memory"** — [frei als PDF](https://people.freebsd.org/~lstewart/articles/cpumemory.pdf). Der Klassiker über Cache-Hierarchien, TLBs, Prefetching, NUMA — ~100 Seiten, davon die ersten 50 Pflicht. Einsatz: vor Semesterstart; danach verstehst du *warum* jede DMH-Optimierung funktioniert.
- 📄 **Boncz/Zukowski/Nes, „MonetDB/X100: Hyper-Pipelining Query Execution" (CIDR 2005)** und **Neumann, „Efficiently Compiling Efficient Query Plans for Modern Hardware" (VLDB 2011)** — die zwei Papers, die Vectorized Execution bzw. Query Compilation begründet haben; **Kemper/Neumann HyPer** und **„Morsel-Driven Parallelism" (SIGMOD 2014)** für NUMA-aware Scheduling. Einsatz: Kern-Lektüre fürs Portfolio; in Diskussionsteilen zitierfähig.
- 📚 **Brendan Gregg, „Systems Performance" (2. Aufl.)** — Methodik des Performance-Engineerings (USE-Methode, Profiling, Flame Graphs, perf). Einsatz: fürs Portfolio-Messen — sauberes Benchmarking-Handwerk, das dir auch bei CSB und in der Thesis-Evaluation wieder begegnet.
- 🛠 **Agner Fog, Optimization Manuals** ([agner.org/optimize](https://www.agner.org/optimize/)) + **perf/VTune-Tutorials** — wenn das Portfolio Mikro-Benchmarks verlangt (Cache-Misses zählen, SIMD-Speedups messen), sind das die Referenzwerkzeuge. Einsatz: punktuell bei den Übungsaufgaben.

## 4. MDS — Management of Data Streams ([#40310](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40310&version=8), 6 LP, WiSe, mündlich)

**Modulprofil:** Stream-Processing: Datenstrom-Modelle, Fenstersemantik, Event Time vs. Processing Time, Out-of-Order-Verarbeitung, Stream-Joins, Fehlertoleranz/State, Streaming-Algorithmen. Heimspiel der Markl-Gruppe — **Apache Flink wurde hier (als Stratosphere) erfunden**; erwarte Flink-Nähe.

- 📚 **Akidau/Chernyak/Lax, „Streaming Systems" (O'Reilly)** — *das* Buch zur Semantik: Watermarks, Trigger, Accumulation, Exactly-Once, Streams↔Tables-Dualität. Geschrieben von den Google-Dataflow-Architekten, deren Modell Flink übernommen hat. Einsatz: Hauptbegleitlektüre; Kapitel 1–5 vor der Semestermitte, danach sitzt die Fenster-/Watermark-Theorie für die mündliche Prüfung.
- 📄 **Tyler Akidau, „Streaming 101" + „Streaming 102"** — [oreilly.com/radar/the-world-beyond-batch-streaming-101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (frei). Die Kurzfassung des Buchs als zwei Essays. Einsatz: **vor** Semesterstart — in zwei Stunden hast du das Begriffsgerüst, in das die Vorlesung einsortiert.
- 📄 **Carbone et al., „Apache Flink: Stream and Batch Processing in a Single Engine"** + **„Lightweight Asynchronous Snapshots for Distributed Dataflows"** (Chandy-Lamport-Variante hinter Flinks Checkpointing) — Papers direkt aus dem TU-Berlin-Umfeld. Einsatz: Pflichtlektüre; in einer mündlichen Prüfung bei DIMA über Flink-Checkpointing sprechen zu können ist Gold.
- 🎓 **Stanford CS246 „Mining of Massive Datasets"** — [web.stanford.edu/class/cs246](https://web.stanford.edu/class/cs246/) · Buch frei auf [mmds.org](http://www.mmds.org/). Kapitel 4 (Mining Data Streams) liefert die Algorithmen-Seite: Sampling, Bloom Filter, Count-Min Sketch, DGIM, HyperLogLog. Einsatz: gezielt für den Streaming-Algorithmen-Teil; die mündliche Prüfung fragt solche Sketches gern als Verständnischeck.
- 🛠 **Apache Flink Training & Docs** — [nightlies.apache.org/flink](https://nightlies.apache.org/flink/flink-docs-stable/) (Learn-Flink-Tutorials: DataStream API, Event Time, State, Checkpointing). Einsatz: Hands-on parallel zur Vorlesung — ein kleines Event-Time-Windowing-Beispiel selbst bauen macht die Theorie konkret.
- 📚 **Kleppmann, „Designing Data-Intensive Applications"**, Kapitel 11 (Stream Processing) — die beste Einbettung von Streams ins Gesamtbild verteilter Datensysteme (Logs, Kafka, CDC, Exactly-Once-Mythen). Einsatz: Wiederholungslektüre vor der Prüfung; verbindet MDS mit LDE/DDIA-Wissen.

## 5. DILA — Data Integration and Large-scale Analysis ([#41112](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41112&version=2), 6 LP, WiSe, Klausur, Böhm)

**Modulprofil:** Datenintegration (Schema Matching/Mapping, Entity Resolution, Data Cleaning) + Large-Scale-Analysis-Infrastruktur (verteilte Ausführung, Cloud, ML-Systeme). **Großer Vorteil: Böhm hält exakt diese Vorlesung seit Jahren öffentlich dokumentiert.**

- 🎓 **Böhms eigene Kursseiten (TU Graz → TU Berlin), alle Folien frei** — [aktuelle Ausgabe WiSe 25/26](https://mboehm7.github.io/teaching/ws2526_dia/index.htm) · [WS 21/22 mit allen PDFs](https://mboehm7.github.io/teaching/ws2122_dia/index.htm) · [Übersicht auf mboehm7.github.io](https://mboehm7.github.io/). **Das ist das Modul selbst** — 12+ Foliensätze (Data Cleaning, Schema Matching, Entity Resolution, Distributed Data Storage, Cloud Computing, Stream Processing, ML Systems). Die Graz-Jahrgänge (ab WS 19/20) enthalten Aufzeichnungen/Recordings der Zoom-Vorlesungen. Einsatz: **die** Primärquelle — du kannst die komplette Vorlesung vor M3 einmal durchgehen; Klausurvorbereitung = alte Foliensätze + [Studenten-Mitschrift DIA-Notes](https://philipportner.github.io/DIA-Notes/) als komprimierte Zusammenfassung.
- 📚 **Doan/Halevy/Ives, „Principles of Data Integration"** — das Standardwerk zur Integrationstheorie: Schema Matching, Mappings (GAV/LAV), Entity Resolution, Datenaustausch. Einsatz: Vertiefung der ersten Semesterhälfte; die formalen Mapping-Kapitel sind klausurrelevante Theorie.
- 📚 **Ilyas/Chu, „Data Cleaning" (ACM Books)** — systematische Abdeckung von Fehlererkennung, Constraint-basiertem Cleaning, Deduplizierung, ML-gestütztem Cleaning. Einsatz: für den Cleaning-Block; gleichzeitig EDML-Vorinvestition (Überschneidung der beiden Module!).
- 🛠 **Apache SystemDS** — [systemds.apache.org](https://systemds.apache.org/) — Böhms eigenes System (er ist Gründungs-Committer); die DIA-Programmierprojekte in Graz liefen auf SystemDS/DAPHNE. Einsatz: Codebasis anschauen, bevor du in seine Sprechstunde gehst — und potenzieller Anknüpfungspunkt für Projekte im Böhm-Orbit.
- 📄 **Stonebraker et al., „Data Curation at Scale: The Data Tamer System" (CIDR 2013)** + **Konda et al., „Magellan: Toward Building Entity Matching Management Systems" (VLDB 2016)** — zwei Systeme-Papers, die Integration end-to-end denken. Einsatz: Zusatzstoff für Transferfragen in der Klausur.

## 6. Data Integration: Algorithms and Systems ([#41213](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41213&version=2), 6 LP, WiSe, mündlich, Abedjan)

**Modulprofil:** Die algorithmische Tiefenbohrung zur Integration: Data Profiling (Dependencies!), Duplicate Detection/Entity Resolution, Schema Matching, Data Discovery. Abedjan ist Data-Profiling-Koryphäe (HPI-Naumann-Schule).

- 📚 **Abedjan/Golab/Naumann/Papenbrock, „Data Profiling" (Synthesis Lectures)** — **vom Modulverantwortlichen selbst.** Unique Column Combinations, funktionale/Inklusions-Abhängigkeiten, Discovery-Algorithmen (TANE & Co.). Einsatz: Hauptlektüre — wer das Buch des Prüfers kennt, führt die mündliche Prüfung.
- 🎓 **HPI-Vorlesungen (Naumann-Gruppe): „Data Profiling" + „Information Integration"** — [hpi.de Data-Profiling-Kursseite](https://hpi.de/en/naumann/teaching/course-archive.html); Folien und teils Videos öffentlich (tele-Task/openHPI). Abedjans wissenschaftliche Heimat — die HPI-Folien sind die ausführlichste deutschsprachige Quelle zu Profiling-Algorithmen. Einsatz: semesterbegleitend; openHPI-Kurse von Naumann ([z. B. „Data Engineering und Data Science"](https://open.hpi.de/courses/data-engineering2020)) als sanfter Einstieg.
- 📄 **Naumann/Herschel, „An Introduction to Duplicate Detection"** (Synthesis Lectures) + **Papadakis et al., „Blocking and Filtering Techniques for Entity Resolution: A Survey" (ACM CSUR 2020)** — Duplikaterkennung von Grundlagen bis State of the Art. Einsatz: für den ER-Block; Survey-Strukturen eignen sich hervorragend als Antwortgerüst in mündlichen Prüfungen.
- 📚 **Doan/Halevy/Ives** (s. DILA) — doppelt nutzbar; die beiden Module teilen sich das theoretische Fundament, unterscheiden sich aber in Tiefe (Abedjan: Algorithmen) vs. Breite (Böhm: Systeme).

## 7. EDML — Engineering Data for Machine Learning ([#41221](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41221&version=1), 6 LP, WiSe, Portfolio, **Schelter/DEEM**)

**Modulprofil:** Datenseite von ML-Pipelines: Data Validation/Quality, Feature Engineering/Preprocessing-Pipelines, Label-Probleme, Bias/Responsibility, Pipeline-Tooling. **Dein DEEM-Einstiegsmodul — inhaltlich der direkteste Vorlauf zu Stratum und zur Thesis.**

- 📄 **Schelters eigene Papers — Pflichtprogramm:** „Automating Large-Scale Data Quality Verification" (VLDB 2018, das **Deequ**-Paper) · „mlinspect: Lightweight Inspection of Native ML Pipelines" (CIDR 2021 — Provenance/Inspection über Pipeline-DAGs, **konzeptioneller Stratum-Nachbar!**) · „Hidden Technical Debt in Machine Learning Systems" (Sculley et al., NeurIPS 2015) als Rahmenpaper, das Schelter konsequent zitiert. Einsatz: vor M3 lesen — du sitzt beim Autor im Kurs; im Portfolio und in DEEM-Gesprächen sind diese Referenzen deine gemeinsame Sprache.
- 🎓 **MIT „Introduction to Data-Centric AI"** — [dcai.csail.mit.edu](https://dcai.csail.mit.edu/) · [Videos auf YouTube](https://www.youtube.com/@dcai-course) · [Labs auf GitHub](https://github.com/dcai-course/dcai-course). Der einzige offene Kurs, der EDMLs Kernthese teilt: Datenqualität schlägt Modelltuning. Label Errors (Confident Learning), Dataset Curation, Data-Centric Evaluation — mit Jupyter-Labs. Einsatz: kompletter Durchgang (kompakt, ~8 Lectures) vor oder zu Semesterbeginn.
- 🎓 **Stanford CS329S „Machine Learning Systems Design" (Chip Huyen)** — [stanford-cs329s.github.io](https://stanford-cs329s.github.io/) (Notes öffentlich) + 📚 **Huyen, „Designing Machine Learning Systems" (O'Reilly)**. Kapitel zu Training Data, Feature Engineering, Data Distribution Shifts decken die EDML-Praxisseite ab. Einsatz: begleitend; das Buch bleibt für MLMMI (M4) relevant — eine Anschaffung, zwei Module.
- 🛠 **Deequ / Great Expectations / TFX Data Validation** — [github.com/awslabs/deequ](https://github.com/awslabs/deequ) (Schelters System aus seiner Amazon-Zeit!), [greatexpectations.io](https://greatexpectations.io/), TFDV-Tutorials. Einsatz: eines davon im Portfolio aktiv benutzen; Deequ zu kennen ist im DEEM-Kontext quasi Dialekt.
- 📚 **Ilyas/Chu, „Data Cleaning"** (s. DILA) — die wissenschaftliche Tiefe hinter dem Cleaning-Teil. Doppelnutzung DILA↔EDML im selben WiSe ist ein echter Synergie-Gewinn.

## 8. MLMMI — ML Model Management and Inference ([#41289](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41289&version=2), 6 LP, SoSe, Portfolio, **Schelter/DEEM**)

**Modulprofil:** Lifecycle nach dem Training: Modell-Versionierung/Metadaten, Deployment/Serving, Inference-Optimierung (Batching, Quantisierung, Compilation), Monitoring/Drift, Retraining. Die 🚀-Seite von DEEM.

- 🎓 **CMU 10-414/714 „Deep Learning Systems" (Chen/Kolter)** — [dlsyscourse.org](https://dlsyscourse.org/) · [Lectures](https://dlsyscourse.org/lectures/) · [YouTube-Playlist](https://www.youtube.com/playlist?list=PLGzYMymX8amNyGPuJ35YWdq59eQ5jYCZ1). Du baust „Needle", ein Mini-PyTorch: Autodiff, GPU-Kernels, Operator-Graphen, Compilation. Einsatz: die Inference-/Compilation-Hälfte von MLMMI von innen verstehen; für dein Runtime/Optimizer-Profil ohnehin das wertvollste offene MLSys-Material überhaupt.
- 🎓 **Stanford MLSys Seminar (CS528)** — [mlsys.stanford.edu](https://mlsys.stanford.edu/) · [YouTube-Kanal](https://www.youtube.com/c/StanfordMLSysSeminars). 100+ Talks von Praktikern (Serving, Feature Stores, Model Management, LLM-Inference). Einsatz: à la carte — pro Portfolio-Thema gibt es hier einen passenden Talk als aktuelle Industrie-Perspektive.
- 📚 **„Machine Learning Systems" (Vijay Janapa Reddi, Harvard)** — [mlsysbook.ai](https://mlsysbook.ai/) (frei, lebendes Lehrbuch). Kapitel zu Model Optimization, Serving, MLOps, Monitoring — das fehlende Lehrbuch zwischen Huyens Praxisbuch und Systems-Papers. Einsatz: Referenztext fürs Semester.
- 📄 **Papers:** „TFX: A TensorFlow-Based Production-Scale ML Platform" (KDD 2017) · „Hidden Technical Debt" (s. o.) · „Clipper: A Low-Latency Online Prediction Serving System" (NSDI 2017) · „Model Cards for Model Reporting" (FAT* 2019 — Schelter-nahe Responsibility-Schiene). Einsatz: Portfolio-Zitierbasis; Clipper vs. modernes Serving (vLLM, Triton) ist eine schöne Diskussionsachse.
- 🛠 **MLflow + Weights&Biases (Tracking) · TorchServe/Triton/ONNX Runtime (Serving)** — offizielle Tutorials. Einsatz: ein Mini-Projekt „Modell trainieren → registrieren → servieren → überwachen" einmal end-to-end bauen; genau dieses Skelett verlangen MLMMI-Portfolios typischerweise.

## 9. LDE — Large-scale Data Engineering ([#41086](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41086&version=3), 12 LP, WiSe+SoSe, Portfolio, Böhm, **max 10 Plätze — nur als DBTLAB-Ersatz, nie zusätzlich**)

**Modulprofil:** Großes (12 LP!) Engineering-Modul über verteilte Datenpipelines und -infrastruktur im Böhm-Orbit (SystemDS/DAPHNE-Nähe).

- 📚 **Kleppmann, „Designing Data-Intensive Applications"** — falls du nur ein Buch für verteilte Datensysteme liest, dann dieses: Replikation, Partitionierung, Konsistenz, Batch (MapReduce/Spark), Streams. Einsatz: komplett; DDIA ist außerdem die gemeinsame Wissensbasis für MDS, CSB und Scalability Engineering.
- 🎓 **MIT 6.824/6.5840 „Distributed Systems"** — [pdos.csail.mit.edu/6.824](https://pdos.csail.mit.edu/6.824/) (Notes, Papers, Videos, Go-Labs: MapReduce, Raft, Sharded KV). Einsatz: die Infrastruktur-Grundlagen unter jeder Large-Scale-Pipeline; Labs nur bei echtem Zeitbudget (das Modul ist selbst schon 12 LP schwer).
- 📄 **Klassiker-Papers:** „MapReduce" (OSDI 2004) · „Resilient Distributed Datasets" (Spark, NSDI 2012) · „Dremel" (VLDB 2010) · „The Google File System" (SOSP 2003) · dazu Böhms „SystemDS: A Declarative ML System" (CIDR 2020). Einsatz: Reading-Grundstock; das SystemDS-Paper, weil der Dozent damit denkt.
- 🛠 **Spark- und Flink-Doku/Tutorials** + **Fundamentals of Data Engineering (Reis/Housley, O'Reilly)** als Praxis-Rahmenbuch über Pipelines, Orchestrierung, Storage-Formate (Parquet/Iceberg). Einsatz: begleitend zur Projektarbeit.

## 10. ML&DMS — Machine Learning and Data Management Systems ([#41146](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41146&version=2), 3 LP, WiSe+SoSe, Referat, Böhm)

**Modulprofil:** Paper-Seminar an der Schnittstelle „ML für Datensysteme / Datensysteme für ML" — du liest, präsentierst und diskutierst aktuelle Forschung. Klein, aber profilbildend: exakt deine Nische.

- 📄 **Venues, aus denen die Paper kommen:** CIDR ([cidrdb.org](https://www.cidrdb.org/) — alle Papers frei), SIGMOD, VLDB ([vldb.org/pvldb](https://www.vldb.org/pvldb/) — frei), MLSys ([mlsys.org](https://mlsys.org/)). Einsatz: vorab je ein, zwei aktuelle Jahrgänge der CIDR/MLSys-Proceedings überfliegen — dann kannst du dir im Seminar das Paper wünschen, das auf Stratum einzahlt (Optimizer für ML-Pipelines, learned query optimization, Provenance).
- 📄 **Einstiegs-Surveys:** „Machine Learning for Databases" bzw. learned-components-Literatur (z. B. „The Case for Learned Index Structures", SIGMOD 2018) für die eine Richtung; „A Survey on Deep Learning Data Systems"-artige Überblicke und Schelters/Böhms eigene Übersichtsarbeiten für die andere. Einsatz: Orientierung, welche der beiden Richtungen dein Referat bedienen soll.
- 📄 **S. Keshav, „How to Read a Paper"** — [frei als PDF](https://web.stanford.edu/class/ee384m/Handouts/HowtoReadPaper.pdf). Drei-Pass-Methode; 2 Seiten. Einsatz: einmal lesen, dauerhaft anwenden — auch für Research Seminar DEEM und die Thesis-Literaturphase.
- 🎓 **Stanford MLSys Seminar** (s. MLMMI) + **CMU DB Group „Vaccination Database Tech Talks"** ([db.cs.cmu.edu](https://db.cs.cmu.edu/) → Seminars, alle auf YouTube) — laufende Talk-Reihen, in denen Paper-Autoren ihre Systeme selbst vorstellen. Einsatz: zum gewählten Referatsthema den passenden Talk suchen — Vortragsstil-Vorbild inklusive.

## 11. Knowledge Graphs and AI-driven Applications ([#41261](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41261&version=1), 6 LP, WiSe, Portfolio, Hauswirth)

**Modulprofil (lt. Katalog):** Vier Blöcke — I) **KG-Grundlagen** (Konzepte/Formalismen, Abfragesprachen & Operatoren, KG-Embeddings); II) **KG-Aufbau** (Datenaufnahme/-transformation, Anreicherung/Angleichung, Einsatz von LLMs/Foundation Models); III) **Speicherung & Verarbeitung** (Storage-Design, Graphabfragen, Reasoning, Streaming/dynamische KGs). Hauswirth (Open Distributed Systems / Fraunhofer FOKUS). Direkter Andockpunkt an deine Integrations-Linie (DI:AS/DILA).

- 📚 **Hogan et al., „Knowledge Graphs" (ACM Computing Surveys 2021)** — [frei: aidanhogan.com](https://aidanhogan.com/docs/knowledge-graphs-computing-surveys.pdf) / [arXiv 2003.02320](https://arxiv.org/abs/2003.02320); auch als Buch (Synthesis Lectures). Deckt Block I–III fast 1:1 (Modelle, Query, Embeddings, Reasoning). Einsatz: Hauptlektüre — vor Semesterstart einmal komplett.
- 🎓 **Stanford CS520 „Knowledge Graphs"** — [web.stanford.edu/class/cs520](https://web.stanford.edu/class/cs520/) (Seminar, Videos öffentlich). Einsatz: semesterbegleitend, besonders für den Aufbau-/LLM-Teil (Block II).
- 📄 **W3C RDF/SPARQL + Property Graphs/Cypher** — die Abfragesprachen aus Block I. Einsatz: Hands-on mit einem Triple-Store (Apache Jena) oder Neo4j.
- 📄 **KG-Embeddings:** Bordes et al., „Translating Embeddings (TransE)" (NeurIPS 2013) + Wang et al., „Knowledge Graph Embedding: A Survey" (IEEE TKDE 2017). Einsatz: für den Embedding-Block.
- 🛠 **PyKEEN** ([github.com/pykeen/pykeen](https://github.com/pykeen/pykeen)) + **Neo4j / Apache Jena** — Embedding-Library bzw. Storage/Query. Einsatz: Portfolio-Projekt.
- **Cross:** KG-Aufbau (Anreicherung/Angleichung) = Entity Resolution/Schema Matching aus **DI:AS (§6)** — gleiche Algorithmen, andere Verpackung.

## 12. Research Data Infrastructures and Knowledge Graphs ([#41273](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41273&version=1), 6 LP, WiSe, Portfolio, Schimmler)

**Modulprofil (lt. Katalog):** Forschungsdateninfrastrukturen + Wissensgraphen; **Themen wechseln pro Semester** — Semantic Web/Linked Data/KG, Datenmanagement & Dateninfrastrukturen, **Datenqualität & FAIRness**, Sprachmodelle/NLP, Informationsextraktion/Textzusammenfassung. Schimmler (Fraunhofer FOKUS; Sprecherin **NFDI4DataScience**; Weizenbaum-Institut). Seminar-/Projektcharakter mit aktuellen Technologien.

- 📄 **Wilkinson et al., „The FAIR Guiding Principles for scientific data management and stewardship" (Scientific Data 2016)** — das Gründungspaper der FAIR-Bewegung; Kern des Datenqualitäts-/FAIRness-Teils. Einsatz: Pflicht, zuerst lesen.
- 🌐 **NFDI / NFDI4DataScience** — [nfdi.de](https://www.nfdi.de/) — Schimmlers Konsortium; Research Knowledge Graphs + FAIR Digital Objects als Infrastruktur. Einsatz: der konkrete Anwendungskontext des Moduls.
- 📚 **Hogan et al., „Knowledge Graphs"** (s. §11) — die KG-Hälfte, doppelt nutzbar. Einsatz: Überschneidung mit KG&AI gezielt ausnutzen.
- 🌐 **Open Research Knowledge Graph (ORKG)** — [orkg.org](https://orkg.org/) + GO-FAIR/RDM-Grundlagen. Einsatz: konkretes Beispiel eines Research-KG für Exposé/Projekt.
- **Cross:** überlappt mit Schelters **Responsible-DE-Linie** (Datenqualität, Reproduzierbarkeit) und mit **KG&AI (§11)**. Hinweis: Themen variieren semesterweise → beim Modulstart das aktuelle Programm prüfen.

## 13. Cloud Native Architecture and Engineering ([#40103](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40103&version=13), 9 LP, WiSe, Portfolio, Tai)

**Modulprofil (lt. Katalog):** Cloud-native Architektur — Softwarearchitekturen so anpassen, dass sie Cloud-Dienste (AWS Lambda, Cloud Spanner) nutzen; **Serverless, Container-Orchestrierung, VM-Cluster** als Bausteine & Zielumgebung; skalierbare, resiliente Lösungen. Tai (Information Systems Engineering, ISE). Eher systemnah (nicht Kern-Datensysteme), aber DSE.

- 📚 **Kleppmann, „Designing Data-Intensive Applications"** — [dataintensive.net](https://dataintensive.net/) — die System-Denkschule (Replikation, Partitionierung, Konsistenz); der Daten-Blickwinkel auf Cloud-Native. Einsatz: Hauptbuch für die Architektur-Prinzipien (kennst du ggf. aus DBT/DMH).
- 📚 **Newman, „Building Microservices" (2. Aufl., O'Reilly)** — Service-Decomposition, Deployment, Resilienz. Einsatz: für den Microservices-/Architektur-Teil.
- 🌐 **CNCF / Kubernetes-Doku + AWS Well-Architected Framework** — Praxis-Referenz zu Container-Orchestrierung & Serverless. Einsatz: semesterbegleitend.
- 📄 **„Twelve-Factor App"** ([12factor.net](https://12factor.net/)) + Fowler/Lewis, „Microservices" — die Architektur-Prinzipien kompakt. Einsatz: schneller Einstieg.
- **Cross:** Skalierbarkeit/Resilienz überlappt mit **Scalability Engineering & CSB** (📊-Block); Patterns ähneln der AWS Builders' Library.

## 14. Advanced Cloud Prototyping ([#41153](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41153&version=2), 12 LP, WiSe+SoSe, Portfolio, Tai) — Projekt-Alternative

**Modulprofil (lt. Katalog):** Projekt — Kleingruppen lösen anspruchsvolle Software-/Prototyping-Probleme; nutzen **Public-Cloud (AWS)** und moderne Stacks; je nach Fokus cloud-native/serverless/quality-driven; eigenständige Teamarbeit. Als **Pflichtprojekt-Alternative** (≥9 LP) zu RDE-Project/BDSPRO nutzbar.

- 🛠 **AWS Free Tier + AWS Well-Architected Labs** — [wellarchitectedlabs.com](https://wellarchitectedlabs.com/) — Hands-on mit echten Services. Einsatz: Pflicht — das Modul lebt vom Bauen.
- 🛠 **Infrastructure as Code:** Terraform + AWS CDK + Serverless Framework — reproduzierbare Deployments. Einsatz: für saubere, bewertbare Prototypen.
- 📚 **Cloud Native (§13)** als theoretischer Unterbau — gleiche Tai-Linie. Einsatz: Architekturentscheidungen begründen.
- **Cross:** „quality-driven assessment" = Benchmarking-Methodik (**CSB/📊**); dokumentiere Messungen nach Bermbach-Regeln, dann ist das Projekt thesis-zitierfähig.

## 15. Forschungsseminar Datenintegration und Datenaufbereitung ([#41218](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41218&version=2), 3 LP, WiSe+SoSe, Portfolio, Abedjan)

**Modulprofil (lt. Katalog):** Forschungsseminar, an eine **Masterarbeit** im Bereich Datenverwaltungssysteme (Abedjans D2IP-Gruppe) gekoppelt — Exposé präsentieren, Seminarteilnahme, Abschluss-Ergebnisse vorstellen. Deutschsprachiges Pendant zum Data Integration Seminar; Abedjans Kernthema (Data Profiling/Cleaning/Integration).

- 📚 **Abedjan/Golab/Naumann/Papenbrock, „Data Profiling" (Synthesis Lectures)** — wie bei **DI:AS (§6)**: vom Seminarleiter, die thematische Grundlage. Einsatz: Hauptlektüre.
- 📄 **Aktuelle Venues für die Paper-Auswahl:** VLDB, SIGMOD, ICDE (Data Integration / Preparation / Cleaning Tracks). Einsatz: das Exposé an einem aktuellen Paper dieser Konferenzen aufhängen.
- 🛠 **Praxis-Tools:** Deequ/PyDeequ (Datenqualität, Schelter), skrub, OpenRefine — passend zum Datenaufbereitungs-Fokus. Einsatz: für den praktischen Teil/die begleitete Thesis.
- 🎓 **Paper-Reading-Methodik:** Keshav, „How to Read a Paper" (s. ML&DMS §10) + HPI-Naumann-Folien (s. DI:AS §6). Einsatz: für Exposé und Präsentation.
- **Cross:** identisches Fundament wie **DI:AS (§6)** — wer DI:AS belegt, hat das Seminar inhaltlich halb erledigt. Hinweis: explizit **thesis-begleitend** → an deine DEEM/DAMS-Thesis koppeln.

---

## Querverbindungen (so verzahnt sich der Block)

1. **Engine-Linie:** DBT (Theorie) → DBTLAB (selbst bauen) → DMH (schnell machen) → Thesis. RookieDB/BusTub im Sommer vor M3 ist die Investition mit dem höchsten Return.
2. **Integrations-Linie:** DILA (Böhm, Breite) ↔ DI:AS (Abedjan, Algorithmen-Tiefe) teilen sich Doan/Halevy/Ives und das Cleaning-Buch — im selben WiSe belegen spart real Lesezeit.
3. **DEEM-Linie:** EDML → MLMMI → RDE-Projekt → Thesis. Gemeinsamer Kanon: Schelter-Papers (Deequ, mlinspect), Hidden Technical Debt, DCAI-Kurs, Huyen-Buch. **mlinspect lesen = Stratum verstehen.**
4. **Evaluations-Handwerk** (Gregg, Benchmarking-Methodik) zieht sich von DMH über CSB bis zur Thesis-Evaluation — einmal lernen, vierfach nutzen.

> **Pflege:** Kurs-URLs mit Semester im Pfad (TUM, Böhm, CS186) beim tatsächlichen Modulstart auf den dann aktuellen Jahrgang prüfen. Tote Links → hier korrigieren, nicht nur im Kopf.

---

## Mega-Sweep-Nachtrag (2026-06-11): Übungen, Klausuren & Code-Repos

> Ergänzung auf Arams Wunsch: Übungsmaterial mit Lösungen, fremde Klausurarchive, Open-Source-Repos zum Architektur-Lernen. Quellen u. a. [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) („Build your own Database") und Arams `Ultimate-Index.md`.

### Übungsblätter & Klausuren anderer Unis

- 📝 **CMU 15-445: Past Exams** — auf [15445.courses.cs.cmu.edu](https://15445.courses.cs.cmu.edu/) verlinken die Jahrgänge Midterm/Final-Archive (teils mit Lösungen). Die Fragenformate (B+Tree-Operationen durchspielen, Join-Kosten rechnen, Lock-Schedules prüfen) sind exakt das DBT-Klausurformat. Einsatz: 2–3 Exams unter Zeitdruck vor der DBT-Klausur.
- 📝 **Berkeley CS186: Discussion Worksheets + Exam-Archiv** — die Kursseiten je Semester ([cs186berkeley.net](https://cs186berkeley.net/)) veröffentlichen Worksheets **mit Lösungen** und Altklausuren; zusätzlich führt das Berkeley-HKN-Archiv ältere CS186-Klausuren. Bestes frei verfügbares Rechentraining für Selektivitäten/Selinger-Optimierung.
- 📝 **MIT 6.5830: Practice Quizzes** — auf der [Assignments-Seite](https://dsg.csail.mit.edu/6.5830/assign.php) liegen Übungs-Quizzes + ältere Quizzes mit Lösungen; zusätzlich [6.830 Fall 2010 auf OCW](https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/) mit kompletten Psets/Exams (aus deinem Ultimate-Index: MIT-OCW-Schiene).
- 📝 **Flink Training Exercises** — [github.com/apache/flink-training](https://github.com/apache/flink-training): offizielle Übungsaufgaben **mit Lösungs-Branches** (Event Time, Windows, State). Das praktische MDS-Pflichttraining.

### Open-Source-Repos zum Engine-Verständnis (DBT/DBTLAB/DMH)

- 🛠 **cstack/db_tutorial** — [github.com/cstack/db_tutorial](https://github.com/cstack/db_tutorial): „Let's Build a Simple Database" (SQLite-Klon in C, Schritt für Schritt — der build-your-own-x-Klassiker). Einsatz: Wochenend-Warm-up vor DBTLAB; B-Tree + Pager from scratch.
- 🛠 **skyzh/mini-lsm** — [github.com/skyzh/mini-lsm](https://github.com/skyzh/mini-lsm): geführtes Tutorial, eine LSM-Storage-Engine in Rust zu bauen (vom BusTub-TA). Moderne Storage-Seite, die RookieDB nicht abdeckt.
- 🛠 **erikgrinaker/toydb** — [github.com/erikgrinaker/toydb](https://github.com/erikgrinaker/toydb): verteilte SQL-DB in Rust mit *exzellent dokumentierter Architektur* (Parser→Planner→Optimizer→Executor→Raft) — als Lese-Repo ideal, um eine komplette Engine-Pipeline zu sehen.
- 🛠 **risinglightdb/risinglight** — [github.com/risinglightdb/risinglight](https://github.com/risinglightdb/risinglight): educational OLAP-DB in Rust (vektorisierte Execution!) — die DMH-Konzepte (Spaltenlayout, Vektorisierung) in lesbarem Code.
- 🛠 **Apache Calcite** — [github.com/apache/calcite](https://github.com/apache/calcite): der Industrie-Standard-**Query-Optimizer** in Java (regelbasiert + Cascades-artig). **Für Stratum das wichtigste Lese-Repo dieser Liste**: so sieht produktionsreife Rewrite-Infrastruktur aus; Java passt zu DBTLAB.
- 🛠 **DuckDB** — [github.com/duckdb/duckdb](https://github.com/duckdb/duckdb): moderne In-Process-OLAP-Engine; Optimizer- und Vektorisierungs-Code kompakt genug zum Studieren; dazu der lesenswerte [DuckDB-Blog](https://duckdb.org/news/) (Pushdown, Out-of-Core-Joins).
- 🛠 **DataFusion** — [github.com/apache/datafusion](https://github.com/apache/datafusion): Andy Groves Buch (s. o.) als reales Projekt — logische/physische Pläne + Optimizer-Rules in Rust.

### DEEM-Orbit-Repos (EDML/MLMMI/Thesis)

- 🛠 **stefan-grafberger/mlinspect** — [github.com/stefan-grafberger/mlinspect](https://github.com/stefan-grafberger/mlinspect): der Code zum mlinspect-Paper (DAG-Extraktion aus nativen ML-Pipelines) — **das architektonisch Stratum-ähnlichste öffentliche Repo**; lesen, bevor du Thesis-Design-Entscheidungen triffst.
- 🛠 **awslabs/deequ** (+ **python-deequ**) — Schelters Data-Quality-System im Produktionszustand; Test-Suite zeigt, wie man Datenqualitäts-Checks API-fähig macht.
- 🛠 **skrub-data/skrub** — [github.com/skrub-data/skrub](https://github.com/skrub-data/skrub): kennst du aus dem Job — hier als Lern-Referenz gelistet, wie sklearn-kompatible Pipeline-APIs designt werden.

### Generalfundament (aus deinem Ultimate-Index übernommen)

- 🎓 **MIT 6.824 (OCW + aktuelle pdos-Seite)** — bereits in §9 verankert; dein Index bestätigt die OCW-Edition als Einstieg.
- 📚 **OSTEP** ([pages.cs.wisc.edu/~remzi/OSTEP](https://pages.cs.wisc.edu/~remzi/OSTEP/)) — OS-Grundlagen (Scheduling, Memory, Concurrency, Persistence) mit **Übungs-Homeworks + Simulatoren im Repo**; das fehlende Fundament unter DBT-Buffer-Management und DMH. Einsatz: gezielt die Persistence-/Concurrency-Kapitel.
- 🎓 **MIT Missing Semester** ([missing.csail.mit.edu](https://missing.csail.mit.edu/)) — Shell/Git/Debugging-Handwerk mit Übungen; vor DBTLAB-Semestern als Werkzeug-Check.
