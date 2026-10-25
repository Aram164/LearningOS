"""V1 finding: changing-contracts.md:7 — "Every record schema is
``additionalProperties: false``".

The data contract's own record-schema set (``data_contract.record_schemas``:
every schema under system/schema/ that does not declare ``x-governs: artifact``,
counted as ``record_schemas: 36``) contains two definition-only libraries
without any root object constraint: ``learning-plan.schema.json`` and
``material-comparison-defs.schema.json``. Any object — including one carrying
arbitrary unknown keys — validates against them, so the documented universal
claim is false as written. This test asserts the documented claim; it fails on
the pin.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from learning_os.store.contracts.data_contract import ROOT, record_schemas
from learning_os.store.contracts.json_schema import schema_registry

SCHEMA_DIR = ROOT / "system" / "schema"


def test_every_record_schema_rejects_an_unknown_root_key():
    """The documented claim: a record schema is closed (additionalProperties:
    false), so an object with an unknown top-level key cannot validate."""
    registry = schema_registry(SCHEMA_DIR)
    accepted = {}
    for path in record_schemas(SCHEMA_DIR):
        schema = json.loads(path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, registry=registry)
        errors = list(validator.iter_errors({"x-unknown-probe-key": {"probe": True}}))
        if not errors:
            accepted[path.name] = "accepted an object with an unknown top-level key"
    assert not accepted, (
        "changing-contracts.md:7 claims every record schema is "
        "additionalProperties: false, but these record schemas accept unknown "
        f"top-level keys: {accepted}"
    )
