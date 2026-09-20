"""Stage-4 manifest proof: validation is reused only on identical identity.

The proof key covers the complete manifest bytes, the contract closure,
the validator implementation, and the semantics version. Anything else
reruns enforce(); failures raise out of the builder, which the engine
never caches. The enforce spy below counts shadow-side validations, so
"hit" means validation truly did not run again.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from repo_builders import (
    add_manifest_fixtures,
    curriculum_mini,
    stage_manifest_producers,
    trace_summary,
)

from learning_os.contracts.manifest_contract import (
    ManifestContractError,
    declared_version,
)
from learning_os.derived.identity import digest_bytes
from learning_os.derived.store import canonical_bytes, derived_dir, read_state
from learning_os.genout import manifest_derived
from learning_os.genout.manifest_derived import (
    VALIDATION_PROOF_ID,
    build_manifest_shadow,
    compare_shadow_manifest,
    contract_closure_digest,
)
from learning_os.loader import load_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
STAMP = "2026-09-20T00:00:00+02:00"
NOTE = "knowledge/notes/mathematics/note-demo.md"


def _warmed(tmp_path: Path, *, rich: bool = False) -> Path:
    mini = curriculum_mini(tmp_path)
    if rich:
        add_manifest_fixtures(mini)
    repo = load_repo(mini)
    stage_manifest_producers(mini, repo)
    assert compare_shadow_manifest(repo, STAMP).equivalent
    return mini


class _EnforceSpy:
    """Counts shadow-side enforce() calls while preserving behavior."""

    def __init__(self, monkeypatch):
        self.calls = 0
        real = manifest_derived.enforce

        def counting(payload, root):
            self.calls += 1
            return real(payload, root)

        monkeypatch.setattr(manifest_derived, "enforce", counting)


def test_warm_manifest_reuses_proof_without_validating(tmp_path, monkeypatch):
    mini = _warmed(tmp_path)
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    build_manifest_shadow(load_repo(mini), STAMP, trace=trace)
    assert trace_summary(trace)[VALIDATION_PROOF_ID] == ("hit", "node-key-equal")
    assert spy.calls == 0


def test_manifest_change_reruns_validation(tmp_path, monkeypatch):
    mini = _warmed(tmp_path)
    note = mini / NOTE
    note.write_text(note.read_text(encoding="utf-8") + "\nTrailing.\n",
                    encoding="utf-8")
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    build_manifest_shadow(load_repo(mini), STAMP, trace=trace)
    assert trace_summary(trace)[VALIDATION_PROOF_ID] == (
        "rebuilt", "node-key-changed-output-changed")
    assert spy.calls == 1


def test_identical_rewrite_reuses_proof(tmp_path, monkeypatch):
    """Same bytes, same proof: content addressing, not mtime luck."""
    mini = _warmed(tmp_path)
    note = mini / NOTE
    note.write_bytes(note.read_bytes())
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    summary = trace_summary(trace)
    assert summary[VALIDATION_PROOF_ID] == ("hit", "node-key-equal")
    assert all(status == "hit" for status, _ in summary.values())
    assert spy.calls == 0


def test_contract_comment_reruns_validation(tmp_path, monkeypatch):
    mini = _warmed(tmp_path, rich=True)
    contract = mini / "system/contracts/manifest-contract.yaml"
    contract.write_text(contract.read_text(encoding="utf-8") + "\n# probe\n",
                        encoding="utf-8")
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace_summary(trace)[VALIDATION_PROOF_ID][0] == "rebuilt"
    assert spy.calls == 1


def test_registry_schema_change_reruns_validation(tmp_path, monkeypatch):
    mini = _warmed(tmp_path, rich=True)
    schemas = sorted((mini / "system/schema").glob("*.schema.json"))
    assert schemas
    target = schemas[0]
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace_summary(trace)[VALIDATION_PROOF_ID][0] == "rebuilt"
    assert spy.calls == 1


def test_validator_code_change_reruns_only_validation(tmp_path, monkeypatch):
    mini = _warmed(tmp_path)
    staged = mini / "tools/learning_os/contracts/manifest_contract.py"
    staged.write_text(staged.read_text(encoding="utf-8") + "\n# probe\n",
                      encoding="utf-8")
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    summary = trace_summary(trace)
    assert summary[VALIDATION_PROOF_ID] == (
        "rebuilt", "node-key-changed-output-same")
    for node, (status, reason) in summary.items():
        if node != VALIDATION_PROOF_ID:
            assert (status, reason) == ("hit", "node-key-equal"), node
    assert spy.calls == 1


def test_corrupt_proof_blob_reruns_and_heals(tmp_path, monkeypatch):
    mini = _warmed(tmp_path)
    blob = derived_dir(mini) / read_state(mini)[VALIDATION_PROOF_ID].blob
    blob.write_bytes(b"forged-bytes")
    spy = _EnforceSpy(monkeypatch)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace_summary(trace)[VALIDATION_PROOF_ID] == ("rebuilt", "cache-miss")
    assert spy.calls == 1
    healed: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=healed).equivalent
    assert trace_summary(healed)[VALIDATION_PROOF_ID] == ("hit", "node-key-equal")
    assert spy.calls == 1


def test_failed_validation_is_never_reused(tmp_path, monkeypatch):
    mini = _warmed(tmp_path, rich=True)
    import yaml

    contract_doc = yaml.safe_load(
        (mini / "system/contracts/manifest-contract.yaml").read_text(encoding="utf-8"))
    schema = mini / contract_doc["schema_path"]
    original = schema.read_bytes()
    schema.write_bytes(original + b"\n")
    spy = _EnforceSpy(monkeypatch)
    with pytest.raises(ManifestContractError):
        build_manifest_shadow(load_repo(mini), STAMP)
    assert spy.calls == 1
    # The failure stored nothing: restoring the exact bytes hits the old proof.
    schema.write_bytes(original)
    trace: list = []
    build_manifest_shadow(load_repo(mini), STAMP, trace=trace)
    assert trace_summary(trace)[VALIDATION_PROOF_ID] == ("hit", "node-key-equal")
    assert spy.calls == 1


def test_proof_value_carries_its_identity(tmp_path):
    mini = _warmed(tmp_path)
    payload = build_manifest_shadow(load_repo(mini), STAMP)
    full_digest = digest_bytes(canonical_bytes(payload))
    state = read_state(mini)[VALIDATION_PROOF_ID]
    blob = derived_dir(mini) / state.blob
    import json

    proof = json.loads(blob.read_text(encoding="utf-8"))
    assert proof["valid"] is True
    assert proof["contract_version"] == declared_version(mini)
    assert proof["manifest_sha256"] == full_digest
    assert proof["contract_closure_sha256"] == contract_closure_digest(mini)


def test_reuse_can_be_disabled_without_changing_output(tmp_path, monkeypatch):
    mini = _warmed(tmp_path)
    spy = _EnforceSpy(monkeypatch)
    direct = build_manifest_shadow(load_repo(mini), STAMP, reuse_validation=False)
    assert spy.calls == 1
    assert compare_shadow_manifest(load_repo(mini), STAMP).equivalent
    assert direct == compare_shadow_manifest(load_repo(mini), STAMP).shadow
