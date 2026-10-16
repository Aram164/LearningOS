#!/usr/bin/env python3
"""Check or regenerate documentation blocks from their declared metadata owners."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="repository root (default: parent of tools/)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check currentness without writing (default)")
    mode.add_argument("--write", action="store_true", help="regenerate existing block interiors")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sys.dont_write_bytecode = True
    from learning_os.adapters.cli_parser import build_parser as cli_parser
    from learning_os.contracts import doc_blocks
    from learning_os.derive.semantics import PREDICATES

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    try:
        try:
            parser = cli_parser()
            names = [name for action in parser._actions if isinstance(action, argparse._SubParsersAction)
                     for name in action.choices]
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            raise doc_blocks.DocBlockError(
                f"cannot construct generated CLI from request metadata: {exc}",
                doc_blocks.REQUESTS,
            ) from exc
        values = doc_blocks.collect(root, predicate_names=PREDICATES, cli_command_names=names)
        if args.write:
            changed = doc_blocks.write(root, values)
            print(f"doc-blocks: {len(changed)} document(s) regenerated")
            return 0
        issues = doc_blocks.check(root, values)
        for issue in issues:
            print(f"{issue.code}: {issue.message} [{issue.path}]", file=sys.stderr)
        if not issues:
            print("doc-blocks: all generated documentation is current")
        return int(bool(issues))
    except doc_blocks.DocBlockError as exc:
        print(f"DOC-BLOCK-STALE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
