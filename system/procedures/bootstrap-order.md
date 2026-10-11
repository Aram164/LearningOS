---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Bootstrap order (CLAUDE §2)

Executable transcript of the agent startup order: discover the
task-shaped entry, start from one bootstrap read, enter material
maintenance through the guarded route context, look records up
directly, resume interrupted study instead of re-deriving it, and
enter an authorized mutation through the capability contract. All
reads; nothing here writes. The fixture ships no repository-root
`CLAUDE.md`, so the single-copy rule has no link to show.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Discover the task-shaped entry

```scrut
$ los capabilities --compact --json | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract_version"]); print(len(d["queries"]), len(d["commands"])); print(d["operator_contract"])'
2
19 47
system/OPERATOR.md
```

## Start from the brief bootstrap

```scrut
$ los bootstrap --brief | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["snapshot_id"]); print(d["session_identity"]["session_id"], d["session_identity"]["source"]); print(d["pointer_state"], d["resume_pointer"]["unit_id"], d["resume_pointer"]["stage_id"]); print(d["counts"]["notes"], d["counts"]["concepts"], d["counts"]["sources"], d["counts"]["workspaces_active"])'
bootstrap-brief sha256:94e93d3032e1f89b5112208e9614cc86243f8c850a1a8ff3855510d85170350b
channel:operator channel
confirmed unit-demo-l01 stage-demo
2 2 1 2
```

## Orient across domains with the atlas glance

```scrut
$ los bootstrap --brief | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); [print(a["domain"], a["notes"], a["crosswalks"], a["shelves"]) for a in d["domain_atlas"]] '
mathematics 2 0 0
machine-learning 0 0 0
systems 0 0 0
data-systems 0 0 0
algorithms 0 0 0
programming 0 0 0
cross-domain 0 0 1
```

## Expand to the compact bootstrap when the task needs it

```scrut
$ los bootstrap --compact | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["snapshot_id"]); print(d["collections"]["units"]["total"], d["collections"]["study_maps"]["total"]); print(d["resume_pointer"]["unit_id"], d["counts"]["units_needing_map"])'
bootstrap-summary sha256:94e93d3032e1f89b5112208e9614cc86243f8c850a1a8ff3855510d85170350b
2 1
unit-demo-l01 1
```

## Enter material maintenance through the named route

```scrut
$ los plan-edit-context unit-demo-l01 --route-id route-b2f1f80014860a929a3af0bc | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["unit_id"]); print(d["route"]["id"], d["route"]["title"]); print(d["patch_capability"])'
plan-edit-context unit-demo-l01
route-b2f1f80014860a929a3af0bc Demo book — expected-value derivation
route.patch
```

## Enter through the named stage

```scrut
$ los plan-edit-context unit-demo-l01 --stage-id stage-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["requested_stage_id"]); print(d["stage"]["id"], d["stage"]["title"], d["stage"]["status"]); print(d["scope"])'
plan-edit-context-stage stage-demo
stage-demo Derive expected value active
one stage only — universe questions (e.g. no source covers X) need the full unit context
```

## Discover units with exact filters

```scrut
$ los unit-list --compact
{"schema_version":1,"snapshot_id":"sha256:94e93d3032e1f89b5112208e9614cc86243f8c850a1a8ff3855510d85170350b","contract":"unit-list-summary","filters":{},"items":[{"id":"unit-demo-l01","title":"Expected value","status":"active","module_id":"module-demo","order":1,"current_study_map":"study-map-demo-l01","needs_study_map":false},{"id":"unit-demo-l02","title":"Variance","status":"active","module_id":"module-demo","order":2,"needs_study_map":true}],"total":2,"next_offset":null,"detail":"inspect UNIT_ID"}
```

## Batch known record ids in one inspect call

```scrut
$ los inspect note-demo concept-expected-value
{"schema_version":1,"snapshot_id":"sha256:94e93d3032e1f89b5112208e9614cc86243f8c850a1a8ff3855510d85170350b","contract":"record-batch","requested_ids":["note-demo","concept-expected-value"],"records":[{"id":"note-demo","type":"note","title":"Demo note","path":"knowledge/notes/mathematics/note-demo.md","domain":"mathematics","summary":"Body prose.","role":"synthesis","state":null,"authorship":null,"concepts":["concept-expected-value"],"sources":["source-demo-book"],"contexts":[],"attachments":[],"evidence":[],"supersedes":[],"reviewed":null,"transcription":null,"semantic_review":null,"atlas_question":null,"material_analysis":null},{"id":"concept-expected-value","type":"concept","title":"Expected value","path":"knowledge/concepts.yaml","aliases":["Erwartungswert"],"deprecated":false}]}
```

## Resolve the id through its alias

```scrut
$ los search Erwartungswert
[{"deprecated":false,"id":"concept-expected-value","path":"knowledge/concepts.yaml","state":null,"status":null,"title":"Expected value","type":"concept"}]
```

## Read the concept's relations with their reasons

```scrut
$ los related concept-expected-value
[{"id":"concept-variance","path":"knowledge/concepts.yaml","title":"Variance","type":"concept","via":["relation"]},{"id":"note-demo","path":"knowledge/notes/mathematics/note-demo.md","title":"Demo note","type":"note","via":["backlink:concept_to_notes"]},{"id":"note-demo-analysis","path":"knowledge/notes/mathematics/note-demo-analysis.md","title":"Expected value — analysis of Demo Book §1","type":"note","via":["backlink:concept_to_notes"]}]
```

## Open the note body

```scrut
$ los note-read note-demo
{"schema_version":1,"snapshot_id":"sha256:94e93d3032e1f89b5112208e9614cc86243f8c850a1a8ff3855510d85170350b","contract":"note-content","note_id":"note-demo","path":"knowledge/notes/mathematics/note-demo.md","content_sha256":"sha256:5bfb18040cdeba3b47d06700b13c0edf6ebcac90d085e6fc78cfe8565261d276","offset":0,"offset_unit":"unicode_characters","total_characters":162,"start_line":1,"content":"---\nid: note-demo\ntype: note\ntitle: Demo note\ncreated: 2026-07-16\nrole: synthesis\nconcepts: [concept-expected-value]\nsources: [source-demo-book]\n---\n\nBody prose.\n","next_offset":null}
```

## Return to interrupted study without re-deriving it

```scrut
$ los resume | grep -v "decide per goal id" | grep -v "^  Next"
Demo Module · Expected value · stage-demo
  (via resume pointer; pointer updated 2026-09-20 (11 days ago))

  Recorded aims (compare with current dates and state):
    Coordination priorities (undated): (none)
      source: work/COORDINATION.md#Priorities
    Workspace workspace-demo: Do the demo thing.
      source: work/active/workspace-demo/CONTEXT.md#Next-Action

  Requirement  knowledge-demo-expectation
               capability: {"kind": "explain", "operands": ["expectation"]}
               under: unfamiliar-example
               evidence: explain-reason

  Evidence     none recorded yet
  Last result  none
  Stage note   nothing recorded yet (curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md)

  Open here    —

  Top goal     Re-judge covers:route-b2f1f80014860a929a3af0bc: lineage reads moved (1 goal)
               tier 1 — 2026-10-09 (8 days); seeing it files nothing

  Exam         2. Termin — 2026-10-09 (8 days)
```

## Enter a mutation through the capability contract

```scrut
$ los capabilities note.create --json | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); c = d["commands"]["note.create"]; print(c["handler"], c["cli_command"], c["writes"])'
note_create note-create ['knowledge/notes/**']
```

## Consult the corpus before treating a document as binding

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; d = yaml.safe_load(open("system/contracts/normative-corpus.yaml")); print(len(d["documents"])); e = [x for x in d["documents"] if x["path"] == "system/OPERATOR.md"][0]; print(e["path"], e["class"], e["authority"])'
68
system/OPERATOR.md contract binding
```

## The fixture ships no root CLAUDE.md to link

```scrut
$ $H/los-assert-file CLAUDE.md --absent
```

## Reads change nothing

```scrut
$ los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```
