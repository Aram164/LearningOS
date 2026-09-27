Durable notes — programming languages, compilers, software engineering.

=== note-compiler-pipeline-overview
domain: programming
title: The phases of a compiler
created: 2026-05-03
role: reference
state: evolving
authorship: user
concepts: [concept-compiler-structure]
sources: [source-crafting-interpreters]
---
Source text → **lexer** (tokens) → **parser** (syntax tree) → semantic
analysis (name resolution, type checking) → **intermediate representation** →
optimization passes over the IR → code generation (or, for an interpreter,
walk the tree / run bytecode).

Crafting Interpreters builds jlox as a tree-walking interpreter first, then
clox as a bytecode VM, and the bytecode VM is roughly 50× faster on the
Fibonacci benchmark.

Front end = language-specific; back end = machine-specific; the IR in the
middle is what lets LLVM have many front ends and many back ends.

=== note-constant-folding-cse
domain: programming
title: Constant folding and common subexpression elimination
created: 2026-05-17
role: synthesis
state: evolving
authorship: user
concepts: [concept-compiler-optimization]
sources: [source-dragon-book]
---
Optimization passes rewrite the IR into cheaper IR that computes the same
thing. Every rewrite must preserve meaning — that is the whole contract.

- **Constant folding**: 2 * 3 → 6; `if (false) {…}` → nothing.
- **Algebraic simplification**: x * 1 → x, x + 0 → x, x * 2 → x << 1 (for
  integers). Careful with floats: x * 0 → 0 is wrong for NaN and inf.
- **Common subexpression elimination**: `a = b + c; d = b + c` → compute
  b + c once, if neither b nor c changed in between.
- **Dead code elimination**: drop computations whose result is never used.

Passes enable each other — folding produces dead branches, removing them
exposes more folding — so compilers run them repeatedly until nothing changes
(a fixed point), with a limit on iterations.

=== note-ssa-form
domain: programming
title: Static single assignment
created: 2026-06-13
role: synthesis
state: rough
authorship: user
concepts: [concept-ssa, concept-compiler-optimization]
sources: [source-dragon-book]
---
Every variable is assigned exactly once; reassignments get new names (x₁, x₂).
Where control flow merges, a φ-node picks the version from whichever branch
was taken: x₃ = φ(x₁, x₂).

Why: every use has exactly one definition, so def-use chains are trivial and
optimizations like constant propagation and CSE become simple passes over a
graph of values.

The program becomes a dataflow graph: nodes are operations, edges carry
values.

=== note-dynamic-programming-memoization
domain: programming
title: Dynamic programming and memoization
created: 2026-04-26
role: synthesis
state: evolving
authorship: user
concepts: [concept-dynamic-programming]
sources: []
---
Two ingredients:

1. **Optimal substructure** — an optimal solution is built from optimal
   solutions to subproblems.
2. **Overlapping subproblems** — the same subproblems come up again and again.

Top-down: write the recursion and cache results (memoization). Bottom-up: fill
a table from the smallest subproblems upwards.

Fibonacci: naive recursion O(φⁿ), memoized O(n).

Edit distance between strings a and b: D[i][j] = min(D[i−1][j] + 1,
D[i][j−1] + 1, D[i−1][j−1] + [a_i ≠ b_j]). O(|a|·|b|) table; the answer is in
the corner; the path back through the table gives the alignment.

When greedy fails (coin change with coins 1, 3, 4 for amount 6: greedy 4+1+1,
optimal 3+3), DP still works.

=== note-forward-mode-autodiff-dual-numbers
domain: programming
title: Forward-mode autodiff with dual numbers
created: 2026-07-11
role: implementation
state: rough
authorship: user
concepts: [concept-automatic-differentiation]
sources: []
evidence:
  - {type: implementation, ref: "github://noor-haddad/scratch/dual.py"}
---
A dual number a + bε with ε² = 0. Evaluate f at x + 1ε and the ε-part of the
result is f'(x):

    (a + bε)(c + dε) = ac + (ad + bc)ε      — the product rule falls out
    sin(a + bε) = sin a + b cos a · ε

Implemented a Dual class with operator overloading; derivatives of arbitrary
Python functions without writing any derivative code.

Cost: one forward evaluation per input variable — to get the full gradient
of a function with n inputs you run it n times. Great for few inputs and many
outputs; the other direction (reverse mode) is what you want for one output
and many inputs.

=== note-type-inference-unification
domain: programming
title: Type inference by unification
created: 2026-06-20
role: synthesis
state: rough
authorship: user
concepts: [concept-type-inference]
sources: [source-dragon-book]
---
Hindley–Milner: give every expression a type variable, generate equality
constraints from the syntax (a function application f x means type(f) =
type(x) → result), and solve them by unification — repeatedly replace a type
variable with what it must equal, fail on a mismatch like Int = Bool or on an
infinite type (the occurs check: α = List α).

let-polymorphism: generalize the type of a let-bound name, so `id` can be used
at Int and at Bool in the same body.

Rust and OCaml infer local types like this; Rust requires signatures on
functions, so inference stays local.

=== note-garbage-collection-generational
domain: programming
title: Generational garbage collection
created: 2026-06-27
role: synthesis
state: rough
authorship: user
concepts: [concept-garbage-collection]
sources: []
---
Weak generational hypothesis: most objects die young. So split the heap: a
small young generation collected often and cheaply (copying: evacuate the few
survivors, everything else is freed at once), and an old generation collected
rarely.

Needs a write barrier: when an old object starts pointing to a young one,
record it (remembered set), otherwise a young collection would miss that
reference and free a live object.

Tracing (mark from roots) vs reference counting (free at zero; cycles leak
unless there is a cycle collector — CPython does both).

=== note-regression-testing-snapshots
domain: programming
title: Regression tests and snapshot files
created: 2026-07-09
role: synthesis
state: rough
authorship: user
concepts: [concept-regression-testing]
sources: []
---
A regression test pins behaviour that used to work so that a later change
cannot silently break it. Every fixed bug gets a test that fails before the fix
and passes after.

Snapshot (golden-file) tests: run the code, save the output to a file, compare
future runs byte-for-byte. Cheap to write for compilers and formatters. Danger:
people accept a changed snapshot without reading the diff, and then the test
protects nothing.

In Tessera I snapshot the printed optimized plan for twenty example queries.

=== note-property-based-testing
domain: programming
title: Property-based testing
created: 2026-07-16
role: synthesis
state: rough
authorship: user
concepts: [concept-property-based-testing]
sources: []
---
Instead of hand-written examples, state a property that must hold for every
input and let the library generate hundreds of random inputs.

    for all lists xs: sort(sort(xs)) == sort(xs)
    for all queries q: execute(optimize(q)) == execute(q)   ← the Tessera one

When a property fails, the library *shrinks* the input to a minimal failing
case — the difference between "fails on this 400-element list" and "fails on
[0, −1]".

Hypothesis (Python), proptest (Rust).

=== note-event-sourcing-append-only
domain: programming
title: Event sourcing
created: 2026-08-01
role: synthesis
state: evolving
authorship: user
concepts: [concept-event-sourcing]
sources: [source-kleppmann-ddia]
contexts: [workspace-ledgerline]
---
Store the sequence of events that happened ("item added to cart", "cart
checked out"), not the current state. The current state is a fold over the
events, recomputed or cached in materialized views.

Why: complete history for free; you can answer "how did we get here?" and
rebuild state as of any past moment; new views can be derived later from the
same log; bugs in a view are fixed by replaying.

Costs: the log grows forever (snapshots help), schema changes of old events
are painful, and deleting personal data from an immutable log needs extra
design (crypto-shredding).

Events are facts about the past — never edited, only followed by new events
that compensate.

=== note-idempotency-keys-api
domain: programming
title: Idempotency keys
created: 2026-08-02
role: synthesis
state: evolving
authorship: user
concepts: [concept-idempotency]
sources: []
contexts: [workspace-ledgerline]
---
A client that times out on "charge 20 €" does not know whether the charge
happened. Retrying blindly may charge twice.

Payment-API pattern: the client generates a unique key per logical operation
and sends it with every retry. The server stores key → result; a repeated key
returns the stored result instead of running the operation again.

Details: store the key in the same transaction as the effect; keys expire
after a while (24 h); a retry with the same key but a different request body
is an error, not a replay.

=== note-build-systems-dag-incremental
domain: programming
title: Build systems — DAGs and incrementality
created: 2026-08-06
role: synthesis
state: rough
authorship: user
concepts: [concept-build-systems]
sources: []
---
A build is a DAG: targets depend on sources and other targets. make compares
timestamps; Bazel and similar tools hash the inputs and the command, so a
target is rebuilt only if something it actually depends on changed.

"Build Systems à la Carte" separates the scheduler (in which order to visit
targets: topological, restarting, suspending) from the rebuilder (how to
decide a target is out of date: dirty bits, verifying traces, constructive
traces).

A dependency cycle is an error — make prints "Circular dependency dropped".

Early cutoff: if a rebuilt target turns out identical to before, stop — its
dependents need not rebuild.

=== note-rust-ownership-borrowing
domain: programming
title: Rust ownership and borrowing
created: 2026-07-29
role: synthesis
state: rough
authorship: user
concepts: [concept-rust-ownership]
sources: [source-rust-book]
contexts: [workspace-tessera-engine]
---
Every value has exactly one owner; when the owner goes out of scope the value
is dropped. Assignment moves ownership (for non-Copy types).

Borrowing: any number of shared references &T, or exactly one mutable
reference &mut T, never both at once. The borrow checker enforces this at
compile time, which rules out data races and use-after-free.

Where it hurt in Tessera: a rewrite rule wanted to mutate a plan node while
holding a reference to its child. Fix: rules take the node by value and return
a new node (Box<Plan>), instead of mutating in place.

=== note-tagless-visitor-pattern-ast
domain: programming
title: Rewriting plan trees with a visitor
created: 2026-08-04
role: implementation
state: evolving
authorship: user
concepts: [concept-visitor-pattern, concept-rust-ownership]
sources: [source-crafting-interpreters]
contexts: [workspace-tessera-engine]
---
Tessera's logical plan is an enum: Scan, Filter, Project, Join, Aggregate.
Each optimizer rule is a function Plan → Plan that matches on one node shape
and returns a replacement (or the node unchanged).

A generic `transform_up(plan, rule)` visits the children first, rebuilds the
node with the rewritten children, then applies the rule to the node itself.
The driver applies all rules repeatedly until a pass changes nothing, with a
cap of 50 passes.

Rules so far: merge adjacent Filters into one with AND; remove a Project that
keeps all columns; fold constant expressions like `1 = 1` to `true`, then drop
`Filter(true)`.

Crafting Interpreters' visitor chapter was the model, adapted to Rust enums
and match instead of classes.

=== note-error-handling-result-types
domain: programming
title: Errors as values
created: 2026-07-31
role: synthesis
state: rough
authorship: user
concepts: [concept-rust-ownership]
sources: [source-rust-book]
---
Rust has no exceptions for recoverable errors: functions return Result<T, E>
and the caller must handle both variants. The ? operator returns early with
the error, converting it via From.

Tessera's parser returns Result<Plan, ParseError> with a byte offset, so the
REPL can underline the bad token.

panic! only for bugs (broken invariants), not for bad input.

=== note-git-internals-content-addressing
domain: programming
title: Git's object model
created: 2026-06-29
role: synthesis
state: evolving
authorship: user
concepts: [concept-content-addressing]
sources: []
---
Git stores four kinds of objects, each named by the hash of its content:
blobs (file contents), trees (directory listings of names → object ids),
commits (a tree id, parent commit ids, author, message), annotated tags.

Consequences:
- identical content is stored once;
- a commit id pins the entire history below it — change anything in the past
  and every later id changes (a Merkle DAG);
- integrity checking is free: recompute the hash.

Branches are just files containing a commit id. A merge commit has two
parents. "Rewriting history" really means creating new objects and moving the
branch pointer; the old objects stay until garbage collection.

=== note-simulated-annealing
domain: programming
title: Simulated annealing
created: 2026-07-20
role: implementation
state: rough
authorship: user
concepts: [concept-simulated-annealing]
sources: []
evidence:
  - {type: implementation, ref: "github://noor-haddad/scratch/tsp_anneal.py"}
---
Local search that sometimes accepts a worse move, to escape local minima.

From a state with cost E, propose a neighbour with cost E'. If E' < E, move.
Otherwise move with probability exp(−(E' − E) / T). The temperature T starts
high (accept almost anything) and is lowered slowly (T ← 0.995 T); at low T it
behaves like plain hill-climbing.

TSP with 200 random cities: 2-opt hill-climbing got stuck at length 12.9;
annealing reached 11.7. Cooling too fast gave the same result as
hill-climbing.

The name comes from metallurgy: cooling metal slowly lets atoms settle into a
low-energy arrangement.
