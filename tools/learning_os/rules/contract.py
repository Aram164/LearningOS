"""The data-format contract gate.

Every record schema is ``additionalProperties: false`` and no canonical record
carries a version, so editing a schema silently redefines what "valid" means for
data already on disk. Nothing recorded that the meaning had changed, which makes
the question "what format was this note written under, and what brings it
forward?" unanswerable a few years later.

``system/contracts/data-contract.yaml`` records the format version and a
fingerprint over the record schemas. This check compares the two on every run,
so a schema edit cannot land without a deliberate decision about existing data.
See tools/schema_contract.py for the reasoning and the bump procedure.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _schema_contract():
    """Import the contract helper from tools/ without a package dependency."""
    tools = Path(__file__).resolve().parents[2]
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import schema_contract  # noqa: PLC0415 — deliberately lazy

    return schema_contract


class ChecksContract:
    """Mixed into Validator; see rules/core.py."""

    def check_data_contract(self):
        root = self.repo.root
        contract_path = root / "system" / "contracts" / "data-contract.yaml"
        schema_dir = root / "system" / "schema"
        if not schema_dir.is_dir():
            return

        module = _schema_contract()
        if not contract_path.exists():
            self.warn("SCHEMA-CONTRACT-MISSING",
                      "no system/contracts/data-contract.yaml — the record "
                      "schemas have no declared version, so a schema change "
                      "cannot be distinguished from the format it replaced; "
                      "declare it with `python tools/schema_contract.py --bump "
                      "--note 'baseline'`",
                      "system/contracts/")
            return

        ok, message = module.check(schema_dir, contract_path)
        if not ok:
            # One error, multi-line: the message names the exact next step.
            self.err("SCHEMA-CONTRACT-DRIFT", message.replace("\n", " "),
                     "system/contracts/data-contract.yaml")
