# Stage Working Notes

## Mental Models

### API model

A public API is a long-lived promise about names, data, mutation, errors, and resource ownership.

### Refactoring model

Refactoring changes structure while tests hold behavior steady; separate it from semantic changes so review stays legible.

### Abstraction model

An abstraction earns its place by stabilizing a real variation or policy, not by making the design look sophisticated.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: compare the public surface in stratum/__init__.py, stratum/optimizer/physical/_registry.py, and one operation family with internal helpers and tests. Do not edit or execute Stratum.

## Component

- stratum/__init__.py
- stratum/optimizer/physical/_registry.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
