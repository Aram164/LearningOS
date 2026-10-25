# C1-C report — knowledge batch (hunting pass)

Session: GLM-5.3-Flash, 2026-10-24. Base: GitHub `origin/main` at
`d6c4779029e366718b71bda158d2aa8f9da1db39` (exactly the commit the ground
rules name; the remote read `d6c47790` before cloning). Clone:
`~/los-glm-C1-C-2026-10/repository`, branch `glm/C1-C-2026-10-24` (local
only — nothing pushed, nothing committed). The live trees, the vault and all
other campaigns' clones were not touched. One focused pytest process at a
time (three short runs); no full suite, no gates, no CI.

Batch scope: the 12 capabilities in `system/contracts/capabilities.yaml`
whose names start with `note`, `concept`, `ability`, `atlas`, `garden`,
`relationship`, `semantic` — queries `note.content`, `note.search`,
`ability.context`, `atlas.context`, `semantic.query`; commands `note.create`,
`note.revise`, `note.evidence.add`, `note.analysis.save` (and its batch
sibling), `concept.relations.change`, `garden.seed.create`,
`ability.candidate.append`, `atlas.question.save`; domain capabilities
`garden.update`, `garden.add-transcription`, `relationship.create`.

## Findings (2)

Each comes with a failing pytest in this folder; both fail on base main and
pass once the expected behaviour holds.

1. **`note.revise/revise-voids-dedicated-guarantees`** — `note.revise`
   validates only id, type and role (`tools/learning_os/app/handlers/notes.py:186-199`),
   so a replacement file can retarget a question note's
   `atlas_question.target` (probed: commits rc 0; the exact change
   `atlas.question.save` refuses as "the original question target is
   preserved"), and can replace a reference note's body while leaving its
   `material_analysis` binding claiming — per `note.schema.json` — "the note
   body is exactly the file's last N bytes" (probed: commits rc 0; the
   binding now describes bytes the body no longer contains). No validator
   rule covers either field, so staged canonical validation blesses both.
   This is the hole `ARCHITECTURE.md` §5.7 says the general path must never
   offer: "provenance bindings and question wording can never be bypassed by
   the general path". Severity: moderate.

2. **`garden.seed.create/invisible-reserved-slug`** — the seed slug has no
   reserved-name check (`app/handlers/capture.py:53-71`), while the garden
   reader skips `readme` stems as meta
   (`store/loading/knowledge.py:111-113`). A seed titled "README" is created
   and receipted at `knowledge/garden/readme.md`, then unreadable by its own
   stable id (probed: `note-read garden-note-readme` →
   `los: INVALID_REQUEST: note not found: garden-note-readme`), invisible to
   `note.search --type garden-note`, and absent from the Nebula. `derive/garden.py`'s
   own docstring says garden existence and identity "must remain available"
   as Core facts. Severity: low-moderate.

## Attacked and held (no finding)

Labelled **probed** when I drove the real V2 gateway (`los capability …`
envelopes built with `tests/gateway_helpers.py`) against the synthetic mini
repository and observed the outcome; **read** when I verified by reading the
handler, contract, validator and procedure without a probe.

- `note.create` (**read**): destination refuses absolute paths, `..`
  components, non-`.md` suffixes, filename ≠ id, and paths outside
  `knowledge/notes/` (`_destination`), walks every path component for
  symlinks (`_safe`), validates the id against `note.schema.json`
  (`^note-[a-z0-9-]+$`) before filename use — which also closes the
  id-as-traversal class (an id like `..` passes the stem check but fails the
  schema); reserved roles `reference`/`question` refuse; handler-owned
  fields (`type/created/state/authorship/semantic_review`) refuse; body
  bytes are rendered verbatim (`_render_exact_note`) and an
  already-deprecated `supersedes` target is not rewritten.
- `note.evidence.add` (**read**): the shared frontmatter re-renderer
  `body.lstrip()` looked like a "note body is never modified" violation, but
  `FRONTMATTER_RE`'s greedy `\s*\n?` tail already consumes all body-leading
  whitespace for every frontmatter'd note, so the strip is a no-op on any
  valid tree; a frontmatter-less note fails the note schema
  (required `id`) and is refused at staged validation, so no silent body
  rewrite is reachable. Duplicate (type, ref) evidence refuses append-only.
- `note.search` (**read**): content mode refuses a nonempty-`--type` other
  than `note` and an empty query; the indexed prefilter's soundness holds by
  construction — non-ASCII terms return `None` (all candidates), non-ASCII
  notes are always candidates, and ASCII `str.lower`/`re.IGNORECASE` agree —
  so the exhaustive oracle and the indexed path cannot disagree on true
  matches; a derived-store failure falls back to the exhaustive
  implementation, never to a partial answer.
- `semantic.query` (**read**): an unknown predicate names the registry with
  the count and the `--list` pointer (the invariant's "way forward");
  `--input k=v` parses JSON-first with a typed refusal for malformed inputs;
  `--recipe`/`--list` short-circuit deterministically.
- `ability.context` / `derive/abilities.py` (**read**): the horizon pages
  over `sorted(repo.abilities)` re-ranked by a deterministic priority, so
  every ability appears exactly once across pages; edges are page-local with
  per-row off-page counts, as the invariant requires; `reason_codes` are
  decided from structured facts and the handler validates parallelism on
  every row before answering; the evidence-transfer path requires a reviewed,
  currently-fresh equivalence bridge whose conditions are a superset of both
  abilities' conditions, and the `conditions_not_met` check it appears to
  omit is unreachable-harmful because `read_ability_observations` refuses any
  row whose met/not-met sets intersect; prerequisite cycles are guarded at
  registry validation and again by the recursion `building` set. A corrupt
  observations/candidates ledger raises `RuntimeInputError(ValueError)`,
  which the handler converts to a typed refusal.
- `atlas.context` (**read**): scoped read with an after-read fingerprint
  re-check; unknown concept answers with suggestions; corrupt
  `concept-relations` YAML refuses typed via the schema check.
- `concept.relations.change` (**read**): requires exact add/replace/remove
  operation shapes, schema-validates each old/new row, requires the exact
  previous row to exist uniquely across both registry layouts, refuses a
  consolidated+partitioned mix, and delegates duplicate/unknown-endpoint/
  cycle refusal to staged canonical validation — which the
  `add-concept-relation` procedure transcript pins verbatim
  (`E REL-DUP: duplicate relation edge …`).
- `ability.candidate.append` (**probed**): requires the V2 gateway, refuses
  retired/self/unknown endpoints, and the payload schema's optional
  `condition` field defaults safely through the parser-derived namespace
  (probed by omitting it: the append commits with empty conditions — my
  KeyError suspicion was wrong); the V2 path pins `expected_revisions` to
  exactly the transaction's artifacts, so concurrent appends conflict with a
  typed revision refusal rather than a silent lost row.
- Domain capabilities (**read**, `app/ai_actions/service.py:822-900`):
  `garden.update` enforces `allowed_fields` (title, state);
  `garden.add-transcription` never touches the original seed, requires an
  explicit `supersedes` to replace an existing transcription, and stamps
  `provenance: ai-derived`; `relationship.create` requires stable ids and
  endpoint mappings and dedupes by id.
- Exact replay (**probed**, as a side effect of the finding flows):
  resubmitted envelopes answer `replayed: true` with no second write.
- Crash windows, two-writer races, rollback (**read**, not kill-tested):
  the engine journals a compare-and-undo intent (`_publish_journal`,
  `store/transactions.py:1894-1966`) staged whole and published by one
  atomic rename before the first mutation, re-checks every path against the
  captured pre-state immediately before each write (`_guard_apply`), and
  `reconcile_inflight_transactions` unwinds published journals with the same
  compare-and-undo proof obligations. Same conclusion as C1-B: the net is
  real; handler-level holes that validation also blesses are the findable
  class.

## Reproducing the tests

Both finding tests are copied into this folder; in the clone they live at
`tests/test_c1c_revise_guarantees.py` and
`tests/test_c1c_garden_reserved_slug.py`, registered in
`tests/group_map.py` under `gateway` (the conftest refuses unregistered
files — the registration is part of the repro). Run each on its own:

```
.venv/bin/python -m pytest tests/test_c1c_revise_guarantees.py -q      # 2 failed on base
.venv/bin/python -m pytest tests/test_c1c_garden_reserved_slug.py -q   # 1 failed on base
```

The assertions are written fix-agnostic on purpose ("refused, or the stored
fact still describes the stored bytes"), so a verifier can fix either way
without rewriting the tests. Nothing was committed; the clone's working tree
carries the two test files plus the `group_map.py` registration uncommitted,
exactly as the ground rules require.

## ASSUMPTIONs

- ASSUMPTION: the **read**-labelled verdicts above are as strong as stated
  only for the attack classes listed; I did not probe them empirically, and
  the verification pass should treat them as code-reading evidence, not
  proof.
- ASSUMPTION: crash-window and recovery behaviour is asserted from the
  engine's journal/rollback design and code comments, not from a kill test.
- ASSUMPTION: the `note.evidence.add` lstrip analysis rests on
  `FRONTMATTER_RE` regex semantics (`domain/vocabulary.py:13`), verified by
  reading; I did not construct a frontmatter-less note end-to-end to confirm
  staged validation refuses it.
- ASSUMPTION: this batch needs no `obsidian-ui` clone (no UI capability in
  these families); I cloned Core only, following the C1-A/C1-B precedent.
- The venv was built with `python3.14 -m venv .venv && .venv/bin/pip install
  -e '.[dev]'` as prescribed; `make setup` / `make hooks` were never run.

## Not done, on purpose

No pushes, no commits, no CI runs, no issue filing, no fixes, no contract
edits. Verification belongs to the C1 verification pass on GLM-5.3; landing
belongs to Aram or Claude.
