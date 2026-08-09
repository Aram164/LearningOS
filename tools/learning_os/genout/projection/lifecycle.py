"""Two state machines a module record mixes into one field, told apart."""

from __future__ import annotations

# `module.status` mixes two state machines. `planned / enrolled / awaiting-grade
# / completed / dropped / archived` answer "what does the university think?";
# `active / paused` answer "am I working on this?". They are independent — Algo 2
# is administratively enrolled and operationally paused, PPDS is submitted with a
# grade pending and operationally paused — so any consumer reading one field for
# both questions has to guess. Home guessed wrong: it treated everything except
# `complete`/`archived` as current work, which put dropped Algo 2 and finished
# PPDS in "Continue elsewhere".
#
# Splitting the field itself is the right long-term fix and a breaking change to
# every stored module record. Projecting both axes plus the answer the interface
# actually wants costs nothing and removes the guessing today (engineering audit
# 2026-08-08, finding 4).
ADMINISTRATIVE_STATUSES = frozenset({
    "planned", "enrolled", "awaiting-grade", "completed", "dropped", "archived",
})
# Nothing is expected of you for these, whatever the units say.
SETTLED_ADMINISTRATIVE = frozenset({"awaiting-grade", "completed", "dropped", "archived"})
# Unit states that mean there is something to pick up. `not-started` counts:
# unstarted work is still work. `ready-to-shelve` does not — it is a review
# decision, which Review surfaces, not a study session.
LIVE_UNIT_STATUSES = frozenset({"needs-map", "not-started", "ready", "active"})


def module_lifecycle(module: dict, unit_statuses: list[str]) -> dict:
    """Administrative state, operational state, and whether work is available.

    Operational state is derived from the units rather than read from
    `module.status`, because the units are where work actually lives — a module
    cannot be operationally active while every unit under it is paused, no
    matter what its own field says.
    """
    status = str(module.get("status", "") or "")
    if status in ADMINISTRATIVE_STATUSES:
        administrative = status
    elif module.get("kind", "academic") == "academic":
        # `active`/`paused` on an academic module says nothing administrative,
        # but you cannot be working on one you are not enrolled in.
        administrative = "enrolled"
    else:
        # Skill, foundation and project modules have no registrar.
        administrative = None

    if not unit_statuses:
        operational = "none"
    elif all(s == "complete" for s in unit_statuses):
        operational = "complete"
    elif any(s in LIVE_UNIT_STATUSES for s in unit_statuses):
        operational = "active"
    else:
        operational = "paused"

    actionable = (
        operational == "active"
        and administrative not in SETTLED_ADMINISTRATIVE
        and status != "paused"
    )
    return {
        "administrative_status": administrative,
        "operational_state": operational,
        "is_actionable": actionable,
    }
