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
import functools
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


def _atomic_destination(rel: str) -> str:
    """Use the final name of an atomic-write sibling when comparing scopes."""
    head, separator, name = rel.rpartition("/")
    match = _TEMP_BASENAME.fullmatch(name)
    return head + separator + match.group(1) if match else rel


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
        destinations.append(_atomic_destination(rel))
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


def _read_population_log(log_path: Path, add) -> list[dict] | None:
    """Parse one population log; corrupt or witness-less evidence fails closed.

    Shared by A19 and the runtime writer gate (2A §5.5): one parser, one
    fail-closed policy.
    """
    from arch_writes_fixtures import witness_failures

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
        return None
    if not any(r.get("event") == "installed" for r in records):
        add(f"{log_path.name}::missing-witness", str(log_path))
        return None
    for problem in witness_failures(records, allow_isolated=True):
        add(f"{log_path.name}::bad-witness", problem)
    return records


def _violations_in_log(log_path: Path, owners: dict) -> dict[str, list[str]]:
    """Check retained, root-bound evidence; unknown evidence fails closed."""
    violations: dict[str, list[str]] = {}

    def add(signature: str, evidence: str) -> None:
        violations.setdefault(signature, []).append(evidence)

    records = _read_population_log(log_path, add)
    if records is None:
        return violations

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
        for row in index.get("linked_transcripts", []):
            if row.get("transcript"):
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


# --- 2A §5.5: runtime writer conformance (Bar 4 v3 re-entry) ---
#
# A second, blocking consumer of the same population. For every audited write
# inside a world it resolves the real writer, then requires a declaration in
# tests/architecture/effects.yaml that covers the path, and authority for owned
# territory outside A19's own domain (operations/ and <STATE>/ stay A19's).
# Events are read by their effect, not A19's destination-only view: a rename or
# move removes its source and creates its destination, so both are checked.

#: Events whose every path is affected; the rest touch only their destination.
_ALL_PATH_EVENTS = frozenset({
    "open", "io.open", "os.rename", "shutil.move", "os.remove", "os.unlink",
    "os.rmdir", "shutil.rmtree", "os.truncate", "os.write",
})
_DESTINATION_EVENTS = frozenset({"os.link", "os.symlink", "shutil.copyfile"})
#: Caller-selected output: inside a world generic output may land only where
#: the output guard admits it without producer scopes (the .venv/ scratch).
#: A generated/ producer area needs the producer's declared destination.
#: 2A+2D R3b: required behavioral witnesses for the eight runtime-witnessed
#: writers. Each entry names the relevant operation as (audit events,
#: world-relative destination glob): the CI population must show the writer
#: performing that operation. Observing an unrelated write from the same
#: module does not satisfy the requirement. Globs use scope_matches; every
#: entry below is exercised by a dedicated audit-window witness test or by
#: the scenario population (verified against merged CI population artifacts
#: before adoption — never require an operation the suite does not perform).
_REQUIRED_BEHAVIORAL_WITNESSES: dict[str, tuple[tuple[frozenset, str], ...]] = {
    "tools/learning_os/store/transactions.py": (
        # Receipt publication plus at least one authorized canonical write.
        # The basename check keeps the receipt filename convention while the
        # directory pattern stays inside the valid scope grammar (embedded
        # wildcards are not valid scopes).
        (frozenset({"os.rename"}), "operations/transactions/*.yaml", "transaction-*.yaml"),
        (frozenset({"os.rename"}), "knowledge/**"),
    ),
    "tools/learning_os/store/ai_actions/storage.py": (
        # Relevant request and delivery persistence (not staging reads).
        (frozenset({"os.rename"}), "operations/ai-actions/requests/**"),
        (frozenset({"os.rename"}), "operations/ai-actions/deliveries/**"),
    ),
    "tools/learning_os/store/diagnostics/store.py": (
        # Trace persistence plus a pruning rewrite (distinct operations).
        (frozenset({"open"}), "operations/diagnostics/traces.jsonl"),
        (frozenset({"os.rename"}), "operations/diagnostics/traces.jsonl"),
    ),
    "tools/diagnostics_prune.py": (
        # The standalone tool's own direct sidecar removal.
        (frozenset({"os.remove", "os.unlink"}), "generated/reports/validation-report.cache.json"),
    ),
    "tools/material_summarize.py": (
        # Atomic publication of the canonical summary pair: the whole range
        # directory is renamed into place. Per-file staging renames alone do
        # not prove final publication; the durable publication tests assert
        # the final bytes.
        (frozenset({"os.rename"}), "knowledge/summaries/*/*"),
    ),
    "tools/library_reconciliation.py": (
        # Freeze publication of the authorized reconciliation artifacts.
        (frozenset({"os.rename"}), "work/active/*/outputs/dispositions.yaml"),
    ),
    "tools/learning_os/store/contracts/data_contract.py": (
        # An authorized data-contract update.
        (frozenset({"os.rename"}), "system/contracts/data-contract.yaml"),
    ),
    "tools/learning_os/store/warning_baseline.py": (
        # The atomic warning-baseline replacement.
        (frozenset({"os.rename"}), "operations/validation-warning-baseline.yaml"),
    ),
}
_CALLER_SELECTED_PREFIXES = ("<EXPLICIT_OUT_DIR>/", "<OUT_DIR>/", "<PRIVATE_REPORT_DIR>/",
                             "<RESTORED_COPY>/")
_CALLER_SELECTED_TOKENS = frozenset({
    "<EXPLICIT_OUT_FILE>", "<EXPLICIT_REPORT_OUT>", "<EXPLICIT_LOCAL_OUTPUT>",
    "<TRACE_DEBUG_FILE>", "<LOS_OBSERVATIONS>", "<COUNTER_FILE>",
})


def _world_relative(raw: str, binding: dict) -> str | None:
    """``<STATE>/…`` or a repository path for one absolute audited path; None outside."""
    return _world_relative_cached(raw, str(binding["root"]), binding.get("state_dir"),
                                  bool(binding.get("state_anchored")))


@functools.cache
def _world_relative_cached(raw: str, root: str, state_dir: str | None,
                           anchored: bool) -> str | None:
    lexical = Path(raw).resolve()
    if state_dir and anchored:
        try:
            rel = lexical.relative_to(Path(state_dir).resolve()).as_posix()
        except ValueError:
            pass
        else:
            return _atomic_destination(f"<STATE>/{rel}")
    try:
        rel = lexical.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return None
    if rel in {"", "."}:
        return None
    return _atomic_destination(rel)


def _is_tool_process(binding: dict) -> bool:
    """A LearningOS tool process, as opposed to test or procedure scaffolding."""
    argv = binding.get("argv") or []
    first = str(argv[0]).replace(os.sep, "/") if argv else ""
    return first.startswith("tools/") or "/tools/" in first


@functools.cache
def _writer_key(identity: str) -> str | None:
    """The effects.yaml key for a hook writer identity, if it names a tools/ file."""
    if identity.startswith("tools/"):
        return identity
    head, _, rest = identity.partition(".")
    if head not in {"learning_os", "migrations"} or not rest:
        return None
    base = ROOT / "tools" / head / Path(*rest.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate.relative_to(ROOT).as_posix()
    return None


@functools.cache
def _effects() -> dict:
    import test_arch_writes as census

    return census._load_effects_yaml()


@functools.cache
def _declares(writer_key: str, rel: str) -> bool:
    """True when one declared destination of the writer covers the world-relative path."""
    from learning_os.store.contracts import write_scopes

    for dest in _effects()[writer_key].get("destinations", []):
        if dest.startswith("<STATE>/"):
            if rel.startswith("<STATE>/") and fnmatch.fnmatchcase(rel, dest):
                return True
            continue
        if rel.startswith("<STATE>/"):
            continue
        if dest in _CALLER_SELECTED_TOKENS or dest.startswith(_CALLER_SELECTED_PREFIXES):
            # R2: caller-selected output authorizes only the generic areas
            # (external paths never reach this world-relative check; in-repo
            # that leaves the .venv/ scratch). A generated/ producer area
            # needs the producer's own declared destination below, so generic
            # output cannot overwrite another producer's artifacts.
            parts = tuple(rel.split("/"))
            if parts[0] == "generated":
                continue
            if write_scopes.admitted_repository_output(parts):
                return True
            continue
        if dest == "<GIT_INDEX_AND_COMMIT>":
            if rel == ".git" or rel.startswith(".git/"):
                return True
            continue
        if dest.startswith(("<", "$", "../", "~")):
            continue  # destinations outside every world
        try:
            if write_scopes.scope_matches(rel, dest):
                return True
        except write_scopes.WriteScopeError:
            continue
    return False


@functools.cache
def _authorized(writer_key: str, rel: str) -> bool:
    """Owned territory outside A19's domain needs the engine or a recorded exception."""
    import test_arch_writes as census

    from learning_os.store.contracts import capability_catalog, write_scopes

    if rel.startswith("<STATE>/") or rel == "operations" or rel.startswith("operations/"):
        return True  # A19's domain: its owner check runs over the same records
    try:
        if not capability_catalog.in_owned_territory(rel):
            return True
    except write_scopes.WriteScopeError:
        return False
    if writer_key == census._CANONICAL_ENGINE_MODULE:
        return not any(write_scopes.scope_matches(rel, p) for p in ("bases/**", "boards/**"))
    exception = census._RECORDED_CANONICAL_EXCEPTIONS.get(writer_key)
    if exception is None:
        return False
    return any(write_scopes.scope_matches(rel, dest) for dest in exception[1])


def _conformance_in_log(
    log_path: Path,
    observed: set[tuple[str, str, str]] | None = None,
) -> tuple[dict[str, list[str]], set[str]]:
    """Runtime writer conformance for one log; returns violations and witnessed writers.

    When ``observed`` is given, every attributed (writer, event, world-relative
    destination) triple is added to it for the R3b behavioral-witness check.
    """
    import arch_audit_hook

    violations: dict[str, list[str]] = {}
    witnessed: set[str] = set()

    def add(signature: str, evidence: str) -> None:
        violations.setdefault(signature, []).append(evidence)

    records = _read_population_log(log_path, add)
    if records is None:
        return violations, witnessed
    worlds: dict = {}
    for record in records:
        event = record.get("event")
        if event == "installed":
            worlds[record.get("pid")] = record
            continue
        if event not in _ALL_PATH_EVENTS and event not in _DESTINATION_EVENTS:
            continue
        if event in {"open", "io.open"} and record.get("mode") == "r":
            continue
        binding = worlds.get(record.get("pid"))
        if binding is None or binding.get("root") is None:
            continue  # A19 fails closed on unbound writers and worlds
        paths = record.get("resolved_paths") or record.get("paths") or []
        if event in _DESTINATION_EVENTS:
            paths = paths[-1:]
        writer = record.get("writer")
        if writer in arch_audit_hook.MECHANICAL_HELPERS:
            writer = record.get("caller")
        for raw in paths:
            if not isinstance(raw, str) or not os.path.isabs(raw):
                add(f"{log_path.name}::unresolved", str(record))
                continue
            rel = _world_relative(raw, binding)
            if rel is None:
                continue  # outside the world: the output guard and the census
            evidence = (f"{log_path.name}: {event} {rel} writer={record.get('writer')} "
                        f"caller={record.get('caller')} at {record.get('writer_file')}:"
                        f"{record.get('writer_line')}")
            if writer is None:
                if _is_tool_process(binding):
                    add(f"{rel}::unknown-writer", evidence)
                continue  # test or procedure scaffolding, not LearningOS code
            key = _writer_key(writer)
            if key is None or key not in _effects():
                add(f"{rel}::undeclared-writer={writer}", evidence)
                continue
            witnessed.add(key)
            if observed is not None:
                observed.add((key, event, rel))
            if not _declares(key, rel):
                add(f"{rel}::outside-declaration={key}", evidence)
            if not _authorized(key, rel):
                add(f"{rel}::unauthorized={key}", evidence)
    return violations, witnessed


def _conformance_population(
    audit_dir: Path,
    observed: set[tuple[str, str, str]] | None = None,
) -> tuple[dict[str, list[str]], set[str]]:
    merged: dict[str, list[str]] = {}
    witnessed: set[str] = set()
    for log_path in sorted(audit_dir.glob("*.jsonl")):
        violations, seen = _conformance_in_log(log_path, observed)
        for signature, evidence in violations.items():
            merged.setdefault(signature, []).extend(evidence)
        witnessed |= seen
    return merged, witnessed


def _behavioral_witness_gaps(
    observed: set[tuple[str, str, str]],
) -> list[str]:
    """2A+2D R3b: required (writer, operation, destination) triples with no witness.

    ``observed`` holds one triple per attributed population write. A gap names
    the writer, the relevant operation's audit events, and the destination
    glob from _REQUIRED_BEHAVIORAL_WITNESSES. An unrelated write from the same
    module never closes its gap.
    """
    import fnmatch

    from learning_os.store.contracts import write_scopes

    gaps: list[str] = []
    for writer_key, requirements in _REQUIRED_BEHAVIORAL_WITNESSES.items():
        seen = {(event, rel) for (key, event, rel) in observed if key == writer_key}
        for requirement in requirements:
            events, pattern = requirement[0], requirement[1]
            # An optional basename glob keeps filename conventions (receipt
            # names) without embedded wildcards in the scope pattern.
            basename = requirement[2] if len(requirement) > 2 else None
            if not any(
                event in events
                and write_scopes.scope_matches(rel, pattern)
                and (basename is None or fnmatch.fnmatchcase(
                    rel.rpartition("/")[2], basename))
                for event, rel in seen
            ):
                gaps.append(
                    f"{writer_key}: no observed {sorted(events)} write to "
                    f"{pattern} (R3b behavioral witness)")
    return sorted(gaps)


def test_runtime_writer_conformance_population():
    """2A §5.5/§5.6 + 2A+2D R3b: every witnessed world write has a resolved, declared, authorized writer.

    Also proves witness coverage: every writer whose effects.yaml disposition
    is ``witness: runtime`` was observed writing in this CI population, and
    every required (writer, operation, destination) behavioral witness from
    _REQUIRED_BEHAVIORAL_WITNESSES was observed — an unrelated write from the
    same module does not count.
    """
    audit_dir = _audit_dir()
    logs = sorted(audit_dir.glob("*.jsonl")) if audit_dir else []
    if not logs:
        if os.environ.get("CI"):
            raise AssertionError("2A runtime gate: CI requires audit witnesses, found none")
        pytest.skip("2A runtime gate: no audit logs this run (local partial run)")
    observed: set[tuple[str, str, str]] = set()
    violations, witnessed = _conformance_population(audit_dir, observed)
    assert not violations, "2A runtime writer violations:\n" + "\n".join(
        f"{sig}: {violations[sig][0]}" for sig in sorted(violations))
    if os.environ.get("CI"):
        expected = {rel for rel, row in _effects().items() if row.get("witness") == "runtime"}
        missing = sorted(expected - witnessed)
        assert not missing, (
            f"2A witness accounting: writers declared runtime-witnessed were not observed "
            f"in the CI population: {missing}")
        gaps = _behavioral_witness_gaps(observed)
        assert not gaps, (
            "R3b behavioral witness gaps: required writer operations unobserved "
            "in the CI population:\n" + "\n".join(gaps))


def test_behavioral_witness_requires_the_relevant_operation(tmp_path):
    """R3b negative control: a declared but irrelevant write leaves the gap open."""
    world = tmp_path / "world"
    world.mkdir()
    # A direct open of the baseline is declared for warning_baseline, so it
    # raises no violation — but the required operation is the atomic rename.
    direct = dict(_write_record("/w/operations/validation-warning-baseline.yaml",
                                "learning_os.store.warning_baseline"))
    log = _write_log(tmp_path, "behavioral-negative", [direct], world)
    observed: set[tuple[str, str, str]] = set()
    violations, _ = _conformance_in_log(log, observed)
    assert not violations, violations
    gaps = _behavioral_witness_gaps(observed)
    assert any("warning_baseline" in gap and "validation-warning-baseline.yaml" in gap
               for gap in gaps), gaps


def test_behavioral_witness_accepts_the_relevant_operation(tmp_path):
    """R3b positive control: the required rename closes the writer's gap."""
    world = tmp_path / "world"
    world.mkdir()
    rename = {"event": "os.rename",
              "paths": ["/w/operations/.validation-warning-baseline.yaml.tmp-1",
                        "/w/operations/validation-warning-baseline.yaml"],
              "writer": "learning_os.store.warning_baseline",
              "writer_file": "/repo/tools/learning_os/store/warning_baseline.py",
              "writer_line": 1}
    log = _write_log(tmp_path, "behavioral-positive", [rename], world)
    observed: set[tuple[str, str, str]] = set()
    violations, _ = _conformance_in_log(log, observed)
    assert not violations, violations
    gaps = _behavioral_witness_gaps(observed)
    assert not any("warning_baseline" in gap for gap in gaps), gaps


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


def test_mechanical_delegation_is_bounded_to_the_immediate_caller(tmp_path, monkeypatch):
    import arch_audit_hook

    helper = "learning_os.store.example_helper"
    engine = "learning_os.store.transactions"
    monkeypatch.setitem(arch_audit_hook.MECHANICAL_HELPERS, helper, frozenset({engine}))
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


# ---- 2A re-entry §5.5: the runtime writer gate on real and fabricated logs ----
#
# Real executed writes run inside a private hook window whose log stays in
# tmp_path: it never joins the CI population, so deliberate violations here
# cannot reach the population gates. Fabricated records test only the consumer.


def _private_window(tmp_path: Path, root: Path, argv=("pytest",)):
    import contextlib
    import tempfile
    import uuid

    import arch_audit_hook

    @contextlib.contextmanager
    def window():
        log = tmp_path / f"private-{uuid.uuid4().hex[:8]}.jsonl"
        git_dir = root / ".git"
        header = {"event": "case", "operation": "private", "case": log.stem, "root": str(root)}
        installed = {
            "event": "installed", "pid": os.getpid(), "ppid": os.getppid(), "token": "private",
            "argv": list(argv), "root": str(root),
            "state_dir": str(git_dir / "learningos") if git_dir.is_dir() else tempfile.gettempdir(),
            "state_anchored": git_dir.is_dir(),
        }
        log.write_text(json.dumps(header) + "\n" + json.dumps(installed) + "\n", encoding="utf-8")
        arch_audit_hook.install(str(log))
        try:
            yield log
        finally:
            arch_audit_hook.uninstall()
        arch_audit_hook.assert_capture_ok()
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "event": "completed", "pid": os.getpid(), "token": "private",
                "root": str(root), "capture_ok": True, "new_receipts": []}) + "\n")

    return window()


def _write_events(log: Path) -> list[dict]:
    return [row for row in (json.loads(line) for line in log.read_text().splitlines())
            if row.get("event") in {"open", "os.rename", "os.replace"}
            and (row.get("mode") or "w") != "r"]


def test_runtime_gate_accepts_atomic_review_check_state(tmp_path):
    import subprocess

    from learning_os.store import session_ledger
    from learning_os.store.fs import clean_git_env

    world = tmp_path / "world"
    subprocess.run(["git", "init", "-q", str(world)], check=True, env=clean_git_env())
    with _private_window(tmp_path, world) as log:
        session_ledger.remember_review_check(world, "snapshot", "digest")

    assert session_ledger.has_review_check(world, "snapshot", "digest")
    events = _write_events(log)
    assert any(row["event"] == "open" and any(".json.tmp-" in p for p in row["paths"])
               for row in events)
    assert any(row["event"] == "os.rename" for row in events)
    violations, witnessed = _conformance_in_log(log)
    assert not violations, violations
    assert "tools/learning_os/store/session_ledger.py" in witnessed


def _fake_checkout(tmp_path: Path, files: dict[str, str]) -> Path:
    """A disposable LearningOS-shaped checkout; the hook attributes its tools/ frames."""
    fake = tmp_path / "fake-checkout"
    (fake / "system/contracts").mkdir(parents=True, exist_ok=True)
    (fake / "system/contracts/tree-contract.yaml").write_text("directories: []\n", encoding="utf-8")
    for rel, source in files.items():
        (fake / rel).parent.mkdir(parents=True, exist_ok=True)
        (fake / rel).write_text(source, encoding="utf-8")
    return fake


def _load_file(path: Path):
    import importlib.util
    import uuid

    spec = importlib.util.spec_from_file_location(f"zz_probe_{uuid.uuid4().hex[:8]}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_gate_accepts_a_package_writer_inside_its_scope(tmp_path):
    from collections import Counter

    from learning_os.store.warning_baseline import write_baseline

    world = tmp_path / "world"
    world.mkdir()
    with _private_window(tmp_path, world) as log:
        write_baseline(world, Counter({("LOCATOR-VAGUE", "a.yaml"): 1}), "private window")
    writers = {row["writer"] for row in _write_events(log)}
    assert writers == {"learning_os.store.warning_baseline"}, writers
    violations, witnessed = _conformance_in_log(log)
    assert violations == {}
    assert witnessed == {"tools/learning_os/store/warning_baseline.py"}


def test_runtime_gate_rejects_an_executed_out_of_scope_write(tmp_path):
    """§7: a declared package writer driven outside its declaration is caught."""
    from collections import Counter

    from learning_os.store.warning_baseline import write_baseline

    world = tmp_path / "world"
    (world / "knowledge").mkdir(parents=True)
    with _private_window(tmp_path, world) as log:
        write_baseline(world / "knowledge", Counter({("LOCATOR-VAGUE", "a.yaml"): 1}), "leak")
    violations, _ = _conformance_in_log(log)
    rel = "knowledge/operations/validation-warning-baseline.yaml"
    key = "tools/learning_os/store/warning_baseline.py"
    assert f"{rel}::outside-declaration={key}" in violations, violations
    assert f"{rel}::unauthorized={key}" in violations, violations


def test_runtime_gate_credits_the_ai_action_storage_route_through_fs(tmp_path):
    from learning_os.store.ai_actions.storage import FilesystemAIActionRepository

    world = tmp_path / "world"
    world.mkdir()
    repository = FilesystemAIActionRepository(world)
    with _private_window(tmp_path, world) as log:
        repository.write_continuation(
            "ai-request-20261127-abc123", pass_number=1, route_id="route-demo",
            record_text="pass: 1\n", slice_relative="slices/pass-1.md",
            slice_body=b"slice\n", index_text="{}\n")
    events = _write_events(log)
    assert events and {row["writer"] for row in events} == {"learning_os.store.fs"}
    assert {row.get("caller") for row in events} == {"learning_os.store.ai_actions.storage"}
    violations, witnessed = _conformance_in_log(log)
    assert violations == {}
    assert witnessed == {"tools/learning_os/store/ai_actions/storage.py"}


def test_runtime_gate_credits_a_real_standalone_tool_through_fs(tmp_path, capsys, monkeypatch):
    """The recorded exception material_summarize.py writes knowledge/summaries/**."""
    import test_material_summaries as summaries_tests

    ms = summaries_tests._material_summarize()
    world = tmp_path / "world"
    cache = world / "knowledge" / "summaries"
    cache.mkdir(parents=True)
    text = summaries_tests._text_cache(tmp_path)
    draft = tmp_path / "draft.md"
    draft.write_text("A detailed chapter compression. " * 20, encoding="utf-8")
    with _private_window(tmp_path, world) as log:
        assert summaries_tests._promote(ms, cache, text, draft) == 0
    capsys.readouterr()
    events = _write_events(log)
    assert events and {row.get("caller") for row in events} == {"tools/material_summarize.py"}
    violations, witnessed = _conformance_in_log(log)
    assert violations == {}
    assert witnessed == {"tools/material_summarize.py"}


def test_runtime_gate_attributes_and_rejects_a_standalone_tool_writing_owned_state(tmp_path):
    """§7: a standalone tool writing records/ is credited to its file and refused."""
    fake = _fake_checkout(tmp_path, {
        "tools/zz_rogue_standalone.py":
            "def run(root):\n    (root / 'records' / 'x.yaml').write_text('x\\n')\n",
    })
    rogue = _load_file(fake / "tools/zz_rogue_standalone.py")
    world = tmp_path / "world"
    (world / "records").mkdir(parents=True)
    with _private_window(tmp_path, world) as log:
        rogue.run(world)
    assert {row["writer"] for row in _write_events(log)} == {"tools/zz_rogue_standalone.py"}
    violations, _ = _conformance_in_log(log)
    assert "records/x.yaml::undeclared-writer=tools/zz_rogue_standalone.py" in violations, violations


def test_runtime_gate_attributes_a_migration_frame(tmp_path):
    """A tools/migrations/ frame is a migration writer; an unknown one is refused."""
    fake = _fake_checkout(tmp_path, {
        "tools/migrations/zz_probe_migration.py":
            "def apply(root):\n    (root / 'curriculum' / 'x.yaml').write_text('x\\n')\n",
    })
    migration = _load_file(fake / "tools/migrations/zz_probe_migration.py")
    world = tmp_path / "world"
    (world / "curriculum").mkdir(parents=True)
    with _private_window(tmp_path, world) as log:
        migration.apply(world)
    assert {row["writer"] for row in _write_events(log)} == {"migrations.zz_probe_migration"}
    violations, _ = _conformance_in_log(log)
    assert "curriculum/x.yaml::undeclared-writer=migrations.zz_probe_migration" in violations


def test_runtime_gate_credits_a_standalone_callback_to_its_own_file(tmp_path):
    """A standalone callback run by a package frame is never credited to that frame."""
    fake = _fake_checkout(tmp_path, {
        "tools/learning_os/zz_runner.py": "def run(callback, path):\n    callback(path)\n",
        "tools/zz_callback.py": "def write(path):\n    path.write_text('x\\n')\n",
    })
    runner = _load_file(fake / "tools/learning_os/zz_runner.py")
    callback = _load_file(fake / "tools/zz_callback.py")
    world = tmp_path / "world"
    (world / "generated/reports").mkdir(parents=True)
    with _private_window(tmp_path, world) as log:
        runner.run(callback.write, world / "generated/reports/x.md")
    assert {row["writer"] for row in _write_events(log)} == {"tools/zz_callback.py"}
    violations, _ = _conformance_in_log(log)
    assert "generated/reports/x.md::undeclared-writer=tools/zz_callback.py" in violations


def _conformance_signatures(tmp_path: Path, records: list[dict], argv=None) -> set[str]:
    import uuid

    world = tmp_path / f"world-{uuid.uuid4().hex[:8]}"
    (world / "operations" / "transactions").mkdir(parents=True)
    log = _write_log(tmp_path, f"conformance-{uuid.uuid4().hex[:8]}", records, world)
    if argv is not None:
        rows = [json.loads(line) for line in log.read_text().splitlines()]
        for row in rows:
            if row.get("event") == "installed":
                row["argv"] = list(argv)
        log.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    violations, _ = _conformance_in_log(log)
    return set(violations)


_CACHE_WRITER = "learning_os.store.validation_cache"
_CACHE_KEY = "tools/learning_os/store/validation_cache.py"
_CACHE_FILE = "generated/reports/validation-report.cache.json"


def test_runtime_gate_checks_the_source_of_a_rename(tmp_path):
    """§7: a non-owner rename whose source is in owned territory is caught."""
    sigs = _conformance_signatures(tmp_path, [{
        "event": "os.rename", "paths": ["/w/knowledge/notes/a.md", f"/w/{_CACHE_FILE}"],
        "mode": None, "writer": _CACHE_WRITER, "writer_file": "/repo/x.py", "writer_line": 1}])
    assert f"knowledge/notes/a.md::outside-declaration={_CACHE_KEY}" in sigs, sigs
    assert f"knowledge/notes/a.md::unauthorized={_CACHE_KEY}" in sigs, sigs
    assert not any(sig.startswith(_CACHE_FILE) for sig in sigs), sigs


def test_runtime_gate_checks_only_the_destination_of_a_copy(tmp_path):
    assert _conformance_signatures(tmp_path, [{
        "event": "shutil.copyfile", "paths": ["/w/knowledge/notes/a.md", f"/w/{_CACHE_FILE}"],
        "mode": None, "writer": _CACHE_WRITER, "writer_file": "/repo/x.py", "writer_line": 1}]) == set()


def test_runtime_gate_refuses_an_unknown_writer_only_in_a_tool_process(tmp_path):
    record = {"event": "open", "paths": ["/w/generated/reports/x.md"], "mode": "w",
              "writer": None, "writer_file": None, "writer_line": None}
    assert _conformance_signatures(tmp_path, [record], argv=["tools/los.py", "status"]) == {
        "generated/reports/x.md::unknown-writer"}
    assert _conformance_signatures(tmp_path, [record]) == set()  # test scaffolding


@pytest.mark.parametrize("rel, ok", [
    ("generated/reports/out.json", True),
    (".venv/scratch/out.json", True),
    ("generated/undeclared-child/out.json", False),
    ("archive/out.json", False),
])
def test_runtime_gate_admits_caller_selected_output_only_where_the_guard_does(tmp_path, rel, ok):
    sigs = _conformance_signatures(tmp_path, [{
        "event": "open", "paths": [f"/w/{rel}"], "mode": "w",
        "writer": "learning_os.app.handlers.platform", "writer_file": "/repo/x.py",
        "writer_line": 1}])
    key = "tools/learning_os/app/handlers/platform.py"
    assert (f"{rel}::outside-declaration={key}" not in sigs) is ok, sigs


def test_runtime_gate_refuses_the_engine_on_interface_roots_and_admits_its_controls(tmp_path):
    engine = "learning_os.store.transactions"
    key = "tools/learning_os/store/transactions.py"
    sigs = _conformance_signatures(tmp_path, [{
        "event": "open", "paths": ["/w/boards/x.canvas"], "mode": "w", "phase": "apply",
        "writer": engine, "writer_file": "/repo/x.py", "writer_line": 1}])
    assert f"boards/x.canvas::unauthorized={key}" in sigs, sigs
    # Controls: the engine:apply alternative row and a legitimate migration.
    assert _conformance_signatures(tmp_path, [{
        "event": "open", "paths": ["/w/operations/ai-actions/requests/r1/request.yaml"],
        "mode": "w", "phase": "apply", "writer": engine,
        "writer_file": "/repo/x.py", "writer_line": 1}]) == set()
    assert _conformance_signatures(tmp_path, [{
        "event": "open", "paths": ["/w/curriculum/programs/x.yaml"], "mode": "w",
        "writer": "migrations.curriculum_v2", "writer_file": "/repo/x.py",
        "writer_line": 1}]) == set()
