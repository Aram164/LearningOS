# Stage 4A — thesis migration inventory and dry-run specification

## Understanding

The thesis will use the existing Module and milestone Units under the Bachelor's area, and the separate Projects product surface will be retired. Its research content and historical references must remain usable without changing learner state or inventing academic facts. This increment inventories and specifies the change; it does not apply a migration or remove any canonical Project record.

## Verified inventory

The [inventory](../../workbench/agility-experiment/stage4a-inventory.json) binds the input files at Core `873a77613dc237cd638b25d345f9f01ffcd44748` with SHA-256 checksums. Its [tool](../../workbench/agility-experiment/stage4a_inventory.py) refuses a dirty source checkout and writes its report outside that checkout; it has no apply mode.

| Input | Observed count |
|---|---:|
| Active Project registry records | 1 |
| Project top-level fields / mapped scalar values | 22 / 71 |
| Workstream/nested nodes | 7 |
| Research decisions | 2 |
| Relationships / mapped scalar values | 3 / 22 |
| Referenced files, each checked present inside Core | 3 |
| Existing milestone Units | 2 |
| Existing study maps | 1 |
| Matching references in the bounded authored/historical scan | 43 |

The second Unit remains `needs-map`; no scope or empty study map is invented to discharge that obligation. `curriculum/resume.yaml` is absent in this clean checkout; absence is explicitly pinned, and a present pointer must be preserved byte-for-byte when a later migration runs against another fixture or an approved installation.

The owning source records are `projects/registry/project-bachelor-thesis.yaml`, `curriculum/modules/module-project-bachelor-thesis/module.yaml`, their two Unit directories, and `work/active/workspace-thesis-mle-medical/CONTEXT.md`. Detailed field pointers, hashes, relationship fields, legacy IDs and reference locations belong to the inventory JSON; they are not copied into this specification.

Reproduce from a clean experimental Core checkout: `.venv/bin/python workbench/agility-experiment/stage4a_inventory.py --root . --output /tmp/learningos-thesis-stage4a.json`. Input record hashes and mapped field coverage should match; the input commit may advance with subsequent documentation-only increments.

## Decisions and reasons

1. **Keep the current Module kind `project`; move its area to `program-bachelors` and remove its compatibility-only status.** `kind: project` is an existing kind of ordinary Module, not a separate entity or navigation section. It truthfully describes the currently unregistered research work. Changing an active Module to `academic` would make the existing lifecycle derive enrollment and would require institution/semester values that these thesis records do not provide. Keep the current status, title, Unit order and IDs; do not infer registration, semester, credits, examination, grade or degree completion.
2. **Keep academic facts on the same Module identity whenever supplied.** The current record has none of the academic-fact fields. The Module schema accepts those fields and requires institution/semester only for academic kinds; Module/Program display paths read credits from that same record. Inspection of the owned Core and UI `credits`/`ECTS` consumers found projection and display code, not a degree-credit summation implementation. This migration adds no accounting engine: 4B must test exact preservation of supplied facts and unknowns; later official facts or a justified kind transition use the same Module owner and existing governed administrative/plan paths.
3. **Use the existing workspace as the active operational owner.** Preserve its existing body verbatim and append clearly named research-context, workstream, research-decision, materials/deliverables, milestone-identity and boundary sections. Carry the Project's meaningful field values and stable anchors there without collapsing parallel workstreams into a sequential study map. Keep priority/coordination decisions in `work/COORDINATION.md`; migration must not rewrite those decisions. This replaces the earlier idea of another `outputs/thesis-operational-context.md` file and reduces the number of active owners and files.
4. **Retain the existing Module's thematic groups; add only the explicitly linked Module IDs to `related_module_ids`.** These are existing fields. Preserve relationship reasons, contributions, Topic Pack links, files and root URI in the workspace's operational sections. Do not recreate the Project record as a large Module metadata extension.
5. **Reuse the existing flat compatibility alias mechanism as direct owner redirects.** Remove the current Module-to-Project alias and add old Project-to-Module resolution. Workstream, step, decision and relationship IDs resolve to the owning workspace, where their stable anchors and original values remain present; bare milestone IDs resolve to the existing milestone Units, as specified in the inventory. This retires the old Project-shaped response while keeping a usable canonical destination. Extend the existing schema/validator to the recognized legacy prefixes and Module/Workspace/Unit targets; never create alias chains, self aliases or aliases that shadow active identities. Derive projected `target_type` from the actual target, rather than the current hardcoded Project type.
6. **Preserve history as history.** Retain original bytes with the bounded migration's before-images/backups and field map. Keep historical receipts, idempotency entries and original artifact revision identities literal; alias resolution must never relabel a historical Project revision as a Module revision. The migration's new receipt guards the current Module, Project and workspace revisions separately.
7. **Make ordinary access an acceptance test.** The Module overview already renders its workspace card, but that card has no action to open the full workspace context. Add a read-only Open workspace context action using the existing authored-path opener, and test the Module → workspace → research-content path. Current structural search indexes IDs/titles/aliases rather than complete Project decision bodies; preserve the historical ID/title destinations and test normal file/record navigation instead of claiming existing full-text indexing. No generic workspace body projection or new search engine is needed for this consolidation.
8. **Retain read compatibility for historical formats while removing the active product path.** Old frozen Project fixtures remain evidence. The final interface has no Projects navigation, Project renderer or active Project authoring workflow; working-code repositories are outside this migration.
9. **Keep migration authority explicit and application-owned.** The current transaction service refuses unknown write authorities, and `commit_proposal` requires GatewayEnvelopeV2 for ordinary writes; a migration must not bypass either safeguard by disabling the catalogue. Use the documented one-shot migration exception with a narrowly declared, generation-bounded authority and an application-owned controller over the existing transaction service. The standalone tool remains a dry-run-first frontend, not a new permanent writer. The fixture suite must exercise the real declared scopes, including refusal of destinations outside the exact migration set.

## Files affected in later increments

- `tools/migrations/projects_to_modules_v62.py` (new): prepare, review and apply the bounded migration through the existing transaction service, dry-run by default and tied to the supported data generation.
- `tools/learning_os/app/project_migration.py` (new) and `system/contracts/capabilities.yaml`: keep transaction invocation in the application layer and declare only the one-shot migration's exact write scopes; retain ordinary gateway admission unchanged.
- `system/schema/project-aliases.schema.json`, `tools/learning_os/derive/validation/projects.py`, `tools/learning_os/derive/projection/projection/records_projects.py`: admit direct owner redirects and validate their actual target types; preserve old fixture compatibility.
- `tools/learning_os/app/handlers/platform.py`, `tools/learning_os/app/handlers/reads.py`: prove historical inspect/related calls resolve the new canonical owner rather than the retired Project.
- `curriculum/modules/module-project-bachelor-thesis/module.yaml`, the thesis workspace `CONTEXT.md`, and the three active `projects/` data files named in the inventory: apply only the reviewed ownership/alias changes and original-byte retirement.
- `tools/learning_os/derive/semesters.py`, `obsidian-ui/src/manifest-store.ts`: keep Core/UI ordinary-Module listing behavior aligned without altering academic lifecycle semantics.
- `obsidian-ui/src/components.ts`: add the missing workspace-context open action to the existing card through a narrow read/navigation port.
- The existing UI router/navigator, Project view registrations, search/navigation tests and Module/Unit surfaces named by the campaign plan: retire Project routes and test compatibility destinations.
- Data/manifest contracts and their fixtures/mirrors: bump the stored contract for the alias change. Inspection of `system/contracts/manifest-v15.schema.json` confirms that its compatibility-alias target ID and type are Project-only, so the new owner targets also require a deliberate paired manifest-contract bump. Do not edit the old version's schema or treat the separate unmerged #64/UI #9 version as compatible without reconciliation.

## Checkable execution and acceptance

1. Reproduce the inventory from the pinned clean source and verify all input hashes/absence pins before drafting a migration. Refuse an unmapped Project field or unexpected source identity.
2. In 4B fixtures, review the exact proposed write set and original-byte backups. Prove current schema cannot silently accept new alias targets before its deliberate update; no hand-edited aliases or unguarded writer.
3. Apply atomically in fixtures through the shared transaction service. Compare Unit files, the existing study map, note/attachment bytes, resume pointer or its absence, and existing workspace body against their source values. The only record changes are the specified ownership/context/retirement changes.
4. Test repeated apply as a no-op/idempotent result, stale snapshot/source/revision refusal, before-receipt failures, uncertain receipt publication and rollback/reconciliation behavior. Preserve the established recovery semantics rather than introducing another journal.
5. Test old Project/Module/sub-ID lookups, alias cycles/missing targets/shadowing, and literal historical receipt/revision verification. The ordinary Module ID must resolve to itself after migration.
6. In 4C, test Module visibility, old routes, title/ID search, workspace-context opening, every preserved operational field and file link, and exclusion of closed/compatibility-only/quarantine/boundary records. Only after that evidence may the experimental records be migrated and the separate Projects UI/writers be retired.
7. Run owning local tests and zero-error/no-new-warning checks, then the full hosted gate on exact resulting Core/UI commits. Production application and installation remain outside this experiment's authority.

## Risks and verification

The main risks are changing academic meaning to get visibility, losing operational access while retaining only backups, conflating research-node status with Unit study state, reversing an alias into a cycle, and rewriting historical evidence. The preceding tests attack those failures directly. Exact source hashes, pinned absent files, zero source writes and exhaustive field coverage are the 4A checks; executable migration, recovery and UI equivalence remain 4B/4C checks and are not claimed here.

## Out of scope

Canonical migration/removal during 4A, new pedagogical content or study maps, inferred academic facts, new domain entities or a query language, a replacement transaction system, paid-model experiments, external working-code directories, production merge and installation.
