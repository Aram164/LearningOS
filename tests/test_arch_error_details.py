"""Core's own response validation enforces the typed D3 details (SPEC 9.3)."""

from __future__ import annotations

import pytest

from learning_os.app.gateway import validate_capability_envelope as _validate_capability_envelope
from learning_os.domain.failures import WriteRefused


def _response(details: dict) -> dict:
    return {
        "schema_version": 2,
        "request_id": "r",
        "idempotency_key": "k",
        "capability": "capture.create",
        "ok": False,
        "replayed": False,
        "transaction_id": None,
        "receipt_path": None,
        "snapshot_after": None,
        "result": {},
        "error": {
            "code": "INVALID_REQUEST",
            "message": "m",
            "retryable": False,
            "details": details,
        },
    }


def test_empty_details_stay_valid(mini_repo):
    _validate_capability_envelope(mini_repo, _response({}), kind="result")


def test_fully_enriched_details_stay_valid(mini_repo):
    _validate_capability_envelope(
        mini_repo,
        _response({"reason": "NOT_FOUND", "suggestions": ["a", "b"],
                   "remedy": "fix it"}),
        kind="result")


def test_pre_existing_detail_keys_survive(mini_repo):
    _validate_capability_envelope(
        mini_repo,
        _response({"stage": "core.projection", "rollback_complete": True,
                   "reason": "NOT_FOUND"}),
        kind="result")


@pytest.mark.parametrize("paths, total", [([], 0), (["knowledge/note.md"], 1),
                                        (["knowledge/note.md"], 40)])
def test_projection_input_details_are_validated(mini_repo, paths, total):
    response = _response({
        "stage": "core.projection", "rollback_complete": True,
        "reason": "CANONICAL_INPUTS_CHANGED",
        "changed_paths": paths, "changed_paths_total": total,
    })
    response["error"]["code"] = "PROJECTION_FAILED"
    _validate_capability_envelope(mini_repo, response, kind="result")


@pytest.mark.parametrize("change", [
    {"reason": "CANONICAL_INPUTS_CHANGED"},
    {"changed_paths": []},
    {"changed_paths_total": 0},
    {"reason": "NOT_FOUND", "changed_paths": [], "changed_paths_total": 0},
    {"changed_paths": "knowledge/note.md", "changed_paths_total": 1},
    {"changed_paths": [""], "changed_paths_total": 1},
    {"changed_paths": ["knowledge/note.md"] * 2, "changed_paths_total": 2},
    {"changed_paths": [f"knowledge/note-{i}.md" for i in range(33)],
     "changed_paths_total": 33},
    {"changed_paths": [], "changed_paths_total": -1},
    {"changed_paths": [], "changed_paths_total": "0"},
])
def test_malformed_projection_input_details_are_refused(mini_repo, change):
    details = {"reason": "CANONICAL_INPUTS_CHANGED", **change}
    with pytest.raises(WriteRefused):
        _validate_capability_envelope(mini_repo, _response(details), kind="result")


@pytest.mark.parametrize("details", [
    {"reason": ["NOT_FOUND"]},
    {"suggestions": 5},
    {"remedy": {"x": 1}},
    {"reason": "BOGUS"},
    {"suggestions": ["ok", ""]},
    {"suggestions": ["a", "b", "c", "d", "e", "f"]},
    {"remedy": ""},
])
def test_malformed_details_refused(mini_repo, details):
    with pytest.raises(WriteRefused):
        _validate_capability_envelope(mini_repo, _response(details),
                                      kind="result")
