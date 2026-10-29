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

The user-supplied code review was incorporated before Stage 7 profiling. Its
open-modal/End-session risk reproduced in a built fixture, then failed to
reactivate after the lifetime-generation repair. Pending preview/activation
checks across end/close/reset/switch-back pass. Numeric ranks were replaced by
one-action relative movement on 10/50-stage forms; progress labels now separate
the sitting from the full plan. Full UI checks pass. Date expiry still updates
an idle display on the next read/render, as explicitly documented.
