#!/usr/bin/env python3
"""Write system/schema/capabilities/<name>.schema.json from the CLI parser.

Generated, not authored: the payload surface of a capability is defined by the
parser for its named command. Run after changing a command's arguments; the
test suite asserts the checked-in files match what this produces.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from learning_os.contracts.capability_catalog import command_definitions  # noqa: E402
from learning_os.contracts.payloads import all_payload_schemas  # noqa: E402


def main() -> int:
    root = TOOLS.parent
    import los  # noqa: E402  (imports the parser, not a command)

    schemas = all_payload_schemas(los.build_parser(), command_definitions(root))
    out = root / "system" / "schema" / "capabilities"
    out.mkdir(parents=True, exist_ok=True)
    for name, schema in schemas.items():
        (out / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(schemas)} capability payload schemas -> {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
