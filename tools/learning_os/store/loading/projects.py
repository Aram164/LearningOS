"""projects/ — compatibility aliases for retired project ids.

The registry inside the repository is canonical metadata; the external
``LearningOS/projects`` tree remains the optional working-file location
addressed by ``project://`` URIs.
"""

from __future__ import annotations

from pathlib import Path

from learning_os.domain.snapshot import Repo
from learning_os.store.loading.yamlio import LoaderError
from learning_os.store.loading.yamlio import load_yaml as _load_yaml


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
