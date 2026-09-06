"""Read-only, allowlisted backup inventory and restore verification."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from learning_os.contracts.json_schema import validate_contract
from learning_os.contracts.manifest_contract import declared_version


class BackupManifestError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BackupManifestError(f"backup path is unreadable: {path}") from exc
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _refuse_unreadable(exc: OSError) -> None:
    """`os.walk` error callback: refuse the inventory rather than skip silently.

    Only admitted directories reach this. Excluded names are pruned before the
    walk descends into them, so anything that fails here is a tree the contract
    asked for and we could not read — which is a backup that would omit it.
    """
    raise BackupManifestError(
        f"backup path is unreadable: {exc.filename or '<unknown path>'}"
    ) from exc


def _safe_relative(value: str) -> PurePosixPath:
    if value == ".":
        return PurePosixPath(".")
    rel = PurePosixPath(value)
    if (
        not isinstance(value, str)
        or "\\" in value
        or rel.is_absolute()
        or not rel.parts
        or rel.as_posix() != value
        or any(part in {"", ".", ".."} for part in rel.parts)
    ):
        raise BackupManifestError(f"unsafe backup root declaration: {value}")
    return rel


def _inspect_path(path: Path) -> os.stat_result | None:
    """Distinguish genuine absence from failure to inspect an admitted path."""
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise BackupManifestError(f"backup path is unreadable: {path}") from exc


def _load_contract(root: Path) -> dict[str, Any]:
    path = root / "system" / "contracts" / "backup-roots.yaml"
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BackupManifestError(f"cannot read backup root contract: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1 \
            or value.get("contract") != "learningos-backup-roots":
        raise BackupManifestError("backup root contract has an unsupported shape")
    roots = value.get("roots")
    if not isinstance(roots, dict) or set(roots) != {"core", "ui", "materials"}:
        raise BackupManifestError("backup root contract must declare core, ui, and materials")
    for label, row in roots.items():
        if not isinstance(row, dict):
            raise BackupManifestError(f"backup root {label} must be an object")
        for field in ("trees", "files"):
            entries = row.get(field)
            if not isinstance(entries, list) or any(not isinstance(item, str) for item in entries):
                raise BackupManifestError(f"backup root {label}.{field} must be a string list")
            for item in entries:
                _safe_relative(item)
    return value


PLUGIN_ASSETS_TYPE = "learningos-ui-plugin-assets"
PLUGIN_ASSETS_KEYS = {"schema_version", "type", "shipped", "vault_owned"}


def _asset_names(values: Any, field: str) -> list[str]:
    """Mirror the UI installer's `_check_names` for either ownership list."""
    if not isinstance(values, list) or not values:
        if field == "shipped":
            raise BackupManifestError("plugin-assets.json declares no shipped assets")
        raise BackupManifestError(f"plugin-assets.json {field} must be a non-empty array")
    for name in values:
        if not isinstance(name, str) or not name.strip():
            raise BackupManifestError(f"plugin-assets.json {field} entries must be filenames")
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise BackupManifestError(
                f"plugin-assets.json {field} entry {name!r} is not a bare filename"
            )
    if len(set(values)) != len(values):
        raise BackupManifestError(f"plugin-assets.json repeats a {field} asset")
    return values


def read_shipped_assets(ui_root: Path) -> list[str]:
    """The UI's own declaration of what it installs into a vault.

    Core cannot import the UI's installer to ask — they are separate
    repositories, and a restore root is only a directory on disk — so the shape
    `install.py` enforces is repeated here, deliberately and in one place. The
    bare-filename rule is not decoration: joining a `..` onto the plugin
    directory would walk a verification check out of the tree it is verifying.
    """
    path = ui_root / "plugin-assets.json"
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupManifestError(f"plugin-assets.json could not be read: {exc}") from exc
    if not isinstance(parsed, dict):
        raise BackupManifestError("plugin-assets.json is not an object")
    if set(parsed) != PLUGIN_ASSETS_KEYS:
        raise BackupManifestError(
            "plugin-assets.json must carry exactly " + ", ".join(sorted(PLUGIN_ASSETS_KEYS))
        )
    # bool is a subclass of int, so JSON `true` would otherwise pass as 1.
    if type(parsed.get("schema_version")) is not int or parsed["schema_version"] != 1:
        raise BackupManifestError("plugin-assets.json has an unsupported schema_version")
    if parsed.get("type") != PLUGIN_ASSETS_TYPE:
        raise BackupManifestError("plugin-assets.json has an unsupported type")
    shipped = _asset_names(parsed["shipped"], "shipped")
    vault_owned = _asset_names(parsed["vault_owned"], "vault_owned")
    overlap = sorted(set(shipped) & set(vault_owned))
    if overlap:
        raise BackupManifestError(
            f"plugin-assets.json: {', '.join(overlap)} cannot be both shipped and vault-owned"
        )
    return shipped


def _inside(authority: Path, relative: str) -> Path:
    rel = _safe_relative(relative)
    authority = authority.resolve()
    lexical = authority if relative == "." else authority.joinpath(*rel.parts)
    cursor = authority
    for part in (() if relative == "." else rel.parts):
        cursor = cursor / part
        if cursor.is_symlink():
            raise BackupManifestError(
                f"backup declaration traverses a symlink: {relative}"
            )
    try:
        resolved = lexical.resolve(strict=False)
        resolved.relative_to(authority)
    except (OSError, ValueError) as exc:
        raise BackupManifestError(f"backup declaration escapes {authority}: {relative}") from exc
    return lexical


def _admit_file(authority: Path, path: Path, excluded: set[str]) -> bool:
    try:
        relative = path.relative_to(authority)
    except ValueError:
        return False
    if any(part in excluded for part in relative.parts):
        return False
    st = _inspect_path(path)
    if st is None:
        return False
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        return False
    try:
        path.resolve().relative_to(authority.resolve())
    except OSError as exc:
        raise BackupManifestError(f"backup path is unreadable: {path}") from exc
    except ValueError:
        return False
    return True


def build_backup_manifest(
    root: Path,
    *,
    ui_root: Path | None = None,
    materials_root: Path | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    ui_root = (ui_root or root.parent / "obsidian-ui").resolve()
    materials_root = (materials_root or root.parent / "materials").resolve()
    authorities = {"core": root, "ui": ui_root, "materials": materials_root}
    contract = _load_contract(root)
    excluded = set(contract.get("excluded_names") or [])
    entries: dict[tuple[str, str], dict[str, Any]] = {}
    for label, authority in authorities.items():
        if not authority.is_dir():
            raise BackupManifestError(f"backup authority is unavailable: {label}: {authority}")
        declared = contract["roots"][label]
        for relative in declared["files"]:
            path = _inside(authority, relative)
            if _admit_file(authority, path, excluded):
                rel = path.relative_to(authority).as_posix()
                entries[(label, rel)] = {
                    "root": label, "path": rel, "size": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
        for relative in declared["trees"]:
            if any(part in excluded for part in PurePosixPath(relative).parts):
                continue
            tree = _inside(authority, relative)
            tree_stat = _inspect_path(tree)
            if tree_stat is None or not stat.S_ISDIR(tree_stat.st_mode):
                continue
            # `rglob` suppresses the errors raised while descending, so an
            # unreadable directory yielded nothing and raised nothing — the same
            # answer as an empty one, and its contents left the inventory
            # without a trace (#25). `os.walk` reports those failures instead.
            # `excluded` is applied to directory names *before* descending, so a
            # tree the contract deliberately skips is never read, never fails,
            # and is never confused with one that could not be read.
            for parent, dirs, files in os.walk(tree, onerror=_refuse_unreadable):
                dirs[:] = [name for name in dirs if name not in excluded]
                for name in files:
                    path = Path(parent) / name
                    if _admit_file(authority, path, excluded):
                        rel = path.relative_to(authority).as_posix()
                        entries[(label, rel)] = {
                            "root": label, "path": rel, "size": path.stat().st_size,
                            "sha256": _sha256_file(path),
                        }
        if label == "ui":
            # Derived, not declared: the contract names `plugin-assets.json` and
            # this reads what that declares, so the shipping inventory has one
            # author. A declared asset the checkout cannot ship is refused here
            # rather than quietly left out — `install.py` refuses the same case,
            # and a backup that omits it would restore a plugin that cannot be
            # installed.
            for name in read_shipped_assets(authority):
                path = _inside(authority, f"plugin/{name}")
                if not _admit_file(authority, path, excluded):
                    raise BackupManifestError(
                        f"declared plugin asset cannot be backed up: plugin/{name}"
                    )
                rel = path.relative_to(authority).as_posix()
                entries[(label, rel)] = {
                    "root": label, "path": rel, "size": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
    rows = [entries[key] for key in sorted(entries)]
    aggregate = "sha256:" + hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    timestamp = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC).replace(microsecond=0)
    manifest = {
        "schema_version": 1,
        "type": "backup-manifest",
        "generated_at": timestamp.isoformat(),
        "roots": sorted(authorities),
        "entries": rows,
        "aggregate_sha256": aggregate,
    }
    try:
        validate_contract(root, "backup-manifest.schema.json", manifest)
    except ValueError as exc:
        raise BackupManifestError(str(exc)) from exc
    return manifest


def verify_backup_manifest(
    root: Path,
    manifest: dict[str, Any],
    *,
    restored_core: Path,
    restored_ui: Path,
    restored_materials: Path,
) -> dict[str, Any]:
    try:
        validate_contract(root, "backup-manifest.schema.json", manifest)
    except ValueError as exc:
        raise BackupManifestError(str(exc)) from exc
    authorities = {
        "core": restored_core.resolve(),
        "ui": restored_ui.resolve(),
        "materials": restored_materials.resolve(),
    }
    issues = []
    rows = list(manifest["entries"])
    identities = [(row["root"], row["path"]) for row in rows]
    if len(identities) != len(set(identities)):
        issues.append({"root": "manifest", "path": "<entries>",
                       "issue": "duplicate-entry"})
    expected_aggregate = "sha256:" + hashlib.sha256(
        json.dumps(
            rows,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if manifest["aggregate_sha256"] != expected_aggregate:
        issues.append({"root": "manifest", "path": "<aggregate>",
                       "issue": "aggregate-mismatch"})
    for row in rows:
        if row["root"] not in authorities:
            issues.append({"root": row["root"], "path": row["path"],
                           "issue": "unknown-root"})
            continue
        authority = authorities[row["root"]]
        path = _inside(authority, row["path"])
        if not path.is_file() or path.is_symlink():
            issues.append({"root": row["root"], "path": row["path"], "issue": "missing"})
        elif path.stat().st_size != row["size"] or _sha256_file(path) != row["sha256"]:
            issues.append({"root": row["root"], "path": row["path"], "issue": "checksum-mismatch"})
    return {"ok": not issues, "checked": len(manifest["entries"]), "issues": issues}


def _overlaps(left: Path, right: Path) -> bool:
    left = left.resolve()
    right = right.resolve()
    return left == right or left in right.parents or right in left.parents


def verify_restored_system(
    root: Path,
    manifest: dict[str, Any],
    *,
    restored_core: Path,
    restored_ui: Path,
    restored_materials: Path,
) -> dict[str, Any]:
    """Verify hashes, projections, validation, and a trusted restored UI bundle.

    This operates only on a separate restore tree.  It intentionally does not
    install the UI into a live vault or open Obsidian; those remain explicit
    post-restore approval steps. It executes the inventoried installer in
    dry-run mode: hashes prove integrity, not the trustworthiness of its code.
    """
    live_roots = (root.resolve(), (root.parent / "obsidian-ui").resolve(),
                  (root.parent / "materials").resolve())
    restored_roots = (
        restored_core.resolve(), restored_ui.resolve(), restored_materials.resolve(),
    )
    if any(_overlaps(restored, live) for restored in restored_roots for live in live_roots):
        raise BackupManifestError(
            "restore verification requires three new directories outside every live root"
        )
    if any(
        _overlaps(left, right)
        for index, left in enumerate(restored_roots)
        for right in restored_roots[index + 1:]
    ):
        raise BackupManifestError("restored Core, UI, and materials roots must be disjoint")

    checksum = verify_backup_manifest(
        root,
        manifest,
        restored_core=restored_core,
        restored_ui=restored_ui,
        restored_materials=restored_materials,
    )
    checks: list[dict[str, Any]] = [{
        "id": "checksums",
        "ok": checksum["ok"],
        "detail": checksum,
    }]
    if not checksum["ok"]:
        return {"ok": False, "checks": checks, "manual_ui_open_required": True}

    try:
        from learning_os.genout import generate_all, write_outputs
        from learning_os.loader import load_repo
        from learning_os.rules import validate

        repo = load_repo(restored_core)
        errors = [str(issue) for issue in validate(repo, online=False) if issue.severity == "E"]
        checks.append({"id": "canonical-validation", "ok": not errors,
                       "detail": {"errors": errors[:20]}})
        if not errors:
            outputs = generate_all(repo)
            write_outputs(repo, outputs)
            projected = json.loads(outputs["manifest.json"])
            checks.append({"id": "projection-regeneration", "ok": True,
                           "detail": {"snapshot_id": projected["_generated"]["snapshot_id"]}})
        else:
            projected = None
            checks.append({"id": "projection-regeneration", "ok": False,
                           "detail": {"reason": "canonical validation failed"}})
    except Exception as exc:
        projected = None
        checks.append({"id": "canonical-validation", "ok": False,
                       "detail": {"error": str(exc)}})
        checks.append({"id": "projection-regeneration", "ok": False,
                       "detail": {"reason": "Core restore could not be loaded"}})

    try:
        version = declared_version(restored_core)
        lock_path = restored_ui / "contracts" / f"manifest-v{version}.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        generated = (projected or {}).get("_generated") or {}
        contract_ok = (
            lock.get("contract_version") == generated.get("contract_version")
            and lock.get("schema_sha256") == generated.get("schema_sha256")
        )
        checks.append({"id": "ui-contract-lock", "ok": contract_ok, "detail": {
            "ui_version": lock.get("contract_version"),
            "core_version": generated.get("contract_version"),
            "ui_schema_sha256": lock.get("schema_sha256"),
            "core_schema_sha256": generated.get("schema_sha256"),
        }})
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        checks.append({"id": "ui-contract-lock", "ok": False,
                       "detail": {"error": str(exc)}})

    # Two questions, two answers. "The declaration or an asset it requires is
    # missing" and "the bundle does not parse" are different recoveries, and a
    # restore that reported the first as the second sent you to rebuild
    # something that was never broken.
    try:
        shipped = read_shipped_assets(restored_ui)
    except BackupManifestError as exc:
        checks.append({"id": "ui-asset-declaration", "ok": False,
                       "detail": {"error": str(exc)}})
    else:
        missing = [
            name for name in shipped
            if not (restored_ui / "plugin" / name).is_file()
            or (restored_ui / "plugin" / name).is_symlink()
        ]
        checks.append({"id": "ui-asset-declaration", "ok": not missing,
                       "detail": {"shipped": shipped, "missing": missing}})

    # The restored install.py owns preflight_plugin_directory and all other
    # install inputs, including bases/*.base. Ask that exact installer, rather
    # than maintaining a second prerequisite list in Core. --skip-tests avoids
    # rebuilding a recovered bundle (and needing npm/network); the existing
    # bundle/contract checks below and above remain independent. A disposable
    # fresh vault proves source readiness, not compatibility with a live vault.
    installer = restored_ui / "install.py"
    installer_row = next((row for row in manifest["entries"]
                          if (row["root"], row["path"]) == ("ui", "install.py")), None)
    detail: dict[str, Any] = {
        "requirement": "restored install.py --dry-run --skip-tests",
        "scope": "installation inputs for a fresh vault; excludes UI runtime tests and live-vault checks",
    }
    if installer_row is None or not installer.is_file() or installer.is_symlink():
        detail["error"] = "restored install.py must be an inventoried regular file"
        preflight_ok = False
    else:
        detail["installer_sha256"] = installer_row["sha256"]
        try:
            with tempfile.TemporaryDirectory(prefix="learningos-install-preflight-") as vault:
                result = subprocess.run(
                    [sys.executable, "-I", "-B", str(installer.resolve()),
                     "--dry-run", "--skip-tests", "--vault", vault],
                    cwd=restored_ui, capture_output=True, text=True, timeout=30, check=False,
                )
                untouched = not any(Path(vault).iterdir())
                preflight_ok = result.returncode == 0 and untouched
                detail.update(returncode=result.returncode, stdout=result.stdout.strip()[-4000:],
                              stderr=result.stderr.strip()[-4000:], vault_unchanged=untouched)
        except (OSError, subprocess.SubprocessError) as exc:
            preflight_ok = False
            detail["error"] = str(exc)
    checks.append({"id": "ui-install-preflight", "ok": preflight_ok, "detail": detail})

    bundle = restored_ui / "plugin" / "main.js"
    if not bundle.is_file() or bundle.is_symlink():
        checks.append({"id": "ui-bundle-smoke", "ok": False,
                       "detail": {"reason": "restored plugin bundle is incomplete"}})
    else:
        try:
            result = subprocess.run(
                ["node", "--check", str(bundle)],
                cwd=restored_ui,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            checks.append({"id": "ui-bundle-smoke", "ok": result.returncode == 0,
                           "detail": {"stderr": result.stderr.strip()[:1000]}})
        except (OSError, subprocess.SubprocessError) as exc:
            checks.append({"id": "ui-bundle-smoke", "ok": False,
                           "detail": {"error": str(exc)}})

    return {
        "ok": all(bool(check["ok"]) for check in checks),
        "checks": checks,
        "manual_ui_open_required": True,
    }
