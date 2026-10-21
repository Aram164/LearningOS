"""Transactional creation: `module.create` and `collection.create`.

Creation was the one structural act the gateway did not model. These tests
pin the properties that make it a governed write rather than a hand edit:

* the exact files it writes, named in an append-only receipt;
* a refusal when the destination already exists — an absent artifact
  revision resolves to ``0``, so a revision of ``0`` cannot prove absence,
  and the two modules created by hand on 2026-10-21 carry no revision entry
  at all;
* a refusal when the approved snapshot is stale;
* a rollback that leaves the tree at its pre-state;
* an identical retry that replays the original success instead of writing
  twice, and a *distinct* request for the same identity that refuses.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_call, approved_v2_envelope, file_sha256

from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.revisions import artifact_revision

ROOT = Path(__file__).resolve().parents[1]


def _module_package(module_id: str, *, title: str = "Created module",
                    source_id: str | None = None) -> str:
    sources = ""
    if source_id:
        sources = (
            "  sources:\n"
            f"  - source_id: {source_id}\n"
            "    role: spine\n"
            "    why: The adopted spine of the created module.\n"
            "    priority: 0\n"
        )
    else:
        sources = "  sources: []\n"
    return (
        "module:\n"
        f"  id: {module_id}\n"
        "  type: module\n"
        "  kind: academic\n"
        "  area_id: program-bachelors\n"
        f"  title: {title}\n"
        "  status: enrolled\n"
        "  institution: HU Berlin\n"
        "  semester: wise-2026\n"
        "  unit_order: []\n"
        "  source_map: source-map.yaml\n"
        "source_map:\n"
        "  type: module-source-map\n"
        f"  module_id: {module_id}\n"
        + sources
    )


COLLECTION_RECORD = (
    "title: Created collection\n"
    "collection_kind: catalogue\n"
    "entries:\n"
    "- source: source-demo-book\n"
    "  group: Demo\n"
    "  why: The demo book, in the created collection.\n"
)


@pytest.fixture()
def repo(mini_repo: Path) -> Path:
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    return mini_repo


def _write(root: Path, name: str, text: str) -> Path:
    """The reviewed draft, outside the repository: it is an input, not a write.

    `work/inbox/` is a canonical tree, so a draft parked there would change
    the repository's fingerprint and make a "nothing was written" assertion
    read as a false negative.
    """
    path = root.parent / "drafts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _payload(path: Path) -> dict:
    return {"file": str(path), "file_sha256": file_sha256(path)}


def _result(proc) -> dict:
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - diagnostics only
        raise AssertionError(
            f"expected JSON, got exit {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}") from exc


# --------------------------------------------------------------------------
# module.create
# --------------------------------------------------------------------------

def test_creation_writes_exactly_the_two_files_and_records_a_receipt(repo: Path):
    package = _write(repo, "package.yaml", _module_package("module-created-1"))
    proc = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-created-1"], idempotency_key="create-module-1")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = _result(proc)
    assert result["ok"] is True
    assert result["transaction_id"]
    receipt = yaml.safe_load(
        (repo / result["receipt_path"]).read_text(encoding="utf-8"))
    assert [row["path"] for row in receipt["writes"]] == [
        "curriculum/modules/module-created-1/module.yaml",
        "curriculum/modules/module-created-1/source-map.yaml",
    ]
    assert all(row["created"] is True for row in receipt["writes"])
    assert receipt["capability"] == "module.create"
    assert receipt["artifact_revisions"]["module-created-1"] == {
        "before": 0, "after": 1}
    created = repo / "curriculum/modules/module-created-1/module.yaml"
    assert created.is_file()
    record = yaml.safe_load(created.read_text(encoding="utf-8"))
    assert record["id"] == "module-created-1"


def test_creation_registers_the_artifact_revision_from_birth(repo: Path):
    package = _write(repo, "package.yaml", _module_package("module-created-2"))
    assert artifact_revision(repo, "module-created-2") == 0
    proc = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-created-2"], idempotency_key="create-module-2")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert artifact_revision(repo, "module-created-2") == 1


def test_creation_refuses_an_existing_destination(repo: Path):
    """The fixture already carries `module-demo`."""
    package = _write(repo, "package.yaml", _module_package("module-demo"))
    proc = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-demo"], idempotency_key="create-module-existing")
    assert proc.returncode != 0
    result = _result(proc)
    assert result["ok"] is False
    assert "already exists" in result["error"]["message"]
    # Nothing was written and no receipt was produced.
    assert not list((repo / "operations/transactions").glob(
        "transaction-*.yaml")) or all(
        "module.create" not in p.read_text(encoding="utf-8")
        for p in (repo / "operations/transactions").glob("transaction-*.yaml"))


def test_creation_refuses_a_destination_that_exists_without_a_revision(
        repo: Path):
    """Revision 0 cannot prove absence: the file is what proves it.

    The two modules created by hand on 2026-10-21 exist on disk and carry
    no artifact revision at all. A creation aimed at such an identity must
    refuse even though its revision guard would pass.
    """
    target = repo / "curriculum/modules/module-handwritten"
    target.mkdir(parents=True, exist_ok=True)
    (target / "module.yaml").write_text(
        _module_package("module-handwritten"), encoding="utf-8")
    assert artifact_revision(repo, "module-handwritten") == 0
    package = _write(repo, "package.yaml",
                     _module_package("module-handwritten"))
    proc = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-handwritten"],
        idempotency_key="create-module-handwritten")
    assert proc.returncode != 0
    assert "already exists" in _result(proc)["error"]["message"]


def test_creation_refuses_a_stale_snapshot(repo: Path):
    package = _write(repo, "package.yaml", _module_package("module-created-3"))
    envelope = approved_v2_envelope(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-created-3"], idempotency_key="create-module-stale")
    envelope["expected_snapshot"] = "sha256:" + "0" * 64
    from gateway_helpers import run_v2_capability
    proc = run_v2_capability(repo, envelope)
    assert proc.returncode != 0
    result = _result(proc)
    assert result["ok"] is False
    assert not (repo / "curriculum/modules/module-created-3").exists()


def test_an_identical_retry_replays_the_original_success(repo: Path):
    package = _write(repo, "package.yaml", _module_package("module-created-4"))
    envelope = approved_v2_envelope(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-created-4"], idempotency_key="create-module-replay")
    from gateway_helpers import run_v2_capability
    first = run_v2_capability(repo, envelope)
    assert first.returncode == 0, first.stdout + first.stderr
    second = run_v2_capability(repo, envelope)
    assert second.returncode == 0, second.stdout + second.stderr
    first_result = _result(first)
    second_result = _result(second)
    assert second_result["transaction_id"] == first_result["transaction_id"]
    assert second_result.get("replayed") is True
    # One write, one revision: the retry did not write again.
    assert artifact_revision(repo, "module-created-4") == 1


def test_a_distinct_request_for_the_same_identity_refuses(repo: Path):
    package = _write(repo, "package.yaml", _module_package("module-created-5"))
    first = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-created-5"], idempotency_key="create-module-5-a")
    assert first.returncode == 0, first.stdout + first.stderr
    # A different request: new idempotency key, same identity.
    second = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-created-5"], idempotency_key="create-module-5-b")
    assert second.returncode != 0
    assert "already exists" in _result(second)["error"]["message"]


def test_a_refused_creation_leaves_the_tree_unchanged(repo: Path):
    before = canonical_fingerprint(repo)
    package = _write(repo, "package.yaml", _module_package("module-demo"))
    proc = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-demo"], idempotency_key="create-module-rollback")
    assert proc.returncode != 0
    assert canonical_fingerprint(repo) == before


def test_creation_refuses_a_record_that_breaks_its_schema(repo: Path):
    package = _write(repo, "package.yaml", "module:\n  id: nope\n")
    proc = approved_v2_call(
        repo, capability="module.create", payload=_payload(package),
        artifact_ids=["module-nope"], idempotency_key="create-module-bad")
    assert proc.returncode != 0
    result = _result(proc)
    assert result["ok"] is False
    assert not (repo / "curriculum/modules/module-nope").exists()


# --------------------------------------------------------------------------
# collection.create
# --------------------------------------------------------------------------

def test_collection_creation_writes_exactly_one_file(repo: Path):
    source = _write(repo, "created-shelf.yaml", COLLECTION_RECORD)
    proc = approved_v2_call(
        repo, capability="collection.create", payload=_payload(source),
        artifact_ids=["collection:created-shelf"],
        idempotency_key="create-collection-1")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = _result(proc)
    receipt = yaml.safe_load(
        (repo / result["receipt_path"]).read_text(encoding="utf-8"))
    assert [row["path"] for row in receipt["writes"]] == [
        "sources/collections/created-shelf.yaml"]
    assert (repo / "sources/collections/created-shelf.yaml").is_file()


def test_collection_creation_refuses_an_existing_destination(repo: Path):
    existing = repo / "sources" / "collections" / "shelf.yaml"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text(COLLECTION_RECORD, encoding="utf-8")
    source = _write(repo, "shelf.yaml", COLLECTION_RECORD)
    proc = approved_v2_call(
        repo, capability="collection.create", payload=_payload(source),
        artifact_ids=["collection:shelf"], idempotency_key="create-collection-existing")
    assert proc.returncode != 0
    assert "already exists" in _result(proc)["error"]["message"]


def test_collection_identity_is_the_reviewed_file_name(repo: Path):
    """A collection's identity is its kebab-case filename stem."""
    source = _write(repo, "Not A Stem.yaml", COLLECTION_RECORD)
    proc = approved_v2_call(
        repo, capability="collection.create", payload=_payload(source),
        artifact_ids=[], idempotency_key="create-collection-bad-stem")
    assert proc.returncode != 0
    assert "kebab-case filename stem" in _result(proc)["error"]["message"]


def test_collection_creation_refuses_a_stale_snapshot(repo: Path):
    source = _write(repo, "stale-shelf.yaml", COLLECTION_RECORD)
    envelope = approved_v2_envelope(
        repo, capability="collection.create", payload=_payload(source),
        artifact_ids=["collection:stale-shelf"],
        idempotency_key="create-collection-stale")
    envelope["expected_snapshot"] = "sha256:" + "0" * 64
    from gateway_helpers import run_v2_capability
    proc = run_v2_capability(repo, envelope)
    assert proc.returncode != 0
    assert not (repo / "sources/collections/stale-shelf.yaml").exists()
