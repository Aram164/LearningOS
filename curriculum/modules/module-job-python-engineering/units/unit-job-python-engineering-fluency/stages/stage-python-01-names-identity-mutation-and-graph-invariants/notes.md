# Stage Working Notes

## Mental Models

### Python model

names reference objects; assignment rebinds a name while methods and item assignment may mutate a shared object. Identity and equality answer different questions, and hashability couples equality to dictionary behavior.

### Stratum relevance

optimizer edges and Op dictionaries rely on object identity, while graph rewrites mutate shared input/output lists.

### Failure mode

treating names as C++-style boxes, using == where is is contractual, or rewiring one side of a shared edge only.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: stratum/optimizer/ir/_base.py::replace_input and _check_dup_in_inputs; stratum/optimizer/_numeric_rewrites.py::eliminate_two_op_chain; stratum/runtime/_buffer_pool.py. Use Job/python-drills/STRATUM-ANCHORS.md Stage 0 as the job-side reading guide.

## Component

- stratum/optimizer/_numeric_rewrites.py
- stratum/optimizer/ir/_base.py
- stratum/runtime/_buffer_pool.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
