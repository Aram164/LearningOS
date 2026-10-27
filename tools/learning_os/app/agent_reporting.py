"""Complete stdout budgets and private, incremental recovery evidence."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from types import TracebackType
from typing import cast

from learning_os.domain.codes import STEP_FAILED
from learning_os.store.transactions import atomic_write_bytes

REPORT_PREFIX = "los-agent-plan-"
RETENTION_MARKER = ".report-retention.json"
RETENTION_KIND = "learningos-agent-report"
MAX_REPORT_RUNS = 50
MAX_REPORT_AGE_S = 14 * 24 * 60 * 60


def encode(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def ledger_row(row: dict[str, object], index: int) -> dict[str, object]:
    result: dict[str, object] = {
        "id": row["id"], "status": row["status"],
        "commit_certainty": row.get("commit_certainty", "none"),
        "details_index": index, "output_omitted": True,
    }
    error = row.get("error")
    if isinstance(error, dict):
        result["error"] = {"code": str(error.get("code", STEP_FAILED))[:64],
                           "retryable": error.get("retryable") is True}
    if row.get("receipt") is not None:
        result["receipt_in_full_report"] = True
    return result


def minimum_ledger_bytes(step_ids: list[str], artifact_path: str = "") -> int:
    rows = [{"id": s, "status": "not_ready", "commit_certainty": "committed",
             "error": {"code": "X" * 64, "retryable": False}, "receipt": True}
            for s in step_ids]
    report = {"schema_version": 2, "steps": [ledger_row(r, i) for i, r in enumerate(rows)],
              "totals": {}, "full_report": artifact_path, "output_omitted": True}
    return len(encode(report).encode("utf-8")) + 513


def write_full_report(artifact_dir: Path, report: dict[str, object]) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    body = encode(report).encode("utf-8")
    target = artifact_dir / "full-report.json"
    atomic_write_bytes(target, body)
    atomic_write_bytes(artifact_dir / "full-report.sha256",
                       (hashlib.sha256(body).hexdigest() + "\n").encode())
    return target


def _retention_info(path: Path) -> tuple[int, bool] | None:
    """Recognize only owned report directories, including finalized legacy runs."""
    marker = path / RETENTION_MARKER
    try:
        if marker.is_symlink():
            return None
        if marker.exists():
            data = json.loads(marker.read_text())
            if (not isinstance(data, dict) or data.get("kind") != RETENTION_KIND
                    or data.get("version") != 1 or type(data.get("created_ns")) is not int
                    or data["created_ns"] <= 0 or type(data.get("keep")) is not bool):
                return None
            return data["created_ns"], data["keep"]
        # Old versions had no marker/lock. Only finalized, digest-bound reports
        # with the complete known layout are eligible; partial legacy evidence
        # stays available for review rather than being guessed disposable.
        names = ("plan.json", "approved-envelopes.json", "checkpoint.jsonl",
                 "raw-steps.jsonl", "full-report.json", "full-report.sha256")
        if any((path / name).is_symlink() or not (path / name).is_file() for name in names):
            return None
        with (path / "full-report.json").open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != (path / "full-report.sha256").read_text().strip():
            return None
        return (path / "full-report.json").stat().st_mtime_ns, False
    except (OSError, ValueError, TypeError):
        return None


def prune_reports(parent: Path, *, now_ns: int | None = None,
                  max_runs: int = MAX_REPORT_RUNS,
                  max_age_s: int = MAX_REPORT_AGE_S) -> list[Path]:
    """Bound one report collection, preserving kept and actively locked runs."""
    now = time.time_ns() if now_ns is None else now_ns
    candidates = []
    for path in parent.glob(REPORT_PREFIX + "*"):
        if path.is_symlink() or not path.is_dir():
            continue
        info = _retention_info(path)
        if info is not None and not info[1]:
            candidates.append((info[0], path))
    candidates.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    removed = []
    for index, (created, path) in enumerate(candidates):
        if index < max_runs and now - created <= max_age_s * 1_000_000_000:
            continue
        descriptor = None
        try:
            flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path / ".active.lock", flags, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            shutil.rmtree(path)
            removed.append(path)
        except OSError:
            pass  # Active, concurrently removed, or unreadable evidence stays safe.
        finally:
            if descriptor is not None:
                os.close(descriptor)
    return removed


def bound_report(report: dict[str, object], max_bytes: int,
                 artifact_path: str | None) -> dict[str, object]:
    bounded = cast(dict[str, object], json.loads(encode(report)))
    bounded["full_report"] = artifact_path
    if len(encode(bounded).encode("utf-8")) + 1 <= max_bytes:
        return bounded
    raw_rows = cast(list[dict[str, object]], bounded["steps"])
    bounded["steps"] = [ledger_row(row, i) for i, row in enumerate(raw_rows)]
    bounded["output_omitted"] = True
    if len(encode(bounded).encode("utf-8")) + 1 > max_bytes:
        # Admission reserves this exact ledger. Never silently exceed a budget.
        raise ValueError("report budget cannot hold the recovery ledger")
    return bounded


class ReportStore:
    def __init__(self, root: Path, requested: Path | None = None, *, keep_report: bool = False):
        parent = (requested if requested is not None else Path(tempfile.gettempdir())).resolve()
        if parent.is_relative_to(root.resolve()):
            raise ValueError("full report directory must be outside the selected data root")
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = Path(tempfile.mkdtemp(prefix=REPORT_PREFIX, dir=parent))
        os.chmod(self.path, 0o700)
        self._lock = os.fdopen(os.open(self.path / ".active.lock", os.O_CREAT | os.O_RDWR, 0o600), "a+b")
        fcntl.flock(self._lock, fcntl.LOCK_EX)
        marker = {"kind": RETENTION_KIND, "version": 1,
                  "created_ns": time.time_ns(), "keep": keep_report}
        atomic_write_bytes(self.path / RETENTION_MARKER, encode(marker).encode())
        self.full_path = self.path / "full-report.json"
        self.rows: list[dict[str, object]] = []
        self.plan_digest = ""
        # Probe before any mutation; the directory is also the emergency recovery index.
        for name in ("checkpoint.jsonl", "raw-steps.jsonl"):
            atomic_write_bytes(self.path / name, b"")
        prune_reports(parent)

    def __enter__(self) -> ReportStore:
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc: BaseException | None, traceback: TracebackType | None) -> None:
        self.close()

    def close(self) -> None:
        lock = getattr(self, "_lock", None)
        if lock is not None and not lock.closed:
            lock.close()

    def __del__(self) -> None:
        self.close()

    def inputs(self, plan: object, envelopes: list[bytes]) -> None:
        body = encode(plan).encode("utf-8")
        self.plan_digest = "sha256:" + hashlib.sha256(body).hexdigest()
        atomic_write_bytes(self.path / "plan.json", body)
        names = []
        for index, raw in enumerate(envelopes):
            name = f"approved-envelope-{index:04d}.json"
            atomic_write_bytes(self.path / name, raw)
            names.append({"file": name, "sha256": hashlib.sha256(raw).hexdigest()})
        atomic_write_bytes(self.path / "approved-envelopes.json", encode(names).encode("utf-8"))

    def raw(self, index: int, stdout: str, stderr: str) -> tuple[str, str]:
        body = encode({"index": index, "stdout": stdout, "stderr": stderr}).encode("utf-8")
        with (self.path / "raw-steps.jsonl").open("ab") as stream:
            stream.write(body + b"\n")
        return f"raw-steps.jsonl#{index}", hashlib.sha256(body).hexdigest()

    def record(self, row: dict[str, object]) -> None:
        stored = cast(dict[str, object], json.loads(encode(row)))
        with (self.path / "checkpoint.jsonl").open("ab") as stream:
            stream.write(encode(stored).encode("utf-8") + b"\n")
        self.rows.append(stored)
        # Flush evidence before admitting another mutation. Read-only rows are
        # linear append I/O, then synced together at finalization.
        if row.get("commit_certainty") != "none" or row.get("status") != "ok":
            self.sync()

    def correct(self, row: dict[str, object]) -> None:
        """Append the replacement evidence; never rewrite an earlier checkpoint."""
        index = next((i for i, old in enumerate(self.rows) if old["id"] == row["id"]), None)
        if index is None:
            raise ValueError("cannot correct an unrecorded step")
        stored = cast(dict[str, object], json.loads(encode(row)))
        old = self.rows[index]
        if old.get("commit_certainty") == "committed" and (
                stored.get("commit_certainty") != "committed" or stored.get("receipt") != old.get("receipt")):
            raise ValueError("a checkpoint correction cannot erase committed receipt evidence")
        event = {"event": "step-correction", "details_index": index, "row": stored}
        with (self.path / "checkpoint.jsonl").open("ab") as stream:
            stream.write(encode(event).encode("utf-8") + b"\n")
        self.rows[index] = stored
        self.sync()

    def sync(self) -> None:
        for name in ("raw-steps.jsonl", "checkpoint.jsonl"):
            with (self.path / name).open("ab") as stream:
                stream.flush()
                os.fsync(stream.fileno())


def expand_report(path: Path, step_id: str | None = None) -> dict[str, object]:
    """Check finalized-report and journal corruption, then expand.

    Adjacent digests are not signatures: changing both data and its digest can
    pass these checks. They do not authenticate reports or approval evidence.
    """
    if path.name != "full-report.json":
        raise ValueError("full report is not finalized")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path.parent / ".active.lock", flags, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("report is still active; expand it after finalization") from exc
        return _expand_report_contents(path, step_id)
    finally:
        os.close(descriptor)


def _expand_report_contents(path: Path, step_id: str | None) -> dict[str, object]:
    body = path.read_bytes()
    if path.name != "full-report.json" or hashlib.sha256(body).hexdigest() != (path.parent / "full-report.sha256").read_text().strip():
        raise ValueError("full report digest mismatch or report is not finalized")
    report = cast(dict[str, object], json.loads(body))
    rows = cast(list[dict[str, object]], report["steps"])
    if step_id is not None:
        rows = [r for r in rows if r["id"] == step_id]
        if not rows:
            raise ValueError("step not found in full report")
    raw = {json.loads(line)["index"]: line for line in (path.parent / "raw-steps.jsonl").read_bytes().splitlines()}
    for row in rows:
        pointer = row.get("raw_artifact")
        if isinstance(pointer, str):
            name, index = pointer.split("#")
            if name != "raw-steps.jsonl":
                raise ValueError("invalid raw artifact pointer")
            line = raw[int(index)]
            if hashlib.sha256(line).hexdigest() != row.get("raw_sha256"):
                raise ValueError("raw step digest mismatch")
            row["raw"] = json.loads(line)
    report["steps"] = rows
    return report
