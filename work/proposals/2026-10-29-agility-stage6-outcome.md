# Stage 6 — temporary study sequence

Stage 6 implements a read-only `study-sequence` preview and Obsidian's
**Sequence for this sitting** control. The learner chooses an ordered subset
of existing stages, reviews Core's exact order and omissions, and explicitly
uses it for the current Unit view. Use rechecks the reviewed snapshot; it
creates no transaction, receipt, stage, progress or persisted Session.

The choice lives only in view memory. Closing or changing the Unit view,
requesting End session, a stale/changed snapshot, a Berlin date change or an
explicit reset expires it. Date validity is checked on read/use. Temporary
navigation is excluded from saved selection settings and route state. Normal
progress and note writes retain their existing gateways and expire the choice
when their canonical snapshot changes. The durable map, resource placements,
notes, attachments, feedback and global resume pointer are unchanged.

Core enforces transitive authored `builds_on` links through stage node mappings.
Mapped prerequisite stages must precede their dependent unless already recorded
complete. This exception records prior study activity and grants no mastery.
Cycles in selected prerequisite ancestry and open required-now detours refuse.
Unmapped prerequisite scope is visibly unchecked; no missing dependency is
invented and no readiness claim is made. The evidence-focused `runtime.session`
compiler keeps its separate existing scope. Data v62 and manifest v16 remain
unchanged; the new request/result schemas are artifacts.

Owning evidence: the runtime/CLI/catalogue/fixture run passed 177 cases before
three final focused runtime cases were added; the final temporary-sequence
selection passed all 14 cases. The catalogue/CLI/JSON/surface/ID run passed 76,
architecture boundary checks passed 82, and the affected query/discovery/backup
characterizations and refusal witnesses passed 66 after eight owning recordings
were regenerated. The new Unit lookup's suggestion oracle passed. Full UI check
passed, with an additional built-dashboard recheck for closing during the final
read. Tests prove no canonical write or receipt, exact review and omissions,
no saved-setting change, stale/day/Unit/map expiry, reset, End session, view
closure and late-response invalidation. These runs overlap; totals are not added.

Ruff, maintained mypy, import boundaries, system-map, reachability and whitespace
checks passed. Validation has zero errors and no new/grown warning signature:
964 baseline-managed warnings across the same 32 signatures. Local-only and
operational advisories remain visible. Full combined hosted/artifact acceptance
belongs to Stage 8; intermediate commits retain the explicit unverified status
and skip automatic whole-suite push workflows. No verified-pair stamp is made.
Stage 5's earlier branch run 40862888841 is green; it is not Stage 6 acceptance.

Issue #73 records the observed capability boundary. No actual learner Unit,
today's durable plan, live Obsidian installation, production migration, merge,
paid trial or subagent was used. Aram's latest instruction is to push Stage 6
and immediately begin Stage 7; that supersedes the earlier stop-after-6 step.

## Review corrections

The supplied Stage 6 review identified an open-modal lifetime gap, numeric-rank
friction and ambiguous progress scope. The built disposable fixture reproduced
reactivation from an already checked modal after End session. The repair binds
modal checks and activation to the Unit view's sequence lifetime generation;
reset/end/close/Unit change and a new accepted choice invalidate older reviews.
Eight pending-preview/activation combinations across end, close, reset and
switch-away/back now refuse. Existing changed-input/modal-close checks remain.

The form now keeps an ordered stable-ID array and inclusion set, with Move
before controls. Tests demonstrate one move action putting the last stage first
on both 10- and 50-stage inputs, preserving all other relative order and sending
only the final array to the existing Core read. The rail separately labels
sitting completion and full-plan completion. The full UI check passes after
these corrections. Core contracts and prerequisite authority are unchanged.

Idle-screen date expiry remains a documented limitation: validity is checked
on read/render/use rather than through a midnight redraw scheduler. These fixes
still do not claim live installation or final Stage 8 hosted acceptance.
