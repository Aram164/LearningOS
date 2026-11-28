"""The bounded AI action workflow: prepare, import, validate, apply."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import yaml

from learning_os.app.proposal import TransactionProposal
from learning_os.derive.garden import project_garden_entries
from learning_os.derive.material_synthesis import (
    current_unit_material_basis,
    inspected_material_by_route,
    publication_lineage,
    resolve_route_provenance,
    synthesis_destination,
    synthesis_route_ids,
    validate_synthesis_page_provenance,
    validate_unit_material_synthesis,
)
from learning_os.derive.semantics.lineage import LEDGER_RELATIVE
from learning_os.domain.ai_errors import (
    ActionPolicyError,
    AIActionError,
    ConceptNotFound,
    ContinuationRefusedError,
    DeliveryAlreadyExists,
    DeliveryBindingError,
    DeliveryIdempotencyConflict,
    DeliveryRevisionConflict,
    DeliveryScopeError,
    DeliveryValidationError,
    RouteNotFound,
    StaleDeliveryError,
    TargetNotFound,
    TargetNotFoundError,
    UnresolvedMaterialError,
)
from learning_os.domain.ai_types import (
    AIActionRequest,
    ApplyDeliveryResult,
    DeliveryRecord,
    DeliveryValidationResult,
    GardenTarget,
    OriginalArtifact,
    RequestStatus,
    ValidatedDelivery,
)
from learning_os.domain.failures import (
    PostCommitFailure,
    ProjectionFailure,
    TransactionConflict,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionPublicationUncertain,
    TransactionRollbackIncomplete,
    TransactionSnapshotConflict,
)
from learning_os.store import observations
from learning_os.store.ai_actions.binding import (
    read_bound_delivery,
    read_delivery_for_preview,
    validated_sha256,
)
from learning_os.store.ai_actions.registry import ActionRegistry, AdapterRegistry
from learning_os.store.ai_actions.storage import FilesystemAIActionRepository
from learning_os.store.ai_actions.support import (
    REQUEST_ID_RE,
    Clock,
    check_request_id,
    parse_frontmatter_request_id,
)
from learning_os.store.ai_actions.support import dump_yaml as _dump_yaml
from learning_os.store.ai_actions.support import inside as _inside
from learning_os.store.ai_actions.support import iso as _iso
from learning_os.store.ai_actions.support import now_utc as _now_utc
from learning_os.store.ai_actions.support import read_yaml as _read_yaml
from learning_os.store.ai_actions.support import sha256_bytes as _sha256_bytes
from learning_os.store.ai_actions.support import sha256_file as _sha256_file
from learning_os.store.ai_actions.support import snapshot as _snapshot
from learning_os.store.contracts.capability_catalog import (
    domain_capability_definitions,
    load_capability_catalog,
)
from learning_os.store.contracts.gateway import (
    current_gateway_request,
    gateway_snapshot_is_verified,
)
from learning_os.store.contracts.manifest_contract import declared_version
from learning_os.store.contracts.write_scopes import (
    WriteScopeError,
    require_write_scope,
)
from learning_os.store.evidence import replay_for_request
from learning_os.store.fingerprint import source_fingerprint
from learning_os.store.loader import load_repo
from learning_os.store.materials.slices import (
    MAX_SLICE_BYTES_TOTAL,
    SLICE_BUNDLE_PREFIX,
    ContinuationError,
    SliceResolutionError,
    UnknownConceptIds,
    build_unit_slices,
    continuation_record_dict,
    plan_continuation,
    read_bundle_slice_index,
    slice_index_entry,
)
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import transaction_artifacts


#: Bundle name for the unit-scoped source-map read view. Deliberately not
#: the canonical filename: the view is a filtered projection for one unit,
#: never the module file.
@dataclass(frozen=True)
class _PlannedDeliveryApplication:
    """Side-effect-free staging plan shared by delivery preview and apply."""

    delivery_id: str
    request: AIActionRequest
    target: GardenTarget
    staged: dict[Path, tuple[str, str]]
    created_ids: list[str]
    updated_ids: list[str]
    superseded_ids: list[str]
    artifact_ids: list[str]
    request_path: Path
    touched_base: list[Path]


UNIT_SOURCE_MAP_VIEW_PATH = "attachments/unit-source-map.yaml"


def _scoped_source_ids(unit) -> set[str]:
    ids = set()
    for key in ("scope_sources", "source_selections"):
        for row in unit.data.get(key, []) or []:
            if isinstance(row, dict) and row.get("source_id"):
                ids.add(row["source_id"])
    return ids


def build_unit_source_map_view(*, source_map: dict, canonical_path: str,
                               canonical_bytes: bytes, unit,
                               target_id: str) -> tuple[bytes, dict[str, str]]:
    """One unit's filtered source-map read view plus its transport identity.

    Keeps the module identity and every parent source field, but replaces
    the target unit's route bodies with their ids: dict routes by unit_id
    plus legacy string entries naming the target become ``unit_route_ids``.
    Route bodies live once in the bundle's ``context.md`` routes; this view
    carries only parent metadata plus ids pointing there. Sources the
    unit's scope authority or selections name stay with an empty id list;
    every other unit's route is omitted. Returns (view_bytes, identity):
    the view's own checksum is a transport identity only, kept beside —
    never mixed with — the canonical file digest.
    """
    named = _scoped_source_ids(unit)
    sources = []
    included = omitted = 0
    for source_row in source_map.get("sources", []) or []:
        if not isinstance(source_row, dict):
            continue
        entries = source_row.get("unit_routes", [])
        if not isinstance(entries, list):
            entries = []
        kept = [entry for entry in entries
                if (isinstance(entry, dict) and entry.get("unit_id") == target_id)
                or (isinstance(entry, str) and entry == target_id)]
        included += len(kept)
        omitted += len(entries) - len(kept)
        if not kept and source_row.get("source_id") not in named:
            continue
        shaped = {key: value for key, value in source_row.items()
                  if key != "unit_routes"}
        shaped["unit_route_ids"] = [
            entry.get("id") if isinstance(entry, dict) else entry
            for entry in kept
        ]
        sources.append(shaped)
    view = {
        "view": {
            "kind": "unit-source-map-view",
            "canonical_path": canonical_path,
            "canonical_sha256": _sha256_bytes(canonical_bytes),
            "target_unit_id": target_id,
            "routes_included": included,
            "routes_omitted": omitted,
        },
        "module_id": source_map.get("module_id"),
        "sources": sources,
    }
    body = ("# Filtered read view: this unit's source-map slice only, not "
            "the canonical module file.\n"
            + _dump_yaml(view)).encode("utf-8")
    identity = {
        "bundle_path": UNIT_SOURCE_MAP_VIEW_PATH,
        "view_sha256": _sha256_bytes(body),
        "canonical_sha256": view["view"]["canonical_sha256"],
    }
    return body, identity


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
            raise DeliveryScopeError(
                f"capability {capability} declares no write scope; refusing to write {rel}"
            )
        try:
            require_write_scope(capability, rel, allowed)
        except WriteScopeError as exc:
            raise DeliveryScopeError(
                f"{exc} (declared scope: {', '.join(allowed)})"
            ) from exc

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

    def list_garden_targets(self, *, repo=None) -> list[dict[str, Any]]:
        """Use the same Garden projection every other Core consumer uses."""
        return project_garden_entries(load_repo(self.root) if repo is None else repo)

    def _target(self, target_id: str, target_kind: str = "garden-note", *, repo=None) -> tuple[GardenTarget, Path]:
        repo = load_repo(self.root) if repo is None else repo
        if target_kind == "unit":
            unit = repo.units.get(target_id)
            if unit is None:
                # Already loaded above ((cx) D-8).
                raise TargetNotFound(
                    "target", target_id, list(repo.units),
                    message=f"Unit target not found: {target_id}")
            return cast(GardenTarget, {
                "id": unit.id,
                "type": "unit",
                "title": unit.data.get("title", unit.id),
                "path": unit.path.relative_to(self.root).as_posix(),
                "state": unit.data.get("status", "unknown"),
                "tags": [],
                "revision": artifact_revision(self.root, unit.id),
            }), unit.path
        rows = self.list_garden_targets(repo=repo)
        for row in rows:
            if row["id"] == target_id:
                target = cast(GardenTarget, row)
                return target, self.root / target["path"]
        # Already loaded above ((cx) D-8).
        raise TargetNotFound(
            "target", target_id, [str(row["id"]) for row in rows],
            message=f"Garden target not found: {target_id}")

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
        if request_id is not None and REQUEST_ID_RE.fullmatch(str(request_id)) \
                and self.repository.request_dir(request_id).exists():
            return self._prepared_request_replay(
                request_id, action_id=action.id, target_kind=target_kind,
                target_id=target_id, provider=provider, adapter_id=adapter.id,
                expected_snapshot=expected_snapshot,
            )
        repo = load_repo(self.root)
        target, source = self._target(target_id, target_kind, repo=repo)
        snapshot = _snapshot(self.root)
        if expected_snapshot and expected_snapshot != snapshot:
            raise StaleDeliveryError(
                f"expected snapshot {expected_snapshot}, current snapshot is {snapshot}"
            )
        now = self.clock()
        if request_id is not None:
            # A caller-supplied id that the manifest cannot publish would be
            # persisted and then break every projection read (JF-08): refuse
            # before anything is written. The minted default matches by
            # construction.
            check_request_id(request_id)
        else:
            request_id = f"ai-request-{now:%Y%m%d-%H%M%S}-{observations.new_hex()[:6]}"
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
            basis = current_unit_material_basis(self.root, target_id, repo=repo)
            request["material_basis"] = basis
            try:
                slices = build_unit_slices(repo, routes, basis=basis)
            except SliceResolutionError as exc:
                raise UnresolvedMaterialError(f"{exc} No request was prepared.") from exc
            for slice_, body in slices:
                bundle_files[slice_.bundle_path] = body
            bundle_files[f"{SLICE_BUNDLE_PREFIX}/index.json"] = (
                json.dumps([slice_index_entry(slice_) for slice_, _ in slices],
                           indent=2) + "\n"
            ).encode("utf-8")
            context = {
                "target": {k: target[k] for k in
                           ("id", "type", "title", "path", "state", "revision")},
                "knowledge_map": unit.data.get("knowledge_map"),
                "related_module_ids": unit.data.get("related_module_ids", []),
                "artifacts": unit.data.get("artifacts", {}),
                "routes": routes,
                "basis": basis,
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
            if source_map_path is not None and source_map_path.is_file():
                canonical_bytes = source_map_path.read_bytes()
                if source_map_path.is_relative_to(self.root):
                    canonical_rel = source_map_path.relative_to(
                        self.root).as_posix()
                else:
                    canonical_rel = source_map_path.as_posix()
                view_body, view_identity = build_unit_source_map_view(
                    source_map=source_map, canonical_path=canonical_rel,
                    canonical_bytes=canonical_bytes, unit=unit,
                    target_id=target_id)
                bundle_files[UNIT_SOURCE_MAP_VIEW_PATH] = view_body
                context["source_map_view"] = view_identity
            instructions = (
                "# Compare one unit's materials\n\n"
                "Work only from the explicitly listed local routes. List every route. "
                "Deep-review current and prerequisite routes; label all others honestly. Use "
                "qualitative evidence-bearing comparisons only. Do not score, order, schedule, "
                "upload, create sources, create concepts, or write a standalone lesson. Return "
                "one whole approved `unit-material-synthesis.schema.json` record as an artifact "
                "for capability `unit.material-synthesis.publish`.\n"
                "\n"
                "Route bodies live once in context.md's routes. Parent source "
                "metadata for those routes is attached at "
                "attachments/unit-source-map.yaml — a filtered view of the module map "
                "for this unit only, never the canonical file — carrying "
                "unit_route_ids that point at context.md, never duplicate bodies. "
                "Request the full module map explicitly for a genuinely broader "
                "investigation.\n"
                "\n"
                "Material slices are attached under attachments/slices/<route-id>.md with an "
                "index at attachments/slices/index.json — one slice per deep-review route, "
                "nothing else was read. Judge the attached pages themselves: fill contribution, "
                "assumptions, notation, exercise_value, best_for and limitations from the slice "
                "text and cite exact slice pages in every evidence note (e.g. 'PDF pp. 386-393'). "
                "Every deep-reviewed assessment must also carry scope_of_absence: the exact "
                "pages this review had in front of it, in the same house style and naming "
                "every file (e.g. 'UE3.pdf, PDF pp. 15-38 of 54'). Copy it from the slice "
                "index; it is checked against the attachment exactly like evidence. "
                "evidence.checksum is always the material_checksum from the slice header — never "
                "the slice_sha256, which only proves the transport bytes of the extracted text. "
                "Every evidence item for a PDF route must cite the exact inspected pages in "
                "house style (e.g. 'PDF pp. 386-393'); evidence without exact page citations, "
                "or citing pages beyond the attachment, is rejected at publish. On routes "
                "binding several files, name the file in every evidence locator (e.g. "
                "'part-b.pdf, PDF pp. 21-23'); text-material evidence names its file and "
                "cites no pages. "
                "When a slice header reports truncation, record it in limitations; never claim "
                "pages beyond the attachment.\n"
                "\n"
                "When the attached pages cannot support a claim, do not guess and do not "
                "claim absence: absence from the inspected pages is never proof of absence "
                "from the source. Every negative sentence you write in contribution or "
                "limitations is read as bounded by scope_of_absence and by nothing wider, so "
                "write it that way: 'no worked solution in pp. 15-38', never 'no worked "
                "solution'. A published dossier once said a 54-page exercise set contained no "
                "sheet solution on the strength of 24 inspected pages; that claim ranged over "
                "30 pages nobody had opened. State the concrete evidence gap in the "
                "discussion — which "
                "concept, what kind of material is missing (concept-coverage, prerequisite, "
                "notation, derivation, example, exercise or limitation) and which exact pages "
                "should be read next. The operator may then attach a targeted continuation "
                "pass to this same request; passes stay small and bounded and stop after a "
                "few rounds. Request another pass only for a named gap; stop as soon as the "
                "evidence suffices, or record the point as not established from inspected "
                "material.\n"
            )
            bundle_files["instructions.md"] = instructions.encode("utf-8")
            bundle_files["context.md"] = (
                "# Bounded unit context\n\n```json\n"
                + json.dumps(context, indent=2, ensure_ascii=False)
                + "\n```\n"
            ).encode("utf-8")
        self.repository.save_request(request, bundle_files)
        return request

    def _prepared_request_replay(
        self,
        request_id: str,
        *,
        action_id: str,
        target_kind: str,
        target_id: str,
        provider: str,
        adapter_id: str,
        expected_snapshot: str | None,
    ) -> AIActionRequest:
        """Answer a retried prepare whose request id already committed (CL-03).

        The interface mints the id and records it before Core runs, so a lost
        response is retried with the same id. The committed request is returned
        unchanged, and nothing is written, only when it was prepared from the
        same action, target, provider and snapshot and its bundle is intact.
        Any difference is refused: an id never names two different intents.
        """
        path = self.repository.request_path(request_id)
        existing = _read_yaml(path) if path.is_file() else None
        if not isinstance(existing, dict):
            raise DeliveryValidationError(
                f"request already exists: {request_id}; its request.yaml is "
                "missing or unreadable, so it cannot be confirmed")
        request = cast(AIActionRequest, existing)
        differs = []
        if request.get("id") != request_id:
            differs.append("id")
        if request.get("action_id") != action_id:
            differs.append("action_id")
        if request.get("target") != {"kind": target_kind, "id": target_id}:
            differs.append("target")
        if request.get("provider") != {"preferred": provider, "adapter": adapter_id}:
            differs.append("provider")
        snapshot_id = (request.get("preconditions") or {}).get("snapshot_id")
        if expected_snapshot and snapshot_id != expected_snapshot:
            differs.append("expected_snapshot")
        if differs:
            raise DeliveryValidationError(
                f"request already exists: {request_id} with a different "
                f"{', '.join(differs)}; nothing was prepared")
        self._verify_request_bundle(request)
        return request

    def _verify_request_bundle(self, request: AIActionRequest) -> None:
        """Refuse a committed request whose prepared bundle is not intact."""
        directory = self.repository.request_dir(str(request["id"]))
        for name in ("instructions.md", "context.md", "contract-lock.json"):
            entry = directory / name
            if entry.is_symlink() or not entry.is_file():
                raise DeliveryValidationError(
                    f"request {request['id']} bundle is missing {name}")
        context = request.get("context") or {}
        originals = list(context.get("originals") or [])
        for name, expected in (
            ("artifact-index.json", originals),
            ("allowed-capabilities.json", list(request.get("allowed_capabilities") or [])),
        ):
            entry = directory / name
            try:
                if entry.is_symlink():
                    raise ValueError("symbolic link")
                value = json.loads(entry.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise DeliveryValidationError(
                    f"request {request['id']} bundle has an unreadable {name}: {exc}"
                ) from None
            if value != expected:
                raise DeliveryValidationError(
                    f"request {request['id']} bundle {name} does not match request.yaml")
        for original in originals:
            entry = _inside(directory, str(original.get("bundle_path", "")))
            if entry.is_symlink() or not entry.is_file() \
                    or _sha256_file(entry) != original.get("checksum"):
                raise DeliveryValidationError(
                    f"request {request['id']} bundle attachment "
                    f"{original.get('bundle_path')} does not match its checksum")

    def append_slices(
        self,
        *,
        request_id: str,
        route_id: str,
        start: int,
        end: int,
        kind: str,
        concept_ids: list[str],
        reason: str,
        material_uri: str | None = None,
        expected_snapshot: str | None = None,
    ) -> dict[str, Any]:
        """Attach one targeted follow-up pass to a prepared compare request.

        Pass 1 came from preparation; this adds pass 2 (or 3) for exactly
        one route with an explicit page range and a stated evidence gap.
        The snapshot and the material bytes are re-verified first: anything
        that moved since preparation refuses with a re-prepare instruction
        instead of mixing stale reads. Only ``prepared`` requests grow;
        deliveries, canonical records and other actions are untouched.
        """
        request = self.repository.get_request(request_id)
        if request.get("action_id") != "unit.compare-materials":
            raise ActionPolicyError(
                f"continuations only amend unit.compare-materials requests: {request_id}")
        if request.get("status") != "prepared":
            raise ActionPolicyError(
                f"request {request_id} is {request.get('status')}; "
                "only prepared requests accept continuation passes")
        snapshot = _snapshot(self.root)
        if expected_snapshot and expected_snapshot != snapshot:
            raise StaleDeliveryError(
                f"expected snapshot {expected_snapshot}, current snapshot is {snapshot}"
            )
        target_id = str((request.get("target") or {}).get("id"))
        repo = load_repo(self.root)
        self._assert_target_unchanged(request, repo=repo)
        unit = repo.units.get(target_id)
        if unit is None:
            raise TargetNotFoundError(f"Unit target not found: {target_id}")
        source_map = repo.module_source_maps.get(unit.module_id) or {}
        route: dict[str, Any] | None = None
        route_ids: list[str] = []
        for source_row in source_map.get("sources", []) or []:
            if not isinstance(source_row, dict):
                continue
            for row in source_row.get("unit_routes", []) or []:
                if isinstance(row, dict) and row.get("unit_id") == target_id:
                    route_ids.append(str(row.get("id")))
                    if str(row.get("id")) == route_id:
                        route = {**row,
                                 "source_id": source_row.get("source_id")}
        if route is None:
            raise RouteNotFound(
                "route", route_id, route_ids,
                message=(f"route {route_id} is not part of this "
                         "request's unit"))
        bundle_dir = self.repository.request_dir(str(request["id"]))
        index_records = read_bundle_slice_index(bundle_dir)
        prior = [entry for entry in index_records
                 if isinstance(entry, dict) and entry.get("route_id") == route_id]
        if not prior:
            raise ContinuationRefusedError(
                f"route {route_id} continuation refused: "
                "it has no first-pass slice to continue from")
        stored_basis = request.get("material_basis")
        if not isinstance(stored_basis, dict) or not stored_basis.get("material_checksums"):
            raise ContinuationRefusedError(
                f"route {route_id} continuation refused: this request predates "
                "slice-basis binding; re-prepare the request instead of continuing it")
        inspected = {uri: entry["pages"] for uri, entry in
                     inspected_material_by_route(index_records).get(route_id, {}).items()}
        try:
            record, index_entry, body = plan_continuation(
                repo, route, basis=stored_basis, inspected=inspected,
                passes_used=len(prior), start=start, end=end, kind=kind,
                concept_ids=concept_ids, reason=reason, material_uri=material_uri,
            )
        except UnknownConceptIds as exc:
            raise ConceptNotFound(
                "concept", exc.unknown_ids[0], exc.known_ids,
                message=str(exc)) from exc
        except ContinuationError as exc:
            raise ContinuationRefusedError(str(exc)) from exc
        spent = len(body)
        for entry in index_records:
            if not isinstance(entry, dict):
                continue
            existing = bundle_dir / str(entry.get("bundle_path", ""))
            if existing.is_file():
                spent += existing.stat().st_size
        if spent > MAX_SLICE_BYTES_TOTAL:
            raise ContinuationRefusedError(
                f"route {route_id} continuation refused: its slice tips the bundle "
                f"over the {MAX_SLICE_BYTES_TOTAL}-byte ceiling")
        index_records.append(index_entry)
        record_path = self.repository.write_continuation(
            str(request["id"]),
            pass_number=int(record.pass_number),
            route_id=route_id,
            record_text=_dump_yaml(continuation_record_dict(record)),
            slice_relative=index_entry["bundle_path"],
            slice_body=body,
            index_text=json.dumps(index_records, indent=2) + "\n",
        )
        passes = list(request.get("reading_passes") or [])
        passes.append({"route_id": route_id, "pass": record.pass_number,
                       "bundle_path": index_entry["bundle_path"],
                       "continuation": record_path})
        request["reading_passes"] = passes
        self.repository.update_request(request)
        return {"request_id": str(request["id"]), "route_id": route_id,
                "pass": record.pass_number, "bundle_path": index_entry["bundle_path"],
                "pages": list(range(start, end + 1)), "page_total": record.page_total}

    def import_delivery(self, source: Path) -> DeliveryRecord:
        try:
            delivery, staged = self.repository.stage_delivery_directory(source)
        except DeliveryAlreadyExists as occupied:
            return self._resume_delivery_import(source, occupied.delivery_id)
        delivery_id = str(delivery.get("id", ""))
        try:
            request_id = str(delivery.get("request_id", ""))
            if not request_id:
                raise DeliveryValidationError("delivery must name its request_id")
            request = self.repository.get_request(request_id)
            prior_status = request.get("status")
            if prior_status != "prepared":
                raise DeliveryValidationError(
                    f"request {request_id!r} has status {prior_status!r}; "
                    "only prepared requests accept delivery import"
                )
            self._validate(delivery, staged)
        except Exception:
            self.repository.discard_staged_delivery(staged)
            raise
        request = self.repository.get_request(str(delivery["request_id"]))
        request["status"] = "delivery-ready"
        request["delivery_id"] = delivery_id
        self.repository.commit_delivery_import(staged, delivery_id, request)
        return delivery

    def _resume_delivery_import(self, source: Path, delivery_id: str) -> DeliveryRecord:
        """Settle a retried import of a delivery that already landed (CL-02).

        A crash between publishing ``deliveries/<id>`` and advancing
        ``request.yaml`` leaves the delivery on disk while its request still
        says ``prepared``, and the old refusal ("delivery already exists")
        dead-ended every retry. A retry is accepted only when the existing
        directory holds exactly the bytes being imported again and the request
        it names is still ``prepared``, or already ``delivery-ready`` for this
        same delivery. Every other state, and any differing byte, is refused
        with both left untouched.
        """
        existing, directory = self.repository.get_delivery(delivery_id)
        if not self.repository.same_delivery_bytes(source, directory):
            raise DeliveryValidationError(
                f"delivery already exists: {delivery_id}; the bundle being "
                "imported differs from the imported one, so nothing was changed")
        request_id = str(existing.get("request_id", ""))
        if not request_id:
            raise DeliveryValidationError("delivery must name its request_id")
        request = self.repository.get_request(request_id)
        status = request.get("status")
        bound = request.get("delivery_id")
        if status == "delivery-ready" and bound == delivery_id:
            return existing
        if status != "prepared" or bound not in (None, delivery_id):
            bound_text = f" for delivery {bound!r}" if bound else ""
            raise DeliveryValidationError(
                f"delivery already exists: {delivery_id}; request {request_id!r} "
                f"has status {status!r}{bound_text}, so the import cannot resume")
        self._validate(existing, directory)
        request["status"] = "delivery-ready"
        request["delivery_id"] = delivery_id
        self.repository.update_request(request)
        return existing

    def validate_delivery(self, delivery_id: str) -> DeliveryValidationResult:
        delivery, directory = self.repository.get_delivery(delivery_id)
        outcome = self._validate(delivery, directory)
        return {"ok": True, "delivery_id": outcome.delivery_id,
                "request_id": outcome.request_id}

    def _validate_garden_transcription_op(
        self,
        target_id: str,
        operation: dict[str, Any],
    ) -> tuple[str, Path]:
        transcription_id = f"transcription-{target_id}"
        destination = (
            self.root / "knowledge" / "garden" / "transcriptions" / f"{target_id}.md"
        )
        # Re-shelving must not quietly discard an earlier AI reading of the
        # same seed: superseding is an explicit, receipted act.
        if destination.is_file() and operation.get("supersedes") != transcription_id:
            previous = parse_frontmatter_request_id(destination)
            raise DeliveryValidationError(
                f"a transcription for {target_id} already exists"
                + (f" (from request {previous})" if previous else "")
                + f"; set supersedes: {transcription_id} to replace it"
            )
        return transcription_id, destination

    def _validate_garden_update_op(
        self,
        operation: dict[str, Any],
        capability_definitions: dict[str, Any],
    ) -> dict[str, Any]:
        patch = operation.get("patch") or {}
        if not isinstance(patch, dict):
            raise DeliveryValidationError("garden.update patch must be a mapping")
        allowed_fields = set(capability_definitions["garden.update"].allowed_fields)
        illegal = set(patch) - allowed_fields
        if illegal:
            raise DeliveryValidationError(
                f"garden.update contains forbidden fields: {sorted(illegal)}"
            )
        return patch

    @staticmethod
    def _validate_relationship_create_op(
        delivery_id: str,
        request: AIActionRequest,
        operation: dict[str, Any],
    ) -> dict[str, Any]:
        payload = operation.get("payload") or {}
        if not isinstance(payload, dict) or not payload.get("id"):
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
            raise DeliveryValidationError(
                "relationship requires from, relation, and to identifiers"
            )
        return relation

    def _validate_synthesis_publish_op(
        self,
        *,
        target_id: str,
        delivery_id: str,
        request: AIActionRequest,
        operation: dict[str, Any],
        raw_bytes: bytes,
        repo: Any,
    ) -> tuple[dict[str, Any], Path]:
        try:
            synthesis = yaml.safe_load(raw_bytes.decode("utf-8", errors="strict"))
        except (UnicodeError, yaml.YAMLError) as exc:
            raise DeliveryValidationError(
                f"material synthesis artifact is unreadable: {exc}"
            ) from exc
        if not isinstance(synthesis, dict):
            raise DeliveryValidationError("material synthesis artifact must be an object")
        try:
            validate_unit_material_synthesis(self.root, target_id, synthesis, repo=repo)
        except ValueError as exc:
            raise DeliveryValidationError(str(exc)) from exc
        bundle_dir = self.repository.request_dir(str(request["id"]))
        index_records = read_bundle_slice_index(bundle_dir)
        try:
            inspected = resolve_route_provenance(
                repo,
                repo,
                target_id,
                synthesis_route_ids(synthesis),
                extra_inspected=inspected_material_by_route(index_records),
            )
            validate_synthesis_page_provenance(inspected, synthesis)
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
        destination = synthesis_destination(self.root, target_id, repo=repo)
        if destination.is_file() and operation.get("supersedes") != synthesis.get("id"):
            raise DeliveryValidationError(
                f"a dossier for {target_id} already exists; explicit supersedes is required"
            )
        return synthesis, destination

    def _validate(
        self,
        delivery: DeliveryRecord,
        directory: Path,
        *,
        repo=None,
        check_operations: bool = True,
    ) -> ValidatedDelivery:
        delivery_id = str(delivery.get("id", ""))
        if not str(delivery.get("request_id", "")):
            raise DeliveryValidationError("delivery must name its request_id")
        request = self.repository.get_request(str(delivery.get("request_id", "")))
        # Shape problems aggregate: a hand-authored delivery should learn
        # everything wrong with it in one round, not one field per import
        # (JF-07). Live freshness guards below still fail fast.
        problems: list[str] = []
        if delivery.get("type") != "ai-action-delivery":
            problems.append("delivery type must be ai-action-delivery")
        if delivery.get("action_id") != request.get("action_id"):
            problems.append(
                f"delivery action_id {delivery.get('action_id')!r} does not match "
                f"prepared request {request.get('action_id')!r}")
        producer = delivery.get("producer") or {}
        expected_adapter = (request.get("provider") or {}).get("adapter")
        if producer.get("adapter") != expected_adapter:
            problems.append(
                f"delivery producer.adapter {producer.get('adapter')!r} does not match "
                f"prepared request provider.adapter {expected_adapter!r}")
        if delivery.get("preconditions") != request.get("preconditions"):
            problems.append(
                "delivery preconditions must equal the prepared request preconditions")
        if not (delivery.get("approval") or {}).get("user_approved"):
            problems.append("delivery approval.user_approved must be true")
        operations = delivery.get("operations")
        if not isinstance(operations, list) or not operations:
            problems.append("delivery must contain at least one operation")
        else:
            allowed = set(request.get("allowed_capabilities", []))
            forbidden = set(request.get("forbidden_capabilities", []))
            target_id = str((request.get("target") or {}).get("id", ""))
            for index, operation in enumerate(operations):
                where = f"operations[{index}]"
                if not isinstance(operation, dict):
                    problems.append(f"{where} must be a mapping")
                    continue
                capability = operation.get("capability")
                if capability in forbidden or capability not in allowed:
                    problems.append(
                        f"{where} capability is not allowed: {capability!r}")
                if operation.get("target_id") and operation.get("target_id") != target_id:
                    problems.append(f"{where} targets an unrelated artifact")
                artifact_ref = operation.get("artifact_ref")
                if capability in {"garden.add-transcription", "unit.material-synthesis.publish"} and not artifact_ref:
                    problems.append(f"{where} requires artifact_ref")
                if artifact_ref:
                    try:
                        artifact = _inside(directory, str(artifact_ref))
                    except DeliveryValidationError as exc:
                        problems.append(f"{where} artifact_ref is unsafe: {exc}")
                    else:
                        if not artifact.is_file():
                            problems.append(
                                f"{where} artifact is missing: {artifact_ref}")
        if problems:
            shown = problems[:12]
            if len(problems) > 12:
                shown.append(f"{len(problems) - 12} further problem(s) omitted")
            raise DeliveryValidationError(
                f"delivery {delivery_id!r} is invalid: " + "; ".join(shown))
        # Staleness is scoped to what the delivery actually reasoned about.  The
        # repository-wide fingerprint is provenance, not a gate: rejecting a
        # delivery because an unrelated note moved (feature specification §20.4
        # scopes staleness to *the target*) makes the workflow unusable in a
        # live repository and tempts users to re-prepare blindly.
        if repo is None:
            repo = load_repo(self.root)
        target = self._assert_target_unchanged(request, repo=repo)
        if check_operations:
            capability_definitions = self.capability_definitions()
            target_id = str(request["target"]["id"])
            for operation in delivery["operations"]:
                capability = operation["capability"]
                if capability == "garden.add-transcription":
                    self._validate_garden_transcription_op(target_id, operation)
                elif capability == "garden.update":
                    self._validate_garden_update_op(operation, capability_definitions)
                elif capability == "relationship.create":
                    self._validate_relationship_create_op(delivery_id, request, operation)
                elif capability == "unit.material-synthesis.publish":
                    artifact_ref = str(operation.get("artifact_ref", ""))
                    if not artifact_ref:
                        raise DeliveryValidationError(
                            "unit.material-synthesis.publish requires artifact_ref"
                        )
                    raw_bytes = _inside(directory, artifact_ref).read_bytes()
                    self._validate_synthesis_publish_op(
                        target_id=target_id,
                        delivery_id=delivery_id,
                        request=request,
                        operation=operation,
                        raw_bytes=raw_bytes,
                        repo=repo,
                    )
                else:
                    raise DeliveryValidationError(
                        f"unsupported pilot capability: {capability}"
                    )
        return ValidatedDelivery(
            delivery_id=delivery_id,
            request_id=request["id"],
            request=request,
            target=target,
        )

    def _assert_target_unchanged(self, request: AIActionRequest, *, repo=None) -> GardenTarget:
        """Re-read the target, refuse if it moved, and hand back the fresh row.

        Returning the row is what lets callers stop re-walking the Garden tree:
        the read has to happen anyway for the guard to mean anything.
        """
        target_id = str((request.get("target") or {}).get("id", ""))
        target_kind = str((request.get("target") or {}).get("kind", "garden-note"))
        target, _ = self._target(target_id, target_kind, repo=repo)
        expected_revision = (request.get("preconditions") or {}).get(
            "artifact_revisions", {}).get(target_id)
        if target.get("revision") != expected_revision:
            raise StaleDeliveryError("Garden target changed after request preparation")
        for original in (request.get("context") or {}).get("originals", []):
            path = _inside(self.root, str(original["canonical_path"]))
            if not path.is_file() or _sha256_file(path) != original.get("checksum"):
                raise DeliveryValidationError("original artifact changed after request preparation")
        return target

    def _plan_delivery_application(
        self,
        delivery_id: str,
        delivery: DeliveryRecord,
        bound_artifacts: dict[str, bytes],
        directory: Path,
        *,
        repo: Any = None,
        authority: Any = None,
    ) -> _PlannedDeliveryApplication:
        """Compute exact writes and artifact ids without writing any bytes."""
        if repo is None:
            repo = load_repo(self.root)
        outcome = self._validate(delivery, directory, repo=repo, check_operations=False)
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
                transcription_id, destination = self._validate_garden_transcription_op(
                    target_id, operation,
                )
                if destination.is_file():
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
                patch = self._validate_garden_update_op(operation, capability_definitions)
                state.update(patch)
            elif capability == "relationship.create":
                relation = self._validate_relationship_create_op(
                    delivery_id, request, operation,
                )
                relation_id = str(relation["id"])
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
                synthesis, destination = self._validate_synthesis_publish_op(
                    target_id=target_id,
                    delivery_id=delivery_id,
                    request=request,
                    operation=operation,
                    raw_bytes=bound_artifacts[artifact_ref],
                    repo=repo,
                )
                content = _dump_yaml(synthesis)
                staged[destination] = (content, capability)
                ledger_content = (
                    publication_lineage(
                        self.root, target_id, synthesis, content, authority, repo=repo
                    )
                    if authority is not None
                    else ""
                )
                staged[self.root / LEDGER_RELATIVE] = (ledger_content, capability)
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
        artifact_ids = transaction_artifacts(
            self.root,
            {*created_ids, *updated_ids, *superseded_ids},
            staged,
        )
        return _PlannedDeliveryApplication(
            delivery_id=delivery_id,
            request=request,
            target=target,
            staged=staged,
            created_ids=created_ids,
            updated_ids=updated_ids,
            superseded_ids=superseded_ids,
            artifact_ids=artifact_ids,
            request_path=request_path,
            touched_base=[*staged, request_path],
        )

    def preview_delivery(self, delivery_id: str) -> dict[str, Any]:
        """Measure digests, snapshot, and exact artifact revisions without writing."""
        directory = self.repository.delivery_dir(delivery_id)
        delivery_file = directory / "delivery.yaml"
        if not delivery_file.exists() and not delivery_file.is_symlink():
            self.repository.get_delivery(delivery_id)
        delivery, bound_artifacts, delivery_sha256, artifact_sha256 = (
            read_delivery_for_preview(directory)
        )
        if delivery.get("id") != delivery_id:
            raise DeliveryBindingError(
                "approved delivery id does not match its imported directory"
            )
        repo = load_repo(self.root)
        plan = self._plan_delivery_application(
            delivery_id,
            delivery,
            bound_artifacts,
            directory,
            repo=repo,
            authority=None,
        )
        return {
            "ok": True,
            "delivery_id": delivery_id,
            "request_id": plan.request["id"],
            "delivery_sha256": delivery_sha256,
            "artifact_sha256": artifact_sha256,
            "expected_snapshot": f"sha256:{source_fingerprint(repo)}",
            "expected_revisions": {
                artifact_id: artifact_revision(self.root, artifact_id)
                for artifact_id in plan.artifact_ids
            },
        }

    def apply_delivery_proposal(
        self,
        delivery_id: str,
        *,
        delivery_sha256: str,
        artifact_sha256: dict[str, Any],
        expected_snapshot: str,
        expected_revisions: dict[str, int],
    ) -> tuple[TransactionProposal | None, ApplyDeliveryResult | None, list[Path]]:
        """The approved-delivery application up to its commit (SPEC §12 R5, (be)).

        Returns ``(proposal, None, touched_base)``: the proposal carries every
        argument the commit call took, with this service's except chain as
        ``translate``, and ``touched_base`` the staged and request paths the
        command records after a successful commit. A request that already
        committed returns ``(None, replay_result, [])`` without a proposal.
        """
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
            raise DeliveryBindingError(
                "approved delivery id does not match its imported directory"
            )
        try:
            replay = replay_for_request(self.root, authority)
        except TransactionIdempotencyConflict as exc:
            raise DeliveryIdempotencyConflict(f"delivery idempotency conflict: {exc}") from exc
        except TransactionFailure as exc:
            raise DeliveryValidationError(f"delivery replay failed: {exc}") from exc
        if replay is not None:
            return None, self._apply_result(replay, touched_paths=[]), []

        expected_snapshot = validated_sha256(
            expected_snapshot, label="expected_snapshot"
        )
        if not gateway_snapshot_is_verified(self.root, expected_snapshot):
            actual_snapshot = _snapshot(self.root)
            if expected_snapshot != actual_snapshot:
                raise StaleDeliveryError(
                    "approved delivery snapshot conflict "
                    f"(expected {expected_snapshot}, actual {actual_snapshot})"
                )
        repo = load_repo(self.root)
        plan = self._plan_delivery_application(
            delivery_id,
            delivery,
            bound_artifacts,
            directory,
            repo=repo,
            authority=authority,
        )
        request = plan.request
        request_path = plan.request_path
        # The exact original envelope was answered by the replay above. Any
        # other envelope for a request that already completed, however fresh
        # its guards, is refused before the write window (CL-04).
        if request.get("status") == "completed":
            raise DeliveryValidationError(
                f"AI request {request.get('id')} has already been applied "
                f"(receipt {request.get('receipt_id')}); nothing was written")
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
            raise DeliveryBindingError(
                "approved delivery bytes changed while application was being prepared"
            )

        def request_write(transaction_id: str) -> dict[Path, str]:
            completed = dict(request)
            completed["status"] = "completed"
            completed["receipt_id"] = transaction_id
            return {request_path: _dump_yaml(completed)}

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
            "created_ids": plan.created_ids,
            "updated_ids": plan.updated_ids,
            "deleted_ids": [],
            "superseded_ids": plan.superseded_ids,
            "validation": {
                "schemas": "passed",
                "references": "passed",
                "boundaries": "passed",
                "projection": "passed",
            },
        }
        proposal = TransactionProposal(
            capability="ai-action.delivery.apply",
            writes={path: content for path, (content, _capability) in plan.staged.items()},
            artifact_ids=set(plan.artifact_ids),
            deletes=None,
            expected_revisions=expected_revisions,
            touched="STANDARD",
            metadata=metadata,
            expected_snapshot=expected_snapshot,
            transaction_writes=request_write,
            write_authorities={
                **{
                    path: domain_capability
                    for path, (_content, domain_capability) in plan.staged.items()
                },
                request_path: "ai-action.delivery.apply",
            },
            clock=self.clock,
            translate=self._translate_commit_failure,
        )
        return proposal, None, plan.touched_base

    @staticmethod
    def _translate_commit_failure(exc: BaseException) -> AIActionError | None:
        """The except chain that wrapped the delivery commit (SPEC §12 R5)."""
        if isinstance(exc, TransactionConflict):
            return DeliveryRevisionConflict(str(exc))
        if isinstance(exc, TransactionSnapshotConflict):
            return StaleDeliveryError(str(exc))
        if isinstance(exc, TransactionIdempotencyConflict):
            return DeliveryValidationError(f"delivery idempotency conflict: {exc}")
        if isinstance(exc, (PostCommitFailure, ProjectionFailure,
                            TransactionPublicationUncertain, TransactionRollbackIncomplete)):
            return None
        if isinstance(exc, TransactionFailure):
            return DeliveryValidationError(f"delivery transaction failed: {exc}")
        return None

    def apply_delivery_receipt(
        self, confirmation: dict[str, Any], touched_base: list[Path],
    ) -> ApplyDeliveryResult:
        """The committed receipt as the old ``apply_delivery`` returned it (SPEC (be)).

        Reads the receipt the commit wrote, exactly as before; a replayed
        commit reports no touched paths.
        """
        result = SimpleNamespace(
            receipt_path=self.root / confirmation["receipt_path"],
            transaction_id=confirmation["transaction_id"],
            revisions=confirmation["artifact_revisions"],
            replayed=confirmation["replayed"],
        )
        return self._apply_result(
            result,
            touched_paths=(
                [] if result.replayed
                else [*touched_base, result.receipt_path]
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
        # Compatibility method for callers that already hold a service. The
        # read model itself lives in the dependency-light projection module so
        # manifest generation never imports this write orchestrator.
        from learning_os.derive.ai_actions import manifest_ai_projection

        return manifest_ai_projection(self.root)
