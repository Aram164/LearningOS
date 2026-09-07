"""Smaller discovery and shared reads retain complete, current evidence."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from test_cli import run_los

from learning_os.commands import query, reads
from learning_os.loader import load_repo


def test_compact_catalogue_preserves_all_public_names_and_rules(mini_repo):
    full = run_los(mini_repo, "capabilities", "--json")
    compact = run_los(mini_repo, "capabilities", "--compact", "--json")
    assert full.returncode == compact.returncode == 0
    expected, actual = json.loads(full.stdout), json.loads(compact.stdout)
    for section in ("queries", "commands"):
        assert actual[section] == sorted(expected[section])
    assert actual["rules"] == expected["rules"]
    assert actual["operator_contract"] == expected["operator_contract"]
    assert len(compact.stdout) < len(full.stdout) / 3


def test_named_capability_includes_exact_definition_and_schema(mini_repo):
    full = json.loads(run_los(mini_repo, "capabilities", "--json").stdout)
    result = run_los(mini_repo, "capabilities", "module.plan.import", "--json")
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert actual["commands"] == {
        "module.plan.import": full["commands"]["module.plan.import"],
    }
    assert actual["queries"] == {}
    assert actual["rules"] == full["rules"]
    assert actual["payload_schema"] == json.loads(
        (mini_repo / actual["payload_schema_path"]).read_text(),
    )
    assert "expected_snapshot" not in actual["payload_schema"]["properties"]


def test_named_query_preserves_definition_without_inventing_a_write_schema(mini_repo):
    result = run_los(mini_repo, "capabilities", "operator.bootstrap")
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert list(actual["queries"]) == ["operator.bootstrap"]
    assert actual["commands"] == {}
    assert "payload_schema" not in actual


@pytest.mark.parametrize("command", ["cmd_note_read", "content_search"])
def test_note_queries_parse_only_notes_but_guard_the_whole_snapshot(
    mini_repo, monkeypatch, capsys, command,
):
    from learning_os.loading import yamlio

    repo = load_repo(mini_repo)
    note = next(iter(repo.notes.values()))
    parsed = []
    safe_yaml = yamlio._safe_yaml

    def tracked_parse(text):
        parsed.append(text)
        return safe_yaml(text)

    monkeypatch.setattr(yamlio, "_safe_yaml", tracked_parse)
    args = SimpleNamespace(
        root=str(mini_repo), note_id=note.id, query=note.id, type="note",
        offset=0, limit=100, expected_snapshot=None,
    )
    invoke = getattr(reads, command)
    assert invoke(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(parsed) == len(repo.notes)
    if command == "cmd_note_read":
        assert payload["content"] == note.path.read_text()[:100]
    else:
        assert payload["total"] == 1
        assert payload["items"][0]["id"] == note.id

    # A change outside the note owner must still invalidate continuation.
    modules = mini_repo / "records/modules.yaml"
    modules.write_text(modules.read_text() + "\n# changed while reading\n")
    args.expected_snapshot = payload["snapshot_id"]
    args.offset = 1
    parsed.clear()
    assert invoke(args) == 3
    output = capsys.readouterr()
    assert not output.out
    assert "snapshot changed" in output.err
    assert parsed == []


@pytest.mark.parametrize("arguments", [
    ("../../private",), ("unknown",), ("module.plan.import", "--compact"),
])
def test_bad_capability_selection_has_no_partial_output(mini_repo, arguments):
    result = run_los(mini_repo, "capabilities", *arguments)
    assert result.returncode == 2
    assert not result.stdout


@pytest.mark.parametrize("content", [None, "not json", "[]"])
def test_named_capability_refuses_missing_or_malformed_schema(mini_repo, content):
    path = mini_repo / "system/schema/capabilities/module.plan.import.schema.json"
    if content is None:
        path.unlink()
    else:
        path.write_text(content)
    result = run_los(mini_repo, "capabilities", "module.plan.import")
    assert result.returncode == 2
    assert "payload schema" in result.stderr
    assert not result.stdout


def test_batch_matches_single_reads_and_preserves_requested_order(mini_repo):
    repo = load_repo(mini_repo)
    ids = [next(iter(repo.notes)), *list(repo.concepts)[:2]]
    singles = [json.loads(run_los(mini_repo, "inspect", rid).stdout) for rid in ids]
    result = run_los(mini_repo, "inspect", *ids)
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert actual["requested_ids"] == ids
    assert actual["records"] == singles
    assert actual["snapshot_id"].startswith("sha256:")
    assert actual["contract"] == "record-batch"


def test_batch_builds_once_and_preserves_aliases(mini_repo, monkeypatch, capsys):
    calls = []

    def manifest(root):
        calls.append(root)
        return {"project_aliases": {"old": "new"}, "records": [{"id": "new"}]}

    monkeypatch.setattr(reads, "_fresh_manifest", manifest)
    args = SimpleNamespace(root=str(mini_repo), id="old", more_ids=["new", "old"])
    assert query.cmd_inspect(args) == 0
    assert len(calls) == 1
    assert json.loads(capsys.readouterr().out)["records"] == [
        {"id": "new", "resolved_from": "old"}, {"id": "new"},
        {"id": "new", "resolved_from": "old"},
    ]


def test_batch_refuses_changed_snapshot_before_emitting_records(mini_repo, monkeypatch, capsys):
    monkeypatch.setattr(reads, "_fresh_manifest", lambda root: {"records": [{"id": "a"}]})
    fingerprints = iter(["a" * 64, "b" * 64])
    monkeypatch.setattr(reads, "canonical_fingerprint", lambda root: next(fingerprints))
    assert query.cmd_inspect(SimpleNamespace(root=str(mini_repo), id="a", more_ids=["a"])) == 3
    assert not capsys.readouterr().out


def test_batch_refuses_missing_id_and_oversized_requests(mini_repo):
    note_id = next(iter(load_repo(mini_repo).notes))
    for ids in ([note_id, "missing"], [note_id] * 21):
        result = run_los(mini_repo, "inspect", *ids)
        assert result.returncode == 2
        assert not result.stdout
