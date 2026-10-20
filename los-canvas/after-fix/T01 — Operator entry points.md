# T01 — Operator entry points

**19/19 passed.**

## PASS — entry-01-discover-capabilities

*Intent:* An agent starts a session and learns what the system can do.

**exit_code**

```
0
```

**queries**

```
19
```

**commands**

```
47
```

**bytes**

```
2101
```

**tokens**

```
525
```

**rules_declared**

```
{
 "canonical_writes_are_transactional": true,
 "successful_writes_have_receipts": true,
 "artifact_revision_conflicts_fail_closed": true,
 "shelving_requires_explicit_approval": true,
 "ordinary_interfaces_read_projection_only": true,
 "module_plan_preflight_required": true,
 "ai_actions_are_provider_independent": true,
 "bounded_ai_actions_use_exact_context": true
}
```

**one_capability_exit**

```
0
```

**one_capability_bytes**

```
3178
```

**one_capability_tokens**

```
794
```

## PASS — entry-02-plan-edit-context-brief

*Intent:* Unit coverage, source completeness, or unknown ids → brief context.

**exit_code**

```
0
```

**bytes**

```
4618
```

**tokens**

```
1154
```

**keys**

```
[
 "analysis_refs",
 "artifact_revisions",
 "claims",
 "contract",
 "expand",
 "inventory",
 "module_id",
 "preflight",
 "required_inputs",
 "schema_version",
 "snapshot_id",
 "unit_audit",
 "unit_id"
]
```

**route_id_discovered**

```
route-b2f1f80014860a929a3af0bc
```

## PASS — entry-03-plan-edit-context-route

*Intent:* Edit a known material route → route-scoped edit context.

**exit_code**

```
0
```

**bytes**

```
1441
```

**tokens**

```
360
```

**keys**

```
[
 "artifact_revisions",
 "claim",
 "contract",
 "module_id",
 "patch_capability",
 "patch_fields",
 "preflight",
 "route",
 "schema_version",
 "snapshot_id",
 "unit_id",
 "uses"
]
```

## PASS — entry-04-plan-edit-context-stage

*Intent:* Edit a known stage → stage-scoped edit context.

**exit_code**

```
0
```

**bytes**

```
1643
```

**tokens**

```
410
```

**keys**

```
[
 "artifact_revisions",
 "contract",
 "module_id",
 "preflight",
 "requested_stage_id",
 "schema_version",
 "scope",
 "snapshot_id",
 "stage",
 "stage_results",
 "unit_id"
]
```

## PASS — entry-05-bootstrap-brief

*Intent:* Open work or a priority question → one-page session entry.

**exit_code**

```
0
```

**bytes**

```
3728
```

**tokens**

```
932
```

**keys**

```
[
 "academic_deadlines",
 "active_study_maps",
 "contract",
 "counts",
 "deadline_count",
 "domain_atlas",
 "expand",
 "owed_study_maps",
 "pointer_state",
 "pointer_state_note",
 "recorded_options",
 "recorded_options_note",
 "resume_pointer",
 "schema_version",
 "session_identity",
 "snapshot_id"
]
```

**session_identity**

```
{
 "session_id": "canvas-t01",
 "source": "environment",
 "how_to_set": "name it before the first write \u2014 export LOS_SESSION_ID=<id> when the shell persists, or seal session_id in each write envelope (.venv/bin/python tools/seal_envelope.py --session-id <id>); without either, writes share this channel's ledger"
}
```

**snapshot_id**

```
sha256:7f74dca429b92ba440e67a970ae1df06c6461c135f371d1473bee1f5e631fb36
```

## PASS — entry-05b-bootstrap-unbounded

*Intent:* TRAP: the same entry without --brief (measured, not asserted).

**exit_code**

```
0
```

**bytes**

```
43558
```

**tokens**

```
10889
```

**note**

```
the contract calls this 'a bulk read, never a session start'
```

## PASS — entry-06-inspect-workspace

*Intent:* Open work → inspect the workspace record.

**exit_code**

```
0
```

**bytes**

```
436
```

**tokens**

```
109
```

**keys**

```
[
 "archived",
 "concepts",
 "deadline",
 "id",
 "module_ids",
 "next_action",
 "notes",
 "objective",
 "path",
 "program_ids",
 "project_id",
 "revision",
 "sources",
 "standing",
 "status",
 "title",
 "type",
 "unit_ids"
]
```

## PASS — entry-07-note-read

*Intent:* Read the body of a saved reasoning note.

**exit_code**

```
0
```

**bytes**

```
1212
```

**tokens**

```
303
```

**total_characters**

```
750
```

**path**

```
knowledge/notes/mathematics/note-demo-analysis.md
```

**content_sha256**

```
sha256:ecd673fe86ebb2952d5efaf15ee8c4dc49f2f10c3710b795f3b8b0cafd23330c
```

## PASS — entry-07b-note-read-paged

*Intent:* Read a bounded segment of a note (context discipline).

**exit_code**

```
0
```

**bytes**

```
849
```

**tokens**

```
212
```

**content_len**

```
400
```

**next_offset**

```
400
```

**total_characters**

```
750
```

## PASS — entry-08-material-context

*Intent:* Find a saved explanation by need.

**exit_code**

```
0
```

**bytes**

```
1435
```

**tokens**

```
358
```

**keys**

```
[
 "contract",
 "items",
 "next_offset",
 "observations_sha256",
 "pool",
 "ranked_by",
 "schema_version",
 "searched",
 "snapshot_id",
 "total"
]
```

## PASS — entry-09-material-span

*Intent:* Describe one exact route.

**exit_code**

```
0
```

**bytes**

```
1575
```

**tokens**

```
393
```

**keys**

```
[
 "analysis_refs",
 "availability",
 "contract",
 "expansion",
 "locator",
 "module_id",
 "next_action",
 "route_id",
 "schema_version",
 "snapshot_id",
 "source_id",
 "spans",
 "unit_id",
 "url"
]
```

## PASS — entry-10-resume

*Intent:* Resume recorded study without moving state.

**exit_code**

```
0
```

**bytes**

```
1176
```

**tokens**

```
294
```

**keys**

```
[]
```

## PASS — entry-11-resume-study

*Intent:* The study suggestion must not move the resume pointer.

**exit_code**

```
2
```

**bytes**

```
0
```

**tokens**

```
1
```

**stderr**

```
los: INVALID_REQUEST: no upcoming exam is recorded for an enrolled module; `status` shows the recorded exam spine
```

**keys**

```
[]
```

**note**

```
the fixture's only exam date (2026-10-09) is in the past relative to the wall clock, so the study suggestion has no upcoming exam to project
```

## PASS — entry-12-intelligence-scan

*Intent:* Read the decision queue (changes awaiting a decision).

**exit_code**

```
0
```

**bytes**

```
1972
```

**tokens**

```
493
```

**keys**

```
[
 "contract",
 "detectors",
 "full_result",
 "groups",
 "omitted_goals",
 "omitted_groups",
 "total_goals",
 "total_groups"
]
```

## PASS — entry-13-ability-context-horizon

*Intent:* Read the small ability horizon.

**exit_code**

```
0
```

**bytes**

```
1214
```

**tokens**

```
303
```

**keys**

```
[
 "abilities",
 "bridges",
 "candidate_connection_count",
 "candidate_connections",
 "contract",
 "expand",
 "expansions",
 "has_more",
 "next_offset",
 "offset",
 "returned",
 "schema_version",
 "snapshot_id",
 "total",
 "truncated"
]
```

## PASS — entry-14-ability-context-one

*Intent:* Expand one known ability.

**exit_code**

```
0
```

**bytes**

```
1612
```

**tokens**

```
403
```

**keys**

```
[
 "ability",
 "bridges",
 "candidate_connections",
 "contract",
 "encounters",
 "expand",
 "focus",
 "related_encounters",
 "related_encounters_total",
 "schema_version",
 "shared_concept_candidates",
 "snapshot_id"
]
```

## PASS — entry-15-semantic-list

*Intent:* Governance question → the semantic registry.

**exit_code**

```
0
```

**bytes**

```
5349
```

**tokens**

```
1337
```

**predicate_count**

```
26
```

**first_predicates**

```
[
 "AllowedMutation",
 "AttemptConsistent",
 "CanonicalWritePath",
 "ClaimStale",
 "CritiquePointActionable",
 "CurrentScopeAuthority",
 "DossierFresh",
 "EvidenceComplete"
]
```

**distinct_authorities**

```
[
 "ADR-015; OPERATOR.md rule 2",
 "ARCHITECTURE.md \u00a75.5; OPERATOR.md boundaries 4-5",
 "OPERATOR.md 'clean'",
 "OPERATOR.md boundaries 4-5",
 "OPERATOR.md rule 10",
 "OPERATOR.md rule 10, boundary 17",
 "OPERATOR.md rule 12",
 "OPERATOR.md rule 14",
 "OPERATOR.md rule 15",
 "OPERATOR.md rule 16",
 "OPERATOR.md rule 2",
 "OPERATOR.md rule 3"
]
```

## PASS — entry-16-semantic-predicate

*Intent:* Ask one governance question through the semantic surface.

**predicate**

```
AllowedMutation
```

**exit_code**

```
2
```

**bytes**

```
0
```

**tokens**

```
1
```

**stdout_head**

```

```

**stderr_head**

```
los: INVALID_REQUEST: malformed inputs for AllowedMutation: allowed_mutation() missing 3 required keyword-only arguments: 'capability', 'target_path', and 'scopes'

```

## PASS — entry-17-supporting-reads

*Intent:* The other operator reads: lists, search, related, dossier.

**status**

```
{
 "exit_code": 0,
 "bytes": 543,
 "tokens": 135
}
```

**module-list**

```
{
 "exit_code": 0,
 "bytes": 944,
 "tokens": 236
}
```

**unit-list**

```
{
 "exit_code": 0,
 "bytes": 2126,
 "tokens": 531
}
```

**project-list**

```
{
 "exit_code": 0,
 "bytes": 518,
 "tokens": 129
}
```

**program-list**

```
{
 "exit_code": 0,
 "bytes": 296,
 "tokens": 74
}
```

**inbox-list**

```
{
 "exit_code": 0,
 "bytes": 454,
 "tokens": 113
}
```

**search-empty**

```
{
 "exit_code": 0,
 "bytes": 3482,
 "tokens": 870
}
```

**search-content**

```
{
 "exit_code": 0,
 "bytes": 783,
 "tokens": 195
}
```

**related-note**

```
{
 "exit_code": 0,
 "bytes": 302,
 "tokens": 75
}
```

**dossier**

```
{
 "exit_code": 0,
 "bytes": 1523,
 "tokens": 380
}
```
