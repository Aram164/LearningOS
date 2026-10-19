"""Pure Markdown section extraction over a supplied body."""

from __future__ import annotations

import re


def md_section(body: str, heading: str) -> str | None:
    """Return the text of a `## <heading>` body section, if present.

    Single implementation of Markdown ``## heading`` section extraction, shared
    by Workspace, Coordination, and the validator (previously duplicated in
    three places). A section runs from its heading to the next `## ` heading or
    end of document.
    """
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else None
