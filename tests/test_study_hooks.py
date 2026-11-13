"""Optional UX hooks for the study profile: session nudges, turn ends, and settings (Plan C/D, ADR-021).

Client-side Bash/path enforcement moved to Seatbelt (`tools/study_launch.py`)
and `learning_os.adapters.study_broker` in Plan D; `tools/study_hooks.py` now
retains only UX hints (`session-start`), turn-end debt reminders (`stop` /
`SubagentStop`), standalone `session-end`, opt-in Claude `--settings` emission,
and `LOS_GATE_SOCK` broker forwarding during Seatbelt study runs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import seal_envelope
import study_hooks
from repo_builders import add_curriculum, write_minimal_pdf

from learning_os.adapters.study_broker import GATE_SOCK_ENV, BrokerServer, StudyBroker
from learning_os.store.materials.reading_cards import ReadingStore

ROOT = Path(__file__).resolve().parents[1]
S = "cccccccc-3333-4333-8333-333333333333"
OTHER = "dddddddd-4444-4444-8444-444444444444"
BOOK = "_unsorted/review/book.pdf"


@pytest.fixture(autouse=True)
def _in_process_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """In-process hook calls record activity in a temporary store, never live checkout."""
    real = study_hooks.ReadingStore
    store = tmp_path / "in-process-reading-memory"
    monkeypatch.setattr(
        study_hooks,
        "ReadingStore",
        lambda core, root=None: real(core, root=root or store),
    )
    return store


@pytest.fixture(scope="module")
def code_copy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    copy = tmp_path_factory.mktemp("study-hooks-code") / "tools"
    shutil.copytree(ROOT / "tools", copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return copy


@pytest.fixture
def world(mini_repo: Path, code_copy: Path) -> Path:
    add_curriculum(mini_repo)
    shutil.copytree(code_copy, mini_repo / "tools", dirs_exist_ok=True)
    (mini_repo / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)
    write_minimal_pdf(
        mini_repo.parent / "materials" / BOOK,
        [f"page {n} on evidence" for n in range(1, 6)],
    )
    return mini_repo


def _hook(
    world: Path,
    event_name: str,
    payload: dict[str, object],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    run_env.pop(GATE_SOCK_ENV, None)
    if env is not None:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(world / "tools/study_hooks.py"), event_name],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
        env=run_env,
    )


def _open_study_span(world: Path, page: int, *, session: str = S) -> dict[str, object]:
    proc = subprocess.run(
        [
            str(world / ".venv/bin/python"),
            str(world / "tools/los.py"),
            "--root",
            str(world),
            "material-study-span",
            "--material",
            BOOK,
            "--pages",
            f"pdf p. {page}",
            "--extract",
            "--session",
            session,
        ],
        cwd=str(world),
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_client_side_ast_and_file_fences_were_removed() -> None:
    for removed in ("pre_tool_use", "rewrite_bash", "check_file_tool", "_subtree_reaches"):
        assert not hasattr(study_hooks, removed), removed
    subparsers = [
        action.choices
        for action in study_hooks.build_parser()._actions
        if hasattr(action, "choices") and isinstance(action.choices, dict)
    ]
    assert subparsers and "pre-tool-use" not in subparsers[0]


def test_session_start_touches_store_and_reports_clean_state(_in_process_store: Path) -> None:
    beside = study_hooks.CORE.parent / "reading-memory"
    existed = beside.exists()
    out = study_hooks.session_start({"session_id": S, "source": "startup"})
    assert "los bootstrap --brief" in out
    assert "No adoptable entries." in out
    assert "no overdue entries" in out
    assert (_in_process_store / "sessions" / f"{S}.json").is_file()
    assert beside.exists() == existed
    assert not (beside / "sessions" / f"{S}.json").exists()

    no_sid = study_hooks.session_start({"source": "startup"})
    assert "No session id arrived" in no_sid


def test_stop_asks_twice_then_marks_overdue_and_session_start_reports_it(world: Path) -> None:
    study = _open_study_span(world, 3)
    assert study["contract"] == "material-study-span-v1"
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

    # Stop only asks and marks overdue; a turn end never records a session end.
    other = _hook(world, "session-start", {"session_id": OTHER, "source": "startup"})
    assert "No adoptable entries." in other.stdout
    assert "--adopt" not in other.stdout

    ended = _hook(world, "session-end", {"session_id": S})
    assert ended.returncode == 0, ended.stderr
    other = _hook(world, "session-start", {"session_id": OTHER, "source": "startup"})
    assert f"los material-card-settle --adopt {S}" in other.stdout


def test_session_end_records_end_and_unknown_session_is_harmless(world: Path) -> None:
    _open_study_span(world, 4)
    assert _hook(world, "session-end", {"session_id": OTHER}).returncode == 0
    result = _hook(world, "session-end", {"session_id": S})
    assert result.returncode == 0, result.stderr
    assert "session end recorded" in result.stdout
    other = _hook(world, "session-start", {"session_id": OTHER, "source": "startup"})
    assert f"los material-card-settle --adopt {S}" in other.stdout


def test_profile_writer_wires_ux_hooks_only_and_never_overwrites(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/study_hooks.py"), "profile", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert set(settings["hooks"]) == {"SessionStart", "Stop", "SubagentStop", "SessionEnd"}
    assert "permissions" not in settings
    for entries in settings["hooks"].values():
        for entry in entries:
            for hook in entry["hooks"]:
                assert "onFailure" not in hook
    sub_stop = settings["hooks"]["SubagentStop"][0]["hooks"][0]
    assert sub_stop["command"].endswith(" stop")

    again = subprocess.run(
        [sys.executable, str(ROOT / "tools/study_hooks.py"), "profile", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert again.returncode != 0


def test_hooks_forward_over_broker_socket_and_session_end_noops_in_sandbox(world: Path) -> None:
    _open_study_span(world, 2)
    sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losh-", dir="/tmp")))
    sock_path = sock_dir / "g.sock"
    broker = StudyBroker(world, S)
    server = BrokerServer(broker, sock_path)
    server.start()
    try:
        sock_env = {GATE_SOCK_ENV: str(sock_path)}
        # Client payload omits or mismatches session_id; host broker pins broker.session_id.
        started = _hook(world, "session-start", {"session_id": OTHER}, env=sock_env)
        assert started.returncode == 0, started.stderr
        assert "los bootstrap --brief" in started.stdout

        stopped = _hook(world, "stop", {"session_id": OTHER, "stop_hook_active": False}, env=sock_env)
        assert stopped.returncode == 0, stopped.stderr
        decision = json.loads(stopped.stdout)
        assert decision["decision"] == "block"
        assert "material-card-settle rd-" in decision["reason"]

        # Inside Seatbelt, study_launch owns session_end on exit; hook SessionEnd no-ops safely.
        ended = _hook(world, "session-end", {"session_id": S}, env=sock_env)
        assert ended.returncode == 0
        assert ended.stdout == ""
        store = ReadingStore(world)
        session_row = json.loads((store.root / "sessions" / f"{S}.json").read_text(encoding="utf-8"))
        assert session_row.get("ended_at") is None
    finally:
        server.close()
        shutil.rmtree(sock_dir, ignore_errors=True)

    # Dead broker socket degrades UX nudges without crashing Claude turns.
    dead_start = _hook(world, "session-start", {"session_id": S}, env={GATE_SOCK_ENV: str(sock_path)})
    assert dead_start.returncode == 0
    assert "los bootstrap --brief" in dead_start.stdout
    dead_stop = _hook(world, "stop", {"session_id": S}, env={GATE_SOCK_ENV: str(sock_path)})
    assert dead_stop.returncode == 0
    assert dead_stop.stdout == ""


def test_seal_scratch_path_problem_expands_tilde(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("HOME", str(repo))
    problem = seal_envelope._scratch_path_problem(repo, "~/work/probe.json", "--out")
    assert problem is not None and ".venv" in problem
