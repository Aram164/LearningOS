"""Record projection for projects/: projects, relationships, compatibility aliases."""

from __future__ import annotations

from collections.abc import Callable

from ...loader import Repo

Revision = Callable[..., int]


def unit_to_project_ids(repo: Repo) -> dict[str, list[str]]:
    """Projects own units explicitly; this is that edge, inverted for units."""
    table: dict[str, list[str]] = {}
    for project_id, project in sorted(repo.projects.items()):
        for unit_id in project.data.get("unit_ids", []) or []:
            table.setdefault(unit_id, []).append(project_id)
    for unit_id in table:
        table[unit_id] = sorted(set(table[unit_id]))
    return table


def project_projects(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for project_id in sorted(repo.projects):
        project = repo.projects[project_id]
        data = project.data
        records.append({
            **dict(data),
            "revision": revision(project_id, data),
            "path": str(project.path.relative_to(repo.root)),
            "relationship_ids": [
                relation.get("id") for relation in repo.project_relations
                if relation.get("from_project_id") == project_id
            ],
        })
    return records


def project_project_relationships(repo: Repo) -> list[dict]:
    return [
        {**dict(relation), "type": "project-relationship",
         "path": "projects/relations/project-relations.yaml"}
        for relation in sorted(repo.project_relations, key=lambda row: str(row.get("id")))
    ]


def project_project_aliases(repo: Repo) -> list[dict]:
    return [
        {
            "id": old_id, "type": "compatibility-alias",
            "target_id": target_id, "target_type": "project",
            "path": "projects/aliases.yaml",
        }
        for old_id, target_id in sorted(repo.project_aliases.items())
    ]
