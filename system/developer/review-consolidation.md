# Review consolidation register

Informative owner/caller adoption table for the systemwide review
consolidation. The machine-checkable register is
`system/contracts/review-consolidation.yaml`, validated by
`tests/test_review_consolidation.py`. This page is not a rulebook; the
binding contracts remain OPERATOR.md and the owning component pages.

Every finding names one owner, its affected callers, regression tests and a
disposition: `already-inherited`, `implemented`, `implemented-opt-in`, or
`rejected-as-unsafe` (inline envelope and stamp-only cache authority).
Source, hosted-CI and installed status are tracked separately; a green
source branch never claims live installation.
