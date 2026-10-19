"""Outcome mapping: exception to public result per phase (SPEC §9.1).

Transcribed from today's branches, in today's order; nothing here changes
a result. ``gateway.refusal`` drives the replaced ``_refusal_from_failure``
and ``_classify_failure``; ``cli`` drives ``tools/los.py`` main. The
``gateway.replay`` and ``gateway.dispatch`` rows are used by S13's
``run_gateway``; until then ``cmd_capability`` keeps its own clauses.
"""

from __future__ import annotations

import contextvars
from collections.abc import Callable
from dataclasses import dataclass

from learning_os.app.backup_manifest import BackupManifestError
from learning_os.derive.health import HealthReportError
from learning_os.derive.masters_catalog import MastersPlanningError
from learning_os.derive.material_synthesis import MaterialSynthesisError
from learning_os.domain.ai_errors import AIActionError, StaleDeliveryError
from learning_os.domain.codes import (
    IDEMPOTENCY_CONFLICT,
    INTERNAL_FAILURE,
    INVALID_REQUEST,
    OUT_OF_SCOPE,
    PROJECTION_FAILED,
    REVISION_CONFLICT,
    STALE_SNAPSHOT,
    VALIDATION_FAILED,
)
from learning_os.domain.failures import (
    PostCommitFailure,
    ProjectionFailure,
    Refusal,
    ReplayEvidenceError,
    StaleSnapshot,
    TransactionConflict,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionPublicationUncertain,
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

#: The typed refusal a failed handler step recorded for the gateway.
#:
#: Handlers answer with an int exit code plus printed prose, so a typed
#: refusal caught inside a handler (a revision conflict in
#: ``_write_transaction``, a stale delivery in the AI-action handler)
#: would lose its type at that boundary. The catching step records the
#: ``(code, retryable)`` pair here instead, and the gateway dispatch
#: takes it after a non-zero return. Never reconstructed from prose or
#: from the exit code: exit 3 alone is ambiguous (a snapshot guard, a
#: revision conflict, and a stale reviewed digest all use it).
_GATEWAY_REFUSAL: contextvars.ContextVar[Refusal | None] = (
    contextvars.ContextVar("learningos_gateway_refusal", default=None)
)

def record_gateway_refusal(code: str, retryable: bool) -> None:
    """Carry one typed refusal across the handler's int-exit boundary."""
    _GATEWAY_REFUSAL.set(Refusal(code, retryable))

def take_gateway_refusal() -> Refusal | None:
    """Read and clear the recorded refusal, if any."""
    refusal = _GATEWAY_REFUSAL.get()
    _GATEWAY_REFUSAL.set(None)
    return refusal

def refusal_from_failure(failure: BaseException) -> Refusal | None:
    """Map a refusal to its V2 ``(code, retryable)`` by type, never by prose.

    Returns ``None`` for an untyped refusal, which the gateway reports as
    ``INVALID_REQUEST``. ``TransactionConflict`` and
    ``TransactionSnapshotConflict`` normally never reach this helper —
    ``_write_transaction`` records the first and re-raises the second —
    but mapping them here keeps the table total over every failure the
    gateway boundary can observe.
    """
    row = classify(failure, "gateway.refusal")
    if row is None:
        return None
    resolved = resolve(row, failure)
    if resolved["code"] is None:
        return None
    return Refusal(resolved["code"], resolved["retryable"])


Value = str | bool | int | None
Fn = Callable[[BaseException], Value]


@dataclass(frozen=True)
class Row:
    context: str
    failure: tuple[type[BaseException], ...]
    when: Callable[[BaseException], bool] | None = None
    code: str | Fn | None = None
    retryable: bool | Fn | None = None
    exit: int | Fn = 2
    details: Callable[[BaseException], dict] | None = None
    close: dict | None = None


def _empty_details(exc: BaseException) -> dict:
    """Today's error dict carries an empty details object on this branch."""
    return {}


def _recovery_details(exc: BaseException) -> dict:
    """Today's conflicting-paths details (replay and dispatch share them)."""
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


def _snapshot_details(exc: BaseException) -> dict:
    return {"expected": exc.expected, "actual": exc.actual}


def _projection_complete_defect_details(exc: BaseException) -> dict:
    return {"stage": "core.projection", "rollback_complete": True,
            "pre_existing_defect": True}


def _projection_complete_details(exc: BaseException) -> dict:
    return {"stage": "core.projection", "rollback_complete": True}


def _projection_incomplete_details(exc: BaseException) -> dict:
    return {"stage": "core.projection", "rollback_complete": False}


def _commit_details(exc: BaseException) -> dict:
    return {"stage": "core.commit", "committed": True}


def _publication_details(exc: BaseException) -> dict:
    return {"stage": "core.receipt", "publication": "uncertain"}


def _deferred_code(exc: BaseException) -> Value:
    """The ``gateway.refusal`` code for this exception, else INVALID_REQUEST."""
    row = classify(exc, "gateway.refusal")
    if row is None:
        return INVALID_REQUEST
    code = resolve(row, exc)["code"]
    return INVALID_REQUEST if code is None else code


def _deferred_retryable(exc: BaseException) -> Value:
    row = classify(exc, "gateway.refusal")
    if row is None:
        return False
    resolved = resolve(row, exc)
    if resolved["code"] is None:
        return False
    return resolved["retryable"]


def _deferred_exit(exc: BaseException) -> Value:
    """Today's ``_v2_exit_code`` on the dispatch defer path (handler code 2)."""
    if isinstance(exc, WriteRefused) and exc.exit_code is not None:
        return exc.exit_code
    return 3 if _deferred_code(exc) == STALE_SNAPSHOT else 2


def _cli_refused_exit(exc: BaseException) -> Value:
    if isinstance(exc, WriteRefused) and exc.exit_code is not None:
        return exc.exit_code
    return 2


def _cli_stale_exit(exc: BaseException) -> Value:
    if isinstance(exc, WriteRefused) and exc.exit_code is not None:
        return exc.exit_code
    return 3


TABLE: tuple[Row, ...] = (
    # gateway.refusal: _refusal_from_failure, in its order.
    Row("gateway.refusal", (WriteRefused,),
        code=lambda exc: exc.gateway_code,
        retryable=lambda exc: exc.gateway_retryable),
    Row("gateway.refusal", (TransactionConflict,),
        code=REVISION_CONFLICT, retryable=True),
    Row("gateway.refusal", (TransactionSnapshotConflict,),
        code=STALE_SNAPSHOT, retryable=True),
    Row("gateway.refusal", (TransactionIdempotencyConflict,),
        code=IDEMPOTENCY_CONFLICT, retryable=False),
    Row("gateway.refusal", (ReplayEvidenceError, TransactionRecoveryConflict),
        code=INTERNAL_FAILURE, retryable=False),
    Row("gateway.refusal", (TransactionScopeError,),
        code=OUT_OF_SCOPE, retryable=False),
    Row("gateway.refusal", (TransactionValidationFailure,),
        code=VALIDATION_FAILED, retryable=False),
    Row("gateway.refusal", (TransactionRollbackIncomplete,),
        code=INTERNAL_FAILURE, retryable=True),
    Row("gateway.refusal", (TransactionPublicationUncertain,),
        code=INTERNAL_FAILURE, retryable=True),
    Row("gateway.refusal", (TransactionFailure,),
        when=lambda exc: exc.pre_existing_defect,
        code=VALIDATION_FAILED, retryable=False),
    Row("gateway.refusal", (TransactionFailure,), code=None),
    Row("gateway.refusal", (WriteScopeError, PathBoundaryError),
        code=OUT_OF_SCOPE, retryable=False),
    # gateway.replay: cmd_capability's replay except chain, in order.
    Row("gateway.replay", (TransactionIdempotencyConflict,),
        code=IDEMPOTENCY_CONFLICT, retryable=False,
        details=_empty_details, close={"stage": "core.replay"}),
    Row("gateway.replay", (ReplayEvidenceError, _ReplayRecoveryError),
        code=INTERNAL_FAILURE, retryable=False,
        details=_empty_details, close={"stage": "core.replay"}),
    Row("gateway.replay", (TransactionRecoveryConflict,),
        code=INTERNAL_FAILURE, retryable=False,
        details=_recovery_details, close={"stage": "core.replay"}),
    Row("gateway.replay", (TransactionFailure,),
        code=INTERNAL_FAILURE, retryable=True,
        details=_empty_details, close={"stage": "core.replay"}),
    # gateway.dispatch: cmd_capability's dispatch except chain, specific
    # rows before the general defer row (SPEC §9.1 order).
    Row("gateway.dispatch", (TransactionSnapshotConflict,),
        code=STALE_SNAPSHOT, retryable=True, exit=3,
        details=_snapshot_details, close={"stage": "core.snapshot_guard"}),
    Row("gateway.dispatch", (ProjectionFailure,),
        when=lambda exc: exc.rollback_complete and exc.pre_existing_defect,
        code=VALIDATION_FAILED, retryable=False,
        details=_projection_complete_defect_details,
        close={"stage": "core.projection"}),
    Row("gateway.dispatch", (ProjectionFailure,),
        when=lambda exc: exc.rollback_complete,
        code=PROJECTION_FAILED, retryable=True,
        details=_projection_complete_details,
        close={"stage": "core.projection"}),
    Row("gateway.dispatch", (ProjectionFailure,),
        code=INTERNAL_FAILURE, retryable=True,
        details=_projection_incomplete_details,
        close={"stage": "core.projection"}),
    Row("gateway.dispatch", (PostCommitFailure,),
        code=INTERNAL_FAILURE, retryable=True,
        details=_commit_details, close={"stage": "core.commit"}),
    Row("gateway.dispatch", (TransactionPublicationUncertain,),
        code=INTERNAL_FAILURE, retryable=True,
        details=_publication_details, close={"stage": "core.receipt"}),
    Row("gateway.dispatch", (TransactionRecoveryConflict,),
        code=INTERNAL_FAILURE, retryable=False,
        details=_recovery_details, close={"code": INTERNAL_FAILURE}),
    Row("gateway.dispatch", (WriteRefused, TransactionFailure, ValueError),
        code=_deferred_code, retryable=_deferred_retryable,
        exit=_deferred_exit, details=_empty_details, close={}),
    Row("gateway.dispatch", (Exception,),
        code=INTERNAL_FAILURE, retryable=True,
        details=_empty_details, close={"code": INTERNAL_FAILURE}),
    # cli: tools/los.py main's except chain, in order. No catch-all row:
    # classify returns None and the caller re-raises.
    Row("cli", (StaleDeliveryError,), exit=3),
    Row("cli", (AIActionError,), exit=1),
    Row("cli", (StaleSnapshot,), exit=_cli_stale_exit),
    Row("cli", (WriteRefused,), exit=_cli_refused_exit),
    Row("cli", (TransactionFailure,), exit=2),
    Row("cli", (MaterialSynthesisError, LegacyArchiveError,
                MastersPlanningError, BackupManifestError,
                HealthReportError), exit=2),
    Row("cli", (ManifestContractError,), exit=2),
)


def classify(exc: BaseException, context: str) -> Row | None:
    """First matching row in TABLE order, else None."""
    for row in TABLE:
        if row.context != context:
            continue
        if not isinstance(exc, row.failure):
            continue
        if row.when is not None and not row.when(exc):
            continue
        return row
    return None


def resolve(row: Row, exc: BaseException) -> dict:
    """The row's outcome with callables applied."""
    code = row.code(exc) if callable(row.code) else row.code
    retryable = row.retryable(exc) if callable(row.retryable) else row.retryable
    exit = row.exit(exc) if callable(row.exit) else row.exit
    details = row.details(exc) if row.details is not None else None
    return {"code": code, "retryable": retryable, "exit": exit,
            "details": details, "close": row.close}


def exit_for(exc: BaseException, context: str) -> int | None:
    row = classify(exc, context)
    if row is None:
        return None
    return resolve(row, exc)["exit"]


def error_object(code, message, *, retryable, details=None, reason=None,
                 suggestions=None, remedy=None) -> dict:
    """Build one V2 error object, merging optional typed details (SPEC 9.2).

    `details` is copied; `reason`, `suggestions` and `remedy` are added only
    when not None. A `details` entry for one of those three keys with a
    different value is a programming error (AssertionError); every other
    pre-existing key survives untouched.
    """

    merged = dict(details) if details else {}
    for key, value in (("reason", reason), ("suggestions", suggestions),
                       ("remedy", remedy)):
        if value is None:
            continue
        if key in merged and merged[key] != value:
            raise AssertionError(f"error details conflict for {key!r}")
        merged[key] = value
    return {"code": code, "message": message, "retryable": retryable,
            "details": merged}
