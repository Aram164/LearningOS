"""Negative population fixture: wiring shapes are not counted (SPEC §3.5a).

AST-scanned only. The hook-passing call inside ``commit_proposal``
counts under no exclusion and vanishes once the central-wiring
exclusion covers it; the forwarded ``None``/``"STANDARD"`` values
and the hookless call never count.
"""

from learning_os.app.proposal import TransactionProposal


def _hook(root, writes):
    return []


def commit_proposal(ctx, proposal):
    return TransactionProposal(
        capability="fixture.wiring",
        writes={},
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

_HOOKLESS = TransactionProposal(capability="fixture.neg", writes={})
