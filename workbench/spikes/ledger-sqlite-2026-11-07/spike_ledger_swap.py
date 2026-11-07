"""Pytest plugin to swap in the SQLite-backed ledger and evidence verifier.

Use:
    PYTHONPATH="tools:workbench/spikes/ledger-sqlite-2026-11-07" \
        .venv/bin/pytest -p spike_ledger_swap tests/test_evidence_parity.py ...

Swaps verify_committed_evidence, replay_for_request, shared_ledgers_proven_since,
load_revisions, and artifact_revision in-process. Production files remain untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import learning_os.store.evidence as _evidence  # noqa: E402
import learning_os.store.revisions as _revisions  # noqa: E402
import spike_receipt_verifier as _spike  # noqa: E402

_REPLACEMENTS = {
    (_evidence, "verify_committed_evidence"): _spike.verify_committed_evidence_sql,
    (_evidence, "replay_for_request"): _spike.replay_for_request_sql,
    (_evidence, "shared_ledgers_proven_since"): _spike.shared_ledgers_proven_since_sql,
    (_revisions, "load_revisions"): _spike.load_revisions_sql,
    (_revisions, "artifact_revision"): _spike.artifact_revision_sql,
}

for (mod, attr), new_fn in _REPLACEMENTS.items():
    orig_fn = getattr(mod, attr)
    setattr(mod, attr, new_fn)
    # Rebind in already imported modules
    for m in list(sys.modules.values()):
        if m is not None and hasattr(m, "__dict__"):
            if getattr(m, attr, None) is orig_fn:
                setattr(m, attr, new_fn)
