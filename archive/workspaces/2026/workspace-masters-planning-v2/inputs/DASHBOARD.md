---
id: masters-dashboard
type: brain
status: live
---

# DASHBOARD (renders in Obsidian — Dataview queries)

> Open this note in Obsidian to get live tables over the whole system. In a plain editor you just see the query blocks — that's fine, nothing depends on them (`MASTERS-ARCHITECTURE.md` §9).

## All tier-3 units

```dataview
TABLE module, depth, concepts FROM "" WHERE type = "unit" SORT module, id
```

## Units not yet at full depth (build queue)

```dataview
LIST FROM "" WHERE type = "unit" AND depth != "full"
```

## Module cards awaiting promotion

```dataview
TABLE module, status FROM "Masters-Planning/module-cards" WHERE status = "stub"
```

## Concept lookup (edit the term)

```dataview
TABLE concepts, depth FROM "" WHERE contains(concepts, "mle")
```

## Quick links

Brains: `MASTERS-HANDOFF.md` · `MASTERS-STATUS.md` · `MASTERS-ARCHITECTURE.md` — Retrieval: `CONCEPT-INDEX.md` · `DEGREE-WIRING.md` — Semester: `SEMESTER-STATUS.md` (root)
