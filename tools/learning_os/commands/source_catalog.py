"""Governed registry intake: shelve metadata-only sources, correct intake fields.

`source.intake.record` (`los source-intake`) is the one standalone writer of
the source registry outside plan and migration transactions. It creates a
metadata-only source from intake evidence or corrects intake-owned fields of
an existing record. Evaluations, topics, material, routes, selections, notes,
feedback and observations are never touched here; anything outside the
create/correct allowlist is refused with the field named.

`source.record.revise` (`los source-revise`) is the companion writer for one
existing record: it attaches verified local material (live bytes checked
against both the request hash and the materials manifest) and optionally
replaces a stale evaluation. Identity and intake-owned fields stay with
intake; replacement of a held material is refused outright. Routes without
their own vault_path inherit the record's material, so an attach can move a
dossier's basis: affected approved dossiers must ship reviewed replacements,
validated against the staged state, in the same transaction — or a reviewed
rebase when every moved route is screened, evidence-free, analysis-free and
outside every comparison. The check also lists referring collection entries
so a stale list note is noticed; collection prose itself is corrected through
`collection.entry.revise`, never here.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from learning_os.contracts.gateway import current_gateway_request
from learning_os.contracts.json_schema import validate_contract
from learning_os.domain.failures import WriteRefused
from learning_os.loader import load_repo
from learning_os.material_synthesis import (
    _COMPARED_BASIS_FIELDS,
    MaterialSynthesisError,
    current_unit_material_basis,
    publication_lineage_record,
    validate_unit_material_synthesis,
)
from learning_os.materials_resolution import (
    MATERIAL_SCHEME,
    canonical_material_uri,
    material_uri_authority,
    sha256_file,
)
from learning_os.ops._legacy_plumbing import (
    _dump_yaml,
    _operator_lock,
    _read_structured_file,
)
from learning_os.pathing import PathBoundaryError, resolve_symlinks_inside
from learning_os.revisions import artifact_revision
from learning_os.semantics.lineage import LEDGER_RELATIVE, dump_ledger, load_ledger

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _write_transaction,
)

SOURCE_ID = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*$")
# What a source-record revision may carry. `material` attaches verified local
# bytes to a source that holds none; `evaluations` is an explicit full
# replacement for a stale judgment. Identity and every intake-owned field stay
# with `source.intake.record`; `material_sha256` is request evidence and is
# never stored on the record (the materials manifest owns hashes).
# `material_syntheses` carries reviewed replacement dossiers for exactly the
# units whose approved dossier basis the new material moves.
REVISE_FIELDS = frozenset({"id", "material", "material_sha256", "evaluations",
                           "material_syntheses", "dossier_rebases"})
# Intake's create/correct vocabulary minus identity keys (frozen from the intake
# allowlists, which now live with the converted `source.intake.record`
# handler): revise refuses these with an intake pointer instead of its own
# unknown-field complaint.
INTAKE_OWNED_FIELDS = frozenset({
    "partition", "title", "type", "authors", "organization", "year", "url",
    "identifiers", "remove_url", "remove_identifiers", "discovery",
    "thematic_group_ids",
})
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _input_record(args, label: str) -> dict:
    value = getattr(args, "record", None)
    if value is not None:
        if not isinstance(value, dict):
            raise WriteRefused(f"{label} must be an object")
        return value
    file_name = getattr(args, "file", None)
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


def _require_gateway_v2() -> None:
    from learning_os.contracts.gateway import current_gateway_request

    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


def _refuse_without_approval(args, label: str) -> int | None:
    if getattr(args, "approve", False):
        return None
    print(json.dumps({"ok": False, "error": f"{label} requires explicit approval"}))
    return 2


def _refuse_outside_revise_allowlist(item: dict, sid: str) -> None:
    for field in sorted(set(item) - REVISE_FIELDS):
        if field in INTAKE_OWNED_FIELDS:
            raise WriteRefused(f"{sid}: field '{field}' is owned by intake")
        raise WriteRefused(
            f"{sid}: field '{field}' is outside the revise allowlist "
            "(only 'material' and 'evaluations' are revised here; identity, "
            "intake-owned fields, topics, routes, selections, notes, feedback "
            "and observations are never written through revision)"
        )


def _resolve_revise_material(root: Path, repo, uri: str,
                             sid: str) -> tuple[str, str, int]:
    """Resolve a requested material URI to (manifest key, live sha256, size).

    Resolution follows the runtime exactly (materials_resolution.
    material_location): id-form URIs through ``repo.materials_root`` — the
    .flat/ alias farm when it exists — with no physical-form fallback, so a
    link the learner could not open is refused here instead of recorded. A
    folder-level reference has no single hashable byte string, so only one
    concrete file is attachable.
    """
    authority = material_uri_authority(uri)
    if authority is None:
        raise WriteRefused(f"{sid}: '{uri}' is not a safe material:// URI")
    if authority != sid:
        raise WriteRefused(
            f"{sid}: material URI authority '{authority}' must equal the source id"
        )
    canonical = canonical_material_uri(uri)
    if canonical is not None and canonical != uri:
        raise WriteRefused(
            f"{sid}: '{uri}' is not the canonical material spelling; "
            f"use '{canonical}'"
        )
    payload = str(uri)[len(MATERIAL_SCHEME):]
    physical = repo.learningos_root / "materials"
    if physical.is_symlink() or not physical.is_dir():
        raise WriteRefused(
            f"{sid}: materials tree not mounted at {physical} — attach needs "
            "the live bytes, not just the URI"
        )
    try:
        resolved = resolve_symlinks_inside(
            physical, repo.materials_root / payload, strict=False)
        relative = resolved.relative_to(physical)
    except (OSError, PathBoundaryError, ValueError):
        raise WriteRefused(
            f"{sid}: '{uri}' does not resolve to a file in the materials tree"
        ) from None
    if resolved.is_dir():
        raise WriteRefused(
            f"{sid}: '{uri}' must resolve to one file, not a directory"
        )
    if not resolved.is_file():
        raise WriteRefused(
            f"{sid}: '{uri}' does not resolve to a file in the materials tree"
        )
    digest = sha256_file(resolved)
    live = digest[len("sha256:"):] if digest.startswith("sha256:") else digest
    return relative.as_posix(), live, resolved.stat().st_size


def _read_unit_dossier(path: Path, sid: str, uid: str) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WriteRefused(f"{sid}: cannot read the dossier for '{uid}': {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"{sid}: dossier for '{uid}' is not a mapping")
    return data


def _read_dossier_status(path: Path, sid: str, uid: str):
    return _read_unit_dossier(path, sid, uid).get("status")


def _dossier_digest(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _rebase_routes_or_refuse(sid: str, uid: str, live_basis: dict,
                             staged_basis: dict, by_route: dict,
                             comparisons: list,
                             requested_ids: list) -> list[dict]:
    """Changed routes eligible for the dossier rebase shortcut, else refused.

    The shortcut is deliberately narrow: only `material_checksums` may move,
    and every moved route must be screened, evidence-free, analysis-free and
    outside every comparison. Anything else keeps the full reviewed
    replacement path, where a human re-examines the changed evidence.
    """
    for field in _COMPARED_BASIS_FIELDS:
        if field == "material_checksums":
            continue
        if live_basis.get(field) != staged_basis.get(field):
            raise WriteRefused(
                f"{sid}: unit '{uid}' moves '{field}' too — the rebase shortcut "
                "covers only material_checksums; use a full reviewed replacement"
            )
    live_sums = live_basis.get("material_checksums") or {}
    staged_sums = staged_basis.get("material_checksums") or {}
    if set(live_sums) != set(staged_sums):
        raise WriteRefused(
            f"{sid}: unit '{uid}' gains or loses checksummed routes — use a "
            "full reviewed replacement"
        )
    changed = sorted(rid for rid in live_sums if live_sums[rid] != staged_sums[rid])
    if sorted(requested_ids) != changed:
        raise WriteRefused(
            f"{sid}: unit '{uid}' rebase names route_ids {sorted(requested_ids)} "
            f"but the attach moves {changed}; name exactly the moved routes"
        )
    compared: set[str] = set()
    for comparison in comparisons:
        if isinstance(comparison, dict):
            compared.add(comparison.get("left_route_id"))
            compared.add(comparison.get("right_route_id"))
    moved = []
    for rid in changed:
        if rid in compared:
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' appears in a comparison — "
                "its narrative may depend on the old material; use a full "
                "reviewed replacement"
            )
        assessment = by_route.get(rid) or {}
        status = assessment.get("review_status")
        if status != "screened":
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' is not screened "
                f"({status or 'no status'}) — use a full reviewed replacement"
            )
        if assessment.get("evidence"):
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' carries evidence bound to "
                "the old material; use a full reviewed replacement"
            )
        if assessment.get("analysis_refs"):
            raise WriteRefused(
                f"{sid}: unit '{uid}' route '{rid}' carries analysis references "
                "bound to the old material; use a full reviewed replacement"
            )
        moved.append({"route_id": rid, "before": live_sums[rid],
                      "after": staged_sums[rid],
                      "reason": assessment.get("reason")})
    return moved


def _source_referrers(repo, sid: str) -> dict:
    """Every route, dossier and collection entry naming this source.

    Evidence for the reviewer; the basis comparison in `_plan_revise`
    decides which dossiers the new material actually moves, and collection
    entries are listed so a stale operational claim is noticed — this
    operation never rewrites collection content itself.
    """
    routes = []
    for mid in sorted(repo.module_source_maps or {}):
        entries = (repo.module_source_maps[mid] or {}).get("sources") or []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("source_id") != sid:
                continue
            for route in entry.get("unit_routes") or []:
                if isinstance(route, dict) and route.get("id"):
                    routes.append({
                        "module_id": mid, "unit_id": route.get("unit_id"),
                        "route_id": route.get("id"),
                    })
    routes.sort(key=lambda row: (row["module_id"], row["unit_id"] or "",
                                 row["route_id"]))
    dossiers = set()
    for row in routes:
        unit = (repo.units or {}).get(row["unit_id"])
        path = getattr(unit, "path", None)
        if path is not None and (path.parent / "material-synthesis.yaml").is_file():
            dossiers.add(row["unit_id"])
    collections = []
    for stem in sorted(repo.collections or {}):
        doc = repo.collections[stem] or {}
        for entry in doc.get("entries") or []:
            if isinstance(entry, dict) and entry.get("source") == sid:
                collections.append({"collection": stem,
                                    "group": entry.get("group"),
                                    "why": entry.get("why")})
    return {"routes": routes, "dossiers": sorted(dossiers),
            "collections": collections}


def _plan_revise(root: Path, item: Any) -> dict:
    """Validate one source-record revision; return its diff, writes, guards."""
    if not isinstance(item, dict):
        raise WriteRefused("revise payload must be an object")
    sid = item.get("id")
    if not isinstance(sid, str) or not SOURCE_ID.match(sid):
        raise WriteRefused("'id' must match source-<slug>")
    repo = load_repo(root)
    known = repo.sources.get(sid)
    if known is None:
        raise WriteRefused(f"{sid}: revising an unknown source")
    _refuse_outside_revise_allowlist(item, sid)
    record = dict(known)
    if "material" in item:
        uri = item["material"]
        if not isinstance(uri, str) or not uri.strip():
            raise WriteRefused(f"{sid}: 'material' must be a non-empty string")
        if uri != known.get("material"):
            if known.get("material") is not None:
                raise WriteRefused(
                    f"{sid}: already holds {known['material']} — replacing a "
                    "material binding is not supported; it would orphan every "
                    "route and dossier resolved against those bytes"
                )
            want = item.get("material_sha256")
            if not isinstance(want, str) or not _SHA256_HEX.match(want):
                raise WriteRefused(
                    f"{sid}: a material change needs 'material_sha256' as "
                    "64 lowercase hex"
                )
            key, live, _size = _resolve_revise_material(root, repo, uri, sid)
            manifest_path = root / "records" / "materials-manifest.yaml"
            try:
                manifest = yaml.safe_load(
                    manifest_path.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError):
                manifest = {}
            recorded = manifest.get("files") or {}
            want_row = None
            for row_key, row in recorded.items():
                if (isinstance(row_key, str) and isinstance(row, dict)
                        and unicodedata.normalize("NFC", row_key)
                        == unicodedata.normalize("NFC", key)):
                    want_row = row
                    break
            if want_row is None:
                raise WriteRefused(
                    f"{sid}: '{key}' is absent from the materials manifest — "
                    "run `make inventory` before attaching it"
                )
            if want_row.get("sha256") != live:
                raise WriteRefused(
                    f"{sid}: live bytes of '{key}' do not match the manifest "
                    "entry — rebuild it (`make inventory`) before attaching"
                )
            if live != want:
                raise WriteRefused(
                    f"{sid}: live bytes of '{key}' do not match the request hash"
                )
            record["material"] = uri
    elif "material_sha256" in item:
        raise WriteRefused(f"{sid}: 'material_sha256' without a 'material' change")
    if "evaluations" in item:
        evaluations = item["evaluations"]
        if not isinstance(evaluations, list):
            raise WriteRefused(f"{sid}: 'evaluations' must be a list of evaluation mappings")
        for position, evaluation in enumerate(evaluations):
            sections = (evaluation.get("useful_sections")
                        if isinstance(evaluation, dict) else None)
            if sections is not None and not isinstance(sections, list):
                raise WriteRefused(f"{sid}: evaluations[{position}].useful_sections must be a list")
            for entry in sections or []:
                if isinstance(entry, dict) and ({"locator", "use"} & set(entry)):
                    raise WriteRefused(
                        f"{sid}: evaluations[{position}].useful_sections uses "
                        "'locator'/'use' pseudo-fields — write one "
                        "section-to-note pair per object instead, e.g. "
                        "{'§4.1, physical PDF pp. 141–149': 'Discrete "
                        "conditioning, reversed urn tree, ...'}"
                    )
        record["evaluations"] = item["evaluations"]
    try:
        validate_contract(root, "sources.schema.json", {"sources": [record]})
    except ValueError as exc:
        raise WriteRefused(f"{sid}: {exc}") from exc
    fields = {}
    for field in ("material", "evaluations"):
        old, new = known.get(field), record.get(field)
        if old != new:
            fields[field] = {"before": old, "after": new}
    if not fields:
        raise WriteRefused(f"{sid}: no source-record changes")
    refers = _source_referrers(repo, sid)
    # Routes without their own vault_path inherit this record's material, so an
    # attach can move a dossier's basis without touching any route (SaD L04).
    # Freshness is therefore computed against the PROPOSED record; every unit
    # whose approved basis moves must ship a reviewed replacement validated
    # against that staged state — or a reviewed rebase when the shortcut's
    # strict conditions hold — in this same transaction.
    affected: list[str] = []
    replacements: dict[str, dict] = {}
    rebased: dict[str, dict] = {}
    dossier_writes: dict[Path, str] = {}
    dossier_publications: list[tuple[str, dict, str]] = []
    if "material" in fields:
        syntheses = item.get("material_syntheses", [])
        if not isinstance(syntheses, list):
            raise WriteRefused(f"{sid}: 'material_syntheses' must be a list")
        requested: dict[str, dict] = {}
        for position, entry in enumerate(syntheses):
            where = f"material_syntheses[{position}]"
            if not isinstance(entry, dict) or set(entry) != {"unit_id", "dossier"}:
                raise WriteRefused(f"{where} needs exactly unit_id and dossier")
            uid, dossier = entry["unit_id"], entry["dossier"]
            if not isinstance(uid, str) or not isinstance(dossier, dict):
                raise WriteRefused(f"{where} needs a unit id and a dossier mapping")
            if uid in requested:
                raise WriteRefused(f"{where} replaces '{uid}' twice")
            requested[uid] = dossier
        rebases = item.get("dossier_rebases", [])
        if not isinstance(rebases, list):
            raise WriteRefused(f"{sid}: 'dossier_rebases' must be a list")
        requested_rebases: dict[str, dict] = {}
        for position, entry in enumerate(rebases):
            where = f"dossier_rebases[{position}]"
            if not isinstance(entry, dict) or set(entry) != {
                    "unit_id", "dossier_digest", "route_ids", "provenance"}:
                raise WriteRefused(
                    f"{where} needs exactly unit_id, dossier_digest, "
                    "route_ids and provenance"
                )
            uid, digest, rids, provenance = (
                entry["unit_id"], entry["dossier_digest"],
                entry["route_ids"], entry["provenance"])
            if not isinstance(uid, str):
                raise WriteRefused(f"{where} needs a unit id")
            if not isinstance(digest, str) or not digest:
                raise WriteRefused(f"{where} needs the current dossier digest")
            if (not isinstance(rids, list) or not rids
                    or not all(isinstance(rid, str) for rid in rids)):
                raise WriteRefused(
                    f"{where} 'route_ids' must be a non-empty list of route ids"
                )
            if (not isinstance(provenance, dict)
                    or not all(isinstance(provenance.get(key), str)
                               and provenance.get(key)
                               for key in ("request_id", "delivery_id",
                                           "provider"))):
                raise WriteRefused(
                    f"{where} 'provenance' must carry request_id, "
                    "delivery_id and provider"
                )
            if uid in requested_rebases:
                raise WriteRefused(f"{where} rebases '{uid}' twice")
            requested_rebases[uid] = entry
        staged = copy.copy(repo)
        staged.sources = {**repo.sources, sid: record}
        required: list[str] = []
        bases: dict[str, tuple[dict, dict]] = {}
        for uid in refers["dossiers"]:
            unit = (repo.units or {}).get(uid)
            if unit is None or getattr(unit, "path", None) is None:
                raise WriteRefused(f"{sid}: unit '{uid}' is not registered")
            try:
                live_basis = current_unit_material_basis(root, uid, repo=repo, cache={})
                staged_basis = current_unit_material_basis(root, uid, repo=staged, cache={})
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: cannot establish the dossier basis for '{uid}': {exc}"
                ) from exc
            if any(live_basis[field] != staged_basis[field]
                   for field in _COMPARED_BASIS_FIELDS):
                affected.append(uid)
                bases[uid] = (live_basis, staged_basis)
                dossier_path = unit.path.parent / "material-synthesis.yaml"
                if _read_dossier_status(dossier_path, sid, uid) == "approved":
                    required.append(uid)
        for uid in requested:
            if uid not in required:
                raise WriteRefused(
                    f"{sid}: replacement dossier for '{uid}' is not needed "
                    "(no approved dossier basis changes there)"
                )
        for uid in requested_rebases:
            if uid in requested:
                raise WriteRefused(
                    f"{sid}: unit '{uid}' takes only one of "
                    "'material_syntheses' and 'dossier_rebases'"
                )
            if uid not in required:
                unit = (repo.units or {}).get(uid)
                if unit is None:
                    raise WriteRefused(
                        f"{sid}: unit '{uid}' is not registered"
                    )
                unit_path = getattr(unit, "path", None)
                dossier_path = (unit_path.parent / "material-synthesis.yaml"
                                if unit_path is not None else None)
                if dossier_path is not None and not dossier_path.exists():
                    raise WriteRefused(
                        f"{sid}: rebase for '{uid}' has no dossier to rebase "
                        "(no material-synthesis.yaml there)"
                    )
                raise WriteRefused(
                    f"{sid}: rebase for '{uid}' is not needed "
                    "(no approved dossier basis changes there)"
                )
        for uid in required:
            if uid not in requested and uid not in requested_rebases:
                raise WriteRefused(
                    f"{sid}: attaching material changes the approved dossier "
                    f"basis for '{uid}'; supply a reviewed replacement dossier "
                    "under 'material_syntheses' or a rebase under "
                    "'dossier_rebases'"
                )
        for uid in sorted(requested):
            try:
                validate_unit_material_synthesis(root, uid, requested[uid], repo=staged)
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: replacement dossier for '{uid}' is not valid: {exc}"
                ) from exc
            unit = repo.units[uid]
            dossier_path = unit.path.parent / "material-synthesis.yaml"
            live_provenance = (
                _read_unit_dossier(dossier_path, sid, uid).get("basis") or {}
            ).get("ai_provenance")
            submitted = (requested[uid].get("basis") or {}).get("ai_provenance")
            if submitted == live_provenance:
                raise WriteRefused(
                    f"{sid}: replacement dossier for '{uid}' reuses the live "
                    "dossier's provenance unchanged — stamp the reviewed "
                    "replacement with its own request_id/delivery_id "
                    "(provenance must identify the event that produced the "
                    "new basis, as the publish gate requires)"
                )
            dossier_writes[dossier_path] = _dump_yaml(requested[uid])
            dossier_publications.append((uid, requested[uid], dossier_writes[dossier_path]))
        replacements = {uid: requested[uid] for uid in sorted(requested)}
        for uid in sorted(requested_rebases):
            entry = requested_rebases[uid]
            unit = repo.units[uid]
            dossier_path = unit.path.parent / "material-synthesis.yaml"
            live_dossier = _read_unit_dossier(dossier_path, sid, uid)
            if _dossier_digest(live_dossier) != entry["dossier_digest"]:
                raise WriteRefused(
                    f"{sid}: dossier for '{uid}' changed since the rebase was "
                    "prepared; re-run --check"
                )
            live_provenance = (live_dossier.get("basis") or {}).get("ai_provenance")
            if entry["provenance"] == live_provenance:
                raise WriteRefused(
                    f"{sid}: rebase for '{uid}' reuses the live dossier's "
                    "provenance unchanged — stamp the rebase with its own "
                    "request_id/delivery_id (provenance must identify the "
                    "event that produced the new basis, as the publish gate "
                    "requires)"
                )
            by_route = {row["route_id"]: row
                        for row in live_dossier.get("route_assessments", []) or []
                        if isinstance(row, dict) and row.get("route_id")}
            live_basis, staged_basis = bases[uid]
            moved = _rebase_routes_or_refuse(
                sid, uid, live_basis, staged_basis, by_route,
                live_dossier.get("comparisons", []) or [],
                entry["route_ids"])
            try:
                validate_unit_material_synthesis(root, uid, live_dossier, repo=repo)
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: dossier for '{uid}' is already stale: {exc}; use "
                    "a full reviewed replacement"
                ) from exc
            rebased_dossier = copy.deepcopy(live_dossier)
            rebased_dossier["basis"] = {
                **staged_basis, "ai_provenance": entry["provenance"]}
            try:
                validate_unit_material_synthesis(root, uid, rebased_dossier, repo=staged)
            except MaterialSynthesisError as exc:
                raise WriteRefused(
                    f"{sid}: rebased dossier for '{uid}' is not valid: {exc}"
                ) from exc
            dossier_writes[dossier_path] = _dump_yaml(rebased_dossier)
            dossier_publications.append((uid, rebased_dossier, dossier_writes[dossier_path]))
            rebased[uid] = {"routes": moved,
                            "dossier_digest": entry["dossier_digest"],
                            "provenance": entry["provenance"]}
    elif "material_syntheses" in item:
        raise WriteRefused(f"{sid}: 'material_syntheses' without a 'material' change")
    elif "dossier_rebases" in item:
        raise WriteRefused(f"{sid}: 'dossier_rebases' without a 'material' change")
    origin = repo.source_origins.get(sid)
    destination = Path(origin) if origin else root / "sources" / "sources.yaml"
    try:
        current = yaml.safe_load(destination.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot re-read {destination}: {exc}") from exc
    if not isinstance(current, dict) or not isinstance(current.get("sources"), list):
        raise WriteRefused(f"{destination} is not a source registry file")
    merged = [record if (isinstance(entry, dict) and entry.get("id") == sid)
              else entry for entry in current["sources"]]
    try:
        filename = destination.resolve().relative_to(
            (root / "sources").resolve()).as_posix()
    except ValueError:
        filename = destination.name
    diff = [{"id": sid, "partition": filename, "fields": fields,
             "refers": refers, "affected_units": affected,
             "replacements": replacements, "rebases": rebased}]
    canonical = json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    writes = {destination: _dump_yaml({"sources": merged})}
    writes.update(dossier_writes)
    unit_ids = sorted(set(replacements) | set(rebased))
    revisions = {sid: artifact_revision(root, sid)}
    revisions.update({uid: artifact_revision(root, uid) for uid in unit_ids})
    return {
        "diff": diff,
        "diff_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "writes": writes,
        "dossier_publications": dossier_publications,
        "artifact_ids": [sid] + unit_ids,
        "expected_revisions": revisions,
    }


def cmd_source_record_revise(args) -> int:
    """Attach verified local material to one existing source, atomically."""
    root = _root(args)
    try:
        data = _input_record(args, "revise record")
        plan = _plan_revise(root, data)
    except WriteRefused as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    if getattr(args, "check", False):
        print(json.dumps({
            "ok": True, "check": True, "records": len(plan["diff"]),
            "diff": plan["diff"], "diff_sha256": plan["diff_sha256"],
            "expected_revisions": plan["expected_revisions"],
            "artifact_ids": plan["artifact_ids"],
        }, indent=2, ensure_ascii=False))
        return 0
    denied = _refuse_without_approval(args, "source revision")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        try:
            plan = _plan_revise(root, data)
        except WriteRefused as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 2
        expected_diff = getattr(args, "expected_diff_sha256", None)
        if not expected_diff:
            print(json.dumps({"ok": False, "error":
                              "apply needs --expected-diff-sha256 from a check run"}))
            return 2
        if expected_diff != plan["diff_sha256"]:
            print(json.dumps({"ok": False, "error":
                              "revision diff changed since check; re-run --check"}))
            return 2
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        if plan["dossier_publications"]:
            records = load_ledger(root)
            request = current_gateway_request()
            for uid, dossier, content in plan["dossier_publications"]:
                claim_id = f"dossier:{dossier['id']}"
                records[claim_id] = publication_lineage_record(
                    root, uid, dossier, content, request, prior=records.get(claim_id))
            plan["writes"][root / LEDGER_RELATIVE] = dump_ledger(records)
        code, errors, confirmation = _write_transaction(
            root,
            plan["writes"],
            capability="source.record.revise",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=tuple(plan["artifact_ids"]),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code
