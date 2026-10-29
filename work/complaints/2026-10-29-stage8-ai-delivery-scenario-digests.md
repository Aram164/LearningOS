# Exact-pair AI delivery scenarios disagree with recorded request before/after hashes

Workflow: Stage 8 hosted exact-pair acceptance; Core `455c4c165e6f5973a906d9a0457d1d9902980e9a` / UI `8e82f8a3311d05415edfb9b17c5517e652a3dd61`.

`pytest-shards (witness-0)` failed `tests/test_scenarios_effects.py::test_scenario_effects` for `ai-action.delivery.apply::apply-garden-shelve` and `ai-action.delivery.apply::exact-replay`.

Observed request row `operations/ai-actions/requests/KEY1/request.yaml`: recorded before `2b47eb2494b21d476caa725d630111818b6369e67a5cb5c7e254170735a2feee`, actual `a724b1df547b0d02e5080a5d5ea321d786ed54a70c1a9d32a6c56fc3b4980644`; recorded after `ddf2bb2b9e01776fffe36ff443c75e64421a6ce919d3308c5532a075fae8284f`, actual `2e65277fbbfa416b5244666192543bbddcc57b83277682917d46993349ce18de`. The receipt/stdout representation also differs at those hashes.

Cause is not isolated. Do not treat this as permission to regenerate recordings or weaken digest checks. Smallest follow-up: reproduce both cases in disposable fixtures, compare actual request bytes/bindings against the recorded source assumptions, and decide from that evidence whether the implementation or recordings need repair. Acceptance requires exact retry/receipt identity and both characterization cases plus hosted population checks to pass. No repair was performed during Stage 8.

Proof: [run](https://github.com/Aram164/LearningOS/actions/runs/40945395574), [job](https://github.com/Aram164/LearningOS/actions/runs/40945395574/job/123699314569); retained `stage8/witness-0.log`, `junit-verification.json` and digest-verified shard archives in the agility campaign. Environment: hosted Ubuntu, Python 3.14.4, Node 22. No original learner-vault changes or production actions.

Filed after duplicate search: https://github.com/Aram164/LearningOS/issues/77

Authorized repair follow-up: see `work/proposals/2026-10-29-agility-stage8-repair.md` and retained differential/procedure results under `workbench/agility-experiment/stage8-*`. The focused owning checks pass; final hosted acceptance belongs to the new exact-pair run.
