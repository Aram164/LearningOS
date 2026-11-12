"""Data written in an older format must still load under today's schemas.

This is the multi-year guarantee, and it is the one thing the rest of the test
suite cannot provide: every other test builds its input with *current* code, so
it can only ever prove the system is self-consistent right now. A frozen fixture
is different — it is a record of what the repository actually wrote at a point
in time, and it does not move when the schemas do.

`tests/fixtures/formats/v<N>/` therefore holds DATA ONLY. The schemas and the
contract come from the live tree, so each test here asks the real question:
*old data, new rules — does it still load?*

When a schema change breaks one of these, that is the test working. The fix is a
migration under `tools/migrations/`, a contract bump, and a new frozen fixture
for the new shape — never an edit to an existing fixture, which would erase the
evidence of what the old format was.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from repo_builders import copy_real_contracts

from learning_os.derive.validation import validate
from learning_os.store.loader import load_repo

FORMATS = [
    path.name
    for path in sorted(
        (Path(__file__).parent / "fixtures" / "formats").glob("v[0-9]*"),
        key=lambda path: int(path.name.removeprefix("v")),
    )
    if path.is_dir()
]


def test_every_recorded_fixture_pointer_resolves(repo_root: Path):
    """The contract's own `fixture:` pointers must name a directory that exists.

    `FORMATS` above is built by globbing, so a history entry can name a fixture
    that was never frozen and no test will ever notice — which is exactly what
    happened to v13 between 2026-08-25 and 2026-08-28. The contract then claims
    a frozen snapshot of a shape nobody can load, and the claim is invisible.
    `bump()` writes the pointer for the version being adopted, before its
    fixture exists, so the honest rule is: whatever the pointer says at rest
    must resolve.
    """
    import yaml

    contract = yaml.safe_load(
        (repo_root / "system/contracts/data-contract.yaml").read_text(encoding="utf-8")
    )
    dangling = [
        (entry["version"], entry["fixture"])
        for entry in contract["history"]
        if entry.get("fixture") and not (repo_root / entry["fixture"]).is_dir()
    ]
    assert not dangling, (
        "data-contract.yaml names fixture directories that do not exist: "
        + ", ".join(f"v{version} -> {path}" for version, path in dangling)
        + ". Freeze the fixture, or point the entry at the frozen shape that "
        "still applies — never delete the pointer."
    )


def _materialise(version: str, repo_root, tmp_path):
    """Assemble a repository from frozen data plus the CURRENT system definitions."""
    fixture = repo_root / "tests" / "fixtures" / "formats" / version
    if not fixture.is_dir():
        pytest.skip(f"no frozen fixture for {version}")

    root = tmp_path / "LearningOS" / "repository"
    root.mkdir(parents=True)
    (root.parent / "materials").mkdir()

    for tree in sorted(p for p in fixture.iterdir() if p.is_dir()):
        # The private reading store lives beside the repository (ADR-021), never in it.
        target = root.parent / tree.name if tree.name == "reading-memory" else root / tree.name
        shutil.copytree(tree, target)

    # Current schemas and current contract — deliberately not the frozen ones.
    shutil.copytree(repo_root / "system" / "schema", root / "system" / "schema")
    copy_real_contracts(repo_root, root)
    (root / "generated" / "reports").mkdir(parents=True)
    (root / "work" / "inbox").mkdir(parents=True, exist_ok=True)
    (root / "archive" / "workspaces").mkdir(parents=True)
    (root / ".gitignore").write_text("generated/*\n!generated/.gitkeep\n", encoding="utf-8")
    return root


@pytest.mark.parametrize("version", FORMATS)
def test_frozen_format_still_loads_without_errors(version, repo_root, tmp_path):
    root = _materialise(version, repo_root, tmp_path)
    issues = validate(load_repo(root))
    errors = [str(i) for i in issues if i.severity == "E"]
    assert errors == [], (
        f"data frozen as format {version} no longer validates against the "
        f"current schemas. This is the fixture doing its job: write a migration "
        f"under tools/migrations/, bump the contract "
        f"(.venv/bin/python tools/schema_contract.py --bump), and freeze the new shape as "
        f"a NEW fixture directory — do not edit {version}. Errors:\n"
        + "\n".join(errors))


@pytest.mark.parametrize("version", FORMATS)
def test_frozen_format_parses_into_the_expected_record_families(version, repo_root, tmp_path):
    """A fixture that silently stopped covering a family would pass vacuously."""
    root = _materialise(version, repo_root, tmp_path)
    repo = load_repo(root)
    assert repo.parse_failures == [], repo.parse_failures

    populated = {
        "notes": repo.notes,
        "concepts": repo.concepts,
        "sources": repo.sources,
        "modules": repo.modules,
        "units": repo.units,
        "study_maps": repo.study_maps,
        "workspaces": repo.workspaces,
        "programs": repo.programs,
    }
    empty = sorted(name for name, records in populated.items() if not records)
    assert empty == [], f"format {version} fixture covers no {empty}"


@pytest.mark.parametrize("version", [
    version for version in FORMATS
    if (Path(__file__).parent / "fixtures" / "formats" / version / "reading-memory").is_dir()])
def test_frozen_reading_memory_still_validates(version, repo_root, tmp_path):
    """Frozen private-store records (ADR-021) still validate and still read.

    The store sits beside the repository, so the repository validator never
    sees it; this asks the same old-data-new-rules question of its records.
    """
    from learning_os.store.contracts.json_schema import validate_contract
    from learning_os.store.materials.reading_cards import SCHEMA_NAME, ReadingStore

    root = _materialise(version, repo_root, tmp_path)
    store = root.parent / "reading-memory"
    records = 0
    for path in sorted(store.rglob("*.json")):
        validate_contract(repo_root, SCHEMA_NAME, json.loads(path.read_text(encoding="utf-8")),
                          label=f"{version} {path.relative_to(store)}")
        records += 1
    for path in sorted(store.rglob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            validate_contract(repo_root, SCHEMA_NAME, json.loads(line),
                              label=f"{version} {path.relative_to(store)}")
            records += 1
    assert records, f"{version} freezes no reading-memory records"
    reader = ReadingStore(root)
    assert reader.entries() and reader.entries(settled=True) and reader.all_cards()


def test_fixture_is_data_only(repo_root):
    """system/ must come from the live tree, or the fixture would test nothing.

    A fixture carrying its own schemas would validate old data against old rules
    and pass forever, which is precisely the failure this suite exists to catch.
    """
    for version in FORMATS:
        fixture = repo_root / "tests" / "fixtures" / "formats" / version
        if not fixture.is_dir():
            continue
        assert not (fixture / "system").exists(), (
            f"{version} carries its own system/ — it must validate against the "
            "current schemas, not frozen ones")


def test_every_schema_is_classified(repo_root):
    schema_dir = repo_root / "system" / "schema"
    unclassified = []
    for path in schema_dir.glob("*.schema.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("x-governs") not in ("record", "artifact"):
            unclassified.append(path.name)
    assert not unclassified, "Unclassified schemas: " + ", ".join(unclassified)


def test_nothing_the_validator_applies_to_records_is_an_artifact(
    repo_root, mini_repo, monkeypatch
):
    from learning_os.derive.validation.core import Validator

    applied: set[str] = set()
    original = Validator._schema_check

    def record_name(self, name, instance, where):
        applied.add(name)
        return original(self, name, instance, where)

    monkeypatch.setattr(Validator, "_schema_check", record_name)
    validate(load_repo(mini_repo), online=False)
    assert applied, "the fixture exercised no schema at all — this proves nothing"

    schema_dir = repo_root / "system" / "schema"
    offenders = []
    for name in applied:
        path = schema_dir / (name if name.endswith(".schema.json") else f"{name}.schema.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("x-governs") != "record":
            offenders.append(name)
    assert not offenders, "Validator applied non-record schemas: " + ", ".join(offenders)


def _mutate_schema_title(path: Path) -> None:
    before = path.read_bytes()
    data = json.loads(before.decode("utf-8"))
    data["title"] = f"{data.get('title', '')} edited"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert path.read_bytes() != before


def test_classification_decides_the_fingerprint(repo_root, tmp_path):
    from learning_os.store.contracts.data_contract import fingerprint

    schema_dir = tmp_path / "schema"
    shutil.copytree(repo_root / "system" / "schema", schema_dir)

    base_fingerprint = fingerprint(schema_dir)
    by_kind: dict[str, list[tuple[Path, dict]]] = {"artifact": [], "record": []}
    for path in sorted(schema_dir.glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        kind = data.get("x-governs")
        if kind in by_kind:
            by_kind[kind].append((path, data))
    assert by_kind["artifact"] and by_kind["record"]

    # Deterministic selection plus explicit coverage of an artifact schema lacking `title`.
    artifact_targets = [by_kind["artifact"][0][0]]
    titleless_artifact = next((p for p, d in by_kind["artifact"] if "title" not in d), None)
    if titleless_artifact is not None and titleless_artifact not in artifact_targets:
        artifact_targets.append(titleless_artifact)

    for artifact_schema in artifact_targets:
        _mutate_schema_title(artifact_schema)
        assert fingerprint(schema_dir) == base_fingerprint, (
            "Editing an artifact schema should leave the fingerprint unchanged"
        )

    _mutate_schema_title(by_kind["record"][0][0])
    assert fingerprint(schema_dir) != base_fingerprint, (
        "Editing a record schema should change the fingerprint"
    )


def test_unclassified_schema_still_counts_as_record(repo_root, tmp_path):
    from learning_os.store.contracts.data_contract import record_schemas

    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    new_schema = schema_dir / "test.schema.json"
    new_schema.write_text(json.dumps({"title": "Test"}), encoding="utf-8")

    schemas = record_schemas(schema_dir)
    assert new_schema in schemas, "Unclassified schema should count as a record"


@pytest.mark.parametrize("fingerprint_only", [True, False])
def test_data_contract_cli_defaults_follow_its_moved_owner(repo_root, tmp_path, fingerprint_only):
    """The public tool finds real schemas even from outside the repository."""
    import subprocess
    import sys

    from learning_os.store.contracts.data_contract import fingerprint, record_schemas

    schemas = repo_root / "system/schema"
    assert record_schemas(schemas)
    args = [sys.executable, str(repo_root / "tools/schema_contract.py")]
    if fingerprint_only:
        args.append("--fingerprint")
    proc = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stderr == ""
    if fingerprint_only:
        assert proc.stdout == fingerprint(schemas) + "\n"
    else:
        assert f"matches {len(record_schemas(schemas))} record schemas" in proc.stdout
