# Stage Working Notes

## Mental Models

### Tool model

a coding agent repeatedly samples a model, invokes authorized tools through a harness, observes results, and continues within a finite context; it is powerful but probabilistic and can make confident, state-changing mistakes.

### Working practice

give a bounded objective and acceptance tests, supply relevant context, constrain writable/read-only systems, inspect diffs and commands, interrupt divergence, and verify with independent checks.

### Job relevance

agents can accelerate navigation, tests, refactors, and review only if confidential repositories, external actions, and destructive commands have explicit boundaries.

### Safety rule

repository access may expose its contents to a provider; never assume privacy, permission, or correctness from the interface alone.

### Failure mode

vague prompts, authority creep, accepting plausible tests written by the same agent, or letting an agent act on production/external systems without review.

## Read-only Anchor

Stratum remains read-only and confidential. Before any agent-assisted Stratum task, state allowed paths, forbidden writes/external actions, data-handling assumptions, acceptance tests, and the human review point. Do not broaden access through this learning exercise.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
