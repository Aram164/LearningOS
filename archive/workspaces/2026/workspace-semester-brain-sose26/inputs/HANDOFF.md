# Handoff — SoSe 2026 Semester Brain

> **Created:** 2026-05-21 (KW 21)
> **Purpose:** This file lets a fresh Cowork project pick up the entire semester planning system. Read this first, then SEMESTER-STATUS.md for current state.

---

## Who You're Working With

**Aram Aljanadi** (aramaljanadi2003@gmail.com) — MSc student at HU Berlin + TU Berlin (SoSe 2026), specializing in ML x Data Engineering. Intermediate C++, learning Python via Fluent Python, near-zero ML background at semester start. Prefers ambitious pacing — stay ahead of lectures when possible. Does not want excessive hand-holding but appreciates structured guidance.

---

## The System Architecture

This folder (`semestercontext/`) is the single source of truth for Aram's entire semester. It contains course materials, project repos, and planning documents. A multi-chat Cowork system manages different study areas, coordinated by a central "brain" document.

### Core Planning Files (read these)

| File | Purpose |
|---|---|
| **SEMESTER-STATUS.md** | **THE BRAIN.** Central control plane, live state only: open loops (§0.5), progress tracker, dependency map, priority stack, weekly load planner, neglect detection. Read this first after HANDOFF.md. |
| **SESSION-LOG.md** | The archive: session log + adjustment log (split from the brain KW 27). Append one entry after every work session. |
| **CHAT-DIVISION.md** | Defines what each chat covers, its plan file, step ID prefix, and active weeks. Reference when opening any chat. |
| **Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md** | Foundations: AML lectures + SaD lectures + ISLP textbook. Block-by-block reading plan with strict prerequisite ordering. Step prefix: **F** |
| **Plans/ML/systems/Chat2_AMLS_Theory_Plan.md** | AMLS lecture content (systems architecture, compilation, parallelism). Step prefix: **S** |
| **Plans/ML/systems/Chat3_AMLS_Project_Plan.md** | AMLS exercise: AI Image Detection (Tasks 1.1–1.4, CNN, report, Docker). Step prefix: **P** |
| **Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md** | PPDS project: building the `mlprov` provenance library. Step prefix: **M** |
| **Plans/archive/Chat5_DBT_Plan.md** | **DROPPED KW 21.** Kept for reference only. |
| **Plans/crosscutting/job/Chat6_Job_Onboarding_Plan.md** | BIFOLD/DEEM job onboarding (Stratum project). 8 phases, prerequisite-ordered. Step prefix: **JK** |
| **Chat 7 / Plans/crosscutting/seminar/Chat7_Seminar_Presentation_Sprint.md** | Seminar IuG (Prof. Vladova): Plattformregulierung. 2-week presentation sprint + peer reviews. Step prefix: **SE**. Overview in Plans/crosscutting/seminar/Chat7_Seminar_IuG_Plan.md. |
| **Chat 8 / Plans/Math/analysis/Chat8_Analysis_SaD_Plan.md** | Analysis (M2.1, **Kombimodul with SaD — one module grade**). Skript-based blocks AN.0–AN.X, MIT 18.100A + Professor Leonard mapped, 15 SaD/AML cross-wires. Step prefix: **AN**. Added KW 24; Klausur date TBD. |
| **Chat 9 / Plans/CS-Theory/algo2/Chat9_Algo2_Plan.md** | Algo 2 / AlgoDat II (Prof. Kratsch, HU). 12 topics, Moodle-verified literature (CLRS 4. Aufl. DE = EN 3rd ed + DMS + OW). **Mündliche Prüfung 30 min, 2. PZ**; Übungen ungraded. Books in `Plans/CS-Theory/algo2/Algo2/`. Step prefix: **AL**. Added KW 24; dormant until post-Jul 23. |

### Step ID Prefixes

| Prefix | Area |
|---|---|
| **F** | Foundations (AML + SaD) — Chat 1 |
| **S** | AMLS Theory — Chat 2 |
| **P** | AMLS Project — Chat 3 |
| **M** | mlprov (PPDS) — Chat 4 |
| **DL** | MIT 6.S191 supplement (integrated into Chat 1 + Chat 3) |
| **JK** | Job Onboarding — Chat 6 |
| **PY** | Python (Fluent Python) — cross-cutting |
| **SE** | Seminar IuG — Chat 7 (presentation + peer reviews) |
| **AN** | Analysis (Kombimodul with SaD) — Chat 8 |
| **AL** | Algo 2 — Chat 9 |

---

## Live State — NOT in this file (by design, since KW 27)

> **This file contains NO status, priorities, or deadlines.** All of that lives in **`SEMESTER-STATUS.md`** (dashboard §1, open loops §0.5, priorities §9, key dates §8) and changes weekly — a copy here would only drift (it did: this section once claimed KW-21 state months later). Full history: `SESSION-LOG.md`.
>
> The only durable strategy facts (also in the Memory System section below): **AML-first** (AMLS is incomprehensible without ML foundations — F blocks lead, S lags); **DBT dropped KW 21**; **AMLS project runs on internal deadlines ~4 weeks ahead of the Jul-15 submission**; **6.S191 cherry-picked** (L1, L3, Labs 1–2) and later deprioritized to DL1-prep.

---

## Supplementary Resources (links collected across sessions)

> **As of KW 24 the canonical home for ALL external learning material is `LEARNING-RESOURCES.md`** (tagged per module, includes everything below plus the topic-doc video libraries and Brandon Rohrer's blog). Add new finds there. The list below is kept as a snapshot.

### MIT 6.S191 — Introduction to Deep Learning
- **Playlist:** https://www.youtube.com/playlist?list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI
- **Course site (slides + labs):** https://introtodeeplearning.com/
- **Lab code:** https://github.com/MITDeepLearning/introtodeeplearning
- Cherry-picked: L1 (Intro), L3 (Computer Vision), Lab 1 (DL in Python), Lab 2 (Facial Detection), L8 (Parallel Training, optional)

### 3Blue1Brown — Neural Networks (4 videos)
- **KI-Campus page:** https://ki-campus.org/en/learning-opportunities/videos/neural-networks
- **YouTube playlist:** https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi
- Maps to: F.L (neural nets), F.D–E (loss/GD intuition)

### Patrick Loeber — PyTorch CNN Tutorial (CIFAR-10)
- **Video:** https://www.youtube.com/watch?v=pDdP0TFzsoQ
- **Code:** https://github.com/patrickloeber/pytorchTutorial
- Maps to: Chat 3 CNN build (same task structure as AMLS project)

### TU Python-for-ML Course
- **GitHub:** https://github.com/mahmutoezmen/Python-for-ML-Course
- Sheet 2 (Inheritance/NumPy) → Chat 4 (mlprov), Chat 6 (JK Phase 1)
- Sheet 3 (Dataset analysis) → Chat 3 (Task 1.1)
- Sheet 4 (Linear Algebra) → Chat 1 (Block E regression)
- Sheet 5 (Autograd/Numba/Cython) → Chat 1 (Block L), Chat 6 (JK Phase 4)

### SaD 2025 Lecture Videos (supplement)
- Located in `Plans/Math/sad/SaD/SaD-2025/` within this folder
- Video recordings of lectures 01–13 from WiSe 2025
- Numbering differs from 2026: see mapping table in SEMESTER-STATUS.md § 3 (DL Supplement section)
- Most useful for: L05+L06 (expected values — more depth), L09+L10 (estimation/testing), L14+L15 (neural nets — two full lectures vs one in 2026)

### Course Links
- **AMLS course page:** https://mboehm7.github.io/teaching/ss26_amls/index.htm
- **AMLS Moodle:** https://moodle.hu-berlin.de (enrollment key in Chat2 plan)
- **Seminar Moodle:** https://moodle.hu-berlin.de/course/view.php?id=138145 (key: IuG_2026)
- **Seminar topic list:** https://box.hu-berlin.de/f/c842d14d4b134aac9e5a/
- **PRISMA method:** https://www.prisma-statement.org/ (for seminar research)
- **Stratum repo:** cloned in `Plans/crosscutting/job/Job/repo/stratum/`
- **skrub repo:** https://github.com/skrub-data/skrub
- **mlprov repo:** in `Plans/ML/mlprov/PPDS ML Data Provenance/Project/`
- **AMLS project repo:** in `Plans/ML/systems/AMLS/AMLS-project/amls-project/`

---

## Directory Structure (key paths)

> **Restructured KW 24 (Jun 13, 2nd pass).** Domain-based layout: plans grouped by subject (ML, Math, CS-Theory, Libraries, Programming, crosscutting). Course folders hold only course materials. All paths are root-relative. `Plans/WIRING.md` is the cross-domain routing table. **KW 28 (Jul 10):** material folders type-normalized per the canonical layout in `LEARNING-RESOURCES.md` §0 (`Lecture-slides/` · `Buecher/`/`Books/` · `Klausuren-extern/` · `papers/` · `notes/`).

```
semestercontext/
├── HANDOFF.md                  ← This file (read first)
├── SEMESTER-STATUS.md          ← THE BRAIN (read second — live state only)
├── SESSION-LOG.md              ← session + adjustment log archive (KW 27 split)
├── tools/check_links.py        ← link-integrity check (⚠️ role covered by check_system.py + lychee since KW 28 — retire-or-keep pending, Open Loop #8)
├── lychee.toml                 ← lychee link-checker config (KW 28; validation stack = `lychee --offline .` + `Masters-Planning/tools/check_system.py`, see Masters-Planning/TOOLING.md)
├── .gitignore                  ← git adopted KW 28 — tracks the md SYSTEM only, not material archives; pre-commit hook = check_system.py (Masters-Planning/TOOLING.md §5)
├── CHAT-DIVISION.md            ← Chat scope definitions
├── LEARNING-RESOURCES.md       ← all external learning material, tagged per module (KW 24)
├── MASTERS-PROJECT-KICKOFF-PROMPT.md   ← bootstrap prompt for the Masters-Planning project
│
├── Plans/                      ← ALL plans — domain-based (see Plans/README.md)
│   ├── WIRING.md               ← cross-domain routing table (interdependency index)
│   ├── README.md               ← full index of all plan files
│   │
│   ├── ML/
│   │   ├── foundations/        ← AML (SaD moved to Plans/Math/sad/ KW 27 — still studied as a pair via Chat1 + Master Wiring)
│   │   │   ├── Chat1_Foundations_AML_SaD_Plan.md        (prefix F)
│   │   │   ├── HANDOFF-AML-SaD.md                       ← chat-level handoff: boots a fresh Chat-1 session (KW 26)
│   │   │   ├── reference/      ← AML↔SaD cross-module docs (cross-cutting ONLY)
│   │   │   │   ├── AML-SaD_Master_Wiring.md             ← THE SPINE (KW 24)
│   │   │   │   └── Regression_SaD-AML-ISLP_Bridge.md
│   │   │   │   (per-lecture references live in AML/my notes/lectNN…/; SaD deep plan in SaD/notes/)
│   │   │   ├── AML/            ← AML material (KW 28 layout): SoSe 2026/ (lecture slides VL 01–10, Exercise slides, Bonus-exercises), older lecture slides/ (incl. 11-rnn), Bücher/, CS4780-homeworks/, Klausuren-extern/, papers/, my notes/ (crosswalk + lecture units L02–L07)
│   │   ├── systems/            ← AMLS theory + project + DL supplement
│   │   │   ├── Chat2_AMLS_Theory_Plan.md                (prefix S)
│   │   │   ├── Chat3_AMLS_Project_Plan.md               (prefix P)
│   │   │   ├── DL-AMLS-Learning-Plan.md                 (two-phase DL plan)
│   │   │   └── AMLS/           ← learningcontent/ (Lecture-slides/, Buecher/, notes/ — demixed KW 28), papers/, project repo
│   │   │       └── AMLS-project/amls-project/           ← project code
│   │   └── mlprov/             ← PPDS mlprov library project
│   │       ├── Chat4_PPDS_mlprov_Plan.md                (prefix M)
│   │       └── PPDS ML Data Provenance/  ← PPDS materials + mlprov project repo
│   │
│   ├── Math/
│   │   ├── sad/                ← Statistik & Datenanalyse (Kombimodul twin of analysis; moved KW 27)
│   │   │   ├── SaD-Module-Overview.md               ← module map + unit-build order (KW 27)
│   │   │   ├── SaD_Source-Crosswalk_L01-L15.md      ← 📒🎥🧪 per-lecture source selector (KW 27)
│   │   │   └── SaD/            ← slides 01–15, exercises UE1–7, Books/Statistik.pdf, SaD-2025/, notes/
│   │   └── analysis/
│   │       ├── Chat8_Analysis_SaD_Plan.md               (prefix AN)
│   │       ├── AN_Source-Crosswalk.md                   ← per-block 📒🎥🧪 selector (KW 27)
│   │       └── Analysis/       ← tidied KW 27: Skript+HU/ · Buecher/ · Drill-Loesungen/ · Klausuren-extern/ · Strang site
│   │
│   ├── CS-Theory/
│   │   └── algo2/
│   │       ├── Chat9_Algo2_Plan.md                      (prefix AL)
│   │       └── Algo2/          ← Algo 2 books (CLRS DE, DMS, OW) + Frankfurt Klausuren
│   │
│   ├── Libraries/              ← Library-level reference (plans only, no material folder)
│   │   ├── sklearn/
│   │   │   ├── Sklearn-5h-Crash-Plan.md
│   │   │   └── Sklearn-mlprov-Object-Map.md
│   │   └── skrub/
│   │       ├── skrub-DataOp-DAG-Reference.md
│   │       └── skrub-Evaluation-Engine-Reference.md
│   │
│   ├── Programming/
│   │   ├── Git/                ← Git-GitHub-Interactive-Overview.html, Git-GitHub-Reference-by-Block.md, GIT.pdf, HU-intro-to-git.pdf
│   │   ├── python/
│   │   │   ├── Python-Intermediate-Roadmap.md
│   │   │   ├── Python-OOP-Scope-Repair-Plan.md
│   │   │   ├── Programming-Toolbox-Bootcamp.md
│   │   │   └── Python/         ← Fluent Python PDF + Python books
│   │   └── rust/
│   │       ├── Rust-Learning-Plan.md
│   │       └── Rust/           ← Comprehensive-Rust PDF + The Book epub
│   │
│   ├── crosscutting/
│   │   ├── job/
│   │   │   ├── Chat6_Job_Onboarding_Plan.md             (prefix JK)
│   │   │   └── Job/            ← papers/ + repo/
│   │   │       └── repo/stratum/                        ← Stratum repo (cloned)
│   │   └── seminar/
│   │       ├── Chat7_Seminar_IuG_Plan.md                (prefix SE, course overview)
│   │       ├── Chat7_Seminar_Presentation_Sprint.md     (prefix SE, 2-week sprint)
│   │       ├── Vortrag-Quellenpaket-und-Bauplan.md
│   │       └── Seminar/        ← deliverables/ + reference/ (split KW 28; PRISMA guide, review example)
│   │
│   └── archive/                ← superseded, kept for reference only
│       ├── Chat5_DBT_Plan.md                    (DBT dropped KW 21)
│       ├── BIFOLD-DEEM-Job-Plan.md              (superseded by Chat6 plan)
│       ├── BIFOLD-DEEM-Job-Vorbereitung-v2.md   (superseded by Chat6 plan)
│       ├── SoSe2026_Praxisplan.md               (original, superseded)
│       └── DBT/                ← DBT course materials (module dropped)
│   (deleted KW 24: ML-Semester-Master-Plan copy 2.md, SoSe2026_Theorieplan.md — superseded)
│
└── Masters-Planning/           ← whole-degree planning (own STATUS/HANDOFF, self-contained)
```

---

## Memory System (from previous project)

The previous Cowork project maintained these memories. They won't transfer automatically — the new project should rebuild them by reading this file and the plans. Key facts to internalize:

1. **AML-first strategy:** Always complete matching AML block (F.*) before deeply processing AMLS blocks (S.*). AMLS is incomprehensible without ML foundations.
2. **AMLS Project team:** 3-person team. Abdalla manages GitHub. Internal deadlines are 4 weeks early.
3. **Seminar:** Informatik und Gesellschaft, Prof. Vladova. Aram's topic: Plattformregulierung (DSA/DMA, Big Tech). Presentation Jun 18 (20 min + 10 min discussion). Oral peer review Jul 2 (Linus Kurth's talk on Desinformation/Bots). Written peer review due Jul 16 (2–4 pages).
4. **Job:** BIFOLD/DEEM, Stratum project, supervisor Arnab. 40h/month (~10h/week). Started May 5. Skrub DataOps + Stratum optimizer. 50% features, 30% skrub, 20% benchmarks.
5. **Fluent Python order:** 1→6→2→3→7→17→11→14→5→9→13→8→15→18. Done so far: Ch 1, 5, 6, 11, 14.
6. **Python-for-ML course:** 5 sheets from TU Berlin, mapped as optional supplements across Chats 1/3/4/6.

---

## How to Use This in a New Project

1. **Connect the `semestercontext` folder** as your workspace
2. **Read HANDOFF.md** (this file) — gives you the full context
3. **Read SEMESTER-STATUS.md** — gives you the live state (progress, priorities, dependencies)
4. **Read CHAT-DIVISION.md** — gives you the chat scope definitions
5. **For any specific chat topic**, read the corresponding plan file (e.g., Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md for AML/SaD study)
6. **Save memories** for the key facts in the "Memory System" section above
7. **Ask Aram for a status dump** — things may have changed since this handoff was written

---

*Generated by Hub Chat (Brain), KW 21. This file should be updated whenever major structural changes happen.*
