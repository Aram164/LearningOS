# Chat Division — SoSe 2026

> Paste the relevant section of this file when opening a new chat so Claude has immediate context.
> Update SEMESTER-STATUS.md at the end of each work session.

---

## Bootcamp Chat: "Programming Toolbox" — Shell, Git, Python Env, pytest, Docker

**Scope:** The foundation everything else rests on. Shell power-ups (pipes, grep, find), Git beyond add/commit/push, Python virtual environments, VS Code, pytest, Docker basics. Two parallel tracks: Tools (mornings) and Python on-ramp via ATBS → Fluent Python (afternoons).

**Plan file:** Plans/Programming/python/Programming-Toolbox-Bootcamp.md  
**Step ID prefix:** (none — Bootcamp steps are referenced as prerequisites, not tracked individually in SEMESTER-STATUS)

**Mode:** Hands-on exercises, tool setup.

**Active weeks:** KW 17–18. Must be done before job starts (May 5).

---

## Chat 1: "Foundations" — AML + Statistik & Data Science + Math Toolbox

**Scope:** Lecture comprehension, exercise sheets, reading guidance, exam prep for AML and SaD. Math toolbox repair (linear algebra, probability, calculus) lives here too.

**Plan file:** Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md  
**Step ID prefix:** **F** (F.A1, F.B2, F.E-test, etc.)

**Key resources:** HU AML slides (Lectures 01–11), ISLP, CS229, SaD slides (01–15 + UE2–UE7), 3Blue1Brown, Khan Academy for gaps. **MIT 6.S191** L1 (Intro to DL) integrated as supplement alongside F.D–H.

**Mode:** Theory study, problem solving, exam preparation.

**Active weeks:** KW 17–30 (AML lectures start KW 18; SaD already running).

---

## Chat 2: "AMLS Theory" — Architecture of ML Systems lectures

**Scope:** AMLS lecture content only — systems architecture, compilation, parallelism, hardware, lifecycle. Vijay's book, DLSys lectures, Chip Huyen. Cross-references to AML theory. Exam prep for the 2. Prüfungszeitraum (**moved off Jul 23 on Jun 12** — exact date TBD).

**Plan file:** Plans/ML/systems/Chat2_AMLS_Theory_Plan.md  
**Step ID prefix:** **S** (S.A1, S.B3, S.X-test, etc.)

**Key resources:** AMLS slides (L01–L13), Vijay "Intro to ML Systems," DLSys lectures (L4–L23), Chip Huyen "Designing ML Systems," AMLS course page (mboehm7.github.io).

**Mode:** Theory study, systems thinking, exam preparation.

**Active weeks:** KW 16 through 2. PZ. Lectures Thu 4–6pm (until Jul 16); S.X exam prep Aug/Sep.

---

## Chat 3: "AMLS Project" — AI Image Detection (Tasks 1.1–1.4)

**Scope:** The practical AMLS exercise — `clean.py`, `prepare.py`, `train.py`, `predict.py`, augmentation, explainability, Docker, 8-page report. All coding, debugging, and engineering decisions.

**Plan file:** Plans/ML/systems/Chat3_AMLS_Project_Plan.md  
**Step ID prefix:** **P** (P.1.1.3, P.1.2.8, P.Report, P.Docker)

**Key resources:** AMLS_2026_Exercise.pdf, project repo, scikit-learn/PyTorch docs, Docker docs. **MIT 6.S191** L3 (Deep Computer Vision) + Lab 1 + Lab 2 integrated as DL supplement before/during CNN build.

**Mode:** Coding, model training, report writing.

**Active weeks:** KW 19–29. Submission deadline: **15 Jul 2026**.

**Task roadmap:**

- Task 1.1 (15 pts): Data exploration + cleaning → `clean.py`
- Task 1.2 (35 pts): Modelling → `prepare.py`, `train.py`, `predict.py`
- Task 1.3 (30 pts): Data augmentation → `train_augmented.py`, `predict_augmented.py`
- Task 1.4 (20 pts): Explainability
- Report (8 pages) + Docker container

---

## Chat 4: "PPDS mlprov" — ML Data Provenance Project

**Scope:** The PPDS programming project — building the `mlprov` library. ProvDataFrame, sklearn wrappers, MLProvManager, provenance analyses (DataLeakage, DataUsage, Fairness), tests, documentation, presentation. *(DuckDB optimization CUT KW 24 — stretch goal only if the suite is green early. Current plan: "KW 24 SKLEARN SPRINT" section in the plan file.)*

**Plan file:** Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md  
**Step ID prefix:** **M** (M.1.0.1, M.2.2.2, M.4.3.1, M.6.5)

**Key resources:** mlprov repo (github.com/deem-teaching/2026-ppds-mlprov-students), mlinspect paper, pandas/sklearn docs, DuckDB docs, Fluent Python (for implementation patterns).

**Mode:** Coding, testing, documentation.

**Active weeks:** KW 19–29. Submission deadline: **15 Jul 2026**.

**Relation to Chat 6:** mlprov and the job share the same conceptual layer (instrumenting pandas/sklearn pipelines). Cross-references exist in both plans. Use Chat 4 for mlprov-specific implementation work; use Chat 6 for job-specific competency building (Stratum, skrub, polars, benchmarking).

---

## ~~Chat 5: "DBT" — DROPPED KW 21~~

**Status:** Dropped. Hours reallocated to MIT 6.S191 Deep Learning supplement.

**Reason:** Semester is ML-heavy; DBT was conditional. Dropping frees ~2–2.5h/week for DL content that directly supports the AMLS Project (CNN) and invests in future DL 1 course at TU.

---

## Chat 6: "Job Onboarding" — BIFOLD / DEEM / Stratum Ramp-Up

**Scope:** Dedicated onboarding for the DEEM lab job. Phase-based progression (not week-based): Stratum paper + repo orientation, DataFrame mastery (pandas/polars/NumPy profiling), skrub deep dive, Stratum internals, benchmarking methodology, C++ refresh, first contributions, Rust ramp (summer).

**Plan file:** Plans/crosscutting/job/Chat6_Job_Onboarding_Plan.md  
**Step ID prefix:** **JK** (JK.0.1, JK.1A.3, JK.3.6, JK.7.4)

**Key resources:** Stratum paper + repo, skrub docs + source, polars User Guide, pandas/NumPy docs, "Fair Benchmarking Considered Difficult" (Raasveldt), pytest-benchmark, hyperfine, Effective Modern C++, Rust Book + Rustlings + PyO3.

**Mode:** Reading source code, hands-on exercises, profiling, benchmarking, contributing patches.

**Active weeks:** KW 17 onward (prep), job starts May 5. Ongoing through semester. Rust ramp Jul–Sep.

**Relation to Chat 4:** Chat 4 is the PPDS mlprov project. Chat 6 is job competency building. They share conceptual overlap (both instrument pandas/sklearn pipelines) but have different goals: Chat 4 produces a graded deliverable, Chat 6 builds long-term job skills. Cross-references exist in both plans.

---

## Chat 7: "Seminar IuG" — Informatik und Gesellschaft

**Scope:** The seminar with Prof. Vladova. Aram's topic: **Plattformregulierung** (Sollte Big Tech stärker kontrolliert werden? — DSA/DMA, EU lens). Covers all three graded deliverables: the 20-min presentation (Jun 18), the oral peer review of Linus Kurth's talk (Jul 2), and the written peer review (2–4 pages, due Jul 16). Research, slide-building, rehearsal, and review writing.

**Plan files:** Plans/crosscutting/seminar/Chat7_Seminar_Presentation_Sprint.md (active 2-week sprint) + Plans/crosscutting/seminar/Chat7_Seminar_IuG_Plan.md (course overview)  
**Step ID prefix:** **SE** (SE.1 research, SE.2 outline, SE.3 slides, SE.4 rehearse, SE.5 oral review, SE.6 written review)

**Key resources:** Seminar Moodle (key IuG_2026), topic list (HU Box), PRISMA method, `Plans/crosscutting/seminar/Seminar/reference/REFERENZBEISPIEL_Review.pdf` (review template), `Plans/crosscutting/seminar/Seminar/reference/SystematicLiteratureReview.pdf`. Current DSA/DMA enforcement cases (2024–25: Apple/Meta/Google) for the talk.

**Mode:** Research, German-language slide-building (~12–15 slides), rehearsal, academic review writing.

**Active weeks:** KW 23–29. Presentation **Jun 18** (finish by Jun 16); oral review **Jul 2**; written review **Jul 16**.

---

## Chat 8: "Analysis" — Analysis und ihre Bezüge zur Informatik (Kombimodul with SaD)

**Scope:** The Analysis half of the SaD Kombimodul (M2.1, HU Institut für Mathematik) — two separate exams, **one module grade**. Skript work, proof technique, solved-problem drill, Klausur prep. The SaD half stays in Chat 1.

**Plan file:** Plans/Math/analysis/Chat8_Analysis_SaD_Plan.md  
**Step ID prefix:** **AN** (AN.0.1, AN.A2, AN.X-test, etc.)

**Key resources:** `Plans/Math/analysis/Analysis/Skript+HU/unser skript.pdf` (THE exam source — Exkurse excluded, Ausflüge low-priority), MIT 18.100A Real Analysis (Rodriguez — playlist + `mit18_100af20_lec_full2.pdf`, mapped lectures only), Professor Leonard Calc 1+2 (intuition layer), Strang *Calculus* (in folder), HU serie05–09 + serieWV sheets, `kleine_beweise.pdf` ⭐ (HU Tutorium exam-prep proof list), solved collections (AS-Ana1, IngMath_2, gute Aufgaben, KIT/Tutorium Reihen).

**Mode:** Theory study, proof writing, drill, exam preparation. Every block self-test includes a SaD/AML wire check (15-wire registry in the plan).

**Active weeks:** Dormant until Klausur date confirmed. Scenario 1 (late-Jul exam): KW 26–31, ~4h/wk triaged. Scenario 2 (Sept/Okt): 5-week push after Jul 23. AN.0 refresh allowed as KW 25–26 filler.

**Relation to Chat 1:** Kombimodul partner — the grade is shared. Cross-wires run both directions; SaD Block N exam prep rehearses Analysis concepts and vice versa.

---

## Chat 9: "Algo 2" — AlgoDat II (Prof. Kratsch, HU)

**Scope:** "Algorithmen und Datenstrukturen II" — 12 topics, schnellere Multiplikation through FFT. Deliberate re-learning module: Aram took it to rebuild forgotten algorithmics fundamentals — depth over speed. **Prüfung: mündlich, 30 min, Zoom (DE/EN), 2. Prüfungszeitraum (Sept/Okt)** — together with the AMLS exam (also moved to 2. PZ). Übungen ungraded.

**Plan file:** Plans/CS-Theory/algo2/Chat9_Algo2_Plan.md (Moodle-verified: per-chapter literature + recommended exercises)  
**Step ID prefix:** **AL** (AL.A1, AL.B2, AL.X2, etc.)

**Key resources:** `Plans/CS-Theory/algo2/Algo2/` folder: CLRS 4. Aufl. Deutsch (= EN 3rd ed — Standardbuch), Dietzfelbinger/Mehlhorn/Sanders (Kap. 1 → AL.A; hashing Aufgaben → AL.F), Ottmann/Widmayer (5.4 Splay → AL.E; 9.8 Matching → AL.I), EN 3rd ed parallel text. Public: Pagh [2006] Cuckoo notes, Sleator/Tarjan [1985], MIT 6.046J OCW, Erickson *Algorithms*. ⚠️ Course policy: lecture slides + UB book PDFs must not be fed into AI systems — sessions work from owned books, public papers, and Aram's own notes.

**Mode:** Theory study, proof rehearsal, hand-run drills, oral-exam prep (explain aloud).

**Active weeks:** Dormant until post-Jul 23, then ~8–10h/wk interleaved with AN + S.X. ~40–50h total.

**Relation to other chats:** FFT ↔ CNN convolutions (Chat 1 Block M); B-trees ↔ DB indexes (Chat 6 / Stratum); amortized analysis ↔ pandas/NumPy growth (Chat 4); shares the 2. PZ prep window with Chat 2 (S.X) and Chat 8 (AN).

---

## Hub Chat (this one): "Brain" — Central Planning & Coordination

**Scope:** This chat doesn't produce code or study material. It tracks progress across all chats, detects neglect, identifies blocking dependencies, and recommends priorities. It owns SEMESTER-STATUS.md.

**What to bring here:**
- "I finished steps X, Y, Z in Chat N — update status."
- "What should I work on next?"
- "Am I neglecting anything?"
- "Is my load balanced this week?"
- "I'm stuck on X in Chat N — what does this block?"

---

## Cross-Chat Protocol

**When opening a chat**, paste this and fill in:

> "Since last time I've completed [step IDs, e.g. F.A1, F.A2] in Chat [N]. See SEMESTER-STATUS.md for current state."

**At the end of each session**, ask Claude to update SEMESTER-STATUS.md:
1. Mark completed steps with ✓ and the KW
2. Update § 6 Neglect Tracker
3. Update § 9 Priority Stack
4. Add a row to § 10 Session Log

**Step ID Prefixes:** F = Foundations, S = AMLS Theory, P = AMLS Project, M = mlprov, DL = MIT 6.S191, JK = Job, PY = Python, SE = Seminar IuG, AN = Analysis, AL = Algo 2

---

## Python Learning (cross-cutting, tracked in SEMESTER-STATUS.md)

Fluent Python chapter order: 1 → 6 → 2 → 3 → 7 → 17 → 11 → 14 → 5 → 9 → 13 → 8 → 15 → 18.

Python learning happens across Chats 1, 3, 4, and 6. Each chat applies Python in its domain. Progress tracked centrally in SEMESTER-STATUS.md (PY.01–PY.14).
