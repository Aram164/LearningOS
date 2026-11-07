"""Pytest plugin to transparently swap in SQLite FTS5 search.

Use:
    PYTHONPATH="tools:workbench/spikes/search-fts5-2026-11-07" \
        .venv/bin/pytest -p spike_search_swap tests/test_search_index.py ...

Swaps candidates, build_segment, and build_postings in-process. Production files remain untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import learning_os.derive.search.index as _search_index  # noqa: E402
import learning_os.derive.search.query as _search_query  # noqa: E402
import spike_search_fts5 as _spike  # noqa: E402

# Swap candidates
setattr(_search_query, "candidates", _spike.candidates_sql)

# Swap segment and postings builders
setattr(_search_index, "build_segment", _spike.build_segment_sql)
setattr(_search_index, "build_postings", _spike.build_postings_sql)

# Rebind in already imported modules
for m in list(sys.modules.values()):
    if m is not None and hasattr(m, "__dict__"):
        if getattr(m, "candidates", None) is not None and m.__name__.startswith("learning_os"):
            setattr(m, "candidates", _spike.candidates_sql)
        if getattr(m, "build_segment", None) is not None and m.__name__.startswith("learning_os"):
            setattr(m, "build_segment", _spike.build_segment_sql)
        if getattr(m, "build_postings", None) is not None and m.__name__.startswith("learning_os"):
            setattr(m, "build_postings", _spike.build_postings_sql)
