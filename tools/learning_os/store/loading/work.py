"""work/ and archive/ — operational state: workspaces and coordination."""

from __future__ import annotations

from pathlib import Path

from learning_os.domain.snapshot import Coordination, Repo, Workspace
from learning_os.domain.snapshot import register as _register
from learning_os.store.loading.yamlio import LoaderError, parse_frontmatter
from learning_os.store.loading.yamlio import read_text as _read_text
from learning_os.store.loading.yamlio import record_id as _record_id


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
            _register(repo, repo.workspaces, wid, ws, f, "workspace")


def load_coordination(repo: Repo, root: Path) -> None:
    coord_file = root / "work" / "COORDINATION.md"
    if not coord_file.exists():
        return
    try:
        meta, body = parse_frontmatter(_read_text(coord_file, root), coord_file)
        repo.coordination = Coordination(path=coord_file, meta=meta, body=body)
    except LoaderError as exc:
        repo.parse_failures.append((coord_file, str(exc)))
