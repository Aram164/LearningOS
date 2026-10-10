"""Durable source-analysis notes. Every write uses the ordinary V2 transaction.

`note.analysis.save` preserves one agent-authored source analysis byte-exactly
as a `role: reference` note with a `material_analysis` provenance binding;
`note.analysis.save_batch` preserves a bounded batch of them atomically under
one snapshot and one receipt. Saving preserves bytes; it never approves
claims, adopts plans, or records understanding. Authorship and review defaults
are owned by this handler and cannot be supplied by the caller.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from learning_os.ops._legacy_plumbing import (
    _operator_lock,
    _precheck_analysis,
    _read_content_bound_file,
    _read_structured_file,
    _resolve_note,
)

from ..contracts.batch_notes import (
    BATCH_FIELDS,
    BATCH_ITEM_FIELDS,
    BATCH_MAX_NOTES,
    BATCH_MIN_NOTES,
)
from ..domain.failures import WriteRefused
from ..fingerprint import canonical_fingerprint
from ..loader import load_repo
from ..revisions import artifact_revision
from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _write_transaction,
)


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
    from learning_os.ops._legacy_plumbing import prepare_review_envelope

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
    submit = (f".venv/bin/python tools/los.py capability note.analysis.save_batch "
              f"--payload-file {envelope_path}")
    print(json.dumps({"ok": True, "out_dir": str(out),
                      "envelope": str(envelope_path),
                      "expected_snapshot": snapshot,
                      "expected_revisions": revisions,
                      "notes": report, "submit": submit},
                     indent=2, ensure_ascii=False))
    return 0
