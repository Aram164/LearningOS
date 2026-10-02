"""Resolve a routed inbox drop to the archive (WORKFLOWS §21).

``inbox-resolve`` is the write path that lets the inbox trend toward empty:
after a drop has been routed to its deterministic destination, this moves
the drop itself — one named drop, or one file inside a drop folder —
byte-identical to ``archive/inbox/YYYY/``. The drop's SHA-256 must match
the bytes read (a changed drop refuses), ``routed_to`` names every
destination that received it (a missing destination refuses), and the
receipt names both endpoints plus ``routed_to``. The archive never
overwrites: a collision refuses rather than merging histories.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

from learning_os.contracts.gateway import current_gateway_request

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
)

INBOX_RESOLVE_CAPABILITY = "inbox.resolve"


def _file_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _folder_digest(files: dict[str, bytes]) -> str:
    """One digest for a folder drop: SHA-256 over the sorted name->sha map.

    Canonical JSON over parsed digests, never raw bytes, so the value is
    stable regardless of read order and re-derivable by any caller holding
    the same files.
    """
    manifest = {name: hashlib.sha256(files[name]).hexdigest()
                for name in sorted(files)}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _admit(inbox: Path, name: str) -> Path:
    """The inbox path ``name`` addresses, or raise with a refusal message."""
    if not name or name in {".", "./"} or Path(name).is_absolute() \
            or ".." in Path(name).parts:
        raise ValueError(f"inbox name must be relative to work/inbox: {name}")
    target = inbox / name
    try:
        target.resolve(strict=True).relative_to(inbox.resolve(strict=True))
    except OSError as exc:
        raise ValueError(f"inbox item not found: {name}") from exc
    cursor: Path | None = target
    while cursor is not None and cursor != inbox and inbox in cursor.parents:
        if cursor.is_symlink():
            raise ValueError("inbox resolve refuses symlinks")
        cursor = cursor.parent if cursor != cursor.parent else None
    return target


def _collect(inbox: Path, target: Path) -> dict[str, bytes]:
    """Every regular file under ``target`` as inbox-relative name -> bytes."""
    if target.is_file() and not target.is_symlink():
        return {target.relative_to(inbox).as_posix(): target.read_bytes()}
    if not target.is_dir() or target.is_symlink():
        raise ValueError(f"inbox item is not a regular file or folder: {target.name}")
    files: dict[str, bytes] = {}
    for path in sorted(target.rglob("*")):
        if path.is_symlink():
            raise ValueError("inbox resolve refuses symlinks")
        if not path.is_file():
            continue
        files[path.relative_to(inbox).as_posix()] = path.read_bytes()
    if not files:
        raise ValueError(f"inbox item has no files to archive: {target.name}")
    return files


def _prune_empty_dirs(inbox: Path, target: Path) -> None:
    """Remove directories the move just emptied, up to (not incl.) the inbox.

    Best-effort structural cleanup after a committed move: empty
    directories carry no canonical content (Git does not track them, the
    fingerprint walks files), so a redir that fills again concurrently
    simply stops the prune. Never touches the inbox itself.
    """
    cursor = target if target.is_dir() else target.parent
    while cursor != inbox and inbox in cursor.parents:
        try:
            if any(cursor.iterdir()):
                return
            cursor.rmdir()
        except OSError:
            return
        cursor = cursor.parent


def cmd_inbox_resolve(args) -> int:
    root = _root(args)
    if current_gateway_request() is None:
        print("los: inbox resolve requires GatewayEnvelopeV2; direct CLI application is disabled",
              file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        try:
            inbox = root / "work" / "inbox"
            target = _admit(inbox, args.name)
            files = _collect(inbox, target)
            if target.is_file():
                actual = _file_digest(next(iter(files.values())))
            else:
                actual = _folder_digest(files)
            if actual != args.drop_sha256:
                raise ValueError(
                    f"inbox drop changed since read: {args.name} "
                    f"(re-read it with `inbox-read {args.name}` and re-seal)")
            routed_to = [str(entry).strip() for entry in (args.routed_to or [])]
            if not routed_to or any(not entry for entry in routed_to):
                raise ValueError("inbox resolve needs a non-empty routed_to list naming where the drop went")
            year = str(_dt.date.today().year)
            writes: dict[Path, bytes] = {}
            deletes: list[Path] = []
            for rel, data in files.items():
                destination = root / "archive" / "inbox" / year / rel
                if destination.exists() or destination.is_symlink():
                    raise ValueError(
                        f"archive already holds {destination.relative_to(root).as_posix()}; "
                        "the archive never overwrites")
                writes[destination] = data
                deletes.append(inbox / rel)
            code, errors, confirmation = _write_transaction(
                root, writes, capability=INBOX_RESOLVE_CAPABILITY,
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=(),
                deletes=deletes,
                metadata={"routed_to": routed_to},
            )
            if code:
                for error in errors[:12]:
                    print(error, file=sys.stderr)
                return code
            _prune_empty_dirs(inbox, target)
        except (ValueError, OSError) as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
    print(json.dumps({"ok": True, "resolved": args.name,
                      "archived": sorted(path.relative_to(root).as_posix()
                                         for path in writes),
                      "routed_to": routed_to, **confirmation}))
    return 0
