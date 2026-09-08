# L07 bounded semantic repair audit — 2026-09-08

Boundary: `unit-m2-sad-l07` unit scope plus six of its source-map routes
(deck prose; MIT prose+covers; Dekking covers; Schaum covers; Arbeitsbuch
prose; Leuphana prose). Tijms, Harvard Stat 110, Kurzes Tutorium, and every
other L07 route are deliberately untouched. Knowledge nodes, unit order,
stage structure, source selections, and all other units are unchanged.
Stage-4 flags ride a separate `unit.map.import` package.

## Local

The deck and exercise PDFs are registered materials whose bytes are absent
from this checkout (materials tree not present); their page-slice locators
are inherited unchanged from the prior verified repair and this package does
not alter them. The MIT materials were opened from official MIT hosts on
2026-09-08 and text-extracted: Reading 4a (18 pages; §§3.1-3.4 Bernoulli,
Binomial, Geometric; §3.7 look-up-only Hypergeometric; zero Poisson
mentions) and Problem Set 2 (3 pages; Problem 6 `rbinom` coin-flip runs
simulation; no Poisson/Hypergeometric/Geometric items, no per-distribution
R functions).

## Linked

| Route | Evidence basis for this package |
|---|---|
| Deck prose | Prior repair's scope note (no dedicated Geometric section) |
| MIT 18.05 | Opened Reading 4a + PS2 PDFs named above |
| Dekking covers | Route's own locator (§4.4 Geometric; no Hypergeometric) |
| Schaum covers | Route's own locator (Ch 6 Binomial/Normal/Poisson) |
| Arbeitsbuch prose | Fail-closed narrowing; workbook slice unopened, nothing added |
| Leuphana angle | Adjudicated waiting-time item on Aufgabenblatt 2 |
| Tijms / Harvard / Tutorium | Untouched (Cambridge index; locator-consistent) |

The Dekking, Schaum, and Arbeitsbuch books were not opened in this
environment; no `covers` edge in this package rests on unopened-book
content (the Dekking/Schaum changes remove edges their own locators
contradict; the Arbeitsbuch change adds nothing).

## Completeness

Changed: unit scope (1 field), six routes (fields listed above).
Unchanged: all other module content. Unresolved and explicitly not
claimed: Arbeitsbuch Geometric coverage; deck/exercise physical page
slices (inherited, not reverified). No claim of mastery, readiness, or
exam weighting is made here; the deck route now disclaims exam-weighting
inference explicitly.
