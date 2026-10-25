# C1-B report — units and paths batch (hunting pass)

Session: GLM-5.3-Flash, 2026-10-24. Base: GitHub `origin/main` at
`d6c4779029e366718b71bda158d2aa8f9da1db39` (exactly the commit the ground
rules name). Clone: `~/los-glm-C1-B-2026-10/repository`, branch
`glm/C1-B-2026-10-24` (local only — nothing pushed, nothing committed).
The live trees, the vault and all other campaigns' clones were not touched.
One focused pytest process at a time; no full suite, no gates, no CI.

Batch scope: the 19 capabilities in `system/contracts/capabilities.yaml`
whose names start with `unit`, `stage`, `path`, `route`, `detour`, `review`,
`learner` — commands `learner.ability-observation.append`,
`learner.observation.append`, `learner.stage-result.append`, `route.patch`,
`unit.plan.revise`, `unit.map.import`, `unit.note.append`,
`unit.source-selection.set`, `unit.material-synthesis.publish` (also a domain
capability), `stage.note.write`, `stage.progress.update`,
`stage.attachment.add`, `detour.create`, `detour.resolve`, `review.prepare`,
`review.apply`, `path.note.write`, `path.progress.update`,
`path.attachment.add`. No queries fall in these families.

## Findings (1)

Comes with a failing pytest in this folder; it fails on base main and passes
once the expected behaviour holds. Details, verbatim output, contract lines,
root cause and suggested fix are in `review.apply/partial-apply-hides-remainder/finding.md`.

1. **`review.apply/partial-apply-hides-remainder`** — applying an explicitly
   selected subset of a shelving proposal (the designed case, OPERATOR
   boundary 9) sets `shelving.state = "applied"` unconditionally
   (`tools/learning_os/app/handlers/capture.py:543`), and the decision
   surface publishes a shelving row only while `state == "proposed"`
   (`tools/learning_os/derive/projection/review.py:79`). The unapplied
   remainder stays in the packet and remains appliable later (verified), but
   disappears from `review_items` — pending work silently leaves the decision
   queue, and the map falsely records the packet as applied. No canonical
   corruption; validation stays green. Severity: moderate.

## Attacked and held (no finding)

Labelled **probed** when I drove the real V2 gateway (`los capability …`
envelopes built with `tests/gateway_helpers.py`) against a synthetic mini
repository and observed the outcome; **read** when I verified by reading the
handler, contract and procedure without a probe. The exploratory probes live
in the clone at `tests/test_c1b_probes.py` (all 5 pass; a copy is in this
folder as `probes_attacked_and_held.py`).

- `detour.create` off a non-active stage (**probed**): `required-now` off a
  pending stage, while another stage is active, is refused at commit by
  staged canonical validation — verbatim
  `E MAP-ACTIVE: a non-active study map may not contain an active stage`.
  `required-now` off a completed stage is refused — verbatim
  `E MAP-COMPLETED-DATE: stage 'stage-two' has a completion date but is not
  complete`. Both leave the tree unchanged and validation-clean;
  `helpful-now`/`deferred`/`reference-only` off any stage commit without
  status changes, as designed.
- `stage.progress.update` on a non-current stage (**probed**): pausing a
  pending stage while another is current+active is refused at commit
  (verbatim `E MAP-ACTIVE`, same rule); the resume-pointer write, the
  progress summary/next pairing refusal and the complete/skip
  active-only-guard were **read** (`handlers/learner.py:112-191`) and the
  happy path is pinned by the `end-a-session` Scrut transcript.
- Exact replay and idempotency (**probed**): resubmitting the identical V2
  envelope answers `ok: true, replayed: true` with no second write
  (`review.prepare`, `stage.progress.update`).
- Two writers from one snapshot (**probed**): two envelopes sealed against
  the same snapshot/revisions, submitted sequentially — the second exits 3
  `STALE_SNAPSHOT: canonical state changed since this request was approved`,
  and the note file carries only writer one's text. Handler and commit run
  under the exclusive operator lock (`app/pipeline.py:241`), closing the
  read-modify-write window in the append handlers (**read**).
- Shelving safety (**probed** + **read**): `review.apply` destinations are
  confined to `knowledge/notes`/`knowledge/garden` with `..`/symlink escape
  resolved-and-refused (`_approved_destination`, `capture.py:490-496`);
  re-applying an applied destination refuses (`unsafe or existing shelving
  destination`); an item whose content is not a schema-valid note (missing
  frontmatter, or filename ≠ frontmatter id) is refused by staged canonical
  validation before anything commits.
- `path.*` family on a schema-valid learning path (**probed**): completing a
  non-active stage refuses (`only the active stage can be completed or
  skipped; activate it first`); `path.note.write` on a stage without
  `notes_path` refuses (`stage has no notes_path: stage-two`); append writes
  exactly the given text; completing the final stage moves the path to
  `ready-to-shelve` with `shelving.state: draft`. `path.attachment.add` was
  probed only to its payload-dependency refusal (my probe omitted
  `file_sha256`); its write confinement is the shared `write_target` layer
  (**read**).
- Paths with unicode and spaces (**probed**): `stage.attachment.add` accepts
  `télé notes (1).pdf` and records it verbatim in the stage's attachments.
- `unit.source-selection.set` remove-guard (**probed**): removing the demo
  selection wired into the current map's stage resource refuses
  (`this choice is used by the current study path …`); the guard matches by
  stable route id first, falling back to exact `(source_id, locator)` only
  for pre-id resources (**read**, `handlers/learner.py:804-830`).
- `learner.observation.append` / `learner.stage-result.append` /
  `learner.ability-observation.append` (**read**): all three are V2-only
  (direct CLI refuses), workspace-scoped, and their `supersedes` rules bind
  the prior row to the same ledger, the same requirement/unit+stage, and
  refuse an already-superseded prior; a condition cannot be recorded as both
  met and not met; `assistance` is schema-required on the ability path, so
  the handler's direct index cannot KeyError through the gateway.
- `unit.map.import` (**read**): content-bound file bytes, `unit_id` binding,
  identity-preserving replacement with explicit reorder/reset/retire
  declarations (`_plan_map_replacement`), and schema validation of both the
  authored and the expanded map before any write.
- `unit.plan.revise` (**read**): funnels into the `module.plan.import` engine
  whose traversal/schema guards C1-A probed; the reviewed-apply path re-binds
  the exact reviewed bytes, report and guards (`apply_reviewed_envelope`).
- `unit.material-synthesis.publish` (**read**): `approve` is envelope
  authority, not payload; the dossier is validated twice — once for fast
  feedback, again inside the serialized write window — and the lineage ledger
  lands in the same transaction.
- `route.patch` (**read**): only the six declared descriptive fields, with
  the ambiguous-route and legacy-mirror rules (`handlers/routes.py:119-190`);
  claim admission preflight and the plan-hash binding were **read**, the
  shared transaction layer was C1-A-probed.
- `detour.resolve` (**read**): a dangling `return_to_stage` is unreachable
  through capabilities (create resolves the stage; `DETOUR-STAGE` validates
  every commit), and resolve demotes only active/paused stages, preserving
  completed ones.
- Crash windows and rollback (**read**, not kill-tested): the transaction
  engine journals to `operations/transactions/.inflight` before applying,
  validates the staged state, and republishes the recorded pre-state on any
  failure (limit: I did not kill processes between phases this session).

## Reproducing the tests

The finding's test is copied into this folder; in the clone it lives at
`tests/test_c1b_shelving_partial_apply.py`, registered in `tests/group_map.py`
under `studyplan` (the conftest refuses unregistered files — the
registration is part of the repro). Run each on its own:

```
.venv/bin/python -m pytest tests/test_c1b_shelving_partial_apply.py -q   # FAILS on base
.venv/bin/python -m pytest tests/test_c1b_probes.py -q                   # 5 passed (held attacks)
```

Nothing was committed; the clone's working tree carries both files plus the
`group_map.py` registration uncommitted, exactly as the ground rules require.

## ASSUMPTIONs

- ASSUMPTION: the six **read**-labelled verdicts above are as strong as
  stated only for the attack classes listed; I did not probe them
  empirically, and the verification pass should treat them as code-reading
  evidence, not proof.
- ASSUMPTION: `path.attachment.add`'s happy path (bytes copied under
  `scratch/paths/<id>/attachments/<stage>`) is correct as read; my probe
  stopped at the payload-dependency refusal.
- ASSUMPTION: the C1-B batch needs no `obsidian-ui` clone (no UI capability
  in these families). The ground rules' clone layout names both repos; I
  cloned Core only, following the C1-A precedent.
- The venv was built with `python3.14 -m venv .venv && .venv/bin/pip install
  -e '.[dev]'` as prescribed; `make setup` / `make hooks` were never run.
- Crash-window behaviour is asserted from the engine's journal/rollback
  design and code comments, not from a kill test (see the limit above).

## Not done, on purpose

No pushes, no commits, no CI runs, no issue filing, no fixes, no contract
edits. Verification belongs to the C1 verification pass on GLM-5.3; landing
belongs to Aram or Claude.
