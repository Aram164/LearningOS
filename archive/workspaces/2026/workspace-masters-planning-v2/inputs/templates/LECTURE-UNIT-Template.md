---
id: lecture-unit-template
type: template
status: live
---

# LECTURE-UNIT — Template (tier 3, the degree-wide standard)

> Formalizes the format proven in SoSe 26 (AML L02–L07, SaD L01–L05). One folder per lecture: `<module material>/notes/lectNN <topic>/` (or module convention). Executable version: `skills-src/lecture-unit-builder/`.

## Folder contents (4 files + optional extras)

| File | Job | Rules |
|---|---|---|
| `<MOD>_LNN_Ultimate_Reference.md` | **The anchor.** Complete worked treatment of the lecture: every concept, derivation, worked example, pitfalls | Carries the unit's frontmatter (§3.2 anchor-file rule). Scope = the lecture as taught, NOT the textbook chapter (scope-to-lecture lesson) |
| `<MOD>_LNN_Mini_Plan.md` | The only study script for this lecture (single-study-script rule) | Cites *specific* videos/book sections selected from tier 1–2 crosswalks; never re-lists whole series. For re-covered concepts: "revise via `<old unit>`" pointer instead of new steps |
| `<MOD>_LNN_Exercise_Bank.md` | Solved + unsolved practice, source-tagged | Feeds Anki card generation later — keep Q/A pairs cleanly separated |
| `<MOD>_LNN_Mock_Exam.md` | Exam-conditions self-test with solutions | Difficulty ≥ real exam |
| *(optional)* bonus-sheet / Übung solutions | course-specific artifacts | |

## Anchor frontmatter (fill all keys)

```yaml
---
id: <MODULE-ID>-LNN          # e.g. AML-SoSe26-L05
type: unit
module: <MODULE-ID>
concepts: [slug-1, slug-2]   # match/extend CONCEPT-INDEX slugs
depth: full                  # partial if unit is incomplete
status: live
---
```

## On completion (do immediately, 2 min)

1. Add/upgrade the concept rows in `Masters-Planning/CONCEPT-INDEX.md` (depth 🟢).
2. Set the module plan's block table pointer to this unit.
3. If a concept re-covers an older unit's ground → add the cross-link in both Mini Plans.
