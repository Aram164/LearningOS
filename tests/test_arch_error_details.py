"""Core's own response validation enforces the typed D3 details (SPEC 9.3)."""

from __future__ import annotations

import pytest

from learning_os.commands.capability import _validate_capability_envelope
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
