"""Validated inputs for the bounded learning runtime (V0).

Ownership: the canonical study-map stage owns requirement semantics via its
``runtime_target`` block. :func:`compile_requirement` deterministically derives
the LearningRequirement IR from that block; there is no independently authored
``requirements.yaml`` sidecar channel. A knowledge-* target denotes a unit-local
knowledge-map entry; it is never silently promoted to a global concept. Readers
refuse damaged evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from learning_os.domain.snapshot import Repo
from learning_os.store.layout import PathBoundaryError


class RuntimeInputError(ValueError):
    """A runtime input is invalid or cannot be read safely."""


def runtime_path(root: Path, path: Path) -> Path:
    """Admit an exact path without following any symbolic-link component."""
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RuntimeInputError(f"runtime path escapes repository: {path}") from exc
    cursor = root
    for part in relative.parts:
        if part in {"..", "."}:
            raise RuntimeInputError(f"invalid runtime path: {path}")
        cursor /= part
        if cursor.is_symlink():
            raise RuntimeInputError(f"runtime path may not contain a symlink: {cursor}")
    return path


def validate_runtime_record(repo: Repo, name: str, value: dict) -> None:
    schema = json.loads((repo.root / "system/schema" / f"{name}.schema.json").read_text())
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value), key=str)
    if errors:
        raise RuntimeInputError(f"{name}: {errors[0].message}")
    if name == "learner-observation" and set(value.get("conditions", ())) & set(value.get("conditions_not_met", ())):
        raise RuntimeInputError("learner-observation: conditions and conditions_not_met must be disjoint")


def requirement_fingerprint(requirement: dict) -> str:
    data = json.dumps(requirement, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def activity_fingerprint(repo: Repo, resource: dict) -> str | None:
    """Bind suitability to the exact local prompt bytes and authored scope.

    Materials use the shared boundary-checked resolver. Hashes attest identity,
    not correctness or the learner's familiarity with the activity.
    """
    from learning_os.store.materials.resolution import project_material_resource

    projected = project_material_resource(repo, resource)
    try:
        if projected.get("material_exists") is True and projected.get("material_path"):
            path = repo.learningos_root / projected["material_path"]
        elif resource.get("vault_path") and not resource["vault_path"].startswith("material://"):
            path = runtime_path(repo.root, repo.root / resource["vault_path"])
        else:
            return None
        payload = {key: resource.get(key) for key in (
            "route_id", "source", "source_id", "vault_path", "locator", "label", "angle", "angle_detail")}
        payload["content_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return requirement_fingerprint(payload)
    except (RuntimeInputError, OSError):
        return None


RUNTIME_REVIEW_VERSION = "runtime-review-v1"


def runtime_review_fingerprint(stage: dict) -> str:
    """Bind a review attestation to one stage's exact runtime payload.

    Covers the version tag, the stage id, the ``runtime_target`` block, and
    the sorted ``(route_id, affordance)`` pairs of its resources — and nothing
    else, so unrelated edits (titles, notes, locators) leave a review valid.
    Canonicalized with sorted keys over parsed structures, never raw text, so
    the value survives YAML dump/load round-trips.
    """
    resources = stage.get("resources") or []
    pairs = sorted(
        (str(resource.get("route_id") or ""), str(resource.get("affordance") or ""))
        for resource in resources
        if isinstance(resource, dict)
    )
    payload = {
        "version": RUNTIME_REVIEW_VERSION,
        "stage_id": stage.get("id"),
        "runtime_target": stage.get("runtime_target"),
        "affordances": pairs,
    }
    if "ability_ids" in stage:
        payload["ability_ids"] = sorted(stage["ability_ids"])
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def bind_runtime_reviews(map_data: object) -> object:
    """Fill the fingerprint of every ``runtime_review`` that omits one.

    The fingerprint is a pure function of the stage, so an author who
    declares a review in an imported map gets the value they would have
    computed for the stage they are importing; the import's reviewed bytes
    then bind it (agent-cost D3). Material-reference expansion never touches
    the fingerprinted fields, so the authored and the loaded stage agree. A
    fingerprint already present is kept as written, stale or not: replacing
    it would re-bind a review to a payload nobody reviewed. Returns a copy.
    """
    if not isinstance(map_data, dict) or not isinstance(map_data.get("stages"), list):
        return map_data
    return {**map_data, "stages": [
        {**stage, "runtime_review": {**stage["runtime_review"],
                                     "fingerprint": runtime_review_fingerprint(stage)}}
        if isinstance(stage, dict) and isinstance(stage.get("runtime_review"), dict)
        and "fingerprint" not in stage["runtime_review"] else stage
        for stage in map_data["stages"]
    ]}


def requirement_id_for(unit_id: str, stage_id: str) -> str:
    """Deterministic IR id derived from the owning unit and stage only."""
    unit_suffix = unit_id[len("unit-"):] if unit_id.startswith("unit-") else unit_id
    stage_suffix = stage_id[len("stage-"):] if stage_id.startswith("stage-") else stage_id
    return f"req-{unit_suffix}-{stage_suffix}"


def compile_requirement(stage: dict, unit_id: str, module_id: str) -> dict:
    """Derive the LearningRequirement IR from one canonical stage.

    The stage's ``runtime_target`` block is the only semantic source. Raises
    :class:`RuntimeInputError` when the block is missing or malformed; callers
    treat a missing block as "no requirement authored for this stage" and only
    call this when the block is present.
    """
    target = stage.get("runtime_target")
    if not isinstance(target, dict):
        raise RuntimeInputError(f"{stage.get('id', '?')}: stage has no runtime_target")
    requirement = {
        "id": requirement_id_for(unit_id, stage["id"]),
        "concept": target["concept"],
        "capability": target["capability"],
        "conditions": list(target.get("conditions", [])),
        "evidence_spec": list(target["evidence_spec"]),
        "source_stage": {"module_id": module_id, "unit_id": unit_id, "stage_id": stage["id"]},
    }
    return requirement


def requirement_stage(repo: Repo, requirement: dict):
    source = requirement["source_stage"]
    unit = repo.units.get(source["unit_id"])
    if unit is None or unit.module_id != source["module_id"]:
        raise RuntimeInputError(f"{requirement['id']}: unknown or mismatched source unit/module")
    study_map = repo.study_maps.get(unit.data.get("current_study_map"))
    if study_map is None or study_map.unit_id != unit.id or study_map.module_id != unit.module_id:
        raise RuntimeInputError(f"{requirement['id']}: no matching current study map")
    stage = next((s for s in study_map.data.get("stages", []) if s["id"] == source["stage_id"]), None)
    if stage is None:
        raise RuntimeInputError(f"{requirement['id']}: unknown source stage")
    return unit, study_map, stage


def collect_requirements(repo: Repo) -> list[dict]:
    """Compile every LearningRequirement IR from current study-map stages."""
    requirements = {}
    try:
        for unit in sorted(repo.units.values(), key=lambda item: item.id):
            map_id = (unit.data or {}).get("current_study_map")
            if not map_id:
                continue
            study_map = repo.study_maps.get(map_id)
            if study_map is None or study_map.unit_id != unit.id or study_map.module_id != unit.module_id:
                continue
            for stage in study_map.data.get("stages", []):
                if not isinstance(stage, dict) or "runtime_target" not in stage:
                    continue
                try:
                    row = compile_requirement(stage, unit.id, unit.module_id)
                    validate_runtime_record(repo, "learning-requirement", row)
                except (RuntimeInputError, TypeError, KeyError, AttributeError) as exc:
                    raise RuntimeInputError(
                        f"{study_map.path}: invalid runtime_target on stage {stage.get('id', '?')}: {exc}"
                    ) from exc
                concept = row["concept"]
                if concept.startswith("knowledge-"):
                    known = {item["id"] for item in (unit.data.get("knowledge_map", {}) or {}).get("nodes", [])}
                else:
                    known = set(repo.concepts) & set(stage.get("concepts", []))
                if concept not in known:
                    raise RuntimeInputError(
                        f"{study_map.path}: unknown or out-of-scope requirement concept {concept}"
                    )
                if row["id"] in requirements:
                    raise RuntimeInputError(f"duplicate requirement ID: {row['id']}")
                requirements[row["id"]] = row
    except (OSError, yaml.YAMLError, json.JSONDecodeError, PathBoundaryError, TypeError, KeyError) as exc:
        raise RuntimeInputError(f"cannot read runtime requirements: {exc}") from exc
    return [requirements[key] for key in sorted(requirements)]


def read_observations(repo: Repo, requirements: list[dict]) -> list[dict]:
    known = {req["id"] for req in requirements}
    observations = []
    seen = set()
    corrected = set()
    try:
        for workspace in sorted(repo.workspaces.values(), key=lambda item: item.id):
            path = runtime_path(repo.root, workspace.path.parent / "observations.jsonl")
            try:
                content = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                continue
            relative = path.relative_to(repo.root).as_posix()
            for line_number, line in enumerate(content.splitlines(), 1):
                if not line.strip():
                    continue
                obs = json.loads(line)
                validate_runtime_record(repo, "learner-observation", obs)
                if obs["requirement"] not in known:
                    # The ledger line is where this is noticed, not where it went
                    # wrong. A requirement exists only while its stage declares a
                    # `runtime_target`, so retiring or re-homing that stage orphans
                    # every attempt already recorded against it — and the reader
                    # then pointed at observations.jsonl, which is the one file
                    # that is still correct. Say which stage stopped declaring it.
                    raise RuntimeInputError(
                        f"{relative}:{line_number}: no stage declares requirement "
                        f"{obs['requirement']} any more, but this recorded attempt "
                        f"still refers to it. A requirement exists only while its "
                        f"study-map stage carries a runtime_target: restore that "
                        f"target, or supersede/relocate the attempts recorded "
                        f"against it. The ledger line itself is not the fault.")
                # Legacy records have no ID. Bind a reproducible ID to their
                # exact ledger location and bytes, rather than a timestamp.
                identity = obs.get("id") or "observation-" + hashlib.sha256(
                    f"{relative}:{line_number}:{line}".encode()
                ).hexdigest()
                if identity in seen:
                    raise RuntimeInputError(f"duplicate observation ID: {identity}")
                if obs.get("supersedes"):
                    prior = next((item for item in observations if item["id"] == obs["supersedes"]), None)
                    if (prior is None or prior["requirement"] != obs["requirement"]
                            or prior["origin"]["path"] != relative or prior["id"] in corrected):
                        raise RuntimeInputError("correction must supersede one uncorrected earlier observation of this requirement in this ledger")
                    corrected.add(prior["id"])
                seen.add(identity)
                observations.append({**obs, "id": identity, "origin": {"path": relative, "line": line_number}})
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        raise RuntimeInputError(f"cannot read runtime observations: {exc}") from exc
    return observations


def read_stage_results(repo: Repo) -> list[dict]:
    """Read every untargeted stage result from the workspace ledgers.

    Same append-only ledger style as :func:`read_observations`: one
    ``stage-results.jsonl`` beside each workspace's ``CONTEXT.md``, schema
    validated, duplicate ids refused, and a ``--supersedes`` correction
    chain that must name one uncorrected earlier row for the same
    unit/stage in the same ledger. Readers refuse damaged rows; a row
    whose unit/stage no longer resolves names the stage that went away.
    Nothing here grants credit — the evidence interpreters read the
    observation ledgers only, so these rows are context whatever the
    requirement state.
    """
    results = []
    seen = set()
    corrected = set()
    try:
        for workspace in sorted(repo.workspaces.values(), key=lambda item: item.id):
            path = runtime_path(repo.root, workspace.path.parent / "stage-results.jsonl")
            try:
                content = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                continue
            relative = path.relative_to(repo.root).as_posix()
            for line_number, line in enumerate(content.splitlines(), 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                validate_runtime_record(repo, "learner-stage-result", row)
                unit = repo.units.get(row["unit"])
                study_map = (
                    repo.study_maps.get((unit.data or {}).get("current_study_map"))
                    if unit is not None else None
                )
                stage = next(
                    (item for item in (study_map.data.get("stages", []) if study_map else [])
                     if isinstance(item, dict) and item.get("id") == row["stage"]),
                    None,
                )
                if unit is None or study_map is None or stage is None:
                    raise RuntimeInputError(
                        f"{relative}:{line_number}: no current study-map stage "
                        f"{row['stage']} in unit {row['unit']} any more, but this "
                        f"recorded result still refers to it. The ledger line "
                        f"itself is not the fault.")
                identity = row.get("id") or "stage-result-" + hashlib.sha256(
                    f"{relative}:{line_number}:{line}".encode()
                ).hexdigest()
                if identity in seen:
                    raise RuntimeInputError(f"duplicate stage-result ID: {identity}")
                if row.get("supersedes"):
                    prior = next((item for item in results if item["id"] == row["supersedes"]), None)
                    if (prior is None or prior["unit"] != row["unit"]
                            or prior["stage"] != row["stage"]
                            or prior["origin"]["path"] != relative or prior["id"] in corrected):
                        raise RuntimeInputError("correction must supersede one uncorrected earlier stage result of this unit/stage in this ledger")
                    corrected.add(prior["id"])
                seen.add(identity)
                results.append({**row, "id": identity, "origin": {"path": relative, "line": line_number}})
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        raise RuntimeInputError(f"cannot read runtime stage results: {exc}") from exc
    return results


def stage_results_for(results: list[dict], unit_id: str, stage_id: str) -> list[dict]:
    """Live (non-superseded) rows for one unit/stage, newest first.

    Unparseable timestamps sort as oldest rather than crashing the read.
    """
    superseded = {row.get("supersedes") for row in results
                  if isinstance(row, dict) and row.get("supersedes")}
    live = [row for row in results
            if isinstance(row, dict) and row.get("id") not in superseded
            and row.get("unit") == unit_id and row.get("stage") == stage_id]

    def _when(row: dict) -> str:
        stamp = row.get("timestamp")
        return stamp if isinstance(stamp, str) else ""

    return sorted(live, key=_when, reverse=True)


def temporary_study_sequence(repo: Repo, unit_id: str, stage_ids: object) -> dict:
    """Derive one ordered subset, enforcing only authored prerequisite nodes.

    This is a read model. It neither changes stage lifecycle nor infers mastery
    from a completed study activity. Its caller binds the result to a snapshot.
    """
    unit = repo.units.get(unit_id)
    if unit is None:
        raise RuntimeInputError(f"unknown unit: {unit_id}")
    study_map = repo.study_maps.get(unit.data.get("current_study_map"))
    if study_map is None or study_map.unit_id != unit_id:
        raise RuntimeInputError("unit has no current study map belonging to this Unit")
    stages = study_map.data.get("stages", [])
    by_id = {row["id"]: row for row in stages}
    if len(by_id) != len(stages):
        raise RuntimeInputError("ambiguous stage IDs in current study map")
    if stage_ids is None:
        stage_ids = list(by_id)
    if not isinstance(stage_ids, list) or not stage_ids or any(not isinstance(sid, str) for sid in stage_ids):
        raise RuntimeInputError("stage IDs must be a nonempty ordered list of strings")
    if len(stage_ids) != len(set(stage_ids)) or any(sid not in by_id for sid in stage_ids):
        raise RuntimeInputError("stage IDs must be distinct existing stages of this Unit")
    if any(row.get("status") == "open" and row.get("classification") == "required-now"
           for row in study_map.data.get("detours", [])):
        raise RuntimeInputError("an open required-now detour must retain its repair and return flow")
    nodes = {row["id"]: row for row in (unit.data.get("knowledge_map") or {}).get("nodes", [])}
    stages_by_node: dict[str, list[dict]] = {}
    for stage in stages:
        if stage.get("knowledge_node_id"):
            stages_by_node.setdefault(stage["knowledge_node_id"], []).append(stage)
    positions = {sid: i for i, sid in enumerate(stage_ids)}
    authored = {row["id"]: i for i, row in enumerate(stages)}
    edges: set[tuple[str, str]] = set()
    notes = {"Only authored knowledge-node prerequisites are checked; this sequence grants no readiness or mastery."}
    def ancestors(start: str) -> set[str]:
        visiting: set[str] = set()
        visited: set[str] = set()
        stack = [(start, False)]
        while stack:
            nid, finished = stack.pop()
            if finished:
                visiting.remove(nid)
                visited.add(nid)
                continue
            if nid in visiting:
                raise RuntimeInputError("cycle in selected stage's authored prerequisite ancestry")
            if nid in visited:
                continue
            if nid not in nodes:
                raise RuntimeInputError(f"unknown prerequisite knowledge node: {nid}")
            visiting.add(nid)
            stack.append((nid, True))
            stack.extend((dependency, False) for dependency in nodes[nid].get("builds_on", []))
        return visited - {start}

    for sid in stage_ids:
        node_id = by_id[sid].get("knowledge_node_id")
        if not node_id:
            notes.add(f"No prerequisite stage mapping is authored for {sid}.")
            continue
        for dependency in sorted(ancestors(node_id)):
            mapped = stages_by_node.get(dependency, [])
            if not mapped:
                notes.add(f"Prerequisite node {dependency} has no mapped stage; its satisfaction is unchecked.")
                continue
            if not any(authored[row["id"]] < authored[sid] for row in mapped):
                # The map itself teaches this stage first: mock one, repair, mock two.
                notes.add(f"{sid} is authored before every stage of prerequisite node {dependency}; that link is not enforced for it.")
                continue
            # A prerequisite names a concept, not every stage that revisits it.
            # Iterative maps repeat a node, so one of its stages, already
            # complete or placed earlier, satisfies it.
            satisfied = [row["id"] for row in mapped
                         if row.get("status") == "complete"
                         or (row["id"] in positions and positions[row["id"]] < positions[sid])]
            if not satisfied:
                if len(mapped) == 1:
                    raise RuntimeInputError(f"prerequisite stage {mapped[0]['id']} must precede {sid} or already record complete")
                options = ", ".join(row["id"] for row in mapped)
                raise RuntimeInputError(f"one of the prerequisite stages {options} must precede {sid} or already record complete")
            if len(mapped) > 1:
                notes.add(f"Prerequisite node {dependency} has several stages; one placed earlier or already complete satisfies it.")
            edges.update((pid, sid) for pid in satisfied)
    return {
        "unit_id": unit_id, "study_map_id": study_map.id,
        "canonical_current_stage": study_map.data.get("current_stage"),
        "durable_stage_ids": list(by_id),
        "stages": [{"id": sid, "title": by_id[sid]["title"], "status": by_id[sid]["status"]} for sid in stage_ids],
        "omitted_stage_ids": [sid for sid in by_id if sid not in positions],
        "prerequisite_edges": [{"prerequisite_stage_id": a, "dependent_stage_id": b} for a, b in sorted(edges)],
        "limitations": sorted(notes),
    }
