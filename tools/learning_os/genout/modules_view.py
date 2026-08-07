"""Academic module views, exam spine and deadline rows."""

from __future__ import annotations

import datetime as _dt
from ..loader import Repo
from .common import _md_header

def _exam_spine(repo: Repo) -> list[tuple[str, str, dict, dict]]:
    """(date, module_id, module, attempt) for attempts with result=registered."""
    spine = []
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        for att in module.get("attempts", []) or []:
            if att.get("result") == "registered" and att.get("date"):
                spine.append((str(att["date"]), mid, module, att))
    spine.sort()
    return spine


def _academic_deadlines(repo: Repo) -> list[dict]:
    """Project structured exam sittings and registration windows for interfaces.

    Attempts remain the authority for what the learner actually registered,
    withdrew from, sat, or passed.  Examination sittings describe available
    dates even before an attempt exists; correlating the two here keeps that
    business rule out of every interface.
    """
    deadlines: list[dict] = []
    represented_attempts: set[tuple[str, int, str]] = set()
    grouped_windows: dict[tuple[str, str, str], dict] = {}

    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        examination = module.get("examination") or {}
        attempts = module.get("attempts", []) or []

        for sitting in examination.get("sittings", []) or []:
            start = str(sitting.get("date", ""))
            if not start:
                continue
            end = str(sitting.get("end_date") or start)
            termin = int(sitting.get("termin", 1))
            matching = [
                attempt for attempt in attempts
                if int(attempt.get("termin", 0)) == termin
                and start <= str(attempt.get("date", "")) <= end
            ]
            state = "unregistered"
            for result in ("registered", "passed", "failed", "withdrawn"):
                if any(attempt.get("result") == result for attempt in matching):
                    state = result
                    break
            represented_attempts.update(
                (mid, termin, str(attempt.get("date")))
                for attempt in matching if attempt.get("date")
            )
            # Availability is actionable state, not historical inventory. Keep
            # past sittings when an attempt gives them administrative meaning,
            # but do not advertise an elapsed, never-chosen sitting as open.
            if state == "unregistered" and end < _dt.date.today().isoformat():
                continue
            deadlines.append({
                "kind": "exam",
                "start_date": start,
                "end_date": end,
                "module_id": mid,
                "title": module.get("title", mid),
                "termin": termin,
                "label": sitting.get("label") or f"Termin {termin}",
                "time": sitting.get("time"),
                "notes": sitting.get("notes"),
                "registration_state": state,
            })

        for window in examination.get("registration_windows", []) or []:
            opens = str(window.get("opens", ""))
            closes = str(window.get("closes", ""))
            label = str(window.get("label", "Registration window"))
            if not opens or not closes:
                continue
            key = (opens, closes, label)
            grouped = grouped_windows.setdefault(key, {
                "kind": "registration-window",
                "start_date": opens,
                "end_date": closes,
                "label": label,
                "modules": [],
            })
            grouped["modules"].append({
                "module_id": mid,
                "title": module.get("title", mid),
                "action": window.get("action"),
                "termins": list(window.get("termins", []) or []),
            })

    # A registered attempt remains visible even if its module has not yet been
    # backfilled with an available-sitting record.
    for date, mid, module, attempt in _exam_spine(repo):
        key = (mid, int(attempt.get("termin", 1)), date)
        if key in represented_attempts:
            continue
        deadlines.append({
            "kind": "exam",
            "start_date": date,
            "end_date": date,
            "module_id": mid,
            "title": module.get("title", mid),
            "termin": attempt.get("termin"),
            "label": f"Termin {attempt.get('termin', '')}".strip(),
            "time": None,
            "notes": attempt.get("notes"),
            "registration_state": "registered",
        })

    for grouped in grouped_windows.values():
        grouped["modules"].sort(key=lambda row: row["module_id"])
        deadlines.append(grouped)
    deadlines.sort(key=lambda row: (
        row.get("start_date", ""),
        0 if row.get("kind") == "registration-window" else 1,
        row.get("label", ""),
        row.get("module_id", ""),
    ))
    return deadlines


def _exam_spine_lines(repo: Repo) -> list[str]:
    lines = []
    spine = _exam_spine(repo)
    if spine:
        lines.append("| Date | Module | Termin | Notes |")
        lines.append("|---|---|---|---|")
        for date, mid, module, att in spine:
            lines.append(f"| {date} | {module.get('title', mid)} (`{mid}`) "
                         f"| {att.get('termin', '')} | {att.get('notes', '')} |")
    else:
        lines.append("(no registered attempts in records/modules.yaml)")
    deadlines = _academic_deadlines(repo)
    pending = [row for row in deadlines
               if row.get("kind") == "exam"
               and row.get("registration_state") == "unregistered"]
    if pending:
        lines.append("")
        lines.append("**Available sittings with no registered attempt yet:**")
        lines.append("")
        for row in pending:
            date = row["start_date"]
            if row.get("end_date") != date:
                date += f" to {row['end_date']}"
            lines.append(f"- **{date}** — {row['title']} (`{row['module_id']}`), "
                         f"{row['label']} — not registered"
                         + (f" · {row['notes']}" if row.get("notes") else ""))
    windows = [row for row in deadlines if row.get("kind") == "registration-window"]
    if windows:
        lines.append("")
        lines.append("**Registration windows:**")
        lines.append("")
        for row in windows:
            titles = ", ".join(module["title"] for module in row["modules"])
            lines.append(f"- **{row['start_date']} to {row['end_date']}** — "
                         f"{row['label']}: {titles}")
    return lines


def build_module_view(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Module view", generated_at)
    lines.append("## Upcoming exam spine (registered attempts, sorted by date)")
    lines.append("")
    lines.extend(_exam_spine_lines(repo))
    lines.append("")
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        lines.append(f"## {m.get('title', mid)}")
        lines.append("")
        ident = [f"`{mid}`", m.get("institution", ""), m.get("code", "")]
        lines.append(" · ".join(str(x) for x in ident if x))
        lines.append("")
        facts = []
        if m.get("credits") is not None:
            facts.append(f"credits: {m['credits']}")
        if m.get("semester"):
            facts.append(f"semester: {m['semester']}")
        facts.append(f"status: {m.get('status', '')}")
        if m.get("examination"):
            ex = m["examination"]
            facts.append(f"examination: {ex.get('type', '')}"
                         + (f" ({ex.get('notes')})" if ex.get("notes") else ""))
        if m.get("grade") is not None:
            facts.append(f"final grade: {m['grade']}")
        lines.append(" · ".join(facts))
        if m.get("components"):
            lines.append("")
            component_titles = [c.get("title", c.get("id", "")) if isinstance(c, dict)
                                else str(c) for c in m["components"]]
            lines.append("Components (one grade): " + " + ".join(component_titles))
        attempts = m.get("attempts", []) or []
        if attempts:
            lines.append("")
            lines.append("| # | Termin | Date | Result | Grade | Notes |")
            lines.append("|---|---|---|---|---|---|")
            for i, att in enumerate(attempts, 1):
                lines.append(f"| {i} | {att.get('termin', '')} | {att.get('date', '')} "
                             f"| {att.get('result', '')} | {att.get('grade', '')} "
                             f"| {att.get('notes', '')} |")
        lines.append("")
    return "\n".join(lines)
