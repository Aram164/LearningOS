"""Outcome table equals today's branches (SPEC §9.1).

Every row of ``ops.outcomes.TABLE`` is compared against a test-local copy
of the pre-change function or branch body it transcribes (pasted from
``git show main:…``; line numbers cite that base) on code, retryable,
exit, details and close. ``main`` here is the S11 base: the literals below
are the pre-A14 spellings, deliberately.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learning_os.app.backup_manifest import BackupManifestError
from learning_os.app.outcomes import TABLE, classify, error_object, exit_for, resolve
from learning_os.app.outcomes import refusal_from_failure as _refusal_from_failure
from learning_os.app.pipeline import (
    _classify_failure,
    _post_commit_error,
    _projection_error,
)
from learning_os.derive.health import HealthReportError
from learning_os.derive.masters_catalog import MastersPlanningError
from learning_os.derive.material_synthesis import MaterialSynthesisError
from learning_os.domain.ai_errors import AIActionError, StaleDeliveryError
from learning_os.domain.failures import (
    MalformedId,
    NotFound,
    PostCommitFailure,
    ProjectionFailure,
    ReplayEvidenceError,
    StaleSnapshot,
    TransactionConflict,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionRecoveryConflict,
    TransactionRollbackIncomplete,
    TransactionScopeError,
    TransactionSnapshotConflict,
    TransactionValidationFailure,
    WriteRefused,
)
from learning_os.domain.failures import ReplayRecoveryError as _ReplayRecoveryError
from learning_os.store.contracts.manifest_contract import ManifestContractError
from learning_os.store.contracts.write_scopes import WriteScopeError
from learning_os.store.layout import PathBoundaryError
from learning_os.store.legacy_archive import LegacyArchiveError

# ---------------------------------------------------------------------------
# Old copies, pasted from git show main:… (S11 base, pre-A14 literals).
# ---------------------------------------------------------------------------

# main:tools/learning_os/commands/capability.py:473-480
def _old_gateway_error(code, message, *, retryable=False, details=None):
    return {
        "code": code,
        "message": message,
        "retryable": retryable,
        "details": dict(details or {}),
    }


# main:tools/learning_os/commands/support.py:496-528
def _old_refusal_from_failure(failure):
    if isinstance(failure, WriteRefused):
        return (failure.gateway_code, failure.gateway_retryable)
    if isinstance(failure, TransactionConflict):
        return ("REVISION_CONFLICT", True)
    if isinstance(failure, TransactionSnapshotConflict):
        return ("STALE_SNAPSHOT", True)
    if isinstance(failure, TransactionIdempotencyConflict):
        return ("IDEMPOTENCY_CONFLICT", False)
    if isinstance(failure, (ReplayEvidenceError, TransactionRecoveryConflict)):
        return ("INTERNAL_FAILURE", False)
    if isinstance(failure, TransactionScopeError):
        return ("OUT_OF_SCOPE", False)
    if isinstance(failure, TransactionValidationFailure):
        return ("VALIDATION_FAILED", False)
    if isinstance(failure, TransactionRollbackIncomplete):
        return ("INTERNAL_FAILURE", True)
    if isinstance(failure, TransactionFailure):
        if failure.pre_existing_defect:
            return ("VALIDATION_FAILED", False)
        return None
    if isinstance(failure, (WriteScopeError, PathBoundaryError)):
        return ("OUT_OF_SCOPE", False)
    return None


# main:tools/learning_os/commands/capability.py:483-505
def _old_classify_failure(code, message, *,
                           failure=None, refusal=None):
    if refusal is not None:
        refused_code, retryable = refusal
        return _old_gateway_error(refused_code, message, retryable=retryable)
    if failure is not None:
        mapped = _old_refusal_from_failure(failure)
        if mapped is not None:
            refused_code, retryable = mapped
            return _old_gateway_error(refused_code, message, retryable=retryable)
    return _old_gateway_error("INVALID_REQUEST", message)


# main:tools/learning_os/commands/capability.py:508-515
def _old_v2_exit_code(handler_code, error):
    if error is not None and error.get("code") == "STALE_SNAPSHOT":
        return 3
    return handler_code


# main:tools/learning_os/commands/capability.py:518-537
def _old_projection_error(exc):
    if exc.rollback_complete:
        if exc.pre_existing_defect:
            return _old_gateway_error(
                "VALIDATION_FAILED", str(exc), retryable=False,
                details={"stage": "core.projection", "rollback_complete": True,
                         "pre_existing_defect": True})
        return _old_gateway_error(
            "PROJECTION_FAILED", str(exc), retryable=True,
            details={"stage": "core.projection", "rollback_complete": True})
    return _old_gateway_error(
        "INTERNAL_FAILURE", str(exc), retryable=True,
        details={"stage": "core.projection", "rollback_complete": False})


# main:tools/learning_os/commands/capability.py:540-544
def _old_post_commit_error(exc):
    return _old_gateway_error(
        "INTERNAL_FAILURE", str(exc), retryable=True,
        details={"stage": "core.commit", "committed": True})


def _old_recovery_details(exc):
    # main:tools/learning_os/commands/capability.py:1110-1119 and 1247-1256
    # (the two branches build the identical dict).
    return {
        "transaction_id": exc.transaction_id,
        "conflicting_paths": [
            entry.get("path") for entry in exc.conflicts
        ],
        "reasons": sorted({
            entry.get("reason") for entry in exc.conflicts
            if entry.get("reason")
        }),
    }


def _old_replay_outcome(exc):
    """One replay branch decision (main:capability.py:1072-1137)."""
    replay_close = {"stage": "core.replay"}
    if isinstance(exc, TransactionIdempotencyConflict):
        error = _old_gateway_error("IDEMPOTENCY_CONFLICT", str(exc))
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"], "close": replay_close}
    if isinstance(exc, (ReplayEvidenceError, _ReplayRecoveryError)):
        error = _old_gateway_error("INTERNAL_FAILURE", str(exc),
                                   retryable=False)
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"], "close": replay_close}
    if isinstance(exc, TransactionRecoveryConflict):
        error = _old_gateway_error(
            "INTERNAL_FAILURE", str(exc), retryable=False,
            details=_old_recovery_details(exc))
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"], "close": replay_close}
    if isinstance(exc, TransactionFailure):
        error = _old_gateway_error("INTERNAL_FAILURE", str(exc),
                                   retryable=True)
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"], "close": replay_close}
    return None


def _old_dispatch_outcome(exc):
    """One dispatch branch decision (main:capability.py:1195-1303)."""
    if isinstance(exc, WriteRefused):
        return _old_dispatch_defer(exc)
    if isinstance(exc, TransactionSnapshotConflict):
        error = _old_gateway_error(
            "STALE_SNAPSHOT",
            "canonical state changed before the transaction write window",
            retryable=True,
            details={"expected": exc.expected, "actual": exc.actual})
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 3, "details": error["details"],
                "close": {"stage": "core.snapshot_guard"}}
    if isinstance(exc, ProjectionFailure):
        error = _old_projection_error(exc)
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"],
                "close": {"stage": "core.projection"}}
    if isinstance(exc, PostCommitFailure):
        error = _old_post_commit_error(exc)
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"],
                "close": {"stage": "core.commit"}}
    if isinstance(exc, TransactionRecoveryConflict):
        error = _old_gateway_error(
            "INTERNAL_FAILURE", str(exc), retryable=False,
            details=_old_recovery_details(exc))
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"],
                "close": {"code": "INTERNAL_FAILURE"}}
    if isinstance(exc, TransactionFailure):
        return _old_dispatch_defer(exc)
    if isinstance(exc, ValueError):
        return _old_dispatch_defer(exc)
    if isinstance(exc, Exception):
        error = _old_gateway_error(
            "INTERNAL_FAILURE", str(exc) or type(exc).__name__,
            retryable=True)
        return {"code": error["code"], "retryable": error["retryable"],
                "exit": 2, "details": error["details"],
                "close": {"code": "INTERNAL_FAILURE"}}
    return None


def _old_dispatch_defer(exc):
    """The shared defer tail (main:capability.py:1281-1303, code 2)."""
    # On the exception path result is {"error": str(exc)}: no carried
    # error_code, so refusal is None and the complaint is str(exc).
    error = _old_classify_failure(2, str(exc), failure=exc, refusal=None)
    return {"code": error["code"], "retryable": error["retryable"],
            "exit": _old_v2_exit_code(2, error), "details": error["details"],
            "close": {}}


def _old_cli_exit(exc):
    """tools/los.py main's except chain (main:tools/los.py:1387-1425)."""
    if isinstance(exc, StaleDeliveryError):
        return 3
    if isinstance(exc, AIActionError):
        return 1
    if isinstance(exc, StaleSnapshot):
        return 3
    if isinstance(exc, WriteRefused):
        return 2
    if isinstance(exc, TransactionFailure):
        return 2
    if isinstance(exc, (MaterialSynthesisError, LegacyArchiveError,
                        MastersPlanningError, BackupManifestError,
                        HealthReportError)):
        return 2
    if isinstance(exc, ManifestContractError):
        return 2
    return None


# ---------------------------------------------------------------------------
# Case batteries.
# ---------------------------------------------------------------------------

def _conflicts():
    return [{"path": "a/b.md", "reason": "DIVERGED_FROM_TRANSACTION"},
            {"path": "c.md", "reason": "BACKUP_HASH_MISMATCH"},
            {"path": "d.md"}]


REFUSAL_CASES = [
    WriteRefused("w"),
    StaleSnapshot("s"),
    NotFound("unit", "unit-9", ["unit-1"]),
    MalformedId("unit", "unit-!"),
    TransactionConflict({"a": (1, 2)}),
    TransactionSnapshotConflict("e", "a"),
    TransactionIdempotencyConflict("i"),
    ReplayEvidenceError("r"),
    TransactionRecoveryConflict("r", transaction_id="t",
                                conflicts=_conflicts()),
    TransactionScopeError("s"),
    TransactionValidationFailure("v"),
    TransactionRollbackIncomplete("r"),
    TransactionFailure("t"),
    TransactionFailure("t", pre_existing_defect=True),
    ProjectionFailure("p", rollback_complete=True,
                      pre_existing_defect=True),
    ProjectionFailure("p", rollback_complete=False),
    PostCommitFailure("p", transaction_id="t", receipt_path="r",
                      snapshot_after="s"),
    WriteScopeError("w"),
    PathBoundaryError("p"),
    ValueError("v"),
    KeyError("k"),
]

REPLAY_CASES = [
    TransactionIdempotencyConflict("i"),
    ReplayEvidenceError("r"),
    _ReplayRecoveryError("r"),
    TransactionRecoveryConflict("r", transaction_id="t",
                                conflicts=_conflicts()),
    TransactionRecoveryConflict("r2", transaction_id="t2", conflicts=[]),
    TransactionFailure("t"),
    TransactionFailure("t", pre_existing_defect=True),
    TransactionValidationFailure("v"),
]

DISPATCH_CASES = [
    TransactionSnapshotConflict("e", "a"),
    ProjectionFailure("p", rollback_complete=True,
                      pre_existing_defect=True),
    ProjectionFailure("p", rollback_complete=True,
                      pre_existing_defect=False),
    ProjectionFailure("p", rollback_complete=False,
                      pre_existing_defect=True),
    ProjectionFailure("p", rollback_complete=False,
                      pre_existing_defect=False),
    PostCommitFailure("p", transaction_id="t", receipt_path="r",
                      snapshot_after="s"),
    TransactionRecoveryConflict("r", transaction_id="t",
                                conflicts=_conflicts()),
    WriteRefused("w"),
    StaleSnapshot("s"),
    NotFound("unit", "unit-9", ["unit-1"]),
    TransactionFailure("t"),
    TransactionFailure("t", pre_existing_defect=True),
    TransactionIdempotencyConflict("i"),
    TransactionScopeError("s"),
    TransactionValidationFailure("v"),
    TransactionRollbackIncomplete("r"),
    ValueError("v"),
    WriteScopeError("w"),
    RuntimeError("r"),
    RuntimeError(""),
    OSError("os"),
    KeyError("k"),
]

CLI_CASES = [
    StaleDeliveryError("s"),
    AIActionError("a"),
    StaleSnapshot("s"),
    WriteRefused("w"),
    NotFound("unit", "unit-9", ["unit-1"]),
    TransactionFailure("t"),
    TransactionFailure("t", pre_existing_defect=True),
    TransactionSnapshotConflict("e", "a"),
    ProjectionFailure("p", rollback_complete=False),
    MaterialSynthesisError("m"),
    LegacyArchiveError("l"),
    MastersPlanningError("m"),
    BackupManifestError("b"),
    HealthReportError("h"),
    ManifestContractError("m"),
    RuntimeError("r"),
    ValueError("v"),
]


def _resolved_or_none(exc, context):
    row = classify(exc, context)
    if row is None:
        return None
    return resolve(row, exc)


def test_table_contexts_are_complete():
    assert [row.context for row in TABLE] == (
        ["gateway.refusal"] * 12 + ["gateway.replay"] * 4
        + ["gateway.dispatch"] * 9 + ["cli"] * 7)


def test_refusal_rows_match_old_helper():
    for exc in REFUSAL_CASES:
        old = _old_refusal_from_failure(exc)
        row = classify(exc, "gateway.refusal")
        if old is None:
            assert row is None or resolve(row, exc)["code"] is None, exc
            continue
        assert row is not None, exc
        resolved = resolve(row, exc)
        assert (resolved["code"], resolved["retryable"]) == old, exc
        assert resolved["exit"] == 2, exc
        assert resolved["details"] is None, exc
        assert resolved["close"] is None, exc


def test_replay_rows_match_old_branches():
    for exc in REPLAY_CASES:
        assert _resolved_or_none(exc, "gateway.replay") == (
            _old_replay_outcome(exc)), exc
    assert classify(WriteRefused("w"), "gateway.replay") is None
    assert classify(ValueError("v"), "gateway.replay") is None
    assert exit_for(TransactionFailure("t"), "gateway.replay") == 2


def test_dispatch_rows_match_old_branches():
    for exc in DISPATCH_CASES:
        assert _resolved_or_none(exc, "gateway.dispatch") == (
            _old_dispatch_outcome(exc)), exc
    assert classify(KeyboardInterrupt(), "gateway.dispatch") is None
    assert exit_for(KeyboardInterrupt(), "gateway.dispatch") is None
    assert exit_for(StaleSnapshot("s"), "gateway.dispatch") == 3
    assert exit_for(WriteRefused("w"), "gateway.dispatch") == 2
    assert exit_for(RuntimeError("r"), "gateway.dispatch") == 2


def test_cli_rows_match_old_chain():
    for exc in CLI_CASES:
        row = classify(exc, "cli")
        old_exit = _old_cli_exit(exc)
        if old_exit is None:
            assert row is None, exc
            assert exit_for(exc, "cli") is None, exc
            continue
        assert row is not None, exc
        resolved = resolve(row, exc)
        assert resolved["exit"] == old_exit, exc
        assert resolved["code"] is None, exc
        assert resolved["details"] is None, exc
        assert resolved["close"] is None, exc
        assert exit_for(exc, "cli") == old_exit, exc


def test_replaced_helpers_match_old_copies():
    for exc in REFUSAL_CASES:
        assert _refusal_from_failure(exc) == (
            _old_refusal_from_failure(exc)), exc
    for exc in REFUSAL_CASES + [None]:
        message = "complaint" if exc is None else str(exc)
        new = _classify_failure(2, message, failure=exc, refusal=None)
        old = _old_classify_failure(2, message, failure=exc, refusal=None)
        if isinstance(exc, WriteRefused) and exc.reason is not None:
            # S14 D3: specified enrichment; prove it is purely additive.
            stripped = dict(new)
            stripped["details"] = {
                key: value for key, value in new["details"].items()
                if key not in ("reason", "suggestions", "remedy")}
            assert stripped == old, exc
        else:
            assert new == old, exc
    from learning_os.domain.failures import Refusal

    assert _classify_failure(2, "m", failure=None,
                             refusal=Refusal("STALE_SNAPSHOT", True)) == (
        _old_classify_failure(2, "m", failure=None,
                              refusal=("STALE_SNAPSHOT", True)))
    for rollback_complete in (True, False):
        for pre_existing in (True, False):
            exc = ProjectionFailure(
                "p", rollback_complete=rollback_complete,
                pre_existing_defect=pre_existing)
            assert _projection_error(exc) == _old_projection_error(exc), exc
    exc = PostCommitFailure("p", transaction_id="t", receipt_path="r",
                            snapshot_after="s")
    assert _post_commit_error(exc) == _old_post_commit_error(exc)


def test_explicit_source_exit_overrides():
    cli_row = classify(WriteRefused("w", exit_code=3), "cli")
    assert resolve(cli_row, WriteRefused("w", exit_code=3))["exit"] == 3
    stale_row = classify(StaleSnapshot("s", exit_code=2), "cli")
    assert resolve(stale_row, StaleSnapshot("s", exit_code=2))["exit"] == 2
    defer_row = classify(StaleSnapshot("s", exit_code=2), "gateway.dispatch")
    assert resolve(defer_row,
                   StaleSnapshot("s", exit_code=2))["exit"] == 2
    assert exit_for(WriteRefused("w", exit_code=3), "cli") == 3


def test_explicit_gateway_message_replaces_raw_message():
    exc = WriteRefused("raw complaint", gateway_message="los: old complaint")
    error = _classify_failure(2, "raw complaint", failure=exc, refusal=None)
    assert error["message"] == "los: old complaint"
    assert error["code"] == "INVALID_REQUEST"
    assert error["retryable"] is False
    plain = _classify_failure(2, "raw complaint",
                              failure=WriteRefused("raw complaint"),
                              refusal=None)
    assert plain["message"] == "raw complaint"


def test_cli_unlisted_exception_propagates(monkeypatch, capsys):
    import los

    boom = RuntimeError("boom")

    def raiser(args):
        raise boom

    monkeypatch.setattr(
        los, "build_parser",
        lambda: SimpleNamespace(
            parse_args=lambda: SimpleNamespace(func=raiser,
                                               lock_timeout=None)))
    with pytest.raises(RuntimeError, match="boom"):
        los.main()
    assert capsys.readouterr().err == ""


def test_cli_listed_exception_returns_mapped_exit(monkeypatch, capsys):
    import los

    def run(exc):
        def raiser(args):
            raise exc

        monkeypatch.setattr(
            los, "build_parser",
            lambda: SimpleNamespace(
                parse_args=lambda: SimpleNamespace(func=raiser,
                                                   lock_timeout=None)))
        return los.main()

    assert run(StaleSnapshot("stale")) == 3
    assert capsys.readouterr().err == "los: stale\n"
    assert run(AIActionError("ai")) == 1
    assert run(WriteRefused("w")) == 2


def test_explicit_falsy_metadata_is_an_override_not_absence():
    """(ac): exit_code=0 and gateway_message='' are explicit overrides —
    the checks test None-ness, not truthiness."""
    assert exit_for(WriteRefused("w", exit_code=0), "cli") == 0
    assert exit_for(StaleSnapshot("s", exit_code=0), "cli") == 0
    assert exit_for(WriteRefused("w", exit_code=0),
                    "gateway.dispatch") == 0
    assert exit_for(StaleSnapshot("s", exit_code=0),
                    "gateway.dispatch") == 0
    error = _classify_failure(
        2, "raw complaint",
        failure=WriteRefused("raw complaint", gateway_message=""),
        refusal=None)
    assert error["message"] == ""
    assert error["code"] == "INVALID_REQUEST"
    assert error["retryable"] is False


def test_error_object_add_only_merge():
    """SPEC 9.2: pre-existing keys survive; new keys added only when set."""

    error = error_object(
        "INVALID_REQUEST", "nope", retryable=False,
        details={"stage": "core.projection", "committed": True, "other": 1},
        reason="NOT_FOUND")
    assert error == {
        "code": "INVALID_REQUEST", "message": "nope", "retryable": False,
        "details": {"stage": "core.projection", "committed": True,
                    "other": 1, "reason": "NOT_FOUND"},
    }
    bare = error_object("X", "m", retryable=True)
    assert bare == {"code": "X", "message": "m", "retryable": True,
                    "details": {}}
    same = error_object("X", "m", retryable=False,
                        details={"reason": "NOT_FOUND"}, reason="NOT_FOUND")
    assert same["details"] == {"reason": "NOT_FOUND"}


def test_error_object_conflicting_key_raises():
    """SPEC 9.2: a details entry colliding with a new key is a bug."""

    with pytest.raises(AssertionError):
        error_object("X", "m", retryable=False,
                     details={"reason": "NOT_FOUND"}, reason="MALFORMED_ID")
    with pytest.raises(AssertionError):
        error_object("X", "m", retryable=False,
                     details={"suggestions": ["a"]}, suggestions=["b"])
    with pytest.raises(AssertionError):
        error_object("X", "m", retryable=False,
                     details={"remedy": "a"}, remedy="b")


def test_classify_failure_passes_refusal_details():
    """SPEC 9.2: a reason-carrying WriteRefused enriches the error."""

    failure = NotFound("unit", "u-missing", ["u-alpha", "u-beta"])
    error = _classify_failure(2, str(failure), failure=failure)
    assert error["code"] == "INVALID_REQUEST"
    assert error["details"]["reason"] == "NOT_FOUND"
    assert error["details"]["suggestions"] == failure.suggestions
    assert "remedy" not in error["details"]

    malformed = MalformedId("unit", "???")
    error = _classify_failure(2, str(malformed), failure=malformed)
    assert error["details"] == {"reason": "MALFORMED_ID"}

    plain = WriteRefused("plain refusal")
    error = _classify_failure(2, str(plain), failure=plain)
    assert error["details"] == {}
