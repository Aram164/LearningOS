"""SPIKE behavior script - DB-equivalent corruption/rebuild/identity demonstrations.

Run:  PYTHONPATH="tools:workbench/spikes/roleb-sqlite-2026-11-06" \
        .venv/bin/python workbench/spikes/roleb-sqlite-2026-11-06/spike_behavior.py

Each scenario mirrors a format-pinning test from tests/test_derived_state.py /
tests/test_search_index.py in the DB medium, plus the open-time contract the
JSON store cannot express (schema version, root identity, rebuild-or-refuse).
Output is the evidence: every scenario prints its observed result.
"""

import hashlib
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing, contextmanager
import sys
from pathlib import Path

sys.path.insert(0, "tools")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import spike_store_sqlite as spike  # noqa: E402

_results: list[tuple[bool, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    _results.append((ok, name, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def fresh_root() -> Path:
    return Path(tempfile.mkdtemp(prefix="los-spike-roleb-"))


@contextmanager
def with_db_rows(root: Path):
    conn = sqlite3.connect(spike.db_path(root))
    try:
        yield conn
    finally:
        conn.close()


print("== Round-trips and layout ==")
root = fresh_root()
state = spike.store_node(root, "n", node_key="k1", value={"b": 1, "a": [1, 2]})
check("store_node returns NodeState with blob string parity",
      state.blob == f"blobs/{state.output_sha256}")
found = spike.lookup(root, "n")
check("lookup returns (state, value)", found is not None and found[1] == {"a": [1, 2], "b": 1})
check("lookup of unknown node is a miss", spike.lookup(root, "other") is None)

empty = fresh_root()
check("lookup on empty root is a miss", spike.lookup(empty, "n") is None)
check("read_state on empty root is {}", spike.read_state(empty) == {})
check("read open creates nothing (derived_dir absent)", not spike.derived_dir(empty).exists())

spike.publish_staged_states(fresh_root(), {})
probe = fresh_root()
spike.publish_staged_states(probe, {})
check("empty publish creates nothing on a fresh root", not spike.db_path(probe).exists())
root3 = fresh_root()
spike.publish_staged_states(root3, {})
check("empty publish creates no DB", not spike.db_path(root3).exists())

root4 = fresh_root()
spike.invalidate(root4, "missing")
check("invalidate on missing DB is a no-op creating nothing",
      not spike.db_path(root4).exists())

print("== Corruption tolerance (miss, never an error) ==")
root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
with with_db_rows(root) as conn:
    conn.execute("DELETE FROM blobs")            # drop every blob row
    conn.commit()
check("missing blob row is a miss", spike.lookup(root, "n") is None)

root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
with with_db_rows(root) as conn:
    conn.execute("UPDATE blobs SET bytes = ?", (b'{"v": 2}\n',))  # tamper
    conn.commit()
check("tampered blob row is a miss (hash verify retained)",
      spike.lookup(root, "n") is None)

root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
forged = hashlib.sha256(b'{"v": 9}\n').hexdigest()
with with_db_rows(root) as conn:
    conn.execute("UPDATE nodes SET output_sha256 = ? WHERE node_id = 'n'", (forged,))
    conn.commit()
check("forged state hash is a miss (blob path derived from verified hash)",
      spike.lookup(root, "n") is None)

root = fresh_root()
spike.store_node(root, "n", node_key="k", value=b"not-json-at-all" and {"v": 1})
raw = b"\xff\xfe not json \x00"
with with_db_rows(root) as conn:
    digest = hashlib.sha256(raw).hexdigest()
    conn.execute("INSERT OR REPLACE INTO nodes(node_id, node_key, output_sha256) "
                 "VALUES ('odd', 'k', ?)", (digest,))
    conn.execute("INSERT OR REPLACE INTO blobs(sha256, bytes) VALUES (?, ?)", (digest, raw))
    conn.commit()
check("unparseable blob with matching hash is a miss", spike.lookup(root, "odd") is None)

root = fresh_root()
db = spike.db_path(root)
db.parent.mkdir(parents=True, exist_ok=True)
db.write_bytes(b"this is not a database at all, just garbage bytes")
check("corrupt DB file: read_state is {} (miss, never error)", spike.read_state(root) == {})
check("corrupt DB file: lookup is a miss", spike.lookup(root, "n") is None)
spike.store_node(root, "n", node_key="k", value={"v": 1})
check("corrupt DB file: write path rebuilds and store succeeds",
      spike.lookup(root, "n") is not None)

print("== Rebuild-or-refuse on the write path ==")
root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
db = spike.db_path(root)
db.write_bytes(b"garbage")                       # corrupt the DB
with with_db_rows(root) as conn:
    pass
import os
os.chmod(db.parent, 0o755)
db.write_bytes(b"garbage")
# Simulate unrecoverable: make the parent read-only so unlink fails.
os.chmod(db.parent, 0o555)
try:
    spike.store_node(root, "other", node_key="k", value={"v": 2})
    refused = False
    detail = "store succeeded (rebuild worked despite read-only parent?)"
except Exception as exc:
    refused = True
    detail = f"{type(exc).__name__}: {str(exc)[:60]}"
os.chmod(db.parent, 0o755)
check("unrecoverable corruption refuses (TransactionFailure, never partial)",
      refused and "TransactionFailure" in detail, detail)

print("== Versioned schema + root identity ==")
root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
with with_db_rows(root) as conn:
    conn.execute("UPDATE meta SET value = '999' WHERE key = 'schema_version'")
    conn.commit()
check("wrong schema_version: read is a miss", spike.read_state(root) == {})
spike.store_node(root, "n2", node_key="k", value={"v": 2})
check("wrong schema_version: write rebuilds (old row dropped, new stored)",
      set(spike.read_state(root)) == {"n2"})

root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
moved = fresh_root()
shutil.rmtree(moved)
shutil.copytree(root, moved)
check("copied repo (new fingerprint): read is a miss (all entries rebuilt)",
      spike.read_state(moved) == {})
spike.store_node(moved, "n2", node_key="k", value={"v": 2})
check("copied repo: write rebuilds identity and stores",
      set(spike.read_state(moved)) == {"n2"})

print("== Path-safety policy retained ==")
root = fresh_root()
(root / "generated").mkdir(parents=True)
(root / "generated" / "derived-state").symlink_to("/tmp")
try:
    spike.store_node(root, "n", node_key="k", value={"v": 1})
    check("symlinked derived-state dir refused", False, "no exception raised")
except Exception as exc:
    check("symlinked derived-state dir refused (TransactionFailure)",
          "TransactionFailure" in type(exc).__name__, str(exc)[:60])

root = fresh_root()
(root / "generated").mkdir(parents=True)
db = root / "generated" / "derived-state" / spike.DB_FILENAME
db.parent.mkdir(parents=True)
db.symlink_to("/tmp/elsewhere.db")
try:
    spike.store_node(root, "n", node_key="k", value={"v": 1})
    check("symlinked DB file refused", False, "no exception raised")
except Exception as exc:
    check("symlinked DB file refused (TransactionFailure)",
          "TransactionFailure" in type(exc).__name__, str(exc)[:60])

print("== Sweep, sharing, replacement ==")
root = fresh_root()
s1 = spike.store_node(root, "a", node_key="k1", value={"same": 1})
s2 = spike.store_node(root, "b", node_key="k2", value={"same": 1})
with with_db_rows(root) as conn:
    n = conn.execute("SELECT COUNT(*) FROM blobs").fetchone()[0]
check("identical values share one blob row", n == 1)
counts = spike.sweep_unreferenced_blobs(root, dry_run=True)
check("sweep dry-run counts", counts["kept"] == 1 and counts["deleted"] == 0, str(counts))
root = fresh_root()
first = spike.store_node(root, "n", node_key="k1", value={"v": 1})
second = spike.store_node(root, "n", node_key="k2", value={"v": 2})
counts = spike.sweep_unreferenced_blobs(root)
check("sweep deletes the orphaned old blob",
      counts["deleted"] == 1 and spike.lookup(root, "n")[0] == second, str(counts))
root = fresh_root()
spike.store_node(root, "a", node_key="k", value={"v": 1})
spike.store_node(root, "b", node_key="k", value={"v": 2})
spike.invalidate(root, "a")
check("invalidate drops one entry, keeps the other",
      spike.lookup(root, "a") is None and spike.lookup(root, "b") is not None)
check("invalidate leaves the blob row as a harmless orphan",
      spike.sweep_unreferenced_blobs(root)["deleted"] == 1)

print("== Adversarial (review round 2): identity, foreign stores, corruption ==")


def _snapshot(root):
    """Full store content snapshot: nodes, meta, blobs - for proving that a
    refused or mismatched database was NOT modified by any attempt."""
    with with_db_rows(root) as conn:
        return (conn.execute("SELECT node_id, node_key, output_sha256 FROM nodes"
                             " ORDER BY node_id").fetchall(),
                conn.execute("SELECT key, value FROM meta ORDER BY key").fetchall(),
                conn.execute("SELECT sha256 FROM blobs ORDER BY sha256").fetchall())


# (a) invalid schema_version in the DB: reads refuse to serve and the
# mismatched database is not modified by those reads.
root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
before = _snapshot(root)
with with_db_rows(root) as conn:
    conn.execute("UPDATE meta SET value = '999' WHERE key = 'schema_version'")
    conn.commit()
mismatched = _snapshot(root)
check("invalid schema_version: read_state is a miss", spike.read_state(root) == {})
check("invalid schema_version: lookup is a miss", spike.lookup(root, "n") is None)
check("mismatched DB not modified by the reads", _snapshot(root) == mismatched)
spike.store_node(root, "n2", node_key="k", value={"v": 2})
check("invalid schema_version: write rebuilds (only the new entry survives)",
      set(spike.read_state(root)) == {"n2"})

# (b) symlinked derived-state/ pointing at a FOREIGN store: every attempt
# refuses or misses, and the foreign store is untouched.
foreign = fresh_root()
spike.store_node(foreign, "victim", node_key="fk", value={"secret": True})
foreign_before = _snapshot(foreign)
root = fresh_root()
(root / "generated").mkdir(parents=True)
(root / "generated" / "derived-state").symlink_to(foreign / "generated" / "derived-state")
check("symlinked derived-state: read_state is a miss (no traversal)",
      spike.read_state(root) == {})
check("symlinked derived-state: lookup is a miss", spike.lookup(root, "x") is None)
try:
    spike.store_node(root, "local", node_key="lk", value={"v": 1})
    refused = False
    detail = "store_node succeeded through the symlink"
except Exception as exc:
    refused = "TransactionFailure" in type(exc).__name__
    detail = f"{type(exc).__name__}: {str(exc)[:60]}"
check("symlinked derived-state: write refused (TransactionFailure)", refused, detail)
try:
    spike.sweep_unreferenced_blobs(root)
    swept = False
    detail = "sweep succeeded through the symlink"
except Exception as exc:
    swept = "TransactionFailure" in type(exc).__name__
    detail = f"{type(exc).__name__}: {str(exc)[:60]}"
check("symlinked derived-state: sweep refused (never deletes rows abroad)", swept, detail)
check("foreign store untouched by every attempt", _snapshot(foreign) == foreign_before)

# (c) corrupt DB file: reads are misses that do not touch the file; the
# write path rebuilds atomically (build-to-temp, verify, rename).
root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
db = spike.db_path(root)
db.write_bytes(b"garbage")
corrupt_bytes = db.read_bytes()
check("corrupt DB: read_state is a miss", spike.read_state(root) == {})
check("corrupt DB: lookup is a miss", spike.lookup(root, "n") is None)
check("corrupt DB unmodified by the reads", db.read_bytes() == corrupt_bytes)
spike.store_node(root, "n2", node_key="k", value={"v": 2})
check("corrupt DB: write rebuilds atomically and serves",
      spike.lookup(root, "n2") is not None)
check("atomic rebuild left no .rebuild temp",
      not (spike.derived_dir(root) / "state-v1.db.rebuild").exists())
check("sweep after rebuild reports zeros on the fresh store",
      spike.sweep_unreferenced_blobs(root, dry_run=True)["deleted"] == 0)

# (d) predictable temp name attack (review round 3): a dangling symlink at
# the historical fixed temp path is inert - mkstemp creates its own
# unpredictable exclusive file and never touches the planted name.
root = fresh_root()
spike.store_node(root, "n", node_key="k", value={"v": 1})
db = spike.db_path(root)
old_tmp = spike.derived_dir(root) / "state-v1.db.rebuild"
foreign_target = fresh_root() / "outside.db"
old_tmp.symlink_to(foreign_target)          # dangling: the target does not exist
db.write_bytes(b"garbage")                  # force a rebuild on the next write
spike.store_node(root, "n2", node_key="k", value={"v": 2})
check("planted temp symlink: store rebuilt and serves",
      spike.lookup(root, "n2") is not None)
check("planted temp symlink: never followed or replaced",
      old_tmp.is_symlink() and not old_tmp.exists())
check("planted temp symlink: external target never created",
      not foreign_target.exists())
check("planted temp symlink: live store is a plain regular file, not a link",
      not os.path.islink(db))

print()
passed = sum(1 for ok, _, _ in _results if ok)
print(f"RESULT: {passed}/{len(_results)} scenarios passed")
sys.exit(0 if passed == len(_results) else 1)
