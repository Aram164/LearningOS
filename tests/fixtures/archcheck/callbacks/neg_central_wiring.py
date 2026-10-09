"""Negative population fixture: wiring shapes are not counted (SPEC §3.5a).

AST-scanned only. The hook-passing call inside ``commit_proposal``
counts under no exclusion and vanishes once the central-wiring
exclusion covers it; the forwarded ``None``/``"STANDARD"`` values
and the hookless call never count.
"""

from learning_os.commands.support import _write_transaction
from learning_os.ops.proposal import TransactionProposal


def _hook(root, writes):
    return []


def commit_proposal(ctx, proposal):
    return _write_transaction(
        capability="fixture.wiring",
        validate_extra=_hook,
    )


_FORWARDED = TransactionProposal(
    capability="fixture.neg",
    writes={},
    artifact_ids=(),
    validate_extra=None,
    publish="STANDARD",
    touched=None,
)

_HOOKLESS = _write_transaction(capability="fixture.neg")
