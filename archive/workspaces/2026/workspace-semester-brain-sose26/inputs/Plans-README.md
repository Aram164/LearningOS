# Plans/ — Index

> Restructured KW 24 (Jun 13, 2026) — domain-based layout. **Architecture formalized KW 27 (Jul 2026).**

## The 3-tier architecture

Every piece of study material lives on exactly one of three tiers:

| Tier | What | Where | Job |
|---|---|---|---|
| **1 — Master index** | ALL learning materials (books, video series, blogs, solved-exam banks), tagged per module | **`LEARNING-RESOURCES.md`** (root) | The single place new finds get logged. Nothing else duplicates its lists — lower tiers *select from* it. |
| **2 — Module plans** | One plan per module (Chat1–9) + cross-module wiring docs + per-source crosswalks | `Plans/<domain>/<module>/ChatN_*.md` · `ML/foundations/reference/` (spine + bridges) · `AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md` | What to study in which order, how modules connect, which sources cover which lecture. |
| **3 — Lecture units** | Per-lecture: **Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam** (+ bonus-sheet solution) | `ML/foundations/AML/my notes/lectNN <topic>/` · `Math/sad/SaD/notes/lectNN <topic>/` | The actual study surface. Mini Plans pull *specific* videos/readings from tiers 1–2 — scope-matched to the lecture. |

Flow: **new material → tier 1. Planning a module → tier 2. Studying a lecture → tier 3.** A tier-3 Mini Plan cites concrete lecture videos + book sections; it never re-lists whole series (that's tier 1's job).

**Single-study-script rule (KW 27):** once a lecture has a complete tier-3 unit, its **Mini Plan is the only study script** for that lecture. Module-plan block tables = step-ID ledger + pointer; Master Wiring §5 sequences apply only to lectures without units. (Prevents the "four documents describe how to study L07" problem.)

> **Layout rules:**
> - **Domain folders** (`ML/`, `Math/`, `CS-Theory/`, `Libraries/`, `Programming/`, `crosscutting/`) group content by subject area, not by chat.
> - Each domain folder has **one subdirectory per module/language/library** with its plan(s) inside.
> - **`ML/foundations/reference/`** holds only *cross-module* docs (wiring spine + bridges). Per-lecture references live inside their tier-3 unit folders.
> - **`WIRING.md`** (this folder's root) is the cross-domain routing table — check it when a study session spans two domains.
> - **`archive/`** = superseded docs — never delete, move here. Redirect stubs are NOT kept — fix the links and delete (KW 27 policy).
> - All paths everywhere are root-relative (e.g. `Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md`).
> - Brain files stay at root: HANDOFF.md, SEMESTER-STATUS.md, CHAT-DIVISION.md, LEARNING-RESOURCES.md.

---

## ML/ — Machine Learning

### ML/foundations/ — AML + SaD (studied as a pair)

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat1_Foundations_AML_SaD_Plan.md | 1 — Foundations (AML + SaD + ISLP) | F | active |

**Material subfolder:** `AML/` (2026 lecture slides VL 01–10 + older decks incl. 11-rnn, Bücher/, CS4780-homeworks/, Bonus-exercises, Exercise slides). *(SaD material moved to `Math/sad/` KW 27 — the study pairing with AML continues via Chat1 + Master Wiring.)*

#### ML/foundations/reference/ — AML↔SaD cross-module docs (tier 2)

| File | What it is |
|---|---|
| **AML-SaD_Master_Wiring.md** | **The spine.** AML↔SaD lecture map, 4 pipelines, 18 cross-wires, session sequences |
| Regression_SaD-AML-ISLP_Bridge.md | regression deep bridge, Tiers 0–5 (Blocks E+H) |

#### ML/foundations/AML/my notes/ — AML tier-2 crosswalk + tier-3 lecture units

| Item | What it is |
|---|---|
| **AML_Book-Concept-Crosswalk_L02-L10.md** | every AML L02–L10 concept → 3 scope-flagged layers: 📒 exact book sections/pages (7 sources) · 🎥 verified video picks · 🧪 solved-practice selector |
| `lect02 KNN-classifier/` … `lect07 linear classifiers/` | **complete units** (Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam + bonus solutions) |

### ML/systems/ — AMLS (theory + project) + DL supplement

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat2_AMLS_Theory_Plan.md | 2 — AMLS theory | S | lag mode |
| Chat3_AMLS_Project_Plan.md | 3 — AMLS project (AI Image Detection) | P | active |
| DL-AMLS-Learning-Plan.md | 1+3 supplement — two-phase DL plan | DL | Phase 1 active |

**Material subfolder:** `AMLS/` (lecture slides + `AMLS-project/amls-project/` project code)

### ML/mlprov/ — PPDS mlprov project

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat4_PPDS_mlprov_Plan.md | 4 — PPDS mlprov library | M | active sprint |

**Material subfolder:** `PPDS ML Data Provenance/` (PPDS course materials + mlprov project repo)

---

## Math/ — Mathematics

### Math/sad/ — Statistik & Datenanalyse (Kombimodul with Analysis; moved here KW 27)

| File | What it is |
|---|---|
| **SaD-Module-Overview.md** | module map, exam clusters, unit-build priority order (12 → 14 → 15-half; 06–10 covered by the deep plan) |
| **SaD_Source-Crosswalk_L01-L15.md** | 📒🎥🧪 per-lecture source selector (Fahrmeir/Blitzstein/OpenIntro + verified ML-half locals) |

**Material subfolder:** `SaD/` (Lecture-slides 01–15, `SaD-2025/` + UE1–7, `Books/Statistik.pdf`, `notes/` incl. the 06–10 deep plan + L11 reference)

*Study home remains Chat1 (prefix F, joint with AML); grade pairing is with `Math/analysis/` (M2.1, one grade).*

### Math/analysis/ — Analysis (Kombimodul with SaD)

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat8_Analysis_SaD_Plan.md | 8 — Analysis (Kombimodul w/ SaD — one grade) | AN | active from KW 25 |
| **AN_Source-Crosswalk.md** | per-block 📒🎥🧪 source selector, keyed to the skript (KW 27) | — | reference |

**Material subfolder:** `Analysis/` — **tidied KW 27** into `Skript+HU/` (skript ⭐ + kleine_beweise + HU Serien) · `Buecher/` (Abbott, Rudin, Lebl I+II, Ross, Forster-Wessoly, Thomas, DE notes …) · `Drill-Loesungen/` · `Klausuren-extern/` (Marburg ⭐, Regensburg ⭐, Stuttgart) · `Strang-Calculus/`

---

## CS-Theory/ — Computer Science Theory

### CS-Theory/algo2/ — AlgoDat II

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat9_Algo2_Plan.md | 9 — Algo 2 (mündl. Prüfung 2. PZ) | AL | dormant until post-Jul 23 |

**Material subfolder:** `Algo2/` (CLRS 4. Aufl. DE, DMS, OW, Kleinberg-Tardos + Frankfurt Klausuren 2021–24)

---

## Libraries/ — Library-level reference + crash plans

### Libraries/sklearn/

| File | Serves |
|---|---|
| Sklearn-5h-Crash-Plan.md | Chat 4 mlprov M.Phase 3 sprint prerequisite |
| Sklearn-mlprov-Object-Map.md | Chat 4 mlprov — sklearn class hierarchy map |

### Libraries/skrub/

| File | Serves |
|---|---|
| skrub-DataOp-DAG-Reference.md | Job (JK.2) + mlprov Phase 2 |
| skrub-Evaluation-Engine-Reference.md | Job (JK.2–3) + mlprov Phase 4 |

*(Add new library docs here: one subfolder per library, naming `<library>-<Topic>-Reference.md`.)*

---

## Programming/ — Languages & tooling

### Programming/python/

| File | What it is |
|---|---|
| Python-Intermediate-Roadmap.md | Symptom-indexed 21-step lookup map (PY prefix, FP skeleton) |
| Python-OOP-Scope-Repair-Plan.md | 5 drill sessions: scope/super()/classes |
| Programming-Toolbox-Bootcamp.md | Shell/git/pytest/Docker |

**Material subfolder:** `Python/` (Fluent Python PDF, Géron Hands-On ML, ProGit)

### Programming/rust/

| File | What it is |
|---|---|
| Rust-Learning-Plan.md | 3 phases, 17+3 steps, beginner→intermediate; needed for BIFOLD/DEEM job |

**Material subfolder:** `Rust/books/` (Comprehensive-Rust-Google.pdf, The-Rust-Programming-Language.epub)

---

## crosscutting/ — Spans multiple domains

### crosscutting/job/ — BIFOLD/DEEM job onboarding

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat6_Job_Onboarding_Plan.md | 6 — BIFOLD/DEEM (Stratum) | JK | active |

**Material subfolder:** `Job/repo/stratum/` (Stratum repo, cloned)

### crosscutting/seminar/ — Seminar IuG

| File | Chat | Prefix | Status |
|---|---|---|---|
| Chat7_Seminar_IuG_Plan.md | 7 — Seminar overview | SE | active |
| Chat7_Seminar_Presentation_Sprint.md | 7 — presentation sprint (Jun 18) | SE | active |
| Vortrag-Quellenpaket-und-Bauplan.md | — | — | reference |

**Material subfolder:** `Seminar/` (REFERENZBEISPIEL_Review.pdf, SystematicLiteratureReview.pdf)

---

## archive/

Chat5_DBT_Plan.md · BIFOLD-DEEM-Job-Plan.md · BIFOLD-DEEM-Job-Vorbereitung-v2.md · SoSe2026_Praxisplan.md — all superseded; kept for reference.

---

## Cross-domain wiring

**→ See `Plans/WIRING.md`** for the domain-to-domain routing table (which domain connects to which, hard prereqs, synergy windows, library coverage map).
