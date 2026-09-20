"""Content digests for derived-state inputs.

Modification times are never identity here: authored files may be edited
directly, so every digest is over bytes. Inadmissible symlinks contribute
link identity without reading the target, mirroring fingerprint.py; a file
that is simply absent digests distinctly from one that cannot be admitted.
"""

from __future__ import annotations

import hashlib
import os
import sys
from collections.abc import Iterable, Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath

from ..githistory import GitHistoryError, last_commit_dates
from ..pathing import PathBoundaryError, read_bytes_inside
from .model import DerivedError


def digest_bytes(data: bytes) -> str:
    """Hex SHA-256 of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def digest_file(root: Path, path: Path) -> str:
    """Digest one file's bytes under ``root``.

    Three states digest distinctly: readable content, an inadmissible or
    unreadable link (its link value, never its target), and absence.
    """
    digest = hashlib.sha256()
    try:
        digest.update(read_bytes_inside(root, path))
    except (OSError, PathBoundaryError):
        if not path.is_symlink() and not path.exists():
            digest.update(b"<missing>\0")
        else:
            # Same contribution as canonical_fingerprint: the link moves the
            # guard without the external target being read.
            digest.update(b"<inadmissible-symlink>\0")
            if path.is_symlink():
                try:
                    digest.update(os.readlink(path).encode("utf-8"))
                except OSError:
                    digest.update(b"<unreadable>")
    digest.update(b"\0")
    return digest.hexdigest()


def _checked_relative_root(relative_root: str) -> PurePosixPath:
    relative = PurePosixPath(relative_root)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise DerivedError(f"derived tree root escapes its root: {relative_root!r}")
    return relative


def digest_tree(root: Path, relative_root: str) -> str:
    """Digest a rooted subtree: sorted relative paths plus file contents.

    Same walk shape as canonical_fingerprint: dot-prefixed paths are
    skipped, entries are ordered deterministically, and a missing or empty
    tree contributes nothing (both project to "no records" downstream).
    """
    relative = _checked_relative_root(relative_root)
    base = root.joinpath(*relative.parts) if relative.parts else root
    digest = hashlib.sha256()
    if not base.exists() and not base.is_symlink():
        return digest.hexdigest()
    if base.is_file() or base.is_symlink():
        entries = [base]
    else:
        entries = sorted(path for path in base.rglob("*") if path.is_file() or path.is_symlink())
    for path in entries:
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def digest_paths(root: Path, paths: Sequence[str]) -> str:
    """Digest a fixed list of repo-relative paths in canonical order."""
    digest = hashlib.sha256()
    for rel in sorted(PurePosixPath(path).as_posix() for path in paths):
        relative = _checked_relative_root(rel)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, root.joinpath(*relative.parts)).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def digest_matching_files(root: Path, paths: Iterable[Path]) -> str:
    """Digest an explicit file set: sorted relative paths plus contents.

    Loader-faithful selection is the caller's job (mirror the loader's
    glob/rglob exactly, including its missing-dir tolerance); hashing is
    shared here. A rename moves the digest even when bytes are identical.
    Members must sit under ``root`` lexically; a member outside it is a
    programming bug and fails closed. Missing members digest distinctly
    (never silently dropped), so callers must pass the full selected set.
    """
    relatives: set[str] = set()
    for path in paths:
        candidate = path if path.is_absolute() else root / path
        try:
            rel = candidate.relative_to(root)
        except ValueError as exc:
            raise DerivedError(f"derived input escapes its root: {path}") from exc
        if not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
            raise DerivedError(f"derived input is not normalized under root: {path}")
        relatives.add(rel.as_posix())
    digest = hashlib.sha256()
    for rel in sorted(relatives):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, root / rel).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def digest_producer_files(root: Path, paths: Sequence[str]) -> str:
    """Digest the implementation files a node's value depends on.

    Unlike data inputs, a missing or inadmissible producer file is a
    programming bug — a mistyped producer path would otherwise track
    nothing and silently reuse stale values — so it fails closed.
    """
    digest = hashlib.sha256()
    for rel in sorted(PurePosixPath(path).as_posix() for path in paths):
        relative = _checked_relative_root(rel)
        target = root.joinpath(*relative.parts)
        try:
            content = read_bytes_inside(root, target)
        except (OSError, PathBoundaryError) as exc:
            raise DerivedError(f"derived producer file is not readable: {rel}") from exc
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


#: Repo-relative root of the Core implementation every derived node runs.
CODE_TREE_RELATIVE = "tools/learning_os"


def digest_code_tree(root: Path) -> str:
    """Digest every Core implementation file (F3).

    Hand-maintained per-node producer lists are too easy to get subtly
    wrong — one undeclared transitive import and a semantic code change
    reuses stale values. This digest covers ``tools/learning_os/**/*.py``
    wholesale, so ANY Core code change invalidates every cached node.
    Full invalidation after a code update is cheap; a missed producer is
    a soundness hole. ``__pycache__`` is skipped (derived bytes, never
    executed identity); a rename moves the digest like any other change.

    A root without a Core tree (engine unit tests, an installed-package
    run) digests to a distinct constant: those evaluations share one
    code identity and can only invalidate each other through the
    runtime digest and their declared producers.
    """
    base = root / CODE_TREE_RELATIVE
    digest = hashlib.sha256()
    if not base.is_dir() or base.is_symlink():
        digest.update(b"<no-code-tree>\0")
        return digest.hexdigest()
    members = sorted(
        path for path in base.rglob("*.py")
        if path.is_file() or path.is_symlink()
    )
    for path in members:
        rel = path.relative_to(root)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


#: Distributions whose behavior a derived value can depend on: YAML and
#: contract parsing plus the installed Core itself (an installed-package
#: run has no Core tree under the root, so the distribution version is
#: what invalidates it across upgrades).
_RUNTIME_DISTRIBUTIONS = ("PyYAML", "jsonschema", "referencing", "learningos-core")


def _runtime_components() -> tuple[tuple[str, str], ...]:
    """Version facts the runtime digest is built from (seam for tests)."""
    components: list[tuple[str, str]] = [("python", sys.version)]
    for name in _RUNTIME_DISTRIBUTIONS:
        try:
            components.append((name, version(name)))
        except PackageNotFoundError:
            components.append((name, "not-installed"))
    return tuple(components)


def runtime_digest() -> str:
    """Digest the execution environment derived values depend on (F4).

    A cached validation proof is only sound under the validator that
    produced it: a ``jsonschema`` upgrade changing validation behavior
    must not reuse proofs from the old semantics. Same for YAML parsing
    and the interpreter itself. One process computes this once per
    evaluation session; it is constant within a run.
    """
    digest = hashlib.sha256()
    for name, fact in _runtime_components():
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(fact.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


#: Top-level names that are never generation inputs: generated/ is
#: written by the run itself, tests/ is not read by any builder.
_SNAPSHOT_EXCLUDED_TOP = frozenset({"generated", "tests"})

#: Subtrees whose BYTES no loader or builder reads (only names travel,
#: via note frontmatter which the input digests pin). knowledge/
#: attachments/ is ~265MB; hashing it three times per run would buy
#: nothing.
_SNAPSHOT_EXCLUDED_SUBTREES = (("knowledge", "attachments"),)


def canonical_snapshot_digest(root: Path) -> str:
    """One coarse content digest over every generation input (F2).

    The fine input maps pin each node's declared reads; this snapshot
    pins the whole tree those reads come from, plus the whole-tree git
    table. A snapshot-bound transaction observes it before loading, after
    loading, and after evaluation: equality across the three observations
    proves the Repo and every hashed input describe one filesystem
    snapshot, including reads the fine maps might miss and producer
    bytes the per-node digests read at different moments.

    ``__pycache__`` is skipped: a lazy import between two observations
    writes ``.pyc`` files, which must not read as an input change.
    """
    digest = hashlib.sha256()
    members = sorted(
        path for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    )
    for path in members:
        rel = path.relative_to(root)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        if rel.parts[0] in _SNAPSHOT_EXCLUDED_TOP:
            continue
        if any(
            tuple(rel.parts[: len(prefix)]) == prefix
            for prefix in _SNAPSHOT_EXCLUDED_SUBTREES
        ):
            continue
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(digest_file(root, path).encode("ascii"))
        digest.update(b"\0")
    try:
        table = last_commit_dates(str(root))
    except GitHistoryError:
        table = None
    if table is None:
        digest.update(b"<git-unreadable>\0")
    else:
        for rel in sorted(table):
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(table[rel].encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()
