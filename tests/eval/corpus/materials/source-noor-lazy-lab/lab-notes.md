# Synthetic Lazy Query Lab

This is original evaluation material for Noor's fictional course. It is not a
copy of the Polars documentation.

## 1. Reading a plan

A lazy query records transformations before execution. In the lab's example,
the source has 1,000 rows. A predicate on `active` retains 240 rows. A
projection then keeps `id` and `amount`, and a group-by produces 12 customer
totals. A plan explanation shows the predicate below the projection, close to
the scan. Moving a predicate below a scan is permitted only when the predicate
uses columns available at that point and preserves the intended null rules.

## 2. An intentionally wrong aggregate

The lab's first report says 13 customer totals. The extra group appears when a
join duplicates one `customer_id`: the right-hand key is not unique. Filtering
earlier reduces the number of rows processed but does not repair the duplicate.
The correct repair is to establish the join-key cardinality before aggregating.
The before/after row counts are 240, 241, and 12 after correcting the join.

## 3. Materialization and provenance

Collecting a lazy plan creates an in-memory result. Repeating a query after a
source file changes is a new observation, even if the query text is identical.
An explanation saved from the earlier source bytes is historical evidence;
it must not be presented as analysis of the changed file. A saved analysis may
quote the exact section it inspected and bind to those bytes.
