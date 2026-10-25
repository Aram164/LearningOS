"""V4 probe: full AI-action round trip through the real V2 gateway.

Builds the same fixture `tests/test_ai_actions.py` builds (mini_repo + real
contracts + one garden seed), then drives every step through the public
surfaces exactly as a user would:

  1. `los.py ai-action-list --json`            (read path)
  2. `los.py ai-action-prepare ... --json`     (manual path)
  3. hand-built stub provider delivery bundle  (the "provider response")
  4. `los.py ai-action-import-delivery`        (manual path)
  5. `los.py ai-action-validate-delivery`      (manual path)
  6. `los.py capability ai-action.delivery.apply --payload-file -`
     with an approved-delivery GatewayEnvelopeV2 on stdin (the real gateway)

Prints each step's exit code and the interesting output. No network, no model.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path("/Users/aramaljanadi/los-glm-V4-2026-10/repository")
LOS = REPO / "tools" / "los.py"
PY = REPO / ".venv" / "bin" / "python"
FIXED_STAMP = "2026-08-04T01:00:00+00:00"


def write_yaml(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")


def build_fixture(tmp: Path) -> Path:
    sys.path.insert(0, str(REPO / "tests"))
    from conftest import build_mini_repo
    from repo_builders import copy_real_contracts

    root = build_mini_repo(tmp)
    copy_real_contracts(REPO, root)
    for rel in ("operations/ai-actions/requests",
                "operations/ai-actions/deliveries",
                "operations/ai-actions/garden-state",
                "knowledge/garden"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "knowledge/garden/handwritten-import-registration.md").write_text(
        "# Import registration\n\nThe decorator stores the function during "
        "import. #python #optimizer\n", encoding="utf-8")
    write_yaml(root / "operations/ai-actions/relationships.yaml", {
        "schema_version": 1, "relationships": []})
    return root


def los(root: Path, *args: str, payload: dict | None = None):
    cmd = [str(PY), str(LOS), "--root", str(root), *args]
    return subprocess.run(
        cmd,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True, text=True, timeout=120,
    )


def snapshot(root: Path) -> str:
    sys.path.insert(0, str(REPO / "tools"))
    from learning_os.store.fingerprint import canonical_fingerprint
    return "sha256:" + canonical_fingerprint(root)


def artifact_revision(root: Path, artifact_id: str) -> int:
    sys.path.insert(0, str(REPO / "tools"))
    from learning_os.store.revisions import artifact_revision
    return artifact_revision(root, artifact_id)


def approved_apply_envelope(root: Path, delivery_id: str, directory: Path) -> dict:
    delivery = yaml.safe_load((directory / "delivery.yaml").read_text())
    request = yaml.safe_load(
        (root / "operations/ai-actions/requests" / delivery["request_id"]
         / "request.yaml").read_text())
    tid = request["target"]["id"]
    artifact_ids = {tid}
    artifact_hashes = {}
    for op in delivery["operations"]:
        ref = op.get("artifact_ref")
        if ref:
            artifact_hashes[ref] = "sha256:" + hashlib.sha256(
                (directory / ref).read_bytes()).hexdigest()
        if op["capability"] == "garden.add-transcription":
            artifact_ids.add(f"transcription-{tid}")
        elif op["capability"] == "relationship.create":
            artifact_ids.add(op["payload"]["id"])
        elif op["capability"] == "unit.material-synthesis.publish":
            record = yaml.safe_load((directory / ref).read_text())
            artifact_ids.add(record["id"])
    delivery_hash = "sha256:" + hashlib.sha256(
        (directory / "delivery.yaml").read_bytes()).hexdigest()
    envelope = {
        "schema_version": 2,
        "request_id": f"apply-{delivery_id}",
        "idempotency_key": f"apply-{delivery_id}",
        "capability": "ai-action.delivery.apply",
        "channel": "operator",
        "expected_snapshot": snapshot(root),
        "expected_revisions": {a: artifact_revision(root, a)
                               for a in sorted(artifact_ids)},
        "approval": {"kind": "approved-delivery",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": {"delivery_id": delivery_id,
                    "delivery_sha256": delivery_hash,
                    "artifact_sha256": artifact_hashes},
    }
    envelope["approval"]["subject_sha256"] = intent_hash(envelope)
    return envelope


def intent_hash(envelope: dict) -> str:
    sys.path.insert(0, str(REPO / "tools"))
    from learning_os.store.contracts.gateway import intent_sha256
    return intent_sha256(envelope)


def stub_delivery(root: Path, tmp: Path, request: dict, *,
                  delivery_id: str = "ai-delivery-probe-001",
                  target_id: str, operations=None) -> Path:
    source = tmp / f"provider-response-{delivery_id}"
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


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="v4-roundtrip-"))
    root = build_fixture(tmp)
    print("fixture:", root)

    # 1. read path
    r = los(root, "ai-action-list", "--json")
    print("\n[1] ai-action-list:", r.returncode)
    listing = json.loads(r.stdout)
    print("   actions:", [a["id"] for a in listing["actions"]])

    # 2. prepare via the real CLI
    r = los(root, "ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note",
            "--target-id", "garden-note-handwritten-import-registration",
            "--provider", "manual-bundle", "--json")
    print("\n[2] ai-action-prepare:", r.returncode)
    if r.returncode != 0:
        print("   stdout:", r.stdout[-500:])
        print("   stderr:", r.stderr[-500:])
        return
    request = json.loads(r.stdout)["request"]
    print("   request id:", request["id"], "status:", request["status"])
    print("   target:", request["target"])
    tid = request["target"]["id"]

    # 3. stub provider writes a delivery bundle OUTSIDE the repo (no network)
    full_request = yaml.safe_load(
        (root / request["bundle_path"] / "request.yaml").read_text())
    source = stub_delivery(root, tmp, full_request, target_id=tid)

    # 4. import via the real CLI
    r = los(root, "ai-action-import-delivery", str(source), "--json")
    print("\n[4] ai-action-import-delivery:", r.returncode)
    if r.returncode != 0:
        print("   stdout:", r.stdout[-800:])
        print("   stderr:", r.stderr[-800:])
        return
    print("   ", json.dumps(json.loads(r.stdout))[:300])

    # 5. validate via the real CLI
    r = los(root, "ai-action-validate-delivery", "ai-delivery-probe-001",
            "--json")
    print("\n[5] ai-action-validate-delivery:", r.returncode,
          r.stdout.strip()[:200])

    # 6. apply through the real gateway
    directory = root / "operations/ai-actions/deliveries/ai-delivery-probe-001"
    envelope = approved_apply_envelope(root, "ai-delivery-probe-001", directory)
    before = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "generated" not in p.parts
    }
    r = los(root, "capability", "ai-action.delivery.apply",
            "--payload-file", "-", payload=envelope)
    print("\n[6] gateway apply:", r.returncode)
    if r.returncode != 0:
        print("   stdout:", r.stdout[-800:])
        print("   stderr:", r.stderr[-800:])
        return
    receipt = json.loads(r.stdout)
    print("   status:", receipt.get("status"), "replayed:",
          receipt.get("replayed"))
    print("   receipt_path:", receipt.get("receipt_path"))
    print("   created:", receipt.get("metadata", {}).get("created_ids"))
    print("   updated:", receipt.get("metadata", {}).get("updated_ids"))

    after = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "generated" not in p.parts
    }
    print("\nfiles written by apply:")
    for line in sorted(after - before):
        print("   +", line)
    print("files removed:", sorted(before - after) or "none")
    seed = (root / "knowledge/garden/handwritten-import-registration.md"
            ).read_text()
    print("original seed unchanged:", "during import" in seed or
          seed.startswith("# Import registration"))
    print("\ntmp:", tmp)


if __name__ == "__main__":
    main()
