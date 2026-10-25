# C2-R — M2's unchecked no-`vault_path` routes, re-checked (L2-14)

Campaign block C2-R (CAMPAIGNS.md, "Next blocks"). Evidence only — no fixes,
no fix packages, no issues, nothing pushed. Item id **L2-14**.

## 1. What was run

- Clone: `~/los-glm-C2-2026-10/repository`, branch
  `takeover/complete-and-install-2026-10-23` at `a2e2d49d`, clean tree,
  read-only, never pushed. Same state the L1-234 measurement used.
- Materials read in place via the mounted symlink
  `~/los-glm-C2-2026-10/materials` → live `LearningOS/materials`; nothing
  wrote to it.
- Script: `scripts/c2_recheck80_audit.py` (next to the C2 scripts), run with
  the clone's venv (Python 3.14, pypdf 6.21.2). Full per-claim results with
  file paths and evidence snippets: `scripts/recheck80-results.json`.
- PDF lookup follows symlinks, as the block prescribes:
  `os.walk(MATERIALS, followlinks=True)` with a realpath cycle guard —
  527 PDF files under 511 distinct normalised names (NFC, ligatures
  ﬀﬁﬂﬃ→ff fi fl ffi, quotes ′ ’ ‘ ” → ', whitespace collapsed, lowercased,
  space-collapsed). The original `find_pdf` (`c2_sections_audit.py:69-75`)
  returned 0 files over the same tree because `.flat/` entries are symlinks
  and `Path.rglob` without `recurse_symlinks=True` never enters them.
- C2 pitfalls applied throughout: ligature/quote/diaeresis normalisation
  before every comparison, misses confirmed against whole-document text
  (never one page), pages read as PDF page numbers unless the page itself
  carries a printed number, title matches checked for TOC/heading context.

## 2. The audited set

Partition reproduced over all 600 `unit_routes` of the module's
`source-map.yaml`, same logic as `L1-234-CLAUDE-VERDICT.md`:

| bucket | verdict | this pass |
|---|---|---|
| URL sources, skipped by design | 16 | 16 |
| have `vault_path`, resolve | 318 | 318 |
| name no PDF, no `vault_path` | 186 | 183 |
| **name a PDF, no `vault_path`** | **80** | **83** |

The 3 extra routes (`route-an-ch05/06/07-analysisklausurenextern`) name
their PDFs in the abbreviated prose form `Regensburg_...pdf` /
`Marburg_...pdf` / `Paderborn_...pdf`. The original measurement's `PDFNAME`
regex cannot capture these (the character class excludes `.` before
`\.pdf`), so they sat in the "name no PDF" bucket. They are re-checked here
too; **the report's audited universe is 83 routes: the verdict's 80 plus
these 3.** Every one of the 83 resolved to at least one real PDF through the
symlink-aware index (exact, suffix, abbreviated-prefix or trimmed matches;
per-route resolution is in the JSON). No route in the module names a PDF
that is absent from the materials tree except the one in F1 below.

## 3. Findings

### F1 — defect (own class: PDF named but absent): `VL 09-training-neural-networks.pdf` does not exist

`source-map.yaml:10858`, route `route-b3e5bcb8f3813cbc477ac799`
(unit-m2-sad-l15, source-aml-ss26-lectures), locator verbatim:

> `lecture-slides/VL 08-feedforward-neural-network.pdf and VL 09-training-neural-networks.pdf`

`VL 08-feedforward-neural-network.pdf` exists. `VL 09-training-neural-networks.pdf`
exists **nowhere** in the materials tree (527-PDF index, exact and
fuzzy lookups). The actual AML deck is `VL 09-neural-networks.pdf`
(`machine-learning/classical/aml-ss26-lectures/lecture-slides/`); the
module that owns the deck binds it by the correct name —
`module-hu-aml/unit.yaml` for unit-aml-l09: "locator: lecture-slides/
VL 09-neural-networks.pdf (74 pages)". So the one-word name drift
("training") is in M2's route only, and the route's promised material is
unreachable as addressed.

Origin (per the C2 rule, checked before calling it anything): the same
wrong name is carried by the **original generated plans** —
`work/active/workspace-m2-exam-prep/outputs/Analysis-chapter-plan-2026-08-29.yaml:9237`
and `M2-exact-locator-plan-2026-09-01.yaml` (6 occurrences, lines 9342,
32216, 32392, 32671, 32971, 33185). No later pass overwrote a correct name.
**Classification: original defect, not broadcast damage** — the route was
born pointing at a file that never existed, which is why no validator
check ever caught it (nothing compares a bare prose filename against the
tree when there is no `vault_path`).

### F2 — defect (low): the three IngMath2 routes cite the book's printed page numbers as bare `p. N`

`IngMath2_Aufgaben.pdf` (312 pp) carries the printed book page number on
each page; the PDF position is exactly printed + 3 (2 pages of
Inhaltsverzeichnis + title page). The three routes
(`source-map.yaml:3111` ch05-drill-2, `:3150` ch06-drill, `:3177`
ch07-drill) cite section pages that match the book's own TOC but not the
PDF position. Measured, section name → claimed p. → actual PDF page:

| section | claimed | actual PDF page |
|---|---|---|
| §11 Stetige Funktionen / §11.1 | 75 | 78 |
| §12.3 Exponentialfunktion, Logarithmusfunktion | 118 | 121 |
| §13 Differenzierbare reelle Funktionen / §13.1 | 127 | 130 |
| §14.3 Der Satz von Taylor | 158 | 161 |
| §16 Das bestimmte Riemannsche Integral / §16.1 | 219 | 222 |
| §17.2 Partielle Integration | 238 | 241 |

Evidence: the page text where each heading sits carries the printed number
(e.g. PDF p. 161 begins "158 kapitel 14. anwendungen der
differentialrechnung 14.3 der satz von taylor …"; PDF p. 222 begins
"kapitel 16 das bestimmte riemannsche integral 16.1 definition…"). A
reader who jumps to "p. 219" in a PDF viewer lands on the last page of
Kapitel 15, three pages early. Every section *name* and every *page-range*
claim in these locators verifies against the book's own TOC (all
§16.1–17.4, Kap. 11/13/14/15/16/17/18/19 titles found); only the bare
page anchors are off, uniformly by 3. Same defect class as the AML
session's F1 (printed-page anchors, there −30), here +3 and low.

Not affected: `AS-Ana1.pdf` and `Grenzwerte-von-Folgen.pdf` page anchors in
the same drill routes were measured and are **exact PDF pages** (AS-Ana1:
all 14 locator page claims equal both the file's own TOC and the observed
heading page, e.g. Aufgabe 1.8 p. 9 = PDF p. 9; Grenzwerte: Definition
p. 4 = PDF p. 4, Lehrsätze p. 8, Übungen p. 11–12, Lösungen p. 13–26).
The klausuren-TUM locators write `PDF p. N` and are correct PDF positions
(Anhang A claimed PDF p. 82; TOC printed 79 + 3 = 82 exactly).

### F3 — everything else in the 83: verified (the gap closes clean)

Per-claim outcome over the 83 routes (machine + hand passes; details and
verbatim evidence in `scripts/recheck80-results.json`):

- **Named files:** all resolve; the only absent file is F1's. Abbreviated
  names (`Regensburg_...pdf` etc.) resolve uniquely by prefix.
- **Slide-count claims (15):** all `N slides` claims equal the deck's real
  page count (e.g. 02_basics.pdf "39 slides" = 39 pages).
- **Slide-range and page-range claims (197 in-range, 0 out-of-range):**
  every `slides a–b`, `PDF pp. N–M` and `Physical pp. N–M` claim sits
  inside its named file's page count.
- **Strang book-page anchors (16, all verified):** the locators cite the
  Strang book's page numbers (`mitres_18_001_f17_ch02.pdf §2.6 Limits
  p. 123` …), and each named section heading sits on the excerpt page that
  carries exactly that printed number — §2.6→"123" (PDF p. 37), §2.7→"131"
  (45), §2.1→"87" (1), §2.5→"116" (30), §3.2→"143" (7), §3.8→"197" (61),
  §4.3 Inverse Functions→"216" (13), §6.2→"292" (10), §6.4→"310" (28),
  §10.4 The Taylor Series for e^x, sin x and cos x→"452" (22), §5.1→"229"
  (1), §5.3 Summation versus Integration→"240" (12), §5.5→"254" (26),
  §5.7→"267" (39), §7.1 Integration by Parts→"342" (2), §7.5 Improper
  Integrals→"367" (27). A naive page-count check flags these out of range;
  they are correct as printed-page anchors, and the printed numbers are
  visible on the pages themselves. Recorded so the next checker does not
  re-flag them.
- **Cross-book section refs in SaD routes (all verified in the named
  books, TOC context):** OpenIntro §1.3 "sampling principles and
  strategies" / §2.2 "considering categorical data" (l02); Blitzstein §3.9
  "connections between binomial and hypergeometric" and §4.8 "connections
  between poisson and binomial" (l07 — precisely the deck's
  relationships claim); Fahrmeir §10.3 "multiple testprobleme" (l10);
  ESL §7.10 "cross-validation" (l11); Kelleher §6.4.4 "bayesian networks"
  (l14); Forster §21 "gleichmäßige konvergenz von funktionen…" (ch05-TUM
  angle). All six books are in the materials tree.
- **Cross-refs to the skript (all verified in `unser skript.pdf`'s own
  TOC):** §§1.1–1.3 (Zahlenmengen / Vollständige Induktion / Wichtige
  Beziehungen), §3.5 "konvergenzkriterien für folgen", §3.6 "rechnen mit
  konvergenten folgen", §4.3 "absolute konvergenz", §4.5 "exkurs –
  produktreihen", §5.5 "besonderheiten stetiger funktionen…", §5.6
  "exponentialfunktion und logarithmen", §5.7 "gleichmäßige konvergenz
  von funktionenfolgen", §5.8 "exkurs – potenzreihen", §7.2 "hauptsatz und
  integrationsregeln", §7.3 "uneigentliche integrale", §7.4 "exkurs:
  einblick in die numerische integration", and the "Kapitel 1-7" range
  (TOC lists chapters 1 through 7).
- **Cross-refs to HU serie sheets (all verified):** Serie 05.2/05.3/05.4 in
  `ana_inf_serie05.pdf` (the "HU Hausaufgabe 5.4" ref is serie 05's
  Aufgabe 4, present), Serie 06.3, Serie 07.1 (Heron, exactly as the ch03
  klausur route says), Serie 08.1, Serie 09.1 — each sheet present with the
  named Aufgabe.
- **Task labels in the klausur papers (all verified):** Marburg Aufgabe 2
  ("sei r ein ring und p ⊂ r eine teilmenge…" — the ordered-ring task),
  Aufgabe 11 ("die reihe … n!nn konvergiert" = Σ n!/n^n), Aufgabe 12;
  Regensburg Aufgabe 3 and the 19 "[häufige fehler : …]" commentary boxes
  (the routes' quoted 'Häufige Fehler' and the A2.2 note "dass 'die'
  negation der definition von konvergenz anders 'aussieht'" — the route's
  'the negation looks different' is a faithful translation);
  Paderborn Aufgabe 6 ("bestimmen sie das integral ∫10 arcsin(t)dt",
  10 points); Stuttgart 'Aufgabe 3 ist gut.pdf' is 3 pp titled "lösungen
  zur probeklausur 1" with Aufgabe 1 Äquivalenzrelation, Aufgabe 2
  komplexe Zahlen, Aufgabe 3 Cauchy definition/negation — exactly the
  route's description, including the 2026-08-29 correction that the file
  is solved.
- **Drill-sheet claims (all verified):** auf-2-2 "Aufgabe 1 'Monotone
  Zahlenfolgen I'", auf-2-3 "Aufgabe 1 'Cauchy Konvergenzkriterium'",
  Loesungen4 "Aufgabe 16", Aufgabensammlung "Aufgabe 1"/"Aufgabe 13",
  KIT "Aufgabe 26", Tutorium "die jeder kennen muss" and "Hinweis für die
  Klausur", u10 "G31" with sections "Informelle Vorüberlegung" and
  "Formaler Beweis" — every quoted heading and Aufgabe number found in the
  named file.
- **Duplicates among sibling routes of one (source_id, unit_id) group
  within the 83: 0** — consistent with the original report's check D on
  all 600 routes.
- **Unverifiable locally (1 route, self-declared, not a defect):**
  `route-an-ch02-analysisdrillblaetterext-2`'s second file
  `Bestimmt_Scan.pdf` — its own locator says "(12 pp; scanned, weak text
  layer)" and the 2026-08-03 inventory flagged it; the §2.2/§2/§3 claims
  in its angle cannot be text-verified. The file itself is present.
- **Non-claims filtered (recorded so they are not re-chased):** 'Chapter
  1/3/6/7' occurrences are references to the module's own course chapters,
  not PDF sections; 'part 3' describes the filename
  `13_similarity_based_part3.pdf`; 'für Informatiker' describes the Ulm
  and Leipzig filenames; ' scopes stitched together do not reproduce the
  M2 paper' is a negative prose statement about the assembly itself; the
  `guide_chNN.pdf` in the ch06 Strang locator is a deliberate pattern
  placeholder and the concrete guides it stands for (guide_ch02/05/06/07)
  all exist.

## 4. What this changes in the prior verdicts

- The L1-234 measurement ("80 routes, silent skip") is confirmed and now
  closed: same 80 reproduced, plus 3 routes the original PDF-name regex
  could not see. No positive claim of the M2 report is invalidated; its
  check C is now accurate for **all** 601 claim-bearing routes it originally
  covered only for 318.
- The M2 report's misses list gains exactly two defect entries: F1 (one
  route, absent deck file, original defect) and F2 (three routes, printed-
  page anchors, low). Everything else the skipped routes claim verifies
  against the materials.

## 5. Assumptions and limits

- ASSUMPTION: the pypdf text extraction is faithful for the files probed;
  two known extraction quirks were handled (standalone `¨` before vowels
  breaks naive "ue" comparisons — the Regensburg 'Häufige Fehler' boxes
  were nearly mis-scored as absent because of it; math notation such as
  Σ n!/n^n extracts mangled — verified via surrounding words).
- ASSUMPTION: `module-hu-aml/unit.yaml:57` "74 pages" for VL 09 is cited
  from the live clone's AML module; the deck's existence under the correct
  name was verified directly in the materials tree.
- The F1 origin conclusion rests on the generated plans in
  `work/active/workspace-m2-exam-prep/outputs/` being the originals, per
  CAMPAIGNS.md C2 — consistent with the M2 report's use of the same folder.
- Text-verification cannot prove a scanned page's content;
  `Bestimmt_Scan.pdf`'s claims stay unverifiable by design of the file.

## 6. Out of scope (per block: evidence only)

No fixes, no `module-plan-import --check`, no issues, no edits to any
canonical file, nothing pushed. The one-command repair for F1 (correct the
locator to `VL 09-neural-networks.pdf`) and the page-anchor decision for F2
belong to Aram or the landing session per CAMPAIGNS.md.
