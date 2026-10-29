# Stage 5 — proportional structural editing

The experimental milestone implements stable-ID stage movement and resource
insertion/movement through Core and Obsidian's **Adjust study plan** dialog.
The dialog renders Core's exact before/after order and resource changes, then
requires an explicit Apply; editing any control invalidates the review, including
checks that finish late. It uses the existing map-import gateway and persisted
recovery path, with no new capability or admission widening.

Compact module imports also support new Unit/map/route additions and relative
Unit movement. They derive unchanged routing and numeric Unit orders internally,
retain the existing coverage audit, claim evidence and operator review, and show
exact file diffs plus the resulting Unit order. Unit additions/order remain on
that operator-reviewed file path; this milestone adds direct Obsidian controls
for stage/resource changes only. No academic scope is inferred by the interface.

## Verified behavior

- Preflight writes no canonical data; apply is bound to the exact file digest,
  snapshot and artifact revisions. Changed intent, stale snapshots/revisions,
  ambiguous/missing/self anchors, ID collisions and no-op moves refuse.
- Stage/resource IDs, progress, current stage, shared material references,
  working notes, attachments, resource feedback and global resume state survive.
  Resource movement stays inside its owning stage. Apply produces one receipt;
  exact replay produces no second receipt. Injected publication failure rolls
  back the structural edit and produces no receipt.
- Unit addition reproduces no existing route/map in its draft; old Units/maps
  are preserved. Unit movement changes only the module order and numeric Unit
  order fields. New IDs cannot overwrite existing Units or maps.
- The original checkout's seven protected hashes remain unchanged. No learner
  Unit, map, today's sequence, installation or production migration was used
  to demonstrate the controls.

## Focused evidence

The combined owning run passed 209 Core cases across material editing, compact
revision, curriculum, runtime-review and shared transactions. The additional
injected structural rollback case passed. Architecture/layer/ratchet/surface,
ID and JSON gates passed 124 cases. The new refusal witnesses and changed
compact-empty diagnostic passed their owning six-case recheck; the other 167
selected module/map characterization and site checks passed before that repair.
Full UI `npm run check` passed, including the exact-order, invalidation and
late-check controls. Ruff, maintained mypy (19 files), import boundaries,
reachability, system map and whitespace checks passed. Validation reported zero
errors; baseline-managed warnings remain 964 across 32 signatures, with no new
or grown signature. Operational/local-attachment advisories remain visible.

The retained benchmark's initial Stage 5 run measured stage-move drafts at
184 bytes on each of 2/10/50 stages, compared with the retained original
1,672/7,285/35,525 bytes; no unchanged stage record is reproduced. Compact Unit
addition measured 2,943 bytes versus 3,464 and reproduces no existing route.
Resource append stays at 768 bytes. Every measured preflight wrote zero
canonical data and every apply produced one receipt. Structural preflight now
validates the resulting shadow, so stage movement uses two validations instead
of the original path's one; this milestone claims proportional input, not a
latency, model-token or monetary improvement. Clean-commit reproduction and
provenance are retained in `workbench/agility-experiment/` after implementation.

## Boundary

Aram narrowed this continuation to finishing the current milestone. Stage 5 is
the completed implementation milestone; Stages 6–8 are deferred. The complete
combined exact-pair campaign acceptance belongs to Stage 8. Automatic branch CI
is separate evidence and will be followed to completion after this milestone's
push. No merge, installation, live Obsidian acceptance, paid-model trial or
production-vault migration is claimed.
