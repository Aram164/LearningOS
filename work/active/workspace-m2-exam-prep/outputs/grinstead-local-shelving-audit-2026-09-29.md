# Grinstead & Snell local shelving audit — 2026-09-29

## Local

- The newly supplied `LearningOS/Grinstead and Snells Intro to Probability.pdf` is a 518-page, 4 July 2006 Chance Project version of *Grinstead and Snell's Introduction to Probability*. Its SHA-256 before shelving was `763eab9894983ddfd6cd7f84685548d1515a9326a2d9fd015474534460551a5e`.
- The exact bytes were moved to `materials/mathematics/probability-statistics/grinstead-snell/grinstead.pdf`; the post-move SHA-256 is identical. The `material://source-grinstead-snell/grinstead.pdf` compatibility path resolves to that file.
- Inspected physical PDF pp. 67–69 (density/CDF), 192–197 and 201 (discrete families), 213–215 (exponential/count connection), 313–318 (Chebyshev/LLN), 333–340 and 364–366 (CLT and continuous examples). Printed page numbers in this PDF are eight lower.

## Linked

- `source-grinstead-snell` already exists in `sources/registry/mathematics.yaml` and has five rich routes in the SaD module source map (L04–L08). The registry's claim that the download never landed is now stale. The three L06–L08 routes are in the complete menu but not in the ordered study stages.
- This shelving change adds the local path to the existing source record. It leaves the five routes unchanged, including their current external links, and does not change route identity, coverage, stage placements, order, course scope, learner progress, or source selection. The no-write preflight refused a proposed local-link addition to L04 because that route has an approved material synthesis; no route changes were applied.
- The existing URL remains as an external provenance and access option. `sources/collections/math-bookshelf.yaml` already lists the book; its pending-download description needs to be corrected.

## Completeness

- This is a local-availability repair for an already registered source, not a new source or a new pedagogical coverage claim. The earlier SaD L06–L08 distribution-bridges audit remains the analysis of selected stage content.
- The complete local copy is available and page-checked; no known missing part of this PDF is being represented as present. Broad chapter locators in the existing menu remain for a later reading-order revision; this shelving change does not treat those whole chapters as required reading.
