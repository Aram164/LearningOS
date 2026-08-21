"""Hashing, atomic writes, path containment, garden identity, and the one
place the manifest AI shape is defined."""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import os
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .errors import DeliveryValidationError


def _read_yaml(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if value is None else value


def _dump_yaml(value: Any) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100)


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)


def _sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _iso(value: dt.datetime) -> str:
    return value.isoformat(timespec="seconds")


def _safe_relative(value: str) -> PurePosixPath:
    rel = PurePosixPath(str(value))
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
        raise DeliveryValidationError(f"unsafe bundle path: {value}")
    return rel


def _inside(root: Path, rel: str) -> Path:
    target = (root / Path(*_safe_relative(rel).parts)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise DeliveryValidationError(f"path escapes repository boundary: {rel}") from exc
    return target


def _snapshot(root: Path) -> str:
    # Local import avoids a cycle when genout projects AI-action state.
    from learning_os.fingerprint import source_fingerprint
    from learning_os.loader import load_repo

    return f"sha256:{source_fingerprint(load_repo(root))}"


def parse_frontmatter_request_id(path: Path) -> str | None:
    """Best-effort provenance read for an existing AI-derived transcription."""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:12]:
            if line.startswith("request_id:"):
                return line.split(":", 1)[1].strip() or None
    except OSError:
        return None
    return None


Clock = Callable[[], dt.datetime]


def _projection(*, garden_entries: list[dict[str, Any]], available: list[dict[str, Any]],
                adapters: list[dict[str, Any]], requests: list[dict[str, Any]]) -> dict[str, Any]:
    """The one place the manifest's AI shape is defined."""
    return {
        "garden_entries": garden_entries,
        "ai_actions": {
            "contract_version": 1,
            "available": available,
            "provider_adapters": adapters,
            "requests": requests,
        },
    }
