"""Shared transaction receipt chain, live drift, and baseline inspection.

One implementation shared by ``tools/receipt_drift.py``,
``learning_os.derive.validation.projects``, and
``learning_os.store.diagnostics.resolver``. Every check reads the committed
``writes`` log chronologically and verifies per-path byte continuity
(``sha256_before == previous.sha256_after``) as well as live on-disk hashes.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

from learning_os.store.layout import PathBoundaryError, read_text_inside
from learning_os.store.loading.yamlio import UniqueKeySafeLoader

RECEIPT_DIR = Path("operations") / "transactions"
RECEIPT_GLOB = "transaction-*.yaml"
CHAIN_BASELINE_RELATIVE = "operations/receipt-chain-baseline.yaml"
CHAIN_BASELINE_SCHEMA = "receipt-chain-baseline"

ID_PATTERN = re.compile(r"^transaction-[0-9]{8}-[0-9]{6}-[0-9]{3}$")
HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")

PLAN_RECORD_GLOBS = (
    "curriculum/modules/*/units/*/study-map.yaml",
    "curriculum/modules/*/source-map.yaml",
)
RECORD_GLOBS = (
    *PLAN_RECORD_GLOBS,
    "curriculum/modules/*/module.yaml",
)
CHAIN_GATED_GLOBS = (
    *RECORD_GLOBS,
    "curriculum/programs/*.yaml",
)
# Gitignored AI-action handoff bundles exist only on the active operator disk
# (`.gitignore` excludes `requests/*`, `deliveries/*`, and `incoming/*`).
OPERATIONAL_HANDOFF_PREFIXES = (
    "operations/ai-actions/requests/",
    "operations/ai-actions/deliveries/",
    "operations/ai-actions/incoming/",
)


#: Roots whose receipted Markdown is the learner's own prose: durable notes,
#: unit notes, exercise sheets and workspace context. Obsidian is where the
#: learner reads and writes these files, so a hand edit there is ordinary use,
#: not an ungated change to a record the system interprets.
LEARNER_PROSE_ROOTS = ("knowledge", "curriculum", "work")


def is_learner_prose_path(relative: str) -> bool:
    """Return True for receipted learner-owned Markdown (notes, sheets, context).

    Drift on these paths is reported as a warning, never a gateway-blocking
    error: one stray keystroke in a note must not stop every write in the
    system. The canonical snapshot guard still refuses any write sealed
    against the bytes from before the edit, so a hand edit cannot be
    overwritten silently. YAML, JSON, code and everything under
    ``operations/`` stay error-level, and so does Markdown elsewhere
    (``archive/`` is frozen history).
    """
    parts = PurePosixPath(relative).parts
    return (
        len(parts) >= 2
        and parts[0] in LEARNER_PROSE_ROOTS
        and parts[-1].endswith(".md")
    )


def is_operational_handoff_path(relative: str) -> bool:
    """Return True when *relative* is gitignored AI-action operational handoff state."""
    normalized = relative.strip("/")
    if normalized.endswith("/.gitkeep"):
        return False
    return any(normalized.startswith(prefix) for prefix in OPERATIONAL_HANDOFF_PREFIXES)


@dataclass(frozen=True)
class BaselineData:
    """Validated receipt-chain baseline entries (fail-closed when invalid)."""

    chain_keys: dict[tuple[str, str], dict[str, object]]
    drift_by_path: dict[str, dict[str, object]]
    errors: tuple[str, ...] = ()
    valid: bool = True


def _hash_value_ok(value: object) -> bool:
    return value is None or (isinstance(value, str) and bool(HASH_PATTERN.match(value)))


def receipt_shape_ok(receipt: object) -> bool:
    """Validate receipt metadata and ``writes`` structure before trusting rows."""
    if not isinstance(receipt, dict):
        return False
    rid = receipt.get("id")
    if not isinstance(rid, str) or not ID_PATTERN.match(rid):
        return False
    writes = receipt.get("writes")
    if not isinstance(writes, list):
        return False
    seen_paths: set[str] = set()
    for row in writes:
        if not isinstance(row, dict):
            return False
        path = row.get("path")
        if not isinstance(path, str) or not path or path in seen_paths:
            return False
        seen_paths.add(path)
        if not _hash_value_ok(row.get("sha256_before")):
            return False
        if not _hash_value_ok(row.get("sha256_after")):
            return False
    return True


def is_migration_receipt(receipt: dict[str, object]) -> bool:
    """Return True when the receipt records an explicit migration operation."""
    capability = receipt.get("capability")
    if isinstance(capability, str) and capability.startswith("migration."):
        return True
    metadata = receipt.get("metadata")
    if isinstance(metadata, dict):
        migration = metadata.get("migration")
        if isinstance(migration, str) and bool(migration.strip()):
            return True
    return False


def is_chain_gated_path(relative: str) -> bool:
    """Return True for plan, module, program, and source-map canonical records."""
    parts = PurePosixPath(relative).parts
    if len(parts) == 3 and parts[0] == "curriculum" and parts[1] == "programs" and parts[2].endswith(".yaml"):
        return True
    if len(parts) == 4 and parts[0] == "curriculum" and parts[1] == "modules" and parts[3] in {"module.yaml", "source-map.yaml"}:
        return True
    if (
        len(parts) == 6
        and parts[0] == "curriculum"
        and parts[1] == "modules"
        and parts[3] == "units"
        and parts[5] == "study-map.yaml"
    ):
        return True
    return False


def sha256_file(path: Path) -> str:
    """Compute hex SHA-256 of a file using bounded 1 MiB reads."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_receipts(root: Path) -> tuple[list[dict[str, object]], list[str]]:
    """Parse every receipt in chronological id order; surface unusable filenames."""
    receipts: list[dict[str, object]] = []
    malformed: list[str] = []
    directory = root / RECEIPT_DIR
    if not directory.is_dir():
        return receipts, malformed
    for path in sorted(directory.glob(RECEIPT_GLOB)):
        if path.is_symlink():
            malformed.append(path.name)
            continue
        try:
            raw: object = yaml.load(read_text_inside(root, path), Loader=UniqueKeySafeLoader)
        except (OSError, PathBoundaryError, yaml.YAMLError, UnicodeDecodeError):
            malformed.append(path.name)
            continue
        if isinstance(raw, dict) and raw.get("type") == "transaction-receipt" and receipt_shape_ok(raw):
            receipts.append({str(k): v for k, v in raw.items()})
        else:
            malformed.append(path.name)
    receipts.sort(key=lambda receipt: str(receipt.get("id", "")))
    return receipts, malformed


def committed_receipts(receipts: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
    """Filter shape-valid receipts to ``status == committed``, preserving id sort."""
    committed: list[dict[str, object]] = []
    skipped = 0
    for receipt in receipts:
        if not receipt_shape_ok(receipt):
            continue
        if receipt.get("status") != "committed":
            skipped += 1
            continue
        committed.append(receipt)
    committed.sort(key=lambda receipt: str(receipt.get("id", "")))
    return committed, skipped


def last_writes(receipts: list[dict[str, object]]) -> tuple[dict[str, tuple[str | None, str]], int]:
    """Map path -> (sha256_after, receipt_id) using the last committed write."""
    last: dict[str, tuple[str | None, str]] = {}
    committed, skipped = committed_receipts(receipts)
    for receipt in committed:
        rid = str(receipt.get("id", ""))
        writes = receipt.get("writes")
        if not isinstance(writes, list):
            continue
        for row in writes:
            if not isinstance(row, dict):
                continue
            path = row.get("path")
            if isinstance(path, str) and path:
                sha_after = row.get("sha256_after")
                last[path] = (sha_after if isinstance(sha_after, str) else None, rid)
    return last, skipped


def record_files(root: Path, globs: tuple[str, ...] = RECORD_GLOBS) -> list[str]:
    """Collect sorted relative paths of canonical record files under ``globs``."""
    files: set[str] = set()
    for pattern in globs:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                files.add(path.relative_to(root).as_posix())
    return sorted(files)


def _inflight_transitions(root: Path) -> dict[str, tuple[str | None, str | None]]:
    """Map path -> (before_hex, after_hex) for an active in-flight commit journal.

    During ``TransactionService.commit()``, ``_validate()`` runs after
    ``_apply()`` writes the new bytes to disk and before ``_write_receipt()``
    records the new receipt. Reading ``.inflight/<tx>/intent.json`` lets
    ``compute_drift`` evaluate the pre-apply bytes (``before``) for paths whose
    on-disk bytes match the in-flight ``after`` image, so legitimate second
    writes do not self-conflict while pre-existing hand edits still fail.
    """
    inflight_root = root / RECEIPT_DIR / ".inflight"
    if not inflight_root.is_dir():
        return {}
    transitions: dict[str, tuple[str | None, str | None]] = {}
    for entry in sorted(inflight_root.iterdir(), key=lambda p: p.name):
        if entry.name.startswith(".") or not entry.is_dir():
            continue
        intent_path = entry / "intent.json"
        if not intent_path.is_file():
            continue
        try:
            intent: object = json.loads(read_text_inside(root, intent_path))
        except (OSError, PathBoundaryError, ValueError, UnicodeDecodeError):
            continue
        if not isinstance(intent, dict):
            continue
        paths = intent.get("paths")
        if not isinstance(paths, list):
            continue
        for row in paths:
            if not isinstance(row, dict):
                continue
            rel = row.get("path")
            before = row.get("before")
            after = row.get("after")
            if not isinstance(rel, str) or not isinstance(before, dict) or not isinstance(after, dict):
                continue
            before_sha = before.get("sha256") if before.get("kind") == "file" else None
            after_sha = after.get("sha256") if after.get("kind") == "file" else None
            before_hex = (
                before_sha.removeprefix("sha256:")
                if isinstance(before_sha, str)
                else None
            )
            after_hex = (
                after_sha.removeprefix("sha256:")
                if isinstance(after_sha, str)
                else None
            )
            transitions[rel] = (before_hex, after_hex)
    return transitions


def compute_drift(
    root: Path,
    last: dict[str, tuple[str | None, str]],
) -> list[dict[str, object]]:
    """Compare on-disk bytes of tracked paths against their last committed receipt."""
    drift: list[dict[str, object]] = []
    inflight = _inflight_transitions(root)
    for path in sorted(last):
        expected, receipt_id = last[path]
        actual_path = root / path
        if actual_path.is_symlink():
            actual_digest: str | None = None
            if actual_path.exists() and actual_path.is_file():
                try:
                    actual_digest = sha256_file(actual_path)
                except OSError:
                    actual_digest = None
            drift.append({
                "path": path,
                "receipt": receipt_id,
                "expected": expected,
                "actual": actual_digest,
                "note": "canonical record is a symlink; the ledger cannot vouch for where its bytes live",
            })
            continue
        if not actual_path.is_file():
            disk_actual: str | None = None
        else:
            try:
                disk_actual = sha256_file(actual_path)
            except OSError:
                drift.append({
                    "path": path,
                    "receipt": receipt_id,
                    "expected": expected,
                    "actual": None,
                    "note": "file is unreadable",
                })
                continue
        if path in inflight and disk_actual == inflight[path][1]:
            actual = inflight[path][0]
        else:
            actual = disk_actual
        if actual is None:
            if expected and not is_operational_handoff_path(path):
                drift.append({
                    "path": path,
                    "receipt": receipt_id,
                    "expected": expected,
                    "actual": None,
                    "note": "file deleted after the receipt recorded it",
                })
            continue
        if expected is None:
            drift.append({
                "path": path,
                "receipt": receipt_id,
                "expected": None,
                "actual": actual,
                "note": "file exists but the last receipt recorded its deletion",
            })
            continue
        if actual != expected:
            drift.append({
                "path": path,
                "receipt": receipt_id,
                "expected": expected,
                "actual": actual,
                "note": "bytes differ from the last receipt",
            })
    return drift


def find_chain_breaks(receipts: list[dict[str, object]]) -> list[dict[str, object]]:
    """Detect per-path sha256 discontinuities across committed receipts."""
    committed, _ = committed_receipts(receipts)
    last_after: dict[str, tuple[str | None, str]] = {}
    breaks: list[dict[str, object]] = []
    for receipt in committed:
        rid = str(receipt.get("id", ""))
        migration_exempt = is_migration_receipt(receipt)
        writes = receipt.get("writes")
        if not isinstance(writes, list):
            continue
        for row in writes:
            if not isinstance(row, dict):
                continue
            path = row.get("path")
            if not isinstance(path, str) or not path:
                continue
            raw_after = row.get("sha256_after")
            raw_before = row.get("sha256_before")
            after = raw_after if isinstance(raw_after, str) else None
            before = raw_before if isinstance(raw_before, str) else None
            prev = last_after.get(path)
            if prev is not None:
                prev_after, prev_receipt = prev
                if before != prev_after:
                    breaks.append({
                        "path": path,
                        "receipt": rid,
                        "previous_receipt": prev_receipt,
                        "expected_sha256_before": prev_after,
                        "actual_sha256_before": before,
                        "gated": is_chain_gated_path(path),
                        "migration_exempt": migration_exempt,
                    })
            last_after[path] = (after, rid)
    return breaks


def load_chain_baseline(
    root: Path,
    committed_list: list[dict[str, object]],
    raw_breaks: list[dict[str, object]],
    *,
    schema_check: Callable[[dict[str, object]], bool] | None = None,
) -> BaselineData:
    """Load and validate ``operations/receipt-chain-baseline.yaml`` (fail closed)."""
    path = root / CHAIN_BASELINE_RELATIVE
    if not path.exists() and not path.is_symlink():
        return BaselineData(chain_keys={}, drift_by_path={}, errors=(), valid=True)
    if path.is_symlink():
        return BaselineData(
            chain_keys={},
            drift_by_path={},
            errors=(f"{CHAIN_BASELINE_RELATIVE} cannot be a symlink",),
            valid=False,
        )
    try:
        raw_data: object = yaml.load(read_text_inside(root, path), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError, UnicodeDecodeError) as exc:
        return BaselineData(
            chain_keys={},
            drift_by_path={},
            errors=(f"cannot read receipt chain baseline: {exc}",),
            valid=False,
        )
    if not isinstance(raw_data, dict):
        return BaselineData(
            chain_keys={},
            drift_by_path={},
            errors=("receipt chain baseline does not match contract header",),
            valid=False,
        )
    data: dict[str, object] = {str(k): v for k, v in raw_data.items()}
    if data.get("schema_version") != 1 or data.get("type") != CHAIN_BASELINE_SCHEMA:
        return BaselineData(
            chain_keys={},
            drift_by_path={},
            errors=("receipt chain baseline does not match contract header",),
            valid=False,
        )
    if schema_check is not None and not schema_check(data):
        return BaselineData(chain_keys={}, drift_by_path={}, errors=(), valid=False)
    entries = data.get("entries")
    if not isinstance(entries, list):
        return BaselineData(
            chain_keys={},
            drift_by_path={},
            errors=("receipt chain baseline entries must be a list",),
            valid=False,
        )

    receipt_by_id = {str(r.get("id")): r for r in committed_list}
    break_lookup: dict[tuple[str, str], dict[str, object]] = {
        (str(row["receipt"]), str(row["path"])): row for row in raw_breaks
    }
    errors: list[str] = []
    chain_keys: dict[tuple[str, str], dict[str, object]] = {}
    for index, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            errors.append(f"baseline entry {index} must be a mapping")
            continue
        entry: dict[str, object] = {str(k): v for k, v in raw_entry.items()}
        tx_id = entry.get("transaction")
        rel_path = entry.get("path")
        where = f"baseline entry {index} ({tx_id}, {rel_path})"
        if not isinstance(tx_id, str) or tx_id not in receipt_by_id:
            errors.append(f"{where}: transaction is not a committed receipt")
            continue
        if not isinstance(rel_path, str) or not rel_path:
            errors.append(f"{where}: missing path")
            continue
        key = (tx_id, rel_path)
        if key in chain_keys:
            errors.append(f"{where}: duplicate baseline entry")
            continue
        brk = break_lookup.get(key)
        if brk is None:
            errors.append(f"{where}: no chain break matches this transaction and path")
            continue
        if (
            entry.get("previous_transaction") != brk.get("previous_receipt")
            or entry.get("expected_sha256_before") != brk.get("expected_sha256_before")
            or entry.get("actual_sha256_before") != brk.get("actual_sha256_before")
        ):
            errors.append(f"{where}: baseline hash/previous claim contradicts receipt history")
            continue
        chain_keys[key] = entry

    drift_entries = data.get("historical_drift") or []
    drift_by_path: dict[str, dict[str, object]] = {}
    if not isinstance(drift_entries, list):
        errors.append("historical_drift must be a list")
    else:
        for index, raw_drift_entry in enumerate(drift_entries):
            if not isinstance(raw_drift_entry, dict):
                errors.append(f"historical_drift entry {index} must be a mapping")
                continue
            drift_entry: dict[str, object] = {str(k): v for k, v in raw_drift_entry.items()}
            rel_path = drift_entry.get("path")
            tx_id = drift_entry.get("receipt")
            if not isinstance(rel_path, str) or not rel_path or not isinstance(tx_id, str):
                errors.append(f"historical_drift entry {index}: invalid path or receipt")
                continue
            if tx_id not in receipt_by_id:
                errors.append(
                    f"historical_drift entry {index} ({tx_id}, {rel_path}): "
                    "receipt is not a committed receipt"
                )
                continue
            if rel_path in drift_by_path:
                errors.append(f"historical_drift entry {index}: duplicate path {rel_path}")
                continue
            drift_by_path[rel_path] = drift_entry

    if errors:
        return BaselineData(
            chain_keys={},
            drift_by_path={},
            errors=tuple(errors),
            valid=False,
        )
    return BaselineData(
        chain_keys=chain_keys,
        drift_by_path=drift_by_path,
        errors=(),
        valid=True,
    )


def _drift_row_is_baselined(row: dict[str, object], baseline: BaselineData) -> bool:
    if not baseline.valid:
        return False
    path = row.get("path")
    if not isinstance(path, str):
        return False
    entry = baseline.drift_by_path.get(path)
    if entry is None:
        return False
    if entry.get("receipt") != row.get("receipt") or entry.get("expected_sha256") != row.get("expected"):
        return False
    if entry.get("derived_rebuild"):
        return True
    return entry.get("observed_sha256") == row.get("actual")


@dataclass(frozen=True)
class ReceiptChainAnalysis:
    """Complete view of committed receipt chain, live drift, and baseline."""

    receipt_count: int
    non_committed_skipped: int
    malformed_receipts: list[str]
    tracked_paths: int
    records_checked: int
    drift: list[dict[str, object]]
    untracked: list[str]
    all_chain_breaks: list[dict[str, object]]
    active_chain_breaks: list[dict[str, object]]
    baselined_chain_breaks: list[dict[str, object]]
    migration_exempt_breaks: list[dict[str, object]]
    unbaselined_drift: list[dict[str, object]]
    baseline: BaselineData


def analyze_receipt_chain(
    root: Path,
    *,
    receipts: list[dict[str, object]] | None = None,
    malformed: list[str] | None = None,
    record_globs: tuple[str, ...] = RECORD_GLOBS,
    schema_check: Callable[[dict[str, object]], bool] | None = None,
) -> ReceiptChainAnalysis:
    """Analyze committed receipt chain breaks, live drift, and untracked records."""
    if receipts is None:
        loaded, malformed_names = load_receipts(root)
    else:
        loaded = list(receipts)
        malformed_names = list(malformed or [])
    committed, skipped = committed_receipts(loaded)
    last, _ = last_writes(committed)
    records = record_files(root, globs=record_globs)
    drift = compute_drift(root, last)
    tracked = set(last)
    untracked = [path for path in records if path not in tracked]

    raw_breaks = find_chain_breaks(committed)
    baseline = load_chain_baseline(root, committed, raw_breaks, schema_check=schema_check)

    active_breaks: list[dict[str, object]] = []
    baselined_breaks: list[dict[str, object]] = []
    migration_breaks: list[dict[str, object]] = []
    for brk in raw_breaks:
        if brk.get("migration_exempt"):
            migration_breaks.append(brk)
        elif baseline.valid and (str(brk.get("receipt", "")), str(brk.get("path", ""))) in baseline.chain_keys:
            baselined_breaks.append(brk)
        else:
            active_breaks.append(brk)

    unbaselined_drift = [row for row in drift if not _drift_row_is_baselined(row, baseline)]

    return ReceiptChainAnalysis(
        receipt_count=len(loaded),
        non_committed_skipped=skipped,
        malformed_receipts=malformed_names,
        tracked_paths=len(last),
        records_checked=len(records),
        drift=drift,
        untracked=untracked,
        all_chain_breaks=raw_breaks,
        active_chain_breaks=active_breaks,
        baselined_chain_breaks=baselined_breaks,
        migration_exempt_breaks=migration_breaks,
        unbaselined_drift=unbaselined_drift,
        baseline=baseline,
    )


def report_findings(root: Path) -> dict[str, object]:
    """Build the diagnostic payload used by ``tools/receipt_drift.py``."""
    analysis = analyze_receipt_chain(root)
    return {
        "receipts": analysis.receipt_count,
        "non_committed_skipped": analysis.non_committed_skipped,
        "tracked_paths": analysis.tracked_paths,
        "records_checked": analysis.records_checked,
        "drift": analysis.drift,
        "untracked": analysis.untracked,
        "malformed_receipts": analysis.malformed_receipts,
        "chain_breaks": analysis.active_chain_breaks,
        "baselined_chain_breaks": len(analysis.baselined_chain_breaks),
        "migration_exempt_breaks": len(analysis.migration_exempt_breaks),
        "baseline_errors": list(analysis.baseline.errors),
    }


def has_unreceipted_history_or_drift(root: Path, receipts: list[dict[str, object]]) -> bool:
    """True if committed receipts show un-baselined chain breaks or live byte drift.

    Synthetic unit-test receipts without ``status: committed`` and ``writes``
    produce zero committed writes and answer False. If a baseline file exists
    and is invalid, fail closed and answer True so drift cannot silently settle.
    """
    baseline_path = root / CHAIN_BASELINE_RELATIVE
    if baseline_path.exists() or baseline_path.is_symlink():
        committed, _ = committed_receipts(receipts)
        raw_breaks = find_chain_breaks(committed)
        baseline = load_chain_baseline(root, committed, raw_breaks)
        if not baseline.valid:
            return True
    else:
        committed, _ = committed_receipts(receipts)
    if not committed:
        return False
    analysis = analyze_receipt_chain(root, receipts=committed)
    if not analysis.baseline.valid:
        return True
    return bool(analysis.active_chain_breaks or analysis.unbaselined_drift)
