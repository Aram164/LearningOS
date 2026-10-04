"""Seven A2 prototype-gate fixtures (PLAN step 0.2).

One function per fixture, each asserting exactly its expected oracle and
hook outcome. ``test_arch_writes.py`` runs them.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
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
    if not log_path.is_file():
        return []
    records = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


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
    import learning_os.commands.support as support

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
        with support._operator_lock(root, shared=True):
            pass
    finally:
        arch_audit_hook.uninstall()
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


def _witness_gaps(records: list[dict]) -> list[dict]:
    popens = [rec for rec in records
              if rec.get("event") == "subprocess.Popen"
              and _is_python_argv(rec.get("argv") or [])]
    witnesses = [rec for rec in records if rec.get("event") == "installed"]
    gaps = []
    for popen in popens:
        if not any(witness.get("pid") != popen.get("pid")
                   for witness in witnesses):
            gaps.append(popen)
    return gaps


def fixture_6_python_child(tmp_path: Path) -> None:
    tmp_path = Path(tmp_path)
    # With PYTHONPATH: the child's write is logged.
    root = _build_root(tmp_path, "a2-f6-with")
    target = root / "work" / "inbox" / "child-with.md"
    log_path = tmp_path / "a2-f6-with.log"
    arch_audit_hook.install(str(log_path))
    try:
        env = dict(os.environ)
        env["LOS_ARCH_AUDIT_LOG"] = str(log_path)
        env["PYTHONPATH"] = str(_ARCH_SITE) + os.pathsep + env.get(
            "PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-c",
             f"from pathlib import Path; Path({str(target)!r}).write_text('from child\\n')"],
            capture_output=True, text=True, env=env, timeout=120)
    finally:
        arch_audit_hook.uninstall()
    assert proc.returncode == 0, f"child failed: {proc.stderr[-500:]}"
    assert target.is_file()
    records = _read_log(log_path)
    assert _witness_gaps(records) == [], "python child needs a witness"
    child_writes = [rec for rec in _canonical_records(records, root)
                    if rec.get("event") == "open"]
    assert child_writes, "the child's write must be logged"
    # Without PYTHONPATH: the scenario fails for the missing witness.
    root2 = _build_root(tmp_path, "a2-f6-without")
    target2 = root2 / "work" / "inbox" / "child-without.md"
    log2 = tmp_path / "a2-f6-without.log"
    arch_audit_hook.install(str(log2))
    try:
        env2 = dict(os.environ)
        env2["LOS_ARCH_AUDIT_LOG"] = str(log2)
        env2.pop("PYTHONPATH", None)
        proc2 = subprocess.run(
            [sys.executable, "-c",
             f"from pathlib import Path; Path({str(target2)!r}).write_text('from child\\n')"],
            capture_output=True, text=True, env=env2, timeout=120)
    finally:
        arch_audit_hook.uninstall()
    assert proc2.returncode == 0, f"child failed: {proc2.stderr[-500:]}"
    records2 = _read_log(log2)
    assert _witness_gaps(records2), (
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


FIXTURES = {
    "fixture_1_query_escalated_recovery": fixture_1_query_escalated_recovery,
    "fixture_2_unproven_restore": fixture_2_unproven_restore,
    "fixture_3_rogue_callbacks": fixture_3_rogue_callbacks,
    "fixture_4_descriptor_and_dir_fd": fixture_4_descriptor_and_dir_fd,
    "fixture_5_rename_into_canonical": fixture_5_rename_into_canonical,
    "fixture_6_python_child": fixture_6_python_child,
    "fixture_7_non_python_child": fixture_7_non_python_child,
}
