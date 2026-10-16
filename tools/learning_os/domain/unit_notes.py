"""The unit working note: one section format, written and read in one place.

``unit-note`` appends a session section; the manifest projects those sections;
shelving assembles the review packet from them. Those three had drifted into
two ownership models — the writer stored session reasoning on the unit while
shelving still walked stage-owned notes — so a saved note was safely stored and
then silently absent from the review it was written for (2026-09-05 audit F06).

The marker, its metadata, and the parser now live here, so a change to the
format cannot reach one side without the others.
"""

from __future__ import annotations

import json
import re

MARKER_PREFIX = "<!-- learningos:unit-note "
MARKER_RE = re.compile(r"^<!-- learningos:unit-note (\{.*\}) -->\s*$", re.MULTILINE)


def unit_note_marker(metadata: dict) -> str:
    """Render the machine-readable header that opens one session section."""
    return MARKER_PREFIX + json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + " -->"


def unit_note_sections(text: str) -> list[dict]:
    """Split a unit working note into its recorded session sections.

    Learner wording is returned exactly as saved: the parser removes only the
    marker and the section's own ``## `` heading, which it returns as ``title``.
    """
    matches = list(MARKER_RE.finditer(text or ""))
    sections: list[dict] = []
    for index, match in enumerate(matches):
        try:
            metadata = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        heading = ""
        lines = body.splitlines()
        if lines and lines[0].startswith("## "):
            heading = lines[0][3:].strip()
            body = "\n".join(lines[1:]).strip()
        sections.append({
            "recorded_at": metadata.get("recorded_at"),
            "title": metadata.get("title") or heading or "Learning session note",
            "stage_ids": list(metadata.get("stage_ids") or []),
            "attachments": list(metadata.get("attachments") or []),
            "text": body,
        })
    return sections
