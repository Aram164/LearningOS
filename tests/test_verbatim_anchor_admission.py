"""Real parser, byte-snapshot and exact-place evidence in disposable materials."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from repo_builders import add_curriculum, write_minimal_pdf, write_yaml

from learning_os.domain.verbatim import Quote
from learning_os.store.loader import load_repo
from learning_os.store.materials import anchors
from learning_os.store.materials.anchors import AnchorError, AnchorReader, RouteMaterial

TEXT = "The expected value is the probability weighted sum of the possible outcomes."
OTHER = "A different chapter explains conditional distributions and independence."
URI = "material://source-demo-book/"


@pytest.fixture
def material_world(mini_repo):
    add_curriculum(mini_repo)
    registry = mini_repo / "sources/sources.yaml"
    data = yaml.safe_load(registry.read_text())
    data["sources"][0]["material"] = URI
    write_yaml(registry, data)
    folder = mini_repo.parent / "materials/source-demo-book"
    write_minimal_pdf(folder / "book.pdf", [TEXT, OTHER])
    write_minimal_pdf(folder / "other.pdf", [OTHER])
    manifest = {f"source-demo-book/{path.name}": {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in folder.iterdir()}
    return mini_repo, folder, manifest


def reader(world):
    root, _, manifest = world
    return AnchorReader(load_repo(root), manifest)


def route(**changes):
    return replace(RouteMaterial("route-test", "source-demo-book",
                                 "book.pdf, PDF pp. 1-2", URI + "book.pdf"), **changes)


def test_right_file_page_and_digest(material_world):
    proof = reader(material_world).verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))
    assert proof.manifest_path == "source-demo-book/book.pdf"
    assert proof.quote_sha256.startswith("sha256:")
    assert proof.trail.startswith("quote:" + URI + "book.pdf#p1 sha256:")
    assert TEXT not in proof.trail


@pytest.mark.parametrize(("quote", "message"), [
    (Quote(URI + "other.pdf", OTHER, page=1), "wrong file"),
    (Quote(URI + "book.pdf", TEXT, page=3), "locator span"),
    (Quote(URI + "book.pdf", OTHER, page=1), "not found"),
    (Quote(URI + "book.pdf", TEXT, window="00:00-00:30"), "explicit page"),
])
def test_wrong_file_page_or_quote_refuses(material_world, quote, message):
    with pytest.raises(AnchorError, match=message):
        reader(material_world).verify_quote(route(), quote)


def test_page_beyond_file_and_page_outside_own_span(material_world):
    with pytest.raises(AnchorError, match="outside this 2-page file"):
        reader(material_world).verify_quote(route(locator="book.pdf"),
                                            Quote(URI + "book.pdf", TEXT, page=3))
    with pytest.raises(AnchorError, match="locator span"):
        reader(material_world).verify_quote(route(locator="book.pdf, PDF p. 2"),
                                            Quote(URI + "book.pdf", TEXT, page=1))


def test_quote_can_cross_one_page_break(material_world):
    quote = Quote(URI + "book.pdf", TEXT[-30:] + " " + OTHER[:35], page=1, page_end=2)
    assert reader(material_world).verify_quote(route(), quote).place == "p1-2"


def test_manifest_digest_mismatch_refuses(material_world):
    material_world[2]["source-demo-book/book.pdf"]["sha256"] = "0" * 64
    with pytest.raises(AnchorError, match="digest differs"):
        reader(material_world).verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))


def test_unmounted_and_unresolved_local_material_are_explicit(material_world):
    root, folder, _ = material_world
    observed = reader(material_world)
    assert observed.materials(route(vault_path="", locator="missing.pdf")).kind == "local-unresolved"
    folder.rename(folder.with_name("unmounted-source"))
    assert observed.materials(route()).kind == "local-unresolved"
    root.parent.joinpath("materials").rename(root.parent / "offline-materials")
    assert observed.materials(route()).kind == "offline"
    with pytest.raises(AnchorError, match="offline"):
        observed.verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))


def test_removing_binding_or_ambiguous_locator_cannot_downgrade_local_claim(material_world):
    observed = reader(material_world)
    before = route()
    for after in (route(vault_path="", locator=""),
                  route(vault_path="", locator="book.pdf through other.pdf")):
        assert observed.materials(after, before).kind == "local-unresolved"
        with pytest.raises(AnchorError, match="cannot downgrade"):
            observed.verify_quote(after, Quote(URI + "book.pdf", TEXT, page=1), before)


def test_partial_multi_file_resolution_refuses_even_a_correct_quote(material_world):
    observed = reader(material_world)
    partial = route(vault_path="", locator="book.pdf, PDF p. 1; missing.pdf, PDF p. 1")
    assert observed.materials(partial).kind == "local-unresolved"
    with pytest.raises(AnchorError, match="cannot downgrade"):
        observed.verify_quote(partial, Quote(URI + "book.pdf", TEXT, page=1))


def test_multi_file_page_span_belongs_to_the_named_file(material_world):
    both = route(vault_path="", locator="book.pdf, PDF p. 1; other.pdf, PDF p. 2")
    with pytest.raises(AnchorError, match="locator span"):
        reader(material_world).verify_quote(both, Quote(URI + "other.pdf", OTHER, page=1))


def test_no_text_fallback_needs_explicit_place_and_note(material_world):
    _, folder, manifest = material_world
    write_minimal_pdf(folder / "book.pdf", [""])
    manifest["source-demo-book/book.pdf"]["sha256"] = hashlib.sha256((folder / "book.pdf").read_bytes()).hexdigest()
    observed = reader(material_world)
    with pytest.raises(AnchorError, match="no text layer"):
        observed.verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))
    for page, note in ((None, "reviewed image page"), (1, ""), (True, "reviewed image page")):
        with pytest.raises(AnchorError):
            observed.verify_unreadable(route(), "source-demo-book/book.pdf", note, page)
    proof = observed.verify_unreadable(route(), "source-demo-book/book.pdf", "reviewed image page", 1)
    assert proof.place == "p1" and not proof.quote_sha256


def test_parser_failure_is_never_the_no_text_fallback(material_world):
    _, folder, manifest = material_world
    (folder / "book.pdf").write_bytes(b"broken PDF bytes")
    manifest["source-demo-book/book.pdf"]["sha256"] = hashlib.sha256(b"broken PDF bytes").hexdigest()
    with pytest.raises(AnchorError, match="cannot be parsed"):
        reader(material_world).verify_unreadable(route(), "source-demo-book/book.pdf", "inspected", 1)


def test_readable_pdf_cannot_use_manifest_only_evidence(material_world):
    with pytest.raises(AnchorError, match="readable and requires"):
        reader(material_world).verify_unreadable(route(), "source-demo-book/book.pdf", "inspected", 1)


def test_unsupported_format_has_explicit_digest_bound_fallback(material_world):
    _, folder, manifest = material_world
    (folder / "lesson.ipynb").write_bytes(b'{"cells": []}')
    manifest["source-demo-book/lesson.ipynb"] = {"sha256": hashlib.sha256(b'{"cells": []}').hexdigest()}
    notebook = route(vault_path=URI + "lesson.ipynb", locator="lesson.ipynb")
    observed = reader(material_world)
    assert observed.verify_unreadable(notebook, "source-demo-book/lesson.ipynb", "inspected externally").place == "unsupported-format"
    with pytest.raises(AnchorError, match="wrong file"):
        observed.verify_unreadable(notebook, "source-demo-book/book.pdf", "inspected externally")


def _transcript(world, *, video_id="video-demo"):
    _, folder, manifest = world
    content = (f"- video_id: `{video_id}`\n- duration: 20:00\n- window: 30s\n\n"
               f"[00:00] {TEXT}\n[00:30] {OTHER}\n[15:00] {TEXT}\n").encode()
    path = folder / "transcript.md"
    path.write_bytes(content)
    manifest["source-demo-book/transcript.md"] = {"sha256": hashlib.sha256(content).hexdigest()}
    return URI + "transcript.md"


def test_transcript_window_and_explicit_authority_fallback(material_world):
    ref = _transcript(material_world)
    video = route(vault_path="", locator="Video section 00:00-00:30", url="https://youtu.be/video-demo")
    proof = reader(material_world).verify_quote(video, Quote(ref, TEXT, window="00:00-00:30"))
    assert proof.place == "t00:00-00:30"
    assert "lang=en" in proof.trail


@pytest.mark.parametrize("window", ["00:00-06:00", "15:00-15:30", "19:30-20:30", "00:01-00:31"])
def test_transcript_rejects_wide_distant_outside_or_off_grid_windows(material_world, window):
    ref = _transcript(material_world)
    video = route(vault_path=ref, locator="transcript.md, video 00:00-00:30", url="https://youtu.be/video-demo")
    with pytest.raises(AnchorError):
        reader(material_world).verify_quote(video, Quote(ref, TEXT, window=window))


def test_transcript_video_identity_must_match(material_world):
    ref = _transcript(material_world, video_id="different-video")
    video = route(vault_path="", locator="00:00-00:30", url="https://youtube.com/watch?v=video-demo")
    with pytest.raises(AnchorError, match="video_id differs"):
        reader(material_world).verify_quote(video, Quote(ref, TEXT, window="00:00-00:30"))


def test_replacement_during_extraction_is_detected(material_world, monkeypatch):
    _, folder, _ = material_world
    original = anchors.pdf_page_text

    def replace_after_extract(pdf, page):
        text = original(pdf, page)
        write_minimal_pdf(folder / "book.pdf", [OTHER])
        return text

    monkeypatch.setattr(anchors, "pdf_page_text", replace_after_extract)
    with pytest.raises(AnchorError, match="changed during admission"):
        reader(material_world).verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))


def test_apply_uses_a_new_observation_and_refuses_changed_bytes(material_world):
    _, folder, _ = material_world
    assert reader(material_world).verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))
    write_minimal_pdf(folder / "book.pdf", [OTHER])
    with pytest.raises(AnchorError, match="digest differs"):
        reader(material_world).verify_quote(route(), Quote(URI + "book.pdf", TEXT, page=1))


def test_unique_file_is_read_and_parsed_once_per_request(material_world, monkeypatch):
    _, folder, _ = material_world
    counts = {"read": 0, "parse": 0, "page": 0}
    original_open, original_reader, original_page = Path.open, anchors.pdf_reader, anchors.pdf_page_text

    def opened(path, *args, **kwargs):
        if path == (folder / "book.pdf").resolve():
            counts["read"] += 1
        return original_open(path, *args, **kwargs)

    def parsed(content):
        counts["parse"] += 1
        return original_reader(content)

    def page_text(pdf, page):
        counts["page"] += 1
        return original_page(pdf, page)

    observed = reader(material_world)
    monkeypatch.setattr(Path, "open", opened)
    monkeypatch.setattr(anchors, "pdf_reader", parsed)
    monkeypatch.setattr(anchors, "pdf_page_text", page_text)
    for page, text in ((1, TEXT), (1, TEXT), (2, OTHER)):
        observed.verify_quote(route(), Quote(URI + "book.pdf", text, page=page))
    assert counts == {"read": 1, "parse": 1, "page": 2}


def _patch_world(root):
    from repo_builders import SLICED_LECTURE_TEXT, _sliced_route, _sliced_unit

    from learning_os.app.validation_service import collect
    from learning_os.store.warning_baseline import write_baseline

    _sliced_unit(root, [_sliced_route("route-test", "lecture-01.pdf")])
    write_baseline(root, collect(root)[0], "route patch claim fixture")
    return {"claim_id": "covers:route-test", "evidence": [{
        "kind": "quote", "ref": URI + "lecture-01.pdf", "page": 1, "text": SLICED_LECTURE_TEXT}]}


def test_route_patch_material_change_requires_evidence_before_writing(mini_repo):
    import json

    from repo_builders import run_los

    from learning_os.store.fingerprint import canonical_fingerprint

    _patch_world(mini_repo)
    before = canonical_fingerprint(mini_repo)
    result = run_los(mini_repo, "route-patch", "unit-demo-l01", "route-test", "--changes",
                     json.dumps({"locator": "lecture-01.pdf, PDF p. 1"}), "--check")
    assert result.returncode == 1
    assert "without claim evidence" in result.stderr
    assert canonical_fingerprint(mini_repo) == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_route_patch_uses_shared_admission_guard_and_atomic_lineage(mini_repo):
    import json

    from gateway_helpers import approved_v2_envelope, run_v2_capability
    from repo_builders import SLICED_LECTURE_TEXT, run_los

    from learning_os.derive.semantics.lineage import load_ledger

    evidence = _patch_world(mini_repo)
    changes = {"locator": "lecture-01.pdf, PDF p. 1"}
    checked = run_los(mini_repo, "route-patch", "unit-demo-l01", "route-test", "--changes",
                      json.dumps(changes), "--claim-evidence", json.dumps(evidence), "--check")
    assert checked.returncode == 0, checked.stderr + checked.stdout
    report = json.loads(checked.stdout)
    assert "operations/transactions/lineage.yaml" in report["affected_files"]
    assert "file:operations/transactions/lineage.yaml" in report["expected_revisions"]
    assert report["claim_anchors"][0]["classification"] == "anchored"
    envelope = approved_v2_envelope(mini_repo, capability="route.patch", payload=report["next"]["payload"],
                                    artifact_ids=report["artifact_ids"], idempotency_key="patch-anchored")
    applied = run_v2_capability(mini_repo, envelope)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    response = json.loads(applied.stdout)
    lineage = load_ledger(mini_repo)["covers:route-test"]
    assert any(trail.startswith("quote:") for trail in lineage.derived_from.evidence)
    receipt = yaml.safe_load((mini_repo / response["receipt_path"]).read_text())
    for row in receipt["writes"]:
        assert SLICED_LECTURE_TEXT.encode() not in (mini_repo / row["path"]).read_bytes()
    repeated = run_v2_capability(mini_repo, envelope)
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert json.loads(repeated.stdout)["replayed"] is True


def test_route_patch_cannot_supply_another_routes_evidence(mini_repo):
    import json

    from repo_builders import run_los

    evidence = _patch_world(mini_repo)
    evidence["claim_id"] = "covers:route-other"
    result = run_los(mini_repo, "route-patch", "unit-demo-l01", "route-test", "--changes",
                     json.dumps({"locator": "lecture-01.pdf, PDF p. 1"}),
                     "--claim-evidence", json.dumps(evidence), "--check")
    assert result.returncode == 1
    assert "exactly this route" in result.stderr


def _source_patch_admission(root, material, evidence=None):
    """The route inherits the source's exact-file binding, without a row edit."""
    from learning_os.app.claim_admission import prepare_claim_admission

    _patch_world(root)
    registry = root / "sources/sources.yaml"
    data = yaml.safe_load(registry.read_text())
    data["sources"][0]["material"] = URI + "lecture-01.pdf"
    write_yaml(registry, data)
    source_map = root / "curriculum/modules/module-demo/source-map.yaml"
    data = yaml.safe_load(source_map.read_text())
    data["sources"][0]["unit_routes"][0]["locator"] = "Chapter on expectation"
    write_yaml(source_map, data)
    repo = load_repo(root)
    package = {"source_patches": [{"id": "source-demo-book", "material": material}]}
    if evidence is not None:
        package["claim_evidence"] = [{"claim_id": "covers:route-test", "evidence": evidence}]
    return prepare_claim_admission(root, repo, "module-demo", package), repo


def test_source_material_change_requires_readmission_without_route_edit(mini_repo):
    result, repo = _source_patch_admission(mini_repo, URI + "replacement.pdf")
    assert any("without claim evidence" in problem for problem in result.problems)
    assert repo.sources["source-demo-book"]["material"] == URI + "lecture-01.pdf"


@pytest.mark.parametrize("material", ["", "https://example.test/remote", URI + "missing.pdf"])
def test_source_material_removal_cannot_downgrade_to_remote(mini_repo, material):
    result, _ = _source_patch_admission(mini_repo, material, [
        {"kind": "external", "ref": "https://example.test/remote", "note": "reviewed"}])
    assert any("local claim requires" in problem for problem in result.problems)


def test_source_material_replacement_checks_proposed_file_not_old_binding(mini_repo):
    from repo_builders import SLICED_LECTURE_TEXT

    folder = mini_repo.parent / "materials/source-demo-book"
    write_minimal_pdf(folder / "replacement.pdf", [OTHER])
    manifest_path = mini_repo / "records/materials-manifest.yaml"
    write_yaml(manifest_path, {"files": {"source-demo-book/replacement.pdf": {
        "sha256": hashlib.sha256((folder / "replacement.pdf").read_bytes()).hexdigest()}}})
    result, _ = _source_patch_admission(mini_repo, URI + "replacement.pdf", [{
        "kind": "quote", "ref": URI + "lecture-01.pdf", "page": 1, "text": SLICED_LECTURE_TEXT}])
    assert any("wrong file" in problem for problem in result.problems)
    from learning_os.app.claim_admission import prepare_claim_admission

    repo = load_repo(mini_repo)
    result = prepare_claim_admission(mini_repo, repo, "module-demo", {
        "source_patches": [{"id": "source-demo-book", "material": URI + "replacement.pdf"}],
        "claim_evidence": [{"claim_id": "covers:route-test", "evidence": [{
            "kind": "quote", "ref": URI + "replacement.pdf", "page": 1, "text": OTHER}]}]})
    assert not result.problems
    assert result.evidence["covers:route-test"].anchors[0].material_uri.endswith("replacement.pdf")


@pytest.mark.parametrize(("path", "content", "message"), [
    ("operations/transactions/lineage.yaml", "records: [broken", "cannot read"),
    ("records/materials-manifest.yaml", "files: [broken", "cannot read materials manifest"),
    ("operations/transactions/revisions.yaml", "revisions: [broken", "revision ledger is unreadable"),
])
def test_admission_returns_named_problem_for_malformed_inputs(mini_repo, path, content, message):
    from learning_os.app.claim_admission import prepare_claim_admission

    _patch_world(mini_repo)
    repo = load_repo(mini_repo)
    target = mini_repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    result = prepare_claim_admission(mini_repo, repo, "module-demo", {})
    assert any(message in problem for problem in result.problems)


@pytest.mark.parametrize(("kind", "message"), [("none", "without claim evidence"),
    ("donor", "wrong file"), ("wrong-text", "not found"), ("genuine", "ROUTE-LOCATOR-DUPLICATE")])
def test_broadcast_replay_refuses_in_admission_or_staged_validation(mini_repo, monkeypatch, kind, message):
    import copy
    import json

    from repo_builders import _sliced_route, _sliced_unit, run_los

    from learning_os.app.validation_service import collect
    from learning_os.store.fingerprint import canonical_fingerprint
    from learning_os.store.warning_baseline import write_baseline

    script = {**_sliced_route("route-script", "script.pdf, PDF pp. 1-2"), "vault_path": URI + "script.pdf"}
    sheet = {**_sliced_route("route-sheet", "sheet.pdf, PDF p. 1"), "vault_path": URI + "sheet.pdf"}
    _sliced_unit(mini_repo, [script, sheet])
    folder = mini_repo.parent / "materials/source-demo-book"
    write_minimal_pdf(folder / "script.pdf", [TEXT, OTHER])
    write_minimal_pdf(folder / "sheet.pdf", [OTHER])
    manifest_path = mini_repo / "records/materials-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    for name in ["script.pdf", "sheet.pdf"]:
        path = folder / name
        manifest["files"]["source-demo-book/" + name] = {"size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    write_yaml(manifest_path, manifest)
    write_baseline(mini_repo, collect(mini_repo)[0], "broadcast fixture")
    before = canonical_fingerprint(mini_repo)
    args = ["route-patch", "unit-demo-l01", "route-script", "--changes", json.dumps({
        "locator": sheet["locator"], "angle_detail": sheet["angle_detail"]}), "--check"]
    evidence = None
    if kind != "none":
        evidence = {"claim_id": "covers:route-script", "evidence": [{"kind": "quote",
            "ref": URI + ("sheet.pdf" if kind == "donor" else "script.pdf"),
            "page": 1, "text": TEXT if kind == "genuine" else OTHER}]}
        args += ["--claim-evidence", json.dumps(evidence)]
    result = run_los(mini_repo, *args)
    assert result.returncode == (2 if kind == "genuine" else 1) and message in result.stderr
    if kind == "genuine":
        assert "ROUTE-VAULT-LOCATOR-MISMATCH" in result.stderr
    assert canonical_fingerprint(mini_repo) == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    from learning_os.app import claim_admission
    from learning_os.derive.validation import plan_rigor
    repo = load_repo(mini_repo)
    source_map = copy.deepcopy(repo.module_source_maps["module-demo"])
    changed = source_map["sources"][0]["unit_routes"][0]
    changed.update(locator=sheet["locator"], angle_detail=sheet["angle_detail"])
    assert claim_admission.prepare_claim_admission(mini_repo, repo, "module-demo", {"source_map": source_map}).problems
    with monkeypatch.context() as disabled:
        disabled.setattr(claim_admission, "IDENTITY_FIELDS", ())
        assert not claim_admission.prepare_claim_admission(mini_repo, repo, "module-demo", {"source_map": source_map}).problems
    corrected = run_los(mini_repo, "route-patch", "unit-demo-l01", "route-script", "--changes",
        json.dumps({"angle_detail": "A reviewed explanation specific to the script's expectation derivation."}), "--check")
    assert corrected.returncode == 0, corrected.stderr
    # Replay the actual bad authored rows; disable only the new binding rules
    # and run the production validator again, retaining all other checks.
    write_yaml(mini_repo / "curriculum/modules/module-demo/source-map.yaml", source_map)
    errors = collect(mini_repo)[1]
    assert len(errors) == 2
    assert all(any(code in error for error in errors) for code in {"ROUTE-LOCATOR-DUPLICATE", "ROUTE-VAULT-LOCATOR-MISMATCH"})
    with monkeypatch.context() as disabled:
        disabled.setattr(plan_rigor, "locator_binding_findings", lambda *_: [])
        assert collect(mini_repo)[1] == []


def test_source_binding_change_stales_an_admitted_claim(mini_repo):
    import json

    from gateway_helpers import approved_v2_envelope, run_v2_capability
    from repo_builders import run_los

    from learning_os.derive.semantics.claim_status import observe_claims

    evidence = _patch_world(mini_repo)
    result = run_los(mini_repo, "route-patch", "unit-demo-l01", "route-test", "--changes",
        json.dumps({"locator": "lecture-01.pdf, PDF p. 1"}), "--claim-evidence", json.dumps(evidence), "--check")
    report = json.loads(result.stdout)
    envelope = approved_v2_envelope(mini_repo, capability="route.patch", payload=report["next"]["payload"],
        artifact_ids=report["artifact_ids"], idempotency_key="source-binding-pin")
    applied = run_v2_capability(mini_repo, envelope)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert observe_claims(mini_repo)["covers:route-test"].status == "supported"
    registry = mini_repo / "sources/sources.yaml"
    data = yaml.safe_load(registry.read_text())
    data["sources"][0]["material"] = "https://example.test/rebound"
    write_yaml(registry, data)
    status = observe_claims(mini_repo)["covers:route-test"]
    assert status.status == "stale" and "source-material:source-demo-book" in status.moved
