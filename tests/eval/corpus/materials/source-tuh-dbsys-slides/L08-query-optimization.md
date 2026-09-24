# Database Systems — L08 Query optimization (slide text export)

Slide 5. Query → parse → logical plan (relational algebra) → rewrite → physical plan → execute.
Slide 9. Heuristic rewrites: push selections down, push projections down, replace σ(R × S) by a join.
Slide 14. Cost model inputs: page counts, tuple counts, histograms, index availability.
Slide 17. Selectivity of conjunctions under the independence assumption: product of selectivities.
Slide 22. Join ordering in System R: bottom-up enumeration of left-deep plans; keep the cheapest plan per subset; interesting orders.
Slide 28. Exam: apply the rewrite rules to a given SQL query and draw the resulting operator tree.
