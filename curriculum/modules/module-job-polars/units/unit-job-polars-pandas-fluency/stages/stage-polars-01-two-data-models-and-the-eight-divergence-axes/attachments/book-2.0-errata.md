# Reading the book on Polars 2.0

Your copy of *Python Polars: The Definitive Guide* is Early Release 8 (2024-12-03) and says it uses
Polars 1.13.1. Stratum locks 2.0.0 (released 2026-10-06). The concepts hold. These passages do not.
Page numbers are PDF viewer pages, checked against the file on 2026-11-02.

| PDF page | The book shows | On 2.0 | Use instead |
|---|---|---|---|
| 136 | `.melt(…)` in the lazy/eager method table | removed | `.unpivot(…)` |
| 138 | `.with_row_count(…)` in the method table | removed | `.with_row_index(…)` |
| 139 | `lf.collect(streaming=True)` | argument removed; streaming is now the default for `collect()` | `lf.collect()`, or `engine="in-memory"` to opt out |
| 139, 556-558 | `lf.profile()` | removed | see the upgrade guide; not needed for this module |
| 404 | `join_nulls` | renamed | `nulls_equal` |
| 424 | `pl.concat(..., how="horizontal")` padding unequal heights | raises `ShapeError` | `how="horizontal_extend"` to pad |

Two changes the book cannot warn you about, because they change behaviour rather than names:

- **Row order.** A lazy `join`, `group_by` or `unpivot` no longer promises row order. Sort at the end
  or ask for `maintain_order`. Anything the book shows coming out "in order" from a lazy query may not.
- **Stricter casts.** A string no longer casts to `Date` or `Datetime` (use `str.to_date` and
  `str.to_datetime`), and `Int64` with `UInt64` now widens to `Int128`, not `Float64`.

The full list is the [2.0 upgrade guide](https://docs.pola.rs/releases/upgrade/2/). The companion
notebooks are newer than the book (pinned to Polars 1.33.0) but still predate 2.0.
