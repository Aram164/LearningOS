"""Attachments kept on disk but out of Git, pinned by size and SHA-256.

``system/contracts/local-attachments.yaml`` names note attachments that stay
canonical user artifacts (ARCHITECTURE rule 3) but are too large or too
private to publish: handwritten scans of tens of megabytes each. They live at
their usual ``knowledge/attachments/<note-id>/`` path, Git ignores them, and
backups still carry them (the backup walk reads disk, not the index).

What this module makes executable:

- **Present files match their pins.** A rewritten or truncated scan is an
  error, never a silent replacement: nothing else holds a second copy.
- **Absent files are an environmental warning**, like MATERIALS-OFFLINE. A
  CI checkout or a fresh clone has none of them; the note still names them,
  and the pin still records what belongs there.
- **Every pin is owned.** Each listed path is referenced by a note's
  ``attachments`` frontmatter, under that note's own attachment folder.
- **They stay out of Git.** A listed path that Git tracks, or would track
  because no ignore rule covers it, is an error: one ``git add -A`` would
  republish exactly what this declaration exists to keep private. Outside a
  Git checkout (the synthetic test repositories) these two checks are silent.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..digests import file_sha256

LOCAL_ATTACHMENTS_RELATIVE = "system/contracts/local-attachments.yaml"
CONTRACT_MARKER = "learningos-local-attachments"
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}")
_HASH_BLOCK = 1024 * 1024


class LocalAttachmentsError(ValueError):
    """The declaration itself cannot be read."""


@dataclass(frozen=True)
class LocalAttachment:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class LocalAttachmentIssue:
    code: str
    message: str
    path: str = ""
    severity: str = "E"


def load(root: Path) -> dict[str, LocalAttachment]:
    """The declared local-only attachments by repo-relative path.

    A repository without the file declares none. A present but malformed
    file raises: an unreadable declaration must never read as "nothing is
    local-only", which would turn every pinned scan into ATTACH-MISSING.
    """
    path = root / LOCAL_ATTACHMENTS_RELATIVE
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise LocalAttachmentsError(f"cannot read {LOCAL_ATTACHMENTS_RELATIVE}: {exc}") from exc
    if not isinstance(data, dict) or data.get("contract") != CONTRACT_MARKER \
            or data.get("schema_version") != 1:
        raise LocalAttachmentsError(
            f"{LOCAL_ATTACHMENTS_RELATIVE} must be schema_version 1 with "
            f"contract: {CONTRACT_MARKER}")
    files = data.get("files")
    if not isinstance(files, dict):
        raise LocalAttachmentsError(f"{LOCAL_ATTACHMENTS_RELATIVE}: 'files' must be a mapping")
    declared: dict[str, LocalAttachment] = {}
    for rel, pin in files.items():
        if not isinstance(rel, str) or not rel.startswith("knowledge/attachments/") \
                or ".." in Path(rel).parts or Path(rel).is_absolute():
            raise LocalAttachmentsError(
                f"{LOCAL_ATTACHMENTS_RELATIVE}: {rel!r} is not a path under knowledge/attachments/")
        if not isinstance(pin, dict) or not isinstance(pin.get("bytes"), int) \
                or isinstance(pin.get("bytes"), bool) or pin["bytes"] < 0 \
                or not isinstance(pin.get("sha256"), str) \
                or not _SHA256_RE.fullmatch(pin["sha256"]):
            raise LocalAttachmentsError(
                f"{LOCAL_ATTACHMENTS_RELATIVE}: {rel} needs integer bytes and sha256:<64 hex>")
        declared[rel] = LocalAttachment(rel, pin["bytes"], pin["sha256"])
    return declared


def _blocks(path: Path):
    with path.open("rb") as handle:
        while block := handle.read(_HASH_BLOCK):
            yield block


def _sha256(root: Path, path: Path) -> str:
    """The file's ``sha256:`` digest through the shared digest layer.

    The read stays the same plain streaming read: the layer only skips
    the second hash of unchanged bytes in a process.
    """
    return "sha256:" + file_sha256(root, path, lambda p=path: _blocks(p))


def _git_lines(root: Path, *args: str) -> list[str] | None:
    """Git's answer, or None outside a usable Git checkout."""
    if not (root / ".git").exists():
        return None
    try:
        proc = subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode not in (0, 1):  # check-ignore exits 1 when nothing matches
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def check(root: Path, referenced: set[str]) -> list[LocalAttachmentIssue]:
    """Every way a pinned local-only attachment can be wrong.

    ``referenced`` holds the repo-relative attachment paths notes declare.
    """
    try:
        declared = load(root)
    except LocalAttachmentsError as exc:
        return [LocalAttachmentIssue("UNREADABLE", str(exc), LOCAL_ATTACHMENTS_RELATIVE)]
    issues: list[LocalAttachmentIssue] = []
    for rel, pin in sorted(declared.items()):
        if rel not in referenced:
            issues.append(LocalAttachmentIssue(
                "ORPHAN", "declared local-only attachment that no note's "
                "attachments frontmatter names", rel))
        target = root / rel
        if target.is_symlink() or (target.exists() and not target.is_file()):
            issues.append(LocalAttachmentIssue(
                "NOT-FILE", "local-only attachment is not a regular file", rel))
            continue
        if not target.exists():
            issues.append(LocalAttachmentIssue(
                "ABSENT", "local-only attachment is not on this machine (expected in "
                "a CI checkout or a fresh clone; the pin still records it)", rel, "W"))
            continue
        try:
            size = target.stat().st_size
            actual = _sha256(root, target) if size == pin.bytes else None
        except OSError as exc:
            issues.append(LocalAttachmentIssue("UNREADABLE", f"cannot read {rel}: {exc}", rel))
            continue
        if size != pin.bytes or actual != pin.sha256:
            issues.append(LocalAttachmentIssue(
                "CHANGED", f"bytes differ from the pin ({pin.bytes} bytes, {pin.sha256}); "
                "this is the only copy outside backups — restore it, or re-pin "
                "deliberately", rel))
    if declared:
        paths = sorted(declared)
        tracked = _git_lines(root, "ls-files", "--", *paths)
        for rel in tracked or ():
            issues.append(LocalAttachmentIssue(
                "TRACKED", "Git tracks a local-only attachment; untrack it with "
                "`git rm --cached`", rel))
        ignored = _git_lines(root, "check-ignore", "--no-index", "--", *paths)
        if ignored is not None:
            for rel in sorted(set(paths) - set(ignored)):
                issues.append(LocalAttachmentIssue(
                    "UNIGNORED", "no .gitignore rule covers this local-only attachment, "
                    "so `git add` would publish it", rel))
    return issues


def local_paths(root: Path) -> set[str]:
    """Declared paths, or the empty set when the declaration is unreadable
    (the unreadable declaration is reported by ``check``)."""
    try:
        return set(load(root))
    except LocalAttachmentsError:
        return set()
