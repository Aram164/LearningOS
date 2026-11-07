"""SQLite-backed Verifier and Reconciliation Engine for Transactions (Task B.2).

Replaces dictionary lookups in learning_os.store.evidence and store.revisions
with relational queries over SQLite tables:
- Monotone floor verification via anti-join
- Relational idempotency replay resolution
- Reverse ledger traversal for provenance proofs
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from learning_os.domain.failures import (
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
)
from learning_os.domain.transaction import TransactionResult
from learning_os.store.contracts.gateway import GatewayRequestContext
from learning_os.store.contracts.write_scopes import WriteScopeError, scope_matches, write_target
from learning_os.store.evidence import (
    _proven_delivery_delegation,
    default_authority_root,
    dump_idempotency_entries,
    idempotency_ledger_path,
)
from learning_os.store.layout import PathBoundaryError, read_text_inside
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import dump_revisions, revision_ledger_path

from spike_receipt_ingest import build_receipt_store


def load_revisions_sql(root: Path, conn: sqlite3.Connection | None = None) -> dict[str, int]:
    """Read live revisions from SQLite live_revisions table."""
    close_after = False
    if conn is None:
        conn = sqlite3.connect(":memory:")
        build_receipt_store(root, conn)
        close_after = True

    try:
        cur = conn.cursor()
        cur.execute("SELECT artifact, revision FROM live_revisions ORDER BY artifact")
        return {str(art): int(rev) for art, rev in cur.fetchall()}
    finally:
        if close_after:
            conn.close()


def artifact_revision_sql(root: Path, artifact_id: str, conn: sqlite3.Connection | None = None) -> int:
    """Read a single artifact revision from SQLite."""
    close_after = False
    if conn is None:
        conn = sqlite3.connect(":memory:")
        build_receipt_store(root, conn)
        close_after = True

    try:
        cur = conn.cursor()
        cur.execute("SELECT revision FROM live_revisions WHERE artifact = ?", (artifact_id,))
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        if close_after:
            conn.close()


def load_idempotency_entries_sql(root: Path, conn: sqlite3.Connection | None = None) -> dict[str, dict]:
    """Read idempotency ledger entries and child revisions from SQLite."""
    close_after = False
    if conn is None:
        conn = sqlite3.connect(":memory:")
        build_receipt_store(root, conn)
        close_after = True

    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT idempotency_key, request_id, capability, channel,
                      intent_sha256, transaction_id, receipt_path,
                      snapshot_before, snapshot_after
               FROM idempotency_entries ORDER BY idempotency_key"""
        )
        entries: dict[str, dict[str, Any]] = {}
        for (
            key, req_id, cap, chan, intent, tx_id, rec_path, snap_b, snap_a
        ) in cur.fetchall():
            entries[str(key)] = {
                "request_id": str(req_id),
                "capability": str(cap),
                "channel": str(chan),
                "intent_sha256": str(intent),
                "transaction_id": str(tx_id),
                "receipt_path": str(rec_path),
                "snapshot_before": str(snap_b),
                "snapshot_after": str(snap_a),
                "revisions": {},
            }

        cur.execute("SELECT idempotency_key, artifact, revision FROM idempotency_revisions")
        for key, art, rev in cur.fetchall():
            if str(key) in entries:
                entries[str(key)]["revisions"][str(art)] = int(rev)

        return entries
    finally:
        if close_after:
            conn.close()


def verify_monotone_floors_sql(conn: sqlite3.Connection) -> list[tuple[str, str, int, int]]:
    """Anti-join query finding any transaction whose rev_after exceeds live_revisions."""
    cur = conn.cursor()
    cur.execute(
        """SELECT rr.transaction_id, rr.artifact, rr.rev_after, COALESCE(lr.revision, 0) AS current_rev
           FROM receipt_revisions rr
           LEFT JOIN live_revisions lr ON rr.artifact = lr.artifact
           WHERE COALESCE(lr.revision, 0) < rr.rev_after
           ORDER BY rr.transaction_id, rr.artifact"""
    )
    return [(str(row[0]), str(row[1]), int(row[2]), int(row[3])) for row in cur.fetchall()]


def verify_committed_evidence_sql(
    root: Path,
    request: GatewayRequestContext,
    *,
    authority_root: Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> tuple[dict, dict, Path] | None:
    """SQL-backed strict committed evidence verification."""
    close_after = False
    if conn is None:
        conn = sqlite3.connect(":memory:")
        build_receipt_store(root, conn)
        close_after = True

    try:
        cur = conn.cursor()

        # 1. Lookup Idempotency Ledger Entry
        cur.execute(
            """SELECT request_id, capability, channel, intent_sha256,
                      transaction_id, receipt_path, snapshot_before, snapshot_after
               FROM idempotency_entries WHERE idempotency_key = ?""",
            (request.idempotency_key,),
        )
        row_tuple = cur.fetchone()
        if row_tuple is None:
            return None

        (
            req_id, cap, chan, intent, tx_id, receipt_relative, snap_b, snap_a
        ) = row_tuple

        row = {
            "request_id": str(req_id),
            "capability": str(cap),
            "channel": str(chan),
            "intent_sha256": str(intent),
            "transaction_id": str(tx_id),
            "receipt_path": str(receipt_relative),
            "snapshot_before": str(snap_b),
            "snapshot_after": str(snap_a),
            "revisions": {},
        }

        cur.execute(
            "SELECT artifact, revision FROM idempotency_revisions WHERE idempotency_key = ?",
            (request.idempotency_key,),
        )
        for art, rev in cur.fetchall():
            row["revisions"][str(art)] = int(rev)

        # 2. Strict Request Binding Checks
        if row["capability"] != request.capability or row["intent_sha256"] != request.intent_sha256:
            raise TransactionIdempotencyConflict(
                "idempotency key was already used for a different approved intent"
            )
        if row["request_id"] != request.request_id:
            raise TransactionIdempotencyConflict(
                "idempotency ledger records a different request id for this key "
                f"({row['request_id']}); an exact retry resubmits that request's saved "
                "envelope unchanged"
            )
        if row["channel"] != request.channel:
            raise ReplayEvidenceError(
                "idempotency ledger records a different channel for this key"
            )

        # 3. Path canonicalization and existence
        try:
            receipt_path, normalized = write_target(root, root / receipt_relative)
        except WriteScopeError as exc:
            raise ReplayEvidenceError(
                f"idempotency ledger names an unsafe receipt: {exc}"
            ) from exc
        if normalized != receipt_relative or not receipt_path.is_file():
            raise ReplayEvidenceError(
                "idempotency ledger names a missing or non-canonical receipt"
            )

        try:
            receipt = yaml.load(read_text_inside(root, receipt_path), Loader=UniqueKeySafeLoader)
        except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
            raise ReplayEvidenceError(f"idempotent receipt is unreadable: {exc}") from exc
        if not isinstance(receipt, dict):
            raise ReplayEvidenceError("idempotent receipt is not a mapping")

        # 4. Schema Validation
        schema_root = authority_root or default_authority_root(root) or root
        schema_path = schema_root / "system" / "schema" / "transaction-receipt.schema.json"
        if not schema_path.is_file():
            raise ReplayEvidenceError(
                "no transaction receipt schema available to verify replay evidence"
            )
        receipt_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_errors = sorted(
            Draft202012Validator(receipt_schema).iter_errors(receipt),
            key=lambda error: list(error.path),
        )
        if schema_errors:
            detail = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<receipt>'}: {error.message}"
                for error in schema_errors[:4]
            )
            raise ReplayEvidenceError(f"idempotent receipt fails schema validation: {detail}")

        if receipt.get("schema_version") != 2:
            raise ReplayEvidenceError("idempotent receipt is not a GatewayEnvelopeV2 receipt")
        if receipt.get("id") != row["transaction_id"]:
            raise ReplayEvidenceError("idempotent receipt id does not match its ledger entry")
        if receipt.get("capability") != request.capability:
            raise ReplayEvidenceError("idempotent receipt names a different capability")
        if receipt.get("status") != "committed":
            raise ReplayEvidenceError("idempotent receipt is not committed")

        receipt_request = receipt.get("request")
        if not isinstance(receipt_request, dict):
            raise ReplayEvidenceError("idempotent receipt has no request record")
        if receipt_request.get("idempotency_key") != request.idempotency_key:
            raise ReplayEvidenceError("idempotent receipt does not match its ledger entry")
        if receipt_request.get("intent_sha256") != request.intent_sha256:
            raise ReplayEvidenceError("idempotent receipt does not match its ledger entry")
        if receipt_request.get("request_id") != request.request_id:
            raise ReplayEvidenceError("idempotent receipt names a different request id")
        if receipt_request.get("channel") != request.channel:
            raise ReplayEvidenceError("idempotent receipt names a different channel")
        approval = receipt_request.get("approval")
        approval_subject = approval.get("subject_sha256") if isinstance(approval, dict) else None
        if approval_subject != request.approval_subject_sha256:
            raise ReplayEvidenceError(
                "idempotent receipt approval subject does not match this request"
            )

        if receipt.get("snapshot_before") != row["snapshot_before"] \
                or receipt.get("snapshot_after") != row["snapshot_after"]:
            raise ReplayEvidenceError("idempotent receipt snapshot does not match its ledger entry")

        artifact_revisions = receipt.get("artifact_revisions")
        if not isinstance(artifact_revisions, dict):
            raise ReplayEvidenceError("idempotent receipt has no artifact revisions")
        for artifact, after in row["revisions"].items():
            entry = artifact_revisions.get(artifact)
            if not isinstance(entry, dict) or entry.get("after") != after:
                raise ReplayEvidenceError(
                    f"idempotent receipt artifact revision does not match its ledger entry: {artifact}"
                )

        # 5. Monotone Floor Verification via SQL
        cur.execute(
            """SELECT ir.artifact, ir.revision, COALESCE(lr.revision, 0)
               FROM idempotency_revisions ir
               LEFT JOIN live_revisions lr ON ir.artifact = lr.artifact
               WHERE ir.idempotency_key = ? AND COALESCE(lr.revision, 0) < ir.revision""",
            (request.idempotency_key,),
        )
        floor_violation = cur.fetchone()
        if floor_violation:
            art, after_val, cur_val = floor_violation
            raise ReplayEvidenceError(
                f"the artifact revision ledger contradicts this receipt: {art} "
                f"stands at {cur_val}, below the {after_val} this transaction recorded"
            )

        # 6. Authority Grants & Writes Scopes
        writes = receipt.get("writes")
        if not isinstance(writes, list) or not writes:
            raise ReplayEvidenceError("idempotent receipt records no writes")

        authority = receipt.get("authority")
        grants = authority.get("grants") if isinstance(authority, dict) else None
        if not isinstance(grants, list) or not grants:
            raise ReplayEvidenceError("idempotent receipt has no authority grants")

        resolved_authority_root = authority_root or default_authority_root(root)
        allowed_scopes: list[str] = []
        if resolved_authority_root is not None:
            from learning_os.store.contracts.capability_catalog import (
                command_definitions,
                domain_capability_definitions,
            )

            scopes_by_capability = {
                name: definition.writes
                for name, definition in {
                    **command_definitions(resolved_authority_root, include_internal=True),
                    **domain_capability_definitions(resolved_authority_root),
                }.items()
            }

            def catalog_scopes_for(name: str) -> tuple[str, ...]:
                scopes = scopes_by_capability.get(name)
                if scopes is None:
                    raise ReplayEvidenceError(
                        f"idempotent receipt names an unknown write authority: {name}"
                    )
                return scopes

            granted_capabilities: list[str] = []
            for grant in grants:
                if not isinstance(grant, dict):
                    raise ReplayEvidenceError("idempotent receipt authority grant is malformed")
                granted_capability = grant.get("capability")
                declared = grant.get("declared_writes")
                if not isinstance(granted_capability, str) or not isinstance(declared, list):
                    raise ReplayEvidenceError("idempotent receipt authority grant is malformed")
                if tuple(declared) != tuple(catalog_scopes_for(granted_capability)):
                    raise ReplayEvidenceError(
                        "idempotent receipt authority grant does not match the declared "
                        f"capability scope: {granted_capability}"
                    )
                granted_capabilities.append(granted_capability)

            if request.capability == "ai-action.delivery.apply":
                if "ai-action.delivery.apply" not in granted_capabilities:
                    raise ReplayEvidenceError(
                        "idempotent receipt for ai-action.delivery.apply carries no grant "
                        "for its own top-level capability"
                    )
                delegated = sorted(
                    {c for c in granted_capabilities if c != "ai-action.delivery.apply"}
                )
                if delegated:
                    proven = _proven_delivery_delegation(root, receipt)
                    unproven = [c for c in delegated if c not in proven]
                    if unproven:
                        raise ReplayEvidenceError(
                            "idempotent receipt claims AI-action delegated authority its "
                            f"bound delivery does not prove: {', '.join(unproven)}"
                        )
            elif granted_capabilities != [request.capability]:
                raise ReplayEvidenceError(
                    "idempotent receipt authority grants must carry exactly the top-level "
                    "request capability"
                )

            for granted_capability in granted_capabilities:
                allowed_scopes.extend(catalog_scopes_for(granted_capability))

        for entry in writes:
            if not isinstance(entry, dict):
                raise ReplayEvidenceError("idempotent receipt write row is malformed")
            relative = entry.get("path")
            if not isinstance(relative, str) or not relative:
                raise ReplayEvidenceError("idempotent receipt write row names no path")
            try:
                _write_path, normalized_write = write_target(root, root / relative)
            except WriteScopeError as exc:
                raise ReplayEvidenceError(
                    f"idempotent receipt write path is unsafe: {exc}"
                ) from exc
            if normalized_write != relative:
                raise ReplayEvidenceError(
                    f"idempotent receipt write path is not canonical: {relative}"
                )
            if resolved_authority_root is not None and not any(
                scope_matches(relative, pattern) for pattern in allowed_scopes
            ):
                raise ReplayEvidenceError(
                    "idempotent receipt write path is outside its capability's "
                    f"declared scope: {relative}"
                )

        return receipt, row, receipt_path

    finally:
        if close_after:
            conn.close()


def replay_for_request_sql(
    root: Path,
    request: GatewayRequestContext,
    *,
    authority_root: Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> TransactionResult | None:
    """Return the original committed receipt for an exact approved retry via SQL."""
    verified = verify_committed_evidence_sql(
        root, request, authority_root=authority_root, conn=conn
    )
    if verified is None:
        return None
    receipt, row, receipt_path = verified
    return TransactionResult(
        transaction_id=str(row["transaction_id"]),
        receipt_path=receipt_path,
        revisions={str(key): int(value) for key, value in row["revisions"].items()},
        snapshot_before=str(row["snapshot_before"]),
        snapshot_after=str(row["snapshot_after"]),
        replayed=True,
        receipt=receipt,
    )


def shared_ledgers_proven_since_sql(
    root: Path,
    *,
    revisions_sha256: str | None = None,
    idempotency_sha256: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> bool:
    """Prove live revisions/idempotency advanced from hashes via SQL reverse walk."""
    if revisions_sha256 is None and idempotency_sha256 is None:
        return False

    close_after = False
    if conn is None:
        conn = sqlite3.connect(":memory:")
        build_receipt_store(root, conn)
        close_after = True

    try:
        rev_path = revision_ledger_path(root)
        idem_path = idempotency_ledger_path(root)
        revisions = load_revisions_sql(root, conn)
        entries = load_idempotency_entries_sql(root, conn)

        if rev_path.is_file() and rev_path.read_bytes() != dump_revisions(revisions).encode("utf-8"):
            return False
        if idem_path.is_file() and idem_path.read_bytes() != dump_idempotency_entries(entries).encode("utf-8"):
            return False

        def _matches(cur_revisions: dict[str, int], cur_entries: dict[str, dict]) -> bool:
            if revisions_sha256 is not None:
                rev_digest = hashlib.sha256(dump_revisions(cur_revisions).encode("utf-8")).hexdigest()
                if rev_digest != revisions_sha256:
                    return False
            if idempotency_sha256 is not None:
                idem_digest = hashlib.sha256(
                    dump_idempotency_entries(cur_entries).encode("utf-8")
                ).hexdigest()
                if idem_digest != idempotency_sha256:
                    return False
            return True

        if _matches(revisions, entries):
            return True

        cur = conn.cursor()
        cur.execute(
            """SELECT id, schema_version, status, idempotency_key, raw_yaml
               FROM receipts
               ORDER BY id DESC"""
        )
        for tx_id, s_ver, status, idem_key, raw_yaml in cur.fetchall():
            if status != "committed":
                return False
            receipt = yaml.load(raw_yaml, Loader=UniqueKeySafeLoader)
            if not isinstance(receipt, dict):
                return False
            artifact_revisions = receipt.get("artifact_revisions")
            if not isinstance(artifact_revisions, dict) or not artifact_revisions:
                return False

            if s_ver == 2:
                if not idem_key:
                    return False
                row = entries.get(idem_key)
                if row is None or row.get("transaction_id") != tx_id:
                    return False

            for artifact, bounds in artifact_revisions.items():
                if not isinstance(bounds, dict) or revisions.get(artifact, 0) != bounds.get("after"):
                    return False

            for artifact, bounds in artifact_revisions.items():
                before = bounds.get("before", 0)
                if before == 0:
                    revisions.pop(artifact, None)
                else:
                    revisions[artifact] = int(before)

            if idem_key is not None:
                entries.pop(idem_key, None)

            if _matches(revisions, entries):
                return True

        return False
    finally:
        if close_after:
            conn.close()
