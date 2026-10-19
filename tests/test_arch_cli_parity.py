"""CLI parity: generated parser equals the old parser (PLAN D2, SPEC 10.7).

Also enforces ``system/contracts/cli-operations.yaml`` (SPEC 10.8).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import sys
from pathlib import Path
from unittest import mock

import arch_cli_describe
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
CLI_OPS_PATH = ROOT / "system/contracts/cli-operations.yaml"
BASELINE_PATH = ROOT / "tests/architecture/cli-parity-baseline.json"
CORPUS_PATH = ROOT / "tests/architecture/cli-parity-corpus.json"
REQUESTS_DIR = ROOT / "system/schema/requests"

FIX = "Generated parser drifted from the recorded CLI surface (PLAN D2)."


def test_cli_operations_lists_every_cli_primary():
    data = yaml.safe_load(CLI_OPS_PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == 1
    operations = data.get("operations", {})
    assert len(operations) == 41, len(operations)
    for name, entry in sorted(operations.items()):
        command = entry.get("cli_command")
        assert isinstance(command, str) and command, name
        if name != "cli.capability":
            assert _handler_for_subcommand(command) == "learning_os.adapters.cli.invoke:" + name
            assert not name.startswith("cli."), name
        assert entry.get("kind") in {"query", "command", "porcelain", "tool"}, name


def _handler_for_subcommand(subcommand: str) -> str | None:
    for path in REQUESTS_DIR.glob("*.schema.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cmd = data.get("x-los-cli-command")
        if cmd is not None and cmd.get("name") == subcommand:
            handler = cmd.get("handler", "")
            return handler if isinstance(handler, str) else None
    return None


# Approved B2 internal binding relocation. These five commands were lock-free
# tools before their duplicate registrations merged into canonical queries.
CLI_TOOL_BINDINGS = {
    "backup.manifest", "health.report", "legacy.archive.inspect",
    "legacy.archive.status", "masters-planning.dashboard",
}


def _normalize_registered_namespace(recorded: dict, handler: str) -> dict:
    """Amendment (u) item 2: baseline namespace for a converted subcommand."""
    prefix = "learning_os.adapters.cli.invoke:"
    assert handler.startswith(prefix), handler
    operation = handler[len(prefix):]
    normalized = dict(recorded)
    normalized["func"] = "learning_os.adapters.cli.invoke"
    normalized["_operation"] = operation
    if operation in {"repository.validate", "projection.generate"}:
        normalized["json"] = False
    if operation in CLI_TOOL_BINDINGS:
        normalized["_operation_kind"] = "tool"
    return normalized


def _normalize_registered_defaults(baseline_defaults: dict, handler: str) -> dict:
    prefix = "learning_os.adapters.cli.invoke:"
    assert handler.startswith(prefix), handler
    operation = handler[len(prefix):]
    normalized = dict(baseline_defaults)
    normalized["func"] = "learning_os.adapters.cli.invoke"
    normalized["_operation"] = repr(operation)
    if operation in CLI_TOOL_BINDINGS:
        normalized["_operation_kind"] = repr("tool")
    return normalized


#: SPEC (bf) item 1, generalized by (bi) item 6: (subcommand, dest)
#: pairs whose baseline help (None: the placeholder suppresses help)
#: normalizes to the live request-schema description, as (u) item 2
#: does for handler bindings. Pilot pairs first, then the wave 1 and
#: final-wave authorized description pointers, one entry per operation.
BF_HELP_PAIRS: dict[str, set[str]] = {
    "route-patch": {"unit_id", "route_id", "changes", "check",
                    "expected_snapshot"},
    "stage-progress": {"unit_id", "stage_id", "status",
                       "expected_snapshot"},
    "ai-action-apply-delivery": {"delivery_id", "expected_snapshot"},
    "inspect": {"id"},
    "ai-action-append-slices": {"request_id", "route_id",
                                "expected_snapshot"},
    "ai-action-import-delivery": {"path"},
    "ai-action-prepare": {"action_id", "target_kind", "target_id",
                          "provider", "expected_snapshot"},
    "ai-action-status": {"request_id"},
    "ai-action-validate-delivery": {"delivery_id"},
    "detour-create": {"unit_id", "stage_id", "title", "classification",
                      "expected_snapshot"},
    "detour-resolve": {"unit_id", "detour_id", "resolution",
                       "expected_snapshot"},
    "ability-observation-append": {"workspace", "ability", "activity",
                                   "result", "assistance", "condition",
                                   "evidence_tag", "condition_not_met",
                                   "supersedes", "expected_snapshot"},
    "observation-append": {"workspace", "requirement", "activity",
                           "result", "assistance", "tags", "context",
                           "expected_snapshot"},
    "stage-result": {"workspace", "unit", "stage", "activity", "result",
                     "assistance", "expected_snapshot"},
    "note-evidence": {"note_id", "evidence_type", "expected_snapshot"},
    "note-revise": {"note_id", "approve", "expected_snapshot"},
    "path-attach": {"path_id", "stage_id", "label"},
    "path-note": {"path_id", "stage_id"},
    "path-progress": {"path_id", "stage_id", "status"},
    "source-feedback": {"unit_id", "stage_id", "source_id", "feedback",
                        "note", "expected_snapshot"},
    "stage-attach": {"unit_id", "stage_id", "label",
                     "expected_snapshot"},
    "stage-note": {"unit_id", "stage_id", "text", "expected_snapshot"},
    "unit-note": {"unit_id", "title", "text", "expected_snapshot"},
    "unit-source-selection": {"unit_id", "source_id", "locator",
                              "action", "purpose", "expected_snapshot"},
    "ability-candidate-append": {"carries", "changes", "condition",
                                 "expected_snapshot", "from_ability", "kind",
                                 "source_ref", "to_ability"},
    "ability-context": {"expected_snapshot", "limit"},
    "atlas-question-save": {"expected_snapshot", "question"},
    "atlas-context": {"concept_id", "expected_snapshot"},
    "backup-manifest": {"materials_root", "ui_root"},
    "backup-verify": {"manifest", "restored_core", "restored_materials",
                      "restored_ui"},
    "bootstrap": {"expected_snapshot", "limit", "offset"},
    "goal": {"close", "defer", "reject"},
    "inbox-read": {"expected_snapshot"},
    "legacy-archive-inspect": {"allowlist", "archive_root"},
    "masters-planning-dashboard": {"confirm_masters_planning"},
    "module-list": {"program_id", "status"},
    "note-read": {"expected_snapshot", "note_id"},
    "observe": {"activity", "assistance", "result", "tags"},
    "plan-edit-context": {"expected_snapshot", "unit_id"},
    "plan-template": {"module_id", "profile", "title", "unit_id"},
    "project-list": {"status"},
    "related": {"id"},
    "runtime-session": {"context_json", "event", "expected_snapshot",
                        "requirement"},
    "search": {"expected_snapshot", "limit", "offset"},
    "unit-list": {"component_id", "expected_snapshot", "limit", "module_id",
                  "offset", "status"},
    "collection-entry-revise": {"approve", "expected_snapshot", "record"},
    "concept-relations-change": {"change", "expected_snapshot"},
    "coordination-section-revise": {"expected_snapshot", "section"},
    "garden-seed-create": {"expected_snapshot"},
    "inbox-resolve": {"expected_snapshot"},
    "legacy-archive-lock-publish": {"approve", "expected_snapshot", "record"},
    "masters-planning-catalog-update": {"approve", "expected_snapshot",
                                        "record"},
    "masters-planning-comparison-publish": {"approve", "candidate_module_id",
                                            "expected_snapshot", "record"},
    "material-context": {"expected_snapshot", "limit", "offset"},
    "material-span": {"expected_snapshot", "extract", "route_id", "unit_id"},
    "module-attempt": {"expected_snapshot", "module_id"},
    "module-materials-compact": {"check", "expected_snapshot", "module_id"},
    "module-sitting": {"expected_snapshot", "module_id"},
    "note-analysis-save": {"analysis", "expected_snapshot"},
    "note-analysis-save-batch": {"expected_snapshot"},
    "note-create": {"expected_snapshot", "note"},
    "project-create": {"expected_snapshot"},
    "project-update": {"expected_snapshot", "project_id"},
    "shelving-apply": {"approve", "expected_snapshot", "selected", "unit_id"},
    "shelving-prepare": {"expected_snapshot", "summary", "unit_id"},
    "source-intake": {"approve", "expected_snapshot", "record"},
    "source-revise": {"approve", "expected_snapshot", "record"},
    "unit-map-import": {"expected_snapshot", "unit_id"},
    "unit-material-synthesis-publish": {"approve", "check",
                                        "expected_snapshot", "record",
                                        "unit_id"},
    "workspace-next-action": {"expected_snapshot", "workspace_id"},
}

#: The request-schema operation behind each normalized subcommand.
_BF_HELP_OPERATIONS: dict[str, str] = {
    "route-patch": "route.patch",
    "stage-progress": "stage.progress.update",
    "ai-action-apply-delivery": "ai-action.delivery.apply",
    "inspect": "project.inspect",
    "ai-action-append-slices": "ai-action.append-slices",
    "ai-action-import-delivery": "ai-action.delivery.import",
    "ai-action-prepare": "ai-action.prepare",
    "ai-action-status": "ai-action.status",
    "ai-action-validate-delivery": "ai-action.delivery.validate",
    "detour-create": "detour.create",
    "detour-resolve": "detour.resolve",
    "ability-observation-append": "learner.ability-observation.append",
    "observation-append": "learner.observation.append",
    "stage-result": "learner.stage-result.append",
    "note-evidence": "note.evidence.add",
    "note-revise": "note.revise",
    "path-attach": "path.attachment.add",
    "path-note": "path.note.write",
    "path-progress": "path.progress.update",
    "source-feedback": "source.feedback.record",
    "stage-attach": "stage.attachment.add",
    "stage-note": "stage.note.write",
    "unit-note": "unit.note.append",
    "unit-source-selection": "unit.source-selection.set",
    "ability-candidate-append": "ability.candidate.append",
    "ability-context": "ability.context",
    "atlas-question-save": "atlas.question.save",
    "atlas-context": "atlas.context",
    "backup-manifest": "backup.manifest",
    "backup-verify": "backup.verify",
    "bootstrap": "operator.bootstrap",
    "goal": "goal.decide",
    "inbox-read": "inbox.content",
    "legacy-archive-inspect": "legacy.archive.inspect",
    "masters-planning-dashboard": "masters-planning.dashboard",
    "module-list": "module.list",
    "note-read": "note.content",
    "observe": "learner.observe",
    "plan-edit-context": "plan.edit-context",
    "plan-template": "plan.template",
    "project-list": "project.list",
    "related": "related.read",
    "runtime-session": "runtime.session",
    "search": "note.search",
    "unit-list": "unit.list",
    "collection-entry-revise": "collection.entry.revise",
    "concept-relations-change": "concept.relations.change",
    "coordination-section-revise": "coordination.section.revise",
    "garden-seed-create": "garden.seed.create",
    "inbox-resolve": "inbox.resolve",
    "legacy-archive-lock-publish": "legacy.archive.lock.publish",
    "masters-planning-catalog-update": "masters-planning.catalog.update",
    "masters-planning-comparison-publish": "masters-planning.comparison.publish",
    "material-context": "material.context",
    "material-span": "material.span",
    "module-attempt": "module.attempt.record",
    "module-materials-compact": "module.materials.compact",
    "module-sitting": "module.sitting.update",
    "note-analysis-save": "note.analysis.save",
    "note-analysis-save-batch": "note.analysis.save_batch",
    "note-create": "note.create",
    "project-create": "project.create",
    "project-update": "project.update",
    "shelving-apply": "review.apply",
    "shelving-prepare": "review.prepare",
    "source-intake": "source.intake.record",
    "source-revise": "source.record.revise",
    "unit-map-import": "unit.map.import",
    "unit-material-synthesis-publish": "unit.material-synthesis.publish",
    "workspace-next-action": "workspace.next-action.update",
}


def _normalize_bf_help(expected: dict) -> dict:
    """Baseline help at exactly the (bf) pairs becomes the live text.

    The baseline value at each listed pair must be None — the help the
    placeholder produced — before the live description is substituted.
    """
    normalized = copy.deepcopy(expected)
    for subcommand, dests in BF_HELP_PAIRS.items():
        operation = _BF_HELP_OPERATIONS[subcommand]
        doc = json.loads((REQUESTS_DIR / f"{operation}.schema.json")
                         .read_text(encoding="utf-8"))
        assert doc["x-los-cli-command"]["name"] == subcommand, subcommand
        properties = doc.get("properties", {})
        for action in normalized["subparsers"][subcommand]["actions"]:
            if action["dest"] in dests:
                assert action["help"] is None, (
                    subcommand, action["dest"], action["help"])
                action["help"] = properties[action["dest"]]["description"]
    return normalized


def test_registered_normalization_with_synthetic_handler():
    # No production registration exists in S12; prove the future rule.
    handler = "learning_os.adapters.cli.invoke:project.inspect"
    recorded = {"func": "learning_os.commands.query.cmd_inspect", "id": "X"}
    normalized = _normalize_registered_namespace(recorded, handler)
    assert normalized["func"] == "learning_os.adapters.cli.invoke"
    assert normalized["_operation"] == "project.inspect"
    assert normalized["id"] == "X"
    defaults = {"func": "learning_os.commands.query.cmd_inspect"}
    normalized_defaults = _normalize_registered_defaults(defaults, handler)
    assert normalized_defaults["func"] == "learning_os.adapters.cli.invoke"
    assert normalized_defaults["_operation"] == repr("project.inspect")


def _normalize_describe(doc: dict) -> dict:
    normalized = copy.deepcopy(doc)
    # The moved parser class keeps its code but not its module.
    if normalized["parser_class"] == "learning_os.adapters.cli_parser._LosArgumentParser":
        normalized["parser_class"] = "los._LosArgumentParser"
    for sub in normalized.get("subparsers", {}).values():
        defaults = sub.get("defaults", {})
        if defaults.get("_parser_factory") == "learning_os.adapters.cli_parser.build_parser":
            defaults["_parser_factory"] = "los.build_parser"
    return normalized


def test_only_the_documented_relocation_normalizes():
    """SPEC (ap): arbitrary class/factory changes fail the real comparison."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    expected = _normalize_describe(baseline)
    # Positive control: the exact relocation maps onto the old bytes.
    moved = copy.deepcopy(baseline)
    moved["parser_class"] = (
        "learning_os.adapters.cli_parser._LosArgumentParser")
    for sub in moved["subparsers"].values():
        if "_parser_factory" in sub.get("defaults", {}):
            sub["defaults"]["_parser_factory"] = (
                "learning_os.adapters.cli_parser.build_parser")
    assert _normalize_describe(moved) == expected
    # Arbitrary changes survive normalization, so the comparison fails.
    for parser_class in ("argparse.ArgumentParser",
                         "learning_os.adapters.cli_parser.Parser",
                         "los.ArgumentParser"):
        wrong = copy.deepcopy(baseline)
        wrong["parser_class"] = parser_class
        assert _normalize_describe(wrong)["parser_class"] == parser_class
        assert _normalize_describe(wrong) != expected
    name = next(iter(baseline["subparsers"]))
    for factory in ("other.build_parser",
                    "learning_os.adapters.cli_parser.build_parser2",
                    "x.learning_os.adapters.cli_parser.build_parser"):
        wrong = copy.deepcopy(baseline)
        wrong["subparsers"][name].setdefault("defaults", {})[
            "_parser_factory"] = factory
        normalized = _normalize_describe(wrong)
        assert normalized["subparsers"][name]["defaults"][
            "_parser_factory"] == factory
        assert normalized != expected


def test_namespace_normalization_accepts_only_the_exact_factory():
    assert _normalize_namespace(
        {"_parser_factory":
         "learning_os.adapters.cli_parser.build_parser"}) == \
        {"_parser_factory": "los.build_parser"}
    # The old bytes and anything else pass through untouched.
    for factory in ("los.build_parser", "other.build_parser",
                    "learning_os.adapters.cli_parser.build_parser2"):
        assert _normalize_namespace(
            {"command": "inspect",
             "_parser_factory": factory}) == {
                 "command": "inspect", "_parser_factory": factory}


def test_registered_normalization_with_invoke_binding_and_root_options(
        tmp_path, monkeypatch):
    """Future (u) rule against an actual synthetic invoke binding.

    Root options precede the subcommand, so the first non-dash token is
    the root value, not the subcommand: selection must use the recorded
    namespace's ``command``. Every unrelated value is kept.
    """
    directory = tmp_path / "requests"
    directory.mkdir()
    (directory / "project.inspect.schema.json").write_text(json.dumps({
        "x-los-cli-command": {
            "name": "inspect",
            "handler": "learning_os.adapters.cli.invoke:project.inspect",
        },
    }), encoding="utf-8")
    monkeypatch.setattr("test_arch_cli_parity.REQUESTS_DIR", directory)
    argv = ["--root", "/tmp/x", "inspect", "note-demo"]
    recorded = {"namespace": {
        "command": "inspect", "id": "note-demo",
        "func": "learning_os.commands.query.cmd_inspect",
        "_parser_factory": "los.build_parser", "root": "/tmp/x",
    }}
    naive_first_token = next(
        token for token in argv if not token.startswith("-"))
    assert naive_first_token == "/tmp/x"
    subcommand = recorded.get("namespace", {}).get("command")
    assert subcommand == "inspect"
    handler = _handler_for_subcommand(subcommand)
    assert handler == "learning_os.adapters.cli.invoke:project.inspect"
    normalized = _normalize_registered_namespace(
        _normalize_namespace(recorded["namespace"]), handler)
    assert normalized == {
        "command": "inspect", "id": "note-demo",
        "func": "learning_os.adapters.cli.invoke",
        "_operation": "project.inspect",
        "_parser_factory": "los.build_parser", "root": "/tmp/x",
    }
    normalized_defaults = _normalize_registered_defaults(
        {"func": "learning_os.commands.query.cmd_inspect",
         "_parser_factory": "los.build_parser"}, handler)
    assert normalized_defaults == {
        "func": "learning_os.adapters.cli.invoke",
        "_operation": repr("project.inspect"),
        "_parser_factory": "los.build_parser",
    }


def test_generated_parser_matches_baseline_structure():
    import los

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    live = _normalize_describe(arch_cli_describe.describe(los.build_parser()))
    expected = _normalize_describe(baseline)
    # Future registered subcommands (none yet) normalize per (u) item 2.
    for name, sub in expected.get("subparsers", {}).items():
        handler = _handler_for_subcommand(name)
        if handler is not None and handler.startswith(
                "learning_os.adapters.cli.invoke:"):
            sub["defaults"] = _normalize_registered_defaults(
                sub.get("defaults", {}), handler)
    # SPEC (bf) item 1: pilot descriptions became argparse help.
    expected = _normalize_bf_help(expected)
    # B1 adds the same pre-existing JSON transport flag to the former tools.
    json_action = next(action for action in baseline["subparsers"]["health-report"]["actions"] if action["dest"] == "json")
    for command in ("validate", "generate"):
        expected["subparsers"][command]["actions"].append(copy.deepcopy(json_action))
    assert live["order"] == expected["order"], f"{FIX} order"
    assert live["parser_class"] == expected["parser_class"]
    assert live["prog"] == expected["prog"], f"{FIX} prog"
    assert live["description"] == expected["description"], f"{FIX} description"
    assert live["formatter_class"] == expected["formatter_class"], f"{FIX} formatter"
    assert live["root_options"] == expected["root_options"], f"{FIX} root options"
    assert set(live["subparsers"]) == set(expected["subparsers"]), f"{FIX} subcommands"
    for name in expected["order"]:
        assert live["subparsers"][name] == expected["subparsers"][name], \
            f"{FIX} subcommand {name}"


def test_bf_help_normalization_touches_only_the_listed_pairs():
    """A help change anywhere else still fails the gate (SPEC (bf) 1)."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    normalized = _normalize_bf_help(baseline)
    changed = []
    for subcommand, sub in baseline["subparsers"].items():
        live_doc = None
        if subcommand in BF_HELP_PAIRS:
            operation = _BF_HELP_OPERATIONS[subcommand]
            live_doc = json.loads(
                (REQUESTS_DIR / f"{operation}.schema.json")
                .read_text(encoding="utf-8"))
        norm_actions = normalized["subparsers"][subcommand]["actions"]
        for base_action, norm_action in zip(sub["actions"], norm_actions,
                                                 strict=True):
            listed = (subcommand in BF_HELP_PAIRS
                      and base_action["dest"] in BF_HELP_PAIRS[subcommand])
            if listed:
                want = live_doc["properties"][base_action["dest"]][
                    "description"]
                assert norm_action["help"] == want, (
                    subcommand, base_action["dest"])
                assert norm_action["help"] != base_action["help"], (
                    subcommand, base_action["dest"])
                rest_base = {k: v for k, v in base_action.items()
                             if k != "help"}
                rest_norm = {k: v for k, v in norm_action.items()
                             if k != "help"}
                assert rest_norm == rest_base, (
                    subcommand, base_action["dest"])
                changed.append((subcommand, base_action["dest"]))
            else:
                assert norm_action == base_action, (
                    subcommand, base_action["dest"])
    assert sorted(changed) == sorted(
        (sub, dest) for sub, dests in BF_HELP_PAIRS.items()
        for dest in dests), changed
    assert len(changed) == 12 + 83 + 122, changed  # pilot 12 + wave 1 (bi) 6 + final wave (cc)
    # Control: a baseline whose listed help is already a real string —
    # not the placeholder's None — must fail normalization.
    poisoned = copy.deepcopy(baseline)
    poisoned["subparsers"]["inspect"]["actions"] = [
        dict(action, help="a real help string")
        if action["dest"] == "id" else action
        for action in poisoned["subparsers"]["inspect"]["actions"]]
    with pytest.raises(AssertionError):
        _normalize_bf_help(poisoned)


def _normalize_namespace(namespace: dict) -> dict:
    normalized = dict(namespace)
    for key, value in list(normalized.items()):
        if key == "_parser_factory" and value == "learning_os.adapters.cli_parser.build_parser":
            normalized[key] = "los.build_parser"
    return normalized


def _run(parser, argv: list[str]) -> dict:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with mock.patch.object(sys, "argv", ["los", *argv]):
        with contextlib.redirect_stdout(stdout_buf), \
                contextlib.redirect_stderr(stderr_buf):
            try:
                namespace = parser.parse_args(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
                stderr = stderr_buf.getvalue()
                first = stderr.strip().splitlines()[0] if stderr.strip() else ""
                return {"error": {"exit": code, "first_line": first,
                                  "stderr": stderr},
                        "stdout": stdout_buf.getvalue()}
    data = dict(vars(namespace))
    for key, value in list(data.items()):
        if callable(value):
            module = getattr(value, "__module__", "") or ""
            qualname = getattr(value, "__qualname__", "") \
                or getattr(value, "__name__", "")
            data[key] = f"{module}.{qualname}" if module else str(qualname)
    return {"namespace": _normalize_namespace(data),
            "stdout": stdout_buf.getvalue()}


def test_corpus_parity():
    import los

    parser = los.build_parser()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    for index, entry in enumerate(corpus["cases"]):
        argv = entry["argv"]
        recorded = entry["result"]
        # These two historical rejections are the exact JSON flags B1 adds.
        # Derive every other argument from the frozen old no-flag observation.
        added_json = argv in (["generate", "--json"], ["validate", "--json"])
        if added_json:
            assert recorded["error"]["exit"] == 2
            assert "--json" in recorded["error"]["stderr"]
            baseline = next(row["result"] for row in corpus["cases"]
                            if row["argv"] == argv[:1] and "namespace" in row["result"])
            recorded = copy.deepcopy(baseline)
        actual = _run(parser, argv)
        # Registered-subcommand normalization (none yet; see unit test).
        subcommand = recorded.get("namespace", {}).get("command")
        if subcommand is not None and "namespace" in recorded:
            handler = _handler_for_subcommand(subcommand)
            if handler is not None and handler.startswith(
                    "learning_os.adapters.cli.invoke:"):
                recorded = {"namespace": _normalize_registered_namespace(
                    _normalize_namespace(recorded["namespace"]), handler)}
            else:
                recorded = {"namespace": _normalize_namespace(recorded["namespace"])} \
                    if "namespace" in recorded else recorded
        elif "namespace" in recorded:
            recorded = {"namespace": _normalize_namespace(recorded["namespace"])}
        if added_json:
            recorded["namespace"]["json"] = True
        if "namespace" in recorded and "namespace" in actual:
            if recorded["namespace"] != actual["namespace"]:
                failures.append(f"case {index} argv={argv}: namespace differs")
        elif "error" in recorded and "error" in actual:
            if recorded["error"].get("stderr") != actual["error"]["stderr"]:
                failures.append(f"case {index} argv={argv}: full stderr differs")
            if recorded["error"]["exit"] != actual["error"]["exit"] or \
                    recorded["error"]["first_line"] != actual["error"]["first_line"]:
                failures.append(
                    f"case {index} argv={argv}: error differs "
                    f"(want {recorded['error']['exit']} "
                    f"{recorded['error']['first_line']!r}, got "
                    f"{actual['error']['exit']} {actual['error']['first_line']!r})")
        else:
            failures.append(f"case {index} argv={argv}: success/error differs")
        if len(failures) >= 10:
            break
    assert not failures, f"{FIX}\n" + "\n".join(failures)


def test_capability_schema_check_passes():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import generate_capability_schemas
    finally:
        del sys.path[0]
    assert generate_capability_schemas.main(["--check"]) == 0, FIX


def _normalize_claim_surface_observation(parser, argv, recorded):
    """Keep old-source observations; account only for the three added fields.

    Changed command declarations own their usage prefix. Error bodies, exits,
    stdout and all historical argument values remain exact.
    """
    result = copy.deepcopy(recorded)
    command = argv[0] if argv else ""
    additions = {"goal": {"authorize": False, "audit_file": None},
                 "route-patch": {"claim_evidence": None}}
    if command not in additions:
        return result
    if "namespace" in result:
        for name, default in additions[command].items():
            assert name not in result["namespace"], (command, name)
            result["namespace"][name] = default
    elif command == "goal":
        frozen_error_cases = {
            ("goal", "X", "--reject", "--reject", "--defer"),
            ("goal", "X", "--reject", "--reviewed-sha256", "ab" * 32),
        }
        assert tuple(argv) in frozen_error_cases
        prefix, separator, body = result["error"]["stderr"].partition("los goal: error:")
        assert separator and prefix.startswith("usage: los goal")
        action = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
        usage = action.choices[command].format_usage()
        result["error"]["stderr"] = usage + separator + body
        result["error"]["first_line"] = usage.strip().splitlines()[0]
    return result


@pytest.mark.parametrize("argv,field,value", [
    (["goal", "lineage-stale:covers:route-demo@" + "a"*64, "--authorize"], "authorize", True),
    (["goal", "claims-audit:" + "a"*64, "--close", "--audit-file", "/scratch/audit.yaml", "--check"], "audit_file", "/scratch/audit.yaml"),
    (["route-patch", "unit-demo", "route-demo", "--changes", "{}", "--claim-evidence", "{}", "--check"], "claim_evidence", {}),
])
def test_claim_surface_additions_parse_without_rewriting_historical_corpus(argv, field, value):
    import los
    assert _run(los.build_parser(), argv)["namespace"][field] == value


def test_actual_old_source_supplement_parity():
    """Additional old-source observations retain full stdout and stderr."""
    import los

    corpus = json.loads((ROOT / "tests/architecture/cli-parity-supplement.json")
                        .read_text(encoding="utf-8"))
    assert sum(row["count"] for row in corpus["sources"].values()) == 265
    assert len(corpus["cases"]) == 265
    parser = los.build_parser()
    for row in corpus["cases"]:
        recorded = copy.deepcopy(row["result"])
        if "namespace" in recorded:
            namespace = _normalize_namespace(recorded["namespace"])
            handler = _handler_for_subcommand(namespace.get("command"))
            if handler and handler.startswith("learning_os.adapters.cli.invoke:"):
                namespace = _normalize_registered_namespace(namespace, handler)
            recorded["namespace"] = namespace
        recorded = _normalize_claim_surface_observation(parser, row["argv"], recorded)
        assert _run(parser, row["argv"]) == recorded, row["source"]
