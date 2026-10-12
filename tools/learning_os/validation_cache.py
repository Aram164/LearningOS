"""Cached static validation issues for fast `status` reads (#103).

`status` re-ran the full validator on every invocation. The validator's
output splits two ways: static issues, which change only when validation
inputs change, and the two clock-derived advisories (`WS-NEGLECT`,
`INBOX-STALE`), which can appear with no authored change at all simply
because time passed. This module caches the static issues in the
derived node ``cache.validation-static`` under content pins and
recomputes the advisories live on every read, so a cache hit answers
without re-validating while clock-derived warnings stay current.

Pinned inputs (all must match; anything else misses and re-validates):

- canonical fingerprint: the authored canonical inputs;
- code identity: ``digest_code_identity`` (target AND executing trees) —
  a validator change invalidates too;
- runtime: interpreter and YAML/schema distribution versions;
- materials: a stat digest of the materials tree (add/delete/replace);
- operations: the revision ledger, AI request bundles, and garden
  sidecars — AI-request prep changes validation with no fingerprint move;
- validator inputs: a stat digest of everything else the validator reads
  outside the canonical roots — generated/ (the GEN-* checks, and
  HYGIENE-VIEWS compares the published manifest's stamp, so ``make
  views`` alone changes the answer), system/ prose, transaction receipts,
  the repository tree, and the two perimeter levels above it — plus two
  targeted stat sets inside otherwise name-only subtrees: every checked
  text-cache JSON/Markdown file (including each ``index.json``) and each
  declared local-only attachment (definition 2 took them out of the
  content fingerprint, so a scan rewrite would otherwise serve stale).

All pins are observed *before* validation runs and stored with its
result. `status` holds no lock, so a write landing mid-run then leaves a
cache whose pins describe the pre-write state, and the next read misses;
pins observed afterwards would vouch for a state the issues never saw.

A git index.lock's age is clock-derived too (HYGIENE-LOCK) and is likewise
recomputed live.

Warmth comes from two writers: `status` memoizes on a miss (best-effort,
never failing the read) and ``tools/validate.py`` refreshes the cache on
offline runs only — ``--online`` results depend on network state and must
not poison it. There is deliberately no commit-path hook: every commit
moves ledger/fingerprint pins, so post-write reads correctly miss once,
while refreshing from mid-commit results would miss receipt/idempotency
errors (including the deliberate JF-13/L4 duplicate-key check).

A structurally unreadable cache (corrupt state, hash-mismatched blob,
wrong shape) is an ordinary miss before its caller falls back to a full
run: blobs are content-addressed and hash-verified, so a corrupt value
can never be served, and a malformed one is invalidated. The pre-4.3
sidecar at ``generated/reports/validation-report.cache.json`` is obsolete
and never written; leftovers are discarded by
``discard_unreadable_cache`` and reclaimed by derived-state GC.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING

from .contracts.local_attachments import local_paths
from .derived.engine import BuildContext, evaluate
from .derived.identity import digest_code_identity, runtime_digest
from .derived.model import DERIVED_SUBSTRATE_FILES, DerivedError, NodeSpec
from .derived.store import invalidate
from .domain.failures import TransactionFailure
from .fingerprint import CANONICAL_ROOTS, canonical_fingerprint
from .manifest_identity import materials_digest, operations_digest
from .rules import validate
from .rules.advisories import advisory_issues, is_live_advisory
from .rules.common import Issue

if TYPE_CHECKING:
    from typing import Any

    from .loader import Repo

#: Obsolete sidecar location (pre-4.3). Active reads/writes go through the
#: derived node below; this path survives only so pre-migration leftovers
#: are still discarded by `discard_unreadable_cache` and reclaimed by
#: `diagnostics_prune --derived-state` and the reports GC. Never written.
CACHE_RELATIVE = Path("generated/reports/validation-report.cache.json")

#: Obsolete sidecar contract, kept for the leftover discard above.
CACHE_FORMAT = 4

#: Derived node holding the cached static validation issues (SPEC §14, D-12).
#: One named node: every validation input is global, so per-artifact splits
#: would only multiply keys over identical pins.
VALIDATION_NODE_ID = "cache.validation-static"
VALIDATION_NODE_VERSION = 1
VALIDATION_PRODUCER_FILES = (
    "tools/learning_os/validation_cache.py",
    *DERIVED_SUBSTRATE_FILES,
)

#: `cache_pins` key -> derived direct-input id. Namespaced so this node's
#: inputs cannot collide with another node's in a shared evaluation.
_VALIDATION_INPUT_IDS = {
    "canonical_fingerprint": "cache.validation.canonical_fingerprint",
    "code_identity": "cache.validation.code_identity",
    "runtime_digest": "cache.validation.runtime_digest",
    "materials_digest": "cache.validation.materials_digest",
    "operations_digest": "cache.validation.operations_digest",
    "validator_inputs": "cache.validation.validator_inputs",
}

#: Directory names never descended into: version control, environments and
#: interpreter/tool caches. No rule reads inside them, and several change on
#: every run. (At the repository root they are dot-entries, recorded by name.)
_WALK_PRUNE = frozenset({".git", ".venv", "node_modules", "__pycache__",
                         ".pytest_cache", ".ruff_cache"})

#: Subtrees recorded by name only: the material text cache (~70k
#: machine-written page blobs, none of them read by any rule) and the
#: disposable diagnostics trace store, which no rule reads. The exception
#: inside the text cache is its JSON/Markdown files, which GEN-* reads:
#: ``validator_inputs_digest`` lists that tree separately and stats only
#: those checked files, leaving page blobs unstatted.
_WALK_NAME_ONLY = frozenset({"generated/text-cache", "operations/diagnostics"})

#: Subtrees skipped entirely: the derived-state cache this module now
#: writes through. Statting it would self-invalidate every write — pins
#: observed pre-run could never match the post-write state. Blobs are
#: never read by any rule; a corrupt state index still misses through the
#: store's own empty-on-corrupt read, which rebuilds and heals.
_WALK_SKIP = frozenset({"generated/derived-state"})


def cache_pins(root: Path) -> dict[str, str]:
    """The six validation-input pins every cached entry is keyed on."""
    return {
        "canonical_fingerprint": canonical_fingerprint(root),
        "code_identity": digest_code_identity(root),
        "runtime_digest": runtime_digest(),
        "materials_digest": materials_digest(root),
        "operations_digest": operations_digest(root),
        "validator_inputs": validator_inputs_digest(root),
    }


def observe_pins(root: Path) -> dict[str, str] | None:
    """The live pins, or None when they cannot be observed (never raises
    on environmental failure; the caller then validates uncached)."""
    try:
        return cache_pins(root)
    except OSError:
        return None


def _validation_spec() -> NodeSpec:
    """The derived node holding the static issues (SPEC §14: version 1)."""
    return NodeSpec(
        id=VALIDATION_NODE_ID,
        version=VALIDATION_NODE_VERSION,
        producer_files=VALIDATION_PRODUCER_FILES,
        direct_inputs=tuple(sorted(_VALIDATION_INPUT_IDS.values())),
    )


def _validation_inputs(pins: dict[str, str]) -> dict[str, str]:
    """Map the six frozen pins onto derived direct-input digests.

    Strict: exactly the six `cache_pins` keys, no more and no fewer.
    Anything else is a miss (DerivedError), never a partial key.
    """
    if set(pins) != set(_VALIDATION_INPUT_IDS):
        raise DerivedError(
            f"validation-cache pins must be exactly {sorted(_VALIDATION_INPUT_IDS)}")
    return {_VALIDATION_INPUT_IDS[key]: pins[key] for key in _VALIDATION_INPUT_IDS}


def _freeze_static(issues: list[Issue]) -> list[dict]:
    """Frozen static issues: live advisories filtered at this one choke
    point, so no caller can persist clock-derived issues by accident."""
    return [
        {"severity": issue.severity, "code": issue.code,
         "message": issue.message, "path": issue.path}
        for issue in issues if not is_live_advisory(issue)
    ]


def _valid_static_value(value: Any) -> bool:
    """Whether a derived hit has exactly the frozen-static shape we write."""
    if not isinstance(value, list):
        return False
    return all(
        isinstance(entry, dict)
        and entry.get("severity") in ("E", "W")
        and isinstance(entry.get("code"), str)
        and isinstance(entry.get("message"), str)
        and isinstance(entry.get("path"), str)
        for entry in value
    )


def _restore_static(value: list[dict]) -> list[Issue]:
    return [Issue(
        severity=entry["severity"], code=entry["code"],
        message=entry["message"], path=entry["path"],
    ) for entry in value]


def _inside(relative: str, roots) -> bool:
    return any(relative == r or relative.startswith(f"{r}/") for r in roots)


def validator_inputs_digest(root: Path) -> str:
    """Stat digest of what the validator reads beyond the other five pins.

    One walk of the repository plus the two perimeter levels above it
    (wrapper and umbrella, non-recursive, as ``contracts.perimeter``
    observes them). Inside the canonical roots only names are recorded:
    their bytes are content-pinned already, and an mtime-only change such as
    inbox aging must keep hitting (it reaches status through the live
    advisories). Root dot-entries (``.obsidian`` rewrites its state while
    the app is open), ``.DS_Store`` files, and the validator's own outputs
    in generated/reports/ are recorded by name or skipped, so neither the
    app nor ``tools/validate.py`` forces a miss. Everything else contributes
    size, mtime and ctime — a rule added later that reads a new
    non-canonical path is covered without touching this function.

    Two targeted stat sets cover validator inputs inside otherwise
    name-only subtrees, in the same line format as the walk. Each
    checked text-cache JSON/Markdown file is statted (GEN-* reads them;
    ordinary page blobs are listed but never statted), and each declared local-only
    attachment is statted (definition 2 took the scans out of the
    content fingerprint, so without this a scan rewrite would serve
    the pre-rewrite issues from the cache). An absent path contributes
    no line: its add/delete already moves the pin by the line's
    absence or presence.

    ``generated/derived-state`` is skipped entirely: it holds this
    module's own cache entries, and statting it would self-invalidate
    every write. Corruption there still misses via the store's own
    empty-on-corrupt read.
    """
    root = root.resolve()
    digest = hashlib.sha256()

    def emit(line: str) -> None:
        digest.update(line.encode("utf-8", "surrogateescape"))
        digest.update(b"\0")

    def emit_link(label: str, full: str) -> None:
        try:
            target = os.readlink(full)
        except OSError:
            target = "<unreadable>"
        emit(f"{label}\0<link:{target}>")
        # GEN-* reads through file symlinks. The unchanged link string
        # cannot pin a rewritten target; include its followed stat too.
        try:
            st = os.stat(full)
        except OSError:
            emit(f"{label}\0<unreadable-target>")
        else:
            emit(f"{label}\0target:{st.st_dev}\0{st.st_ino}\0{st.st_size}"
                 f"\0{st.st_mtime_ns}\0{st.st_ctime_ns}\0{st.st_mode}")

    def emit_entry(label: str, entry: os.DirEntry, names_only: bool) -> None:
        if entry.is_symlink():
            if names_only:
                try:
                    target = os.readlink(entry.path)
                except OSError:
                    target = "<unreadable>"
                emit(f"{label}\0<link:{target}>")
            else:
                emit_link(label, entry.path)
            return
        if entry.is_dir(follow_symlinks=False):
            emit(f"{label}/")
            return
        if names_only or entry.name == ".DS_Store":
            emit(label)
            return
        try:
            st = entry.stat(follow_symlinks=False)
        except OSError:
            emit(f"{label}\0<unreadable>")
            return
        if not stat.S_ISREG(st.st_mode):
            emit(f"{label}\0<not-file>")
            return
        emit(f"{label}\0{st.st_size}\0{st.st_mtime_ns}\0{st.st_ctime_ns}")

    def scan(directory: str) -> list[os.DirEntry] | None:
        try:
            with os.scandir(directory) as iterator:
                return sorted(iterator, key=lambda entry: entry.name)
        except OSError:
            return None

    def emit_stat_path(label: str, full: str) -> None:
        """One stat line for a directly addressed path, absent or not.

        Same line format ``emit_entry`` uses for a walked file, without
        listing its directory: an absent path contributes nothing, so
        add/delete moves the pin by the line's absence or presence, while
        a present-but-unstatable path keeps the walk's ``<unreadable>``.
        """
        try:
            st = os.lstat(full)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                emit(f"{label}\0<unreadable>")
            return
        if stat.S_ISLNK(st.st_mode):
            emit_link(label, full)
        elif stat.S_ISDIR(st.st_mode):
            emit(f"{label}/")
        elif not stat.S_ISREG(st.st_mode):
            emit(f"{label}\0<not-file>")
        else:
            emit(f"{label}\0{st.st_size}\0{st.st_mtime_ns}\0{st.st_ctime_ns}")

    root_str = os.fspath(root)
    stack = [root_str]
    while stack:
        directory = stack.pop()
        rel_dir = os.path.relpath(directory, root_str).replace(os.sep, "/")
        entries = scan(directory)
        if entries is None:
            emit(f"{rel_dir}\0<unreadable-dir>")
            continue
        names_only = _inside(rel_dir, CANONICAL_ROOTS)
        for entry in entries:
            rel = entry.name if rel_dir == "." else f"{rel_dir}/{entry.name}"
            if rel_dir == "." and entry.name.startswith("."):
                emit_entry(rel, entry, names_only=True)
                continue
            if entry.name in _WALK_PRUNE:
                continue
            if _inside(rel, _WALK_SKIP):
                continue
            if rel_dir == "generated/reports" and entry.name.lstrip(".").startswith(
                    "validation-report"):
                continue
            emit_entry(rel, entry, names_only=names_only)
            if (entry.is_dir(follow_symlinks=False) and not entry.is_symlink()
                    and rel not in _WALK_NAME_ONLY):
                stack.append(entry.path)

    # List the text-cache directories, but stat only files GEN-* reads.
    # An index-only shortcut misses an unexpected nested *.json/*.md,
    # whose corruption the full validator would report. Page blobs are
    # never statted or read, keeping the expensive part bounded.
    text_cache = os.path.join(root_str, "generated", "text-cache")
    text_stack = [text_cache]
    while text_stack:
        directory = text_stack.pop()
        entries = scan(directory)
        if entries is None:
            if os.path.exists(directory):
                emit(f"{os.path.relpath(directory, root_str)}\0<unreadable-dir>")
            continue
        for child in entries:
            rel = os.path.relpath(child.path, root_str).replace(os.sep, "/")
            is_directory = child.is_dir(follow_symlinks=False) and not child.is_symlink()
            if is_directory or child.name.endswith((".json", ".md")):
                emit_entry(rel, child, names_only=False)
            if is_directory:
                text_stack.append(child.path)

    # Declared local-only attachments: present ones read full stats, so a
    # scan rewrite misses; absent ones contribute nothing (their add/delete
    # already moves the pin through the canonical name walk above).
    for rel in sorted(local_paths(root)):
        emit_stat_path(rel, os.path.join(root_str, *rel.split("/")))

    for label, level in (("<umbrella>", root.parent), ("<wrapper>", root.parent.parent)):
        entries = scan(os.fspath(level))
        if entries is None:
            emit(f"{label}\0<unreadable-dir>")
            continue
        for entry in entries:
            emit_entry(f"{label}/{entry.name}", entry, names_only=False)
    return digest.hexdigest()


def discard_unreadable_cache(root: Path) -> None:
    """Best-effort removal of a structurally unreadable cache file.

    Never raises: callers invoke this on the validation path, where a
    hygiene failure must not become a validation failure.
    """
    try:
        raw = (root / CACHE_RELATIVE).read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError:
        return
    except ValueError:
        # Unparseable includes undecodable: UnicodeDecodeError subclasses
        # ValueError, so non-UTF-8 bytes land here, not in the OSError arm.
        _unlink_quietly(root)
        return
    if not isinstance(data, dict) or data.get("format") != CACHE_FORMAT:
        _unlink_quietly(root)


def _unlink_quietly(root: Path) -> None:
    try:
        (root / CACHE_RELATIVE).unlink()
    except OSError:
        pass


def read_cached_static_issues(
    root: Path, pins: dict[str, str] | None = None,
) -> list[Issue] | None:
    """Cached static issues, or None on any miss.

    A miss covers: absent state, unreadable state, key mismatch, corrupt
    blob (hash-verified by the store), and malformed values (invalidated).
    Never raises on environmental failures. ``pins`` are the live pins
    when the caller already observed them.
    """
    # Pre-migration leftovers must never phantom: a corrupt obsolete
    # sidecar is discarded here (best-effort, never raises) as well as
    # by validate.py's pre-run discard, exactly as the old read path did.
    discard_unreadable_cache(root)
    if pins is None:
        pins = observe_pins(root)
        if pins is None:
            return None
    try:
        inputs = _validation_inputs(pins)
    except DerivedError:
        return None

    def _no_rebuild(_ctx: BuildContext) -> Any:
        raise DerivedError("validation-cache lookup miss (no rebuild)")

    try:
        evaluation = evaluate(
            root, VALIDATION_NODE_ID,
            registry={VALIDATION_NODE_ID: (_validation_spec(), _no_rebuild)},
            inputs=inputs)
    except (OSError, DerivedError, TransactionFailure, ValueError):
        return None
    if not _valid_static_value(evaluation.value):
        try:
            invalidate(root, VALIDATION_NODE_ID)
        except (OSError, TransactionFailure):
            pass
        return None
    return _restore_static(evaluation.value)


def write_static_cache(
    root: Path, issues: list[Issue], pins: dict[str, str] | None = None,
) -> None:
    """Persist the static issues, keyed on ``pins`` (derived store).

    A caller that just validated passes the pins it observed *before*
    validating (see the module docstring); None observes them now, which
    is only sound when ``issues`` cannot be older than this call.

    Live advisories are filtered at the one choke point
    (``_freeze_static``), so no caller can persist clock-derived issues
    by accident. Raises OSError on write failure; both callers treat the
    cache as auxiliary and catch it. Under ``LOS_NO_CACHE=1`` the engine
    bypasses persistence, so this is a no-op that still filters.
    """
    if pins is None:
        pins = cache_pins(root)
    try:
        inputs = _validation_inputs(pins)
    except DerivedError as exc:
        raise OSError(f"validation-cache pins are incomplete: {exc}") from exc
    frozen = _freeze_static(issues)

    def _fixed(_ctx: BuildContext) -> Any:
        return frozen

    try:
        evaluate(
            root, VALIDATION_NODE_ID,
            registry={VALIDATION_NODE_ID: (_validation_spec(), _fixed)},
            inputs=inputs)
    except (DerivedError, TransactionFailure, ValueError) as exc:
        raise OSError(f"validation-cache store failed: {exc}") from exc


def status_issues(repo: Repo, pins: dict[str, str] | None = None) -> list[Issue]:
    """Validation issues for `status`: cached static plus live advisories.

    On a key match the static issues are served from the derived node and
    only the clock-derived advisories are recomputed; on any miss the full
    validator runs (once) and its static issues memoize the node
    best-effort, under pins observed before it ran. Pass ``pins`` observed
    before ``repo`` was loaded; None observes them now. Unobservable pins
    or any cache-layer failure validates uncached, exactly as today: a
    cache problem never becomes stale data or a new refusal.
    """
    if pins is None:
        pins = observe_pins(repo.root)
    if pins is None:
        return validate(repo, online=False)
    try:
        inputs = _validation_inputs(pins)
    except DerivedError:
        return validate(repo, online=False)
    captured: list[Any] = []

    def _build(_ctx: BuildContext) -> Any:
        frozen = _freeze_static(validate(repo, online=False))
        captured.append(frozen)
        return frozen

    try:
        evaluation = evaluate(
            repo.root, VALIDATION_NODE_ID,
            registry={VALIDATION_NODE_ID: (_validation_spec(), _build)},
            inputs=inputs)
    except OSError:
        # The build may have succeeded before the store failed: serve its
        # result (one validation, best-effort memoize, as before) rather
        # than validating twice. Nothing captured means the failure came
        # before or inside the build itself, so validate uncached.
        if captured and _valid_static_value(captured[0]):
            return _restore_static(captured[0]) + advisory_issues(repo)
        return validate(repo, online=False)
    except (DerivedError, TransactionFailure, ValueError):
        return validate(repo, online=False)
    if not _valid_static_value(evaluation.value):
        try:
            invalidate(repo.root, VALIDATION_NODE_ID)
        except (OSError, TransactionFailure):
            pass
        issues = validate(repo, online=False)
        try:
            write_static_cache(repo.root, issues, pins)
        except OSError:
            pass
        return issues
    return _restore_static(evaluation.value) + advisory_issues(repo)
