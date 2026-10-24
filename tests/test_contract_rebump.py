"""--rebump folds a schema iteration into the branch's own top entry.

Companion to ``test_arch_ratchets.py::test_contract_rises_at_most_one_version
_per_branch``: the ratchet caps a branch at one new contract version, and
this is the fold that keeps a second schema iteration on the same branch
inside the cap.
"""

from __future__ import annotations

import shutil

import pytest

from learning_os.store.contracts.data_contract import (
    SCHEMA_DIR,
    bump,
    load_contract,
    rebump,
)


@pytest.fixture()
def contract_pair(tmp_path):
    schema_dir = tmp_path / "schema"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    return schema_dir, tmp_path / "data-contract.yaml"


def test_rebump_keeps_the_version_and_replaces_the_top_entry(contract_pair):
    schema_dir, path = contract_pair
    bump("first shape", schema_dir=schema_dir, path=path)
    second = bump("second shape", schema_dir=schema_dir, path=path)
    assert second["contract_version"] == 2 and len(second["history"]) == 2

    folded = rebump("second shape, folded", schema_dir=schema_dir, path=path)
    assert folded["contract_version"] == 2          # no third version on this branch
    assert len(folded["history"]) == 2              # the iteration replaced, not appended
    assert folded["history"][0]["note"] == "first shape"
    assert folded["history"][-1]["note"] == "second shape, folded"
    assert folded["schema_fingerprint"] == second["schema_fingerprint"]


def test_rebump_moves_the_fingerprint_when_schemas_changed(contract_pair):
    schema_dir, path = contract_pair
    bump("first shape", schema_dir=schema_dir, path=path)
    before = rebump("fold point", schema_dir=schema_dir, path=path)

    target = next(iter(sorted(schema_dir.glob("*.schema.json"))))
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    after = rebump("schema iteration folded", schema_dir=schema_dir, path=path)
    assert after["contract_version"] == before["contract_version"]
    assert after["schema_fingerprint"] != before["schema_fingerprint"]
    # the written contract agrees with what rebump returned
    on_disk = load_contract(path)
    assert on_disk["schema_fingerprint"] == after["schema_fingerprint"]


def test_rebump_refuses_when_there_is_no_entry_to_fold(tmp_path):
    with pytest.raises(ValueError, match="no history entry"):
        rebump("nothing to fold", schema_dir=SCHEMA_DIR,
               path=tmp_path / "absent.yaml")
