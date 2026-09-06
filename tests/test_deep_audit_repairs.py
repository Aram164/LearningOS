"""Regression pins for the 2026-08-25 deep system repair."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from learning_os.commands import support as command_support
from learning_os.genout import common as genout_common
from learning_os.genout.materials import _material_location, _safe_material_locator
from learning_os.genout.outputs import write_outputs
from learning_os.genout.projection.records_curriculum import project_units
from learning_os.genout.projection.stages import project_stages
from learning_os.loader import load_repo
from learning_os.loading.model import Repo, Unit
from learning_os.loading.yamlio import LoaderError, _load_yaml, parse_frontmatter
from learning_os.rules import validate
from learning_os.transactions import TransactionFailure, load_revisions


def issue_codes(root: Path, severity: str = "E") -> list[str]:
    return [
        issue.code for issue in validate(load_repo(root))
        if issue.severity == severity
    ]


def test_material_locator_accepts_slide_counts_but_rejects_compounds():
    assert _safe_material_locator("slides/L03.pdf, 48 slides") == "slides/L03.pdf"
    assert _safe_material_locator("slides/L06.pdf (60 slides)") == "slides/L06.pdf"
    assert _safe_material_locator("slides/L03.pdf; slides/L06.pdf") is None
    assert _safe_material_locator("../outside.pdf, 12 pages") is None


def test_material_location_refuses_symlink_escape_to_external_directory(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    materials = mini_repo.parent / "materials"
    materials.mkdir(exist_ok=True)
    external = mini_repo.parent.parent / "external-code"
    external.mkdir()
    (external / "sealed.pdf").write_bytes(b"EXTERNAL SENTINEL")
    (materials / "escape").symlink_to(external, target_is_directory=True)

    real_stat = os.stat
    real_lstat = os.lstat

    def refuse_external(path, *args, **kwargs):
        if isinstance(path, (str, bytes, os.PathLike)) \
                and "external-code" in Path(os.fsdecode(path)).parts:
            raise AssertionError("material resolution touched an external directory")

    def guarded_stat(path, *args, **kwargs):
        refuse_external(path)
        return real_stat(path, *args, **kwargs)

    def guarded_lstat(path, *args, **kwargs):
        refuse_external(path)
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", guarded_stat)
    monkeypatch.setattr(os, "lstat", guarded_lstat)

    location = _material_location(
        load_repo(mini_repo), "material://escape/sealed.pdf"
    )

    assert location == {"material_path": None, "material_exists": False}


def test_material_location_allows_flat_alias_that_stays_inside_materials(
    mini_repo: Path,
):
    materials = mini_repo.parent / "materials"
    physical = materials / "mathematics" / "source-demo"
    physical.mkdir(parents=True, exist_ok=True)
    (physical / "lecture.pdf").write_bytes(b"synthetic lecture")
    flat = materials / ".flat"
    flat.mkdir(exist_ok=True)
    (flat / "source-demo").symlink_to(physical, target_is_directory=True)

    location = _material_location(
        load_repo(mini_repo), "material://source-demo/lecture.pdf"
    )

    assert location == {
        "material_path": "materials/mathematics/source-demo/lecture.pdf",
        "material_exists": True,
    }


def test_yaml_and_frontmatter_reject_duplicate_explicit_keys(tmp_path: Path):
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text("id: first\nid: second\n", encoding="utf-8")
    with pytest.raises(LoaderError, match="duplicate key"):
        _load_yaml(duplicate, tmp_path)

    note = tmp_path / "note.md"
    text = "---\nid: note-first\nid: note-second\n---\n\nBody\n"
    with pytest.raises(LoaderError, match="duplicate key"):
        parse_frontmatter(text, note)


def test_loader_refuses_markdown_symlink_outside_authority(mini_repo: Path):
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    outside = mini_repo.parent / "outside-note.md"
    outside.write_text("SECRET SENTINEL\n", encoding="utf-8")
    note.unlink()
    note.symlink_to(outside)

    repo = load_repo(mini_repo)
    assert "note-demo" not in repo.notes
    assert any("escapes" in message for _path, message in repo.parse_failures)


def test_duplicate_parent_does_not_contribute_unique_children(mini_repo: Path):
    modules = mini_repo / "curriculum/modules"
    first = modules / "a-module"
    duplicate = modules / "b-module"
    first.mkdir(parents=True)
    (duplicate / "units/unit-from-duplicate").mkdir(parents=True)
    (first / "module.yaml").write_text(
        "id: module-duplicate\ntype: module\ntitle: First\n", encoding="utf-8"
    )
    (duplicate / "module.yaml").write_text(
        "id: module-duplicate\ntype: module\ntitle: Duplicate\n", encoding="utf-8"
    )
    (duplicate / "units/unit-from-duplicate/unit.yaml").write_text(
        "id: unit-from-duplicate\ntype: unit\nmodule_id: module-duplicate\n"
        "title: Hidden child\nstatus: active\n",
        encoding="utf-8",
    )

    repo = load_repo(mini_repo)
    assert "unit-from-duplicate" not in repo.units
    assert ("module", "module-duplicate") in {
        (family, record_id) for family, record_id, _path in repo.duplicate_ids
    }


def test_projection_never_reads_out_of_root_working_notes(tmp_path: Path):
    root = tmp_path / "repository"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("SECRET SENTINEL\n", encoding="utf-8")
    repo = Repo(root=root)
    repo.modules["module-demo"] = {"id": "module-demo", "status": "enrolled"}
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo/unit.yaml"
    repo.units["unit-demo"] = Unit(
        "unit-demo",
        unit_path,
        {
            "id": "unit-demo",
            "type": "unit",
            "module_id": "module-demo",
            "working_note": "../outside.md",
        },
        "module-demo",
    )
    [unit] = project_units(repo, lambda *_args: 0, {})
    assert unit["notes_text"] == ""

    [stage] = project_stages(
        repo,
        {"stages": [{"id": "stage-demo", "notes_path": "../outside.md"}]},
        "notes_path",
    )
    assert stage["notes_text"] == ""


def test_generated_symlink_is_refused_before_any_publication(mini_repo: Path):
    generated = mini_repo / "generated"
    marker = generated / "marker.md"
    marker.write_text("original\n", encoding="utf-8")
    outside = mini_repo.parent / "outside-generated"
    outside.mkdir()
    (generated / "collections").symlink_to(outside, target_is_directory=True)

    with pytest.raises(TransactionFailure, match="symbolic link"):
        write_outputs(
            load_repo(mini_repo),
            {
                "collections/probe.md": "new\n",
                "manifest.json": "{}\n",
            },
        )
    assert marker.read_text(encoding="utf-8") == "original\n"
    assert not (outside / "probe.md").exists()


def test_git_dirty_state_covers_every_canonical_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    commands: list[list[str]] = []

    def run(command, **_kwargs):
        commands.append(list(command))
        return SimpleNamespace(stdout="deadbeef\n" if command[1] == "rev-parse" else "",
                               stderr="", returncode=0)

    monkeypatch.setattr(genout_common.subprocess, "run", run)
    assert genout_common._git_state(tmp_path) == ("deadbeef", False)
    status = next(command for command in commands if command[1] == "status")
    for canonical_root in genout_common.CANONICAL_ROOTS:
        assert canonical_root in status


def test_invalid_schema_and_escaping_link_are_reported_not_crashed(mini_repo: Path):
    schema = mini_repo / "system/schema/note.schema.json"
    schema.write_text("{", encoding="utf-8")
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(
        note.read_text(encoding="utf-8")
        + "\n[escape](../../../../outside.md)\n",
        encoding="utf-8",
    )
    codes = issue_codes(mini_repo)
    assert "SCHEMA-UNREADABLE" in codes
    assert "LINK-ESCAPE" in codes


def test_revision_ledger_damage_fails_closed_and_is_reported(mini_repo: Path):
    ledger = mini_repo / "operations/transactions/revisions.yaml"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        "schema_version: 1\ntype: artifact-revision-ledger\nrevisions:\n"
        "  unit-demo: nope\n",
        encoding="utf-8",
    )
    with pytest.raises(TransactionFailure, match="invalid row"):
        load_revisions(mini_repo)
    assert "TRANSACTION-REVISIONS" in issue_codes(mini_repo)


def test_session_ownership_state_detects_post_transaction_edits(mini_repo: Path):
    target = mini_repo / "work/inbox/session-note.md"
    target.write_text("recorded\n", encoding="utf-8")
    command_support._record_touched(mini_repo, [target])
    recorded = command_support._load_session_paths(mini_repo)
    assert command_support._session_path_state(
        mini_repo, "work/inbox/session-note.md"
    ) == recorded["work/inbox/session-note.md"]
    target.write_text("edited elsewhere\n", encoding="utf-8")
    assert command_support._session_path_state(
        mini_repo, "work/inbox/session-note.md"
    ) != recorded["work/inbox/session-note.md"]
