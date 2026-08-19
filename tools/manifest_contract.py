#!/usr/bin/env python3
"""The published manifest's declared shape, and the gate that keeps it honest.

    python tools/manifest_contract.py                  # check: does the build match?
    python tools/manifest_contract.py --show           # print the current shape
    python tools/manifest_contract.py --bump --note "topics collection added"

WHY THIS EXISTS
---------------
``system/contracts/data-contract.yaml`` versions what Core *stores*. This one
versions what Core *publishes* — the manifest every interface reads. They are
different contracts with different consumers and they move independently.

Until 2026-08-08 only the consumer declared the projection version, in the
Obsidian UI's ``contracts/manifest-v2.lock.json``. Core could reshape the
manifest, pass its own CI, and push; the incompatibility surfaced in the other
repository. That is exactly what happened when Core started publishing a
top-level ``topics`` collection while still announcing ``contract_version: 2``.

Now ``build_manifest`` enforces the declared shape on every build, so the same
mistake fails in Core's own test run. See
``tools/learning_os/contracts/manifest_contract.py`` for the enforcement and
``system/contracts/manifest-contract.yaml`` for the record.

BUMPING
-------
``--bump`` rebuilds the manifest with enforcement OFF, adopts whatever shape it
actually has, and writes the next version with a history entry. Mirror the new
version into the UI in the same change — Core and UI ship together.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from learning_os.contracts.manifest_contract import (  # noqa: E402
    ManifestContractError, bump, check, shape_of,
)
from learning_os.genout.manifest import build_manifest  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402


def _manifest(root: Path, enforce_contract: bool) -> dict:
    return build_manifest(load_repo(root), _dt.date.today().isoformat(),
                          enforce_contract=enforce_contract)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--show", action="store_true",
                        help="print the shape the current build actually produces")
    parser.add_argument("--bump", action="store_true",
                        help="adopt the current build's shape as the next version")
    parser.add_argument("--note", default=None,
                        help="what changed in the projection (required with --bump)")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent

    if args.show:
        print(json.dumps(shape_of(_manifest(root, enforce_contract=False)), indent=2))
        return 0

    if args.bump:
        if not args.note:
            print("--bump requires --note describing what changed in the projection",
                  file=sys.stderr)
            return 2
        updated = bump(_manifest(root, enforce_contract=False), root, args.note)
        print(f"declared manifest contract v{updated['contract_version']} over "
              f"{len(updated['top_level_keys'])} top-level keys")
        print("next: mirror it into the UI — contracts/manifest-v"
              f"{updated['contract_version']}.lock.json, MANIFEST_CONTRACT_VERSION, "
              f"ManifestV{updated['contract_version']}, fixture-vault/generated/manifest.json")
        return 0

    try:
        ok, message = check(_manifest(root, enforce_contract=False), root)
    except ManifestContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
