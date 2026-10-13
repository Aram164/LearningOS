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
    "os.link", "os.symlink", "os.write", "io.open",
})


def _load_owners() -> dict:
    return yaml.safe_load(OWNERS_PATH.read_text(encoding="utf-8"))


def _recorded_signatures() -> set[str]:
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    return {entry["signature"]
            for entry in data["checks"].get(CHECK_ID, [])}


def _relative_destination(raw: str) -> str | None:
    """The operational-relative path for one audited path, or None."""
    path = raw.replace(os.sep, "/")
    if "/operations/" in path:
        return "operations/" + path.split("/operations/", 1)[1]
    name = path.rsplit("/", 1)[-1]
    if re.fullmatch(r"learningos-.+-touched\.json", name):
        return f"<STATE>/{name}"
    if path.startswith("operations/"):
        return path
    return None


def _destinations(record: dict) -> list[str]:
    """Normalized destinations for one record (SPEC §3.6 rules)."""
    event = record.get("event")
    if event == "os.mkdir" or event not in _WRITE_EVENTS:
        return []
    paths = [p for p in record.get("paths", []) if isinstance(p, str)]
    if event == "os.rename" and len(paths) >= 2:
        paths = paths[1:]
    destinations = []
    for raw in paths:
        rel = _relative_destination(raw)
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
    if entry["sink"] == "module":
        writer = record.get("writer")
        if not isinstance(writer, str) or not writer:
            return False
        owner = entry["owner"]
        return writer == owner or writer.startswith(owner + ".")
    # engine:apply: apply phase plus a same-run receipt for this path
    # naming one of the declared capabilities.
    if record.get("phase") != "apply":
        return False
    declared = set(entry.get("capabilities", []))
    return any(capability in declared and rel in writes
               for capability, writes in receipts)


def _violations_in_log(log_path: Path, owners: dict) -> dict[str, list[str]]:
    """Signature -> evidence lines for one audit log (fail closed)."""
    violations: dict[str, list[str]] = {}

    def add(signature: str, evidence: str) -> None:
        violations.setdefault(signature, []).append(evidence)

    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        add(f"{log_path.name}::unreadable", f"{log_path}: {exc}")
        return violations
    records = []
    for line in lines:
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            add(f"{log_path.name}::corrupt",
                f"{log_path}: unreadable audit line — {FIX}")
            return violations
    header = next((r for r in records if r.get("event") == "case"), {})
    receipts = _receipts_for_run(header.get("root"))
    excluded = [row["glob"] for row in owners.get("excluded", [])]
    entries = owners.get("entries", [])
    helpers = set(owners.get("io_helpers", []))
    for record in records:
        if record.get("event") in (None, "case", "installed",
                                   "subprocess.Popen"):
            continue
        writer = record.get("writer")
        if isinstance(writer, str) and writer in helpers:
            continue
        for rel in _destinations(record):
            if any(fnmatch.fnmatch(rel, glob) for glob in excluded):
                continue
            matched = [e for e in entries
                       if fnmatch.fnmatch(rel, e["glob"])]
            if any(_owner_satisfied(e, record, rel, receipts)
                   for e in matched):
                continue
            evidence = (f"{log_path.name}: {rel} writer={writer} "
                        f"at {record.get('writer_file')}:"
                        f"{record.get('writer_line')} phase="
                        f"{record.get('phase')}")
            if matched:
                who = writer if isinstance(writer, str) and writer \
                    else "unknown"
                for entry in matched:
                    if entry["sink"] == "engine:apply":
                        caps = "+".join(entry.get("capabilities", []))
                        add(f"{entry['glob']}::{caps}", evidence)
                    else:
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
            (ROOT / "system/procedures/INDEX.yaml").read_text(
                encoding="utf-8"))
        for row in index.get("procedures", []):
            stem = Path(row["file"]).stem \
                if isinstance(row, dict) else Path(str(row)).stem
            expected.add(f"procedure__{stem}")
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
    header = {"event": "case", "operation": "control", "case": name,
              "root": str(root)}
    log.write_text("\n".join(
        json.dumps(row) for row in [header, *records]) + "\n",
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
        "/w/operations/new-state.yaml", "learning_os.transactions")])
    assert sigs == {"operations/new-state.yaml::undeclared"}


def test_module_owner_and_temp_sibling_pass(tmp_path):
    assert _signatures(tmp_path, [
        _write_record("/w/operations/transactions/revisions.yaml",
                      "learning_os.transactions.engine"),
        _write_record(
            "/w/operations/transactions/.revisions.yaml.tmp-123",
            "learning_os.transactions.engine"),
    ]) == set()


def test_engine_apply_needs_declared_capability_receipt(tmp_path):
    path = "/w/operations/transactions/lineage.yaml"
    good = {"capability": "lineage.restamp",
            "writes": [{"path": "operations/transactions/lineage.yaml"}]}
    assert _signatures(tmp_path, [
        _write_record(path, "learning_os.transactions", phase="apply"),
    ], receipts=good) == set()
    wrong = {"capability": "goal.decision.record",
             "writes": [{"path": "operations/transactions/lineage.yaml"}]}
    sigs = _signatures(tmp_path, [
        _write_record(path, "learning_os.transactions", phase="apply"),
    ], receipts=wrong)
    assert len(sigs) == 1 and "lineage.yaml" in next(iter(sigs))


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
         "writer": "learning_os.ai_actions.storage",
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
    log.write_text('{"event": "case", "root": "%s"}\nnot json\n'
                   % world, encoding="utf-8")
    assert _violations_in_log(log, _load_owners()) != {}
