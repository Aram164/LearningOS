"""C1-A finding: module.create refuses only a filesystem destination, not a
legacy-registry identity.

The declared invariant (``system/contracts/capabilities.yaml``, module.create)
says the destination must not exist: "an existing canonical identity or file is
refused, because an absent revision entry cannot prove absence".
``_creation_destination_problems`` (tools/learning_os/app/handlers/plan.py)
checks only the filesystem under ``curriculum/modules/<id>/``. A module id that
already exists as a canonical record in the legacy registry
``records/modules.yaml`` (``repo.legacy_modules``) passes the check, and
creation proceeds. The legacy record is then shadowed: once any partitioned
module exists, ``load_modules`` registers only partitioned records, so the
legacy record's facts (its attempts) disappear from every view while the
validator stays green (MODULE-MIGRATION only requires the id to be *covered*).

Expected: creation refuses with the already-exists refusal.
Observed on base main (d6c47790): --check exits 0 and the apply writes the
partitioned module.
"""

from __future__ import annotations

import json
import subprocess
import sys

import yaml

from conftest import build_mini_repo  # noqa: F401  (mini_repo lives in conftest)
from gateway_helpers import approved_v2_envelope, file_sha256, run_v2_capability
from repo_builders import add_curriculum, run_los, write_yaml

LOS_MODULE_CREATE = "module-create"


def _recreate_legacy_record(root, module_id: str) -> None:
    """Rename the mini's legacy registry record to an unpartitioned id."""
    path = root / "records/modules.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["modules"][0]["id"] = module_id
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8")


def _creation_package(root, tmp_path, module_id: str):
    package = {
        "module": {
            "id": module_id, "type": "module", "kind": "academic",
            "area_id": "program-bachelors", "institution": "HU Berlin",
            "title": "Legacy Clash", "semester": "sose-2026",
            "status": "enrolled", "source_map": "source-map.yaml",
            "unit_order": [],
        },
        "source_map": {
            "type": "module-source-map", "module_id": module_id,
            "sources": [],
        },
    }
    path = tmp_path / "creation-package.yaml"
    write_yaml(path, package)
    return path


def test_module_create_refuses_a_legacy_registry_identity(mini_repo, tmp_path):
    root = mini_repo
    add_curriculum(root)
    _recreate_legacy_record(root, "module-legacy-clash")
    package = _creation_package(root, tmp_path, "module-legacy-clash")

    checked = run_los(root, LOS_MODULE_CREATE, "--file", str(package), "--check")
    # The invariant: an existing canonical identity is refused. The legacy
    # registry record is a canonical identity (the loader reads it, and
    # MODULE-MIGRATION treats its id as an owned module).
    assert checked.returncode != 0, (
        "module.create --check accepted an id that already exists as a "
        "legacy-registry canonical identity:\n"
        + checked.stdout[:400]
    )
    assert "already exists" in checked.stderr, checked.stderr[:400]

    envelope = approved_v2_envelope(
        root, capability="module.create",
        payload={"file": str(package), "file_sha256": file_sha256(package)},
        artifact_ids=["module-legacy-clash"], idempotency_key="c1a-legacy-clash")
    applied = run_v2_capability(root, envelope)
    assert applied.returncode != 0, applied.stdout[:400]
    assert not (root / "curriculum/modules/module-legacy-clash" / "module.yaml").exists()
