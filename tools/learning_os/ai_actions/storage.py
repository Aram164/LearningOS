"""Filesystem repository for requests, bundles and deliveries."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any
from .errors import DeliveryValidationError, MAX_DELIVERY_BYTES, MAX_DELIVERY_ENTRIES, TargetNotFoundError
from .support import _atomic_text, _dump_yaml, _inside, _read_yaml

class FilesystemAIActionRepository:
    def __init__(self, root: Path):
        self.root = root
        self.base = root / "operations" / "ai-actions"
        self.requests = self.base / "requests"
        self.deliveries = self.base / "deliveries"
        self.receipts = self.base / "receipts"
        self.garden_state = self.base / "garden-state"
        self.quarantine = self.base / "incoming"

    @staticmethod
    def _id(value: str) -> str:
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,127}", str(value)):
            raise DeliveryValidationError(f"unsafe exchange identifier: {value}")
        return str(value)

    def request_dir(self, request_id: str) -> Path:
        return self.requests / self._id(request_id)

    def request_path(self, request_id: str) -> Path:
        return self.request_dir(request_id) / "request.yaml"

    def delivery_dir(self, delivery_id: str) -> Path:
        return self.deliveries / self._id(delivery_id)

    def state_path(self, target_id: str) -> Path:
        return self.garden_state / f"{self._id(target_id)}.yaml"

    def save_request(self, request: dict[str, Any], bundle_files: dict[str, bytes]) -> None:
        destination = self.request_dir(str(request["id"]))
        if destination.exists():
            raise DeliveryValidationError(f"request already exists: {request['id']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
        try:
            _atomic_text(temp / "request.yaml", _dump_yaml(request))
            for rel, content in bundle_files.items():
                target = _inside(temp, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            os.replace(temp, destination)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise

    def get_request(self, request_id: str) -> dict[str, Any]:
        path = self.request_path(request_id)
        value = _read_yaml(path)
        if not isinstance(value, dict):
            raise TargetNotFoundError(f"AI action request not found: {request_id}")
        return value

    def update_request(self, request: dict[str, Any]) -> None:
        _atomic_text(self.request_path(str(request["id"])), _dump_yaml(request))

    def stage_delivery_directory(self, source: Path) -> tuple[dict[str, Any], Path]:
        """Copy untrusted provider output into a quarantine directory.

        Nothing lands at its published path until validation has passed, so a
        rejected delivery never occupies a canonical-looking location even
        momentarily.
        """
        source = source.expanduser().resolve()
        if not source.is_dir() or not (source / "delivery.yaml").is_file():
            raise DeliveryValidationError(
                "delivery import requires a directory containing delivery.yaml")
        total_bytes = 0
        for entries, path in enumerate(source.rglob("*"), start=1):
            if path.is_symlink():
                raise DeliveryValidationError("delivery bundles may not contain symbolic links")
            if entries > MAX_DELIVERY_ENTRIES:
                raise DeliveryValidationError(
                    f"delivery bundle exceeds {MAX_DELIVERY_ENTRIES} entries")
            if path.is_file():
                total_bytes += path.stat().st_size
                if total_bytes > MAX_DELIVERY_BYTES:
                    raise DeliveryValidationError(
                        f"delivery bundle exceeds {MAX_DELIVERY_BYTES} bytes")
        delivery = _read_yaml(source / "delivery.yaml")
        if not isinstance(delivery, dict):
            raise DeliveryValidationError("delivery.yaml must contain a mapping")
        destination = self.delivery_dir(str(delivery.get("id", "")))
        if destination.exists():
            raise DeliveryValidationError(f"delivery already exists: {delivery.get('id')}")
        self.quarantine.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=f"{destination.name}-", dir=self.quarantine))
        staged = temp / "bundle"
        try:
            shutil.copytree(source, staged)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        return delivery, staged

    def publish_delivery(self, staged: Path, delivery_id: str) -> Path:
        destination = self.delivery_dir(delivery_id)
        try:
            if destination.exists():
                raise DeliveryValidationError(f"delivery already exists: {delivery_id}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged, destination)
        except Exception:
            # Never leave quarantined bytes behind, whatever went wrong.
            shutil.rmtree(staged.parent, ignore_errors=True)
            raise
        shutil.rmtree(staged.parent, ignore_errors=True)
        return destination

    def get_delivery(self, delivery_id: str) -> tuple[dict[str, Any], Path]:
        directory = self.delivery_dir(delivery_id)
        delivery = _read_yaml(directory / "delivery.yaml")
        if not isinstance(delivery, dict):
            raise TargetNotFoundError(f"AI delivery not found: {delivery_id}")
        return delivery, directory

    def receipt_path(self, transaction_id: str) -> Path:
        return self.receipts / f"{self._id(transaction_id)}.yaml"

    def request_projections(self) -> list[dict[str, Any]]:
        rows = []
        if not self.requests.is_dir():
            return rows
        for path in sorted(self.requests.glob("*/request.yaml")):
            request = _read_yaml(path)
            if not isinstance(request, dict):
                continue
            rows.append({
                "id": request.get("id"),
                "action_id": request.get("action_id"),
                "target": request.get("target"),
                "provider": (request.get("provider") or {}).get("preferred"),
                "status": request.get("status"),
                "created_at": request.get("created_at"),
                "delivery_id": request.get("delivery_id"),
                "receipt_id": request.get("receipt_id"),
                "bundle_path": path.parent.relative_to(self.root).as_posix(),
            })
        return rows
