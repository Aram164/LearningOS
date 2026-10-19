# Algo 2 resource coverage audit — 2026-08-16

This audit covers the resource layer of the existing `unit-algo2-exam-prep`
reinstatement plan. It does not reactivate the paused module and it does not
replace the twelve-topic course spine. Its purpose is to make every assigned
local item directly openable, add a small number of high-value explanations and
practice routes, and keep optional depth visibly separate from required work.

## Local inventory

The complete current HU bundle was checked at
`material://source-algo2-hu-materials`. It contains all twelve topic decks:

- `ad2_fastmultiplication.pdf`
- `ad2_amortizedanalysis.pdf`
- `ad2_btrees.pdf`
- `ad2_fibonacciheap.pdf`
- `ad2_splaytrees.pdf`
- `ad2_hashing.pdf`
- `ad2_shortestpaths.pdf`
- `ad2_maximumflow.pdf`
- `ad2_bipartitematching.pdf`
- `ad2_stablematching.pdf`
- `ad2_computationalgeometry.pdf`
- `ad2_fastfouriertransform.pdf`

The same bundle also contains the stable-matching exercise sheet and six
assigned or course-adjacent papers:

- `stable matching aufgaben.pdf`
- `BayerM1970_OrganizationAndMaintenanceOfLargeOrderedIndices.pdf`
- `Pagh06_CuckooHashingForUndergraduates.pdf`
- `SleatorT1985_SelfAdjustingBinarySearchTrees.pdf`
- `Thorup1999_UndirectedSingleSourceShortestPathsWithPositiveIntegerWeightsInLinearTime.pdf`
- `ChenKLPPS22_MaximumFlowAndMinimumCostFlowInAlmostLinearTime.pdf`
- `Vazirani20_AProofOfTheMVMatchingAlgorithm.pdf`

All course-named books are held locally and were mapped to their exact files:

- DMS, `material://source-dms-grundwerkzeuge/dms.pdf`
- CLRS German, `material://source-clrs/clrs-de.pdf`
- Ottmann/Widmayer, `material://source-ottmann-widmayer/ow.pdf`
- Kleinberg/Tardos, `material://source-kleinberg-tardos/Kleinberg-Tardos_Algorithm-Design.pdf`

Eight solved Frankfurt ALGO2 exams from 2021–2024 were also inventoried under
`material://source-algo2-frankfurt-klausuren`; the newest 2024 sitting is linked
directly from the oral-delivery stage and the directory remains the complete
reserve bank.

The two previously recorded local gaps remain real: the 8 April organisation
deck is absent, and there are no HU exercise sheets except stable matching.

## Linked inventory

The following linked resources were opened and checked on 2026-08-16. Selection
was topic-specific; no full second course is prescribed.

- MIT OpenCourseWare 6.046J: exact lectures for convex hull, FFT, amortized
  analysis, all-pairs shortest paths, max-flow/min-cut, and matching.
- MIT OpenCourseWare 6.006 Fall 2011: the exact Karatsuba lecture.
- Goethe Frankfurt ALGO2: German short videos, exercise sheets, and the solved
  exam index; used for transfer vocabulary and practice, not as scope authority.
- CMU 15-451: the splay-tree access-lemma notes.
- TU Wien AD2: the German Fibonacci-heap chapter.
- Princeton/Kleinberg–Tardos: the stable-matching slide deck.
- Reducible: the single FFT intuition video.
- VisuAlgo: exact SSSP, max-flow, matching, and convex-hull visualizers.
- Open Data Structures: the exact B-tree chapter.
- Jeff Erickson's free Algorithms book/notes, William Fiset's graph playlist,
  and KIT Algorithmen 2 remain optional menu routes rather than required stage
  work.

Every selected linked item uses an `https://` URL. Every local stage item uses an
explicit `material://`/vault path or, for the one filename containing spaces, an
exact resolver-safe filename tied to its registered source. The interface no
longer has to guess from a human chapter label.

## Reconciliation, duplicates, and exclusions

- The current twelve-topic order, prerequisites, estimates, paused state, and
  oral-exam emphasis are preserved.
- Each topic now has one required course deck, the assigned book/paper where one
  exists, and at most a small number of clearly ranked support items.
- Repeated full-course recommendations were not copied into every stage. They
  live in the module source menu and are opened only for a diagnosed gap.
- The duplicate T07 completion condition was removed.
- Source records already present in the Algorithms registry were reused. Only
  VisuAlgo and Open Data Structures were added because they fill distinct visual
  and B-tree explanation gaps.
- The Frankfurt material is external and written; it cannot substitute for an
  HU oral mock. The oral stage therefore continues to require spoken viva drills.
- Research papers by Bayer/McCreight, Thorup, Chen et al., and Vazirani are
  preserved as optional depth. They are not assigned during the first exam pass.

## Completeness sign-off

Local inventory is complete for the files currently registered for Algo 2.
Linked inventory is complete for the selected topic routes. Local files and web
targets were opened or resolved to exact targets, current and prior scope were
reconciled, duplicate topic numbering was checked, and all known exclusions and
unresolved gaps are recorded above. This audit is therefore sufficient to apply
the resource-only revision through the module-plan import gateway.
