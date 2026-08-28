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

import shutil
from pathlib import Path

import pytest

from learning_os.loader import load_repo
from learning_os.rules import validate

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
        shutil.copytree(tree, root / tree.name)

    # Current schemas and current contract — deliberately not the frozen ones.
    shutil.copytree(repo_root / "system" / "schema", root / "system" / "schema")
    shutil.copytree(repo_root / "system" / "contracts", root / "system" / "contracts")
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
        f"(python tools/schema_contract.py --bump), and freeze the new shape as "
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
        "projects": repo.projects,
    }
    empty = sorted(name for name, records in populated.items() if not records)
    assert empty == [], f"format {version} fixture covers no {empty}"


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
