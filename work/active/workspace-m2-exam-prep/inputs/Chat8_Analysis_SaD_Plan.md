# Analysis × SaD — Kombimodul Study Plan

> **Created:** 2026-06-11 (KW 24) | **Updated:** 2026-07-04 (KW 27) — **exam facts final (screenshot-verified Jul 3): M2 = ONE combined SaD+Analysis Klausur, Mo 27.07, 12:00–15:00, ESZ 110/115/307** (2. Termin Fr 09.10, 13–16h; Rücktritt via AGNES by Mo 20.07). Calendar recalibrated for the KW-27 reality (see Calendar Fit); 5 surfaced Buecher-PDFs triaged into the crosswalk. Earlier: Forster Übungsbuch added (KW 24); Leonard video titles per block (KW 24); Scenario 1 active (Jun 12).
> **Module:** M2.1 *Analysis und ihre Bezüge zur Informatik* (HU, Institut für Mathematik) — **Kombimodul with SaD**: ⚠️ corrected Jul 3 — **ONE combined 3h Klausur covers BOTH halves** (not two separate exams), one module grade. The SaD half is covered by Chat 1 (Blocks A–N); this plan covers the Analysis half and wires every block into the SaD/AML plane so the two halves reinforce each other. **Consequence: F.N and AN.X are ONE merged prep track — interleave SaD stats clusters with AN proof drill, don't run two parallel tracks.**
> **Step prefix:** **AN**
> **Primary source:** `Plans/Math/analysis/Analysis/Skript+HU/unser skript.pdf` (258 pp). Page numbers below refer to this PDF.
> **Scope rule (Aram's decision, KW 24):** sections titled **„Exkurs"** are EXCLUDED. Sections titled **„Ausflug"** stay in scope but at lower priority (read once, don't drill). The final skript chapter „Exkurse" (Rⁿ, topology, gradient, DGL) is excluded — except one optional cross-read flagged in the wire registry.
> **Starting state (KW 24):** Aram learned for this exam ~1 year ago — **Ch. 1 (Grundlagen) + Ch. 2 (Reelle Zahlen) done, everything from Folgen onward untouched.** AN.0 is therefore a refresh, not a first pass.
> **Exam date:** ✅ **FINAL (Jul 3, KW 27): Mo 27.07, 12:00–15:00, ESZ 110/115/307 — ONE combined M2 Klausur (SaD + Analysis, Leser).** 2. Termin: Fr 09.10, 13:00–16:00 (fallback only; Rücktritt via AGNES by Mo 20.07 is the decision gate). AML is skipped → 2. Termin Mi 30.09 (Rücktritt by 15.07!), AMLS → Aug 06/27, so **July = this ONE exam.** ⚠️ Verify M2 registration (1.-PZ Anmeldung closed 02.07). Scenario-1 table below superseded by the **KW-27 recalibration** in Calendar Fit.

---

## Step ID Convention

`AN.<Block><Number>` — e.g. `AN.A2` = Block A, step 2. Block self-tests are `AN.A-test` etc. Completion entries in SEMESTER-STATUS §3: `AN.A1 ✓ (KW 27)`.

---

## Why This Plan Exists

1. **The grade is coupled.** Analysis and SaD average into one Kombimodul grade — a weak Analysis exam drags the SaD work down. Both halves deserve the same systematic treatment.
2. **The content is coupled.** Analysis is the machinery *underneath* SaD and AML: limits are consistency of estimators, series are discrete distributions, the Hauptsatz is the density↔CDF relationship, derivatives are MLE and gradient descent, Taylor is Newton/Adam. Studying Analysis with these wires active is double-paid time. The wire registry (§ Cross-Wires) makes every connection explicit, in the style of `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`.
3. **The folder is rich but unordered.** `Plans/Math/analysis/Analysis/` holds the skript, 6 HU exercise sheets, ~8 solved problem collections, MIT lecture notes, Rudin, and Strang — with no sequence. This plan turns the pile into an ordered path.

---

## Resource Stack (3 layers — use in this order per block)

| Layer | Resource | Role |
|---|---|---|
| **1. Intuition / calculation fluency** | **Professor Leonard** — [youtube.com/@ProfessorLeonard](https://www.youtube.com/@ProfessorLeonard) (Calculus 1 + Calculus 2 playlists) + **Strang, *Calculus*** (`Plans/Math/analysis/Analysis/Strang-Calculus/resources/`, chapters as PDFs) | Watch/read FIRST when a topic is new. Long-form, computational, zero intimidation. Builds the "what is this object" picture before the ε-δ formalism. |
| **2. The skript (exam-defining)** | `unser skript.pdf` | THE source of truth for definitions, theorem statements, and notation. Everything in the exam comes from here. Work it second, with Layer 1 intuition already loaded. |
| **2b. Drill companion** | **Forster/Wessoly — Übungsbuch zur Analysis** (`Analysis/Buecher/`, downloaded KW 24 via HU Springer license) + **Fritzsche *Trainingsbuch zur Analysis 1*** and **Deitmar *Übungsbuch zur Analysis*** (both `Buecher/`, triaged Jul 4 — chapter map in the crosswalk) | Problem set mapped exactly to the German Analysis curriculum. Use alongside the skript for AN.A–G: after each skript section, pull the matching Forster problems. Especially valuable for AN.E (derivatives/MVT) and AN.G (integration technique) where clean calculation fluency is the exam differentiator. |
| **3. Rigor / proof technique** | **MIT 18.100A Real Analysis** (Casey Rodriguez, Fall 2020) — [playlist](https://www.youtube.com/watch?v=LY7YmuDbuW0&list=PLUl4u3cNGP61O7HkcF7UImpM0cR_L2gSw) + full lecture notes `mit18_100af20_lec_full2.pdf` (92 pp, same numbering as the playlist) | Watch the MAPPED lectures only (never linearly — same rule as the university supplements in LEARNING-RESOURCES §2). Closest free sibling of the skript: proof-based, sequence→series→continuity→derivative→integral, same order. |
| *(optional rigor track)* | Rudin `Principles_of_Mathematical_Analysis-Rudin.pdf`, `realanal.pdf`/`realanal2.pdf` | Same pattern as 18.650/STAT110x for SaD: only if a proof in the skript feels unmotivated and you have spare appetite. NOT exam-required. |

**MIT 18.100A lecture index** (numbers = playlist position = notes sections):
L1 Sets/Induction · L2–L3 Cardinality (skip) · L4 Characterization of ℝ · L5 Archimedean/Density/|x| · L6 Uncountability (skip) · L7 Convergent sequences · L8 Squeeze + operations · L9 Limsup/Liminf/Bolzano-Weierstrass · L10 Completeness + series basics · L11 Absolute convergence + comparison test · L12 Ratio/Root/Alternating tests · L13 Limits of functions · L14 Sequential limits + continuity · L15 sin/cos continuity + Dirichlet function · L16 Min/Max + IVT · L17 Uniform continuity + derivative definition · L18 Weierstrass nowhere-differentiable (skip) · L19 Differentiation rules + Rolle + MVT · L20 Taylor + Riemann sums · L21 Riemann integral of continuous f · L22 FTC + parts + substitution · L23 Pointwise vs. uniform convergence · L24 Uniform convergence + M-test · L25 Power series (skip — Exkurs territory)

**Solved-problem bank in `Plans/Math/analysis/Analysis/`** (mapped to blocks below):

> 🗂️ **Folder tidied KW 27 (Jul 2):** the flat pile is now sorted — **`Skript+HU/`** (unser skript, kleine_beweise ⭐, ana_inf serie05–09 + WV), **`Buecher/`** (all books+notes — incl. 8 NEWLY SURFACED from a nested duplicate folder, **all 5 unknowns triaged Jul 4** — see the crosswalk's triage table: Grieser *Analysis I*, Fritzsche *Trainingsbuch*, Deitmar *Übungsbuch*, Ableitinger/Herrmann *Musterlösungen*, plus a 49-pp skript excerpt Ch 1–2), **`Drill-Loesungen/`** (all solved practice), **`Klausuren-extern/`** (Marburg ⭐, Regensburg ⭐, Stuttgart Probeklausur + the full external bank, local since Jul 2). Duplicates deleted (nested skript copy; 'gute Aufgaben' = auf_2_2). Source selector: **`Plans/Math/analysis/AN_Source-Crosswalk.md`**. File names below unchanged — prepend the subfolder.

| File | Content | Block |
|---|---|---|
| `Mengen und Abbildungen ( sehr hilfreich !).pdf`, `Relationen .pdf` | Sets, maps, relations | AN.0 |
| `ana_inf_serie05.pdf` | HU sheet 5: Vollständigkeit, Rekursionen, Folgen/Grenzwerte | AN.0→A |
| `ana_inf_serie06.pdf`, `ana_inf_serie07.pdf` | HU sheets 6–7: Folgen, Konvergenz, Häufungspunkte | AN.A |
| `Grenzwert von folgen.pdf`, `loesungen4.pdf`, `auf_2_2_Folgen_loesungen.pdf` (30 pp Folgen-Katalog w/ solutions — *was also present as duplicate 'gute Aufgaben mit lösungen.pdf', deleted KW 27*), `bestimmt..pdf` | Solved sequence-convergence practice | AN.A |
| `Pd3szO-ana_inf_serie08.pdf` | HU sheet 8: Reihen, Grenzwerte | AN.B |
| `KIT blatt zu Reihen .pdf`, `Tutorium-Musterloesung-Reihen.pdf`, `auf_2_3_Reihen_loesungen.pdf` | Solved series practice | AN.B |
| `ana_inf_serie09.pdf` | HU sheet 9: Grenzwerte von Funktionen, Stetigkeit | AN.C |
| `Proofs in calculus.pdf` | Limits/series proof patterns (EN) | AN.A–C |
| `u10_L.pdf` (solved Blatt 10, TU Darmstadt), `IngMath_2_aufgaben.pdf` (312 pp solved, Voß) | Derivative/Taylor/integral drill — pull by topic | AN.E–G |
| `Aufgabensammlung_M1__Loesung.pdf`, `AS-Ana1.pdf` (53 pp themed Aufgabensammlung) | Mixed Klausur-style collections | AN.X |
| `kleine_beweise.pdf` ⭐ | **HU Tutorium zur Prüfungsvorbereitung (SoSe 2025!)** — list of "small proofs" expected in THIS module's exam | AN.X (and skim NOW — it tells you what the exam rewards) |
| `ana_inf_serieWV.pdf` | HU Wiederholung & Vertiefung sheet | AN.X |
| `Aufgabe 3 ist gut.pdf` | Solved Probeklausur (Stuttgart) | AN.X |
| *(external, added KW 24)* LEARNING-RESOURCES §6 "Analysis (AN)" bank | Solved Klausuren from Marburg ⭐, Regensburg ⭐ (w/ grader commentary), MIT 18.100C psets+final w/ solutions, Darmstadt/Paderborn/Leipzig/Ulm Probeklausuren, TUM Ferienkurs script | AN.A–G drill + AN.X |

---

## Prerequisite Dependency Graph

```
AN.0 (Refresh: Grundlagen + ℝ)          [done a year ago — refresh only]
  │
  ▼
AN.A (Folgen & Konvergenz)  ◄─── the single most load-bearing block:
  │                              everything after it is "a limit of something"
  ├──────────────► AN.B (Reihen)            [a series IS a sequence of partial sums]
  ▼
AN.C (Grenzwerte von Funktionen & Stetigkeit)   [function limits defined via sequences]
  │
  ├──────────────► AN.D (exp/log + glm. Konvergenz)  [exp defined via series/limit → needs AN.B]
  ▼
AN.E (Differenzierbarkeit, MWS, l'Hospital)     [derivative = a limit; l'Hospital needs MWS]
  │
  ▼
AN.F (Höhere Ableitungen + Taylor)              [Taylor needs MWS machinery]
  │
  ▼
AN.G (Integralrechnung)                          [Riemann sums = limits; Hauptsatz needs AN.E]
  │
  ▼
AN.X (Exam prep: kleine Beweise, WV-Serie, Probeklausur, cheat sheet)
```

Strict chain: **0 → A → C → E → F → G**. B hangs off A (do before D). D needs B+C but nothing needs D except exam coverage — schedulable late.

---

## Block-by-Block Plan

> Per-block pattern (house style): skript sections → Layer-1 intuition → Layer-3 rigor → solved problems → self-test. Time estimates assume the SaD-style "extract concepts/formulas while reading" workflow.

### BLOCK AN.0: Refresh — Grundlagen + Reelle Zahlen *(~3h, was learned 1 year ago)*

Skript: Ch. „Wiederholung – Grundlagen" (pp. 11–16) + „Die reellen Zahlen" (pp. 17–35) + Ausflug Maschinenzahlen (pp. 36–50, skim).

- **AN.0.1** *(1h)* — Speed-reread pp. 11–35. You've done this; the goal is reactivation, not relearning. Write a one-page recall sheet from memory FIRST, then check against the skript: Induktion template, Bernoulli, binomischer Lehrsatz, Körper-/Anordnungsaxiome, Betragsfunktion + Dreiecksungleichung, sup/inf definitions, Vollständigkeitsaxiom, Archimedes, Wurzel-existence.
- **AN.0.2** *(1h)* — Drill: `Mengen und Abbildungen`, `Relationen`, plus serie05 completeness tasks. One induction proof, one sup/inf determination (with proof), one inequality via Dreiecksungleichung.
- **AN.0.3** *(0.5h, Ausflug-priority)* — Skim Maschinenzahlen/Rundungsfehler/Rechnerarithmetik pp. 36–50. Don't drill. **Wire W14:** this is the math behind fp32/fp16 precision in AMLS L08/hardware (S.E) — float rounding error is why mixed-precision training needs loss scaling.
- **AN.0-test** — Can you state the Vollständigkeitsaxiom and explain why ℚ fails it (√2)? Prove `sup` of a given set. Run an induction proof start to finish without looking.

MIT: L1 (induction part), L4, L5 — only if the recall sheet shows real gaps.

### BLOCK AN.A: Folgen & Konvergenz *(~7h — the load-bearing block)*

Skript: pp. 51–89 — Folgen (52), Konvergenzkriterien (65), Rechnen mit konvergenten Folgen (71), Bestimmt divergente Folgen (79). Ausflüge: Lineare Rekursionsgleichungen (57, read once — CS-flavored, recursions as sequences), Quadratwurzel-Berechnung/Heron (84, read once). Skip: Exkurs Landau (56), Exkurs homogene Rekursionen (62).

- **AN.A1** *(1.5h)* — Layer 1: Professor Leonard Calc 2 — search **"Professor Leonard sequences"** (the "Introduction to Sequences" video, ~50 min; covers convergence/divergence/monotone/bounded intuitively before any ε). Then skript pp. 52–65: Folge, Teilfolge, Beschränktheit, Monotonie, ε-N definition of `lim aₙ = a`. Write the ε-N definition out and translate it into your own words — this ONE definition is the template for every other limit in the module.
- **AN.A2** *(2h)* — Skript pp. 65–79: Konvergenzkriterien (monotone+beschränkt ⇒ konvergent, Cauchy, Häufungspunkte, Bolzano-Weierstrass, Sandwich/Einschließung) + Grenzwertsätze (Summe/Produkt/Quotient). MIT L7–L9 for the proofs that feel thin.
- **AN.A3** *(1h)* — Skript pp. 79–84: bestimmte Divergenz (→ ±∞), Standardgrenzwerte (qⁿ, ⁿ√n, (1+x/n)ⁿ → eˣ). `bestimmt..pdf` for drill.
- **AN.A4** *(2.5h)* — **Drill block** (this is where the exam points live): serie06, serie07, `auf_2_2_Folgen_loesungen.pdf` (work ≥10 of the 30 pp), `loesungen4.pdf` (the "find N(ε)" type — a classic Klausur opener), `auf_2_2_Folgen_loesungen.pdf`. Target fluency: given a sequence, decide convergent/divergent + prove it, in <10 min.
- **AN.A-test** — (1) ε-N proof from scratch for aₙ = (n+3)/(n−1) → 1. (2) State + sketch-prove Bolzano-Weierstrass. (3) Heron iteration: why does it converge? (4) **Wire check W1/W13:** explain in one paragraph why "the estimator X̄ₙ is consistent" (SaD 09) and "gradient descent converges" (AML L03/L06) are both *exactly* statements about convergent sequences.

### BLOCK AN.B: Reihen *(~5h)*

Skript: pp. 90–104 — Reihen (90), Konvergenzkriterien für Reihen (94), Absolute Konvergenz (98), Ausflug Umordnungen (102, read once). Skip: Exkurs Produktreihen (105).

- **AN.B1** *(1.5h)* — Layer 1: Professor Leonard Calc 2 — **"Introduction to Series"** and **"Geometric Series"** videos (~40 min combined). Then skript pp. 90–94: series as sequence of partial sums; geometric series Σqᵏ = 1/(1−q); harmonic series diverges; Teleskopsummen; Nullfolgenkriterium (necessary, not sufficient!).
- **AN.B2** *(2h)* — Skript pp. 94–102: Majoranten-/Minorantenkriterium, Quotientenkriterium, Wurzelkriterium, Leibniz, absolute vs. bedingte Konvergenz. MIT L10–L12. Professor Leonard **"Ratio Test"**, **"Root Test"**, **"Alternating Series"** (~30 min each) if a test isn't clicking from the skript alone. Build the **decision tree** (which test to try in which order) — this is the cheat-sheet artifact for this block.
- **AN.B3** *(1.5h)* — Drill: serie08, `KIT blatt zu Reihen`, `Tutorium-Musterloesung-Reihen`, `auf_2_3_Reihen_loesungen`.
- **AN.B-test** — (1) Classify 5 series (convergent/abs. convergent/divergent) with proof. (2) Why does the Quotientenkriterium fail for Σ1/n²? (3) **Wire check W2/W3:** show that the geometric distribution's probabilities sum to 1 (SaD 07 — it's the geometric series), and that Poisson's do (it's the exp series, see AN.D).

### BLOCK AN.C: Grenzwerte von Funktionen & Stetigkeit *(~5.5h)*

Skript: pp. 108–131 — Grenzwerte bei Funktionen (108), Uneigentliche/einseitige Grenzwerte (112), Stetige Funktionen (117), Zwischenwertsatz/Umkehrfunktion/Extrempunkte (121), Stetigkeit auf kompakten Intervallen (131).

- **AN.C1** *(1.5h)* — Layer 1: Professor Leonard Calc 1 — **"Introduction to Limits"** + **"Continuity"** videos (~1h combined; these are from the Calc 1 playlist, not Calc 2). Skript pp. 108–117: function limits (ε-δ AND sequence characterization — the skript leans on AN.A here), one-sided/improper limits.
- **AN.C2** *(1.5h)* — Skript pp. 117–131: Stetigkeit (ε-δ, Folgenkriterium), Zwischenwertsatz, stetige Umkehrfunktion, Extrempunkte, Min/Max-Satz on [a,b]. MIT L13–L14, L16.
- **AN.C3** *(1.5h)* — Drill: serie09 (exactly this topic), `Proofs in calculus.pdf` continuity sections.
- **AN.C-test** — (1) ε-δ continuity proof for a concrete f. (2) IVT application: show f has a root, justify. (3) Why does a continuous f on [a,b] attain its min? (4) **Wire check W5/W11:** a CDF F is monotone + right-continuous, its inverse is the quantile function (SaD 06/08) — which theorems from this block make the quantile function well-defined? And: the Min/Max-Satz is the reason a loss function on a compact parameter set HAS a minimizer (AML L03).

### BLOCK AN.D: Exponentialfunktion, Logarithmus, gleichmäßige Konvergenz *(~3.5h)*

Skript: pp. 132–139 — Exponentialfunktion und Logarithmen (132), Gleichmäßige Konvergenz von Funktionenfolgen (139). Skip: Exkurs Potenzreihen (140). Needs AN.B (exp via series) + AN.C (continuity).

- **AN.D1** *(1.5h)* — Skript pp. 132–139: exp via series/limit, functional equation eˣ⁺ʸ = eˣeʸ, ln as inverse, Logarithmusgesetze, allgemeine Potenz aˣ. This is mostly consolidation — but make the laws automatic (they're exam currency AND the daily toolkit of log-likelihoods).
- **AN.D2** *(1.5h)* — Skript pp. 139–140: punktweise vs. gleichmäßige Konvergenz, continuity of the limit function. MIT L23–L24 — Rodriguez's counterexamples (xⁿ on [0,1]) are exactly the exam's favorite trap.
- **AN.D-test** — (1) Prove ln(xy) = ln x + ln y from the functional equation. (2) Show fₙ(x)=xⁿ converges pointwise but not uniformly on [0,1). (3) **Wire check W4:** take the SaD 09 / AML L05 MLE step "maximize Πp(xᵢ|θ) ⇒ maximize Σlog p(xᵢ|θ)" and justify every move with a Logarithmusgesetz + monotonicity of ln (AN.C inverse-function block). This wire is the MLE→cross-entropy derivation in AML L05.

### BLOCK AN.E: Differenzierbarkeit, Mittelwertsatz, l'Hospital *(~5.5h)*

Skript: pp. 147–163 — Differenzierbarkeit und Ableitungen (147), Mittelwertsatz (155), Regel von l'Hospital (161). Ausflug sin/cos/tan (158, read once — values table + derivatives are assumed knowledge). Skip: Exkurse (154, 163).

- **AN.E1** *(2h)* — Layer 1: Professor Leonard Calc 1 — **"Definition of the Derivative"** + **"Differentiation Rules"** (skim these if Abitur calc is solid; his **"Mean Value Theorem"** video is worth it regardless of background — one of his best). Skript pp. 147–155: derivative as limit of Differenzenquotient, differentiability ⇒ continuity (not conversely — |x|!), Produkt-/Quotienten-/Kettenregel, derivative of inverse functions.
- **AN.E2** *(1.5h)* — Skript pp. 155–161: Satz von Rolle, Mittelwertsatz, monotonicity from f′ sign, local extrema (f′=0 necessary; sign change / f″ sufficient). MIT L17 (derivative def), L19 (Rolle/MVT).
- **AN.E3** *(1h)* — Skript pp. 161–163: l'Hospital (and when it does NOT apply). Drill the standard limit types 0/0, ∞/∞, 0·∞, 1^∞.
- **AN.E4** *(1h)* — Drill: pull derivative/MVT/l'Hospital tasks from `IngMath_2_aufgaben.pdf` + `AS-Ana1.pdf`.
- **AN.E-test** — (1) Differentiate from the definition (one concrete f). (2) Prove: f′ > 0 on (a,b) ⇒ f strictly increasing (via MVT). (3) Two l'Hospital limits, one where it's inapplicable. (4) **Wire check W6/W7:** "set the derivative to zero" is the SaD 03 least-squares derivation AND the SaD 09 MLE recipe AND the stationarity condition behind every AML loss minimization (L03). The MVT is what makes "small gradient steps decrease the loss" honest.

### BLOCK AN.F: Höhere Ableitungen + Taylor *(~4h)*

Skript: pp. 175–183 — Höhere Ableitungen (175), Taylorpolynome und Taylorreihen (178). Ausflug Interpolation (184, read once at most). Skip: Exkurs (183).

- **AN.F1** *(1.5h)* — Layer 1: Professor Leonard Calc 2 — **"Taylor Polynomials"** + **"Lagrange Error Bound"** (two videos, ~1h combined — the error bound video is especially important since this is the exam's favorite problem type). Then skript pp. 175–183: Cᵏ classes, Taylor polynomial, **Restglied (Lagrange form)**. MIT L20 first half.
- **AN.F2** *(1.5h)* — Standard expansions by heart: eˣ, sin, cos, ln(1+x), (1+x)^α. Practice: compute T₂/T₃ + error bound on a given interval (IngMath_2 has dozens, solved).
- **AN.F-test** — (1) Taylor T₂ of f at x₀ + Lagrange error bound. (2) Use Taylor to compute a limit (alternative to l'Hospital). (3) **Wire check W8:** Newton's method and the Hessian-based view of optimization in AML L06 are literally "replace the loss by its T₂ and jump to the minimum of the parabola" — write that sentence with the formulas. Also: second-order Taylor is where convexity (f″ ≥ 0) enters AML's convergence story.

### BLOCK AN.G: Integralrechnung *(~5.5h)*

Skript: pp. 201–225 — Das Riemann-Integral (202), Hauptsatz und Integrationsregeln (213), Uneigentliche Integrale (222). Skip: Exkurs numerische Integration (225).

- **AN.G1** *(1.5h)* — Skript pp. 202–213: Riemann sums (Ober-/Untersummen), integrability of continuous/monotone f, linearity + monotonicity of ∫. MIT L20 second half + L21. Layer 1: Strang Ch. 5 if Riemann sums feel abstract.
- **AN.G2** *(2h)* — Skript pp. 213–222: **Hauptsatz** (both directions), partielle Integration, Substitution. Professor Leonard Calc 2 — **"Fundamental Theorem of Calculus"** (non-negotiable, watch before the skript section), then **"Integration by Parts"** and **"U-Substitution"** videos for fluency drill — exam points are won on clean technique here. Forster Übungsbuch integration chapters for volume.
- **AN.G3** *(1h)* — Skript pp. 222–225: uneigentliche Integrale (unbounded interval / unbounded integrand), convergence via comparison — note the deliberate echo of AN.B's Majorantenkriterium.
- **AN.G4** *(1h)* — Drill: u10_L, IngMath_2 integral chapters, AS-Ana1 integral tasks.
- **AN.G-test** — (1) Compute ∫ via parts AND via substitution. (2) Decide convergence of ∫₁^∞ 1/x^s dx by s. (3) State the Hauptsatz precisely. (4) **Wire check W9/W10:** Hauptsatz ⇔ "the density is the derivative of the CDF, F′ = f" (SaD 06/08); E[X] = ∫xf(x)dx is an improper integral over ℝ, and "the normal density integrates to 1" (SaD 08) is an improper-integral statement. P(a ≤ X ≤ b) = F(b) − F(a) IS the Hauptsatz.

### BLOCK AN.X: Exam Prep *(~9h, after AN.G — mirrors Chat 1 Block N's 3-phase structure)*

- **AN.X1** *(2h)* — **`kleine_beweise.pdf` ⭐ — work EVERY proof on the list.** This is the HU Tutorium's own exam-prep sheet for this exact module (SoSe 2025): the "small proofs" the Klausur expects you to reproduce. The single highest-signal document in the folder.
- **AN.X2** *(2h)* — `ana_inf_serieWV.pdf` (the course's own Wiederholung & Vertiefung sheet) under semi-exam conditions.
- **AN.X3** *(1.5h)* — Cheat sheet (1–2 pages, Chat 1 N6 style): ε-N/ε-δ templates · Standardgrenzwerte · series decision tree (from AN.B2) · derivative/integral rules · standard Taylor expansions · theorem names with hypotheses (Bolzano-Weierstrass, ZWS, Min/Max, Rolle, MWS, Hauptsatz).
- **AN.X4** *(2.5h)* — Timed mixed practice: `Aufgabe 3 ist gut.pdf` (Probeklausur, solved) + a self-assembled Klausur from AS-Ana1/Aufgabensammlung_M1 (1 Folgen-ε-N + 1 Reihen-classification + 1 Stetigkeit/ZWS + 1 Kurvendiskussion/Taylor + 1 Integral). **External solved-Klausur bank: LEARNING-RESOURCES §6 → "Analysis (AN)" subsection** — Marburg (3 solved Klausuren, first-half archetypes) + Regensburg (solved exam *with examiner "Häufige Fehler" commentary*, second-half + state-and-prove style) are the two ⭐ anchors; both PDFs ✅ downloaded in `Plans/Math/analysis/Analysis/Klausuren-extern/`.
- **AN.X5** *(1h)* — Gap pass: re-drill whatever X4 exposed. **Also chase real HU Altklausuren via the same 3 channels as LEARNING-RESOURCES §6** (Moodle Probeklausur, Fachschaft archive, last-year students) — `kleine_beweise.pdf` proves last year's tutors circulated prep material; there may be more.
- **AN.X-test** — comprehensive: one full self-assembled Klausur, timed, graded against solutions.

**Total: ~48h** (AN.0 3 + A 7 + B 5 + C 5.5 + D 3.5 + E 5.5 + F 4 + G 5.5 + X 9).

---

## Cross-Wire Registry (Analysis ↔ SaD ↔ AML/AMLS)

> Same format as `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`. Each wire is rehearsed in the block self-tests above.

| # | Analysis (this plan) | Connects to | The wire |
|---|---|---|---|
| W1 | AN.A ε-N convergence | SaD 09 estimation | Consistency of X̄ₙ (LLN) IS sequence convergence; "limit of relative frequency" is the frequentist definition of probability (SaD 04) |
| W2 | AN.B geometric series | SaD 07 geometric distribution | Σp(1−p)ᵏ = 1 normalization; E[X] computed via differentiated geometric series |
| W3 | AN.B/AN.D exp series | SaD 07 Poisson | Σλᵏ/k! = e^λ is exactly why Poisson probabilities sum to 1 |
| W4 | AN.D Logarithmusgesetze + ln monotone | SaD 09 MLE, **AML L05 MLE→cross-entropy** | log turns Π into Σ; monotonicity (AN.C inverse functions) is why argmax survives the log |
| W5 | AN.C continuity, monotone inverse | SaD 06/08 CDF + quantile function | CDF properties; quantile = inverse function, well-defined by AN.C theorems |
| W6 | AN.E f′ = 0 + extrema | SaD 03 least squares, SaD 09 MLE, AML L03 loss minimization | "Differentiate, set to zero, check second order" is THE shared recipe of all three |
| W7 | AN.E Mittelwertsatz | AML L03/L06 gradient descent | MVT honesty behind "f decreases in the direction of −f′"; Lipschitz-type step-size arguments |
| W8 | AN.F Taylor/T₂ | AML L06 Newton, Hessian, Adam | Newton = jump to the minimum of the local T₂ parabola; convexity = f″ ≥ 0 |
| W9 | AN.G Hauptsatz | SaD 06/08 density ↔ CDF | F′ = f and P(a≤X≤b) = F(b)−F(a) ARE the Hauptsatz |
| W10 | AN.G uneigentliche Integrale | SaD 08 normal distribution, SaD 06 E[X] | ∫ℝ φ = 1 and E[X] = ∫xf dx are improper integrals; comparison test decides existence of moments |
| W11 | AN.C Min/Max-Satz (compact) | AML L03 | Why a continuous loss on a compact set HAS a minimizer at all |
| W12 | AN.A recursions (Ausflug) + convergence | AML L03/L06 | GD iterates θₖ₊₁ = θₖ − η∇L form a recursively defined sequence; convergence questions are AN.A questions |
| W13 | AN.A standard limits ((1+x/n)ⁿ→eˣ) | SaD 08/10 | Shows up inside CLT-flavored and Poisson-limit arguments |
| W14 | AN.0 Maschinenzahlen (Ausflug) | **AMLS L08/S.E hardware** | Float rounding/precision is the math behind fp16/bf16 mixed-precision training |
| W15 | *(excluded chapter, optional)* Skript „Exkurse": Gradientenverfahren pp. 243–247 | AML L03/L06 | The skript's OWN bridge to gradient descent. Excluded from exam scope — but a 20-min read right before F.J pays off. Flagged, not scheduled. |

**Direction of traffic:** when you hit these topics on the SaD/AML side (Chat 1 Blocks E–J, F.N), the wires run backwards too — each one is a free Analysis rehearsal. The Kombimodul coupling means this is not a nicety; it is the grade.

---

## Calendar Fit

### ⭐ KW-27 RECALIBRATION (Jul 4) — THE operative schedule

**Reality check:** exam is **Mo 27.07** (Monday, start of KW 31), no AN study logged yet, mlprov binds until Jul 15. That leaves ~3 weeks. The Scenario-1 table below assumed AN.0 in KW 25 — it didn't happen; superseded. Realistic budget ~25–28h → triage below the old 30–35h target:

| Window | AN hours | Blocks (compressed targets) |
|---|---|---|
| **Jul 4–5 (KW 27 wknd)** | ~2h | **AN.0** compressed: recall sheet + check, skip 0.3 (Maschinenzahlen → read W14 note only). Skim `kleine_beweise.pdf` (20 min) — it calibrates everything after |
| **KW 28 (Jul 6–12)** | ~5h | **AN.A** (A1–A3 + half of A4 drill; target: ε-N fluency + Grenzwertsätze + Standardgrenzwerte) |
| **KW 29 (Jul 13–19)** | ~6h (post-Jul-15 freed) | **AN.A finish + AN.B** (decision tree = the artifact) **+ AN.C start** |
| **KW 30 (Jul 20–26)** | ~12–15h (exam week, merged with F.N) | **AN.C finish → AN.E core (MWS, l'Hospital) → AN.G core (Hauptsatz + parts/substitution) → AN.D+F formula-level only (log laws; T₂ + Lagrange bound) → AN.X merged**: kleine_beweise EVERY proof ⭐ · WV-Serie · cheat sheet folded into the M2 sheet with the SaD clusters · ONE timed Probeklausur (Stuttgart or Marburg) |
| **Mo 27.07, 12–15h** | — | **M2 Klausur (SaD + Analysis, one sitting)** |

**Hard-floor spine if hours collapse** (protect in this order): AN.0 → AN.A (ε-N + limits) → AN.B decision tree → AN.C (ZWS/Min-Max statements) → AN.E (MWS + l'Hospital) → AN.G (Hauptsatz + technique) → kleine_beweise → one timed Klausur. AN.D/AN.F drop to cheat-sheet formulas.

**Merged-prep rule (the Jul-3 insight):** ONE 3h Klausur covers both halves → every KW-30 session pairs an AN block with its F.N cluster via the wires (AN.A↔N4 consistency, AN.B↔N3 distributions, AN.G↔N3 density/CDF, AN.D↔N3 MLE-log-steps). One combined cheat sheet, not two. Sequence F.N cluster review in the same sittings.

---

### Historical scenarios (KW 24 — kept for the record, superseded by the recalibration above)

Analysis was invisible in SEMESTER-STATUS §7; binding constraints (Seminar Jun 18, mlprov Jul 15) could not move. Two scenarios were defined:

### Scenario 1 — Analysis Klausur in the late-July cluster (with SaD/AML) — ✅ ACTIVE (confirmed Jun 12; table superseded Jul 4)

Tight but possible IF it starts on time. ~48h cannot fit; triage to ~30–35h: compress drill steps (A4→1.5h, X4→1.5h), lean harder on Layer 1 skips.

| KW | Slot | Blocks |
|---|---|---|
| 25 (Jun 16–22) | post-seminar, ≤2h | AN.0 refresh |
| 26 (Jun 23–29) | 4h | AN.A |
| 27 (Jun 30–Jul 6) | 4h | AN.A finish + AN.B |
| 28 (Jul 7–13) | 4h | AN.C |
| 29 (Jul 14–20) | 4h (after Jul 15 submission!) | AN.D + AN.E start |
| 30 (Jul 21–27) | ~~AMLS exam week~~ (AMLS → 2. PZ, Jun 12) — window now belongs to AML/SaD/AN exam prep | AN.E continue |
| 31+ | 8–10h/wk | AN.E–G + AN.X before the Klausur |

⚠️ This only closes if the Klausur is in **August or the very end of July**. If it collides with the Jul 23–31 window, talk to the Prüfungsbüro about the Zweittermin — three exams + two submissions in two weeks is not a plan, it's a pile-up.

### Scenario 2 — Zweittermin / September–October (recommended if free choice exists)

The clean version. Until Jul 23: **zero scheduled Analysis hours** (the wires in Chat 1 Block N exam prep keep the concepts warm for free). Then:

| Week post-Jul 23 | Blocks | Hours |
|---|---|---|
| 1 | AN.0 + AN.A | ~10h |
| 2 | AN.B + AN.C | ~10h |
| 3 | AN.D + AN.E | ~9h |
| 4 | AN.F + AN.G | ~10h |
| 5 | AN.X | ~9h |

Full ~48h, no triage, done in 5 weeks with summer-level capacity. Buffer before an October Klausur.

**Default until the date is known:** behave as Scenario 2, except do AN.0 (3h, low-energy refresh material) opportunistically in KW 25–26 — it's a good "too tired for mlprov" filler and de-risks Scenario 1.

---

## Action Items (updated KW 27, Jul 4)

1. ✅ ~~Confirm the Analysis Klausur date~~ — **RESOLVED Jul 3: Mo 27.07, 12–15h, ONE combined M2 Klausur with SaD** (2. Termin Fr 09.10). Remaining admin: **verify M2 registration** (1.-PZ Anmeldung closed 02.07!); Rücktritt gate Mo 20.07 if prep collapses.
2. Skim `kleine_beweise.pdf` once NOW (20 min) — it calibrates what "exam-ready" means for every block above. *(Scheduled in the KW-27 recalibration: Jul 4–5.)*
3. Ask in the Analysis Moodle/Fachschaft for Altklausuren (same channels as LEARNING-RESOURCES §6).

---

*Created by Hub Chat (Brain), KW 24. Wired into SEMESTER-STATUS §0/§1/§3/§5/§6/§11, CHAT-DIVISION, HANDOFF, LEARNING-RESOURCES.*
