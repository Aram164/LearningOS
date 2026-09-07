#!/usr/bin/env python3
"""Plan the Job learning-data collapse into ordinary LearningOS modules.

This module is deliberately a planner, not a writer.  ``plan_migration`` reads
the five declared Job plans and their bounded note/paper inputs, returns exact
``FileChange``/``FileDeletion`` objects, and never mutates either tree.  A
future gateway capability may apply an approved plan after checking
``plan_sha256`` and ``verify_plan_inputs``.  Direct ``--apply`` always refuses.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode
from yaml.resolver import BaseResolver

from learning_os.material_inventory import render_manifest

MIGRATION_ID = "job-quarantine-collapse-v1"
CAPTURED = "2026-08-26"
NEW_CONCEPTS = (
    ("concept-aggregation", "Aggregation"),
    ("concept-aggregation-family", "Aggregation family"),
    ("concept-dataframe-ops", "Dataframe operations"),
    ("concept-dataframe-semantics", "Dataframe semantics"),
    ("concept-dispatch", "Dispatch"),
    ("concept-join-family", "Join family"),
    ("concept-logical-ir", "Logical IR"),
    ("concept-map-family", "Map family"),
    ("concept-op-rewriting", "Operation rewriting"),
    ("concept-projection-family", "Projection family"),
    ("concept-selection-family", "Selection family"),
)
LEGACY_CONCEPTS = frozenset(cid.removeprefix("concept-") for cid, _ in NEW_CONCEPTS)
NOTE_FIELDS = frozenset({
    "id", "type", "title", "created", "reviewed", "role", "state",
    "authorship", "transcription", "semantic_review", "concepts", "sources",
    "attachments", "contexts", "evidence", "supersedes",
})


@dataclass(frozen=True)
class PlanSpec:
    filename: str
    plan_id: str
    module_id: str
    module_title: str
    unit_id: str
    study_map_id: str


PLAN_SPECS = (
    PlanSpec(
        "job-track-git.yaml", "job-track-git", "module-job-git", "Git",
        "unit-job-git-fluency", "study-map-job-git-fluency",
    ),
    PlanSpec(
        "job-track-missing-semester.yaml", "job-track-missing-semester",
        "module-job-engineering-tools", "Engineering tools",
        "unit-job-engineering-tools-fluency",
        "study-map-job-engineering-tools-fluency",
    ),
    PlanSpec(
        "job-track-polars.yaml", "job-track-polars", "module-job-polars",
        "Polars and pandas", "unit-job-polars-pandas-fluency",
        "study-map-job-polars-pandas-fluency",
    ),
    PlanSpec(
        "job-track-python.yaml", "job-track-python",
        "module-job-python-engineering", "Python engineering",
        "unit-job-python-engineering-fluency",
        "study-map-job-python-engineering-fluency",
    ),
    PlanSpec(
        "job-track-rust.yaml", "job-track-rust",
        "module-job-rust-engineering", "Rust engineering",
        "unit-job-rust-engineering-fluency",
        "study-map-job-rust-engineering-fluency",
    ),
)


SOURCE_RECORDS = (
    {
        "id": "source-polars-definitive-guide",
        "title": "Python Polars: The Definitive Guide",
        "type": "book",
        "authors": ["Jeroen Janssens", "Thijs Nieuwdorp"],
        "material": (
            "material://source-polars-definitive-guide/"
            "python-polars-the-definitive-guide.pdf"
        ),
    },
    {
        "id": "source-stratum-paper",
        "title": (
            "stratum: A System Infrastructure for Massive Agent-Centric "
            "ML Workloads [Vision]"
        ),
        "type": "paper",
        "authors": ["Arnab Phani", "Elias Strauss", "Sebastian Schelter"],
        "material": "material://source-stratum-paper/stratum-paper.pdf",
    },
    {
        "id": "source-scalable-dataframe-systems-paper",
        "title": "Towards Scalable Dataframe Systems",
        "type": "paper",
        "authors": [
            "Devin Petersohn", "Stephen Macke", "Doris Xin", "William Ma",
            "Doris Lee", "Xiangxi Mo", "Joseph E. Gonzalez",
            "Joseph M. Hellerstein", "Anthony D. Joseph",
            "Aditya Parameswaran",
        ],
        "year": 2020,
        "material": (
            "material://source-scalable-dataframe-systems-paper/"
            "Towards Scalable Dataframe Systems.pdf"
        ),
    },
)


MATERIAL_SPECS = (
    (
        "source-polars-definitive-guide",
        "LearningOS/python-polars-the-definitive-guide.pdf",
        "software/python/polars-definitive-guide/"
        "python-polars-the-definitive-guide.pdf",
    ),
    (
        "source-stratum-paper",
        "Job/papers/stratum-paper.pdf",
        "data-systems/architecture/stratum-paper/stratum-paper.pdf",
    ),
    (
        "source-scalable-dataframe-systems-paper",
        "Job/legacy-plans/Towards Scalable Dataframe Systems.pdf",
        "data-systems/architecture/scalable-dataframe-systems/"
        "Towards Scalable Dataframe Systems.pdf",
    ),
)


@dataclass(frozen=True)
class Problem:
    code: str
    path: Path
    detail: str


@dataclass(frozen=True)
class FileChange:
    path: Path
    before: str | None
    after: str


@dataclass(frozen=True)
class FileDeletion:
    path: Path
    before: str


@dataclass(frozen=True)
class SourceSnapshot:
    label: str
    path: Path
    size: int
    sha256: str


@dataclass(frozen=True)
class MigrationPlan:
    root: Path
    job_root: Path
    changes: tuple[FileChange, ...]
    deletions: tuple[FileDeletion, ...]
    inputs: tuple[SourceSnapshot, ...]
    problems: tuple[Problem, ...]
    statistics: dict[str, int] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict[str, Any]:
        return {
            "migration": MIGRATION_ID,
            "ready": self.ready,
            "plan_sha256": plan_sha256(self),
            "statistics": dict(sorted(self.statistics.items())),
            "changed_files": [
                _display(self.root, change.path) for change in self.changes
            ],
            "deleted_files": [
                _display(self.root, deletion.path) for deletion in self.deletions
            ],
            "input_files": [
                {
                    "path": item.label,
                    "size": item.size,
                    "sha256": item.sha256,
                }
                for item in self.inputs
            ],
            "problems": [
                {
                    "code": problem.code,
                    "path": _display(self.root, problem.path),
                    "detail": problem.detail,
                }
                for problem in self.problems
            ],
        }


class _UniqueKeyLoader(yaml.SafeLoader):
    """PyYAML loader which refuses silent duplicate-key replacement."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: MappingNode, deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                "found an unhashable key", key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found duplicate key {key!r}", key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping,
)


def _display(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _dump(data: Any) -> str:
    return yaml.safe_dump(
        data, sort_keys=False, allow_unicode=True, width=100,
    )


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _path_symlink(path: Path) -> Path | None:
    """Return the first existing symlink component in an absolute path."""

    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            if current.is_symlink():
                return current
        except OSError:
            return current
        if not current.exists():
            break
    return None


def _target_guard(root: Path, path: Path) -> Problem | None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return Problem("unsafe-target", path, "planned target is outside Core root")
    if relative.is_absolute() or ".." in relative.parts:
        return Problem("unsafe-target", path, "planned target is not a safe relative path")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return Problem(
                "unsafe-symlink-target", current,
                "migration targets may not pass through a symlink",
            )
        if not current.exists():
            break
    return None


def _read_external(
    path: Path,
    label: str,
    snapshots: dict[str, SourceSnapshot],
    problems: list[Problem],
) -> bytes | None:
    symlink = _path_symlink(path)
    if symlink is not None:
        problems.append(Problem(
            "unsafe-symlink-source", symlink,
            f"migration input {label!r} passes through a symlink",
        ))
        return None
    try:
        content = path.read_bytes()
    except OSError as exc:
        problems.append(Problem("missing-input", path, str(exc)))
        return None
    snapshots[label] = SourceSnapshot(
        label=label, path=path, size=len(content), sha256=_sha256_bytes(content),
    )
    return content


def _load_yaml_bytes(content: bytes, path: Path) -> tuple[dict[str, Any] | None, Problem | None]:
    try:
        data = yaml.load(content.decode("utf-8"), Loader=_UniqueKeyLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return None, Problem("invalid-yaml", path, str(exc))
    if not isinstance(data, dict):
        return None, Problem("invalid-document", path, "expected one YAML mapping")
    return data, None


def _walk_bounded(base: Path, problems: list[Problem]) -> list[Path]:
    if base.is_symlink():
        problems.append(Problem(
            "unsafe-symlink-source", base, "source directory is a symlink",
        ))
        return []
    if not base.is_dir():
        problems.append(Problem("missing-input", base, "source directory is missing"))
        return []
    found: list[Path] = []
    for directory, names, filenames in os.walk(base, followlinks=False):
        here = Path(directory)
        keep: list[str] = []
        for name in sorted(names):
            candidate = here / name
            if candidate.is_symlink():
                problems.append(Problem(
                    "unsafe-symlink-source", candidate,
                    "source traversal refuses symlinked directories",
                ))
            else:
                keep.append(name)
        names[:] = keep
        for name in sorted(filenames):
            candidate = here / name
            if candidate.is_symlink():
                problems.append(Problem(
                    "unsafe-symlink-source", candidate,
                    "source traversal refuses symlinked files",
                ))
            elif candidate.is_file():
                found.append(candidate)
    return sorted(found)


def _unit_note(plan: dict[str, Any]) -> str:
    parts = ["# Unit Working Notes", ""]
    for heading, key in (
        ("Title", "title"), ("Horizon", "horizon"),
        ("Cadence", "cadence"), ("Outcome", "outcome"),
    ):
        parts.extend((f"## {heading}", "", str(plan[key]), ""))
    return "\n".join(parts).rstrip() + "\n"


def _stage_note(context: dict[str, Any]) -> str:
    parts = ["# Stage Working Notes", "", "## Mental Models", ""]
    for model in context.get("mental_models", []):
        parts.extend((f"### {model['label']}", "", str(model["text"]), ""))
    parts.extend(("## Read-only Anchor", "", str(context.get("read_only_anchor", "")), ""))
    parts.extend(("## Component", ""))
    parts.extend(f"- {value}" for value in context.get("component", []))
    parts.extend(("", "## Verified Against", "", str(context.get("verified_against", "")), ""))
    parts.extend((
        "## External Code Boundary",
        "",
        (
            "Any Stratum paths above refer to the sibling `semestercontext/Stratum/` "
            "worktree. They are optional read-only learning anchors: LearningOS does "
            "not index, validate, manage, or write that codebase."
        ),
        "",
    ))
    return "\n".join(parts).rstrip() + "\n"


def _verify_stage(stage: Any, path: Path, problems: list[Problem]) -> bool:
    required = {
        "id", "number", "title", "status", "objective", "done_when",
        "exam_critical", "concepts", "scope_triage", "resources",
        "attachments", "source_feedback", "job_context",
    }
    if not isinstance(stage, dict) or not required.issubset(stage):
        problems.append(Problem(
            "invalid-stage", path,
            f"stage must be a mapping with {', '.join(sorted(required))}",
        ))
        return False
    context = stage.get("job_context")
    if not isinstance(context, dict):
        problems.append(Problem("invalid-job-context", path, "job_context must be a mapping"))
        return False
    if not isinstance(context.get("mental_models"), list) or not isinstance(
        context.get("read_only_anchor"), str
    ):
        problems.append(Problem(
            "invalid-job-context", path,
            "job_context requires mental_models and read_only_anchor",
        ))
        return False
    for model in context["mental_models"]:
        if not isinstance(model, dict) or not all(
            isinstance(model.get(key), str) for key in ("label", "text")
        ):
            problems.append(Problem(
                "invalid-job-context", path,
                "each mental model requires string label and text",
            ))
            return False
    if not isinstance(context.get("component", []), list) or not all(
        isinstance(item, str) for item in context.get("component", [])
    ) or not isinstance(context.get("verified_against", ""), str):
        problems.append(Problem(
            "invalid-job-context", path,
            "component must be strings and verified_against must be text",
        ))
        return False
    if not isinstance(stage.get("resources"), list):
        problems.append(Problem("invalid-stage", path, "resources must be a list"))
        return False
    return True


def _flat_material_uri(
    root: Path,
    source_id: str,
    legacy_path: str,
    problem_path: Path,
    problems: list[Problem],
) -> str | None:
    prefix = "LearningOS/materials/"
    physical = root.parent / "materials" / legacy_path.removeprefix(prefix)
    if physical.is_symlink() or not physical.is_file():
        problems.append(Problem(
            "invalid-material-input", physical,
            "legacy material path must resolve to one regular physical file",
        ))
        return None
    flat = root.parent / "materials" / ".flat" / source_id
    if not flat.is_symlink():
        problems.append(Problem(
            "missing-flat-source", flat,
            f"materials/.flat has no source mapping for {source_id}",
        ))
        return None
    try:
        flat_root = flat.resolve(strict=True)
        relative = physical.resolve(strict=True).relative_to(flat_root)
    except (OSError, ValueError) as exc:
        problems.append(Problem(
            "material-source-mismatch", problem_path,
            f"{legacy_path!r} is not inside materials/.flat/{source_id}: {exc}",
        ))
        return None
    return f"material://{source_id}/{relative.as_posix()}"


def _normalise_resource_locator(
    result: dict[str, Any],
    problem_path: Path,
    problems: list[Problem],
) -> bool:
    """Apply the three exact, reviewable locator-to-contract translations."""

    normalizations = {
        "resource-polars-02-05-local-material-contention-probes": (
            "Your own probe scripts — read semantics.py and verify.py as the "
            "reference shape for a probe before writing a new one",
            "semantics.py and verify.py",
            "Reference shape for a probe before writing a new one.",
        ),
        "resource-polars-10-90-local-material-contention-map-groupby": (
            "Your own contention map — read it before the docs; it is more specific "
            "than either library's documentation about where the two disagree",
            "Full contention map",
            (
                "Read it before the docs; it is more specific than either library's "
                "documentation about where the two disagree."
            ),
        ),
        "resource-rust-02-02-the-rust-programming-language": (
            "Chapters 2–3 — Programming a Guessing Game and Common Programming Concepts",
            "Chapters 2–3: Programming a Guessing Game and Common Programming Concepts",
            None,
        ),
    }
    resource_id = result.get("id")
    if resource_id not in normalizations:
        return True
    expected, locator, angle = normalizations[resource_id]
    if result.get("locator") != expected:
        problems.append(Problem(
            "resource-normalization-drift", problem_path,
            f"approved locator normalization no longer matches {resource_id}",
        ))
        return False
    result["locator"] = locator
    if angle is not None:
        result["angle"] = angle
    return True


def _convert_resource(
    root: Path,
    resource: Any,
    problem_path: Path,
    problems: list[Problem],
) -> dict[str, Any] | None:
    if not isinstance(resource, dict) or not isinstance(resource.get("kind"), str) \
            or not isinstance(resource.get("label"), str):
        problems.append(Problem("invalid-resource", problem_path, "resource must be a mapping"))
        return None
    result = copy.deepcopy(resource)
    if not _normalise_resource_locator(result, problem_path, problems):
        return None
    vault_path = result.get("vault_path")
    if vault_path is None:
        return result
    if not isinstance(vault_path, str):
        problems.append(Problem("invalid-vault-path", problem_path, "vault_path must be text"))
        return None
    if vault_path.startswith("LearningOS/materials/"):
        source_id = result.get("source_id")
        if not isinstance(source_id, str):
            problems.append(Problem(
                "material-source-missing", problem_path,
                f"{vault_path!r} has no source_id",
            ))
            return None
        uri = _flat_material_uri(root, source_id, vault_path, problem_path, problems)
        if uri is None:
            return None
        result["vault_path"] = uri
    elif vault_path.startswith("LearningOS/repository/knowledge/"):
        destination = vault_path.removeprefix("LearningOS/repository/")
        canonical = root / destination
        if canonical.is_symlink() or not canonical.exists():
            problems.append(Problem(
                "invalid-knowledge-path", canonical,
                f"canonical knowledge target for {vault_path!r} is absent",
            ))
            return None
        result["vault_path"] = destination
    elif vault_path == "LearningOS/python-polars-the-definitive-guide.pdf":
        result["source_id"] = "source-polars-definitive-guide"
        result["vault_path"] = (
            "material://source-polars-definitive-guide/"
            "python-polars-the-definitive-guide.pdf"
        )
    elif vault_path == (
        "Job/notes/dataframe-semantics/"
        "note-pandas-polars-aggregation-contentions.md"
    ):
        result["vault_path"] = (
            "knowledge/notes/data-systems/dataframe-semantics/"
            "note-pandas-polars-aggregation-contentions.md"
        )
    elif vault_path == "Job/notes/dataframe-semantics/note-pandas-groupby-signatures.md":
        result["vault_path"] = (
            "knowledge/notes/data-systems/dataframe-semantics/"
            "note-pandas-groupby-signatures.md"
        )
    elif vault_path == "Job/notes/dataframe-semantics/probes":
        result["vault_path"] = (
            "knowledge/attachments/"
            "note-pandas-polars-aggregation-contentions"
        )
    else:
        problems.append(Problem(
            "unresolved-vault-path", problem_path,
            f"no deterministic mapping for {vault_path!r}",
        ))
        return None

    return result


def _plan_records_for_plan(
    root: Path,
    spec: PlanSpec,
    plan: dict[str, Any],
    path: Path,
    problems: list[Problem],
) -> tuple[dict[Path, str], set[str], set[str], set[str]]:
    outputs: dict[Path, str] = {}
    required_plan = {
        "type", "plan_template_version", "id", "title", "status", "horizon",
        "cadence", "outcome", "stages",
    }
    if plan.get("type") != "job-learning-plan" or plan.get("plan_template_version") != 1 \
            or plan.get("id") != spec.plan_id or not required_plan.issubset(plan):
        problems.append(Problem(
            "invalid-job-plan", path,
            f"expected canonical v1 Job plan {spec.plan_id!r}",
        ))
        return outputs, set(), set(), set()
    if not all(isinstance(plan.get(key), str) and plan[key].strip() for key in (
        "title", "status", "horizon", "cadence", "outcome",
    )) or not isinstance(plan.get("stages"), list) or not plan["stages"]:
        problems.append(Problem("invalid-job-plan", path, "plan metadata/stages are incomplete"))
        return outputs, set(), set(), set()

    module_root = root / "curriculum" / "modules" / spec.module_id
    unit_root = module_root / "units" / spec.unit_id
    converted_stages: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    stage_ids: set[str] = set()
    resource_ids: set[str] = set()
    for stage in plan["stages"]:
        if not _verify_stage(stage, path, problems):
            continue
        stage_id = stage["id"]
        if not isinstance(stage_id, str) or stage_id in stage_ids:
            problems.append(Problem("duplicate-stage-id", path, f"duplicate/invalid stage id {stage_id!r}"))
            continue
        stage_ids.add(stage_id)
        converted = copy.deepcopy(stage)
        context = converted.pop("job_context")
        converted_resources: list[dict[str, Any]] = []
        for resource in converted["resources"]:
            converted_resource = _convert_resource(root, resource, path, problems)
            if converted_resource is None:
                continue
            resource_id = converted_resource.get("id")
            if isinstance(resource_id, str):
                if resource_id in resource_ids:
                    problems.append(Problem(
                        "duplicate-resource-id", path,
                        f"duplicate resource id {resource_id!r}",
                    ))
                resource_ids.add(resource_id)
            source_id = converted_resource.get("source_id")
            if isinstance(source_id, str):
                source_ids.add(source_id)
            converted_resources.append(converted_resource)
        converted["resources"] = converted_resources
        working_note = (
            f"curriculum/modules/{spec.module_id}/units/{spec.unit_id}/"
            f"stages/{stage_id}/notes.md"
        )
        converted["working_note"] = working_note
        outputs[root / working_note] = _stage_note(context)
        converted_stages.append(converted)

    if len(converted_stages) != len(plan["stages"]):
        return outputs, source_ids, stage_ids, resource_ids
    module = {
        "id": spec.module_id,
        "type": "module",
        "kind": "skill",
        "area_id": "program-job",
        "title": spec.module_title,
        "status": "active",
        "source_map": "source-map.yaml",
        "unit_order": [spec.unit_id],
    }
    source_map = {
        "type": "module-source-map",
        "module_id": spec.module_id,
        "sources": [
            {
                "source_id": source_id,
                "role": "reference",
                "why": f"Referenced by migrated learning plan {spec.plan_id}.",
                "priority": 0,
                "unit_routes": [],
            }
            for source_id in sorted(source_ids)
        ],
    }
    unit_note_path = (
        f"curriculum/modules/{spec.module_id}/units/{spec.unit_id}/notes.md"
    )
    unit = {
        "id": spec.unit_id,
        "type": "unit",
        "module_id": spec.module_id,
        "kind": "topic",
        "title": plan["title"],
        "order": 1,
        "scope": plan["outcome"],
        "status": "ready",
        "scope_sources": [],
        "source_selections": [],
        "working_note": unit_note_path,
        "artifacts": {},
        "workspace_ids": [],
        "current_study_map": spec.study_map_id,
    }
    study_map = {
        "id": spec.study_map_id,
        "type": "study-map",
        "plan_template_version": 1,
        "unit_id": spec.unit_id,
        "status": plan["status"],
        "current_stage": converted_stages[0]["id"],
        "source_plan": {
            "path": f"Job/plans/{spec.filename}",
            "provenance": "migrated-mini-plan",
        },
        "detours": [],
        "shelving": {"state": "none"},
        "stages": converted_stages,
    }
    outputs[module_root / "module.yaml"] = _dump(module)
    outputs[module_root / "source-map.yaml"] = _dump(source_map)
    outputs[unit_root / "unit.yaml"] = _dump(unit)
    outputs[root / unit_note_path] = _unit_note(plan)
    outputs[unit_root / "study-map.yaml"] = _dump(study_map)
    return outputs, source_ids, stage_ids, resource_ids


_FRONTMATTER_RE = re.compile(r"\A---\n(?P<front>.*?)\n---\n", re.DOTALL)


def _note_destination(root: Path, relative: Path) -> Path | None:
    if relative.parts[0] == "dataframe-semantics":
        tail = Path(*relative.parts[1:])
        return root / "knowledge/notes/data-systems/dataframe-semantics" / tail
    if relative.parts[0] == "stratum":
        tail = Path(*relative.parts[1:])
        return root / "knowledge/notes/data-systems/stratum" / tail
    if len(relative.parts) == 1 and relative.name.startswith("note-skrub-"):
        return root / "knowledge/notes/data-systems/skrub" / relative.name
    return None


def _normalise_note(
    text: str,
    path: Path,
    problems: list[Problem],
    *,
    additional_attachments: Iterable[str] = (),
) -> tuple[str | None, str | None]:
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        problems.append(Problem("invalid-note", path, "note has no LF-delimited YAML frontmatter"))
        return None, None
    front = match.group("front")
    try:
        metadata = yaml.load(front, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        problems.append(Problem("invalid-note", path, str(exc)))
        return None, None
    if not isinstance(metadata, dict) or not all(key in metadata for key in (
        "id", "type", "title", "created",
    )):
        problems.append(Problem("invalid-note", path, "required note frontmatter is missing"))
        return None, None
    note_id = metadata.get("id")
    if not isinstance(note_id, str) or re.fullmatch(
        r"note-[a-z0-9]+(?:-[a-z0-9]+)*", note_id,
    ) is None:
        problems.append(Problem("invalid-note-id", path, f"invalid note id {note_id!r}"))
        return None, None

    concepts = metadata.get("concepts", []) or []
    if not isinstance(concepts, list) or not all(isinstance(item, str) for item in concepts):
        problems.append(Problem("invalid-note-concepts", path, "concepts must be strings"))
        return None, None
    attachments = metadata.get("attachments", []) or []
    if not isinstance(attachments, list) or not all(
        isinstance(item, str) and item for item in attachments
    ):
        problems.append(Problem(
            "invalid-note-attachments", path,
            "attachments must be non-empty path strings",
        ))
        return None, None
    merged_attachments = list(dict.fromkeys([
        *attachments,
        *(str(item) for item in additional_attachments),
    ]))
    normalised_concepts: list[str] = []
    for concept in concepts:
        if concept in LEGACY_CONCEPTS:
            normalised_concepts.append(f"concept-{concept}")
        elif concept.startswith("concept-"):
            normalised_concepts.append(concept)
        else:
            problems.append(Problem(
                "unregistered-legacy-concept", path,
                f"no approved normalization for concept {concept!r}",
            ))
            return None, None

    legacy = {
        key: metadata[key]
        for key in ("component", "verified_against", "status")
        if key in metadata
    }
    lines = front.splitlines(keepends=True)
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        field_match = re.match(r"^(?P<indent>\s*)(?P<key>[A-Za-z_]+):(?P<rest>.*)$", line)
        if field_match is None or field_match.group("indent"):
            out.append(line)
            continue
        key = field_match.group("key")
        if key in {"component", "verified_against", "status"}:
            seen.add(key)
            continue
        if key == "authorship" and metadata.get("authorship") == "aram":
            newline = "\n" if line.endswith("\n") else ""
            out.append("authorship: user" + newline)
            seen.add(key)
            continue
        if key == "concepts":
            newline = "\n" if line.endswith("\n") else ""
            rendered = yaml.safe_dump(
                normalised_concepts, default_flow_style=True,
                sort_keys=False, allow_unicode=True,
            ).strip()
            out.append(f"concepts: {rendered}{newline}")
            seen.add(key)
            continue
        if key == "attachments":
            newline = "\n" if line.endswith("\n") else ""
            rendered = yaml.safe_dump(
                merged_attachments, default_flow_style=True,
                sort_keys=False, allow_unicode=True,
            ).strip()
            out.append(f"attachments: {rendered}{newline}")
            seen.add(key)
            continue
        out.append(line)
    if concepts and "concepts" not in seen:
        problems.append(Problem(
            "unsupported-note-frontmatter", path,
            "concepts must use one top-level flow-style line",
        ))
        return None, None
    if merged_attachments and "attachments" not in seen:
        rendered = yaml.safe_dump(
            merged_attachments, default_flow_style=True,
            sort_keys=False, allow_unicode=True,
        ).strip()
        out.append(f"\nattachments: {rendered}")
    transformed_front = "".join(out).rstrip("\n")
    try:
        transformed_meta = yaml.load(transformed_front, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        problems.append(Problem("invalid-normalized-note", path, str(exc)))
        return None, None
    if not isinstance(transformed_meta, dict) or set(transformed_meta) - NOTE_FIELDS:
        extras = sorted(set(transformed_meta or {}) - NOTE_FIELDS)
        problems.append(Problem(
            "invalid-normalized-note", path,
            f"unsupported frontmatter fields remain: {extras}",
        ))
        return None, None
    body = text[match.end():]
    provenance: list[str] = []
    if legacy:
        provenance = ["", "", "## Legacy Job provenance", ""]
        for key in ("component", "verified_against", "status"):
            if key not in legacy:
                continue
            provenance.extend((f"### {key}", ""))
            value = legacy[key]
            if isinstance(value, list):
                provenance.extend(f"- {item}" for item in value)
            else:
                provenance.append(str(value))
            provenance.append("")
    after = "---\n" + transformed_front + "\n---\n" + body
    if provenance:
        after = after.rstrip("\n") + "\n" + "\n".join(provenance).rstrip() + "\n"
    return after, note_id


def _registry_entries(text: str, key: str, path: Path) -> tuple[list[dict[str, Any]] | None, Problem | None]:
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        return None, Problem("invalid-yaml", path, str(exc))
    entries = data.get(key) if isinstance(data, dict) else None
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        return None, Problem("invalid-registry", path, f"expected {key} list")
    return entries, None


def _append_registry(text: str, key: str, records: Iterable[dict[str, Any]]) -> str:
    records = list(records)
    if not records:
        return text
    rendered = _dump({key: records}).splitlines()
    addition = "\n".join("  " + line for line in rendered[1:]) + "\n"
    empty = re.compile(rf"^{re.escape(key)}:\s*\[\]\s*$", re.MULTILINE)
    if empty.search(text):
        return empty.sub(f"{key}:\n" + addition.rstrip("\n"), text, count=1).rstrip("\n") + "\n"
    return text.rstrip("\n") + "\n" + addition


def _plan_concepts(path: Path, problems: list[Problem]) -> tuple[str | None, str | None]:
    if path.is_symlink() or not path.is_file():
        problems.append(Problem("missing-input", path, "concept registry must be a regular file"))
        return None, None
    before = path.read_text(encoding="utf-8")
    entries, problem = _registry_entries(before, "concepts", path)
    if problem or entries is None:
        problems.append(problem or Problem("invalid-registry", path, "invalid concepts"))
        return before, None
    by_id = {item.get("id"): item for item in entries}
    skrub = by_id.get("concept-skrub")
    if not isinstance(skrub, dict):
        problems.append(Problem("missing-concept", path, "concept-skrub is required"))
        return before, None
    after = before
    marker = "  - id: concept-skrub\n"
    start = after.find(marker)
    if start < 0:
        problems.append(Problem("unsupported-registry-style", path, "cannot locate concept-skrub block"))
        return before, None
    next_start = after.find("\n  - id: ", start + len(marker))
    end = len(after) if next_start < 0 else next_start + 1
    block = after[start:end]
    if "quarantin" in block.casefold() or "Job/" in block:
        description = re.compile(r"^    description:.*?(?=^    [a-z_]+:|^  - id:|\Z)", re.M | re.S)
        replacement = "    description: Canonical concept identity for skrub DataOps.\n"
        if description.search(block):
            block = description.sub(replacement, block, count=1)
        else:
            block = block.rstrip("\n") + "\n" + replacement
        after = after[:start] + block + after[end:]

    missing: list[dict[str, Any]] = []
    expected = {cid: {"id": cid, "label": label} for cid, label in NEW_CONCEPTS}
    for cid, record in expected.items():
        existing = by_id.get(cid)
        if existing is None:
            missing.append(record)
        elif existing != record:
            problems.append(Problem(
                "concept-collision", path,
                f"concept {cid!r} already exists with different content",
            ))
    after = _append_registry(after, "concepts", missing)
    return before, after


def _all_registered_sources(root: Path, problems: list[Problem]) -> tuple[set[str], dict[str, dict[str, Any]]]:
    registry = root / "sources" / "registry"
    if registry.is_symlink() or not registry.is_dir():
        problems.append(Problem("missing-input", registry, "source registry directory is missing"))
        return set(), {}
    ids: set[str] = set()
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(registry.glob("*.yaml")):
        if path.is_symlink():
            problems.append(Problem("unsafe-symlink-source", path, "source registry is symlinked"))
            continue
        entries, problem = _registry_entries(path.read_text(encoding="utf-8"), "sources", path)
        if problem or entries is None:
            problems.append(problem or Problem("invalid-registry", path, "invalid sources"))
            continue
        for entry in entries:
            source_id = entry.get("id")
            if not isinstance(source_id, str):
                problems.append(Problem("invalid-source", path, "source id is missing"))
            elif source_id in ids:
                problems.append(Problem("duplicate-source-id", path, f"duplicate source {source_id}"))
            else:
                ids.add(source_id)
                records[source_id] = entry
    return ids, records


def _plan_sources(path: Path, records: dict[str, dict[str, Any]], problems: list[Problem]) -> tuple[str | None, str | None]:
    if path.is_symlink() or not path.is_file():
        problems.append(Problem("missing-input", path, "software source registry must be a regular file"))
        return None, None
    before = path.read_text(encoding="utf-8")
    missing: list[dict[str, Any]] = []
    for expected in SOURCE_RECORDS:
        existing = records.get(expected["id"])
        if existing is None:
            missing.append(expected)
        elif existing != expected:
            problems.append(Problem(
                "source-collision", path,
                f"source {expected['id']!r} already exists with different content",
            ))
    return before, _append_registry(before, "sources", missing)


def _material_source_path(root: Path, job_root: Path, label: str) -> Path:
    if label.startswith("LearningOS/"):
        return root.parent.parent / label
    if label.startswith("Job/"):
        return job_root / label.removeprefix("Job/")
    raise ValueError(label)


def _plan_material_manifest(
    root: Path,
    job_root: Path,
    snapshots: dict[str, SourceSnapshot],
    problems: list[Problem],
) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    manifest_path = root / "records" / "materials-manifest.yaml"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        problems.append(Problem("missing-input", manifest_path, "materials manifest is missing"))
        return None, None, []
    before = manifest_path.read_text(encoding="utf-8")
    try:
        manifest = yaml.load(before, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        problems.append(Problem("invalid-yaml", manifest_path, str(exc)))
        return before, None, []
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict) \
            or not isinstance(manifest.get("totals"), dict):
        problems.append(Problem("invalid-materials-manifest", manifest_path, "invalid manifest shape"))
        return before, None, []
    files = dict(manifest["files"])
    if manifest["totals"].get("files") != len(files) or manifest["totals"].get("bytes") != sum(
        row.get("size", -1) for row in files.values() if isinstance(row, dict)
    ):
        problems.append(Problem(
            "invalid-materials-manifest", manifest_path,
            "manifest totals do not match its current rows",
        ))
        return before, None, []

    material_rows: list[dict[str, Any]] = []
    added_manifest_rows = False
    materials = root.parent / "materials"
    if materials.is_symlink() or not materials.is_dir():
        problems.append(Problem("unsafe-materials-root", materials, "materials root is missing or symlinked"))
    for source_id, source_label, target_relative in MATERIAL_SPECS:
        source_path = _material_source_path(root, job_root, source_label)
        content = _read_external(source_path, source_label, snapshots, problems)
        if content is None:
            continue
        wanted = {"size": len(content), "sha256": _sha256_bytes(content)}
        target = materials / target_relative
        symlink = _path_symlink(target)
        if symlink is not None:
            problems.append(Problem(
                "unsafe-symlink-target", symlink,
                "prepared material target may not be symlinked",
            ))
        else:
            try:
                target_content = target.read_bytes()
            except OSError as exc:
                problems.append(Problem("material-target-missing", target, str(exc)))
            else:
                if len(target_content) != wanted["size"] or _sha256_bytes(target_content) != wanted["sha256"]:
                    problems.append(Problem(
                        "material-target-mismatch", target,
                        "prepared material target differs from migration source",
                    ))
                else:
                    target_label = f"LearningOS/materials/{target_relative}"
                    snapshots[target_label] = SourceSnapshot(
                        target_label, target, len(target_content), _sha256_bytes(target_content),
                    )
        flat = materials / ".flat" / source_id
        expected_directory = target.parent
        try:
            flat_ok = flat.is_symlink() and flat.resolve(strict=True) == expected_directory.resolve(strict=True)
        except OSError:
            flat_ok = False
        if not flat_ok:
            problems.append(Problem(
                "material-flat-mismatch", flat,
                f".flat/{source_id} must resolve to {expected_directory}",
            ))

        current = files.get(target_relative)
        if current is None:
            files[target_relative] = wanted
            added_manifest_rows = True
        elif current != wanted:
            problems.append(Problem(
                "material-manifest-collision", manifest_path,
                f"manifest row {target_relative!r} conflicts with source bytes",
            ))
        material_rows.append({
            "source_id": source_id,
            "source": source_label,
            "destination": f"LearningOS/materials/{target_relative}",
            **wanted,
        })

    # The capture date describes the complete external-material inventory, not
    # the migration. Stamp the migration date only when this plan actually
    # adds rows. A later full manifest rebuild owns its newer capture date and
    # must not make the already-applied one-time migration non-idempotent.
    if added_manifest_rows:
        manifest["captured"] = CAPTURED
    manifest["files"] = files
    manifest["totals"] = {
        "files": len(files),
        "bytes": sum(row["size"] for row in files.values()),
    }
    # The inventory has one renderer, and it is not this module's `_dump`.
    # `learning_os.material_inventory.render_manifest` owns wrap width and key
    # ordering, so `make inventory` and this migration cannot disagree
    # about the bytes of a file neither one fully owns. It supplies its own
    # header, so the header no longer has to be sliced off the prior text.
    after = render_manifest(manifest)
    return before, after, material_rows


def _desired_change(
    root: Path,
    path: Path,
    after: str,
    changes: list[FileChange],
    problems: list[Problem],
    *,
    managed_before: str | None = None,
) -> None:
    guard = _target_guard(root, path)
    if guard:
        problems.append(guard)
        return
    if managed_before is not None:
        if after != managed_before:
            changes.append(FileChange(path, managed_before, after))
        return
    if path.exists():
        if path.is_symlink() or not path.is_file():
            problems.append(Problem("destination-collision", path, "destination is not a regular file"))
            return
        before = path.read_text(encoding="utf-8")
        if before != after:
            problems.append(Problem(
                "destination-collision", path,
                "destination exists with non-idempotent content",
            ))
        return
    changes.append(FileChange(path, None, after))


def _existing_note_ids(root: Path, excluded: set[Path], problems: list[Problem]) -> dict[str, Path]:
    notes = root / "knowledge" / "notes"
    found: dict[str, Path] = {}
    if not notes.is_dir() or notes.is_symlink():
        return found
    for path in sorted(notes.rglob("*.md")):
        if path in excluded or path.is_symlink():
            continue
        match = _FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            meta = yaml.safe_load(match.group("front"))
        except yaml.YAMLError:
            continue
        note_id = meta.get("id") if isinstance(meta, dict) else None
        if isinstance(note_id, str):
            found.setdefault(note_id, path)
    return found


def _provenance(
    snapshots: dict[str, SourceSnapshot],
    material_rows: list[dict[str, Any]],
    statistics: dict[str, int],
) -> str:
    groups: dict[str, list[dict[str, Any]]] = {
        "plans": [], "notes": [], "probes": [], "materials": [],
    }
    for item in sorted(snapshots.values(), key=lambda row: row.label):
        if item.label.startswith("Job/plans/"):
            group = "plans"
        elif item.label.startswith("Job/notes/") and item.label.endswith(".md"):
            group = "notes"
        elif item.label.startswith("Job/notes/") and item.label.endswith(".py"):
            group = "probes"
        elif item.label in {
            source_label for _, source_label, _ in MATERIAL_SPECS
        } or item.label.startswith("LearningOS/materials/"):
            group = "materials"
        else:
            continue
        groups[group].append({
            "path": item.label, "size": item.size, "sha256": item.sha256,
        })
    document = {
        "schema_version": 1,
        "id": MIGRATION_ID,
        "type": "migration-provenance",
        "status": "applied",
        "applied": CAPTURED,
        "application": "legacy.job-learning.migrate via GatewayEnvelopeV2",
        "program_id": "program-job",
        "statistics": dict(sorted(statistics.items())),
        "plans": [
            {
                "source": f"Job/plans/{spec.filename}",
                "module_id": spec.module_id,
                "unit_id": spec.unit_id,
                "study_map_id": spec.study_map_id,
            }
            for spec in PLAN_SPECS
        ],
        "source_files": groups,
        "material_targets": material_rows,
        "normalizations": {
            "authorship": "aram -> user",
            "legacy_concepts": [cid for cid, _ in NEW_CONCEPTS],
            "legacy_note_fields": ["component", "verified_against", "status"],
        },
        "preservation": {
            "original_job_data": "retained",
            "stratum_references": "prose-only",
            "concept_relations_inferred": False,
            "source_evaluations_inferred": False,
        },
    }
    return _dump(document)


def plan_migration(root: Path, job_root: Path | None = None) -> MigrationPlan:
    """Return an exact, deterministic, no-write collapse plan.

    This is the public gateway integration entry point.  ``root`` is Core's
    repository root.  ``job_root`` defaults to the shelved
    ``LearningOS/legacy/Job`` source tree.
    """

    raw_root = Path(root).absolute()
    raw_job = Path(job_root).absolute() if job_root is not None else None
    initial: list[Problem] = []
    root_link = _path_symlink(raw_root)
    if root_link is not None:
        initial.append(Problem("unsafe-symlink-root", root_link, "Core root is symlinked"))
    resolved_root = raw_root.resolve(strict=False)
    resolved_job = (
        raw_job.resolve(strict=False) if raw_job is not None
        else resolved_root.parent / "legacy" / "Job"
    )
    job_link = _path_symlink(raw_job or resolved_job)
    if job_link is not None:
        initial.append(Problem("unsafe-symlink-root", job_link, "Job root is symlinked"))
    if not resolved_root.is_dir():
        initial.append(Problem("missing-root", resolved_root, "Core root is missing"))
    if not resolved_job.is_dir():
        initial.append(Problem("missing-root", resolved_job, "Job root is missing"))
    if initial:
        return MigrationPlan(
            resolved_root, resolved_job, (), (), (), tuple(initial), {},
        )

    problems: list[Problem] = []
    snapshots: dict[str, SourceSnapshot] = {}
    desired: dict[Path, str] = {}
    all_source_ids: set[str] = set()
    all_stage_ids: set[str] = set()
    all_resource_ids: set[str] = set()
    statistics = {"plans": 0, "stages": 0, "resources": 0, "notes": 0, "probes": 0}

    plan_dir = resolved_job / "plans"
    actual_plans = sorted(path.name for path in plan_dir.glob("job-track-*.yaml")) \
        if plan_dir.is_dir() and not plan_dir.is_symlink() else []
    expected_plans = sorted(spec.filename for spec in PLAN_SPECS)
    if actual_plans != expected_plans:
        problems.append(Problem(
            "unexpected-plan-inventory", plan_dir,
            f"expected exactly {expected_plans}, found {actual_plans}",
        ))
    for spec in PLAN_SPECS:
        path = plan_dir / spec.filename
        content = _read_external(path, f"Job/plans/{spec.filename}", snapshots, problems)
        if content is None:
            continue
        plan, problem = _load_yaml_bytes(content, path)
        if problem or plan is None:
            problems.append(problem or Problem("invalid-job-plan", path, "invalid plan"))
            continue
        outputs, source_ids, stage_ids, resource_ids = _plan_records_for_plan(
            resolved_root, spec, plan, path, problems,
        )
        for output, text in outputs.items():
            if output in desired and desired[output] != text:
                problems.append(Problem("planned-path-collision", output, "two outputs disagree"))
            desired[output] = text
        duplicate_stages = all_stage_ids & stage_ids
        duplicate_resources = all_resource_ids & resource_ids
        for value in sorted(duplicate_stages):
            problems.append(Problem("duplicate-stage-id", path, f"global stage id collision {value}"))
        for value in sorted(duplicate_resources):
            problems.append(Problem("duplicate-resource-id", path, f"global resource id collision {value}"))
        all_stage_ids.update(stage_ids)
        all_resource_ids.update(resource_ids)
        all_source_ids.update(source_ids)
        statistics["plans"] += 1
        statistics["stages"] += len(plan.get("stages", []))
        statistics["resources"] += sum(
            len(stage.get("resources", []))
            for stage in plan.get("stages", []) if isinstance(stage, dict)
        )

    program = {
        "id": "program-job",
        "type": "program",
        "title": "Job",
        "kind": "skills",
        "status": "active",
        "default": False,
        "semester_bound": False,
        "description": "Job learning represented as ordinary LearningOS skill modules.",
        "semesters": [],
    }
    desired[resolved_root / "curriculum/programs/program-job.yaml"] = _dump(program)

    probe_root = resolved_job / "notes/dataframe-semantics/probes"
    probe_files = sorted(
        path for path in _walk_bounded(probe_root, problems)
        if path.suffix == ".py"
    )
    if len(probe_files) != 8:
        problems.append(Problem(
            "unexpected-probe-inventory", probe_root,
            f"expected 8 probe scripts, found {len(probe_files)}",
        ))
    probe_attachment_paths = tuple(
        "knowledge/attachments/note-pandas-polars-aggregation-contentions/"
        f"{path.name}"
        for path in probe_files
    )

    note_files = [
        path for path in _walk_bounded(resolved_job / "notes", problems)
        if path.suffix == ".md" and path.name not in {"README.md", "_TEMPLATE.md"}
    ]
    if len(note_files) != 19:
        problems.append(Problem(
            "unexpected-note-inventory", resolved_job / "notes",
            f"expected 19 real notes, found {len(note_files)}",
        ))
    note_ids: dict[str, Path] = {}
    note_destinations: set[Path] = set()
    for path in note_files:
        relative = path.relative_to(resolved_job / "notes")
        destination = _note_destination(resolved_root, relative)
        if destination is None:
            problems.append(Problem(
                "unresolved-note-destination", path,
                f"no standard destination for {relative.as_posix()}",
            ))
            continue
        content = _read_external(
            path, f"Job/notes/{relative.as_posix()}", snapshots, problems,
        )
        if content is None:
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            problems.append(Problem("invalid-note", path, str(exc)))
            continue
        after, note_id = _normalise_note(
            text,
            path,
            problems,
            additional_attachments=(
                probe_attachment_paths
                if relative == Path(
                    "dataframe-semantics/"
                    "note-pandas-polars-aggregation-contentions.md"
                )
                else ()
            ),
        )
        if after is None or note_id is None:
            continue
        if note_id in note_ids:
            problems.append(Problem(
                "duplicate-note-id", path,
                f"note id {note_id!r} also appears in {note_ids[note_id]}",
            ))
        note_ids[note_id] = path
        note_destinations.add(destination)
        desired[destination] = after
        statistics["notes"] += 1

    existing_notes = _existing_note_ids(resolved_root, note_destinations, problems)
    for note_id, source_path in note_ids.items():
        collision = existing_notes.get(note_id)
        if collision is not None:
            problems.append(Problem(
                "note-id-collision", collision,
                f"migrated {source_path.name} reuses canonical id {note_id}",
            ))

    for path in probe_files:
        content = _read_external(
            path,
            f"Job/notes/dataframe-semantics/probes/{path.name}",
            snapshots,
            problems,
        )
        if content is None:
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            problems.append(Problem("invalid-probe", path, str(exc)))
            continue
        desired[
            resolved_root / "knowledge/attachments/"
            "note-pandas-polars-aggregation-contentions" / path.name
        ] = text
        statistics["probes"] += 1

    registered_ids, source_records = _all_registered_sources(resolved_root, problems)
    planned_source_ids = {record["id"] for record in SOURCE_RECORDS}
    unknown_sources = all_source_ids - registered_ids - planned_source_ids
    for source_id in sorted(unknown_sources):
        problems.append(Problem(
            "unregistered-source", resolved_root / "sources",
            f"study resources reference unknown source {source_id}",
        ))

    concepts_path = resolved_root / "knowledge/concepts.yaml"
    concepts_before, concepts_after = _plan_concepts(concepts_path, problems)
    software_path = resolved_root / "sources/registry/software.yaml"
    software_before, software_after = _plan_sources(software_path, source_records, problems)
    manifest_before, manifest_after, material_rows = _plan_material_manifest(
        resolved_root, resolved_job, snapshots, problems,
    )

    provenance_path = resolved_root / "operations/migrations" / f"{MIGRATION_ID}.yaml"
    desired[provenance_path] = _provenance(snapshots, material_rows, statistics)

    changes: list[FileChange] = []
    for path, after in sorted(desired.items(), key=lambda row: row[0].as_posix()):
        _desired_change(resolved_root, path, after, changes, problems)
    for path, before, after in (
        (concepts_path, concepts_before, concepts_after),
        (software_path, software_before, software_after),
        (resolved_root / "records/materials-manifest.yaml", manifest_before, manifest_after),
    ):
        if before is not None and after is not None:
            _desired_change(
                resolved_root, path, after, changes, problems,
                managed_before=before,
            )

    deletions: list[FileDeletion] = []
    boundary = resolved_root / "curriculum/programs/program-job-boundary.yaml"
    guard = _target_guard(resolved_root, boundary)
    if guard:
        problems.append(guard)
    elif boundary.exists():
        if boundary.is_symlink() or not boundary.is_file():
            problems.append(Problem("unsafe-symlink-target", boundary, "boundary target is unsafe"))
        else:
            before = boundary.read_text(encoding="utf-8")
            try:
                data = yaml.safe_load(before)
            except yaml.YAMLError as exc:
                problems.append(Problem("invalid-boundary", boundary, str(exc)))
            else:
                if not isinstance(data, dict) or data.get("id") != "program-job-boundary":
                    problems.append(Problem(
                        "destination-collision", boundary,
                        "refusing to delete a non-boundary program record",
                    ))
                else:
                    deletions.append(FileDeletion(boundary, before))

    return MigrationPlan(
        root=resolved_root,
        job_root=resolved_job,
        changes=tuple(sorted(changes, key=lambda item: item.path.as_posix())),
        deletions=tuple(sorted(deletions, key=lambda item: item.path.as_posix())),
        inputs=tuple(sorted(snapshots.values(), key=lambda item: item.label)),
        problems=tuple(sorted(
            problems, key=lambda item: (item.path.as_posix(), item.code, item.detail),
        )),
        statistics=statistics,
    )


def render_diff(plan: MigrationPlan) -> str:
    """Render the exact deterministic unified diff bound by ``plan_sha256``."""

    operations: list[tuple[Path, str]] = []
    for change in plan.changes:
        relative = _display(plan.root, change.path)
        before = "" if change.before is None else change.before
        operations.append((change.path, "".join(difflib.unified_diff(
            before.splitlines(keepends=True),
            change.after.splitlines(keepends=True),
            fromfile="/dev/null" if change.before is None else f"a/{relative}",
            tofile=f"b/{relative}",
        ))))
    for deletion in plan.deletions:
        relative = _display(plan.root, deletion.path)
        operations.append((deletion.path, "".join(difflib.unified_diff(
            deletion.before.splitlines(keepends=True), [],
            fromfile=f"a/{relative}", tofile="/dev/null",
        ))))
    return "".join(chunk for _, chunk in sorted(operations, key=lambda row: row[0].as_posix()))


def plan_sha256(plan: MigrationPlan) -> str:
    """Hash the exact diff plus every external input/target byte snapshot."""

    payload = {
        "migration": MIGRATION_ID,
        "diff": render_diff(plan),
        "inputs": [
            {"path": item.label, "size": item.size, "sha256": item.sha256}
            for item in plan.inputs
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def migration_artifact_ids(plan: MigrationPlan) -> tuple[str, ...]:
    """Return the closed logical concurrency set for this exact migration.

    The global snapshot binds all canonical bytes. These identities add the
    same artifact-level guards used by ordinary program, module, unit, map,
    note, source, and attachment writes. An unfamiliar target is a planner
    defect and therefore refuses before the transaction boundary.
    """

    artifacts: set[str] = set()
    for change in plan.changes:
        relative = change.path.relative_to(plan.root).parts
        if relative == ("curriculum", "programs", "program-job.yaml"):
            artifacts.add("program-job")
        elif len(relative) == 4 and relative[:2] == ("curriculum", "modules"):
            module_id, filename = relative[2], relative[3]
            if module_id not in {spec.module_id for spec in PLAN_SPECS}:
                raise ValueError(f"undeclared migrated module target: {'/'.join(relative)}")
            if filename == "module.yaml":
                artifacts.add(module_id)
            elif filename == "source-map.yaml":
                artifacts.add(f"source-map-{module_id.removeprefix('module-')}")
            else:
                raise ValueError(f"undeclared module target: {'/'.join(relative)}")
        elif len(relative) == 6 and relative[:2] == ("curriculum", "modules") \
                and relative[3] == "units":
            module_id, unit_id, filename = relative[2], relative[4], relative[5]
            spec = next((item for item in PLAN_SPECS if item.module_id == module_id), None)
            if spec is None or unit_id != spec.unit_id \
                    or filename not in {"unit.yaml", "notes.md", "study-map.yaml"}:
                raise ValueError(f"undeclared unit target: {'/'.join(relative)}")
            artifacts.add(unit_id)
            if filename == "study-map.yaml":
                data = yaml.safe_load(change.after)
                if not isinstance(data, dict) or data.get("id") != spec.study_map_id:
                    raise ValueError(f"invalid planned study-map target: {'/'.join(relative)}")
                artifacts.add(spec.study_map_id)
        elif len(relative) == 8 and relative[:2] == ("curriculum", "modules") \
                and relative[3] == "units" and relative[5] == "stages" \
                and relative[7] == "notes.md":
            module_id, unit_id, stage_id = relative[2], relative[4], relative[6]
            spec = next((item for item in PLAN_SPECS if item.module_id == module_id), None)
            if spec is None or unit_id != spec.unit_id or not stage_id.startswith("stage-"):
                raise ValueError(f"undeclared stage target: {'/'.join(relative)}")
            artifacts.add(stage_id)
        elif relative[:3] == ("knowledge", "notes", "data-systems") \
                and relative[-1].endswith(".md"):
            match = _FRONTMATTER_RE.match(change.after)
            metadata = yaml.safe_load(match.group("front")) if match else None
            note_id = metadata.get("id") if isinstance(metadata, dict) else None
            if not isinstance(note_id, str) or not note_id.startswith("note-"):
                raise ValueError(f"invalid planned note target: {'/'.join(relative)}")
            artifacts.add(note_id)
        elif relative[:3] == (
            "knowledge", "attachments", "note-pandas-polars-aggregation-contentions",
        ) and len(relative) == 4 and relative[-1].endswith(".py"):
            artifacts.add(f"attachment:{'/'.join(relative)}")
        elif relative == ("knowledge", "concepts.yaml"):
            artifacts.add("concept-skrub")
            artifacts.update(cid for cid, _ in NEW_CONCEPTS)
        elif relative == ("sources", "registry", "software.yaml"):
            artifacts.update(record["id"] for record in SOURCE_RECORDS)
        elif relative == ("records", "materials-manifest.yaml"):
            artifacts.add("materials-manifest")
        elif relative == ("operations", "migrations", f"{MIGRATION_ID}.yaml"):
            artifacts.add(MIGRATION_ID)
        else:
            raise ValueError(f"undeclared migration target: {'/'.join(relative)}")

    for deletion in plan.deletions:
        relative = deletion.path.relative_to(plan.root).parts
        if relative != ("curriculum", "programs", "program-job-boundary.yaml"):
            raise ValueError(f"undeclared migration deletion: {'/'.join(relative)}")
        artifacts.add("program-job-boundary")
    return tuple(sorted(artifacts))


def verify_plan_inputs(plan: MigrationPlan) -> tuple[Problem, ...]:
    """Recheck source hashes and before-images immediately before gateway apply.

    Exact already-applied outputs are accepted as idempotent.  Any other
    source, target, or canonical before-image drift is returned as a blocker.
    """

    problems: list[Problem] = []
    for item in plan.inputs:
        symlink = _path_symlink(item.path)
        if symlink is not None:
            problems.append(Problem("unsafe-symlink-source", symlink, item.label))
            continue
        try:
            content = item.path.read_bytes()
        except OSError as exc:
            problems.append(Problem("source-drift", item.path, str(exc)))
            continue
        if len(content) != item.size or _sha256_bytes(content) != item.sha256:
            problems.append(Problem(
                "source-drift", item.path,
                f"{item.label} changed after plan approval",
            ))
    for change in plan.changes:
        if change.path.is_symlink():
            problems.append(Problem("unsafe-symlink-target", change.path, "target became a symlink"))
            continue
        if change.before is None:
            if change.path.exists() and change.path.read_text(encoding="utf-8") != change.after:
                problems.append(Problem("destination-drift", change.path, "new destination appeared"))
        else:
            try:
                current = change.path.read_text(encoding="utf-8")
            except OSError as exc:
                problems.append(Problem("destination-drift", change.path, str(exc)))
            else:
                if current not in {change.before, change.after}:
                    problems.append(Problem("destination-drift", change.path, "before-image changed"))
    for deletion in plan.deletions:
        if deletion.path.exists() and deletion.path.read_text(encoding="utf-8") != deletion.before:
            problems.append(Problem("destination-drift", deletion.path, "deletion before-image changed"))
    return tuple(sorted(
        problems, key=lambda item: (item.path.as_posix(), item.code, item.detail),
    ))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--job-root", type=Path,
        help="explicit Job source root for this dry-run only",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--diff", action="store_true")
    args = parser.parse_args(argv)

    if args.apply:
        print(
            "refusing direct --apply: an approved legacy.job-learning.migrate "
            "GatewayEnvelopeV2 capability must bind plan_sha256 and recheck "
            "all before-images"
        )
        return 2

    plan = plan_migration(args.root, args.job_root)
    if args.json:
        print(json.dumps(plan.as_dict(), indent=2, sort_keys=True, ensure_ascii=False))
    else:
        state = "ready" if plan.ready else "blocked"
        print(
            f"{MIGRATION_ID}: {state}; {len(plan.changes)} change(s); "
            f"{len(plan.deletions)} deletion(s); {len(plan.problems)} problem(s); "
            f"plan {plan_sha256(plan)}"
        )
        for problem in plan.problems:
            print(f"{problem.code}: {_display(plan.root, problem.path)}: {problem.detail}")
    if args.diff:
        print(render_diff(plan), end="")
    return 0 if plan.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
