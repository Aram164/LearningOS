"""Session-area converted handler: the thin `cli.session-end` facade (D7).

The D7 machine in `ops/session.py` does the work; this module only binds
its refusals to refusal sites and its results to `Result`s.
"""

from __future__ import annotations

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result
from learning_os.app.registry import register
from learning_os.app.session import SessionChannelError as _SessionChannelError
from learning_os.app.session import SessionCommittedError as _SessionCommittedError
from learning_os.app.session import SessionConflictError as _SessionConflictError
from learning_os.app.session import SessionEmptyError as _SessionEmptyError
from learning_os.app.session import SessionHeadMovedError as _SessionHeadMovedError
from learning_os.app.session import SessionLedgerError as _SessionLedgerError
from learning_os.app.session import SessionMismatchError as _SessionMismatchError
from learning_os.app.session import SessionUsageError as _SessionUsageError
from learning_os.app.session import session_end
from learning_os.domain.failures import WriteRefused


@register("session.end", kind="porcelain")
def session_end_command(ctx: OpContext, req: dict) -> Result:
    """Validate, show exact session-owned files, optionally commit/push."""
    try:
        outcome = session_end(
            ctx.root,
            channel=req.get("channel"),
            session_id=req.get("session_id"),
            include_stale=req.get("include_stale", False),
            close=req.get("close", False),
            commit_message=req.get("commit_message"),
            push=req.get("push", False),
        )
    except _SessionUsageError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.close-with-commit",
            prefixed=True, exit_code=2) from exc
    except _SessionChannelError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.unknown-channel",
            prefixed=True, exit_code=2) from exc
    except _SessionLedgerError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.unreadable-ledger",
            prefixed=True, exit_code=2) from exc
    except _SessionEmptyError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.nothing-touched",
            prefixed=True, exit_code=2) from exc
    except _SessionConflictError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.ownership-conflict",
            prefixed=True, exit_code=2) from exc
    except _SessionMismatchError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.review-invalidated",
            prefixed=True, exit_code=2) from exc
    except _SessionCommittedError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.already-committed",
            prefixed=True, exit_code=2) from exc
    except _SessionHeadMovedError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.head-changed",
            prefixed=True, exit_code=2) from exc
    return Result(outcome)
    return Result(outcome)
