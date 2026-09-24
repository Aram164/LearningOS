"""Durable source-analysis notes. Every write uses the ordinary V2 transaction.

`note.analysis.save` preserves one agent-authored source analysis byte-exactly
as a `role: reference` note with a `material_analysis` provenance binding;
`note.analysis.save_batch` preserves a bounded batch of them atomically under
one snapshot and one receipt. Saving preserves bytes; it never approves
claims, adopts plans, or records understanding. Authorship and review defaults
are owned by this handler and cannot be supplied by the caller.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import jsonschema

from ..contracts.batch_notes import (
    ANALYSIS_FIELDS,
    BATCH_FIELDS,
    BATCH_ITEM_FIELDS,
    BATCH_MAX_NOTES,
    BATCH_MIN_NOTES,
)
from ..fingerprint import canonical_fingerprint
from ..loader import load_repo
from ..material_analysis import binding_consistent, observe_local_material
from ..materials_resolution import MATERIAL_SCHEME, material_uri_authority
from ..revisions import artifact_revision
from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_content_bound_file,
    _read_structured_file,
    _root,
    _write_transaction,
)

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


def _precheck_analysis(analysis: object, body: bytes) -> dict:
    """Record shape, binding coherence, and frozen-byte agreement.

    Shared by single and batch saves so both refuse the same bytes for the
    same reason. Everything needing the loaded repository — source
    registration, live-byte observation, replay classification — stays in
    `_resolve_note`, inside the snapshot guard.
    """
    if not isinstance(analysis, dict):
        raise WriteRefused("analysis must be an object")
    unknown = set(analysis) - ANALYSIS_FIELDS
    if unknown or not isinstance(analysis.get("id"), str):
        raise WriteRefused("analysis has unknown fields or no note id")
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
    return binding


def _resolve_note(root: Path, repo, analysis: dict, binding: dict,
                  body: bytes) -> tuple[str, Path, bytes | None]:
    """Classify one prechecked analysis against the loaded repository.

    Returns (note_id, destination, rendered_bytes); rendered_bytes is None
    when the request replays an identical note. Any collision, unregistered
    source, or unobservable resolved material refuses. Callers commit every
    returned write in one transaction.
    """
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
        return note_id, path, None
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
    return note_id, path, _render_exact_note(meta, body)


def cmd_note_analysis_save(args) -> int:
    root = _root(args)
    _, body = _read_content_bound_file(
        args.body_file, getattr(args, "body_file_sha256", None),
        label="analysis body file")
    binding = _precheck_analysis(args.analysis, body)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note_id, path, content = _resolve_note(
            root, repo, args.analysis, binding, body)
        if content is None:
            print(json.dumps({"ok": True, "replayed": True, "note_id": note_id,
                              "note_path": path.relative_to(root).as_posix()},
                             ensure_ascii=False))
            return 0
        code, errors, confirmation = _write_transaction(
            root, {path: content},
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


def _read_batch_items(bundle: object) -> list[tuple[int, dict, dict, bytes]]:
    """Read and precheck every batch body before the snapshot guard.

    Each item carries its own content-bound body file, so the bytes hashed
    here are the approved bytes even if a file changes before the write.
    Returns (index, analysis, binding, body) per item, in request order.
    """
    if not isinstance(bundle, dict):
        raise WriteRefused("bundle must be an object")
    unknown = set(bundle) - BATCH_FIELDS
    if unknown:
        raise WriteRefused("bundle has unknown fields: "
                           + ", ".join(sorted(str(key) for key in unknown)))
    items = bundle.get("notes")
    if not isinstance(items, list) or len(items) < BATCH_MIN_NOTES:
        raise WriteRefused("bundle must carry a non-empty notes list")
    if len(items) > BATCH_MAX_NOTES:
        raise WriteRefused(f"batch carries {len(items)} notes; "
                           f"at most {BATCH_MAX_NOTES} per batch")
    prepared: list[tuple[int, dict, dict, bytes]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise WriteRefused(f"batch item {index} must be an object")
        unknown = set(item) - BATCH_ITEM_FIELDS
        if unknown:
            raise WriteRefused(f"batch item {index} has unknown fields: "
                               + ", ".join(sorted(str(key) for key in unknown)))
        if not isinstance(item.get("body_file"), str) or not item["body_file"]:
            raise WriteRefused(f"batch item {index} needs a body_file path")
        _, body = _read_content_bound_file(
            item["body_file"], item.get("body_file_sha256"),
            label=f"batch item {index} body file")
        try:
            binding = _precheck_analysis(item.get("analysis"), body)
        except WriteRefused as exc:
            raise WriteRefused(f"batch item {index}: {exc}") from exc
        note_id = item["analysis"]["id"]
        if note_id in seen:
            # Even two identical rows refuse: the transaction needs unique
            # artifact ids, and silently dropping one would lie about what
            # the batch carried.
            raise WriteRefused(
                f"batch carries note id {note_id} twice; refusing")
        seen.add(note_id)
        prepared.append((index, item["analysis"], binding, body))
    return prepared


def cmd_note_analysis_save_batch(args) -> int:
    root = _root(args)
    prepared = _read_batch_items(args.bundle)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        writes: dict[Path, bytes] = {}
        created: list[str] = []
        replayed_ids: list[str] = []
        paths: dict[str, str] = {}
        for index, analysis, binding, body in prepared:
            try:
                note_id, path, content = _resolve_note(
                    root, repo, analysis, binding, body)
            except WriteRefused as exc:
                raise WriteRefused(
                    f"batch item {index} ({analysis['id']}): {exc}") from exc
            paths[note_id] = path.relative_to(root).as_posix()
            if content is None:
                replayed_ids.append(note_id)
            else:
                created.append(note_id)
                writes[path] = content
        if not writes:
            print(json.dumps(
                {"ok": True, "replayed": True, "created_note_ids": [],
                 "replayed_note_ids": replayed_ids, "note_paths": paths},
                ensure_ascii=False))
            return 0
        # The envelope guards every batch id, but only new notes become
        # transaction artifacts: replayed notes keep their revision exactly
        # as a single-note replay does.
        wanted = set(created)
        expected = {artifact: revision
                    for artifact, revision
                    in _expected_revisions_from_args(args).items()
                    if artifact in wanted}
        code, errors, confirmation = _write_transaction(
            root, writes,
            capability="note.analysis.save_batch",
            expected_revisions=expected,
            artifact_ids=created,
        )
        if code:
            raise WriteRefused("; ".join(str(issue) for issue in errors[:12]))
        print(json.dumps(
            {**confirmation, "ok": True, "replayed": False,
             "created_note_ids": created, "replayed_note_ids": replayed_ids,
             "note_paths": paths}, ensure_ascii=False))
        return 0


DRAFTS_FIELDS = frozenset({"notes"})
DRAFT_ITEM_FIELDS = frozenset({"id", "title", "path", "binding", "body"})
DRAFT_FROZEN_REFUSED = ("frozen_input_sha256", "frozen_input_bytes")


def _read_drafts_file(value: object) -> dict:
    """Read the UTF-8 JSON drafts file, or stdin JSON when given `-`.

    JSON is the only accepted format: bodies are JSON strings, so what the
    author writes is codepoint-exactly what prep stages — no folding style
    can silently mangle whitespace the way a YAML block choice could.
    """
    if value == "-":
        return _read_structured_file("-", label="batch drafts")
    if not isinstance(value, str) or not value:
        raise WriteRefused("drafts must be a UTF-8 JSON file (.json)")
    if Path(value).suffix.lower() != ".json":
        raise WriteRefused("drafts must be a UTF-8 JSON file (.json)")
    return _read_structured_file(value, label="batch drafts")


def _read_draft_items(drafts: object) -> list[tuple[dict, dict, bytes]]:
    """Validate drafts and derive every hash. No repository state needed.

    Returns (analysis, binding, body_bytes) per item, in draft order.
    Drafts carry no derived hashes: a precomputed frozen value refuses
    rather than being silently recomputed, since a stale one signals
    confusion about which bytes were approved.
    """
    if not isinstance(drafts, dict):
        raise WriteRefused("drafts must be an object")
    unknown = set(drafts) - DRAFTS_FIELDS
    if unknown:
        raise WriteRefused("drafts has unknown fields: "
                           + ", ".join(sorted(str(key) for key in unknown)))
    notes = drafts.get("notes")
    if not isinstance(notes, list) or len(notes) < BATCH_MIN_NOTES:
        raise WriteRefused("drafts must carry a non-empty notes list")
    if len(notes) > BATCH_MAX_NOTES:
        raise WriteRefused(f"drafts carry {len(notes)} notes; "
                           f"at most {BATCH_MAX_NOTES} per batch")
    prepared: list[tuple[dict, dict, bytes]] = []
    seen: set[str] = set()
    for index, item in enumerate(notes):
        if not isinstance(item, dict):
            raise WriteRefused(f"draft {index} must be an object")
        unknown = set(item) - DRAFT_ITEM_FIELDS
        if unknown:
            raise WriteRefused(f"draft {index} has unknown fields: "
                               + ", ".join(sorted(str(key) for key in unknown)))
        for field in ("id", "title", "path"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise WriteRefused(f"draft {index} needs a non-empty {field}")
        binding = item.get("binding")
        if not isinstance(binding, dict):
            raise WriteRefused(f"draft {index} needs a binding object")
        for derived in DRAFT_FROZEN_REFUSED:
            if derived in binding:
                raise WriteRefused(
                    f"draft {index} must not precompute {derived}; "
                    f"prep derives it from the body")
        body = item.get("body")
        if not isinstance(body, str) or not body:
            raise WriteRefused(f"draft {index} needs a non-empty body string")
        body_bytes = body.encode("utf-8")
        completed = dict(binding)
        completed["frozen_input_sha256"] = hashlib.sha256(body_bytes).hexdigest()
        completed["frozen_input_bytes"] = len(body_bytes)
        analysis = {"id": item["id"], "title": item["title"],
                    "path": item["path"], "binding": completed}
        try:
            checked = _precheck_analysis(analysis, body_bytes)
        except WriteRefused as exc:
            raise WriteRefused(f"draft {index}: {exc}") from exc
        if item["id"] in seen:
            raise WriteRefused(
                f"drafts carry note id {item['id']} twice; refusing")
        seen.add(item["id"])
        prepared.append((analysis, checked, body_bytes))
    return prepared


def _prepare_out_dir(root: Path, value: object) -> Path:
    """Resolve the staging dir, which must stay outside the repository.

    Prep writes no canonical data, so staging lives out-of-tree by
    contract, like every other draft. ``bodies/`` is prep-owned and
    rebuilt every run, so a re-prep with fewer notes leaves no stale
    body files behind.
    """
    if not isinstance(value, str) or not value or value == "-":
        raise WriteRefused(
            "--out must be a staging directory outside the repository")
    out = Path(value).expanduser()
    if not out.is_absolute():
        out = Path.cwd() / out
    try:
        resolved = out.resolve()
    except OSError as exc:
        raise WriteRefused(f"cannot use staging dir {value}: {exc}") from exc
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        pass
    else:
        raise WriteRefused("staging dir must stay outside the repository")
    bodies = resolved / "bodies"
    try:
        if bodies.exists():
            if not bodies.is_dir() or bodies.is_symlink():
                raise WriteRefused(
                    f"staging bodies path is not a directory: {bodies}")
            shutil.rmtree(bodies)
        bodies.mkdir(parents=True)
    except OSError as exc:
        raise WriteRefused(f"cannot stage into {resolved}: {exc}") from exc
    return resolved


def cmd_note_analysis_prepare(args) -> int:
    """Drafts in, reviewable staging plus the exact envelope out.

    Read-only against the repository: no operator lock, no canonical
    writes, no publication. Every check runs before a single staged byte,
    so a refused prep stages no body files and no envelope.
    Review the staged files, then submit the envelope unchanged through
    ``note.analysis.save_batch``; the content hashes and intent binding
    refuse anything altered after review.
    """
    from .capability import prepare_review_envelope

    root = _root(args)
    prepared = _read_draft_items(_read_drafts_file(args.drafts))
    out = _prepare_out_dir(root, args.out)
    repo = load_repo(root)
    snapshot = f"sha256:{canonical_fingerprint(root)}"
    staged: list[tuple[str, str, bytes, dict, bool]] = []
    for index, (analysis, binding, body_bytes) in enumerate(prepared):
        try:
            note_id, path, content = _resolve_note(
                root, repo, analysis, binding, body_bytes)
        except WriteRefused as exc:
            raise WriteRefused(
                f"draft {index} ({analysis['id']}): {exc}") from exc
        staged.append((note_id, path.relative_to(root).as_posix(),
                       body_bytes, analysis, content is not None))
    bundle_notes = []
    report = []
    try:
        for note_id, relpath, body_bytes, analysis, predicted_new in staged:
            body_path = out / "bodies" / f"{note_id}.bin"
            body_path.write_bytes(body_bytes)
            digest = hashlib.sha256(body_bytes).hexdigest()
            bundle_notes.append({
                "analysis": analysis,
                "body_file": str(body_path),
                "body_file_sha256": f"sha256:{digest}",
            })
            report.append({
                "note_id": note_id,
                "note_path": relpath,
                "predicted_new": predicted_new,
                "frozen_input_sha256": digest,
                "body_file": str(body_path),
            })
        revisions = {note_id: artifact_revision(root, note_id)
                     for note_id, _, _, _, _ in staged}
        envelope = prepare_review_envelope(
            "note.analysis.save_batch", {"bundle": {"notes": bundle_notes}},
            snapshot, revisions)
        envelope_path = out / "envelope.json"
        envelope_path.write_text(
            json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(f"cannot write staging dir {out}: {exc}") from exc
    submit = (f"python tools/los.py capability note.analysis.save_batch "
              f"--payload-file {envelope_path}")
    print(json.dumps({"ok": True, "out_dir": str(out),
                      "envelope": str(envelope_path),
                      "expected_snapshot": snapshot,
                      "expected_revisions": revisions,
                      "notes": report, "submit": submit},
                     indent=2, ensure_ascii=False))
    return 0
