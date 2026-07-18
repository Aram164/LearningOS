# Review — recommended improvements (2026-07-17)

**Status:** open backlog · **Source:** a 30-point code/design review Aram
supplied on 2026-07-17 (originally `recommended Imorovments .txt` at the repo
root; shelved here 2026-07-18). Companion to `external-review-2026-07-16.md` and
`ADR-001-external-review-2026-07-17.md`. The original list is preserved verbatim
below; nothing is edited.

## Status read (operator, 2026-07-18 — verify against code before relying on it)

Several **High-Priority** items already appear implemented in the current
loader/validator/generator:

- **#1 empty/missing IDs** — `loader._record_id` rejects empty/non-string ids;
  each family records a `parse_failure` and skips the record.
- **#2 stable timestamps** — `genout.stable_generated_at` uses the last-commit
  time; regeneration is byte-for-byte reproducible.
- **#3 delete stale generated files** — `genout.write_outputs` / `_remove_stale`.
- **#4 attachment ownership by resolved path** — `rules.py` resolves paths and
  checks `parents` (the `ATTACH-PATH` rule), not string prefixes.
- **#6 defensive registry/collection loading** — `loader._load_registry` skips
  non-mapping documents/items instead of assuming shape.
- **#7 alias/label `strip().casefold()`** — normalized before collision checks.
- **#15 (partial)** — the contract is now canonical in `system/CLAUDE.md` with
  root/`LearningOS/` copies as symlinks.

**Not yet addressed / unverified:** #5 (regression tests for the above — 55
tests pass but specific coverage is unconfirmed), most of Medium (#8–#17) and
the Data-Model (#18–#22) and Low-Priority (#23–#30) items. Notably, the new
Garden layer (ADR-002) added no tests of its own yet — that folds into #5/#14.

This read is the operator's, not an audit; confirm each against the code before
closing it.

---

## Original list (verbatim)

```
Recommended Improvements

========================

High Priority

-------------

1. Reject records with missing or empty IDs during loading.

2. Remove or stabilize generated timestamps for reproducible output.

3. Delete stale generated files so generated/ exactly reflects canonical data.

4. Validate attachment ownership using resolved filesystem paths rather than string prefixes.

5. Add regression tests for all four behaviors above.

6. Defensively reject malformed registry and collection documents instead of assuming mappings.

Medium Priority

---------------

7. Normalize aliases and labels with strip().casefold() before collision checks.

8. Normalize attempt dates to one type before chronological comparison.

9. Preserve and report the originating partition file in validation diagnostics.

10. Prevent Mermaid node-ID collisions after identifier sanitization.

11. Test byte-for-byte generation with a fixed timestamp.

12. Test repeated generation for filesystem stability.

13. Test deletion or renaming of generated collections and outputs.

14. Test attachment containment, empty IDs, malformed YAML, duplicate IDs, and alias collisions.

15. Replace duplicated CLAUDE.md contracts with one canonical or generated source.

16. Consolidate duplicated Markdown heading/section parsing.

17. Document the direction and semantics of concept relations explicitly.

Data-Model Improvements

-----------------------

18. Separate Module identity from Enrollment or semester participation if repeated enrollment becomes relevant.

19. Convert important facts currently stored in free-text notes into structured fields, such as:

    - pending grades

    - submission dates

    - examination duration

    - registration windows

20. Consider stable IDs for module components if they need to be referenced independently.

21. Make semester strategy more explicit in COORDINATION:

    - current focus

    - deliberately dormant workspaces

    - sequencing decisions

22. Represent coordination dependencies as structured edges if future automation needs to query them.

Low Priority

------------

23. Rename misleading constants such as IMAGE_OK.

24. Make archived-workspace discovery less dependent on a fixed directory depth.

25. Centralize workspace and coordination heading parsing.

26. Add exact boundary tests for workspace-count warnings.

27. Test that reset generation reproduces identical content, not merely the same filenames.

28. Test generated-file governance, including unexpected files and required generated headers.

29. Add tests for orphan attachment directories, binaries under knowledge/, stale inbox items, and Git-based neglect detection.

30. Improve the README with a shorter quick start and an early definition of "operator."
```
