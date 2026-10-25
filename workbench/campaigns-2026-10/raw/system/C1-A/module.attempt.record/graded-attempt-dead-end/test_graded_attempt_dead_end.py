"""C1-A finding: a graded attempt's result can never be corrected through the
declared capability — the sticky grade dead-ends against MOD-GRADE.

The declared invariant (``system/contracts/capabilities.yaml``,
module.attempt.record): "one module; appends a new attempts row or updates the
row for the same termin; termin, date, result and optional grade/notes record
Aram's stated exam fact". The handler (tools/learning_os/app/handlers/admin.py,
``module_attempt``) updates ``date``/``result`` unconditionally but only ever
writes ``grade`` when the request supplies one — an omitted grade keeps the
previous row's grade. The validator refuses the resulting state
(``MOD-GRADE``, tools/learning_os/derive/validation/curriculum.py): a grade on
a non-passed attempt of a non-completed module is an error.

So once a termin's row carries a grade, every future "update the row for the
same termin" that states a non-passed result is refused at commit, and no
payload of the capability can clear the grade. Boundary 16 (OPERATOR) forbids
hand-editing module.yaml, and no other capability touches attempts: the
correction is unreachable.

Expected: the correction applies (the row updates, and — since the stated fact
no longer carries a grade — the stale grade goes with it).
Observed on base main (d6c47790): the commit refuses with
"E MOD-GRADE ... carries a grade but result is 'withdrawn'".
"""

from __future__ import annotations

import yaml

from gateway_helpers import approved_v2_envelope, run_v2_capability
from repo_builders import add_curriculum


def _record_attempt(root, payload: dict, key: str):
    envelope = approved_v2_envelope(
        root, capability="module.attempt.record", payload=payload,
        artifact_ids=["module-demo"], idempotency_key=key)
    return run_v2_capability(root, envelope)


def _attempts(root):
    data = yaml.safe_load(
        (root / "curriculum/modules/module-demo/module.yaml").read_text(
            encoding="utf-8"))
    return {row["termin"]: row for row in data.get("attempts", [])}


def test_graded_attempt_result_is_correctable(mini_repo):
    root = mini_repo
    add_curriculum(root)

    # A legitimate forward flow: termin 2 was sat, termin 3 was passed
    # with a grade (dates after the fixture's 2026-10-09 sitting).
    settled = _record_attempt(
        root, {"module_id": "module-demo", "termin": 2,
               "date": "2026-10-09", "result": "sat"}, "c1a-t2-sat")
    assert settled.returncode == 0, settled.stdout[:400]
    passed = _record_attempt(
        root, {"module_id": "module-demo", "termin": 3,
               "date": "2026-11-01", "result": "passed", "grade": 2.3},
        "c1a-t3-passed")
    assert passed.returncode == 0, passed.stdout[:400]
    assert _attempts(root)[3]["grade"] == 2.3

    # The stated fact changes: the sitting was withdrawn (Rücktritt), so
    # the grade no longer applies. The capability contract says the row
    # for the same termin is *updated*; the grade is optional per fact.
    corrected = _record_attempt(
        root, {"module_id": "module-demo", "termin": 3,
               "date": "2026-11-01", "result": "withdrawn"},
        "c1a-t3-corrected")
    assert corrected.returncode == 0, (
        "module.attempt.record could not update the graded termin's result "
        "to a non-passed fact:\n" + corrected.stdout[:500]
    )
    row = _attempts(root)[3]
    assert row["result"] == "withdrawn"
    assert "grade" not in row, f"stale grade survived the correction: {row}"
