"""Filesystem repository for requests, bundles and deliveries."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import cast

import yaml

from learning_os.domain.ai_errors import (
    MAX_DELIVERY_BYTES,
    MAX_DELIVERY_ENTRIES,
    DeliveryAlreadyExists,
    DeliveryNotFound,
    DeliveryValidationError,
    RequestNotFound,
)
from learning_os.domain.ai_types import AIActionRequest, DeliveryRecord, RequestStatus
from learning_os.store.ai_actions.support import dump_yaml as _dump_yaml
from learning_os.store.ai_actions.support import inside as _inside
from learning_os.store.ai_actions.support import read_yaml as _read_yaml
from learning_os.store.ai_actions.support import sha256_file as _sha256_file
from learning_os.store.contracts.write_scopes import (
    WriteScopeError,
    path_segment,
    scoped_write_target,
)
from learning_os.store.fs import (
    atomic_write_bytes_exclusive,
    atomic_write_text_exclusive,
    sync_directory,
)
from learning_os.store.materials.slices import SLICE_BUNDLE_PREFIX


def atomic_text(path: Path, content: str) -> None:
    atomic_write_text_exclusive(
        path, content, error_factory=DeliveryValidationError
    )


class FilesystemAIActionRepository:
    def __init__(self, root: Path):
        self.root = root
        self.base = root / "operations" / "ai-actions"
        self.requests = self.base / "requests"
        self.deliveries = self.base / "deliveries"
        self.garden_state = self.base / "garden-state"
        self.quarantine = self.base / "incoming"

    @staticmethod
    def _id(value: str) -> str:
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,127}", str(value)):
            raise DeliveryValidationError(f"unsafe exchange identifier: {value}")
        return str(value)

    def request_dir(self, request_id: str) -> Path:
        return scoped_write_target(
            self.root, f"operations/ai-actions/requests/{self._id(request_id)}",
            ("operations/ai-actions/requests/*",),
        )

    def request_path(self, request_id: str) -> Path:
        return self.request_dir(request_id) / "request.yaml"

    def delivery_dir(self, delivery_id: str) -> Path:
        return scoped_write_target(
            self.root, f"operations/ai-actions/deliveries/{self._id(delivery_id)}",
            ("operations/ai-actions/deliveries/*",),
        )

    def state_path(self, target_id: str) -> Path:
        return self.garden_state / f"{self._id(target_id)}.yaml"

    def save_request(self, request: AIActionRequest, bundle_files: dict[str, bytes]) -> None:
        destination = self.request_dir(str(request["id"]))
        if destination.exists():
            raise DeliveryValidationError(f"request already exists: {request['id']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
        try:
            atomic_write_text_exclusive(
                temp / "request.yaml",
                _dump_yaml(request),
                boundary=temp,
                error_factory=DeliveryValidationError,
            )
            for rel, content in bundle_files.items():
                target = _inside(temp, rel)
                atomic_write_bytes_exclusive(
                    target,
                    content,
                    boundary=temp,
                    error_factory=DeliveryValidationError,
                )
            os.replace(temp, destination)
            sync_directory(destination.parent)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise

    def get_request(self, request_id: str) -> AIActionRequest:
        path = self.request_path(request_id)
        try:
            path.parent.lstat()
        except FileNotFoundError:
            # Miss-only inventory ((cx) D-8): the happy path above keeps
            # its single-file read; only a miss enumerates the same store.
            candidates = [str(row["id"]) for row in self.request_projections()
                          if row.get("id")]
            raise RequestNotFound(
                "request", request_id, candidates,
                message=f"AI action request not found: {request_id}") from None
        try:
            value = _read_yaml(path) if not path.is_symlink() else None
        except (OSError, ValueError, yaml.YAMLError):
            value = None
        if not isinstance(value, dict):
            raise DeliveryValidationError(
                f"request already exists: {request_id}; its request.yaml is "
                "missing or unreadable, so it cannot be confirmed"
            )
        return cast(AIActionRequest, value)

    def update_request(self, request: AIActionRequest) -> None:
        atomic_text(self.request_path(str(request["id"])), _dump_yaml(request))

    def _scan_delivery_tree(self, root: Path) -> None:
        entries = 0
        total_bytes = 0
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            current = Path(dirpath)
            for name in sorted(dirnames):
                entries += 1
                if entries > MAX_DELIVERY_ENTRIES:
                    raise DeliveryValidationError(
                        f"delivery bundle exceeds {MAX_DELIVERY_ENTRIES} entries"
                    )
                if (current / name).is_symlink():
                    raise DeliveryValidationError(
                        "delivery bundles may not contain symbolic links"
                    )
            for name in sorted(filenames):
                entries += 1
                if entries > MAX_DELIVERY_ENTRIES:
                    raise DeliveryValidationError(
                        f"delivery bundle exceeds {MAX_DELIVERY_ENTRIES} entries"
                    )
                candidate = current / name
                if candidate.is_symlink():
                    raise DeliveryValidationError(
                        "delivery bundles may not contain symbolic links"
                    )
                if candidate.is_file():
                    total_bytes += candidate.stat().st_size
                    if total_bytes > MAX_DELIVERY_BYTES:
                        raise DeliveryValidationError(
                            f"delivery bundle exceeds {MAX_DELIVERY_BYTES} bytes"
                        )

    def stage_delivery_directory(self, source: Path) -> tuple[DeliveryRecord, Path]:
        """Copy untrusted provider output into a quarantine directory.

        Nothing lands at its published path until validation has passed, so a
        rejected delivery never occupies a canonical-looking location even
        momentarily.
        """
        expanded = source.expanduser()
        if expanded.is_symlink():
            raise DeliveryValidationError("delivery bundles may not contain symbolic links")
        source = expanded.resolve()
        if not source.is_dir() or not (source / "delivery.yaml").is_file():
            raise DeliveryValidationError(
                "delivery import requires a directory containing delivery.yaml")
        self._scan_delivery_tree(source)
        try:
            delivery = _read_yaml(source / "delivery.yaml")
        except yaml.YAMLError as exc:
            # Provider output is untrusted: a malformed file is a named refusal,
            # never a parser traceback citing "<unicode string>".
            raise DeliveryValidationError(
                f"{source / 'delivery.yaml'} is not valid YAML: {exc}") from None
        if not isinstance(delivery, dict):
            raise DeliveryValidationError("delivery.yaml must contain a mapping")
        if not str(delivery.get("id", "")).strip():
            raise DeliveryValidationError("delivery.yaml must carry a non-empty id")
        destination = self.delivery_dir(str(delivery.get("id", "")))
        if destination.exists():
            raise DeliveryAlreadyExists(str(delivery.get("id")))
        try:
            quarantine = scoped_write_target(
                self.root, self.quarantine.absolute(), ("operations/ai-actions/incoming",),
            )
        except WriteScopeError as exc:
            raise DeliveryValidationError(f"unsafe delivery quarantine: {exc}") from exc
        quarantine.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=f"{destination.name}-", dir=quarantine))
        staged = temp / "bundle"
        try:
            # Preserve links as links so the post-copy admission pass can see
            # and reject a source that changed during the copy window.
            shutil.copytree(source, staged, symlinks=True)
            self._scan_delivery_tree(staged)
            delivery = _read_yaml(staged / "delivery.yaml")
            if not isinstance(delivery, dict):
                raise DeliveryValidationError("delivery.yaml must contain a mapping")
            if not str(delivery.get("id", "")).strip():
                raise DeliveryValidationError("delivery.yaml must carry a non-empty id")
            destination = self.delivery_dir(str(delivery.get("id", "")))
            if destination.exists():
                raise DeliveryAlreadyExists(str(delivery.get("id")))
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        return cast(DeliveryRecord, delivery), staged

    def _delivery_tree(self, root: Path) -> dict[str, str]:
        """Every entry under ``root``: directories as ``dir``, files by digest."""
        self._scan_delivery_tree(root)
        tree: dict[str, str] = {}
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            current = Path(dirpath)
            for name in dirnames:
                tree[(current / name).relative_to(root).as_posix()] = "dir"
            for name in filenames:
                candidate = current / name
                if candidate.is_symlink() or not candidate.is_file():
                    raise DeliveryValidationError(
                        f"delivery entry is not a regular file: {name}")
                tree[candidate.relative_to(root).as_posix()] = _sha256_file(candidate)
        return tree

    def same_delivery_bytes(self, source: Path, directory: Path) -> bool:
        """True when ``source`` holds exactly the imported delivery's bytes.

        The untrusted source gets the same admission checks as a fresh import
        (no symbolic links, the entry and byte limits) before anything is read.
        """
        expanded = source.expanduser()
        if expanded.is_symlink():
            raise DeliveryValidationError("delivery bundles may not contain symbolic links")
        source = expanded.resolve()
        if not source.is_dir() or not (source / "delivery.yaml").is_file():
            raise DeliveryValidationError(
                "delivery import requires a directory containing delivery.yaml")
        return self._delivery_tree(source) == self._delivery_tree(directory)

    def _checked_staged_delivery(self, staged: Path) -> Path:
        try:
            return scoped_write_target(
                self.root, staged.absolute(), ("operations/ai-actions/incoming/*/bundle",),
            )
        except WriteScopeError as exc:
            raise DeliveryValidationError(f"unsafe staged delivery: {exc}") from exc

    def commit_delivery_import(
        self,
        staged: Path,
        delivery_id: str,
        request: AIActionRequest,
    ) -> Path:
        """Publish a delivery and its request-state transition as one unit."""
        staged_bundle = self._checked_staged_delivery(staged)
        request_path = self.request_path(str(request["id"]))
        try:
            previous_request = request_path.read_text(encoding="utf-8")
        except OSError as exc:
            shutil.rmtree(staged_bundle.parent, ignore_errors=True)
            raise DeliveryValidationError(
                f"cannot preserve AI request before delivery import: {exc}"
            ) from exc
        destination: Path | None = None
        try:
            destination = self.publish_delivery(staged_bundle, delivery_id)
            self.update_request(request)
            return destination
        except Exception as exc:
            if destination is not None:
                shutil.rmtree(destination, ignore_errors=True)
            try:
                atomic_text(request_path, previous_request)
            except Exception as rollback_exc:
                raise DeliveryValidationError(
                    "delivery import failed and request rollback also failed"
                ) from rollback_exc
            raise exc

    def publish_delivery(self, staged: Path, delivery_id: str) -> Path:
        staged_bundle = self._checked_staged_delivery(staged)
        destination = self.delivery_dir(delivery_id)
        try:
            if destination.exists():
                raise DeliveryValidationError(f"delivery already exists: {delivery_id}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_bundle, destination)
        except Exception:
            # Never leave quarantined bytes behind, whatever went wrong.
            shutil.rmtree(staged_bundle.parent, ignore_errors=True)
            raise
        shutil.rmtree(staged_bundle.parent, ignore_errors=True)
        return destination

    def delivery_ids(self) -> list[str]:
        """Every imported delivery id, from directory names only."""
        if not self.deliveries.is_dir():
            return []
        return sorted(path.name for path in self.deliveries.iterdir()
                      if path.is_dir())

    def get_delivery(self, delivery_id: str) -> tuple[DeliveryRecord, Path]:
        directory = self.delivery_dir(delivery_id)
        delivery = _read_yaml(directory / "delivery.yaml")
        if not isinstance(delivery, dict):
            # Miss-only inventory ((cx) D-8), as in get_request above.
            raise DeliveryNotFound(
                "delivery", delivery_id, self.delivery_ids(),
                message=f"AI delivery not found: {delivery_id}")
        return cast(DeliveryRecord, delivery), directory

    def request_projections(self) -> list[RequestStatus]:
        rows: list[RequestStatus] = []
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


    def write_bundle_slice(self, request_id: str, relative: str, body: bytes) -> None:
        req_dir = self.request_dir(request_id)
        target = _inside(req_dir, relative)
        atomic_write_bytes_exclusive(
            target, body, boundary=req_dir, error_factory=DeliveryValidationError
        )

    def write_continuation(
        self,
        request_id: str,
        *,
        pass_number: int,
        route_id: str,
        record_text: str,
        slice_relative: str,
        slice_body: bytes,
        index_text: str,
    ) -> str:
        """Persist one reading-pass continuation inside its request bundle.

        Storage builds these paths and owns the writes (2A, Bar 4 v3 §5.4); the
        service only orchestrates. Order and atomicity are unchanged: the
        continuation record, then the slice body, then the slice index, each
        written atomically. Returns the record's bundle-relative path.
        """
        req_dir = self.request_dir(request_id)
        continuations = req_dir / SLICE_BUNDLE_PREFIX / "continuations"
        continuations.mkdir(parents=True, exist_ok=True)
        name = f"pass-{int(pass_number)}-{path_segment(route_id)}.yaml"
        atomic_write_text_exclusive(
            continuations / name, record_text, boundary=req_dir,
            error_factory=DeliveryValidationError,
        )
        self.write_bundle_slice(request_id, slice_relative, slice_body)
        atomic_write_text_exclusive(
            req_dir / SLICE_BUNDLE_PREFIX / "index.json", index_text, boundary=req_dir,
            error_factory=DeliveryValidationError,
        )
        return f"{SLICE_BUNDLE_PREFIX}/continuations/{name}"

    def discard_staged_delivery(self, staged: Path) -> None:
        staged_bundle = self._checked_staged_delivery(staged)
        shutil.rmtree(staged_bundle.parent, ignore_errors=True)
