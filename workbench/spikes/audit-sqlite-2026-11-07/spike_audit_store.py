"""Historical Transaction Audit Stream Store (Task C.3).

Operationalizes the relational receipt schema into a persistent SQLite index
(.derived/transactions.sqlite3). Provides high-performance incremental sync
that reads only transaction files added since the latest indexed transaction.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml

AUDIT_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS receipts (
    id TEXT PRIMARY KEY COLLATE BINARY,
    schema_version INTEGER,
    type TEXT COLLATE BINARY,
    status TEXT COLLATE BINARY,
    capability TEXT COLLATE BINARY,
    committed_at TEXT COLLATE BINARY,
    snapshot_before TEXT COLLATE BINARY,
    snapshot_after TEXT COLLATE BINARY,
    request_id TEXT COLLATE BINARY,
    idempotency_key TEXT COLLATE BINARY,
    receipt_path TEXT NOT NULL COLLATE BINARY,
    raw_yaml TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_receipts_committed_at ON receipts (committed_at);
CREATE INDEX IF NOT EXISTS idx_receipts_capability ON receipts (capability);
CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts (status);

CREATE TABLE IF NOT EXISTS receipt_revisions (
    transaction_id TEXT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    artifact TEXT NOT NULL COLLATE BINARY,
    rev_before INTEGER NOT NULL,
    rev_after INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, artifact)
);
CREATE INDEX IF NOT EXISTS idx_receipt_revisions_artifact ON receipt_revisions (artifact);

CREATE TABLE IF NOT EXISTS receipt_writes (
    transaction_id TEXT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    path TEXT NOT NULL COLLATE BINARY,
    sha256_before TEXT COLLATE BINARY,
    sha256_after TEXT COLLATE BINARY,
    created INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, path)
);
CREATE INDEX IF NOT EXISTS idx_receipt_writes_path ON receipt_writes (path);

CREATE TABLE IF NOT EXISTS sync_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_audit_db(db_path: str = ":memory:") -> sqlite3.Connection:
    """Initialize an SQLite connection with the transaction audit schema."""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.executescript(AUDIT_SCHEMA_DDL)
    return con


def sync_receipt_entry(cur: sqlite3.Cursor, receipt_path: Path, data: dict, raw_text: str) -> None:
    """Insert or replace a single transaction receipt and its child tables."""
    tx_id = data.get("id")
    if not tx_id:
        return

    cur.execute(
        """
        INSERT OR REPLACE INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx_id,
            data.get("schema_version", 1),
            data.get("type", "transaction-receipt"),
            data.get("status", "committed"),
            data.get("capability", ""),
            data.get("committed_at", ""),
            data.get("snapshot_before", ""),
            data.get("snapshot_after", ""),
            data.get("request_id", ""),
            data.get("idempotency_key", ""),
            str(receipt_path),
            raw_text,
        ),
    )

    # Ingest artifact revisions
    revisions = data.get("artifact_revisions") or {}
    for art, rev_info in revisions.items():
        if isinstance(rev_info, dict):
            b = rev_info.get("before", 0)
            a = rev_info.get("after", 0)
        else:
            b, a = 0, int(rev_info)
        cur.execute(
            """
            INSERT OR REPLACE INTO receipt_revisions VALUES (?, ?, ?, ?)
            """,
            (tx_id, art, b, a),
        )

    # Ingest writes
    writes = data.get("writes") or []
    for w in writes:
        w_path = w.get("path")
        if w_path:
            cur.execute(
                """
                INSERT OR REPLACE INTO receipt_writes VALUES (?, ?, ?, ?, ?)
                """,
                (
                    tx_id,
                    w_path,
                    w.get("sha256_before"),
                    w.get("sha256_after"),
                    1 if w.get("created") else 0,
                ),
            )


def sync_all_transactions(
    root: Path, con: sqlite3.Connection, incremental: bool = True
) -> tuple[int, int]:
    """Synchronize transaction receipts from disk into SQLite.

    Returns:
        (total_transactions_in_db, new_transactions_indexed)
    """
    tx_dir = root / "operations" / "transactions"
    if not tx_dir.is_dir():
        return 0, 0

    all_files = sorted(tx_dir.glob("transaction-*.yaml"))

    cur = con.cursor()
    cur.execute("PRAGMA defer_foreign_keys = ON;")

    indexed_ids = set()
    if incremental:
        cur.execute("SELECT id FROM receipts")
        indexed_ids = {r[0] for r in cur.fetchall()}

    new_count = 0
    for f in all_files:
        # Quick stem check: transaction IDs typically match the file stem
        stem_id = f.stem
        if incremental and stem_id in indexed_ids:
            continue

        raw = f.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        tx_id = data.get("id")
        if incremental and tx_id in indexed_ids:
            continue

        sync_receipt_entry(cur, f.relative_to(root), data, raw)
        indexed_ids.add(tx_id)
        new_count += 1

    con.commit()
    total_count = cur.execute("SELECT count(*) FROM receipts").fetchone()[0]
    return total_count, new_count
