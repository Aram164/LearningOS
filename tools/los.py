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
from learning_os.loader import load_repo  # noqa: E402
from learning_os.rules import validate  # noqa: E402

TOOLS = Path(__file__).resolve().parent
CONTRACT_VERSION = 1


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


# ---------------------------------------------------- machine discovery/read
def _capabilities(root: Path) -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "gateway": "tools/los.py",
        "projection": "generated/manifest.json",
        "operator_contract": "system/OPERATOR.md",
        "commands": {
            "read": ["status", "capabilities", "bootstrap", "search", "inspect", "related"],
            "safe_writes": ["capture", "path-note", "path-progress", "path-attach", "generate"],
            "approval_gated": ["shelve"],
        },
        "rules": {
            "canonical_writes_require_operator": True,
            "shelving_requires_explicit_approval": True,
            "job_quarantine": True,
            "interfaces_read_projection_only": True,
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
    paths = [r for r in manifest["records"]
             if r.get("type") == "learning-path" and not r.get("archived")]
    payload = {
        "capabilities": _capabilities(root),
        "snapshot": manifest.get("_generated", {}),
        "active_learning_paths": paths,
        "next": "Inspect an active path, or ask the learner which subtopic to begin.",
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
    for key in ("concepts", "sources", "contexts", "notes"):
        ids.update(rec.get(key, []) or [])
    if rec.get("workspace_id"):
        ids.add(rec["workspace_id"])
    backlinks = manifest.get("backlinks", {})
    for table in ("concept_to_notes", "source_to_notes", "workspace_to_notes",
                  "module_to_workspaces"):
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
    print("routing is the operator's job (WORKFLOWS §21); the inbox trends "
          "toward empty")
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
