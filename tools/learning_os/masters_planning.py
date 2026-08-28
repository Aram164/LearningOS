"""Sanitized, deliberately opened Future Master's Planning boundary.

Normal repository loading never imports this catalog.  This module reads only
the exact sanitized catalog and approved comparison files after an explicit
gesture; raw planning inputs are not traversed or parsed here.
"""

from __future__ import annotations

import copy
import datetime as dt
import difflib
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from learning_os.contracts.json_schema import validate_contract
from learning_os.loader import load_repo
from learning_os.transactions import artifact_revision


class MastersPlanningError(ValueError):
    pass


_FORBIDDEN_KEYS = frozenset({
    "job", "employer", "credential", "credentials", "account", "account_id",
    "private_url", "secret", "token", "application_material", "contact_details",
})

_PROMOTION_VERIFICATION_MAX_AGE_DAYS = 30


@dataclass(frozen=True)
class MasterPromotionPlan:
    """One fully checked promotion transaction, before any canonical write."""

    package_sha256: str
    writes: dict[Path, str]
    artifact_ids: tuple[str, ...]
    expected_revisions: dict[str, int]
    affected_paths: tuple[str, ...]
    diff: str
    updated_catalog: dict[str, Any]
    provenance: dict[str, Any]


def _assert_academic_only(value: Any, *, pointer: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            name = str(key).casefold().replace("-", "_")
            if name in _FORBIDDEN_KEYS:
                raise MastersPlanningError(
                    f"sanitized Master Planning input contains forbidden field at {pointer}/{key}"
                )
            _assert_academic_only(child, pointer=f"{pointer}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_academic_only(child, pointer=f"{pointer}/{index}")


def _sanitized_file(
    root: Path,
    path: Path,
    *,
    label: str,
    required: bool,
) -> Path | None:
    """Resolve one exact sanitized file without following any indirection."""
    root = root.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise MastersPlanningError(f"{label} escapes the repository") from exc
    cursor = root
    for index, component in enumerate(relative.parts):
        cursor = cursor / component
        if cursor.is_symlink():
            raise MastersPlanningError(f"{label} traverses a symlink")
        if index < len(relative.parts) - 1 and cursor.exists() \
                and not cursor.is_dir():
            raise MastersPlanningError(f"{label} parent is not a directory")
    if not cursor.exists():
        if required:
            raise MastersPlanningError(f"{label} is missing")
        return None
    if not cursor.is_file():
        raise MastersPlanningError(f"{label} is not a regular file")
    try:
        cursor.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise MastersPlanningError(f"{label} escapes the repository") from exc
    return cursor


def _read_yaml_object(root: Path, path: Path, *, label: str) -> dict[str, Any]:
    safe_path = _sanitized_file(root, path, label=label, required=True)
    assert safe_path is not None  # required=True
    try:
        value = yaml.safe_load(safe_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise MastersPlanningError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise MastersPlanningError(f"{label} must be an object")
    return value


def _dump_yaml(value: dict[str, Any]) -> str:
    return yaml.safe_dump(
        value,
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


def promotion_package_sha256(value: dict[str, Any]) -> str:
    """Return the review token for the exact inline promotion package."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _record_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def master_promotion_destination(root: Path, promotion_id: str) -> Path:
    return (
        root / "curriculum" / "quarantine" / "masters-planning" /
        "promotions" / f"{promotion_id}.yaml"
    )


def _utc_now(value: dt.datetime | None) -> dt.datetime:
    current = value or dt.datetime.now(dt.UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.UTC)
    return current.astimezone(dt.UTC).replace(microsecond=0)


def _parse_date(value: Any, *, label: str) -> dt.date:
    if not isinstance(value, str):
        raise MastersPlanningError(f"{label} must be an ISO date")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise MastersPlanningError(f"{label} must be an ISO date") from exc


def _parse_datetime(value: Any, *, label: str) -> dt.datetime:
    if not isinstance(value, str):
        raise MastersPlanningError(f"{label} must be an ISO date-time")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MastersPlanningError(f"{label} must be an ISO date-time") from exc
    if parsed.tzinfo is None:
        raise MastersPlanningError(f"{label} must include a timezone")
    return parsed.astimezone(dt.UTC)


def _require_fresh_date(value: Any, *, label: str, today: dt.date) -> dt.date:
    parsed = _parse_date(value, label=label)
    age = (today - parsed).days
    if age < 0:
        raise MastersPlanningError(f"{label} cannot be in the future")
    if age > _PROMOTION_VERIFICATION_MAX_AGE_DAYS:
        raise MastersPlanningError(
            f"{label} is stale ({age} days old; maximum is "
            f"{_PROMOTION_VERIFICATION_MAX_AGE_DAYS})"
        )
    return parsed


def _require_current_fact_state(
    row: dict[str, Any],
    *,
    label: str,
    today: dt.date,
) -> None:
    fact_state = row.get("fact_state")
    if not isinstance(fact_state, dict) \
            or fact_state.get("status") != "verified-current":
        raise MastersPlanningError(f"{label} must be verified-current")
    _require_fresh_date(
        fact_state.get("as_of"),
        label=f"{label} fact_state.as_of",
        today=today,
    )
    evidence = fact_state.get("evidence")
    if not isinstance(evidence, list) or not evidence \
            or any(not isinstance(item, str) or not item.strip() for item in evidence):
        raise MastersPlanningError(f"{label} must retain verification evidence")


def _safe_academic_reference(root: Path, value: Any, *, label: str) -> Path:
    """Resolve an explicitly named academic evidence path without crossing a boundary."""

    if not isinstance(value, str) or not value.strip():
        raise MastersPlanningError(f"{label} must name a repository-relative file")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise MastersPlanningError(f"{label} must stay inside the repository")
    forbidden_components = {
        "job", "legacy", "master", "masters-planning", "quarantine",
    }
    lowered = {part.casefold() for part in relative.parts}
    if lowered & forbidden_components:
        raise MastersPlanningError(f"{label} crosses a sealed planning boundary")
    lexical = root
    for component in relative.parts:
        lexical = lexical / component
        if lexical.is_symlink():
            raise MastersPlanningError(
                f"{label} may not traverse a symlink component"
            )
    try:
        resolved = lexical.resolve(strict=True)
        resolved_relative = resolved.relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise MastersPlanningError(f"{label} is not a safe repository file") from exc
    if {part.casefold() for part in resolved_relative.parts} & forbidden_components:
        raise MastersPlanningError(
            f"{label} resolves across a sealed planning boundary"
        )
    if not resolved.is_file():
        raise MastersPlanningError(f"{label} is not a regular file")
    return resolved


def _source_ids_in(value: Any) -> set[str]:
    """Collect canonical source references from one sanitized module plan."""

    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "source_id" and isinstance(child, str):
                found.add(child)
            elif key in {"source_ids", "sources"} and isinstance(child, list) \
                    and all(isinstance(item, str) for item in child):
                found.update(child)
            _source_ids_in_into(child, found)
    elif isinstance(value, list):
        for child in value:
            _source_ids_in_into(child, found)
    return found


def _source_ids_in_into(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "source_id" and isinstance(child, str):
                found.add(child)
            elif key in {"source_ids", "sources"} and isinstance(child, list) \
                    and all(isinstance(item, str) for item in child):
                found.update(child)
            _source_ids_in_into(child, found)
    elif isinstance(value, list):
        for child in value:
            _source_ids_in_into(child, found)


def _assert_no_sealed_references(value: Any, *, pointer: str = "") -> None:
    """Reject path-shaped module-plan values that could reactivate sealed inputs."""

    path_keys = {
        "coverage_audit", "material", "path", "proposal_path", "url",
        "vault_path", "working_note",
    }
    forbidden = {"job", "legacy", "master", "masters-planning", "quarantine"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in path_keys and isinstance(child, str):
                normalized = child.casefold().replace("\\", "/")
                components = {
                    part for part in normalized.replace("://", "/").split("/") if part
                }
                if components & forbidden or normalized.startswith("file:"):
                    raise MastersPlanningError(
                        f"promoted module plan references a sealed path at {pointer}/{key}"
                    )
            _assert_no_sealed_references(child, pointer=f"{pointer}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_sealed_references(child, pointer=f"{pointer}/{index}")


def _promotion_diff(root: Path, writes: dict[Path, str]) -> str:
    chunks: list[str] = []
    for path in sorted(writes, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        before = path.read_text(encoding="utf-8") if path.is_file() else ""
        chunks.extend(difflib.unified_diff(
            before.splitlines(keepends=True),
            writes[path].splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        ))
    return "".join(chunks)


def _safe_source_registry_target(root: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    permitted = relative == Path("sources/sources.yaml") or (
        len(relative.parts) == 3
        and relative.parts[:2] == ("sources", "registry")
        and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.yaml", relative.name)
    )
    if not permitted:
        raise MastersPlanningError(
            f"new canonical source registry target is out of scope: {relative_value}"
        )
    lexical = root
    for index, component in enumerate(relative.parts):
        lexical = lexical / component
        if lexical.is_symlink():
            raise MastersPlanningError(
                f"new canonical source registry target traverses a symlink: {relative_value}"
            )
        if index < len(relative.parts) - 1 and lexical.exists() \
                and not lexical.is_dir():
            raise MastersPlanningError(
                f"new canonical source registry parent is not a directory: {relative_value}"
            )
    if lexical.exists() and not lexical.is_file():
        raise MastersPlanningError(
            f"new canonical source registry target is not a regular file: {relative_value}"
        )
    try:
        lexical.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise MastersPlanningError(
            f"new canonical source registry target escapes the repository: {relative_value}"
        ) from exc
    return lexical


def _render_source_list_item(record: dict[str, Any]) -> str:
    lines = _dump_yaml(record).rstrip().splitlines()
    rendered = "- " + lines[0] + "\n"
    rendered += "\n".join("  " + line if line else "" for line in lines[1:])
    return rendered.rstrip() + "\n"


def _append_source_record(
    root: Path,
    path: Path,
    record: dict[str, Any],
    *,
    current_text: str | None = None,
) -> str:
    """Append one source without reformatting any existing registry sibling."""

    if current_text is None and path.is_file():
        current_text = path.read_text(encoding="utf-8")
    item = _render_source_list_item(record)
    if current_text is None:
        rendered = "sources:\n" + item
    else:
        try:
            document = yaml.safe_load(current_text)
        except yaml.YAMLError as exc:
            raise MastersPlanningError(
                f"cannot parse explicit source registry target {path.relative_to(root)}: {exc}"
            ) from exc
        if not isinstance(document, dict) or set(document) != {"sources"} \
                or not isinstance(document["sources"], list):
            raise MastersPlanningError(
                f"explicit source registry target has an unsupported shape: "
                f"{path.relative_to(root)}"
            )
        if any(
            isinstance(row, dict) and row.get("id") == record["id"]
            for row in document["sources"]
        ):
            raise MastersPlanningError(
                f"explicit source registry target already contains {record['id']}"
            )
        if document["sources"]:
            rendered = current_text.rstrip() + "\n" + item
        else:
            empty = re.compile(r"^(?P<indent>[ ]*)sources:[ ]*\[\][ ]*$", re.MULTILINE)
            match = empty.search(current_text)
            if match is None:
                raise MastersPlanningError(
                    f"empty source registry target is not appendable without reformatting: "
                    f"{path.relative_to(root)}"
                )
            replacement = f"{match.group('indent')}sources:\n" + item
            rendered = current_text[:match.start()] + replacement + current_text[match.end():]
            if not rendered.endswith("\n"):
                rendered += "\n"
    try:
        parsed = yaml.safe_load(rendered)
        validate_contract(root, "sources.schema.json", parsed)
    except (ValueError, yaml.YAMLError) as exc:
        raise MastersPlanningError(
            f"new canonical source would invalidate {path.relative_to(root)}: {exc}"
        ) from exc
    return rendered


def validate_master_catalog(
    root: Path,
    value: dict[str, Any],
    *,
    planned_canonical_source_ids: set[str] | frozenset[str] = frozenset(),
) -> dict[str, Any]:
    _assert_academic_only(value)
    try:
        validate_contract(root, "master-planning-catalog.schema.json", value)
    except ValueError as exc:
        raise MastersPlanningError(str(exc)) from exc
    module_ids = [row["id"] for row in value["candidate_modules"]]
    source_ids = [row["id"] for row in value["candidate_sources"]]
    if len(module_ids) != len(set(module_ids)):
        raise MastersPlanningError("Master Planning catalog has duplicate candidate module IDs")
    if len(source_ids) != len(set(source_ids)):
        raise MastersPlanningError("Master Planning catalog has duplicate candidate source IDs")
    source_set = set(source_ids)
    for module in value["candidate_modules"]:
        unknown = sorted(set(module["source_ids"]) - source_set)
        if unknown:
            raise MastersPlanningError(
                f"{module['id']} references unknown candidate sources: {unknown}"
            )
        if module["planning_state"] == "promoted" and not module.get("promoted_module_id"):
            raise MastersPlanningError(
                f"{module['id']} is promoted but has no canonical module mapping"
            )
        if module.get("promoted_module_id") and module["planning_state"] != "promoted":
            raise MastersPlanningError(
                f"{module['id']} has a canonical mapping but is not promoted"
            )
    repo = load_repo(root)
    for source in value["candidate_sources"]:
        canonical = source.get("canonical_source_id")
        if canonical and canonical not in repo.sources \
                and canonical not in planned_canonical_source_ids:
            raise MastersPlanningError(
                f"{source['id']} maps to unknown canonical source: {canonical}"
            )
    return value


def master_catalog_destination(root: Path) -> Path:
    return root / "curriculum" / "quarantine" / "masters-planning" / "catalog.yaml"


def load_master_catalog(root: Path) -> dict[str, Any] | None:
    path = master_catalog_destination(root)
    safe_path = _sanitized_file(
        root,
        path,
        label="Master Planning catalog",
        required=False,
    )
    if safe_path is None:
        return None
    return validate_master_catalog(
        root,
        _read_yaml_object(root, safe_path, label="Master Planning catalog"),
    )


def validate_catalog_revision(root: Path, value: dict[str, Any]) -> None:
    current = load_master_catalog(root)
    expected = 0 if current is None else int(current["revision"]) + 1
    if value.get("revision") != expected:
        raise MastersPlanningError(
            f"catalog revision must be {expected}; got {value.get('revision')}"
        )


def prepare_master_promotion(
    root: Path,
    value: dict[str, Any],
    *,
    now: dt.datetime | None = None,
) -> MasterPromotionPlan:
    """Prepare exactly one selected prospective bundle for an atomic import.

    Only the exact sanitized catalog is opened.  Comparisons and raw planning
    originals are preserved by reference and are never traversed here.
    """

    _assert_academic_only(value)
    try:
        validate_contract(root, "master-planning-promotion.schema.json", value)
    except ValueError as exc:
        raise MastersPlanningError(str(exc)) from exc

    current_time = _utc_now(now)
    today = current_time.date()
    recorded_at = _parse_datetime(value["recorded_at"], label="recorded_at")
    if recorded_at > current_time:
        raise MastersPlanningError("recorded_at cannot be in the future")

    verification = value["verification"]
    verified_as_of = _require_fresh_date(
        verification["as_of"],
        label="verification.as_of",
        today=today,
    )
    for index, evidence in enumerate(verification["evidence"]):
        verified_on = _require_fresh_date(
            evidence["verified_on"],
            label=f"verification.evidence[{index}].verified_on",
            today=today,
        )
        if verified_on < verified_as_of:
            raise MastersPlanningError(
                f"verification.evidence[{index}].verified_on predates verification.as_of"
            )

    catalog = load_master_catalog(root)
    if catalog is None:
        raise MastersPlanningError("a sanitized Master Planning catalog is required")
    catalog_updated_at = _parse_datetime(
        catalog["updated_at"],
        label="catalog.updated_at",
    )
    if catalog_updated_at > current_time:
        raise MastersPlanningError("catalog.updated_at cannot be in the future")
    if recorded_at < catalog_updated_at:
        raise MastersPlanningError(
            "recorded_at cannot precede the current sanitized catalog update"
        )
    if value["catalog_revision"] != catalog["revision"]:
        raise MastersPlanningError(
            "promotion package was prepared against a stale catalog revision"
        )

    candidate_module_id = value["candidate_module_id"]
    canonical_module_id = value["canonical_module_id"]
    modules = {row["id"]: row for row in catalog["candidate_modules"]}
    sources = {row["id"]: row for row in catalog["candidate_sources"]}
    candidate_module = modules.get(candidate_module_id)
    if candidate_module is None:
        raise MastersPlanningError(
            f"promotion targets unknown candidate module: {candidate_module_id}"
        )
    if candidate_module["planning_state"] != "selected":
        raise MastersPlanningError(
            f"{candidate_module_id} must be selected before promotion"
        )
    if candidate_module.get("promoted_module_id"):
        raise MastersPlanningError(f"{candidate_module_id} was already promoted")
    if candidate_module["unresolved_references"]:
        raise MastersPlanningError(
            f"{candidate_module_id} has unresolved references; promotion never guesses"
        )
    _require_current_fact_state(
        candidate_module,
        label=candidate_module_id,
        today=today,
    )

    repo = load_repo(root)
    if canonical_module_id in repo.modules:
        raise MastersPlanningError(
            f"promotion canonical module already exists: {canonical_module_id}"
        )
    module_directory = root / "curriculum" / "modules" / canonical_module_id
    if module_directory.exists() or module_directory.is_symlink():
        raise MastersPlanningError(
            f"promotion target module directory already exists: {canonical_module_id}"
        )

    adopted = value["adopted_sources"]
    candidate_source_ids = [row["candidate_source_id"] for row in adopted]
    canonical_source_ids = [row["canonical_source_id"] for row in adopted]
    if len(candidate_source_ids) != len(set(candidate_source_ids)):
        raise MastersPlanningError("adopted candidate source mappings must be unique")
    if len(canonical_source_ids) != len(set(canonical_source_ids)):
        raise MastersPlanningError("adopted canonical source mappings must be unique")
    available_for_module = set(candidate_module["source_ids"])
    new_source_ids: set[str] = set()
    registry_texts: dict[Path, str] = {}
    source_provenance_mappings: list[dict[str, Any]] = []
    for mapping in adopted:
        candidate_source_id = mapping["candidate_source_id"]
        canonical_source_id = mapping["canonical_source_id"]
        if candidate_source_id not in available_for_module:
            raise MastersPlanningError(
                f"{candidate_source_id} is not part of {candidate_module_id}"
            )
        candidate_source = sources.get(candidate_source_id)
        if candidate_source is None:
            raise MastersPlanningError(
                f"promotion maps unknown candidate source: {candidate_source_id}"
            )
        if candidate_source["planning_state"] != "selected":
            raise MastersPlanningError(
                f"adopted source {candidate_source_id} must be selected"
            )
        if candidate_source.get("canonical_source_id"):
            raise MastersPlanningError(
                f"candidate source was already promoted: {candidate_source_id}"
            )
        _require_current_fact_state(
            candidate_source,
            label=candidate_source_id,
            today=today,
        )
        new_source = mapping.get("canonical_source")
        registry_target = mapping.get("registry_target")
        if canonical_source_id in repo.sources:
            if new_source is not None or registry_target is not None:
                raise MastersPlanningError(
                    f"{candidate_source_id} maps to an existing canonical source and "
                    "may not replace or relocate it"
                )
            canonical_source = repo.sources[canonical_source_id]
            source_provenance_mappings.append({
                "candidate_source_id": candidate_source_id,
                "canonical_source_id": canonical_source_id,
                "created": False,
                "source_record_sha256": _record_sha256(canonical_source),
            })
            continue
        if not isinstance(new_source, dict) or not isinstance(registry_target, str):
            raise MastersPlanningError(
                f"{candidate_source_id} maps to unknown canonical source "
                f"{canonical_source_id}; supply its exact canonical_source record "
                "and explicit registry_target or resolve the mapping"
            )
        if new_source.get("id") != canonical_source_id:
            raise MastersPlanningError(
                f"new canonical source record ID disagrees with mapping for "
                f"{candidate_source_id}"
            )
        try:
            validate_contract(root, "sources.schema.json", {"sources": [new_source]})
        except ValueError as exc:
            raise MastersPlanningError(str(exc)) from exc
        _assert_no_sealed_references(new_source)
        source_url = new_source.get("url")
        if source_url is not None and not source_url.startswith("https://"):
            raise MastersPlanningError(
                f"new canonical source {canonical_source_id} URL must use HTTPS"
            )
        material = new_source.get("material")
        if material is not None:
            prefix = f"material://{canonical_source_id}"
            if material != prefix and not material.startswith(prefix + "/"):
                raise MastersPlanningError(
                    f"new canonical source {canonical_source_id} material URI must "
                    "stay inside its own material namespace"
                )
            if ".." in Path(material.removeprefix("material://")).parts:
                raise MastersPlanningError(
                    f"new canonical source {canonical_source_id} material URI traverses"
                )
        serialized_source = json.dumps(new_source, ensure_ascii=False, sort_keys=True)
        leaked_source_ids = sorted(
            candidate_id
            for candidate_id in {*modules, *sources}
            if candidate_id in serialized_source
        )
        if leaked_source_ids:
            raise MastersPlanningError(
                "candidate IDs may not leak into a canonical source record: "
                f"{leaked_source_ids}"
            )
        target = _safe_source_registry_target(root, registry_target)
        registry_texts[target] = _append_source_record(
            root,
            target,
            new_source,
            current_text=registry_texts.get(target),
        )
        new_source_ids.add(canonical_source_id)
        source_provenance_mappings.append({
            "candidate_source_id": candidate_source_id,
            "canonical_source_id": canonical_source_id,
            "created": True,
            "source_record_sha256": _record_sha256(new_source),
            "registry_target": registry_target,
        })

    package = value["module_plan"]
    _assert_no_sealed_references(package)
    serialized_package = json.dumps(package, ensure_ascii=False, sort_keys=True)
    leaked_candidate_ids = sorted(
        candidate_id
        for candidate_id in {*modules, *sources}
        if candidate_id in serialized_package
    )
    if leaked_candidate_ids:
        raise MastersPlanningError(
            "candidate IDs may not leak into the canonical module bundle: "
            f"{leaked_candidate_ids}"
        )
    if package["module_id"] != canonical_module_id \
            or package["module_patch"]["id"] != canonical_module_id \
            or package["source_map"]["module_id"] != canonical_module_id:
        raise MastersPlanningError(
            "candidate-to-canonical module mapping disagrees with the module bundle"
        )
    if package["module_patch"]["status"] != "planned":
        raise MastersPlanningError(
            "a promoted prospective module must enter canonical state as planned"
        )
    if package["module_patch"]["source_map"] != "source-map.yaml":
        raise MastersPlanningError(
            "promoted module source_map must be the canonical source-map.yaml"
        )
    if package["module_patch"]["area_id"] not in repo.programs:
        raise MastersPlanningError(
            "promoted module maps to an unknown canonical program"
        )

    _safe_academic_reference(
        root,
        package["plan_contract"]["coverage_audit"],
        label="module_plan.plan_contract.coverage_audit",
    )
    adopted_canonical = set(canonical_source_ids)
    source_map_ids = [row["source_id"] for row in package["source_map"]["sources"]]
    if len(source_map_ids) != len(set(source_map_ids)):
        raise MastersPlanningError("promoted source map contains duplicate sources")
    if set(source_map_ids) != adopted_canonical:
        raise MastersPlanningError(
            "promoted source map must contain exactly the explicitly adopted sources"
        )
    referenced_sources = _source_ids_in(package)
    if referenced_sources != adopted_canonical:
        missing = sorted(adopted_canonical - referenced_sources)
        unadopted = sorted(referenced_sources - adopted_canonical)
        raise MastersPlanningError(
            "promoted bundle source references must equal the adopted source mapping "
            f"(missing={missing}, unadopted={unadopted})"
        )

    units = package["units"]
    unit_ids = [entry["unit"]["id"] for entry in units]
    if len(unit_ids) != len(set(unit_ids)):
        raise MastersPlanningError("promoted module contains duplicate unit IDs")
    if package["module_patch"]["unit_order"] != unit_ids:
        raise MastersPlanningError(
            "promoted module unit_order must list every bundled unit exactly once in bundle order"
        )
    existing_units = sorted(set(unit_ids) & set(repo.units))
    if existing_units:
        raise MastersPlanningError(
            f"promotion refuses existing canonical unit IDs: {existing_units}"
        )
    route_ids: list[str] = []
    for source in package["source_map"]["sources"]:
        if source["role"] == "candidate":
            raise MastersPlanningError(
                f"promoted canonical source {source['source_id']} may not retain candidate role"
            )
        routes = source.get("unit_routes")
        if not isinstance(routes, list) or not routes:
            raise MastersPlanningError(
                f"adopted source {source['source_id']} must have at least one stable route"
            )
        for route in routes:
            if not isinstance(route, dict) or not isinstance(route.get("id"), str):
                raise MastersPlanningError(
                    "newly promoted source routes require stable route-* IDs"
                )
            if route["unit_id"] not in set(unit_ids):
                raise MastersPlanningError(
                    f"{route['id']} routes outside the promoted module bundle"
                )
            route_ids.append(route["id"])
    if len(route_ids) != len(set(route_ids)):
        raise MastersPlanningError("promoted source routes must have unique route IDs")

    writes: dict[Path, str] = {
        module_directory / "module.yaml": _dump_yaml(package["module_patch"]),
        module_directory / "source-map.yaml": _dump_yaml(package["source_map"]),
        **registry_texts,
    }
    study_map_ids: list[str] = []
    stage_note_paths: set[Path] = set()
    for entry in units:
        unit = entry["unit"]
        unit_id = unit["id"]
        if unit["module_id"] != canonical_module_id:
            raise MastersPlanningError(f"{unit_id} belongs to a different module")
        if unit["status"] not in {"needs-map", "not-started", "ready"}:
            raise MastersPlanningError(
                f"promoted planned unit {unit_id} may not enter an active/completed state"
            )
        unit_directory = module_directory / "units" / unit_id
        writes[unit_directory / "unit.yaml"] = _dump_yaml(unit)
        study_map = entry.get("study_map")
        if study_map is None:
            if unit.get("current_study_map"):
                raise MastersPlanningError(
                    f"{unit_id} names a current study map that is not bundled"
                )
            continue
        if study_map["unit_id"] != unit_id \
                or unit.get("current_study_map") != study_map["id"]:
            raise MastersPlanningError(
                f"bundled study map/current_study_map mapping disagrees for {unit_id}"
            )
        _safe_academic_reference(
            root,
            study_map["source_plan"]["path"],
            label=f"{study_map['id']}.source_plan.path",
        )
        study_map_ids.append(study_map["id"])
        writes[unit_directory / "study-map.yaml"] = _dump_yaml(study_map)
        note_prefix = (
            f"curriculum/modules/{canonical_module_id}/units/{unit_id}/stages/"
        )
        for stage in study_map["stages"]:
            note_ref = stage.get("working_note")
            if not isinstance(note_ref, str) or not note_ref.startswith(note_prefix) \
                    or not note_ref.endswith("/notes.md"):
                raise MastersPlanningError(
                    f"stage note escapes promoted module/unit scope: {note_ref}"
                )
            note_path = root / note_ref
            if note_path in stage_note_paths:
                raise MastersPlanningError(
                    f"promoted stages repeat a working note path: {note_ref}"
                )
            if note_path.exists() or note_path.is_symlink():
                raise MastersPlanningError(
                    f"promotion refuses an existing stage note: {note_ref}"
                )
            stage_note_paths.add(note_path)
            writes[note_path] = ""

    if len(study_map_ids) != len(set(study_map_ids)):
        raise MastersPlanningError("promoted study maps must have unique IDs")
    existing_maps = sorted(set(study_map_ids) & set(repo.study_maps))
    if existing_maps:
        raise MastersPlanningError(
            f"promotion refuses existing canonical study-map IDs: {existing_maps}"
        )

    updated_catalog = copy.deepcopy(catalog)
    updated_catalog["revision"] = catalog["revision"] + 1
    updated_catalog["updated_at"] = value["recorded_at"]
    updated_modules = {
        row["id"]: row for row in updated_catalog["candidate_modules"]
    }
    updated_modules[candidate_module_id]["planning_state"] = "promoted"
    updated_modules[candidate_module_id]["promoted_module_id"] = canonical_module_id
    updated_sources = {
        row["id"]: row for row in updated_catalog["candidate_sources"]
    }
    for mapping in adopted:
        row = updated_sources[mapping["candidate_source_id"]]
        row["planning_state"] = "promoted"
        row["canonical_source_id"] = mapping["canonical_source_id"]
    validate_master_catalog(
        root,
        updated_catalog,
        planned_canonical_source_ids=new_source_ids,
    )

    package_hash = promotion_package_sha256(value)
    catalog_path = master_catalog_destination(root)
    promotion_path = master_promotion_destination(root, value["id"])
    if promotion_path.exists() or promotion_path.is_symlink():
        raise MastersPlanningError(
            f"promotion provenance already exists: {value['id']}"
        )
    writes[catalog_path] = _dump_yaml(updated_catalog)

    affected_paths = tuple(sorted(
        [
            *(path.relative_to(root).as_posix() for path in writes),
            promotion_path.relative_to(root).as_posix(),
        ]
    ))
    provenance = {
        "schema_version": 1,
        "id": value["id"],
        "type": "master-planning-promotion-provenance",
        "status": "promoted",
        "recorded_at": value["recorded_at"],
        "candidate_module_id": candidate_module_id,
        "canonical_module_id": canonical_module_id,
        "catalog_revision_before": catalog["revision"],
        "catalog_revision_after": updated_catalog["revision"],
        "package_sha256": package_hash,
        "verification": copy.deepcopy(verification),
        "source_mappings": source_provenance_mappings,
        "unit_ids": unit_ids,
        "affected_paths": list(affected_paths),
        "preservation": {
            "originals_immutable": True,
            "comparison_ids": list(catalog["comparison_ids"]),
        },
    }
    try:
        validate_contract(
            root,
            "master-planning-promotion-provenance.schema.json",
            provenance,
        )
    except ValueError as exc:
        raise MastersPlanningError(str(exc)) from exc
    writes[promotion_path] = _dump_yaml(provenance)

    mutable_existing_paths = {catalog_path, *registry_texts}
    for path in writes:
        if path in mutable_existing_paths:
            continue
        if path.exists() or path.is_symlink():
            raise MastersPlanningError(
                "promotion refuses to replace an existing canonical or provenance file: "
                f"{path.relative_to(root).as_posix()}"
            )

    artifact_ids = tuple(sorted({
        "master-planning-catalog",
        candidate_module_id,
        canonical_module_id,
        value["id"],
        *candidate_source_ids,
        *new_source_ids,
        *unit_ids,
        *study_map_ids,
    }))
    expected_revisions = {
        artifact_id: artifact_revision(root, artifact_id)
        for artifact_id in artifact_ids
    }
    return MasterPromotionPlan(
        package_sha256=package_hash,
        writes=writes,
        artifact_ids=artifact_ids,
        expected_revisions=expected_revisions,
        affected_paths=affected_paths,
        diff=_promotion_diff(root, writes),
        updated_catalog=updated_catalog,
        provenance=provenance,
    )


def validate_candidate_comparison(
    root: Path,
    value: dict[str, Any],
    *,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _assert_academic_only(value)
    try:
        validate_contract(root, "candidate-source-comparison.schema.json", value)
    except ValueError as exc:
        raise MastersPlanningError(str(exc)) from exc
    catalog = catalog if catalog is not None else load_master_catalog(root)
    if catalog is None:
        raise MastersPlanningError("a sanitized Master Planning catalog is required")
    modules = {row["id"]: row for row in catalog["candidate_modules"]}
    sources = {row["id"]: row for row in catalog["candidate_sources"]}
    module_id = value["candidate_module_id"]
    if module_id not in modules:
        raise MastersPlanningError(f"comparison targets unknown candidate module: {module_id}")
    allowed_sources = set(modules[module_id]["source_ids"])
    assessed = [row["candidate_source_id"] for row in value["source_assessments"]]
    if len(assessed) != len(set(assessed)):
        raise MastersPlanningError("candidate comparison has duplicate source assessments")
    if set(assessed) != allowed_sources:
        raise MastersPlanningError(
            "candidate comparison must assess every source selected for its module exactly once"
        )
    for source_id in assessed:
        if source_id not in sources:
            raise MastersPlanningError(f"comparison references unknown source: {source_id}")
    selected = [
        row for row in value["source_assessments"] if row["role"] == "selected"
    ]
    if not selected:
        raise MastersPlanningError(
            "candidate comparison must identify at least one selected source"
        )
    for row in value["source_assessments"]:
        if row["role"] in {"selected", "current", "prerequisite"} \
                and row["review_status"] != "deep-reviewed":
            raise MastersPlanningError(
                f"{row['candidate_source_id']} is {row['role']} and must be deep-reviewed"
            )
    known_concepts = set(load_repo(root).concepts)
    unknown_assessment_concepts = sorted({
        concept_id
        for assessment in value["source_assessments"]
        for concept_id in assessment["concept_ids"]
        if concept_id not in known_concepts
    })
    if unknown_assessment_concepts:
        raise MastersPlanningError(
            "prospective assessment names unknown global concepts: "
            f"{unknown_assessment_concepts}"
        )
    if value["basis"]["catalog_revision"] != catalog["revision"]:
        raise MastersPlanningError("candidate comparison was prepared against a stale catalog")
    expected_candidate_set = candidate_set_checksum(catalog, module_id)
    if value["basis"]["candidate_set_checksum"] != expected_candidate_set:
        raise MastersPlanningError(
            "candidate comparison candidate set changed after preparation"
        )
    assessed_by_id = {
        row["candidate_source_id"]: row for row in value["source_assessments"]
    }
    seen_comparisons: set[tuple[str, str, str]] = set()
    for row in value["comparisons"]:
        left, right = row["left_candidate_source_id"], row["right_candidate_source_id"]
        if left == right or left not in allowed_sources or right not in allowed_sources:
            raise MastersPlanningError(
                "candidate comparison endpoints must be two distinct selected sources"
            )
        if assessed_by_id[left]["review_status"] != "deep-reviewed" \
                or assessed_by_id[right]["review_status"] != "deep-reviewed":
            raise MastersPlanningError(
                "prospective pairwise comparisons require two deep-reviewed sources"
            )
        comparison_key = (*sorted((left, right)), row["relation"])
        if comparison_key in seen_comparisons:
            raise MastersPlanningError(
                "duplicate prospective pairwise comparison relation"
            )
        seen_comparisons.add(comparison_key)
        unknown = sorted(set(row["concept_ids"]) - known_concepts)
        if unknown:
            raise MastersPlanningError(
                f"prospective comparison names unknown global concepts: {unknown}"
            )
    return value


def candidate_set_checksum(catalog: dict[str, Any], module_id: str) -> str:
    """Hash the exact candidate module and ordered source records under review."""

    modules = {row["id"]: row for row in catalog["candidate_modules"]}
    sources = {row["id"]: row for row in catalog["candidate_sources"]}
    module = modules.get(module_id)
    if module is None:
        raise MastersPlanningError(f"unknown candidate module: {module_id}")
    payload = {
        "module": module,
        "sources": [sources[source_id] for source_id in sorted(module["source_ids"])],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def candidate_comparison_destination(root: Path, comparison_id: str) -> Path:
    return (
        root / "curriculum" / "quarantine" / "masters-planning" /
        "comparisons" / f"{comparison_id}.yaml"
    )


def _load_comparisons(root: Path, catalog: dict[str, Any] | None) -> list[dict[str, Any]]:
    if catalog is None:
        return []
    comparisons = []
    # This glob is deliberately bounded to the sanitized comparison directory
    # and occurs only after an explicit dashboard gesture.
    for comparison_id in catalog["comparison_ids"]:
        path = candidate_comparison_destination(root, comparison_id)
        value = _read_yaml_object(
            root,
            path,
            label=f"candidate comparison {comparison_id}",
        )
        if value.get("id") != comparison_id:
            raise MastersPlanningError(f"comparison filename/id mismatch: {comparison_id}")
        comparisons.append(validate_candidate_comparison(root, value, catalog=catalog))
    return comparisons


def masters_planning_dashboard(
    root: Path,
    *,
    confirmed: bool,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    if not confirmed:
        raise MastersPlanningError(
            "opening Future Master's Planning requires an explicit access gesture"
        )
    catalog = load_master_catalog(root)
    timestamp = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC).replace(microsecond=0)
    value = {
        "schema_version": 1,
        "type": "masters-planning-dashboard",
        "opened_at": timestamp.isoformat(),
        "banner": "Prospective—not current LearningOS",
        "catalog": catalog,
        "comparisons": _load_comparisons(root, catalog),
        "isolation": {
            "normal_manifest": False,
            "search": False,
            "workload": False,
            "recommendations": False,
            "deadlines": False,
            "ordinary_ai_context": False,
        },
    }
    try:
        validate_contract(root, "masters-planning-dashboard.schema.json", value)
    except ValueError as exc:
        raise MastersPlanningError(str(exc)) from exc
    return value
