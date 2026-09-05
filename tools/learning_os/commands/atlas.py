"""Learner-authored Atlas changes. Every write uses the ordinary V2 transaction."""

from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import jsonschema
import yaml

from ..fingerprint import canonical_fingerprint
from ..loader import load_repo
from ..loading.yamlio import UniqueKeySafeLoader
from ..revisions import artifact_revision
from .support import (
    WriteRefused,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _render_frontmatter,
    _root,
    _write_transaction,
)

RELATION_ARTIFACT = "registry-concept-relations"


def _safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(f"Atlas cannot use a symlink: {relative}")
    return path


def _registries(root: Path) -> dict[Path, dict]:
    single = _safe(root, root / "knowledge/concept-relations.yaml")
    folder = _safe(root, root / "knowledge/concept-relations")
    paths = ([single] if single.exists() else []) + (
        sorted(folder.glob("*.yaml")) if folder.exists() else [])
    if single.exists() and len(paths) > 1:
        raise WriteRefused("both consolidated and partitioned relations exist")
    records = {}
    for path in paths:
        data = yaml.load(_safe(root, path).read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
        _schema(root, "concept-relations", data)
        records[path] = data
    return records


def _schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc


def _commit(root: Path, args, capability: str, writes: dict, ids: list[str], result: dict) -> int:
    code, errors, confirmation = _write_transaction(
        root, writes, capability=capability,
        expected_revisions=_expected_revisions_from_args(args), artifact_ids=ids,
    )
    if code:
        raise WriteRefused("; ".join(str(issue) for issue in errors[:12]))
    print(json.dumps({"ok": True, **result, **confirmation}, ensure_ascii=False))
    return 0


def cmd_atlas_context(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        snapshot = "sha256:" + canonical_fingerprint(root)
        if not _expected_ok(root, getattr(args, "expected_snapshot", None)):
            return 3
        repo = load_repo(root)
        if args.concept_id not in repo.concepts:
            raise WriteRefused("unknown concept")
        # This is a scoped editor read, not another full-manifest endpoint.
        rows = [copy.deepcopy(row) for data in _registries(root).values()
                for row in data["relations"]
                if args.concept_id in (row["from"], row["to"])]
        questions = []
        for note in repo.notes.values():
            question = note.meta.get("atlas_question")
            if not isinstance(question, dict):
                continue
            target = question["target"]
            ids = target.get("concepts", []) or [target.get("from"), target.get("to")]
            if args.concept_id in ids:
                questions.append({"id": note.id, "title": note.meta["title"],
                                  "path": note.path.relative_to(root).as_posix(),
                                  "revision": artifact_revision(root, note.id),
                                  **copy.deepcopy(question)})
        if snapshot != "sha256:" + canonical_fingerprint(root):
            raise WriteRefused("snapshot changed while reading Atlas")
        print(json.dumps({"schema_version": 1, "snapshot_id": snapshot,
                          "relation_revision": artifact_revision(root, RELATION_ARTIFACT),
                          "relations": rows, "questions": questions}, ensure_ascii=False))
    return 0


def cmd_concept_relations_change(args) -> int:
    root = _root(args)
    changes = args.change
    if not isinstance(changes, dict) or set(changes) != {"operations"}:
        raise WriteRefused("change must contain only operations")
    operations = changes["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 50:
        raise WriteRefused("supply between 1 and 50 explicit operations")
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        registries = _registries(root)
        changed = set()
        for operation in operations:
            if not isinstance(operation, dict):
                raise WriteRefused("operation must be an object")
            kind = operation.get("action")
            required = {"add": {"action", "new"}, "replace": {"action", "old", "new"},
                        "remove": {"action", "old"}}.get(kind)
            if required is None or set(operation) != required:
                raise WriteRefused("expected exact add, replace, or remove operation")
            for key in ("old", "new"):
                if key in operation:
                    _schema(root, "concept-relations", {"relations": [operation[key]]})
            if "old" in operation:
                matches = [(path, i) for path, data in registries.items()
                           for i, row in enumerate(data["relations"]) if row == operation["old"]]
                if len(matches) != 1:
                    raise WriteRefused("the exact previous relation no longer exists uniquely; reload and review")
                path, index = matches[0]
                if kind == "remove":
                    registries[path]["relations"].pop(index)
                else:
                    registries[path]["relations"][index] = copy.deepcopy(operation["new"])
            else:
                single = root / "knowledge/concept-relations.yaml"
                path = single if single in registries else root / "knowledge/concept-relations/atlas.yaml"
                _safe(root, path)
                registries.setdefault(path, {"relations": []})["relations"].append(copy.deepcopy(operation["new"]))
            changed.add(path)
        writes = {path: yaml.safe_dump(registries[path], sort_keys=False, allow_unicode=True)
                  for path in changed}
        # Existing validator rejects duplicates, unknown endpoints/sources and prerequisite cycles.
        return _commit(root, args, "concept.relations.change", writes,
                       [RELATION_ARTIFACT], {"operation_count": len(operations)})


def cmd_atlas_question_save(args) -> int:
    root = _root(args)
    question = args.question
    if not isinstance(question, dict):
        raise WriteRefused("question must be an object")
    allowed = {"id", "title", "text", "target", "state", "answer_notes"}
    if set(question) - allowed or not isinstance(question.get("id"), str):
        raise WriteRefused("question has unknown fields or no note id")
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note_id = question["id"]
        existing = repo.notes.get(note_id)
        if existing:
            if existing.meta.get("role") != "question" or "atlas_question" not in existing.meta:
                raise WriteRefused("this note is not an Atlas question")
            if "target" in question and question["target"] != existing.meta["atlas_question"]["target"]:
                raise WriteRefused("the original question target is preserved")
            meta, body, path = copy.deepcopy(existing.meta), existing.body, existing.path
        else:
            if not all(key in question for key in ("title", "text", "target")):
                raise WriteRefused("new questions require title, text and target")
            meta = {"id": note_id, "type": "note", "role": "question",
                    "title": question["title"], "created": date.today().isoformat(),
                    "authorship": "user", "atlas_question": {
                        "state": "open", "target": copy.deepcopy(question["target"])}}
            body = question["text"]
            # Validate id before it can be used as a filename.
            _schema(root, "note", meta)
            path = root / "knowledge/notes/questions" / f"{note_id}.md"
            if path.exists():
                raise WriteRefused("question destination already exists")
            target = question["target"]
            concept_ids = target.get("concepts", []) or [target.get("from"), target.get("to")]
            if any(cid not in repo.concepts for cid in concept_ids):
                raise WriteRefused("question target contains an unknown concept")
            if "from" in target and not any(all(row.get(k) == target[k] for k in ("from", "type", "to")) for row in repo.relations):
                raise WriteRefused("question connection target does not exist")
        _safe(root, path)
        if "title" in question:
            meta["title"] = question["title"]
        if "text" in question:
            if not isinstance(question["text"], str) or not question["text"].strip():
                raise WriteRefused("question text cannot be empty")
            body = question["text"]
        for field in ("state", "answer_notes"):
            if field in question:
                meta["atlas_question"][field] = copy.deepcopy(question[field])
        _schema(root, "note", meta)
        for answer in meta["atlas_question"].get("answer_notes", []):
            if answer not in repo.notes or answer == note_id:
                raise WriteRefused("answer note must resolve to another durable note")
        return _commit(root, args, "atlas.question.save", {path: _render_frontmatter(meta, body)},
                       [note_id], {"note_id": note_id, "note_path": path.relative_to(root).as_posix()})
