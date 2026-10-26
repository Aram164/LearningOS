"""Complete-report budgeting (D12): bound stdout, preserve full evidence."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


def encode(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def minimum_ledger_bytes(step_ids: list[str]) -> int:
    rows = [{"id": s, "status": "skipped", "ms": 0} for s in step_ids]
    return len(encode({"schema_version": 2, "steps": rows, "totals": {}}).encode("utf-8")) + 512


def write_full_report(artifact_dir: Path, report: dict[str, object]) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    body = encode(report)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    target = artifact_dir / "full-report.json"
    fd, tmp = tempfile.mkstemp(dir=artifact_dir, suffix=".tmp")
    try:
        os.write(fd, body.encode("utf-8"))
        os.close(fd)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    (artifact_dir / "full-report.sha256").write_text(digest + "\n", encoding="utf-8")
    return target


def bound_report(report: dict[str, object], max_bytes: int, artifact_path: str | None) -> dict[str, object]:
    """Strip output bodies until the encoded report fits; keep every row."""
    bounded: dict[str, object] = json.loads(encode(report))
    bounded["full_report"] = artifact_path
    if len(encode(bounded).encode("utf-8")) + 1 <= max_bytes:
        return bounded
    steps_obj = bounded.get("steps")
    rows: list[dict[str, object]] = steps_obj if isinstance(steps_obj, list) else []
    for row in rows:
        row.pop("output", None)
        row["output_omitted"] = True
    if len(encode(bounded).encode("utf-8")) + 1 <= max_bytes:
        return bounded
    for row in rows:
        err = row.get("error")
        if isinstance(err, dict):
            for key in list(err):
                if key not in ("code", "retryable"):
                    err.pop(key, None)
    return bounded
