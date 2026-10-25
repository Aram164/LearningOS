# Claude's verdict on C1-A (2026-10-24)

## Decisions

Aram said "you decide".

- **Finding 2 is filed as Aram164/LearningOS#27.** The issue also proposes
  letting `failed` carry exactly 5.0. The reason: CLAUDE.md §3 records a
  module event exactly as an official document states it, and HU grades a
  failed sitting 5,0.
- **Finding 1 is not filed.** It cannot happen in the live tree, and the
  handler's docstring states the filesystem check as intended design. Reword
  the `capabilities.yaml:399` invariant the next time that file is touched.

Both reproduction tests were re-run on Core `main` `d6c47790`, in Claude's
scratch clone, and both fail as described.

## 1. `module.create` accepts a legacy-registry identity

**CONFIRMED as a mismatch between the contract and the code. Low severity.**

- `system/contracts/capabilities.yaml:399` says that "an existing canonical
  identity or file is refused".
- `_creation_destination_problems`
  (`tools/learning_os/app/handlers/plan.py:940-957`) checks only the
  filesystem.

**Against treating it as urgent:**
- The handler's own docstring says, by design, that only the filesystem
  decides identity.
- CLAUDE.md hard rule 2 calls `records/modules.yaml` a frozen compatibility
  snapshot, not an owner of facts.
- Every legacy id in the live tree is already partitioned, so this is
  unreachable in Aram's tree today.

**Fix:** refuse an id that is present in `repo.legacy_modules` but has no
partition, or reword the invariant to say "file". Cheap either way. Not
urgent.

## 2. A graded attempt's result can never be corrected

**CONFIRMED. A real dead end with no path through the gateway. Moderate
severity.**

- In `system/schema/requests/module.attempt.record.schema.json`, `grade` is
  `type: number`, so it cannot be null.
- The handler keeps an existing `grade` when an update omits it
  (`admin.py`, `if grade is not None`).
- MOD-GRADE refuses a grade on any result that is not `passed`.

So once a termin carries a grade, its result can only ever stay `passed`.

GLM's citation is wrong: boundary 16 covers plans. The rule that forbids the
hand edit is CLAUDE.md hard rule 12, which says canonical writes go only
through gateway capabilities. The conclusion stands.

**Fix:** allow an explicit clear of the grade (`grade: null` in the schema and
the handler), or drop the grade when the result moves away from `passed`.

**Product question for Aram:** under the same rule, a failed sitting cannot
carry its 5.0. Is that intended?

## The report's other claims

- **"The live local `main` is divergent": WRONG.** `1d80aa03` is an ancestor
  of `d6c47790`. The live repo had simply not fetched since. It was harmless,
  because GLM based its branch on GitHub's `main`.
- **The clone was made from the live checkout,** so it holds the personal
  branch `takeover/complete-and-install-2026-10-23`. Nothing was pushed. The
  ground rules now require clones from GitHub.
