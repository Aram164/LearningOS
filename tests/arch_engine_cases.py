"""Engine-effect cases for the marker-neutrality baseline (S03 Task 1).

Each case builds a ``mini_repo``-style fixture (``build_mini_repo`` plus
``add_curriculum``) and drives ``TransactionService`` directly with a fixed
clock. Cases return JSON-serializable records with before/after effects.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import arch_effects
import yaml
from history_baselines import historical_files

CASE_NAMES = [
    "apply-writes-and-deletes",
    "rollback-complete",
    "rollback-incomplete",
    "crash-recovery",
    "sink-exception",
    "post-receipt-callback-failure",
]

CLOCK_DT = datetime(2026, 10, 1, 9, 0, tzinfo=ZoneInfo("Europe/Berlin"))


def _clock() -> datetime:
    return CLOCK_DT


_TX_RE = re.compile(r"transaction-\d{8}-\d{6}-\d{3}")
_BK_RE = re.compile(r"backup-\d+")


class _Normalizer:
    """Map transaction ids, backup ids and absolute paths to stable tokens."""

    def __init__(self, root: Path):
        resolved = str(root.resolve())
        raw = str(root)
        tmp = tempfile.gettempdir()
        tmp_resolved = str(Path(tmp).resolve())
        # Longest first so resolved forms win over raw prefixes.
        self._roots = sorted(
            {resolved, raw, tmp, tmp_resolved} - {""}, key=len, reverse=True)
        self._tx_map: dict[str, str] = {}
        self._bk_map: dict[str, str] = {}

    def norm_str(self, value: str) -> str:
        for prefix in self._roots:
            if prefix in value:
                value = value.replace(prefix, "<ROOT>")
        def _tx_sub(match: re.Match) -> str:
            orig = match.group(0)
            if orig not in self._tx_map:
                self._tx_map[orig] = f"TX{len(self._tx_map) + 1}"
            return self._tx_map[orig]
        value = _TX_RE.sub(_tx_sub, value)
        def _bk_sub(match: re.Match) -> str:
            orig = match.group(0)
            if orig not in self._bk_map:
                self._bk_map[orig] = f"BK{len(self._bk_map) + 1}"
            return self._bk_map[orig]
        return _BK_RE.sub(_bk_sub, value)

    def norm_obj(self, obj):
        if isinstance(obj, str):
            return self.norm_str(obj)
        if isinstance(obj, dict):
            return {
                (self.norm_str(k) if isinstance(k, str) else k):
                self.norm_obj(v)
                for k, v in obj.items()
            }
        if isinstance(obj, (list, tuple)):
            return [self.norm_obj(v) for v in obj]
        return obj


class _pinned_tz:
    """Pin TZ=Europe/Berlin in-process, restoring afterwards (SPEC §0)."""

    def __init__(self):
        self._old = os.environ.get("TZ")
        self._had_tzset = hasattr(time, "tzset")

    def __enter__(self):
        os.environ["TZ"] = "Europe/Berlin"
        if self._had_tzset:
            time.tzset()

    def __exit__(self, *exc):
        if self._old is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = self._old
        if self._had_tzset:
            time.tzset()


def _build_root(tmp_path: Path, name: str) -> Path:
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    root = build_mini_repo(tmp_path / name).resolve()
    add_curriculum(root)
    # This historical engine oracle includes contract bytes in its tree and
    # snapshot hashes. Keep its original inputs when later contracts change;
    # the full scenario suite exercises current contracts independently.
    historical = historical_files("074f4717e14527798752de84b3c9c4e88348b658")
    # Freeze the inventory as well as bytes: later schemas are not inputs
    # to this historical oracle. Current-contract scenarios run separately.
    for target in (root / "system/schema").rglob("*.schema.json"):
        if target.relative_to(root).as_posix() not in historical:
            target.unlink()
    for relpath, data in historical.items():
        target = root / relpath
        # build_mini_repo deliberately omits host-local attachment policy.
        if target.is_file():
            target.write_bytes(data)
    return root


def _read_yaml_or_absent(path: Path):
    if not path.is_file() or path.is_symlink():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _list_receipts(root: Path) -> list[Path]:
    directory = root / "operations" / "transactions"
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.glob("transaction-*.yaml")
        if p.is_file() and not p.is_symlink())


def _capture_journal(root: Path, normalizer: _Normalizer) -> dict:
    inflight = root / "operations" / "transactions" / ".inflight"
    files: dict[str, str] = {}
    intents: dict[str, object] = {}
    if inflight.is_dir() and not inflight.is_symlink():
        for dirpath, dirnames, filenames in os.walk(
                inflight, followlinks=False):
            dirnames[:] = [
                d for d in dirnames
                if not Path(dirpath, d).is_symlink()
            ]
            for name in filenames:
                full = Path(dirpath, name)
                if full.is_symlink() or not full.is_file():
                    continue
                rel = normalizer.norm_str(
                    full.relative_to(root).as_posix())
                files[rel] = hashlib.sha256(
                    full.read_bytes()).hexdigest()
                if name == "intent.json":
                    try:
                        parsed = json.loads(
                            full.read_text(encoding="utf-8"))
                    except (OSError, ValueError):
                        parsed = {"<unreadable>": True}
                    intents[rel] = normalizer.norm_obj(parsed)
    return {"files": files, "intents": intents}


def _capture_ledger(root: Path, normalizer: _Normalizer):
    import learning_os.store.session_ledger as plumbing

    path = plumbing.session_ledger(root)
    if not path.is_file() or path.is_symlink():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"<unreadable>": True}
    try:
        return normalizer.norm_obj(json.loads(text))
    except ValueError:
        return normalizer.norm_str(text)


def _capture_all(root: Path, normalizer: _Normalizer) -> dict:
    return {
        "tree": arch_effects.capture_tree(root),
        "revisions": _read_yaml_or_absent(
            root / "operations" / "transactions" / "revisions.yaml"),
        "idempotency": _read_yaml_or_absent(
            root / "operations" / "transactions" / "idempotency.yaml"),
        "journal": _capture_journal(root, normalizer),
        "ledger": _capture_ledger(root, normalizer),
    }


def _result_to_dict(result, normalizer: _Normalizer):
    if result is None:
        return None
    return normalizer.norm_obj({
        "transaction_id": result.transaction_id,
        "receipt_path": str(result.receipt_path),
        "revisions": dict(result.revisions),
        "snapshot_before": result.snapshot_before,
        "snapshot_after": result.snapshot_after,
    })


def _exc_to_dict(exc: BaseException | None, normalizer: _Normalizer):
    if exc is None:
        return None
    return {
        "type": type(exc).__name__,
        "message": normalizer.norm_str(str(exc)),
    }


def _finish_case(name: str, root: Path, normalizer: _Normalizer,
                 before: dict, after: dict,
                 receipts_before: list[Path],
                 result, exc: BaseException | None) -> dict:
    receipts_after = _list_receipts(root)
    before_names = {p.name for p in receipts_before}
    added = []
    for path in receipts_after:
        if path.name not in before_names:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
            added.append(normalizer.norm_obj(parsed))
    added.sort(key=lambda item: json.dumps(item, sort_keys=True, default=str))
    return {
        "case": name,
        "tree_before": normalizer.norm_obj(before["tree"]),
        "tree_after": normalizer.norm_obj(after["tree"]),
        "receipts_added": added,
        "revisions_before": normalizer.norm_obj(before["revisions"]),
        "revisions_after": normalizer.norm_obj(after["revisions"]),
        "idempotency_before": normalizer.norm_obj(before["idempotency"]),
        "idempotency_after": normalizer.norm_obj(after["idempotency"]),
        "journal_before": normalizer.norm_obj(before["journal"]),
        "journal_after": normalizer.norm_obj(after["journal"]),
        "ledger_before": normalizer.norm_obj(before["ledger"]),
        "ledger_after": normalizer.norm_obj(after["ledger"]),
        "exception": _exc_to_dict(exc, normalizer),
        "result": _result_to_dict(result, normalizer),
    }


def case_apply_writes_and_deletes(tmp_path: Path) -> dict:
    from learning_os.store.transactions import TransactionService

    name = "apply-writes-and-deletes"
    with _pinned_tz():
        root = _build_root(tmp_path, name)
        normalizer = _Normalizer(root)
        to_delete = root / "work" / "inbox" / "to-delete.md"
        to_delete.write_text("old inbox note\n", encoding="utf-8")
        to_write = root / "work" / "inbox" / "new.md"
        before = _capture_all(root, normalizer)
        receipts_before = _list_receipts(root)
        result = None
        exc: BaseException | None = None
        try:
            result = TransactionService(
                root, clock=_clock).commit(
                    capability="capture.create",
                    writes={to_write: "new inbox note\n"},
                    deletes=[to_delete],
                    artifact_ids=["arch-apply"])
        except BaseException as error:  # noqa: BLE001 - recorded, not raised
            exc = error
        after = _capture_all(root, normalizer)
        return _finish_case(
            name, root, normalizer, before, after,
            receipts_before, result, exc)


def case_rollback_complete(tmp_path: Path) -> dict:
    from learning_os.store.transactions import TransactionService

    name = "rollback-complete"
    with _pinned_tz():
        root = _build_root(tmp_path, name)
        normalizer = _Normalizer(root)
        target = root / "work" / "inbox" / "rollback.md"
        before = _capture_all(root, normalizer)
        receipts_before = _list_receipts(root)
        result = None
        exc: BaseException | None = None
        try:
            result = TransactionService(
                root, clock=_clock).commit(
                    capability="capture.create",
                    writes={target: "will roll back\n"},
                    artifact_ids=["arch-rollback-complete"],
                    validate_state=lambda: ["forced validation failure"])
        except BaseException as error:  # noqa: BLE001 - recorded, not raised
            exc = error
        after = _capture_all(root, normalizer)
        return _finish_case(
            name, root, normalizer, before, after,
            receipts_before, result, exc)


def case_rollback_incomplete(tmp_path: Path) -> dict:
    import learning_os.store.transactions as tx_module
    from learning_os.store.transactions import TransactionFailure, TransactionService

    name = "rollback-incomplete"
    with _pinned_tz():
        root = _build_root(tmp_path, name)
        normalizer = _Normalizer(root)
        target = root / "work" / "inbox" / "rollback-incomplete.md"
        target.write_text("old\n", encoding="utf-8")
        resolved_target = target.resolve()
        before = _capture_all(root, normalizer)
        receipts_before = _list_receipts(root)
        original_write = tx_module.atomic_write_bytes

        def fail_only_when_restoring(path: Path, content: bytes):
            try:
                same = Path(path).resolve() == resolved_target
            except OSError:
                same = False
            if same and content == b"old\n":
                raise TransactionFailure("forced restore failure")
            return original_write(path, content)

        result = None
        exc: BaseException | None = None
        tx_module.atomic_write_bytes = fail_only_when_restoring
        try:
            try:
                result = TransactionService(
                    root, clock=_clock).commit(
                        capability="capture.create",
                        writes={target: "new\n"},
                        artifact_ids=["arch-rollback-incomplete"],
                        validate_state=lambda: ["forced validation failure"])
            except BaseException as error:  # noqa: BLE001 - recorded
                exc = error
        finally:
            tx_module.atomic_write_bytes = original_write
        after = _capture_all(root, normalizer)
        return _finish_case(
            name, root, normalizer, before, after,
            receipts_before, result, exc)


_CRASH_WRAPPER = """\
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import learning_os.store.transactions as tx
from learning_os.store.transactions import TransactionService

original_write = tx.atomic_write_bytes
call_count = 0
target_calls = int(sys.argv[1])

def crashing_write(path, content):
    global call_count
    original_write(path, content)
    call_count += 1
    if call_count == target_calls:
        os._exit(77)

tx.atomic_write_bytes = crashing_write

root = Path(sys.argv[2])
clock_dt = datetime(2026, 10, 1, 9, 0, tzinfo=ZoneInfo("Europe/Berlin"))
TransactionService(root, clock=lambda: clock_dt).commit(
    capability="capture.create",
    writes={root / "work/inbox/crash.md": "crashed\\n"},
    artifact_ids=["arch-crash"],
)
"""


def case_crash_recovery(tmp_path: Path) -> dict:
    import learning_os.app.lock as plumbing

    name = "crash-recovery"
    with _pinned_tz():
        root = _build_root(tmp_path, name)
        normalizer = _Normalizer(root)
        before = _capture_all(root, normalizer)
        receipts_before = _list_receipts(root)
        wrapper = tmp_path / "crash-wrapper.py"
        wrapper.write_text(_CRASH_WRAPPER, encoding="utf-8")
        env = dict(os.environ)
        env["TZ"] = "Europe/Berlin"
        proc = subprocess.run(
            [sys.executable, str(wrapper), "2", str(root)],
            capture_output=True, text=True, env=env, timeout=120)
        if proc.returncode != 77:
            raise AssertionError(
                f"crash wrapper exited {proc.returncode}, expected 77: "
                f"stdout={proc.stdout[-500:]} stderr={proc.stderr[-2000:]}")
        result = None
        exc: BaseException | None = None
        try:
            with plumbing.operator_lock(root):
                pass
        except BaseException as error:  # noqa: BLE001 - recorded
            exc = error
        after = _capture_all(root, normalizer)
        return _finish_case(
            name, root, normalizer, before, after,
            receipts_before, result, exc)


def case_sink_exception(tmp_path: Path) -> dict:
    import learning_os.store.transactions as tx_module
    from learning_os.store.transactions import TransactionService

    name = "sink-exception"
    with _pinned_tz():
        root = _build_root(tmp_path, name)
        normalizer = _Normalizer(root)
        target = root / "work" / "inbox" / "sink.md"
        before = _capture_all(root, normalizer)
        receipts_before = _list_receipts(root)
        original_write = tx_module.atomic_write_bytes
        calls = 0

        def fail_on_second(path: Path, content: bytes):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("forced sink failure")
            return original_write(path, content)

        result = None
        exc: BaseException | None = None
        tx_module.atomic_write_bytes = fail_on_second
        try:
            try:
                result = TransactionService(
                    root, clock=_clock).commit(
                        capability="capture.create",
                        writes={target: "sink\n"},
                        artifact_ids=["arch-sink"])
            except BaseException as error:  # noqa: BLE001 - recorded
                exc = error
        finally:
            tx_module.atomic_write_bytes = original_write
        after = _capture_all(root, normalizer)
        return _finish_case(
            name, root, normalizer, before, after,
            receipts_before, result, exc)


def case_post_receipt_callback_failure(tmp_path: Path) -> dict:
    from learning_os.store.transactions import TransactionService

    name = "post-receipt-callback-failure"
    with _pinned_tz():
        root = _build_root(tmp_path, name)
        normalizer = _Normalizer(root)
        target = root / "work" / "inbox" / "post-receipt.md"
        before = _capture_all(root, normalizer)
        receipts_before = _list_receipts(root)

        def fail_touched(_paths):
            raise RuntimeError("forced touched failure")

        result = None
        exc: BaseException | None = None
        try:
            result = TransactionService(
                root, clock=_clock).commit(
                    capability="capture.create",
                    writes={target: "committed\n"},
                    artifact_ids=["arch-post-receipt"],
                    touched=fail_touched)
        except BaseException as error:  # noqa: BLE001 - recorded
            exc = error
        after = _capture_all(root, normalizer)
        return _finish_case(
            name, root, normalizer, before, after,
            receipts_before, result, exc)


CASE_FUNCS = {
    "apply-writes-and-deletes": case_apply_writes_and_deletes,
    "rollback-complete": case_rollback_complete,
    "rollback-incomplete": case_rollback_incomplete,
    "crash-recovery": case_crash_recovery,
    "sink-exception": case_sink_exception,
    "post-receipt-callback-failure": case_post_receipt_callback_failure,
}


def run_case(name: str, tmp_path: Path) -> dict:
    return CASE_FUNCS[name](Path(tmp_path))


def run_all(tmp_path: Path) -> dict[str, dict]:
    return {name: run_case(name, Path(tmp_path)) for name in CASE_NAMES}
