"""The study profile's hooks: the fence, the rewrite and turn ends (Plan C, ADR-021).

Synthetic hook inputs, no model. Path fences and the ordinary-write probes run
against a world that carries its own copy of ``tools/`` (a symlink would
resolve back to this checkout), so every rewritten command acts on the world.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import study_hooks
from repo_builders import _structural_fixture, add_curriculum, write_minimal_pdf

ROOT = Path(__file__).resolve().parents[1]
S = "cccccccc-3333-4333-8333-333333333333"
OTHER = "dddddddd-4444-4444-8444-444444444444"
BOOK = "_unsorted/review/book.pdf"


@pytest.fixture(autouse=True)
def _in_process_store(monkeypatch, tmp_path):
    """In-process hook calls record activity in a temporary store.

    The hook writes the store beside the Core that holds it (decision P11).
    Run from a live checkout, the in-process cases below would otherwise
    create ``LearningOS/reading-memory/`` or write fake sessions into the
    learner's own store.
    """
    real = study_hooks.ReadingStore
    store = tmp_path / "in-process-reading-memory"
    monkeypatch.setattr(study_hooks, "ReadingStore",
                        lambda core, root=None: real(core, root=root or store))
    return store


# ---- in-process: the Bash allowlist ------------------------------------------------


def _bash(command: str, cwd: Path = ROOT, session: str = S) -> dict:
    return study_hooks.pre_tool_use({"session_id": session, "tool_name": "Bash",
                                     "tool_input": {"command": command, "description": "x"},
                                     "cwd": str(cwd), "hook_event_name": "PreToolUse"})


def _decision(output: dict) -> tuple[str, str, str | None]:
    hook = output["hookSpecificOutput"]
    return (hook["permissionDecision"], hook["permissionDecisionReason"],
            (hook.get("updatedInput") or {}).get("command"))


@pytest.mark.parametrize("command", [
    "ls materials",
    "cd repository && los status",
    "los status; ls",
    "los status > /tmp/out.json",
    "los status 2>/tmp/err",
    "los status < /tmp/in",
    "los status | cat",
    'los material-search "$(cat /tmp/x)"',
    "los material-search `whoami`",
    "los material-search ${HOME}",
    "los status &",
    "los status || true",
    "los status\nls",
    "los material-search x | head",
    "los material-search x | head -n 5 /etc/hosts",
    "los material-search x | jq -c '.hits | .[0]'",
    "los material-search x | head -n 5 && cat ../materials/x.pdf",
    "los status && /bin/cat ../materials/x.pdf",
    "cat /tmp/rec.json",
    "python3 -c 'print(1)'",
    "LOS_OBSERVATIONS=/tmp/o.json los status",
    "los --root /tmp/elsewhere status",
    "los --r /tmp/elsewhere status",
    "los ai-action-prepare x unit unit-x",
    f"los material-span --material {BOOK} --pages 'pdf p. 1' --extract --session {OTHER}",
    f"los material-search Bayes --s {OTHER}",
    f"los material-search Bayes --session={OTHER}",
    "los material-search *.pdf",
    "los material-search ~/x",
    "los capture --file ../materials/a.pdf",
    ".venv/bin/python tools/seal_envelope.py --root /tmp/x --capability capture.create --payload '{}' --key k",
    ".venv/bin/python tools/seal_envelope.py --capability capture.create --payload '{\"file\": \"../materials/a.pdf\"}' --key k --submit",
    ".venv/bin/python tools/seal_envelope.py --capability capture.create --payload '{}' --key k --guards auto --check-out tools/rec.json",
])
def test_the_allowlist_refuses_everything_else(command):
    decision, reason, rewritten = _decision(_bash(command))
    assert decision == "deny", (command, rewritten)
    assert reason


def test_material_span_extract_becomes_the_study_read_with_the_hooks_session():
    decision, _, rewritten = _decision(
        _bash(f"los material-span --material {BOOK} --pages 'pdf pp. 2-3' --extract"))
    assert decision == "allow"
    assert rewritten.startswith(f"{study_hooks.CORE_PYTHON} {study_hooks.LOS_SCRIPT} material-study-span ")
    assert rewritten.endswith(f"--session {S}")
    # An abbreviation argparse would accept is still the extract form.
    _, _, abbreviated = _decision(
        _bash(f".venv/bin/python tools/los.py material-span --material {BOOK} --pages 'pdf p. 2' --ext"))
    assert " material-study-span " in abbreviated
    # Without --extract nothing is read, so nothing is rewritten or injected.
    _, _, describe = _decision(_bash("los material-span unit-demo-l01 route-x"))
    assert " material-span unit-demo-l01 route-x" in describe and "--session" not in describe


def test_search_context_and_settle_receive_the_session_and_other_commands_do_not(
        _in_process_store):
    beside = study_hooks.CORE.parent / "reading-memory"
    existed = beside.exists()
    for command in ("los material-search 'naive Bayes' --limit 3",
                    "los material-context Bayes",
                    "los material-card-settle --adopt " + OTHER):
        decision, _, rewritten = _decision(_bash(command))
        assert decision == "allow" and rewritten.endswith(f"--session {S}"), command
    _, _, status = _decision(_bash("los bootstrap --brief"))
    assert status.endswith("los.py bootstrap --brief")
    # P11: an allowed gateway call records the session's activity, here in the
    # test's own store and never beside this checkout.
    assert (_in_process_store / "sessions" / f"{S}.json").is_file()
    assert beside.exists() == existed
    assert not (beside / "sessions" / f"{S}.json").exists()


def test_pipes_to_head_and_the_reviewed_record_pairing_are_allowed(tmp_path):
    decision, _, rewritten = _decision(_bash("los material-search Bayes | head -n 20"))
    assert decision == "allow" and rewritten.endswith("| /usr/bin/head -n 20")
    record = tmp_path / "rec.json"
    command = (".venv/bin/python tools/seal_envelope.py --capability capture.create "
               f"--payload '{{\"text\": \"note\"}}' --key k1 --guards auto --check-out {record} "
               f"&& cat {record}")
    decision, reason, rewritten = _decision(_bash(command))
    assert decision == "allow", reason
    assert rewritten.endswith(f"&& /bin/cat {os.path.realpath(record)}")
    assert _decision(_bash("los status 2>&1 | head -n 5"))[0] == "allow"


def test_a_missing_session_or_a_crash_refuses_every_call(monkeypatch):
    assert _decision(_bash("los status", session=""))[0] == "deny"

    def broken(*args):
        raise RuntimeError("boom")

    monkeypatch.setattr(study_hooks, "rewrite_bash", broken)
    decision, reason, _ = _decision(_bash("los status"))
    assert decision == "deny" and "hook failed" in reason


def test_unknown_and_mcp_tools_refuse_and_harmless_tools_pass():
    def tool(name, tool_input=None):
        return _decision(study_hooks.pre_tool_use(
            {"session_id": S, "tool_name": name, "tool_input": tool_input or {}, "cwd": str(ROOT)}))[0]

    assert tool("mcp__filesystem__read_file", {"path": "/x"}) == "deny"
    assert tool("SomeFutureTool") == "deny"
    assert tool("TodoWrite", {"todos": []}) == "allow"


# ---- a world with its own code: fences, writes, turn ends --------------------------


@pytest.fixture(scope="module")
def code_copy(tmp_path_factory) -> Path:
    copy = tmp_path_factory.mktemp("study-code") / "tools"
    shutil.copytree(ROOT / "tools", copy,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return copy


@pytest.fixture
def world(mini_repo: Path, code_copy: Path) -> Path:
    add_curriculum(mini_repo)
    shutil.copytree(code_copy, mini_repo / "tools", dirs_exist_ok=True)
    (mini_repo / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)
    write_minimal_pdf(mini_repo.parent / "materials" / BOOK,
                      [f"page {n} on evidence" for n in range(1, 6)])
    for tree in ("generated/text-cache/abc", "generated/material-search",
                 "operations/ai-actions/requests/r/attachments/slices"):
        (mini_repo / tree).mkdir(parents=True, exist_ok=True)
    (mini_repo / "generated/text-cache/abc/p1.txt").write_text("raw page text")
    alias = mini_repo.parent / "workbench" / "old"
    alias.mkdir(parents=True)
    (alias / "materials").symlink_to(mini_repo.parent / "materials", target_is_directory=True)
    return mini_repo


def _hook(world: Path, event_name: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(world / "tools/study_hooks.py"), event_name],
                          input=json.dumps(payload), capture_output=True, text=True, timeout=120,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))


def _pre(world: Path, tool: str, tool_input: dict, cwd: Path | None = None) -> tuple[str, str, dict]:
    result = _hook(world, "pre-tool-use", {"session_id": S, "tool_name": tool,
                                           "tool_input": tool_input, "cwd": str(cwd or world.parent)})
    assert result.returncode == 0, result.stderr
    hook = json.loads(result.stdout)["hookSpecificOutput"]
    return hook["permissionDecision"], hook["permissionDecisionReason"], hook.get("updatedInput") or {}


def test_file_tools_stay_out_of_raw_text_and_the_store(world):
    learningos = world.parent
    closed = [learningos / "materials" / BOOK,
              learningos / "workbench" / "old" / "materials" / BOOK,  # path alias
              world / "generated/text-cache/abc/p1.txt",
              world / "generated/material-search/index.sqlite3",
              world / "operations/ai-actions/requests/r/attachments/slices/route.md",
              learningos / "reading-memory" / "pending" / "rd-0000000000000000.json"]
    for path in closed:
        assert _pre(world, "Read", {"file_path": str(path)})[0] == "deny", path
    assert _pre(world, "Read", {"file_path": str(world / "system/contracts/capabilities.yaml")})[0] == "allow"
    assert _pre(world, "Grep", {"pattern": "Bayes"})[0] == "deny"  # cwd is LearningOS/
    assert _pre(world, "Grep", {"pattern": "Bayes", "path": str(learningos / "workbench")})[0] == "deny"
    assert _pre(world, "Grep", {"pattern": "x", "path": str(world / "knowledge")})[0] == "allow"
    assert _pre(world, "Glob", {"pattern": "../materials/**/*.pdf", "path": str(world)})[0] == "deny"
    assert _pre(world, "Glob", {"pattern": "**/*.pdf"})[0] == "deny"
    scratch = Path(os.path.realpath(study_hooks.scratch_roots()[0])) / "study-scratch.json"
    assert _pre(world, "Write", {"file_path": str(scratch), "content": "{}"})[0] == "allow"
    for path in (world / "tools/learning_os/store/materials/reading_cards.py",
                 learningos / ".claude" / "settings.json",
                 learningos / "reading-memory" / "pending" / "rd-0000000000000000.json"):
        assert _pre(world, "Edit", {"file_path": str(path), "old_string": "a", "new_string": "b"})[0] == "deny"


def test_rewritten_reads_run_from_any_folder_and_capture_the_hooks_session(world):
    for cwd, form in ((world.parent, "repository/.venv/bin/python repository/tools/los.py"),
                      (world, ".venv/bin/python tools/los.py"), (world.parent, "los")):
        decision, _, updated = _pre(world, "Bash", {"command": (
            f"{form} material-span --material {BOOK} --pages 'pdf p. 2' --extract")}, cwd=cwd)
        assert decision == "allow"
        ran = subprocess.run(updated["command"], shell=True, cwd=cwd, capture_output=True, text=True,
                             timeout=120)
        assert ran.returncode == 0, ran.stderr
        study = json.loads(ran.stdout)
        assert study["contract"] == "material-study-span-v1" and study["study"]["session"] == S
    pending = list((world.parent / "reading-memory" / "pending").glob("rd-*.json"))
    assert len(pending) == 1 and json.loads(pending[0].read_text())["session"] == S


def test_stop_asks_twice_then_marks_overdue_and_session_start_reports_it(world):
    _, _, updated = _pre(world, "Bash", {"command": (
        f"los material-span --material {BOOK} --pages 'pdf p. 3' --extract")})
    assert subprocess.run(updated["command"], shell=True, capture_output=True).returncode == 0
    replies = []
    for active in (False, True, True):
        result = _hook(world, "stop", {"session_id": S, "stop_hook_active": active})
        assert result.returncode == 0, result.stderr
        replies.append(json.loads(result.stdout) if result.stdout.strip() else {})
    assert [reply.get("decision") for reply in replies] == ["block", "block", None]
    assert "material-card-settle rd-" in replies[0]["reason"]
    assert "now overdue" in replies[2]["systemMessage"]
    start = _hook(world, "session-start", {"session_id": S, "source": "resume"})
    assert "1 overdue entries" in start.stdout
    # Stop only asks and marks overdue; a turn end never records an end, so the
    # session can still resume and its entries are not adoptable yet
    # (ADR-021 decision 5).
    other = _hook(world, "session-start", {"session_id": OTHER, "source": "startup"})
    assert "No adoptable entries." in other.stdout
    assert "--adopt" not in other.stdout
    ended = _hook(world, "session-end", {"session_id": S})
    assert ended.returncode == 0, ended.stderr
    other = _hook(world, "session-start", {"session_id": OTHER, "source": "startup"})
    assert f"los material-card-settle --adopt {S}" in other.stdout


def test_session_end_records_the_end_and_an_unknown_session_is_harmless(world):
    _, _, updated = _pre(world, "Bash", {"command": (
        f"los material-span --material {BOOK} --pages 'pdf p. 4' --extract")})
    assert subprocess.run(updated["command"], shell=True, capture_output=True).returncode == 0
    assert _hook(world, "session-end", {"session_id": OTHER}).returncode == 0
    result = _hook(world, "session-end", {"session_id": S})
    assert result.returncode == 0, result.stderr
    assert "session end recorded" in result.stdout
    other = _hook(world, "session-start", {"session_id": OTHER, "source": "startup"})
    assert f"los material-card-settle --adopt {S}" in other.stdout


def test_a_stage_note_and_a_resource_append_complete_under_the_profile(world, tmp_path):
    def run(command: str) -> dict:
        decision, reason, updated = _pre(world, "Bash", {"command": command}, cwd=world)
        assert decision == "allow", reason
        ran = subprocess.run(updated["command"], shell=True, cwd=world, capture_output=True,
                             text=True, timeout=300)
        assert ran.returncode == 0, ran.stdout + ran.stderr
        return json.loads(ran.stdout)

    note = json.dumps({"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                       "text": "studied the evidence pages under the profile"})
    written = run(f".venv/bin/python tools/seal_envelope.py --capability stage.note.write "
                  f"--payload '{note}' --key profile-note-1 --guards auto --submit")
    assert written["ok"] is True
    _structural_fixture(world)
    draft = tmp_path / "append.json"
    draft.write_text(json.dumps({"unit_id": "unit-demo-l01", "structural_edit": {
        "reason": "Append the named route without creating a study obligation.",
        "resource_append": {"stage_id": "stage-demo", "resource": {
            "id": "resource-profile-append",
            "material_ref": {"route_id": "route-demo-book",
                             "inherit": ["label", "source_id", "locator", "angle", "angle_detail"]}}}}}))
    digest = "sha256:" + hashlib.sha256(draft.read_bytes()).hexdigest()
    payload = json.dumps({"unit_id": "unit-demo-l01", "file": str(draft), "file_sha256": digest,
                          "replace": True})
    appended = run(f".venv/bin/python tools/seal_envelope.py --capability unit.map.import "
                   f"--payload '{payload}' --key profile-append-1 --guards auto --submit")
    assert appended["ok"] is True
    receipts = list((world / "operations/transactions").glob("transaction-*.yaml"))
    assert len(receipts) >= 2


def test_the_profile_writer_wires_the_hooks_and_never_overwrites(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "tools/study_hooks.py"), "profile",
                             "--out", str(tmp_path)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert set(settings["hooks"]) == {"SessionStart", "PreToolUse", "Stop", "SessionEnd"}
    assert settings["hooks"]["PreToolUse"][0]["matcher"] == "*"
    assert settings["hooks"]["PreToolUse"][0]["hooks"][0]["onFailure"] == "block"
    assert any(rule.startswith("Read(//") and "/materials/**" in rule
               for rule in settings["permissions"]["deny"])
    again = subprocess.run([sys.executable, str(ROOT / "tools/study_hooks.py"), "profile",
                            "--out", str(tmp_path)], capture_output=True, text=True, timeout=60)
    assert again.returncode != 0
