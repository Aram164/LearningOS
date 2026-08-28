from __future__ import annotations

from pathlib import Path

import pytest

from learning_os.contracts.write_scopes import (
    WriteScopeError,
    normalize_scope_pattern,
    require_write_scope,
    scope_matches,
    write_target,
)
from learning_os.transactions import TransactionScopeError, TransactionService


@pytest.mark.parametrize(
    ("path", "scope"),
    [
        ("work/inbox/capture.md", "work/inbox/**"),
        ("projects/registry/project-demo.yaml", "projects/registry/*"),
        (
            "curriculum/modules/module-a/units/unit-b/stages/stage-c/notes.md",
            "curriculum/modules/**/units/**",
        ),
        ("operations/legacy/archive-lock.yaml", "operations/legacy/archive-lock.yaml"),
        ("knowledge/garden/transcriptions/item.md", "knowledge/garden/transcriptions/"),
    ],
)
def test_declared_scope_semantics(path: str, scope: str):
    assert scope_matches(path, scope)


@pytest.mark.parametrize(
    ("path", "scope"),
    [
        ("work/inbox-escape/capture.md", "work/inbox/**"),
        ("projects/registry/nested/project-demo.yaml", "projects/registry/*"),
        ("curriculum/modules/module-a/unit.yaml", "curriculum/modules/**/units/**"),
        ("operations/legacy/archive-lock.yaml.bak", "operations/legacy/archive-lock.yaml"),
    ],
)
def test_nearby_paths_do_not_inherit_authority(path: str, scope: str):
    assert not scope_matches(path, scope)


@pytest.mark.parametrize(
    "scope",
    [
        "/absolute/**", "../escape/**", "a//b", "a/**suffix", "a/prefix-*",
        "a/[bc]", "a\\b",
    ],
)
def test_malformed_scope_declarations_fail_closed(scope: str):
    with pytest.raises(WriteScopeError):
        normalize_scope_pattern(scope)


def test_write_target_refuses_parent_traversal(tmp_path: Path):
    with pytest.raises(WriteScopeError, match="not normalized"):
        write_target(tmp_path, tmp_path / "work" / ".." / "outside.yaml")


@pytest.mark.parametrize("relative", ["work/./item.yaml", "work/item.yaml/"])
def test_write_target_refuses_lexically_malformed_relative_path(
    tmp_path: Path, relative: str
):
    with pytest.raises(WriteScopeError, match="not normalized"):
        write_target(tmp_path, relative)


def test_write_target_refuses_symlink_even_when_destination_is_inside_root(tmp_path: Path):
    destination = tmp_path / "real"
    destination.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(destination, target_is_directory=True)

    with pytest.raises(WriteScopeError, match="traverses symlink"):
        write_target(tmp_path, link / "file.yaml")


def test_scope_refusal_names_capability_and_safe_relative_path():
    with pytest.raises(
        WriteScopeError,
        match=r"capability capture\.create may not write sources/registry/demo\.yaml",
    ):
        require_write_scope(
            "capture.create",
            "sources/registry/demo.yaml",
            ["work/inbox/**"],
        )


def test_transaction_service_enforces_the_catalogue_before_writing(mini_repo: Path):
    target = mini_repo / "sources/registry/out-of-scope.yaml"

    with pytest.raises(TransactionScopeError, match="capture.create may not write"):
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "sources: []\n"},
            artifact_ids=["capture:out-of-scope"],
        )

    assert not target.exists()
    assert not (mini_repo / "operations/transactions/revisions.yaml").exists()
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_module_import_authority_includes_the_source_registry(mini_repo: Path):
    target = mini_repo / "sources/registry/imported.yaml"

    result = TransactionService(mini_repo).commit(
        capability="module.plan.import",
        writes={target: "sources: []\n"},
        artifact_ids=["source-registry:imported"],
    )

    assert target.is_file()
    assert result.receipt_path.is_file()
