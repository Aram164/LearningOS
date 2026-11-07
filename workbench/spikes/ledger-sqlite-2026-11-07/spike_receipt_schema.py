"""Relational schema for Ledger and Revision Reconciliation (Role A / Role B Spike).

Declares tables for live artifact revisions, idempotency entries, and
transaction receipts (including child revisions, writes, and grants).

Collation is strictly BINARY for exact string/hash comparison.
"""

from __future__ import annotations

import sqlite3

RECEIPT_SCHEMA_DDL = """
-- Live artifact revisions (revisions.yaml)
CREATE TABLE live_revisions (
    artifact TEXT PRIMARY KEY COLLATE BINARY,
    revision INTEGER NOT NULL CHECK (revision >= 0)
);

-- Idempotency ledger entries (idempotency.yaml)
CREATE TABLE idempotency_entries (
    idempotency_key TEXT PRIMARY KEY COLLATE BINARY,
    request_id      TEXT NOT NULL COLLATE BINARY,
    capability      TEXT NOT NULL COLLATE BINARY,
    channel         TEXT NOT NULL COLLATE BINARY,
    intent_sha256   TEXT NOT NULL COLLATE BINARY,
    transaction_id  TEXT NOT NULL COLLATE BINARY,
    receipt_path    TEXT NOT NULL COLLATE BINARY,
    snapshot_before TEXT NOT NULL COLLATE BINARY,
    snapshot_after  TEXT NOT NULL COLLATE BINARY
);
CREATE INDEX idx_idempotency_tx_id ON idempotency_entries (transaction_id);

-- Child revisions declared per idempotency entry
CREATE TABLE idempotency_revisions (
    idempotency_key TEXT NOT NULL COLLATE BINARY,
    artifact        TEXT NOT NULL COLLATE BINARY,
    revision        INTEGER NOT NULL CHECK (revision >= 0),
    PRIMARY KEY (idempotency_key, artifact)
);
CREATE INDEX idx_idempotency_revs_artifact ON idempotency_revisions (artifact);

-- Historical and live transaction receipts (transaction-*.yaml)
CREATE TABLE receipts (
    id                      TEXT PRIMARY KEY COLLATE BINARY,
    schema_version          INTEGER NOT NULL,
    type                    TEXT NOT NULL COLLATE BINARY,
    status                  TEXT NOT NULL COLLATE BINARY,
    capability              TEXT NOT NULL COLLATE BINARY,
    committed_at            TEXT COLLATE BINARY,
    snapshot_before         TEXT COLLATE BINARY,
    snapshot_after          TEXT COLLATE BINARY,
    request_id              TEXT COLLATE BINARY,
    idempotency_key         TEXT COLLATE BINARY,
    channel                 TEXT COLLATE BINARY,
    intent_sha256           TEXT COLLATE BINARY,
    approval_kind           TEXT COLLATE BINARY,
    approval_subject_sha256 TEXT COLLATE BINARY,
    receipt_path            TEXT NOT NULL COLLATE BINARY,
    raw_yaml                TEXT NOT NULL
);
CREATE INDEX idx_receipts_idempotency ON receipts (idempotency_key);
CREATE INDEX idx_receipts_capability ON receipts (capability);

-- Child artifact revisions recorded per transaction receipt
CREATE TABLE receipt_revisions (
    transaction_id TEXT NOT NULL COLLATE BINARY,
    artifact       TEXT NOT NULL COLLATE BINARY,
    rev_before     INTEGER NOT NULL,
    rev_after      INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, artifact)
);
CREATE INDEX idx_receipt_revs_artifact ON receipt_revisions (artifact);

-- Child write entries recorded per transaction receipt
CREATE TABLE receipt_writes (
    transaction_id TEXT NOT NULL COLLATE BINARY,
    path           TEXT NOT NULL COLLATE BINARY,
    sha256_before  TEXT COLLATE BINARY,
    sha256_after   TEXT COLLATE BINARY,
    created        INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, path)
);

-- Capability authority grants recorded per transaction receipt
CREATE TABLE receipt_grants (
    transaction_id TEXT NOT NULL COLLATE BINARY,
    capability     TEXT NOT NULL COLLATE BINARY,
    PRIMARY KEY (transaction_id, capability)
);

-- Declared write scope patterns per authority grant
CREATE TABLE receipt_grant_scopes (
    transaction_id TEXT NOT NULL COLLATE BINARY,
    capability     TEXT NOT NULL COLLATE BINARY,
    scope_pattern  TEXT NOT NULL COLLATE BINARY,
    PRIMARY KEY (transaction_id, capability, scope_pattern)
);
"""


def init_receipt_db(conn: sqlite3.Connection) -> None:
    """Initialize transaction and revision tables on an SQLite connection."""
    conn.executescript(RECEIPT_SCHEMA_DDL)
