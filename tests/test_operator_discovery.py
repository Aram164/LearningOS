"""The operator surface an agent meets first: one catalogue, one kind, one scope.

The capability catalogue, the CLI operation contract and the request schemas
each answered a different part of "what does this command do, and how do I
find it". The operator contract told the reader that one of them was the way
in, and refused the names the contract itself used: ``capabilities NAME
--json`` wanted the dotted capability id while every other document wrote the
command. Nine operations declared one kind and ran under another, and nothing
compared them.

These tests hold the joined surface together: every command appears once,
with the kind the runtime gives it; the discovery index names every command;
a name resolves to a capability, a command or a task; and the operator entry
table is the task contract rather than a copy of it that can drift.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
from repo_builders import run_los

from learning_os.store.contracts.cli_operations import load_cli_operations
from learning_os.store.contracts.task_scope import (
    entry_read_verbs,
    load_task_scope,
    operator_entry_table,
    render_entry_table,
)
from learning_os.store.contracts.verb_catalogue import build_verb_catalogue

ROOT = Path(__file__).resolve().parents[1]


def _parser_commands() -> set[str]:
    import los

    parser = los.build_parser()
    return {
        name
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
        for name in action.choices
    }


def _capability_verbs(root: Path) -> set[str]:
    import yaml

    catalogue = yaml.safe_load(
        (root / "system/contracts/capabilities.yaml").read_text(encoding="utf-8"))
    verbs = set()
    for section in ("queries", "commands", "internal_commands"):
        for row in (catalogue.get(section) or {}).values():
            command = row.get("cli_command")
            if command:
                verbs.add(command)
    return verbs


def test_the_catalogue_names_every_cli_command_exactly_once():
    root = ROOT
    catalogue = build_verb_catalogue(root)
    commands = _parser_commands()
    names = [row.verb for row in catalogue.verbs]
    assert len(names) == len(set(names)), "a command is listed twice"
    assert set(names) == commands, (
        "the catalogue and the parser disagree about the command surface")
    for row in catalogue.verbs:
        assert row.kind in {"query", "command", "porcelain", "tool"}
        assert row.surface in {"catalog", "internal", "cli-only"}


def test_the_two_contracts_cover_the_command_surface_between_them():
    """Neither contract claims a command the other already declares."""
    root = ROOT
    catalogue_verbs = _capability_verbs(root)
    operation_verbs = {op.cli_command for op in load_cli_operations(root).values()}
    assert not catalogue_verbs & operation_verbs, (
        "a command is declared by both contracts")
    assert catalogue_verbs | operation_verbs == _parser_commands()


def test_the_discovery_index_names_every_command_the_contract_uses():
    result = run_los(ROOT, "capabilities", "--compact", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload["verbs"]) == _parser_commands()
    # The four the operator contract routes to, which the index used to omit.
    for command in ("resume", "inspect", "semantic", "intelligence-scan"):
        assert command in payload["verbs"]


def test_a_name_resolves_to_a_capability_a_command_or_a_task():
    catalogue = build_verb_catalogue(ROOT)
    for name, expected in (
        ("note.create", "note-create"),
        ("note-create", "note-create"),
        ("resume", "resume"),
        ("semantic", "semantic"),
    ):
        result = run_los(ROOT, "capabilities", name, "--json")
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["verb"]["verb"] == expected
        assert payload["verb"]["capability"] == catalogue.verb(expected).capability


def test_a_task_name_answers_what_binds_it():
    result = run_los(ROOT, "capabilities", "governance-question", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    task = payload["task"]
    assert task["id"] == "governance-question"
    assert "system/OPERATOR.md" in task["scope"]
    assert "system/SEMANTIC-CONTRACT.md" in task["scope"]
    assert task["procedures"]
    assert [row["verb"] for row in payload["verbs"]] == ["semantic"]


def test_an_unknown_name_is_refused_without_output():
    result = run_los(ROOT, "capabilities", "not-a-thing", "--json")
    assert result.returncode == 2
    assert not result.stdout
    assert "unknown or non-public capability" in result.stderr


def test_the_entry_table_is_the_task_contract():
    tasks = load_task_scope(ROOT)
    assert render_entry_table(tasks) == operator_entry_table(ROOT)


def test_a_task_scope_names_only_current_binding_documents():
    import yaml

    corpus = yaml.safe_load(
        (ROOT / "system/contracts/normative-corpus.yaml").read_text(encoding="utf-8"))
    binding = {
        document["path"]
        for document in corpus["documents"]
        if document["authority"] == "binding" and document["status"] == "current"
    }
    for task in load_task_scope(ROOT).values():
        assert task.scope, task.id
        for document in task.scope:
            # A whole binding document, or one section of one (`path#anchor`).
            assert document.partition("#")[0] in binding, (task.id, document)
        assert "system/OPERATOR.md" in task.scope, task.id


@pytest.mark.parametrize("change", ["missing", "extra", "unknown"])
def test_corpus_applicability_must_agree_in_both_directions(mini_repo, change):
    import yaml

    from learning_os.store.contracts.task_scope import TaskScopeError

    path = mini_repo / "system/contracts/normative-corpus.yaml"
    corpus = yaml.safe_load(path.read_text())
    document = next(d for d in corpus["documents"] if d["path"] == "system/SEMANTIC-CONTRACT.md")
    if change == "missing":
        document["applies_to"] = []
    else:
        document["applies_to"].append(
            "discover-capabilities" if change == "extra" else "unknown-task")
    path.write_text(yaml.safe_dump(corpus))
    with pytest.raises(TaskScopeError, match="applicability disagrees|unknown tasks"):
        load_task_scope(mini_repo)


def test_corpus_applicability_is_optional_for_legacy_declarations(mini_repo):
    import yaml

    path = mini_repo / "system/contracts/normative-corpus.yaml"
    corpus = yaml.safe_load(path.read_text())
    for document in corpus["documents"]:
        document.pop("applies_to", None)
    path.write_text(yaml.safe_dump(corpus))
    assert load_task_scope(mini_repo)


def test_every_entry_read_names_a_command_that_exists():
    commands = _parser_commands()
    for task in load_task_scope(ROOT).values():
        verbs = entry_read_verbs(task.entry_read)
        if task.procedure_text:
            assert not verbs, (task.id, task.entry_read)
            continue
        assert verbs, task.id
        for verb in verbs:
            assert verb in commands, (task.id, verb)


@pytest.mark.parametrize("name", ["resume", "semantic", "intelligence-scan", "goal"])
def test_a_command_the_contract_routes_to_is_reachable_by_its_own_name(name):
    result = run_los(ROOT, "capabilities", name, "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["verb"]["verb"] == name
    assert payload["verb"]["operation"]


def test_a_task_read_inlines_the_sections_it_binds_within_its_bound():
    """`capabilities TASK --json` carries the reading (agent-cost plan D7).

    Every procedure and every scoped section arrives inline, the whole read
    stays within ~3k tokens, and a cut section says what it left out and
    where the rest is, so no task starts by opening whole documents.
    """
    from learning_os.store.contracts.task_scope import READ_TOTAL_LIMIT

    for task in load_task_scope(ROOT).values():
        result = run_los(ROOT, "capabilities", task.id, "--json")
        assert result.returncode == 0, result.stderr
        read = json.loads(result.stdout)["read"]
        expected = [link.target for link in task.procedures] + [
            entry for entry in task.scope if "#" in entry]
        assert [row["ref"] for row in read] == list(dict.fromkeys(expected)), task.id
        assert sum(len(row["text"]) for row in read) <= READ_TOTAL_LIMIT, task.id
        for row in read:
            assert row["text"].startswith("## ") or "omitted_chars" in row, row["ref"]
            if "omitted_chars" in row:
                assert row["omitted_chars"] > 0 and "section '## " in row["rest"]


def test_the_log_task_read_carries_the_one_call_write():
    result = run_los(ROOT, "capabilities", "log-a-line", "--json")
    assert result.returncode == 0, result.stderr
    text = "".join(row["text"] for row in json.loads(result.stdout)["read"])
    assert "--submit" in text
    assert "stage.note.write" in text and "capture.create" in text


def test_a_scoped_section_must_exist(mini_repo):
    from learning_os.store.contracts.task_scope import TaskScopeError

    (mini_repo / "system/SEMANTIC-CONTRACT.md").write_text(
        "# Semantic contract\n\n## A real section\n\nText.\n", encoding="utf-8")
    path = mini_repo / "system/contracts/task-scope.yaml"
    text = path.read_text(encoding="utf-8")
    assert "      - system/SEMANTIC-CONTRACT.md\n" in text
    path.write_text(text.replace(
        "      - system/SEMANTIC-CONTRACT.md\n",
        "      - system/SEMANTIC-CONTRACT.md#no-such-section\n", 1), encoding="utf-8")
    with pytest.raises(TaskScopeError, match="section that does not exist"):
        load_task_scope(mini_repo)
