"""Memoized transaction-receipt checks (#112).

Committed receipts are immutable, but ``check_transaction_receipts``
re-read, re-parsed and schema-checked every one of them on every
validation (244 ms at 328 receipts, growing with each write). This
module memoizes the per-receipt result — parse/schema issues plus the
receipt id and idempotency key — in a ``generated/`` sidecar keyed on
the live content hash, recomputed in each process through the shared
digest layer. Stat equality across processes never proves receipt
immutability. Only new or changed receipts pay the full check; the
cross-receipt duplicate-id and duplicate-idempotency-key checks run
over the cached ids and keys every run, in the same order.

A cold sidecar (absent, unparseable, wrongly shaped, or pinned to
different code, runtime, format providers, or receipt-schema bytes)
falls back to today's full pass and rewrites the sidecar. A corrupt
sidecar is discarded on load, before GEN-JSON can report it as a
phantom. Issues — and the unhashable-id crash the run contains as
SCHEMA-DEPENDENT — are byte-identical warm or cold.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .. import __version__
from ..derived.identity import (
    digest_code_identity,
    runtime_digest,
    validator_runtime_digest,
)
from ..digests import file_content, file_sha256
from ..loading.yamlio import UniqueKeySafeLoader
from .common import Issue

if TYPE_CHECKING:
    from .core import Validator

#: Sidecar location inside generated/. The ``validation-report`` prefix
#: keeps it under the reports GC keep-rule and the validator's own
#: GENERATED_REPORT_PREFIXES allowlist, and ``validator_inputs_digest``
#: skips it, so refreshing it never invalidates the status cache.
SIDECAR_RELATIVE = Path("generated/reports/validation-report-receipts.cache.json")

#: Sidecar contract. A reader meeting another format revalidates fully.
RECEIPT_CACHE_FORMAT = 2


def _current_pins(validator: Validator) -> dict[str, str]:
    """Everything a cached per-receipt verdict depends on."""
    root = validator.repo.root
    # Validator captured its schemas before this pass. A later disk read
    # could pin a new schema while the verdict used the old loaded one.
    schema = validator.schemas.get("transaction-receipt")
    schema_pin = "<missing>" if schema is None else "sha256:" + hashlib.sha256(
        json.dumps(schema, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "code_identity": digest_code_identity(root),
        "runtime_digest": runtime_digest(),
        "validator_runtime_digest": validator_runtime_digest(),
        "receipt_schema": schema_pin,
    }


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _load_entries(validator: Validator) -> tuple[dict[str, Any], dict[str, str]]:
    """Cached per-receipt entries plus the pins they were read under.

    The pins describe the loaded schema this run uses, reused by the
    save so one run computes them once. A structurally unreadable
    sidecar (unparseable, wrong shape, wrong format) is discarded
    best-effort, exactly like the status cache: the validator scans
    ``generated/**/*.json`` itself, so a corrupt sidecar would otherwise
    surface as a GEN-JSON error about the cache. A pin mismatch leaves
    the file in place — this run overwrites it.
    """
    root = validator.repo.root
    pins = _current_pins(validator)
    sidecar = root / SIDECAR_RELATIVE
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except OSError:
        return {}, pins
    except ValueError:
        _unlink_quietly(sidecar)
        return {}, pins
    if not isinstance(data, dict) or data.get("format") != RECEIPT_CACHE_FORMAT:
        _unlink_quietly(sidecar)
        return {}, pins
    if not isinstance(data.get("pins"), dict) or data["pins"] != pins:
        return {}, pins
    entries = data.get("entries")
    if not isinstance(entries, dict):
        _unlink_quietly(sidecar)
        return {}, pins
    return entries, pins


def _save_entries(
    root: Path, entries: dict[str, Any], pins: dict[str, str],
) -> None:
    """Persist per-receipt entries under ``pins`` (atomic write).

    Best-effort in both directions: an unserializable entry is dropped
    (that receipt revalidates fresh every run), and a write failure is
    swallowed — the cache is auxiliary and must never fail validation.
    """
    safe = {rel: entry for rel, entry in entries.items() if _json_safe(entry)}
    try:
        text = json.dumps({
            "_generated": {
                "warning": "GENERATED file - do not edit; "
                           "rebuilt by python tools/validate.py",
                "generator": f"learning_os v{__version__}",
            },
            "format": RECEIPT_CACHE_FORMAT,
            "pins": pins,
            "entries": safe,
        }, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return
    target = root / SIDECAR_RELATIVE
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.name}.tmp-{os.getpid()}")
        try:
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, target)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
    except OSError:
        pass


def _json_safe(value: Any) -> bool:
    """Whether ``value`` round-trips through the sidecar's JSON.

    Receipt ids are usually strings, but a schema-invalid receipt may
    carry anything YAML parses — including datetimes, which ``json``
    cannot write. Such a receipt simply stays uncached.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_safe(item)
                   for key, item in value.items())
    return False


def _receipt_stat(path: Path) -> tuple[int, int] | None:
    """The ``(size, mtime_ns)`` cache key, or None when unstatable."""
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_size, stat.st_mtime_ns)


def _entry_shape_ok(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not isinstance(entry.get("size"), int) \
            or not isinstance(entry.get("mtime_ns"), int):
        return False
    if not isinstance(entry.get("sha256"), str) \
            or not isinstance(entry.get("parse_failed"), bool):
        return False
    issues = entry.get("issues")
    if not isinstance(issues, list):
        return False
    for issue in issues:
        if not isinstance(issue, dict) \
                or issue.get("severity") not in ("E", "W") \
                or not isinstance(issue.get("code"), str) \
                or not isinstance(issue.get("message"), str) \
                or not isinstance(issue.get("path"), str):
            return False
    if "id" not in entry or "idempotency_key" not in entry \
            or not _json_safe(entry["id"]) or not _json_safe(entry["idempotency_key"]):
        return False
    proof = entry.get("proof_sha256")
    return isinstance(proof, str) and proof == _proof_digest(entry)


def _proof_digest(entry: dict) -> str | None:
    """Detect structural cache corruption beyond JSON syntax.

    This is an integrity checksum, not authority or authentication: the
    generated sidecar remains disposable local cache state.
    """
    body = {key: value for key, value in entry.items() if key != "proof_sha256"}
    try:
        raw = json.dumps(body, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_fresh(
    validator: Validator, path: Path, rel: str,
) -> tuple[list[Issue], Any, Any, bool, str | None]:
    """Today's per-receipt body: parse, schema-check, extract id and key.

    Schema issues append to the validator as they always have; the
    returned issues are the same objects, for the sidecar entry. An
    unparseable receipt reports and stops here (``parse_failed``), as
    the ``continue`` in the old loop did — it never joins the
    duplicate checks.
    """
    mark = len(validator.issues)
    content_hash = None
    try:
        # `yaml.safe_load` is the pure-Python loader: 214 receipts cost
        # about a second of parsing on every validate, and every
        # canonical write validates. This is the loader the rest of the
        # repository already reads through — LibYAML when the C
        # extension is present, and the same duplicate-key rule, which
        # no current receipt trips. A file it refuses is reported below
        # as an unparseable receipt rather than raised.
        # Bind the proof hash to exactly the bytes parsed. Re-reading after
        # schema checking can otherwise bless a concurrent replacement.
        content = file_content(validator.repo.root, path, path.read_bytes)
        content_hash = hashlib.sha256(content).hexdigest()
        data = yaml.load(content.decode("utf-8"), Loader=UniqueKeySafeLoader) or {}
    except Exception as exc:  # noqa: BLE001 - report as validation issue
        validator.err("TRANSACTION-RECEIPT", f"cannot parse receipt: {exc}", rel)
        return list(validator.issues[mark:]), None, None, True, content_hash
    validator._schema_check("transaction-receipt", data, rel)
    fresh = list(validator.issues[mark:])
    transaction_id = data.get("id") if isinstance(data, dict) else None
    request = data.get("request") if isinstance(data, dict) else None
    key = request.get("idempotency_key") if isinstance(request, dict) else None
    return fresh, transaction_id, key, False, content_hash


def _restore(issues: list[dict]) -> list[Issue]:
    return [Issue(severity=entry["severity"], code=entry["code"],
                  message=entry["message"], path=entry["path"])
            for entry in issues]


def _freeze(issues: list[Issue]) -> list[dict]:
    return [{"severity": issue.severity, "code": issue.code,
             "message": issue.message, "path": issue.path}
            for issue in issues]


def _content_hash(root: Path, path: Path) -> str | None:
    """The receipt's content hash through the shared layer, or None when
    the file cannot be read (the fresh check below then reports it, as
    today)."""
    try:
        return file_sha256(root, path, lambda p=path: [p.read_bytes()])
    except OSError:
        return None


def receipt_file_issues(validator: Validator) -> None:
    """Per-receipt parse/schema issues plus cross-receipt duplicates.

    Only new or changed receipts pay the full check; everything else is
    replayed from the sidecar. The duplicate checks always run over the
    live (cached or fresh) ids and keys, in sorted-path order, so their
    issues — including which path each names as the first occurrence —
    match the full pass exactly.
    """
    root = validator.repo.root
    directory = root / "operations" / "transactions"
    cached, pins = _load_entries(validator)
    fresh: dict[str, Any] = {}
    seen: set = set()
    seen_keys: dict[str, str] = {}
    for path in sorted(directory.glob("transaction-*.yaml")):
        rel = validator._rel(path)
        entry = cached.get(rel)
        if not _entry_shape_ok(entry):
            entry = None
        stat = _receipt_stat(path)
        reused = False
        # Persisted stat equality is not content proof: a same-size edit
        # can restore mtime. Hash live receipt bytes in each process; the
        # shared digest layer makes repeated checks within it inexpensive.
        if entry is not None and stat is not None \
                and _content_hash(root, path) == entry["sha256"]:
            entry = {**entry, "size": stat[0], "mtime_ns": stat[1]}
            entry["proof_sha256"] = _proof_digest(entry)
            reused = True
        if reused:
            assert entry is not None
            issues = _restore(entry["issues"])
            transaction_id = entry["id"]
            key = entry["idempotency_key"]
            parse_failed = entry["parse_failed"]
            validator.issues.extend(issues)
            if _json_safe(entry):
                fresh[rel] = entry
        else:
            issues, transaction_id, key, parse_failed, content_hash = _validate_fresh(
                validator, path, rel)
            if stat is not None:
                if content_hash is not None:
                    candidate = {
                        "size": stat[0],
                        "mtime_ns": stat[1],
                        "sha256": content_hash,
                        "parse_failed": parse_failed,
                        "id": transaction_id,
                        "idempotency_key": key,
                        "issues": _freeze(issues),
                    }
                    candidate["proof_sha256"] = _proof_digest(candidate)
                    if _json_safe(candidate):
                        fresh[rel] = candidate
        if parse_failed:
            continue
        # Two committed receipts sharing one idempotency key is genuinely
        # ambiguous: replay can prove at most one of them. Ledger loss
        # followed by key reuse produces exactly this (JF-13/L4).
        if transaction_id in seen:
            validator.err("TRANSACTION-RECEIPT",
                          f"duplicate transaction receipt id '{transaction_id}'", rel)
        seen.add(transaction_id)
        if isinstance(key, str) and key:
            first = seen_keys.setdefault(key, rel)
            if first != rel:
                validator.err("TRANSACTION-RECEIPT",
                              f"duplicate idempotency key '{key}' also committed "
                              f"in {first}", rel)
    _save_entries(root, fresh, pins)
