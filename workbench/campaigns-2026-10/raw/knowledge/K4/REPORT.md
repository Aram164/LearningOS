# K4 — the authoring path, probed (REPORT)

**Result: 0 findings.** All nine cases in the batch held under real V2
gateway probes in a disposable fixture repository. 25 probe tests across 7
files, every one green on the pinned base; the focused files that share the
machinery re-ran green afterwards. Four boundary observations recorded (not
findings — each lacks a violated contract line, and the reasons are stated).

## Base

- Clone: `/Users/aramaljanadi/los-glm-K4-2026-10/repository` (full clone from
  `https://github.com/Aram164/LearningOS.git`, private branch `glm/K4-2026-10-25`).
- Core pin: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` (branch
  `codex/operator-developer-docs-20261025`), HEAD verified after checkout:
  `git rev-parse HEAD` → `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`.
- UI pin `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94` is the paired candidate;
  K4 is Core-only and never loaded it.
- venv: `python3.14 -m venv .venv && .venv/bin/pip install -e '.[dev]'`
  (exit 0). `make setup` / `make hooks` not run, per the 2026-10-24
  environment rules.
- Working-tree footprint in the clone (nothing committed, nothing pushed):
  7 untracked probe files `tests/test_k4_*.py`, plus registration —
  `tests/group_map.py` (+7 lines, group `gateway`) and
  `.github/shard-manifest.json` (+7 lines, sorted into the leg carrying
  `tests/test_atlas_authoring.py`). `git status --porcelain` shows exactly
  those two modified files and the seven untracked probes.
- No pushes, no CI dispatches, no `system/contracts/` edits, no live-tree
  edits, no production fixes, no other chat launched. One pytest process at
  a time, one focused file per process, throughout.

## Scope decisions

C1-C's "Attacked and held" labels drove what this batch drove:

- `concept.relations.change` was **read**-only in C1-C, so all five of its
  K4 cases were attacked empirically through the real V2 gateway
  (`los capability concept.relations.change --payload-file -` with
  envelopes built by `tests/gateway_helpers.py`).
- `atlas.question.save` appears nowhere in C1-C's attacked list (its finding
  1 only witnessed the retarget refusal), so all three K4 cases were
  attacked from scratch.
- Nothing in K4's case list is marked **probed** by C1-C (its probed items
  were `ability.candidate.append` and generic exact replay), so the
  skip-list is empty. Exact replay appears inside probes 5 and 6 as a
  witness step, not as a re-attack.
- The note-to-concept case was attacked through both surfaces that could
  answer it: the validator CLI and a gateway write's staged validation.

Reading route completed before probing: Core `AGENTS.md` →
`system/OPERATOR.md` (hard boundaries) → `system/DEVELOPER.md` (read-in-order
route; task row "Add a test file" for the registration rules) →
`system/developer/CODEMAP.md`. Law under test read directly:
ADR-015 (registry shape), ADR-016 decision 4 (strict cycles only), ADR-017
decisions 1–5 plus its Consequences (the authoring contract),
`ARCHITECTURE.md` §8 (eight types, no `related-to`), the
`concept.relations.change` and `atlas.question.save` entries in
`system/contracts/capabilities.yaml`, `concept-relations.schema.json`,
`note.schema.json` (`atlas_question.target`), the handler
`tools/learning_os/app/handlers/atlas.py`, the validator rules
`derive/validation/registries.py` and `derive/validation/references.py`,
and the commit path `app/commit.py` (staged validation = the full validator
over severity-E issues) with `store/transactions.py` (`_guard_snapshot`).

## Results per case

Every probe drives the real V2 gateway (or the validator CLI for probe 7's
direct question) against the suite's own `mini_repo` fixture. Probe copies:
`probes/test_k4_*.py`; exact pytest commands and full output: `logs/*.out`.

| # | K4 case | Probe | Result |
|---|---|---|---|
| 1 | replace/remove with a stale old row | `test_k4_1_stale_old_row.py` | **HELD** — 3/3 |
| 2 | a cycle introduced by a replace | `test_k4_2_replace_cycle.py` | **HELD** — 4/4 |
| 3 | 50 operations, then 51 | `test_k4_3_operation_budget.py` | **HELD** — 4/4 |
| 4 | an operation naming an alias | `test_k4_4_alias_endpoints.py` | **HELD** — 3/3 |
| 5 | two sessions, different rows, one snapshot | `test_k4_5_two_sessions.py` | **HELD** — 3/3 |
| 6 | question on a relation | `test_k4_6_question_lifecycle.py` | **HELD** — 5/5 |
| 7 | target later removed by `concept.relations.change` | `test_k4_6_question_lifecycle.py` | **HELD** — (same file) |
| 8 | the same wording saved twice | `test_k4_6_question_lifecycle.py` | **HELD** — (same file) |
| 9 | note names a concept id that is then removed | `test_k4_7_note_concept_link.py` | **HELD** — 3/3 |

What each probe did and observed (refusal bodies verbatim):

1. **Stale old row.** Commit `replace old→new` in session one; then offer the
   now-stale `old` to remove and to replace. Both refuse with
   `INVALID_REQUEST`: `the exact previous relation no longer exists
   uniquely; reload and review`, and the registry file stays byte-identical
   each time (asserted). The refusal is the handler's `old-not-found` site;
   no partial state exists to clean up.
2. **Cycle via replace.** Fixture: `variance builds-on expected-value`,
   `expected-value requires concept-cycle-c`, `cycle-c motivates variance`
   (semantic, harmless). Replacing the semantic row with
   `cycle-c requires variance` completes a strict cycle. The gateway refuses
   with `VALIDATION_FAILED` (retryable false):
   `transaction failed canonical validation: E REL-PREREQ-CYCLE:
   prerequisite cycle: concept-cycle-c -> concept-variance ->
   concept-expected-value -> concept-cycle-c
   [knowledge/concept-relations.yaml]` — and the registry is byte-identical
   afterwards (staged-validation rollback witnessed end to end through the
   gateway, the part C1-C only read). The refusal message is byte-identical
   across two fresh envelopes, and it walks the cycle via the strict edges
   only. Controls: the same replace with a *semantic* type commits
   (ADR-016 decision 4), and the same cycle offered as two `add`s in one
   batch also refuses atomically.
3. **50 operations, then 51.** One envelope with 50 distinct semantic adds
   commits in one transaction (`operation_count: 50`, one receipt, 51 rows
   in the registry). 51 adds refuse at gateway payload admission —
   `INVALID_REQUEST`: `invalid payload for concept.relations.change:
   change/operations: …` (the declared `max_items: 50` in the capability's
   payload record; the handler's own 1..50 check is defense in depth behind
   it) — with the registry byte-identical. Two batch-atomicity probes: a
   batch whose late add duplicates its first add is refused by staged
   validation (`REL-DUP`) committing nothing; an empty operations list
   refuses.
4. **Alias instead of an id.** Two alias shapes:
   - a free-form declared alias (`Erwartungswert`) is refused by the
     handler's row-schema check — `INVALID_REQUEST`:
     `concept-relations: 'Erwartungswert' does not match
     '^concept-[a-z0-9]+(?:-[a-z0-9]+)*$'` (site `bad-relation-row`);
   - a declared alias shaped like a concept id (`concept-ew`) passes the
     pattern, and staged canonical validation refuses the commit —
     `VALIDATION_FAILED`: `E REL-ENDPOINT: relation[1] 'from' does not
     resolve: 'concept-ew' [knowledge/concept-relations.yaml]` — with the
     registry byte-identical. No alias-named row can land in the registry
     through either door (the committed-alias failure this hunts is not
     reachable). The replace shape behaves the same.
5. **Two sessions, different rows, one snapshot.** Both envelopes are built
   from the same pre-state. Session A commits its replace of row 1. Session
   B submits its replace of row 2 carrying the same snapshot token and is
   refused with `STALE_SNAPSHOT` (retryable true):
   `canonical state changed since this request was approved`, details
   carrying expected/actual fingerprints; row 2 is unchanged in the file —
   no lost update. A third envelope omitting `expected_snapshot` entirely
   (re-bound approval over the reduced intent) is refused at admission:
   `INVALID_REQUEST`: `invalid capability envelope … is not valid under any
   of the given schemas` — the V2 envelope schema makes the token mandatory
   (see boundary observation 3). Exact replay of A's envelope answers
   `replayed: true` with no second write.
6. **Question on a relation.** A new question with target
   `{from, type, to}` naming the authored relation commits; the note lands
   at `knowledge/notes/questions/<id>.md`; `atlas-context` lists the
   question from BOTH endpoints (the `to` endpoint check is new relative to
   the suite's own authoring test, which only checks `from`).
7. **Target later removed.** With a question saved on the relation,
   `concept.relations.change` removes that relation and commits — as
   ADR-017's Consequences require ("removing a connection removes an
   assertion. It never deletes … a question recorded against it"). The
   question note keeps its recorded target byte-for-byte (wording asserted
   in the note file), stays `open`, and `atlas-context` still lists it from
   both endpoints with `relations: []`. A NEW question on the
   now-removed relation refuses: `INVALID_REQUEST`: `question connection
   target does not exist`, and no note file is created. The
   missing-target *display* is boundary observation 1.
8. **Same wording twice.** Three shapes, all behaving as the law says:
   - the exact envelope resubmitted answers `replayed: true` and writes
     nothing new;
   - the same wording under the same note id with a fresh idempotency key
     commits as an update: still one note, note bytes identical after the
     save, stored target unchanged, and the artifact revision bumps (see
     boundary observation 4);
   - the same wording under a second note id commits as a second question
     note; `atlas-context` lists both. Nothing dedups wording — see
     boundary observation 2.
9. **Note names a removed concept.** A note whose frontmatter carries
   `concepts: [concept-expected-value, concept-variance]` while
   `concept-variance` is removed from the fixture's `knowledge/concepts.yaml`
   (direct authoring is how concepts leave — there is no write capability,
   so the fixture simulates Aram's act): `los validate` exits non-zero and
   reports `REF-CONCEPT … note 'note-k4-linked' references unknown concept
   'concept-variance'` with the note's path as the location — validation
   DOES name the note. The same dangling link also refuses an unrelated
   gateway write (its staged validation surfaces the same `REF-CONCEPT`
   naming the note, registry byte-identical), and restoring the concept
   releases exactly that write — the refusal was the dangling link, not the
   operation.

## Boundary observations (recorded, NOT findings)

1. **No explicit missing-target marker in `atlas.context`.** ADR-017's
   Consequences say a question whose recorded target stops existing "shows
   the missing-target state". Core's `atlas.context` response carries
   `relations` (the live rows) and `questions` (with their recorded
   targets) in one response, so a consumer can derive the state by
   composing them — and nothing more: the response has no
   target-exists/missing field, and no contract line (the capability entry,
   the request schema, ADR-017 itself) promises one. The derivation basis
   is asserted by `test_k4_6_question_lifecycle.py` (relations empty,
   target intact). Whether the Atlas UI surfaces it as a distinct state
   was K3's surface, not Core's; recorded here so the absence is a counted
   fact rather than a surprise.
2. **Same wording under two ids is two question notes.** ADR-017 decision 4
   makes a question a note whose id is its identity; nothing in the
   capability entry, ADR-017, or ARCHITECTURE dedups question wording, and
   none forbids it. Core's observed semantics: no dedup. Recording as a
   fact, not a defect.
3. **`expected_snapshot` is mandatory in the V2 envelope schema.** An
   envelope without the token refuses at admission (`INVALID_REQUEST`),
   so through the gateway there is no token-less path that could reach the
   transaction and lean on the registry-revision guard alone. For this
   capability the revision guard is therefore defense in depth (its
   handler-level `expected_revision` parsing remains for callers that
   present one), and the snapshot guard answers the two-session race.
   Recorded because C1-C's note that "the V2 path pins expected_revisions
   to exactly the transaction's artifacts" left this question open for
   `concept.relations.change` specifically.
4. **Revisions count committed writes, not byte changes.** Saving the same
   wording a second time under the same id (fresh idempotency key) commits
   a real transaction and bumps the note's artifact revision (1→2) even
   though the note bytes are identical. No contract line promises
   content-addressed revisions; recorded so the counter's semantics are
   on the record. Likewise: exact replay requires resubmitting the exact
   original envelope — the same payload rebuilt with fresh
   `expected_revisions` is a *different* approved intent under the same
   idempotency key and refuses with `IDEMPOTENCY_CONFLICT` (`idempotency
   key was already used for a different approved intent`, retryable
   false). That refusal is the intent-binding working as designed;
   witnessed during probe 6's development, kept here as an observed
   mechanic.

## Probe-authoring notes (for the verifier)

Five probe drafts failed on fixture/assertion mistakes, never on Core
behavior; each was corrected and the final runs are what the logs hold:

- probe 2 first asserted whole-response equality across two envelopes —
  the echoed `request_id`/`idempotency_key` differ by design; the
  `error.message` is the deterministic part (now asserted).
- probe 3's first fixture generated 50 distinct rows including both
  directions of strict types — a genuine prerequisite cycle validation
  correctly refused; switched to semantic types only. Its first response
  assertion missed the envelope nesting (`result.operation_count`).
- probe 5's "no snapshot token" variant initially passed
  `expected_snapshot=None` to the envelope helper — which *computes* the
  current fingerprint (it is a default, not an omission); the omission is
  `del envelope["expected_snapshot"]`.
- probe 6's replay step first rebuilt the envelope instead of resubmitting
  the original object — the rebuilt envelope carries fresh
  `expected_revisions`, a different intent, and correctly answers
  `IDEMPOTENCY_CONFLICT` (boundary observation 4). Its first response
  assertions missed the envelope nesting too.
- One scratch script (logged as `logs/refusal-bodies-scratch.out`) briefly
  suggested a question could target a removed relation: its own earlier
  replace had committed, so its remove was refused as stale and the target
  never disappeared. The step-by-step rerun confirms the refusal; probe 6
  asserts it.

Envelope response shape facts for anyone re-running: success bodies nest
the handler result under `result` (which carries its own `replayed`,
`artifact_revisions`, `snapshot_after`); error bodies carry
`error.code`/`error.message`; `replayed: true` appears top-level on
replays.

## Logs

- `logs/test_k4_1_stale_old_row.out` … `logs/test_k4_7_note_concept_link.out`
  — one file per probe, produced by `.venv/bin/python -m pytest
  tests/<file> -v` from the clone root (exact command visible in each
  file's header line), final passing runs.
- `logs/refusal-bodies-scratch.out` — the scratch that produced the verbatim
  refusal bodies quoted above (with the flow error corrected as described).
- `logs/original-focused-tests-after-probes.out` — the files sharing the
  probes' machinery, re-run after the probes landed in `tests/`:
  `test_atlas_authoring.py` 6 passed; `test_gateway_typed_refusals.py`
  38 passed; `test_gateway_v2.py` 73 passed.

## ASSUMPTIONs

- ASSUMPTION: the 50-operation commit's registry (51 rows) and the 51-op
  refusal's registry (1 row) were checked by reading the file, not by
  re-projection; no consumer-side projection was exercised for the bulk
  case.
- ASSUMPTION: `los validate`'s exit code and stderr text for the dangling
  note link were asserted by substring; the exact REF-CONCEPT line quoted
  in the report comes from the logged run.
- ASSUMPTION: the UI side of the missing-target display (boundary
  observation 1) is not re-litigated here; K3's report is the authority for
  what the UI does.
