Observed during the authorized LearningOS clutter cleanup on 2026-10-22. Core commit: `1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
The umbrella project inventory `LearningOS/projects/README.md` still lists Stratum at `../../Job/stratum/` and describes old compatibility paths as usable. Resolving its listed Stratum path produces a nonexistent directory. The current `LearningOS/README.md`, workspace AGENTS instruction and Core perimeter instead identify Stratum as the independent external sibling `semestercontext/Stratum/`.

This creates conflicting guidance during dependency and cleanup audits: following the stale inventory cannot locate the project and blurs the external-repository boundary.

## Reproduction and proof
1. Read the Stratum row and compatibility-path paragraph of `LearningOS/projects/README.md`.
2. Resolve its listed relative location from that document's directory: the path does not exist.
3. Compare with the umbrella README and workspace instruction: the external sibling directory exists. No Stratum contents were traversed.

The inventoried document SHA-256 was `1369aaa1b5ce53357c400955e77f6cb7f55e7c0b2767b01d5bd1976c93f1c963`. Actual AMLS retained patch/PDF and PPDS recovery assets were preserved; this report does not allege they are disposable.

## Smallest improvement and acceptance
Refresh the project inventory's current locations and boundary statements while retaining useful dated migration history.

- Every location presented as current resolves correctly.
- Stratum is explicitly external and never becomes a LearningOS-managed project.
- Current inventory and historical migration claims are clearly distinguished.
- No retained source, uncommitted patch or submission archive is removed by this documentation correction.

Local audit/deletion evidence is retained under `LearningOS/workbench/cleanup-2026-10-22`; it is not assumed to be uploaded to GitHub.


## Filing status
Duplicate search found no matching issue. Aram directly approved publication on 2026-10-22. Filed: https://github.com/Aram164/LearningOS/issues/9

## Local repair — 2026-10-22
The project inventory now distinguishes current locations from dated migration history and references the external Stratum boundary. Retained AMLS/PPDS assets and their links were checked; only the Stratum directory root was inspected. Related architecture wording references existing study-map obligations and operation boundaries. Core corpus/architecture/material tests: 134 passed; lint, import layers, reachability and strict typing passed. This is a local uncommitted repair. Evidence update: https://github.com/Aram164/LearningOS/issues/9#issuecomment-6347548340
