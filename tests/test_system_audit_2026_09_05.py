"""Regression pins for the 2026-09-05 three-pillar audit.

Each test names the finding it pins and asserts the *intended* behaviour, not
the observed failure: the audit's reproduction scripts print state and exit 0
either way, so only an assertion here can keep a repair from silently
regressing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_cli, file_sha256
from test_curriculum_v2 import _add_material_overview, add_curriculum, write_yaml

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def _material_toc():
    """Load the authoring tool as a module without running its CLI."""
    spec = importlib.util.spec_from_file_location(
        "audit_material_toc", TOOLS / "material_toc.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------- F12 material
def _duplicate_basename_tree(tmp_path: Path) -> Path:
    materials = tmp_path / "materials"
    for branch in ("a", "b"):
        target = materials / "source-demo" / branch / "chapter.pdf"
        target.parent.mkdir(parents=True)
        target.write_bytes(branch.encode())
    return materials


def test_locator_verification_resolves_the_exact_requested_path(tmp_path: Path):
    """F12: two files share a basename; the full relative path decides."""
    toc = _material_toc()
    toc.MATERIALS = _duplicate_basename_tree(tmp_path)

    for branch in ("a", "b"):
        resolved = toc.resolve(f"material://source-demo/{branch}/chapter.pdf")
        assert resolved.parent.name == branch
        assert resolved.read_bytes() == branch.encode()


def test_locator_verification_refuses_a_basename_only_match(tmp_path: Path):
    """F12: a request naming no existing exact path fails closed."""
    toc = _material_toc()
    toc.MATERIALS = _duplicate_basename_tree(tmp_path)

    with pytest.raises(SystemExit, match="no material at the exact path"):
        toc.resolve("material://source-demo/chapter.pdf")
    with pytest.raises(SystemExit, match="no material at the exact path"):
        toc.resolve("material://source-demo/c/chapter.pdf")


def test_locator_verification_refuses_unsafe_and_escaping_references(tmp_path: Path):
    """F12: traversal and escaping symlinks stay refused by the boundary."""
    toc = _material_toc()
    materials = _duplicate_basename_tree(tmp_path)
    toc.MATERIALS = materials
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sealed.pdf").write_bytes(b"EXTERNAL")
    (materials / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SystemExit):
        toc.resolve("material://source-demo/../outside/sealed.pdf")
    with pytest.raises(SystemExit):
        toc.resolve("material://escape/sealed.pdf")


def test_locator_verification_refuses_two_equally_valid_spellings(tmp_path: Path):
    """F12: `demo` and `source-demo` both existing is an ambiguity, not a pick."""
    toc = _material_toc()
    materials = tmp_path / "materials"
    for folder in ("demo", "source-demo"):
        target = materials / folder / "chapter.pdf"
        target.parent.mkdir(parents=True)
        target.write_bytes(folder.encode())
    toc.MATERIALS = materials

    with pytest.raises(SystemExit, match="ambiguous material reference"):
        toc.resolve("material://demo/chapter.pdf")


def test_locator_verification_uses_the_flat_alias_root(tmp_path: Path):
    """F12: id-based URIs resolve through `materials/.flat/`, as the manifest does."""
    toc = _material_toc()
    materials = tmp_path / "materials"
    physical = materials / "mathematics" / "sad-lectures"
    physical.mkdir(parents=True)
    (physical / "03_correlation.pdf").write_bytes(b"lecture")
    flat = materials / ".flat"
    flat.mkdir()
    (flat / "source-sad").symlink_to(physical, target_is_directory=True)
    toc.MATERIALS = materials

    resolved = toc.resolve("material://source-sad/03_correlation.pdf")

    assert resolved.read_bytes() == b"lecture"


# ------------------------------------------------------ F07 map replacement
def _two_stage_map(root: Path) -> tuple[Path, dict]:
    """Give the demo unit a second stage, so a reversal is expressible."""
    import copy as _copy

    unit_dir = root / "curriculum/modules/module-demo/units/unit-demo-l01"
    map_path = unit_dir / "study-map.yaml"
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    data["plan_template_version"] = 1
    first = data["stages"][0]
    first.update(number=1, exam_critical=False, concepts=[], resources=[])
    second = _copy.deepcopy(first)
    second.update(id="stage-second", number=2, title="Second stage", status="pending")
    second["working_note"] = first["working_note"].replace("stage-demo/", "stage-second/")
    note = root / second["working_note"]
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("", encoding="utf-8")
    data["stages"].append(second)
    write_yaml(map_path, data)
    return map_path, data


def _revision(base: dict, tmp_path: Path, name: str, *, reverse: bool = False) -> Path:
    """A draft revision as the assembler writes one: no recorded state."""
    import copy as _copy

    revision = _copy.deepcopy(base)
    if reverse:
        revision["stages"].reverse()
    for number, stage in enumerate(revision["stages"], 1):
        stage["number"] = number
        stage["status"] = "pending"
        stage["attachments"] = []
        stage["source_feedback"] = []
        stage.pop("completed", None)
    revision["status"] = "ready"
    revision["current_stage"] = revision["stages"][0]["id"]
    path = tmp_path / name
    write_yaml(path, revision)
    return path


def test_map_replacement_refuses_a_silent_reorder(mini_repo: Path, tmp_path: Path):
    """F07: an authorized request still may not reshuffle reviewed stages."""
    add_curriculum(mini_repo)
    map_path, base = _two_stage_map(mini_repo)
    reversed_file = _revision(base, tmp_path, "reversed.yaml", reverse=True)

    applied = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l01", "--replace",
        "--file", str(reversed_file), "--file-sha256", file_sha256(reversed_file),
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-map-reversal-refused",
    )

    assert applied.returncode != 0
    assert "reorders existing stages" in applied.stdout + applied.stderr
    after = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in after["stages"]] == ["stage-demo", "stage-second"]


def test_map_replacement_preserves_progress_and_lifecycle(mini_repo: Path, tmp_path: Path):
    """F07: same-content replacement keeps the unit active and the work recorded."""
    add_curriculum(mini_repo)
    map_path, base = _two_stage_map(mini_repo)
    unit_dir = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    same = _revision(base, tmp_path, "same.yaml")

    applied = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l01", "--replace",
        "--file", str(same), "--file-sha256", file_sha256(same),
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-map-same-content",
    )

    assert applied.returncode == 0, applied.stderr
    after = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in after["stages"]] == ["stage-demo", "stage-second"]
    assert after["stages"][0]["status"] == "active"
    assert after["status"] == "active"
    assert after["current_stage"] == "stage-demo"
    unit = yaml.safe_load((unit_dir / "unit.yaml").read_text(encoding="utf-8"))
    assert unit["status"] == "active"


def test_map_replacement_allows_a_reviewed_reorder(mini_repo: Path, tmp_path: Path):
    """F07: the guarded path stays open when the reorder is declared."""
    add_curriculum(mini_repo)
    map_path, base = _two_stage_map(mini_repo)
    reversed_file = _revision(base, tmp_path, "reversed.yaml", reverse=True)

    applied = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l01", "--replace",
        "--file", str(reversed_file), "--file-sha256", file_sha256(reversed_file),
        "--intentional-reorder",
        "Scatterplots must precede the covariance computation they motivate.",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-map-declared-reorder",
    )

    assert applied.returncode == 0, applied.stderr
    after = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in after["stages"]] == ["stage-second", "stage-demo"]
    # A declared reorder is still not a licence to discard recorded work.
    assert {stage["id"]: stage["status"] for stage in after["stages"]} == {
        "stage-demo": "active", "stage-second": "pending",
    }


def test_map_replacement_refuses_to_drop_a_stage_silently(mini_repo: Path, tmp_path: Path):
    """F07: a disappearing stage takes evidence with it, so it must be declared."""
    add_curriculum(mini_repo)
    map_path, base = _two_stage_map(mini_repo)
    shortened = dict(base)
    shortened["stages"] = [base["stages"][0]]
    dropped = _revision(shortened, tmp_path, "dropped.yaml")

    refused = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l01", "--replace",
        "--file", str(dropped), "--file-sha256", file_sha256(dropped),
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-map-silent-drop",
    )
    assert refused.returncode != 0
    assert "stage-second" in refused.stdout + refused.stderr

    allowed = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l01", "--replace",
        "--file", str(dropped), "--file-sha256", file_sha256(dropped),
        "--retire-stage", "stage-second",
        "--retire-reason", "Merged into the first stage after review; no work recorded.",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-map-declared-drop",
    )
    assert allowed.returncode == 0, allowed.stderr
    after = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    assert [stage["id"] for stage in after["stages"]] == ["stage-demo"]
    assert after["current_stage"] == "stage-demo"


def test_map_replacement_check_mode_writes_nothing_and_shows_the_diff(
    mini_repo: Path, tmp_path: Path
):
    """F07: the concrete diff is available before any canonical application."""
    import json as _json

    add_curriculum(mini_repo)
    map_path, base = _two_stage_map(mini_repo)
    before = map_path.read_bytes()
    reversed_file = _revision(base, tmp_path, "reversed.yaml", reverse=True)

    checked = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l01", "--replace", "--check",
        "--file", str(reversed_file), "--file-sha256", file_sha256(reversed_file),
        "--intentional-reorder", "Reviewed pedagogical change.",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-map-check",
    )

    assert checked.returncode == 0, checked.stderr
    assert map_path.read_bytes() == before
    payload = _json.loads(checked.stdout)
    diff = payload["result"]["diff"] if "result" in payload else payload["diff"]
    assert diff["relative_order_changed"] is True
    assert diff["stages_before"] == ["stage-demo", "stage-second"]
    assert diff["stages_after"] == ["stage-second", "stage-demo"]
    assert diff["stages_retired"] == []
    assert yaml.safe_load(map_path.read_text(encoding="utf-8"))["stages"][0]["id"] \
        == "stage-demo"


# --------------------------------------------------- F06 shelving review packet
def test_shelving_packet_carries_unit_note_and_legacy_stage_note_once(
    mini_repo: Path, tmp_path: Path
):
    """F06: saved session reasoning reaches the review it was written for."""
    add_curriculum(mini_repo)
    session_text = "Session: I mixed up covariance and correlation on the second attempt."
    stage_text = "Legacy stage scratch: the normal equation derivation, step 3 failed."
    attachment = tmp_path / "worked-attempt.md"
    attachment.write_text("# worked attempt\n", encoding="utf-8")

    saved = approved_v2_cli(
        mini_repo, "unit-note", "unit-demo-l01", "--text", session_text,
        "--stage-id", "stage-demo",
        "--attachment", str(attachment), "--attachment-sha256", file_sha256(attachment),
        artifact_ids=["unit-demo-l01"], idempotency_key="audit-f06-unit-note",
    )
    assert saved.returncode == 0, saved.stderr
    legacy = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--text", stage_text,
        artifact_ids=["unit-demo-l01"],
        idempotency_key="audit-f06-stage-note",
    )
    assert legacy.returncode == 0, legacy.stderr

    prepared = approved_v2_cli(
        mini_repo, "shelving-prepare", "unit-demo-l01",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-f06-prepare",
    )
    assert prepared.returncode == 0, prepared.stderr

    packet = (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
              / "shelving-proposal.md").read_text(encoding="utf-8")
    assert packet.count(session_text) == 1
    assert packet.count(stage_text) == 1
    # Provenance: the section says which stage it was recorded against, and the
    # attachment saved with it is referenced.
    assert "stage-demo" in packet
    assert "worked-attempt.md" in packet


def test_shelving_packet_is_not_hidden_by_an_empty_stage_note(mini_repo: Path):
    """F06: a stage with nothing recorded must not displace session reasoning."""
    add_curriculum(mini_repo)
    session_text = "Session: the only place this reasoning exists."
    approved_v2_cli(
        mini_repo, "unit-note", "unit-demo-l01", "--text", session_text,
        artifact_ids=["unit-demo-l01"], idempotency_key="audit-f06-only-unit-note",
    )
    prepared = approved_v2_cli(
        mini_repo, "shelving-prepare", "unit-demo-l01",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-f06-empty-stage",
    )
    assert prepared.returncode == 0, prepared.stderr

    packet = (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
              / "shelving-proposal.md").read_text(encoding="utf-8")
    assert session_text in packet
    assert "*(No stage note yet.)*" not in packet


def test_shelving_prepare_does_not_create_durable_notes(mini_repo: Path):
    """F06 acceptance: preparing a packet never asserts mastery or shelves anything."""
    import yaml
    add_curriculum(mini_repo)
    before = sorted(p.name for p in (mini_repo / "knowledge" / "notes").glob("*"))
    approved_v2_cli(
        mini_repo, "unit-note", "unit-demo-l01", "--text", "Session reasoning.",
        artifact_ids=["unit-demo-l01"], idempotency_key="audit-f06-no-durable-note",
    )
    approved_v2_cli(
        mini_repo, "shelving-prepare", "unit-demo-l01",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="audit-f06-no-durable-prepare",
    )

    assert sorted(p.name for p in (mini_repo / "knowledge" / "notes").glob("*")) == before
    study_map = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
         / "study-map.yaml").read_text(encoding="utf-8"))
    assert study_map["shelving"]["state"] == "draft"


# ---------------------------------------------------- F01 route identity
def test_assembled_stage_resources_carry_route_identity():
    """F01: a stage resource keeps the id of the route it was assembled from."""
    import assemble_lecture_study_maps as assembler

    unit = {
        "id": "unit-demo-l01",
        "knowledge_map": {"nodes": [
            {"id": "knowledge-demo-a", "title": "A", "summary": "State A."},
        ]},
    }
    routes = [{
        "id": "route-demo-deck", "source_id": "source-demo-book",
        "unit_id": "unit-demo-l01", "title": "Course deck",
        "format": "course-material", "angle": "Notation used in the lecture.",
        "locator": "slides/VL 01.pdf", "covers": ["knowledge-demo-a"],
        "depth": "course-aligned", "scope": "current",
        "material_uri": "material://source-demo-book/slides/VL 01.pdf",
    }, {
        "id": "route-demo-setosa", "source_id": "source-setosa",
        "unit_id": "unit-demo-l01", "title": "Setosa visual explainer",
        "format": "course-material", "angle": "Interactive intuition.",
        "url": "https://setosa.io/ev/ordinary-least-squares-regression/",
        "covers": ["knowledge-demo-a"], "depth": "intuition", "scope": "complementary",
    }]

    record = assembler.build(unit, "module-demo", routes, {}, exam_bearing=False)
    resources = record["stages"][0]["resources"]

    assert [row["route_id"] for row in resources] == [
        "route-demo-deck", "route-demo-setosa"]
    # A web route's openable target survives assembly too.
    assert resources[1]["url"] == "https://setosa.io/ev/ordinary-least-squares-regression/"
    assert resources[0]["vault_path"] == "material://source-demo-book/slides/VL 01.pdf"


def test_assembly_refuses_a_stage_resource_without_route_identity():
    """F01: losing the id is a refusal, not a silently unopenable stage."""
    import assemble_lecture_study_maps as assembler

    unit = {
        "id": "unit-demo-l01",
        "knowledge_map": {"nodes": [
            {"id": "knowledge-demo-a", "title": "A", "summary": "State A."},
        ]},
    }
    routes = [{
        "source_id": "source-demo-book", "unit_id": "unit-demo-l01",
        "title": "Course deck", "format": "course-material",
        "angle": "Notation.", "locator": "slides/VL 01.pdf",
        "covers": ["knowledge-demo-a"], "depth": "course-aligned", "scope": "current",
    }]

    record = assembler.build(unit, "module-demo", routes, {}, exam_bearing=False)
    problems = assembler.assembly_problems(unit, routes, record)

    assert any("no route identity" in problem for problem in problems)


# ----------------------------------------------------- F13 repeated work
def test_dossier_projection_loads_the_repository_once_and_hashes_once(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """F13: many dossiers must not multiply repository loads or file hashes."""
    from learning_os import material_synthesis
    from learning_os.genout import build_manifest
    from learning_os.loader import load_repo
    from learning_os.routes import deterministic_route_id

    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)

    materials = mini_repo.parent / "materials" / "source-demo-book"
    materials.mkdir(parents=True, exist_ok=True)
    (materials / "lecture-01.pdf").write_bytes(b"one shared deck")

    # Two routes on one unit, both reaching the same file: the shape that made
    # the old code hash the same bytes once per route.
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    first = source_map["sources"][0]["unit_routes"][0]
    second = dict(first)
    second["title"] = "Demo book — worked example"
    second["angle"] = "Works the discrete example in full."
    source_map["sources"][0]["unit_routes"] = [first, second]
    for route in source_map["sources"][0]["unit_routes"]:
        route["id"] = deterministic_route_id("module-demo", "source-demo-book", route)
    write_yaml(source_map_path, source_map)

    basis = material_synthesis.current_unit_material_basis(mini_repo, "unit-demo-l01")
    assert len(basis["material_checksums"]) == 2
    assert len(set(basis["material_checksums"].values())) == 1, \
        "two routes onto one file share one checksum"

    write_yaml(
        mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
        / "material-synthesis.yaml",
        {
            "schema_version": 1,
            "id": "material-synthesis-demo-l01",
            "type": "unit-material-synthesis",
            "unit_id": "unit-demo-l01",
            "status": "approved",
            "basis": {
                **basis,
                "ai_provenance": {
                    "request_id": "request-demo",
                    "delivery_id": "delivery-demo",
                    "provider": "local",
                },
            },
            "route_assessments": [
                {
                    "route_id": route_id,
                    "source_id": "source-demo-book",
                    "locator": "lecture-01.pdf",
                    "review_status": "deep-reviewed",
                    "concept_ids": ["concept-expected-value"],
                    "contribution": "Derives the weighted sum.",
                    "assumptions": "Discrete outcomes are defined.",
                    "notation": "Uses E[X].",
                    "exercise_value": "One worked calculation.",
                    "best_for": "Rebuilding the derivation.",
                    "limitations": "No continuous variables.",
                    "evidence": [{
                        "locator": "lecture-01.pdf",
                        "checksum": basis["material_checksums"][route_id],
                    }],
                }
                for route_id in basis["material_checksums"]
            ],
            "comparisons": [],
            "concept_groups": [],
        },
    )

    loads: list[str] = []
    hashed: list[bytes] = []
    real_load = material_synthesis.load_repo
    real_hash = material_synthesis._sha256_bytes

    def counted_load(root, *args, **kwargs):
        loads.append(str(root))
        return real_load(root, *args, **kwargs)

    def counted_hash(value: bytes) -> str:
        hashed.append(value)
        return real_hash(value)

    monkeypatch.setattr(material_synthesis, "load_repo", counted_load)
    monkeypatch.setattr(material_synthesis, "_sha256_bytes", counted_hash)

    repo = load_repo(mini_repo)
    manifest = build_manifest(repo, "T1")

    assert manifest["unit_material_syntheses"], "the dossier is projected"
    assert loads == [], \
        "projection passes its loaded repository in; the service reloads nothing"
    assert hashed.count(b"one shared deck") == 1, \
        "one file is hashed once per build, however many routes reach it"


# ------------------------------------------------- F14 operator runbooks
def test_an_unindexed_operator_skill_is_an_error():
    """F14: a skill is a runbook, so leaving it unclassified is where drift hid."""
    import json as _json

    import yaml as _yaml

    from learning_os.contracts import normative_corpus as nc

    assert "system/skills/*/SKILL.md" in nc.CORPUS_GLOBS

    root = Path(__import__("tempfile").mkdtemp())
    (root / "system" / "contracts").mkdir(parents=True)
    schema = (Path(__file__).resolve().parents[1] / nc.SCHEMA_RELATIVE)
    (root / nc.SCHEMA_RELATIVE).write_text(schema.read_text(encoding="utf-8"),
                                           encoding="utf-8")
    (root / "system" / "OPERATOR.md").write_text("# operator\n", encoding="utf-8")
    (root / "system" / "skills" / "demo").mkdir(parents=True)
    (root / "system" / "skills" / "demo" / "SKILL.md").write_text(
        "# demo skill\n", encoding="utf-8")
    entry = {
        "path": "system/OPERATOR.md", "class": "contract", "status": "current",
        "authority": "binding", "owner": "test", "summary": "the contract",
    }
    (root / nc.CORPUS_RELATIVE).write_text(
        _yaml.safe_dump({"corpus_version": 1, "entrypoint": "system/OPERATOR.md",
                         "documents": [entry]}, sort_keys=False),
        encoding="utf-8")

    unindexed = nc.check(root)
    assert {issue.code for issue in unindexed} == {"MISSING"}
    assert any(issue.path == "system/skills/demo/SKILL.md" for issue in unindexed)

    # Classifying it clears the gate; the schema admits the skill path shape.
    skill_entry = {
        "path": "system/skills/demo/SKILL.md", "class": "adapter",
        "status": "current", "authority": "binding", "owner": "test",
        "summary": "a runbook",
    }
    (root / nc.CORPUS_RELATIVE).write_text(
        _yaml.safe_dump({"corpus_version": 1, "entrypoint": "system/OPERATOR.md",
                         "documents": [entry, skill_entry]}, sort_keys=False),
        encoding="utf-8")
    assert nc.check(root) == []
    assert _json.loads(schema.read_text(encoding="utf-8"))  # schema stays valid JSON


def test_the_shipped_operator_skills_are_classified_and_agree_with_the_contract():
    """F14: the three verified contradictions, pinned where they were found."""
    from learning_os.contracts import normative_corpus as nc

    root = Path(__file__).resolve().parents[1]
    assert nc.check(root) == []

    corpus = nc.load(root)
    indexed = {doc.path for doc in corpus.documents}
    for skill in sorted(root.glob("system/skills/*/SKILL.md")):
        assert str(skill.relative_to(root)) in indexed

    builder = (root / "system/skills/lecture-unit-builder/SKILL.md").read_text(
        encoding="utf-8")
    # The declared entry point is OPERATOR.md; CLAUDE.md is its adapter.
    assert "`system/OPERATOR.md`" in builder
    assert "(the operating contract)" not in builder
    # The acceptance gate is rule 13, not a stricter local one.
    assert "0 errors, 0 warnings" not in builder
    assert "warning_baseline.py --check" in builder
    # Whether a unit owes a map is the producer's answer, not a preference.
    assert "needs_study_map" in builder
    assert "A `study-map.yaml` is optional" not in builder


def test_the_sop_and_the_contract_agree_on_where_a_draft_goes():
    """F14: the SOP wrote drafts into a canonical root without saying so."""
    import re

    raw = (Path(__file__).resolve().parents[1]
           / "system/PLAN-CREATION-SOP.md").read_text(encoding="utf-8")
    # The prose is hard-wrapped, so compare on collapsed whitespace.
    sop = re.sub(r"\s+", " ", raw)
    assert "OPERATOR rule 16 owns this" in sop
    assert "moves the snapshot" in sop
    assert "Capture `snapshot.snapshot_id` after the draft" in sop
    # And the fact that makes the ordering necessary is itself checkable:
    from learning_os.fingerprint import CANONICAL_ROOTS
    assert "work" in CANONICAL_ROOTS
