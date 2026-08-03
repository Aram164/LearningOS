#!/usr/bin/env python3
"""Learning OS CLI — the stable machine gateway for interface layers (ADR-006).

    python tools/los.py status            # one-screen repository state
    python tools/los.py status --json     # same, machine-readable (stable keys)
    python tools/los.py validate          # delegate to tools/validate.py
    python tools/los.py generate          # delegate to tools/generate.py
    python tools/los.py capture ...       # drop a capture into work/inbox/

Interface layers (the Obsidian UI project, scripts, agents) call THESE
commands instead of parsing YAML or reimplementing rules. The Python loader
remains the single authority; `validate` and `generate` are thin delegations
to the canonical scripts, so there is exactly one implementation of every
rule.

Deliberately NOT here (CLAUDE.md §3–§5, §14): anything requiring operator
judgment — routing inbox items, creating notes and assigning roles, harvesting
the Garden, finishing sessions, semantic edits. `capture` is the one write
because it is judgment-free: it puts bytes in `work/inbox/`, where routing is
explicitly the operator's job. Exit codes: 0 ok · 1 validation errors ·
2 usage/environment error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os import __version__  # noqa: E402
from learning_os.genout import _exam_spine, adoption_counts  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402
from learning_os.rules import validate  # noqa: E402

TOOLS = Path(__file__).resolve().parent


def _root(args) -> Path:
    return Path(args.root).resolve() if args.root else TOOLS.parent


# ----------------------------------------------------------------- status
def cmd_status(args) -> int:
    root = _root(args)
    repo = load_repo(root)
    issues = validate(repo, online=False)
    errors = sum(1 for i in issues if i.severity == "E")
    warnings = sum(1 for i in issues if i.severity == "W")

    inbox = root / "work" / "inbox"
    n_inbox = len([f for f in inbox.iterdir()
                   if not f.name.startswith(".")]) if inbox.is_dir() else 0
    active = repo.active_workspaces()
    ad = adoption_counts(repo)
    spine = [
        {"date": date, "module_id": mid,
         "title": module.get("title", mid), "termin": att.get("termin")}
        for date, mid, module, att in _exam_spine(repo)
    ]

    payload = {
        "learning_os": __version__,
        "root": str(root),
        "counts": {
            "notes": len(repo.notes),
            "concepts": len(repo.concepts),
            "concept_relations": len(repo.relations),
            "sources": len(repo.sources),
            "modules": len(repo.modules),
            "modules_enrolled": sum(
                1 for m in repo.modules.values() if m.get("status") == "enrolled"),
            "active_workspaces": len(active),
            "standing_workspaces": sum(1 for w in active if w.standing),
            "archived_workspaces": len(repo.archived_workspaces()),
            "inbox_items": n_inbox,
            "garden_notes": len(repo.garden_notes),
        },
        "adoption": {
            "notes_reviewed": ad["notes_reviewed"],
            "notes_with_evidence": ad["notes_with_evidence"],
        },
        "exam_spine": spine,
        "validation": {"errors": errors, "warnings": warnings,
                       "ok": errors == 0 and warnings == 0},
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    c = payload["counts"]
    print(f"Learning OS v3 · learning_os v{__version__} · {root}")
    print(f"  notes {c['notes']} · concepts {c['concepts']} · "
          f"relations {c['concept_relations']} · sources {c['sources']}")
    print(f"  modules {c['modules']} ({c['modules_enrolled']} enrolled) · "
          f"workspaces {c['active_workspaces']} active "
          f"({c['standing_workspaces']} standing), "
          f"{c['archived_workspaces']} archived")
    print(f"  inbox {c['inbox_items']} · garden {c['garden_notes']} · "
          f"reviewed {ad['notes_reviewed']}/{c['notes']} · "
          f"evidence {ad['notes_with_evidence']}/{c['notes']}")
    if spine:
        for e in spine:
            print(f"  exam: {e['date']} — {e['title']} (Termin {e['termin']})")
    else:
        print("  exam: no registered attempts in records/modules.yaml")
    state = "OK" if payload["validation"]["ok"] else \
        f"{errors} error(s), {warnings} warning(s)"
    print(f"  validation: {state}")
    print("  human home page: generated/reading-room.md (make views)")
    return 0


# ---------------------------------------------------- validate / generate
def _delegate(script: str, extra: list[str], args) -> int:
    """One implementation of every rule: shell out to the canonical script."""
    cmd = [sys.executable, str(TOOLS / script), *extra]
    if args.root:
        cmd += ["--root", str(_root(args))]
    return subprocess.run(cmd).returncode


def cmd_validate(args) -> int:
    return _delegate("validate.py", ["--online"] if args.online else [], args)


def cmd_generate(args) -> int:
    return _delegate("generate.py", [], args)


# ---------------------------------------------------------------- capture
def cmd_capture(args) -> int:
    """Judgment-free capture into work/inbox/ (ARCHITECTURE §3.3: no naming,
    no filing — the operator routes later)."""
    root = _root(args)
    inbox = root / "work" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.file:
        src = Path(args.file).expanduser()
        if not src.is_file():
            print(f"los: no such file: {src}", file=sys.stderr)
            return 2
        target = inbox / src.name
        if target.exists():
            target = inbox / f"{stamp}-{src.name}"
        shutil.copy2(src, target)
    else:
        text = args.text if args.text is not None else sys.stdin.read()
        if not text.strip():
            print("los: nothing to capture (empty input)", file=sys.stderr)
            return 2
        slug = re.sub(r"[^a-z0-9]+", "-",
                      (args.title or text).lower()).strip("-")[:40] or "capture"
        target = inbox / f"{stamp}-{slug}.md"
        body = (f"# {args.title}\n\n{text}\n" if args.title else text.rstrip() + "\n")
        target.write_text(body, encoding="utf-8")

    print(f"captured -> {target.relative_to(root)}")
    print("routing is the operator's job (WORKFLOWS §21); the inbox trends "
          "toward empty")
    return 0


# ------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(
        prog="los", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="one-screen repository state")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("validate", help="delegate to tools/validate.py")
    p.add_argument("--online", action="store_true", help="also audit external URLs")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("generate", help="delegate to tools/generate.py")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("capture",
                       help="drop text or a file into work/inbox/ (no routing)")
    p.add_argument("--text", default=None, help="capture this text (else stdin)")
    p.add_argument("--file", default=None, help="copy this file into the inbox")
    p.add_argument("--title", default=None, help="optional title for text captures")
    p.set_defaults(func=cmd_capture)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
