"""The bounded AI action workflow: prepare, import, validate, apply."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import yaml

from learning_os.contracts.capability_catalog import (
    domain_capability_definitions,
    load_capability_catalog,
)
from learning_os.contracts.gateway import current_gateway_request
from learning_os.contracts.manifest_contract import declared_version
from learning_os.contracts.write_scopes import WriteScopeError, require_write_scope
from learning_os.garden import project_garden_entries
from learning_os.loader import load_repo
from learning_os.material_synthesis import (
    current_unit_material_basis,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.transactions import (
    TransactionConflict,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionService,
    artifact_revision,
    replay_for_request,
)

from .errors import (
    ActionPolicyError,
    DeliveryValidationError,
    StaleDeliveryError,
    TargetNotFoundError,
)
from .registry import ActionRegistry, AdapterRegistry
from .storage import FilesystemAIActionRepository
from .support import (
    Clock,
    _dump_yaml,
    _inside,
    _iso,
    _now_utc,
    _projection,
    _read_yaml,
    _sha256_bytes,
    _sha256_file,
    _snapshot,
    parse_frontmatter_request_id,
)
from .types import (
    AIActionRequest,
    ApplyDeliveryResult,
    DeliveryRecord,
    DeliveryValidationResult,
    GardenTarget,
    OriginalArtifact,
    RequestStatus,
    ValidatedDelivery,
)


def read_bound_delivery(
    directory: Path,
    *,
    delivery_sha256: str,
    artifact_sha256: dict[str, Any],
) -> tuple[DeliveryRecord, dict[str, bytes]]:
    """Read and verify the exact bytes named by an approved V2 payload.

    A free function (not a method) so replay evidence verification
    (``transactions.replay_for_request``) can re-derive exactly the same
    hash-bound delivery evidence a live ``apply_delivery`` call would, without
    duplicating the binding logic or needing a full ``AIActionService``.
    """
    expected_delivery = AIActionService._validated_sha256(
        delivery_sha256, label="delivery_sha256"
    )
    delivery_path = directory / "delivery.yaml"
    if not delivery_path.is_file() or delivery_path.is_symlink():
        raise DeliveryValidationError(
            "approved delivery record is missing or is not a regular file"
        )
    try:
        delivery_bytes = delivery_path.read_bytes()
    except OSError as exc:
        raise DeliveryValidationError(
            f"approved delivery record is unreadable: {exc}"
        ) from exc
    if _sha256_bytes(delivery_bytes) != expected_delivery:
        raise DeliveryValidationError(
            "approved delivery content hash does not match the imported delivery record"
        )
    try:
        delivery = yaml.safe_load(delivery_bytes.decode("utf-8", errors="strict"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise DeliveryValidationError(
            f"approved delivery record is unreadable: {exc}"
        ) from exc
    if not isinstance(delivery, dict):
        raise DeliveryValidationError("delivery.yaml must contain a mapping")

    operations = delivery.get("operations")
    if not isinstance(operations, list):
        raise DeliveryValidationError("delivery operations must be a list")
    refs: set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict):
            raise DeliveryValidationError("each delivery operation must be a mapping")
        artifact_ref = operation.get("artifact_ref")
        if artifact_ref is not None:
            if not isinstance(artifact_ref, str) or not artifact_ref:
                raise DeliveryValidationError(
                    "delivery artifact_ref must be a non-empty relative path"
                )
            refs.add(artifact_ref)
    if not isinstance(artifact_sha256, dict):
        raise DeliveryValidationError("artifact_sha256 must be an object")
    if any(not isinstance(key, str) or not key for key in artifact_sha256):
        raise DeliveryValidationError(
            "artifact_sha256 keys must be non-empty artifact_ref strings"
        )
    supplied = set(artifact_sha256)
    if supplied != refs:
        raise DeliveryValidationError(
            "approved delivery artifact hashes must bind exactly every artifact_ref "
            f"(missing={sorted(refs - supplied)}, unexpected={sorted(supplied - refs)})"
        )
    artifacts: dict[str, bytes] = {}
    for artifact_ref in sorted(refs):
        expected = AIActionService._validated_sha256(
            artifact_sha256[artifact_ref],
            label=f"artifact_sha256[{artifact_ref}]",
        )
        artifact = _inside(directory, artifact_ref)
        if not artifact.is_file() or artifact.is_symlink():
            raise DeliveryValidationError(
                f"approved delivery artifact is missing or is not a regular file: {artifact_ref}"
            )
        try:
            content = artifact.read_bytes()
        except OSError as exc:
            raise DeliveryValidationError(
                f"approved delivery artifact is unreadable: {artifact_ref}: {exc}"
            ) from exc
        if _sha256_bytes(content) != expected:
            raise DeliveryValidationError(
                "approved delivery artifact content hash does not match "
                f"the imported bytes: {artifact_ref}"
            )
        artifacts[artifact_ref] = content
    return cast(DeliveryRecord, delivery), artifacts


class AIActionService:
    """Bounded gateway for AI-proposed canonical writes.

    Concurrency: callers are responsible for holding the repository operator
    lock (``tools/los.py`` takes it around every mutating command).  The service
    deliberately does not take a second lock of its own — a bespoke
    ``O_CREAT|O_EXCL`` lockfile survives a crash and would wedge every later
    transaction behind a stale file.
    """

    def __init__(self, root: Path, *, clock: Clock = _now_utc):
        self.root = root.resolve()
        self.clock = clock
        self.contracts = self.root / "system" / "contracts"
        self.registry = ActionRegistry(self.contracts / "ai-actions")
        self.adapters = AdapterRegistry(self.contracts / "ai-adapters.yaml")
        self.repository = FilesystemAIActionRepository(self.root)

    def list_actions(self) -> list[dict[str, Any]]:
        return [action.project() for action in self.registry.list()]

    def capability_definitions(self):
        """Validated AI-domain declarations from the one capability catalogue."""
        return domain_capability_definitions(self.root)

    def capability_writes(self) -> dict[str, tuple[str, ...]]:
        """Declared write scopes, keyed by capability.

        The operating contract requires a *post-action scope check* on every
        gateway write (CLAUDE.md hard rule 12).  The allowlist is read from
        ``system/contracts/capabilities.yaml`` so the contract and the code
        cannot drift apart silently.
        """
        return {
            name: definition.writes
            for name, definition in self.capability_definitions().items()
        }

    def _assert_in_scope(self, capability: str, path: Path,
                         scopes: dict[str, tuple[str, ...]] | None = None) -> None:
        rel = path.relative_to(self.root).as_posix()
        allowed = (scopes if scopes is not None else self.capability_writes()).get(capability, ())
        if not allowed:
            raise DeliveryValidationError(
                f"capability {capability} declares no write scope; refusing to write {rel}"
            )
        try:
            require_write_scope(capability, rel, allowed)
        except WriteScopeError as exc:
            raise DeliveryValidationError(
                f"{exc} (declared scope: {', '.join(allowed)})"
            ) from exc

    @staticmethod
    def _validated_sha256(value: Any, *, label: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(
            r"sha256:[a-f0-9]{64}", value
        ):
            raise DeliveryValidationError(
                f"{label} must be sha256 followed by 64 lowercase hexadecimal digits"
            )
        return value

    def _bound_delivery_content(
        self,
        directory: Path,
        *,
        delivery_sha256: str,
        artifact_sha256: dict[str, Any],
    ) -> tuple[DeliveryRecord, dict[str, bytes]]:
        """Read and verify the exact bytes named by an approved V2 payload."""
        return read_bound_delivery(
            directory, delivery_sha256=delivery_sha256, artifact_sha256=artifact_sha256,
        )

    def _apply_result(
        self,
        result,
        *,
        touched_paths: list[Path],
    ) -> ApplyDeliveryResult:
        receipt = _read_yaml(result.receipt_path)
        if not isinstance(receipt, dict):  # pragma: no cover - commit guarantees this
            raise DeliveryValidationError(
                "transaction committed without a readable receipt"
            )
        return cast(ApplyDeliveryResult, {
            **receipt,
            "transaction_id": result.transaction_id,
            "revision_updates": dict(result.revisions),
            "receipt_path": result.receipt_path.relative_to(self.root).as_posix(),
            "replayed": bool(result.replayed),
            "touched_paths": [
                path.relative_to(self.root).as_posix() for path in touched_paths
            ],
        })

    def list_garden_targets(self) -> list[dict[str, Any]]:
        """Use the same Garden projection every other Core consumer uses."""
        return project_garden_entries(load_repo(self.root))

    def _target(self, target_id: str, target_kind: str = "garden-note") -> tuple[GardenTarget, Path]:
        if target_kind == "unit":
            repo = load_repo(self.root)
            unit = repo.units.get(target_id)
            if unit is None:
                raise TargetNotFoundError(f"Unit target not found: {target_id}")
            return cast(GardenTarget, {
                "id": unit.id,
                "type": "unit",
                "title": unit.data.get("title", unit.id),
                "path": unit.path.relative_to(self.root).as_posix(),
                "state": unit.data.get("status", "unknown"),
                "tags": [],
                "revision": artifact_revision(self.root, unit.id),
            }), unit.path
        for row in self.list_garden_targets():
            if row["id"] == target_id:
                target = cast(GardenTarget, row)
                return target, self.root / target["path"]
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
    ) -> AIActionRequest:
        action = self.registry.get(action_id)
        if target_kind not in action.target_kinds:
            raise ActionPolicyError(f"action {action_id} does not support target kind {target_kind}")
        if action.status != "implemented":
            raise ActionPolicyError(
                f"action {action_id} is declared {action.status}; no request was prepared"
            )
        if provider not in action.supported_providers:
            raise ActionPolicyError(f"provider {provider} is not supported for action {action_id}")
        # The core, not the interface, decides whether a provider can be served.
        adapter = self.adapters.resolve(provider)
        if action.interaction_mode not in adapter.supported_modes:
            raise ActionPolicyError(
                f"adapter {adapter.id} does not support {action.interaction_mode} mode"
            )
        target, source = self._target(target_id, target_kind)
        snapshot = _snapshot(self.root)
        if expected_snapshot and expected_snapshot != snapshot:
            raise StaleDeliveryError(
                f"expected snapshot {expected_snapshot}, current snapshot is {snapshot}"
            )
        now = self.clock()
        request_id = request_id or f"ai-request-{now:%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
        original: OriginalArtifact = {
            "id": f"original-{target_id}",
            "canonical_path": target["path"],
            "bundle_path": f"attachments/{source.name}",
            "checksum": _sha256_file(source),
            "media_type": "text/markdown",
        }
        request: AIActionRequest = {
            "schema_version": 1,
            "id": request_id,
            "type": "ai-action-request",
            "action_id": action.id,
            "status": "prepared",
            "target": {"kind": target_kind, "id": target_id},
            "provider": {"preferred": provider, "adapter": adapter.id},
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
                "external_repository_access": False,
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
                "relationship_registry": "operations/ai-actions/relationships.yaml",
            },
        }
        instructions = (
            "# Shelve with AI\n\n"
            "Discuss this bounded Garden seed with the user. Preserve the original file "
            "unchanged. Keep transcription distinct from synthesis. Return an approved "
            "delivery directory containing `delivery.yaml`; use only capabilities listed "
            "in `allowed-capabilities.json`. Do not request or read external repositories.\n"
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
                "capability_contract_version": load_capability_catalog(self.root)[
                    "contract_version"
                ],
                "manifest_contract_version": declared_version(self.root),
                "action_registry_schema_version": 1,
            }, indent=2) + "\n").encode("utf-8"),
            original["bundle_path"]: source.read_bytes(),
        }
        if action.id == "unit.compare-materials":
            repo = load_repo(self.root)
            unit = repo.units[target_id]
            source_map_path = repo.module_source_map_origins.get(unit.module_id)
            source_map = repo.module_source_maps.get(unit.module_id) or {}
            routes = []
            for source_row in source_map.get("sources", []) or []:
                if not isinstance(source_row, dict):
                    continue
                for route in source_row.get("unit_routes", []) or []:
                    if isinstance(route, dict) and route.get("unit_id") == target_id:
                        routes.append({**route, "source_id": source_row.get("source_id")})
            request["context"] = {
                "artifact_ids": [target_id, *[str(row.get("id")) for row in routes]],
                "attachment_ids": [original["id"]],
                "originals": [original],
            }
            context = {
                "target": {k: target[k] for k in
                           ("id", "type", "title", "path", "state", "revision")},
                "knowledge_map": unit.data.get("knowledge_map"),
                "related_module_ids": unit.data.get("related_module_ids", []),
                "artifacts": unit.data.get("artifacts", {}),
                "routes": routes,
                "basis": current_unit_material_basis(self.root, target_id),
                "policy": {
                    "all_routes_listed": True,
                    "deep_scopes": ["current", "prerequisite"],
                    "other_statuses": ["screened", "unevaluated", "unavailable"],
                    "numeric_scores": False,
                    "study_order": False,
                    "time_recommendations": False,
                    "standalone_lesson": False,
                },
            }
            instructions = (
                "# Compare one unit's materials\n\n"
                "Work only from the explicitly listed local routes. List every route. "
                "Deep-review current and prerequisite routes; label all others honestly. Use "
                "qualitative evidence-bearing comparisons only. Do not score, order, schedule, "
                "upload, create sources, create concepts, or write a standalone lesson. Return "
                "one whole approved `unit-material-synthesis.schema.json` record as an artifact "
                "for capability `unit.material-synthesis.publish`.\n"
            )
            bundle_files["instructions.md"] = instructions.encode("utf-8")
            bundle_files["context.md"] = (
                "# Bounded unit context\n\n```json\n"
                + json.dumps(context, indent=2, ensure_ascii=False)
                + "\n```\n"
            ).encode("utf-8")
            if source_map_path is not None and source_map_path.is_file():
                bundle_files["attachments/source-map.yaml"] = source_map_path.read_bytes()
        self.repository.save_request(request, bundle_files)
        return request

    def import_delivery(self, source: Path) -> DeliveryRecord:
        delivery, staged = self.repository.stage_delivery_directory(source)
        delivery_id = str(delivery.get("id", ""))
        try:
            self._validate(delivery, staged)
        except Exception:
            shutil.rmtree(staged.parent, ignore_errors=True)
            raise
        request = self.repository.get_request(str(delivery["request_id"]))
        request["status"] = "delivery-ready"
        request["delivery_id"] = delivery_id
        self.repository.commit_delivery_import(staged, delivery_id, request)
        return delivery

    def validate_delivery(self, delivery_id: str) -> DeliveryValidationResult:
        delivery, directory = self.repository.get_delivery(delivery_id)
        outcome = self._validate(delivery, directory)
        return {"ok": True, "delivery_id": outcome.delivery_id,
                "request_id": outcome.request_id}

    def _validate(self, delivery: DeliveryRecord, directory: Path) -> ValidatedDelivery:
        delivery_id = str(delivery.get("id", ""))
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
        # Staleness is scoped to what the delivery actually reasoned about.  The
        # repository-wide fingerprint is provenance, not a gate: rejecting a
        # delivery because an unrelated note moved (feature specification §20.4
        # scopes staleness to *the target*) makes the workflow unusable in a
        # live repository and tempts users to re-prepare blindly.
        target = self._assert_target_unchanged(request)
        return ValidatedDelivery(
            delivery_id=delivery_id,
            request_id=request["id"],
            request=request,
            target=target,
        )

    def _assert_target_unchanged(self, request: AIActionRequest) -> GardenTarget:
        """Re-read the target, refuse if it moved, and hand back the fresh row.

        Returning the row is what lets callers stop re-walking the Garden tree:
        the read has to happen anyway for the guard to mean anything.
        """
        target_id = str((request.get("target") or {}).get("id", ""))
        target_kind = str((request.get("target") or {}).get("kind", "garden-note"))
        target, _ = self._target(target_id, target_kind)
        expected_revision = (request.get("preconditions") or {}).get(
            "artifact_revisions", {}).get(target_id)
        if target.get("revision") != expected_revision:
            raise StaleDeliveryError("Garden target changed after request preparation")
        for original in (request.get("context") or {}).get("originals", []):
            path = _inside(self.root, str(original["canonical_path"]))
            if not path.is_file() or _sha256_file(path) != original.get("checksum"):
                raise DeliveryValidationError("original artifact changed after request preparation")
        return target

    def apply_delivery(
        self,
        delivery_id: str,
        *,
        delivery_sha256: str,
        artifact_sha256: dict[str, Any],
        expected_snapshot: str,
        expected_revisions: dict[str, int],
    ) -> ApplyDeliveryResult:
        authority = current_gateway_request()
        if authority is None or authority.capability != "ai-action.delivery.apply" \
                or authority.approval_kind != "approved-delivery":
            raise DeliveryValidationError(
                "approved delivery application requires GatewayEnvelopeV2 "
                "approved-delivery authority"
            )
        directory = self.repository.delivery_dir(delivery_id)
        delivery, bound_artifacts = self._bound_delivery_content(
            directory,
            delivery_sha256=delivery_sha256,
            artifact_sha256=artifact_sha256,
        )
        if delivery.get("id") != delivery_id:
            raise DeliveryValidationError(
                "approved delivery id does not match its imported directory"
            )
        try:
            replay = replay_for_request(self.root, authority)
        except TransactionIdempotencyConflict as exc:
            raise DeliveryValidationError(f"delivery idempotency conflict: {exc}") from exc
        except TransactionFailure as exc:
            raise DeliveryValidationError(f"delivery replay failed: {exc}") from exc
        if replay is not None:
            return self._apply_result(replay, touched_paths=[])

        expected_snapshot = self._validated_sha256(
            expected_snapshot, label="expected_snapshot"
        )
        actual_snapshot = _snapshot(self.root)
        if expected_snapshot != actual_snapshot:
            raise StaleDeliveryError(
                "approved delivery snapshot conflict "
                f"(expected {expected_snapshot}, actual {actual_snapshot})"
            )
        # Validation already read the delivery, the request and the target; reuse
        # them rather than parsing the same three files a second time.
        outcome = self._validate(delivery, directory)
        request = outcome.request
        target = outcome.target
        capability_definitions = self.capability_definitions()
        target_id = str(request["target"]["id"])
        is_unit_synthesis = request.get("action_id") == "unit.compare-materials"
        state_path = self.repository.state_path(target_id)
        state = _read_yaml(state_path, {})
        if not isinstance(state, dict):
            state = {}
        relationship_path = self.root / "operations" / "ai-actions" / "relationships.yaml"
        relationships = _read_yaml(relationship_path, {"schema_version": 1, "relationships": []})
        if not isinstance(relationships, dict):
            relationships = {"schema_version": 1, "relationships": []}
        rows = relationships.setdefault("relationships", [])
        if not isinstance(rows, list):
            raise DeliveryValidationError("operations/ai-actions/relationships.yaml has an invalid relationships list")

        # path -> (content, the capability that authorised writing it)
        staged: dict[Path, tuple[str, str]] = {}
        created_ids: list[str] = []
        updated_ids: list[str] = []
        superseded_ids: list[str] = []
        relations_added = False
        for operation in delivery["operations"]:
            capability = operation["capability"]
            if capability == "garden.add-transcription":
                artifact_ref = str(operation["artifact_ref"])
                body = bound_artifacts[artifact_ref].decode("utf-8", errors="replace")
                transcription_id = f"transcription-{target_id}"
                destination = self.root / "knowledge" / "garden" / "transcriptions" / f"{target_id}.md"
                # Re-shelving must not quietly discard an earlier AI reading of
                # the same seed: superseding is an explicit, receipted act.
                if destination.is_file():
                    previous = parse_frontmatter_request_id(destination)
                    if operation.get("supersedes") != transcription_id:
                        raise DeliveryValidationError(
                            f"a transcription for {target_id} already exists"
                            + (f" (from request {previous})" if previous else "")
                            + f"; set supersedes: {transcription_id} to replace it"
                        )
                    superseded_ids.append(transcription_id)
                staged[destination] = ((
                    "---\n"
                    f"id: {transcription_id}\n"
                    "type: garden-transcription\n"
                    f"garden_entry_id: {target_id}\n"
                    "provenance: ai-derived\n"
                    f"request_id: {request['id']}\n"
                    f"delivery_id: {delivery_id}\n"
                    "---\n\n" + body.rstrip() + "\n"
                ), capability)
                state["transcription_path"] = destination.relative_to(self.root).as_posix()
                created_ids.append(transcription_id)
            elif capability == "garden.update":
                patch = operation.get("patch") or {}
                if not isinstance(patch, dict):
                    raise DeliveryValidationError("garden.update patch must be a mapping")
                allowed_fields = set(capability_definitions[capability].allowed_fields)
                illegal = set(patch) - allowed_fields
                if illegal:
                    raise DeliveryValidationError(
                        f"garden.update contains forbidden fields: {sorted(illegal)}"
                    )
                state.update(patch)
            elif capability == "relationship.create":
                payload = operation.get("payload") or {}
                if not payload.get("id"):
                    raise DeliveryValidationError(
                        "relationship.create in an approved delivery requires a stable id"
                    )
                relation_id = str(payload["id"])
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
                    relations_added = True
            elif capability == "unit.material-synthesis.publish":
                artifact_ref = str(operation.get("artifact_ref", ""))
                if not artifact_ref:
                    raise DeliveryValidationError(
                        "unit.material-synthesis.publish requires artifact_ref"
                    )
                try:
                    synthesis = yaml.safe_load(
                        bound_artifacts[artifact_ref].decode("utf-8", errors="strict")
                    )
                except (UnicodeError, yaml.YAMLError) as exc:
                    raise DeliveryValidationError(
                        f"material synthesis artifact is unreadable: {exc}"
                    ) from exc
                if not isinstance(synthesis, dict):
                    raise DeliveryValidationError("material synthesis artifact must be an object")
                try:
                    validate_unit_material_synthesis(self.root, target_id, synthesis)
                except ValueError as exc:
                    raise DeliveryValidationError(str(exc)) from exc
                provenance = (synthesis.get("basis") or {}).get("ai_provenance") or {}
                expected_provider = (request.get("provider") or {}).get("preferred")
                if provenance != {
                    "request_id": request["id"],
                    "delivery_id": delivery_id,
                    "provider": expected_provider,
                }:
                    raise DeliveryValidationError(
                        "material synthesis provenance does not match its approved delivery"
                    )
                destination = synthesis_destination(self.root, target_id)
                if destination.is_file() and operation.get("supersedes") != synthesis.get("id"):
                    raise DeliveryValidationError(
                        f"a dossier for {target_id} already exists; explicit supersedes is required"
                    )
                staged[destination] = (_dump_yaml(synthesis), capability)
                (updated_ids if destination.is_file() else created_ids).append(synthesis["id"])
            else:
                raise DeliveryValidationError(f"unsupported pilot capability: {capability}")

        if not is_unit_synthesis:
            state.update({
                "schema_version": 1,
                "id": target_id,
                "type": "garden-ai-state",
                "source_path": target["path"],
                "source_revision": target["revision"],
                "revision": int(state.get("revision", 0)) + 1,
                "last_ai_request_id": request["id"],
            })
            staged[state_path] = (_dump_yaml(state), "garden.update")
        # Only rewrite the AI-action relationship registry when this delivery
        # actually added a relation — re-serialising an untouched file would
        # reformat the user's own YAML for nothing.
        if relations_added:
            staged[relationship_path] = (_dump_yaml(relationships), "relationship.create")
        updated_ids.append(target_id)

        # Post-action scope check (operating contract, hard rule 12): every
        # canonical destination must fall inside the write scope its capability
        # declares in system/contracts/capabilities.yaml.
        scopes = {
            name: definition.writes
            for name, definition in capability_definitions.items()
        }
        for path, (_content, capability) in staged.items():
            self._assert_in_scope(capability, path, scopes)

        request_path = self.repository.request_path(str(request["id"]))
        # Re-check the *target*, not the whole repository, immediately before the
        # write window; unrelated concurrent edits are not this delivery's
        # business, a changed target is.
        self._assert_target_unchanged(request)

        # The delivery directory is exchange state and can be edited outside the
        # canonical transaction engine. Re-hash it at the last possible point,
        # inside the operator lock and immediately before the atomic commit.
        final_delivery, final_artifacts = self._bound_delivery_content(
            directory,
            delivery_sha256=delivery_sha256,
            artifact_sha256=artifact_sha256,
        )
        if final_delivery != delivery or final_artifacts != bound_artifacts:
            raise DeliveryValidationError(
                "approved delivery bytes changed while application was being prepared"
            )
        actual_snapshot = _snapshot(self.root)
        if expected_snapshot != actual_snapshot:
            raise StaleDeliveryError(
                "approved delivery snapshot changed before commit "
                f"(expected {expected_snapshot}, actual {actual_snapshot})"
            )

        def request_write(transaction_id: str) -> dict[Path, str]:
            completed = dict(request)
            completed["status"] = "completed"
            completed["receipt_id"] = transaction_id
            return {request_path: _dump_yaml(completed)}

        validated_repo = None

        def validation_errors() -> list:
            nonlocal validated_repo
            from learning_os.rules import validate

            validated_repo = load_repo(self.root)
            return [
                issue for issue in validate(validated_repo, online=False)
                if issue.severity == "E"
            ]

        def publish() -> None:
            nonlocal validated_repo
            from learning_os.genout import generate_all, write_outputs

            repo = validated_repo or load_repo(self.root)
            validated_repo = None
            write_outputs(repo, generate_all(repo))

        def rollback_publish() -> None:
            from learning_os.genout import generate_all, write_outputs

            repo = load_repo(self.root)
            write_outputs(repo, generate_all(repo))

        metadata = {
            "request_id": request["id"],
            "delivery_id": delivery_id,
            "action_id": request["action_id"],
            "approved_delivery": {
                "delivery_sha256": delivery_sha256,
                "artifact_sha256": {
                    key: artifact_sha256[key] for key in sorted(artifact_sha256)
                },
            },
            "created_ids": created_ids,
            "updated_ids": updated_ids,
            "deleted_ids": [],
            "superseded_ids": superseded_ids,
            "validation": {
                "schemas": "passed",
                "references": "passed",
                "boundaries": "passed",
                "projection": "passed",
            },
        }
        try:
            result = TransactionService(self.root, clock=self.clock).commit(
                capability="ai-action.delivery.apply",
                writes={path: content for path, (content, _capability) in staged.items()},
                artifact_ids={*created_ids, *updated_ids, *superseded_ids},
                expected_revisions=expected_revisions,
                validate_state=validation_errors,
                publish=publish,
                rollback_publish=rollback_publish,
                metadata=metadata,
                transaction_writes=request_write,
                write_authorities={
                    **{
                        path: domain_capability
                        for path, (_content, domain_capability) in staged.items()
                    },
                    request_path: "ai-action.delivery.apply",
                },
            )
        except TransactionConflict as exc:
            raise StaleDeliveryError(str(exc)) from exc
        except TransactionIdempotencyConflict as exc:
            raise DeliveryValidationError(f"delivery idempotency conflict: {exc}") from exc
        except TransactionFailure as exc:
            raise DeliveryValidationError(f"delivery transaction failed: {exc}") from exc
        return self._apply_result(
            result,
            touched_paths=(
                [] if result.replayed
                else [*staged, request_path, result.receipt_path]
            ),
        )

    def request_status(self, request_id: str) -> RequestStatus:
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
        return _projection(
            garden_entries=self.list_garden_targets(),
            available=self.list_actions(),
            adapters=[a.project() for a in self.adapters.list()],
            requests=self.repository.request_projections(),
        )
