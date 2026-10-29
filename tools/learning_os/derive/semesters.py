"""Which semester is current, and which modules the interface lists.

Two questions an operator asks after creating a module or turning a term:

* **Is this module listed?** The rule is Core-owned, because the facts it
  reads are Core-owned: a module is listed when it is academic and still
  open — its status is not completed, archived or dropped. The sibling
  interface applies the same rule when it renders the module list
  (``src/manifest-store.ts`` — ``openAcademicModules``). The semester is
  context there, not a gate: a module created for a later term is not
  hidden by the term that happens to be current.
* **Which semester is current?** One program record declares it: the
  semester row whose status is ``current``. A program without semesters
  (skills, projects) has none, and the interface shows the module list
  without a semester label.

The two are deliberately separate. Turning the term does not change which
modules are listed, and creating a module does not turn the term. What
changes is the label the interface prints and the term a module belongs to
— so a report that conflates the two is the bug LearningOS #2 reports.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping

from learning_os.domain.snapshot import Repo

#: Statuses that close a module: the record stays, the module leaves the list.
CLOSED_MODULE_STATUSES = ("completed", "archived", "dropped")

#: The rule, in the words the interface uses for it.
LISTING_RULE = (
    "open learning modules: kind in (academic, project) and not compatibility_only and status not in "
    "(completed, archived, dropped)"
)

#: One canonical record: a YAML document whose fields vary by kind.
Record = Mapping[str, object]


def _text(value: object) -> str:
    """A record field as text, empty when it is absent."""
    return "" if value is None else str(value)


def _order(value: object) -> int:
    """A record field as an ordering number, zero when it is not one."""
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _semester_rows(program_data: Record | None) -> list[Record]:
    """The program record's semester rows, in the order it declares them."""
    if program_data is None:
        return []
    raw = program_data.get("semesters")
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, dict)]


def is_listed(module: Record) -> bool:
    """Whether a module record belongs in the listed open learning modules.

    Pure over the record's own fields: kind, compatibility_only, and status.
    Nothing else decides membership — not the semester, not the thematic group,
    not the source usage.
    """
    if module.get("compatibility_only"):
        return False
    if module.get("kind") not in ("academic", "project"):
        return False
    return _text(module.get("status")) not in CLOSED_MODULE_STATUSES


def current_semester(program_data: Record | None) -> Record | None:
    """The program record's current semester row, if it declares one.

    A program declares at most one current semester. When it declares more
    than one, the earliest ``order`` wins — the same tie-break the
    interface applies when it picks the current semester.
    """
    rows = [row for row in _semester_rows(program_data)
            if row.get("status") == "current"]
    if not rows:
        return None
    return min(rows, key=lambda row: (_order(row.get("order")),
                                      _text(row.get("id"))))


def semester_matches(current_id: str | None, module_semester: str | None) -> bool:
    """Whether a module's semester is the current one.

    Two spellings name the same term: the program record says
    ``semester-wise-2026`` and the module record says ``wise-2026``. The
    interface accepts both at its read boundary, so the comparison here
    accepts both too.
    """
    if not current_id or not module_semester:
        return False
    if module_semester == current_id:
        return True
    return module_semester == current_id.removeprefix("semester-")


def module_listing(repo: Repo, module: Record) -> dict[str, object]:
    """What the interface will do with this module, and which term it is in.

    The answer is the record's own facts plus the owning program's current
    semester — the two things an operator needs after a creation to know
    that the module they just made is where they expect it to be.
    """
    program_id = module.get("area_id")
    program = repo.programs.get(program_id) if isinstance(program_id, str) else None
    current = current_semester(program.data if program is not None else None)
    module_semester = module.get("semester")
    listed = is_listed(module)
    facts: dict[str, object] = {
        "listed": listed,
        "rule": LISTING_RULE,
        "kind": module.get("kind"),
        "status": module.get("status"),
        "semester": module_semester,
        "program_id": program_id,
        "current_semester": None,
        "semester_matches_current": False,
    }
    if current is not None:
        facts["current_semester"] = {
            "id": current.get("id"),
            "title": current.get("title"),
        }
        facts["semester_matches_current"] = semester_matches(
            _text(current.get("id")),
            _text(module_semester) or None,
        )
    if not listed:
        kind = module.get("kind")
        adj = "academic" if kind == "academic" else "learning"
        facts["note"] = (
            f"this module is not an open {adj} module (kind="
            f"{kind!r}, status={module.get('status')!r}), "
            "so the module list does not show it"
        )
    elif not facts["semester_matches_current"] and current is not None:
        facts["note"] = (
            f"the module's semester ({module_semester!r}) differs from the "
            f"current semester ({current.get('id')!r}); the module list is "
            "not gated by the semester, so the module is still listed"
        )
    return facts


def semester_plan(program_data: Record, semester: Record) -> dict[str, object]:
    """The semester list a reviewed update produces, and what it changes.

    Pure over the program record and the reviewed semester: the current
    semester becomes ``previous``, the reviewed one becomes ``current``,
    and every other row keeps its status. History is never dropped — a
    semester that leaves the current slot stays in the list.
    """
    rows = [copy.deepcopy(dict(row)) for row in _semester_rows(program_data)]
    semester_id = _text(semester.get("id"))
    for row in rows:
        if _text(row.get("id")) == semester_id:
            row["title"] = semester.get("title")
            row["order"] = semester.get("order")
            row["status"] = "current"
            break
    else:
        rows.append({
            "id": semester_id,
            "title": semester.get("title"),
            "order": semester.get("order"),
            "status": "current",
        })
    for row in rows:
        if _text(row.get("id")) != semester_id and row.get("status") == "current":
            row["status"] = "previous"
    before = current_semester(program_data)
    after = current_semester({"semesters": rows})
    return {
        "semesters": rows,
        "current_before": before,
        "current_after": after,
        "added": not any(_text(row.get("id")) == semester_id
                         for row in _semester_rows(program_data)),
    }
