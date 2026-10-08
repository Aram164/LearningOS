#!/usr/bin/env python3
"""Write system/schema/capabilities/<name>.schema.json from the CLI parser.

Generated, not authored: the payload surface of a capability is defined by the
parser for its named command. Run after changing a command's arguments; the
test suite asserts the checked-in files match what this produces. --check
asks the same question without writing, and also verifies the envelope
schema's resultV2 error code enum still equals domain.codes.PUBLIC_CODES
and its error details fragment still equals the typed D3 fragment below.
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
    return all_payload_schemas(
        root, command_definitions(root),
        payload_records=resolve_all(root))


def _details_fragment() -> dict:
    """The typed D3 error-details fragment (SPEC 9.3).

    The reason enum is generated from domain.codes.REASONS; pre-existing
    detail keys keep working through additionalProperties.
    """

    from learning_os.domain.codes import REASONS  # noqa: E402

    return {
        "type": "object",
        "properties": {
            "reason": {"enum": list(REASONS)},
            "suggestions": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "maxItems": 5,
            },
            "remedy": {"type": "string", "minLength": 1},
        },
        "additionalProperties": True,
    }


def _envelope_path(root: Path) -> Path:
    return root / "system" / "schema" / "capability-envelope.schema.json"


def _render_fragment_span(indent: str) -> str:
    """The details fragment as file text at the given key indent."""

    rendered = json.dumps(_details_fragment(), indent=2,
                          ensure_ascii=False).splitlines()
    head = f'{indent}"details": {rendered[0]}'
    body = [f"{indent}{line}" if line.strip() else line
            for line in rendered[1:]]
    return "\n".join([head, *body])


def _write_envelope_fragment(root: Path) -> bool:
    """Splice the typed D3 fragment into the envelope schema (SPEC 9.3).

    Surgical and idempotent: only the error-details span changes, so the
    file's hand formatting elsewhere is preserved. Returns True when the
    file changed.
    """

    path = _envelope_path(root)
    text = path.read_text(encoding="utf-8")
    anchor = '"details": {'
    if text.count(anchor) != 1:
        raise SystemExit(
            f"envelope details anchor is not unique in {path.name}")
    start = text.index(anchor)
    line_start = text.rindex("\n", 0, start) + 1
    indent = text[line_start:start]
    depth = 0
    in_string = False
    escaped = False
    end = None
    for pos in range(start + len(anchor) - 1, len(text)):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
    if end is None:
        raise SystemExit(f"unbalanced details span in {path.name}")
    new_text = text[:line_start] + _render_fragment_span(indent) + text[end:]
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def _read_envelope_details(root: Path) -> dict:
    envelope = json.loads(_envelope_path(root).read_text(encoding="utf-8"))
    return envelope["$defs"]["resultV2"]["properties"]["error"][
        "oneOf"][1]["properties"]["details"]


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (SPEC §7.4, PLAN D11)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="compare the checked-in schemas with the parser instead of "
             "writing; exit 1 listing drifted files")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = TOOLS.parent
    schemas = _build_schemas(root)
    out = root / "system" / "schema" / "capabilities"
    if args.check:
        # SPEC §8.2: the envelope schema's resultV2 error code enum is the
        # public vocabulary; domain.codes.PUBLIC_CODES must equal it, in
        # order. The schema file itself stays as it is.
        from learning_os.domain.codes import PUBLIC_CODES  # noqa: E402
        envelope = json.loads((root / "system" / "schema"
                               / "capability-envelope.schema.json").read_text(
                                   encoding="utf-8"))
        enum = envelope["$defs"]["resultV2"]["properties"]["error"][
            "oneOf"][1]["properties"]["code"]["enum"]
        if list(PUBLIC_CODES) != enum:
            print("domain.codes.PUBLIC_CODES drifted from the envelope code enum:")
            print(f"  codes.py: {list(PUBLIC_CODES)!r}")
            print(f"  schema:   {enum!r}")
            return 1
        # SPEC 9.3: the typed D3 details fragment is generated from
        # domain.codes.REASONS; the checked-in span must equal it.
        if _read_envelope_details(root) != _details_fragment():
            print("envelope error details fragment drifted from the D3 fragment:")
            print("  run tools/generate_capability_schemas.py to refresh it")
            return 1
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
    if _write_envelope_fragment(root):
        print("wrote envelope error details fragment -> "
              "system/schema/capability-envelope.schema.json")
    else:
        print("envelope error details fragment current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
