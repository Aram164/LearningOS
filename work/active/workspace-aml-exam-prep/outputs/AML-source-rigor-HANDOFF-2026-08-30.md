# AML source-rigor — handoff, 2026-08-30

Stopped on instruction after Gate 1 + P1 preflight. **Nothing applied; the tree is
unchanged apart from these four new files under `outputs/`.**

## What is in the workspace

| File | What it is | State |
|---|---|---|
| `AML-SOURCE-RIGOR-PLAN-2026-08-30.md` | the design: measured gap, the standard, per-unit angle spine + locator repair tables, the sweep, four packages, risks, numeric acceptance | complete |
| `AML-source-rigor-coverage-audit-2026-08-30.md` | Gate 1 evidence: page basis for every local material, the printed-vs-PDF defect, exclusions and deferrals | complete for P1; two boxes deliberately un-ticked for P3 |
| `AML-source-rigor-plan-P1.yaml` | the P1 import package (33 sources, 223 routes, ships `unit-aml-exam-prep` for its selection guard) | **preflight-clean, not imported** |
| `aml-source-rigor-build/` | `builder.py`, `run.py`, `p1.py`, and `toc-evidence/` — the raw PDF outlines every page number came from | reusable for P2–P4 |

## To resume

```bash
cd LearningOS/repository && .venv/bin/python tools/los.py bootstrap
```

then, with that snapshot:

```bash
cd LearningOS/repository && .venv/bin/python tools/los.py module-plan-import module-hu-aml --file work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P1.yaml --expected-snapshot sha256:CURRENT
```

P2–P4 are authored as further `pN.py` edit modules and built with
`run.py p1,p2 …` (edits apply cumulatively over the canonical map).

## Decisions taken, per the approved recommendations

- **Sweep depth:** priorities 1–3 (~17 sources, ~40 routes). Candidates are ranked in the
  design §7 and triaged in the audit; **none has been opened yet** — each is still an
  assumption about fit.
- **`source-sutton-barto-rl`:** reference-only, unrouted, with the reason written into its
  `why`. Applied in P1.
- **Graduate-depth books and the fourth video rail:** deferred with reasons recorded.
- **Granularity:** four packages, smallest first.

## Two things a resumer must not lose

1. **Registry page numbers are printed pages.** ISLP +7, Murphy +30, Kroese ~+18, csc411
   +5. Never copy a `useful_sections` page into a locator; re-derive it with
   `tools/material_toc.py --toc`. The evidence is in `toc-evidence/`.
2. **`SELECTION-LOCATOR-GUARD` is an error.** Changing a route locator that
   `unit-aml-exam-prep` selects requires shipping that unit record too. `run.py` does this
   automatically — keep using it rather than hand-editing the package.

## Environment change made

`brew install poppler` was run, because `tools/material_toc.py --verify` and its
printed-contents fallback shell out to `pdftotext`, which was missing. Without it the two
outline-less books (`csc411.pdf`, `Zacharski_…pdf`) cannot be verified at all.
