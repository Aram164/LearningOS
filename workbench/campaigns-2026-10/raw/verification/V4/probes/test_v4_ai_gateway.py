"""V4 campaign (2026-10-25): the seven AI-action cases through the real gateway.

Every test drives the public surfaces exactly as `tests/gateway_helpers.py`
does — the AI capability via a GatewayEnvelopeV2 subprocess with
``approved-delivery`` authority, the manual verbs via their CLI — over the
same fixture `tests/test_ai_actions.py` builds. Stub/manual providers only;
no network, no model. All tests pass on the pin `fb73b0f9`; they pin the
refusal behaviors the 2026-10-25 V4 verification batch relied on, plus two
observed behaviors (duplicate-relation dedup, re-apply under a fresh approval).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from repo_builders import copy_real_contracts

from learning_os.store.contracts.gateway import intent_sha256
from learning_os.store.fingerprint import canonical_fingerprint, source_fingerprint
from learning_os.store.loader import load_repo
from learning_os.store.revisions import artifact_revision

ROOT = Path(__file__).resolve().parent.parent
LOS = ROOT / "tools" / "los.py"
FIXED_STAMP = "2026-08-04T01:00:00+00:00"
TARGET_ID = "garden-note-handwritten-import-registration"
SEED = "knowledge/garden/handwritten-import-registration.md"
CANONICAL = ("knowledge/", "curriculum/", "records/", "sources/", "work/",
             "archive/", "materials/")


def write_yaml(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")


@pytest.fixture()
def v4_repo(mini_repo: Path) -> Path:
    copy_real_contracts(ROOT, mini_repo)
    for rel in ("operations/ai-actions/requests",
                "operations/ai-actions/deliveries",
                "operations/ai-actions/garden-state",
                "knowledge/garden"):
        (mini_repo / rel).mkdir(parents=True, exist_ok=True)
    (mini_repo / SEED).write_text(
        "# Import registration\n\nThe decorator stores the function during "
        "import. #python #optimizer\n", encoding="utf-8")
    write_yaml(mini_repo / "operations/ai-actions/relationships.yaml", {
        "schema_version": 1, "relationships": []})
    return mini_repo


def los(root: Path, *args: str, payload: dict | None = None):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True, text=True, timeout=120,
    )


def v2_error(r) -> str:
    for stream in (r.stdout, r.stderr):
        try:
            body = json.loads(stream)
            if isinstance(body, dict) and body.get("ok") is False:
                return str(body.get("error", {}).get("message", ""))
        except Exception:
            pass
    return (r.stderr or r.stdout)


def snapshot(root: Path) -> str:
    return "sha256:" + canonical_fingerprint(root)


def prepare(root: Path, *, provider: str = "manual-bundle",
            request_id: str | None = None, expect_ok: bool = True):
    args = ["ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note", "--target-id", TARGET_ID,
            "--provider", provider, "--json"]
    if request_id:
        args += ["--request-id", request_id]
    r = los(root, *args)
    if expect_ok:
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)["request"]
    assert r.returncode != 0
    return json.loads(r.stderr)


def full_request(root: Path, request: dict) -> dict:
    return yaml.safe_load(
        (root / request["bundle_path"] / "request.yaml").read_text())


def stub_delivery(root: Path, tmp_path: Path, request: dict, *,
                  delivery_id: str, target_id: str, operations=None) -> Path:
    source = tmp_path / f"provider-response-{delivery_id}"
    (source / "artifacts").mkdir(parents=True, exist_ok=True)
    (source / "artifacts/transcription.md").write_text(
        "The decorator factory receives the family first; its returned "
        "decorator later receives the function.\n", encoding="utf-8")
    ops = operations if operations is not None else [
        {"capability": "garden.add-transcription", "target_id": target_id,
         "artifact_ref": "artifacts/transcription.md"},
        {"capability": "garden.update", "target_id": target_id,
         "patch": {"title": "Import-Time Registration", "state": "developing"}},
        {"capability": "relationship.create",
         "payload": {"id": "relationship-garden-module-demo",
                     "from": {"kind": "garden-note", "id": target_id},
                     "relation": "supports",
                     "to": {"kind": "module", "id": "module-demo"}}},
    ]
    write_yaml(source / "delivery.yaml", {
        "schema_version": 1,
        "id": delivery_id,
        "type": "ai-action-delivery",
        "request_id": request["id"],
        "action_id": request["action_id"],
        "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {"user_approved": True, "approved_at": FIXED_STAMP},
        "operations": ops,
        "preconditions": request["preconditions"],
    })
    return source


def import_delivery(root: Path, source: Path, delivery_id: str,
                    expect_ok: bool = True):
    r = los(root, "ai-action-import-delivery", str(source), "--json")
    if expect_ok:
        assert r.returncode == 0, r.stderr or r.stdout
        r2 = los(root, "ai-action-validate-delivery", delivery_id, "--json")
        assert r2.returncode == 0, r2.stderr
        return json.loads(r.stdout)
    assert r.returncode != 0
    return json.loads(r.stderr)["error"]["message"]


def artifact_transaction_ids(root: Path, delivery_id: str) -> set[str]:
    directory = root / "operations/ai-actions/deliveries" / delivery_id
    delivery = yaml.safe_load((directory / "delivery.yaml").read_text())
    request = yaml.safe_load(
        (root / "operations/ai-actions/requests" / delivery["request_id"]
         / "request.yaml").read_text())
    tid = request["target"]["id"]
    ids = {tid}
    for op in delivery["operations"]:
        if op["capability"] == "garden.add-transcription":
            ids.add(f"transcription-{tid}")
        elif op["capability"] == "relationship.create":
            ids.add(op["payload"]["id"])
        elif op["capability"] == "unit.material-synthesis.publish":
            record = yaml.safe_load((directory / op["artifact_ref"]).read_text())
            ids.add(record["id"])
    return ids


def build_apply_envelope(root: Path, delivery_id: str, *,
                         idempotency_key: str | None = None,
                         fresh_snapshot: bool = False,
                         extra_payload: dict | None = None) -> dict:
    directory = root / "operations/ai-actions/deliveries" / delivery_id
    delivery = yaml.safe_load((directory / "delivery.yaml").read_text())
    delivery_hash = "sha256:" + hashlib.sha256(
        (directory / "delivery.yaml").read_bytes()).hexdigest()
    artifact_hashes = {}
    for op in delivery["operations"]:
        ref = op.get("artifact_ref")
        if ref:
            artifact_hashes[ref] = "sha256:" + hashlib.sha256(
                (directory / ref).read_bytes()).hexdigest()
    ids = artifact_transaction_ids(root, delivery_id)
    revisions = {a: artifact_revision(root, a) for a in sorted(ids)}
    envelope = {
        "schema_version": 2,
        "request_id": f"apply-{idempotency_key or delivery_id}",
        "idempotency_key": idempotency_key or f"apply-{delivery_id}",
        "capability": "ai-action.delivery.apply",
        "channel": "operator",
        "expected_snapshot": snapshot(root) if fresh_snapshot else None,
        "expected_revisions": revisions,
        "approval": {"kind": "approved-delivery",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": {"delivery_id": delivery_id,
                    "delivery_sha256": delivery_hash,
                    "artifact_sha256": artifact_hashes},
    }
    if envelope["expected_snapshot"] is None:
        # the pre-apply snapshot: only valid before the first apply touches
        # the tree, so compute it here and freeze it for exact replays
        envelope["expected_snapshot"] = snapshot(root)
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    if extra_payload:
        envelope["payload"].update(extra_payload)
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def apply_env(root: Path, envelope: dict, *, expect_ok: bool = True) -> dict:
    r = los(root, "capability", "ai-action.delivery.apply",
            "--payload-file", "-", payload=envelope)
    body = None
    for stream in (r.stdout, r.stderr):
        try:
            parsed = json.loads(stream)
            if isinstance(parsed, dict):
                body = parsed
                break
        except Exception:
            continue
    if expect_ok:
        assert r.returncode == 0, body or r.stderr
        return body
    assert r.returncode != 0
    assert body is not None and body.get("ok") is False, body
    return body


def apply_delivery(root: Path, delivery_id: str, *, expect_ok: bool = True,
                   **kwargs) -> dict:
    return apply_env(root, build_apply_envelope(root, delivery_id, **kwargs),
                     expect_ok=expect_ok)


def file_tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
        and "generated" not in p.parts and ".git" not in p.parts
    }


def canonical_effects(before: dict, after: dict) -> list[str]:
    changed = [k for k in set(before) & set(after) if before[k] != after[k]]
    added = sorted(set(after) - set(before))
    return [p for p in added + changed if p.startswith(CANONICAL)]


def receipts(root: Path) -> list[str]:
    tx = root / "operations/transactions"
    return sorted(p.name for p in tx.glob("transaction-*.yaml")) if tx.is_dir() else []


# ------------------------------------------------------- case 1: binding

def test_target_change_after_prepare_refuses_import(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-1a")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-1a",
                           target_id=request["target"]["id"])
    seed = v4_repo / SEED
    seed.write_text(seed.read_text() + "\nChanged after preparation.\n")
    message = import_delivery(v4_repo, source, "ai-delivery-v4-1a",
                              expect_ok=False)
    assert "Garden target changed after request preparation" in message


def test_target_change_after_import_refuses_apply_with_fresh_snapshot(
        v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-1b")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-1b",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-1b")
    seed = v4_repo / SEED
    seed.write_text(seed.read_text() + "\nChanged after import.\n")
    before = file_tree(v4_repo)
    error = apply_delivery(v4_repo, "ai-delivery-v4-1b", fresh_snapshot=True,
                           expect_ok=False)
    assert error["error"]["code"] == "STALE_SNAPSHOT"
    assert "Garden target changed after request preparation" \
        in error["error"]["message"]
    assert canonical_effects(before, file_tree(v4_repo)) == []


def test_prepare_refuses_a_stale_expected_snapshot(v4_repo):
    r = los(v4_repo, "ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note", "--target-id", TARGET_ID,
            "--provider", "manual-bundle",
            "--expected-snapshot", "sha256:" + "0" * 64, "--json")
    assert r.returncode != 0
    assert "expected snapshot sha256:0000" in json.loads(r.stderr)["error"]["message"]


def test_operation_targeting_another_note_is_refused(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-1d")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-1d",
                           target_id=request["target"]["id"],
                           operations=[{
                               "capability": "garden.add-transcription",
                               "target_id": "garden-note-some-other-seed",
                               "artifact_ref": "artifacts/transcription.md",
                           }])
    message = import_delivery(v4_repo, source, "ai-delivery-v4-1d",
                              expect_ok=False)
    assert "targets an unrelated artifact" in message


# --------------------------------------------- case 2: partial approval

def test_apply_payload_admits_no_subset_selection(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-2a")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-2a",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-2a")
    error = apply_delivery(v4_repo, "ai-delivery-v4-2a",
                           extra_payload={"selected_operations": [0]},
                           expect_ok=False)
    assert "Additional properties are not allowed" in error["error"]["message"]


def test_whole_delivery_approval_applies_every_operation(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-2b")
    tid = request["target"]["id"]
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-2b", target_id=tid)
    import_delivery(v4_repo, source, "ai-delivery-v4-2b")
    out = apply_delivery(v4_repo, "ai-delivery-v4-2b")
    receipt = yaml.safe_load((v4_repo / out["receipt_path"]).read_text())
    written = {w["path"] for w in receipt["writes"]}
    assert {
        f"knowledge/garden/transcriptions/{tid}.md",
        f"operations/ai-actions/garden-state/{tid}.yaml",
        "operations/ai-actions/relationships.yaml",
    } <= written
    state = yaml.safe_load(
        (v4_repo / f"operations/ai-actions/garden-state/{tid}.yaml").read_text())
    assert state["title"] == "Import-Time Registration"
    registry = yaml.safe_load(
        (v4_repo / "operations/ai-actions/relationships.yaml").read_text())
    assert len(registry["relationships"]) == 1
    assert full_request(v4_repo, request)["status"] == "completed"


def test_duplicate_relationship_id_is_deduplicated_not_applied(
        v4_repo, tmp_path):
    """Observed behavior (V4 O2): an approved relationship.create naming an
    existing registry id is silently dropped — the pre-existing row survives
    with its own provenance, created_ids stays empty, and the receipt stays
    honest about what was applied."""
    request = prepare(v4_repo, request_id="ai-request-v4-o2")
    tid = request["target"]["id"]
    registry = v4_repo / "operations/ai-actions/relationships.yaml"
    write_yaml(registry, {"schema_version": 1, "relationships": [{
        "id": "relationship-garden-module-demo",
        "from": {"kind": "garden-note", "id": tid},
        "relation": "supports", "to": {"kind": "module", "id": "module-demo"},
        "provenance": {"source": "manual"},
    }]})
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-o2", target_id=tid,
                           operations=[
                               {"capability": "relationship.create",
                                "payload": {
                                    "id": "relationship-garden-module-demo",
                                    "from": {"kind": "garden-note", "id": tid},
                                    "relation": "supports",
                                    "to": {"kind": "module", "id": "module-demo"}}},
                               {"capability": "garden.update",
                                "target_id": tid,
                                "patch": {"title": "T", "state": "developing"}},
                           ])
    import_delivery(v4_repo, source, "ai-delivery-v4-o2")
    # the deduped relation id is not a transaction artifact, so the envelope
    # must not cover it
    envelope = build_apply_envelope(v4_repo, "ai-delivery-v4-o2")
    envelope["expected_revisions"] = {
        tid: artifact_revision(v4_repo, tid)}
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    out = apply_env(v4_repo, envelope)
    receipt = yaml.safe_load((v4_repo / out["receipt_path"]).read_text())
    assert receipt["metadata"]["created_ids"] == []
    rows = yaml.safe_load(registry.read_text())["relationships"]
    assert [row["provenance"]["source"] for row in rows] == ["manual"]


# ------------------------------------------------------- case 3: receipts

def test_receipt_written_once_and_exact_replay_reuses_it(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-3a")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-3a",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-3a")
    envelope = build_apply_envelope(v4_repo, "ai-delivery-v4-3a")
    first = apply_env(v4_repo, envelope)
    one = receipts(v4_repo)
    assert len(one) == 1
    before = file_tree(v4_repo)
    replayed = apply_env(v4_repo, envelope)
    assert replayed["replayed"] is True
    assert replayed["receipt_path"] == first["receipt_path"]
    assert receipts(v4_repo) == one
    assert canonical_effects(before, file_tree(v4_repo)) == []


def test_receipt_matches_disk_bytes_and_live_snapshot(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-3b")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-3b",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-3b")
    out = apply_delivery(v4_repo, "ai-delivery-v4-3b")
    receipt = yaml.safe_load((v4_repo / out["receipt_path"]).read_text())
    for row in receipt["writes"]:
        path = v4_repo / row["path"]
        assert path.is_file(), row["path"]
        if row.get("sha256_after"):
            assert row["sha256_after"] in (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            ), row["path"]
    live = "sha256:" + source_fingerprint(load_repo(v4_repo))
    assert receipt["snapshot_after"] == live


def test_reapply_under_a_new_key_is_refused(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-3c")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-3c",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-3c")
    apply_delivery(v4_repo, "ai-delivery-v4-3c")
    one = receipts(v4_repo)
    error = apply_delivery(v4_repo, "ai-delivery-v4-3c", fresh_snapshot=True,
                           idempotency_key="apply-v4-3c-second",
                           expect_ok=False)
    assert "already exists" in error["error"]["message"]
    assert receipts(v4_repo) == one


def test_reapply_under_a_fresh_approval_is_a_second_transaction(
        v4_repo, tmp_path):
    """Observed behavior (V4 O1): with no transcription to guard it, the same
    delivery applies again under a second, freshly minted approval — two
    receipts, one per approved intent, each honest. Gateway semantics; no
    contract names a one-application-per-delivery rule."""
    request = prepare(v4_repo, request_id="ai-request-v4-o1")
    tid = request["target"]["id"]
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-o1", target_id=tid,
                           operations=[{"capability": "garden.update",
                                        "target_id": tid,
                                        "patch": {"title": "Once",
                                                  "state": "developing"}}])
    import_delivery(v4_repo, source, "ai-delivery-v4-o1")
    first = apply_delivery(v4_repo, "ai-delivery-v4-o1")
    second = apply_delivery(v4_repo, "ai-delivery-v4-o1", fresh_snapshot=True,
                            idempotency_key="apply-v4-o1-second")
    assert first["transaction_id"] != second["transaction_id"]
    assert second["replayed"] is False
    assert len(receipts(v4_repo)) == 2
    state = yaml.safe_load(
        (v4_repo / f"operations/ai-actions/garden-state/{tid}.yaml").read_text())
    assert state["revision"] == 2
    assert full_request(v4_repo, request)["receipt_id"] == second["transaction_id"]


def test_manifest_regeneration_after_gateway_apply(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-3e")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-3e",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-3e")
    apply_delivery(v4_repo, "ai-delivery-v4-3e")
    manifest = json.loads((v4_repo / "generated/manifest.json").read_text())
    assert any(row.get("id") == request["id"] and row.get("status") == "completed"
               for row in manifest.get("ai_actions", {}).get("requests", []))


# ------------------------------------- case 4: replay / foreign requests

def test_exact_replay_answers_replayed_with_no_writes(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-4a")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-4a",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-4a")
    envelope = build_apply_envelope(v4_repo, "ai-delivery-v4-4a")
    first = apply_env(v4_repo, envelope)
    before = file_tree(v4_repo)
    replayed = apply_env(v4_repo, envelope)
    assert replayed["replayed"] is True
    assert replayed["transaction_id"] == first["transaction_id"]
    assert canonical_effects(before, file_tree(v4_repo)) == []


def test_delivery_for_an_unknown_request_is_refused(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-4b")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-4b",
                           target_id=request["target"]["id"])
    body = yaml.safe_load((source / "delivery.yaml").read_text())
    body["request_id"] = "ai-request-does-not-exist"
    write_yaml(source / "delivery.yaml", body)
    message = import_delivery(v4_repo, source, "ai-delivery-v4-4b",
                              expect_ok=False)
    assert "not found" in message


def test_delivery_for_a_foreign_request_with_wrong_preconditions_is_refused(
        v4_repo, tmp_path):
    request1 = prepare(v4_repo, request_id="ai-request-v4-r1")
    full1 = full_request(v4_repo, request1)
    seed = v4_repo / SEED
    seed.write_text(seed.read_text() + "\nChanged before request 2.\n")
    prepare(v4_repo, request_id="ai-request-v4-r2")
    source = stub_delivery(v4_repo, tmp_path, full1,
                           delivery_id="ai-delivery-v4-4c",
                           target_id=request1["target"]["id"])
    body = yaml.safe_load((source / "delivery.yaml").read_text())
    body["request_id"] = "ai-request-v4-r2"
    write_yaml(source / "delivery.yaml", body)
    message = import_delivery(v4_repo, source, "ai-delivery-v4-4c",
                              expect_ok=False)
    assert "preconditions must equal the prepared request preconditions" in message


# ------------------------------------------------ case 5: one relation path

def test_concept_relation_registry_has_one_declared_writer(v4_repo):
    contract = yaml.safe_load(
        (v4_repo / "system/contracts/capabilities.yaml").read_text())
    writers = []
    for kind in ("domain_capabilities", "commands"):
        for name, definition in contract[kind].items():
            for scope in definition.get("writes", []) or []:
                if "concept-relations" in scope:
                    writers.append(f"{kind}:{name}")
    assert writers == ["commands:concept.relations.change",
                       "commands:concept.relations.change"]


def test_ai_delivery_cannot_carry_concept_relations_change(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-5b")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-5b",
                           target_id=request["target"]["id"],
                           operations=[{
                               "capability": "concept.relations.change",
                               "target_id": request["target"]["id"],
                               "payload": {"change": {"operations": [
                                   {"action": "add",
                                    "new": {"from": "concept-variance",
                                            "type": "builds-on",
                                            "to": "concept-expected-value"}}]}},
                           }])
    message = import_delivery(v4_repo, source, "ai-delivery-v4-5b",
                              expect_ok=False)
    assert "capability is not allowed" in message


def test_manual_relation_edit_works_without_any_ai(v4_repo):
    relations = v4_repo / "knowledge/concept-relations.yaml"
    before = relations.read_bytes()
    envelope = {
        "schema_version": 2,
        "request_id": "request-v4-5c",
        "idempotency_key": "v4-5c",
        "capability": "concept.relations.change",
        "channel": "operator",
        "expected_snapshot": snapshot(v4_repo),
        "expected_revisions": {
            "registry-concept-relations":
                artifact_revision(v4_repo, "registry-concept-relations")},
        "approval": {"kind": "operator-approval",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": {"change": {"operations": [
            {"action": "add", "new": {"from": "concept-expected-value",
                                      "type": "motivates",
                                      "to": "concept-variance"}}]}},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    r = los(v4_repo, "capability", "concept.relations.change",
            "--payload-file", "-", payload=envelope)
    assert r.returncode == 0, v2_error(r)
    assert relations.read_bytes() != before


def test_gesture_claim_of_the_relation_editor_fails_closed(v4_repo):
    envelope = {
        "schema_version": 2,
        "request_id": "request-v4-5e",
        "idempotency_key": "v4-5e",
        "capability": "concept.relations.change",
        "channel": "operator",
        "expected_snapshot": snapshot(v4_repo),
        "expected_revisions": {
            "registry-concept-relations":
                artifact_revision(v4_repo, "registry-concept-relations")},
        "approval": {"kind": "direct-user-gesture",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": {"change": {"operations": [
            {"action": "add", "new": {"from": "concept-expected-value",
                                      "type": "motivates",
                                      "to": "concept-variance"}}]}},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    r = los(v4_repo, "capability", "concept.relations.change",
            "--payload-file", "-", payload=envelope)
    assert r.returncode != 0
    assert "reviewed action" in v2_error(r)


def test_garden_apply_leaves_concept_registry_byte_identical(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-5d")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-5d",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-5d")
    before = (v4_repo / "knowledge/concept-relations.yaml").read_bytes()
    apply_delivery(v4_repo, "ai-delivery-v4-5d")
    assert (v4_repo / "knowledge/concept-relations.yaml").read_bytes() == before


# ------------------------------------------------ case 6: no provider

def test_unavailable_provider_refused_at_prepare(v4_repo):
    error = prepare(v4_repo, provider="claude", expect_ok=False)
    assert "provider claude has no available adapter" in error["error"]["message"]


def test_with_zero_adapters_the_manual_authoring_path_still_works(v4_repo):
    adapters_path = v4_repo / "system/contracts/ai-adapters.yaml"
    adapters = yaml.safe_load(adapters_path.read_text())
    for row in adapters["adapters"]:
        row["available"] = False
    write_yaml(adapters_path, adapters)
    assert los(v4_repo, "ai-action-list", "--json").returncode == 0
    error = prepare(v4_repo, expect_ok=False)
    assert "no available adapter" in error["error"]["message"]
    envelope = {
        "schema_version": 2,
        "request_id": "request-v4-6b",
        "idempotency_key": "v4-6b",
        "capability": "concept.relations.change",
        "channel": "ui",
        "expected_snapshot": snapshot(v4_repo),
        "expected_revisions": {
            "registry-concept-relations":
                artifact_revision(v4_repo, "registry-concept-relations")},
        "approval": {"kind": "operator-approval",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": {"change": {"operations": [
            {"action": "add", "new": {"from": "concept-expected-value",
                                      "type": "motivates",
                                      "to": "concept-variance"}}]}},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    r = los(v4_repo, "capability", "concept.relations.change",
            "--payload-file", "-", payload=envelope)
    assert r.returncode == 0, v2_error(r)


def test_manual_bundle_round_trip_on_the_pin(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-6c")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-6c",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-6c")
    out = apply_delivery(v4_repo, "ai-delivery-v4-6c")
    assert out["ok"] is True


# --------------------------------------------- case 7: no direct writes

def test_symlink_in_bundle_refused_quarantine_only(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-7a")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-7a",
                           target_id=request["target"]["id"])
    (source / "artifacts/link.md").symlink_to(
        source / "artifacts/transcription.md")
    before = file_tree(v4_repo)
    message = import_delivery(v4_repo, source, "ai-delivery-v4-7a",
                              expect_ok=False)
    assert "may not contain symbolic links" in message
    after = file_tree(v4_repo)
    assert all(name.startswith("operations/")
               for name in set(after) - set(before))


def test_traversal_artifact_ref_refused_and_seed_untouched(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-7b")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-7b",
                           target_id=request["target"]["id"],
                           operations=[{
                               "capability": "garden.add-transcription",
                               "target_id": request["target"]["id"],
                               "artifact_ref": "artifacts/../../seed-escape.md",
                           }])
    seed = v4_repo / SEED
    before_seed = seed.read_bytes()
    message = import_delivery(v4_repo, source, "ai-delivery-v4-7b",
                              expect_ok=False)
    assert "unsafe bundle path" in message
    assert seed.read_bytes() == before_seed


def test_rejected_import_never_lands_in_deliveries(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-7c")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-7c",
                           target_id=request["target"]["id"])
    (source / "artifacts/link.md").symlink_to(
        source / "artifacts/transcription.md")
    import_delivery(v4_repo, source, "ai-delivery-v4-7c", expect_ok=False)
    deliveries = v4_repo / "operations/ai-actions/deliveries"
    assert not any(deliveries.glob("*"))


def test_canonical_writer_outside_allowlist_refused(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-7d")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-7d",
                           target_id=request["target"]["id"],
                           operations=[{"capability": "note.create",
                                        "payload": {"id": "note-evil"}}])
    message = import_delivery(v4_repo, source, "ai-delivery-v4-7d",
                              expect_ok=False)
    assert "capability is not allowed" in message


def test_post_approval_artifact_tamper_refused_at_apply(v4_repo, tmp_path):
    request = prepare(v4_repo, request_id="ai-request-v4-7e")
    source = stub_delivery(v4_repo, tmp_path, full_request(v4_repo, request),
                           delivery_id="ai-delivery-v4-7e",
                           target_id=request["target"]["id"])
    import_delivery(v4_repo, source, "ai-delivery-v4-7e")
    envelope = build_apply_envelope(v4_repo, "ai-delivery-v4-7e")
    artifact = (v4_repo / "operations/ai-actions/deliveries/ai-delivery-v4-7e"
                / "artifacts/transcription.md")
    artifact.write_text("TAMPERED after approval.\n", encoding="utf-8")
    before = file_tree(v4_repo)
    error = apply_env(v4_repo, envelope, expect_ok=False)
    assert "content hash does not match the imported bytes" \
        in error["error"]["message"]
    assert canonical_effects(before, file_tree(v4_repo)) == []


# ------------------------------------ scope: the second registered action

def test_unit_compare_materials_round_trip_through_gateway(v4_repo, tmp_path):
    from repo_builders import _sliced_route, _sliced_unit
    from learning_os.derive.material_synthesis import current_unit_material_basis

    _sliced_unit(v4_repo, [_sliced_route("route-demo-l01",
                                         "lecture-01.pdf, PDF p. 1")])
    args = ["ai-action-prepare", "--action-id", "unit.compare-materials",
            "--target-kind", "unit", "--target-id", "unit-demo-l01",
            "--provider", "manual-bundle",
            "--request-id", "ai-request-v4-unit", "--json"]
    r = los(v4_repo, *args)
    assert r.returncode == 0, r.stderr
    request = json.loads(r.stdout)["request"]
    full = full_request(v4_repo, request)

    basis = current_unit_material_basis(v4_repo, "unit-demo-l01")
    basis = {**basis, "ai_provenance": {
        "request_id": full["id"],
        "delivery_id": "ai-delivery-v4-unit",
        "provider": "manual-bundle",
    }}
    checksum = basis["material_checksums"]["route-demo-l01"]
    synthesis = {
        "schema_version": 1,
        "id": "material-synthesis-unit-demo-l01",
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": basis,
        "route_assessments": [{
            "route_id": "route-demo-l01",
            "source_id": "source-demo-book",
            "locator": "lecture-01.pdf, PDF p. 1",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "A direct derivation of the weighted sum.",
            "assumptions": "Finite discrete outcomes are assumed.",
            "notation": "Uses uppercase X and lowercase outcome values.",
            "exercise_value": "Includes a small worked calculation.",
            "best_for": "Checking the lecture's core derivation.",
            "limitations": "Does not cover continuous variables.",
            "scope_of_absence": "lecture-01.pdf, PDF p. 1 of 1",
            "evidence": [{"locator": "lecture-01.pdf p.1",
                          "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [
            {"concept_id": "concept-variance",
             "local_node_ids": ["knowledge-demo-outcomes"],
             "related_unit_ids": [], "bridge_note_ids": [],
             "narrative": "Outcomes feed later dispersion measures."},
            {"concept_id": "concept-expected-value",
             "local_node_ids": ["knowledge-demo-expectation"],
             "related_unit_ids": ["unit-demo-l01"],
             "bridge_note_ids": ["note-demo"],
             "narrative": "The local derivation is the canonical concept."},
        ],
    }
    source = tmp_path / "provider-response-ai-delivery-v4-unit"
    (source / "artifacts").mkdir(parents=True)
    (source / "artifacts/synthesis.yaml").write_text(
        yaml.safe_dump(synthesis, sort_keys=False), encoding="utf-8")
    write_yaml(source / "delivery.yaml", {
        "schema_version": 1,
        "id": "ai-delivery-v4-unit",
        "type": "ai-action-delivery",
        "request_id": full["id"],
        "action_id": "unit.compare-materials",
        "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {"user_approved": True, "approved_at": FIXED_STAMP},
        "operations": [{"capability": "unit.material-synthesis.publish",
                        "target_id": "unit-demo-l01",
                        "artifact_ref": "artifacts/synthesis.yaml"}],
        "preconditions": full["preconditions"],
    })
    import_delivery(v4_repo, source, "ai-delivery-v4-unit")
    envelope = build_apply_envelope(v4_repo, "ai-delivery-v4-unit")
    out = apply_env(v4_repo, envelope)
    assert out["ok"] is True
    dossier = (v4_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
               / "material-synthesis.yaml")
    assert dossier.is_file()
    manifest = json.loads((v4_repo / "generated/manifest.json").read_text())
    assert any(row.get("id") == full["id"]
               for row in manifest.get("ai_actions", {}).get("requests", []))
    replayed = apply_env(v4_repo, envelope)
    assert replayed["replayed"] is True
