#!/usr/bin/env python3
"""Generate or verify the exact-pair release receipt (release-hardening Phase 9).

    python tools/release_pair_receipt.py generate \\
        --core-root . --ui-root ../obsidian-ui \\
        --core-sha <40 lowercase hex> --ui-sha <40 lowercase hex> \\
        --workflow-run-id <id> --workflow-run-attempt <n> \\
        --out pair-receipt.json

    python tools/release_pair_receipt.py verify \\
        --receipt pair-receipt.json --artifact-dir <directory containing plugin/>

WHY THIS EXISTS
---------------
Branch-based CI (validate.yml, ui-ci.yml) is useful but mutable: a green run
today proves nothing about whether the same Core SHA is still paired with the
same UI SHA tomorrow. This receipt is the one artifact that can answer "were
these two exact commits built and verified together" without re-running
anything — a downloaded pair-receipt.json plus the four shipped files beside
it is either internally consistent, or it is not. It is operational evidence,
never a canonical LearningOS entity: generating one changes no data-contract
or manifest-contract version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat as stat_module
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "system" / "contracts" / "release-pair-receipt.schema.json"
SHIPPED_ASSETS = ("main.js", "styles.css", "manifest.json", "build-info.json")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from learning_os.contracts.manifest_contract import (  # noqa: E402
    ManifestContractError,
    declared_schema_sha256,
    declared_version,
)

_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ReleasePairReceiptError(Exception):
    """The receipt, or the artifact it describes, is not internally consistent."""


def _sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _sha256_file(path: Path) -> str:
    try:
        st = path.lstat()
        if path.is_symlink() or not stat_module.S_ISREG(st.st_mode):
            raise ReleasePairReceiptError(
                f"cannot hash {path}: shipped assets must be regular files, not links or directories"
            )
        return _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ReleasePairReceiptError(f"cannot read {path}: {exc}") from exc


def _shipped_asset_sha256(plugin_dir: Path) -> dict[str, str]:
    """Hash the complete, closed shipped inventory in its declared order."""
    return {name: _sha256_file(plugin_dir / name) for name in SHIPPED_ASSETS}


def _require_full_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not _FULL_SHA_RE.fullmatch(value):
        raise ReleasePairReceiptError(
            f"{label} is not a 40-character lowercase hex SHA: {value!r}"
        )
    return value


def _git(repo: Path, *args: str) -> str:
    """A Git command's output, or a refusal. Unreadable Git state is never clean."""
    try:
        proc = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleasePairReceiptError(f"cannot run 'git {' '.join(args)}' in {repo}: {exc}") from exc
    if proc.returncode != 0:
        raise ReleasePairReceiptError(
            f"'git {' '.join(args)}' in {repo} exited {proc.returncode}: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _require_clean_head(repo: Path, expected_sha: str, label: str) -> str:
    actual = _git(repo, "rev-parse", "HEAD")
    if not _FULL_SHA_RE.fullmatch(actual):
        raise ReleasePairReceiptError(f"{label} HEAD is not a readable 40-character revision: {actual!r}")
    if actual != expected_sha:
        raise ReleasePairReceiptError(
            f"{label} HEAD ({actual}) does not equal the requested SHA ({expected_sha})"
        )
    status = _git(repo, "status", "--porcelain")
    if status:
        raise ReleasePairReceiptError(f"{label} worktree is dirty; a release-pair receipt requires a clean checkout")
    return actual


def _current_branch(repo: Path) -> str:
    try:
        return _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    except ReleasePairReceiptError:
        return "detached"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_receipt(receipt: dict) -> None:
    errors = sorted(
        Draft202012Validator(_load_schema()).iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<receipt>'}: {error.message}"
            for error in errors[:6]
        )
        raise ReleasePairReceiptError(f"receipt fails schema validation: {detail}")


def _data_contract_version(core_root: Path) -> int:
    path = core_root / "system" / "contracts" / "data-contract.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReleasePairReceiptError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("contract_version"), int):
        raise ReleasePairReceiptError(f"{path} must declare an integer contract_version")
    return int(data["contract_version"])


def generate(
    *,
    core_root: Path,
    ui_root: Path,
    core_sha: str,
    ui_sha: str,
    workflow_run_id: str,
    workflow_run_attempt: str,
) -> dict:
    """Build one schema-validated receipt from the current, already-built pair.

    Refuses rather than guesses at every step: a dirty worktree, a HEAD that
    does not equal the requested SHA, or a build-info.json that disagrees with
    either SHA all raise before a receipt is produced.
    """
    core_sha = _require_full_sha(core_sha, "core_sha")
    ui_sha = _require_full_sha(ui_sha, "ui_sha")

    _require_clean_head(core_root, core_sha, "Core")
    _require_clean_head(ui_root, ui_sha, "UI")

    build_info_path = ui_root / "plugin" / "build-info.json"
    try:
        build_info = json.loads(build_info_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleasePairReceiptError(f"cannot read {build_info_path}: {exc}") from exc

    if build_info.get("source_revision") != ui_sha:
        raise ReleasePairReceiptError(
            f"{build_info_path} source_revision ({build_info.get('source_revision')!r}) "
            f"does not equal ui_sha ({ui_sha})"
        )
    if build_info.get("core_revision") != core_sha:
        raise ReleasePairReceiptError(
            f"{build_info_path} core_revision ({build_info.get('core_revision')!r}) "
            f"does not equal core_sha ({core_sha})"
        )
    if build_info.get("source_dirty") is not False:
        raise ReleasePairReceiptError(
            f"{build_info_path} source_dirty is not false: {build_info.get('source_dirty')!r}"
        )
    if build_info.get("core_dirty") is not False:
        raise ReleasePairReceiptError(
            f"{build_info_path} core_dirty is not false: {build_info.get('core_dirty')!r}"
        )
    for field in ("source_fingerprint", "bundle_sha256", "stylesheet_sha256"):
        if not isinstance(build_info.get(field), str):
            raise ReleasePairReceiptError(f"{build_info_path} is missing {field}")

    try:
        manifest_contract_version = declared_version(core_root)
        manifest_contract_schema_sha256 = declared_schema_sha256(core_root)
    except ManifestContractError as exc:
        raise ReleasePairReceiptError(str(exc)) from exc

    shipped_asset_sha256 = _shipped_asset_sha256(ui_root / "plugin")
    actual_bundle_sha256 = shipped_asset_sha256["main.js"]
    if actual_bundle_sha256 != build_info["bundle_sha256"]:
        raise ReleasePairReceiptError(
            "plugin/main.js does not match build-info.json's own bundle_sha256"
        )
    actual_stylesheet_sha256 = shipped_asset_sha256["styles.css"]
    if actual_stylesheet_sha256 != build_info["stylesheet_sha256"]:
        raise ReleasePairReceiptError(
            "plugin/styles.css does not match build-info.json's own stylesheet_sha256"
        )
    if build_info.get("manifest_contract_version") != manifest_contract_version:
        raise ReleasePairReceiptError(
            f"{build_info_path} manifest_contract_version "
            f"({build_info.get('manifest_contract_version')!r}) does not equal the Core "
            f"manifest contract version ({manifest_contract_version})"
        )

    receipt = {
        "schema_version": 1,
        "type": "release-pair-receipt",
        "core_sha": core_sha,
        "ui_sha": ui_sha,
        "core_branch": _current_branch(core_root),
        "ui_branch": _current_branch(ui_root),
        "data_contract_version": _data_contract_version(core_root),
        "manifest_contract_version": manifest_contract_version,
        "manifest_contract_schema_sha256": manifest_contract_schema_sha256,
        "runtime_source_fingerprint": build_info["source_fingerprint"],
        "bundle_sha256": build_info["bundle_sha256"],
        "stylesheet_sha256": build_info["stylesheet_sha256"],
        "shipped_asset_sha256": shipped_asset_sha256,
        "system_check_passed": True,
        "stress_scope": "not-run-materials-unprovisioned",
        "workflow_run_id": str(workflow_run_id),
        "workflow_run_attempt": str(workflow_run_attempt),
    }
    validate_receipt(receipt)
    return receipt


def verify(receipt: dict, artifact_dir: Path) -> None:
    """Refuse unless the receipt and every shipped file agree, exactly.

    Every check below is independent — one failure is reported by raising
    immediately, but each is written so an unrelated field cannot mask another
    field's mismatch (no early success path skips a later check).
    """
    validate_receipt(receipt)

    plugin_dir = artifact_dir / "plugin"
    found = {entry.name for entry in plugin_dir.iterdir()} if plugin_dir.is_dir() else set()
    missing = [name for name in SHIPPED_ASSETS if name not in found]
    if missing:
        raise ReleasePairReceiptError(f"artifact is missing shipped file(s): {', '.join(missing)}")
    surplus = sorted(found - set(SHIPPED_ASSETS))
    if surplus:
        raise ReleasePairReceiptError(f"artifact carries undeclared file(s): {', '.join(surplus)}")

    expected_assets = receipt["shipped_asset_sha256"]
    for name in SHIPPED_ASSETS:
        actual = _sha256_file(plugin_dir / name)
        expected = expected_assets[name]
        if actual != expected:
            raise ReleasePairReceiptError(
                f"plugin/{name} sha256 ({actual}) does not match the receipt ({expected})"
            )

    if receipt["bundle_sha256"] != expected_assets["main.js"]:
        raise ReleasePairReceiptError(
            "receipt bundle_sha256 does not match shipped_asset_sha256['main.js']"
        )
    if receipt["stylesheet_sha256"] != expected_assets["styles.css"]:
        raise ReleasePairReceiptError(
            "receipt stylesheet_sha256 does not match shipped_asset_sha256['styles.css']"
        )

    try:
        build_info = json.loads((plugin_dir / "build-info.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleasePairReceiptError(f"cannot read plugin/build-info.json: {exc}") from exc
    if build_info.get("source_revision") != receipt["ui_sha"]:
        raise ReleasePairReceiptError("plugin/build-info.json source_revision does not match the receipt's ui_sha")
    if build_info.get("core_revision") != receipt["core_sha"]:
        raise ReleasePairReceiptError("plugin/build-info.json core_revision does not match the receipt's core_sha")
    if build_info.get("source_dirty") is not False or build_info.get("core_dirty") is not False:
        raise ReleasePairReceiptError("plugin/build-info.json records a dirty or unknown worktree")
    if build_info.get("source_fingerprint") != receipt["runtime_source_fingerprint"]:
        raise ReleasePairReceiptError(
            "plugin/build-info.json source_fingerprint does not match the receipt's "
            "runtime_source_fingerprint"
        )
    if build_info.get("bundle_sha256") != expected_assets["main.js"]:
        raise ReleasePairReceiptError(
            "plugin/build-info.json bundle_sha256 does not match the receipt's main.js hash"
        )
    if build_info.get("stylesheet_sha256") != expected_assets["styles.css"]:
        raise ReleasePairReceiptError(
            "plugin/build-info.json stylesheet_sha256 does not match the receipt's styles.css hash"
        )
    if build_info.get("manifest_contract_version") != receipt["manifest_contract_version"]:
        raise ReleasePairReceiptError(
            "plugin/build-info.json manifest_contract_version does not match the receipt"
        )


def _cli_generate(args: argparse.Namespace) -> int:
    try:
        receipt = generate(
            core_root=Path(args.core_root).resolve(),
            ui_root=Path(args.ui_root).resolve(),
            core_sha=args.core_sha,
            ui_sha=args.ui_sha,
            workflow_run_id=args.workflow_run_id,
            workflow_run_attempt=args.workflow_run_attempt,
        )
    except ReleasePairReceiptError as exc:
        print(f"release-pair-receipt: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "action": "generate", "path": str(out)}))
    return 0


def _cli_verify(args: argparse.Namespace) -> int:
    try:
        receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"release-pair-receipt: cannot read {args.receipt}: {exc}", file=sys.stderr)
        return 1
    try:
        verify(receipt, Path(args.artifact_dir).resolve())
    except ReleasePairReceiptError as exc:
        print(f"release-pair-receipt: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "ok": True, "action": "verify",
        "core_sha": receipt["core_sha"], "ui_sha": receipt["ui_sha"],
    }))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="action", required=True)

    generate_parser = sub.add_parser("generate", help="build a receipt from an already-built clean pair")
    generate_parser.add_argument("--core-root", default=".")
    generate_parser.add_argument("--ui-root", required=True)
    generate_parser.add_argument("--core-sha", required=True)
    generate_parser.add_argument("--ui-sha", required=True)
    generate_parser.add_argument("--workflow-run-id", required=True)
    generate_parser.add_argument("--workflow-run-attempt", required=True)
    generate_parser.add_argument("--out", required=True)
    generate_parser.set_defaults(func=_cli_generate)

    verify_parser = sub.add_parser("verify", help="verify a receipt against an artifact directory")
    verify_parser.add_argument("--receipt", required=True)
    verify_parser.add_argument("--artifact-dir", required=True)
    verify_parser.set_defaults(func=_cli_verify)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
