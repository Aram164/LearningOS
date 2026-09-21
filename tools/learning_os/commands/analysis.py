"""Durable source-analysis notes. Every write uses the ordinary V2 transaction.

`note.analysis.save` preserves one agent-authored source analysis byte-exactly
as a `role: reference` note with a `material_analysis` provenance binding.
Saving preserves bytes; it never approves claims, adopts plans, or records
understanding. Authorship and review defaults are owned by this handler and
cannot be supplied by the caller.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path

import jsonschema

from ..loader import load_repo
from ..material_analysis import binding_consistent, observe_local_material
from ..materials_resolution import MATERIAL_SCHEME, material_uri_authority
from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_content_bound_file,
    _root,
    _write_transaction,
)

ANALYSIS_FIELDS = frozenset({"id", "title", "path", "binding"})
NOTES_PREFIX = Path("knowledge/notes")


def _safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(f"analysis save cannot use a symlink: {relative}")
    return path


def _schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc


def _render_exact_note(meta: dict, body: bytes) -> bytes:
    """Frontmatter plus the body bytes verbatim.

    Unlike the ordinary renderer this never strips leading whitespace: the
    bytes after the frontmatter block are exactly the preserved analysis.
    """
    front = "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n"
    return front.encode("utf-8") + body


def _destination(root: Path, note_id: str, relpath: object) -> Path:
    if not isinstance(relpath, str) or not relpath:
        raise WriteRefused("analysis path must be a repo-relative note path")
    relative = Path(relpath)
    if relative.is_absolute() or ".." in relative.parts:
        raise WriteRefused("analysis path must stay inside knowledge/notes/")
    if relative.suffix != ".md" or relative.stem != note_id:
        raise WriteRefused("analysis filename must be the note id with .md")
    try:
        relative.relative_to(NOTES_PREFIX)
    except ValueError:
        raise WriteRefused("analysis path must stay inside knowledge/notes/") from None
    path = root / relative
    return _safe(root, path)


def _verify_resolved_material(root: Path, repo, binding: dict) -> None:
    """A resolved binding claims live registered bytes: observe them.

    Digest agreement proves the agent's story is coherent; this proves it
    is true. The material must exist and hash to the claimed live digest
    right now, and it must be the source's registered file or lie under
    the source's registered directory — compared as resolved filesystem
    locations so `.flat` id-aliases match their physical targets.
    """
    materials = root.parent / "materials"
    observation = observe_local_material(
        materials, str(binding.get("material") or ""),
        str(binding.get("live_source_digest") or ""))
    if observation["status"] != "current":
        raise WriteRefused(
            "resolved material is not observable at its claimed live "
            f"digest ({observation['status']})")
    registered = (repo.sources.get(binding.get("source_id")) or {}).get("material")
    if material_uri_authority(registered) is None:
        raise WriteRefused("resolved source registers no local material")
    try:
        boundary = materials.resolve()
        base = (repo.materials_root / str(registered)[len(MATERIAL_SCHEME):]).resolve()
        target = (materials / str(binding.get("material"))).resolve()
        base.relative_to(boundary)
        target.relative_to(boundary)
    except (OSError, ValueError):
        raise WriteRefused(
            "resolved material escapes the materials tree") from None
    if target != base and base not in target.parents:
        raise WriteRefused(
            "resolved material is not the source's registered file or "
            "under its registered directory")


def cmd_note_analysis_save(args) -> int:
    root = _root(args)
    analysis = args.analysis
    if not isinstance(analysis, dict):
        raise WriteRefused("analysis must be an object")
    unknown = set(analysis) - ANALYSIS_FIELDS
    if unknown or not isinstance(analysis.get("id"), str):
        raise WriteRefused("analysis has unknown fields or no note id")
    _, body = _read_content_bound_file(
        args.body_file, getattr(args, "body_file_sha256", None),
        label="analysis body file")
    if not body:
        raise WriteRefused("analysis body is empty")
    try:
        body.decode("utf-8")
    except UnicodeDecodeError:
        raise WriteRefused("analysis body is not valid UTF-8") from None
    binding = analysis.get("binding")
    problem = binding_consistent(binding if isinstance(binding, dict) else {})
    if problem is not None:
        raise WriteRefused(problem)
    frozen = hashlib.sha256(body).hexdigest()
    if binding["frozen_input_sha256"] != frozen:
        raise WriteRefused("analysis body does not match frozen_input_sha256")
    if binding["frozen_input_bytes"] != len(body):
        raise WriteRefused("analysis body does not match frozen_input_bytes")
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note_id = analysis["id"]
        if binding["resolution"] == "resolved":
            if binding.get("source_id") not in repo.sources:
                raise WriteRefused("resolved source is not registered")
            _verify_resolved_material(root, repo, binding)
        existing = repo.notes.get(note_id)
        path = _destination(root, note_id, analysis.get("path"))
        if existing:
            if "material_analysis" not in existing.meta:
                raise WriteRefused("this note id is not a source analysis")
            # The loader strips leading body whitespace on read, so replay
            # compares exact on-disk bytes: the body is the file's last N
            # bytes where N is the stored frozen_input_bytes.
            stored = existing.meta["material_analysis"].get("frozen_input_bytes")
            try:
                stored_body = existing.path.read_bytes()[-stored:] \
                    if isinstance(stored, int) else None
            except OSError:
                stored_body = None
            same = (
                existing.meta.get("title") == analysis.get("title")
                and existing.meta.get("material_analysis") == binding
                and stored_body == body
                and existing.path == path
            )
            if not same:
                raise WriteRefused(
                    "note id collides with a different analysis; refusing")
            print(json.dumps({"ok": True, "replayed": True, "note_id": note_id,
                              "note_path": path.relative_to(root).as_posix()},
                             ensure_ascii=False))
            return 0
        if not isinstance(analysis.get("title"), str) or not analysis["title"].strip():
            raise WriteRefused("new analyses require a title")
        meta = {"id": note_id, "type": "note", "role": "reference",
                "title": analysis["title"], "created": date.today().isoformat(),
                "state": "rough", "authorship": "operator-drafted",
                "semantic_review": "unreviewed",
                "material_analysis": copy.deepcopy(binding)}
        # Validate id before it can be used as a filename.
        _schema(root, "note", meta)
        if path.exists():
            raise WriteRefused("analysis destination already exists")
        code, errors, confirmation = _write_transaction(
            root, {path: _render_exact_note(meta, body)},
            capability="note.analysis.save",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[note_id],
        )
        if code:
            raise WriteRefused("; ".join(str(issue) for issue in errors[:12]))
        print(json.dumps({"ok": True, "replayed": False, "note_id": note_id,
                          "note_path": path.relative_to(root).as_posix(),
                          **confirmation}, ensure_ascii=False))
        return 0
