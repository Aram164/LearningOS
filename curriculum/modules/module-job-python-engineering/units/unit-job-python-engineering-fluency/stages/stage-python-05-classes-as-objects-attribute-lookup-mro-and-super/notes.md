# Stage Working Notes

## Mental Models

### Python model

class bodies execute to create class objects; method binding supplies self or cls; attribute lookup walks instance, class, and MRO; super means the next implementation in the actual instance's MRO.

### Stratum relevance

IR subclasses, physical implementation classes, slots, and runtime class rebinding all depend on this machinery.

### Failure mode

treating self as magic, confusing class and instance state, assuming super means a fixed parent, or using cooperative super with a non-cooperative library class.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: MissingMaskExpr in stratum/optimizer/ir/_column_expr.py; OperandRef and IRNode in stratum/optimizer/ir/_base.py; implementation-class rebinding and on_impl_selected in stratum/optimizer/physical/_impl_selection.py.

## Component

- stratum/optimizer/ir/_base.py
- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/physical/_impl_selection.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
