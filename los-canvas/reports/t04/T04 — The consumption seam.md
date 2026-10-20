# T04 — The consumption seam

**5/5 passed.**

## PASS — s1-ui-reachable-surface

*Intent:* Which Core capabilities can the Obsidian UI actually invoke?

**ui_source_files**

```
125
```

**ui_verbs_named**

```
154
```

**core_declared_queries**

```
19
```

**core_declared_commands**

```
47
```

**reachable_queries**

```
[]
```

**reachable_write_capabilities**

```
[
 "ability.candidate.append",
 "atlas.question.save",
 "capture.create",
 "concept.relations.change",
 "detour.create",
 "detour.resolve",
 "garden.seed.create",
 "learner.ability-observation.append",
 "review.apply",
 "review.prepare",
 "source.feedback.record",
 "stage.attachment.add",
 "stage.note.write",
 "stage.progress.update",
 "unit.map.import",
 "unit.note.append",
 "unit.source-selection.set"
]
```

**note_reading_reachable**

```
[]
```

**note_queries_declared_but_unreachable**

```
[
 "note.content",
 "note.search"
]
```

## PASS — s2-projection-vs-note-body

*Intent:* What does a projection-only consumer see of a durable note?

**notes_in_projection**

```
2
```

**rows**

```
[
 {
  "note_id": "note-demo",
  "projection_keys": [
   "atlas_question",
   "attachments",
   "authorship",
   "concepts",
   "contexts",
   "domain",
   "evidence",
   "id",
   "material_analysis",
   "path",
   "reviewed",
   "role",
   "semantic_review",
   "sources",
   "state",
   "summary",
   "supersedes",
   "title",
   "transcription",
   "type"
  ],
  "body_chars": 162,
  "summary_chars": 11,
  "visible_fraction": 0.068,
  "has_body_key": false
 },
 {
  "note_id": "note-demo-analysis",
  "projection_keys": [
   "atlas_question",
   "attachments",
   "authorship",
   "concepts",
   "contexts",
   "domain",
   "evidence",
   "id",
   "material_analysis",
   "path",
   "reviewed",
   "role",
   "semantic_review",
   "sources",
   "state",
   "summary",
   "supersedes",
   "title",
   "transcription",
   "type"
  ],
  "body_chars": 750,
  "summary_chars": 56,
  "visible_fraction": 0.075,
  "has_body_key": false
 }
]
```

**gateway_note_read_bytes**

```
609
```

**note**

```
the projection carries a note's identity, summary and provenance; the body only travels through note.content
```

## PASS — s3-note-corpus-search

*Intent:* The durable-note corpus is searchable — but only from the CLI.

**search_content_exit**

```
0
```

**matches**

```
null
```

**keys**

```
[
 "contract",
 "items",
 "next_offset",
 "schema_version",
 "snapshot_id",
 "total"
]
```

**note**

```
`search --content` reaches the full text of durable notes, and it is a CLI command the UI never names
```

## PASS — s4-ui-has-no-note-body-path

*Intent:* Does any UI code path read a durable note's body?

**ui_has_a_notes_collection**

```
true
```

**ui_note_body_reads**

```
0
```

**note**

```
the Atlas surface filters note *records*; no UI code path reads a note body
```

## PASS — s5-ui-renders-note-provenance

*Intent:* Does the UI render a note's provenance, or only its summary?

**rendered_facts**

```
{
 "summary": true,
 "authorship": true,
 "lifecycle": true,
 "semantic_review": true,
 "reviewed": true,
 "recorded_sources": true,
 "material_analysis": true,
 "analysis_resolution": true,
 "inspected_range": true,
 "recorded_evidence": true
}
```

**renders_note_body**

```
false
```

**renders_evidence_refs**

```
true
```

**resolves_evidence_refs**

```
false
```

**note**

```
the UI shows the bindings and the refs, but not the body, and it does not resolve a ref against the corpus
```
