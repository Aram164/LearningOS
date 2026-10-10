"""Smaller discovery and shared reads retain complete, current evidence."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from repo_builders import run_los

from learning_os import fingerprint
from learning_os.commands import reads
from learning_os.loader import load_repo
from learning_os.ops._legacy_plumbing import _json_layout


def test_entry_doc_commands_execute_through_the_declared_gateway(mini_repo, tmp_path):
    """Run the entry docs' concrete commands, including one governed write."""
    from gateway_helpers import approved_v2_envelope
    from repo_builders import add_curriculum

    from learning_os.warning_baseline import collect, write_baseline

    root = Path(__file__).resolve().parents[1]
    operator = (root / "system/OPERATOR.md").read_text(encoding="utf-8")
    claude = (root / "system/CLAUDE.md").read_text(encoding="utf-8")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    readme = " ".join((root / "README.md").read_text(encoding="utf-8").split())
    blocks = re.findall(r"```bash\n(.*?)\n```", operator, flags=re.DOTALL)
    commands = [line for block in blocks for line in block.splitlines() if line.strip()]
    assert commands == [
        ".venv/bin/python tools/warning_baseline.py --check",
        ".venv/bin/python tools/los.py capabilities --compact --json",
        ".venv/bin/python tools/los.py capabilities stage.progress.update --json",
        ".venv/bin/python tools/los.py capability stage.progress.update --payload-file ENVELOPE.json",
    ]
    # Task-shaped entry: the unconditional startup read is documented in
    # every entry doc, the open-question bootstrap likewise, while the
    # stage.progress pair below is the governed-write example executed
    # further down.
    assert commands[1] in agents
    assert commands[1] in readme
    assert "bootstrap --brief" in agents
    assert "bootstrap --brief" in readme
    bootstrap_section = claude.split("## 2. Bootstrap order", 1)[1].split("## 3.", 1)[0]
    assert "capabilities --compact --json" in " ".join(bootstrap_section.split())
    assert "bootstrap --brief" in " ".join(bootstrap_section.split())
    assert ".venv/bin/python tools/validate.py --compact" in claude
    assert ".venv/bin/python tools/warning_baseline.py --check" in claude

    add_curriculum(mini_repo)
    write_baseline(mini_repo, collect(mini_repo)[0], "entry-doc fixture")
    envelope = approved_v2_envelope(
        mini_repo, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="entry-doc-stage-progress",
    )
    envelope_path = tmp_path / "ENVELOPE.json"
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    for command in commands:
        executable, script, *args = shlex.split(command)
        assert executable == ".venv/bin/python"
        args = [str(envelope_path) if arg == "ENVELOPE.json" else arg
                for arg in args]
        proc = subprocess.run(
            [sys.executable, str(root / script), "--root", str(mini_repo), *args],
            capture_output=True, text=True, timeout=120,
        )
        assert proc.returncode == 0, (command, proc.stdout, proc.stderr)
        if script.endswith("los.py"):
            body = json.loads(proc.stdout)
            if args[0] == "capability":
                assert body["ok"] is True
                assert body["receipt_path"]
    validation = subprocess.run(
        [sys.executable, str(root / "tools/validate.py"), "--compact",
         "--root", str(mini_repo)],
        capture_output=True, text=True, timeout=120,
    )
    assert validation.returncode == 0, validation.stdout + validation.stderr
    assert "0 error" in validation.stdout


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
    if command == "cmd_note_read":
        import los
        from learning_os.ops.pipeline import run_cli

        parser = los.build_parser()
        cli_args = parser.parse_args(
            ["note-read", note.id, "--offset", "0", "--limit", "100"])
        outcome = run_cli(mini_repo, "cli.note-read", cli_args)
        assert outcome.exit_code == 0
        payload = json.loads(outcome.stdout)
    else:
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
    parsed.clear()
    if command == "cmd_note_read":
        cli_args = parser.parse_args(
            ["note-read", note.id, "--offset", "1", "--limit", "100",
             "--expected-snapshot", payload["snapshot_id"]])
        outcome = run_cli(mini_repo, "cli.note-read", cli_args)
        assert outcome.exit_code == 3
        assert not outcome.stdout
        assert "snapshot changed" in outcome.stderr
    else:
        args.expected_snapshot = payload["snapshot_id"]
        args.offset = 1
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


def test_batch_builds_once_and_preserves_aliases(mini_repo, monkeypatch):
    from learning_os.ops.context import OpContext
    from learning_os.ops.handlers import platform as platform_handlers

    calls = []

    def manifest(root, *, snapshot_id=None):
        calls.append(root)
        return {"project_aliases": {"old": "new"}, "records": [{"id": "new"}]}, None

    monkeypatch.setattr(platform_handlers, "_fresh_manifest_and_repo", manifest)
    ctx = OpContext(root=mini_repo, operation="cli.inspect",
                    channel="operator", invocation="query", gateway=None)
    result = platform_handlers.inspect(
        ctx, {"id": "old", "more_ids": ["new", "old"]})
    assert len(calls) == 1
    assert result.payload["records"] == [
        {"id": "new", "resolved_from": "old"}, {"id": "new"},
        {"id": "new", "resolved_from": "old"},
    ]


def test_batch_refuses_changed_snapshot_before_emitting_records(mini_repo, monkeypatch):
    from learning_os.domain.failures import StaleSnapshot
    from learning_os.ops import _legacy_plumbing as plumbing
    from learning_os.ops.context import OpContext
    from learning_os.ops.handlers import platform as platform_handlers

    monkeypatch.setattr(platform_handlers, "_fresh_manifest_and_repo",
                        lambda root, **kwargs: ({"records": [{"id": "a"}]}, None))
    fingerprints = iter(["a" * 64, "b" * 64])
    monkeypatch.setattr(plumbing, "canonical_fingerprint", lambda root: next(fingerprints))
    ctx = OpContext(root=mini_repo, operation="cli.inspect",
                    channel="operator", invocation="query", gateway=None)
    with pytest.raises(StaleSnapshot, match="snapshot changed"):
        platform_handlers.inspect(ctx, {"id": "a", "more_ids": ["a"]})


def test_json_layout_follows_stream_and_inspect_json_is_equivalent(mini_repo, monkeypatch):
    from learning_os.ops.handlers import platform as platform_handlers
    from learning_os.ops.pipeline import run_cli

    class Terminal(StringIO):
        def isatty(self):
            return True

    terminal, pipe = Terminal(), StringIO()
    assert _json_layout(terminal) == {"indent": 2}
    assert _json_layout(pipe) == {"separators": (",", ":")}
    monkeypatch.setattr(platform_handlers, "_fresh_manifest_and_repo", lambda root: ({
        "records": [{"id": "record-demo", "title": "Demo"}],
    }, None))
    args = SimpleNamespace(root=str(mini_repo), id="record-demo", more_ids=[])
    outputs = []
    for stream in (terminal, pipe):
        with redirect_stdout(stream):
            outcome = run_cli(mini_repo, "cli.inspect", args)
        assert outcome.exit_code == 0, outcome.stderr
        outputs.append(outcome.stdout)
    terminal_out, pipe_out = outputs
    assert json.loads(terminal_out) == json.loads(pipe_out)
    assert "\n  " in terminal_out
    assert "\n  " not in pipe_out


@pytest.mark.parametrize("command", ["brief", "compact", "inspect"])
def test_bounded_read_hashes_thrice_with_seeded_manifest(
    mini_repo, monkeypatch, capsys, command,
):
    from learning_os.ops import _legacy_plumbing as plumbing

    original = fingerprint.canonical_fingerprint
    calls = []

    def counted(root):
        calls.append(root)
        return original(root)

    monkeypatch.setattr(plumbing, "canonical_fingerprint", counted)
    monkeypatch.setattr(fingerprint, "canonical_fingerprint", counted)
    if command == "inspect":
        from learning_os.ops.pipeline import run_cli

        repo = load_repo(mini_repo)
        args = SimpleNamespace(root=str(mini_repo), id=next(iter(repo.notes)),
                               more_ids=[next(iter(repo.concepts))])
        outcome = run_cli(mini_repo, "cli.inspect", args)
        assert outcome.exit_code == 0, outcome.stderr
        payload = json.loads(outcome.stdout)
    else:
        from learning_os.ops.pipeline import run_cli

        args = SimpleNamespace(root=str(mini_repo), brief=(command == "brief"),
                               compact=(command == "compact"),
                               expected_snapshot=None, offset=0, limit=10)
        outcome = run_cli(mini_repo, "cli.bootstrap", args)
        assert outcome.exit_code == 0, outcome.stderr
        payload = json.loads(outcome.stdout)
    assert payload["snapshot_id"].startswith("sha256:")
    # Snapshot, rebuild re-walk, revalidation. The rebuild walk always ran
    # here (the fixture keeps no stored manifest); it only became visible
    # to this count when the fresh-manifest closure moved into the patched
    # module.
    assert len(calls) == 3


def test_batch_refuses_missing_id_and_oversized_requests(mini_repo):
    note_id = next(iter(load_repo(mini_repo).notes))
    for ids in ([note_id, "missing"], [note_id] * 21):
        result = run_los(mini_repo, "inspect", *ids)
        assert result.returncode == 2
        assert not result.stdout
