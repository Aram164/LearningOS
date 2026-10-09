"""Positive population fixture: a hook-passing call is counted (SPEC §3.5a).

AST-scanned only, never imported by the (a) test: the
``validate_extra`` keyword carries a real callable, so the call
counts exactly once as ``fixture.pos-hook::validate_extra``.
"""

from learning_os.ops.proposal import TransactionProposal


def _extra(root, writes):
    return []


_COUNTED = TransactionProposal(
    capability="fixture.pos-hook",
    writes={},
    artifact_ids=(),
    validate_extra=_extra,
)
