# The refusal-site rule cannot see a site raised through the shared plan helper

Task: add the governed program-semester update capability
(`program.semester.update`) and satisfy the refusal-site rule for every
site it raises.

Observed: the rule reads the refusal sites a capability declares
statically, and it resolves a site only when the slug is a literal in
the template. A site raised through the shared plan helper
(`_plan_refuse`, whose slug is an argument) is invisible to it: the
helper's own raise is skipped, so the eight `module.create` sites it
produces are neither required to carry a scenario nor checked against
one. Writing the new handler with the same helper shape makes the rule
fail outright with `unresolvable site form`, so every site had to be
inlined instead. The collector's declared set for `module.create` is
`['module.create.bad-expected-revision', 'module.create.bad-file']` —
the two sites raised with a literal inside the handler.

Impact: the rule that every declared refusal site is witnessed from its
case does not reach the sites raised through the shared helper, so a new
refusal there needs no scenario and no test failure. The behaviour is
right today — the scenario cases for those eight sites exist and pass —
so this is missing enforcement, not a wrong refusal.

The safety benefit the rule does provide stands: the sites it can see
are proven by a scenario run, with the witness line, the class and the
exit.

Smallest improvement to investigate: let the collector resolve a
helper's literal slug arguments, for both helper shapes, and declare
the sites they produce. Retain the fail-closed refusal path and the
existing scenarios as the witnesses.

Filed on 2026-10-22: [LearningOS #6](https://github.com/Aram164/LearningOS/issues/6),
with the collector output, the reproduction, the scope limit and the
acceptance criteria.

## Implementation follow-up, 2026-10-22

The resumed work follows local helper calls from each registered handler, binding positional/keyword/default slug and failure-class arguments. The collector now declares 497 sites, including all ten module.create sites. Thirty-nine existing scenarios now assert their actual site witnesses; forty-one internal assembly and fault-only branches have pipeline proofs asserting the exact site, typed refusal and unchanged canonical bytes. Both helper shapes and an uncalled-helper negative control pass. Final paired verification is pending.
