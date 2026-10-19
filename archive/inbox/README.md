# Resolved inbox drops

Drops leave `work/inbox/` only through the `inbox.resolve` capability
(WORKFLOWS §21): after a drop has been routed, the drop itself moves here
byte-identical, under the year it was resolved (`archive/inbox/YYYY/`,
preserving the inbox-relative path). Each move carries one receipt naming
both endpoints and the `routed_to` destinations.

Retained and never deleted; the archive never overwrites. The validator
and the loader do not read this tree — it is provenance, not live state.
