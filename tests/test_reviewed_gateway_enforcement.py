"""Reviewed-write enforcement at the gateway (route.patch).

A capability in ``REVIEWED_SEALING_CAPABILITIES`` applies only with the
checked payload, snapshot and revisions of a prior check record, bound
by that record's own digest. Re-sealing the same draft with freshly
derived guards (``--guards auto --out`` plus ``los capability``) must
refuse, even though every guard matches the current tree.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gateway_helpers import approved_v2_call, run_v2_capability
from repo_builders import material_fixture

from learning_os.app.handlers.routes import route_patch_plan
from learning_os.store.contracts.gateway import intent_sha256, review_record_sha256
from learning_os.store.loader import load_repo

SEAL = Path(__file__).resolve().parent.parent / "tools" / "seal_envelope.py"
CAPABILITY = "route.patch"


def _seal(root: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(SEAL), "--root", str(root), *extra],
        capture_output=True, text=True, timeout=120)


def _check_out(root: Path, record: Path, payload: dict, key: str):
    return _seal(root, "--capability", CAPABILITY,
                 "--payload", json.dumps(payload), "--key", key,
                 "--guards", "auto", "--check-out", str(record),
                 "--out", str(record.with_suffix(".unused.json")))


def _receipts(root: Path) -> list[Path]:
    return sorted((root / "operations/transactions").glob("transaction-*.yaml"))


def _route_angle(root: Path, rid: str) -> str:
    repo = load_repo(root)
    route = repo.module_source_maps["module-demo"]["sources"][0]["unit_routes"][0]
    return route.get("angle")


def _apply_competing(root: Path, unit_id: str, rid: str) -> None:
    repo = load_repo(root)
    changes = {"angle": "Competing angle"}
    _, artifacts, _ = route_patch_plan(repo, unit_id, rid, changes)
    response = approved_v2_call(
        root, capability=CAPABILITY,
        payload={"unit_id": unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), idempotency_key="competing-edit")
    assert response.returncode == 0, response.stdout + response.stderr


def test_fresh_review_applies_and_the_auto_reseal_of_the_old_draft_refuses(
        mini_repo: Path, tmp_path: Path):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    payload = {"unit_id": unit_id, "route_id": rid,
               "changes": {"angle": "Reviewed angle"}}
    record = tmp_path / "review.json"
    reviewed = _check_out(mini_repo, record, payload, "reviewed-route-001")
    assert reviewed.returncode == 0, reviewed.stderr
    assert json.loads(record.read_text(encoding="utf-8"))["ok"] is True

    _apply_competing(mini_repo, unit_id, rid)
    assert _route_angle(mini_repo, rid) == "Competing angle"
    receipts_after_competing = len(_receipts(mini_repo))

    stale = _seal(mini_repo, "--guards-from", str(record), "--submit")
    assert stale.returncode != 0, stale.stdout
    assert json.loads(stale.stdout)["error"]["code"] == "STALE_SNAPSHOT"
    assert len(_receipts(mini_repo)) == receipts_after_competing

    bypass_out = tmp_path / "bypass.json"
    resealed = _seal(mini_repo, "--capability", CAPABILITY,
                     "--payload", json.dumps(payload),
                     "--key", "reviewed-route-001",
                     "--guards", "auto", "--out", str(bypass_out))
    assert resealed.returncode == 0, resealed.stderr
    refused = run_v2_capability(
        mini_repo, json.loads(bypass_out.read_text(encoding="utf-8")))
    body = json.loads(refused.stdout)
    assert refused.returncode != 0, refused.stdout
    assert body["ok"] is False
    assert body["error"]["code"] == "UNCONFIRMED", body
    assert "review" in body["error"]["message"]
    assert len(_receipts(mini_repo)) == receipts_after_competing
    assert _route_angle(mini_repo, rid) == "Competing angle"

    forged = json.loads(bypass_out.read_text(encoding="utf-8"))
    forged["review"] = {"record_sha256": review_record_sha256(
        capability=CAPABILITY, payload=forged["payload"],
        expected_snapshot=forged["expected_snapshot"],
        expected_revisions=forged["expected_revisions"])}
    forged["approval"]["subject_sha256"] = intent_sha256(forged)
    response = run_v2_capability(mini_repo, forged)
    assert response.returncode == 2, response.stdout + response.stderr
    assert json.loads(response.stdout)["error"]["code"] == "UNCONFIRMED"
    assert len(_receipts(mini_repo)) == receipts_after_competing
    assert _route_angle(mini_repo, rid) == "Competing angle"

    fresh_payload = {"unit_id": unit_id, "route_id": rid,
                     "changes": {"angle": "New reviewed angle"}}
    fresh_record = tmp_path / "fresh-review.json"
    reviewed_fresh = _check_out(mini_repo, fresh_record, fresh_payload,
                                "reviewed-route-002")
    assert reviewed_fresh.returncode == 0, reviewed_fresh.stderr
    applied = _seal(mini_repo, "--guards-from", str(fresh_record), "--submit")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(applied.stdout)["ok"] is True
    assert len(_receipts(mini_repo)) == receipts_after_competing + 1
    assert _route_angle(mini_repo, rid) == "New reviewed angle"

    replay = _seal(mini_repo, "--guards-from", str(fresh_record), "--submit")
    assert json.loads(replay.stdout)["replayed"] is True
    assert len(_receipts(mini_repo)) == receipts_after_competing + 1


def test_tampered_payload_with_a_fresh_intent_hash_still_refuses(
        mini_repo: Path, tmp_path: Path):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    payload = {"unit_id": unit_id, "route_id": rid,
               "changes": {"angle": "Reviewed angle"}}
    record = tmp_path / "review.json"
    reviewed = _check_out(mini_repo, record, payload, "reviewed-route-tamper")
    assert reviewed.returncode == 0, reviewed.stderr
    sealed_out = tmp_path / "sealed.json"
    sealed = _seal(mini_repo, "--guards-from", str(record),
                   "--out", str(sealed_out))
    assert sealed.returncode == 0, sealed.stderr
    envelope = json.loads(sealed_out.read_text(encoding="utf-8"))
    envelope["payload"]["changes"]["angle"] = "Tampered angle"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = run_v2_capability(mini_repo, envelope)
    body = json.loads(refused.stdout)
    assert refused.returncode != 0, refused.stdout
    assert body["ok"] is False
    assert body["error"]["code"] == "UNCONFIRMED", body
    assert _receipts(mini_repo) == []
    assert _route_angle(mini_repo, rid) != "Tampered angle"
