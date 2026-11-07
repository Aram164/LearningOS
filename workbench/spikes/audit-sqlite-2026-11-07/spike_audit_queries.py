"""High-Frequency Audit Queries evaluated across Python YAML scan vs SQLite (Task C.3).

Implements 4 core historical transaction audit operations:
1. Capability Frequency: aggregate transaction counts grouped by capability in a date range.
2. Artifact History: full revision transition provenance for an artifact.
3. Transaction Window: chronological listing of receipts in a time interval.
4. Monotone Floor Anti-Join: detects stale live revisions strictly lower than committed receipts.
"""

from __future__ import annotations

import sqlite3
from typing import Any


# ---------------------------------------------------------------------------
# 1. Capability Frequency
# ---------------------------------------------------------------------------

def py_capability_frequency(
    receipts: list[dict[str, Any]], start_date: str, end_date: str
) -> list[tuple[str, int]]:
    """Python filesystem walk: count transactions by capability within date range."""
    counts: dict[str, int] = {}
    for r in receipts:
        c_at = r.get("committed_at", "")
        if start_date <= c_at <= end_date:
            cap = r.get("capability", "unknown")
            counts[cap] = counts.get(cap, 0) + 1
    # Sort by count desc, capability asc
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))


def sql_capability_frequency(
    con: sqlite3.Connection, start_date: str, end_date: str
) -> list[tuple[str, int]]:
    """SQLite index: count transactions by capability within date range."""
    cur = con.execute(
        """
        SELECT capability, count(*) AS cnt
        FROM receipts
        WHERE committed_at >= ? AND committed_at <= ?
        GROUP BY capability
        ORDER BY cnt DESC, capability ASC
        """,
        (start_date, end_date),
    )
    return [(r[0], r[1]) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# 2. Artifact History
# ---------------------------------------------------------------------------

def py_artifact_history(
    receipts: list[dict[str, Any]], artifact: str
) -> list[dict[str, Any]]:
    """Python filesystem walk: full revision lineage for an artifact."""
    history = []
    for r in receipts:
        revs = r.get("artifact_revisions") or {}
        if artifact in revs:
            info = revs[artifact]
            b = info.get("before", 0) if isinstance(info, dict) else 0
            a = info.get("after", 0) if isinstance(info, dict) else int(info)
            history.append({
                "transaction_id": r.get("id"),
                "committed_at": r.get("committed_at"),
                "rev_before": b,
                "rev_after": a,
                "capability": r.get("capability"),
            })
    history.sort(key=lambda h: h["committed_at"])
    return history


def sql_artifact_history(
    con: sqlite3.Connection, artifact: str
) -> list[dict[str, Any]]:
    """SQLite index: full revision lineage for an artifact."""
    cur = con.execute(
        """
        SELECT r.id, r.committed_at, rr.rev_before, rr.rev_after, r.capability
        FROM receipt_revisions rr
        JOIN receipts r ON r.id = rr.transaction_id
        WHERE rr.artifact = ?
        ORDER BY r.committed_at ASC
        """,
        (artifact,),
    )
    return [
        {
            "transaction_id": r[0],
            "committed_at": r[1],
            "rev_before": r[2],
            "rev_after": r[3],
            "capability": r[4],
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# 3. Transaction Window
# ---------------------------------------------------------------------------

def py_transaction_window(
    receipts: list[dict[str, Any]], start_time: str, end_time: str, status: str
) -> list[dict[str, Any]]:
    """Python filesystem walk: query receipts within window with matching status."""
    matched = []
    for r in receipts:
        c_at = r.get("committed_at", "")
        if start_time <= c_at <= end_time and r.get("status") == status:
            matched.append({
                "id": r.get("id"),
                "committed_at": c_at,
                "capability": r.get("capability"),
                "status": r.get("status"),
                "snapshot_before": r.get("snapshot_before"),
                "snapshot_after": r.get("snapshot_after"),
            })
    matched.sort(key=lambda m: m["committed_at"])
    return matched


def sql_transaction_window(
    con: sqlite3.Connection, start_time: str, end_time: str, status: str
) -> list[dict[str, Any]]:
    """SQLite index: query receipts within window with matching status."""
    cur = con.execute(
        """
        SELECT id, committed_at, capability, status, snapshot_before, snapshot_after
        FROM receipts
        WHERE committed_at >= ? AND committed_at <= ? AND status = ?
        ORDER BY committed_at ASC
        """,
        (start_time, end_time, status),
    )
    return [
        {
            "id": r[0],
            "committed_at": r[1],
            "capability": r[2],
            "status": r[3],
            "snapshot_before": r[4],
            "snapshot_after": r[5],
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# 4. Monotone Floor Anti-Join
# ---------------------------------------------------------------------------

def py_monotone_floor_anti_join(
    receipts: list[dict[str, Any]], live_revisions: dict[str, int]
) -> list[dict[str, Any]]:
    """Python calculation: find live revisions strictly below committed receipts."""
    max_revs: dict[str, int] = {}
    for r in receipts:
        for art, rev_info in (r.get("artifact_revisions") or {}).items():
            a = rev_info.get("after", 0) if isinstance(rev_info, dict) else int(rev_info)
            if a > max_revs.get(art, -1):
                max_revs[art] = a

    stale = []
    for art, max_a in max_revs.items():
        live = live_revisions.get(art, 0)
        if live < max_a:
            stale.append({"artifact": art, "max_committed_rev": max_a, "live_rev": live})
    stale.sort(key=lambda s: s["artifact"])
    return stale


def sql_monotone_floor_anti_join(
    con: sqlite3.Connection, live_revisions: dict[str, int]
) -> list[dict[str, Any]]:
    """SQLite relational anti-join: find live revisions strictly below committed receipts."""
    cur = con.cursor()
    cur.execute("CREATE TEMP TABLE IF NOT EXISTS live_revs_temp (artifact TEXT PRIMARY KEY, rev INTEGER);")
    cur.execute("DELETE FROM live_revs_temp;")
    cur.executemany("INSERT INTO live_revs_temp VALUES (?, ?);", live_revisions.items())

    cur.execute(
        """
        WITH max_revs AS (
            SELECT artifact, MAX(rev_after) AS max_committed_rev
            FROM receipt_revisions
            GROUP BY artifact
        )
        SELECT m.artifact, m.max_committed_rev, COALESCE(l.rev, 0) AS live_rev
        FROM max_revs m
        LEFT JOIN live_revs_temp l ON l.artifact = m.artifact
        WHERE COALESCE(l.rev, 0) < m.max_committed_rev
        ORDER BY m.artifact
        """
    )
    return [
        {
            "artifact": r[0],
            "max_committed_rev": r[1],
            "live_rev": r[2],
        }
        for r in cur.fetchall()
    ]
