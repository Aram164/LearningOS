#!/usr/bin/env python3
"""Deliver verified flashcards append-only into a LearnKit practice vault.

Usage:
  export_learnkit.py --init --vault PATH
  export_learnkit.py --check --vault PATH --item ID [--item ID ...] --out PLAN
  export_learnkit.py --apply PLAN --vault PATH

The Core root follows the documented convention (the parent of `tools/`,
overridable with --root). Init creates the foreign-vault marker in an absent
or empty destination; check writes an explicit plan with no card text; apply
re-derives every hash and publishes create-only. Existing reviewed cards are
kept byte-identical or refuse — never edited, never deleted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from learning_os.domain.failures import WriteRefused  # noqa: E402
from learning_os.store.loader import load_repo  # noqa: E402
from learning_os.store.practice_export import (  # noqa: E402
    apply_plan,
    init_vault,
    plan_document,
    validate_vault,
    write_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=TOOLS.parent,
                        help="Core repository root (default: parent of tools/)")
    parser.add_argument("--vault", required=True, type=Path,
                        help="the explicitly selected practice vault")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true",
                      help="create the practice-vault marker")
    mode.add_argument("--check", action="store_true",
                      help="write an export plan without touching the vault")
    mode.add_argument("--apply", type=Path, metavar="PLAN",
                      help="publish a checked plan, create-only")
    parser.add_argument("--item", action="append", default=[], metavar="ID",
                        help="a verified practice item id (repeatable)")
    parser.add_argument("--out", type=Path, metavar="PLAN",
                        help="where --check writes the plan (explicit scratch path)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root
    try:
        if args.init:
            marker = init_vault(args.vault, root)
            print(json.dumps({"status": "initialized",
                              "vault_id": marker["vault_id"]}))
            return 0
        marker = validate_vault(args.vault, root)
        repo = load_repo(root)
        if args.check:
            if not args.item:
                raise WriteRefused("--check needs at least one --item")
            if args.out is None:
                raise WriteRefused("--check needs an explicit --out plan path")
            document, _entries = plan_document(
                repo, list(dict.fromkeys(args.item)), args.vault, marker)
            write_plan(args.out, document, root, args.vault)
            print(json.dumps({
                "status": "planned",
                "actions": [entry["action"] for entry in document["items"]],
                "out": str(args.out),
            }))
            return 0
        document = json.loads(args.apply.read_text(encoding="utf-8"))
        result = apply_plan(repo, document, args.vault)
        print(json.dumps({"status": "applied", **result["counts"]}))
        return 0
    except WriteRefused as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
