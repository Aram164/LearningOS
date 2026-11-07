"""Serve the stored manifest when it is provably current (#83).

Reads rebuild the 15 MB projection on every call although the stored
``generated/manifest.json`` usually describes exactly the current state.
``_fresh_manifest`` serves the stored file only when its identity sidecar
pins every manifest input to its live value — canonical snapshot,
contract/schema, projection-code digest, runtime, operations state,
materials state, and build date — and otherwise rebuilds exactly as
before. A partially matching or corrupt file is never served.

These tests assert hit/miss behavior (never wall time, which is load
dependent): byte-identical outputs on both paths, rebuild on every
invalidation, and repo equivalence for callers that need the object.
"""

from __future__ import annotations

import datetime
import json

import pytest
import yaml
from repo_builders import add_curriculum, run_los, write_yaml

from learning_os.app import projection as plumbing
from learning_os.app.handlers.reads import (
    _use_evidence_from_manifest,
    related_records,
)
from learning_os.derive.projection import generate_all, write_outputs
from learning_os.derive.semantics.source_use import use_evidence as _use_evidence
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loader import load_repo
from learning_os.store.manifest_identity import (
    IDENTITY_FILENAME,
    build_identity,
    check_identity,
    materials_digest,
    operations_digest,
)


def _generate(root) -> dict:
    """Publish the projection (manifest plus identity sidecar) like make views."""
    repo = load_repo(root)
    outputs = generate_all(repo, generated_at="T1")
    write_outputs(repo, outputs)
    assert (root / "generated" / IDENTITY_FILENAME).is_file()
    return json.loads(outputs["manifest.json"])


def _stored_manifest(root) -> dict:
    return json.loads((root / "generated/manifest.json").read_text(encoding="utf-8"))


def _stored_identity(root) -> dict:
    return json.loads((root / "generated" / IDENTITY_FILENAME).read_text(encoding="utf-8"))


def _live_snapshot(root) -> str:
    return f"sha256:{canonical_fingerprint(root)}"


def _without_generated(manifest: dict) -> dict:
    """Payload comparison: a rebuild stamps the live clock, not "T1"."""
    return {key: value for key, value in manifest.items() if key != "_generated"}


def _counted(monkeypatch, name):
    calls = []

    real = getattr(plumbing, name)

    def wrapper(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(plumbing, name, wrapper)
    return calls


def test_reuse_serves_the_stored_build_without_rebuilding(mini_repo, monkeypatch):
    built = _generate(mini_repo)
    builds = _counted(monkeypatch, "build_manifest")
    loads = _counted(monkeypatch, "load_repo")

    manifest = plumbing.fresh_manifest(mini_repo)

    assert builds == [] and loads == []
    assert manifest == built == _stored_manifest(mini_repo)


def test_reuse_check_accepts_a_fresh_build(mini_repo):
    manifest = _generate(mini_repo)
    ok, reason = check_identity(
        mini_repo, manifest, _stored_identity(mini_repo),
        live_snapshot=_live_snapshot(mini_repo))
    assert (ok, reason) == (True, "current")


@pytest.mark.parametrize("command", [
    ["inspect", "note-demo"],
    ["related", "note-demo"],
    ["search", "demo"],
    ["unit-list"],
])
def test_read_outputs_are_byte_identical_on_both_paths(mini_repo, command):
    add_curriculum(mini_repo)
    if command[0] == "unit-list":
        command = ["unit-list", "--module-id", "module-demo"]
    _generate(mini_repo)
    reused = run_los(mini_repo, *command)
    assert reused.returncode == 0, reused.stderr
    (mini_repo / "generated/manifest.json").unlink()
    (mini_repo / "generated" / IDENTITY_FILENAME).unlink()
    rebuilt = run_los(mini_repo, *command)
    assert rebuilt.returncode == 0, rebuilt.stderr
    assert (reused.stdout, reused.stderr) == (rebuilt.stdout, rebuilt.stderr)


def test_canonical_edit_rebuilds_with_fresh_output(mini_repo, monkeypatch):
    _generate(mini_repo)
    before = run_los(mini_repo, "inspect", "note-demo")
    assert before.returncode == 0, before.stderr

    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text(encoding="utf-8").replace(
        "Body prose.", "Body prose with an edited second sentence."), encoding="utf-8")

    builds = _counted(monkeypatch, "build_manifest")
    manifest = plumbing.fresh_manifest(mini_repo)
    assert len(builds) == 1
    [record] = [row for row in manifest["records"] if row["id"] == "note-demo"]
    assert record["summary"] == "Body prose with an edited second sentence."

    after = run_los(mini_repo, "inspect", "note-demo")
    assert after.returncode == 0, after.stderr
    assert json.loads(after.stdout)["summary"] == record["summary"]
    assert after.stdout != before.stdout


def test_code_edit_invalidates_in_a_fixture(mini_repo, monkeypatch):
    """An uncommitted code change rebuilds: identity keys on bytes, not HEAD."""
    manifest = _generate(mini_repo)
    identity = _stored_identity(mini_repo)
    monkeypatch.setattr(
        "learning_os.store.manifest_identity.digest_code_identity",
        lambda root: "0" * 64)
    ok, reason = check_identity(
        mini_repo, manifest, identity, live_snapshot=_live_snapshot(mini_repo))
    assert ok is False
    assert "code" in reason

    builds = _counted(monkeypatch, "build_manifest")
    plumbing.fresh_manifest(mini_repo)
    assert len(builds) == 1


@pytest.mark.parametrize("breakage", ["manifest-garbage", "identity-garbage",
                                      "identity-missing", "manifest-missing",
                                      "identity-shape"])
def test_corrupt_or_missing_files_rebuild(mini_repo, monkeypatch, breakage):
    manifest = _generate(mini_repo)
    gen = mini_repo / "generated"
    if breakage == "manifest-garbage":
        (gen / "manifest.json").write_text("{nope", encoding="utf-8")
    elif breakage == "identity-garbage":
        (gen / IDENTITY_FILENAME).write_text("nul", encoding="utf-8")
    elif breakage == "identity-missing":
        (gen / IDENTITY_FILENAME).unlink()
    elif breakage == "manifest-missing":
        (gen / "manifest.json").unlink()
    else:
        (gen / IDENTITY_FILENAME).write_text("[1,2]", encoding="utf-8")

    builds = _counted(monkeypatch, "build_manifest")
    served = plumbing.fresh_manifest(mini_repo)

    assert len(builds) == 1
    assert _without_generated(served) == _without_generated(manifest)


def test_stale_snapshot_rebuilds(mini_repo, monkeypatch):
    manifest = _generate(mini_repo)
    path = mini_repo / "generated" / IDENTITY_FILENAME
    identity = json.loads(path.read_text(encoding="utf-8"))
    identity["snapshot_id"] = "sha256:" + "0" * 64
    path.write_text(json.dumps(identity), encoding="utf-8")

    builds = _counted(monkeypatch, "build_manifest")
    served = plumbing.fresh_manifest(mini_repo)

    assert len(builds) == 1
    assert _without_generated(served) == _without_generated(manifest)


def test_yesterday_build_rebuilds(mini_repo):
    """Availability is today-relative, so a previous-day build is stale."""
    manifest = _generate(mini_repo)
    identity = _stored_identity(mini_repo)
    identity["built_date"] = (
        datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    ok, reason = check_identity(
        mini_repo, manifest, identity, live_snapshot=_live_snapshot(mini_repo))
    assert ok is False
    assert "previous day" in reason


def test_operations_state_invalidates(mini_repo):
    ledger = mini_repo / "operations/transactions/revisions.yaml"
    before = operations_digest(mini_repo)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(ledger, {"schema_version": 1, "type": "artifact-revision-ledger",
                        "revisions": {"note-demo": 3}})
    assert operations_digest(mini_repo) != before

    manifest = _generate(mini_repo)
    ok, _ = check_identity(mini_repo, manifest, _stored_identity(mini_repo),
                           live_snapshot=_live_snapshot(mini_repo))
    assert ok is True
    write_yaml(ledger, {"schema_version": 1, "type": "artifact-revision-ledger",
                        "revisions": {"note-demo": 4}})
    ok, reason = check_identity(mini_repo, manifest, _stored_identity(mini_repo),
                                live_snapshot=_live_snapshot(mini_repo))
    assert ok is False
    assert "operations" in reason


def test_materials_state_invalidates(mini_repo):
    materials = mini_repo.parent / "materials"
    target = materials / "demo-slides.pdf"
    target.write_bytes(b"%PDF-1.4 demo bytes")
    before = materials_digest(mini_repo)
    target.write_bytes(b"%PDF-1.4 demo bytes, revised")
    assert materials_digest(mini_repo) != before

    manifest = _generate(mini_repo)
    ok, _ = check_identity(mini_repo, manifest, _stored_identity(mini_repo),
                           live_snapshot=_live_snapshot(mini_repo))
    assert ok is True
    (materials / "another.pdf").write_bytes(b"new file")
    ok, reason = check_identity(mini_repo, manifest, _stored_identity(mini_repo),
                                live_snapshot=_live_snapshot(mini_repo))
    assert ok is False
    assert "materials" in reason


def test_dotfiles_do_not_move_the_materials_digest(mini_repo):
    (mini_repo.parent / "materials" / "deck.pdf").write_bytes(b"slides")
    before = materials_digest(mini_repo)
    (mini_repo.parent / "materials" / ".DS_Store").write_bytes(b"finder")
    assert materials_digest(mini_repo) == before


def test_identity_sidecar_pins_the_live_build(mini_repo):
    manifest = _generate(mini_repo)
    identity = _stored_identity(mini_repo)
    assert identity["snapshot_id"] == manifest["_generated"]["snapshot_id"]
    assert identity["snapshot_id"] == _live_snapshot(mini_repo)
    assert identity["contract_version"] == manifest["_generated"]["contract_version"]
    assert identity["schema_sha256"] == manifest["_generated"]["schema_sha256"]
    assert identity["built_date"] == datetime.date.today().isoformat()
    rebuilt = build_identity(mini_repo, manifest)
    assert rebuilt == identity


def test_lazy_repo_loads_once_on_first_use(mini_repo, monkeypatch):
    _generate(mini_repo)
    loads = _counted(monkeypatch, "load_repo")
    manifest, repo = plumbing.fresh_manifest_and_repo(mini_repo)
    assert isinstance(repo, plumbing._LazyRepo)
    assert loads == []
    assert sorted(repo.notes) == sorted(
        row["id"] for row in manifest["records"] if row["type"] == "note")
    assert len(loads) == 1
    _ = repo.notes
    assert len(loads) == 1


def test_manifest_tallies_match_repo_tallies_with_feedback(mini_repo):
    """related ranks identically whether tallies come from repo or manifest."""
    add_curriculum(mini_repo)
    path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["stages"][0]["source_feedback"] = [
        {"source_id": "source-demo-book", "feedback": "helpful",
         "recorded": "2026-09-21"},
        {"source_id": "source-demo-book", "feedback": "too-advanced",
         "recorded": "2026-09-21"},
    ]
    write_yaml(path, data)
    repo = load_repo(mini_repo)
    manifest = json.loads(generate_all(repo, generated_at="T1")["manifest.json"])
    assert _use_evidence_from_manifest(manifest) == _use_evidence(repo)
    assert _use_evidence(repo) != {}
    assert related_records(manifest, "source-demo-book", repo) == related_records(
        manifest, "source-demo-book", None,
        tallies=_use_evidence_from_manifest(manifest))


def test_snapshot_bound_reads_share_one_hash_on_reuse(mini_repo, monkeypatch):
    """The reuse check reuses the caller's snapshot instead of re-hashing."""
    _generate(mini_repo)
    snapshot = _live_snapshot(mini_repo)
    hashes = _counted(monkeypatch, "canonical_fingerprint")
    builds = _counted(monkeypatch, "build_manifest")
    plumbing.fresh_manifest(mini_repo, snapshot_id=snapshot)
    assert hashes == [] and builds == []


def test_a_manifest_the_sidecar_does_not_describe_is_rebuilt(mini_repo, monkeypatch):
    """A crash (or a concurrent read) between the two publications after a
    code-only change leaves a sidecar beside a manifest it does not
    describe. Both carry the same snapshot stamp, so only the pinned bytes
    can tell them apart: the pair must rebuild, never serve the old bytes."""
    from learning_os.store.manifest_identity import manifest_text

    _generate(mini_repo)
    stored = _stored_manifest(mini_repo)
    stale = json.loads(json.dumps(stored))
    stale["_stale_build_marker"] = "built by the previous code"
    (mini_repo / "generated/manifest.json").write_text(
        manifest_text(stale), encoding="utf-8")
    assert _stored_identity(mini_repo)["snapshot_id"] == stale["_generated"]["snapshot_id"]
    builds = _counted(monkeypatch, "build_manifest")

    manifest = plumbing.fresh_manifest(mini_repo)

    assert len(builds) == 1
    assert "_stale_build_marker" not in manifest
    assert _without_generated(manifest) == _without_generated(stored)


# ---------------------------------------------------------------------------
# A rebuilding read publishes, so the next read of the same state reuses.
# The clock moves through LOS_OBSERVATIONS, the same override characterization
# uses: a previous-day build is stale by date alone, every other pin matching.


def _clock(monkeypatch, tmp_path, day: str) -> None:
    path = tmp_path / f"clock-{day}.json"
    path.write_text(json.dumps({"now": f"{day}T09:00:00"}), encoding="utf-8")
    monkeypatch.setenv("LOS_OBSERVATIONS", str(path))


def _stored_pair(root) -> tuple[bytes, bytes]:
    gen = root / "generated"
    return (gen / "manifest.json").read_bytes(), (gen / IDENTITY_FILENAME).read_bytes()


def _yesterdays_build(root, monkeypatch, tmp_path) -> tuple[bytes, bytes]:
    _clock(monkeypatch, tmp_path, "2026-11-06")
    _generate(root)
    _clock(monkeypatch, tmp_path, "2026-11-07")
    ok, reason = check_identity(root, _stored_manifest(root), _stored_identity(root),
                                live_snapshot=_live_snapshot(root))
    assert (ok, reason) == (False, "stored build is from a previous day")
    return _stored_pair(root)


def test_first_read_of_a_day_publishes_and_the_second_reuses(mini_repo, monkeypatch, tmp_path):
    _yesterdays_build(mini_repo, monkeypatch, tmp_path)
    builds = _counted(monkeypatch, "build_manifest")

    first = plumbing.fresh_manifest(mini_repo)
    assert len(builds) == 1
    assert _stored_identity(mini_repo)["built_date"] == "2026-11-07"
    second = plumbing.fresh_manifest(mini_repo)

    assert len(builds) == 1
    assert second == first == _stored_manifest(mini_repo)


def test_a_rebuilding_read_publishes_exactly_what_generation_does(mini_repo, monkeypatch, tmp_path):
    _yesterdays_build(mini_repo, monkeypatch, tmp_path)
    plumbing.fresh_manifest(mini_repo)
    gen = mini_repo / "generated"
    published = {p.relative_to(gen).as_posix(): p.read_bytes()
                 for p in gen.rglob("*") if p.is_file()}

    expected = generate_all(load_repo(mini_repo))

    assert {rel: published.get(rel) for rel in expected} == {
        rel: text.encode("utf-8") for rel, text in expected.items()}


def test_a_caller_already_holding_the_lock_exclusive_does_not_publish(
        mini_repo, monkeypatch, tmp_path):
    from learning_os.app.lock import operator_lock

    before = _yesterdays_build(mini_repo, monkeypatch, tmp_path)
    builds = _counted(monkeypatch, "build_manifest")
    with operator_lock(mini_repo):
        plumbing.fresh_manifest(mini_repo)
    assert len(builds) == 1
    assert _stored_pair(mini_repo) == before


@pytest.mark.parametrize("failure", ["unwritable", "view-defect"])
def test_a_failed_publication_keeps_the_pair_and_the_answer(
        mini_repo, monkeypatch, tmp_path, failure):
    from learning_os.derive.projection import outputs

    before = _yesterdays_build(mini_repo, monkeypatch, tmp_path)

    def broken(*_args, **_kwargs):
        raise (OSError("read-only file system") if failure == "unwritable"
               else KeyError("a defect in one Markdown view"))

    if failure == "unwritable":
        monkeypatch.setattr(plumbing, "write_outputs", broken)
    else:
        monkeypatch.setattr(outputs, "build_module_view", broken)
    served = plumbing.fresh_manifest(mini_repo)

    assert _stored_pair(mini_repo) == before
    assert _without_generated(served) == _without_generated(_stored_manifest(mini_repo))


@pytest.mark.parametrize("mover", ["materials", "clock"])
def test_an_input_that_moves_during_the_build_is_not_published(
        mini_repo, monkeypatch, tmp_path, mover):
    before = _yesterdays_build(mini_repo, monkeypatch, tmp_path)
    real = plumbing.build_backlinks

    def moving(repo, generated_at):
        if mover == "materials":
            (mini_repo.parent / "materials" / "added-mid-build.pdf").write_bytes(b"%PDF new")
        else:
            _clock(monkeypatch, tmp_path, "2026-11-08")  # midnight passes mid-build
        return real(repo, generated_at)

    monkeypatch.setattr(plumbing, "build_backlinks", moving)
    plumbing.fresh_manifest(mini_repo)
    assert _stored_pair(mini_repo) == before


def test_a_canonical_edit_during_an_unseeded_build_is_not_published(
        mini_repo, monkeypatch, tmp_path):
    """Content loaded before the edit, stamp hashed after it: published, the
    pair would pass the next read's snapshot check while describing the
    pre-edit text. The pre-load hash must equal the build's own stamp."""
    before = _yesterdays_build(mini_repo, monkeypatch, tmp_path)
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    real = plumbing.load_repo

    def load_then_edit(root):
        repo = real(root)
        note.write_text(note.read_text(encoding="utf-8") + "\nEdited mid-build.\n",
                        encoding="utf-8")
        return repo

    monkeypatch.setattr(plumbing, "load_repo", load_then_edit)
    plumbing.fresh_manifest(mini_repo)
    assert _stored_pair(mini_repo) == before


def test_generate_all_accepts_one_prebuilt_build_only(mini_repo):
    from learning_os.derive.projection import build_backlinks, build_manifest

    repo = load_repo(mini_repo)
    backlinks = build_backlinks(repo, "T1")
    manifest = build_manifest(repo, "T1", backlinks)
    assert generate_all(repo, "T1", backlinks=backlinks, manifest=manifest) == generate_all(
        repo, "T1")
    with pytest.raises(ValueError, match="another generated_at"):
        generate_all(repo, "T2", backlinks=backlinks, manifest=manifest)
    with pytest.raises(ValueError, match="together"):
        generate_all(repo, "T1", manifest=manifest)
