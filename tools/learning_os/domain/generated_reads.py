"""One shared read of a generated file's GEN-JSON/GEN-HEADER findings.

Both the generated-files validator (``rules.generated.check_generated``)
and the validation cache's derived-state pin
(``validation_cache.validator_inputs_digest``) must read the same
findings from the same bytes: the pin misses exactly when the validator's
answer would change. Two copies of this read drifted once already (the
cache pin's copy missed view-named directories its walk descended into),
so the implementation lives here, imported by both callers, with no
layer exception either way. Pure: same path shape and bytes, same
findings, same raises.
"""

from __future__ import annotations

import json
from pathlib import Path


def generated_file_findings(path: Path) -> list[tuple[str, str]]:
    """Per-file GEN-JSON/GEN-HEADER findings for one generated path. Pure.

    Exactly the per-file logic `check_generated` applies to each `*.md`
    and `*.json` under `generated/`: same codes, same messages, same
    order (at most one finding per file). Other suffixes have no
    findings. Raises `OSError` on unreadable files and
    `UnicodeDecodeError` on non-UTF-8 JSON, as `check_generated` does;
    callers that pin outcomes catch `ValueError` and treat it as a
    distinct state.
    """
    name = path.name
    if name.endswith(".md"):
        if path.is_symlink() and not path.exists():
            return [("GEN-HEADER",
                     "generated Markdown is a broken symlink, not the "
                     "published view — delete it and rebuild")]
        if not path.is_file():
            return [("GEN-HEADER",
                     "generated Markdown is a directory, not the published "
                     "view — delete it and rebuild")]
        head = path.read_text(encoding="utf-8", errors="replace")[:400]
        if "GENERATED" not in head:
            return [("GEN-HEADER",
                     "generated file lacks a generated-file warning header")]
        return []
    if name.endswith(".json"):
        if path.is_symlink() and not path.exists():
            return [("GEN-JSON",
                     "generated JSON is a broken symlink, not the published "
                     "view — delete it and rebuild")]
        if not path.is_file():
            return [("GEN-JSON",
                     "generated JSON is a directory, not the published "
                     "view — delete it and rebuild")]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return [("GEN-JSON", "generated JSON does not parse")]
        if isinstance(data, dict) and "_generated" not in data:
            return [("GEN-HEADER",
                     "generated JSON lacks the '_generated' warning key")]
        return []
    return []
