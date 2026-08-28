"""Allowlist-only inspection for the frozen Legacy archive.

There is intentionally no discovery operation in this module.  Callers name
each safe relative file in a reviewed allowlist; excluded material is carried
only as a count and is never enumerated, stat'ed, opened, or hashed.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from learning_os.contracts.json_schema import validate_contract


class LegacyArchiveError(ValueError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _safe_relative(value: str) -> PurePosixPath:
    rel = PurePosixPath(value)
    if (
        not isinstance(value, str)
        or "\\" in value
        or rel.is_absolute()
        or not rel.parts
        or rel.as_posix() != value
        or any(part in {"", ".", ".."} for part in rel.parts)
    ):
        raise LegacyArchiveError(f"unsafe allowlisted path: {value}")
    return rel


def _exact_file(authority: Path, relative: str, *, must_exist: bool) -> Path:
    rel = _safe_relative(relative)
    authority = authority.resolve()
    lexical = authority.joinpath(*rel.parts)
    cursor = authority
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise LegacyArchiveError(
                f"allowlisted path traverses a symlink: {relative}"
            )
    try:
        resolved = lexical.resolve(strict=must_exist)
        resolved.relative_to(authority)
    except (OSError, ValueError) as exc:
        raise LegacyArchiveError(f"allowlisted path escapes its authority: {relative}") from exc
    if must_exist and not resolved.is_file():
        raise LegacyArchiveError(f"allowlisted Legacy file is missing: {relative}")
    return resolved


def load_legacy_allowlist(root: Path, path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise LegacyArchiveError(f"allowlist is not a regular file: {path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LegacyArchiveError(f"cannot read Legacy allowlist: {exc}") from exc
    if not isinstance(value, dict):
        raise LegacyArchiveError("Legacy allowlist must be an object")
    try:
        validate_contract(root, "legacy-archive-allowlist.schema.json", value)
    except ValueError as exc:
        raise LegacyArchiveError(str(exc)) from exc
    paths = [row["relative_path"] for row in value["safe_entries"]]
    if len(paths) != len(set(paths)):
        raise LegacyArchiveError("Legacy allowlist contains duplicate safe paths")
    return value


def inspect_legacy_archive(
    root: Path,
    archive_root: Path,
    allowlist: dict[str, Any],
    *,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    archive_root = archive_root.resolve()
    if not archive_root.is_dir():
        raise LegacyArchiveError(f"Legacy archive root is unavailable: {archive_root}")
    issues: list[str] = []
    entries = []
    for safe in allowlist["safe_entries"]:
        relative = safe["relative_path"]
        source = _exact_file(archive_root, relative, must_exist=True)
        content = source.read_bytes()
        source_checksum = _sha256_bytes(content)
        targets = []
        for target_rel in safe["canonical_targets"]:
            target = _exact_file(root, target_rel, must_exist=False)
            exists = target.is_file() and not target.is_symlink()
            target_checksum = _sha256_bytes(target.read_bytes()) if exists else None
            matches = target_checksum == source_checksum if exists else None
            targets.append({
                "path": target_rel,
                "exists": exists,
                "checksum_matches": matches,
                "sha256": target_checksum,
            })
            if safe["disposition"] == "byte-preserved" and not (exists and matches):
                issues.append(f"byte-preservation evidence failed for safe entry: {relative}")
        entries.append({
            "relative_path": relative,
            "size": len(content),
            "sha256": source_checksum,
            "category": safe["category"],
            "disposition": safe["disposition"],
            "canonical_targets": targets,
        })
    timestamp = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC).replace(microsecond=0)
    lock = {
        "schema_version": 1,
        "id": "legacy-archive-lock",
        "type": "legacy-archive-lock",
        "created_at": timestamp.isoformat(),
        "entries": entries,
        "excluded": {
            "count": allowlist["excluded_count"],
            "status": "sealed-not-inspected",
        },
        "verification": {
            "verified_at": timestamp.isoformat(),
            "status": "verified" if not issues else "attention-required",
            "issues": issues,
        },
    }
    try:
        validate_contract(root, "legacy-archive-lock.schema.json", lock)
    except ValueError as exc:
        raise LegacyArchiveError(str(exc)) from exc
    return lock


def load_legacy_archive_lock(root: Path) -> dict[str, Any] | None:
    path = root / "operations" / "legacy" / "archive-lock.yaml"
    if not path.is_file() or path.is_symlink():
        return None
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LegacyArchiveError(f"Legacy archive lock is unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise LegacyArchiveError("Legacy archive lock must be an object")
    try:
        validate_contract(root, "legacy-archive-lock.schema.json", value)
    except ValueError as exc:
        raise LegacyArchiveError(str(exc)) from exc
    return value


def legacy_archive_lock_destination(root: Path) -> Path:
    return root / "operations" / "legacy" / "archive-lock.yaml"
