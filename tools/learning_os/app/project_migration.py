"""Generation-bounded thesis consolidation (OPERATOR boundary 16).

This one-shot controller uses the shared transaction engine and its declared
authority. Ordinary operation proposals still require GatewayEnvelopeV2.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import yaml
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from learning_os.app.lock import operator_lock
from learning_os.derive.validation import validate
from learning_os.domain.failures import WriteRefused
from learning_os.store.contracts.migration_lifecycle import retired_migration
from learning_os.store.fingerprint import snapshot
from learning_os.store.loader import load_repo, parse_frontmatter
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import TransactionService
from learning_os.store.warning_baseline import delta, load_baseline, signatures_from_issues

MIGRATION = "projects-to-modules-v62"
AUTHORITY = "migration.projects-to-modules-v62"
PROJECT = "project-bachelor-thesis"
MODULE = "module-project-bachelor-thesis"
WORKSPACE = "workspace-thesis-mle-medical"
PROJECT_PATH = f"projects/registry/{PROJECT}.yaml"
MODULE_PATH = f"curriculum/modules/{MODULE}/module.yaml"
WORKSPACE_PATH = f"work/active/{WORKSPACE}/CONTEXT.md"
ALIASES_PATH = "projects/aliases.yaml"
RELATIONS_PATH = "projects/relations/project-relations.yaml"
BASE = f"operations/migrations/{MIGRATION}"
MARKER = f"{BASE}/committed.json"
SOURCES = (PROJECT_PATH, MODULE_PATH, WORKSPACE_PATH, ALIASES_PATH, RELATIONS_PATH)
MILESTONES = {"milestone-thesis-scope": "unit-thesis-landscape",
              "milestone-thesis-baseline": "unit-thesis-experiments"}
SECTIONS = {
    "Research context": ("id", "type", "title", "project_type", "status", "objective",
                         "root_uri", "linked_module_ids", "unit_ids", "workspace_ids",
                         "thematic_group_ids"),
    "Workstreams": ("structure",),
    "Research decisions": ("decisions",),
    "Materials and deliverables": ("files",),
    "Milestone identities": ("milestone_ids",),
    "Boundaries": ("boundaries",),
    "Migration provenance": ("schema_version", "revision", "migrated_at", "migrated_from",
                             "migration", "source_sha256"),
}


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def plan_sha256(report: dict[str, object]) -> str:
    """Identity of the complete review artifact, including proposed file bodies."""
    return hashlib.sha256(_json(report).encode()).hexdigest()


def _path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise WriteRefused(f"migration path is outside its scope: {relative}")
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise WriteRefused(f"migration refuses symlink: {relative}")
    return path


def _read(root: Path, relative: str) -> bytes:
    return _path(root, relative).read_bytes()


def _yaml(root: Path, relative: str) -> dict[str, object]:
    value = yaml.load(_read(root, relative), Loader=UniqueKeySafeLoader)
    if not isinstance(value, dict):
        raise WriteRefused(f"migration requires a mapping: {relative}")
    return value


def _dump(value: object) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def _generation(root: Path) -> None:
    retired = retired_migration(root, MIGRATION, supported_through=62)
    if retired:
        raise WriteRefused(retired.message())


def _validation_errors(root: Path) -> list[str]:
    issues = validate(load_repo(root), online=False)
    signatures, errors = signatures_from_issues(issues)
    baseline, _ = load_baseline(root)
    regressions, _ = delta(baseline, signatures)
    return [*errors, *regressions]


def _scalar_paths(value: object, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        return [path for key, child in value.items()
                for path in _scalar_paths(child, f"{prefix}/{key}")]
    if isinstance(value, list):
        return [path for index, child in enumerate(value)
                for path in _scalar_paths(child, f"{prefix}/{index}")]
    return [prefix]


def _ids(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            yield value["id"]
        for child in value.values():
            yield from _ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from _ids(child)


def prepare(root: Path) -> dict[str, object]:
    """Read-only draft; a snapshot race refuses rather than returning a torn plan."""
    root = root.resolve()
    _generation(root)
    if _path(root, MARKER).exists():
        raise WriteRefused("migration already recorded; use apply to verify its receipt")
    inflight = root / "operations/transactions/.inflight"
    if inflight.exists() and any(inflight.iterdir()):
        raise WriteRefused("recovery required before drafting a migration")
    before_snapshot = snapshot(root)
    errors = _validation_errors(root)
    if errors:
        raise WriteRefused("migration preflight failed: " + "; ".join(errors))
    project = _yaml(root, PROJECT_PATH)
    module = _yaml(root, MODULE_PATH)
    ws_text = _read(root, WORKSPACE_PATH).decode()
    ws, body = parse_frontmatter(ws_text, root / WORKSPACE_PATH)
    aliases = _yaml(root, ALIASES_PATH)
    relations = _yaml(root, RELATIONS_PATH)
    allowed = {key for keys in SECTIONS.values() for key in keys}
    if set(project) - allowed:
        raise WriteRefused(f"unmapped Project fields: {sorted(set(project) - allowed)}")
    if (project.get("id") != PROJECT or module.get("id") != MODULE
            or ws.get("id") != WORKSPACE or not module.get("compatibility_only")
            or module.get("migrated_to") != PROJECT or module.get("kind") != "project"
            or module.get("area_id") != "program-thesis-projects"
            or ws.get("project_id") != PROJECT
            or cast(dict[str, str], aliases.get("aliases", {})).get(MODULE) != PROJECT
            or project.get("workspace_ids") != [WORKSPACE]
            or project.get("unit_ids") != module.get("unit_order")
            or set(cast(list[str], project.get("milestone_ids", []))) != set(MILESTONES)
            or set(cast(list[str], module.get("unit_order", []))) != set(MILESTONES.values())):
        raise WriteRefused("unexpected thesis ownership or milestone identity")
    # Existing Module fields are preserved wholesale, including supplied academic facts.
    updated = dict(module)
    updated["area_id"] = "program-bachelors"
    for key in ("compatibility_only", "migrated_to", "migrated_at", "migration", "source_sha256"):
        updated.pop(key, None)
    for field, additions in (("related_module_ids", project.get("linked_module_ids", [])),
                             ("thematic_group_ids", project.get("thematic_group_ids", []))):
        updated[field] = list(dict.fromkeys([*cast(list[str], updated.get(field, [])), *cast(list[str], additions)]))
    updated_ws = dict(ws)
    updated_ws.pop("project_id")
    updated_ws["program_ids"] = list(dict.fromkeys(
        "program-bachelors" if item == "program-thesis-projects" else item
        for item in ws.get("program_ids", [])))
    if "program-bachelors" not in updated_ws["program_ids"]:
        updated_ws["program_ids"].append("program-bachelors")
    owned_relations = [row for row in cast(list[dict[str, object]], relations["relations"]) if row["from_project_id"] == PROJECT]
    redirects = {PROJECT: MODULE, **MILESTONES}
    for legacy in _ids([project.get("structure"), project.get("decisions"), owned_relations]):
        if legacy in redirects:
            raise WriteRefused(f"duplicate legacy identity: {legacy}")
        redirects[legacy] = WORKSPACE
    updated_aliases = dict(cast(dict[str, str], aliases["aliases"]))
    del updated_aliases[MODULE]
    for legacy, owner in redirects.items():
        if legacy in updated_aliases and updated_aliases[legacy] != owner:
            raise WriteRefused(f"conflicting legacy alias: {legacy}")
        updated_aliases[legacy] = owner
    field_map = {}
    appended = ""
    for section, keys in SECTIONS.items():
        data = {key: project[key] for key in keys if key in project}
        if section == "Materials and deliverables":
            data["relationships"] = owned_relations
        anchors = "".join(f'<a id="{legacy}"></a>\n' for legacy in _ids(data))
        appended += f"\n\n## {section}\n\n{anchors}\n```yaml\n{_dump(data)}```\n"
        for key in keys:
            if key in project:
                for pointer in _scalar_paths(project[key], f"/{key}"):
                    field_map["project" + pointer] = section
        if section == "Materials and deliverables":
            for pointer in _scalar_paths(owned_relations):
                field_map["relationships" + pointer] = section
        if section == "Milestone identities":
            appended += "\n```yaml\n" + _dump({"owners": MILESTONES}) + "```\n"
    writes = {
        MODULE_PATH: _dump(updated),
        WORKSPACE_PATH: "---\n" + _dump(updated_ws) + "---\n" + body + appended,
        ALIASES_PATH: _dump({"aliases": updated_aliases}),
        RELATIONS_PATH: _dump({"relations": [row for row in cast(list[dict[str, object]], relations["relations"])
                                            if row["from_project_id"] != PROJECT]}),
    }
    pins = set(SOURCES) | {"curriculum/resume.yaml", "work/COORDINATION.md",
                          "curriculum/programs/program-bachelors.yaml",
                          "curriculum/programs/program-thesis-projects.yaml",
                          "operations/transactions/revisions.yaml"}
    module_dir = _path(root, str(Path(MODULE_PATH).parent))
    pins.update(path.relative_to(root).as_posix() for path in module_dir.rglob("*")
                if path.is_file() or path.is_symlink())
    for row in cast(list[dict[str, str]], project.get("files", [])):
        relative = row["path"]
        _read(root, relative)  # No external URI traversal or missing deliverable.
        pins.add(relative)
    pin_hashes = {relative: hashlib.sha256(_read(root, relative)).hexdigest()
                  if _path(root, relative).exists() else None for relative in sorted(pins)}
    for relative in SOURCES:
        writes[f"{BASE}/before/{relative}"] = _read(root, relative).decode()
    writes[f"{BASE}/evidence.json"] = _json({"field_map": field_map, "redirects": redirects,
                                            "source_sha256": pin_hashes})
    # No previous evidence may be overwritten, even if a marker is missing.
    for relative in [*writes, MARKER]:
        path = _path(root, relative)
        if relative.startswith(BASE + "/") and path.exists():
            raise WriteRefused(f"migration evidence destination already exists: {relative}")
    if snapshot(root) != before_snapshot:
        raise WriteRefused("source changed while drafting migration")
    return {"migration": MIGRATION, "snapshot": before_snapshot, "source_sha256": pin_hashes,
            "expected_revisions": {key: artifact_revision(root, key)
                                   for key in (PROJECT, MODULE, WORKSPACE)},
            "writes": writes, "deletes": [PROJECT_PATH], "redirects": redirects,
            "field_map": field_map}


def _completed(root: Path, reviewed_sha256: str) -> dict[str, object] | None:
    if not _path(root, MARKER).exists():
        return None
    marker_bytes = _read(root, MARKER)
    marker = json.loads(marker_bytes)
    if marker.get("plan_sha256") != reviewed_sha256:
        raise WriteRefused("recorded migration differs from reviewed plan")
    txid = marker.get("transaction_id", "")
    if not isinstance(txid, str) or not txid.startswith("transaction-") or Path(txid).name != txid:
        raise WriteRefused("invalid migration transaction identity")
    receipt_relative = f"operations/transactions/{txid}.yaml"
    receipt = _yaml(root, receipt_relative)
    schema = json.loads(_read(root, "system/schema/transaction-receipt.schema.json"))
    if list(Draft202012Validator(schema).iter_errors(receipt)):
        raise WriteRefused("migration receipt is invalid")
    if (receipt.get("id") != txid or receipt.get("status") != "committed"
            or receipt.get("capability") != AUTHORITY
            or cast(dict[str, object], receipt.get("metadata", {})).get("plan_sha256") != reviewed_sha256):
        raise WriteRefused("migration marker lacks its committed receipt")
    rows = {cast(str, row["path"]): row for row in cast(list[dict[str, object]], receipt["writes"])}
    if rows.get(MARKER, {}).get("sha256_after") != hashlib.sha256(marker_bytes).hexdigest():
        raise WriteRefused("migration marker does not match receipt")
    for relative, row in rows.items():
        if relative.startswith(BASE + "/before/") or relative == f"{BASE}/evidence.json":
            if hashlib.sha256(_read(root, relative)).hexdigest() != row["sha256_after"]:
                raise WriteRefused(f"migration evidence differs from receipt: {relative}")
    # Evolved Module/workspace state is deliberately not rewritten on replay.
    return {"replayed": True, "transaction_id": txid, "receipt_path": receipt_relative}


def apply(root: Path, report: dict[str, object], *, reviewed_sha256: str) -> dict[str, object]:
    """Apply only an exact reviewed plan, under the normal lock/recovery boundary."""
    root = root.resolve()
    _generation(root)
    if plan_sha256(report) != reviewed_sha256:
        raise WriteRefused("reviewed migration plan hash does not match")
    with operator_lock(root):
        completed = _completed(root, reviewed_sha256)
        if completed:
            return completed
        if prepare(root) != report:
            raise WriteRefused("migration source, snapshot or revisions changed; prepare again")
        writes = {_path(root, relative): content for relative, content in cast(dict[str, str], report["writes"]).items()}
        marker_path = _path(root, MARKER)
        result = TransactionService(root).commit(
            capability=AUTHORITY, writes=writes,
            deletes=[_path(root, relative) for relative in cast(list[str], report["deletes"])],
            artifact_ids=cast(dict[str, int], report["expected_revisions"]),
            expected_revisions=cast(dict[str, int], report["expected_revisions"]),
            expected_snapshot=cast(str, report["snapshot"]),
            validate_state=lambda: _validation_errors(root),
            metadata={"migration": MIGRATION, "plan_sha256": reviewed_sha256},
            transaction_writes=lambda txid: {marker_path: _json({
                "migration": MIGRATION, "plan_sha256": reviewed_sha256,
                "transaction_id": txid})},
            write_authorities={marker_path: AUTHORITY},
        )
        return {"replayed": False, "transaction_id": result.transaction_id,
                "receipt_path": result.receipt_path.relative_to(root).as_posix()}
