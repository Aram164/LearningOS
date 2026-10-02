"""Cached static validation issues for fast `status` reads (#103).

`status` re-ran the full validator on every invocation. The validator's
output splits two ways: static issues, which change only when validation
inputs change, and the two clock-derived advisories (`WS-NEGLECT`,
`INBOX-STALE`), which can appear with no authored change at all simply
because time passed. This module caches the static issues at
``generated/reports/validation-report.cache.json`` under content pins and
recomputes the advisories live on every read, so a cache hit answers
without re-validating while clock-derived warnings stay current.

Pinned inputs (all must match; anything else misses and re-validates):

- canonical fingerprint: the authored canonical inputs;
- code identity: ``digest_code_identity`` (target AND executing trees) —
  a validator change invalidates too;
- runtime: interpreter and YAML/schema distribution versions;
- materials: a stat digest of the materials tree (add/delete/replace);
- operations: the revision ledger, AI request bundles, and garden
  sidecars — AI-request prep changes validation with no fingerprint move.

Warmth comes from two writers: `status` memoizes on a miss (best-effort,
never failing the read) and ``tools/validate.py`` refreshes the cache on
offline runs only — ``--online`` results depend on network state and must
not poison it. There is deliberately no commit-path hook: every commit
moves ledger/fingerprint pins, so post-write reads correctly miss once,
while refreshing from mid-commit results would miss receipt/idempotency
errors (including the deliberate JF-13/L4 duplicate-key check).

A structurally unreadable cache (unparseable, wrong shape, wrong format)
is discarded best-effort before its caller falls back to a full run: the
validator scans ``generated/**/*.json`` itself, so a corrupt cache file
would otherwise surface as a GEN-JSON error about the cache and get
memoized as a phantom that no cleanup invalidates (``generated/`` is not
fingerprinted). A pin mismatch leaves the file in place — a later offline
validate overwrites it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from . import __version__
from .derived.identity import digest_code_identity, runtime_digest
from .fingerprint import canonical_fingerprint
from .manifest_identity import materials_digest, operations_digest
from .rules import validate
from .rules.advisories import advisory_issues, is_live_advisory
from .rules.common import Issue

if TYPE_CHECKING:
    from .loader import Repo

#: Cache location inside generated/. The ``validation-report`` prefix keeps
#: it under both the reports GC keep-rule (genout/outputs) and the
#: validator's own GENERATED_REPORT_PREFIXES allowlist.
CACHE_RELATIVE = Path("generated/reports/validation-report.cache.json")

#: Cache contract. A reader meeting another format discards and misses.
CACHE_FORMAT = 1


def cache_pins(root: Path) -> dict[str, str]:
    """The five validation-input pins every cached entry is keyed on."""
    return {
        "canonical_fingerprint": canonical_fingerprint(root),
        "code_identity": digest_code_identity(root),
        "runtime_digest": runtime_digest(),
        "materials_digest": materials_digest(root),
        "operations_digest": operations_digest(root),
    }


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


def read_cached_static_issues(root: Path) -> list[Issue] | None:
    """Cached static issues, or None on any miss.

    A miss covers: absent file, unreadable file, structural unread
    (discarded, see above), pin mismatch (left in place), and malformed
    entries (discarded). Never raises on environmental failures.
    """
    try:
        raw = (root / CACHE_RELATIVE).read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError:
        return None
    except ValueError:
        _unlink_quietly(root)
        return None
    if not isinstance(data, dict) or data.get("format") != CACHE_FORMAT:
        _unlink_quietly(root)
        return None
    try:
        pins = cache_pins(root)
    except OSError:
        return None
    if not isinstance(data.get("pins"), dict) or data["pins"] != pins:
        return None
    entries = data.get("issues")
    if not isinstance(entries, list):
        _unlink_quietly(root)
        return None
    issues: list[Issue] = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or entry.get("severity") not in ("E", "W")
            or not isinstance(entry.get("code"), str)
            or not isinstance(entry.get("message"), str)
            or not isinstance(entry.get("path", ""), str)
        ):
            _unlink_quietly(root)
            return None
        issues.append(Issue(
            severity=entry["severity"],
            code=entry["code"],
            message=entry["message"],
            path=entry.get("path", ""),
        ))
    return issues


def write_static_cache(root: Path, issues: list[Issue]) -> None:
    """Persist the static issues, keyed on the live pins (atomic write).

    Live advisories are filtered here — the one choke point — so no
    caller can persist clock-derived issues by accident. Raises OSError
    on write failure; both callers treat the cache as auxiliary and
    catch it.
    """
    static = [issue for issue in issues if not is_live_advisory(issue)]
    payload = {
        "_generated": {
            "warning": "GENERATED file - do not edit; rebuilt by python tools/validate.py",
            "generator": f"learning_os v{__version__}",
        },
        "format": CACHE_FORMAT,
        "pins": cache_pins(root),
        "issues": [
            {"severity": issue.severity, "code": issue.code,
             "message": issue.message, "path": issue.path}
            for issue in static
        ],
    }
    target = root / CACHE_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tmp, target)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def status_issues(repo: Repo) -> list[Issue]:
    """Validation issues for `status`: cached static plus live advisories.

    On a pin match the static issues are served from the cache and only
    the clock-derived advisories are recomputed; on any miss the full
    validator runs and its static issues memoize the cache best-effort.
    """
    cached = read_cached_static_issues(repo.root)
    if cached is not None:
        return cached + advisory_issues(repo)
    issues = validate(repo, online=False)
    try:
        write_static_cache(repo.root, issues)
    except OSError:
        pass
    return issues
