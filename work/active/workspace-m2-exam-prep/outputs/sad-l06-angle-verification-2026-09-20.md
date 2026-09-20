# SaD L06 angle verification — pilot record (2026-09-20)

Method: full deck read from the disposable text cache (60 pages, 34,839
bytes) plus rendered-page checks for formula-heavy claims (pp. 20, 21,
28–30, 41). Every deck angle checked claim-by-claim against cited
pages. Verdicts double as the first triage grades for the summary
layer (7 chapters promoted, ratio 0.214 over full deck text — recomputed
2026-09-20 from bytes on disk; the earlier 0.252 draft figure was stale).

## Grades

- Ch A pp. 5–8 (RV/discrete): accept with note.
- Ch B pp. 9–13 (CDF discrete): accept.
- Ch C pp. 15–23 (continuous/pdf/examples): accept with finding F3.
- Ch D pp. 24–32 (independence/expectation): accept with findings F4, F5.
- Ch E pp. 34–42 (variance): accept.
- Ch F pp. 44–50 (Chebyshev): accept.
- Ch G pp. 52–60 (LLN): accept.

## Confirmed (rendered where formulas matter)

- p.15 integral-to-+∞ slip + p.17 correct limit; p.20 uniform missing
  =1 branch and density-labeled-as-F(x) exponential (rendered);
  p.41 "Slope is 1" quoted exactly and wrong as written, integration
  itself correct (rendered); repair-cost numbers 3.0467/4.6733
  recomputed exactly and the per-error-vs-daily-total mismatch is real
  (rendered table); linearity proof without independence (p.31);
  E[XY] under independence (p.32); p.55 variance-half gap (proof line
  covers expectation only); p.58 stochastic-not-plain convergence;
  p.60 pointwise (not Glivenko–Cantelli) statement; Übung-3 Aufgabe 1
  cross-refs resolve to the SS26 sheet (values, masses, Z=|X| all
  match); all four spot-checked material_ref routes resolve.

## Findings (F1–F5 applied 2026-09-20 via unit-plan-revise transaction-20260920-023923-001; F6 deliberate no-change)

- F1 (transformations locator): cites p. 39, whose content is Var(aX+b)
  scaling — unrelated to the LOTUS/cost/|X| discussion. Propose
  locator "pp. 28–30,38" (p. 38 computes E[Z²] from Z's own
  probabilities — the combining method) and cite p. 31's combining
  note for the many-to-one sentence.
- F2 (stage 1 locator): P(X=x)=0 is stated at p. 19, outside cited
  pp. 5–8,18. Propose "pp. 5–8,18–19".
- F3 (stage 2, p. 21 — needs Aram's exam-model call): the slide's
  discrete-minutes model (x∈{0..9}, 0.4/0.5) is self-consistent; the
  angle teaches only the continuous-U reading (0.3/0.6) and calls the
  slide mixing. The genuine slip is "P(X≤3) = F(4)" (value 0.4 is
  F(3)). Propose teaching both models plus the slip, not replacing one
  with the other.
- F4 (transformations wording): p. 28 states the LOTUS formula but the
  name LOTUS appears nowhere on the rendered slide. Propose "(unnamed
  on the slide)".
- F5 (coverage gap): p. 24 (independence definition) is cited nowhere
  although p. 32 and pp. 53–55 depend on it. Propose adding p. 24 to
  the expectation locator.
- F6 (minor, no patch): p.19 "density need not be continuous" and the
  finite-expectation caveat are true beyond deck scope; the deck
  assumes steady cdfs. Leave, noted here.

All six touch map-local angle/locator fields (study-map.yaml), so the
fix path is a compact unit-plan-revise map patch — not route.patch
(the shared route carries only unit-level fields).

## Volumes

Full deck read 34,839 bytes; 7 summaries 7,453 bytes (ratio 0.214);
plus Übung-3 spot pages, 5 rendered pages, and the study map itself.
Overturns this session: one — my own suspicion that "Blatt 3" meant
recordings UE3 was overturned by the Übung-3.pdf evidence. Summary-led
grades: 7/7 stood after full read (findings above refine wording and
locators, none reverses an accept).
