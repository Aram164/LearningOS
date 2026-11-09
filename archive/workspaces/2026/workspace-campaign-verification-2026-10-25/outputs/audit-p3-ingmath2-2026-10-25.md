# Coverage audit — IngMath2 printed-page anchors, three routes (L2-16, 2026-10-25)

Scope: page-anchor corrections on the three drill routes named by RECHECK-80
finding F2 (route-an-ch05-analysisdrillblaetterext-2,
route-an-ch06-analysisdrillblaetterext, route-an-ch07-analysisdrillblaetterext).
`--check` only, never applied.

## Local

- `IngMath2_Aufgaben.pdf` (312 pp) opened with pypdf end to end for the cited
  range (PDF pp. 75-270); the printed book page number is carried in each
  page's header, and the PDF position is printed + 3 throughout the cited
  span (title page + two Inhaltsverzeichnis pages), reproducing RECHECK-80
  F2's six measurements and extending them: all 28 section anchors named by
  the three locators were verified at printed + 3 (§11.1 75→78, §11.2 85→88,
  §11.3 90→93, §11.4 92→95, §12.3 118→121, §13.1 127→130, §13.2 132→135,
  §14.1 140→143, §14.2 150→153, §14.3 158→161, §14.4 180→183, §14.5 190→193,
  §16.1 219→222, §16.2 221→224, §16.3 225→228, §16.4 227→230, §17.1 234→237,
  §17.2 238→241, §17.3 245→248, §17.4 246→249, §18.1 252→255, §18.2 265→268,
  and the five chapter starts). Each heading's text was found on the expected
  PDF page; each page also displays the printed number.
- The corrected locators keep every section name and every printed number as
  a `(printed p. N)` cross-reference, and state each PDF position in the
  module's `PDF p. N` house style (the same style the klausuren-TUM routes
  use, verified exact by RECHECK-80).
- The filename gains the provenance paren the module's own ch03 IngMath2
  route already carries — `IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg
  1991):` — which also makes the locator resolvable: the current
  bare-colon form (`IngMath2_Aufgaben.pdf:`) defeats the repository's
  material-suffix token parser and resolves to zero files today; the
  corrected form resolves to the one real file, whose sha256 matches the
  registered materials manifest entry.

## Linked

- No other route or source is touched; the full source map is carried with
  exactly these three locator strings changed. The routes' covers, titles,
  angles and angle_detail are untouched (none carries page numbers).

## Completeness

- Every bare `p. N` anchor in the three locators becomes the correct PDF
  position with the printed number preserved as a cross-reference; a reader
  who jumps to a cited page now lands on the named section.
- Duplicates: none introduced. Exclusions: the ch03 route
  (route-an-ch03-analysisdrillblaetterext-5) carries the same printed-number
  anchors for Kap. 10 (§10.1 p. 2 → PDF p. 5, §10.2 p. 8 → 11, §10.3 p. 16 →
  19, §10.4 p. 35 → 38 — measured this session) but is NOT confirmed by the
  named verdicts; it is recorded in PACKAGES.md as a new finding for Aram and
  deliberately left unchanged here.
- Unresolved gaps: none — the book's offset is uniform + 3 across the whole
  cited span.
- Checks: local_inventory_complete, linked_inventory_complete,
  materials_opened_and_content_checked, current_and_prior_scope_reconciled,
  duplicates_and_numbering_checked, exclusions_and_unresolved_gaps_recorded —
  all true as evidenced above.
