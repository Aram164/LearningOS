"""Provably-current manifest reuse (#83).

Every discovery read rebuilt the 15 MB projection (~2 s) even when the
stored ``generated/manifest.json`` described exactly the current state.
``generate_all`` now also publishes ``generated/manifest.identity.json``,
a sidecar pinning every input the manifest bytes depend on; reads serve
the stored manifest only when all of them still match, and otherwise
rebuild exactly as before.

Pinned inputs (all must match; anything else rebuilds):

- canonical snapshot: sidecar, manifest stamp, and live fingerprint agree;
- contract: manifest and sidecar stamps equal the live declared version
  and schema hash;
- code identity: ``digest_code_identity`` (target AND executing trees) —
  a digest of the projection code, never git HEAD, so an uncommitted
  code change invalidates too;
- runtime: interpreter and YAML/schema distribution versions;
- operations: the revision ledger, AI request bundles, and garden
  sidecars (the non-canonical files the projection reads);
- materials: a stat digest of the materials tree (relpath, size, mtime,
  ctime — content hashing the referenced PDFs costs 0.5 s, over budget);
- date: the manifest embeds today-relative availability, so the sidecar's
  build date must be today;
- generator: the running ``learning_os`` version stamps the build.

A missing file, parse error, or any single mismatch falls back to the
full rebuild. A partially matching or corrupt file is never served.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import stat
from pathlib import Path

from . import __version__
from .contracts.manifest_contract import declared_schema_sha256, declared_version
from .derived.identity import (
    digest_code_identity,
    digest_matching_files,
    runtime_digest,
)

#: Sidecar name inside generated/ (written by generate_all, like the manifest).
IDENTITY_FILENAME = "manifest.identity.json"

#: Sidecar contract. A reader meeting another format rebuilds. Format 2
#: pins the exact manifest bytes (``manifest_sha256``).
IDENTITY_FORMAT = 2


def manifest_text(manifest: dict) -> str:
    """The one serialization ``generate_all`` publishes for manifest.json.

    Shared so the bytes written and the bytes pinned in the sidecar can
    never disagree.
    """
    return json.dumps(manifest, separators=(",", ":"), sort_keys=True,
                      ensure_ascii=False) + "\n"


def bytes_sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def materials_digest(root: Path) -> str:
    """Stat digest of the materials tree the projection resolves against.

    The manifest records per-resource ``material_path``/``material_exists``
    plus freshness derived from live bytes, so materials state is a
    manifest input — but content-hashing the ~300 referenced PDFs costs
    0.5 s, the whole reuse budget. Size+mtime+ctime per file detects
    every realistic change (add, delete, replace, rewrite); only a
    ctime-preserving restore of identical-size bytes would slip through,
    and the need-shaped ``material-context`` path re-observes live bytes
    at read time regardless. Dotfiles (``.DS_Store``) are skipped so a
    Finder browse cannot force a rebuild; dot-directories such as the
    ``.flat`` symlink farm are still descended into, and link values are
    pinned alongside target stats so a retarget invalidates.
    """
    base = root.parent / "materials"
    digest = hashlib.sha256()
    if base.is_symlink() and not base.exists():
        digest.update(b"<dangling>\0")
        return digest.hexdigest()
    if not base.is_dir():
        digest.update(b"<absent>\0")
        return digest.hexdigest()
    # One scandir walk: entry paths stay strings and stat results are reused,
    # so the hot read path pays ~25 ms for ~1500 files, not ~65 ms.
    # Traversal order is deterministic for a fixed tree (sorted entries, an
    # explicit stack), so build and read digest identically.
    base_str = os.fspath(base)
    stack = [base_str]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError:
            rel = os.path.relpath(directory, base_str).replace(os.sep, "/")
            digest.update(f"{rel}\0<unreadable-dir>".encode())
            digest.update(b"\0")
            continue
        for entry in entries:
            rel = os.path.relpath(entry.path, base_str).replace(os.sep, "/")
            if entry.name.startswith(".") and not entry.is_dir(follow_symlinks=False):
                continue
            if entry.is_dir(follow_symlinks=False):
                if entry.is_symlink():
                    try:
                        target = os.readlink(entry.path)
                    except OSError:
                        target = "<unreadable>"
                    digest.update(f"{rel}\0<link:{target}>".encode())
                    digest.update(b"\0")
                else:
                    stack.append(entry.path)
                continue
            try:
                st = entry.stat(follow_symlinks=True)
            except OSError:
                digest.update(f"{rel}\0<unreadable>".encode())
                digest.update(b"\0")
                continue
            if not stat.S_ISREG(st.st_mode) and not entry.is_symlink():
                digest.update(f"{rel}\0<not-file>".encode())
                digest.update(b"\0")
                continue
            line = f"{rel}\0{st.st_size}\0{st.st_mtime_ns}\0{st.st_ctime_ns}"
            if entry.is_symlink():
                try:
                    line += f"\0link:{os.readlink(entry.path)}"
                except OSError:
                    line += "\0link:<unreadable>"
            digest.update(line.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def operations_digest(root: Path) -> str:
    """Bytes digest of the non-canonical files the projection reads.

    Mirrors the shadow graph's manifest inputs (``manifest_derived``):
    the artifact-revision ledger (``manifest.revisions``), AI request
    bundles (``manifest.ai_files``), and the garden-state sidecars folded
    into ``manifest.garden`` (walked as a directory here — the per-id
    enumeration needs a loaded repo, and extra members only cost a
    rebuild if they ever change).
    """
    files: list[Path] = [root / "operations/transactions/revisions.yaml"]
    garden_state = root / "operations/ai-actions/garden-state"
    if garden_state.is_dir():
        files.extend(sorted(garden_state.glob("*.yaml")))
    requests = root / "operations/ai-actions/requests"
    if requests.is_dir():
        files.extend(sorted(requests.glob("*/request.yaml")))
    return digest_matching_files(root, files)


def build_identity(root: Path, manifest: dict) -> dict:
    """Pin every manifest input for a just-built manifest.

    The snapshot is read from the manifest's own stamp (every build path
    stamps the live fingerprint); everything else is observed now.
    """
    generated = manifest.get("_generated") or {}
    return {
        "_generated": {
            "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py",
            "generator": f"learning_os v{__version__}",
        },
        "format": IDENTITY_FORMAT,
        "snapshot_id": generated.get("snapshot_id"),
        "contract_version": declared_version(root),
        "schema_sha256": declared_schema_sha256(root),
        "generator": f"learning_os v{__version__}",
        "code_identity": digest_code_identity(root),
        "runtime_digest": runtime_digest(),
        "built_date": datetime.date.today().isoformat(),
        "operations_digest": operations_digest(root),
        "materials_digest": materials_digest(root),
        # The exact manifest bytes this identity describes. Every other pin
        # is an input; this one binds the output, so a sidecar published
        # beside a different manifest.json — a crash or a concurrent read
        # between the two writes after a code-only change, when both still
        # carry the same snapshot stamp — can never pass as current.
        "manifest_sha256": bytes_sha256(manifest_text(manifest).encode("utf-8")),
    }


def check_identity(
    root: Path, manifest: dict, identity: dict, *, live_snapshot: str
) -> tuple[bool, str]:
    """Whether the stored manifest provably describes current state.

    Returns ``(True, "current")`` or ``(False, reason)``. Shape problems
    answer mismatch, never raise; a missing contract or unreadable code
    tree raises exactly as the fresh build would.
    """
    if not isinstance(identity, dict):
        return False, "identity is not an object"
    if identity.get("format") != IDENTITY_FORMAT:
        return False, "identity format mismatch"
    generated = manifest.get("_generated") if isinstance(manifest, dict) else None
    if not isinstance(generated, dict):
        return False, "manifest has no _generated stamp"
    if identity.get("snapshot_id") != generated.get("snapshot_id"):
        return False, "identity and manifest describe different snapshots"
    if generated.get("snapshot_id") != live_snapshot:
        return False, "canonical state moved since the stored build"
    contract_version = declared_version(root)
    if generated.get("contract_version") != contract_version \
            or identity.get("contract_version") != contract_version:
        return False, "contract version moved since the stored build"
    schema_sha256 = declared_schema_sha256(root)
    if generated.get("schema_sha256") != schema_sha256 \
            or identity.get("schema_sha256") != schema_sha256:
        return False, "manifest schema moved since the stored build"
    generator = f"learning_os v{__version__}"
    if generated.get("generator") != generator \
            or identity.get("generator") != generator:
        return False, "generator version moved since the stored build"
    if identity.get("code_identity") != digest_code_identity(root):
        return False, "projection code moved since the stored build"
    if identity.get("runtime_digest") != runtime_digest():
        return False, "runtime moved since the stored build"
    if identity.get("built_date") != datetime.date.today().isoformat():
        return False, "stored build is from a previous day"
    if identity.get("operations_digest") != operations_digest(root):
        return False, "operations state moved since the stored build"
    if identity.get("materials_digest") != materials_digest(root):
        return False, "materials state moved since the stored build"
    return True, "current"
