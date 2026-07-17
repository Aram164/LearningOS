# MASTERS-BENCHMARKING-RESOURCES — Lernbibliothek für den 📊 Benchmarking & Reproducible-Evaluation-Block

> **Stand:** 2026-06-11 · Phase 2, Teil 6/6 — **damit sind alle sechs Achsen abgedeckt.** (Achse 📊 aus `MASTERS-MODULE-MENU.md`: CSB, Scalability Engineering, Sustainable Computing + Cross-Tag ROC hier voll ausgearbeitet; AE II → `MASTERS-ALGO-RESOURCES.md` §6, DMH → `MASTERS-DATAENG-RESOURCES.md` §3)
> **Modulprofile aus den offiziellen Lehrinhalten im 888-S.-Modulkatalog.** Konvention: 🎓 Vorlesung · 📚 Buch · 📄 Paper/Skript · 🛠 Hands-on, mit Einsatz-Timing.
> **Warum diese Achse strategisch ist:** „Performance benchmarking and reproducible systems evaluation" ist dein erklärtes Profilziel — und die Evaluations-Kapitel der Thesis (Benchmark-Suite, Baselines, Ablationen) werden mit genau diesem Handwerk geschrieben. Alles hier zahlt doppelt: Modulnote + Thesis-Qualität.

---

## 1. CSB — Cloud Service Benchmarking ([#41035](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41035&version=4), 6 LP, WiSe+SoSe, **Portfolio**, Bermbach, max 20)

**Modulprofil (lt. Katalog):** Grundlagen + **gesamter Benchmarking-Lifecycle**, als **Flipped Classroom über ein Buch** + individuelles Benchmarking-Projekt. Der Modultext verlinkt die Buch-Website selbst: [cloudservicebenchmarking.github.io](https://cloudservicebenchmarking.github.io/).

- 📚 **Bermbach/Wittern/Tai, „Cloud Service Benchmarking: Measuring Quality of Cloud Services from a Client Perspective" (Springer)** — **das Kursbuch, vom Dozenten, explizit im Modultext genannt** ([Begleit-Website](https://cloudservicebenchmarking.github.io/)). Benchmark-Design (Qualitäten, Workloads, Metriken), Ausführung (Verteilung, Störfaktoren), Analyse, Wiederholbarkeit. Einsatz: **vor** Semesterstart komplett lesen — der Kurs ist flipped, d. h. wer das Buch kennt, hat den Kurs halb bestanden; via TU-Bibliothek (SpringerLink) kostenlos.
- 📚 **Raj Jain, „The Art of Computer Systems Performance Analysis"** — die zeitlose Methodik-Bibel: Metrikwahl, Workload-Charakterisierung, experimentelles Design (Faktorenanalyse), häufige Benchmarking-Fehler („common mistakes" — als Checkliste Gold wert). Einsatz: Kapitel 1–3 + 14–22 (Experimente/Statistik) fürs Portfolio-Projekt; die Common-Mistakes-Liste vor jeder Messung durchgehen.
- 📄 **Methodik-Papers mit Biss:** Georges et al., „Statistically Rigorous Java Performance Evaluation" (OOPSLA 2007) · Kalibera/Jones, „Rigorous Benchmarking in Reasonable Time" · Huppler, „The Art of Building a Good Benchmark" (TPCTC 2009) · Hoefler/Belli, „Scientific Benchmarking of Parallel Computing Systems" (SC 2015 — die 12 Regeln!). Einsatz: Pflichtkanon für saubere Messung (Warmup, Varianz, Konfidenzintervalle) — wörtlich wiederverwendbar im Thesis-Evaluationskapitel.
- 🛠 **YCSB** ([github.com/brianfrankcooper/YCSB](https://github.com/brianfrankcooper/YCSB)) + **TPC-Benchmarks** ([tpc.org](https://www.tpc.org/)) — der Standard-Workload-Generator für Cloud-/Storage-Dienste (Original-Paper: Cooper et al., SoCC 2010) und die DB-Industrie-Benchmarks (TPC-C/H/DS — Letztere kennst du aus dem DIMA-Umfeld). Einsatz: YCSB einmal gegen zwei Datastores fahren = Mini-Generalprobe fürs Portfolio-Projekt.
- 📚 **Brendan Gregg, „Systems Performance"** (s. `MASTERS-DATAENG-RESOURCES.md` §3) — die Mess-Werkzeugseite (USE-Methode, Profiling). Einsatz: Doppelnutzung DMH↔CSB; einmal anschaffen.

## 2. Scalability Engineering ([#41241](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41241&version=1), 6 LP, SoSe, **Portfolio**, Bermbach, max 30)

**Modulprofil (lt. Katalog):** Grundkonzepte von Skalierbarkeit (**Koordinationsvermeidung** über Maschinengruppen) für zustandslose/zustandsbehaftete Systeme; **Patterns wie Constant Load, Retry with Exponential Backoff**; **Case Studies** existierender Systeme.

- 📄 **AWS Builders' Library** — [aws.amazon.com/builders-library](https://aws.amazon.com/builders-library/) (frei). Essays von Amazon-Principal-Engineers zu exakt den Modul-Patterns: „Timeouts, Retries, and Backoff with Jitter", **„Reliability, Constant Work, and a Good Cup of Coffee" (= das Constant-Load-Pattern!)**, „Avoiding Insurmountable Queue Backlogs". Einsatz: Hauptquelle neben den Folien — die Modulsprache stammt erkennbar aus dieser Praxiswelt.
- 📚 **Nygard, „Release It! (2. Aufl.)"** — der Patterns-Katalog für Stabilität unter Last: Circuit Breaker, Bulkheads, Backpressure, Retry-Strategien. Einsatz: die Stability-Patterns-Kapitel; Portfolio-Diskussionen („warum kippt System X?") argumentieren in genau diesem Vokabular.
- 📚 **Kleppmann, DDIA** (s. `MASTERS-DATAENG-RESOURCES.md` §9) — Partitionierung, Replikation, Koordination (Kap. 5–9) = die theoretische Unterfütterung der Koordinationsvermeidung. Einsatz: Doppelnutzung LDE/MDS↔hier; das Buch trägt inzwischen vier Module deines Plans.
- 📚🎓 **Google SRE Book** — [frei, sre.google/books](https://sre.google/books/). Kapitel zu Load Balancing, Overload-Handling, Cascading Failures — die Betriebssicht auf dieselben Patterns. Einsatz: Auswahl-Kapitel als Zweitperspektive.
- 📄 **Zwei Denk-Papers:** Fox/Brewer, „Harvest, Yield, and Scalable Tolerant Systems" (1999) und **McSherry/Isard/Murray, „Scalability! But at what COST?" (HotOS 2015)** — Letzteres misst, wann „skalierbare" Systeme langsamer sind als ein Laptop-Thread: die perfekte Brücke zwischen diesem Modul und kritischem Benchmarking (§1). Einsatz: beide kurz, beide prägend; COST gehört in jedes Evaluations-Mindset (und in deine Thesis-Diskussion).
- 🛠 **Case-Study-Fundus:** Architektur-Postmortems und „How X scales"-Artikel ([highscalability.com](http://highscalability.com/)-Archiv, Engineering-Blogs von Netflix/Cloudflare/Discord). Einsatz: Material für den Case-Study-Teil des Moduls — eine fremde Architektur entlang der Pattern-Checkliste sezieren ist die typische Portfolio-Aufgabe.

## 3. Sustainable Computing ([#41255](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41255&version=2), 6 LP, WiSe, **Portfolio**, Tai, max 36)

**Modulprofil (lt. Katalog):** Umweltverträgliche Gestaltung/Nutzung von Hard-/Software, Fokus Cloud: **systemweite Energiemessung, energiebewusste Softwarearchitektur & (Re-)Design, digitale Carbon-Accounting-Systeme**, Einfluss von KI/Blockchain — Vorlesung + **Seminarforschung**.

- 🎓 **Green Software Foundation, „Green Software Practitioner"** — [learn.greensoftware.foundation](https://learn.greensoftware.foundation/) (frei, ~6h) + die **SCI-Spezifikation** (Software Carbon Intensity). Die Industrie-Begriffsbasis für Carbon Accounting von Software — exakt der Modulblock „digitale Carbon-Accounting-Systeme". Einsatz: vor Semesterstart als Vokabel-Grundierung.
- 📚 **Currie/Hsu/Bergman, „Building Green Software" (O'Reilly 2024)** — das praxisnahe Buch zu energiebewusster Architektur, Carbon-Aware-Scheduling, Messung — deckt die Architektur-/Redesign-Hälfte des Moduls. Einsatz: Hauptbegleitbuch.
- 📄 **Forschungskanon fürs Seminar:** Gupta et al., **„Chasing Carbon: The Elusive Environmental Footprint of Computing" (HPCA 2021)** — das Paper, das embodied vs. operational Carbon etabliert hat · Patterson et al., „Carbon Emissions and Large Neural Network Training" (2021) + Follow-up „…Will Plateau, Then Shrink" — die ML-Energie-Debatte (dein Profil-Link!) · Strubell et al., „Energy and Policy Considerations for Deep Learning in NLP" (ACL 2019). Einsatz: Seminar-Referenzrahmen; für dich ist die ML-Trainings-/Inference-Energie-Schiene der natürliche Vortragswinkel.
- 📄 **HotCarbon Workshop** — [hotcarbon.org](https://hotcarbon.org/) (Proceedings frei). Die aktuelle Forschungsfront kompakt (Carbon-Aware-Scheduling, Energie-Messung, Wasserverbrauch). Einsatz: Themenquelle für den Seminarteil — ein frisches HotCarbon-Paper referieren schlägt jedes Lehrbuchthema.
- 🛠 **Messwerkzeuge:** Intel RAPL (via `perf`/powercap) für systemnahe Energiemessung · **CodeCarbon** ([codecarbon.io](https://codecarbon.io/)) für ML-Workload-Tracking · Cloud-Carbon-Footprint-Tools (cloudcarbonfootprint.org). Einsatz: fürs Portfolio einmal real messen statt schätzen — systemweite Energiemessung ist der explizite Modulblock; RAPL-Erfahrung verbindet zudem zurück zu DMH.
- ⚠ **Einordnung:** Tai (ISE-Lehrstuhl, Bermbach-Orbit) — methodisch dieselbe Mess-Schule wie CSB; wer beide nimmt, recycelt das halbe Methodik-Toolkit.

## 4. ROC — Foundations for Graduate Research in DM & ML Systems ([#41135](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41135&version=5), 9 LP, WiSe, **Portfolio**, Markl, **max 8!**)

**Modulprofil (lt. Katalog):** **Contemporary Research Method (CRM)**: wissenschaftliches **Lesen, Schreiben, Präsentieren, Prototyping, experimentelles Design**; danach Lese-/Präsentationszyklen zu Datenmanagement-Themen (**Storage/Indexing, Kompilierung von Datenanalyseprogrammen, Anfrageoptimierung & Self-Tuning, adaptive Methoden, Data-Science-Pipelines, Responsible DM**) + **Laborkomponente mit wissenschaftlichem Bericht**. Faktisch: DIMAs Research-Onboarding — die formalisierte Version dessen, was du bei DEEM ohnehin tust.

- 📄 **Handwerks-Trio fürs CRM-Modul:** Keshav, „How to Read a Paper" (s. `MASTERS-DATAENG-RESOURCES.md` §10) · **Simon Peyton Jones, „How to Write a Great Research Paper"** ([Talk + Folien frei, Microsoft-Research-Seite](https://simon.peytonjones.org/great-research-paper/)) · Zobel, „Writing for Computer Science" (Springer, via TU-Bib). Einsatz: die ersten zwei sofort (zusammen <2h), Zobel als Begleiter beim Laborbericht.
- 📚 **Bailis/Hellerstein/Stonebraker (Hrsg.), „Readings in Database Systems" (Red Book, 5. Aufl.)** — [komplett frei, redbook.io](http://www.redbook.io/). Der kuratierte Paper-Kanon zu genau den ROC-Diskussionsthemen (Storage, Optimierung, Adaptivität) mit Stonebraker-Kommentaren. Einsatz: pro ROC-Themenwoche das passende Red-Book-Kapitel als Einstieg, dann das Originalpaper.
- 📄 **Themen-Anker für die Lesezyklen:** Hellerstein et al., „Architecture of a Database System" (s. DBT) · Pavlo et al., „Self-Driving Database Management Systems" (CIDR 2017) — Self-Tuning/adaptive Methoden · Chaudhuri/Narasayya, „Self-Tuning Database Systems: A Decade of Progress" (VLDB 2007) · für Data-Science-Pipelines + Responsible DM: Schelters Deequ/mlinspect (s. EDML) — **deine Heimat-Themen.** Einsatz: in den Präsentationsslots die Pipeline-/Optimizer-Themen besetzen — da referierst du aus erster Hand.
- 📄 **Experimentelles Design & Reproduzierbarkeit:** McGeoch, „A Guide to Experimental Algorithmics" (s. `MASTERS-ALGO-RESOURCES.md` §6) · **ACM-Artifact-Badging / SIGMOD Availability & Reproducibility Initiative** ([sigmod.org/sigmod-reproducibility](https://reproducibility.sigmod.org/)) · Hoefler/Belli (s. §1). Einsatz: die Labor-Komponente nach diesen Standards aufsetzen (Skripte, Seeds, Umgebung dokumentiert) — das ist wörtlich das Reproducibility-Profilziel deiner Achse.
- ⚠ **Kapazität max 8 + WiSe + 9 LP:** ROC konkurriert im Plan mit DBTLAB um den M3-Brocken-Slot (Regel: nie zwei Implementierungs-Brocken). Es ist der DIMA-Weg zur Thesis — dein Default bleibt der DEEM-Weg (EDML → RDE-Projekt); ROC ist die Markl-Alternative, falls die DEEM-Plätze scheitern.

## 5. Internet and Network Measurement and Evaluation ([#41247](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=41247&version=1), 6 LP, Portfolio, Schmid)

**Modulprofil (lt. Katalog):** Wie sieht Internet-/Datacenter-Verkehr aus, welche charakteristischen Eigenschaften? **Wie misst man im Internet?** Wo/wie lässt sich das Internet verbessern und wie testet man Verbesserungen? Schmids Mess-/Evaluationsmethodik — die Netzwerk-Sicht auf deine reproducible-evaluation-Achse.

- 📚 **Crovella/Krishnamurthy, „Internet Measurement: Infrastructure, Traffic and Applications" (Wiley)** — das Standardlehrbuch zur Internet-Messung. Einsatz: Hauptbuch.
- 📄 **Paxson, „Strategies for Sound Internet Measurement" (IMC 2004)** — wie man messmethodisch sauber arbeitet (Kalibrierung, systematische Fehler, Fallstricke). Einsatz: Pflicht — das methodische Rückgrat, exakt dein 📊-Profilziel.
- 🛠 **Mess-Infrastruktur:** RIPE Atlas + CAIDA-Datensätze/Tools — reale Messung statt Theorie. Einsatz: für den praktischen Teil/das Portfolio.
- 📄 **Coordinated Omission (Gil Tene)** (s. Mega-Sweep unten) — Latenz-Messfehler, der auch Netzwerk-Benchmarks betrifft. Einsatz: Querbezug zur restlichen 📊-Methodik.
- **Cross:** dieselbe Methodik-Linie wie **CSB/ScalEng** (Jain, Hoefler, SIGMOD-Reproducibility, §1–§4); Schmid-Modul, ergänzt **Datacenter Networking** (DSN-Annex) und Schmids Algorithms-for-Networked-Systems (`MASTERS-ALGO-RESOURCES.md` §9).

## 6. Advanced Topics in Scalable Software Systems ([#40924](https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?nummer=40924&version=4), 3 LP, Portfolio, Bermbach) — Seminar

**Modulprofil (lt. Katalog):** Geführte Literaturrecherche zu aktuellen Themen der **3S-Gruppe (Bermbach)**, teils kleine Implementierung. Klein (3 LP), Seminarcharakter.

- 📚 **Basis = ScalEng/CSB-Ressourcen (§1–§2)** — selbes Lehrstuhl-Orbit; AWS Builders' Library, Nygard „Release It!". Einsatz: Hintergrund für die Themenwahl.
- 📄 **Venues:** SoCC, Middleware, ICDCS — daraus zieht das Seminar; pro Thema das Quellpaper. Einsatz: Vortragsvorbereitung.
- **Cross:** Mini-Vertiefung neben CSB/ScalEng; Gegenstück zu „Hot Topics in Scalable Software Systems" (§1b).

---

## Querverbindungen (so verzahnt sich der 📊-Block — und die ganze Serie)

1. **Die Bermbach-Schiene:** CSB (WiSe/SoSe) → Scalability Engineering (SoSe) → Sustainable Computing (Tai, WiSe) teilen Mess-Methodik, Cloud-Kontext und Lehrstuhl-Orbit — Methodik-Toolkit einmal aufbauen, dreimal ernten.
2. **Der Methodik-Kanon der gesamten Achse** (Jain · McGeoch · Hoefler/Belli · Georges · COST) ist identisch mit dem Handwerk deines Thesis-Evaluationskapitels: Benchmark-Suite, Baselines, Varianzkontrolle, ehrliche Limitierungen. Diese Achse *ist* die Thesis-Vorschule.
3. **Cross-Tag-Einlösung:** AE II (⚙️, McGeoch) = experimentelle Algorithmik · DMH (🔧, Gregg/perf) = Mikro-Messung · Adversarial ML (🤖, Carlini/Rieck) = Evaluations-Ehrlichkeit · ROC = wissenschaftliche Verpackung. Vier Achsen, ein Skill.
4. **ROC vs. DEEM-Pipeline:** beide führen zur Thesis — ROC über Markl/DIMA (max 8!), EDML+RDE-Projekt über Schelter/DEEM (Default). Nicht beide einplanen; ROC als dokumentierter Fallback.
5. **Serie komplett:** 🔧 🤖 🧮 ⚙️ 🚀 📊 — alle sechs Achsen-Bibliotheken liegen in `Masters-Planning/`. Einstieg immer über `MASTERS-MODULE-MENU.md` → Achsen-Datei → Modul.

> **Pflege:** cloudservicebenchmarking.github.io, Builders' Library und HotCarbon sind stabil; GSF-Kurs-URL gelegentlich prüfen. Tote Links hier korrigieren.

---

## Mega-Sweep-Nachtrag (2026-06-11): Übungen, Werkzeuge & Code-Repos

> Klausuren gibt es für diese Portfolio-Achse kaum — der Übungsersatz ist hier *Werkzeug-Praxis*: einmal sauber messen schlägt zehn Altklausuren.

### Benchmark-Frameworks zum Lesen & Benutzen

- 🛠 **cmu-db/benchbase** — [github.com/cmu-db/benchbase](https://github.com/cmu-db/benchbase): das CMU-Multi-DBMS-Benchmark-Framework (TPC-C, YCSB, 20+ Workloads gegen beliebige JDBC-DBs). **Das beste Lese-Repo dafür, wie man ein Benchmark-Harness architektonisch baut** (Workload-Treiber, Raten-Steuerung, Metrik-Sammlung) — Java, passt zu deinem DBTLAB-Stack. Einsatz: CSB-Portfolio-Vorbild.
- 🛠 **giltene/wrk2** — [github.com/giltene/wrk2](https://github.com/giltene/wrk2): Lastgenerator mit korrekter Latenz-Messung; dazu Gil Tenes Vortrag **„How NOT to Measure Latency"** (YouTube) — *Coordinated Omission* ist der häufigste Benchmarking-Fehler überhaupt und gehört in jedes CSB-Portfolio-Diskussionskapitel.
- 🛠 **Microbenchmark-Harnesses:** **JMH** (Java — Pflicht, wenn du DBTLAB-Komponenten misst) · **google/benchmark** (C++) · **criterion.rs** (Rust) · **hyperfine** (CLI). Einsatz: je Sprache das Harness einmal beherrschen; sie kodifizieren Warmup/Statistik aus Georges et al. (s. §1).
- 🛠 **brendangregg/FlameGraph + perf-Beispiele** — [github.com/brendangregg/FlameGraph](https://github.com/brendangregg/FlameGraph): Profiling-Visualisierung als Standard-Artefakt für Portfolio-Berichte und Thesis-Plots.
- 🛠 **MLPerf (MLCommons)** — [mlcommons.org](https://mlcommons.org/): die Industrie-Benchmarks für Training/Inference inkl. öffentlicher Regeln + Submissions-Repos — **die ML-Systems-Seite des Benchmarking** (dein Profil-Schnittpunkt 📊×🤖); MLPerf-Methodik (Ergebnis-Normierung, Division-Regeln) ist Seminar-/Portfolio-Material erster Güte.
- 🛠 **TPC-Kits + DuckDB-tpch/tpcds-Extensions** — TPC-H/DS-Datengeneratoren praktisch nutzen (DuckDB hat beide eingebaut — `CALL dbgen(sf=1)`): in Minuten reproduzierbare Analytics-Benchmarks für eigene Experimente.

### Reproduzierbarkeit konkret

- 🛠 **ACM/SIGMOD-Artefakt-Praxis als Übung:** ein eigenes Mini-Experiment nach [SIGMOD-Reproducibility-Regeln](https://reproducibility.sigmod.org/) verpacken (Dockerfile, Seeds, `run_all.sh`, README mit Hardware-Angabe) — einmal durchgespielt, ist das Thesis-Artefakt später Routine.
- 🛠 **CodeCarbon / Scaphandre / Kepler** — Energie-Mess-Stack für SustComp-Portfolios: [codecarbon](https://github.com/mlco2/codecarbon) (ML-Workloads), [hubblo-org/scaphandre](https://github.com/hubblo-org/scaphandre) (RAPL-Agent), [sustainable-computing-io/kepler](https://github.com/sustainable-computing-io/kepler) (K8s) — drei Ebenen derselben Messfrage.
- 📄 **SPEC-Methodik-Dokumente** ([spec.org](https://www.spec.org/)) — Run-and-Reporting-Rules der SPEC-Benchmarks als Vorbild dafür, wie man Messregeln *spezifiziert* — ROC-/Thesis-relevant.

### Aus deinem Ultimate-Index integriert

- 🎓 **MIT Missing Semester** — Shell/Tooling-Übungen: die Voraussetzung, um Messpipelines (tmux, ssh, Skripting) überhaupt sauber zu fahren; bereits in der 🔧-Datei, gilt hier doppelt.
- 📚 **OSTEP-Homeworks** — die Simulator-Übungen zu Scheduling/Memory erklären, *was* man bei Systemmessungen eigentlich sieht (Context-Switch-Kosten, Cache-Effekte).

> Einordnung: Cloud-/IoT-/Security-Kurse aus dem Ultimate-Index (Yonsei, Colorado, VMware, Palo Alto) sind Zertifikats-/Überblicksniveau — für diese Achse bewusst nicht aufgenommen.
