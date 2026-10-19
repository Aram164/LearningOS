# SaD L11 angle verification — pilot record (2026-09-20)

Second summary-layer pilot; first with real rejects. Method: 6 chapter
summaries authored from the disposable text cache and promoted
(digest b7decfed…f302, model muse-spark 2026-09); triage grades from
summaries; full read of accepts; full spot-read of rejected Ch G.
Ch A (pp. 1–2, 202 bytes) triaged by direct read — below the
promote window (min 200 chars AND max 80% of source cannot both
hold at 202 bytes), correctly so: tiny ranges need no summary.

## Grades

- Ch A pp. 1–2 (title/quiz admin): REJECT (direct read).
- Ch B pp. 3–11 (DS intro, pipeline, data types): ACCEPT → s1, s3.
- Ch C pp. 12–20 (ML classes, AI vs ML): ACCEPT → s2.
- Ch D pp. 21–32 (supervised setup, splits, loss, learning): ACCEPT
  → s4, s5, s6-loss, s3-p27.
- Ch E pp. 33–38 (confusion matrix, P/R/F, ROC/AUC): ACCEPT → s6.
- Ch F pp. 39–46 (inductive bias, overfitting, CV, bootstrap):
  ACCEPT → s4, s5, s7.
- Ch G pp. 47–49 (compute anecdotes, GreenCompute promo): REJECT —
  spot-check full-read confirms zero definitions, methods, or
  examinable procedures. Rejection SAFE.

## Confirmed

- All five accepted chapters match their stage slices; all slice
  page claims resolve to the stated content.
- s6's macro/micro/weighted aggregation and PR-AUC are absent from
  the deck (deck-wide grep confirms) but covered by siblings:
  Blatt-05 Aufgabe 3(a)-(d) (micro/macro), UE7 slides 22-30
  (per-class/aggregate reporting), book Ch 3 (ROC). Division of
  labor, not a gap.
- Map's "printed slide labels may differ" boilerplate is real:
  printed numbers run exactly physical+1 throughout (p. 3 shows 4,
  …, p. 49 shows 51). Physical numbering in locators is correct.

## Findings (F-L11-1 applied 2026-09-20 via unit-plan-revise transaction-20260920-025624-001)

- F-L11-1 (slice gap): deck pp. 22–23 — the formal D1/D2/loss
  supervised setup plus the open-questions roadmap — sit in no
  stage slice (s2 ends at 20, s4 starts at 24). The D1-train /
  D2-test / gold-standard formalism is substantive and examinable.
  Extended s4 to pp. 22–26 (formalism feeds the split practice it
  opens) via unit-plan-revise transaction-20260920-025624-001.

## Volumes

Full deck 26,991 bytes; 6 summaries 8,729 bytes + Ch A direct 202
bytes = 8,931 triage bytes (ratio 0.331). Rejects A+G = 2,493 bytes
(9.2% of deck). Fidelity: 5/5 accepts stood, 2/2 rejects verified
safe. Exhaustive-verification cost 1.32× full read (pilot pays to
validate — expected at 91% accept). Simulated narrow task "plan s1
from summaries": 8,931 + Ch B 3,670 = 12,601 bytes vs 26,991 full
deck = 2.14×. s6-shaped task (E + pp. 29–30 offsets): 8,931 +
3,715 + 1,026 = 13,672 bytes = 1.97×.
