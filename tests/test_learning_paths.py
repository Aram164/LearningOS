"""Learning-path workflow, contract versioning, and guarded writes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call, file_sha256

from learning_os.contracts.manifest_contract import declared_version
from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo
from learning_os.rules import validate

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def run_los(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        capture_output=True, text=True, timeout=120)


def add_path(root: Path) -> Path:
    ws = root / "work" / "active" / "workspace-demo"
    path_file = ws / "paths" / "path-demo-probability.yaml"
    path_file.parent.mkdir(parents=True)
    path_file.write_text(yaml.safe_dump({
        "id": "path-demo-probability",
        "type": "learning-path",
        "title": "Demo probability",
        "workspace_id": "workspace-demo",
        "area": "university",
        "module_id": "module-demo",
        "status": "active",
        "current_stage": "stage-one",
        "created": "2026-08-03",
        "stages": [
            {"id": "stage-one", "title": "One", "status": "active",
             "objective": "Do one.", "concepts": ["concept-expected-value"],
             "resources": [{"kind": "read", "label": "Demo Book",
                            "source_id": "source-demo-book"}],
             "done_when": ["Explain one."],
             "notes_path": "work/active/workspace-demo/scratch/paths/"
                           "path-demo-probability/stage-one.md"},
            {"id": "stage-two", "title": "Two", "status": "pending",
             "objective": "Do two.", "done_when": ["Explain two."],
             "notes_path": "work/active/workspace-demo/scratch/paths/"
                           "path-demo-probability/stage-two.md"},
        ],
    }, sort_keys=False), encoding="utf-8")
    return path_file


def _path_note(
    root: Path,
    *,
    text: str,
    key: str,
    expected_snapshot: str | None = None,
):
    return approved_v2_call(
        root,
        capability="path.note.write",
        payload={
            "path_id": "path-demo-probability",
            "stage_id": "stage-one",
            "replace": True,
            "text": text,
        },
        artifact_ids=["path-demo-probability"],
        idempotency_key=key,
        expected_snapshot=expected_snapshot,
    )


def _path_progress(root: Path, stage_id: str, *, key: str):
    return approved_v2_call(
        root,
        capability="path.progress.update",
        payload={
            "path_id": "path-demo-probability",
            "stage_id": stage_id,
            "status": "complete",
        },
        artifact_ids=["path-demo-probability"],
        idempotency_key=key,
    )


def test_path_loads_validates_and_projects_stage_notes(mini_repo):
    add_path(mini_repo)
    repo = load_repo(mini_repo)
    assert "path-demo-probability" in repo.learning_paths
    assert not [i for i in validate(repo) if i.severity == "E"]

    note = mini_repo / "work/active/workspace-demo/scratch/paths/" \
        "path-demo-probability/stage-one.md"
    note.parent.mkdir(parents=True)
    note.write_text("My uncertain derivation.\n", encoding="utf-8")
    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    path_rec = next(r for r in manifest["records"] if r["id"] == "path-demo-probability")
    assert path_rec["stages"][0]["notes_text"] == "My uncertain derivation.\n"
    assert path_rec["stages"][1]["resources"] == []
    assert manifest["_generated"]["contract_version"] == declared_version(mini_repo)
    assert manifest["_generated"]["snapshot_id"].startswith("sha256:")
    assert "concept_to_notes" in manifest["backlinks"]


def test_path_attachment_copies_the_exact_approved_bytes(mini_repo, tmp_path):
    add_path(mini_repo)
    source = tmp_path / "path-handwriting.png"
    source.write_bytes(b"approved-path-image")
    result = approved_v2_call(
        mini_repo,
        capability="path.attachment.add",
        payload={
            "path_id": "path-demo-probability",
            "stage_id": "stage-one",
            "file": str(source),
            "file_sha256": file_sha256(source),
        },
        artifact_ids=["path-demo-probability"],
        idempotency_key="path-attachment-content-bound-001",
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)["result"]
    copied = mini_repo / response["attachment"]
    assert copied.read_bytes() == b"approved-path-image"


def test_path_attachment_idempotent_and_non_destructive_under_name_collisions(mini_repo, tmp_path, monkeypatch):
    import json
    import sys
    import textwrap

    from tests import gateway_helpers

    original_run = gateway_helpers.subprocess.run

    wrapper = tmp_path / "frozen_los.py"
    tools_dir = gateway_helpers.Path(__file__).resolve().parent.parent / "tools"
    wrapper.write_text(textwrap.dedent(f"""\
        import sys, datetime as dt
        from pathlib import Path
        sys.path.insert(0, {str(tools_dir)!r})
        class MockDateTime(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return dt.datetime(2026, 9, 6, 12, 0, 0, tzinfo=tz)
        import learning_os.commands.support
        learning_os.commands.support._dt.datetime = MockDateTime
        import runpy
        sys.argv[0] = {str(tools_dir / 'los.py')!r}
        runpy.run_path(sys.argv[0], run_name="__main__")
    """), encoding="utf-8")

    def frozen_run(args, **kwargs):
        if args[0] == sys.executable and "los.py" in str(args[1]):
            args = [args[0], str(wrapper)] + args[2:]
        return original_run(args, **kwargs)

    monkeypatch.setattr(gateway_helpers.subprocess, "run", frozen_run)

    add_path(mini_repo)

    def add_attachment(source_path, idempotency_key):
        return gateway_helpers.approved_v2_call(
            mini_repo,
            capability="path.attachment.add",
            payload={
                "path_id": "path-demo-probability",
                "stage_id": "stage-one",
                "file": str(source_path),
                "file_sha256": gateway_helpers.file_sha256(source_path),
            },
            artifact_ids=["path-demo-probability"],
            idempotency_key=idempotency_key,
        )

    # Upload 1
    source1 = tmp_path / "handwriting.png"
    source1.write_bytes(b"approved-path-image-1")
    res1 = add_attachment(source1, "upload-1")
    assert res1.returncode == 0
    path1 = mini_repo / json.loads(res1.stdout)["result"]["attachment"]

    # Upload 2
    source2 = tmp_path / "upload2" / "handwriting.png"
    source2.parent.mkdir()
    source2.write_bytes(b"approved-path-image-2")
    res2 = add_attachment(source2, "upload-2")
    assert res2.returncode == 0
    path2 = mini_repo / json.loads(res2.stdout)["result"]["attachment"]

    # Upload 3
    source3 = tmp_path / "upload3" / "handwriting.png"
    source3.parent.mkdir()
    source3.write_bytes(b"approved-path-image-3")

    env3 = gateway_helpers.approved_v2_envelope(
        mini_repo,
        capability="path.attachment.add",
        payload={
            "path_id": "path-demo-probability",
            "stage_id": "stage-one",
            "file": str(source3),
            "file_sha256": gateway_helpers.file_sha256(source3),
        },
        artifact_ids=["path-demo-probability"],
        idempotency_key="upload-3",
    )
    res3 = gateway_helpers.run_v2_capability(mini_repo, env3)
    assert res3.returncode == 0
    path3 = mini_repo / json.loads(res3.stdout)["result"]["attachment"]

    assert path1 != path2
    assert path1 != path3
    assert path2 != path3

    assert path1.read_bytes() == b"approved-path-image-1"
    assert path2.read_bytes() == b"approved-path-image-2"
    assert path3.read_bytes() == b"approved-path-image-3"

    # Replay third
    res3_replay = gateway_helpers.run_v2_capability(mini_repo, env3)
    assert res3_replay.returncode == 0

def test_path_note_uses_snapshot_guard_and_atomic_projection(mini_repo):
    add_path(mini_repo)
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, "T1"))
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["_generated"]["snapshot_id"]

    proc = _path_note(
        mini_repo,
        text="My own reasoning.",
        key="path-note-snapshot-001",
        expected_snapshot=snapshot,
    )
    assert proc.returncode == 0, proc.stderr
    updated = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    path_rec = next(r for r in updated["records"] if r["id"] == "path-demo-probability")
    assert path_rec["stages"][0]["notes_text"] == "My own reasoning.\n"
    assert updated["_generated"]["snapshot_id"] != snapshot
    assert not list((mini_repo / "generated").glob(".*.tmp"))

    stale = _path_note(
        mini_repo,
        text="Would overwrite newer work.",
        key="path-note-snapshot-002",
        expected_snapshot=snapshot,
    )
    assert stale.returncode == 3
    stale_response = json.loads(stale.stdout)
    assert stale_response["error"]["code"] == "STALE_SNAPSHOT"


def test_complete_stage_advances_and_last_stage_opens_shelving(mini_repo):
    add_path(mini_repo)
    first = _path_progress(
        mini_repo,
        "stage-one",
        key="path-progress-first-001",
    )
    assert first.returncode == 0, first.stderr
    data = yaml.safe_load((mini_repo / "work/active/workspace-demo/paths/"
                           "path-demo-probability.yaml").read_text(encoding="utf-8"))
    assert data["current_stage"] == "stage-two"
    assert [s["status"] for s in data["stages"]] == ["complete", "active"]

    second = _path_progress(
        mini_repo,
        "stage-two",
        key="path-progress-second-001",
    )
    assert second.returncode == 0, second.stderr
    data = yaml.safe_load((mini_repo / "work/active/workspace-demo/paths/"
                           "path-demo-probability.yaml").read_text(encoding="utf-8"))
    assert data["status"] == "ready-to-shelve"
    assert data["shelving"]["state"] == "draft"


def test_learning_path_direct_cli_write_is_refused(mini_repo):
    path_file = add_path(mini_repo)
    before = path_file.read_bytes()
    proc = run_los(
        mini_repo,
        "path-progress",
        "path-demo-probability",
        "stage-one",
        "complete",
    )
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
    assert path_file.read_bytes() == before


def test_machine_bootstrap_discovers_contract_and_path(mini_repo):
    add_path(mini_repo)
    proc = run_los(mini_repo, "bootstrap")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["capabilities"]["contract_version"] == 2
    assert payload["capabilities"]["rules"]["shelving_requires_explicit_approval"]
    assert payload["active_study_maps"] == []
    assert payload["resume_pointer"] == {}
