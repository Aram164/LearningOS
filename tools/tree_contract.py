#!/usr/bin/env python3
"""Render the ARCHITECTURE tree block from the tree contract, or check it.

``system/contracts/tree-contract.yaml`` is the authored copy. ``ARCHITECTURE.md``
§3.2 is a projection of it. This tool is the projector.

    python tools/tree_contract.py            # check (the default, and what CI runs)
    python tools/tree_contract.py --write    # regenerate the block
    python tools/tree_contract.py --show     # print the projection, change nothing

The block is anchored on ``<!-- tree:begin -->`` / ``<!-- tree:end -->`` comment
markers rather than on a heading number, because heading numbers move and a
checker anchored to one silently stops finding its target.

Exit codes: 0 current, 1 stale or unreadable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.contracts import perimeter as pm  # noqa: E402
from learning_os.contracts.tree_contract import (  # noqa: E402
    ARCHITECTURE_RELATIVE,
    TreeContractError,
    block_is_current,
    load,
    render,
    write_block,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true",
                      help="regenerate the ARCHITECTURE tree block")
    mode.add_argument("--show", action="store_true",
                      help="print the projection without touching any file")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        contract = load(root)
    except TreeContractError as exc:
        print(f"tree-contract: {exc}", file=sys.stderr)
        return 1

    # ARCHITECTURE carries two generated trees: §3.1 is the wrapper root, owned
    # by the perimeter contract, and §3.2 is this repository. One tool renders
    # both, because a reader who regenerates one and not the other has produced
    # exactly the drift these projections exist to prevent.
    try:
        perimeter = pm.load(root)
    except pm.PerimeterError as exc:
        print(f"tree-contract: {exc}", file=sys.stderr)
        return 1

    if args.show:
        print(pm.render(perimeter))
        print()
        print(render(root, contract))
        return 0

    if args.write:
        try:
            changed = [
                pm.write_block(root, perimeter),
                write_block(root, contract),
            ]
        except (TreeContractError, pm.PerimeterError) as exc:
            print(f"tree-contract: {exc}", file=sys.stderr)
            return 1
        print(
            f"tree-contract: {ARCHITECTURE_RELATIVE} "
            + ("regenerated" if any(changed) else "already current")
        )
        return 0

    try:
        current = block_is_current(root, contract) and pm.block_is_current(root, perimeter)
    except (TreeContractError, pm.PerimeterError) as exc:
        print(f"tree-contract: {exc}", file=sys.stderr)
        return 1
    if current:
        print(f"tree-contract: {ARCHITECTURE_RELATIVE} matches the contract")
        return 0
    print(
        f"tree-contract: {ARCHITECTURE_RELATIVE} is stale — run "
        "`python tools/tree_contract.py --write`. Do not hand-edit the block.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
