"""projects/ — first-class projects, their relationships, and their aliases.

The registry inside the repository is canonical metadata; the external
``LearningOS/projects`` tree remains the optional working-file location
addressed by ``project://`` URIs.
"""

from __future__ import annotations

from pathlib import Path

from .model import Project, Repo, _register
from .yamlio import LoaderError, _load_yaml, _record_id


def load_projects(repo: Repo, root: Path) -> None:
    projects_dir = root / "projects" / "registry"
    if not projects_dir.is_dir():
        return
    for f in sorted(projects_dir.glob("project-*.yaml")):
        try:
            data = _load_yaml(f, root)
        except LoaderError as exc:
            repo.parse_failures.append((f, str(exc)))
            continue
        pid = _record_id(data)
        if pid is None:
            repo.parse_failures.append(
                (f, f"{f}: project with missing or empty id — skipped"))
            continue
        project = Project(pid, f, data)
        _register(repo, repo.projects, pid, project, f, "project")
        repo.project_origins.setdefault(pid, f)


def load_project_aliases(repo: Repo, root: Path) -> None:
    aliases_file = root / "projects" / "aliases.yaml"
    if not aliases_file.is_file():
        return
    try:
        aliases_data = _load_yaml(aliases_file, root)
    except LoaderError as exc:
        repo.parse_failures.append((aliases_file, str(exc)))
        return
    repo.project_aliases_path = aliases_file
    aliases = aliases_data.get("aliases", {})
    if not isinstance(aliases, dict):
        repo.parse_failures.append(
            (aliases_file, f"{aliases_file}: 'aliases' must be a mapping"))
        return
    for old_id, project_id in aliases.items():
        if isinstance(old_id, str) and isinstance(project_id, str):
            repo.project_aliases[old_id] = project_id
        else:
            repo.parse_failures.append(
                (aliases_file, f"{aliases_file}: project aliases must map strings to strings"))


def load_project_relations(repo: Repo, root: Path) -> None:
    relations_file = root / "projects" / "relations" / "project-relations.yaml"
    if not relations_file.is_file():
        return
    try:
        relations_data = _load_yaml(relations_file, root)
    except LoaderError as exc:
        repo.parse_failures.append((relations_file, str(exc)))
        return
    repo.project_relations_path = relations_file
    rows = relations_data.get("relations", [])
    if not isinstance(rows, list):
        repo.parse_failures.append(
            (relations_file, f"{relations_file}: 'relations' must be a list"))
        return
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            repo.project_relations.append(row)
        else:
            repo.parse_failures.append(
                (relations_file, f"{relations_file}: relations[{index}] is not a mapping"))
