# Source-less practice rows are refused on a plan revision

Task: revising `module-job-polars` through `module-plan-import` on 2026-11-02, tested at Core `aa692f4`.

Observed: a new stage row with `kind: practise` and no `source_id`, such as "Exercise 1" with a task
description, raises `RESOURCE-SCOPE-UNBOUND` ("material without a source"). On an existing map that is a grown
warning signature, so the preflight refuses the package. The new unit went 0 → 25. The same text passes with
`kind: reference`, because that kind is exempt (`tools/learning_os/derive/validation/plan_rigor.py`,
`_check_row_scope`).

Inference: to pass, an agent must label a task as a reference. The label is then false, and `kind` is meant to
carry the row's meaning. The module already carries such rows inside its baseline, so only new ones are stopped.

Safety benefit to keep: the rule catches teaching material that claims no adopted source. A row that names a
material must still need a route.

Smallest improvement to investigate: exempt `kind: practise` rows that name no `source_id`, `url` or
`vault_path`, since they cite no material.

Filed: https://github.com/Aram164/LearningOS/issues/94
