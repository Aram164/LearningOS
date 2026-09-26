"""Governed Next Action updates for active workspaces.

`workspace.next-action.update` is the governed form of the WORKFLOWS §1
Next Action: one active workspace, section-only replacement through the
fence-aware section editor, frontmatter and other sections preserved.
"""

from __future__ import annotations

import json
import subprocess
import sys

from gateway_helpers import LOS, approved_v2_cli
from repo_builders import add_curriculum, run_los

from learning_os.loader import load_repo

CONTEXT = "work/active/workspace-demo/CONTEXT.md"
ACTION = "Finish the variance derivation closed-book, then shelve."


def _update(mini_repo, action: str, key: str, workspace_id: str = "workspace-demo"):
    return approved_v2_cli(
        mini_repo, "workspace-next-action", workspace_id,
        "--next-action", action,
        artifact_ids=[workspace_id], idempotency_key=key,
    )


def test_update_replaces_only_the_next_action(mini_repo):
    result = _update(mini_repo, ACTION, "next-action-new")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"]["workspace_id"] == "workspace-demo"
    repo = load_repo(mini_repo)
    assert repo.workspaces["workspace-demo"].section("Next Action") == ACTION
    assert repo.workspaces["workspace-demo"].section("Objective") == "Demo."
    assert repo.workspaces["workspace-demo"].section("Current Scope") == "Small."
    assert repo.workspaces["workspace-demo"].section("Open Questions") == "None."
    assert repo.workspaces["workspace-demo"].meta["title"] == "Demo workspace"
    after = (mini_repo / CONTEXT).read_text(encoding="utf-8")
    assert "Do the demo thing." not in after
    assert ACTION in after
    assert "id: workspace-demo" in after and "status: active" in after


def test_latex_and_fences_are_placed_verbatim(mini_repo):
    action = "Let \\gamma denote the rate.\n\n```md\n## Not a heading\n```\n\nThen continue."
    result = _update(mini_repo, action, "next-action-verbatim")
    assert result.returncode == 0, result.stdout + result.stderr
    stored = load_repo(mini_repo).workspaces["workspace-demo"].section("Next Action")
    assert stored is not None and "\\gamma" in stored
    # The section reader is fence-blind (md_section truncates at a fenced
    # ## line — pre-existing read behavior); the fence-aware writer must
    # still have placed the block intact in the file.
    raw = (mini_repo / CONTEXT).read_text(encoding="utf-8")
    assert "```md\n## Not a heading\n```" in raw
    assert load_repo(mini_repo).workspaces["workspace-demo"].section("Objective") == "Demo."


def test_bare_command_never_writes(mini_repo):
    before = (mini_repo / CONTEXT).read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "workspace-next-action", "workspace-demo", "--next-action", ACTION],
        capture_output=True, text=True, cwd=mini_repo.parent,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "GatewayEnvelopeV2" in result.stderr
    assert (mini_repo / CONTEXT).read_text(encoding="utf-8") == before


def test_unknown_workspace_refuses(mini_repo):
    result = _update(mini_repo, ACTION, "next-action-unknown",
                      workspace_id="workspace-missing")
    assert result.returncode != 0


def test_archived_and_completed_workspaces_refuse(mini_repo):
    source = mini_repo / CONTEXT
    target = mini_repo / "archive/workspaces/2026/workspace-demo/CONTEXT.md"
    target.parent.mkdir(parents=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    source.unlink()
    assert load_repo(mini_repo).workspaces["workspace-demo"].archived
    archived = _update(mini_repo, ACTION, "next-action-archived")
    assert archived.returncode != 0
    assert "not active" in archived.stdout + archived.stderr

    target.write_text(
        target.read_text(encoding="utf-8").replace("status: active", "status: complete"),
        encoding="utf-8",
    )
    back = mini_repo / CONTEXT
    back.parent.mkdir(parents=True, exist_ok=True)
    back.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.unlink()
    assert load_repo(mini_repo).workspaces["workspace-demo"].status == "complete"
    completed = _update(mini_repo, ACTION, "next-action-completed")
    assert completed.returncode != 0
    assert "not active" in completed.stdout + completed.stderr


def test_missing_section_and_blank_action_refuse(mini_repo):
    path = mini_repo / CONTEXT
    path.write_text(
        path.read_text(encoding="utf-8").replace("## Next Action", "## Next Up"),
        encoding="utf-8",
    )
    missing = _update(mini_repo, ACTION, "next-action-missing")
    assert missing.returncode != 0
    assert "Next Action" in missing.stdout + missing.stderr

    path.write_text(
        path.read_text(encoding="utf-8").replace("## Next Up", "## Next Action"),
        encoding="utf-8",
    )
    blank = _update(mini_repo, "   ", "next-action-blank")
    assert blank.returncode != 0


def test_resume_shows_the_updated_action(mini_repo):
    add_curriculum(mini_repo)
    result = _update(mini_repo, ACTION, "next-action-resume")
    assert result.returncode == 0, result.stdout + result.stderr
    resumed = run_los(mini_repo, "resume")
    assert resumed.returncode == 0, resumed.stderr
    assert "Finish the variance derivation" in resumed.stdout
