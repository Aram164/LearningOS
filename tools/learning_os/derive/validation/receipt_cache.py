"""Memoized transaction-receipt checks (#112, 4.3 derived).

Committed receipts are immutable, but ``check_transaction_receipts``
re-read, re-parsed and schema-checked every one of them on every
validation (244 ms at 328 receipts, growing with each write). This
module memoizes the per-receipt result — parse/schema issues plus the
receipt id and idempotency key — in one derived node per receipt, keyed
on the live content hash, recomputed in each process through the shared
digest layer. Stat equality across processes never proves receipt
immutability. Only new or changed receipts pay the full check; the
cross-receipt duplicate-id and duplicate-idempotency-key checks run
over the cached ids and keys every run, in the same order.

A cold node (absent state, corrupt blob, or pinned to different code,
runtime, format providers, or receipt-schema bytes) falls back to
today's full per-receipt pass. Blobs are hash-verified, so a corrupt
value is never served. Issues — and the unhashable-id crash the run
contains as SCHEMA-DEPENDENT — are byte-identical warm or cold.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import yaml

from learning_os.derive.validation.common import Issue
from learning_os.domain.failures import TransactionFailure
from learning_os.store.derived.engine import BuildContext, evaluate, evaluate_many
from learning_os.store.derived.identity import (
    digest_code_identity,
    runtime_digest,
    validator_runtime_digest,
)
from learning_os.store.derived.model import DERIVED_SUBSTRATE_FILES, DerivedError, NodeSpec
from learning_os.store.derived.store import invalidate
from learning_os.store.digests import file_content, file_sha256
from learning_os.store.loading.yamlio import UniqueKeySafeLoader

if TYPE_CHECKING:
    from learning_os.domain.snapshot import Repo


class ReceiptValidator(Protocol):
    """The receipt pass's input surface, without importing the rule orchestrator."""

    repo: Repo
    schemas: dict
    schema_registry: Any
    issues: list[Issue]

    def err(self, code: str, msg: str, path: str = "") -> None: ...

    def _rel(self, path: Path) -> str: ...

    def _schema_check(self, name: str, instance: Any, where: str) -> None: ...

#: Obsolete sidecar location (pre-4.3). Active verdicts live in per-receipt
#: derived nodes; this path survives only so leftovers are reclaimed by
#: `diagnostics_prune --derived-state` and the reports GC. Never written.
SIDECAR_RELATIVE = Path("generated/reports/validation-report-receipts.cache.json")

#: Obsolete sidecar contract, kept for the leftover reclaim above.
RECEIPT_CACHE_FORMAT = 2

#: Per-receipt derived nodes (SPEC §14, D-12): one node per artifact, so an
#: expensive receipt never invalidates an unrelated one.
RECEIPT_NODE_VERSION = 1
RECEIPT_PRODUCER_FILES = (
    "tools/learning_os/derive/validation/receipt_cache.py",
    *DERIVED_SUBSTRATE_FILES,
)

#: `_current_pins` key -> derived direct-input id for the four globals.
_RECEIPT_GLOBAL_INPUT_IDS = {
    "code_identity": "cache.receipt.code_identity",
    "runtime_digest": "cache.receipt.runtime_digest",
    "validator_runtime_digest": "cache.receipt.validator_runtime_digest",
    "receipt_schema": "cache.receipt.schema",
}


def _receipt_node_id(rel: str) -> str:
    """Logical derived node holding one receipt's verdict."""
    return f"cache.receipt:{rel}"


def _receipt_content_input_id(rel: str) -> str:
    """Direct-input id carrying one receipt's live content hash."""
    return f"cache.receipt.content:{rel}"


def _receipt_spec(rel: str) -> NodeSpec:
    """One receipt's node: four globals plus its own content hash."""
    return NodeSpec(
        id=_receipt_node_id(rel),
        version=RECEIPT_NODE_VERSION,
        producer_files=RECEIPT_PRODUCER_FILES,
        direct_inputs=(
            *_RECEIPT_GLOBAL_INPUT_IDS.values(),
            _receipt_content_input_id(rel),
        ),
    )


def _current_pins(validator: ReceiptValidator) -> dict[str, str]:
    """Everything a cached per-receipt verdict depends on."""
    root = validator.repo.root
    # Validator captured its schemas before this pass. A later disk read
    # could pin a new schema while the verdict used the old loaded one.
    schema = validator.schemas.get("transaction-receipt")
    schema_inputs = {
        "receipt": schema,
        "registry": {uri: resource.contents
                     for uri, resource in validator.schema_registry.items()},
    }
    schema_pin = "sha256:" + hashlib.sha256(
        json.dumps(schema_inputs, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "code_identity": digest_code_identity(root),
        "runtime_digest": runtime_digest(),
        "validator_runtime_digest": validator_runtime_digest(),
        "receipt_schema": schema_pin,
    }


def _receipt_global_inputs(pins: dict[str, str]) -> dict[str, str]:
    """Map the four frozen global pins onto derived direct-input digests."""
    return {_RECEIPT_GLOBAL_INPUT_IDS[key]: pins[key]
            for key in _RECEIPT_GLOBAL_INPUT_IDS}


def _json_safe(value: Any) -> bool:
    """Whether ``value`` round-trips through the derived blob's JSON.

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


def _valid_verdict(value: Any) -> bool:
    """Whether a derived hit has exactly the verdict shape we write."""
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("sha256"), str) \
            or not isinstance(value.get("parse_failed"), bool):
        return False
    issues = value.get("issues")
    if not isinstance(issues, list):
        return False
    for issue in issues:
        if not isinstance(issue, dict) \
                or issue.get("severity") not in ("E", "W") \
                or not isinstance(issue.get("code"), str) \
                or not isinstance(issue.get("message"), str) \
                or not isinstance(issue.get("path"), str):
            return False
    return "id" in value and "idempotency_key" in value \
        and _json_safe(value["id"]) and _json_safe(value["idempotency_key"])


def _validate_fresh(
    validator: ReceiptValidator, path: Path, rel: str,
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


def _producers_present(root: Path) -> bool:
    """Whether every receipt-node producer file exists under ``root``."""
    return all((root / rel).is_file() for rel in RECEIPT_PRODUCER_FILES)


def _make_pure_build(validator: ReceiptValidator, path: Path, rel: str):
    """A derived build that freezes one receipt's verdict without appending.

    `_validate_fresh` appends as it always has; the append is contained
    here so the caller replays exactly once from the returned value —
    a stored miss never duplicates, and a store failure never loses.
    Looks up `_validate_fresh` at call time so tests can count calls.
    """
    def build(_ctx: BuildContext) -> Any:
        mark = len(validator.issues)
        try:
            issues, transaction_id, key, parse_failed, content_hash = _validate_fresh(
                validator, path, rel)
        finally:
            del validator.issues[mark:]
        return {
            "sha256": content_hash,
            "parse_failed": parse_failed,
            "id": transaction_id,
            "idempotency_key": key,
            "issues": _freeze(issues),
        }
    return build


def receipt_file_issues(validator: ReceiptValidator) -> None:
    """Per-receipt parse/schema issues plus cross-receipt duplicates.

    Only new or changed receipts pay the full check; everything else is
    replayed from its derived node. The duplicate checks always run over
    the live (cached or fresh) ids and keys, in sorted-path order, so
    their issues — including which path each names as the first
    occurrence — match the full pass exactly.
    """
    root = validator.repo.root
    directory = root / "operations" / "transactions"
    pins = _current_pins(validator)
    global_inputs = _receipt_global_inputs(pins)
    # Persisted stat equality is not content proof: a same-size edit can
    # restore mtime. Hash live receipt bytes in each process; the shared
    # digest layer makes repeated checks within it inexpensive. Unreadable
    # files stay uncached: the fresh check below reports them, as today.
    rows: list[tuple[Path, str, str | None]] = []
    for path in sorted(directory.glob("transaction-*.yaml")):
        rel = validator._rel(path)
        rows.append((path, rel, _content_hash(root, path)))
    cacheable = [(path, rel, digest) for path, rel, digest in rows
                 if digest is not None]
    verdicts: dict[str, dict] = {}
    if cacheable:
        registry = {
            _receipt_node_id(rel): (_receipt_spec(rel), _make_pure_build(validator, path, rel))
            for path, rel, _digest in cacheable
        }
        inputs = dict(global_inputs)
        for _path, rel, digest in cacheable:
            assert digest is not None
            inputs[_receipt_content_input_id(rel)] = digest
        node_ids = [_receipt_node_id(rel) for _path, rel, _digest in cacheable]
        try:
            evaluations = evaluate_many(root, node_ids, registry=registry, inputs=inputs)
        except (OSError, TransactionFailure, ValueError):
            evaluations = None
        except DerivedError:
            if not _producers_present(root):
                evaluations = None
            else:
                # One unserializable verdict (e.g. a datetime id) aborts
                # the shared session; isolate per receipt so unrelated
                # receipts still reuse. Each failure below falls through
                # to a fresh check in the replay loop.
                evaluations = {}
                for path, rel, digest in cacheable:
                    node_id = _receipt_node_id(rel)
                    single = dict(global_inputs)
                    assert digest is not None
                    single[_receipt_content_input_id(rel)] = digest
                    try:
                        evaluations[node_id] = evaluate(
                            root, node_id,
                            registry={node_id: (
                                _receipt_spec(rel),
                                _make_pure_build(validator, path, rel))},
                            inputs=single)
                    except (OSError, DerivedError, TransactionFailure, ValueError):
                        continue
        if evaluations is not None:
            live = {rel: digest for _path, rel, digest in cacheable}
            for _path, rel, _digest in cacheable:
                evaluation = evaluations.get(_receipt_node_id(rel))
                if evaluation is None:
                    continue
                value = evaluation.value
                # The key already required the live hash; the stored proof
                # must agree too, or a torn build (bytes replaced between
                # the input hash and the parse) would be served. Either
                # failure invalidates and falls through to fresh below.
                if not _valid_verdict(value) or value.get("sha256") != live[rel]:
                    try:
                        invalidate(root, _receipt_node_id(rel))
                    except (OSError, TransactionFailure):
                        pass
                    continue
                verdicts[rel] = value
    seen: set = set()
    seen_keys: dict[str, str] = {}
    for path, rel, _digest in rows:
        verdict = verdicts.get(rel)
        if verdict is not None:
            issues = _restore(verdict["issues"])
            transaction_id = verdict["id"]
            key = verdict["idempotency_key"]
            parse_failed = verdict["parse_failed"]
            validator.issues.extend(issues)
        else:
            _issues, transaction_id, key, parse_failed, _content = _validate_fresh(
                validator, path, rel)
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
