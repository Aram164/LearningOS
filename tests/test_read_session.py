"""ReadSession epochs and memo eligibility use real read operations."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from learning_os.app.read_session import ReadSession  # noqa: E402


def _root(tmp_path):
    gen = tmp_path / "generated"
    gen.mkdir(exist_ok=True)
    (gen / "manifest.json").write_text('{"_generated":{"snapshot_id":"s1"}}')
    (gen / "manifest.identity.json").write_text('{"snapshot_id":"s1"}')
    return tmp_path


def test_memo_hits_once_per_epoch_and_pin_change_misses(mini_repo):
    tmp_path = mini_repo
    s = ReadSession(_root(tmp_path))
    s.put(("inspect", "x"), {"ok": True})
    assert s.get(("inspect", "x")) == {"ok": True}
    assert s.hits == 1
    (_root(tmp_path) / "generated/manifest.json").write_text('{"_generated":{"snapshot_id":"s2"}}')
    assert s.get(("inspect", "x")) is None  # pin changed: no stale hit


def test_close_ends_epoch(mini_repo):
    tmp_path = mini_repo
    s = ReadSession(_root(tmp_path))
    s.put(("a",), 1)
    s.close()
    assert s.get(("a",)) is None


def test_ranked_scan_loads_one_model_and_reuses_active_epoch(mini_repo):
    from learning_os.app.ranking import ranked_scan
    from learning_os.store.loading import count_repo_loads

    with count_repo_loads() as standalone:
        expected = ranked_scan(mini_repo)
    assert standalone == [1]
    session = ReadSession(mini_repo)
    with count_repo_loads() as bounded:
        with session.activate():
            assert ranked_scan(mini_repo) == expected
            assert ranked_scan(mini_repo) == expected
    assert bounded == [1]
    assert session.loads == 1


def test_activation_observes_dependencies_only_at_its_boundaries(mini_repo, monkeypatch):
    from learning_os.app import read_session

    calls = []
    actual = read_session._dependency_state
    monkeypatch.setattr(read_session, "_dependency_state", lambda root: (calls.append(root), actual(root))[1])
    session = ReadSession(mini_repo)
    assert calls == []
    with session.activate():
        session.put(("read",), 1)
        assert session.get(("read",)) == 1
        assert len(calls) == 1
    assert session.unchanged() and session.unchanged()
    session.close()
    assert len(calls) == 2


def test_epoch_detects_changed_inputs_and_resets_on_next_activation(mini_repo):
    session = ReadSession(mini_repo)
    with session.activate():
        note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
        note.write_text(note.read_text() + "\nA noncooperating edit.\n")
    assert not session.unchanged()
    with session.activate():
        pass
    assert session.unchanged()


def test_prepare_publication_is_outside_the_memo_lifetime(mini_repo):
    from learning_os.app.read_session import current_session

    session = ReadSession(mini_repo)
    calls = []

    def prepare():
        assert current_session(mini_repo) is None
        calls.append(1)
        _root(mini_repo)
        return {}, object()

    with session.activate(prepare):
        assert current_session(mini_repo) is session
    assert calls == [1] and session.unchanged()


def test_git_head_invalidates_standalone_and_active_memos(mini_repo):
    import subprocess

    def git(*args):
        return subprocess.run(["git", "-C", str(mini_repo), *args], check=True,
                              capture_output=True, text=True)

    git("init")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "first")
    session = ReadSession(mini_repo)
    session.put(("history",), "first")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "second")
    assert session.get(("history",)) is None
    with session.activate():
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "third")
    assert not session.unchanged()


def test_prepare_cannot_hide_a_model_from_an_earlier_snapshot(mini_repo):
    from learning_os.store.fingerprint import canonical_fingerprint

    before = "sha256:" + canonical_fingerprint(mini_repo)

    def prepare():
        note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
        note.write_text(note.read_text() + "\nChanged while preparing the model.\n")
        return {"_generated": {"snapshot_id": before}}, object()

    session = ReadSession(mini_repo)
    with session.activate(prepare):
        pass
    assert not session.unchanged()


def test_all_cache_eligible_read_operations_preserve_the_loaded_model(mini_repo):
    import hashlib
    import pickle

    from learning_os.adapters.cli import invoke_outcome
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.app.registry import REGISTRY

    commands = {
        "operator.bootstrap": ["bootstrap", "--brief"],
        "project.inspect": ["inspect", "note-demo"],
        "capabilities.read": ["capabilities", "--compact", "--json"],
        "intelligence.scan": ["intelligence-scan", "--brief", "--json"],
    }
    # Pin the complete eligible set: a new registration needs an exercised read.
    eligible = {name for name, op in REGISTRY.items() if op.memo_profile != "none"}
    assert eligible == commands.keys()
    parser = build_parser()
    session = ReadSession(mini_repo)
    with session.activate():
        repo = session.repository()
        before = hashlib.sha256(pickle.dumps(repo)).digest()
        for argv in commands.values():
            result = invoke_outcome(parser.parse_args(["--root", str(mini_repo), *argv]))
            assert result.exit_code == 0, result.stderr
            assert session.repository() is repo
            assert hashlib.sha256(pickle.dumps(repo)).digest() == before, argv
    assert session.unchanged()
