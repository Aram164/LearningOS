"""Complete stdout budgets and private, incremental recovery evidence."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import cast

from learning_os.domain.codes import STEP_FAILED
from learning_os.store.transactions import atomic_write_bytes


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
    def __init__(self, root: Path, requested: Path | None = None):
        if requested is not None and requested.resolve().is_relative_to(root.resolve()):
            raise ValueError("full report directory must be outside the selected data root")
        if requested is not None:
            requested.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = Path(tempfile.mkdtemp(prefix="los-agent-plan-", dir=requested))
        os.chmod(self.path, 0o700)
        self.full_path = self.path / "full-report.json"
        self.rows: list[dict[str, object]] = []
        self.plan_digest = ""
        # Probe before any mutation; the directory is also the emergency recovery index.
        for name in ("checkpoint.jsonl", "raw-steps.jsonl"):
            atomic_write_bytes(self.path / name, b"")

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
        self.rows.append(row)
        with (self.path / "checkpoint.jsonl").open("ab") as stream:
            stream.write(encode(row).encode("utf-8") + b"\n")
        # Flush evidence before admitting another mutation. Read-only rows are
        # linear append I/O, then synced together at finalization.
        if row.get("commit_certainty") != "none" or row.get("status") != "ok":
            self.sync()

    def sync(self) -> None:
        for name in ("raw-steps.jsonl", "checkpoint.jsonl"):
            with (self.path / name).open("ab") as stream:
                stream.flush()
                os.fsync(stream.fileno())


def expand_report(path: Path, step_id: str | None = None) -> dict[str, object]:
    """Explicit expansion verifies the finalized report and its raw journals."""
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
