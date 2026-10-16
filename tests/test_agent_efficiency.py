"""Smaller discovery and shared reads retain complete, current evidence."""

from __future__ import annotations

import json
import re
import subprocess
import uuid
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from repo_builders import run_los

from learning_os.app.encoders import json_layout as _json_layout
from learning_os.store import fingerprint
from learning_os.store.loader import load_repo


def test_entry_doc_commands_execute_through_the_declared_gateway(tmp_path):
    """Run the linked Scrut inputs, including their write/effect witnesses."""
    from test_procedures import (
        _check_procedure_audit,
        _procedure_child_env,
        _scrut_bin,
    )

    root = Path(__file__).resolve().parents[1]
    operator = (root / "system/OPERATOR.md").read_text(encoding="utf-8")
    claude = (root / "system/CLAUDE.md").read_text(encoding="utf-8")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    readme = " ".join((root / "README.md").read_text(encoding="utf-8").split())
    procedures = root / "system/procedures"
    start_here = (procedures / "start-here.md").read_text(encoding="utf-8")
    session_end = (procedures / "end-a-session.md").read_text(encoding="utf-8")
    bootstrap_order = (procedures / "bootstrap-order.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## .+$", operator, flags=re.MULTILINE)
    assert headings == [
        "## What binds, and what does not", "## What \"clean\" means",
        "## Start here", "## Product hierarchy", "## Hard boundaries",
        "## Procedures", "## Capture routing",
    ]
    assert "### Unit workflow" in operator
    assert "### Shelving and session closure" in operator
    entry_map = operator.split("## Start here", 1)[1].split("## Product hierarchy", 1)[0]
    assert "```" not in entry_map
    assert "procedures/start-here.md" in entry_map
    assert "procedures/revise-an-existing-plan.md" in entry_map
    discovery = ".venv/bin/python tools/los.py capabilities --compact --json"
    assert discovery in agents
    assert discovery in readme
    # Check the actual runner inputs, not inert bash examples retained only
    # to preserve original rule text. The full transcripts execute below.
    assert "$ los capabilities --compact --json" in start_here
    assert "$ los capabilities stage.progress.update --json" in session_end
    assert "$ los capability stage.progress.update --payload-file" in session_end
    assert "tools/warning_baseline.py --root \"$LOS_FX\" --check" in start_here
    assert "$ $H/los-assert-receipt --last --capability stage.progress.update" in session_end
    assert "$ $H/los-assert-file curriculum/modules/module-demo/units/" in session_end
    assert re.search(r'"validation"\s*:\s*"0 error\(s\)', session_end)

    assert "bootstrap --brief" in agents
    assert "bootstrap --brief" in readme
    bootstrap_section = claude.split("## 2. Bootstrap order", 1)[1].split("## 3.", 1)[0]
    assert "procedures/bootstrap-order.md" in bootstrap_section
    assert "capabilities --compact --json" in " ".join(bootstrap_order.split())
    assert "bootstrap --brief" in " ".join(bootstrap_order.split())
    assert ".venv/bin/python tools/validate.py --compact" in claude
    assert ".venv/bin/python tools/warning_baseline.py --check" in claude

    scrut = _scrut_bin()
    assert scrut.is_file(), f"Scrut binary missing: {scrut}"
    for stem in ("start-here", "end-a-session"):
        transcript = procedures / f"{stem}.md"
        log_path = tmp_path / f"entry-{stem}.audit.jsonl"
        token = f"entry-procedure-{uuid.uuid4().hex}"
        proc = subprocess.run(
            [str(scrut), "test", str(transcript)],
            capture_output=True, text=True, timeout=600, cwd=root,
            env=_procedure_child_env(log_path=log_path, token=token),
        )
        assert proc.returncode == 0, (
            f"{transcript.name} failed:\n{proc.stdout}\n{proc.stderr}")
        _check_procedure_audit(transcript.name, log_path)


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


def test_operator_entry_map_links_resolve_to_executable_cases():
    """The map stays useful after procedures replace embedded command lists."""
    root = Path(__file__).resolve().parents[1]
    operator = (root / "system/OPERATOR.md").read_text(encoding="utf-8")
    entry_map = operator.split("## Start here", 1)[1].split(
        "## Product hierarchy", 1)[0]
    links = re.findall(r"\]\((procedures/[^)#]+)#([^)]+)\)", entry_map)
    assert len(links) >= 12
    for relative, fragment in links:
        path = root / "system" / relative
        assert path.is_file(), relative
        text = path.read_text(encoding="utf-8")
        headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
        slugs = {
            re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-"):
            heading
            for heading in headings
        }
        assert fragment in slugs, (relative, fragment)
        section = text.split("## " + slugs[fragment] + "\n", 1)[1].split(
            "\n## ", 1)[0]
        assert "```scrut" in section, (relative, fragment)


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
    mini_repo, monkeypatch, command,
):
    from learning_os.store.loading import yamlio

    repo = load_repo(mini_repo)
    note = next(iter(repo.notes.values()))
    parsed = []
    safe_yaml = yamlio._safe_yaml

    def tracked_parse(text):
        parsed.append(text)
        return safe_yaml(text)

    monkeypatch.setattr(yamlio, "_safe_yaml", tracked_parse)
    import los
    from learning_os.app.pipeline import run_cli

    parser = los.build_parser()
    if command == "cmd_note_read":
        cli_args = parser.parse_args(
            ["note-read", note.id, "--offset", "0", "--limit", "100"])
        outcome = run_cli(mini_repo, "note.content", cli_args)
        assert outcome.exit_code == 0
        payload = json.loads(outcome.stdout)
    else:
        cli_args = parser.parse_args(
            ["search", note.id, "--content", "--offset", "0", "--limit", "100"])
        outcome = run_cli(mini_repo, "note.search", cli_args)
        assert outcome.exit_code == 0
        payload = json.loads(outcome.stdout)
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
        outcome = run_cli(mini_repo, "note.content", cli_args)
        assert outcome.exit_code == 3
        assert not outcome.stdout
        assert "snapshot changed" in outcome.stderr
    else:
        cli_args = parser.parse_args(
            ["search", note.id, "--content", "--offset", "1", "--limit", "100",
             "--expected-snapshot", payload["snapshot_id"]])
        outcome = run_cli(mini_repo, "note.search", cli_args)
        assert outcome.exit_code == 3
        assert not outcome.stdout
        assert "snapshot changed" in outcome.stderr
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
    from learning_os.app.context import OpContext
    from learning_os.app.handlers import platform as platform_handlers

    calls = []

    def manifest(root, *, snapshot_id=None):
        calls.append(root)
        return {"project_aliases": {"old": "new"}, "records": [{"id": "new"}]}, None

    monkeypatch.setattr(platform_handlers, "_fresh_manifest_and_repo", manifest)
    ctx = OpContext(root=mini_repo, operation="project.inspect",
                    channel="operator", invocation="query", gateway=None)
    result = platform_handlers.inspect(
        ctx, {"id": "old", "more_ids": ["new", "old"]})
    assert len(calls) == 1
    assert result.payload["records"] == [
        {"id": "new", "resolved_from": "old"}, {"id": "new"},
        {"id": "new", "resolved_from": "old"},
    ]


def test_batch_refuses_changed_snapshot_before_emitting_records(mini_repo, monkeypatch):
    from learning_os.app.context import OpContext
    from learning_os.app.handlers import platform as platform_handlers
    from learning_os.domain.failures import StaleSnapshot
    from learning_os.store import fingerprint as plumbing

    monkeypatch.setattr(platform_handlers, "_fresh_manifest_and_repo",
                        lambda root, **kwargs: ({"records": [{"id": "a"}]}, None))
    fingerprints = iter(["a" * 64, "b" * 64])
    monkeypatch.setattr(plumbing, "canonical_fingerprint", lambda root: next(fingerprints))
    ctx = OpContext(root=mini_repo, operation="project.inspect",
                    channel="operator", invocation="query", gateway=None)
    with pytest.raises(StaleSnapshot, match="snapshot changed"):
        platform_handlers.inspect(ctx, {"id": "a", "more_ids": ["a"]})


def test_json_layout_follows_stream_and_inspect_json_is_equivalent(mini_repo, monkeypatch):
    from learning_os.app.handlers import platform as platform_handlers
    from learning_os.app.pipeline import run_cli

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
            outcome = run_cli(mini_repo, "project.inspect", args)
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
    from learning_os.app import projection as plumbing

    original = fingerprint.canonical_fingerprint
    calls = []

    def counted(root):
        calls.append(root)
        return original(root)

    monkeypatch.setattr(plumbing, "canonical_fingerprint", counted)
    monkeypatch.setattr(fingerprint, "canonical_fingerprint", counted)
    if command == "inspect":
        from learning_os.app.pipeline import run_cli

        repo = load_repo(mini_repo)
        args = SimpleNamespace(root=str(mini_repo), id=next(iter(repo.notes)),
                               more_ids=[next(iter(repo.concepts))])
        outcome = run_cli(mini_repo, "project.inspect", args)
        assert outcome.exit_code == 0, outcome.stderr
        payload = json.loads(outcome.stdout)
    else:
        from learning_os.app.pipeline import run_cli

        args = SimpleNamespace(root=str(mini_repo), brief=(command == "brief"),
                               compact=(command == "compact"),
                               expected_snapshot=None, offset=0, limit=10)
        outcome = run_cli(mini_repo, "operator.bootstrap", args)
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
