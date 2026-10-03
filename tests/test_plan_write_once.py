"""One full validation per plan-class apply (F4).

`route.patch`, `module.materials.compact` and the module-plan imports used
to validate twice per submit: a shadow pre-validation, then the
transaction's own validation of the same staged state. A gateway apply now
runs the gate once, inside the transaction, on the staged state — the
shadow remains for `--check`, where nothing is written and it is the only
validation, and for direct CLI applies, which the transaction refuses as
envelope-less either way. These tests pin the count and the refusal
equivalence: every refusal survives with identical text.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
from gateway_helpers import approved_v2_envelope
from repo_builders import material_fixture, run_los, write_yaml
from test_compact_module_plan_revision import _revision, _two_units

import los
from learning_os.commands.capability import cmd_capability
from learning_os.commands.material import (
    cmd_module_materials_compact,
    cmd_route_patch,
    route_patch_plan,
)
from learning_os.commands.module import cmd_module_plan_import
from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo
from learning_os.material_refs import unit_routes
from learning_os.rules.core import Validator

FUSED_LOCATOR = ("Lecture 2 — this tail is a very long sentence with many "
                 "words and no digits whatsoever in it")


def _count_validations(monkeypatch: pytest.MonkeyPatch) -> list:
    """Count full validator runs whatever the import path (F4, cf. #104).

    Every caller binds `validate` by name at import, so wrapping the
    module attribute would count nothing; `Validator.run` is the one seam
    every full validation funnels through.
    """
    runs: list = []
    original = Validator.run

    def counted(self):
        runs.append(1)
        return original(self)

    monkeypatch.setattr(Validator, "run", counted)
    return runs


def _capability_args(root: Path, envelope_path: Path, capability: str):
    return argparse.Namespace(
        root=str(root), name=capability, payload_file=str(envelope_path),
        replay_only=False, _parser_factory=los.build_parser)


def _apply_in_process(root: Path, tmp_path: Path, *, capability: str,
                      payload: dict, artifact_ids, key: str,
                      capsys) -> tuple[int, dict]:
    envelope = approved_v2_envelope(
        root, capability=capability, payload=payload,
        artifact_ids=list(artifact_ids), idempotency_key=key)
    envelope_path = tmp_path / f"{key}.json"
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    code = cmd_capability(_capability_args(root, envelope_path, capability))
    out = capsys.readouterr().out
    return code, json.loads(out)


def _compact_check_args(root: Path, draft: Path):
    return argparse.Namespace(
        root=str(root), module_id="module-demo", file=str(draft),
        file_sha256=None, promotion=None, check=True, staged_basis=None,
        expected_snapshot=None, expected_revision=[],
        _parser_factory=los.build_parser, apply_reviewed_sha256=None,
        review_report=None, report_out=None)


def _route_patch_check_text(root: Path, unit_id: str, rid: str,
                            changes: dict) -> str:
    """The --check refusal text, or "" when the check passes."""
    from learning_os.commands.support import ValidationFailed

    args = argparse.Namespace(
        root=str(root), unit_id=unit_id, route_id=rid, changes=changes,
        check=True, plan_sha256=None, expected_snapshot=None,
        expected_revision=[])
    try:
        assert cmd_route_patch(args) == 0
    except ValidationFailed as exc:
        return str(exc)
    return ""


def test_route_patch_apply_validates_once(mini_repo: Path, tmp_path: Path,
                                          monkeypatch, capsys):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    changes = {"angle": "A counted explanation"}
    _, artifacts, _ = route_patch_plan(repo, unit_id, rid, changes)
    runs = _count_validations(monkeypatch)
    code, body = _apply_in_process(
        mini_repo, tmp_path, capability="route.patch",
        payload={"unit_id": unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), key="count-route-patch", capsys=capsys)
    assert code == 0, body
    assert body["ok"] is True
    assert len(runs) == 1


def test_compact_apply_validates_once(mini_repo: Path, tmp_path: Path,
                                      monkeypatch, capsys):
    material_fixture(mini_repo)
    check_args = argparse.Namespace(
        root=str(mini_repo), module_id="module-demo", check=True,
        plan_sha256=None, expected_snapshot=None, expected_revision=[])
    assert cmd_module_materials_compact(check_args) == 0
    plan = json.loads(capsys.readouterr().out)
    runs = _count_validations(monkeypatch)
    code, body = _apply_in_process(
        mini_repo, tmp_path, capability="module.materials.compact",
        payload={"module_id": "module-demo",
                 "plan_sha256": plan["plan_sha256"]},
        artifact_ids=plan["artifact_ids"], key="count-compact", capsys=capsys)
    assert code == 0, body
    assert body["ok"] is True
    assert len(runs) == 1


def test_module_plan_import_apply_validates_once(mini_repo: Path, tmp_path: Path,
                                                monkeypatch, capsys):
    _two_units(mini_repo)
    draft = tmp_path / "compact.yaml"
    write_yaml(draft, _revision(mini_repo))
    assert cmd_module_plan_import(
        _compact_check_args(mini_repo, draft)) == 0, capsys.readouterr().err
    report = json.loads(capsys.readouterr().out)
    review = tmp_path / "review.json"
    review.write_text(json.dumps(report), encoding="utf-8")
    runs = _count_validations(monkeypatch)
    apply_args = argparse.Namespace(
        root=str(mini_repo), module_id="module-demo", file=str(draft),
        file_sha256=None, promotion=None, check=False, staged_basis=None,
        expected_snapshot=None, expected_revision=[],
        _parser_factory=los.build_parser,
        apply_reviewed_sha256=report["reviewed_file_sha256"],
        review_report=str(review), report_out=None)
    assert cmd_module_plan_import(apply_args) == 0, capsys.readouterr().err
    body = json.loads(capsys.readouterr().out)
    assert body["ok"] is True, body
    assert len(runs) == 1


def test_route_patch_error_refusal_matches_check(mini_repo: Path, tmp_path: Path,
                                                 capsys):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    changes = {"locator": FUSED_LOCATOR}
    check_text = _route_patch_check_text(mini_repo, unit_id, rid, changes)
    assert "E LOCATOR-ANGLE-FUSED" in check_text
    capsys.readouterr()
    _, artifacts, _ = route_patch_plan(repo, unit_id, rid, changes)
    before = canonical_fingerprint(mini_repo)
    code, body = _apply_in_process(
        mini_repo, tmp_path, capability="route.patch",
        payload={"unit_id": unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), key="refusal-error", capsys=capsys)
    assert code == 2
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_FAILED"
    assert body["error"]["message"] == check_text
    assert canonical_fingerprint(mini_repo) == before


def _precise_locator_fixture(mini_repo: Path):
    """The material fixture with a precise locator, re-baselined.

    Returns (unit_id, route_id): patching the locator back to a vague one
    introduces a warning signature the recorded baseline does not have.
    """
    import yaml

    from learning_os.warning_baseline import collect, write_baseline

    repo, _, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    source_path = (mini_repo / "curriculum/modules/module-demo/source-map.yaml")
    source_map = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["locator"] = "Chapter 1, pp. 1-20"
    write_yaml(source_path, source_map)
    study_map = load_repo(mini_repo).study_maps[smid]
    data = yaml.safe_load(study_map.path.read_text(encoding="utf-8"))
    for resource in data["stages"][0]["resources"]:
        if resource.get("locator") == "lecture-01.pdf":
            resource["locator"] = "Chapter 1, pp. 1-20"
    write_yaml(study_map.path, data)
    signatures, errors = collect(mini_repo)
    assert errors == []
    write_baseline(mini_repo, signatures, "precise locator re-baseline")
    repo = load_repo(mini_repo)
    routes = unit_routes(repo.module_source_maps["module-demo"],
                         "module-demo", unit_id)
    return unit_id, routes[0]["id"]


def test_route_patch_warning_refusal_matches_check(mini_repo: Path, tmp_path: Path,
                                                   capsys):
    unit_id, rid = _precise_locator_fixture(mini_repo)
    changes = {"locator": "scattered remarks"}
    check_text = _route_patch_check_text(mini_repo, unit_id, rid, changes)
    assert "NEW-OR-GROWN-WARNING" in check_text
    assert "LOCATOR-VAGUE" in check_text
    capsys.readouterr()
    repo = load_repo(mini_repo)
    _, artifacts, _ = route_patch_plan(repo, unit_id, rid, changes)
    before = canonical_fingerprint(mini_repo)
    code, body = _apply_in_process(
        mini_repo, tmp_path, capability="route.patch",
        payload={"unit_id": unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), key="refusal-warning", capsys=capsys)
    assert code == 2
    assert body["ok"] is False
    assert body["error"]["code"] == "VALIDATION_FAILED"
    assert body["error"]["message"] == check_text
    assert canonical_fingerprint(mini_repo) == before


def test_route_patch_stale_revision_still_refuses(mini_repo: Path, tmp_path: Path,
                                                  capsys):
    from learning_os.contracts.gateway import intent_sha256

    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    changes = {"angle": "A counted explanation"}
    _, artifacts, _ = route_patch_plan(repo, unit_id, rid, changes)
    envelope = approved_v2_envelope(
        mini_repo, capability="route.patch",
        payload={"unit_id": unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), idempotency_key="refusal-stale")
    stale = next(iter(sorted(artifacts)))
    envelope["expected_revisions"][stale] += 1
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    envelope_path = tmp_path / "stale.json"
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    before = canonical_fingerprint(mini_repo)
    code = cmd_capability(_capability_args(mini_repo, envelope_path, "route.patch"))
    body = json.loads(capsys.readouterr().out)
    assert code == 3
    assert body["ok"] is False
    assert body["error"]["code"] == "REVISION_CONFLICT"
    assert canonical_fingerprint(mini_repo) == before


def test_module_plan_error_refusal_matches_check(mini_repo: Path, tmp_path: Path,
                                                 capsys):
    import hashlib

    _two_units(mini_repo)
    clean_revision = _revision(mini_repo)
    clean_revision["unit_revisions"] = [clean_revision["unit_revisions"][0]]
    clean = tmp_path / "clean.yaml"
    write_yaml(clean, clean_revision)
    assert cmd_module_plan_import(_compact_check_args(mini_repo, clean)) == 0
    clean_report = json.loads(capsys.readouterr().out)
    revision = _revision(mini_repo)
    revision["unit_revisions"] = [{
        "unit_id": "unit-demo-l01",
        "route_changes": {"update": [{
            "route_id": "route-demo-book",
            "fields": {"locator": FUSED_LOCATOR}}]},
        # Same stage patch as the clean revision, so the same files —
        # and the same commit set — change.
        "stage_patches": [{"stage_id": "stage-demo",
                           "fields": {"title": "First revised stage"}}],
    }]
    draft = tmp_path / "fused.yaml"
    write_yaml(draft, revision)
    draft_sha = "sha256:" + hashlib.sha256(draft.read_bytes()).hexdigest()
    assert cmd_module_plan_import(_compact_check_args(mini_repo, draft)) == 1
    check_err = capsys.readouterr().err
    assert "module plan validation preflight failed" in check_err
    assert "LOCATOR-ANGLE-FUSED" in check_err
    before = canonical_fingerprint(mini_repo)
    # The fused update changes the same files as the clean one, so its
    # commit set is the clean check's — a reviewed apply is impossible
    # (a failing check prepares no envelope), hence the direct submit.
    code, body = _apply_in_process(
        mini_repo, tmp_path, capability="module.plan.import",
        payload={"module_id": "module-demo", "file": str(draft),
                 "file_sha256": draft_sha},
        artifact_ids=clean_report["commit_artifact_ids"],
        key="refusal-module-error", capsys=capsys)
    assert code == 1
    assert body["ok"] is False
    # The preflight path never carried a typed code; the gate keeps it so.
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert body["error"]["message"] == check_err.strip()
    assert canonical_fingerprint(mini_repo) == before


def test_direct_apply_keeps_the_shadow_refusal_text(mini_repo: Path):
    """Without an envelope the apply still fails on the plan, not the gate."""
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    probed = run_los(mini_repo, "route-patch", unit_id, rid,
                     "--changes", json.dumps({"locator": FUSED_LOCATOR}))
    assert probed.returncode == 2
    assert "canonical validation failed: E LOCATOR-ANGLE-FUSED" in probed.stderr
    assert "GatewayEnvelopeV2" not in probed.stderr
