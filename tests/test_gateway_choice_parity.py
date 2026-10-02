"""CLI-vs-gateway choice parity (#87).

The ten enumerated payload fields must accept and refuse exactly the same
values on both documented interfaces: the bare CLI (argparse `choices`)
and the capability gateway (generated schema `enum` plus the
`payload_to_namespace` defence in depth). Before this, the gateway
accepted anything — and `stage.progress.update` recorded an unknown
status as `skipped`.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_call
from jsonschema import Draft202012Validator

import los
from learning_os.commands.support import WriteRefused
from learning_os.contracts.payloads import payload_to_namespace, subparsers
from learning_os.fingerprint import canonical_fingerprint

SHA = "sha256:" + "0" * 64

# capability, CLI command, enumerated field, pinned vocabulary, argv and
# payload templates. `{v}` is the probed value; the templates supply every
# other required field so the value under test decides alone.
CASES = [
    {
        "capability": "stage.progress.update",
        "command": "stage-progress",
        "field": "status",
        "valid": ["active", "paused", "complete", "skipped", "revisit"],
        "argv": lambda v: ["unit-x", "stage-x", v],
        "payload": lambda v: {"unit_id": "unit-x", "stage_id": "stage-x",
                              "status": v},
    },
    {
        "capability": "path.progress.update",
        "command": "path-progress",
        "field": "status",
        "valid": ["active", "complete", "skipped"],
        "argv": lambda v: ["path-x", "stage-x", v],
        "payload": lambda v: {"path_id": "path-x", "stage_id": "stage-x",
                              "status": v},
    },
    {
        "capability": "learner.observation.append",
        "command": "observation-append",
        "field": "result",
        "valid": ["correct", "incorrect", "partial", "abandoned"],
        "argv": lambda v: ["--workspace", "w", "--requirement", "r",
                           "--activity", "a", "--result", v],
        "payload": lambda v: {"workspace": "w", "requirement": "r",
                              "activity": "a", "result": v},
    },
    {
        "capability": "learner.ability-observation.append",
        "command": "ability-observation-append",
        "field": "result",
        "valid": ["correct", "incorrect", "partial", "abandoned"],
        "argv": lambda v: ["--workspace", "w", "--ability", "ab",
                           "--claim", "c", "--work-ref", "conversation://x",
                           "--confirmation-ref", "conversation://y",
                           "--activity", "a", "--result", v,
                           "--assistance", "h"],
        "payload": lambda v: {"workspace": "w", "ability": "ab", "claim": "c",
                              "work_ref": "conversation://x",
                              "confirmation_ref": "conversation://y",
                              "activity": "a", "result": v, "assistance": "h"},
    },
    {
        "capability": "ability.candidate.append",
        "command": "ability-candidate-append",
        "field": "kind",
        "valid": ["equivalence", "extension", "connection"],
        "argv": lambda v: ["--from-ability", "a", "--to-ability", "b",
                           "--kind", v, "--carries", "c", "--changes", "ch",
                           "--source-ref", "conversation://x"],
        "payload": lambda v: {"from_ability": "a", "to_ability": "b",
                              "kind": v, "carries": "c", "changes": "ch",
                              "source_ref": "conversation://x"},
    },
    {
        "capability": "unit.source-selection.set",
        "command": "unit-source-selection",
        "field": "action",
        "valid": ["select", "remove"],
        "argv": lambda v: ["unit-x", "source-x", "locator-x", v],
        "payload": lambda v: {"unit_id": "unit-x", "source_id": "source-x",
                              "locator": "locator-x", "action": v},
    },
    {
        "capability": "source.feedback.record",
        "command": "source-feedback",
        "field": "feedback",
        "valid": ["helpful", "too-advanced", "wrong-perspective",
                  "useful-for-derivation", "useful-for-review", "skipped"],
        "argv": lambda v: ["unit-x", "stage-x", "source-x", v],
        "payload": lambda v: {"unit_id": "unit-x", "stage_id": "stage-x",
                              "source_id": "source-x", "feedback": v},
    },
    {
        "capability": "detour.create",
        "command": "detour-create",
        "field": "classification",
        "valid": ["required-now", "helpful-now", "deferred", "reference-only"],
        "argv": lambda v: ["unit-x", "stage-x", "--title", "t",
                           "--classification", v],
        "payload": lambda v: {"unit_id": "unit-x", "stage_id": "stage-x",
                              "title": "t", "classification": v},
    },
    {
        "capability": "note.evidence.add",
        "command": "note-evidence",
        "field": "evidence_type",
        "valid": ["derivation", "explanation", "implementation", "exercise",
                  "exam", "external"],
        "argv": lambda v: ["note-x", v, "note://ref"],
        "payload": lambda v: {"note_id": "note-x", "evidence_type": v,
                              "ref": "note://ref"},
    },
    {
        "capability": "coordination.section.revise",
        "command": "coordination-section-revise",
        "field": "section",
        "valid": ["Commitments", "Priorities", "Dependencies", "Deferrals"],
        "argv": lambda v: [v, "--text", "t",
                           "--expected-content-sha256", SHA],
        "payload": lambda v: {"section": v, "text": "t",
                              "expected_content_sha256": SHA},
    },
]

# Invalid everywhere: a near-miss verb, a wrong-form completion, an
# unknown token, the empty string, a case slip, and padded whitespace.
INVALID = ["done", "completed", "bogus-value", "", "ACTIVE", " complete",
           "null", "none"]

CASE_IDS = [case["capability"] for case in CASES]


def _command_parser(command: str) -> argparse.ArgumentParser:
    return subparsers(los.build_parser())[command]


def _schema(repo_root: Path, capability: str) -> dict:
    path = (repo_root / "system" / "schema" / "capabilities"
            / f"{capability}.schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _cli_accepts(command: str, argv: list[str]) -> bool:
    """Whether the bare CLI parses these arguments (argparse decides)."""
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            _command_parser(command).parse_args(argv)
        except SystemExit as exc:
            assert exc.code == 2, f"unexpected CLI exit {exc.code} for {argv}"
            return False
    return True


def _schema_errors(schema: dict, payload: dict) -> list:
    return list(Draft202012Validator(schema).iter_errors(payload))


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_parser_choices_match_the_pinned_vocabulary(case: dict):
    """The CLI vocabulary is pinned: changing it updates this table."""
    actions = {action.dest: action
               for action in _command_parser(case["command"])._actions}
    assert list(actions[case["field"]].choices) == case["valid"]


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_schema_enum_matches_the_cli_parser(repo_root: Path, case: dict):
    schema = _schema(repo_root, case["capability"])
    assert schema["properties"][case["field"]] == {"type": "string",
                                                  "enum": case["valid"]}


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_cli_and_gateway_accept_the_same_valid_values(repo_root: Path,
                                                      case: dict):
    schema = _schema(repo_root, case["capability"])
    parser = _command_parser(case["command"])
    for value in case["valid"]:
        assert _cli_accepts(case["command"], case["argv"](value)), value
        payload = case["payload"](value)
        assert _schema_errors(schema, payload) == [], value
        namespace = payload_to_namespace(parser, payload, root=None,
                                         expected_snapshot=None,
                                         expected_revisions=None)
        assert getattr(namespace, case["field"]) == value


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_cli_and_gateway_refuse_the_same_invalid_values(repo_root: Path,
                                                        case: dict):
    schema = _schema(repo_root, case["capability"])
    parser = _command_parser(case["command"])
    for value in [v for v in INVALID if v not in case["valid"]]:
        assert not _cli_accepts(case["command"], case["argv"](value)), value
        payload = case["payload"](value)
        field_errors = [error for error in _schema_errors(schema, payload)
                        if list(error.path) == [case["field"]]]
        assert field_errors, f"{value!r} passed the {case['capability']} schema"
        with pytest.raises(WriteRefused, match="invalid payload"):
            payload_to_namespace(parser, payload, root=None,
                                 expected_snapshot=None,
                                 expected_revisions=None)


def test_progress_next_requires_progress_summary_in_the_schema(repo_root: Path):
    schema = _schema(repo_root, "stage.progress.update")
    assert schema["dependentRequired"]["progress_next"] == ["progress_summary"]
    bare = {"unit_id": "u", "stage_id": "s", "status": "active",
            "progress_next": "then this"}
    assert [list(error.path) for error in _schema_errors(schema, bare)]
    both = {**bare, "progress_summary": "stopped here"}
    assert _schema_errors(schema, both) == []


def test_gateway_refuses_an_unknown_stage_status_before_any_write(
        mini_repo: Path):
    """`{"status": "done"}` refuses with the allowed set; nothing commits."""
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    fingerprint_before = canonical_fingerprint(mini_repo)
    receipts_before = sorted((mini_repo / "operations" / "transactions").glob(
        "transaction-*.yaml")) if (mini_repo / "operations" / "transactions").exists() else []
    result = approved_v2_call(
        mini_repo,
        capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "done"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="choice-parity-done-001",
    )
    assert result.returncode == 2, result.stdout + result.stderr
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_REQUEST"
    message = body["error"]["message"]
    assert "invalid payload" in message
    for allowed in ("active", "paused", "complete", "skipped", "revisit"):
        assert allowed in message, message
    assert body["transaction_id"] is None
    assert canonical_fingerprint(mini_repo) == fingerprint_before
    transactions = mini_repo / "operations" / "transactions"
    receipts_after = sorted(transactions.glob("transaction-*.yaml")) \
        if transactions.exists() else []
    assert receipts_after == receipts_before


def test_gateway_refuses_progress_next_without_a_summary(mini_repo: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    result = approved_v2_call(
        mini_repo,
        capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "active", "progress_next": "then this"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="choice-parity-next-001",
    )
    assert result.returncode == 2, result.stdout + result.stderr
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert "progress_summary" in body["error"]["message"]


def _namespace(root: Path, **fields) -> argparse.Namespace:
    namespace = argparse.Namespace(root=str(root), expected_snapshot=None,
                                   expected_revision=[])
    for key, value in fields.items():
        setattr(namespace, key, value)
    return namespace


def test_stage_handler_refuses_an_unknown_status(mini_repo: Path,
                                                 capsys: pytest.CaptureFixture):
    """The handler backstop: no open `else` maps unknown input to a write."""
    from repo_builders import add_curriculum

    from learning_os.commands.stage import cmd_stage_progress

    add_curriculum(mini_repo)
    code = cmd_stage_progress(_namespace(
        mini_repo, unit_id="unit-demo-l01", stage_id="stage-demo",
        status="done"))
    assert code == 2
    assert "unknown stage status" in capsys.readouterr().err


def test_path_handler_refuses_an_unknown_status(mini_repo: Path,
                                                capsys: pytest.CaptureFixture):
    from learning_os.commands.path import cmd_path_progress

    path_file = (mini_repo / "work" / "active" / "workspace-demo"
                 / "paths" / "path-demo-probability.yaml")
    path_file.parent.mkdir(parents=True)
    path_file.write_text(yaml.safe_dump({
        "id": "path-demo-probability", "type": "learning-path",
        "title": "Demo probability", "workspace_id": "workspace-demo",
        "area": "university", "module_id": "module-demo", "status": "active",
        "current_stage": "stage-one", "created": "2026-08-03",
        "stages": [
            {"id": "stage-one", "title": "One", "status": "active",
             "objective": "Do one.", "concepts": ["concept-expected-value"],
             "resources": [{"kind": "read", "label": "Demo Book",
                            "source_id": "source-demo-book"}],
             "done_when": ["Explain one."],
             "notes_path": "work/active/workspace-demo/scratch/paths/"
                           "path-demo-probability/stage-one.md"},
        ],
    }, sort_keys=False), encoding="utf-8")
    code = cmd_path_progress(_namespace(
        mini_repo, path_id="path-demo-probability", stage_id="stage-one",
        status="done"))
    assert code == 2
    assert "unknown path status" in capsys.readouterr().err


def test_source_selection_handler_refuses_an_unknown_action(
        mini_repo: Path, capsys: pytest.CaptureFixture):
    from repo_builders import rich_fixture

    from learning_os.commands.unit import cmd_unit_source_selection

    rich_fixture(mini_repo)
    code = cmd_unit_source_selection(_namespace(
        mini_repo, unit_id="unit-demo-l01", source_id="source-demo-book",
        locator="lecture-01.pdf", action="bogus", purpose=None))
    assert code == 2
    assert "unknown source-selection action" in capsys.readouterr().err


def test_detour_handler_refuses_an_unknown_classification(
        mini_repo: Path, capsys: pytest.CaptureFixture):
    from repo_builders import add_curriculum

    from learning_os.commands.detour import cmd_detour_create

    add_curriculum(mini_repo)
    code = cmd_detour_create(_namespace(
        mini_repo, unit_id="unit-demo-l01", stage_id="stage-demo",
        title="A gap", classification="urgent"))
    assert code == 2
    assert "unknown detour classification" in capsys.readouterr().err
