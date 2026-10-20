# F-01 scope rule — the 274 source-level cases (Aram's question)

**Question:** the scope rule reports 274 rows where the *source* was adopted
by the module but no route declares it. Are those incomplete authoring, or a
legitimate source-level workflow? Which granularity do the learning workflows
actually require?

**Answer: the rule asks the *route* question, and the system's own records
ask a different one. Both granularities are real, and they answer different
questions — so the 274 are not a false-positive class, but the message is
wrong for one of them.**

## The measurements

Script: `granularity.py` (run from a Core checkout). The buckets sum exactly
to the shipped 1,462 warnings.

| rows | what the row claims | what the records say |
|---|---|---|
| **1,101** | no `source_id` at all | nothing to resolve against a map: 490 name a file, 546 name prose (many of them the unit's *own* note ids), 65 name nothing |
| **135** | a source the module declared, which has **no rich route** | the unit **did** record the adoption — 133 `source_selections`, 2 `scope_sources` (all `module-hu-amls`) |
| **139** | a source the module declared, which has **no rich route** | **no unit record at all** — the four `module-job-*` modules and `module-skill-python`, whose maps declare sources with no routes whatsoever |
| **69** | a source that **has** a rich route, at a locator matching none | the descriptive-locator style difference |
| **18** | a source **no module declared** | the defect — all in `module-skill-python`, in `unit-python-intermediate-roadmap` and `unit-python-oop-scope`; none of the units selects them |

(The earlier "274" figure was the *no rich route* population: 135 + 139.)

## What the learning workflows require

Two records, two questions:

- **OPERATOR.md boundary 14** and **WORKFLOWS §6a** (the source-completeness
  gate): a source is adopted by an **explicit disposition** — *selected for a
  unit/stage*, *reference-only*, or *deferred with a reason*. That
  disposition is the unit's `source_selections` / `scope_sources`. It answers
  **"did this unit adopt this source?"**
- **PLAN-CREATION-SOP.md**: "Each rich `unit_routes` entry is one
  source-to-lecture edge"; "Legacy string routes remain readable for
  backward compatibility, but **a newly mapped lecture must use rich routes**
  so the interface can explain the choice." A route answers **"where in this
  source does *this lecture's* material live?"**

So the rule asks the route question — the right one for a *stage resource*,
which names a place in a source — and the unit's disposition answers a
different question. The two are complementary, not competing.

## What that means for the 274

- **135 rows** — the unit *did* adopt the source; the module's map never
  declared the route to the place the stage teaches. Incomplete
  *route-level* authoring, which the SOP's own rule names for newly mapped
  lectures. These modules are legacy (`module-hu-amls` has 66 legacy string
  routes and no rich ones).
- **139 rows** — the source is in the module's menu, and the unit never
  disposed of it. Incomplete at the *disposition* level (boundary 14). **The
  rule's message is wrong here**: it says "adopt the material in the module's
  map", but the module already did. It should say the unit never recorded a
  disposition.

## Recommendation (for Aram, not for the fixer)

Keep the rule and its severity as they are — a warning, adopted in the
baseline. Two changes are worth considering separately, and neither is a
weakening:

1. **Say what is missing.** The message should distinguish "the module's map
   declares no route to this place" from "this unit never disposed of this
   source" from "this row names no source". One message for three findings
   is the precision problem, not the rule.
2. **The 1,101 source-less rows are a different question.** A row that names
   no source claims no material, so the module's scope is not implicated;
   what it usually *does* show is a missing `source_id` on a row that names
   a file or a lecture. That is an authoring defect of its own, and it is
   75 % of the warning set.

The granularity-aware variant measured earlier (1,188 instead of 1,462 — a
source the module adopted at source level only, judged at source level) would
silence the 274. It should **not** be taken on its own: it would silence
the 139 (a real missing disposition) along with the 135 (a real missing
route). Fix the message first, then measure again.
