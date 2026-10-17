---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Retrieval behavior (CLAUDE §7)

Executable transcript of answering through the task-shaped reads:
resolve a concept through its alias, inspect it, relate it, read
what explains it, open the note bodies, read the source's
evaluations, find exam artifacts by role and concept, show the
trails behind worked-through questions, answer exam questions from
the owning module, and orient operational questions from the brief
and coordination. All reads; nothing here writes. The generated
fallbacks (domain atlas, `FILES.txt`, health report) are absent
from the fixture, so those conditional branches stop pinned.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Shared operating rules


Retrieve through OPERATOR's task-shaped reads — `inspect`, `related`,
`search`, `material-context`, `note-read`, and `bootstrap --brief` — never by
opening generated views first. The generated views
(`generated/concept-index.md`, `generated/domain-atlas.md`,
`generated/coordination-view.md`) are the human or bulk fallback: open one
only when the targeted reads are insufficient.

When asked about a **concept**:

1. resolve the id with `search` (aliases, including German ones, match as values);
2. read it with `inspect CONCEPT_ID`, then `related CONCEPT_ID` for the units
   whose stages tag it and for prerequisites and related concepts (each edge
   reasoned in `via`);
3. read what explains it with `material-context --concept CONCEPT_ID` — notes
   join by their own tags or as route-direct evidence, never through a shared
   source alone — then open the note bodies with `note-read`;
4. read contextual source evaluations with `inspect SOURCE_ID`;
5. include active workspace context only when relevant;
6. exclude archived workspaces unless history is requested.

When asked for **exam artifacts** ("mock exams for AML"): search notes by
`role` + concept (`search --type note`).

When asked **"have I actually worked through this?"**: read the relevant notes
with `note-read` and answer with the evidence attached to them (derivations,
exercises, implementations) — or its documented absence. Never declare mastery;
show trails.

When asked about **exams, registrations, or grades**: answer from the owning
partitioned academic module (`inspect MODULE_ID` carries its attempts and
sittings) — never from `records/modules.yaml` or prose copies.

When a topic **explodes into prerequisites** (scope explosion): propose a triage — *required now / helpful now / defer / reference only* — sized to the workspace objective, record accepted deferrals in the workspace `Deferred` section, and recommend the smallest useful next source or prerequisite. Preserve the wider graph in concept relations without forcing it into the current scope.

When asked "what should I do next" or about **operational state**: start with
`bootstrap --brief`, then the named workspace plus `inspect`; use `inspect
coordination` when priorities matter. Recommendations are computed fresh, not
read from stored plans.

**Cross-domain reach (ADR-005).** When asked where or how to learn something, for source recommendations, or when no concept alias matches the query: search and relate across ALL domains — not just the active workspace's — before concluding the repository has nothing, orienting with the `domain_atlas` glance on `bootstrap --brief`. Name relevant shelves and crosswalks from other domains whenever they exist; a question standing in one module may be answered by another domain's shelf. Open the full generated domain atlas only when the targeted reads are insufficient. If the atlas has no hit either, `materials/FILES.txt` (rebuilt by `make materials`) lists every unregistered file by name — offer a grep there before answering "we don't have this". Visibility debt (sources no concept, shelf, or note points to) is reported in `generated/reports/health.md`; it is repaid on use (WORKFLOWS §6a), never as a bulk project.

Never rely solely on folder names.

---


## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Resolve the concept through its alias

```scrut
$ los search Erwartungswert
[{"id":"concept-expected-value","type":"concept","title":"Expected value","path":"knowledge/concepts.yaml","status":null,"state":null,"deprecated":false}]
```

## Read the concept

```scrut
$ los inspect concept-expected-value
{"aliases":["Erwartungswert"],"deprecated":false,"id":"concept-expected-value","path":"knowledge/concepts.yaml","title":"Expected value","type":"concept"}
```

## Relate it with reasoned edges

```scrut
$ los related concept-expected-value
[{"id":"concept-variance","type":"concept","title":"Variance","path":"knowledge/concepts.yaml","via":["relation"]},{"id":"note-demo","type":"note","title":"Demo note","path":"knowledge/notes/mathematics/note-demo.md","via":["backlink:concept_to_notes"]},{"id":"note-demo-analysis","type":"note","title":"Expected value — analysis of Demo Book §1","path":"knowledge/notes/mathematics/note-demo-analysis.md","via":["backlink:concept_to_notes"]}]
```

## Read what explains it

```scrut
$ los material-context --concept concept-expected-value | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"], d["total"]); [print(i["origin"], i["id"], i["title"]) for i in d["items"]]; print(d["items"][0]["source"]["ref"], d["items"][0]["source"]["pages"], d["items"][0]["source"]["freshness"])'
material-context 1
analysis-note note-demo-analysis Expected value — analysis of Demo Book §1
source-demo-book/book.pdf [1, 1] current
```

## Open the explaining note body

```scrut
$ los note-read note-demo-analysis | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["note_id"], d["path"], d["content_sha256"], d["total_characters"])'
note-demo-analysis knowledge/notes/mathematics/note-demo-analysis.md sha256:ecd673fe86ebb2952d5efaf15ee8c4dc49f2f10c3710b795f3b8b0cafd23330c 750
```

## Read the source's contextual evaluations

```scrut
$ los inspect source-demo-book | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"], d["source_type"]); print(d["material"], d["material_exists"]); [print(e["level"], e["roles"], e["concepts"]) for e in d["evaluations"]]'
source-demo-book Demo Book book
material://source-demo-book/book.pdf True
introductory ['first-learning'] ['concept-expected-value']
```

## Find exam artifacts by role and concept

```scrut
$ los search --type note "reference expected-value"
[{"id":"note-demo-analysis","type":"note","title":"Expected value — analysis of Demo Book §1","path":"knowledge/notes/mathematics/note-demo-analysis.md","status":null,"state":null,"deprecated":null}]
```

## Show the trails behind worked-through questions

```scrut
$ los inspect note-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["role"]); print(d["evidence"]); print(d["concepts"], d["sources"])'
note-demo synthesis
[]
['concept-expected-value'] ['source-demo-book']
```

## Answer exam questions from the owning module

```scrut
$ los inspect module-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"], d["semester"]); [print(a["termin"], a["date"], a["result"]) for a in d["attempts"]]; [print(s["termin"], s["date"], s["label"]) for s in d["examination"]["sittings"]]'
module-demo Demo Module sose-2026
1 2026-07-27 withdrawn
2 2026-10-09 registered
3 2000-01-01 Elapsed sitting with no attempt
2 2026-10-09 2. Termin
```

## Orient operational questions from the brief

```scrut
$ los bootstrap --brief | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["contract"]); print(d["pointer_state"], d["resume_pointer"]["unit_id"]); print(d["counts"]["inbox_items"], d["owed_study_maps"])'
bootstrap-brief
confirmed unit-demo-l01
2 ['unit-demo-l02']
```

## Read coordination when priorities matter

```scrut
$ los inspect coordination
{"id":"coordination","path":"work/COORDINATION.md","sections":{"Commitments":"(none)","Deferrals":"- Demo module deferred to 2. Termin (date lives in records/modules.yaml)","Dependencies":"(none)","Priorities":"(none)"},"type":"coordination","content_sha256":"sha256:667bbd75392b1acdc610aa249aa5f2fe3d7659603901f415b36eda30fe2b4655","section_sha256":{"Commitments":"sha256:552e423045fcbd949252397b4bee754f0b8f99b1bbbe41edc9b25dbfc81b146a","Deferrals":"sha256:c7fd808ba806ad0f53559df2a76f3f3afb32b3cd79e3227ed0d6133abdc962b2","Dependencies":"sha256:552e423045fcbd949252397b4bee754f0b8f99b1bbbe41edc9b25dbfc81b146a","Priorities":"sha256:552e423045fcbd949252397b4bee754f0b8f99b1bbbe41edc9b25dbfc81b146a"}}
```

## The generated fallbacks are absent from the fixture

```scrut
$ $H/los-assert-file generated/domain-atlas.md --absent
```

```scrut
$ test ! -e "$(dirname "$LOS_FX")/materials/FILES.txt" && echo "FILES.txt absent"
FILES.txt absent
```

```scrut
$ $H/los-assert-file generated/reports/health.md --absent
```

## Reads change nothing

```scrut
$ los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```
