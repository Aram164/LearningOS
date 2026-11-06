"""SPIKE pytest plugin - installs the SQLite-backed store behind the production API surface.

Use:  PYTHONPATH="tools:workbench/spikes/roleb-sqlite-2026-11-06" \
        .venv/bin/pytest -p spike_swap tests/...

Loaded by pytest via -p BEFORE conftest and test collection, so every later
`from learning_os.store.derived.store import X` binds the spike functions.
The facade copies the real module namespace, overrides the persistence
functions, and is installed as the sys.modules entry AND as the package
attributes (for `from learning_os.store.derived import X` callers).
Production files are not touched; the swap lives only in this process.
"""

import sys
import types
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spike_store_sqlite as spike  # noqa: E402  (labelled spike module)
import learning_os.store.derived as _pkg  # noqa: E402
import learning_os.store.derived.store as _real  # noqa: E402

_OVERRIDDEN = (
    "read_state", "invalidate", "lookup", "stage_node_blob",
    "publish_staged_states", "store_node", "sweep_unreferenced_blobs",
)

_facade = types.ModuleType(_real.__name__)
_facade.__dict__.update(_real.__dict__)
for _name in _OVERRIDDEN:
    setattr(_facade, _name, getattr(spike, _name))
_facade.__dict__["__doc__"] = (
    "SPIKE facade: production namespace with SQLite-backed persistence "
    "(workbench/spikes/roleb-sqlite-2026-11-06, never imported by production code)")

sys.modules[_real.__name__] = _facade
for _name in _OVERRIDDEN + ("derived_dir", "state_path"):
    if hasattr(_pkg, _name):
        setattr(_pkg, _name, getattr(_facade, _name))
_pkg.store = _facade

# Rebind every ALREADY-imported module that bound the real functions before
# this plugin ran (importing the package __init__ above transitively imports
# engine.py, whose `from ...store import X` bindings would otherwise keep
# calling the real file-backed functions while tests read the DB).
_real_objs = {name: getattr(_real, name) for name in _OVERRIDDEN}
for _mod in list(sys.modules.values()):
    if _mod is None or not hasattr(_mod, "__dict__"):
        continue
    for _name, _real_fn in _real_objs.items():
        if getattr(_mod, _name, None) is _real_fn:
            setattr(_mod, _name, getattr(_facade, _name))
