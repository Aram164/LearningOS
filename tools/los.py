#!/usr/bin/env python3
"""Learning OS CLI — the stable machine gateway for interface layers (ADR-006).

    python tools/los.py status            # one-screen repository state
    python tools/los.py bootstrap         # AI/app startup contract + active paths
    python tools/los.py status --json     # same, machine-readable (stable keys)
    python tools/los.py validate          # delegate to tools/validate.py
    python tools/los.py generate          # delegate to tools/generate.py
    python tools/los.py path-note ...     # save stage-bound working notes
    python tools/los.py path-progress ... # advance the ordered path
    python tools/los.py capture ...       # drop an unrelated capture into work/inbox/

Interface layers (the Obsidian UI project, scripts, agents) call THESE
commands instead of parsing YAML or reimplementing rules. The Python loader
remains the single authority; `validate` and `generate` are thin delegations
to the canonical scripts, so there is exactly one implementation of every
rule.

Deliberately NOT here (OPERATOR.md, CLAUDE.md §3–§5, §14): anything requiring operator
judgment — routing inbox items, creating notes and assigning roles, harvesting
the Garden, finishing sessions, semantic edits. `capture` is the one write
because it is judgment-free: it puts bytes in `work/inbox/`, where routing is
explicitly the operator's job. Exit codes: 0 ok · 1 validation errors ·
2 usage/environment error · 3 optimistic-concurrency conflict.
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import datetime as _dt
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os import __version__  # noqa: E402
from learning_os.genout import (  # noqa: E402
    _exam_spine, _source_fingerprint, adoption_counts, build_backlinks,
    build_manifest, generate_all, stable_generated_at, write_outputs,
)
from learning_os.loader import load_repo, parse_frontmatter  # noqa: E402
from learning_os.rules import validate  # noqa: E402

TOOLS = Path(__file__).resolve().parent
CONTRACT_VERSION = 2


def _root(args) -> Path:
    return Path(args.root).resolve() if args.root else TOOLS.parent


@contextlib.contextmanager
def _operator_lock(root: Path):
    """Cross-process lock for every write/generation transaction."""
    token = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"learningos-{token}.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _expected_ok(root: Path, expected: str | None) -> bool:
    if not expected:
        return True
    actual = f"sha256:{_source_fingerprint(load_repo(root))}"
    if actual == expected:
        return True
    print("los: projection conflict — authored files changed since the app loaded; "
          "reload before writing", file=sys.stderr)
    print(json.dumps({"expected": expected, "actual": actual}), file=sys.stderr)
    return False


def _publish(root: Path) -> None:
    repo = load_repo(root)
    write_outputs(repo, generate_all(repo))


def _path_or_error(root: Path, path_id: str):
    repo = load_repo(root)
    learning_path = repo.learning_paths.get(path_id)
    if learning_path is None or learning_path.archived:
        print(f"los: active learning path not found: {path_id}", file=sys.stderr)
        return repo, None
    return repo, learning_path


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
            "programs": len(repo.programs),
            "modules": len(repo.modules),
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
          f"({c['modules_enrolled']} enrolled) · units {c['units']} · "
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
    return {
        "contract_version": CONTRACT_VERSION,
        "gateway": "tools/los.py",
        "projection": "generated/manifest.json",
        "operator_contract": "system/OPERATOR.md",
        "commands": {
            "read": ["status", "capabilities", "bootstrap", "search", "inspect", "related",
                     "program-list", "module-list", "unit-list"],
            "safe_writes": ["capture", "module-plan-import", "unit-map-import", "stage-note", "stage-progress",
                            "stage-attach", "source-feedback", "detour-create",
                            "detour-resolve", "shelving-prepare", "generate", "session-end"],
            "approval_gated": ["note-revise", "shelving-apply"],
        },
        "rules": {
            "canonical_writes_require_operator": True,
            "shelving_requires_explicit_approval": True,
            "job_quarantine": True,
            "interfaces_read_projection_only": True,
            "module_plan_preflight_required": True,
        },
        "root": str(root),
    }


def _fresh_manifest(root: Path) -> dict:
    repo = load_repo(root)
    generated_at = stable_generated_at(root)
    backlinks = build_backlinks(repo, generated_at)
    return build_manifest(repo, generated_at, backlinks)


def cmd_capabilities(args) -> int:
    payload = _capabilities(_root(args))
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
          if args.json else "\n".join(
              [f"LearningOS operator contract v{payload['contract_version']}",
               f"  gateway: {payload['gateway']}",
               f"  projection: {payload['projection']}",
               "  writes: " + ", ".join(payload["commands"]["safe_writes"]),
               "  shelving: explicit approval required"]))
    return 0


def cmd_bootstrap(args) -> int:
    root = _root(args)
    manifest = _fresh_manifest(root)
    payload = {
        "capabilities": _capabilities(root),
        "snapshot": manifest.get("_generated", {}),
        "programs": manifest.get("programs", []),
        "modules": manifest.get("modules", []),
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
    rec = next((r for r in manifest["records"] if r.get("id") == args.id), None)
    if rec is None:
        print(f"los: record not found: {args.id}", file=sys.stderr)
        return 2
    print(json.dumps(rec, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_related(args) -> int:
    manifest = _fresh_manifest(_root(args))
    by_id = {r.get("id"): r for r in manifest["records"]}
    rec = by_id.get(args.id)
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
        if relation.get("to") == args.id:
            ids.add(relation.get("from"))
    out = [{k: by_id[rid].get(k) for k in ("id", "type", "title", "path")}
           for rid in sorted(ids) if rid in by_id]
    print(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def _print_rows(rows: list[dict]) -> int:
    print(json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_program_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    return _print_rows(manifest.get("programs", []))


def cmd_module_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    rows = manifest.get("modules", [])
    if args.program_id:
        rows = [row for row in rows if row.get("area_id") == args.program_id]
    if args.status:
        rows = [row for row in rows if row.get("status") == args.status]
    return _print_rows(rows)


def cmd_unit_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    rows = manifest.get("units", [])
    if args.module_id:
        rows = [row for row in rows if row.get("module_id") == args.module_id]
    if args.component_id:
        rows = [row for row in rows if row.get("component_id") == args.component_id]
    if args.status:
        rows = [row for row in rows if row.get("status") == args.status]
    return _print_rows(rows)


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
    root = _root(args)
    with _operator_lock(root):
        _publish(root)
    print("published generated/manifest.json (atomic contract snapshot)")
    return 0


# ---------------------------------------------------------------- capture
def cmd_capture(args) -> int:
    """Judgment-free capture into work/inbox/ (ARCHITECTURE §3.3: no naming,
    no filing — the operator routes later)."""
    root = _root(args)
    with _operator_lock(root):
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
            capture_text = args.text if args.text is not None else sys.stdin.read()
            if not capture_text.strip():
                print("los: nothing to capture (empty input)", file=sys.stderr)
                return 2
            slug = re.sub(r"[^a-z0-9]+", "-",
                          (args.title or capture_text).lower()).strip("-")[:40] or "capture"
            target = inbox / f"{stamp}-{slug}.md"
            body = (f"# {args.title}\n\n{capture_text}\n" if args.title
                    else capture_text.rstrip() + "\n")
            _atomic_text(target, body)

    print(f"captured -> {target.relative_to(root)}")
    _record_touched(root, [target])
    print("routing is the operator's job (WORKFLOWS §21); the inbox trends "
          "toward empty")
    return 0


# --------------------------------------------------------- curriculum writes
def _session_ledger(root: Path) -> Path:
    token = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}-touched.json"


def _record_touched(root: Path, paths) -> None:
    ledger = _session_ledger(root)
    current: set[str] = set()
    if ledger.is_file():
        try:
            current.update(json.loads(ledger.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            current.clear()
    for path in paths:
        p = Path(path)
        try:
            rel = p.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        if rel not in {"Untitled.canvas", "Untitled 1.canvas", "Untitled 2.canvas"}:
            current.add(rel)
    _atomic_text(ledger, json.dumps(sorted(current), indent=2) + "\n")


def _write_transaction(root: Path, writes: dict[Path, str], touched_extra=(),
                       *, prevalidated: bool = False) -> tuple[int, list]:
    """Apply authored writes atomically enough to validate and roll back as a set."""
    backups: dict[Path, str | None] = {
        path: path.read_text(encoding="utf-8") if path.is_file() else None
        for path in writes
    }
    for path, content in writes.items():
        _atomic_text(path, content)
    if not prevalidated:
        errors = [issue for issue in validate(load_repo(root), online=False)
                  if issue.severity == "E"]
        if errors:
            for path, old in backups.items():
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_text(path, old)
            return 1, errors
    _publish(root)
    _record_touched(root, [*writes, *touched_extra])
    return 0, []


def _unit_map_or_error(root: Path, unit_id: str):
    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        print(f"los: unit not found: {unit_id}", file=sys.stderr)
        return repo, None, None
    map_id = unit.data.get("current_study_map")
    study_map = repo.study_maps.get(map_id) if map_id else None
    if study_map is None:
        print(f"los: unit has no current study map: {unit_id}", file=sys.stderr)
        return repo, unit, None
    return repo, unit, study_map


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Keep authored YAML deterministic even when an input package uses anchors."""

    def ignore_aliases(self, data):  # noqa: ANN001 - PyYAML callback signature
        return True


def _dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_NoAliasSafeDumper, sort_keys=False,
                     allow_unicode=True, width=100)


def _render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()


def _replace_h2_section(body: str, heading: str, content: str) -> str:
    """Replace one required workspace section without disturbing its neighbours."""
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\s*\n.*?(?=^## |\Z)"
    )
    if not pattern.search(body):
        raise ValueError(f"workspace section not found: {heading}")
    replacement = f"## {heading}\n\n{content.strip()}\n\n"
    return pattern.sub(replacement, body, count=1).rstrip() + "\n"


def _replace_registry_list_record(content: str, record_id: str, record: dict) -> str:
    """Render one record in a top-level YAML list without reformatting siblings."""
    lines = content.splitlines(keepends=True)
    id_line = next((i for i, line in enumerate(lines)
                    if re.match(rf"^[ ]*(?:- )?id: {re.escape(record_id)}[ ]*$",
                                line.rstrip("\r\n"))), None)
    if id_line is None:
        raise ValueError(f"registry record not found in source text: {record_id}")
    id_indent = len(lines[id_line]) - len(lines[id_line].lstrip(" "))
    if lines[id_line].lstrip(" ").startswith("- id:"):
        start = id_line
        item_indent = " " * id_indent
    else:
        item_indent = " " * max(0, id_indent - 2)
        start = next((i for i in range(id_line, -1, -1)
                      if lines[i].startswith(item_indent + "- ")), None)
        if start is None:
            raise ValueError(f"registry list item not found for: {record_id}")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith(item_indent + "- ")), len(lines))
    rendered = _dump_yaml(record).rstrip().splitlines()
    replacement = item_indent + "- " + rendered[0] + "\n"
    replacement += "\n".join(item_indent + "  " + line if line else ""
                              for line in rendered[1:])
    replacement += "\n\n"
    return "".join(lines[:start]) + replacement + "".join(lines[end:]).lstrip("\n")


_PLAN_COMPLETENESS_CHECKS = (
    "local_inventory_complete",
    "linked_inventory_complete",
    "materials_opened_and_content_checked",
    "current_and_prior_scope_reconciled",
    "duplicates_and_numbering_checked",
    "exclusions_and_unresolved_gaps_recorded",
)


def _module_plan_contract_problems(root: Path, package: dict) -> list[str]:
    """Verify the human review evidence required before a plan is executable."""
    problems: list[str] = []
    contract = package.get("plan_contract")
    if not isinstance(contract, dict) or contract.get("version") != 1:
        return ["plan_contract.version must be 1 (see system/PLAN-CREATION-SOP.md)"]
    audit_ref = contract.get("coverage_audit")
    if not isinstance(audit_ref, str) or not audit_ref.strip():
        problems.append("plan_contract.coverage_audit must name the completed audit")
    else:
        audit = (root / audit_ref).resolve()
        try:
            audit.relative_to(root.resolve())
        except ValueError:
            problems.append("plan_contract.coverage_audit must stay inside the repository")
        else:
            if not audit.is_file():
                problems.append(f"coverage audit does not exist: {audit_ref}")
            else:
                audit_text = audit.read_text(encoding="utf-8")
                for marker in ("## Local", "## Linked", "## Completeness"):
                    if marker not in audit_text:
                        problems.append(
                            f"coverage audit lacks required section marker: {marker}"
                        )
    checks = contract.get("checks")
    if not isinstance(checks, dict):
        problems.append("plan_contract.checks must be a mapping")
    else:
        for key in _PLAN_COMPLETENESS_CHECKS:
            if checks.get(key) is not True:
                problems.append(f"plan_contract.checks.{key} must be true")
    return problems


def _unit_source_refs(unit_data: dict, map_data: dict | None) -> set[str]:
    refs: set[str] = set()
    for field in ("scope_sources", "source_selections"):
        for entry in unit_data.get(field, []) or []:
            sid = entry.get("source_id") if isinstance(entry, dict) else None
            if isinstance(sid, str):
                refs.add(sid)
    if isinstance(map_data, dict):
        for stage in map_data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for field in ("resources", "source_feedback"):
                for entry in stage.get(field, []) or []:
                    sid = entry.get("source_id") if isinstance(entry, dict) else None
                    if isinstance(sid, str):
                        refs.add(sid)
    return refs


def _module_plan_routing_problems(repo, module_id: str, package: dict) -> list[str]:
    """Catch source omissions that ordinary referential validation cannot see."""
    source_map = package.get("source_map")
    if source_map is None:
        source_map = repo.module_source_maps.get(module_id, {})
    routes: dict[str, set[str]] = {}
    source_entries = source_map.get("sources", []) if isinstance(source_map, dict) else []
    for entry in source_entries or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("source_id"), str):
            continue
        routes.setdefault(entry["source_id"], set()).update(entry.get("unit_routes", []) or [])

    units: dict[str, tuple[dict, dict | None]] = {}
    for uid, unit in repo.units.items():
        if unit.module_id != module_id:
            continue
        study_map = repo.study_maps.get(unit.data.get("current_study_map"))
        units[uid] = (unit.data, study_map.data if study_map else None)
    for entry in package.get("units", []) or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("unit"), dict):
            continue
        uid = entry["unit"].get("id")
        if isinstance(uid, str):
            units[uid] = (entry["unit"], entry.get("study_map"))

    problems: list[str] = []
    for uid, (unit_data, map_data) in sorted(units.items()):
        for sid in sorted(_unit_source_refs(unit_data, map_data)):
            if sid not in routes:
                problems.append(f"{uid} uses {sid}, but the module source map omits it")
            elif uid not in routes[sid]:
                problems.append(f"{uid} uses {sid}, but its source-map unit_routes omit the unit")
    for update in package.get("workspace_updates", []) or []:
        if not isinstance(update, dict):
            continue
        workspace = repo.workspaces.get(update.get("id"))
        if workspace is None or set(workspace.meta.get("module_ids", []) or []) != {module_id}:
            continue
        for sid in update.get("sources", []) or []:
            if sid not in routes:
                problems.append(
                    f"workspace {update.get('id')} lists {sid}, but the module source map omits it"
                )
    return problems


def _module_plan_validation_errors(root: Path, writes: dict[Path, str]) -> list:
    """Validate planned files in a small shadow repository without canonical writes."""
    ignored_at_root = {
        ".git", ".obsidian", ".pytest_cache", ".venv", "generated",
        "migration", "tests", "tools",
    }

    def ignore_names(directory, names):
        directory = Path(directory).resolve()
        ignored = {"__pycache__"}
        if directory == root.resolve():
            ignored.update(ignored_at_root)
        if directory == (root / "knowledge").resolve():
            ignored.add("attachments")
        return [name for name in names if name in ignored]

    with tempfile.TemporaryDirectory(prefix="learningos-plan-check-") as tmp:
        shadow = Path(tmp) / "repository"
        shutil.copytree(root, shadow, symlinks=True, ignore=ignore_names)
        attachments = root / "knowledge" / "attachments"
        if attachments.exists():
            link = shadow / "knowledge" / "attachments"
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(attachments, target_is_directory=True)
        for external_name in ("materials", "projects"):
            external = root.parent / external_name
            if external.exists():
                (shadow.parent / external_name).symlink_to(external, target_is_directory=True)
        for path, content in writes.items():
            try:
                rel = path.resolve().relative_to(root.resolve())
            except ValueError:
                raise ValueError(f"planned write escapes repository: {path}") from None
            _atomic_text(shadow / rel, content)
        return [issue for issue in validate(load_repo(shadow), online=False)
                if issue.severity == "E"
                or (issue.severity == "W" and issue.code != "HYGIENE-VIEWS")]


def cmd_module_plan_import(args) -> int:
    """Apply one reviewable, module-scoped curriculum plan as a transaction.

    This gateway exists for the structural part of WORKFLOWS §23: a lecture
    batch may add units, their current study maps, module source routing, and
    explicit workspace joins together. It never deletes units or creates
    durable notes, and every stage remains bounded to the requested module.
    """
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such module plan file: {source}", file=sys.stderr)
        return 2
    try:
        package = yaml.safe_load(source.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"los: invalid module-plan YAML: {exc}", file=sys.stderr)
        return 2
    if not isinstance(package, dict) or package.get("module_id") != args.module_id:
        print("los: module plan must be a mapping with the requested module_id",
              file=sys.stderr)
        return 2
    contract_problems = _module_plan_contract_problems(root, package)
    if contract_problems:
        print("los: module plan contract failed; no canonical files were written",
              file=sys.stderr)
        for problem in contract_problems:
            print(f"- {problem}", file=sys.stderr)
        return 2
    if not args.check and not args.expected_snapshot:
        print("los: module plan import requires --expected-snapshot; run --check first, "
              "then copy snapshot.snapshot_id from bootstrap", file=sys.stderr)
        return 2

    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        module = repo.modules.get(args.module_id)
        if module is None:
            print(f"los: module not found: {args.module_id}", file=sys.stderr)
            return 2
        module_path = repo.module_origins[args.module_id]
        writes: dict[Path, str] = {}

        module_patch = package.get("module_patch", {}) or {}
        if not isinstance(module_patch, dict) or module_patch.get("id", args.module_id) != args.module_id:
            print("los: module_patch must stay inside the requested module", file=sys.stderr)
            return 2
        module_data = copy.deepcopy(module)
        module_data.update(module_patch)
        module_data["id"] = args.module_id
        writes[module_path] = _dump_yaml(module_data)

        source_map = package.get("source_map")
        if source_map is not None:
            if not isinstance(source_map, dict) or source_map.get("module_id") != args.module_id:
                print("los: source_map must belong to the requested module", file=sys.stderr)
                return 2
            target = repo.module_source_map_origins.get(
                args.module_id, module_path.parent / "source-map.yaml")
            writes[target] = _dump_yaml(source_map)

        source_patches = package.get("source_patches", []) or []
        if not isinstance(source_patches, list):
            print("los: source_patches must be a list", file=sys.stderr)
            return 2
        registry_texts: dict[Path, str] = {}
        patched_source_ids: set[str] = set()
        for patch in source_patches:
            sid = patch.get("id") if isinstance(patch, dict) else None
            if not sid or sid not in repo.sources or sid in patched_source_ids:
                print(f"los: source patch targets an unknown source: {sid}", file=sys.stderr)
                return 2
            patched_source_ids.add(sid)
            origin = repo.source_origins[sid]
            record = copy.deepcopy(repo.sources[sid])
            record.update(copy.deepcopy(patch))
            content = registry_texts.get(origin, origin.read_text(encoding="utf-8"))
            try:
                registry_texts[origin] = _replace_registry_list_record(content, sid, record)
            except ValueError as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
        writes.update(registry_texts)

        units = package.get("units", []) or []
        if not isinstance(units, list):
            print("los: units must be a list", file=sys.stderr)
            return 2
        seen_units: set[str] = set()
        for entry in units:
            unit_data = entry.get("unit") if isinstance(entry, dict) else None
            map_data = entry.get("study_map") if isinstance(entry, dict) else None
            uid = unit_data.get("id") if isinstance(unit_data, dict) else None
            if not uid or uid in seen_units or unit_data.get("module_id") != args.module_id:
                print(f"los: invalid or duplicate module unit: {uid}", file=sys.stderr)
                return 2
            seen_units.add(uid)
            unit_dir = module_path.parent / "units" / uid
            writes[unit_dir / "unit.yaml"] = _dump_yaml(unit_data)
            if map_data is None:
                continue
            if not isinstance(map_data, dict) or map_data.get("unit_id") != uid:
                print(f"los: study map must belong to {uid}", file=sys.stderr)
                return 2
            writes[unit_dir / "study-map.yaml"] = _dump_yaml(map_data)
            prefix = f"curriculum/modules/{args.module_id}/units/{uid}/stages/"
            for stage in map_data.get("stages", []) or []:
                note_ref = stage.get("working_note") if isinstance(stage, dict) else None
                if not isinstance(note_ref, str) or not note_ref.startswith(prefix) \
                        or not note_ref.endswith("/notes.md"):
                    print(f"los: stage note escapes module/unit scope: {note_ref}", file=sys.stderr)
                    return 2
                note = root / note_ref
                if not note.exists():
                    writes[note] = ""

        workspace_updates = package.get("workspace_updates", []) or []
        if not isinstance(workspace_updates, list):
            print("los: workspace_updates must be a list", file=sys.stderr)
            return 2
        for update in workspace_updates:
            wid = update.get("id") if isinstance(update, dict) else None
            workspace = repo.workspaces.get(wid)
            if workspace is None or workspace.archived or args.module_id not in workspace.meta.get("module_ids", []):
                print(f"los: workspace update is not joined to {args.module_id}: {wid}", file=sys.stderr)
                return 2
            meta = copy.deepcopy(workspace.meta)
            for key in ("sources", "unit_ids"):
                if key in update:
                    meta[key] = copy.deepcopy(update[key])
            body = workspace.body
            try:
                for heading, content in (update.get("sections", {}) or {}).items():
                    body = _replace_h2_section(body, str(heading), str(content))
            except ValueError as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
            writes[workspace.path] = _render_frontmatter(meta, body)

        routing_problems = _module_plan_routing_problems(repo, args.module_id, package)
        if routing_problems:
            print("los: module plan routing preflight failed; no canonical files were written",
                  file=sys.stderr)
            for problem in routing_problems:
                print(f"- {problem}", file=sys.stderr)
            return 1
        try:
            errors = _module_plan_validation_errors(root, writes)
        except ValueError as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        if errors:
            print("los: module plan validation preflight failed; no canonical files were written",
                  file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return 1
        if args.check:
            result = {"ok": True, "mode": "check", "module_id": args.module_id,
                      "units_checked": sorted(seen_units), "files_checked": len(writes),
                      "canonical_files_written": 0}
        else:
            code, errors = _write_transaction(root, writes, prevalidated=True)
            if code:  # Defensive: prevalidated transactions do not normally reach this branch.
                print("los: module plan import failed", file=sys.stderr)
                for issue in errors[:12]:
                    print(issue, file=sys.stderr)
                return code
            result = {"ok": True, "mode": "apply", "module_id": args.module_id,
                      "units_written": sorted(seen_units), "files_written": len(writes)}
    print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_note_revise(args) -> int:
    """Replace one existing note after explicit, reviewable approval.

    IDs, paths, and roles are held stable; this is a semantic revision gateway,
    not a rename, move, role change, merge, or split operation.
    """
    if not args.approve:
        print("los: note revision requires --approve after reviewing the full replacement",
              file=sys.stderr)
        return 2
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such revised note file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note = repo.notes.get(args.note_id)
        if note is None:
            print(f"los: note not found: {args.note_id}", file=sys.stderr)
            return 2
        content = source.read_text(encoding="utf-8")
        try:
            meta, _ = parse_frontmatter(content, source)
        except Exception as exc:  # LoaderError is intentionally presented as usage failure.
            print(f"los: invalid revised note: {exc}", file=sys.stderr)
            return 2
        if meta.get("id") != args.note_id or meta.get("type") != "note":
            print("los: revised note must preserve the requested note id and type", file=sys.stderr)
            return 2
        if meta.get("role") != note.meta.get("role"):
            print("los: note-revise cannot change a note role", file=sys.stderr)
            return 2
        code, errors = _write_transaction(root, {note.path: content.rstrip() + "\n"})
        if code:
            print("los: note revision rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "note_id": args.note_id,
                      "path": note.path.relative_to(root).as_posix()}, ensure_ascii=False))
    return 0


def _stage(data: dict, stage_id: str):
    return next((row for row in data.get("stages", []) or []
                 if isinstance(row, dict) and row.get("id") == stage_id), None)


def cmd_unit_map_import(args) -> int:
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such map file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        unit = repo.units.get(args.unit_id)
        if unit is None:
            print(f"los: unit not found: {args.unit_id}", file=sys.stderr)
            return 2
        target = unit.path.parent / "study-map.yaml"
        if target.exists() and not args.replace:
            print("los: this unit already has a current study map; use --replace to make Git the prior-version archive",
                  file=sys.stderr)
            return 2
        try:
            data = yaml.safe_load(source.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            print(f"los: invalid study-map YAML: {exc}", file=sys.stderr)
            return 2
        if not isinstance(data, dict) or data.get("unit_id") != args.unit_id:
            print("los: imported map must be a mapping with the requested unit_id", file=sys.stderr)
            return 2
        unit_data = dict(unit.data)
        unit_data["current_study_map"] = data.get("id")
        unit_data["status"] = "ready"
        writes = {target: _dump_yaml(data), unit.path: _dump_yaml(unit_data)}
        for stage in data.get("stages", []) or []:
            note_ref = stage.get("working_note") if isinstance(stage, dict) else None
            if note_ref:
                note = root / str(note_ref)
                if not note.exists():
                    writes[note] = ""
        code, errors = _write_transaction(root, writes)
        if code:
            print("los: study map import rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "study_map_id": data.get("id")}, ensure_ascii=False))
    return 0


def cmd_stage_note(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        stage = _stage(study_map.data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        target = root / str(stage.get("working_note", ""))
        if not stage.get("working_note"):
            print("los: stage has no working_note", file=sys.stderr)
            return 2
        value = args.text if args.text is not None else sys.stdin.read()
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        if args.replace:
            updated = value.rstrip() + ("\n" if value.strip() else "")
        else:
            divider = "\n" if old and not old.endswith("\n\n") else ""
            updated = old + divider + value.rstrip() + "\n"
        code, errors = _write_transaction(root, {target: updated})
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "working_note": stage["working_note"]},
                     ensure_ascii=False))
    return 0


def cmd_stage_progress(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None or unit is None:
            return 2
        data = copy.deepcopy(study_map.data)
        unit_data = copy.deepcopy(unit.data)
        stages = data.get("stages", []) or []
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        action = args.status
        if action in {"active", "revisit"}:
            for other in stages:
                if other.get("status") in {"active", "paused"}:
                    other["status"] = "pending"
            stage["status"] = "active"
            stage.pop("completed", None)
            data["current_stage"] = stage["id"]
            data["status"] = "active"
            unit_data["status"] = "active"
        elif action == "paused":
            stage["status"] = "paused"
            data["current_stage"] = stage["id"]
            data["status"] = "paused"
            unit_data["status"] = "paused"
        else:
            if stage.get("status") != "active":
                print("los: complete/skip applies only to the active stage; activate it first",
                      file=sys.stderr)
                return 2
            stage["status"] = "complete" if action == "complete" else "skipped"
            if action == "complete":
                stage["completed"] = _dt.date.today().isoformat()
            following = next((row for row in stages[stages.index(stage) + 1:]
                              if row.get("status") == "pending"), None)
            if following:
                following["status"] = "active"
                data["current_stage"] = following["id"]
                data["status"] = "active"
                unit_data["status"] = "active"
            else:
                data["status"] = "ready-to-shelve"
                data.setdefault("shelving", {})["state"] = "draft"
                unit_data["status"] = "ready-to-shelve"
        code, errors = _write_transaction(root, {
            study_map.path: _dump_yaml(data), unit.path: _dump_yaml(unit_data)})
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id, "stage_id": args.stage_id,
                      "status": action, "map_status": data["status"],
                      "current_stage": data["current_stage"]}, ensure_ascii=False))
    return 0


def cmd_stage_attach(args) -> int:
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        note_path = root / stage["working_note"]
        attachment_dir = note_path.parent / "attachments"
        target = attachment_dir / source.name
        if target.exists():
            stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            target = attachment_dir / f"{stamp}-{source.name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rel = target.relative_to(root).as_posix()
        stage.setdefault("attachments", []).append({"path": rel, "label": args.label or source.stem})
        code, errors = _write_transaction(root, {study_map.path: _dump_yaml(data)}, [target])
        if code:
            target.unlink(missing_ok=True)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "attachment": rel}, ensure_ascii=False))
    return 0


def cmd_source_feedback(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        if args.source_id not in repo.sources:
            print(f"los: source not found: {args.source_id}", file=sys.stderr)
            return 2
        data = copy.deepcopy(study_map.data)
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        entry = {"source_id": args.source_id, "feedback": args.feedback,
                 "recorded": _dt.date.today().isoformat()}
        if args.note:
            entry["note"] = args.note
        stage.setdefault("source_feedback", []).append(entry)
        code, errors = _write_transaction(root, {study_map.path: _dump_yaml(data)})
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "feedback": entry}, ensure_ascii=False))
    return 0


def cmd_detour_create(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None or unit is None:
            return 2
        data = copy.deepcopy(study_map.data)
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        base = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-") or "gap"
        did = f"detour-{base}"
        existing = {row.get("id") for row in data.get("detours", []) or []}
        if did in existing:
            suffix = 2
            while f"{did}-{suffix}" in existing:
                suffix += 1
            did = f"{did}-{suffix}"
        detour = {"id": did, "title": args.title, "spawned_by_stage": args.stage_id,
                  "classification": args.classification, "status": "open",
                  "return_to_stage": args.stage_id}
        data.setdefault("detours", []).append(detour)
        stage["detour_id"] = did
        if args.classification == "required-now":
            stage["status"] = "paused"
            data["status"] = "paused"
            unit_data = copy.deepcopy(unit.data)
            unit_data["status"] = "paused"
        else:
            unit_data = unit.data
        code, errors = _write_transaction(root, {
            study_map.path: _dump_yaml(data), unit.path: _dump_yaml(unit_data)})
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "detour": detour}, ensure_ascii=False))
    return 0


def cmd_detour_resolve(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None or unit is None:
            return 2
        data = copy.deepcopy(study_map.data)
        detour = next((row for row in data.get("detours", []) or []
                       if row.get("id") == args.detour_id), None)
        if detour is None:
            print(f"los: detour not found: {args.detour_id}", file=sys.stderr)
            return 2
        detour["status"] = "resolved"
        if args.resolution:
            detour["resolution"] = args.resolution
        target_stage = _stage(data, detour["return_to_stage"])
        for other in data.get("stages", []) or []:
            if other.get("status") in {"active", "paused"}:
                other["status"] = "pending"
        target_stage["status"] = "active"
        data["current_stage"] = target_stage["id"]
        data["status"] = "active"
        unit_data = copy.deepcopy(unit.data)
        unit_data["status"] = "active"
        code, errors = _write_transaction(root, {
            study_map.path: _dump_yaml(data), unit.path: _dump_yaml(unit_data)})
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "detour_id": args.detour_id,
                      "return_to_stage": target_stage["id"]}, ensure_ascii=False))
    return 0


def cmd_shelving_prepare(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        items = []
        if args.items_file:
            raw = json.loads(Path(args.items_file).read_text(encoding="utf-8"))
            items = raw.get("items", raw) if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                print("los: shelving items file must contain a JSON list", file=sys.stderr)
                return 2
        proposal_path = study_map.path.parent / "shelving-proposal.md"
        lines = ["# Shelving proposal review packet", "",
                 "> Operational proposal only. No canonical change is applied until selected IDs are explicitly approved.", ""]
        for stage in data.get("stages", []) or []:
            lines.extend([f"## {stage.get('title', stage.get('id'))}", ""])
            note = root / str(stage.get("working_note", ""))
            lines.append(note.read_text(encoding="utf-8", errors="replace") if note.is_file()
                         else "*(No stage note yet.)*")
            lines.append("")
            if stage.get("attachments"):
                lines.append("Attachments: " + ", ".join(a["path"] for a in stage["attachments"]))
                lines.append("")
        shelving = data.setdefault("shelving", {})
        shelving.update({"state": "proposed" if items else "draft",
                          "proposal_path": proposal_path.relative_to(root).as_posix(),
                          "summary": args.summary or "Review stage notes and attachments without rewriting learner wording."})
        if items:
            shelving["items"] = items
        code, errors = _write_transaction(root, {
            proposal_path: "\n".join(lines).rstrip() + "\n",
            study_map.path: _dump_yaml(data)})
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "proposal_path": shelving["proposal_path"],
                      "state": shelving["state"]}, ensure_ascii=False))
    return 0


def _approved_destination(root: Path, item: dict) -> Path | None:
    rel = str(item.get("destination", ""))
    target = (root / rel).resolve()
    allowed = (root / "knowledge" / "notes").resolve(), (root / "knowledge" / "garden").resolve()
    if not any(parent == target or parent in target.parents for parent in allowed):
        return None
    return target


def cmd_shelving_apply(args) -> int:
    if not args.approve:
        print("los: shelving apply requires --approve and explicit selected proposal IDs",
              file=sys.stderr)
        return 2
    root = _root(args)
    selected = set(args.selected)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        shelving = data.get("shelving") or {}
        items = [item for item in shelving.get("items", []) or []
                 if item.get("id") in selected]
        if not items or {item.get("id") for item in items} != selected:
            print("los: every selected ID must exist in the current proposal", file=sys.stderr)
            return 2
        writes: dict[Path, str] = {}
        for item in items:
            target = _approved_destination(root, item)
            if target is None or target.exists():
                print(f"los: unsafe or existing shelving destination: {item.get('destination')}",
                      file=sys.stderr)
                return 2
            content = item.get("content")
            if not isinstance(content, str) or not content.strip():
                print(f"los: proposal item {item.get('id')} has no reviewable content", file=sys.stderr)
                return 2
            writes[target] = content.rstrip() + "\n"
        shelving["state"] = "applied"
        writes[study_map.path] = _dump_yaml(data)
        code, errors = _write_transaction(root, writes)
        if code:
            print("los: approved shelving changes failed validation and were rolled back",
                  file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "applied": sorted(selected)}, ensure_ascii=False))
    return 0


def cmd_session_end(args) -> int:
    root = _root(args)
    ledger = _session_ledger(root)
    touched = json.loads(ledger.read_text(encoding="utf-8")) if ledger.is_file() else []
    touched = [path for path in touched
               if path not in {"Untitled.canvas", "Untitled 1.canvas", "Untitled 2.canvas"}]
    # `validate.py` resolves its repository from its own location unless told
    # otherwise, so a bare `cwd=root` would validate the repository the tools
    # live in — not the one this session touched. Pass the root explicitly.
    validation = subprocess.run(
        [sys.executable, str(TOOLS / "validate.py"), "--root", str(root)], cwd=root,
        capture_output=True, text=True)
    if validation.returncode != 0 or "0 warning(s)" not in validation.stdout:
        print(validation.stdout, end="")
        print(validation.stderr, end="", file=sys.stderr)
        return validation.returncode or 1
    with _operator_lock(root):
        _publish(root)
    all_changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
        cwd=root, capture_output=True, text=True, timeout=30).stdout.splitlines()
    owned = [line for line in all_changed if line[3:] in touched]
    unrelated = [line for line in all_changed if line[3:] not in touched]
    payload = {"ok": True, "touched": touched, "owned_changes": owned,
               "unrelated_changes": unrelated, "committed": False, "pushed": False}
    if not args.commit_message:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not touched:
        print("los: no files were touched through this learning session", file=sys.stderr)
        return 2
    subprocess.run(["git", "add", "--", *touched], cwd=root, check=True, timeout=30)
    commit = subprocess.run(["git", "commit", "-m", args.commit_message], cwd=root,
                            capture_output=True, text=True, timeout=180)
    if commit.returncode != 0:
        print(commit.stdout, end="")
        print(commit.stderr, end="", file=sys.stderr)
        return commit.returncode
    payload["committed"] = True
    if args.push:
        pushed = subprocess.run(["git", "push"], cwd=root, capture_output=True,
                                text=True, timeout=180)
        if pushed.returncode != 0:
            print(pushed.stdout, end="")
            print(pushed.stderr, end="", file=sys.stderr)
            return pushed.returncode
        payload["pushed"] = True
    ledger.unlink(missing_ok=True)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------- learning paths
def cmd_path_note(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, learning_path = _path_or_error(root, args.path_id)
        if learning_path is None:
            return 2
        stage = next((s for s in learning_path.data.get("stages", [])
                      if s.get("id") == args.stage_id), None)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        note_ref = stage.get("notes_path")
        if not note_ref:
            print(f"los: stage has no notes_path: {args.stage_id}", file=sys.stderr)
            return 2
        text_value = args.text if args.text is not None else sys.stdin.read()
        target = root / str(note_ref)
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        if args.replace:
            updated = text_value.rstrip() + ("\n" if text_value.strip() else "")
        else:
            divider = "\n" if old and not old.endswith("\n\n") else ""
            updated = old + divider + text_value.rstrip() + "\n"
        _atomic_text(target, updated)
        _publish(root)
    print(json.dumps({"ok": True, "path_id": args.path_id,
                      "stage_id": args.stage_id, "notes_path": note_ref},
                     ensure_ascii=False))
    return 0


def cmd_path_progress(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, learning_path = _path_or_error(root, args.path_id)
        if learning_path is None:
            return 2
        data = learning_path.data
        stages = data.get("stages", []) or []
        stage = next((s for s in stages if s.get("id") == args.stage_id), None)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        if args.status in {"complete", "skipped"} and stage.get("status") != "active":
            print("los: only the active stage can be completed or skipped; activate it first",
                  file=sys.stderr)
            return 2
        if args.status == "active":
            for other in stages:
                if other.get("status") == "active":
                    other["status"] = "pending"
            stage["status"] = "active"
            stage.pop("completed", None)
            data["current_stage"] = stage["id"]
            data["status"] = "active"
        else:
            stage["status"] = args.status
            if args.status == "complete":
                stage["completed"] = _dt.date.today().isoformat()
            following = next((s for s in stages[stages.index(stage) + 1:]
                              if s.get("status") == "pending"), None)
            if following:
                following["status"] = "active"
                data["current_stage"] = following["id"]
                data["status"] = "active"
            else:
                data["status"] = "ready-to-shelve"
                shelving = data.setdefault("shelving", {})
                shelving["state"] = "draft"
        data["updated"] = _dt.date.today().isoformat()
        original = learning_path.path.read_text(encoding="utf-8")
        rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        _atomic_text(learning_path.path, rendered)
        repo_after = load_repo(root)
        errors = [i for i in validate(repo_after, online=False) if i.severity == "E"]
        if errors:
            _atomic_text(learning_path.path, original)
            print("los: path update rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return 1
        _publish(root)
    print(json.dumps({"ok": True, "path_id": args.path_id,
                      "stage_id": args.stage_id, "status": args.status,
                      "path_status": data["status"],
                      "current_stage": data["current_stage"]}, ensure_ascii=False))
    return 0


def cmd_path_attach(args) -> int:
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, learning_path = _path_or_error(root, args.path_id)
        if learning_path is None:
            return 2
        data = learning_path.data
        stage = next((s for s in data.get("stages", [])
                      if s.get("id") == args.stage_id), None)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        workspace = learning_path.path.parent.parent
        attachment_dir = workspace / "scratch" / "paths" / learning_path.id \
            / "attachments" / stage["id"]
        target = attachment_dir / source.name
        if target.exists():
            stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            target = attachment_dir / f"{stamp}-{source.name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rel = target.relative_to(root).as_posix()
        stage.setdefault("attachments", []).append({
            "path": rel, "label": args.label or source.stem})
        data["updated"] = _dt.date.today().isoformat()
        original = learning_path.path.read_text(encoding="utf-8")
        _atomic_text(learning_path.path,
                     yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        errors = [i for i in validate(load_repo(root), online=False) if i.severity == "E"]
        if errors:
            _atomic_text(learning_path.path, original)
            target.unlink(missing_ok=True)
            print("los: attachment rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return 1
        _publish(root)
    print(json.dumps({"ok": True, "path_id": args.path_id,
                      "stage_id": args.stage_id, "attachment": rel}, ensure_ascii=False))
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

    p = sub.add_parser("capabilities", help="discover the stable operator contract")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_capabilities)

    p = sub.add_parser("bootstrap", help="machine bootstrap with active learning paths")
    p.set_defaults(func=cmd_bootstrap)

    p = sub.add_parser("search", help="search the complete fresh projection")
    p.add_argument("query")
    p.add_argument("--type", default=None, help="optional record type")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("inspect", help="inspect one record by stable id")
    p.add_argument("id")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("related", help="list records related to one stable id")
    p.add_argument("id")
    p.set_defaults(func=cmd_related)

    p = sub.add_parser("program-list", help="list programs and boundary areas")
    p.set_defaults(func=cmd_program_list)

    p = sub.add_parser("module-list", help="list modules with optional program/status filters")
    p.add_argument("--program-id", default=None)
    p.add_argument("--status", default=None)
    p.set_defaults(func=cmd_module_list)

    p = sub.add_parser("unit-list", help="list units with optional module/component/status filters")
    p.add_argument("--module-id", default=None)
    p.add_argument("--component-id", default=None)
    p.add_argument("--status", default=None)
    p.set_defaults(func=cmd_unit_list)

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

    p = sub.add_parser("unit-map-import",
                       help="create/import the single current study map for a unit")
    p.add_argument("unit_id")
    p.add_argument("--file", required=True)
    p.add_argument("--replace", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_unit_map_import)

    p = sub.add_parser("module-plan-import",
                       help="transactionally import a standardized module plan and its units")
    p.add_argument("module_id")
    p.add_argument("--file", required=True)
    p.add_argument("--check", action="store_true",
                   help="run contract, routing, and shadow-repository validation without writing")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_module_plan_import)

    p = sub.add_parser("note-revise",
                       help="replace one existing note after explicit full-file review")
    p.add_argument("note_id")
    p.add_argument("--file", required=True)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_note_revise)

    p = sub.add_parser("stage-note", help="save or append a unit-stage working note")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("--text", default=None)
    p.add_argument("--replace", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_stage_note)

    p = sub.add_parser("stage-progress", help="activate, pause, complete, skip, or revisit a unit stage")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("status", choices=("active", "paused", "complete", "skipped", "revisit"))
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_stage_progress)

    p = sub.add_parser("stage-attach", help="attach a file inside a unit stage")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("--file", required=True)
    p.add_argument("--label", default=None)
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_stage_attach)

    p = sub.add_parser("source-feedback", help="record stage-local evidence about source usefulness")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("source_id")
    p.add_argument("feedback", choices=("helpful", "too-advanced", "wrong-perspective",
                                        "useful-for-derivation", "useful-for-review", "skipped"))
    p.add_argument("--note", default=None)
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_source_feedback)

    p = sub.add_parser("detour-create", help="record a prerequisite detour with a return stage")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("--title", required=True)
    p.add_argument("--classification", required=True,
                   choices=("required-now", "helpful-now", "deferred", "reference-only"))
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_detour_create)

    p = sub.add_parser("detour-resolve", help="resolve a detour and return to its originating stage")
    p.add_argument("unit_id")
    p.add_argument("detour_id")
    p.add_argument("--resolution", default=None)
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_detour_resolve)

    p = sub.add_parser("shelving-prepare", help="prepare a review packet; never applies canonical changes")
    p.add_argument("unit_id")
    p.add_argument("--items-file", default=None,
                   help="optional JSON proposal items produced with explicit unit context")
    p.add_argument("--summary", default=None)
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_shelving_prepare)

    p = sub.add_parser("shelving-apply", help="apply only explicitly approved proposal IDs")
    p.add_argument("unit_id")
    p.add_argument("--selected", nargs="+", required=True)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_shelving_apply)

    p = sub.add_parser("session-end", help="validate, show exact session-owned files, optionally commit/push")
    p.add_argument("--commit-message", default=None)
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=cmd_session_end)

    p = sub.add_parser("path-note", help="save or append working notes for one path stage")
    p.add_argument("path_id")
    p.add_argument("stage_id")
    p.add_argument("--text", default=None, help="note text (else stdin)")
    p.add_argument("--replace", action="store_true", help="replace this stage note")
    p.add_argument("--expected-snapshot", default=None,
                   help="optimistic concurrency token from manifest _generated.snapshot_id")
    p.set_defaults(func=cmd_path_note)

    p = sub.add_parser("path-progress", help="advance or activate a learning path stage")
    p.add_argument("path_id")
    p.add_argument("stage_id")
    p.add_argument("status", choices=("active", "complete", "skipped"))
    p.add_argument("--expected-snapshot", default=None,
                   help="optimistic concurrency token from manifest _generated.snapshot_id")
    p.set_defaults(func=cmd_path_progress)

    p = sub.add_parser("path-attach", help="copy handwriting/media into a stage-owned attachment folder")
    p.add_argument("path_id")
    p.add_argument("stage_id")
    p.add_argument("--file", required=True)
    p.add_argument("--label", default=None)
    p.add_argument("--expected-snapshot", default=None,
                   help="optimistic concurrency token from manifest _generated.snapshot_id")
    p.set_defaults(func=cmd_path_attach)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
