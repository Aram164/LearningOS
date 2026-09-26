"""Workspace record updates: the governed Next Action writer."""

from __future__ import annotations

import json
import sys

from learning_os.loader import load_repo
from learning_os.render import replace_h2_section as _replace_h2_section

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _render_frontmatter,
    _root,
    _write_transaction,
)


def cmd_workspace_next_action(args) -> int:
    """Replace one active workspace's Next Action section.

    The governed form of the WORKFLOWS §1 Next Action: the section body is
    replaced verbatim from the envelope-inline text with the same
    fence-aware section editor module.plan.import uses for workspace
    updates, while frontmatter and every other section keep their
    content. Archived or non-active workspaces refuse, as does a blank
    action or a CONTEXT.md without the required section.
    """
    root = _root(args)
    text = args.next_action
    if not isinstance(text, str) or not text.strip():
        print("los: --next-action must not be blank", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        workspace = repo.workspaces.get(args.workspace_id)
        if workspace is None:
            print(f"los: workspace not found: {args.workspace_id}", file=sys.stderr)
            return 2
        if workspace.archived or workspace.status != "active":
            print(f"los: workspace is not active: {args.workspace_id}", file=sys.stderr)
            return 2
        try:
            body = _replace_h2_section(workspace.body, "Next Action", text)
        except ValueError as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        code, errors, confirmation = _write_transaction(
            root, {workspace.path: _render_frontmatter(workspace.meta, body)},
            capability="workspace.next-action.update",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.workspace_id],
        )
        if code:
            print("los: next-action update rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "workspace_id": args.workspace_id,
                      "path": workspace.path.relative_to(root).as_posix(),
                      **confirmation}, ensure_ascii=False))
    return 0
