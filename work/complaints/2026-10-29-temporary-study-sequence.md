# Temporary Unit study sequence boundary

During agility Stage 6, inspection at Core `3dfef0a` showed that
`runtime.session` (`app/handlers/reads.py` and
`derive/projection/session_compiler.py`) owns intervention/evidence resources
for an explicit stage requirement. It provides no ordinary Unit-stage override;
reusing that shape would invent evidence semantics for stages without a target.
Stage 5's map import is deliberately durable, so it also cannot serve this task.

The bounded improvement is one snapshot-bound read and an in-memory Unit-view
choice. Preserve durable order, progress, resume and evidence ownership; enforce
only authored prerequisite links and expose unmapped scope. Expire the choice
on snapshot/day/view/Unit/end-session changes. The Stage 6 campaign plan/outcome
and disposable Core/UI tests retain the implementation and refusal evidence.
No real learner plan or production installation was exercised.

Tracking issue: https://github.com/Aram164/LearningOS/issues/73. This is an
experimental implementation record, not final campaign or production acceptance.
