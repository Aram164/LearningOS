# operation-handlers

## Purpose

Translate each operation family into read results or bounded write proposals.

## Owned paths

- `tools/learning_os/app/handlers/*`

## Entry points

- `tools/learning_os/app/handlers/reads.py::bootstrap`

## Depends on and used by

<!-- system-map:begin name=edges -->
Depends on: `ai-delivery`, `backup`, `contracts`, `derived-store`, `diagnostics`, `domain`, `learner-derivations`, `legacy-archive`, `loading`, `masters-planning`, `materials`, `operation-pipeline`, `package-root`, `plan-gate`, `projection`, `search`, `semantics`, `session-ledger`, `transactions`.

Used by: `operation-pipeline`.
<!-- system-map:end -->

## Invariants

- Handlers must use proposals and shared commit, never a private canonical writer. Pinning: `tests/test_capability_dispatch.py`.

| Family module | Responsibility |
|---|---|
| `_shared.py` | Shared lookup/refusal helpers |
| `admin.py` | Module, program and administrative records |
| `ai.py` | AI request preparation, validation and delivery |
| `atlas.py` | Concept context, relation edits and questions |
| `capture.py` | Captures, inbox, Garden and shelving |
| `goals.py` | Attention decisions and review queue |
| `learner.py` | Study progress, notes and detours |
| `learner_observations.py` | Attempts, stage results and ability observations |
| `maps.py` | Study-map template and map import |
| `materials.py` | Plan context, material context and spans |
| `note_analysis.py` | Analysis-note preparation and saving |
| `notes.py` | Durable note creation, revision and evidence |
| `passthrough.py` | In-process validation and generation commands |
| `plan.py` | Material-plan import, revisions and reads |
| `platform.py` | Shared record inspection |
| `reads.py` | Bootstrap, status, discovery and bounded lists |
| `resume.py` | Resume view and dossier |
| `routes.py` | Route patches and material compaction |
| `session.py` | Session closure facade |
| `sources.py` | Source intake, revision and collection entries |
| `synthesis.py` | Material-synthesis publication and lineage restamp |

## Pinning tests

- `tests/test_capability_dispatch.py`

## Binding ADRs

- `system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md`
