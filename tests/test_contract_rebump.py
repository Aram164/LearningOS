"""--rebump folds a schema iteration into the branch's own top entry.

Companion to ``test_arch_ratchets.py::test_contract_rises_at_most_one_version
_per_branch``: the ratchet caps a branch at one new contract version, and
this is the fold that keeps a second schema iteration on the same branch
inside the cap — without ever rewriting a version the base already adopted.
The tests run against a real (temporary) git repository, because the guard
reads the base ref through git.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from learning_os.store.contracts.data_contract import (
    SCHEMA_DIR,
    base_contract_version,
    bump,
    load_contract,
    rebump,
)

BASE_REF = "rb-base"


def _git(repo, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args],
                   check=True, capture_output=True)


@pytest.fixture()
def contract_repo(tmp_path):
    """A committed v1 contract on ``rb-base``, plus a working tree free of it.

    The contract lives at the real ``system/contracts/`` depth, because the
    base guard derives the repository root from the contract's path.
    """
    subprocess.run(["git", "init", "-q", str(tmp_path)],
                   check=True, capture_output=True)
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _git(tmp_path, "config", "user.name", "tests")
    schema_dir = tmp_path / "system" / "schema"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    path = tmp_path / "system" / "contracts" / "data-contract.yaml"
    bump("base shape", schema_dir=schema_dir, path=path)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "base contract")
    _git(tmp_path, "branch", BASE_REF)
    return schema_dir, path, tmp_path


def test_rebump_refuses_the_base_s_own_entry(contract_repo):
    schema_dir, path, repo = contract_repo
    assert base_contract_version(BASE_REF, path) == 1
    with pytest.raises(ValueError, match="at or below base"):
        rebump("smuggled rewrite", schema_dir=schema_dir, path=path, base=BASE_REF)
    # the refusal changed nothing on disk
    assert load_contract(path)["history"][-1]["note"] == "base shape"


def test_rebump_folds_only_the_branch_entry_above_base(contract_repo):
    schema_dir, path, repo = contract_repo
    branch = bump("branch shape", schema_dir=schema_dir, path=path)
    assert branch["contract_version"] == 2

    folded = rebump("branch shape, folded", schema_dir=schema_dir, path=path,
                    base=BASE_REF)
    assert folded["contract_version"] == 2          # no third version on this branch
    assert len(folded["history"]) == 2              # the iteration replaced, not appended
    assert folded["history"][-1]["note"] == "branch shape, folded"
    assert folded["schema_fingerprint"] == branch["schema_fingerprint"]

    shown = subprocess.run(
        ["git", "-C", str(repo), "show",
         f"{BASE_REF}:system/contracts/data-contract.yaml"],
        check=True, capture_output=True, text=True).stdout
    import yaml
    base_entry = yaml.safe_load(shown)["history"][0]
    assert folded["history"][0] == base_entry       # the base's v1 is untouched


def test_rebump_moves_the_fingerprint_when_schemas_changed(contract_repo):
    schema_dir, path, _repo = contract_repo
    bump("branch shape", schema_dir=schema_dir, path=path)
    before = rebump("fold point", schema_dir=schema_dir, path=path, base=BASE_REF)

    target = next(iter(sorted(schema_dir.glob("*.schema.json"))))
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    after = rebump("schema iteration folded", schema_dir=schema_dir, path=path,
                   base=BASE_REF)
    assert after["contract_version"] == before["contract_version"]
    assert after["schema_fingerprint"] != before["schema_fingerprint"]
    assert load_contract(path)["schema_fingerprint"] == after["schema_fingerprint"]


def test_rebump_fails_closed_on_an_unreadable_base(contract_repo):
    schema_dir, path, _repo = contract_repo
    bump("branch shape", schema_dir=schema_dir, path=path)
    with pytest.raises(ValueError, match="cannot read the data contract"):
        rebump("fold", schema_dir=schema_dir, path=path, base="no-such-ref")


def test_rebump_refuses_when_there_is_no_entry_to_fold(tmp_path):
    with pytest.raises(ValueError, match="no history entry"):
        rebump("nothing to fold", schema_dir=SCHEMA_DIR,
               path=tmp_path / "absent.yaml")
