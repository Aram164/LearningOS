"""Receipt and Ledger Ingest pipeline for SQLite (Task B.2).

Ingests all 380 transaction receipts in operations/transactions/
along with revisions.yaml and idempotency.yaml into an SQLite store.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml

from learning_os.domain.failures import TransactionFailure
from learning_os.store.layout import PathBoundaryError, read_text_inside
from learning_os.store.loading.yamlio import UniqueKeySafeLoader


def _rel_path(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _load_revisions_file(root: Path) -> dict[str, int]:
    path = root / "operations" / "transactions" / "revisions.yaml"
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        data = yaml.load(read_text_inside(root, path), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise TransactionFailure(f"artifact revision ledger is unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("type") != "artifact-revision-ledger":
        raise TransactionFailure("artifact revision ledger has an unsupported contract")
    rows = data.get("revisions")
    if not isinstance(rows, dict):
        raise TransactionFailure("artifact revision ledger revisions must be a mapping")
    revisions: dict[str, int] = {}
    for artifact, value in rows.items():
        if not isinstance(artifact, str) or not artifact.strip() or isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TransactionFailure(f"artifact revision ledger contains an invalid row: {artifact!r}")
        revisions[artifact] = value
    return revisions


def _load_idempotency_file(root: Path) -> dict[str, dict]:
    path = root / "operations" / "transactions" / "idempotency.yaml"
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        data = yaml.load(read_text_inside(root, path), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise TransactionFailure(f"idempotency ledger is unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("type") != "transaction-idempotency-ledger":
        raise TransactionFailure("idempotency ledger has an unsupported contract")
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise TransactionFailure("idempotency ledger entries must be a mapping")
    normalized: dict[str, dict] = {}
    for key, row in entries.items():
        if not isinstance(key, str) or not key or not isinstance(row, dict):
            raise TransactionFailure("idempotency ledger contains an invalid entry")
        normalized[key] = dict(row)
    return normalized


def ingest_revisions(root: Path, conn: sqlite3.Connection) -> int:
    """Ingest revisions.yaml into live_revisions table."""
    revs = _load_revisions_file(root)
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO live_revisions (artifact, revision) VALUES (?, ?)",
        [(str(k), int(v)) for k, v in revs.items()],
    )
    conn.commit()
    return len(revs)


def ingest_idempotency(root: Path, conn: sqlite3.Connection) -> int:
    """Ingest idempotency.yaml into idempotency_entries and idempotency_revisions."""
    entries = _load_idempotency_file(root)
    cur = conn.cursor()
    entry_rows = []
    rev_rows = []
    for key, row in entries.items():
        entry_rows.append((
            str(key),
            str(row["request_id"]),
            str(row["capability"]),
            str(row["channel"]),
            str(row["intent_sha256"]),
            str(row["transaction_id"]),
            str(row["receipt_path"]),
            str(row["snapshot_before"]),
            str(row["snapshot_after"]),
        ))
        for art, rev in (row.get("revisions") or {}).items():
            rev_rows.append((str(key), str(art), int(rev)))

    cur.executemany(
        """INSERT OR REPLACE INTO idempotency_entries (
            idempotency_key, request_id, capability, channel,
            intent_sha256, transaction_id, receipt_path,
            snapshot_before, snapshot_after
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        entry_rows,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO idempotency_revisions (idempotency_key, artifact, revision) VALUES (?, ?, ?)",
        rev_rows,
    )
    conn.commit()
    return len(entries)


def ingest_receipts(root: Path, conn: sqlite3.Connection) -> int:
    """Ingest all operations/transactions/transaction-*.yaml into relational tables."""
    tx_dir = root / "operations" / "transactions"
    if not tx_dir.is_dir():
        return 0

    receipt_rows = []
    rev_rows = []
    write_rows = []
    grant_rows = []
    scope_rows = []

    receipt_paths = sorted(tx_dir.glob("transaction-*.yaml"))
    for path in receipt_paths:
        if path.is_symlink():
            continue
        try:
            raw_text = read_text_inside(root, path)
            receipt: dict[str, Any] = yaml.load(raw_text, Loader=UniqueKeySafeLoader)
        except Exception:
            continue
        if not isinstance(receipt, dict):
            continue

        tx_id = str(receipt.get("id", path.stem))
        schema_version = int(receipt.get("schema_version", 1))
        tx_type = str(receipt.get("type", "transaction-receipt"))
        status = str(receipt.get("status", ""))
        capability = str(receipt.get("capability", ""))
        committed_at = str(receipt.get("committed_at", ""))
        snapshot_before = str(receipt.get("snapshot_before", "")) if receipt.get("snapshot_before") else None
        snapshot_after = str(receipt.get("snapshot_after", "")) if receipt.get("snapshot_after") else None

        req = receipt.get("request") if isinstance(receipt.get("request"), dict) else {}
        req_id = str(req.get("request_id")) if req.get("request_id") else None
        idem_key = str(req.get("idempotency_key")) if req.get("idempotency_key") else None
        channel = str(req.get("channel")) if req.get("channel") else None
        intent_sha256 = str(req.get("intent_sha256")) if req.get("intent_sha256") else None

        approval = req.get("approval") if isinstance(req.get("approval"), dict) else {}
        approval_kind = str(approval.get("kind")) if approval.get("kind") else None
        approval_subject = str(approval.get("subject_sha256")) if approval.get("subject_sha256") else None

        receipt_rows.append((
            tx_id, schema_version, tx_type, status, capability,
            committed_at, snapshot_before, snapshot_after,
            req_id, idem_key, channel, intent_sha256,
            approval_kind, approval_subject, _rel_path(path, root),
            raw_text,
        ))

        for art, bounds in (receipt.get("artifact_revisions") or {}).items():
            if isinstance(bounds, dict):
                rev_rows.append((
                    tx_id, str(art),
                    int(bounds.get("before", 0)),
                    int(bounds.get("after", 0)),
                ))

        for w in receipt.get("writes") or []:
            if isinstance(w, dict) and w.get("path"):
                write_rows.append((
                    tx_id, str(w["path"]),
                    str(w.get("sha256_before")) if w.get("sha256_before") else None,
                    str(w.get("sha256_after")) if w.get("sha256_after") else None,
                    1 if w.get("created") else 0,
                ))

        authority = receipt.get("authority") if isinstance(receipt.get("authority"), dict) else {}
        for grant in authority.get("grants") or []:
            if isinstance(grant, dict) and grant.get("capability"):
                g_cap = str(grant["capability"])
                grant_rows.append((tx_id, g_cap))
                for sc in grant.get("declared_writes") or []:
                    scope_rows.append((tx_id, g_cap, str(sc)))

    cur = conn.cursor()
    cur.executemany(
        """INSERT OR REPLACE INTO receipts (
            id, schema_version, type, status, capability,
            committed_at, snapshot_before, snapshot_after,
            request_id, idempotency_key, channel, intent_sha256,
            approval_kind, approval_subject_sha256, receipt_path, raw_yaml
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        receipt_rows,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO receipt_revisions (transaction_id, artifact, rev_before, rev_after) VALUES (?, ?, ?, ?)",
        rev_rows,
    )
    cur.executemany(
        """INSERT OR REPLACE INTO receipt_writes (
            transaction_id, path, sha256_before, sha256_after, created
        ) VALUES (?, ?, ?, ?, ?)""",
        write_rows,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO receipt_grants (transaction_id, capability) VALUES (?, ?)",
        grant_rows,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO receipt_grant_scopes (transaction_id, capability, scope_pattern) VALUES (?, ?, ?)",
        scope_rows,
    )
    conn.commit()
    return len(receipt_rows)


def build_receipt_store(root: Path, conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """Initialize schema and ingest complete transaction/revision corpus."""
    from spike_receipt_schema import init_receipt_db

    if conn is None:
        conn = sqlite3.connect(":memory:")
    init_receipt_db(conn)
    ingest_revisions(root, conn)
    ingest_idempotency(root, conn)
    ingest_receipts(root, conn)
    return conn
