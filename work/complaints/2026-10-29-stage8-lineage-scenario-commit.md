# Lineage restamp check scenarios retain a different fixture judgment commit

Workflow: Stage 8 hosted exact-pair acceptance; Core `455c4c165e6f5973a906d9a0457d1d9902980e9a` / UI `8e82f8a3311d05415edfb9b17c5517e652a3dd61`.

`pytest-shards (witness-0)` failed `tests/test_scenarios_effects.py::test_scenario_effects` for `lineage.restamp::check-all` and `lineage.restamp::check-all-cli`.

The recorded `judgment_commit` is `9a271b3aa17e903ca91bbc4cb22d7d7834e9cd86`; actual is `67f4f3087c6307c924a0c041f7f7b6a948d03cb8`. The JSON and stdout characterization both differ. The harness commits real fixture trees; the exact causal change behind this particular commit mismatch has not been isolated.

Smallest follow-up: reproduce these two read-only check cases and establish why the judgment commit changed, preserving the real-commit existence/lineage checks. Update or repair only after proving the expected identity. Acceptance requires both CLI/gateway characterizations and the full hosted population gate to pass. No recording or implementation was modified during Stage 8.

Proof: [run](https://github.com/Aram164/LearningOS/actions/runs/40945395574), [job](https://github.com/Aram164/LearningOS/actions/runs/40945395574/job/123699314569); retained `stage8/witness-0.log`, `junit-verification.json` and digest-verified shard archives in the agility campaign. Environment: hosted Ubuntu, Python 3.14.4, Node 22. No original learner-vault changes or production actions.

Filed after duplicate search: https://github.com/Aram164/LearningOS/issues/78

Authorized repair follow-up: see `work/proposals/2026-10-29-agility-stage8-repair.md` and retained differential/procedure results under `workbench/agility-experiment/stage8-*`. The focused owning checks pass; final hosted acceptance belongs to the new exact-pair run.
