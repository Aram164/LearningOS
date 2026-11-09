"""Record projection for projects/ compatibility aliases."""

from __future__ import annotations

from learning_os.domain.snapshot import Repo


def project_project_aliases(repo: Repo) -> list[dict]:
    types = {**dict.fromkeys(repo.modules, "module"),
             **dict.fromkeys(repo.units, "unit"),
             **dict.fromkeys(repo.workspaces, "workspace")}
    return [
        {
            "id": old_id, "type": "compatibility-alias",
            "target_id": target_id, "target_type": types[target_id],
            "path": "projects/aliases.yaml",
        }
        for old_id, target_id in sorted(repo.project_aliases.items())
    ]
