"""The manifest/projection contract — producer-side ownership of the public shape.

``system/contracts/manifest-contract.yaml`` declares the version and the exact
key sets of the manifest Core publishes. :func:`enforce` is called by
``build_manifest`` on every build, so a change to the published shape cannot
reach a consumer without a deliberate bump.

This is deliberately separate from ``tools/schema_contract.py``. That one
governs *stored records*; this one governs *what Core publishes*. Conflating
them is what allowed Core to add a top-level ``topics`` collection while still
announcing ``contract_version: 2`` — the interface changed, the canonical
records did not, and only the consumer's CI noticed.

Why the producer enforces rather than the consumer:

    A consumer that fails closed on an unknown version is correct but late.
    It discovers the breakage after the producer has already committed and
    pushed. Enforcing here means the same mistake fails in the producer's own
    test run, which is the only place it can still be cheap to fix.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import yaml

CONTRACT_RELATIVE = "system/contracts/manifest-contract.yaml"


class ManifestContractError(Exception):
    """The built manifest does not match the declared projection contract."""


def contract_path(root: Path) -> Path:
    return root / "system" / "contracts" / "manifest-contract.yaml"


def load_contract(root: Path) -> dict:
    path = contract_path(root)
    if not path.is_file():
        raise ManifestContractError(
            f"no {CONTRACT_RELATIVE} — the published manifest shape has no declared "
            "version, so an interface change cannot be told apart from the shape it "
            "replaced; declare it with `python tools/manifest_contract.py --bump "
            "--note 'baseline'`")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - malformed checked-in file
        raise ManifestContractError(f"invalid {CONTRACT_RELATIVE}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("contract_version"), int):
        raise ManifestContractError(
            f"{CONTRACT_RELATIVE} must declare an integer contract_version")
    return data


def declared_version(root: Path) -> int:
    """The version ``build_manifest`` stamps into ``_generated``.

    Read rather than hardcoded: one source of truth means the emitted version
    and the declared shape can never disagree, which is exactly the failure
    this module exists to prevent.
    """
    return int(load_contract(root)["contract_version"])


def shape_of(manifest: dict) -> dict:
    """The three key sets that make up the public projection shape."""
    generated = manifest.get("_generated")
    indexes = manifest.get("indexes")
    return {
        "top_level_keys": sorted(manifest),
        "generated_keys": sorted(generated if isinstance(generated, dict) else {}),
        "index_keys": sorted(indexes if isinstance(indexes, dict) else {}),
    }


def _diff(label: str, actual: list[str], expected: list[str]) -> str | None:
    if actual == sorted(expected):
        return None
    added = [k for k in actual if k not in expected]
    missing = [k for k in expected if k not in actual]
    return (f"  {label}: added {added or 'none'}, missing {missing or 'none'}")


def check(manifest: dict, root: Path) -> tuple[bool, str]:
    """Return ``(ok, message)`` for a built manifest against the declared contract."""
    contract = load_contract(root)
    version = int(contract["contract_version"])
    shape = shape_of(manifest)
    problems: list[str] = []

    stamped = (manifest.get("_generated") or {}).get("contract_version")
    if stamped != version:
        problems.append(
            f"  _generated.contract_version is {stamped!r} but "
            f"{CONTRACT_RELATIVE} declares {version}")

    for key in ("top_level_keys", "generated_keys", "index_keys"):
        line = _diff(key, shape[key], list(contract.get(key) or []))
        if line:
            problems.append(line)

    returned = [k for k in (contract.get("forbidden_top_level_keys") or [])
                if k in manifest]
    if returned:
        problems.append(f"  retired keys published again: {returned}")

    if not problems:
        return True, (f"manifest contract v{version} matches "
                      f"{len(shape['top_level_keys'])} top-level keys")

    return False, (
        f"the published manifest no longer matches {CONTRACT_RELATIVE} "
        f"(declared v{version}).\n"
        + "\n".join(problems)
        + "\nA change to the published shape is an interface change, even when it "
          "only adds a key: consumers declare an exact version and fail closed.\n"
        "  1. python tools/manifest_contract.py --bump --note \"<what changed>\"\n"
        "  2. mirror the new version into the UI in the same change — "
        "contracts/manifest-v<N>.lock.json, MANIFEST_CONTRACT_VERSION, "
        "ManifestV<N>, fixture-vault/generated/manifest.json")


def enforce(manifest: dict, root: Path) -> None:
    """Raise unless the manifest matches the declared contract."""
    ok, message = check(manifest, root)
    if not ok:
        raise ManifestContractError(message)


def bump(manifest: dict, root: Path, note: str) -> dict:
    """Declare the shape of ``manifest`` as the next projection version."""
    path = contract_path(root)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    header = "".join(line for line in text.splitlines(keepends=True)
                     if line.startswith("#"))
    current = load_contract(root) if path.is_file() else {"contract_version": 1}
    version = int(current.get("contract_version", 1)) + 1
    shape = shape_of(manifest)
    updated = {
        "contract_version": version,
        **shape,
        "forbidden_top_level_keys": list(current.get("forbidden_top_level_keys") or []),
        "history": list(current.get("history") or []) + [{
            "version": version,
            "adopted": _dt.date.today().isoformat(),
            "note": note,
            "mirrored_in_ui": f"contracts/manifest-v{version}.lock.json",
        }],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + yaml.safe_dump(updated, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")
    return updated
