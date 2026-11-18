"""The module lifecycle: the registrar's status and the work it still permits.

`module.status` mixes two state machines. `planned / enrolled / awaiting-grade
/ completed / dropped / archived` answer "what does the university think?";
`active / paused` answer "am I working on this?". This module owns only the
first axis: the administrative answer, and whether it settles the module.
"""

from __future__ import annotations

ADMINISTRATIVE_STATUSES = frozenset({
    "planned", "enrolled", "awaiting-grade", "completed", "dropped", "archived",
})

#: Nothing is expected of you for these, whatever the units say. They keep
#: their records as history; they are never offered as fresh study choices.
SETTLED_ADMINISTRATIVE = frozenset({
    "awaiting-grade", "completed", "dropped", "archived",
})


def administrative_status(module: dict[str, object]) -> str | None:
    """The registrar's answer for a module, or None for a non-academic module."""
    status = str(module.get("status", "") or "")
    if status in ADMINISTRATIVE_STATUSES:
        return status
    if module.get("kind", "academic") == "academic":
        # `active`/`paused` on an academic module says nothing administrative,
        # but you cannot be working on one you are not enrolled in.
        return "enrolled"
    # Skill, foundation and project modules have no registrar.
    return None
