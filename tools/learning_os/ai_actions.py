"""Provider-independent AI action exchange for the first LearningOS vertical slice.

The pilot intentionally supports one action only: ``garden.shelve`` through a
manual request/delivery bundle.  External providers never receive repository
access.  LearningOS selects the bounded context, persists it, validates the
returned capability list, applies approved writes atomically, and records a
receipt.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from uuid import uuid4

import yaml


class AIActionError(Exception):
    """Base class for a refused AI-action operation."""


class ActionNotFoundError(AIActionError):
    pass


class ActionPolicyError(AIActionError):
    pass


class ConfidentialityError(AIActionError):
    pass


class DeliveryValidationError(AIActionError):
    pass


class StaleDeliveryError(AIActionError):
    pass


class TargetNotFoundError(AIActionError):
    pass


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
    return dt.datetime.now(dt.timezone.utc)


def _iso(value: dt.datetime) -> str:
    return value.isoformat(timespec="seconds")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "garden-seed"


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
    from learning_os.genout import _source_fingerprint
    from learning_os.loader import load_repo

    return f"sha256:{_source_fingerprint(load_repo(root))}"


def _garden_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped:
            return stripped.lstrip("#").strip()
    return fallback


def _garden_tags(body: str) -> list[str]:
    return sorted(set(re.findall(r"(?<![\w/])#([a-zA-Z][\w-]*)", body)))


def _garden_id(garden_root: Path, path: Path) -> str:
    rel = path.relative_to(garden_root).with_suffix("").as_posix()
    base = f"garden-note-{_slug(rel)}"
    # The suffix makes nested same-slug paths stable without making the common
    # one-file case noisy.
    matches = [p for p in garden_root.rglob("*.md")
               if not any(part.startswith(".") for part in p.relative_to(garden_root).parts)
               and p.name.lower() != "readme.md" and _slug(p.stem) == _slug(path.stem)]
    if len(matches) > 1:
        base += "-" + hashlib.sha256(rel.encode("utf-8")).hexdigest()[:8]
    return base


@dataclass(frozen=True)
class ActionDefinition:
    id: str
    title: str
    description: str
    target_kinds: tuple[str, ...]
    interaction_mode: str
    approval_required: bool
    context_selection: str
    supported_providers: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    forbidden_capabilities: tuple[str, ...]
    confidentiality_policy: dict[str, Any]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ActionDefinition":
        return cls(
            id=str(value["id"]),
            title=str(value["title"]),
            description=str(value.get("description", "")),
            target_kinds=tuple(str(v) for v in value.get("target_kinds", [])),
            interaction_mode=str(value.get("interaction_mode", "discussion")),
            approval_required=bool(value.get("approval_required", True)),
            context_selection=str(value.get("context_selection", "exact")),
            supported_providers=tuple(str(v) for v in value.get("supported_providers", [])),
            allowed_capabilities=tuple(str(v) for v in value.get("allowed_capabilities", [])),
            forbidden_capabilities=tuple(str(v) for v in value.get("forbidden_capabilities", [])),
            confidentiality_policy=dict(value.get("confidentiality_policy", {}) or {}),
        )

    def project(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_kinds": list(self.target_kinds),
            "interaction_mode": self.interaction_mode,
            "supported_providers": list(self.supported_providers),
        }


class ActionRegistry:
    def __init__(self, root: Path):
        self.root = root

    def list(self) -> list[ActionDefinition]:
        if not self.root.is_dir():
            return []
        actions = []
        for path in sorted(self.root.glob("*.yaml")):
            value = _read_yaml(path, {})
            if isinstance(value, dict):
                actions.append(ActionDefinition.from_mapping(value))
        return actions

    def get(self, action_id: str) -> ActionDefinition:
        for action in self.list():
            if action.id == action_id:
                return action
        raise ActionNotFoundError(f"unknown AI action: {action_id}")


class FilesystemAIActionRepository:
    def __init__(self, root: Path):
        self.root = root
        self.base = root / "operations" / "ai-actions"
        self.requests = self.base / "requests"
        self.deliveries = self.base / "deliveries"
        self.receipts = self.base / "receipts"
        self.garden_state = self.base / "garden-state"

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

    def import_delivery_directory(self, source: Path) -> dict[str, Any]:
        source = source.expanduser().resolve()
        if not source.is_dir() or not (source / "delivery.yaml").is_file():
            raise DeliveryValidationError("delivery import requires a directory containing delivery.yaml")
        if any(path.is_symlink() for path in source.rglob("*")):
            raise DeliveryValidationError("delivery bundles may not contain symbolic links")
        delivery = _read_yaml(source / "delivery.yaml")
        if not isinstance(delivery, dict):
            raise DeliveryValidationError("delivery.yaml must contain a mapping")
        destination = self.delivery_dir(str(delivery.get("id", "")))
        if destination.exists():
            raise DeliveryValidationError(f"delivery already exists: {delivery.get('id')}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
        shutil.copytree(source, temp)
        os.replace(temp, destination)
        return delivery

    def get_delivery(self, delivery_id: str) -> tuple[dict[str, Any], Path]:
        directory = self.delivery_dir(delivery_id)
        delivery = _read_yaml(directory / "delivery.yaml")
        if not isinstance(delivery, dict):
            raise TargetNotFoundError(f"AI delivery not found: {delivery_id}")
        return delivery, directory

    def save_receipt(self, receipt: dict[str, Any]) -> Path:
        path = self.receipts / f"{self._id(str(receipt['id']))}.yaml"
        if path.exists():
            raise DeliveryValidationError(f"receipt already exists: {receipt['id']}")
        _atomic_text(path, _dump_yaml(receipt))
        return path

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


Clock = Callable[[], dt.datetime]


class AIActionService:
    def __init__(self, root: Path, *, clock: Clock = _now_utc):
        self.root = root.resolve()
        self.clock = clock
        self.registry = ActionRegistry(self.root / "system" / "contracts" / "ai-actions")
        self.repository = FilesystemAIActionRepository(self.root)

    def list_actions(self) -> list[dict[str, Any]]:
        return [action.project() for action in self.registry.list()]

    def list_garden_targets(self) -> list[dict[str, Any]]:
        garden = self.root / "knowledge" / "garden"
        rows = []
        if not garden.is_dir():
            return rows
        for path in sorted(garden.rglob("*.md")):
            rel_parts = path.relative_to(garden).parts
            if path.name.startswith((".", "_")) or path.name.lower() == "readme.md":
                continue
            if any(part in {"transcriptions", "syntheses"} or part.startswith("_")
                   for part in rel_parts[:-1]):
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            target_id = _garden_id(garden, path)
            state = _read_yaml(self.repository.state_path(target_id), {})
            if not isinstance(state, dict):
                state = {}
            rows.append({
                "id": target_id,
                "type": "garden-note",
                "title": state.get("title") or _garden_title(body, path.stem),
                "path": path.relative_to(self.root).as_posix(),
                "state": state.get("state", "seed"),
                "revision": _sha256_file(path),
                "tags": _garden_tags(body),
                "job_derived": bool(state.get("job_derived", False)),
                "transcription_path": state.get("transcription_path"),
                "last_ai_request_id": state.get("last_ai_request_id"),
            })
        return rows

    def _target(self, target_id: str) -> tuple[dict[str, Any], Path]:
        for row in self.list_garden_targets():
            if row["id"] == target_id:
                return row, self.root / row["path"]
        raise TargetNotFoundError(f"Garden target not found: {target_id}")

    def prepare(
        self,
        *,
        action_id: str,
        target_kind: str,
        target_id: str,
        provider: str = "manual-bundle",
        expected_snapshot: str | None = None,
        request_id: str | None = None,
        job_export_confirmed: bool = False,
    ) -> dict[str, Any]:
        action = self.registry.get(action_id)
        if target_kind not in action.target_kinds:
            raise ActionPolicyError(f"action {action_id} does not support target kind {target_kind}")
        if provider not in action.supported_providers:
            raise ActionPolicyError(f"provider {provider} is not supported for action {action_id}")
        if action_id != "garden.shelve":
            raise ActionPolicyError("only the garden.shelve pilot is implemented")
        target, source = self._target(target_id)
        if (target.get("job_derived")
                and action.confidentiality_policy.get("job_derived_requires_confirmation", True)
                and not job_export_confirmed):
            raise ConfidentialityError(
                "job-derived content requires explicit export confirmation; Job/ remains inaccessible"
            )
        snapshot = _snapshot(self.root)
        if expected_snapshot and expected_snapshot != snapshot:
            raise StaleDeliveryError(
                f"expected snapshot {expected_snapshot}, current snapshot is {snapshot}"
            )
        now = self.clock()
        request_id = request_id or f"ai-request-{now:%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
        original = {
            "id": f"original-{target_id}",
            "canonical_path": target["path"],
            "bundle_path": f"attachments/{source.name}",
            "checksum": _sha256_file(source),
            "media_type": "text/markdown",
        }
        request = {
            "schema_version": 1,
            "id": request_id,
            "type": "ai-action-request",
            "action_id": action.id,
            "status": "prepared",
            "target": {"kind": target_kind, "id": target_id},
            "provider": {"preferred": provider, "adapter": provider},
            "context": {
                "artifact_ids": [target_id, original["id"]],
                "attachment_ids": [original["id"]],
                "originals": [original],
            },
            "allowed_capabilities": list(action.allowed_capabilities),
            "forbidden_capabilities": list(action.forbidden_capabilities),
            "preconditions": {
                "snapshot_id": snapshot,
                "artifact_revisions": {target_id: target["revision"]},
            },
            "confidentiality": {
                "classification": "private",
                "job_derived": bool(target.get("job_derived")),
                "export_confirmed": bool(job_export_confirmed),
                "employer_repository_access": False,
            },
            "created_at": _iso(now),
        }
        context = {
            "target": {k: target[k] for k in
                       ("id", "type", "title", "path", "state", "tags", "revision")},
            "content": source.read_text(encoding="utf-8", errors="replace"),
            "destination_metadata": {
                "durable_notes_root": "knowledge/notes/",
                "garden_transcriptions_root": "knowledge/garden/transcriptions/",
                "relationship_registry": "knowledge/relationships.yaml",
            },
        }
        instructions = (
            "# Shelve with AI\n\n"
            "Discuss this bounded Garden seed with the user. Preserve the original file "
            "unchanged. Keep transcription distinct from synthesis. Return an approved "
            "delivery directory containing `delivery.yaml`; use only capabilities listed "
            "in `allowed-capabilities.json`. Do not request or read Job/.\n"
        )
        bundle_files = {
            "instructions.md": instructions.encode("utf-8"),
            "context.md": ("# Bounded context\n\n```json\n"
                           + json.dumps(context, indent=2, ensure_ascii=False)
                           + "\n```\n").encode("utf-8"),
            "artifact-index.json": (json.dumps([original], indent=2) + "\n").encode("utf-8"),
            "allowed-capabilities.json": (
                json.dumps(list(action.allowed_capabilities), indent=2) + "\n"
            ).encode("utf-8"),
            "contract-lock.json": (json.dumps({
                "exchange_bundle_version": 1,
                "capability_contract_version": 1,
                "manifest_contract_version": 2,
                "action_registry_schema_version": 1,
            }, indent=2) + "\n").encode("utf-8"),
            original["bundle_path"]: source.read_bytes(),
        }
        self.repository.save_request(request, bundle_files)
        return request

    def import_delivery(self, source: Path) -> dict[str, Any]:
        delivery = self.repository.import_delivery_directory(source)
        delivery_id = str(delivery.get("id", ""))
        try:
            self.validate_delivery(delivery_id)
        except Exception:
            shutil.rmtree(self.repository.delivery_dir(delivery_id), ignore_errors=True)
            raise
        request = self.repository.get_request(str(delivery["request_id"]))
        request["status"] = "delivery-ready"
        request["delivery_id"] = delivery_id
        self.repository.update_request(request)
        return delivery

    def validate_delivery(self, delivery_id: str) -> dict[str, Any]:
        delivery, directory = self.repository.get_delivery(delivery_id)
        request = self.repository.get_request(str(delivery.get("request_id", "")))
        if delivery.get("type") != "ai-action-delivery":
            raise DeliveryValidationError("delivery type must be ai-action-delivery")
        if delivery.get("action_id") != request.get("action_id"):
            raise DeliveryValidationError("delivery action does not match request")
        producer = delivery.get("producer") or {}
        if producer.get("adapter") != (request.get("provider") or {}).get("adapter"):
            raise DeliveryValidationError("delivery adapter does not match prepared request")
        if delivery.get("preconditions") != request.get("preconditions"):
            raise DeliveryValidationError("delivery preconditions do not match prepared request")
        if not (delivery.get("approval") or {}).get("user_approved"):
            raise DeliveryValidationError("delivery lacks recorded user approval")
        operations = delivery.get("operations")
        if not isinstance(operations, list) or not operations:
            raise DeliveryValidationError("delivery must contain at least one operation")
        allowed = set(request.get("allowed_capabilities", []))
        forbidden = set(request.get("forbidden_capabilities", []))
        target_id = str((request.get("target") or {}).get("id", ""))
        for operation in operations:
            if not isinstance(operation, dict):
                raise DeliveryValidationError("each delivery operation must be a mapping")
            capability = operation.get("capability")
            if capability in forbidden or capability not in allowed:
                raise DeliveryValidationError(f"capability is not allowed: {capability}")
            if operation.get("target_id") and operation.get("target_id") != target_id:
                raise DeliveryValidationError("operation targets an unrelated artifact")
            artifact_ref = operation.get("artifact_ref")
            if artifact_ref:
                artifact = _inside(directory, str(artifact_ref))
                if not artifact.is_file():
                    raise DeliveryValidationError(f"delivery artifact is missing: {artifact_ref}")
        expected = str((request.get("preconditions") or {}).get("snapshot_id", ""))
        current = _snapshot(self.root)
        if current != expected:
            raise StaleDeliveryError(f"delivery is stale: expected {expected}, current {current}")
        target, _ = self._target(target_id)
        expected_revision = (request.get("preconditions") or {}).get(
            "artifact_revisions", {}).get(target_id)
        if target.get("revision") != expected_revision:
            raise StaleDeliveryError("Garden target changed after request preparation")
        for original in (request.get("context") or {}).get("originals", []):
            path = _inside(self.root, str(original["canonical_path"]))
            if not path.is_file() or _sha256_file(path) != original.get("checksum"):
                raise DeliveryValidationError("original artifact changed after request preparation")
        return {"ok": True, "delivery_id": delivery_id, "request_id": request["id"]}

    def apply_delivery(self, delivery_id: str) -> dict[str, Any]:
        self.validate_delivery(delivery_id)
        delivery, directory = self.repository.get_delivery(delivery_id)
        request = self.repository.get_request(str(delivery["request_id"]))
        target_id = str(request["target"]["id"])
        target, _source = self._target(target_id)
        state_path = self.repository.state_path(target_id)
        state = _read_yaml(state_path, {})
        if not isinstance(state, dict):
            state = {}
        relationship_path = self.root / "knowledge" / "relationships.yaml"
        relationships = _read_yaml(relationship_path, {"schema_version": 1, "relationships": []})
        if not isinstance(relationships, dict):
            relationships = {"schema_version": 1, "relationships": []}
        rows = relationships.setdefault("relationships", [])
        if not isinstance(rows, list):
            raise DeliveryValidationError("knowledge/relationships.yaml has an invalid relationships list")

        staged: dict[Path, str] = {}
        created_ids: list[str] = []
        updated_ids: list[str] = []
        for operation in delivery["operations"]:
            capability = operation["capability"]
            if capability == "garden.add-transcription":
                artifact_ref = str(operation["artifact_ref"])
                body = _inside(directory, artifact_ref).read_text(encoding="utf-8", errors="replace")
                transcription_id = f"transcription-{target_id}"
                destination = self.root / "knowledge" / "garden" / "transcriptions" / f"{target_id}.md"
                staged[destination] = (
                    "---\n"
                    f"id: {transcription_id}\n"
                    "type: garden-transcription\n"
                    f"garden_entry_id: {target_id}\n"
                    "provenance: ai-derived\n"
                    f"request_id: {request['id']}\n"
                    f"delivery_id: {delivery_id}\n"
                    "---\n\n" + body.rstrip() + "\n"
                )
                state["transcription_path"] = destination.relative_to(self.root).as_posix()
                created_ids.append(transcription_id)
            elif capability == "garden.update":
                patch = operation.get("patch") or {}
                if not isinstance(patch, dict):
                    raise DeliveryValidationError("garden.update patch must be a mapping")
                illegal = set(patch) - {"title", "state"}
                if illegal:
                    raise DeliveryValidationError(
                        f"garden.update contains forbidden fields: {sorted(illegal)}"
                    )
                state.update(patch)
            elif capability == "relationship.create":
                payload = operation.get("payload") or {}
                relation_id = str(payload.get("id") or f"relationship-{uuid4().hex[:12]}")
                relation = {
                    "id": relation_id,
                    "from": payload.get("from"),
                    "relation": payload.get("relation"),
                    "to": payload.get("to"),
                    "provenance": {
                        "source": "ai-action",
                        "request_id": request["id"],
                        "delivery_id": delivery_id,
                    },
                }
                if not isinstance(relation["from"], dict) or not isinstance(relation["to"], dict):
                    raise DeliveryValidationError("relationship endpoints must be mappings")
                if not relation["relation"] or not relation["from"].get("id") or not relation["to"].get("id"):
                    raise DeliveryValidationError("relationship requires from, relation, and to identifiers")
                if not any(isinstance(row, dict) and row.get("id") == relation_id for row in rows):
                    rows.append(relation)
                    created_ids.append(relation_id)
            else:
                raise DeliveryValidationError(f"unsupported pilot capability: {capability}")

        state.update({
            "schema_version": 1,
            "id": target_id,
            "type": "garden-ai-state",
            "source_path": target["path"],
            "source_revision": target["revision"],
            "revision": int(state.get("revision", 0)) + 1,
            "last_ai_request_id": request["id"],
        })
        staged[state_path] = _dump_yaml(state)
        if rows:
            staged[relationship_path] = _dump_yaml(relationships)
        updated_ids.append(target_id)

        transaction_id = f"transaction-{self.clock():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
        receipt_path = self.repository.receipts / f"{transaction_id}.yaml"
        request_path = self.repository.request_path(str(request["id"]))
        all_destinations = [*staged, request_path, receipt_path]
        backups: dict[Path, bytes | None] = {
            path: path.read_bytes() if path.is_file() else None for path in all_destinations
        }
        lock_path = self.repository.base / ".apply.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd: int | None = None
        pre_snapshot = _snapshot(self.root)
        if pre_snapshot != request["preconditions"]["snapshot_id"]:
            raise StaleDeliveryError("repository changed before transaction application")
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            for path, content in staged.items():
                _atomic_text(path, content)

            from learning_os.loader import load_repo
            from learning_os.rules import validate
            errors = [issue for issue in validate(load_repo(self.root), online=False)
                      if issue.severity == "E"]
            if errors:
                detail = "; ".join(f"{issue.code}: {issue.message}" for issue in errors[:8])
                raise DeliveryValidationError(f"delivery creates invalid repository state: {detail}")

            post_snapshot = _snapshot(self.root)
            receipt = {
                "schema_version": 1,
                "id": transaction_id,
                "type": "transaction-receipt",
                "request_id": request["id"],
                "delivery_id": delivery_id,
                "action_id": request["action_id"],
                "status": "committed",
                "pre_snapshot": pre_snapshot,
                "post_snapshot": post_snapshot,
                "created_ids": created_ids,
                "updated_ids": updated_ids,
                "deleted_ids": [],
                "validation": {
                    "schemas": "passed",
                    "references": "passed",
                    "boundaries": "passed",
                    "projection": "passed",
                },
                "committed_at": _iso(self.clock()),
            }
            request["status"] = "completed"
            request["receipt_id"] = transaction_id
            _atomic_text(request_path, _dump_yaml(request))
            _atomic_text(receipt_path, _dump_yaml(receipt))

            from learning_os.genout import generate_all, write_outputs
            repo = load_repo(self.root)
            write_outputs(repo, generate_all(repo))
            return {**receipt, "touched_paths": [
                path.relative_to(self.root).as_posix() for path in all_destinations
            ]}
        except Exception:
            for path, old in backups.items():
                try:
                    if old is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(old)
                except OSError:
                    pass
            with contextlib.suppress(Exception):
                from learning_os.genout import generate_all, write_outputs
                from learning_os.loader import load_repo
                repo = load_repo(self.root)
                write_outputs(repo, generate_all(repo))
            raise
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
            lock_path.unlink(missing_ok=True)

    def request_status(self, request_id: str) -> dict[str, Any]:
        request = self.repository.get_request(request_id)
        return {
            "id": request["id"],
            "action_id": request["action_id"],
            "target": request["target"],
            "provider": request["provider"]["preferred"],
            "status": request["status"],
            "created_at": request["created_at"],
            "delivery_id": request.get("delivery_id"),
            "receipt_id": request.get("receipt_id"),
            "bundle_path": self.repository.request_dir(request_id).relative_to(self.root).as_posix(),
        }

    def manifest_projection(self) -> dict[str, Any]:
        return {
            "garden_entries": self.list_garden_targets(),
            "ai_actions": {
                "contract_version": 1,
                "available": self.list_actions(),
                "provider_adapters": [
                    {"id": "manual-bundle", "available": True},
                    {"id": "claude", "available": False},
                    {"id": "chatgpt", "available": False},
                ],
                "requests": self.repository.request_projections(),
            },
        }


def manifest_ai_projection(root: Path) -> dict[str, Any]:
    """Best-effort additive projection; a missing optional subsystem stays empty."""
    try:
        return AIActionService(root).manifest_projection()
    except (OSError, ValueError, yaml.YAMLError, AIActionError):
        return {
            "garden_entries": [],
            "ai_actions": {
                "contract_version": 1,
                "available": [],
                "provider_adapters": [{"id": "manual-bundle", "available": True}],
                "requests": [],
            },
        }
