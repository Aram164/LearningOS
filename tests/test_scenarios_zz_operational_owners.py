"""A19: one owner per durable operational destination (SPEC §3.6).

Reads every audit log the session's scenario and procedure cases
appended to ``LOS_ARCH_AUDIT_DIR`` and proves each durable write
under ``operations/`` (or the session state dir) came through its
declared owner: the innermost writing module for ``sink: module``,
or an ``engine:apply`` phase backed by a same-run receipt naming a
declared capability for that destination. Unresolved events,
unknown destinations and missing or corrupt witnesses fail closed.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
OWNERS_PATH = TESTS / "architecture" / "operational-owners.yaml"
RATCHETS_PATH = TESTS / "architecture" / "ratchets.yaml"
CASES_DIR = TESTS / "scenarios" / "cases"
CHECK_ID = "A19-owners"
FIX = "Write durable operational state only through its declared owner (PLAN A19)."

_TEMP_BASENAME = re.compile(r"^\.(.+)\.tmp(-\d+)?$")
_WRITE_EVENTS = frozenset({
    "open", "os.rename", "os.remove", "os.unlink", "os.rmdir",
    "os.link", "os.symlink", "os.write", "io.open", "os.truncate",
    "shutil.copyfile", "shutil.move", "shutil.rmtree",
})


def _load_owners() -> dict:
    return yaml.safe_load(OWNERS_PATH.read_text(encoding="utf-8"))


def _recorded_signatures() -> set[str]:
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    return {entry["signature"]
            for entry in data["checks"].get(CHECK_ID, [])}


def _relative_destination(raw: str, root: str | None = None,
                          state_dir: str | None = None, anchored: bool = False) -> str | None:
    """The operational-relative path for one audited path, or None."""
    path = raw.replace(os.sep, "/")
    if root is not None:
        bound = Path(root).resolve()
        lexical = Path(raw).resolve()
        if state_dir:
            try:
                state_rel = lexical.relative_to(Path(state_dir).resolve()).as_posix()
            except ValueError:
                pass
            else:
                token = hashlib.sha256(str(bound).encode("utf-8")).hexdigest()[:16]
                if anchored or lexical.name.lstrip(".").startswith(f"learningos-{token}"):
                    return f"<STATE>/{state_rel}"
        try:
            rel = lexical.relative_to(bound).as_posix()
        except ValueError:
            token = hashlib.sha256(str(bound).encode("utf-8")).hexdigest()[:16]
            if lexical.name.startswith(f"learningos-{token}-") and lexical.name.endswith("-touched.json"):
                return f"<STATE>/{lexical.name}"
            return None
        return rel if rel.startswith("operations/") else None
    if "/operations/" in path:
        return "operations/" + path.split("/operations/", 1)[1]
    name = path.rsplit("/", 1)[-1]
    if re.fullmatch(r"learningos-.+-touched\.json", name):
        return f"<STATE>/{name}"
    if path.startswith("operations/"):
        return path
    return None


def _destinations(record: dict, root: str | None = None,
                  state_dir: str | None = None, anchored: bool = False) -> list[str]:
    """Normalized destinations for one record (SPEC §3.6 rules)."""
    event = record.get("event")
    if event == "os.mkdir" or event not in _WRITE_EVENTS:
        return []
    paths = [p for p in record.get("paths", []) if isinstance(p, str)]
    if event in ("os.rename", "os.link", "os.symlink", "shutil.copyfile", "shutil.move") and len(paths) >= 2:
        paths = paths[1:]
    destinations = []
    for raw in paths:
        rel = _relative_destination(raw, root, state_dir, anchored)
        if rel is None:
            continue
        head, _, name = rel.rpartition("/")
        match = _TEMP_BASENAME.match(name)
        if match:
            rel = f"{head}/{match.group(1)}" if head else match.group(1)
        destinations.append(rel)
    return destinations


def _receipts_for_run(root: str | None) -> list[tuple[str, set[str]]]:
    """(capability, writes) per transaction receipt in one world."""
    if not root:
        return []
    tx_dir = Path(root) / "operations" / "transactions"
    if not tx_dir.is_dir():
        return []
    receipts = []
    for path in sorted(tx_dir.glob("transaction-*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        writes = {str(row["path"]) for row in data.get("writes", [])
                  if isinstance(row, dict) and row.get("path")}
        receipts.append((str(data.get("capability")), writes))
    return receipts


def _owner_satisfied(entry: dict, record: dict, rel: str,
                     receipts: list[tuple[str, set[str]]]) -> bool:
    import arch_audit_hook

    writer = record.get("writer")
    if writer in arch_audit_hook.MECHANICAL_HELPERS:
        semantic_owner = record.get("delegated_owner")
        if semantic_owner not in arch_audit_hook.MECHANICAL_HELPERS[writer]:
            return False
        writer = semantic_owner
    if entry["sink"] == "module":
        if not isinstance(writer, str) or not writer:
            return False
        owner = entry["owner"]
        return writer == owner or writer.startswith(owner + ".")
    # engine:apply: apply phase plus a same-run receipt for this path
    # naming one of the declared capabilities.
    if record.get("phase") != "apply":
        return False
    if writer != "learning_os.store.transactions":
        return False
    declared = set(entry.get("capabilities", []))
    return any(capability in declared and rel in writes
               for capability, writes in receipts)


def _violations_in_log(log_path: Path, owners: dict) -> dict[str, list[str]]:
    """Check retained, root-bound evidence; unknown evidence fails closed."""
    from arch_writes_fixtures import witness_failures

    violations: dict[str, list[str]] = {}

    def add(signature: str, evidence: str) -> None:
        violations.setdefault(signature, []).append(evidence)

    try:
        records = [json.loads(line) for line in
                   log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not records or not all(isinstance(row, dict) for row in records):
            raise ValueError("empty or non-object audit")
        header = records[0]
        if header.get("event") != "case" or not header.get("operation") or not header.get("case"):
            raise ValueError("missing case identity")
    except (OSError, ValueError) as exc:
        add(f"{log_path.name}::corrupt", f"{log_path}: {exc}")
        return violations
    if not any(r.get("event") == "installed" for r in records):
        add(f"{log_path.name}::missing-witness", str(log_path))
        return violations
    for problem in witness_failures(records, allow_isolated=True):
        add(f"{log_path.name}::bad-witness", problem)

    # Proof is read at child completion from newly created receipt bytes.
    # It remains available after Scrut removes its temporary fixture.
    receipts: dict[tuple[int, str], list[tuple[str, set[str]]]] = {}
    for row in records:
        if row.get("event") != "completed" or not row.get("root"):
            continue
        key = (row.get("pid"), row["root"])
        proofs = receipts.setdefault(key, [])
        try:
            for proof in row.get("new_receipts", []):
                text = proof["text"]
                if hashlib.sha256(text.encode("utf-8")).hexdigest() != proof["sha256"]:
                    raise ValueError("receipt bytes do not match their digest")
                data = yaml.safe_load(text)
                if not isinstance(data, dict) or not isinstance(data.get("writes"), list):
                    raise ValueError("malformed receipt proof")
                proofs.append((str(data.get("capability")),
                               {str(w["path"]) for w in data["writes"] if isinstance(w, dict) and w.get("path")}))
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            add(f"{log_path.name}::bad-receipt", str(exc))

    worlds = {}
    excluded = [row["glob"] for row in owners.get("excluded", [])]
    entries = owners.get("entries", [])
    for record in records:
        event = record.get("event")
        pid = record.get("pid")
        if event == "installed":
            worlds[pid] = record
            continue
        if event not in _WRITE_EVENTS:
            continue
        if event == "open" and record.get("mode") == "r":
            continue
        binding = worlds.get(pid)
        if binding is None:
            # The hook's own append-open precedes the installed witness.
            raw_paths = record.get("paths", [])
            if raw_paths and all(isinstance(p, str) and os.path.isabs(p) and _relative_destination(p) is None for p in raw_paths):
                continue
            add(f"{log_path.name}::unbound-writer", str(record))
            continue
        root = binding.get("root")
        if root is None:
            argv = binding.get("argv", [])
            if argv and Path(argv[0]).name == "los-fixture":
                continue  # explicitly identified fixture construction
            # No world can establish ownership of an unresolved descriptor.
            resolved = record.get("resolved_paths", record.get("paths", []))
            if not resolved or any(not isinstance(p, str) or not os.path.isabs(p) for p in resolved):
                add(f"{log_path.name}::unbound-world", str(record))
                continue
            # A read-only helper can have no world; an unresolved write cannot.
            if any(_relative_destination(p) for p in record.get("paths", []) if isinstance(p, str)):
                add(f"{log_path.name}::unbound-world", str(record))
            continue
        paths = record.get("resolved_paths", record.get("paths", []))
        record = dict(record, paths=paths)
        if record.get("event") in ("os.rename", "os.link", "os.symlink", "shutil.copyfile", "shutil.move"):
            check_paths = paths[-1:]
        else:
            check_paths = paths
        if not check_paths or any(not isinstance(p, str) or not os.path.isabs(p) for p in check_paths):
            add(f"{log_path.name}::unresolved", str(record))
            continue
        for rel in _destinations(record, root, binding.get("state_dir"), binding.get("state_anchored", False)):
            if any(fnmatch.fnmatch(rel, glob) for glob in excluded):
                continue
            matched = [e for e in entries if fnmatch.fnmatch(rel, e["glob"])]
            same_run = receipts.get((pid, root), [])
            if any(_owner_satisfied(e, record, rel, same_run) for e in matched):
                continue
            writer = record.get("writer") or "unknown"
            evidence = (f"{log_path.name}: {rel} writer={writer} "
                        f"at {record.get('writer_file')}:{record.get('writer_line')} "
                        f"phase={record.get('phase')}")
            if matched:
                for entry in matched:
                    who = "+".join(entry.get("capabilities", [])) if entry["sink"] == "engine:apply" else writer
                    add(f"{entry['glob']}::{who}", evidence)
            else:
                add(f"{rel}::undeclared", evidence)
    return violations


def _population_violations(audit_dir: Path) -> dict[str, list[str]]:
    owners = _load_owners()
    merged: dict[str, list[str]] = {}
    for log_path in sorted(audit_dir.glob("*.jsonl")):
        for signature, evidence in _violations_in_log(
                log_path, owners).items():
            merged.setdefault(signature, []).extend(evidence)
    return merged


def _audit_dir() -> Path | None:
    raw = os.environ.get("LOS_ARCH_AUDIT_DIR")
    return Path(raw) if raw else None


def test_operational_owners_population():
    """Every witnessed operational write has its declared owner."""
    audit_dir = _audit_dir()
    logs = sorted(audit_dir.glob("*.jsonl")) if audit_dir else []
    if not logs:
        if os.environ.get("CI"):
            raise AssertionError(
                f"A19: CI requires audit witnesses, found none — {FIX}")
        pytest.skip("A19: no audit logs this run (local partial run)")
    if os.environ.get("CI"):
        cases_file = audit_dir / "cases.txt"
        witnessed = set(cases_file.read_text(
            encoding="utf-8").split()) if cases_file.is_file() else set()
        expected = set()
        import scenario_harness as harness

        for path in sorted(CASES_DIR.glob("*.yaml")):
            doc = harness.load_case_file(path)
            for case in doc.get("cases", []):
                expected.add(f"{path.stem}__{case['id']}")
        index = yaml.safe_load(
            (ROOT / "system/procedures/INDEX.yaml").read_text(encoding="utf-8"))
        for row in index.get("sections", []):
            if row.get("class") == "procedure" and row.get("transcript"):
                expected.add(f"procedure__{Path(row['transcript']).stem}")
        # cases.txt is an index, never proof that the corresponding log exists.
        captured = set()
        for log in logs:
            header = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            captured.add(f"{header.get('operation')}__{header.get('case')}")
        witnessed &= captured
        missing = expected - witnessed
        assert not missing, (
            f"A19: CI population misses witnesses: "
            f"{sorted(missing)[:10]} — {FIX}")
    violations = _population_violations(audit_dir)
    recorded = _recorded_signatures()
    unrecorded = set(violations) - recorded
    assert not unrecorded, (
        "A19 unrecorded violations:\n" + "\n".join(
            f"{sig}: {violations[sig][0]}" for sig in sorted(unrecorded))
        + f" — {FIX}")
    stale = recorded - set(violations)
    assert not stale, (
        f"A19 recorded exceptions no longer occur, remove them: "
        f"{sorted(stale)} — {FIX}")


# --- synthetic controls (fabricated logs; no scenario world needed) ---

def _write_log(tmp_path: Path, name: str, records: list[dict],
               root: Path) -> Path:
    log = tmp_path / f"{name}.jsonl"
    import hashlib

    header = {"event": "case", "operation": "control", "case": name,
              "root": str(root)}
    installed = {"event": "installed", "pid": 1, "ppid": 0,
                 "token": "control", "argv": ["control", "--root", str(root)],
                 "root": str(root), "state_dir": str(root / ".git/learningos"),
                 "state_anchored": True}
    proofs = []
    for path in (root / "operations/transactions").glob("transaction-*.yaml"):
        raw = path.read_bytes()
        proofs.append({"path": path.name, "text": raw.decode(),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    completed = {"event": "completed", "pid": 1, "token": "control",
                 "root": str(root), "capture_ok": True, "new_receipts": proofs}
    bound = []
    for row in records:
        item = dict(row, pid=1)
        if "paths" in item:
            item["paths"] = [str(root) + p[2:] if isinstance(p, str) and p.startswith("/w/") else p for p in item["paths"]]
        bound.append(item)
    log.write_text("\n".join(json.dumps(row) for row in
                             [header, installed, *bound, completed]) + "\n",
                   encoding="utf-8")
    return log


def _write_record(path: str, writer: str | None, phase=None) -> dict:
    return {"event": "open", "paths": [path], "mode": "w",
            "phase": phase, "writer": writer,
            "writer_file": "/repo/tools/learning_os/example.py",
            "writer_line": 42}


def _signatures(tmp_path: Path, records: list[dict],
                receipts: dict | None = None) -> set[str]:
    import uuid

    world = tmp_path / f"world-{uuid.uuid4().hex[:8]}"
    (world / "operations" / "transactions").mkdir(parents=True)
    if receipts:
        (world / "operations" / "transactions"
         / "transaction-20260101-000000-001.yaml").write_text(
            yaml.safe_dump(receipts), encoding="utf-8")
    log = _write_log(tmp_path, "control", records, world)
    return set(_violations_in_log(log, _load_owners()))


def test_rogue_writer_is_a_violation(tmp_path):
    sigs = _signatures(tmp_path, [_write_record(
        "/w/operations/transactions/revisions.yaml",
        "learning_os.rogue")])
    assert sigs == {
        "operations/transactions/revisions.yaml::learning_os.rogue"}


def test_undeclared_destination_fails_closed(tmp_path):
    sigs = _signatures(tmp_path, [_write_record(
        "/w/operations/new-state.yaml", "learning_os.store.transactions")])
    assert sigs == {"operations/new-state.yaml::undeclared"}


def test_module_owner_and_temp_sibling_pass(tmp_path):
    assert _signatures(tmp_path, [
        _write_record("/w/operations/transactions/revisions.yaml",
                      "learning_os.store.transactions.engine"),
        _write_record(
            "/w/operations/transactions/.revisions.yaml.tmp-123",
            "learning_os.store.transactions.engine"),
    ]) == set()


def test_engine_apply_needs_declared_capability_receipt(tmp_path):
    path = "/w/operations/transactions/lineage.yaml"
    good = {"capability": "lineage.restamp",
            "writes": [{"path": "operations/transactions/lineage.yaml"}]}
    assert _signatures(tmp_path, [
        _write_record(path, "learning_os.store.transactions", phase="apply"),
    ], receipts=good) == set()
    wrong = {"capability": "goal.decision.record",
             "writes": [{"path": "operations/transactions/lineage.yaml"}]}
    sigs = _signatures(tmp_path, [
        _write_record(path, "learning_os.store.transactions", phase="apply"),
    ], receipts=wrong)
    assert len(sigs) == 1 and "lineage.yaml" in next(iter(sigs))


def test_engine_phase_cannot_authorize_a_hidden_callback_writer(tmp_path):
    proof = {"capability": "lineage.restamp",
             "writes": [{"path": "operations/transactions/lineage.yaml"}]}
    assert _signatures(tmp_path, [_write_record(
        "/w/operations/transactions/lineage.yaml", "learning_os.app.handlers.plan",
        phase="apply")], receipts=proof)


def test_mechanical_delegation_is_bounded_to_the_immediate_caller(tmp_path):
    import arch_audit_hook

    helper = "learning_os.store.durable_fs"
    engine = "learning_os.store.transactions"
    frames = [(helper, "helper.py", 1), (helper, "helper.py", 2), (engine, "engine.py", 3)]
    assert arch_audit_hook.delegated_owner(frames) == engine
    frames.insert(2, ("learning_os.app.handlers.plan", "callback.py", 4))
    assert arch_audit_hook.delegated_owner(frames) is None
    record = _write_record("/w/operations/transactions/revisions.yaml", helper, phase="apply")
    assert _signatures(tmp_path, [record])
    assert not _signatures(tmp_path, [dict(record, delegated_owner=engine)])


def test_helper_declaration_matches_the_hook():
    import arch_audit_hook

    assert {row["module"]: frozenset(row["callers"]) for row in _load_owners()["io_helpers"]} == (
        arch_audit_hook.MECHANICAL_HELPERS)


def test_source_revision_is_a_declared_lineage_writer(tmp_path):
    proof = {"capability": "source.record.revise",
             "writes": [{"path": "operations/transactions/lineage.yaml"}]}
    assert not _signatures(tmp_path, [_write_record(
        "/w/operations/transactions/lineage.yaml", "learning_os.store.transactions",
        phase="apply")], receipts=proof)


def test_missing_writer_and_excluded_and_rename(tmp_path):
    assert _signatures(tmp_path, [
        _write_record("/w/operations/transactions/revisions.yaml", None),
    ]) != set()
    assert _signatures(tmp_path, [
        _write_record("/w/operations/diagnostics/traces.jsonl",
                      "learning_os.rogue"),
        {"event": "os.rename",
         "paths": ["/w/operations/ai-actions/.x.tmp",
                   "/w/operations/ai-actions/x.yaml"],
         "mode": None, "phase": None,
         "writer": "learning_os.store.ai_actions.storage",
         "writer_file": "/repo/tools/x.py", "writer_line": 7},
        {"event": "os.mkdir",
         "paths": ["/w/operations/transactions/.inflight"],
         "mode": None, "phase": None, "writer": "learning_os.rogue",
         "writer_file": "/repo/tools/x.py", "writer_line": 7},
    ]) == set()


def test_corrupt_log_fails_closed(tmp_path):
    world = tmp_path / "world"
    world.mkdir()
    log = tmp_path / "bad.jsonl"
    log.write_text(
        '{"event": "case", "root": "' + str(world) + '"}\nnot json\n',
        encoding="utf-8")
    assert _violations_in_log(log, _load_owners()) != {}


def test_shadow_world_writes_do_not_become_durable_owners(tmp_path):
    assert _signatures(tmp_path, [_write_record(
        "/disposable/shadow/operations/new-state.yaml", "learning_os.app.check")]) == set()


def test_truncate_and_copy_destinations_are_checked(tmp_path):
    assert _signatures(tmp_path, [{"event": "os.truncate", "paths": ["/w/operations/new-state.yaml"],
                                  "writer": "learning_os.rogue"}]) == {"operations/new-state.yaml::undeclared"}
    assert _signatures(tmp_path, [{"event": "shutil.copyfile", "paths": ["/other/read.yaml", "/w/operations/new-state.yaml"],
                                  "writer": "learning_os.rogue"}]) == {"operations/new-state.yaml::undeclared"}


def test_header_only_and_non_object_audits_fail_closed(tmp_path):
    for text in ('{"event":"case","operation":"x","case":"y"}\n', '[]\n'):
        log = tmp_path / "bad.jsonl"
        log.write_text(text)
        assert _violations_in_log(log, _load_owners())


def test_preexisting_receipt_cannot_claim_an_engine_write(tmp_path):
    root = tmp_path / "world"
    root.mkdir()
    log = _write_log(tmp_path, "baseline", [_write_record(
        "/w/operations/transactions/lineage.yaml", "learning_os.store.transactions", phase="apply")], root)
    assert _violations_in_log(log, _load_owners())


def test_unresolved_write_fails_closed(tmp_path):
    assert _signatures(tmp_path, [{"event": "open", "paths": [9], "mode": "w", "writer": "learning_os.store.transactions"}])


def test_child_captures_only_new_receipt_bytes(tmp_path):
    import subprocess
    import sys

    root = tmp_path / "world"
    tx = root / "operations/transactions"
    tx.mkdir(parents=True)
    baseline = tx / "transaction-20260101-000000-001.yaml"
    baseline.write_text("capability: lineage.restamp\nwrites: []\n")
    log = tmp_path / "child.jsonl"
    env = dict(os.environ)
    env.update(LOS_FX=str(root), LOS_ARCH_AUDIT_LOG=str(log),
               LOS_ARCH_LAUNCH_TOKEN="receipt-control",
               PYTHONPATH=str(Path(__file__).parent / "arch_site") + os.pathsep
               + str(Path(__file__).parent) + os.pathsep + env.get("PYTHONPATH", ""))
    created = tx / "transaction-20260101-000000-002.yaml"
    script = "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('capability: lineage.restamp\\nwrites: []\\n')"
    child = subprocess.run([sys.executable, "-c", script, str(created)], env=env,
                           capture_output=True, text=True)
    assert child.returncode == 0, child.stderr
    records = [json.loads(line) for line in log.read_text().splitlines()]
    installed = next(row for row in records if row.get("event") == "installed")
    completed = next(row for row in records if row.get("event") == "completed")
    assert installed["root"] == str(root.resolve())
    assert installed["receipts_before"] == [baseline.name]
    assert [proof["path"] for proof in completed["new_receipts"]] == [created.name]
    proof = completed["new_receipts"][0]
    assert proof["text"].encode() == created.read_bytes()
    assert proof["sha256"] == hashlib.sha256(created.read_bytes()).hexdigest()


def test_repeated_case_audits_are_preserved(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from scenario_harness import persist_case_audit
    from test_procedures import _persist_procedure_audit

    audit = tmp_path / "audits"
    monkeypatch.setenv("LOS_ARCH_AUDIT_DIR", str(audit))
    log = tmp_path / "source.jsonl"
    log.write_text('{"event":"installed"}\n')
    ctx = SimpleNamespace(operation="same", case_id="case", root=tmp_path,
                          log_path=log)
    persist_case_audit(ctx)
    persist_case_audit(ctx)
    _persist_procedure_audit("same", log)
    _persist_procedure_audit("same", log)
    assert len(list(audit.glob("*.jsonl"))) == 4
    log.unlink()
    with pytest.raises(FileNotFoundError):
        persist_case_audit(ctx)


def test_bad_receipt_digest_fails_closed(tmp_path):
    root = tmp_path / "world"
    (root / "operations/transactions").mkdir(parents=True)
    (root / "operations/transactions/transaction-20260101-000000-001.yaml").write_text(
        "capability: lineage.restamp\nwrites: [{path: operations/transactions/lineage.yaml}]\n")
    log = _write_log(tmp_path, "wrong-digest", [], root)
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    rows[-1]["new_receipts"][0]["sha256"] = "0" * 64
    log.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    assert any("bad-receipt" in sig for sig in _violations_in_log(log, _load_owners()))



def test_unknown_state_destination_fails_closed(tmp_path):
    assert _signatures(tmp_path, [_write_record(
        "/w/.git/learningos/new-state.yaml", "learning_os.store.session_ledger")]) == {"<STATE>/new-state.yaml::undeclared"}


def test_unbound_world_cannot_credit_an_unresolved_descriptor(tmp_path):
    root = tmp_path / "world"
    root.mkdir()
    log = _write_log(tmp_path, "unbound", [{"event": "open", "paths": [9],
                     "resolved_paths": [None], "mode": "w", "writer": "learning_os.store.transactions"}], root)
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    rows[1]["root"] = None
    rows[1]["argv"] = ["-c"]
    log.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    assert _violations_in_log(log, _load_owners())


def test_ai_storage_owner_rejects_application_or_rogue_writers(tmp_path):
    path = "/w/operations/ai-actions/requests/request-demo/request.yaml"
    for owner in ("learning_os.store.ai_actions.storage", "learning_os.store.ai_actions.support"):
        assert _signatures(tmp_path, [_write_record(path, owner)]) == set()
    for rogue in ("learning_os.app.ai_actions.service", "learning_os.rogue"):
        assert _signatures(tmp_path, [_write_record(path, rogue)]) != set()
