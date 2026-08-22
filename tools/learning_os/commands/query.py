"""Read-only commands. Nothing here writes: status, bootstrap, search, inspect, related,
and the thin delegations to validate.py / generate.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from learning_os import __version__
from learning_os.contracts.capability_catalog import load_capability_catalog
from learning_os.genout import adoption_counts, exam_spine
from learning_os.loader import load_repo
from learning_os.rules import validate

from .support import _delegate, _fresh_manifest, _operator_lock, _print_rows, _publish, _root

# The OPERATOR contract (system/OPERATOR.md) — what `los.py capabilities`
# announces about the gateway itself. This is a third, independent version:
#   operator/gateway contract  here (CONTRACT_VERSION below)
#   canonical record format    system/contracts/data-contract.yaml
#   published manifest shape   system/contracts/manifest-contract.yaml
# Three contracts sharing the name "contract_version" is how the manifest came
# to be published under an old version after its shape had already changed
# (2026-08-08). Stored and projected versions must always be read from their
# producer-owned declarations, never copied into this comment.
CONTRACT_VERSION = 2

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
        for date, mid, module, att in exam_spine(repo)
    ]

    payload = {
        "learning_os": __version__,
        "root": str(root),
        "counts": {
            "notes": len(repo.notes),
            "concepts": len(repo.concepts),
            "concept_relations": len(repo.relations),
            "sources": len(repo.sources),
            "programs": len(repo.programs),
            "modules": len(repo.modules),
            "projects": len(repo.projects),
            "modules_enrolled": sum(
                1 for m in repo.modules.values() if m.get("status") == "enrolled"),
            "active_workspaces": len(active),
            "standing_workspaces": sum(1 for w in active if w.standing),
            "archived_workspaces": len(repo.archived_workspaces()),
            "inbox_items": n_inbox,
            "garden_notes": len(repo.garden_notes),
            "units": len(repo.units),
            "study_maps": len(repo.study_maps),
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
    print(f"  programs {c['programs']} · modules {c['modules']} "
          f"({c['modules_enrolled']} enrolled) · projects {c['projects']} · units {c['units']} · "
          f"study maps {c['study_maps']} · "
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


# ---------------------------------------------------- machine discovery/read
def _capabilities(root: Path) -> dict:
    """Return the executable capability catalogue, not a duplicated list."""
    catalogue = load_capability_catalog(root)
    return {
        "contract_version": CONTRACT_VERSION,
        "capability_contract_version": catalogue["contract_version"],
        "cli_protocol": catalogue.get("cli_protocol", 3),
        "gateway": "tools/los.py",
        "projection": "generated/manifest.json",
        "operator_contract": "system/OPERATOR.md",
        "queries": catalogue.get("queries", {}),
        "commands": catalogue.get("commands", {}),
        "rules": {
            "canonical_writes_are_transactional": True,
            "successful_writes_have_receipts": True,
            "artifact_revision_conflicts_fail_closed": True,
            "shelving_requires_explicit_approval": True,
            "job_quarantine": True,
            "ordinary_interfaces_read_projection_only": True,
            "job_dashboard_requires_explicit_access": True,
            "job_dashboard_is_ephemeral": True,
            "module_plan_preflight_required": True,
            "ai_actions_are_provider_independent": True,
            "ai_actions_never_read_job": True,
        },
        "root": str(root),
    }


def cmd_capabilities(args) -> int:
    payload = _capabilities(_root(args))
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
          if args.json else "\n".join(
              [f"LearningOS operator contract v{payload['contract_version']}",
               f"  gateway: {payload['gateway']}",
               f"  projection: {payload['projection']}",
               "  transactional commands: " + ", ".join(sorted(payload["commands"])),
               "  every successful canonical write has one receipt"]))
    return 0


def cmd_bootstrap(args) -> int:
    root = _root(args)
    manifest = _fresh_manifest(root)
    payload = {
        "capabilities": _capabilities(root),
        "snapshot": manifest.get("_generated", {}),
        "programs": manifest.get("programs", []),
        "modules": manifest.get("modules", []),
        "projects": manifest.get("projects", []),
        "units": manifest.get("units", []),
        "active_study_maps": [m for m in manifest.get("study_maps", [])
                              if m.get("status") in {"active", "paused", "ready"}],
        "resume_pointer": manifest.get("resume_pointer", {}),
        "quarantine_boundaries": manifest.get("quarantine_boundaries", []),
        "next": "Resume the pointer or choose any visible module and unit.",
    }
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_search(args) -> int:
    manifest = _fresh_manifest(_root(args))
    words = [w for w in args.query.lower().split() if w]
    matches = []
    for rec in manifest["records"]:
        if args.type and rec.get("type") != args.type:
            continue
        hay = json.dumps(rec, ensure_ascii=False).lower()
        if all(word in hay for word in words):
            matches.append({k: rec.get(k) for k in ("id", "type", "title", "path", "status")})
    print(json.dumps(matches[:args.limit], indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_inspect(args) -> int:
    manifest = _fresh_manifest(_root(args))
    resolved_id = (manifest.get("project_aliases") or {}).get(args.id, args.id)
    rec = next((r for r in manifest["records"] if r.get("id") == resolved_id), None)
    if rec is None:
        print(f"los: record not found: {args.id}", file=sys.stderr)
        return 2
    payload = dict(rec)
    if resolved_id != args.id:
        payload["resolved_from"] = args.id
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_related(args) -> int:
    manifest = _fresh_manifest(_root(args))
    by_id = {r.get("id"): r for r in manifest["records"]}
    resolved_id = (manifest.get("project_aliases") or {}).get(args.id, args.id)
    rec = by_id.get(resolved_id)
    if rec is None:
        print(f"los: record not found: {args.id}", file=sys.stderr)
        return 2
    ids = set()
    for key in ("concepts", "sources", "contexts", "notes", "program_ids",
                "module_ids", "unit_ids", "unit_order", "related_module_ids"):
        ids.update(rec.get(key, []) or [])
    if rec.get("workspace_id"):
        ids.add(rec["workspace_id"])
    for key in ("area_id", "module_id", "unit_id", "current_study_map"):
        if rec.get(key):
            ids.add(rec[key])
    backlinks = manifest.get("backlinks", {})
    for table in ("concept_to_notes", "source_to_notes", "workspace_to_notes",
                  "module_to_workspaces", "unit_to_workspaces", "module_to_units",
                  "source_to_units"):
        ids.update((backlinks.get(table) or {}).get(args.id, []) or [])
    for relation in manifest.get("relations", []):
        if relation.get("from") == args.id:
            ids.add(relation.get("to"))
        if relation.get("to") == resolved_id:
            ids.add(relation.get("from"))
    for relation in manifest.get("project_relationships", []):
        if relation.get("from_project_id") == resolved_id:
            ids.add(relation.get("to_id"))
        if relation.get("to_id") == resolved_id:
            ids.add(relation.get("from_project_id"))
    out = [{k: by_id[rid].get(k) for k in ("id", "type", "title", "path")}
           for rid in sorted(ids) if rid in by_id]
    print(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_program_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    return _print_rows(manifest.get("programs", []))


def cmd_validate(args) -> int:
    return _delegate("validate.py", ["--online"] if args.online else [], args)


def cmd_generate(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        _publish(root)
    print("published generated/manifest.json (atomic contract snapshot)")
    return 0
