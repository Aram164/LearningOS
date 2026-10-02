#!/usr/bin/env python3
"""Write system/schema/capabilities/<name>.schema.json from the CLI parser.

Generated, not authored: the payload surface of a capability is defined by the
parser for its named command. Run after changing a command's arguments; the
test suite asserts the checked-in files match what this produces. --check
asks the same question without writing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

from learning_os.contracts.capability_catalog import command_definitions  # noqa: E402
from learning_os.contracts.payload_records import resolve_all  # noqa: E402
from learning_os.contracts.payloads import all_payload_schemas  # noqa: E402


def _build_schemas(root: Path) -> dict:
    import los  # noqa: E402  (imports the parser, not a command)

    return all_payload_schemas(
        los.build_parser(), command_definitions(root),
        payload_records=resolve_all(root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="compare the checked-in schemas with the parser instead of "
             "writing; exit 1 listing drifted files")
    args = parser.parse_args(argv)
    root = TOOLS.parent
    schemas = _build_schemas(root)
    out = root / "system" / "schema" / "capabilities"
    if args.check:
        # The same verdict as
        # test_capability_dispatch.py::test_payload_schemas_match_the_cli_parser:
        # parsed-JSON equality per generated name. A missing or unreadable
        # file is drift; an extra file on disk is not checked there either.
        drifted = []
        for name, schema in schemas.items():
            path = out / f"{name}.schema.json"
            try:
                on_disk = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                on_disk = None
            if on_disk != schema:
                drifted.append(path.name)
        if drifted:
            print("drifted capability payload schemas:")
            for name in sorted(drifted):
                print(f"  {name}")
            return 1
        print(f"{len(schemas)} capability payload schemas current")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    for name, schema in schemas.items():
        (out / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(schemas)} capability payload schemas -> {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
