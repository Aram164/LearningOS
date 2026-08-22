# Analysis lane — plan audit, 2026-08-21

**Subject:** `unit-m2-analysis-exam-prep` + `study-map-m2-analysis-exam-prep`
(11 stages, 2,850 min) and the `AN_00`–`AN_09` mini plans in the workspace `inputs/`.

**Question asked:** is there room for improvement — measured the same way the SaD
lane was measured: does every stage house the material that advances
understanding of the concepts that part of the course actually teaches?

**Nothing in this audit has been applied.** It is diagnosis only.

> **Status, 2026-08-22:** items 1–4 of §4 were applied — see
> `Analysis-plan-fix-2026-08-22.md`. The two decisions at the end of §4 (chasing
> the HU Moodle sheets; whether Analysis gets the reference + exercise bank +
> mock treatment) remain open. This document is left as written, as the diagnosis
> of record.

---

## Verdict

The Analysis lane is *better built* than SaD was. Its material menu is complete —
every registered Analysis source on the drive carries a route into the unit, the
only exception (Rudin) is deliberately deferred as post-exam depth. Its knowledge
map matches the script section for section, with the Exkurs boundary drawn
correctly. Its `source_selections` are populated where SaD's are empty. Its
2026-08-03 coverage audit opened, hashed and page-counted 107 PDFs — Gate 1 done
properly.

Measured node by node it scores clean: **0 of 10 nodes lack practice or
derivation material, 0 nodes are single-sourced.** On the SaD side those numbers
were 42 and 12.

That headline is misleading, and the rest of this document is why.

**The defect is not coverage. It is distribution.** Every practice and exam asset
in the lane is front-loaded onto script Chapters 1–5. Differentiation, Taylor and
integration — the last three content nodes — run on almost nothing, and the plan
does not say so anywhere.

---

## 1. The skew, with counts

Full-text scans of every practice and exam file in the lane. Counts are keyword
occurrences across the whole document, not estimates.

### The eleven external drill sheets

| File | Pages | Taylor | Integration | Differentiation |
|---|---|---|---|---|
| `AS-Ana1.pdf` | 53 | 0 | 0 | 0 |
| `Aufgabensammlung-M1_Loesung.pdf` | 7 | 0 | 4 | 9 |
| `Bestimmt_Scan.pdf` | 12 | 0 | 0 | 0 |
| `Grenzwerte-von-Folgen.pdf` | 26 | 0 | 0 | 0 |
| **`IngMath2_Aufgaben.pdf`** | **312** | **62** | **167** | **77** |
| `KIT_Blatt-Reihen.pdf` | 4 | 0 | 0 | 0 |
| `Loesungen4.pdf` | 3 | 0 | 0 | 0 |
| `Tutorium-Musterloesung-Reihen.pdf` | 6 | 0 | 0 | 0 |
| `auf-2-2_Folgen_Loesungen.pdf` | 30 | 0 | 0 | 0 |
| `auf-2-3_Reihen_Loesungen.pdf` | 20 | 0 | 0 | 0 |
| `u10_Loesung.pdf` | 4 | 0 | 0 | 0 |

Ten of eleven files are sequences and series. **All of the drill bank's
Chapter 6–7 content sits in one file**, `IngMath2_Aufgaben.pdf` — an
*Ingenieurmathematik 2* problem collection, not an Analysis-für-Informatiker asset.

The unit routes `source-analysis-drill-blaetter-extern` at `depth: practice`
claiming `covers: [sequences, series, limits-continuity, differentiation, taylor,
integration]`, and the matching `source_selection` gives its locator as
**"exact stage locators"** — naming no file. So at stage `anf` the plan says
*practise: source-analysis-drill-blaetter-extern* and leaves you to discover that
ten of the eleven files have no Taylor in them.

The claim is not false. It is unusable at the precision the rest of this
repository holds itself to.

### The eight German exam papers

| Paper | Pages | Seq/Series | Differentiation | Taylor | Integration |
|---|---|---|---|---|---|
| `Aufgabe 3 ist gut.pdf` | 3 | 8 | 0 | **0** | 0 |
| `Darmstadt_…Probeklausur_mit-Loesungen.pdf` | 7 | 35 | 0 | **0** | 0 |
| `Leipzig_Analysis-fuer-Informatiker_Probeklausur.pdf` | 2 | 9 | 0 | **0** | 0 |
| `Marburg_…3-Klausuren-mit-Loesungen.pdf` | 35 | 58 | 0 | **0** | 0 |
| `Paderborn_…Klausur-2023_Loesungsvorschlag.pdf` | 9 | 22 | 3 | **0** | 3 |
| `Regensburg_…Klausur-mit-Loesungen…pdf` | 14 | 32 | 6 | **0** | 8 |
| `Ulm_…Klausur-SS10_nur-Aufgaben.pdf` | 2 | 5 | 1 | **0** | 1 |
| `TUM_Ferienkurs-Analysis-1_Skriptum.pdf` | 88 | 413 | 119 | 26 | 103 |

**Not one German exam paper in the bank contains a Taylor task.** Three contain
token differentiation or integration. The only file with real Chapter 6–7 weight
is the TUM entry — and it is a *Skriptum*, a holiday-course script, mis-shelved
among the Klausuren.

`stage-m2-analysis-anx` is **540 minutes**, the largest single block anywhere in
M2, and its stated `done_when` is two independent Analysis half-mocks drawn from
this bank. As it stands both mocks will be sequences-and-series papers.

### What this costs

| Stage | Minutes | Node | Practice routes that actually contain the topic |
|---|---|---|---|
| `ane` | 330 | differentiation | Fritzsche (strong), Forster-Wessoly, 1 drill file |
| `anf` | 210 | taylor | **1 route, whose Taylor content is one engineering-maths file** |
| `ang` | 330 | integration | Forster-Wessoly, 2 drill files |
| `anx` | 540 | exam-transfer | a bank with zero Taylor tasks |

**1,410 of the lane's 2,850 minutes — just over half — sit on the thin side.**

---

## 2. The fix is already on the drive, already routed, and under-claimed

This is the part that makes the finding worth acting on. Three solved German
exercise books are registered, on disk, dispositioned by the 2026-08-03 audit,
and already carrying routes into this unit. Full-text counts:

| Source | Pages | Seq | Series | Limits | Diff | Taylor | Integration |
|---|---|---|---|---|---|---|---|
| **Fritzsche Trainingsbuch** | 342 | 666 | 380 | 319 | 190 | 64 | **481** |
| Forster-Wessoly Übungsbuch | 206 | 299 | 183 | 112 | 74 | 21 | 89 |
| Deitmar Übungsbuch | 257 | 487 | 126 | 209 | 48 | 9 | 136 |

Fritzsche's structure, read from its outline:

- §3.1 Differenzierbare Funktionen — p116
- §3.2 Der Mittelwertsatz — p126
- §3.3 Stammfunktionen und Integrale — p148
- §3.4 Integrationsmethoden — p159
- §4.1 Gleichmäßige Konvergenz — p189
- **§4.2 Die Taylorentwicklung — p200**
- §4.4 Uneigentliche Integrale — p225
- **§5 Anhang: Lösungen — p253** (full worked solutions)

That is differentiation, the mean-value theorem, integration, integration
technique, uniform convergence, Taylor **and** improper integrals — the exact
content of script §5.7, Ch 6 and Ch 7 — in one German solution-backed book.

Now compare how the plan currently uses it:

| Source | Route claims | Selected for stages | What it actually covers |
|---|---|---|---|
| Fritzsche | `foundations, exp-log-uniform, differentiation` | `an0`, `and` | also Taylor §4.2, integration §3.3–3.4, improper §4.4 |
| Forster-Wessoly | `foundations, sequences, series, limits-continuity, differentiation, integration` | `ana, anb, ane, ang` | **also Taylor** (21 hits), missing from both |
| Deitmar | `foundations, sequences, series` | **never selected, never staged** | 209 limits, 136 integration, 48 differentiation |

**The best-matched, solution-backed drill book in the lane is absent from the two
stages it was made for.** Fritzsche is not routed to `taylor` or `integration`
and appears in neither `anf` nor `ang`. Deitmar is in the menu and in no plan at
all.

Nothing here needs a new source. It needs the routes to claim what the books
contain.

---

## 3. Smaller findings, worst first

**3.1 — The scope authority admits it is not the exam scope.**
`unser skript.pdf` p. iv, in the author's own words: *"Das Skript gibt jedoch
nicht den Wortlaut der Vorlesung wieder und entspricht auch nicht exakt dem
Umfang der behandelten Themen."* The 2026-08-03 audit recorded *"Current lecture
decks/recordings | unresolved | none exist in the declared local Analysis root."*
SaD is scoped from fifteen current decks; Analysis is scoped from a script that
disclaims correspondence to the lecture. This is a declared, accepted risk rather
than an error — but it is the lane's largest single uncertainty and it has sat
unresolved for eighteen days with a passive revisit condition.

**3.2 — The current HU exercise sheets stop at §5.5.**
`source-analysis-skript` bundles nine files: the script, a Chapter 2 variant,
`kleine_beweise.pdf`, and Serie 05–09 + WV. The 2026-08-03 audit already recorded
*"no current local differentiation/Taylor/integration sheets exist."* Eighteen
days on, the revisit condition — "if Moodle supplies matching sheets" — has no
owner and no date. This is the root cause of §1.

**3.3 — Course practice is not modelled as practice.**
On the SaD side, decks and exercises are two sources (`source-sad-ss26-lectures`,
`source-sad-uebungen`), so course practice is visible at `depth: practice`. Here
the Serie sheets live *inside* `source-analysis-skript`, and both of its routes
are `depth: course-aligned`. Consequence: the closest thing to real HU exam
practice never appears as practice-depth material in any coverage measurement,
including the clean scoreboard at the top of this document.

**3.4 — Seven routes point at material whose location the workspace already knows.**
`labs-schreyer`, `mfnf-analysis1`, `ohlbach-eisinger-beweise`,
`velleman-how-to-prove-it`, `ross-elementary-analysis`, `thomas-calculus`,
`stewart-calculus` all carry `locator: "Not yet located; establish on first use"`.
All seven are on disk with registered `.flat` symlinks, and the 2026-08-03 audit
lists a full `material://` URI, page count and SHA256 for every one of them. The
2026-08-15 overhaul reset these routes to `unassessed`/`unevaluated` and dropped
locators the workspace's own audit had already established. The `unassessed`
marker is honest and should stay — inventing a pedagogical judgment would violate
CLAUDE.md §4 — but the *locator* is a fact, not a judgment, and it is recoverable
from a file sitting in the same directory.

**3.5 — The lane has one durable note.**
`note-an-source-crosswalk.md`, 3.4 KB, `role: crosswalk`. That is the entire
durable output of Analysis. For comparison: AML holds 30 notes (reference +
exercise bank + mock for L02–L11), SaD holds 18. Analysis has no reference note,
no exercise bank, no mock exam, no theorem-chain note — for ten concepts and
2,850 planned minutes. COORDINATION already names this lane as the one with "an
unstarted half"; the artifact count is what that looks like on disk.

**3.6 — `Maths220_Proofs-in-Calculus.pdf` is unrouted.**
`source-analysis-grundlagen-handouts` holds three files; the selection names two
(`Mengen-und-Abbildungen.pdf`, `Relationen.pdf`). The third is a 17-page
proofs-in-calculus handout that reads directly onto the `proof-presentation` node —
whose only practice route today is Ableitinger, and that one is gated behind
"a diagnosed presentation error."

**3.7 — `Pd3szO-ana_inf_serie08.pdf`.**
Serie 08 exists only under a download-mangled filename; there is no plain
`ana_inf_serie08.pdf`. Cosmetic, but it is the one file in the set whose name
will not sort or match with its siblings.

---

## 4. What I would propose, if you want it applied

In the order I would do it. Items 1–3 are re-routing already-audited material and
would follow the same SOP gates as the SaD package; item 4 is a build.

1. **Re-route Fritzsche, Forster-Wessoly and Deitmar to the nodes they cover**,
   with exact section locators — Fritzsche §3.1–3.4 / §4.2 / §4.4 and the
   solutions appendix p253, Forster-Wessoly to `taylor`, Deitmar to
   `limits-continuity`, `differentiation`, `integration`. Roughly 8–10 rich routes.
2. **Split the drill and exam sources by what they contain** — name
   `IngMath2_Aufgaben.pdf` explicitly wherever a Ch 6–7 drill is claimed, and
   separate `TUM_Ferienkurs-Analysis-1_Skriptum.pdf` from the Klausur bank, since
   it is a script and is also the only Taylor-bearing file in that folder.
3. **Restore the seven locators** from the 2026-08-03 audit, leaving
   `depth: unassessed` / `scope: unevaluated` untouched. Mechanical; no judgment
   invented.
4. **Record the Taylor exam-transfer gap explicitly** in the `anx` stage rather
   than leaving it implicit, and decide what fills it — the MIT 18.100C papers are
   the only Taylor-bearing exam material on the drive, at the cost of English
   notation and a different syllabus.

Two things need your decision and I have not touched them:

- whether to chase the **HU Moodle sheets for Chapters 6–7**, which would dissolve
  §1 at the source, or accept the book substitutes;
- whether Analysis gets the **reference + exercise bank + mock treatment** the
  other modules have, which is a build, not a re-route.

---

## 5. What this audit does not claim

It does not claim the Analysis plan is bad — measured against its own SOP it is
the most carefully sourced lane in the repository, and its 2026-08-03 coverage
audit is the best single artifact of its kind here. It claims that the clean
per-node scoreboard hides a real asymmetry, that the asymmetry lands on the half
of the syllabus nobody has started, and that most of the repair is already sitting
on the drive waiting to be pointed at correctly.

No claim of mastery or readiness is made anywhere in this document.
