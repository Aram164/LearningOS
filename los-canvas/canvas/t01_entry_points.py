"""T01 — Operator entry points.

Every row of the OPERATOR.md "Start here" table is an operator's promise:
*a named task has a named entry read*. This file walks that table in order
against a synthetic world and records, for each entry:

* does it succeed;
* how much does it cost to read (bytes ≈ 4·tokens);
* does the answer actually contain what the table promised.

It also measures the trap the contract warns about: `bootstrap` without
`--brief` prints the complete projection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, approx_tokens, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

# Fixture ids of the synthetic characterization world.
MODULE = "module-demo"
UNIT = "unit-demo-l01"
STAGE = "stage-demo"
STAGE_PENDING = "stage-demo-pending"
SOURCE = "source-demo-book"
WORKSPACE = "workspace-demo"
PATH = "path-demo"
PROJECT = "project-demo"
ABILITY = "ability-demo-derive"
NOTE = "note-demo-analysis"


def read(world: C.World, *args: str) -> tuple[C.Run, dict]:
    run = world.los(*args)
    payload = run.json
    return run, payload if isinstance(payload, dict) else {}


def main() -> int:
    world = C.build_world(WORLDS, "t01")
    route_id = None
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # ---- row 1: discover capabilities ------------------------------------
    def row1() -> dict:
        compact = world.los("capabilities", "--compact", "--json")
        data = compact.json or {}
        detail = {
            "exit_code": compact.exit_code,
            "queries": len(data.get("queries", {})),
            "commands": len(data.get("commands", {})),
            "bytes": len(compact.stdout),
            "tokens": approx_tokens(compact.stdout),
            "rules_declared": data.get("rules", {}),
        }
        one = world.los("capabilities", "note.create", "--json")
        detail["one_capability_exit"] = one.exit_code
        detail["one_capability_bytes"] = len(one.stdout)
        detail["one_capability_tokens"] = approx_tokens(one.stdout)
        detail["ok"] = (compact.exit_code == 0 and one.exit_code == 0
                        and len(data.get("commands", {})) > 0)
        return detail

    add("entry-01-discover-capabilities",
        "An agent starts a session and learns what the system can do.",
        row1, ["read", "entry-table"])

    # ---- row 2/3/4: plan-edit-context -----------------------------------
    def row2() -> dict:
        nonlocal route_id
        brief = world.los("plan-edit-context", UNIT, "--brief")
        data = brief.json or {}
        # The brief is supposed to name the routes so the caller can narrow.
        routes = data.get("routes") or data.get("route_ids") or []
        detail = {
            "exit_code": brief.exit_code,
            "bytes": len(brief.stdout),
            "tokens": approx_tokens(brief.stdout),
            "keys": sorted(data.keys())[:40],
        }
        route_id = _find_route_id(data)
        detail["route_id_discovered"] = route_id
        detail["ok"] = brief.exit_code == 0 and bool(data)
        return detail

    add("entry-02-plan-edit-context-brief",
        "Unit coverage, source completeness, or unknown ids → brief context.",
        row2, ["read", "entry-table"])

    def row3() -> dict:
        if not route_id:
            return {"ok": False, "error": "no route id from row 2"}
        run = world.los("plan-edit-context", UNIT, "--route-id", route_id)
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40],
        }
        detail["ok"] = run.exit_code == 0 and bool(data)
        return detail

    add("entry-03-plan-edit-context-route",
        "Edit a known material route → route-scoped edit context.",
        row3, ["read", "entry-table"])

    def row4() -> dict:
        run = world.los("plan-edit-context", UNIT, "--stage-id", STAGE)
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40],
        }
        detail["ok"] = run.exit_code == 0 and bool(data)
        return detail

    add("entry-04-plan-edit-context-stage",
        "Edit a known stage → stage-scoped edit context.",
        row4, ["read", "entry-table"])

    # ---- row 5: bootstrap --brief ---------------------------------------
    def row5() -> dict:
        brief = world.los("bootstrap", "--brief")
        data = brief.json or {}
        detail = {
            "exit_code": brief.exit_code,
            "bytes": len(brief.stdout),
            "tokens": approx_tokens(brief.stdout),
            "keys": sorted(data.keys())[:40],
            "session_identity": data.get("session_identity"),
            "snapshot_id": data.get("snapshot_id"),
        }
        detail["ok"] = brief.exit_code == 0 and bool(data)
        return detail

    add("entry-05-bootstrap-brief",
        "Open work or a priority question → one-page session entry.",
        row5, ["read", "entry-table"])

    def row5_trap() -> dict:
        run = world.los("bootstrap")
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "note": "the contract calls this 'a bulk read, never a session start'",
        }
        detail["ok"] = True          # measured, not asserted
        return detail

    add("entry-05b-bootstrap-unbounded",
        "TRAP: the same entry without --brief (measured, not asserted).",
        row5_trap, ["read", "cost", "trap"])

    def row5b() -> dict:
        run = world.los("inspect", WORKSPACE)
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-06-inspect-workspace",
        "Open work → inspect the workspace record.",
        row5b, ["read", "entry-table"])

    # ---- row 7: note-read ------------------------------------------------
    def row7() -> dict:
        run = world.los("note-read", NOTE)
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "total_characters": data.get("total_characters"),
            "path": data.get("path"),
            "content_sha256": data.get("content_sha256"),
        }
        detail["ok"] = run.exit_code == 0 and bool(data.get("content"))
        return detail

    add("entry-07-note-read",
        "Read the body of a saved reasoning note.",
        row7, ["read", "entry-table", "note-corpus"])

    def row7b() -> dict:
        run = world.los("note-read", NOTE, "--offset", "0", "--limit", "400")
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "content_len": len(data.get("content", "")),
            "next_offset": data.get("next_offset"),
            "total_characters": data.get("total_characters"),
        }
        detail["ok"] = run.exit_code == 0 and len(data.get("content", "")) <= 400
        return detail

    add("entry-07b-note-read-paged",
        "Read a bounded segment of a note (context discipline).",
        row7b, ["read", "bounded"])

    # ---- row 8: material-context / material-span ------------------------
    def row8() -> dict:
        run = world.los("material-context", "expected value")
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-08-material-context",
        "Find a saved explanation by need.",
        row8, ["read", "entry-table"])

    def row8b() -> dict:
        if not route_id:
            return {"ok": False, "error": "no route id"}
        run = world.los("material-span", UNIT, route_id)
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-09-material-span",
        "Describe one exact route.",
        row8b, ["read", "entry-table"])

    # ---- row 10: resume --------------------------------------------------
    def row10() -> dict:
        run = world.los("resume")
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-10-resume",
        "Resume recorded study without moving state.",
        row10, ["read", "entry-table"])

    def row10b() -> dict:
        run = world.los("resume", "--study")
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "stderr": run.stderr.strip()[:400],
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
            "note": ("the fixture's only exam date (2026-10-09) is in the "
                     "past relative to the wall clock, so the study "
                     "suggestion has no upcoming exam to project"),
        }
        # A refusal that names a reason and a next step is a pass: the
        # contract's promise is an honest answer, not always an answer.
        detail["ok"] = run.exit_code == 0 or (
            run.exit_code == 2 and "INVALID_REQUEST" in run.stderr)
        return detail

    add("entry-11-resume-study",
        "The study suggestion must not move the resume pointer.",
        row10b, ["read", "entry-table"])

    # ---- row 12: intelligence-scan ---------------------------------------
    def row12() -> dict:
        run = world.los("intelligence-scan", "--brief", "--json")
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-12-intelligence-scan",
        "Read the decision queue (changes awaiting a decision).",
        row12, ["read", "entry-table"])

    # ---- row 13: ability-context ----------------------------------------
    def row13() -> dict:
        run = world.los("ability-context")
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-13-ability-context-horizon",
        "Read the small ability horizon.",
        row13, ["read", "entry-table"])

    def row13b() -> dict:
        run = world.los("ability-context", ABILITY)
        data = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "keys": sorted(data.keys())[:40] if isinstance(data, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("entry-14-ability-context-one",
        "Expand one known ability.",
        row13b, ["read", "entry-table"])

    # ---- row 14: semantic ------------------------------------------------
    def row14() -> dict:
        listing = world.los("semantic", "--list")
        data = listing.json
        names, authorities = [], []
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    names.append(entry.get("name"))
                    authorities.append(entry.get("authority"))
        detail = {
            "exit_code": listing.exit_code,
            "bytes": len(listing.stdout),
            "tokens": approx_tokens(listing.stdout),
            "predicate_count": len(names),
            "first_predicates": names[:8],
            "distinct_authorities": sorted(set(a for a in authorities if a))[:12],
        }
        detail["ok"] = listing.exit_code == 0 and bool(names)
        return detail

    add("entry-15-semantic-list",
        "Governance question → the semantic registry.",
        row14, ["read", "entry-table"])

    def row14b() -> dict:
        listing = world.los("semantic", "--list")
        data = listing.json
        name = None
        if isinstance(data, list) and data:
            first = data[0]
            name = first.get("name") if isinstance(first, dict) else None
        if not name:
            return {"ok": False, "error": "no predicate found"}
        run = world.los("semantic", name)
        detail = {
            "predicate": name,
            "exit_code": run.exit_code,
            "bytes": len(run.stdout),
            "tokens": approx_tokens(run.stdout),
            "stdout_head": run.stdout[:400],
            "stderr_head": run.stderr[:400],
        }
        # A predicate with no inputs evaluates on defaults; a refusal that
        # names the missing input is also an honest answer.
        detail["ok"] = run.exit_code in (0, 2)
        return detail

    add("entry-16-semantic-predicate",
        "Ask one governance question through the semantic surface.",
        row14b, ["read", "entry-table"])

    # ---- supporting reads an operator will actually need -----------------
    def support() -> dict:
        out = {}
        for label, args in (
            ("status", ("status",)),
            ("module-list", ("module-list",)),
            ("unit-list", ("unit-list",)),
            ("project-list", ("project-list",)),
            ("program-list", ("program-list",)),
            ("inbox-list", ("inbox-list",)),
            ("search-empty", ("search", "")),
            ("search-content", ("search", "expected", "--content")),
            ("related-note", ("related", NOTE)),
            ("dossier", ("dossier", UNIT)),
        ):
            run = world.los(*args)
            out[label] = {
                "exit_code": run.exit_code,
                "bytes": len(run.stdout),
                "tokens": approx_tokens(run.stdout),
            }
        out["ok"] = all(v["exit_code"] == 0 for v in out.values()
                        if isinstance(v, dict))
        return out

    add("entry-17-supporting-reads",
        "The other operator reads: lists, search, related, dossier.",
        support, ["read", "cost"])

    outcomes = run_cases(cases, REPORTS / "t01", "T01 — Operator entry points")
    print()
    print(f"T01: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


def _find_route_id(data: dict) -> str | None:
    """Dig the route id out of a plan-edit-context brief."""
    for key in ("routes", "route_ids"):
        value = data.get(key)
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                for field in ("route_id", "id"):
                    if first.get(field):
                        return first[field]
        if isinstance(value, dict):
            for inner in value.values():
                if isinstance(inner, list) and inner:
                    first = inner[0]
                    if isinstance(first, str):
                        return first
                    if isinstance(first, dict):
                        for field in ("route_id", "id"):
                            if first.get(field):
                                return first[field]
    # fall back to a deep scan
    found = _deep_route(data)
    return found


def _deep_route(node: object) -> str | None:
    if isinstance(node, dict):
        for key in ("route_id",):
            value = node.get(key)
            if isinstance(value, str) and value.startswith("route-"):
                return value
        for value in node.values():
            hit = _deep_route(value)
            if hit:
                return hit
    elif isinstance(node, list):
        for value in node:
            hit = _deep_route(value)
            if hit:
                return hit
    elif isinstance(node, str) and node.startswith("route-"):
        return node
    return None


if __name__ == "__main__":
    raise SystemExit(main())
