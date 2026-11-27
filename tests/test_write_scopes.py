from __future__ import annotations

from pathlib import Path

import pytest

from learning_os.domain.failures import TransactionScopeError
from learning_os.store.contracts.write_scopes import (
    WriteScopeError,
    normalize_scope_pattern,
    require_write_scope,
    scope_matches,
    write_target,
)
from learning_os.store.transactions import TransactionService


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
        TransactionService(mini_repo, _unmediated_test_only=True).commit(
            capability="capture.create",
            writes={target: "sources: []\n"},
            artifact_ids=["capture:out-of-scope"],
        )

    assert not target.exists()
    assert not (mini_repo / "operations/transactions/revisions.yaml").exists()
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_module_import_authority_includes_the_source_registry(mini_repo: Path):
    target = mini_repo / "sources/registry/imported.yaml"

    result = TransactionService(mini_repo, _unmediated_test_only=True).commit(
        capability="module.plan.import",
        writes={target: "sources: []\n"},
        artifact_ids=["source-registry:imported"],
    )

    assert target.is_file()
    assert result.receipt_path.is_file()


def test_guard_tool_output_path_refuses_protected_roots_and_symlinks(tmp_path: Path):
    from learning_os.store.contracts.write_scopes import guard_tool_output_path
    from learning_os.store.fingerprint import DATA_ROOTS

    repo = tmp_path / "repo"
    (repo / "system/contracts").mkdir(parents=True)
    (repo / "system/contracts/capabilities.yaml").write_text("schema: 1\n", encoding="utf-8")
    (repo / "knowledge/notes").mkdir(parents=True)
    (repo / "generated/reports").mkdir(parents=True)

    for root_name in (*DATA_ROOTS, "system", "operations"):
        with pytest.raises(WriteScopeError, match=f"protected root {root_name}/"):
            guard_tool_output_path(repo / root_name / "rogue.json", repo_root=repo)
        with pytest.raises(WriteScopeError, match=f"protected root {root_name}/"):
            guard_tool_output_path(
                repo / "generated" / ".." / root_name / "rogue.json", repo_root=repo,
            )

    link_dir = tmp_path / "evil-link"
    link_dir.symlink_to(repo / "knowledge/notes")
    with pytest.raises(WriteScopeError, match="symlink"):
        guard_tool_output_path(link_dir / "out.json", repo_root=repo)

    dangling = tmp_path / "dangling-out.json"
    dangling.symlink_to(repo / "knowledge/notes/missing.json")
    with pytest.raises(WriteScopeError, match="symlink"):
        guard_tool_output_path(dangling, repo_root=repo)

    ext = tmp_path / "outside" / "report.json"
    assert guard_tool_output_path(ext, repo_root=repo) == ext
    gen = repo / "generated/reports/eval.json"
    assert guard_tool_output_path(gen, repo_root=repo) == gen


def _case_insensitive(path: Path) -> bool:
    probe = path / "CaseProbe"
    probe.mkdir()
    try:
        return (path / "caseprobe").exists()
    finally:
        probe.rmdir()


def test_guard_tool_output_path_refuses_case_folded_protected_roots(tmp_path: Path):
    """Bar 4 v2 NF-1a: ``Knowledge/`` is ``knowledge/`` on default macOS APFS."""
    from contextlib import ExitStack

    from learning_os.store.contracts.write_scopes import (
        guard_tool_output_path,
        open_guarded_directory,
    )
    from learning_os.store.fingerprint import DATA_ROOTS

    repo = tmp_path / "repo"
    (repo / "system/contracts").mkdir(parents=True)
    (repo / "system/contracts/capabilities.yaml").write_text("schema: 1\n", encoding="utf-8")
    for root_name in (*DATA_ROOTS, "system", "operations"):
        (repo / root_name).mkdir(parents=True, exist_ok=True)
        for spelling in (root_name.capitalize(), root_name.upper()):
            with pytest.raises(WriteScopeError, match=f"protected root {root_name}/"):
                guard_tool_output_path(repo / spelling / "rogue.json", repo_root=repo)
            with pytest.raises(WriteScopeError, match=f"protected root {root_name}/"):
                guard_tool_output_path(repo / spelling / "rogue.json")
    if _case_insensitive(tmp_path):
        with ExitStack() as stack, pytest.raises(WriteScopeError, match="protected root knowledge/"):
            open_guarded_directory(repo / "Knowledge", stack)
    # A peer whose name merely starts like a protected root is still allowed.
    peer = repo / "generated" / "reports" / "Records-report.json"
    assert guard_tool_output_path(peer, repo_root=repo) == peer


def test_guard_admits_only_declared_generated_children_inside_a_repository(tmp_path: Path):
    """2A N-8: caller-chosen output in a repository lands only in a declared generated/ child."""
    from learning_os.store.contracts.write_scopes import (
        declared_generated_children,
        guard_tool_output_path,
    )

    repo = tmp_path / "repo"
    (repo / "system/contracts").mkdir(parents=True)
    (repo / "system/contracts/capabilities.yaml").write_text("schema: 1\n", encoding="utf-8")
    refused = (
        "archive/inbox/2026/rogue/.claude/settings.json",  # REVIEW-V3 N-8 reproduction
        "archive/workspaces/2026/x.md",
        "boards/atlas.canvas",
        "bases/shelf.base",
        "migration/reports/x.md",
        "tools/x.py",
        "tests/x.py",
        "workbench/x.md",
        "AGENTS.md",
        "generated/manifest.json",
        "generated/undeclared-child/x.json",
        "Generated/reports/x.json",
    )
    for relative in refused:
        with pytest.raises(WriteScopeError, match="repository|protected root"):
            guard_tool_output_path(repo / relative, repo_root=repo)
    with pytest.raises(WriteScopeError, match="repository root"):
        guard_tool_output_path(repo, repo_root=repo, allow_existing_dir=True)
    children = declared_generated_children()
    assert {"reports", ".text-cache", "material-search", "material-outlines"} <= children
    for child in children:
        admitted = repo / "generated" / child / "out.json"
        assert guard_tool_output_path(admitted, repo_root=repo) == admitted
    # The documented repo-confined scratch (build-write-envelope.md) stays admitted.
    scratch = repo / ".venv" / "tmp" / "review.json"
    assert guard_tool_output_path(scratch, repo_root=repo) == scratch
    outside = tmp_path / "scratch" / "out.json"
    assert guard_tool_output_path(outside, repo_root=repo) == outside


def test_owned_territory_comes_from_production_contracts_and_the_guard_refuses_it(tmp_path: Path):
    """2A N-1/N-8: owned territory is production-derived and contained in the guard's refusal."""
    from learning_os.store.contracts.write_scopes import (
        capability_write_scopes,
        guard_tool_output_path,
        in_owned_territory,
        owned_territory,
    )
    from learning_os.store.fingerprint import CANONICAL_ROOTS

    territory = owned_territory()
    assert {f"{name}/**" for name in CANONICAL_ROOTS} <= set(territory)
    assert {"operations/**", "bases/**", "boards/**"} <= set(territory)
    assert set(capability_write_scopes()) <= set(territory)
    assert "archive/inbox/**" in territory
    assert not any(pattern.startswith(("generated/", "tools/", "tests/")) for pattern in territory)
    assert in_owned_territory("operations/transactions/transaction-20991231-000000-001.yaml")
    assert in_owned_territory("system/contracts/capabilities.yaml")
    assert in_owned_territory("archive/inbox/2026/drop.md")
    assert not in_owned_territory("generated/reports/x.json")
    assert not in_owned_territory("system/developer/CODEMAP.md")

    repo = tmp_path / "repo"
    (repo / "system/contracts").mkdir(parents=True)
    (repo / "system/contracts/capabilities.yaml").write_text("schema: 1\n", encoding="utf-8")
    for pattern in territory:
        sample = "/".join("x" if part in {"*", "**"} else part for part in pattern.split("/"))
        with pytest.raises(WriteScopeError):
            guard_tool_output_path(repo / sample, repo_root=repo)


def test_boundary_write_refuses_parent_traversal_through_missing_child(tmp_path: Path):
    """Bar 4 v2 NF-1b: ``boundary/missing/../../records`` must not escape."""
    from learning_os.store.fs import WriteRefused, atomic_write_text_exclusive

    repo = tmp_path / "repo"
    (repo / "generated").mkdir(parents=True)
    (repo / "records").mkdir()
    manifest = repo / "records" / "materials-manifest.yaml"
    manifest.write_text("original\n", encoding="utf-8")
    escape = repo / "generated" / "missing_sub" / ".." / ".." / "records" / "materials-manifest.yaml"
    with pytest.raises(WriteRefused, match=r"'\.\.'"):
        atomic_write_text_exclusive(escape, "pwned\n", boundary=repo / "generated")
    assert manifest.read_text(encoding="utf-8") == "original\n"
    assert not (repo / "generated" / "missing_sub").exists()
    inside = repo / "generated" / "new" / "ok.txt"
    atomic_write_text_exclusive(inside, "ok\n", boundary=repo / "generated")
    assert inside.read_text(encoding="utf-8") == "ok\n"
