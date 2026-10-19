# Independent plan critique and amendments

17 October 2026. This records review of a proposed design, not verification of an implementation.

Three independent, read-only reviews covered operation boundaries/enforcement, storage/recovery, and feature/UI behavior. Each read the draft against the current production code. The resulting [plan](/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/PLAN.md) incorporates the following required amendments:

- Preserve refusal ordering when removing direct stdin reads through deferred materialization. Keep revision notation unchanged in the parser-removal slice instead of silently migrating fourteen consumers.
- Require a quiescent capture source; a hash of sequentially copied data does not establish source consistency.
- Bind finite policies to capabilities and extend callback enforcement to the new representations, with negative controls proving callbacks cannot hide in a new carrier.
- Specify concrete source/dossier, import-preparation and entity-family reference-check separations rather than defer repository-answerable design choices.
- Persist the original pending record and exact resolution envelope before dispatch; reject resolution/original identity aliasing.
- Keep recovery/repair available when ordinary writes are gated. Stage manifest replacement and retain the previous validated view after failed refresh.
- Invalidate freshness during focused use and at midnight, while excluding diagnostic/output churn from watcher inputs.
- Couple accepted-state resolution to engine-owned journal settlement, not merely an idempotency tombstone. Protect active originals before effects through journal storage v3, since older automatic recovery runs before ledger admission.
- Bind ledger storage transitions to receipt evidence with concrete inverse effects; preserve historical proof across the version boundary.
- Use durable settlement certificates and synchronize both rename parents; do not infer settled state from a directory name or current bytes after later valid writes.
- Distinguish recovery authority from ordinary reentrant exclusive authority, including a nested-dispatch refusal witness.

Focused rechecks found no remaining fatal ordering, authority or UI contradiction after these amendments. One boundary remains explicit: before all original journal wrappers are durable, old guarded recovery may still run and invalidate the proposed resolution; after the barrier, older code must refuse without changing canonical bytes. The plan's external-editor limit also remains explicit: uncached preimage checks do not provide atomic exclusion from arbitrary noncooperating writes in the final check/replace interval.

All named existing tests, commands and principal file targets were checked. New files/interfaces are proposals. Performance budgets are acceptance decisions to measure during implementation, not claims of observed performance. No production code, canonical data or installation was changed, and no test pass is claimed for the proposed design.
