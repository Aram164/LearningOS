"""V4 probe: the seven campaign cases against the real V2 gateway.

Run: venv-python probes/probe_cases.py [case numbers...]
Each case prints PASS-EXPECTED / REFUSED / observation lines and a verdict.
Everything through the public surfaces: CLI verbs + `capability` subprocess.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_roundtrip import (  # noqa: E402
    FIXED_STAMP, LOS, PY, REPO, approved_apply_envelope, build_fixture,
    intent_hash, los, snapshot, stub_delivery, write_yaml,
)


def file_tree(root: Path, skip_generated: bool = True) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(root).as_posix()
        if skip_generated and rel.startswith("generated/"):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def diff_trees(before: dict, after: dict) -> tuple[list, list]:
    added = sorted(set(after) - set(before))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    return added, changed


def prepare(root: Path, *, provider: str = "manual-bundle",
            request_id: str | None = None, expect_ok: bool = True) -> dict:
    args = ["ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note",
            "--target-id", "garden-note-handwritten-import-registration",
            "--provider", provider, "--json"]
    if request_id:
        args += ["--request-id", request_id]
    r = los(root, *args)
    body = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    ok = r.returncode == 0
    assert ok == expect_ok, f"prepare returncode={r.returncode} stderr={r.stderr[-300:]}"
    return body.get("request", {})


def full_request(root: Path, request: dict) -> dict:
    return yaml.safe_load(
        (root / request["bundle_path"] / "request.yaml").read_text())


def import_and_validate(root: Path, source: Path, delivery_id: str,
                        expect_ok: bool = True):
    r = los(root, "ai-action-import-delivery", str(source), "--json")
    ok = r.returncode == 0
    assert ok == expect_ok, (
        f"import returncode={r.returncode} stdout={r.stdout[-400:]} stderr={r.stderr[-400:]}")
    if not ok:
        return json.loads(r.stderr)
    r2 = los(root, "ai-action-validate-delivery", delivery_id, "--json")
    assert r2.returncode == 0, r2.stderr[-400:]
    return json.loads(r.stdout)


def build_apply_envelope(root: Path, delivery_id: str, *,
                         idempotency_key: str | None = None,
                         fresh_snapshot: bool = False,
                         extra_payload: dict | None = None) -> dict:
    directory = root / "operations/ai-actions/deliveries" / delivery_id
    envelope = approved_apply_envelope(root, delivery_id, directory)
    if fresh_snapshot:
        # mint the approval AFTER any mutation, exactly as a fresh user
        # gesture would; gateway_helpers computes both from the live tree.
        sys.path.insert(0, str(REPO / "tools"))
        from learning_os.store.revisions import artifact_revision
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
                record = yaml.safe_load(
                    (directory / op["artifact_ref"]).read_text())
                ids.add(record["id"])
        envelope["expected_revisions"] = {
            a: artifact_revision(root, a) for a in sorted(ids)}
        envelope["expected_snapshot"] = snapshot(root)
        envelope["approval"]["subject_sha256"] = intent_hash(envelope)
    if idempotency_key:
        envelope["idempotency_key"] = idempotency_key
        envelope["request_id"] = f"apply-{idempotency_key}"
        envelope["approval"]["subject_sha256"] = intent_hash(envelope)
    payload = dict(envelope["payload"])
    if extra_payload:
        payload.update(extra_payload)
    envelope["payload"] = payload
    envelope["approval"]["subject_sha256"] = intent_hash(envelope)
    return envelope


def apply_env(root: Path, envelope: dict, *, expect_ok: bool = True):
    r = los(root, "capability", "ai-action.delivery.apply",
            "--payload-file", "-", payload=envelope)
    ok = r.returncode == 0
    assert ok == expect_ok, (
        f"apply returncode={r.returncode} stdout={r.stdout[-400:]} stderr={r.stderr[-500:]}")
    if not ok:
        # the capability command reports refusals as ok:false JSON on STDOUT
        for stream in (r.stdout, r.stderr):
            try:
                body = json.loads(stream)
                if isinstance(body, dict) and body.get("ok") is False:
                    return body
            except Exception:
                pass
        return {"raw_stderr": r.stderr[-500:], "raw_stdout": r.stdout[-500:]}
    return json.loads(r.stdout)


def apply_delivery(root: Path, delivery_id: str, *,
                   idempotency_key: str | None = None,
                   fresh_snapshot: bool = False,
                   extra_payload: dict | None = None,
                   expect_ok: bool = True):
    envelope = build_apply_envelope(
        root, delivery_id, idempotency_key=idempotency_key,
        fresh_snapshot=fresh_snapshot, extra_payload=extra_payload)
    return apply_env(root, envelope, expect_ok=expect_ok)
    ok = r.returncode == 0
    assert ok == expect_ok, (
        f"apply returncode={r.returncode} stdout={r.stdout[-400:]} stderr={r.stderr[-500:]}")
    if not ok:
        # the capability command reports refusals as ok:false JSON on STDOUT
        for stream in (r.stdout, r.stderr):
            try:
                body = json.loads(stream)
                if isinstance(body, dict) and body.get("ok") is False:
                    return body
            except Exception:
                pass
        return {"raw_stderr": r.stderr[-500:], "raw_stdout": r.stdout[-500:]}
    return json.loads(r.stdout)


def receipts(root: Path) -> list[str]:
    tx = root / "operations/transactions"
    return sorted(p.name for p in tx.glob("transaction-*.yaml")) if tx.is_dir() else []


def _v2_error_message(r) -> str:
    """Extract error.message from a V2 response on stdout or stderr."""
    for stream in (r.stdout, r.stderr):
        try:
            b = json.loads(stream)
            if isinstance(b, dict) and b.get("ok") is False:
                return str(b.get("error", {}).get("message", ""))
        except Exception:
            pass
    return (r.stderr or r.stdout)[-170:]


# --------------------------------------------------------------------- cases

def case_1(tmp: Path) -> None:
    print("\n=== CASE 1: exact-target binding ===")
    # 1a: target edited after prepare, before import.
    root = build_fixture(tmp / "c1a")
    req = prepare(root)
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c1a")
    note = root / "knowledge/garden/handwritten-import-registration.md"
    note.write_text(note.read_text() + "\nChanged after preparation.\n")
    err = import_and_validate(root, source, "ai-delivery-c1a", expect_ok=False)
    print("1a import-after-target-change refused:", err.get("error", {}).get("message", err)[:160])

    # 1b: target edited after import; apply minted with a FRESH snapshot and
    # fresh revisions (the attacker re-approves after the change).
    root = build_fixture(tmp / "c1b")
    req = prepare(root)
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c1b")
    import_and_validate(root, source, "ai-delivery-c1b")
    note = root / "knowledge/garden/handwritten-import-registration.md"
    note.write_text(note.read_text() + "\nChanged after import.\n")
    before = file_tree(root)
    err = apply_delivery(root, "ai-delivery-c1b", fresh_snapshot=True,
                         expect_ok=False)
    added, changed = diff_trees(before, file_tree(root))
    msg = err.get("error", {}).get("message", str(err))
    print("1b apply-after-target-change refused:", msg[:200])
    non_bookkeeping = [p for p in added + changed
                       if not p.startswith(("operations/", "generated/"))]
    print("1b nothing canonical written:", not non_bookkeeping,
          "canonical-side effects:", non_bookkeeping)

    # 1c: the documented --expected-snapshot guard on prepare refuses a
    # stale token (AI-ACTIONS.md's manual-bundle workflow names the flag).
    root = build_fixture(tmp / "c1c")
    stale = "sha256:" + "0" * 64
    r = los(root, "ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note",
            "--target-id", "garden-note-handwritten-import-registration",
            "--provider", "manual-bundle",
            "--expected-snapshot", stale, "--json")
    print("1c prepare with stale expected-snapshot refused:",
          r.returncode != 0,
          json.loads(r.stderr).get("error", {}).get("message", "")[:140])

    # 1d: an operation whose target_id names a different note than the
    # request target is refused at import.
    root = build_fixture(tmp / "c1d")
    req = prepare(root, request_id="ai-request-c1d")
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c1d",
                           operations=[{
                               "capability": "garden.add-transcription",
                               "target_id": "garden-note-some-other-seed",
                               "artifact_ref": "artifacts/transcription.md",
                           }])
    err = import_and_validate(root, source, "ai-delivery-c1d", expect_ok=False)
    print("1d operation target_id mismatch refused:",
          err.get("error", {}).get("message", str(err))[:170])


def case_2(tmp: Path) -> None:
    print("\n=== CASE 2: partial approval ===")
    # 2a: a payload field selecting a subset of operations must be refused.
    root = build_fixture(tmp / "c2a")
    req = prepare(root)
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c2a")
    import_and_validate(root, source, "ai-delivery-c2a")
    err = apply_delivery(root, "ai-delivery-c2a",
                         extra_payload={"selected_operations": [0]},
                         expect_ok=False)
    msg = err.get("error", {}).get("message", str(err))
    print("2a subset-selection payload refused:", msg[:220])

    # 2b: an approved 3-operation delivery applies ALL of it (whole-delivery
    # approval), and the receipt records every destination.
    root = build_fixture(tmp / "c2b")
    req = prepare(root)
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c2b")
    import_and_validate(root, source, "ai-delivery-c2b")
    out = apply_delivery(root, "ai-delivery-c2b")
    receipt = yaml.safe_load((root / out["receipt_path"]).read_text())
    paths = {w["path"] for w in receipt["writes"]}
    state_yaml = f"operations/ai-actions/garden-state/{tid}.yaml"
    needed = {
        f"knowledge/garden/transcriptions/{tid}.md",
        state_yaml,
        "operations/ai-actions/relationships.yaml",
    }
    print("2b all three destinations written:", needed <= paths,
          "missing:", needed - paths)
    state = yaml.safe_load((root / state_yaml).read_text())
    print("2b garden.update applied:", state.get("title") == "Import-Time Registration")
    rel = yaml.safe_load((root / "operations/ai-actions/relationships.yaml").read_text())
    print("2b relationship applied:", len(rel["relationships"]) == 1)
    print("2b request completed:", yaml.safe_load(
        (root / req["bundle_path"] / "request.yaml").read_text())["status"])


def case_3(tmp: Path) -> None:
    print("\n=== CASE 3: receipts ===")
    root = build_fixture(tmp / "c3")
    req = prepare(root)
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c3")
    import_and_validate(root, source, "ai-delivery-c3")
    envelope = build_apply_envelope(root, "ai-delivery-c3")
    out = apply_env(root, envelope)
    one = receipts(root)
    print("3a exactly one receipt after first apply:", len(one) == 1, one)

    # replay: the EXACT first envelope bytes → replayed, still one receipt.
    before = file_tree(root)
    out2 = apply_env(root, envelope)
    added, changed = diff_trees(before, file_tree(root))
    print("3a replay replayed:", out2.get("replayed") is True,
          "same receipt:", out2.get("receipt_path") == out["receipt_path"])
    print("3a replay wrote nothing canonical:",
          not [p for p in added + changed
               if not p.startswith(("operations/", "generated/"))])
    print("3a still exactly one receipt:", receipts(root) == one)

    # 3b: receipt matches what was applied (bytes on disk). ReceiptV2 stores
    # bare hex digests in writes[].sha256_after.
    receipt = yaml.safe_load((root / out["receipt_path"]).read_text())
    mismatches = []
    for w in receipt["writes"]:
        p = root / w["path"]
        if not p.is_file():
            mismatches.append(w["path"]); continue
        if w.get("sha256_after"):
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if w["sha256_after"] not in (digest, "sha256:" + digest):
                mismatches.append(w["path"])
    print("3b receipt writes match disk bytes:", not mismatches, mismatches)
    live = "sha256:" + source_fingerprint_by_load(root)
    print("3b snapshot_after == live projection fingerprint:",
          receipt["snapshot_after"] == live)

    # 3e: the deterministic manifest projection was regenerated by the
    # gateway apply (invariant 12: validation and regeneration).
    manifest = json.loads((root / "generated/manifest.json").read_text())
    ai_rows = manifest.get("ai_actions", {}).get("requests", [])
    print("3e manifest carries the completed request:",
          any(row.get("id") == req["id"] and row.get("status") == "completed"
              for row in ai_rows))

    # 3c: a second application under a NEW idempotency key with a fresh
    # snapshot must still be refused; no second receipt may appear.
    err = apply_delivery(root, "ai-delivery-c3", fresh_snapshot=True,
                         idempotency_key="apply-c3-second-key",
                         expect_ok=False)
    msg = err.get("error", {}).get("message", str(err))
    print("3c re-apply under new key refused:", msg[:180])
    print("3c still exactly one receipt:", receipts(root) == one)

    # 3d observation: does the same delivery re-apply under a new key when it
    # carries no transcription (so the transcription guard cannot catch it)?
    root = build_fixture(tmp / "c3d")
    req = prepare(root, request_id="ai-request-c3d")
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c3d",
                           operations=[{"capability": "garden.update",
                                        "target_id": tid,
                                        "patch": {"title": "Once", "state": "developing"}}])
    import_and_validate(root, source, "ai-delivery-c3d")
    first = apply_env(root, build_apply_envelope(root, "ai-delivery-c3d"))
    first_receipts = receipts(root)
    state_path = root / f"operations/ai-actions/garden-state/{tid}.yaml"
    rev_after_first = yaml.safe_load(state_path.read_text()).get("revision")
    second = apply_delivery(root, "ai-delivery-c3d", fresh_snapshot=True,
                            idempotency_key="apply-c3d-second")
    state = yaml.safe_load(state_path.read_text())
    request_now = yaml.safe_load(
        (root / req["bundle_path"] / "request.yaml").read_text())
    print("3d update-only re-apply under new key: accepted =",
          second.get("ok") is True,
          "| replayed =", second.get("replayed"))
    print("3d receipts:", len(receipts(root)), "(first round:",
          len(first_receipts), ")",
          "| state revision:", rev_after_first, "->", state.get("revision"))
    print("3d request receipt_id moved:",
          request_now.get("receipt_id") == second["transaction_id"],
          "| distinct transaction ids:",
          first["transaction_id"] != second["transaction_id"])


def source_fingerprint_by_load(root: Path) -> str:
    from learning_os.store.loader import load_repo
    from learning_os.store.fingerprint import source_fingerprint
    return source_fingerprint(load_repo(root))


def case_4(tmp: Path) -> None:
    print("\n=== CASE 4: replay / foreign request ids ===")
    root = build_fixture(tmp / "c4a")
    req = prepare(root, request_id="ai-request-c4-001")
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c4a")
    import_and_validate(root, source, "ai-delivery-c4a")
    # 4a exact replay via gateway with the EXACT first envelope bytes.
    envelope = build_apply_envelope(root, "ai-delivery-c4a")
    out = apply_env(root, envelope)
    before = file_tree(root)
    out2 = apply_env(root, envelope)
    added, changed = diff_trees(before, file_tree(root))
    print("4a replayed flag:", out2.get("replayed") is True,
          "same transaction:", out2.get("transaction_id") == out.get("transaction_id"),
          "no writes:", not added and not changed,
          [p for p in added + changed
           if not p.startswith(("operations/", "generated/"))])

    # 4b: delivery naming an unknown request id.
    root = build_fixture(tmp / "c4b")
    req = prepare(root, request_id="ai-request-c4-001")
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c4b")
    body = yaml.safe_load((source / "delivery.yaml").read_text())
    body["request_id"] = "ai-request-does-not-exist"
    write_yaml(source / "delivery.yaml", body)
    err = import_and_validate(root, source, "ai-delivery-c4b", expect_ok=False)
    print("4b unknown request id refused:",
          err.get("error", {}).get("message", str(err))[:160])

    # 4c: delivery naming ANOTHER existing request's id while carrying the
    # first request's preconditions. Request 2 is prepared only AFTER the
    # target changed, so its preconditions genuinely differ from the bundle's.
    root = build_fixture(tmp / "c4c")
    req1 = prepare(root, request_id="ai-request-c4-r1")
    full1 = full_request(root, req1)
    note = root / "knowledge/garden/handwritten-import-registration.md"
    note.write_text(note.read_text() + "\nChanged before request 2.\n")
    req2 = prepare(root, request_id="ai-request-c4-r2")
    assert full_request(root, req2)["preconditions"] != full1["preconditions"], \
        "fixture broken: the two requests must carry different preconditions"
    source = stub_delivery(root, tmp, full1, target_id=req1["target"]["id"],
                           delivery_id="ai-delivery-c4c")
    body = yaml.safe_load((source / "delivery.yaml").read_text())
    body["request_id"] = "ai-request-c4-r2"
    write_yaml(source / "delivery.yaml", body)
    err = import_and_validate(root, source, "ai-delivery-c4c", expect_ok=False)
    print("4c foreign request id with wrong preconditions refused:",
          err.get("error", {}).get("message", str(err))[:200])


def case_5(tmp: Path) -> None:
    print("\n=== CASE 5: relation proposals, one path ===")
    # 5a: only concept.relations.change may write the concept relation registry.
    c = yaml.safe_load((REPO / "system/contracts/capabilities.yaml").read_text())
    writers = []
    for kind in ("domain_capabilities", "commands"):
        for name, d in c[kind].items():
            for scope in d.get("writes", []) or []:
                if "concept-relations" in scope:
                    writers.append(f"{kind}:{name}")
    print("5a declared writers of concept-relations.yaml:", writers)

    # 5b: a delivery operation naming concept.relations.change is refused.
    root = build_fixture(tmp / "c5b")
    req = prepare(root, request_id="ai-request-c5-001")
    full = full_request(root, req)
    tid = req["target"]["id"]
    ops = [{
        "capability": "concept.relations.change",
        "target_id": tid,
        "payload": {"change": {"operations": [
            {"action": "add", "new": {"from": "concept-variance",
                                      "type": "builds-on",
                                      "to": "concept-expected-value"}}]}},
    }]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c5b", operations=ops)
    err = import_and_validate(root, source, "ai-delivery-c5b", expect_ok=False)
    print("5b AI delivery cannot carry concept.relations.change:",
          err.get("error", {}).get("message", str(err))[:200])

    # 5c: the manual path with no AI involved works through operator
    # approval (ADR-017 decision 3). The mini repo already ships the edge
    # variance --builds-on--> expected-value, so add a distinct one.
    cr_root = build_fixture(tmp / "c5c")
    relations_before = (cr_root / "knowledge/concept-relations.yaml").read_bytes()
    ops_payload = {"change": {"operations": [
        {"action": "add",
         "new": {"from": "concept-expected-value", "type": "motivates",
                 "to": "concept-variance"}}]}}
    sys.path.insert(0, str(REPO / "tools"))
    from learning_os.store.revisions import artifact_revision
    env = {
        "schema_version": 2,
        "request_id": "request-c5-manual",
        "idempotency_key": "c5-manual",
        "capability": "concept.relations.change",
        "channel": "operator",
        "expected_snapshot": snapshot(cr_root),
        "expected_revisions": {
            "registry-concept-relations":
                artifact_revision(cr_root, "registry-concept-relations")},
        "approval": {"kind": "operator-approval",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": ops_payload,
    }
    env["approval"]["subject_sha256"] = intent_hash(env)
    r = los(cr_root, "capability", "concept.relations.change",
            "--payload-file", "-", payload=env)
    refused_msg = _v2_error_message(r)
    print("5c operator-approval manual edit accepted:", r.returncode == 0,
          refused_msg[:170])
    relations_after = (cr_root / "knowledge/concept-relations.yaml").read_bytes()
    print("5c manual path added the relation:",
          r.returncode == 0 and relations_before != relations_after)

    # 5e: a direct-user-gesture approval claiming concept.relations.change
    # must fail closed from a non-UI channel.
    env3 = dict(env)
    env3["approval"] = {"kind": "direct-user-gesture",
                        "subject_sha256": "sha256:" + "0" * 64}
    env3["idempotency_key"] = "c5-gesture"
    env3["request_id"] = "request-c5-gesture"
    env3["approval"]["subject_sha256"] = intent_hash(env3)
    r = los(cr_root, "capability", "concept.relations.change",
            "--payload-file", "-", payload=env3)
    print("5e gesture-kind claim of the relation editor refused:",
          r.returncode != 0, _v2_error_message(r)[:170])

    # 5d: a full approved garden delivery leaves the concept registry
    # byte-identical (the AI registry is a different record family).
    root = build_fixture(tmp / "c5d")
    req = prepare(root, request_id="ai-request-c5d")
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c5d")
    import_and_validate(root, source, "ai-delivery-c5d")
    before = (root / "knowledge/concept-relations.yaml").read_bytes()
    apply_delivery(root, "ai-delivery-c5d")
    after = (root / "knowledge/concept-relations.yaml").read_bytes()
    print("5d concept-relations.yaml byte-identical after AI apply:",
          before == after)


def case_6(tmp: Path) -> None:
    print("\n=== CASE 6: no provider configured ===")
    # 6a: an unavailable provider is refused at prepare, from the CLI.
    root = build_fixture(tmp / "c6a")
    r = los(root, "ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note",
            "--target-id", "garden-note-handwritten-import-registration",
            "--provider", "claude", "--json")
    print("6a prepare(claude) refused:", r.returncode != 0,
          json.loads(r.stderr).get("error", {}).get("message", "")[:160])

    # 6b: with NO adapter available at all, the non-AI manual authoring path
    # still works (ADR-017 decision 3), and reads still work.
    root = build_fixture(tmp / "c6b")
    adapters_path = root / "system/contracts/ai-adapters.yaml"
    adapters = yaml.safe_load(adapters_path.read_text())
    for row in adapters["adapters"]:
        row["available"] = False
    write_yaml(adapters_path, adapters)
    r = los(root, "ai-action-list", "--json")
    print("6b ai-action-list works with zero adapters:", r.returncode == 0)
    r = los(root, "ai-action-prepare", "--action-id", "garden.shelve",
            "--target-kind", "garden-note",
            "--target-id", "garden-note-handwritten-import-registration",
            "--provider", "manual-bundle", "--json")
    print("6b prepare(manual-bundle) refused, typed:",
          r.returncode != 0,
          json.loads(r.stderr).get("error", {}).get("message", "")[:140])
    ops_payload = {"change": {"operations": [
        {"action": "add", "new": {"from": "concept-expected-value",
                                  "type": "motivates",
                                  "to": "concept-variance"}}]}}
    sys.path.insert(0, str(REPO / "tools"))
    from learning_os.store.revisions import artifact_revision
    env = {
        "schema_version": 2,
        "request_id": "request-c6-manual",
        "idempotency_key": "c6-manual",
        "capability": "concept.relations.change",
        "channel": "ui",
        "expected_snapshot": snapshot(root),
        "expected_revisions": {
            "registry-concept-relations":
                artifact_revision(root, "registry-concept-relations")},
        "approval": {"kind": "operator-approval",
                     "subject_sha256": "sha256:" + "0" * 64},
        "payload": ops_payload,
    }
    env["approval"]["subject_sha256"] = intent_hash(env)
    r = los(root, "capability", "concept.relations.change",
            "--payload-file", "-", payload=env)
    print("6b manual concept authoring works with zero adapters:",
          r.returncode == 0, r.stderr[-200:] if r.returncode else "")

    # 6c: the AI manual-bundle path with the OTHER providers unavailable
    # (the pin's default state) still completes a full round trip.
    root = build_fixture(tmp / "c6c")
    req = prepare(root, request_id="ai-request-c6-001")
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c6c")
    import_and_validate(root, source, "ai-delivery-c6c")
    out = apply_delivery(root, "ai-delivery-c6c")
    print("6c manual-bundle round trip works:", out.get("ok") is True)


def case_7(tmp: Path) -> None:
    print("\n=== CASE 7: provider response never writes canonical directly ===")
    # 7a: symlink inside the bundle → refuse.
    root = build_fixture(tmp / "c7a")
    req = prepare(root, request_id="ai-request-c7a")
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c7a")
    (source / "artifacts/link.md").symlink_to(source / "artifacts/transcription.md")
    before = file_tree(root)
    err = import_and_validate(root, source, "ai-delivery-c7a", expect_ok=False)
    added, _ = diff_trees(before, file_tree(root))
    print("7a symlink bundle refused:",
          err.get("error", {}).get("message", str(err))[:140])
    print("7a quarantine-only side effects:",
          all(a.startswith("operations/ai-actions/") for a in added), added)

    # 7b: path traversal in artifact_ref → refuse.
    root = build_fixture(tmp / "c7b")
    req = prepare(root, request_id="ai-request-c7b")
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c7b",
                           operations=[{
                               "capability": "garden.add-transcription",
                               "target_id": tid,
                               "artifact_ref": "artifacts/../../seed-escape.md",
                           }])
    seed = root / "knowledge/garden/handwritten-import-registration.md"
    before_seed = seed.read_bytes()
    err = import_and_validate(root, source, "ai-delivery-c7b", expect_ok=False)
    print("7b traversal artifact_ref refused:",
          err.get("error", {}).get("message", str(err))[:200])
    print("7b seed untouched:", seed.read_bytes() == before_seed)

    # 7c: a rejected import never lands in deliveries/ (nothing canonical).
    d = root / "operations/ai-actions/deliveries"
    print("7c deliveries/ empty after rejection:",
          not any(d.glob('*')) if d.is_dir() else True)

    # 7d: an operation naming a canonical write capability outside the
    # request allowlist → refuse.
    root = build_fixture(tmp / "c7d")
    req = prepare(root, request_id="ai-request-c7d")
    full = full_request(root, req)
    source = stub_delivery(root, tmp, full,
                           target_id=req["target"]["id"],
                           delivery_id="ai-delivery-c7d",
                           operations=[{"capability": "note.create",
                                        "payload": {"id": "note-evil"}}])
    err = import_and_validate(root, source, "ai-delivery-c7d", expect_ok=False)
    print("7d canonical-writer operation refused:",
          err.get("error", {}).get("message", str(err))[:160])

    # 7e: artifact bytes tampered after import, before apply → the hash
    # binding refuses and nothing is written.
    root = build_fixture(tmp / "c7e")
    req = prepare(root, request_id="ai-request-c7e")
    full = full_request(root, req)
    tid = req["target"]["id"]
    source = stub_delivery(root, tmp, full, target_id=tid,
                           delivery_id="ai-delivery-c7e")
    import_and_validate(root, source, "ai-delivery-c7e")
    # The operator approves the imported bytes FIRST; the artifact is then
    # tampered with before the apply reaches the gateway.
    envelope = build_apply_envelope(root, "ai-delivery-c7e")
    artifact = root / "operations/ai-actions/deliveries/ai-delivery-c7e/artifacts/transcription.md"
    artifact.write_text("TAMPERED after approval.\n", encoding="utf-8")
    before = file_tree(root)
    err = apply_env(root, envelope, expect_ok=False)
    added, changed = diff_trees(before, file_tree(root))
    msg = err.get("error", {}).get("message", str(err))
    print("7e tampered artifact refused at apply:", msg[:160])
    non_bookkeeping = [p for p in added + changed
                       if not p.startswith(("operations/", "generated/"))]
    print("7e nothing canonical written:", not non_bookkeeping,
          non_bookkeeping)


def case_8(tmp: Path) -> None:
    """Second registered action: unit.compare-materials end to end."""
    print("\n=== CASE 8 (scope): unit.compare-materials round trip ===")
    sys.path.insert(0, str(REPO / "tests"))
    from repo_builders import _sliced_route, _sliced_unit
    from learning_os.derive.material_synthesis import current_unit_material_basis

    root = build_fixture(tmp / "c8")
    _sliced_unit(root, [_sliced_route("route-demo-l01",
                                      "lecture-01.pdf, PDF p. 1")])
    r = los(root, "ai-action-prepare", "--action-id", "unit.compare-materials",
            "--target-kind", "unit", "--target-id", "unit-demo-l01",
            "--provider", "manual-bundle", "--request-id",
            "ai-request-unit-001", "--json")
    assert r.returncode == 0, r.stderr[-300:]
    request = json.loads(r.stdout)["request"]
    full = yaml.safe_load(
        (root / request["bundle_path"] / "request.yaml").read_text())

    # the stub provider returns one whole synthesis record naming the
    # provenance the request assigned it
    basis = current_unit_material_basis(root, "unit-demo-l01")
    basis = {**basis, "ai_provenance": {
        "request_id": full["id"],
        "delivery_id": "ai-delivery-unit-001",
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
            "evidence": [{"locator": "lecture-01.pdf p.1", "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [
            {"concept_id": "concept-variance",
             "local_node_ids": ["knowledge-demo-outcomes"],
             "related_unit_ids": [],
             "bridge_note_ids": [],
             "narrative": "Outcomes feed later dispersion measures."},
            {"concept_id": "concept-expected-value",
             "local_node_ids": ["knowledge-demo-expectation"],
             "related_unit_ids": ["unit-demo-l01"],
             "bridge_note_ids": ["note-demo"],
             "narrative": "The local derivation is the canonical concept."},
        ],
    }
    source = tmp / f"provider-response-ai-delivery-unit-001"
    (source / "artifacts").mkdir(parents=True, exist_ok=True)
    (source / "artifacts/synthesis.yaml").write_text(
        yaml.safe_dump(synthesis, sort_keys=False), encoding="utf-8")
    write_yaml(source / "delivery.yaml", {
        "schema_version": 1,
        "id": "ai-delivery-unit-001",
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
    import_and_validate(root, source, "ai-delivery-unit-001")
    envelope = build_apply_envelope(root, "ai-delivery-unit-001")
    before = file_tree(root)
    out = apply_env(root, envelope)
    added, changed = diff_trees(before, file_tree(root))
    print("8 apply accepted:", out.get("ok") is True,
          "| receipt:", out.get("receipt_path"))
    dossier = root / ("curriculum/modules/module-demo/units/unit-demo-l01/"
                      "material-synthesis.yaml")
    print("8 dossier landed:", dossier.is_file(),
          "| canonical additions:",
          [p for p in added if not p.startswith(("operations/", "generated/"))])
    manifest = json.loads((root / "generated/manifest.json").read_text())
    print("8 manifest carries the request:",
          any(row.get("id") == full["id"]
              for row in manifest.get("ai_actions", {}).get("requests", [])))

    # 8b: replay of the same envelope
    out2 = apply_env(root, envelope)
    print("8b replay replayed:", out2.get("replayed") is True)


def main() -> None:
    wanted = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5, 6, 7]
    tmp = Path(tempfile.mkdtemp(prefix="v4-cases-"))
    cases = {1: case_1, 2: case_2, 3: case_3, 4: case_4,
             5: case_5, 6: case_6, 7: case_7, 8: case_8}
    for n in wanted:
        try:
            cases[n](tmp)
        except AssertionError as exc:
            print(f"!! case {n} PROBE ASSERTION FAILED: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"!! case {n} raised {type(exc).__name__}: {exc}")
    print("\ntmp:", tmp)


if __name__ == "__main__":
    main()
