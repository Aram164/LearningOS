# Stage Working Notes

## Mental Models

### Engineering ownership

You own the problem statement, architecture, code, tests, evidence, operations, and maintenance. Tool assistance never transfers responsibility.

### AI boundary

No agent authors the brief, baseline architecture, or first working slice. Afterward, AI is an untrusted reviewer whose suggestions need independent justification and tests.

### Completion model

A system is not complete because it runs once. It must be understandable, testable, installable, diagnosable, reviewable, changeable, and reproducible after delay.

## Read-only Anchor

Read-only comparison only after the capstone passes: one bounded path across stratum/optimizer/ir, stratum/optimizer/_op_utils.py, stratum/optimizer/physical/_registry.py, stratum/optimizer/physical/_impl_selection.py, stratum/runtime/_scheduler.py, and its tests. Stratum supplies observations, never code to copy or edit.

## Component

- stratum/optimizer/_op_utils.py
- stratum/optimizer/ir
- stratum/optimizer/physical/_impl_selection.py
- stratum/optimizer/physical/_registry.py
- stratum/runtime/_scheduler.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
