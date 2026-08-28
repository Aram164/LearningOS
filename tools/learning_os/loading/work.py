"""work/ and archive/ — operational state: workspaces, learning paths, coordination.

Learning paths live inside and are owned by the workspace directory, so they
are loaded from within the workspace walk rather than from a registry of their
own. Nothing here is a second knowledge graph.
"""

from __future__ import annotations

from pathlib import Path

from .model import Coordination, LearningPath, Repo, Workspace, _register
from .yamlio import LoaderError, _load_yaml, _read_text, _record_id, parse_frontmatter


def _load_learning_paths(repo: Repo, context_file: Path, workspace_id: str,
                         archived: bool) -> None:
    """The workspace directory, not a duplicated field, determines ownership;
    the schema still carries workspace_id so projections and agents can verify
    that the declaration agrees with location."""
    paths_dir = context_file.parent / "paths"
    if not paths_dir.is_dir():
        return
    for pf in sorted(paths_dir.glob("path-*.yaml")):
        try:
            data = _load_yaml(pf, repo.root)
        except LoaderError as exc:
            repo.parse_failures.append((pf, str(exc)))
            continue
        pid = _record_id(data)
        if pid is None:
            repo.parse_failures.append(
                (pf, f"{pf}: learning path with missing or empty id — skipped"))
            continue
        learning_path = LearningPath(
            id=pid, path=pf, data=data, workspace_id=workspace_id, archived=archived)
        _register(repo, repo.learning_paths, pid, learning_path, pf, "learning-path")


def load_workspaces(repo: Repo, root: Path) -> None:
    """Workspaces: active + archived.

    Active workspaces sit exactly one level under work/active/ (a workspace is a
    single directory). Archived workspaces may be filed under an arbitrary
    bucketing (by year, by year/quarter, …), so their CONTEXT.md is discovered
    at any depth rather than assuming a fixed archive/workspaces/<year>/<ws>/
    layout.
    """
    for base, archived in ((root / "work" / "active", False),
                           (root / "archive" / "workspaces", True)):
        if not base.is_dir():
            continue
        found = base.rglob("CONTEXT.md") if archived else base.glob("*/CONTEXT.md")
        for f in sorted(found):
            try:
                meta, body = parse_frontmatter(_read_text(f, root), f)
            except LoaderError as exc:
                repo.parse_failures.append((f, str(exc)))
                continue
            if "id" in meta and _record_id(meta) is None:
                repo.parse_failures.append(
                    (f, f"{f}: workspace frontmatter id is empty or not a string — skipped"))
                continue
            wid = str(meta.get("id", f.parent.name))
            ws = Workspace(id=wid, path=f, meta=meta, body=body, archived=archived)
            if _register(repo, repo.workspaces, wid, ws, f, "workspace"):
                _load_learning_paths(repo, f, wid, archived)


def load_coordination(repo: Repo, root: Path) -> None:
    coord_file = root / "work" / "COORDINATION.md"
    if not coord_file.exists():
        return
    try:
        meta, body = parse_frontmatter(_read_text(coord_file, root), coord_file)
        repo.coordination = Coordination(path=coord_file, meta=meta, body=body)
    except LoaderError as exc:
        repo.parse_failures.append((coord_file, str(exc)))
