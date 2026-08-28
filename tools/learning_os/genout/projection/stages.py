"""Stage projection, shared by study maps and learning paths.

Both carry an ordered list of stages with resolvable resources and one working
note; they disagree only about what that note field is called. Writing the rule
twice is how the two drifted before — a resource resolution fixed on one side
and not the other is invisible until an interface renders the wrong list.
"""

from __future__ import annotations

from collections.abc import Iterable

from ...loader import Repo
from ...pathing import PathBoundaryError, read_text_inside, resolved_inside
from ..common import _git_last_commit
from ..materials import _project_material_resource

_OPEN_TARGET_KEYS = (
    "material_uri",
    "material_path",
    "material_exists",
    "url",
    "vault_path",
)


def _has_direct_open_target(resource: dict) -> bool:
    """Whether a projected row names one usable file or website.

    A missing material path is not a target, even when its descriptive locator
    happened to end in ``.pdf``.  Treating that path as openable is how range
    locators such as "lecture 01 through lecture 11.pdf" reached the system
    file browser instead of a lecture.
    """
    if resource.get("url"):
        return True
    vault_path = resource.get("vault_path")
    if isinstance(vault_path, str) and vault_path \
            and not vault_path.startswith("material://"):
        return True
    return bool(
        resource.get("material_path")
        and resource.get("material_exists") is True
    )


def _route_target(resource: dict, routes: Iterable[dict]) -> dict | None:
    """Find the one lecture route that owns this stage-resource label.

    Study maps intentionally keep pedagogical prose in ``locator``; generated
    maps append the route angle there, so it is not a stable file identity.
    The source id plus the route title is stable and preserves meaning.  A
    unique match can therefore supply the already-resolved route target.  An
    ambiguous or non-openable match fails closed rather than opening the
    source's collection directory.
    """
    route_id = resource.get("route_id")
    if route_id:
        matches = [
            route for route in routes
            if route.get("id") == route_id and _has_direct_open_target(route)
        ]
        return matches[0] if len(matches) == 1 else None

    source_id = resource.get("source_id")
    label = resource.get("label")
    if not source_id or not label:
        return None
    matches = [
        route for route in routes
        if route.get("source_id") == source_id
        and route.get("title") == label
        and _has_direct_open_target(route)
    ]
    return matches[0] if len(matches) == 1 else None


def _project_stage_resource(repo: Repo, resource: dict,
                            routes: Iterable[dict]) -> dict:
    projected = _project_material_resource(repo, resource)
    if _has_direct_open_target(projected):
        return projected
    route = _route_target(projected, routes)
    if route is None:
        return projected
    return {
        **projected,
        "route_id": route.get("id"),
        **{
            key: route[key]
            for key in _OPEN_TARGET_KEYS
            if route.get(key) is not None
        },
    }


def project_stages(repo: Repo, data: dict, note_key: str,
                   resource_routes: Iterable[dict] = ()) -> list[dict]:
    """Project ``data['stages']`` with resources resolved and notes inlined.

    ``note_key`` is the field naming the stage's working note: ``working_note``
    for a study map, ``notes_path`` for a learning path.
    """
    projected_stages: list[dict] = []
    for stage in data.get("stages", []) or []:
        projected = dict(stage)
        if isinstance(stage, dict) and isinstance(stage.get("resources"), list):
            projected["resources"] = [
                _project_stage_resource(repo, resource, resource_routes)
                if isinstance(resource, dict) else resource
                for resource in stage["resources"]
            ]
        elif isinstance(stage, dict) and "resources" not in stage:
            # The manifest contract publishes a stable collection even when a
            # learning-path stage has no resource rows.  Preserve malformed
            # authored values so schema validation still fails closed.
            projected["resources"] = []
        note_ref = stage.get(note_key) if isinstance(stage, dict) else None
        note_file = repo.root / str(note_ref) if note_ref else None
        try:
            if note_file:
                resolved_inside(repo.root, note_file)
                projected["notes_text"] = read_text_inside(
                    repo.root, note_file, errors="replace")
            else:
                raise FileNotFoundError
            projected["notes_updated"] = _git_last_commit(
                repo.root, note_file.relative_to(repo.root).as_posix())
        except (OSError, PathBoundaryError, ValueError):
            projected["notes_text"] = ""
            projected["notes_updated"] = None
        projected_stages.append(projected)
    return projected_stages
