"""SPIKE pytest plugin - installs the route-guard-unified references module.

Use:  PYTHONPATH="tools:workbench/spikes/route-guard-2026-11-06" \
        .venv/bin/pytest -p spike_guard_swap tests/test_manifest_routes.py ...

Loaded by pytest via -p BEFORE conftest and test collection, so
core.py's `from learning_os.derive.validation.references import
ChecksReferences` binds the spike mixin. spike_references.py is a full copy
of production references.py whose ONLY changes are the guard unification
(diff against production is committed next to this plugin). Production files
are not touched; the swap lives only in this process.
"""

import sys
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spike_references  # noqa: E402  (full module copy, unified guard helper)

sys.modules["learning_os.derive.validation.references"] = spike_references
try:  # patch the package attribute too, if the validation package carries one
    import learning_os.derive.validation as _pkg  # noqa: E402
    if hasattr(_pkg, "references"):
        _pkg.references = spike_references
except Exception:
    pass
