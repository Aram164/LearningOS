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

from .loader import Repo
from .pathing import PathBoundaryError


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


def requirement_fingerprint(requirement: dict) -> str:
    data = json.dumps(requirement, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


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
                    raise RuntimeInputError(f"{relative}:{line_number}: unknown requirement {obs['requirement']}")
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
