"""SPIKE - SQLite-backed derived-state store behind the production store.py API surface.

Labelled spike (workbench/spikes/roleb-sqlite-2026-11-06), throwaway, never
imported by production code (installed only through the spike_swap pytest
plugin or direct import by the spike behavior script). Exists to replace the
+131 L ESTIMATE in Deliverable 2 section 4/7 with a measured count and to test
rebuild-or-refuse against simulated corruption.

Doctrine mapping (Deliverable 1 section 5, brief section 6.4):
- corrupt cache content is a miss  ->  hash verification retained on every
  lookup (reviewer caveat: policy SQLite does not absorb); unreadable or
  corrupt DB on a READ path is a miss, never an error;
- write paths rebuild-or-refuse: a corrupt DB file is deleted and recreated
  once; a second failure raises TransactionFailure - never partial success;
- versioned schema + root identity verified on open: schema_version and a
  root fingerprint live in a meta table; mismatch rebuilds (all misses) -
  sound because every node key is content-addressed;
- publication is one transaction (INSERT .. COMMIT), replacing the blobs-first
  / state-last choreography; stage_node_blob commits its blob before publish,
  matching the file store's staged-orphan window (safe by construction,
  collected by sweep);
- path-safety policy is RETAINED (generated/ and the DB file must not be
  symlinks; nothing escapes the root) - policy SQLite does not absorb;
- single-writer assumption unchanged (operator lock); no WAL (no measured
  concurrency need - brief section 7 stage 5 gate).

Not implemented here (stays production code in any Stage 5): engine.py reuse
decisions, staging decisions, identity.py digests, model.py node keys.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from learning_os.domain.failures import TransactionFailure
from learning_os.store.derived.model import DerivedError, NodeState
from learning_os.store.derived.store import canonical_bytes  # pure serializer, reused

DERIVED_TOP_DIR = "derived-state"
DB_FILENAME = "state-v1.db"
STATE_SCHEMA_VERSION = 1
BLOBS_DIRNAME = "blobs"  # NodeState.blob strings stay "blobs/<sha>" for API parity

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes (
    node_id       TEXT PRIMARY KEY,
    node_key      TEXT NOT NULL,
    output_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS blobs (
    sha256 TEXT PRIMARY KEY,
    bytes  BLOB NOT NULL
);
"""


def derived_dir(root: Path) -> Path:
    return root / "generated" / DERIVED_TOP_DIR


def db_path(root: Path) -> Path:
    return derived_dir(root) / DB_FILENAME


def state_path(root: Path) -> Path:
    """Legacy JSON index path - never created by this store (API parity only)."""
    return derived_dir(root) / "state-v1.json"


def _root_fingerprint(root: Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()


def _checked_store_dir(root: Path) -> Path:
    """Path-safety policy, retained (not absorbed by SQLite). Slimmer than the
    file store's per-part walk: one DB file replaces the whole tree."""
    gen = root / "generated"
    if gen.is_symlink():
        raise TransactionFailure("generated output root may not be a symbolic link")
    db = db_path(root)
    if db.is_symlink():
        raise TransactionFailure("derived-state database is a symbolic link")
    db.parent.mkdir(parents=True, exist_ok=True)
    if not db.parent.resolve().is_relative_to(gen.resolve()):
        raise TransactionFailure("derived-state path escapes generated/")
    return db


def _open_for_read(root: Path) -> sqlite3.Connection | None:
    """Read open: never creates; path safety matches the write open (a
    symlinked generated/ root or a database outside generated/ refuses as a
    miss, never traverses into another root's store); corrupt DB is a miss
    (None), never an error."""
    gen = root / "generated"
    if gen.is_symlink():
        return None  # refuse as a miss: never traverse a linked generated/
    db = db_path(root)
    if not db.exists() or db.is_symlink():
        return None
    if not db.parent.resolve().is_relative_to(gen.resolve()):
        return None  # containment: the store lives inside generated/ or not at all
    try:
        return sqlite3.connect(db, timeout=5.0)
    except sqlite3.DatabaseError:
        return None  # corrupt cache is a miss (read doctrine)


def _rebuild_database(root: Path, db: Path) -> None:
    """Rebuild per brief 6.4: build the replacement database in a temp file
    in the same directory, bind identity, verify, then os.replace() onto the
    live path. No in-place clears; no unlink-before-recreate.

    Failure points: any error during build or verification leaves the old
    database untouched and raises TransactionFailure; a crash before the
    rename leaves the old database plus an orphaned `.rebuild` temp (removed
    by the next rebuild attempt). The old store is retired only at the
    rename, which is atomic."""
    tmp = db.with_name(db.name + ".rebuild")
    if tmp.exists():
        tmp.unlink()  # our own naming convention; single-writer assumption
    conn = None
    try:
        conn = sqlite3.connect(tmp, timeout=5.0)
        conn.executescript(_SCHEMA)
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
                     (str(STATE_SCHEMA_VERSION),))
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('root_fingerprint', ?)",
                     (_root_fingerprint(root),))
        conn.commit()
        if not _identity_ok(conn, root):
            raise sqlite3.DatabaseError("rebuilt database failed identity verification")
        conn.close()
        conn = None
        os.replace(tmp, db)
    except (sqlite3.DatabaseError, OSError) as exc:
        if conn is not None:
            conn.close()
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise TransactionFailure(
            "derived-state database rebuild failed; old store untouched: %s" % exc) from exc


def _open_for_write(root: Path) -> sqlite3.Connection:
    """Write open: versioned schema + root identity verified; missing,
    mismatched or corrupt -> atomic rebuild (build-to-temp, verify, rename);
    rebuild failure -> refuse."""
    db = _checked_store_dir(root)
    conn = None
    try:
        conn = sqlite3.connect(db, timeout=5.0)
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        ok = (meta.get("schema_version") == str(STATE_SCHEMA_VERSION)
              and meta.get("root_fingerprint") == _root_fingerprint(root))
        if not ok:
            conn.close()
            conn = None
            _rebuild_database(root, db)
            return sqlite3.connect(db, timeout=5.0)
        return conn
    except sqlite3.DatabaseError:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        try:
            _rebuild_database(root, db)
            return sqlite3.connect(db, timeout=5.0)
        except (sqlite3.DatabaseError, OSError) as exc:
            raise TransactionFailure(
                "derived-state database is corrupt and could not be rebuilt: %s" % exc) from exc


def _identity_ok(conn: sqlite3.Connection, root: Path) -> bool:
    """Open-time identity contract on the read path too: a DB whose schema
    version or root fingerprint does not match serves nothing (miss)."""
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    except sqlite3.DatabaseError:
        return False
    return (meta.get("schema_version") == str(STATE_SCHEMA_VERSION)
            and meta.get("root_fingerprint") == _root_fingerprint(root))


def read_state(root: Path) -> dict[str, NodeState]:
    conn = _open_for_read(root)
    if conn is None:
        return {}
    if not _identity_ok(conn, root):
        conn.close()
        return {}
    try:
        rows = conn.execute(
            "SELECT node_id, node_key, output_sha256 FROM nodes").fetchall()
    except sqlite3.DatabaseError:
        return {}  # corrupt cache is a miss, never an error
    finally:
        conn.close()
    return {nid: NodeState(node_key=key, output_sha256=digest,
                           blob=f"{BLOBS_DIRNAME}/{digest}")
            for nid, key, digest in rows}


def invalidate(root: Path, node_id: str) -> None:
    """Drop one node's entry; its blob row is left as a harmless orphan.
    A missing DB is a no-op that creates nothing (parity with the file store)."""
    if not db_path(root).exists():
        return
    with closing(_open_for_write(root)) as conn:
        conn.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
        conn.commit()


def lookup(root: Path, node_id: str, *,
           states: dict[str, NodeState] | None = None) -> tuple[NodeState, Any] | None:
    """Verified reuse: node row plus a hash-verified blob row. Anything else is
    a miss (None). Hash verification is retained - policy SQLite does not absorb."""
    if states is None:
        states = read_state(root)
    state = states.get(node_id)
    if state is None:
        return None
    conn = _open_for_read(root)
    if conn is None:
        return None
    if not _identity_ok(conn, root):
        conn.close()
        return None
    try:
        row = conn.execute("SELECT bytes FROM blobs WHERE sha256 = ?",
                           (state.output_sha256,)).fetchone()
    except sqlite3.DatabaseError:
        return None
    finally:
        conn.close()
    if row is None:
        return None
    data = row[0]
    if hashlib.sha256(data).hexdigest() != state.output_sha256:
        return None
    try:
        return state, json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError):
        return None


def stage_node_blob(root: Path, node_id: str, *, node_key: str, value: Any) -> NodeState:
    """Write one node's blob without publishing its state entry (staged orphan
    until publish - same crash window as the file store, safe by construction)."""
    if not node_id:
        raise DerivedError("derived node id must be nonempty")
    data = canonical_bytes(value)
    digest = hashlib.sha256(data).hexdigest()
    with closing(_open_for_write(root)) as conn:
        conn.execute("INSERT OR REPLACE INTO blobs(sha256, bytes) VALUES (?, ?)",
                     (digest, data))
        conn.commit()
    return NodeState(node_key=node_key, output_sha256=digest,
                     blob=f"{BLOBS_DIRNAME}/{digest}")


def publish_staged_states(root: Path, staged: dict[str, NodeState]) -> None:
    """Publish staged entries in ONE transaction. Staged entries overwrite only
    their own node ids; everything else survives (the RMW merge becomes a PK
    upsert). Empty publishes nothing and creates nothing."""
    if not staged:
        return
    with closing(_open_for_write(root)) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO nodes(node_id, node_key, output_sha256) VALUES (?, ?, ?)",
            [(nid, s.node_key, s.output_sha256) for nid, s in staged.items()])
        conn.commit()


def store_node(root: Path, node_id: str, *, node_key: str, value: Any) -> NodeState:
    state = stage_node_blob(root, node_id, node_key=node_key, value=value)
    publish_staged_states(root, {node_id: state})
    return state


def sweep_unreferenced_blobs(root: Path, *, dry_run: bool = False) -> dict[str, int]:
    """Delete blob rows no node row references; return the same count shape.

    The deleting branch runs only through the guarded write open (path
    safety, identity verified, rebuild-or-refuse on mismatch) with an
    explicit identity re-check before the DELETE; a dry run may keep the
    read open. A corrupt database is a miss-shaped zero result on a dry run
    and a refusal on a real sweep. Orphanage is impossible between stage and
    publish within one transaction, but staged-never-published blobs are
    still collected."""
    zeros = {"referenced": 0, "kept": 0, "deleted": 0, "skipped": 0}
    if dry_run:
        conn = _open_for_read(root)
        if conn is None:
            return dict(zeros)
        try:
            if not _identity_ok(conn, root):
                return dict(zeros)
            referenced = {r[0] for r in conn.execute("SELECT output_sha256 FROM nodes")}
            kept = conn.execute(
                "SELECT COUNT(*) FROM blobs WHERE sha256 IN "
                "(SELECT output_sha256 FROM nodes)").fetchone()[0]
            deleted = conn.execute(
                "SELECT COUNT(*) FROM blobs WHERE sha256 NOT IN "
                "(SELECT output_sha256 FROM nodes)").fetchone()[0]
            return {"referenced": len(referenced), "kept": kept,
                    "deleted": deleted, "skipped": 0}
        except sqlite3.DatabaseError:
            return dict(zeros)  # corrupt cache is a miss-shaped zero result
        finally:
            conn.close()
    if not db_path(root).exists():
        return dict(zeros)  # parity: a sweep never creates the store
    try:
        with closing(_open_for_write(root)) as conn:
            if not _identity_ok(conn, root):
                raise TransactionFailure("derived-state identity mismatch after write open")
            referenced = {r[0] for r in conn.execute("SELECT output_sha256 FROM nodes")}
            kept = conn.execute(
                "SELECT COUNT(*) FROM blobs WHERE sha256 IN "
                "(SELECT output_sha256 FROM nodes)").fetchone()[0]
            cur = conn.execute("DELETE FROM blobs WHERE sha256 NOT IN "
                               "(SELECT output_sha256 FROM nodes)")
            conn.commit()
            return {"referenced": len(referenced), "kept": kept,
                    "deleted": cur.rowcount, "skipped": 0}
    except sqlite3.DatabaseError as exc:
        raise TransactionFailure(
            "derived-state sweep failed against the store: %s" % exc) from exc
