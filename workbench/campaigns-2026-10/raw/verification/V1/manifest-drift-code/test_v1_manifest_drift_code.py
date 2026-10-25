"""V1 finding: changing-contracts.md:60 — "When ``MANIFEST-CONTRACT-DRIFT``
fires:" names a drift diagnostic that no code emits.

The sibling gate does emit a named code (``SCHEMA-CONTRACT-DRIFT``,
derive/validation/contract.py:70), but the manifest-contract gate raises
``ManifestContractError`` with prose whose message never contains
``MANIFEST-CONTRACT-DRIFT``. The name appears only in a YAML comment and in
the document itself. This test drives the real gate (as
tests/test_manifest_contract.py does) and asserts the documented diagnostic;
it fails on the pin.
"""

from __future__ import annotations

import pytest

from learning_os.derive.projection.manifest import build_manifest
from learning_os.store.contracts.manifest_contract import check, enforce
from learning_os.store.loader import load_repo


def _tampered_manifest(mini_repo) -> dict:
    """A manifest that genuinely violates the declared contract."""
    manifest = build_manifest(load_repo(mini_repo), "T1", enforce_contract=False)
    manifest["experimental_widgets"] = []
    return manifest


def test_manifest_drift_message_carries_the_documented_code(mini_repo):
    ok, message = check(_tampered_manifest(mini_repo), mini_repo)
    assert not ok, "the tampered manifest must fail the declared contract"
    assert "MANIFEST-CONTRACT-DRIFT" in message, (
        "changing-contracts.md:60 documents the manifest drift failure as "
        "MANIFEST-CONTRACT-DRIFT, but the gate's actual message is: "
        f"{message[:300]}")


def test_manifest_drift_exception_carries_the_documented_code(mini_repo):
    import pytest

    from learning_os.store.contracts.manifest_contract import (
        ManifestContractError,
    )

    with pytest.raises(ManifestContractError) as excinfo:
        enforce(_tampered_manifest(mini_repo), mini_repo)
    assert "MANIFEST-CONTRACT-DRIFT" in str(excinfo.value), (
        "the raised manifest-contract failure never names "
        f"MANIFEST-CONTRACT-DRIFT: {str(excinfo.value)[:300]}")
