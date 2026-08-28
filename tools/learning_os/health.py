"""One explicit LearningOS health report; no watcher or daemon."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from learning_os.contracts.capability_catalog import load_capability_catalog
from learning_os.contracts.json_schema import validate_contract
from learning_os.contracts.manifest_contract import (
    check as check_manifest_contract,
)
from learning_os.contracts.manifest_contract import (
    declared_schema_sha256,
    declared_version,
)
from learning_os.genout import build_backlinks, build_manifest, stable_generated_at
from learning_os.legacy_archive import load_legacy_archive_lock
from learning_os.loader import load_repo
from learning_os.masters_planning import load_master_catalog
from learning_os.material_synthesis import material_synthesis_freshness
from learning_os.rules import validate


class HealthReportError(ValueError):
    pass


def _check(check_id: str, status: str, summary: str, owner: str, remedy: str,
           **details: Any) -> dict[str, Any]:
    row = {
        "id": check_id,
        "status": status,
        "summary": summary,
        "owner": owner,
        "remedy": remedy,
    }
    if details:
        row["details"] = details
    return row


_TIME_MACHINE_STAMP = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2}-\d{6})(?!\d)")


def _time_machine_check(
    *,
    now: dt.datetime | None = None,
    local_timezone: dt.tzinfo | None = None,
) -> dict[str, Any]:
    current = now or dt.datetime.now().astimezone()
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.UTC)
    local_timezone = local_timezone or dt.datetime.now().astimezone().tzinfo or dt.UTC
    current = current.astimezone(local_timezone)
    try:
        result = subprocess.run(
            ["tmutil", "destinationinfo"], capture_output=True, text=True, timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return _check(
            "backup", "unknown", "Time Machine state is unavailable.", "operator",
            "Verify the encrypted external backup destination manually.",
        )
    if result.returncode != 0 or "No destinations configured" in (result.stdout + result.stderr):
        return _check(
            "backup", "warning", "No Time Machine destination is configured.", "operator",
            "After selecting the external drive, configure encryption and complete a restore drill.",
        )
    encrypted = bool(re.search(
        r"(?im)^\s*(?:Encryption|Encrypted)\s*[:=]\s*(?:1|yes|true|on)\s*$",
        result.stdout,
    ))
    try:
        latest = subprocess.run(
            ["tmutil", "latestbackup"], capture_output=True, text=True, timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        latest = None
    latest_text = "" if latest is None else latest.stdout + latest.stderr
    match = _TIME_MACHINE_STAMP.search(latest_text)
    latest_at: dt.datetime | None = None
    if latest is not None and latest.returncode == 0 and match:
        latest_at = dt.datetime.strptime(
            match.group(1), "%Y-%m-%d-%H%M%S"
        ).replace(tzinfo=current.tzinfo)
    age_hours = (
        (current - latest_at).total_seconds() / 3600
        if latest_at is not None else None
    )
    recent = age_hours is not None and 0 <= age_hours <= 24
    ok = encrypted and recent
    if not encrypted:
        summary = "Time Machine is configured, but encryption was not proven."
    elif latest_at is None:
        summary = "Encrypted Time Machine is configured, but no completed backup was proven."
    elif age_hours < 0:
        summary = "The latest Time Machine backup timestamp is in the future."
    elif not recent:
        summary = "The latest encrypted Time Machine backup is older than one day."
    else:
        summary = "Encrypted Time Machine has a completed backup within one day."
    return _check(
        "backup", "ok" if ok else "warning", summary,
        "operator",
        "Confirm encryption, complete a backup, and repeat the restore-to-new-directory drill.",
        encryption_proven=encrypted,
        latest_backup_at=latest_at.isoformat() if latest_at is not None else None,
        age_hours=round(age_hours, 2) if age_hours is not None else None,
        recovery_point_objective_hours=24,
    )


def _core_ui_lock_check(root: Path) -> dict[str, Any]:
    """Compare the producer lock to the explicit sibling UI mirror, if present."""
    expected_version = declared_version(root)
    ui_lock = (
        root.parent
        / "obsidian-ui"
        / "contracts"
        / f"manifest-v{expected_version}.lock.json"
    )
    if not ui_lock.is_file() or ui_lock.is_symlink():
        return _check(
            "schema-core-ui-lock", "unknown",
            "The Obsidian UI manifest lock is unavailable from this Core checkout.",
            "core-ui", "Open the paired UI checkout and run its contract check.",
        )
    try:
        lock = json.loads(ui_lock.read_text(encoding="utf-8"))
        expected_hash = declared_schema_sha256(root)
        actual_version = lock.get("contract_version") if isinstance(lock, dict) else None
        actual_hash = lock.get("schema_sha256") if isinstance(lock, dict) else None
        matched = actual_version == expected_version and actual_hash == expected_hash
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check(
            "schema-core-ui-lock", "error", f"Cannot verify the UI contract lock: {exc}",
            "core-ui", "Repair the UI lock and rerun the paired contract check.",
        )
    return _check(
        "schema-core-ui-lock", "ok" if matched else "error",
        "Core and UI require the same Manifest version and exact schema hash."
        if matched else "Core and UI Manifest locks disagree.",
        "core-ui", "Ship the producer schema and UI lock as one coordinated change.",
        core_version=expected_version,
        ui_version=actual_version,
        core_schema_sha256=expected_hash,
        ui_schema_sha256=actual_hash,
    )


def _projection_check(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    path = root / "generated" / "manifest.json"
    if not path.is_file() or path.is_symlink():
        return _check(
            "projection-state", "warning", "The generated manifest is missing.",
            "core", "Regenerate projections after the next approved transaction.",
        )
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
        expected_generated = expected.get("_generated") or {}
        stored_generated = stored.get("_generated") if isinstance(stored, dict) else {}
        fields = ("contract_version", "schema_sha256", "source_fingerprint", "snapshot_id")
        mismatches = {
            field: {
                "expected": expected_generated.get(field),
                "stored": stored_generated.get(field) if isinstance(stored_generated, dict) else None,
            }
            for field in fields
            if not isinstance(stored_generated, dict)
            or stored_generated.get(field) != expected_generated.get(field)
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check(
            "projection-state", "error", f"The generated manifest is unreadable: {exc}",
            "core", "Regenerate projections from validated canonical files.",
        )
    return _check(
        "projection-state", "ok" if not mismatches else "warning",
        "The generated manifest matches the current canonical snapshot."
        if not mismatches else "The generated manifest is stale or on the wrong contract.",
        "core", "Regenerate projections after the next approved transaction.",
        mismatches=mismatches,
    )


def build_health_report(root: Path, *, now: dt.datetime | None = None) -> dict[str, Any]:
    root = root.resolve()
    repo = load_repo(root)
    checks: list[dict[str, Any]] = []

    issues = validate(repo, online=False)
    errors = [str(issue) for issue in issues if issue.severity == "E"]
    warnings = [str(issue) for issue in issues if issue.severity == "W"]
    checks.append(_check(
        "validation", "error" if errors else ("warning" if warnings else "ok"),
        f"Validation found {len(errors)} error(s) and {len(warnings)} warning(s).",
        "core",
        "Clear every error before a live canonical transaction. Warnings stay "
        "visible and never block; `python tools/warning_baseline.py --check` "
        "is what refuses a NEW one.",
        errors=errors[:20], warnings=warnings[:20],
    ))

    route_issues = [
        issue for issue in issues
        if issue.code.startswith("ROUTE-") or "SOURCE-SELECTION" in issue.code
    ]
    route_errors = [str(issue) for issue in route_issues if issue.severity == "E"]
    route_warnings = [str(issue) for issue in route_issues if issue.severity == "W"]
    checks.append(_check(
        "route-integrity",
        "error" if route_errors else ("warning" if route_warnings else "ok"),
        f"Route validation found {len(route_errors)} error(s) and "
        f"{len(route_warnings)} warning(s).",
        # The v13 route-identity migration was applied and recorded
        # (system/contracts/data-contract.yaml, generation 13). Sending a
        # reader back to it left the one remedy in this report that could not
        # be carried out.
        "curriculum",
        "Repair routes through the plan gateway — `los module-plan-import` "
        "(system/PLAN-CREATION-SOP.md). Never hand-edit a source map.",
        errors=route_errors[:20], warnings=route_warnings[:20],
    ))

    generated_at = stable_generated_at(root)
    manifest = build_manifest(repo, generated_at, build_backlinks(repo, generated_at))
    contract_ok, contract_message = check_manifest_contract(manifest, root)
    checks.append(_check(
        "manifest-contract", "ok" if contract_ok else "error", contract_message,
        "core-ui", "Ship the producer schema and UI lock as one coordinated version.",
    ))
    checks.append(_core_ui_lock_check(root))
    checks.append(_projection_check(root, manifest))

    try:
        load_capability_catalog(root)
        checks.append(_check(
            "capability-authority", "ok", "Capability declarations and scopes load successfully.",
            "core", "Keep every public write behind the declared scope matcher.",
        ))
    except Exception as exc:
        checks.append(_check(
            "capability-authority", "error", str(exc), "core",
            "Repair the capability contract before accepting writes.",
        ))

    synthesis_rows = []
    for unit in repo.units.values():
        path = unit.path.parent / "material-synthesis.yaml"
        if not path.is_file():
            continue
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("synthesis is not an object")
            validate_contract(root, "unit-material-synthesis.schema.json", value)
            freshness = material_synthesis_freshness(root, unit.id, value)
        except Exception as exc:
            freshness = {"status": "stale", "reasons": [str(exc)]}
        synthesis_rows.append({"unit_id": unit.id, **freshness})
    stale = [row for row in synthesis_rows if row["status"] != "current"]
    checks.append(_check(
        "material-synthesis", "warning" if stale else "ok",
        f"{len(synthesis_rows) - len(stale)} current and {len(stale)} stale dossier(s).",
        "learner", "Review and republish only the affected unit dossier.",
        dossiers=synthesis_rows,
    ))

    try:
        lock = load_legacy_archive_lock(root)
        if lock is None:
            checks.append(_check(
                "legacy-archive", "unknown", "No reviewed Legacy archive lock is published.",
                "operator", "Run the explicit allowlist inspection and approve its lock.",
            ))
        else:
            state = lock["verification"]["status"]
            checks.append(_check(
                "legacy-archive", "ok" if state == "verified" else "warning",
                f"Legacy archive last verified at {lock['verification']['verified_at']} ({state}).",
                "operator", "Re-run the explicit safe allowlist inspection when provenance changes.",
                excluded_count=lock["excluded"]["count"],
            ))
    except Exception as exc:
        checks.append(_check(
            "legacy-archive", "error", str(exc), "operator",
            "Replace the lock only through the reviewed archive-lock capability.",
        ))

    try:
        catalog = load_master_catalog(root)
        candidate_ids = [] if catalog is None else [
            *(row["id"] for row in catalog["candidate_modules"]),
            *(row["id"] for row in catalog["candidate_sources"]),
        ]
        encoded_manifest = json.dumps(manifest, ensure_ascii=False)
        leaks = [candidate_id for candidate_id in candidate_ids if candidate_id in encoded_manifest]
        checks.append(_check(
            "masters-isolation", "error" if leaks else "ok",
            "Prospective candidates are isolated from the normal manifest."
            if not leaks else "Prospective candidate IDs leaked into the normal manifest.",
            "core", "Keep all prospective records behind the explicit dashboard query.",
            leaked_ids=leaks,
        ))
    except Exception as exc:
        checks.append(_check(
            "masters-isolation", "error", str(exc), "core",
            "Repair or remove the sanitized catalog before opening the planning surface.",
        ))

    timestamp = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC).replace(microsecond=0)
    checks.append(_time_machine_check(now=timestamp))
    report = {
        "schema_version": 1,
        "type": "health-report",
        "generated_at": timestamp.isoformat(),
        "status": "healthy" if all(row["status"] == "ok" for row in checks)
        else "attention-required",
        "checks": checks,
    }
    try:
        validate_contract(root, "health-report.schema.json", report)
    except ValueError as exc:
        raise HealthReportError(str(exc)) from exc
    return report
