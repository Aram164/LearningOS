"""Platform-area converted handlers: the shared inspect unit (PLAN D4).

``cli.inspect`` and ``project.inspect`` are one conversion unit (SPEC §12.7):
both names register on the one moved handler. The inspect-only helpers moved
with the unit from ``commands.reads`` (SPEC (az) item 2).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import yaml

from learning_os.app.admin import masters_planning
from learning_os.app.backup_manifest import (
    BackupManifestError,
    backup_authorities,
    build_backup_manifest,
    verify_backup_manifest,
    verify_restored_system,
)
from learning_os.app.context import OpContext
from learning_os.app.gateway import read_structured_file as _read_structured_file
from learning_os.app.projection import fresh_manifest as _fresh_manifest
from learning_os.app.projection import fresh_manifest_and_repo as _fresh_manifest_and_repo
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import OperationEffects, register
from learning_os.derive import masters_catalog
from learning_os.derive.health import build_health_report
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused
from learning_os.domain.suggest import not_found, with_suggestions
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.contracts.json_schema import validate_contract
from learning_os.store.diagnostics import conventions
from learning_os.store.diagnostics.resolver import (
    AuthorityEvidence,
    collect_authority,
    load_authority_files,
    resolve,
)
from learning_os.store.diagnostics.store import read_records
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.fs import atomic_text as _atomic_text
from learning_os.store.layout import PathBoundaryError, read_bytes_inside
from learning_os.store.legacy_archive import (
    inspect_legacy_archive,
    legacy_archive_lock_destination,
    load_legacy_allowlist,
    load_legacy_archive_lock,
)
from learning_os.store.transactions import parse_expected_revisions


def _require_gateway_v2() -> None:
    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )

def _input_record_values(record, file_name, label: str) -> dict:
    """The record/file core of ``commands/vnext._input_record`` (SPEC (bl) 3).

    Converted handlers pass their request values directly; the vnext
    wrapper keeps extracting them from the argparse namespace until its
    last caller converts. Validations and messages are the originals.
    """
    if record is not None:
        if not isinstance(record, dict):
            raise WriteRefused(f"{label} must be an object")
        return record
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


def record_payload(manifest, record_id):
    resolved_id = (manifest.get("project_aliases") or {}).get(record_id, record_id)
    record = next((row for row in manifest["records"] if row.get("id") == resolved_id), None)
    if record is None:
        return None
    payload = dict(record)
    if resolved_id != record_id:
        payload["resolved_from"] = record_id
    return payload


def coordination_digest_fields(root: Path, sections) -> dict | None:
    """Whole-file plus per-section digests for the coordination record.

    The whole-file digest is the ``expected_content_sha256`` a
    coordination.section.revise apply must present; each per-section
    digest covers the projected section body exactly as served. Returns
    None when the file is absent or unreadable, so inspect degrades to
    the undigested record instead of refusing a read.
    """
    try:
        raw = read_bytes_inside(root, root / "work/COORDINATION.md")
    except (OSError, PathBoundaryError):
        return None
    fields: dict = {
        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }
    if isinstance(sections, dict):
        fields["section_sha256"] = {
            str(heading): "sha256:" + hashlib.sha256(
                str(body).encode("utf-8")).hexdigest()
            for heading, body in sections.items()
        }
    return fields


def with_coordination_digests(root: Path, payload: dict) -> dict:
    """Attach coordination digests to an inspect payload, when it is one."""
    if not isinstance(payload, dict) or payload.get("type") != "coordination":
        return payload
    fields = coordination_digest_fields(root, payload.get("sections"))
    if fields is None:
        return payload
    return {**payload, **fields}


def _structure_nodes(structure):
    """(node, node_path) pairs for a project structure tree, in order."""
    found = []

    def visit(nodes, path):
        for node in nodes or []:
            if not isinstance(node, dict) or not isinstance(node.get("id"), str):
                continue
            here = [*path, node["id"]]
            found.append((node, here))
            visit(node.get("children"), here)

    if isinstance(structure, dict):
        visit(structure.get("nodes"), [])
    return found


def structural_payload(manifest: dict, record_id: str, repo=None) -> dict | None:
    """Resolve a structural sub-id to its owner context, or None.

    Pure over the manifest except for learning-path stages, which are not
    projected and need the loaded repo. Curriculum stages answer with
    their projected row plus the plan-edit-context invocation that owns
    edits (inspect carries no revision guards); path stages, detours,
    and project nodes answer with their row plus owners; bare milestone
    ids answer with their owning projects, since milestones carry no
    record of their own. Several owners for one id answer one ambiguous
    payload with every candidate in stable order.
    """
    matches: list[dict] = []
    for stage in manifest.get("stages", []) or []:
        if isinstance(stage, dict) and stage.get("id") == record_id:
            unit_id = stage.get("unit_id")
            matches.append({
                "id": record_id, "structural_kind": "curriculum-stage",
                "stage": dict(stage), "unit_id": unit_id,
                "study_map_id": stage.get("study_map_id"),
                "module_id": stage.get("module_id"),
                "edit_via": (f"plan-edit-context {unit_id} "
                             f"--stage-id {record_id}"),
            })
    if repo is not None and record_id.startswith("stage-"):
        for path in sorted(getattr(repo, "learning_paths", {}).values(),
                           key=lambda candidate: candidate.id):
            for stage in path.data.get("stages", []) or []:
                if isinstance(stage, dict) and stage.get("id") == record_id:
                    matches.append({
                        "id": record_id, "structural_kind": "path-stage",
                        "stage": dict(stage), "path_id": path.id,
                        "workspace_id": path.workspace_id,
                        "archived": bool(path.archived),
                    })
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        for detour in study_map.get("detours", []) or []:
            if isinstance(detour, dict) and detour.get("id") == record_id:
                matches.append({
                    "id": record_id, "structural_kind": "detour",
                    "detour": dict(detour), "unit_id": study_map.get("unit_id"),
                    "study_map_id": study_map.get("id"),
                    "module_id": study_map.get("module_id"),
                })
    for record in manifest.get("records", []) or []:
        if not isinstance(record, dict) or record.get("type") != "project":
            continue
        for node, node_path in _structure_nodes(record.get("structure")):
            if node["id"] == record_id:
                matches.append({
                    "id": record_id, "structural_kind": "project-node",
                    "node": dict(node), "project_id": record.get("id"),
                    "node_path": node_path, "record_path": record.get("path"),
                })
        if record_id in (record.get("milestone_ids", []) or []):
            matches.append({
                "id": record_id, "structural_kind": "project-milestone",
                "project_id": record.get("id"), "record_path": record.get("path"),
                "note": ("milestones carry no record of their own; "
                         "the owning project is the record"),
            })
    if not matches:
        return None
    node_projects = {match["project_id"] for match in matches
                     if match["structural_kind"] == "project-node"}
    matches = [match for match in matches
               if match["structural_kind"] != "project-milestone"
               or match["project_id"] not in node_projects]
    if len(matches) == 1:
        return matches[0]
    return {"id": record_id, "structural_kind": "ambiguous",
            "candidates": matches}


#: Id prefixes that name structural sub-records rather than records.
STRUCTURAL_PREFIXES = ("stage-", "detour-", "step-", "workstream-", "milestone-")


def _inspect_candidates(manifest: dict, repo=None, *, include_paths=True) -> list[str]:
    """Every id ``inspect`` could have resolved: records plus structural ids."""
    ids = [row.get("id") for row in manifest.get("records", []) or []
           if isinstance(row, dict) and isinstance(row.get("id"), str)]
    ids.extend(stage.get("id") for stage in manifest.get("stages", []) or []
               if isinstance(stage, dict) and isinstance(stage.get("id"), str))
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        ids.extend(detour.get("id") for detour in study_map.get("detours", []) or []
                   if isinstance(detour, dict) and isinstance(detour.get("id"), str))
    for record in manifest.get("records", []) or []:
        if not isinstance(record, dict) or record.get("type") != "project":
            continue
        ids.extend(node["id"] for node, _ in _structure_nodes(record.get("structure")))
        ids.extend(mid for mid in record.get("milestone_ids", []) or []
                   if isinstance(mid, str))
    if repo is not None and include_paths:
        for path in getattr(repo, "learning_paths", {}).values():
            ids.extend(stage.get("id") for stage in path.data.get("stages", []) or []
                       if isinstance(stage, dict) and isinstance(stage.get("id"), str))
    return ids


def inspect_not_found(record_id: str, candidates=()) -> str:
    if isinstance(record_id, str) and record_id.startswith(STRUCTURAL_PREFIXES):
        return with_suggestions(
            f"record not found: {record_id} (no curriculum stage, path stage, "
            "detour, project node, or milestone carries this id)",
            record_id, candidates)
    return not_found("record", record_id, candidates)


def describe_unresolved_reference(manifest, record_id):
    """Name the record that references an unresolvable id, if there is one.

    Milestones and project structure nodes resolve through
    ``structural_payload``, so an advertised id that still misses is a
    dangling ``*_ids`` cross-reference (the validator refuses those; inspect
    reads without validating). On an inspect miss, point the caller at the
    referring record instead of a bare not-found. Returns None when nothing
    references the id.
    """
    for record in manifest.get("records", []) or []:
        referrer = record.get("id")
        if not referrer:
            continue
        for key, value in record.items():
            if (key.endswith("_ids") and isinstance(value, list)
                    and record_id in value):
                return (f"referenced by {referrer} "
                        f"({record.get('type', 'record')}) in {key}")
    return None


def _inspect_batch(ctx: OpContext, req: dict) -> Result:
    """Resolve a requested batch once; never return a partial or mixed read."""
    ids = [req["id"], *req["more_ids"]]
    if len(ids) > 20:
        raise WriteRefused(
            "inspect accepts at most 20 IDs per batch",
            site=f"{ctx.operation}.too-many-ids",
            prefixed=True,
            exit_code=2,
        )
    root = ctx.root
    try:
        snapshot = _snapshot(root)
        manifest, repo = _fresh_manifest_and_repo(root, snapshot_id=snapshot)
        records = []
        for record_id in ids:
            record = record_payload(manifest, record_id)
            if record is None:
                record = structural_payload(manifest, record_id, repo)
            if record is not None:
                record = with_coordination_digests(root, record)
            if record is None:
                # The hint stays out of the refusal message: it is a
                # separate stderr line (R2 extra_stderr), never part of
                # the complaint.
                message = inspect_not_found(
                    record_id, _inspect_candidates(manifest, repo, include_paths=record_id.startswith("stage-")))
                hint = describe_unresolved_reference(manifest, record_id)
                extra = (f"los: hint: {hint}",) if hint else ()
                raise WriteRefused(
                    message,
                    site=f"{ctx.operation}.unknown-id",
                    extra_stderr=extra,
                    gateway_message=(
                        f"los: {message}"
                        + (f"\nlos: hint: {hint}" if hint else "")
                    ),
                    exit_code=2,
                )
            records.append(record)
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot,
             "contract": "record-batch", "requested_ids": ids,
             "records": records},

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


@register("project.inspect", kind="query", parallel_safe=True, memo_profile="manifest", read_session_profile="manifest", effects=OperationEffects.READ)
def inspect(ctx: OpContext, req: dict) -> Result:
    """Inspect one record or structural id, or a batch of up to 20."""
    if req.get("more_ids"):
        return _inspect_batch(ctx, req)
    root = ctx.root
    manifest, repo = _fresh_manifest_and_repo(root)
    payload = record_payload(manifest, req["id"])
    if payload is None:
        payload = structural_payload(manifest, req["id"], repo)
    if payload is None:
        message = inspect_not_found(req["id"], _inspect_candidates(manifest, repo))
        hint = describe_unresolved_reference(manifest, req["id"])
        extra = (f"los: hint: {hint}",) if hint else ()
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.unknown-id",
            extra_stderr=extra,
            gateway_message=(
                f"los: {message}" + (f"\nlos: hint: {hint}" if hint else "")
            ),
            exit_code=2,
        )
    payload = with_coordination_digests(root, payload)
    return Result(payload)


# ---------------------------------------------------------------------------
# Project records (project.create, project.list, project.update; PLAN D4).
#
# _project_record and _project_write move with the units from commands.project
# (SPEC §12). _project_write stages its write for the pipeline's commit
# instead of calling _write_transaction itself.




def _project_record(req: dict) -> dict:
    """The project record, from wherever this invocation carried it.

    One command, two ways in: a path for a person at a shell, an inline object
    for a caller that already holds the record. The parser declares both as one
    required mutually exclusive group, so the generated capability schema says
    exactly this — which is the whole point. The gateway used to accept the
    inline form through a branch of its own, undeclared and unvalidated.
    """
    record = req.get("project")
    if record is not None:
        if not isinstance(record, dict):
            raise WriteRefused("project must be an object")
        return record
    if not req.get("file"):
        raise WriteRefused("project record required: pass --file or --project")
    return _read_structured_file(
        req.get("file"),
        expected_sha256=req.get("file_sha256"),
        label="project file",
    )


def _project_ids(root: Path) -> list[str]:
    """Every project id the registry holds, for R6 suggestion domains."""
    return sorted(path.stem for path in
                  (root / "projects" / "registry").glob("*.yaml")
                  if path.is_file())


def _project_write(root: Path, data: dict, *,
                   capability: str, operation: str) -> tuple[dict[Path, str], str]:
    """Validate one project record and stage its registry write.

    The pre-transaction half of commands.project._project_write, moved with
    the project units: the same guards in the same order, returning the
    staged writes and the project id for the pipeline's commit.
    """
    project_id = data.get("id")
    if not isinstance(project_id, str) or not re.fullmatch(r"project-[a-z0-9]+(?:-[a-z0-9]+)*", project_id):
        raise WriteRefused("project id must match project-<slug>")
    if data.get("type") != "project":
        raise WriteRefused("project type must be 'project'")
    target = root / "projects" / "registry" / f"{project_id}.yaml"
    exists = target.is_file()
    if capability == "project.create" and exists:
        raise WriteRefused(f"project already exists: {project_id}")
    if capability == "project.update" and not exists:
        raise NotFound(
            "project", project_id, _project_ids(root),
            message=f"project not found: {project_id}",
            site=f"{operation}.unknown-project",
        )
    if exists:
        current = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        if current.get("id") != project_id or current.get("type") != data.get("type"):
            raise WriteRefused("project update cannot change id or type")
    data = copy.deepcopy(data)
    data.setdefault("schema_version", 1)
    data.setdefault("revision", 0)
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    return {target: rendered}, project_id


@register("project.create", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def project_create(ctx: OpContext, req: dict) -> Result:
    """Create one first-class project record."""
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    data = _project_record(req)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    writes, project_id = _project_write(
        root, data, capability="project.create", operation=ctx.operation)
    return Result(
        {"ok": True, "project_id": project_id},
        proposal=TransactionProposal(
            capability="project.create",
            writes=writes,
            artifact_ids=[project_id],
            expected_revisions=expected_revisions,
        ),


    )


@register("project.update", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def project_update(ctx: OpContext, req: dict) -> Result:
    """Update one first-class project record."""
    root = ctx.root
    data = _project_record(req)
    if data.get("id") != req["project_id"]:
        raise NotFound(
            "project", req["project_id"], _project_ids(root),
            message="project file id does not match command project_id",
            site=f"{ctx.operation}.id-mismatch",
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    writes, project_id = _project_write(
        root, data, capability="project.update", operation=ctx.operation)
    return Result(
        {"ok": True, "project_id": project_id},
        proposal=TransactionProposal(
            capability="project.update",
            writes=writes,
            artifact_ids=[project_id],
            expected_revisions=expected_revisions,
        ),


    )


@register("project.list", kind="query", effects=OperationEffects.READ)
def project_list(ctx: OpContext, req: dict) -> Result:
    """List first-class projects, optionally filtered by status."""
    manifest = _fresh_manifest(ctx.root)
    rows = manifest.get("projects", [])
    if req.get("status"):
        rows = [row for row in rows if row.get("status") == req.get("status")]
    return Result(rows)


# ---------------------------------------------------------------------------
# Backup, health, legacy archive, Master's planning (PLAN D4).
#
# Moved with the units from commands.vnext (SPEC §12).


@register("backup.manifest", kind="query", effects=OperationEffects.DERIVED_WRITE)
def backup_manifest(ctx: OpContext, req: dict) -> Result:
    """Build the backup manifest, or write it outside every backed-up root."""
    root = ctx.root
    authorities = backup_authorities(
        root,
        ui_root=Path(req.get("ui_root")).expanduser() if req.get("ui_root") else None,
        materials_root=(Path(req.get("materials_root")).expanduser()
                        if req.get("materials_root") else None),
    )
    manifest = build_backup_manifest(
        root, ui_root=authorities["ui"], materials_root=authorities["materials"])
    if req.get("out"):
        target = Path(req.get("out")).expanduser()
        resolved = target.resolve()
        for label, authority in authorities.items():
            if resolved == authority or authority in resolved.parents:
                raise BackupManifestError(
                    f"refusing to write the manifest inside the backed-up "
                    f"{label} root: {req.get('out')}")
        _atomic_text(target, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        if req.get("stdout"):
            return Result(manifest)
        return Result({
            "ok": True,
            "out": str(resolved),
            "roots": manifest["roots"],
            "entries": len(manifest["entries"]),
            "aggregate_sha256": manifest["aggregate_sha256"],
        })
    if req.get("stdout"):
        return Result(manifest)
    size_kb = len(json.dumps(manifest, ensure_ascii=False).encode("utf-8")) / 1024
    raise BackupManifestError(
        f"backup-manifest prints nothing by default: the manifest holds "
        f"{len(manifest['entries'])} entries (~{size_kb:.0f} KB). Write it "
        f"with --out PATH (outside every backed-up root) or print it with "
        f"--stdout")


@register("backup.verify", kind="tool", effects=OperationEffects.DERIVED_WRITE)
def backup_verify(ctx: OpContext, req: dict) -> Result:
    """Verify a backup manifest against the restored trees."""
    root = ctx.root
    value = _read_structured_file(req["manifest"])
    verifier = verify_backup_manifest if req.get("checksums_only") else verify_restored_system
    result = verifier(
        root,
        value,
        restored_core=Path(req["restored_core"]).expanduser().resolve(),
        restored_ui=Path(req["restored_ui"]).expanduser().resolve(),
        restored_materials=Path(req["restored_materials"]).expanduser().resolve(),
    )
    return Result(result, diagnostic_failed=not result["ok"])


@register("health.report", kind="query", effects=OperationEffects.READ)
def health_report(ctx: OpContext, req: dict) -> Result:
    """Build the repository health report."""
    # Attention is report data, not a transport failure: the UI must be able to
    # render the remedies even when one check is red.
    return Result(build_health_report(ctx.root))


@register("legacy.archive.inspect", kind="query", effects=OperationEffects.READ)
def legacy_archive_inspect(ctx: OpContext, req: dict) -> Result:
    """Inspect a legacy archive against its allowlist."""
    root = ctx.root
    allowlist = load_legacy_allowlist(root, Path(req["allowlist"]).expanduser().resolve())
    lock = inspect_legacy_archive(
        root, Path(req["archive_root"]).expanduser().resolve(), allowlist,
    )
    return Result(lock)


@register("legacy.archive.status", kind="query", effects=OperationEffects.READ)
def legacy_archive_status(ctx: OpContext, req: dict) -> Result:
    """Report the published legacy-archive lock, if any."""
    root = ctx.root
    lock = load_legacy_archive_lock(root)
    value = {
        "schema_version": 1,
        "type": "legacy-archive-status",
        "available": lock is not None,
        "lock": lock,
    }
    validate_contract(root, "legacy-archive-status.schema.json", value)
    return Result(value)


@register("masters-planning.dashboard", kind="query", effects=OperationEffects.READ)
def masters_planning_dashboard(ctx: OpContext, req: dict) -> Result:
    """Render the Master's Planning dashboard."""
    value = masters_planning.masters_planning_dashboard(
        ctx.root, confirmed=bool(req.get("confirm_masters_planning")),
    )
    return Result(value)


# ---------------------------------------------------------------------------
# Operations list and request explanation (cli.operations; PLAN D4).
#
# Moved with the unit from commands.operations (SPEC §12): the read-only
# Operations surface over the disposable trace store plus the authority
# plane — no new evidence, no new authority, no writes.


def _summaries(records: list[dict]) -> list[dict]:
    return [record for record in records
            if record.get("name") == conventions.EVENT_RESPONSE_EMITTED]


def _response_from_summary(summary: dict | None) -> dict | None:
    if summary is None:
        return None
    attrs = summary.get("attrs") or {}
    error = None if attrs.get("ok") else {"code": attrs.get("code"),
                                          "retryable": attrs.get("retryable")}
    return {"ok": attrs.get("ok"), "error": error,
            "replayed": attrs.get("replayed", False),
            "transaction_id": attrs.get("transaction_id"),
            "receipt_path": attrs.get("receipt_path"),
            "snapshot_after": attrs.get("snapshot_after")}


def _identity(records: list[dict]) -> tuple[str | None, str | None, str | None]:
    request_id = idempotency_key = capability = None
    for record in records:
        attrs = record.get("attrs") or {}
        if record.get("name") in (conventions.EVENT_ENVELOPE_VALIDATED,
                                  conventions.EVENT_ENVELOPE_PREPARED):
            request_id = request_id or attrs.get("request_id")
            idempotency_key = idempotency_key or attrs.get("idempotency_key")
        if record.get("kind") == "span-start" and record.get("name") == "attempt":
            capability = capability or attrs.get("capability")
    return request_id, idempotency_key, capability


def _observed_snapshot(root: Path) -> str | None:
    manifest = root / "generated" / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        return (json.loads(manifest.read_text(encoding="utf-8"))
                .get("_generated", {}).get("snapshot_id"))
    except (ValueError, OSError):
        return None


def _observed_for(records: list[dict], snapshot_after: str | None,
                  manifest_snapshot: str | None) -> str | None:
    """What observation evidence exists for one operation.

    Publication is not observation: a projection-published event proves Core
    wrote the snapshot, not that any interface observed it, so it never
    counts here. Observation evidence is the live manifest showing this
    exact snapshot (current visibility), or the UI settling while observing
    it (the durable proof for a superseded snapshot). A receipt with
    neither stays unverified.
    """
    if snapshot_after is None:
        for record in records:
            attrs = record.get("attrs") or {}
            if record.get("name") == conventions.EVENT_RECOVERY_SETTLED \
                    and attrs.get("observed") is True \
                    and isinstance(attrs.get("snapshot_after"), str):
                return attrs["snapshot_after"]
        return manifest_snapshot
    if manifest_snapshot == snapshot_after:
        return manifest_snapshot
    for record in records:
        attrs = record.get("attrs") or {}
        if record.get("name") == conventions.EVENT_RECOVERY_SETTLED \
                and attrs.get("snapshot_after") == snapshot_after \
                and attrs.get("observed") is True:
            return snapshot_after
    return None


def _evidence_for(root: Path, records: list[dict],
                  observed: str | None,
                  authority_files: tuple[list[dict], dict, list[str]]
                  | None = None,
                  drift_cache: dict | None = None) -> AuthorityEvidence:
    # One collection path: the strict receipt verification lives in
    # collect_authority, so Operations can never drift from it.
    request_id, idempotency_key, capability = _identity(records)
    summaries = sorted(_summaries(records), key=lambda row: row.get("ts", 0))
    response = _response_from_summary(summaries[-1] if summaries else None)
    snapshot_after = (response or {}).get("snapshot_after") or next(
        (
            (row.get("attrs") or {}).get("snapshot_after")
            for row in reversed(summaries)
            if (row.get("attrs") or {}).get("snapshot_after")
        ),
        None,
    )
    if response is not None and response.get("snapshot_after") is None and snapshot_after is not None:
        response = {**response, "snapshot_after": snapshot_after}
    codes: list = []
    for summary in summaries:
        attrs = summary.get("attrs") or {}
        codes.append(None if attrs.get("ok") else attrs.get("code"))
    return collect_authority(
        root, request_id=request_id or "unknown-request",
        idempotency_key=idempotency_key or "unknown-key",
        capability=capability or "unknown-capability",
        response=response,
        response_codes=codes,
        observed_snapshot=_observed_for(
            records, snapshot_after, observed),
        # `observed` is the live manifest snapshot itself: the supersession
        # check positions it against the receipt inventory (JF-19).
        manifest_snapshot=observed,
        authority_files=authority_files,
        drift_cache=drift_cache)


def _started_at(records: list[dict]):
    return min([row.get("ts") for row in records if row.get("ts")] or [None])


def list_operations(root: Path, limit: int = 20) -> list[dict]:
    """Newest-first operation summaries for the Operations list."""
    by_op: dict[str, list[dict]] = {}
    for record in read_records(root):
        if record.get("op"):
            by_op.setdefault(record["op"], []).append(record)
    observed = _observed_snapshot(root)
    # Limit first: rank by start time from the trace alone, then diagnose
    # only the requested recent operations against one shared authority
    # load. (Diagnosing everything and slicing after costs one full
    # receipt-inventory parse per operation — limit-after-diagnose.)
    ranked = sorted(by_op.items(),
                    key=lambda item: _started_at(item[1]) or 0, reverse=True)
    selected = ranked[:max(limit, 0)]
    shared = load_authority_files(root) if selected else None
    drift_cache: dict = {}
    rows = []
    for op, records in selected:
        records = sorted(records, key=lambda row: row.get("ts", 0))
        request_id, _, capability = _identity(records)
        starts = [row for row in records if row.get("kind") == "span-start"]
        ends = [row for row in records if row.get("kind") == "span-end"]
        started = _started_at(records)
        finished = max([row.get("ts") for row in ends if row.get("ts")] or [None])
        authority = _evidence_for(root, records, observed,
                                  authority_files=shared,
                                  drift_cache=drift_cache if shared is not None else None)
        diagnosis = resolve(records, authority)
        replayed = any((row.get("attrs") or {}).get("replayed") for row in
                       _summaries(records)) or len(starts) > 1
        rows.append({
            "trace_id": op,
            "request_id": request_id,
            "capability": capability or "unknown",
            "started_at": started,
            "duration_ms": (round((finished - started) * 1000.0, 1)
                            if started and finished else None),
            "attempts": len(starts),
            "replayed": replayed,
            "first_failure_stage": diagnosis.first_failure_stage,
            "canonical_outcome": diagnosis.canonical_outcome,
            "recovery_requirement": diagnosis.recovery_requirement,
            "needs_attention": diagnosis.recovery_requirement != "none",
        })
    rows.sort(key=lambda row: row["started_at"] or 0, reverse=True)
    return rows[:max(limit, 0)]


TIMELINE = (
    ("UI recovery persisted", ("gateway.envelope.prepared",)),
    ("Core admitted request", (conventions.EVENT_ENVELOPE_VALIDATED,)),
    ("Approval", (conventions.EVENT_APPROVAL_PASSED,)),
    ("Replay lookup", (conventions.EVENT_REPLAY_CHECKED,)),
    ("Snapshot guard", (conventions.EVENT_SNAPSHOT_GUARD_PASSED,)),
    ("Handler", (conventions.EVENT_HANDLER_COMPLETED,)),
    ("Validation", (conventions.EVENT_VALIDATION_PASSED,)),
    ("Projection", (conventions.EVENT_PROJECTION_STARTED,
                    conventions.EVENT_PROJECTION_PUBLISHED)),
    ("Transaction committed", (conventions.EVENT_CORE_TRANSACTION_COMMITTED,)),
    ("Receipt persisted", (conventions.EVENT_RECEIPT_PERSISTED,)),
    ("Response classified", ("ui.response.received",)),
    ("Recovery settled", (conventions.EVENT_RECOVERY_SETTLED,)),
    ("Recovery blocked", (conventions.EVENT_RECOVERY_BLOCKED,)),
)

_STAGE_ROW = {
    "ui.prepare": "UI recovery persisted",
    "core.admission": "Core admitted request",
    "core.approval": "Approval",
    "core.replay": "Replay lookup",
    "core.snapshot_guard": "Snapshot guard",
    "core.validation": "Validation",
    "core.projection": "Projection",
    "core.commit": "Transaction committed",
    "core.receipt": "Receipt persisted",
    "ui.reconcile": "Snapshot observed",
    "ui.recovery": "Recovery settled",
}


def build_timeline(records: list[dict], diagnosis) -> list[dict]:
    """Ordered stage checklist; rows without evidence are omitted."""
    names = [record.get("name") for record in records
             if record.get("kind") == "event"]
    failed_label = _STAGE_ROW.get(diagnosis.first_failure_stage or "")
    rows = []
    for label, events in TIMELINE:
        present = [name for name in events if name in names]
        if not present and label != failed_label:
            continue
        state = "passed" if present else "missing"
        if label == failed_label:
            state = "failed"
        detail = None
        if label == "Replay lookup":
            for record in records:
                if record.get("name") == conventions.EVENT_REPLAY_CHECKED:
                    detail = (record.get("attrs") or {}).get("outcome")
        if label == "Projection" and state == "passed" \
                and conventions.EVENT_PROJECTION_PUBLISHED not in names:
            state = "failed"
            detail = "started, never published"
        rows.append({"stage": label, "state": state, "detail": detail})
    return rows


def _note_request_id_reuse(records: list[dict], authority, diagnosis) -> None:
    """Name every distinct request behind one reused request id (JF-19).

    Request ids are caller-chosen and not unique; two writes may share one
    id string under different idempotency keys. Authority resolves the
    first key's evidence, so without this note the explanation silently
    names only the first transaction.
    """
    per_op: dict[str, dict] = {}
    for record in records:
        op = record.get("op")
        if not op:
            continue
        slot = per_op.setdefault(op, {})
        attrs = record.get("attrs") or {}
        if record.get("name") in (conventions.EVENT_ENVELOPE_VALIDATED,
                                  conventions.EVENT_ENVELOPE_PREPARED):
            if attrs.get("idempotency_key") and "key" not in slot:
                slot["key"] = attrs.get("idempotency_key")
        if record.get("name") == conventions.EVENT_RESPONSE_EMITTED:
            slot["outcome"] = "ok" if attrs.get("ok") else attrs.get("code")
            slot["tx"] = attrs.get("transaction_id")
    keys = sorted({slot.get("key") for slot in per_op.values() if slot.get("key")})
    if len(keys) < 2:
        return
    covered = authority.idempotency_key
    others = [f"{slot.get('key')} ({slot.get('outcome')}"
              + (f" {slot.get('tx')}" if slot.get("tx") else "") + ")"
              for slot in sorted(per_op.values(), key=lambda s: str(s.get("key")))
              if slot.get("key") and slot.get("key") != covered]
    diagnosis.reasons.append(
        f"request_id reused across {len(keys)} idempotency keys; this "
        f"explanation covers {covered} only — also: {', '.join(others)}")


def _covered_records(root: Path, records: list[dict],
                     observed: str | None) -> list[dict]:
    """The traces one request-id explanation diagnoses (WORKFLOWS §28).

    A reused request id can span distinct idempotency keys, each its own
    request. The explanation covers the first key over the merged traces,
    as documented, and `_note_request_id_reuse` names the others. Only when
    the first key's receipt does not verify and a later key's does — a
    refused attempt retried under a fresh key — would the merged traces
    contradict themselves: the retry's commit, read against the refused
    key's authority, came out AMBIGUOUS while the list said COMMITTED. Then
    the explanation covers that later key's traces alone (with any traces
    that never named a key).
    """
    by_op: dict[str, list[dict]] = {}
    for record in records:
        by_op.setdefault(record["op"], []).append(record)
    key_of: dict[str, str | None] = {}
    keys: list[str] = []
    for op, op_records in by_op.items():
        key = _identity(op_records)[1]
        key_of[op] = key
        if key and key not in keys:
            keys.append(key)
    if len(keys) < 2:
        return records
    groups = {key: [record for record in records
                    if key_of[record["op"]] in (key, None)]
              for key in keys}
    shared = load_authority_files(root)
    drift_cache: dict = {}

    def verified(key: str) -> bool:
        return bool(_evidence_for(root, groups[key], observed,
                                  authority_files=shared,
                                  drift_cache=drift_cache).verified_receipt)

    if verified(keys[0]):
        return records
    for key in keys[1:]:
        if verified(key):
            return groups[key]
    return records


def _describe_operation(root: Path, request_id: str) -> tuple[dict | None, list[str]]:
    """Diagnosis plus the distinct traced request ids, from one load.

    The domain is every distinct ``request_id`` in the records just
    loaded ((cx) D-6): request ids are caller-chosen and not unique,
    so the miss suggests from distinct values, never from operations.
    """
    everything = read_records(root)
    domain = sorted({str((record.get("attrs") or {}).get("request_id"))
                     for record in everything
                     if isinstance((record.get("attrs") or {}).get("request_id"), str)
                     and (record.get("attrs") or {}).get("request_id")})
    detail = _describe_from_records(root, request_id, everything)
    return detail, domain


def describe_operation(root: Path, request_id: str) -> dict | None:
    """Full diagnosis plus timeline for one request id, or None."""
    return _describe_operation(root, request_id)[0]


def _describe_from_records(root: Path, request_id: str,
                           everything: list[dict]) -> dict | None:
    ops = {record["op"] for record in everything
           if (record.get("attrs") or {}).get("request_id") == request_id
           and record.get("op")}
    records = sorted((record for record in everything if record.get("op") in ops),
                     key=lambda row: row.get("ts", 0))
    if not records:
        return None
    observed = _observed_snapshot(root)
    covered = _covered_records(root, records, observed)
    authority = _evidence_for(root, covered, observed)
    diagnosis = resolve(covered, authority)
    _note_request_id_reuse(records, authority, diagnosis)
    receipt = authority.verified_receipt or {}
    if diagnosis.canonical_outcome == "COMMITTED" \
            and diagnosis.recovery_requirement == "none":
        ui_outcome = "SETTLED"
    elif diagnosis.canonical_outcome == "NOT_COMMITTED" \
            and diagnosis.recovery_requirement == "none":
        ui_outcome = "REFUSED"
    else:
        ui_outcome = "BLOCKED"
    return {
        "request_id": request_id,
        "capability": authority.capability,
        "diagnosis": diagnosis.to_dict(),
        "timeline": build_timeline(covered, diagnosis),
        "observed_snapshot": observed,
        "ui_outcome": ui_outcome,
        "facts": {
            "transaction_id": receipt.get("id"),
            "receipt_path": receipt.get("_path"),
            "snapshot_before": receipt.get("snapshot_before"),
            "snapshot_after": receipt.get("snapshot_after"),
        },
    }


@register("operations.read", kind="tool", effects=OperationEffects.READ)
def operations(ctx: OpContext, req: dict) -> Result:
    """List recent causal operations or explain one request id."""
    root = ctx.root
    if req.get("request_id"):
        detail, domain = _describe_operation(root, req["request_id"])
        if detail is None:
            message = "unknown request_id"
            raise NotFound(
                "request", req["request_id"], domain,
                message=message,
                site=f"{ctx.operation}.unknown-request",
                gateway_message=json.dumps(
                    {"error": message, "request_id": req["request_id"]}),
                exit_code=2,
            )
        return Result(detail)
    limit = req.get("limit") or 20
    return Result(
        {"operations": list_operations(root, limit=min(limit, 50))},

    )


# ---------------------------------------------------------------------------
# Reviewed vNext publishes (PLAN D4).
#
# Moved with the units from commands.vnext (SPEC §12). Each publish takes a
# reviewed record, requires the explicit approval, and commits one receipted
# transaction; a refused commit prints the result JSON on stdout, as the
# legacy handlers did (SPEC (bd)).




@register("legacy.archive.lock.publish", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def legacy_archive_lock_publish(ctx: OpContext, req: dict) -> Result:
    """Publish one reviewed safe Legacy disposition lock."""
    root = ctx.root
    value = _input_record_values(
        req.get("record"), req.get("file"), "Legacy archive lock")
    # Reuse the exact public reader validation before the write boundary.
    validate_contract(root, "legacy-archive-lock.schema.json", value)
    if not req.get("approve"):
        message = "Legacy archive lock publication requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.approval-required",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    validate_contract(root, "legacy-archive-lock.schema.json", value)
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="legacy.archive.lock.publish",
            writes={legacy_archive_lock_destination(root): _dump_yaml(value)},
            artifact_ids=["legacy-archive-lock"],
            expected_revisions=expected_revisions,
        ),


    )


@register("masters-planning.catalog.update", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def masters_planning_catalog_update(ctx: OpContext, req: dict) -> Result:
    """Update the reviewed academic-only Master Planning catalog."""
    root = ctx.root
    value = masters_catalog.validate_master_catalog(
        root,
        _input_record_values(
            req.get("record"), req.get("file"), "Master Planning catalog"),
    )
    masters_planning.validate_catalog_revision(root, value)
    if not req.get("approve"):
        message = "Master Planning catalog update requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.approval-required",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    value = masters_catalog.validate_master_catalog(root, value)
    masters_planning.validate_catalog_revision(root, value)
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="masters-planning.catalog.update",
            writes={masters_catalog.master_catalog_destination(root):
                    _dump_yaml(value)},
            artifact_ids=["master-planning-catalog"],
            expected_revisions=expected_revisions,
        ),


    )


@register("masters-planning.comparison.publish", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def masters_planning_comparison_publish(ctx: OpContext, req: dict) -> Result:
    """Publish one prospective source comparison against its catalog."""
    root = ctx.root
    value = masters_planning.validate_candidate_comparison(
        root,
        _input_record_values(
            req.get("record"), req.get("file"),
            "prospective source comparison"),
    )
    if value["candidate_module_id"] != req["candidate_module_id"]:
        raise WriteRefused(
            "comparison candidate_module_id does not match the command")
    if not req.get("approve"):
        message = "prospective comparison publication requires explicit approval"
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.approval-required",
            gateway_message=json.dumps({"ok": False, "error": message}),
            exit_code=2,
        )
    _require_gateway_v2()
    value = masters_planning.validate_candidate_comparison(root, value)
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    return Result(
        {"ok": True},
        proposal=TransactionProposal(
            capability="masters-planning.comparison.publish",
            writes={masters_planning.candidate_comparison_destination(
                root, value["id"]): _dump_yaml(value)},
            artifact_ids=[req["candidate_module_id"], value["id"]],
            expected_revisions=expected_revisions,
        ),


    )


@register("projection.observe", kind="query", effects=OperationEffects.READ)
def projection_observe(ctx: OpContext, req: dict) -> Result:
    """Verify Core facts for receipt completion and current projection settlement."""
    from learning_os.app.projection_readiness import settlement_ready

    confirmation = req["confirmation"]
    return Result(payload=settlement_ready(
        ctx.root, confirmation["receipt_path"], confirmation["snapshot_after"]))
