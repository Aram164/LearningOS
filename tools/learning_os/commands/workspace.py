"""Workspace record updates: the governed Next Action writer."""

from __future__ import annotations

import hashlib
import json
import re
import sys

from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo
from learning_os.pathing import PathBoundaryError, read_bytes_inside
from learning_os.render import parse_sections
from learning_os.render import replace_h2_section as _replace_h2_section
from learning_os.revisions import artifact_revision

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _render_frontmatter,
    _root,
    _write_transaction,
)

#: A digest-shaped value that was never a real file hash: all zeros.
_PLACEHOLDER_DIGEST = "sha256:" + "0" * 64

_DIGEST_RE = re.compile(r"sha256:[a-f0-9]{64}")


def cmd_coordination_section_revise(args) -> int:
    """Revise one reviewed coordination section, never a curriculum record."""
    root = _root(args)
    path = root / "work/COORDINATION.md"
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        if args.section not in {"Commitments", "Priorities", "Dependencies", "Deferrals"}:
            print("los: unknown coordination section", file=sys.stderr)
            return 2
        if path.is_symlink() or not path.is_file():
            print("los: coordination must be an existing regular file", file=sys.stderr)
            return 2
        try:
            original = read_bytes_inside(root, path)
        except (OSError, PathBoundaryError) as exc:
            print(f"los: cannot read coordination safely: {exc}", file=sys.stderr)
            return 2
        digest = "sha256:" + hashlib.sha256(original).hexdigest()
        supplied = args.expected_content_sha256
        if supplied is None and not args.check:
            print("los: coordination.section.revise apply requires "
                  "--expected-content-sha256: the current content digest is "
                  f"{digest} (read it with `inspect coordination`)",
                  file=sys.stderr)
            return 2
        if supplied is not None:
            if not _DIGEST_RE.fullmatch(supplied):
                print(f"los: malformed content digest {supplied!r}; the current "
                      f"content digest is {digest} "
                      "(read it with `inspect coordination`)", file=sys.stderr)
                return 2
            if supplied != digest:
                if supplied == _PLACEHOLDER_DIGEST:
                    print(f"los: placeholder content digest {supplied}; the current "
                          f"content digest is {digest} "
                          "(read it with `inspect coordination`)", file=sys.stderr)
                    return 2
                print("los: reviewed coordination content changed before use: "
                      f"supplied {supplied}, current is {digest}; re-read with "
                      "`inspect coordination`", file=sys.stderr)
                return 3
        if not args.text.strip():
            print("los: coordination section text must not be blank", file=sys.stderr)
            return 2
        _, injected = parse_sections(args.text)
        _, sections = parse_sections(original.decode("utf-8"))
        targets = [section for section in sections if section.heading == args.section]
        if injected or len(targets) != 1:
            print("los: replace exactly one existing section; new section headings refuse",
                  file=sys.stderr)
            return 2
        revised = _replace_h2_section(original.decode("utf-8"), args.section, args.text)
        if args.check:
            print(json.dumps({
                "ok": True, "section": args.section,
                "before": "\n".join(targets[0].lines).strip(),
                "after": args.text.strip(),
                "expected_content_sha256": digest,
                "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
                "expected_revisions": {"coordination": artifact_revision(root, "coordination")},
                "write_paths": ["work/COORDINATION.md"],
            }, ensure_ascii=False))
            return 0
        code, errors, confirmation = _write_transaction(
            root, {path: revised}, capability="coordination.section.revise",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=["coordination"],
        )
    if code:
        for issue in errors:
            print(issue, file=sys.stderr)
        return code
    print(json.dumps({"ok": True, "section": args.section, **confirmation}, ensure_ascii=False))
    return 0


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
