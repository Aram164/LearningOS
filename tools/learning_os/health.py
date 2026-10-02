"""One explicit LearningOS health report; no watcher or daemon."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import stat
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
from learning_os.manifest_identity import manifest_text
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


def _shipped_file_digest(path: Path) -> str | None:
    """The `sha256:` digest of a shipped plugin file, or None when unusable.

    Mirrors `plugin-assets.mjs shippedFileProblem`: only a regular file
    counts — a symlink, directory, or missing path is not a build the
    vault is running.
    """
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return None
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _ui_plugin_check(root: Path, *, ui_root: Path | None = None,
                     installed_dir: Path | None = None) -> dict[str, Any]:
    """Whether the vault has the UI checkout's current plugin build installed.

    The same comparison `npm run install:status`
    (`scripts/check-install-current.mjs`) performs, from Core's side of
    the pair: every file `plugin-assets.json` declares shipped must be
    byte-identical between the built `plugin/` directory and the vault's
    installed copy. A stale build is a warning, not an error — the app
    still runs — and an absent UI checkout or a vault with nothing
    installed is unknown, never stale: Core is usable alone.
    """
    root = root.resolve()
    ui = ui_root.resolve() if ui_root is not None else root.parent / "obsidian-ui"
    built_dir = ui / "plugin"
    installed = (installed_dir.absolute() if installed_dir is not None
                 else root / ".obsidian" / "plugins" / "learningos-ui")
    try:
        manifest = json.loads((ui / "plugin-assets.json").read_text(encoding="utf-8"))
        if (not isinstance(manifest, dict)
                or set(manifest) != {"schema_version", "type", "shipped", "vault_owned"}
                or manifest["schema_version"] != 1
                or manifest["type"] != "learningos-ui-plugin-assets"):
            raise ValueError("plugin-assets.json has an unsupported shape or version")
        shipped = manifest.get("shipped")
        vault_owned = manifest.get("vault_owned")
        for field, names in (("shipped", shipped), ("vault_owned", vault_owned)):
            if (not isinstance(names, list) or not names
                    or not all(isinstance(name, str) and name.strip()
                               and name not in {".", ".."}
                               and "/" not in name and "\\" not in name for name in names)
                    or len(set(names)) != len(names)):
                raise ValueError(f"plugin-assets.json has invalid {field} filenames")
        if set(shipped) & set(vault_owned):
            raise ValueError("plugin-assets.json overlaps shipped and vault-owned filenames")
    except (OSError, ValueError) as exc:
        return _check(
            "ui-plugin-current", "unknown",
            f"The UI shipping manifest is unavailable: {exc}.",
            "core-ui", "Open the paired UI checkout and run `npm run build`.",
        )
    installed_missing = False
    for directory in (installed.parent.parent, installed.parent, installed):
        try:
            info = directory.lstat()
        except FileNotFoundError:
            installed_missing = True
            continue
        except OSError as exc:
            return _check(
                "ui-plugin-current", "error",
                f"The installed plugin path cannot be inspected: {directory}: {exc}.",
                "core-ui", "Review the path yourself; nothing was changed.",
            )
        if not stat.S_ISDIR(info.st_mode):
            return _check(
                "ui-plugin-current", "error",
                f"The installed plugin path is not a real directory: {directory}.",
                "core-ui", "Review the path yourself; nothing was changed.",
            )
    if installed_missing:
        return _check(
            "ui-plugin-current", "unknown",
            "No plugin is installed in this vault.",
            "core-ui", "Run `python3 install.py` in the UI checkout to install one.",
        )
    try:
        journal = installed.parent / ".learningos-ui-install-transaction.json"
        journal.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        return _check(
            "ui-plugin-current", "error",
            f"The plugin install transaction cannot be inspected: {exc}.",
            "core-ui", "Review the path yourself; nothing was changed.",
        )
    else:
        return _check(
            "ui-plugin-current", "error",
            f"An interrupted plugin install transaction is still present: {journal}.",
            "core-ui", "Review the install transaction before retrying; nothing was changed.",
        )
    try:
        if not stat.S_ISDIR(built_dir.lstat().st_mode):
            raise ValueError("not a directory")
    except (OSError, ValueError):
        return _check(
            "ui-plugin-current", "unknown",
            "The UI checkout has no built plugin directory to compare against.",
            "core-ui", "Run `npm run build` in the UI checkout first.",
        )
    rows = [{
        "name": name,
        "built": _shipped_file_digest(built_dir / name),
        "installed": _shipped_file_digest(installed / name),
    } for name in shipped]
    missing_built = sorted(row["name"] for row in rows if row["built"] is None)
    if missing_built:
        return _check(
            "ui-plugin-current", "unknown",
            "The UI build output is incomplete: "
            f"{', '.join(missing_built)} missing from {built_dir}.",
            "core-ui", "Run `npm run build` in the UI checkout first.",
        )
    try:
        surplus_built = sorted(entry.name for entry in built_dir.iterdir()
                               if entry.name not in shipped)
    except OSError as exc:
        return _check(
            "ui-plugin-current", "unknown",
            f"The UI build output cannot be inspected: {exc}.",
            "core-ui", "Review the build output yourself; nothing was changed.",
        )
    if surplus_built:
        return _check(
            "ui-plugin-current", "error",
            "The UI build has files outside its shipping manifest: "
            f"{', '.join(surplus_built)}.",
            "core-ui", "Review the build output yourself; nothing was changed.",
        )
    try:
        owned = set(shipped) | set(vault_owned)
        unexpected = sorted(
            entry.name for entry in installed.iterdir() if entry.name not in owned)
    except OSError as exc:
        return _check(
            "ui-plugin-current", "error",
            f"The installed plugin directory cannot be inspected: {exc}.",
            "core-ui", "Review the path yourself; nothing was changed.",
        )
    vault_problems = []
    for name in vault_owned:
        candidate = installed / name
        try:
            present = candidate.lstat() is not None
        except OSError:
            present = False
        if present and _shipped_file_digest(candidate) is None:
            vault_problems.append(f"{name} is not a regular file")

    def _build_identity(directory: Path) -> dict[str, Any]:
        try:
            info = json.loads((directory / "build-info.json").read_text(
                encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(info, dict):
            return {}
        return {key: info[key] for key in (
            "source_fingerprint", "source_revision", "source_dirty",
            "core_revision", "core_dirty") if key in info}

    if all(row["installed"] is None for row in rows) and not unexpected and not vault_problems:
        return _check(
            "ui-plugin-current", "unknown",
            "No plugin is installed in this vault.",
            "core-ui", "Run `python3 install.py` in the UI checkout to install one.",
        )
    differing = [row for row in rows if row["built"] != row["installed"]]
    if not differing and not unexpected and not vault_problems:
        return _check(
            "ui-plugin-current", "ok",
            f"The installed plugin matches this build ({len(rows)} shipped files match).",
            "core-ui", "Reinstall the plugin after every UI rebuild.",
        )
    details: dict[str, Any] = {
        "differing": [
            {"name": row["name"], "built": row["built"],
             "installed": row["installed"]} for row in differing
        ],
        "unexpected_entries": unexpected,
        "vault_owned_problems": vault_problems,
        "built": _build_identity(built_dir),
        "installed_build": _build_identity(installed),
    }
    if unexpected or vault_problems:
        summary = ("The installed plugin directory holds entries this build "
                   "does not own.")
    else:
        summary = ("THE VAULT IS RUNNING A DIFFERENT BUILD: "
                   f"{', '.join(row['name'] for row in differing)} "
                   "differ(s) from this UI checkout — reinstall the plugin.")
    return _check(
        "ui-plugin-current", "warning", summary,
        "core-ui", "Run `python3 install.py` in the UI checkout, then reload "
        "Obsidian with Cmd+R.",
        **details,
    )


def _payload_difference(expected: Any, stored: Any) -> dict[str, Any]:
    """How one top-level manifest section differs, without printing the manifest.

    `records` is thousands of rows; quoting both copies into a health report
    helps nobody. What the operator needs is which section is wrong and how far
    off it is, so a collection reports its size and the first differing entry,
    and a scalar reports both values.
    """
    if isinstance(expected, list) and isinstance(stored, list):
        first = next((index for index, (left, right)
                      in enumerate(zip(expected, stored, strict=False)) if left != right),
                     min(len(expected), len(stored)))
        return {"expected": f"{len(expected)} entries", "stored": f"{len(stored)} entries",
                "first_difference_at": first}
    if isinstance(expected, dict) and isinstance(stored, dict):
        keys = sorted(key for key in set(expected) | set(stored)
                      if expected.get(key) != stored.get(key))
        return {"expected": f"{len(expected)} keys", "stored": f"{len(stored)} keys",
                "differing_keys": keys[:10]}
    return {"expected": expected, "stored": stored}


def _projection_check(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    path = root / "generated" / "manifest.json"
    if not path.is_file() or path.is_symlink():
        return _check(
            "projection-state", "warning", "The generated manifest is missing.",
            "core", "Regenerate projections after the next approved transaction.",
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return _check(
            "projection-state", "error", f"The generated manifest is unreadable: {exc}",
            "core", "Regenerate projections from validated canonical files.",
        )
    # Byte-identical to the fresh build implies valid (the fresh build was
    # just enforced) and current — no schema pass needed. Any difference,
    # including stale stamps or a corrupt file, falls through to validation.
    if raw == manifest_text(expected).encode("utf-8"):
        return _check(
            "projection-state", "ok",
            "The generated manifest matches the current canonical snapshot.",
            "core", "Regenerate projections after the next approved transaction.",
            mismatches={},
        )
    try:
        stored = json.loads(raw.decode("utf-8"))

        contract_ok, contract_message = check_manifest_contract(stored, root)
        if not contract_ok:
            return _check(
                "projection-state", "error", f"The stored manifest fails contract validation: {contract_message}",
                "core", "Regenerate projections from validated canonical files.",
            )

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

        if not mismatches:
            # Identifiers matching is a claim about the file, not a fact about
            # its contents: a manifest whose records were replaced keeps its
            # header intact. So the payload itself is compared.
            #
            # Four `_generated` fields are exempt because they move without the
            # projection being wrong: `generated_at` advances on every run;
            # `source_revision` and `source_dirty` describe the checkout at the
            # moment of generation, not the canonical content (a later commit or
            # an unrelated edit changes both); `generator` and `warning` are
            # provenance strings whose compatibility-bearing counterparts —
            # `contract_version` and `schema_sha256` — are compared above.
            exempt_fields = ("generated_at", "source_revision", "source_dirty",
                             "generator", "warning")

            stored_payload = {k: v for k, v in stored.items() if k != "_generated"}
            expected_payload = {k: v for k, v in expected.items() if k != "_generated"}
            stored_meta = {k: v for k, v in stored_generated.items() if k not in exempt_fields}
            expected_meta = {k: v for k, v in expected_generated.items()
                             if k not in exempt_fields}

            # Name what actually differs. "differs" tells the operator only that
            # something is wrong, which is the same failure as reporting `ok`:
            # neither says which part of the projection to distrust.
            for key in sorted(set(stored_payload) | set(expected_payload)):
                if stored_payload.get(key) != expected_payload.get(key):
                    mismatches[key] = _payload_difference(
                        expected_payload.get(key), stored_payload.get(key))
            for key in sorted(set(stored_meta) | set(expected_meta)):
                if stored_meta.get(key) != expected_meta.get(key):
                    mismatches[f"_generated.{key}"] = {
                        "expected": expected_meta.get(key), "stored": stored_meta.get(key)}

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
    # build_manifest already enforced the contract (raising on failure), so a
    # second schema pass over the same bytes proves nothing. Record the same
    # success message check() would return, without re-validating.
    version = declared_version(root)
    contract_message = (
        f"manifest contract v{version} matches {len(manifest)} top-level keys"
    )
    checks.append(_check(
        "manifest-contract", "ok", contract_message,
        "core-ui", "Ship the producer schema and UI lock as one coordinated version.",
    ))
    checks.append(_core_ui_lock_check(root))
    checks.append(_ui_plugin_check(root))
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
