# Noor's plan sketch

For the Section 1 example, the scan starts with 1,000 rows. A safe predicate
move reduces the rows entering the later work to 240; projection keeps the
needed columns, and the final grouping yields 12 rows. I still need to explain
why a predicate that changes null handling cannot simply move across the join.

This is a draft explanation for the active query-lab stage, not a completion
claim or proof that the rewrite is always safe.
