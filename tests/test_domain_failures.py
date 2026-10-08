"""Domain failures keep every pre-existing default (SPEC §8.3, (ac), (ae)).

New ``WriteRefused``/``NotFound`` metadata is explicit-or-None: with unset
fields the exceptions behave exactly as before the move.
"""

from __future__ import annotations

from learning_os.commands import capability
from learning_os.domain import failures, suggest
from learning_os.domain.codes import (
    AMBIGUOUS_MIGRATION,
    INVALID_REQUEST,
    STALE_SNAPSHOT,
    UNCONFIRMED,
    VALIDATION_FAILED,
)


def test_write_refused_defaults_are_unset():
    exc = failures.WriteRefused("nope")
    assert str(exc) == "nope"
    assert exc.args == ("nope",)
    assert exc.site is None
    assert exc.reason is None
    assert exc.remedy is None
    assert exc.gateway_message is None
    assert exc.exit_code is None
    assert exc.gateway_code == INVALID_REQUEST
    assert exc.gateway_retryable is False


def test_write_refused_stores_explicit_metadata():
    exc = failures.WriteRefused(
        "nope", site="op.site", reason="R", remedy="fix",
        gateway_message="los: nope", exit_code=3)
    assert exc.site == "op.site"
    assert exc.reason == "R"
    assert exc.remedy == "fix"
    assert exc.gateway_message == "los: nope"
    assert exc.exit_code == 3
    assert str(exc) == "nope"


def test_preexisting_refusal_codes_are_unchanged():
    cases = [
        (failures.StaleSnapshot("s"), STALE_SNAPSHOT, True),
        (failures.AmbiguousMigration("m"), AMBIGUOUS_MIGRATION, False),
        (failures.ValidationFailed("v"), VALIDATION_FAILED, False),
        (failures.Unconfirmed("u"), UNCONFIRMED, False),
    ]
    for exc, code, retryable in cases:
        assert exc.gateway_code == code
        assert exc.gateway_retryable is retryable
        assert exc.site is None
        assert exc.reason is None
        assert exc.remedy is None
        assert exc.gateway_message is None
        assert exc.exit_code is None


def test_transaction_failure_defaults_are_preserved():
    assert failures.TransactionFailure("t").pre_existing_defect is False
    projection = failures.ProjectionFailure("p", rollback_complete=True)
    assert projection.pre_existing_defect is False
    assert projection.rollback_complete is True
    recovery = failures.TransactionRecoveryConflict("r", transaction_id="t")
    assert recovery.transaction_id == "t"
    assert recovery.conflicts == []


def test_not_found_message_reason_and_suggestions():
    candidates = ["unit-1", "unit-2", "module-9"]
    exc = failures.NotFound("unit", "unit-1x", candidates)
    assert str(exc) == suggest.not_found("unit", "unit-1x", candidates)
    assert exc.reason == "NOT_FOUND"
    assert exc.suggestions == suggest.suggestions("unit-1x", candidates)
    assert exc.gateway_code == INVALID_REQUEST
    assert exc.gateway_retryable is False
    assert exc.site is None
    assert exc.gateway_message is None
    assert exc.exit_code is None


def test_not_found_forwards_explicit_metadata():
    exc = failures.NotFound(
        "unit", "unit-1x", [], site="op.site",
        gateway_message="los: unit not found: unit-1x", exit_code=2)
    assert exc.site == "op.site"
    assert exc.gateway_message == "los: unit not found: unit-1x"
    assert exc.exit_code == 2
    assert exc.reason == "NOT_FOUND"


def test_malformed_id_fields_and_reason():
    exc = failures.MalformedId("unit", "unit-!!")
    assert exc.kind == "unit"
    assert exc.value == "unit-!!"
    assert exc.reason == "MALFORMED_ID"
    assert "unit" in str(exc)
    assert "unit-!!" in str(exc)
    assert exc.site is None
    assert exc.gateway_message is None
    assert exc.exit_code is None


def test_suggestions_returns_exactly_the_shown_ids():
    candidates = ["unit-1", "unit-2", "unit-10", "module-1", "l05", "l5x"]
    for value in ("unit-1", "l5", "zzz-no-match"):
        assert suggest.suggestions(value, candidates) == suggest.suggest(
            value, candidates)


def test_replay_recovery_error_is_one_class_object():
    assert capability._ReplayRecoveryError is failures._ReplayRecoveryError


def test_not_found_one_shot_candidates_preserve_message_and_suggestions():
    cases = [
        ("unit-", [f"unit-{i}" for i in range(8)]),
        ("unit-1x", ["unit-1", "unit-2", "module-9"]),
        ("UNIT-1", ["unit-1", "unit-10"]),
        ("zzz", []),
    ]
    for value, candidates in cases:
        expected_message = suggest.not_found("unit", value, iter(candidates))
        expected_ids = suggest.suggestions(value, iter(candidates))
        exc = failures.NotFound("unit", value, iter(candidates))
        assert str(exc) == expected_message
        assert exc.suggestions == expected_ids
        for candidate in exc.suggestions:
            assert candidate in str(exc)
        # Reiterable callers keep the pre-existing helper's exact formatting.
        listed = failures.NotFound("unit", value, candidates)
        assert str(listed) == suggest.not_found("unit", value, candidates)
        assert listed.suggestions == suggest.suggestions(value, candidates)
