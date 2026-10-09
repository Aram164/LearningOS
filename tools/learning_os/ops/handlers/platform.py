"""Platform-area converted handlers: the shared inspect unit (PLAN D4).

``cli.inspect`` and ``project.inspect`` are one conversion unit (SPEC §12.7):
both names register on the one moved handler. The inspect-only helpers moved
with the unit from ``commands.reads`` (SPEC (az) item 2).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from learning_os.domain.failures import StaleSnapshot, WriteRefused
from learning_os.domain.suggest import not_found, with_suggestions
from learning_os.ops._legacy_plumbing import (
    _fresh_manifest_and_repo,
    _json_layout,
    _snapshot,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError, read_bytes_inside


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
    if repo is not None:
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


def _inspect_candidates(manifest: dict, repo=None) -> list[str]:
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
    if repo is not None:
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


def _dumps_single(payload: dict) -> str:
    """The exact single-inspect encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def _dumps_batch(payload: dict) -> str:
    """The exact batch-inspect encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _inspect_batch(ctx: OpContext, req: dict) -> Result:
    """Resolve a requested batch once; never return a partial or mixed read."""
    ids = [req["id"], *req["more_ids"]]
    if len(ids) > 20:
        raise WriteRefused(
            "inspect accepts at most 20 IDs per batch",
            site=f"{ctx.operation}.too-many-ids",
            gateway_message="los: inspect accepts at most 20 IDs per batch",
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
                    record_id, _inspect_candidates(manifest, repo))
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
            json_dumps=_dumps_batch,
        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            gateway_message=f"los: {exc}",
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc


@register("cli.inspect", kind="query")
@register("project.inspect", kind="query")
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
    return Result(payload, json_dumps=_dumps_single)
