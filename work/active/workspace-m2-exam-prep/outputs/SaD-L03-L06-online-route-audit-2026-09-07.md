# SaD L03–L06 online-route audit — 2026-09-07

Codex's follow-up listed the video routes and external banks as inherited and unverified. Aram asked
for that audit over lectures 3–6. This report covers the routes on those four units that point at
something not held locally: 11 video, 3 website, 3 online-book and 7 course routes.

Every judgment below is against the source's own published index or page, opened on 2026-09-07 and
named inline. Nothing here is inherited.

## Local

No local material was changed and no local claim was re-opened in this pass. The local books,
exercise sheets and exam banks on L03–L06 keep the dispositions from the two earlier repairs; this
audit is bounded to routes whose target is not held on disk. The five stage placements that changed
are the ones belonging to the two online routes marked unavailable below, and they changed only in
`scope_triage`.

## Linked

### Verified — no change needed

- **3Blue1Brown, Essence of Calculus** (L03). Chapter 2 "The paradox of the derivative" and Chapter 3
  "Derivative formulas through geometry", as the route names them. (3blue1brown.com's written
  adaptation calls Chapter 3 "Power Rule through geometry"; the video title is the one the route uses,
  and the source is registered as the video playlist.)
- **3Blue1Brown, Essence of Linear Algebra** (L03). Chapter 9 is "Dot products and duality", confirmed
  on the lesson page, with chapters 1–4 covering vectors, linear combinations, linear transformations
  and matrix multiplication as the route claims.
- **3Blue1Brown, Bayes** (L04). The lesson presents Bayes geometrically with a "Thinking with area"
  section, and both companion videos the route names exist.
- **Grinstead & Snell** (L04, L05, L06). All three routes check out exactly: Ch 3 "Combinatorics"
  starts PDF p. 83 with §3.1 Permutations, §3.2 Combinations, §3.3 Card Shuffling; Ch 4 "Conditional
  Probability" starts PDF p. 141 with §4.3 "Paradoxes" — the Monty Hall / two-child / prisoner section
  the route describes; Ch 6 "Expected Value and Variance" starts PDF p. 233 with §§6.1–6.3.
- **Setosa OLS** (L03), on content. The page really does draw squared residuals as squares whose total
  area you minimise, and its points really are draggable. Only the widget naming was wrong.
- **Jurafsky & Martin** (L04), on placement. The 19 August 2026 draft does carry Naive Bayes as
  Appendix B, as the route says.

### Repaired

| Route | What it claimed | What the source shows |
| --- | --- | --- |
| Bendersky, L03 | "Derives the same closed-form solution twice — once by calculus, once by projection", with a long elaboration on the two independent justifications | The article has one section and one derivation, by calculus. It never mentions projection, column space or orthogonality. |
| jbstatistics, L05 | A three-video "Permutations and Combinations" series deriving nCr from nPr on screen | jbstatistics' full index has thirteen chapters, from discrete distributions to regression. **There is no counting, permutation or combination content on the site at all.** |
| StatQuest, L05 | "The Hypergeometric Distribution, Clearly Explained" (≈12 min), drawing the urn and building the ratio of combinations | StatQuest's index lists exactly one hypergeometric video: "Enrichment Analysis using Fisher's Exact Test and the Hypergeometric Distribution" — a different lesson for a different task. |
| jbstatistics, L06 | Two videos: expected value "and the companion variance video (≈10 min each)" | §1.2 "The Expected Value and Variance of Discrete Random Variables" is a single video covering both moments. |
| Jurafsky, L04 | "§4.3 works a complete numeric example" | In this release §4.3 is inside "Logistic Regression and Text Classification". The worked example is **§B.3**, in the appendix the route otherwise names correctly. A stale reference to the old chapter numbering. |
| Setosa, L03 | "the residual-square and leverage widgets"; "the leverage effect" | The page has a draggable-sample widget and a squared-error-area widget. The words leverage, outlier and influence appear nowhere on it. |
| StatQuest, L03/L04/L06 | "Linear Regression, Clearly Explained"; "Gradient Descent, Step-by-Step"; "Naive Bayes, Clearly Explained"; "Expected Values, Main Ideas" | Corrected to the titles StatQuest publishes in its own index. The channel's uploads carry "!!!" suffixes on some, so these are the author's canonical names rather than a claim that the old strings match nothing. |

The two routes whose material does not exist — jbstatistics counting and StatQuest hypergeometric —
are kept visible and marked unavailable rather than deleted, with the evidence on the route and
`reference-only` on their five stage placements, so the gap stays recorded instead of disappearing.
L05's counting nodes keep Blitzstein Ch 1, Ross, Pitman, Schaum's, Stat 110 and MIT 18.05, so nothing
is stranded. jbstatistics §1.8 "An Introduction to the Hypergeometric Distribution" would plausibly
fill the StatQuest gap, but assigning it is a content decision for review, not a repair, so it is
named here and not routed.

## Completeness

- `local_inventory_complete`: true for this pass, which touches no local material.
- `linked_inventory_complete`: true for L03–L06 — all 24 non-local routes on those four units were
  enumerated and each was either verified, repaired, or listed below as unresolved. None was skipped
  silently.
- `materials_opened_and_content_checked`: true for every claim changed here. The Bendersky article,
  the Setosa page, the StatQuest video index, the jbstatistics table of contents, the SLP3 Appendix B
  PDF and the Grinstead & Snell PDF were each opened and read.
- `current_and_prior_scope_reconciled`: true. No stage was added, removed or reordered; only route
  contextual fields, their unrefined stage copies, and five `scope_triage` values changed.
- `duplicates_and_numbering_checked`: true. Section numbers are quoted from the release the route
  names, and the SLP3 renumbering between drafts is stated explicitly rather than silently fixed.
- `exclusions_and_unresolved_gaps_recorded`: true; see below.

### Unresolved

1. **Kurzes Tutorium Statistik** (L04 and L06, two routes). The channel is `youtube.com/@pdmb`, and
   YouTube serves a consent gate to unauthenticated fetches; accepting it is not this session's to
   accept. Both routes now say on their face that their episode titles are inherited and unchecked.
2. **MIT 18.05, MIT 6.041SC, Harvard Stat 110, Ng's Coursera specialization** (seven routes across
   L03–L06). Their claims are about course structure — which lecture covers what, which problem sets
   have published solutions. The OCW class-materials page redirect-looped on fetch and these were not
   reached before this pass was closed. They remain inherited, not verified.
3. **L07–L15 and clustering.** This audit covered lectures 3 to 6 only. The video and external-bank
   routes on the other units are still in the state Codex left them.
