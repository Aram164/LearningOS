# Stage Working Notes

## Mental Models

### Python model

an import executes a module once, caches it in sys.modules, then binds names; from-import copies a binding, not a live alias, and partially initialized modules expose circular-import hazards.

### Stratum relevance

physical implementations exist only after their modules import, while local imports break selected IR cycles.

### Failure mode

moving an import changes registration order, patching the definition rather than the consumer binding, or resolving a cycle without understanding why it formed.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: stratum/optimizer/physical/_registry.py::build_default_physical_registry; local imports in stratum/optimizer/ir/_column_expr.py; re-exports in stratum/__init__.py and stratum/optimizer/__init__.py.

## Component

- stratum/__init__.py
- stratum/optimizer/__init__.py
- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/physical/_registry.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
