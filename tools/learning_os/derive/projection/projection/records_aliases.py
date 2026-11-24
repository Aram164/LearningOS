"""Record projection for projects/ compatibility aliases."""

from __future__ import annotations

from learning_os.domain.snapshot import Repo


def project_project_aliases(repo: Repo) -> list[dict[str, str]]:
    types = {**dict.fromkeys(repo.modules, "module"),
             **dict.fromkeys(repo.units, "unit"),
             **dict.fromkeys(repo.workspaces, "workspace")}
    records: list[dict[str, str]] = []
    for old_id, target_id in sorted(repo.project_aliases.items()):
        target_type = types.get(target_id)
        if target_type is None:
            continue
        records.append({
            "id": old_id,
            "type": "compatibility-alias",
            "target_id": target_id,
            "target_type": target_type,
            "path": "projects/aliases.yaml",
        })
    return records
