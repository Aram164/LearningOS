"""First-class project records: list, create, update."""

from __future__ import annotations

import copy
import json
import re
import sys
import yaml
from pathlib import Path
from .support import WriteRefused, _expected_ok, _expected_revisions_from_args, _fresh_manifest, _operator_lock, _print_rows, _read_structured_file, _root, _write_transaction

def _project_write(root: Path, data: dict, *, capability: str,
                   expected_revisions: dict[str, int]) -> tuple[int, dict]:
    project_id = data.get("id")
    if not isinstance(project_id, str) or not re.fullmatch(r"project-[a-z0-9]+(?:-[a-z0-9]+)*", project_id):
        raise WriteRefused("project id must match project-<slug>")
    if data.get("type") != "project":
        raise WriteRefused("project type must be 'project'")
    target = root / "projects" / "registry" / f"{project_id}.yaml"
    exists = target.is_file()
    if capability == "project.create" and exists:
        raise WriteRefused(f"project already exists: {project_id}")
    if capability == "project.update" and not exists:
        raise WriteRefused(f"project not found: {project_id}")
    if exists:
        current = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        if current.get("id") != project_id or current.get("type") != data.get("type"):
            raise WriteRefused("project update cannot change id or type")
    data = copy.deepcopy(data)
    data.setdefault("schema_version", 1)
    data.setdefault("revision", 0)
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    code, errors, confirmation = _write_transaction(
        root, {target: rendered}, capability=capability,
        expected_revisions=expected_revisions, artifact_ids=[project_id],
    )
    if code:
        return code, {"errors": [str(issue) for issue in errors]}
    return 0, {"project_id": project_id, **confirmation}


def _project_record(args) -> dict:
    """The project record, from wherever this invocation carried it.

    One command, two ways in: a path for a person at a shell, an inline object
    for a caller that already holds the record. The parser declares both as one
    required mutually exclusive group, so the generated capability schema says
    exactly this — which is the whole point. The gateway used to accept the
    inline form through a branch of its own, undeclared and unvalidated.
    """
    record = getattr(args, "project", None)
    if record is not None:
        if not isinstance(record, dict):
            raise WriteRefused("project must be an object")
        return record
    if not getattr(args, "file", None):
        raise WriteRefused("project record required: pass --file or --project")
    return _read_structured_file(args.file)


def cmd_project_list(args) -> int:
    manifest = _fresh_manifest(_root(args))
    rows = manifest.get("projects", [])
    if getattr(args, "status", None):
        rows = [row for row in rows if row.get("status") == args.status]
    return _print_rows(rows)


def cmd_project_create(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, getattr(args, "expected_snapshot", None)):
            return 3
        code, result = _project_write(
            root, _project_record(args), capability="project.create",
            expected_revisions=_expected_revisions_from_args(args),
        )
    if code:
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return code
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


def cmd_project_update(args) -> int:
    root = _root(args)
    data = _project_record(args)
    if data.get("id") != args.project_id:
        raise WriteRefused("project file id does not match command project_id")
    with _operator_lock(root):
        if not _expected_ok(root, getattr(args, "expected_snapshot", None)):
            return 3
        code, result = _project_write(
            root, data, capability="project.update",
            expected_revisions=_expected_revisions_from_args(args),
        )
    if code:
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return code
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0
