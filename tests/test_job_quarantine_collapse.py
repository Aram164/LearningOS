"""The one-time Job learning collapse is deterministic, lossless, and atomic."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_envelope, run_v2_capability
from materials_manifest import render_manifest
from migrations.job_quarantine_collapse import (
    MATERIAL_SPECS,
    PLAN_SPECS,
    migration_artifact_ids,
    plan_migration,
    plan_sha256,
    verify_plan_inputs,
)
from repo_builders import add_curriculum

from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo
from learning_os.rules import validate

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = ROOT / "tools/migrations/job_quarantine_collapse.py"


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _write_note(path: Path, note_id: str, *, legacy_concept: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    concept = "aggregation" if legacy_concept else "concept-skrub"
    path.write_text(
        "\n".join((
            "---",
            f"id: {note_id}",
            "type: note",
            f"title: Synthetic {note_id}",
            "created: '2026-08-01'",
            "role: reference",
            "state: evolving",
            "authorship: aram",
            f"concepts: [{concept}]",
            "sources: []",
            "component: stratum/synthetic.py",
            "verified_against: abcdef0",
            "status: current",
            "---",
            "",
            f"# {note_id}",
            "",
            "Authored body stays byte-for-byte below the frontmatter.",
            "",
        )),
        encoding="utf-8",
    )


def _ensure_concept_skrub(root: Path) -> None:
    path = root / "knowledge/concepts.yaml"
    if path.is_file():
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        value = {"concepts": []}
    if not any(row.get("id") == "concept-skrub" for row in value["concepts"]):
        value["concepts"].append({
            "id": "concept-skrub",
            "label": "skrub DataOps",
            "description": "Boundary marker for notes quarantined in Job/.",
        })
    rendered = ["concepts:"]
    for record in value["concepts"]:
        block = yaml.safe_dump(
            [record], sort_keys=False, allow_unicode=True,
        ).rstrip().splitlines()
        rendered.extend(f"  {line}" for line in block)
    path.write_text("\n".join(rendered) + "\n", encoding="utf-8")


def _stage(spec_index: int, plan_slug: str) -> dict:
    return {
        "id": f"stage-{plan_slug}-01",
        "number": 1,
        "title": f"Synthetic stage {spec_index}",
        "status": "pending",
        "objective": "Preserve one exact learning objective.",
        "done_when": ["The evidence is recorded without declaring mastery."],
        "estimate_minutes": 30,
        "exam_critical": False,
        "concepts": [],
        "scope_triage": "required-now",
        "resources": [{
            "id": f"resource-{plan_slug}-01",
            "kind": "read",
            "label": "Synthetic source-independent resource",
            "locator": "Exact authored locator",
            "scope_triage": "required-now",
        }],
        "attachments": [],
        "source_feedback": [],
        "job_context": {
            "mental_models": [{
                "label": "Synthetic model",
                "text": "The authored mental model is preserved as prose.",
            }],
            "read_only_anchor": "stratum/synthetic.py is an optional anchor.",
            "component": ["stratum/synthetic.py"],
            "verified_against": "abcdef0",
        },
    }


def _prepare_fixture(root: Path) -> Path:
    """Add the exact bounded legacy inventory around a LearningOS-shaped root."""

    learning_os = root.parent
    job_root = learning_os / "legacy" / "Job"
    materials = learning_os / "materials"
    materials.mkdir(parents=True, exist_ok=True)

    _ensure_concept_skrub(root)
    _write_yaml(root / "sources/registry/software.yaml", {"sources": []})
    _write_yaml(root / "records/materials-manifest.yaml", {
        "schema_version": 1,
        "captured": "2026-08-01",
        "totals": {"files": 0, "bytes": 0},
        "files": {},
    })
    _write_yaml(root / "curriculum/programs/program-job-boundary.yaml", {
        "id": "program-job-boundary",
        "type": "program",
        "title": "Job",
        "kind": "boundary",
        "status": "boundary-only",
        "default": False,
        "semester_bound": False,
        "description": "Synthetic legacy boundary.",
    })

    for index, spec in enumerate(PLAN_SPECS, start=1):
        slug = spec.plan_id.removeprefix("job-track-")
        _write_yaml(job_root / "plans" / spec.filename, {
            "type": "job-learning-plan",
            "plan_template_version": 1,
            "id": spec.plan_id,
            "title": f"{spec.module_title} learning",
            "status": "ready",
            "horizon": "Ongoing",
            "cadence": "One deliberate session at a time",
            "outcome": "Retain the authored learning outcome.",
            "stages": [_stage(index, slug)],
        })

    note_specs = [
        (Path("note-skrub-alpha.md"), "note-skrub-alpha"),
        (Path("note-skrub-beta.md"), "note-skrub-beta"),
        (
            Path("dataframe-semantics/note-pandas-groupby-signatures.md"),
            "note-pandas-groupby-signatures",
        ),
        (
            Path("dataframe-semantics/note-pandas-polars-aggregation-contentions.md"),
            "note-pandas-polars-aggregation-contentions",
        ),
        *[
            (
                Path(f"stratum/dataframe-ops/note-stratum-synthetic-{index:02d}.md"),
                f"note-stratum-synthetic-{index:02d}",
            )
            for index in range(1, 15)
        ],
        (Path("stratum/note-stratum-synthetic-overview.md"), "note-stratum-synthetic-overview"),
    ]
    assert len(note_specs) == 19
    for index, (relative, note_id) in enumerate(note_specs):
        _write_note(
            job_root / "notes" / relative,
            note_id,
            legacy_concept=index == 0,
        )
    for index in range(1, 9):
        probe = job_root / "notes/dataframe-semantics/probes" / f"probe_{index}.py"
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text(f"# preserved probe {index}\n", encoding="utf-8")

    source_bytes = {
        "LearningOS/python-polars-the-definitive-guide.pdf": b"polars-pdf\n",
        "Job/papers/stratum-paper.pdf": b"stratum-paper\n",
        "Job/legacy-plans/Towards Scalable Dataframe Systems.pdf": b"dataframe-paper\n",
    }
    for source_id, source_label, target_relative in MATERIAL_SPECS:
        source = (
            learning_os.parent / source_label
            if source_label.startswith("LearningOS/")
            else job_root / source_label.removeprefix("Job/")
        )
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(source_bytes[source_label])
        target = materials / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_bytes[source_label])
        flat = materials / ".flat" / source_id
        flat.parent.mkdir(parents=True, exist_ok=True)
        flat.symlink_to(target.parent, target_is_directory=True)
    return job_root


def _apply_plan_for_idempotence(plan) -> None:
    for change in plan.changes:
        change.path.parent.mkdir(parents=True, exist_ok=True)
        change.path.write_text(change.after, encoding="utf-8")
    for deletion in plan.deletions:
        deletion.path.unlink()


def test_planner_is_deterministic_lossless_and_idempotent(mini_repo: Path):
    job_root = _prepare_fixture(mini_repo)

    first = plan_migration(mini_repo)
    second = plan_migration(mini_repo)

    assert first.ready and second.ready
    assert first.statistics == {
        "plans": 5, "stages": 5, "resources": 5, "notes": 19, "probes": 8,
    }
    assert len(first.changes) == 62
    assert len(first.deletions) == 1
    assert len(migration_artifact_ids(first)) == 71
    assert plan_sha256(first) == plan_sha256(second)
    assert verify_plan_inputs(first) == ()

    by_path = {
        change.path.relative_to(mini_repo).as_posix(): change.after
        for change in first.changes
    }
    program = yaml.safe_load(by_path["curriculum/programs/program-job.yaml"])
    assert (program["kind"], program["status"]) == ("skills", "active")
    assert "job_context" not in by_path[
        "curriculum/modules/module-job-git/units/unit-job-git-fluency/study-map.yaml"
    ]
    assert "LearningOS does not index, validate, manage, or write" in by_path[
        "curriculum/modules/module-job-git/units/unit-job-git-fluency/"
        "stages/stage-git-01/notes.md"
    ]
    migrated_note = by_path[
        "knowledge/notes/data-systems/skrub/note-skrub-alpha.md"
    ]
    assert "authorship: user" in migrated_note
    assert "concepts: [concept-aggregation]" in migrated_note
    assert "Authored body stays byte-for-byte" in migrated_note
    assert "## Legacy Job provenance" in migrated_note
    attachment_note = by_path[
        "knowledge/notes/data-systems/dataframe-semantics/"
        "note-pandas-polars-aggregation-contentions.md"
    ]
    attachment_meta = yaml.safe_load(attachment_note.split("---\n", 2)[1])
    assert attachment_meta["attachments"] == [
        "knowledge/attachments/note-pandas-polars-aggregation-contentions/"
        f"probe_{index}.py"
        for index in range(1, 9)
    ]
    assert not (job_root / "notes/note-skrub-alpha.md").read_text().startswith(
        "---\nid: altered"
    )

    relations_before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    _apply_plan_for_idempotence(first)
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == relations_before
    material_manifest_path = mini_repo / "records/materials-manifest.yaml"
    rebuilt_material_manifest = yaml.safe_load(
        material_manifest_path.read_text(encoding="utf-8")
    )
    rebuilt_material_manifest["captured"] = "2026-08-27"
    # Stand in for a later `make inventory`, which means its renderer — not a
    # local yaml.safe_dump. The inventory has exactly one canonical byte form
    # (materials_manifest.render_manifest); a fixture that wrote its own would
    # prove idempotence against bytes the real system never produces.
    material_manifest_path.write_text(
        render_manifest(rebuilt_material_manifest), encoding="utf-8",
    )
    repeated = plan_migration(mini_repo)
    assert repeated.ready
    assert repeated.changes == ()
    assert repeated.deletions == ()
    assert "ATTACH-ORPHAN" not in {
        issue.code for issue in validate(load_repo(mini_repo))
    }


def test_source_drift_and_destination_collisions_fail_closed(mini_repo: Path):
    _prepare_fixture(mini_repo)
    plan = plan_migration(mini_repo)
    assert plan.ready

    source = mini_repo.parent / "legacy/Job/plans/job-track-git.yaml"
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert {problem.code for problem in verify_plan_inputs(plan)} == {"source-drift"}

    _write_yaml(mini_repo / "curriculum/programs/program-job.yaml", {"wrong": True})
    collided = plan_migration(mini_repo)
    assert not collided.ready
    assert "destination-collision" in {problem.code for problem in collided.problems}


def test_direct_apply_is_refused(mini_repo: Path):
    _prepare_fixture(mini_repo)
    result = subprocess.run(
        [sys.executable, str(MIGRATION), "--root", str(mini_repo), "--apply"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "legacy.job-learning.migrate GatewayEnvelopeV2" in result.stdout
    assert not (mini_repo / "curriculum/programs/program-job.yaml").exists()


def test_gateway_commits_the_whole_collapse_once(mini_repo: Path):
    add_curriculum(mini_repo)
    _prepare_fixture(mini_repo)
    plan = plan_migration(mini_repo)
    artifacts = migration_artifact_ids(plan)
    snapshot_before = f"sha256:{canonical_fingerprint(mini_repo)}"

    direct = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/los.py"),
            "--root", str(mini_repo),
            "job-learning-migrate",
            "--plan-sha256", plan_sha256(plan),
            "--approve",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert direct.returncode == 2
    assert "GatewayEnvelopeV2" in direct.stderr

    envelope = approved_v2_envelope(
        mini_repo,
        capability="legacy.job-learning.migrate",
        payload={"plan_sha256": plan_sha256(plan)},
        artifact_ids=artifacts,
        idempotency_key="job-learning-collapse-001",
        expected_snapshot=snapshot_before,
    )
    applied = run_v2_capability(mini_repo, envelope)
    assert applied.returncode == 0, applied.stderr or applied.stdout
    response = json.loads(applied.stdout)
    result = response["result"]
    assert response["ok"] is True
    assert result["statistics"] == {
        "notes": 19, "plans": 5, "probes": 8, "resources": 5, "stages": 5,
    }
    assert result["deleted_files"] == [
        "curriculum/programs/program-job-boundary.yaml"
    ]
    receipt = yaml.safe_load(
        (mini_repo / response["receipt_path"]).read_text(encoding="utf-8")
    )
    assert receipt["capability"] == "legacy.job-learning.migrate"
    receipt_writes = {row["path"] for row in receipt["writes"]}
    assert receipt_writes - set(result["changed_files"]) == set(result["deleted_files"])
    assert set(result["changed_files"]) <= receipt_writes
    boundary_row = next(
        row for row in receipt["writes"]
        if row["path"] == "curriculum/programs/program-job-boundary.yaml"
    )
    assert boundary_row["sha256_before"]
    assert boundary_row["sha256_after"] is None
    assert boundary_row["created"] is False
    assert set(receipt["artifact_revisions"]) == set(artifacts)
    assert (mini_repo / "curriculum/programs/program-job.yaml").is_file()
    assert not (mini_repo / "curriculum/programs/program-job-boundary.yaml").exists()
    assert len(list((mini_repo / "curriculum/modules").glob("module-job-*"))) == 5
    assert plan_migration(mini_repo).changes == ()

    replayed = run_v2_capability(mini_repo, envelope)
    assert replayed.returncode == 0, replayed.stderr or replayed.stdout
    assert json.loads(replayed.stdout)["replayed"] is True


@pytest.mark.full_repo
def test_applied_real_migration_provenance_and_receipt_are_stable(repo_root: Path):
    """The applied migration is proved without reopening quarantined Job data.

    Raw-source planning, inventory, drift, and idempotence stay covered by the
    synthetic tests above.  Once the live migration is applied, the normal
    suite must treat its approved provenance and append-only receipt as the
    evidence boundary; consulting ``legacy/Job`` again would defeat the
    quarantine the migration established.
    """

    provenance = repo_root / "operations/migrations/job-quarantine-collapse-v1.yaml"
    if not provenance.is_file():
        return  # a standalone/pre-migration clone is covered by synthetic fixtures

    provenance_bytes = provenance.read_bytes()
    applied = yaml.safe_load(provenance_bytes)
    assert {
        key: applied[key]
        for key in ("schema_version", "id", "type", "status", "application")
    } == {
        "schema_version": 1,
        "id": "job-quarantine-collapse-v1",
        "type": "migration-provenance",
        "status": "applied",
        "application": "legacy.job-learning.migrate via GatewayEnvelopeV2",
    }
    assert applied["statistics"] == {
        "plans": 5,
        "stages": 93,
        "resources": 1051,
        "notes": 19,
        "probes": 8,
    }
    assert applied["plans"] == [
        {
            "source": f"Job/plans/{spec.filename}",
            "module_id": spec.module_id,
            "unit_id": spec.unit_id,
            "study_map_id": spec.study_map_id,
        }
        for spec in PLAN_SPECS
    ]

    source_files = applied["source_files"]
    assert set(source_files) == {"plans", "notes", "probes", "materials"}
    # Every material spec is snapshotted twice — once at its legacy source and
    # once at the prepared `materials/` destination — so the material row count
    # is two per spec, not one.
    assert {key: len(value) for key, value in source_files.items()} == {
        "plans": len(PLAN_SPECS),
        "notes": 19,
        "probes": 8,
        "materials": 2 * len(MATERIAL_SPECS),
    }
    assert {
        row["path"]: (row["size"], row["sha256"])
        for row in source_files["plans"]
    } == {
        "Job/plans/job-track-git.yaml": (
            93946,
            "5939d91dbfe74cf0a86ccfe8c8f7f06c441103bbc06d6c3447f4e66b5cb48225",
        ),
        "Job/plans/job-track-missing-semester.yaml": (
            118219,
            "de7553ea72784d11861d17d89f75d886f502df4b5d16d1684ffb10aa96e904f8",
        ),
        "Job/plans/job-track-polars.yaml": (
            115766,
            "81804fc5f761bc9f0a50b1ef8821a23f9c96b1b54eb7d57d2ed3697e408af0d2",
        ),
        "Job/plans/job-track-python.yaml": (
            131364,
            "4f5e9e37a414e294e2d60af18353b7119d3840916c160818b4f5a87806aa5dbe",
        ),
        "Job/plans/job-track-rust.yaml": (
            50256,
            "491e5e498e824fabe87f3f2ef47ed0271715e2fbf3f77b9b214c876a7c5f7b8e",
        ),
    }

    provenance_sha256 = hashlib.sha256(provenance_bytes).hexdigest()
    assert provenance_sha256 == (
        "f4b6a8b8dbcef9e4ddebd335ae0e60139c0aa24d9ef40f715e972612ba717a5e"
    )
    receipt_path = (
        repo_root
        / "operations/transactions/transaction-20260826-232920-001.yaml"
    )
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    assert {
        key: receipt[key]
        for key in ("schema_version", "id", "type", "status", "capability")
    } == {
        "schema_version": 2,
        "id": "transaction-20260826-232920-001",
        "type": "transaction-receipt",
        "status": "committed",
        "capability": "legacy.job-learning.migrate",
    }
    assert receipt["authority"]["enforced"] is True
    assert receipt["request"]["approval"]["subject_sha256"] == (
        receipt["request"]["intent_sha256"]
    )
    assert len(receipt["writes"]) == 151
    assert len(receipt["artifact_revisions"]) == 159
    assert len({row["path"] for row in receipt["writes"]}) == 151

    provenance_row = next(
        row for row in receipt["writes"]
        if row["path"] == "operations/migrations/job-quarantine-collapse-v1.yaml"
    )
    assert provenance_row == {
        "path": "operations/migrations/job-quarantine-collapse-v1.yaml",
        "sha256_before": None,
        "sha256_after": provenance_sha256,
        "created": True,
    }
    boundary_row = next(
        row for row in receipt["writes"]
        if row["path"] == "curriculum/programs/program-job-boundary.yaml"
    )
    assert boundary_row["sha256_before"]
    assert boundary_row["sha256_after"] is None
    assert boundary_row["created"] is False
