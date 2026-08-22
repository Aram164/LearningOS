# Analysis lane — plan fix applied, 2026-08-22

Applies items 1–4 of `Analysis-plan-audit-2026-08-21.md`, plus the learner's
instruction of 2026-08-22: *fill gaps with everything that fits, do not plan time
per stage, give each stage the set of all possible materials and the angle they
highlight.*

**Records changed**

| File | Change |
|---|---|
| `curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml` | Analysis material menu: 12 routes → 41 |
| `…/units/unit-m2-analysis-exam-prep/unit.yaml` | `source_selections` regenerated from the routes |
| `…/units/unit-m2-analysis-exam-prep/study-map.yaml` | every stage carries the full menu; `estimate_minutes` removed |
| `work/active/workspace-m2-exam-prep/outputs/Analysis-script-led-module-plan.yaml` | mirrors all three, plus twelve source ids added to `workspace_updates` |

`python tools/validate.py` → 0 errors, 0 warnings. `tools/generate.py` rebuilt.

---

## 1. Books re-routed to the nodes they actually contain

Section structure was read from the PDFs themselves, not inferred.

**Fritzsche** — one route (`foundations, exp-log-uniform, differentiation`) became four:

- Kap. 1 Die Sprache der Analysis, pp. 9–38 → foundations, proof-presentation
- Kap. 2 Der Grenzwertbegriff — §2.1 p. 52, §2.2 p. 68, §2.3 p. 77 → sequences, series, limits-continuity
- Kap. 3 Der Calculus — §3.1 p. 116, §3.2 p. 126, §3.3 p. 148, §3.4 p. 159 → differentiation, integration
- Kap. 4 — §4.1 p. 189, **§4.2 Die Taylorentwicklung p. 200**, §4.4 p. 225 → exp-log-uniform, taylor, integration

Solutions live in Kap. 5 Anhang from p. 253 in every case.

**Forster/Wessoly** — one route became four, each naming the Aufgaben page and the
matching Lösungen page. The addition that mattered: **§22 Taylor-Reihen**
(Aufgaben p. 61, Lösungen p. 195), which the old route did not claim.

**Deitmar** — was in the menu and in no stage. Now five routes: Kap. 1–2
(foundations), Kap. 3 (sequences, series), Kap. 4 (limits-continuity,
exp-log-uniform), **Kap. 5–6 (differentiation, integration)**, §7.1 (uniform
convergence), each with its Lösungen chapter. Kap. 8–20 stay closed as past scope.

## 2. Drill and exam sources split by what they hold

`source-analysis-drill-blaetter-extern`, one route claiming six nodes → five
routes naming files:

- seven solved sequence/series sheets
- `u10_Loesung.pdf` (epsilon-delta continuity)
- **`IngMath2_Aufgaben.pdf`** — carries the entire Chapter 6–7 drill load by
  itself; Kap. 13, §14.1–14.4 (**§14.3 Der Satz von Taylor**), Kap. 16–18
- `Aufgabensammlung-M1_Loesung.pdf` (mixed)
- `Bestimmt_Scan.pdf` (handwritten axioms)

`source-analysis-klausuren-extern`, one route → four:

- solved German Klausuren (Marburg, Regensburg, Darmstadt, Paderborn) — the angle
  states the weighting and that **none contains a Taylor task**
- unsolved papers held for timed sittings (Ulm, Leipzig, Stuttgart) — reserved to
  AN.X so they cannot be spent early
- **TUM Ferienkurs Skriptum**, separated out: it is a revision script with
  exercise sets, not a Klausur, and it holds the only Taylor tasks in that folder
  (Satz von Taylor pp. 47–48, Übungsaufgaben pp. 49–50)
- MIT 18.100C set — English, proof-heavy, different syllabus; AN.X only

Also: the HU series route moved from `depth: course-aligned` to `depth: practice`
so course practice is visible as practice, and its angle now states the §5.5 stop
outright. `Maths220_Proofs-in-Calculus.pdf` was unrouted and now carries
proof-presentation. Leonard, 3B1B and Strang gained the nodes their own `why`
already claimed, and their minute caps were dropped.

## 3. Seven locators restored

`labs-schreyer`, `mfnf`, `ohlbach-eisinger`, `velleman`, `ross`, `thomas`,
`stewart` carried *"Not yet located; establish on first use"* while the
2026-08-03 audit held a full `material://` path and page count for each. Paths
restored; `depth: unassessed` and `scope: unevaluated` deliberately untouched —
the locator is a fact, the judgment is not (CLAUDE.md §4).

## 4. Stages became menus, and the pace came out

Each stage now lists every material whose route covers its node, labelled with the
angle it highlights and the exact section, ranked only as required-now /
helpful-now / reference-only. No stage prescribes minutes.

| Stage | Node | Resources before | After |
|---|---|---|---|
| calibrate | method + scope | 3 | 4 |
| AN.0 | foundations | 4 | 12 |
| AN.A | sequences | 6 | 17 |
| AN.B | series | 5 | 17 |
| AN.C | limits-continuity | 4 | 18 |
| AN.D | exp-log-uniform | 3 | 12 |
| AN.E | differentiation | 5 | 16 |
| AN.F | taylor | 4 | 9 |
| AN.G | integration | 5 | 16 |
| AN.X | exam-transfer | 5 | 13 |

`estimate_minutes` removed from all eleven stages. Closed-book test lengths and
the 30–45-minute WV conditions stay: those are exam conditions, not a schedule.

**The Taylor gap is now written down**, not implied. AN.F opens with a note that
no HU sheet reaches §6.8. AN.X opens with the assembly rule: no paper in the
Klausur bank contains a Taylor task, only Regensburg and Paderborn carry Ch 6–7
items, so the Chapter 6–7 half must be built from Fritzsche §4.2, Forster §22,
the TUM Übungsaufgaben and IngMath2 §14.3 — and labelled as an assembly.

---

## Still open — your call, untouched

- **HU Moodle sheets for Chapters 6–7.** Unresolved since 2026-08-03 with no owner
  and no date. Fixing it at the source would retire every substitute above.
- **Whether Analysis gets reference note + exercise bank + mock exam.** The lane
  still holds one durable note against AML's thirty. That is a build, not a route.
- **`Pd3szO-ana_inf_serie08.pdf`** keeps its download-mangled name; it is now
  named as such in the route locator rather than renamed, since the file is
  hashed in the 2026-08-03 inventory.
- **Workspace source list.** Twelve source ids were added to the plan's
  `workspace_updates`; `CONTEXT.md` frontmatter still lists the old set and will
  pick them up when the plan is applied.

No claim of mastery or readiness is made anywhere in this document.
