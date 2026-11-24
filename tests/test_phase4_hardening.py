"""Phase 4 security, durability, symlink walk, Git session, and provenance tests."""

from __future__ import annotations

import ast
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml
from gateway_helpers import run_v2_capability
from repo_builders import add_curriculum, write_minimal_pdf, write_yaml

from learning_os.adapters.process_group import terminate_process_group
from learning_os.app._plan_gate import staged_synthesis_errors
from learning_os.app.admission import REVIEWED_SEALING_CAPABILITIES
from learning_os.app.ai_actions import AIActionService
from learning_os.app.backup_manifest import (
    BackupManifestError,
)
from learning_os.app.backup_manifest import (
    _sha256_file as _backup_sha256_file,
)
from learning_os.app.backup_manifest import (
    _stat_identity as _backup_stat_identity,
)
from learning_os.app.check import staged_shadow
from learning_os.app.handlers import sources as sources_handler
from learning_os.app.handlers import synthesis as synthesis_handler
from learning_os.app.lock import LOS_LOCK_TIMEOUT_ENV, _lock_timeout_seconds, scoped_lock_timeout
from learning_os.app.session import (
    SessionConflictError,
    SessionLedgerError,
    _git_cached_paths,
    _git_status_changes,
    _is_receipt_committed_in_head,
    session_end,
)
from learning_os.derive.garden import _state as _garden_state
from learning_os.derive.material_synthesis import (
    MaterialSynthesisError,
    current_unit_material_basis,
)
from learning_os.domain.ai_errors import DeliveryValidationError
from learning_os.domain.failures import TransactionFailure, WriteRefused
from learning_os.domain.plan_import import apply_material_synthesis_patch
from learning_os.store.fs import (
    atomic_write_bytes_exclusive,
    atomic_write_text_exclusive,
    clean_git_env,
    create_ancestors_and_track,
    exclusive_temp_path,
    iter_files_and_top_symlinks,
    iter_non_symlink_files,
    sync_directory_and_created_ancestors,
    sync_fd,
)
from learning_os.store.loader import load_repo
from learning_os.store.materials.reading_cards import Read, ReadingStore
from learning_os.store.session_ledger import record_touched
from learning_os.store.transactions import atomic_write_bytes as tx_atomic_write_bytes

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
SEAL = TOOLS_DIR / "seal_envelope.py"


# --------------------------------------------------------------------------- #
# 1. Shared durable FS primitives, exclusive writers & shadow boundary
# --------------------------------------------------------------------------- #


def test_fs_sync_fd_calls_fullfsync_when_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "sync.txt"
    target.write_text("ok", encoding="utf-8")
    calls: list[tuple[str, int]] = []
    real_fsync = os.fsync
    monkeypatch.setattr(fcntl, "F_FULLFSYNC", 51, raising=False)
    monkeypatch.setattr(os, "fsync", lambda fd: (calls.append(("fsync", fd)), real_fsync(fd))[1])
    monkeypatch.setattr(fcntl, "fcntl", lambda fd, cmd, *a: calls.append(("fullfsync", cmd)))
    with open(target, "rb") as handle:
        sync_fd(handle.fileno())
    assert ("fullfsync", 51) in calls
    assert any(kind == "fsync" for kind, _ in calls)


def test_fs_exclusive_writer_ancestors_and_tx_dot_tmp_fault_parity(tmp_path: Path) -> None:
    nested = tmp_path / "a/b/c/note.txt"
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    # Created ancestor sync helper works across multi-level creation.
    created = create_ancestors_and_track(nested.parent)
    assert [p.name for p in created] == ["c", "b", "a"]
    sync_directory_and_created_ancestors(nested.parent, created)

    # atomic_write_text_exclusive refuses symlink target without clobbering outside.
    sym = tmp_path / "a/link.txt"
    sym.symlink_to(outside)
    with pytest.raises(WriteRefused):
        atomic_write_text_exclusive(sym, "clobber", boundary=tmp_path)
    assert outside.read_text(encoding="utf-8") == "secret"

    # Symlinked directory component inside boundary is refused before opening.
    symdir = tmp_path / "symdir"
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    symdir.symlink_to(outside_dir)
    with pytest.raises(WriteRefused):
        atomic_write_bytes_exclusive(symdir / "x.bin", b"bad", boundary=tmp_path)

    # exclusive_temp_path returns O_EXCL non-symlink temp handle beside target.
    target = tmp_path / "a/data.yaml"
    fd, temp_path = exclusive_temp_path(target)
    try:
        os.write(fd, b"hello")
    finally:
        os.close(fd)
        temp_path.unlink(missing_ok=True)

    # Transactions use unique exclusive temp siblings and still refuse symlink targets.
    tx_link = tmp_path / "a/tx-link.yaml"
    tx_link.symlink_to(outside)
    with pytest.raises(TransactionFailure):
        tx_atomic_write_bytes(tx_link, b"nope")
    unblocked_target = tmp_path / "a/unblocked.yaml"
    stale = unblocked_target.with_name(f".{unblocked_target.name}.tmp")
    stale.write_text("leftover-from-crash", encoding="utf-8")
    tx_atomic_write_bytes(unblocked_target, b"fresh-write\n")
    assert unblocked_target.read_bytes() == b"fresh-write\n"
    assert stale.read_text(encoding="utf-8") == "leftover-from-crash"


def test_staged_shadow_refuses_attachments_and_symlinks(mini_repo: Path) -> None:
    add_curriculum(mini_repo)
    attach = mini_repo / "knowledge/attachments"
    attach.mkdir(parents=True, exist_ok=True)
    with pytest.raises(ValueError, match="attachments"):
        with staged_shadow(mini_repo, {attach / "evil.txt": "bad"}):
            pass

    sym_dir = mini_repo / "work/sym"
    outside = mini_repo.parent / "outside_target"
    outside.mkdir(parents=True, exist_ok=True)
    sym_dir.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        with staged_shadow(mini_repo, {sym_dir / "pwn.md": "bad"}):
            pass


def test_import_delivery_rejects_symlinks_inside_bundle(
    mini_repo: Path, tmp_path: Path,
) -> None:
    add_curriculum(mini_repo)
    app = AIActionService(mini_repo)
    outside = tmp_path / "outside.yaml"
    outside.write_text("evil: true\n", encoding="utf-8")

    bundle = tmp_path / "bundle-with-symlink"
    (bundle / "artifacts").mkdir(parents=True)
    (bundle / "delivery.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    (bundle / "artifacts/leak.yaml").symlink_to(outside)
    with pytest.raises(DeliveryValidationError, match="symbolic links"):
        app.import_delivery(bundle)

    sym_bundle = tmp_path / "bundle-root-link"
    sym_bundle.symlink_to(bundle)
    with pytest.raises(DeliveryValidationError, match="symbolic links"):
        app.import_delivery(sym_bundle)


# --------------------------------------------------------------------------- #
# 2. Python 3.12 non-symlink walks & explicit symlink reporting
# --------------------------------------------------------------------------- #


def test_iter_non_symlink_files_skips_symlinks_and_cycles(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "keep.txt").write_text("ok", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("no", encoding="utf-8")
    (real_dir / "file-link.txt").symlink_to(outside / "secret.txt")
    (real_dir / "dir-link").symlink_to(outside)
    (real_dir / "cycle").symlink_to(real_dir)

    walked = list(iter_non_symlink_files(real_dir))
    assert walked == [real_dir / "keep.txt"]

    files, symlinks = iter_files_and_top_symlinks(real_dir)
    assert files == [real_dir / "keep.txt"]
    assert symlinks == [
        real_dir / "cycle",
        real_dir / "dir-link",
        real_dir / "file-link.txt",
    ]


def test_no_python313_recurse_symlinks_kwarg_anywhere() -> None:
    offenders: list[str] = []
    for folder in (TOOLS_DIR, ROOT / "tests"):
        for path in iter_non_symlink_files(folder):
            if path.suffix != ".py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if any(kw.arg == "recurse_symlinks" for kw in node.keywords):
                        offenders.append(f"{path}:{node.lineno}")
    assert offenders == [], f"Python 3.13-only recurse_symlinks kwarg found: {offenders}"


def test_legacy_exit_review_reports_symlinks_explicitly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import tools.legacy_exit_review as ler

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target.md").write_text("external", encoding="utf-8")
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "link.md").symlink_to(outside / "target.md")
    (legacy / "dir-link").symlink_to(outside)

    monkeypatch.setattr(ler, "ROOT", tmp_path / "repo")
    (tmp_path / "repo" / "migration").mkdir(parents=True)
    items = ler.review(legacy)
    by_rel = {item.path: item for item in items}
    assert by_rel["dir-link"].disposition == "symlink"
    assert by_rel["link.md"].disposition == "symlink"


# --------------------------------------------------------------------------- #
# 3. Git session hardening (#5, #14)
# --------------------------------------------------------------------------- #


def test_clean_git_env_strips_repo_override_variables() -> None:
    cleaned = clean_git_env({
        "GIT_DIR": "/tmp/evil/.git",
        "GIT_WORK_TREE": "/tmp/evil",
        "GIT_INDEX_FILE": "/tmp/evil/idx",
        "GIT_COMMON_DIR": "/tmp/evil/common",
        "PATH": "/usr/bin",
        "LOS_SESSION_ID": "ui",
    })
    for blocked in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        assert blocked not in cleaned
    assert cleaned["PATH"] == "/usr/bin"
    assert cleaned["LOS_SESSION_ID"] == "ui"


def _init_git_repo(root: Path) -> None:
    env = clean_git_env()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, env=env)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True, env=env)


def test_session_end_refuses_pre_staged_unrelated_paths(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_curriculum(mini_repo)
    (mini_repo / "work/inbox").mkdir(parents=True, exist_ok=True)
    session_file = mini_repo / "work/inbox/note-session.md"
    session_file.write_text("session note\n", encoding="utf-8")
    unrelated = mini_repo / "work/inbox/unrelated.md"
    unrelated.write_text("unrelated v1\n", encoding="utf-8")
    _init_git_repo(mini_repo)

    # Record session ownership for note-session.md, modify unrelated.md and stage it.
    session_file.write_text("session note updated\n", encoding="utf-8")
    record_touched(
        mini_repo,
        [session_file],
        channel="operator",
        session_id="operator",
    )
    unrelated.write_text("unrelated pre-staged\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "work/inbox/unrelated.md"],
        cwd=mini_repo,
        check=True,
        env=clean_git_env(),
    )
    # GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE / GIT_COMMON_DIR in ambient env must not
    # hijack session git index/status inspection or HEAD receipt verification.
    wrong_git = tmp_path / "wrong-repo/.git"
    wrong_git.parent.mkdir(parents=True)
    with monkeypatch.context() as env_patch:
        env_patch.setenv("GIT_DIR", str(wrong_git))
        env_patch.setenv("GIT_WORK_TREE", str(wrong_git.parent))
        env_patch.setenv("GIT_INDEX_FILE", str(tmp_path / "wrong-index"))
        env_patch.setenv("GIT_COMMON_DIR", str(wrong_git))
        assert _git_cached_paths(mini_repo) == ["work/inbox/unrelated.md"]
        changed_rels = {path for _, path, _ in _git_status_changes(mini_repo)}
        assert {"work/inbox/note-session.md", "work/inbox/unrelated.md"}.issubset(changed_rels)

    # Also keep an external GIT_INDEX_FILE poisoned across session_end review & commit refusal.
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "wrong-index"))

    reviewed = session_end(
        mini_repo,
        channel="operator",
        session_id="operator",
        include_stale=False,
        close=False,
        commit_message=None,
        push=False,
    )
    assert "work/inbox/note-session.md" in reviewed["touched"]

    with pytest.raises(SessionConflictError, match="already staged in the git index"):
        session_end(
            mini_repo,
            channel="operator",
            session_id="operator",
            include_stale=False,
            close=False,
            commit_message="should refuse pre-staged",
            push=False,
        )

    # Pre-staged index stays untouched and nothing was committed.
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=mini_repo,
        capture_output=True,
        text=True,
        check=True,
        env=clean_git_env(),
    ).stdout.splitlines()
    assert staged == ["work/inbox/unrelated.md"]


def test_session_end_isolated_index_ignores_concurrent_shared_index_and_recovers(
    mini_repo: Path,
) -> None:
    """Finding 3: isolated index commit excludes concurrent shared-index mutations and recovers."""
    add_curriculum(mini_repo)
    (mini_repo / "work/inbox").mkdir(parents=True, exist_ok=True)
    session_file = mini_repo / "work/inbox/note-iso.md"
    session_file.write_text("iso v1\n", encoding="utf-8")
    unrelated = mini_repo / "work/inbox/unrelated-concurrent.md"
    unrelated.write_text("unrelated v1\n", encoding="utf-8")
    _init_git_repo(mini_repo)

    session_file.write_text("iso v2\n", encoding="utf-8")
    record_touched(
        mini_repo,
        [session_file],
        channel="operator",
        session_id="operator",
    )
    unrelated.write_text("unrelated v2\n", encoding="utf-8")

    # Simulate a race right before commit where another Git writer stages an
    # unrelated path into the shared .git/index while session_end prepares its
    # isolated temporary index.
    import learning_os.app.session as session_mod

    real_run = session_mod.subprocess.run
    injected = False

    def racing_run(argv, *args, **kwargs):
        nonlocal injected
        result = real_run(argv, *args, **kwargs)
        if not injected and isinstance(argv, list) and argv[:2] == ["git", "add"]:
            injected = True
            real_run(
                ["git", "add", "work/inbox/unrelated-concurrent.md"],
                cwd=mini_repo,
                check=True,
                env=clean_git_env(),
            )
        return result

    session_mod.subprocess.run = racing_run
    try:
        res = session_end(
            mini_repo,
            channel="operator",
            session_id="operator",
            include_stale=False,
            close=False,
            commit_message="isolated session commit",
            push=False,
        )
    finally:
        session_mod.subprocess.run = real_run
    assert injected is True
    assert res["committed"] is True

    # Commit contains ONLY the session path, never the raced unrelated path.
    committed_paths = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        cwd=mini_repo,
        capture_output=True,
        text=True,
        check=True,
        env=clean_git_env(),
    ).stdout.splitlines()
    assert committed_paths == ["work/inbox/note-iso.md"]

    # Shared .git/index keeps the raced unrelated path staged, while session file is clean.
    shared_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=mini_repo,
        capture_output=True,
        text=True,
        check=True,
        env=clean_git_env(),
    ).stdout.splitlines()
    assert shared_staged == ["work/inbox/unrelated-concurrent.md"]

    # Simulate crash after isolated commit (before shared index reset & ledger close):
    # restore shared index back to HEAD~1 (leaving HEAD at the committed SHA) and
    # re-record the session ledger row, then run session_end retry -> recovers cleanly!
    subprocess.run(
        ["git", "read-tree", "HEAD~1"],
        cwd=mini_repo,
        check=True,
        env=clean_git_env(),
    )
    record_touched(
        mini_repo,
        [session_file],
        channel="operator",
        session_id="operator",
    )
    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=mini_repo,
        capture_output=True,
        text=True,
        check=True,
        env=clean_git_env(),
    ).stdout.strip()
    recovered = session_end(
        mini_repo,
        channel="operator",
        session_id="operator",
        include_stale=False,
        close=False,
        commit_message="isolated session commit",
        push=False,
    )
    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=mini_repo,
        capture_output=True,
        text=True,
        check=True,
        env=clean_git_env(),
    ).stdout.strip()
    assert recovered["committed"] is True
    assert head_after == head_before


def test_git_status_nonzero_raises_session_ledger_error(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 128, b"", b"fatal: not a git repo"),
    )
    with pytest.raises(SessionLedgerError, match="git status exited 128"):
        _git_status_changes(mini_repo)


def test_is_receipt_committed_in_head_checks_blob_commit_and_idempotency(
    mini_repo: Path,
) -> None:
    add_curriculum(mini_repo)
    tx_dir = mini_repo / "operations/transactions"
    tx_dir.mkdir(parents=True, exist_ok=True)
    receipt_rel = "operations/transactions/transaction-001.yaml"
    receipt_path = mini_repo / receipt_rel
    receipt = {
        "schema_version": 2,
        "transaction_id": "transaction-001",
        "capability": "capture.create",
    }
    receipt_bytes = yaml.safe_dump(receipt, sort_keys=False).encode("utf-8")
    receipt_path.write_bytes(receipt_bytes)
    _init_git_repo(mini_repo)

    # Committed without matching idempotency ledger entry -> False.
    assert _is_receipt_committed_in_head(
        mini_repo, receipt_rel, receipt_bytes, receipt=receipt,
    ) is False

    idem_path = mini_repo / "operations/transactions/idempotency.yaml"
    write_yaml(idem_path, {
        "schema_version": 2,
        "entries": {
            "key-001": {
                "transaction_id": "transaction-001",
                "receipt_path": receipt_rel,
                "capability": "capture.create",
                "intent_sha256": "sha256:" + "1" * 64,
            },
        },
    })
    subprocess.run(
        ["git", "add", "operations/transactions/idempotency.yaml"],
        cwd=mini_repo,
        check=True,
        env=clean_git_env(),
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "forged late idempotency"],
        cwd=mini_repo,
        check=True,
        env=clean_git_env(),
    )
    # Introducing commit for receipt was the initial commit, which lacked idempotency.yaml!
    assert _is_receipt_committed_in_head(
        mini_repo, receipt_rel, receipt_bytes, receipt=receipt,
    ) is False

    # Same-commit introduction of BOTH receipt and idempotency entry -> True.
    receipt_rel2 = "operations/transactions/transaction-002.yaml"
    receipt2 = {
        "schema_version": 2,
        "transaction_id": "transaction-002",
        "capability": "capture.create",
    }
    receipt_bytes2 = yaml.safe_dump(receipt2, sort_keys=False).encode("utf-8")
    (mini_repo / receipt_rel2).write_bytes(receipt_bytes2)
    write_yaml(idem_path, {
        "schema_version": 2,
        "entries": {
            "key-001": {
                "transaction_id": "transaction-001",
                "receipt_path": receipt_rel,
                "capability": "capture.create",
                "intent_sha256": "sha256:" + "1" * 64,
            },
            "key-002": {
                "transaction_id": "transaction-002",
                "receipt_path": receipt_rel2,
                "capability": "capture.create",
                "intent_sha256": "sha256:" + "2" * 64,
            },
        },
    })
    subprocess.run(["git", "add", receipt_rel2, "operations/transactions/idempotency.yaml"],
                   cwd=mini_repo, check=True, env=clean_git_env())
    subprocess.run(["git", "commit", "-q", "-m", "tx2"], cwd=mini_repo, check=True, env=clean_git_env())
    assert _is_receipt_committed_in_head(
        mini_repo, receipt_rel2, receipt_bytes2, receipt=receipt2,
    ) is True


# --------------------------------------------------------------------------- #
# 4. Tool / subprocess / O_NOFOLLOW / handler hardening (#6, #10, #18d, #20b, #25)
# --------------------------------------------------------------------------- #


def test_agent_run_deadline_kills_process_group_without_mutating_os_environ(
    tmp_path: Path,
) -> None:
    import tools.agent_run as agent_run

    before_env = os.environ.get(LOS_LOCK_TIMEOUT_ENV)
    with scoped_lock_timeout(3.5):
        assert _lock_timeout_seconds() == 3.5
        assert os.environ.get(LOS_LOCK_TIMEOUT_ENV) == before_env
    assert _lock_timeout_seconds() == (float(before_env) if before_env else None)

    pid_file = tmp_path / "child.pid"
    script = (
        "import os, subprocess, sys, time\n"
        f"p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        f"open({str(pid_file)!r}, 'w').write(str(p.pid))\n"
        "time.sleep(30)\n"
    )
    with pytest.raises(agent_run.AgentRunError) as exc:
        agent_run._run_subprocess_bounded(
            [sys.executable, "-c", script],
            cwd=tmp_path,
            timeout_s=0.3,
        )
    assert exc.value.code == agent_run.STEP_FAILED
    if pid_file.is_file():
        child_pid = int(pid_file.read_text(encoding="utf-8"))
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)


def test_terminate_process_group_reaps_cleanly(tmp_path: Path) -> None:
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        start_new_session=True,
    )
    pid = proc.pid
    terminate_process_group(proc, grace_s=0.5)
    proc.wait(timeout=5)
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_backup_manifest_and_garden_refuse_symlinks(
    mini_repo: Path, tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.yaml"
    outside.write_text("leaked: true\n", encoding="utf-8")
    link = tmp_path / "symlink.yaml"
    link.symlink_to(outside)
    with pytest.raises(BackupManifestError, match="not a regular file"):
        _backup_stat_identity(link)
    with pytest.raises(BackupManifestError):
        _backup_sha256_file(link)

    add_curriculum(mini_repo)
    state_dir = mini_repo / "operations/ai-actions/garden-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "seed-link.yaml").symlink_to(outside)
    assert _garden_state(mini_repo, "seed-link") == {}
    assert _garden_state(mini_repo, "../outside") == {}


def test_plan_import_and_sources_and_ingest_refuse_bad_inputs(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import tools.ingest_transcript as ingest_tool

    add_curriculum(mini_repo)
    dossier = {
        "route_assessments": [{"route_id": "route-existing"}],
        "concept_groups": [],
    }
    _, errs_unknown = apply_material_synthesis_patch(
        dossier,
        {"route_assessments_remove": ["route-missing"]},
        {},
        "module-demo",
        "unit-demo-l01",
        "units[0]",
    )
    assert any("unassessed route: route-missing" in e for e in errs_unknown)

    _, errs_dup = apply_material_synthesis_patch(
        dossier,
        {"route_assessments_remove": ["route-existing", "route-existing"]},
        {},
        "module-demo",
        "unit-demo-l01",
        "units[0]",
    )
    assert any("repeats route: route-existing" in e for e in errs_dup)

    mat = mini_repo.parent / "materials/source-demo-book/book.pdf"
    write_minimal_pdf(mat, ["page 1"])
    repo = load_repo(mini_repo)
    monkeypatch.setattr(
        sources_handler,
        "sha256_file",
        lambda *_a, **_kw: (_ for _ in ()).throw(OSError(errno.EIO, "disk read failed")),
    )
    with pytest.raises(WriteRefused, match="could not be inspected"):
        sources_handler._resolve_revise_material(
            mini_repo, repo, "material://source-demo-book/book.pdf", "source-demo-book",
        )

    assert not ingest_tool.VALID_VIDEO_ID.fullmatch("../escape")
    assert not ingest_tool.VALID_VIDEO_ID.fullmatch("bad id")
    assert ingest_tool.VALID_VIDEO_ID.fullmatch("dQw4w9WgXcQ")


def test_move_map_rolls_back_moved_files_and_rewrites_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import tools.move_map as move_map

    repo = tmp_path / "repo"
    (repo / "notes").mkdir(parents=True)
    src_file = repo / "notes/old.md"
    src_file.write_text("hello notes/old.md\n", encoding="utf-8")
    _init_git_repo(repo)
    map_file = tmp_path / "moves.yaml"
    map_file.write_text(
        yaml.safe_dump({"moves": [{"from": "notes/old.md", "to": "notes/new.md"}]}),
        encoding="utf-8",
    )

    real_write = sys.modules["learning_os.store.fs"].atomic_write_text_exclusive

    def fail_on_ledger(path: Path, content: str, **kwargs):
        if Path(path).name == "moves.yaml":
            raise OSError("injected ledger write failure")
        return real_write(path, content, **kwargs)

    monkeypatch.setattr(
        sys.modules["learning_os.store.fs"], "atomic_write_text_exclusive", fail_on_ledger,
    )
    monkeypatch.chdir(repo)
    rc = move_map.main(["--map", str(map_file), "--apply"])
    assert rc == 2
    assert src_file.is_file()
    assert not (repo / "notes/new.md").exists()
    assert src_file.read_text(encoding="utf-8") == "hello notes/old.md\n"


# --------------------------------------------------------------------------- #
# 5. Material Synthesis Provenance Matrix across all 3 paths + #29 parity
# --------------------------------------------------------------------------- #


def _seed_provenance_world(
    root: Path, *, two_file: bool = False,
) -> tuple[dict, str, Path]:
    add_curriculum(root)
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average.",
             "builds_on": ["knowledge-demo-outcomes"]},
        ],
    }
    write_yaml(unit_path, unit)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    locator = "lecture-01.pdf; part-b.pdf" if two_file else "lecture-01.pdf"
    source_map["sources"][0]["unit_routes"] = [{
        "id": "route-demo-l01-book",
        "unit_id": "unit-demo-l01",
        "title": "Demo Book",
        "format": "book",
        "angle": "Derives the weighted sum.",
        "covers": ["knowledge-demo-outcomes", "knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": "current",
        "locator": locator,
    }]
    write_yaml(source_map_path, source_map)
    reg_path = root / "sources/sources.yaml"
    reg = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
    reg["sources"][0]["material"] = "material://source-demo-book/book.pdf"
    write_yaml(reg_path, reg)
    pdf1 = root.parent / "materials/source-demo-book/lecture-01.pdf"
    write_minimal_pdf(pdf1, ["lecture page 1"])
    if two_file:
        pdf2 = root.parent / "materials/source-demo-book/part-b.pdf"
        write_minimal_pdf(pdf2, ["part-b page 1"])
    basis = current_unit_material_basis(root, "unit-demo-l01")
    checksum = basis["material_checksums"]["route-demo-l01-book"]
    cited = "part-b.pdf p.1" if two_file else "lecture-01.pdf p.1"
    scope_of_absence = "lecture-01.pdf, PDF p. 1" if two_file else f"{locator}, PDF p. 1"
    dossier = {
        "schema_version": 1,
        "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": {
            **basis,
            "ai_provenance": {
                "request_id": "ai-request-demo",
                "delivery_id": "ai-delivery-demo",
                "provider": "manual-bundle",
            },
        },
        "route_assessments": [{
            "route_id": "route-demo-l01-book",
            "source_id": "source-demo-book",
            "locator": locator,
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "A direct derivation of the weighted sum.",
            "assumptions": "Finite discrete outcomes.",
            "notation": "Uses uppercase X.",
            "exercise_value": "Includes worked calculation.",
            "best_for": "Checking core derivation.",
            "limitations": "Finite only.",
            "scope_of_absence": scope_of_absence,
            "evidence": [{"locator": cited, "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [
            {
                "concept_id": "concept-variance",
                "local_node_ids": ["knowledge-demo-outcomes"],
                "related_unit_ids": [],
                "bridge_note_ids": [],
                "narrative": "Outcomes feed dispersion.",
            },
            {
                "concept_id": "concept-expected-value",
                "local_node_ids": ["knowledge-demo-expectation"],
                "related_unit_ids": ["unit-demo-l01"],
                "bridge_note_ids": ["note-demo"],
                "narrative": "Canonical expectation concept.",
            },
        ],
    }
    return dossier, checksum, pdf1


def _record_card_for_pdf(root: Path, pdf_path: Path, rel_material: str) -> Path:
    store = ReadingStore(root)
    digest_hex = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    sess = str(uuid.UUID("aaaaaaaa-1111-4111-8111-111111111111"))
    admission = store.admit(
        sess,
        [Read(digest=digest_hex, material=rel_material, start=1, end=1, text_sha256="0" * 64)],
        now=dt.datetime(2026, 10, 1, 9, 0, tzinfo=dt.UTC),
    )
    entry_name = admission.opened[0]["entry"]
    store.save(
        sess,
        entry_name,
        {
            "paraphrase": "Restates the expectation derivation on page one cleanly.",
            "kinds": ["statement"],
            "pointers": [{"page": 1, "kind": "statement", "label": "definition"}],
            "concepts": ["concept-expected-value"],
        },
        now=dt.datetime(2026, 10, 1, 9, 1, tzinfo=dt.UTC),
    )
    cards = [
        p for p in iter_non_symlink_files(store.root / "cards")
        if p.name.startswith("v") and p.suffix == ".json"
    ]
    assert len(cards) == 1
    return cards[0]


def _check_all_three_paths(
    mini_repo: Path,
    dossier: dict,
    tmp_path: Path,
    case_tag: str,
    *,
    expected_error: str | None = None,
    clear_attached_slices: bool = False,
) -> tuple[bool, bool, bool]:
    # 1. Direct publication handler path
    pub_ok = True
    try:
        synthesis_handler._validate_publication_synthesis(mini_repo, "unit-demo-l01", dossier)
    except MaterialSynthesisError as exc:
        if expected_error is not None:
            assert re.search(expected_error, str(exc)), f"pub error mismatch: {exc}"
        pub_ok = False

    # 2. Staged module plan gate path (shadow repo under tmp_path -> empty shadow reading-memory!)
    with staged_shadow(mini_repo, {}) as shadow:
        shadow_repo = load_repo(shadow)
        live_repo = load_repo(mini_repo)
        plan_errs = staged_synthesis_errors(
            mini_repo, "module-demo", live_repo, shadow, shadow_repo, [("unit-demo-l01", dossier)],
        )
    gate_ok = plan_errs == []
    if not gate_ok and expected_error is not None:
        assert any(re.search(expected_error, err) for err in plan_errs), (
            f"gate error mismatch: {plan_errs}"
        )

    # 3. AI delivery bundle path
    app = AIActionService(mini_repo)
    req = app.prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id=f"ai-request-{case_tag}",
    )
    if clear_attached_slices:
        slices_idx = (
            mini_repo
            / "operations/ai-actions/requests"
            / req["id"]
            / "attachments/slices/index.json"
        )
        slices_idx.write_text("[]\n", encoding="utf-8")
    deliv_id = f"ai-deliv-{case_tag}"
    bundle_dossier = {
        **dossier,
        "basis": {
            **dossier["basis"],
            "ai_provenance": {
                "request_id": req["id"],
                "delivery_id": deliv_id,
                "provider": "manual-bundle",
            },
        },
    }
    src = tmp_path / f"src-{case_tag}"
    (src / "artifacts").mkdir(parents=True)
    write_yaml(src / "artifacts/material-synthesis.yaml", bundle_dossier)
    write_yaml(src / "delivery.yaml", {
        "schema_version": 1,
        "id": deliv_id,
        "type": "ai-action-delivery",
        "request_id": req["id"],
        "action_id": "unit.compare-materials",
        "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {"user_approved": True, "approved_at": "2026-10-01T09:05:00+00:00"},
        "operations": [{
            "capability": "unit.material-synthesis.publish",
            "target_id": "unit-demo-l01",
            "artifact_ref": "artifacts/material-synthesis.yaml",
        }],
        "preconditions": req["preconditions"],
    })
    deliv_ok = True
    try:
        delivery = app.import_delivery(src)
        app.preview_delivery(delivery["id"])
    except DeliveryValidationError as exc:
        if expected_error is not None:
            assert re.search(expected_error, str(exc)), f"deliv error mismatch: {exc}"
        assert not app.repository.delivery_dir(deliv_id).exists()
        assert app.repository.get_request(req["id"])["status"] == "prepared"
        assert not (
            mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml"
        ).exists()
        assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
        deliv_ok = False
    return pub_ok, gate_ok, deliv_ok


def test_synthesis_provenance_matrix_across_all_three_paths(
    mini_repo: Path, tmp_path: Path,
) -> None:
    # Scenario A: zero reading memory -> legacy compatibility exemption passes on all 3 paths.
    dossier_zero, _, pdf1 = _seed_provenance_world(mini_repo, two_file=False)
    assert _check_all_three_paths(mini_repo, dossier_zero, tmp_path, "zero") == (True, True, True)

    # Scenario B: card recorded, then PDF rewritten -> stale digest fails closed on all 3 paths.
    card_path = _record_card_for_pdf(mini_repo, pdf1, "source-demo-book/lecture-01.pdf")
    write_minimal_pdf(pdf1, ["lecture page 1 modified"])
    # Refresh dossier basis to match live bytes so provenance (not basis checksum) catches staleness!
    live_basis = current_unit_material_basis(mini_repo, "unit-demo-l01")
    live_checksum = live_basis["material_checksums"]["route-demo-l01-book"]
    dossier_stale = {
        **dossier_zero,
        "basis": {
            **live_basis,
            "ai_provenance": dossier_zero["basis"]["ai_provenance"],
        },
        "route_assessments": [{
            **dossier_zero["route_assessments"][0],
            "evidence": [{"locator": "lecture-01.pdf p.1", "checksum": live_checksum}],
        }],
    }
    assert _check_all_three_paths(
        mini_repo,
        dossier_stale,
        tmp_path,
        "stale",
        expected_error=r"reading memory for source-demo-book/lecture-01\.pdf is stale",
    ) == (False, False, False)

    # Scenario C: unreadable / malformed / symlinked reading card -> fails closed on all 3 paths.
    raw_card = card_path.read_text(encoding="utf-8")
    card_path.write_text("{not valid json", encoding="utf-8")
    assert _check_all_three_paths(
        mini_repo,
        dossier_stale,
        tmp_path,
        "malformed",
        expected_error=r"reading memory is unreadable",
    ) == (False, False, False)
    card_path.unlink()
    outside_card = tmp_path / "outside-card.json"
    outside_card.write_text(raw_card, encoding="utf-8")
    card_path.symlink_to(outside_card)
    assert _check_all_three_paths(
        mini_repo,
        dossier_stale,
        tmp_path,
        "symlink",
        expected_error=r"reading memory is unreadable",
    ) == (False, False, False)


def test_synthesis_provenance_two_file_route_fails_uncovered_second_file(
    mini_repo: Path, tmp_path: Path,
) -> None:
    dossier_two, checksum, pdf1 = _seed_provenance_world(mini_repo, two_file=True)
    # Only lecture-01.pdf has a valid live card; part-b.pdf has none (and prepared
    # bundle slices are cleared) so citing part-b.pdf fails closed on all 3 paths.
    _record_card_for_pdf(mini_repo, pdf1, "source-demo-book/lecture-01.pdf")
    assert _check_all_three_paths(
        mini_repo,
        dossier_two,
        tmp_path,
        "twofile",
        expected_error=r"part-b\.pdf pages never inspected",
        clear_attached_slices=True,
    ) == (False, False, False)

    # Positive control: citing only the inspected first PDF with bounded scope_of_absence passes.
    dossier_first_only = {
        **dossier_two,
        "route_assessments": [{
            **dossier_two["route_assessments"][0],
            "scope_of_absence": "lecture-01.pdf, PDF p. 1",
            "evidence": [{"locator": "lecture-01.pdf p.1", "checksum": checksum}],
        }],
    }
    assert _check_all_three_paths(
        mini_repo,
        dossier_first_only,
        tmp_path,
        "twofile-firstonly",
        clear_attached_slices=True,
    ) == (True, True, True)


def test_unit_material_synthesis_publish_review_binding_parity(
    mini_repo: Path, tmp_path: Path,
) -> None:
    assert "unit.material-synthesis.publish" in REVIEWED_SEALING_CAPABILITIES
    dossier, _, _ = _seed_provenance_world(mini_repo, two_file=False)
    dossier_path = tmp_path / "dossier.yaml"
    write_yaml(dossier_path, dossier)
    payload = {"unit_id": "unit-demo-l01", "record": dossier}

    # Handler --check via CLI emits reviewed_file_sha256, mode="check",
    # expected_snapshot, and gateway_envelope matching other reviewed commands.
    cli_check = subprocess.run(
        [
            sys.executable, str(TOOLS_DIR / "los.py"), "--root", str(mini_repo),
            "unit-material-synthesis-publish", "unit-demo-l01",
            "--file", str(dossier_path), "--check", "--json",
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert cli_check.returncode == 0, cli_check.stderr
    cli_doc = json.loads(cli_check.stdout)
    assert cli_doc["ok"] is True
    assert cli_doc["mode"] == "check"
    assert cli_doc["expected_snapshot"].startswith("sha256:")
    assert cli_doc["reviewed_file_sha256"].startswith("sha256:")
    assert cli_doc["gateway_envelope"]["capability"] == "unit.material-synthesis.publish"

    # seal_envelope --check-out emits a valid review record bound to snapshot & review hash.
    out_check = tmp_path / "review.json"
    res_check = subprocess.run(
        [
            sys.executable, str(SEAL), "--root", str(mini_repo),
            "--capability", "unit.material-synthesis.publish",
            "--payload", json.dumps(payload), "--key", "synth-parity-001",
            "--guards", "auto", "--check-out", str(out_check),
            "--out", str(tmp_path / "unused.json"),
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert res_check.returncode == 0, res_check.stderr
    review_doc = json.loads(out_check.read_text(encoding="utf-8"))
    assert review_doc["ok"] is True
    assert review_doc["expected_snapshot"].startswith("sha256:")
    assert "record_sha256" in review_doc["review"]

    # Unreviewed --guards auto bypass refuses at gateway with UNCONFIRMED.
    bypass = tmp_path / "bypass.json"
    res_bypass = subprocess.run(
        [
            sys.executable, str(SEAL), "--root", str(mini_repo),
            "--capability", "unit.material-synthesis.publish",
            "--payload", json.dumps(payload), "--key", "synth-parity-bypass",
            "--guards", "auto", "--out", str(bypass),
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert res_bypass.returncode == 0, res_bypass.stderr
    refused = run_v2_capability(mini_repo, json.loads(bypass.read_text(encoding="utf-8")))
    assert refused.returncode != 0
    assert json.loads(refused.stdout)["error"]["code"] == "UNCONFIRMED"

    # Submitting with --guards-from <check-record> commits cleanly.
    applied = subprocess.run(
        [sys.executable, str(SEAL), "--root", str(mini_repo), "--guards-from", str(out_check), "--submit"],
        capture_output=True, text=True, timeout=120,
    )
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(applied.stdout)["ok"] is True
    dest = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml"
    assert dest.is_file()


def test_session_end_no_git_allows_review_and_close_but_refuses_commit(
    mini_repo: Path,
) -> None:
    review = session_end(
        mini_repo,
        channel=None,
        session_id="cli",
        include_stale=False,
        close=False,
        commit_message=None,
        push=False,
    )
    assert review["committed"] is False
    assert review["session_closed"] is False
    assert review["owned_changes"] == []

    closed = session_end(
        mini_repo,
        channel=None,
        session_id="cli",
        include_stale=False,
        close=True,
        commit_message=None,
        push=False,
    )
    assert closed["committed"] is False
    assert closed["session_closed"] is True

    with pytest.raises(SessionLedgerError, match="no git repository"):
        session_end(
            mini_repo,
            channel=None,
            session_id="cli",
            include_stale=False,
            close=False,
            commit_message="phase4: cannot commit without git",
            push=False,
        )


def test_session_end_with_git_still_refuses_nonzero_git_status(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(mini_repo)
    real_run = subprocess.run

    def fail_status(cmd: object, *args: object, **kwargs: object) -> object:
        if isinstance(cmd, list) and cmd[:4] == ["git", "status", "--porcelain=v1", "-z"]:
            return subprocess.CompletedProcess(cmd, 128, b"", b"fatal: corrupt index")
        return real_run(cmd, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(subprocess, "run", fail_status)
    with pytest.raises(SessionLedgerError, match="git status exited 128"):
        session_end(
            mini_repo,
            channel=None,
            session_id="cli",
            include_stale=False,
            close=False,
            commit_message=None,
            push=False,
        )


def test_atomic_write_text_exclusive_preserves_permission_error_for_oserror_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    real_open = os.open

    def deny_open(path: object, *args: object, **kwargs: object) -> int:
        if Path(os.fsdecode(path)).name.startswith(".denied.txt.tmp-"):  # type: ignore[arg-type]
            raise PermissionError(1, "Permission denied")
        return real_open(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "open", deny_open)
    with pytest.raises(PermissionError):
        atomic_write_text_exclusive(
            tmp_path / "denied.txt", "blocked", boundary=tmp_path, error_factory=OSError,
        )
    monkeypatch.undo()

    real_replace = os.replace

    def deny_replace(src: object, dst: object) -> None:
        if Path(os.fsdecode(dst)).name == "replace-denied.txt":  # type: ignore[arg-type]
            raise PermissionError(1, "Permission denied")
        real_replace(src, dst)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", deny_replace)
    with pytest.raises(PermissionError):
        atomic_write_text_exclusive(
            tmp_path / "replace-denied.txt",
            "blocked-replace",
            boundary=tmp_path,
            error_factory=OSError,
        )
    assert list(tmp_path.glob(".replace-denied.txt.tmp-*")) == []
