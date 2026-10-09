"""Eleven A2 prototype-gate fixtures (PLAN step 0.2, SPEC §3.2e).

One function per fixture, each asserting exactly its expected oracle and
hook outcome. ``test_arch_writes.py`` runs them.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import uuid
from collections import Counter
from pathlib import Path

import arch_audit_hook
import arch_effects

from learning_os.fingerprint import CANONICAL_ROOTS

_ARCH_SITE = Path(__file__).resolve().parent / "arch_site"


def _build_root(tmp_path: Path, name: str) -> Path:
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    root = build_mini_repo(Path(tmp_path) / name).resolve()
    add_curriculum(root)
    return root


def _read_log(log_path: Path) -> list[dict]:
    # Activated logs always exist; a missing one raises (SPEC §3.2c, K30).
    return arch_audit_hook.read_log(log_path)


def _fresh_token() -> str:
    return f"launch-{uuid.uuid4().hex}"


def _child_env(log_path: Path, token: str, with_site: bool = True) -> dict:
    env = dict(os.environ)
    env["LOS_ARCH_AUDIT_LOG"] = str(log_path)
    env["LOS_ARCH_LAUNCH_TOKEN"] = token
    env["TZ"] = "Europe/Berlin"
    if with_site:
        env["PYTHONPATH"] = str(_ARCH_SITE) + os.pathsep + env.get(
            "PYTHONPATH", "")
    else:
        env.pop("PYTHONPATH", None)
    return env


def _is_canonical(path_value, root: Path) -> bool:
    if not isinstance(path_value, str) or not os.path.isabs(path_value):
        return False
    try:
        rel = Path(path_value).resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return False
    for base in CANONICAL_ROOTS:
        if rel == base or rel.startswith(base + "/"):
            return True
    return False


def _write_path_of(record: dict):
    paths = record.get("paths") or []
    if not paths:
        return None
    if record.get("event") in (
            "os.rename", "os.link", "os.symlink",
            "shutil.copyfile", "shutil.move"):
        return paths[-1] if len(paths) >= 2 else paths[0]
    return paths[0]


def _canonical_records(records: list[dict], root: Path) -> list[dict]:
    return [rec for rec in records
            if _is_canonical(_write_path_of(rec), root)]


def _write_journal_v2(root: Path, tx_id: str, entries: list) -> Path:
    tx_dir = root / "operations" / "transactions" / ".inflight" / tx_id
    tx_dir.mkdir(parents=True)
    paths = []
    for index, (relative, before, after) in enumerate(entries):
        if before is None:
            recorded_before: dict = {"kind": "absent"}
        else:
            backup_id = f"backup-{index}"
            (tx_dir / backup_id).write_bytes(before)
            recorded_before = {
                "kind": "file",
                "sha256": f"sha256:{hashlib.sha256(before).hexdigest()}",
                "backup_id": backup_id,
            }
        record: dict = {"path": relative, "before": recorded_before}
        if after is None:
            record["after"] = {"kind": "absent"}
        else:
            record["after"] = {
                "kind": "file",
                "sha256": f"sha256:{hashlib.sha256(after).hexdigest()}",
            }
        paths.append(record)
    intent = {
        "schema_version": 2,
        "transaction_id": tx_id,
        "receipt_path": f"operations/transactions/{tx_id}.yaml",
        "paths": paths,
    }
    (tx_dir / "intent.json").write_text(json.dumps(intent), encoding="utf-8")
    return tx_dir


def fixture_1_query_escalated_recovery(tmp_path: Path) -> None:
    import learning_os.ops._legacy_plumbing as plumbing

    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f1")
    target = root / "knowledge" / "concepts.yaml"
    pre_bytes = target.read_bytes()
    pre_state = arch_effects.capture_tree(root)
    torn = b"# torn by a crashed predecessor\n"
    assert torn != pre_bytes
    target.write_bytes(torn)
    _write_journal_v2(
        root, "transaction-20260101-000000-001",
        [(target.relative_to(root).as_posix(), pre_bytes, torn)])
    before = arch_effects.capture_tree(root)
    receipts_before = [
        p.name for p in (root / "operations" / "transactions").glob(
            "transaction-*.yaml")] if (
                root / "operations" / "transactions").is_dir() else []
    log_path = tmp_path / "a2-f1.log"
    arch_audit_hook.install(str(log_path))
    try:
        with plumbing._operator_lock(root, shared=True):
            pass
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    after = arch_effects.capture_tree(root)
    receipts = arch_effects.new_receipts(receipts_before, root)
    violations = arch_effects.reconcile(
        before, after, receipts, restored_from=pre_state)
    assert violations == [], f"oracle must accept the proven restore: {violations}"
    assert target.read_bytes() == pre_bytes
    records = _canonical_records(_read_log(log_path), root)
    assert records, "hook must log the restore writes"
    for record in records:
        assert record.get("phase") == "restore", (
            f"restore writes carry phase restore: {record}")


def fixture_2_unproven_restore(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f2")
    target = root / "knowledge" / "concepts.yaml"
    before = arch_effects.capture_tree(root)
    receipts_before: list[str] = []
    log_path = tmp_path / "a2-f2.log"
    arch_audit_hook.install(str(log_path))
    try:
        target.write_text("# unproven restore\n", encoding="utf-8")
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    after = arch_effects.capture_tree(root)
    receipts = arch_effects.new_receipts(receipts_before, root)
    violations = arch_effects.reconcile(before, after, receipts)
    assert len(violations) == 1, f"oracle must report one violation: {violations}"
    records = _read_log(log_path)
    unowned = [rec for rec in _canonical_records(records, root)
               if rec.get("phase") not in ("apply", "restore")]
    assert unowned, "hook must report an unowned canonical write"


def _callback_case(tmp_path: Path, name: str, kind: str) -> None:
    from learning_os.transactions import TransactionService

    root = _build_root(tmp_path, name)
    legit = root / "work" / "inbox" / f"{kind}-legit.md"
    rogue = root / "work" / "inbox" / f"{kind}-rogue.md"
    log_path = Path(tmp_path) / f"a2-f3-{kind}.log"
    arch_audit_hook.install(str(log_path))
    try:
        if kind == "transaction_writes":
            def _tw(transaction_id: str):
                rogue.write_text("rogue\n", encoding="utf-8")
                return {}
            TransactionService(root).commit(
                capability="capture.create",
                writes={legit: "legit\n"},
                artifact_ids=[f"arch-f3-{kind}"],
                transaction_writes=_tw,
            )
        elif kind == "validate_state":
            def _validate():
                rogue.write_text("rogue\n", encoding="utf-8")
                return []
            TransactionService(root).commit(
                capability="capture.create",
                writes={legit: "legit\n"},
                artifact_ids=[f"arch-f3-{kind}"],
                validate_state=_validate,
            )
        elif kind == "publish":
            def _publish():
                rogue.write_text("rogue\n", encoding="utf-8")
                return None
            TransactionService(root).commit(
                capability="capture.create",
                writes={legit: "legit\n"},
                artifact_ids=[f"arch-f3-{kind}"],
                publish=_publish,
            )
        else:
            raise AssertionError(f"unknown callback kind {kind!r}")
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    records = _read_log(log_path)
    rogue_abs = str(rogue.resolve())
    unowned = []
    for rec in _canonical_records(records, root):
        if rec.get("phase") in ("apply", "restore"):
            continue
        wrote = _write_path_of(rec)
        if isinstance(wrote, str):
            try:
                if Path(wrote).resolve().as_posix() == Path(
                        rogue_abs).as_posix():
                    unowned.append(rec)
            except OSError:
                continue
    assert unowned, (
        f"hook must report an unowned canonical write for {kind}")


def fixture_3_rogue_callbacks(tmp_path: Path) -> None:
    for kind in ("transaction_writes", "validate_state", "publish"):
        _callback_case(Path(tmp_path), f"a2-f3-{kind}", kind)


def fixture_4_descriptor_and_dir_fd(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f4")
    inbox = root / "work" / "inbox"
    assert inbox.resolve() != Path(os.getcwd()).resolve()
    # Descriptor opened before install().
    fd_target = inbox / "fd-write.md"
    fd = os.open(str(fd_target), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        before_fd = arch_effects.capture_tree(root)
        log_fd = tmp_path / "a2-f4-fd.log"
        arch_audit_hook.install(str(log_fd))
        try:
            os.write(fd, b"via descriptor\n")
        finally:
            arch_audit_hook.uninstall()
    finally:
        os.close(fd)
    arch_audit_hook.assert_capture_ok()
    after_fd = arch_effects.capture_tree(root)
    fd_violations = arch_effects.reconcile(before_fd, after_fd, [])
    assert fd_violations, "oracle must report the descriptor write"
    fd_records = _read_log(log_fd)
    fd_hits = [rec for rec in fd_records
               for path in (rec.get("paths") or [])
               if isinstance(path, str) and path.endswith("fd-write.md")]
    assert fd_hits == [], (
        f"descriptor write must produce no hook event: {fd_hits}")
    # dir_fd write to a canonical directory that is not the process cwd.
    dir_fd = os.open(str(inbox), os.O_RDONLY)
    try:
        before_dd = arch_effects.capture_tree(root)
        log_dd = tmp_path / "a2-f4-dirfd.log"
        arch_audit_hook.install(str(log_dd))
        try:
            child = os.open("dirfd-write.md",
                            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                            0o644, dir_fd=dir_fd)
            try:
                os.write(child, b"via dir_fd\n")
            finally:
                os.close(child)
        finally:
            arch_audit_hook.uninstall()
    finally:
        os.close(dir_fd)
    arch_audit_hook.assert_capture_ok()
    after_dd = arch_effects.capture_tree(root)
    dd_violations = arch_effects.reconcile(before_dd, after_dd, [])
    assert dd_violations, "oracle must report the dir_fd write"
    dd_records = _read_log(log_dd)
    dd_opens = [rec for rec in dd_records if rec.get("event") == "open"]
    assert dd_opens, "hook must log the dir_fd open event"
    assert any(isinstance(rec.get("paths", [None])[0], str)
               and not os.path.isabs(rec["paths"][0])
               for rec in dd_opens), (
        f"dir_fd open must carry a relative path: {dd_opens}")


def fixture_5_rename_into_canonical(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f5")
    scratch = tmp_path / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    src = scratch / "staged.md"
    src.write_text("staged\n", encoding="utf-8")
    dest = root / "work" / "inbox" / "renamed.md"
    log_path = tmp_path / "a2-f5.log"
    arch_audit_hook.install(str(log_path))
    try:
        os.rename(str(src), str(dest))
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    records = _read_log(log_path)
    renames = [rec for rec in records if rec.get("event") == "os.rename"]
    assert renames, "hook must log the rename"
    dest_hits = [rec for rec in renames
                 if len(rec.get("paths") or []) == 2
                 and _is_canonical(rec["paths"][1], root)]
    assert dest_hits, (
        "rename into a canonical root is a canonical write by destination")


def _is_python_argv(argv: list) -> bool:
    if not argv:
        return False
    first = str(argv[0])
    return first.endswith(("python", "python3", "python3.14",
                           ".venv/bin/python"))


def witness_failures(records: list[dict]) -> list[str]:
    """Launch-coverage failures over audit records (SPEC §3.2c, K28-K30).

    Python launches and ``installed`` witnesses are counted per launch
    token; an install is excused from its missing ``completed`` record
    only when its token's launch was logged with ``expect_crash``.
    """
    popens = [rec for rec in records
              if rec.get("event") == "subprocess.Popen"
              and _is_python_argv(rec.get("argv") or [])]
    launches: Counter = Counter()
    crash_expected: dict = {}
    for popen in popens:
        token = popen.get("token")
        launches[token] += 1
        if popen.get("expect_crash"):
            crash_expected[token] = True
    installed = [rec for rec in records if rec.get("event") == "installed"]
    witnessed: Counter = Counter()
    for rec in installed:
        witnessed[rec.get("token")] += 1
    failures = []
    for token in sorted(launches, key=repr):
        if launches[token] > witnessed.get(token, 0):
            failures.append(
                f"token {token!r}: {launches[token]} python launches but "
                f"only {witnessed.get(token, 0)} installed witnesses")
    for rec in records:
        if rec.get("event") == "install_failed":
            failures.append(
                f"install_failed for token {rec.get('token')!r} "
                f"(pid {rec.get('pid')}): {rec.get('error')}")
    completed_pids = {rec.get("pid") for rec in records
                      if rec.get("event") == "completed"}
    for rec in installed:
        if rec.get("pid") not in completed_pids and not crash_expected.get(
                rec.get("token"), False):
            failures.append(
                f"installed pid {rec.get('pid')} (token "
                f"{rec.get('token')!r}) has no completed record")
    for rec in records:
        if rec.get("event") == "completed" and rec.get("capture_ok") is False:
            failures.append(
                f"completed pid {rec.get('pid')} (token "
                f"{rec.get('token')!r}) reports capture_ok: false")
    return failures


def fixture_6_python_child(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    # With PYTHONPATH: the child's write is logged.
    root = _build_root(tmp_path, "a2-f6-with")
    target = root / "work" / "inbox" / "child-with.md"
    log_path = tmp_path / "a2-f6-with.log"
    token = _fresh_token()
    arch_audit_hook.install(str(log_path))
    try:
        proc = subprocess.run(
            [sys.executable, "-c",
             f"from pathlib import Path; Path({str(target)!r}).write_text('from child\\n')"],
            capture_output=True, text=True,
            env=_child_env(log_path, token), timeout=120)
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    assert proc.returncode == 0, f"child failed: {proc.stderr[-500:]}"
    assert target.is_file()
    records = _read_log(log_path)
    assert witness_failures(records) == [], (
        f"python child needs a full witness: {witness_failures(records)}")
    child_writes = [rec for rec in _canonical_records(records, root)
                    if rec.get("event") == "open"]
    assert child_writes, "the child's write must be logged"
    # Without PYTHONPATH: the scenario fails for the missing witness.
    root2 = _build_root(tmp_path, "a2-f6-without")
    target2 = root2 / "work" / "inbox" / "child-without.md"
    log2 = tmp_path / "a2-f6-without.log"
    token2 = _fresh_token()
    arch_audit_hook.install(str(log2))
    try:
        proc2 = subprocess.run(
            [sys.executable, "-c",
             f"from pathlib import Path; Path({str(target2)!r}).write_text('from child\\n')"],
            capture_output=True, text=True,
            env=_child_env(log2, token2, with_site=False), timeout=120)
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    assert proc2.returncode == 0, f"child failed: {proc2.stderr[-500:]}"
    records2 = _read_log(log2)
    assert witness_failures(records2), (
        "without PYTHONPATH the missing witness must fail the scenario")


def fixture_7_non_python_child(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f7")
    target = root / "work" / "inbox" / "shell-write.md"
    before = arch_effects.capture_tree(root)
    proc = subprocess.run(
        ["/bin/sh", "-c", f"printf x > {str(target)}"],
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"shell child failed: {proc.stderr[-500:]}"
    after = arch_effects.capture_tree(root)
    violations = arch_effects.reconcile(before, after, [])
    assert violations, "oracle must report the non-python child's write"


def fixture_8_mixed_children(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f8")
    transient = root / "knowledge" / "transient.md"
    before = arch_effects.capture_tree(root)
    log_path = tmp_path / "a2-f8.log"
    token = _fresh_token()
    arch_audit_hook.install(str(log_path))
    try:
        proc1 = subprocess.run(
            [sys.executable, "-c", "pass"],
            capture_output=True, text=True,
            env=_child_env(log_path, token), timeout=120)
        assert proc1.returncode == 0, (
            f"instrumented child failed: {proc1.stderr[-500:]}")
        proc2 = subprocess.run(
            [sys.executable, "-c",
             f"from pathlib import Path; p = Path({str(transient)!r}); "
             "p.write_text('transient\\n'); p.unlink()"],
            capture_output=True, text=True,
            env=_child_env(log_path, token, with_site=False), timeout=120)
        assert proc2.returncode == 0, (
            f"uninstrumented child failed: {proc2.stderr[-500:]}")
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    after = arch_effects.capture_tree(root)
    assert not transient.exists()
    assert arch_effects.reconcile(before, after, []) == [], (
        "the oracle sees no violation: the final tree is unchanged")
    failures = witness_failures(_read_log(log_path))
    assert any("launch" in failure for failure in failures), (
        f"witness_failures must report the uncovered launch: {failures}")


def fixture_9_failed_installation(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    log_path = tmp_path / "a2-f9.log"
    token = _fresh_token()
    arch_audit_hook.install(str(log_path))
    try:
        env = _child_env(log_path, token)
        env["LOS_ARCH_AUDIT_FORCE_FAIL"] = "1"
        proc = subprocess.run(
            [sys.executable, "-c", "pass"],
            capture_output=True, text=True, env=env, timeout=120)
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    assert proc.returncode == 0, (
        f"the child runs its program anyway: {proc.stderr[-500:]}")
    records = _read_log(log_path)
    assert [rec for rec in records
            if rec.get("event") == "install_failed"], (
        "the failed installation must leave an install_failed record")
    assert [rec for rec in records
            if rec.get("event") == "installed"] == [], (
        "the failed installation must leave no installed witness")
    failures = witness_failures(records)
    assert any("install_failed" in failure for failure in failures), (
        f"witness_failures must report install_failed: {failures}")
    assert any("installed" in failure for failure in failures), (
        f"witness_failures must report the missing installed: {failures}")


def fixture_10_logging_failure(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    # (a) install() validates before activating.
    arch_audit_hook.uninstall()
    try:
        arch_audit_hook.install(str(tmp_path))
    except arch_audit_hook.AuditCaptureError:
        pass
    else:
        raise AssertionError(
            "install() given a directory must raise AuditCaptureError")
    assert arch_audit_hook._ACTIVE_LOG is None, (
        "a failed install activates nothing")
    # (b) a mid-run logging failure is sticky and fatal.
    root = _build_root(tmp_path, "a2-f10")
    transient = root / "knowledge" / "transient.md"
    log_path = tmp_path / "a2-f10.log"
    arch_audit_hook.install(str(log_path))
    try:
        # The replacement syscalls run with this thread's hook suppressed:
        # the live hook would recreate the log file on the mkdir audit
        # event and mkdir would fail with FileExistsError.
        arch_audit_hook._STATE.active = True
        try:
            log_path.unlink()
            log_path.mkdir()
        finally:
            arch_audit_hook._STATE.active = False
        transient.write_text("transient\n", encoding="utf-8")
        transient.unlink()
    finally:
        arch_audit_hook.uninstall()
    try:
        arch_audit_hook.assert_capture_ok()
    except arch_audit_hook.AuditCaptureError:
        pass
    else:
        raise AssertionError(
            "assert_capture_ok() must fail after the log was replaced")


def fixture_11_concurrent_threads(tmp_path: Path) -> None:
    import learning_os.transactions as transactions

    tmp_path = Path(tmp_path)
    root = _build_root(tmp_path, "a2-f11")
    transient = root / "knowledge" / "transient.md"
    scratch_a = tmp_path / "a2-f11-a.txt"
    log_path = tmp_path / "a2-f11.log"
    entered = threading.Event()
    gate = threading.Event()
    real_phase = transactions.current_engine_phase
    holder: dict = {}

    def _gated_phase():
        if threading.current_thread() is holder.get("a"):
            entered.set()
            assert gate.wait(timeout=30), "thread A was never released"
        return real_phase()

    transactions.current_engine_phase = _gated_phase
    try:
        arch_audit_hook.install(str(log_path))
        try:
            try:
                thread_a = threading.Thread(
                    target=scratch_a.write_text, args=("a\n",))
                holder["a"] = thread_a
                thread_a.start()
                assert entered.wait(timeout=30), (
                    "thread A never reached its phase lookup")
                thread_b = threading.Thread(
                    target=lambda: (transient.write_text("transient\n"),
                                    transient.unlink()))
                thread_b.start()
                thread_b.join(timeout=30)
                assert not thread_b.is_alive(), "thread B hung"
            finally:
                gate.set()
            thread_a.join(timeout=30)
            assert not thread_a.is_alive(), "thread A hung"
        finally:
            arch_audit_hook.uninstall()
    finally:
        transactions.current_engine_phase = real_phase
    records = _read_log(log_path)
    transient_abs = transient.resolve().as_posix()
    b_hits = []
    for rec in records:
        for path in rec.get("paths") or []:
            if not isinstance(path, str) or not os.path.isabs(path):
                continue
            try:
                if Path(path).resolve().as_posix() == transient_abs:
                    b_hits.append(rec)
            except OSError:
                continue
    assert b_hits, (
        "thread B's events must be in the log while A is inside the hook")


FIXTURES = {
    "fixture_1_query_escalated_recovery": fixture_1_query_escalated_recovery,
    "fixture_10_logging_failure": fixture_10_logging_failure,
    "fixture_11_concurrent_threads": fixture_11_concurrent_threads,
    "fixture_2_unproven_restore": fixture_2_unproven_restore,
    "fixture_3_rogue_callbacks": fixture_3_rogue_callbacks,
    "fixture_4_descriptor_and_dir_fd": fixture_4_descriptor_and_dir_fd,
    "fixture_5_rename_into_canonical": fixture_5_rename_into_canonical,
    "fixture_6_python_child": fixture_6_python_child,
    "fixture_7_non_python_child": fixture_7_non_python_child,
    "fixture_8_mixed_children": fixture_8_mixed_children,
    "fixture_9_failed_installation": fixture_9_failed_installation,
}
