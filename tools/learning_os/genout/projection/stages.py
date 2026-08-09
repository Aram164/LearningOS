"""Stage projection, shared by study maps and learning paths.

Both carry an ordered list of stages with resolvable resources and one working
note; they disagree only about what that note field is called. Writing the rule
twice is how the two drifted before — a resource resolution fixed on one side
and not the other is invisible until an interface renders the wrong list.
"""

from __future__ import annotations

from ...loader import Repo
from ..common import _git_last_commit
from ..materials import _project_material_resource


def project_stages(repo: Repo, data: dict, note_key: str) -> list[dict]:
    """Project ``data['stages']`` with resources resolved and notes inlined.

    ``note_key`` is the field naming the stage's working note: ``working_note``
    for a study map, ``notes_path`` for a learning path.
    """
    projected_stages: list[dict] = []
    for stage in data.get("stages", []) or []:
        projected = dict(stage)
        if isinstance(stage, dict) and isinstance(stage.get("resources"), list):
            projected["resources"] = [
                _project_material_resource(repo, resource)
                if isinstance(resource, dict) else resource
                for resource in stage["resources"]
            ]
        note_ref = stage.get(note_key) if isinstance(stage, dict) else None
        note_file = repo.root / str(note_ref) if note_ref else None
        if note_file and note_file.is_file():
            projected["notes_text"] = note_file.read_text(
                encoding="utf-8", errors="replace")
            projected["notes_updated"] = _git_last_commit(
                repo.root, note_file.relative_to(repo.root).as_posix())
        else:
            projected["notes_text"] = ""
            projected["notes_updated"] = None
        projected_stages.append(projected)
    return projected_stages
