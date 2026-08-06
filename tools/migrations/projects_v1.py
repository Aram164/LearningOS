#!/usr/bin/env python3
"""Migrate the bachelor thesis from a compatibility module to a Project.

Dry-run is the default.  ``--apply`` commits the migration through the shared
transaction service; ``--rollback`` restores the backed-up compatibility files
and removes the new project records as one receipt-producing transaction.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from learning_os.genout import generate_all, write_outputs  # noqa: E402
from learning_os.loader import load_repo, parse_frontmatter  # noqa: E402
from learning_os.rules import validate  # noqa: E402
from learning_os.transactions import TransactionFailure, TransactionService  # noqa: E402

MIGRATION = "projects-v1"
OLD_MODULE_ID = "module-project-bachelor-thesis"
PROJECT_ID = "project-bachelor-thesis"
WORKSPACE_ID = "workspace-thesis-mle-medical"
PROGRAM_ID = "program-thesis-projects"


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextlib.contextmanager
def lock(root: Path):
    token = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]
    path = Path(tempfile.gettempdir()) / f"learningos-{token}.lock"
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def paths(root: Path) -> dict[str, Path]:
    return {
        "module": root / "curriculum/modules/module-project-bachelor-thesis/module.yaml",
        "program": root / "curriculum/programs/program-thesis-projects.yaml",
        "workspace": root / "work/active/workspace-thesis-mle-medical/CONTEXT.md",
        "project": root / "projects/registry/project-bachelor-thesis.yaml",
        "aliases": root / "projects/aliases.yaml",
        "relations": root / "projects/relations/project-relations.yaml",
        "backup": root / "migration/backups/projects-v1",
    }


def project_record(root: Path, module_data: dict, workspace_body: str) -> dict:
    objective = "Explore and optimize machine-learning-engineering agents for medical use cases."
    section = workspace_body.split("## Objective", 1)
    if len(section) == 2:
        first = section[1].split("## ", 1)[0].strip().split("\n\n", 1)[0]
        objective = " ".join(first.replace("**", "").split()) or objective
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "id": PROJECT_ID,
        "type": "project",
        "revision": 0,
        "title": module_data.get("title", "Bachelor thesis"),
        "project_type": "thesis",
        "status": "active",
        "root_uri": "github://Aram164/LearningOS",
        "objective": objective,
        "milestone_ids": ["milestone-thesis-scope", "milestone-thesis-baseline"],
        "linked_module_ids": ["module-hu-aml", "module-hu-amls", "module-hu-ppds"],
        "unit_ids": ["unit-thesis-landscape", "unit-thesis-experiments"],
        "workspace_ids": [WORKSPACE_ID],
        "thematic_group_ids": list(module_data.get("thematic_group_ids", [])),
        "boundaries": {
            "confidentiality": "private",
            "external_code_access": "approved",
            "notes": "Employer code and Job/ remain outside this project record.",
        },
        "structure": {
            "kind": "parallel",
            "nodes": [
                {
                    "id": "workstream-thesis-landscape",
                    "title": "Landscape and scope",
                    "kind": "workstream",
                    "status": "active",
                    "children": [
                        {"id": "step-thesis-scope", "title": "Confirm scope and compute budget", "kind": "step", "status": "active"},
                        {"id": "step-thesis-survey", "title": "Map MLE-agent and medical benchmark landscape", "kind": "step", "status": "active"},
                    ],
                },
                {
                    "id": "workstream-thesis-experiments",
                    "title": "Baseline and optimization experiments",
                    "kind": "workstream",
                    "status": "planned",
                    "children": [
                        {
                            "id": "step-map-thesis-baseline",
                            "title": "Baseline reproduction map",
                            "kind": "step-map",
                            "status": "planned",
                            "children": [
                                {"id": "step-thesis-aide-baseline", "title": "Reproduce the AIDE baseline", "kind": "step", "status": "planned"},
                                {"id": "step-thesis-optimization", "title": "Run bounded optimization comparisons", "kind": "step", "status": "planned"},
                            ],
                        },
                    ],
                },
            ],
        },
        "files": [
            {"label": "Original thesis brief", "path": "work/active/workspace-thesis-mle-medical/inputs/original-thesis-brief.md", "kind": "input"},
            {"label": "Landscape and experiment plan", "path": "work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md", "kind": "output"},
        ],
        "decisions": [
            {
                "id": "decision-thesis-scope-boundary",
                "title": "Benchmark scope",
                "status": "open",
                "summary": "Decide whether the thesis stays within the MLE-bench medical subset or includes BioML-bench/ReX-MLE.",
            },
            {
                "id": "decision-thesis-compute-budget",
                "title": "Compute budget",
                "status": "open",
                "summary": "Confirm GPU access, wall-clock limits, and allowed model/API budget before experiments.",
            },
        ],
        "migrated_from": OLD_MODULE_ID,
        "migrated_at": timestamp,
        "migration": MIGRATION,
        "source_sha256": sha256(paths(root)["module"]),
    }


def build_apply(root: Path) -> tuple[dict[Path, str], dict]:
    p = paths(root)
    module_data = yaml.safe_load(p["module"].read_text(encoding="utf-8"))
    program_data = yaml.safe_load(p["program"].read_text(encoding="utf-8"))
    workspace_text = p["workspace"].read_text(encoding="utf-8")
    workspace_meta, workspace_body = parse_frontmatter(workspace_text, p["workspace"])
    project = project_record(root, module_data, workspace_body)

    migrated_at = project["migrated_at"]
    module_after = dict(module_data)
    module_after.update({
        "compatibility_only": True,
        "migrated_to": PROJECT_ID,
        "migrated_at": migrated_at,
        "migration": MIGRATION,
        "source_sha256": project["source_sha256"],
    })
    program_after = dict(program_data)
    program_after["status"] = "metadata-only"
    workspace_after = dict(workspace_meta)
    workspace_after["project_id"] = PROJECT_ID

    aliases = {"aliases": {OLD_MODULE_ID: PROJECT_ID}}
    relations = {
        "relations": [
            {
                "id": "relationship-thesis-amls",
                "from_project_id": PROJECT_ID,
                "to_id": "module-hu-amls",
                "to_type": "module",
                "relation_type": "informs",
                "reason": "Advanced ML Systems is the closest active module to the thesis systems questions.",
                "contribution": "Provides systems vocabulary, evaluation discipline, and reference methods for the experiments.",
            },
            {
                "id": "relationship-thesis-project-toolbox",
                "from_project_id": PROJECT_ID,
                "to_id": "project-toolbox",
                "to_type": "topic-pack",
                "relation_type": "uses",
                "reason": "The Project Toolbox is the narrow working shelf chosen for this project.",
                "contribution": "Keeps implementation and experiment-support materials in a deliberate working order.",
            },
            {
                "id": "relationship-thesis-landscape-plan",
                "from_project_id": PROJECT_ID,
                "to_id": "file-thesis-landscape-plan",
                "to_type": "file",
                "relation_type": "produces",
                "reason": "This is the project-owned planning output for the current thesis scope.",
                "contribution": "Stores the evidence landscape, bounded experiment design, and unresolved decisions.",
                "path": "work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md",
            },
        ]
    }
    writes = {
        p["project"]: dump_yaml(project),
        p["aliases"]: dump_yaml(aliases),
        p["relations"]: dump_yaml(relations),
        p["module"]: dump_yaml(module_after),
        p["program"]: dump_yaml(program_after),
        p["workspace"]: render_frontmatter(workspace_after, workspace_body),
    }
    summary = {
        "module": OLD_MODULE_ID,
        "project": PROJECT_ID,
        "workspace": WORKSPACE_ID,
        "program": PROGRAM_ID,
        "writes": [path.relative_to(root).as_posix() for path in writes],
    }
    return writes, summary


def report(root: Path, summary: dict, mode: str) -> Path:
    directory = root / "migration/reports"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"projects-{dt.date.today().isoformat()}.md"
    lines = [
        "# Projects migration report", "", f"Mode: **{mode}**", "",
        "## Identity change", "",
        f"- `{summary['module']}` → `{summary['project']}`", "",
        "## Files", "",
        *[f"- `{path}`" for path in summary["writes"]], "",
        "## Compatibility", "",
        "- The old module ID remains resolvable through `projects/aliases.yaml`.",
        "- Existing thesis units and workspace files stay in place.",
        "- The compatibility module remains on disk until the retirement gate.", "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def publish(root: Path) -> None:
    repo = load_repo(root)
    write_outputs(repo, generate_all(repo))


def new_validation_errors(root: Path, baseline: set[str]):
    return [
        issue for issue in validate(load_repo(root), online=False)
        if issue.severity == "E" and str(issue) not in baseline
    ]


def apply(root: Path) -> int:
    p = paths(root)
    if p["project"].is_file():
        print(json.dumps({"ok": True, "mode": "apply", "changed": False, "project_id": PROJECT_ID}))
        return 0
    writes, summary = build_apply(root)
    p["backup"].mkdir(parents=True, exist_ok=True)
    for key in ("module", "program", "workspace"):
        shutil.copy2(p[key], p["backup"] / p[key].name)
    baseline = {str(issue) for issue in validate(load_repo(root), online=False) if issue.severity == "E"}
    with lock(root):
        try:
            result = TransactionService(root).commit(
                capability="project.migrate",
                writes=writes,
                artifact_ids=[PROJECT_ID, OLD_MODULE_ID, WORKSPACE_ID, PROGRAM_ID],
                validate_state=lambda: new_validation_errors(root, baseline),
                publish=lambda: publish(root),
                metadata={"migration": MIGRATION, "source": OLD_MODULE_ID},
            )
        except TransactionFailure as exc:
            print(f"projects migration failed: {exc}", file=sys.stderr)
            return 1
    report_path = report(root, summary, "apply")
    print(json.dumps({
        "ok": True, "mode": "apply", "changed": True,
        "project_id": PROJECT_ID,
        "transaction_id": result.transaction_id,
        "receipt_path": result.receipt_path.relative_to(root).as_posix(),
        "report": report_path.relative_to(root).as_posix(),
    }, ensure_ascii=False))
    return 0


def rollback(root: Path) -> int:
    p = paths(root)
    if not p["project"].exists():
        print(json.dumps({"ok": True, "mode": "rollback", "changed": False}))
        return 0
    backups = {
        "module": p["backup"] / p["module"].name,
        "program": p["backup"] / p["program"].name,
        "workspace": p["backup"] / p["workspace"].name,
    }
    if not all(path.is_file() for path in backups.values()):
        print("projects rollback requires migration/backups/projects-v1", file=sys.stderr)
        return 2
    writes = {p[key]: backups[key].read_bytes() for key in backups}
    baseline = {str(issue) for issue in validate(load_repo(root), online=False) if issue.severity == "E"}
    with lock(root):
        try:
            result = TransactionService(root).commit(
                capability="project.migrate.rollback",
                writes=writes,
                deletes=[p["project"], p["aliases"], p["relations"]],
                artifact_ids=[PROJECT_ID, OLD_MODULE_ID, WORKSPACE_ID, PROGRAM_ID],
                validate_state=lambda: new_validation_errors(root, baseline),
                publish=lambda: publish(root),
                metadata={"migration": MIGRATION, "rollback": True},
            )
        except TransactionFailure as exc:
            print(f"projects rollback failed: {exc}", file=sys.stderr)
            return 1
    print(json.dumps({"ok": True, "mode": "rollback", "changed": True,
                      "transaction_id": result.transaction_id}, ensure_ascii=False))
    return 0


def dry_run(root: Path) -> int:
    if paths(root)["project"].is_file():
        summary = {
            "module": OLD_MODULE_ID, "project": PROJECT_ID,
            "workspace": WORKSPACE_ID, "program": PROGRAM_ID, "writes": [],
        }
        report_path = report(root, summary, "dry-run (already migrated)")
        print(json.dumps({"ok": True, "mode": "dry-run", "would_change": False,
                          "report": report_path.relative_to(root).as_posix()}))
        return 0
    _, summary = build_apply(root)
    report_path = report(root, summary, "dry-run")
    print(json.dumps({
        "ok": True, "mode": "dry-run", "would_change": True,
        "modules": [OLD_MODULE_ID], "projects": [PROJECT_ID],
        "canonical_files_written": 0,
        "report": report_path.relative_to(root).as_posix(),
    }, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.apply:
        return apply(root)
    if args.rollback:
        return rollback(root)
    return dry_run(root)


if __name__ == "__main__":
    raise SystemExit(main())
