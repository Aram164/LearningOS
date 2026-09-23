"""Governed source intake: shelve metadata-only sources, correct intake fields.

`source.intake.record` is the one standalone registry writer outside plan and
migration transactions. Check runs report the field-level diff; applies bind
to the diff hash, the snapshot and each record's revision.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call, approved_v2_cli
from repo_builders import run_los, write_yaml


def _discovery(**changes):
    value = {
        "observed": "2026-09-23",
        "basis": [{"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"}],
        "possible_use": "Possibly a lecture spine for intro supervised learning.",
    }
    value.update(changes)
    return value


def _package(tmp_path: Path, records: list) -> Path:
    path = tmp_path / "intake.yaml"
    write_yaml(path, {"records": records})
    return path


def _create(sid="source-new-course", **changes):
    value = {
        "action": "create",
        "id": sid,
        "partition": "sources.yaml",
        "title": "New Course",
        "type": "course",
        "discovery": _discovery(),
    }
    value.update(changes)
    return value


def _check(root: Path, package: Path):
    proc = run_los(root, "source-intake", "--file", str(package), "--check")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


def _refuses(root: Path, package: Path, fragment: str):
    proc = run_los(root, "source-intake", "--file", str(package), "--check")
    assert proc.returncode == 2, proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is False
    assert fragment in body["error"], body["error"]


def _thematic_groups(root: Path):
    write_yaml(root / "curriculum" / "thematic-groups.yaml", {
        "thematic_groups": [
            {"id": "thematic-group-machine-learning", "title": "ML",
             "description": "ml", "order": 30},
            {"id": "thematic-group-mathematics", "title": "Math",
             "description": "math", "order": 10},
        ]
    })


# --------------------------------------------------------------------- check
def test_check_create_reports_diff_and_writes_nothing(mini_repo, tmp_path):
    target = mini_repo / "sources" / "sources.yaml"
    before = target.read_bytes()
    body = _check(mini_repo, _package(tmp_path, [_create()]))
    assert body["check"] is True
    assert body["diff_sha256"].startswith("sha256:")
    assert body["artifact_ids"] == ["source-new-course"]
    assert body["expected_revisions"] == {"source-new-course": 0}
    (row,) = body["diff"]
    assert (row["id"], row["action"]) == ("source-new-course", "create")
    assert set(row["fields"]) == {"title", "type", "discovery"}
    assert target.read_bytes() == before


def test_create_needs_discovery(mini_repo, tmp_path):
    record = _create()
    del record["discovery"]
    _refuses(mini_repo, _package(tmp_path, [record]), "needs 'discovery'")


def test_create_rejects_an_existing_id(mini_repo, tmp_path):
    _refuses(mini_repo, _package(tmp_path, [_create("source-demo-book")]),
             "already registered")


def test_create_rejects_a_candidate_id(mini_repo, tmp_path):
    _refuses(mini_repo, _package(tmp_path, [_create("candidate-source-demo")]),
             "never registered as active")


def test_correct_rejects_an_unknown_id(mini_repo, tmp_path):
    _refuses(mini_repo, _package(tmp_path, [
        {"action": "correct", "id": "source-ghost", "title": "Ghost"}]),
        "unknown id")


def test_correct_refuses_create_only_and_foreign_fields(mini_repo, tmp_path):
    _refuses(mini_repo, _package(tmp_path, [
        {"action": "correct", "id": "source-demo-book", "type": "video"}]),
        "'type' is create-only")
    _refuses(mini_repo, _package(tmp_path, [
        {"action": "correct", "id": "source-demo-book",
         "evaluations": [{"roles": ["review"]}]}]),
        "outside the intake allowlist")


def test_batch_bound_and_double_naming(mini_repo, tmp_path):
    many = [_create(f"source-batch-{n:02d}") for n in range(21)]
    _refuses(mini_repo, _package(tmp_path, many), "exceeds the 20-record bound")
    _refuses(mini_repo, _package(tmp_path, [_create(), _create()]),
             "named twice in one batch")


def test_duplicate_address_names_its_holder(mini_repo, tmp_path):
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["url"] = "https://example.org/held/"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _refuses(mini_repo, _package(tmp_path, [_create(url="https://example.org/held/")]),
             "already held by 'source-demo-book'")


def test_unregistered_thematic_group_is_refused(mini_repo, tmp_path):
    _refuses(mini_repo, _package(tmp_path, [_create(
        partition="machine-learning.yaml",
        thematic_group_ids=["thematic-group-machine-learning"])]),
        "not registered")


def test_partition_must_match_the_groups(mini_repo, tmp_path):
    _thematic_groups(mini_repo)
    _refuses(mini_repo, _package(tmp_path, [_create(
        partition="mathematics.yaml",
        thematic_group_ids=["thematic-group-machine-learning"])]),
        "does not match its groups")
    _refuses(mini_repo, _package(tmp_path, [_create(
        partition="stage2b-unsorted-intake.yaml")]),
        "must be 'sources.yaml' or a subject partition")


def test_thematic_correction_needs_a_new_basis_item(mini_repo, tmp_path):
    _thematic_groups(mini_repo)
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["discovery"] = _discovery()
    data["sources"][0]["thematic_group_ids"] = ["thematic-group-mathematics"]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _refuses(mini_repo, _package(tmp_path, [{
        "action": "correct", "id": "source-demo-book",
        "thematic_group_ids": ["thematic-group-machine-learning"]}]),
        "needs a new discovery basis item")
    body = _check(mini_repo, _package(tmp_path, [{
        "action": "correct", "id": "source-demo-book",
        "thematic_group_ids": ["thematic-group-machine-learning"],
        "discovery": _discovery(basis=[
            {"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"},
            {"kind": "landing-page", "ref": "https://example.org/demo/"},
        ])}]))
    assert body["diff"][0]["fields"]["thematic_group_ids"]["after"] == [
        "thematic-group-machine-learning"]


def test_removal_refused_while_cited(mini_repo, tmp_path):
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["url"] = "https://example.org/cited/"
    data["sources"][0]["identifiers"] = {"mirror": "https://example.org/cited/"}
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nSee https://example.org/cited/.\n",
                    encoding="utf-8")
    _refuses(mini_repo, _package(tmp_path, [{
        "action": "correct", "id": "source-demo-book", "remove_url": True}]),
        "still cited by knowledge/notes/mathematics/note-demo.md")


def test_removal_keeps_a_locator_and_leaves_citations(mini_repo, tmp_path):
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"][0]["url"] = "https://example.org/landing/"
    data["sources"][0]["identifiers"] = {"mirror": "https://example.org/mirror/"}
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    body = _check(mini_repo, _package(tmp_path, [{
        "action": "correct", "id": "source-demo-book",
        "remove_identifiers": ["mirror"]}]))
    assert body["diff"][0]["fields"]["identifiers"]["after"] is None
    _refuses(mini_repo, _package(tmp_path, [{
        "action": "correct", "id": "source-demo-book", "remove_url": True,
        "remove_identifiers": ["mirror"]}]),
        "no reachable locator")


def test_correct_with_no_changes_is_refused(mini_repo, tmp_path):
    _refuses(mini_repo, _package(tmp_path, [{
        "action": "correct", "id": "source-demo-book", "title": "Demo Book"}]),
        "no intake field changes")


# --------------------------------------------------------------------- apply
def test_apply_creates_and_corrects_atomically(mini_repo, tmp_path):
    _thematic_groups(mini_repo)
    package = _package(tmp_path, [
        _create(partition="machine-learning.yaml",
                thematic_group_ids=["thematic-group-machine-learning"],
                url="https://example.org/new/"),
        {"action": "correct", "id": "source-demo-book", "title": "Demo Book Retitled"},
    ])
    checked = _check(mini_repo, package)
    payload = json.loads(json.dumps({
        "record": {"records": [
            _create(partition="machine-learning.yaml",
                    thematic_group_ids=["thematic-group-machine-learning"],
                    url="https://example.org/new/"),
            {"action": "correct", "id": "source-demo-book",
             "title": "Demo Book Retitled"},
        ]},
        "expected_diff_sha256": checked["diff_sha256"],
    }))
    proc = approved_v2_call(
        mini_repo, capability="source.intake.record", payload=payload,
        artifact_ids=["source-demo-book", "source-new-course"],
        idempotency_key="intake-apply",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is True
    assert body["receipt_path"].endswith(".yaml")
    created = yaml.safe_load(
        (mini_repo / "sources" / "registry" / "machine-learning.yaml")
        .read_text(encoding="utf-8"))
    assert created["sources"][0]["discovery"]["observed"] == "2026-09-23"
    stored = yaml.safe_load(
        (mini_repo / "sources" / "sources.yaml").read_text(encoding="utf-8"))
    assert stored["sources"][0]["title"] == "Demo Book Retitled"
    revisions = yaml.safe_load(
        (mini_repo / "operations" / "transactions" / "revisions.yaml")
        .read_text(encoding="utf-8"))
    assert revisions["revisions"]["source-new-course"] == 1
    assert revisions["revisions"]["source-demo-book"] == 1


def test_apply_needs_its_check_diff(mini_repo, tmp_path):
    package = _package(tmp_path, [_create()])
    checked = _check(mini_repo, package)
    record = {"records": [_create()]}
    missing = approved_v2_call(
        mini_repo, capability="source.intake.record",
        payload={"record": record}, artifact_ids=["source-new-course"],
        idempotency_key="intake-no-diff")
    inner = json.loads(json.loads(missing.stdout)["error"]["message"])
    assert inner["ok"] is False
    assert "expected-diff-sha256" in inner["error"]
    last = checked["diff_sha256"][-1]
    wrong = checked["diff_sha256"][:-1] + ("0" if last != "0" else "1")
    stale = approved_v2_call(
        mini_repo, capability="source.intake.record",
        payload={"record": record, "expected_diff_sha256": wrong},
        artifact_ids=["source-new-course"], idempotency_key="intake-wrong-diff")
    outer = json.loads(stale.stdout)["error"]["message"]
    assert "changed since check" in json.loads(outer)["error"]


def test_apply_refuses_a_stale_snapshot(mini_repo, tmp_path):
    package = _package(tmp_path, [_create()])
    checked = _check(mini_repo, package)
    proc = approved_v2_call(
        mini_repo, capability="source.intake.record",
        payload={"record": {"records": [_create()]},
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["source-new-course"], idempotency_key="intake-stale",
        expected_snapshot="sha256:" + "0" * 64)
    assert proc.returncode == 3, proc.stdout


def test_gateway_requires_an_inline_record(mini_repo, tmp_path):
    package = _package(tmp_path, [_create()])
    proc = approved_v2_call(
        mini_repo, capability="source.intake.record",
        payload={"file": str(package)}, artifact_ids=["source-new-course"],
        idempotency_key="intake-file")
    assert proc.returncode != 0
    assert "inline record" in proc.stdout + proc.stderr


def test_cli_apply_shape_runs_through_the_gateway(mini_repo, tmp_path):
    package = _package(tmp_path, [_create()])
    checked = _check(mini_repo, package)
    lone = approved_v2_cli(
        mini_repo, "source-intake", "--record", json.dumps({"records": [_create()]}),
        "--expected-diff-sha256", checked["diff_sha256"],
        artifact_ids=["source-new-course"], idempotency_key="intake-cli")
    assert lone.returncode == 0, lone.stderr + lone.stdout
    assert json.loads(lone.stdout)["ok"] is True
