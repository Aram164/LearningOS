"""A8 generated docs: owner identity, refusing partial inputs and lossless writes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from learning_os.adapters.cli_parser import build_parser
from learning_os.contracts import doc_blocks as blocks
from learning_os.derive.semantics import PREDICATES
from learning_os.derive.validation.core import Validator

ROOT = Path(__file__).resolve().parents[1]


def _snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


@pytest.fixture
def docs(tmp_path):
    root = tmp_path / "repository"
    for name, relative in blocks.OWNERS.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Original {name}\n\nPreserved outside block.\n\n"
                        f"<!-- los:generated name={name} -->\nstale\n<!-- /los:generated -->\n"
                        "\nPreserved tail.\n")
    contracts = root / "system/contracts"
    contracts.mkdir()
    shutil.copy2(ROOT / "system/contracts/normative-corpus.schema.json", contracts)
    (contracts / "normative-corpus.yaml").write_text(yaml.safe_dump({
        "corpus_version": 1, "entrypoint": "system/OPERATOR.md", "documents": [
            {"path": relative, "class": "reference", "status": "current",
             "authority": "informative" if relative == "README.md" else "binding",
             "owner": "test", "summary": "Synthetic documentation projection."}
            for relative in blocks.OWNERS.values()]}))
    (contracts / "capabilities.yaml").write_text(yaml.safe_dump({
        "contract": "learningos-capabilities", "schema_version": 1, "contract_version": 2,
        "commands": {"fixture.write": {"handler": "fixture", "cli_command": "write",
                                      "writes": ["work/inbox/*"]}},
        "queries": {"fixture.read": {"handler": "fixture", "result": "fixture"}},
    }))
    requests = root / blocks.REQUESTS
    requests.mkdir(parents=True)
    (requests / "cli.fixture.schema.json").write_text(json.dumps({
        "x-los-cli-command": {"name": "fixture"}}))
    index = root / blocks.INDEX
    index.parent.mkdir(parents=True)
    transcript = index.parent / "fixture.md"
    transcript.write_text("# Executable fixture\n\n  $ true\n")
    index.write_text(yaml.safe_dump({"schema": 1, "sections": [
        {"doc": "system/OPERATOR.md", "heading": "## Fixture", "class": "procedure",
         "transcript": "system/procedures/fixture.md"},
        {"doc": "system/AI-ACTIONS.md", "heading": "## Human input", "class": "procedure",
         "untranscribable": "Needs a real learner decision | preserve reason."},
    ]}, sort_keys=False))
    return root


def _values(root):
    return blocks.collect(root, predicate_names=("predicate-b", "predicate-a"),
                          cli_command_names=("fixture",))


def test_write_is_lossless_idempotent_and_check_never_writes(docs):
    before = _snapshot(docs)
    values = _values(docs)
    assert len(blocks.check(docs, values)) == 4
    assert _snapshot(docs) == before
    changed = blocks.write(docs, values)
    assert len(changed) == 4
    assert blocks.write(docs, values) == ()
    assert blocks.check(docs, values) == []
    current = _snapshot(docs)
    assert blocks.check(docs, values) == []
    assert _snapshot(docs) == current
    assert "1 write capabilities, 1 queries" in (docs / blocks.OWNERS["capability-count"]).read_text()
    operator = (docs / "system/OPERATOR.md").read_text()
    assert "[Transcript](procedures/fixture.md)" in operator
    assert "Untranscribable: Needs a real learner decision \\| preserve reason." in operator
    for path in changed:
        assert "Preserved outside block." in path.read_text()
        assert path.read_text().endswith("\nPreserved tail.\n")


@pytest.mark.parametrize("mutation", ["unknown", "nested", "missing-end", "orphan-end", "malformed", "indented", "duplicate"])
def test_malformed_markers_refuse_before_any_write(docs, mutation):
    values = _values(docs)
    path = docs / blocks.OWNERS["procedure-index"]
    text = path.read_text()
    changes = {
        "unknown": text.replace("name=procedure-index", "name=unknown"),
        "nested": text.replace("\nstale\n", "\n<!-- los:generated name=procedure-index -->\n"),
        "missing-end": text.replace("<!-- /los:generated -->", ""),
        "orphan-end": "<!-- /los:generated -->\n" + text,
        "malformed": text.replace("name=procedure-index", "name='procedure-index'"),
        "indented": text.replace("<!-- los:generated", "  <!-- los:generated"),
        "duplicate": text + text,
    }
    path.write_text(changes[mutation])
    before = _snapshot(docs)
    assert blocks.check(docs, values)[0].path == "system/OPERATOR.md"
    with pytest.raises(blocks.DocBlockError):
        blocks.write(docs, values)
    assert _snapshot(docs) == before
    with pytest.raises(blocks.DocBlockError):
        _values(docs)


@pytest.mark.parametrize("relative", ["system/contracts/capabilities.yaml", blocks.INDEX,
                                      "system/SEMANTIC-CONTRACT.md", blocks.REQUESTS + "/cli.fixture.schema.json"])
def test_missing_metadata_owner_never_becomes_empty_success(docs, relative):
    (docs / relative).unlink()
    with pytest.raises(blocks.DocBlockError):
        _values(docs)


def test_actual_parser_mismatch_and_duplicate_bindings_refuse(docs):
    with pytest.raises(blocks.DocBlockError, match="actual parser command names differ"):
        blocks.collect(docs, predicate_names=("predicate",), cli_command_names=("wrong",))
    (docs / blocks.REQUESTS / "duplicate.schema.json").write_text(json.dumps({
        "x-los-cli-command": {"name": "fixture"}}))
    with pytest.raises(blocks.DocBlockError, match="unique"):
        _values(docs)


def test_owner_metadata_changes_invalidate_counts_and_lists(docs):
    blocks.write(docs, _values(docs))
    catalog_path = docs / "system/contracts/capabilities.yaml"
    catalog = yaml.safe_load(catalog_path.read_text())
    catalog["commands"]["second.write"] = dict(catalog["commands"]["fixture.write"])
    catalog_path.write_text(yaml.safe_dump(catalog))
    (docs / blocks.REQUESTS / "cli.fixture.schema.json").write_text(json.dumps({
        "x-los-cli-command": {"name": "second"}}))
    values = blocks.collect(docs, predicate_names=("a", "b", "c"), cli_command_names=("second",))
    assert {issue.path for issue in blocks.check(docs, values)} == {
        blocks.OWNERS[name] for name in ("capability-count", "predicate-count", "cli-command-list")}


@pytest.mark.parametrize("name", tuple(blocks.OWNERS))
def test_missing_required_marker_refuses_at_its_owner(docs, name):
    path = docs / blocks.OWNERS[name]
    path.write_text("# Owner remains but its generated block was removed.\n")
    with pytest.raises(blocks.DocBlockError) as caught:
        _values(docs)
    assert caught.value.path == blocks.OWNERS[name]


def test_wrong_owner_refuses_and_preserves_every_document(docs):
    values = _values(docs)
    readme = docs / "README.md"
    readme.write_text(readme.read_text() + "<!-- los:generated name=capability-count -->\n"
                      "wrong owner\n<!-- /los:generated -->\n")
    before = _snapshot(docs)
    with pytest.raises(blocks.DocBlockError, match="belongs in"):
        blocks.write(docs, values)
    assert _snapshot(docs) == before


def test_crlf_exterior_bytes_survive_write_and_read_only_check(docs):
    owner = docs / blocks.OWNERS["procedure-index"]
    owner.write_bytes(owner.read_bytes().replace(b"\n", b"\r\n"))
    before = owner.read_bytes()
    prefix, remainder = before.split(b"<!-- los:generated name=procedure-index -->\r\n", 1)
    _, suffix = remainder.split(b"<!-- /los:generated -->", 1)
    values = _values(docs)
    snapshot = _snapshot(docs)
    blocks.check(docs, values)
    assert _snapshot(docs) == snapshot
    blocks.write(docs, values)
    after = owner.read_bytes()
    assert after.startswith(prefix + b"<!-- los:generated name=procedure-index -->\r\n")
    assert after.endswith(b"<!-- /los:generated -->" + suffix)
    assert blocks.check(docs, values) == []
    current = _snapshot(docs)
    assert blocks.write(docs, values) == ()
    assert _snapshot(docs) == current


def test_marker_removal_on_a_production_document_copy_stays_blocking(tmp_path):
    root = tmp_path / "production-copy"
    shutil.copytree(ROOT / "system", root / "system")
    shutil.copy2(ROOT / "README.md", root)
    for name, relative in blocks.OWNERS.items():
        path = root / relative
        original = path.read_bytes()
        start = original.index(f"<!-- los:generated name={name} -->".encode())
        end = original.index(b"<!-- /los:generated -->", start) + len(b"<!-- /los:generated -->")
        path.write_bytes(original[:start] + original[end:])
        assert blocks.applies(root) is True
        validator = Validator(SimpleNamespace(root=root))
        validator.check_doc_blocks()
        assert any(issue.code == "DOC-BLOCK-STALE" and issue.path == relative
                   for issue in validator.issues)
        path.write_bytes(original)


def test_validator_reports_exact_owner_at_error_severity_and_fixture_boundary(docs, tmp_path):
    validator = Validator(SimpleNamespace(root=docs))
    validator.check_doc_blocks()
    assert {issue.path for issue in validator.issues} == set(blocks.OWNERS.values())
    assert all(issue.code == "DOC-BLOCK-STALE" and issue.severity == "E" for issue in validator.issues)
    (docs / blocks.INDEX).unlink()
    validator = Validator(SimpleNamespace(root=docs))
    validator.check_doc_blocks()
    assert len(validator.issues) == 1 and validator.issues[0].path == blocks.INDEX
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "README.md").write_text("# Synthetic learner data\n")
    assert blocks.applies(bare) is False
    (bare / "README.md").write_text("<!-- los:generated name=cli-command-list -->\n")
    assert blocks.applies(bare) is True
    with pytest.raises(blocks.DocBlockError):
        blocks.collect(bare, predicate_names=("predicate",))


def test_production_metadata_matches_real_parser_and_semantic_listing():
    parser = build_parser()
    names = [name for action in parser._actions if isinstance(action, argparse._SubParsersAction)
             for name in action.choices]
    values = blocks.collect(ROOT, predicate_names=PREDICATES, cli_command_names=names)
    assert set(values.cli_command_names) == set(names)
    completed = subprocess.run([sys.executable, str(ROOT / "tools/los.py"), "semantic", "--list"],
                               cwd=ROOT, capture_output=True, text=True, timeout=120,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert completed.returncode == 0, completed.stderr
    assert values.predicate_names == tuple(sorted(row["name"] for row in json.loads(completed.stdout)))


def test_production_tool_and_validator_use_identical_blocks_without_writes():
    values = blocks.collect(ROOT, predicate_names=PREDICATES)
    expected = blocks.check(ROOT, values)
    before = {relative: (ROOT / relative).read_bytes() for relative in blocks.OWNERS.values()}
    completed = subprocess.run([sys.executable, str(ROOT / "tools/doc_blocks.py"), "--check"],
                               cwd=ROOT, capture_output=True, text=True, timeout=120,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert completed.returncode == int(bool(expected)), completed.stderr
    validator = Validator(SimpleNamespace(root=ROOT))
    validator.check_doc_blocks()
    assert [(issue.message, issue.path) for issue in validator.issues] == [
        (issue.message, issue.path) for issue in expected]
    assert {relative: (ROOT / relative).read_bytes() for relative in blocks.OWNERS.values()} == before


@pytest.mark.parametrize("failure", [OSError("missing requests"), ValueError("malformed metadata"),
                                    KeyError("name"), TypeError("invalid binding")])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_tool_parser_dependency_failure_is_typed_and_never_writes(docs, monkeypatch, capsys, failure, mode):
    from learning_os.adapters import cli_parser

    spec = importlib.util.spec_from_file_location("doc_blocks_entrypoint", ROOT / "tools/doc_blocks.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    def broken_parser():
        raise failure

    monkeypatch.setattr(cli_parser, "build_parser", broken_parser)
    before = _snapshot(docs)
    assert tool.main([mode, "--root", str(docs)]) == 1
    captured = capsys.readouterr()
    assert "DOC-BLOCK-STALE" in captured.err
    assert blocks.REQUESTS in captured.err
    assert "Traceback" not in captured.err
    assert _snapshot(docs) == before


@pytest.mark.parametrize("malformed,owner", [
    ("procedure-class-list", blocks.INDEX),
    ("commands-null", "system/contracts/capabilities.yaml"),
    ("queries-null", "system/contracts/capabilities.yaml"),
    ("corpus-invalid-utf8", "system/contracts/normative-corpus.yaml"),
])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_malformed_metadata_is_typed_and_tool_never_writes(docs, monkeypatch, capsys,
                                                          malformed, owner, mode):
    from learning_os.adapters import cli_parser

    path = docs / owner
    if malformed == "corpus-invalid-utf8":
        path.write_bytes(b"\xff\xfe\n")
    else:
        declaration = yaml.safe_load(path.read_text())
        if malformed == "procedure-class-list":
            declaration["sections"][0]["class"] = []
        else:
            declaration[malformed.removesuffix("-null")] = None
        path.write_text(yaml.safe_dump(declaration))
    before = _snapshot(docs)
    with pytest.raises(blocks.DocBlockError) as caught:
        _values(docs)
    assert caught.value.path == owner
    parser = argparse.ArgumentParser()
    parser.add_subparsers().add_parser("fixture")
    monkeypatch.setattr(cli_parser, "build_parser", lambda: parser)
    spec = importlib.util.spec_from_file_location("doc_blocks_bad_metadata", ROOT / "tools/doc_blocks.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.main([mode, "--root", str(docs)]) == 1
    captured = capsys.readouterr()
    assert "DOC-BLOCK-STALE" in captured.err and owner in captured.err
    assert "Traceback" not in captured.err
    assert _snapshot(docs) == before


@pytest.mark.parametrize("location", ["README.md", ".", "../outside.md",
                                      "system/procedures/not-markdown.txt",
                                      "system/procedures/nested/unexecuted.md"])
@pytest.mark.parametrize("mode", ["--check", "--write"])
def test_transcript_links_bind_actual_runnable_population_without_writes(
    docs, monkeypatch, capsys, location, mode
):
    from learning_os.adapters import cli_parser

    target = docs / location
    if location not in ("README.md", "."):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# A file outside the actual transcript population.\n")
    index = docs / blocks.INDEX
    declaration = yaml.safe_load(index.read_text())
    declaration["sections"][0]["transcript"] = location
    index.write_text(yaml.safe_dump(declaration))
    before = _snapshot(docs)
    with pytest.raises(blocks.DocBlockError) as caught:
        _values(docs)
    assert caught.value.path == blocks.INDEX
    parser = argparse.ArgumentParser()
    parser.add_subparsers().add_parser("fixture")
    monkeypatch.setattr(cli_parser, "build_parser", lambda: parser)
    spec = importlib.util.spec_from_file_location("doc_blocks_bad_link", ROOT / "tools/doc_blocks.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.main([mode, "--root", str(docs)]) == 1
    captured = capsys.readouterr()
    assert "DOC-BLOCK-STALE" in captured.err and blocks.INDEX in captured.err
    assert "Traceback" not in captured.err
    assert _snapshot(docs) == before
