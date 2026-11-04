"""One-shot, content-preserving Python topic split through data-contract v63.

OPERATOR boundary 16 permits recorded migrations where the normal plan importer
cannot move a stage between units. The shared transaction service owns every
write, deletion, before-image, revision and receipt.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import cast

import yaml
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from learning_os.app.check import real_perimeter_errors, staged_shadow
from learning_os.app.lock import operator_lock
from learning_os.derive.validation import validate
from learning_os.domain.failures import WriteRefused
from learning_os.store.contracts.migration_lifecycle import retired_migration
from learning_os.store.fingerprint import snapshot
from learning_os.store.loader import load_repo
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import TransactionService
from learning_os.store.warning_baseline import delta, load_baseline, signatures_from_issues

MIGRATION = "python-topic-sessions-v63"
AUTHORITY = "migration.python-topic-sessions-v63"
MODULE = "module-job-python-engineering"
UNIT = "unit-job-python-engineering-fluency"
MODULE_DIR = f"curriculum/modules/{MODULE}"
UNIT_DIR = f"{MODULE_DIR}/units/{UNIT}"
MODULE_PATH = f"{MODULE_DIR}/module.yaml"
SOURCE_MAP_PATH = f"{MODULE_DIR}/source-map.yaml"
UNIT_PATH = f"{UNIT_DIR}/unit.yaml"
MAP_PATH = f"{UNIT_DIR}/study-map.yaml"
RESUME_PATH = "curriculum/resume.yaml"
BASE = f"operations/migrations/{MIGRATION}"
MARKER = f"{BASE}/committed.json"
SHARED_ROUTE = "route-python-modules-imports-python-docs-3"
SHARED_TEST_ROUTE = f"{SHARED_ROUTE}-session-testing"
TOPICS = (
    "everyday-data", "names-mutation", "functions-scope", "decorators-registration",
    "classes-inheritance", "dataclasses-properties", "special-methods", "modules-imports",
    "iterators-with", "type-hints", "interfaces-dispatch", "errors-logging", "testing",
    "tooling", "newer-python", "read-stratum",
)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def plan_sha256(report: dict[str, object]) -> str:
    """Bind the entire review artifact, including every proposed file body."""
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
    return cast(dict[str, object], value)


def _dump(value: object) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def _generation(root: Path) -> None:
    retired = retired_migration(root, MIGRATION, supported_through=63)
    if retired:
        raise WriteRefused(retired.message())


def _validation_errors(root: Path) -> list[str]:
    issues = validate(load_repo(root), online=False)
    signatures, errors = signatures_from_issues(issues)
    baseline, _ = load_baseline(root)
    regressions, _ = delta(baseline, signatures)
    return [*errors, *regressions]


def prepare(root: Path) -> dict[str, object]:
    """Draft and shadow-validate a lossless split; never mutate the selected root."""
    root = root.resolve()
    _generation(root)
    if _path(root, MARKER).exists():
        raise WriteRefused("migration already recorded; use apply to verify its receipt")
    inflight = root / "operations/transactions/.inflight"
    if inflight.exists() and any(inflight.iterdir()):
        raise WriteRefused("recovery required before drafting a migration")
    before_snapshot = snapshot(root)
    module, unit, study, source_map = (
        _yaml(root, relative) for relative in (MODULE_PATH, UNIT_PATH, MAP_PATH, SOURCE_MAP_PATH)
    )
    all_stages = cast(list[dict[str, object]], study.get("stages", []))
    for stage in all_stages:
        note = stage.get("working_note", "")
        if not isinstance(note, str) or not note.startswith(UNIT_DIR + "/stages/"):
            raise WriteRefused("stage note is outside the source unit")
        _path(root, note)
    if unit.get("working_note"):
        if unit["working_note"] != f"{UNIT_DIR}/notes.md":
            raise WriteRefused("unit note is outside its exact source directory")
        _path(root, unit["working_note"])
    errors = [*_validation_errors(root), *real_perimeter_errors(root)]
    if errors:
        raise WriteRefused("migration preflight failed: " + "; ".join(errors))
    expected_stages = [f"stage-python-{topic}" for topic in TOPICS]
    required = all_stages[:len(TOPICS)]
    optional = all_stages[len(TOPICS):]
    if (module.get("unit_order") != [UNIT] or unit.get("module_id") != MODULE
            or study.get("unit_id") != UNIT
            or [stage.get("id") for stage in required] != expected_stages
            or len(optional) != 10
            or any(stage.get("scope_triage") != "required-now" for stage in required)
            or any(stage.get("scope_triage") != "deferred" for stage in optional)):
        raise WriteRefused("Python source shape differs from the reviewed 16-topic/10-optional split")
    if (study.get("detours") or study.get("shelving") != {"state": "none"}
            or unit.get("source_selections") or unit.get("artifacts") or unit.get("workspace_ids")):
        raise WriteRefused("Python source has joins or learner state requiring a new migration")
    if any(stage.get("status") != "pending" or stage.get("attachments")
           or stage.get("source_feedback") or stage.get("completed") for stage in required):
        raise WriteRefused("Python topic progress/evidence requires a newly reviewed migration")
    knowledge = cast(dict[str, object], unit["knowledge_map"])
    nodes = {cast(str, node["id"]): node
             for node in cast(list[dict[str, object]], knowledge["nodes"])}
    node_to_unit: dict[str, str] = {}
    stage_to_unit: dict[str, str] = {}
    writes: dict[str, str] = {}
    deletes: list[str] = []
    pins = {MODULE_PATH, SOURCE_MAP_PATH, UNIT_PATH, MAP_PATH, RESUME_PATH,
            "operations/transactions/revisions.yaml"}
    matrix: list[dict[str, object]] = []
    artifacts = [MODULE, UNIT, cast(str, study["id"])]
    for number, (topic, original_stage) in enumerate(zip(TOPICS, required, strict=True), 1):
        uid = f"unit-job-python-{topic}"
        smid = f"study-map-job-python-{topic}"
        directory = f"{MODULE_DIR}/units/{uid}"
        if _path(root, directory).exists():
            raise WriteRefused(f"session destination already exists: {directory}")
        node_id = cast(str, original_stage.get("knowledge_node_id"))
        if node_id not in nodes or node_id in node_to_unit:
            raise WriteRefused("each required stage must retain one unique existing knowledge node")
        node_to_unit[node_id] = uid
        stage_to_unit[cast(str, original_stage["id"])] = uid
        stage = copy.deepcopy(original_stage)
        for resource in cast(list[dict[str, object]], stage["resources"]):
            if topic == "testing" and resource.get("route_id") == SHARED_ROUTE:
                resource["route_id"] = SHARED_TEST_ROUTE
                if resource.get("material_ref"):
                    cast(dict[str, object], resource["material_ref"])["route_id"] = SHARED_TEST_ROUTE
        before_note = cast(str, stage["working_note"])
        expected_note = f"{UNIT_DIR}/stages/{stage['id']}/notes.md"
        if before_note != expected_note:
            raise WriteRefused("stage note is outside its exact source directory")
        note_parent = _path(root, before_note).parent
        if any(path.name != "notes.md" for path in note_parent.iterdir()):
            raise WriteRefused(f"additional stage files need explicit relocation review: {before_note}")
        after_note = f"{directory}/stages/{stage['id']}/notes.md"
        note_bytes = _read(root, before_note)
        writes[after_note] = note_bytes.decode("utf-8")
        deletes.append(before_note)
        pins.add(before_note)
        stage.update(number=1, working_note=after_note)
        sources = {resource.get("source_id")
                   for resource in cast(list[dict[str, object]], stage["resources"])}
        new_unit = {
            "id": uid, "type": "unit", "module_id": MODULE, "kind": unit["kind"],
            "title": stage["title"], "order": number, "scope": stage["objective"],
            "status": "ready",
            "scope_sources": [copy.deepcopy(row) for row in cast(list[dict[str, object]], unit["scope_sources"])
                              if row["source_id"] in sources],
            "source_selections": [], "working_note": f"{directory}/notes.md",
            "artifacts": {}, "workspace_ids": [], "current_study_map": smid,
            "knowledge_map": {"summary": nodes[node_id]["summary"],
                              "nodes": [copy.deepcopy(nodes[node_id])]},
        }
        new_map = {key: copy.deepcopy(value) for key, value in study.items() if key != "stages"}
        new_map.update(id=smid, unit_id=uid, status="ready", current_stage=stage["id"], stages=[stage])
        writes[f"{directory}/unit.yaml"] = _dump(new_unit)
        writes[f"{directory}/study-map.yaml"] = _dump(new_map)
        writes[f"{directory}/notes.md"] = ""
        artifacts.extend([uid, smid])
        matrix.append({"stage_id": stage["id"], "unit_id": uid, "title": stage["title"],
                       "resource_ids": [row.get("id") for row in cast(list[dict[str, object]], stage["resources"])],
                       "note_before": before_note, "note_after": after_note,
                       "note_sha256": hashlib.sha256(note_bytes).hexdigest()})
    retained_nodes = [copy.deepcopy(node) for key, node in nodes.items() if key not in node_to_unit]
    if len(retained_nodes) != 1:
        raise WriteRefused("optional history must retain its one existing knowledge node")
    old_unit = copy.deepcopy(unit)
    old_unit.update(title=retained_nodes[0]["title"], scope=retained_nodes[0]["summary"],
                    order=17, status="paused",
                    knowledge_map={"summary": retained_nodes[0]["summary"], "nodes": retained_nodes})
    old_map = copy.deepcopy(study)
    old_map.update(status="paused", current_stage=optional[0]["id"], stages=copy.deepcopy(optional))
    for number, stage in enumerate(cast(list[dict[str, object]], old_map["stages"]), 1):
        stage["number"] = number
    writes[UNIT_PATH], writes[MAP_PATH] = _dump(old_unit), _dump(old_map)
    module["unit_order"] = [row["unit_id"] for row in matrix] + [UNIT]
    writes[MODULE_PATH] = _dump(module)
    for source in cast(list[dict[str, object]], source_map["sources"]):
        shared_copy = None
        for route in cast(list[object], source.get("unit_routes", [])):
            if not isinstance(route, dict):
                continue  # Legacy references remain on the retained optional owner.
            targets = {node_to_unit[node] for node in route.get("covers", []) if node in node_to_unit}
            if route.get("id") == SHARED_ROUTE and targets == {
                "unit-job-python-modules-imports", "unit-job-python-testing"
            }:
                # This already-authored page has two placements and two coverage
                # nodes. Split ownership, not the reading or its reviewed scope.
                shared_copy = copy.deepcopy(route)
                shared_copy.update(id=SHARED_TEST_ROUTE, unit_id="unit-job-python-testing",
                                   covers=["knowledge-python-testing"])
                route["covers"] = ["knowledge-python-modules-imports"]
                targets = {"unit-job-python-modules-imports"}
            if len(targets) != 1 or route.get("unit_id") != UNIT:
                raise WriteRefused("rich route has an ambiguous topic owner")
            route["unit_id"] = targets.pop()
        if shared_copy:
            cast(list[object], source["unit_routes"]).append(shared_copy)
    writes[SOURCE_MAP_PATH] = _dump(source_map)
    if _path(root, RESUME_PATH).exists():
        resume = _yaml(root, RESUME_PATH)
        if resume.get("unit_id") == UNIT and resume.get("stage_id") in stage_to_unit:
            uid = stage_to_unit[cast(str, resume["stage_id"])]
            resume.update(unit_id=uid, study_map_id=f"study-map-job-python-{uid.removeprefix('unit-job-python-')}")
            writes[RESUME_PATH] = _dump(resume)
    # Bind every original note as well as the authored records; canonical snapshots
    # intentionally do not serve as content hashes for every working-note byte.
    for stage in all_stages:
        pins.add(cast(str, stage["working_note"]))
    if unit.get("working_note"):
        pins.add(cast(str, unit["working_note"]))
    hashes = {relative: hashlib.sha256(_read(root, relative)).hexdigest()
              if _path(root, relative).exists() else None for relative in sorted(pins)}
    for relative in [*writes, *deletes]:
        if _path(root, relative).exists():
            writes[f"{BASE}/before/{relative}"] = _read(root, relative).decode("utf-8")
    writes[f"{BASE}/evidence.json"] = _json({"source_sha256": hashes,
                                             "sessions": matrix,
                                             "optional_stage_ids": [row["id"] for row in optional]})
    for relative in [*writes, MARKER]:
        if relative.startswith(BASE + "/") and _path(root, relative).exists():
            raise WriteRefused(f"migration evidence destination already exists: {relative}")
    with staged_shadow(root, {_path(root, relative): content for relative, content in writes.items()},
                       [_path(root, relative) for relative in deletes]) as shadow:
        errors = _validation_errors(shadow)
    if errors:
        raise WriteRefused("migration shadow validation failed: " + "; ".join(errors))
    if snapshot(root) != before_snapshot:
        raise WriteRefused("source changed while drafting migration")
    return {"migration": MIGRATION, "snapshot": before_snapshot, "source_sha256": hashes,
            "expected_revisions": {key: artifact_revision(root, key) for key in artifacts},
            "writes": writes, "deletes": deletes, "sessions": matrix,
            "optional_stage_ids": [row["id"] for row in optional]}


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
    return {"replayed": True, "transaction_id": txid, "receipt_path": receipt_relative}


def apply(root: Path, report: dict[str, object], *, reviewed_sha256: str) -> dict[str, object]:
    """Commit only the exact freshly prepared plan, with normal recovery and replay."""
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
        marker_path = _path(root, MARKER)
        result = TransactionService(root).commit(
            capability=AUTHORITY,
            writes={_path(root, relative): content for relative, content in cast(dict[str, str], report["writes"]).items()},
            deletes=[_path(root, relative) for relative in cast(list[str], report["deletes"])],
            artifact_ids=cast(dict[str, int], report["expected_revisions"]),
            expected_revisions=cast(dict[str, int], report["expected_revisions"]),
            expected_snapshot=cast(str, report["snapshot"]),
            validate_state=lambda: _validation_errors(root),
            metadata={"migration": MIGRATION, "plan_sha256": reviewed_sha256},
            transaction_writes=lambda txid: {marker_path: _json({
                "migration": MIGRATION, "plan_sha256": reviewed_sha256, "transaction_id": txid})},
            write_authorities={marker_path: AUTHORITY},
        )
        return {"replayed": False, "transaction_id": result.transaction_id,
                "receipt_path": result.receipt_path.relative_to(root).as_posix()}
