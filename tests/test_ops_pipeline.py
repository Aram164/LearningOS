"""Pipeline tests for the S13 candidate (Task 4).

A test-only registered operation proves the lock rule, req filtering,
human/JSON rendering, refusal rendering and the CLI commit step through
the real run_cli and invoke paths, plus the four gateway-half behaviors
(malformed-payload refusal, parser defaults, envelope guards in req, and
the approve-key refusal) through the real run_gateway path.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

import arch_audit_hook
import pytest
from gateway_helpers import approved_v2_envelope
from scenario_harness import check_render_purity_error, render_violations

from learning_os import observations as observations_module
from learning_os.adapters import cli as cli_adapter
from learning_os.adapters.cli_parser import _repository_root
from learning_os.commands import support as command_support
from learning_os.domain.failures import (
    StaleSnapshot,
    TransactionFailure,
    WriteRefused,
)
from learning_os.ops import _legacy_plumbing as plumbing
from learning_os.ops import pipeline as pipeline_module
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import REGISTRY, register
from learning_os.ops.render import RenderPurityError, call_renderer, current_render

TEST_OP = "test-only.pipe"


def _write_test_schema(root: Path) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "test-only/test-only.pipe",
        "type": "object",
        "properties": {
            "alpha": {"type": "string", "default": "A"},
            "beta": {"type": "integer", "default": 3},
        },
    }
    path = root / "system" / "schema" / "requests" / f"{TEST_OP}.schema.json"
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def pipe(mini_repo):
    """Register the test-only operation; restore the empty registry after."""

    _write_test_schema(mini_repo)

    def make(kind="query", handler=None, human=None, render_check=None):
        calls = []

        def default_handler(ctx, req):
            calls.append({"ctx": ctx, "req": req})
            return Result({"echo": req.get("alpha"), "n": req.get("beta")})

        register(TEST_OP, kind=kind, human=human,
                 render_check=render_check)(handler or default_handler)
        return calls

    yield make
    REGISTRY.pop(TEST_OP, None)


@pytest.fixture
def lock_calls(monkeypatch):
    """Record (shared,) for every pipeline lock take; delegate to the real one."""

    real_lock = plumbing._operator_lock
    calls = []

    from contextlib import contextmanager

    @contextmanager
    def recording(root, *, shared=False):
        calls.append(shared)
        with real_lock(root, shared=shared):
            yield

    monkeypatch.setattr(pipeline_module, "_operator_lock", recording)
    return calls


def _ns(root, *, json=False, alpha="hi", beta=7):
    return argparse.Namespace(
        root=str(root),
        _operation=TEST_OP,
        json=json,
        alpha=alpha,
        beta=beta,
        extra="dropped",
    )


def test_registry_has_no_leaked_test_operation():
    assert TEST_OP not in REGISTRY


def test_query_takes_shared_lock(pipe, lock_calls, mini_repo):
    calls = pipe("query")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert lock_calls == [True]
    assert len(calls) == 1


def test_command_takes_exclusive_lock(pipe, lock_calls, mini_repo):
    calls = pipe("command")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert lock_calls == [False]
    assert len(calls) == 1


def test_porcelain_takes_exclusive_lock(pipe, lock_calls, mini_repo):
    pipe("porcelain")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert lock_calls == [False]


def test_tool_takes_no_lock(pipe, lock_calls, mini_repo):
    calls = pipe("tool")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert lock_calls == []
    assert len(calls) == 1


def test_unknown_kind_falls_back_to_exclusive_lock(pipe, lock_calls, mini_repo):
    # S13 candidate J17 fail-safe default, pinned.
    pipe("mystery")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert lock_calls == [False]


def test_req_filters_to_schema_properties(pipe, mini_repo):
    calls = pipe("query")
    pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert calls[0]["req"] == {"alpha": "hi", "beta": 7}


@pytest.mark.parametrize(
    ("kind", "invocation"),
    [("query", "query"), ("command", "command"), ("porcelain", "porcelain"), ("tool", "query")],
)
def test_opcontext_provenance_mapping(pipe, mini_repo, kind, invocation):
    # S13 candidate decision section 5: recorded provenance values, proven
    # neutral (no S13 path reads them; outputs above are unaffected).
    calls = pipe(kind)
    pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    ctx = calls[0]["ctx"]
    assert ctx.operation == TEST_OP
    assert ctx.channel == "operator"
    assert ctx.invocation == invocation
    assert ctx.gateway is None
    assert ctx.root == mini_repo


def test_human_rendering(pipe, mini_repo):
    pipe("query", human=lambda payload: f"ECHO {payload['echo']}")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stdout == "ECHO hi\n"
    assert outcome.stderr == ""
    assert outcome.exit_code == 0


def test_json_flag_overrides_human(pipe, mini_repo):
    pipe("query", human=lambda payload: "NEVER")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo, json=True))
    assert outcome.stdout == '{"echo":"hi","n":7}\n'
    assert outcome.stderr == ""
    assert outcome.exit_code == 0


def test_json_default_without_human(pipe, mini_repo):
    pipe("query")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stdout == '{"echo":"hi","n":7}\n'


def test_finish_applies_to_empty_confirmation(pipe, mini_repo):
    def handler(ctx, req):
        return Result({"echo": "x"}, finish=lambda conf: {"folded": True, **conf})

    pipe("query", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stdout == '{"folded":true}\n'
    assert outcome.exit_code == 0


def test_refusal_renders_unchanged_message_and_exit(pipe, mini_repo):
    def handler(ctx, req):
        raise WriteRefused("nope")

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stdout == ""
    assert outcome.stderr == "los: INVALID_REQUEST: nope\n"
    assert outcome.exit_code == 2


def test_refusal_preserves_handler_exit_token(pipe, mini_repo):
    def handler(ctx, req):
        raise WriteRefused("stale", exit_code=3)

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stderr == "los: INVALID_REQUEST: stale\n"
    assert outcome.exit_code == 3


def test_stale_refusal_exits_3(pipe, mini_repo):
    def handler(ctx, req):
        raise StaleSnapshot("old")

    pipe("query", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stderr == "los: STALE_SNAPSHOT: old\n"
    assert outcome.exit_code == 3


def test_transaction_failure_exits_2(pipe, mini_repo):
    def handler(ctx, req):
        raise TransactionFailure("boom")

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stderr == "los: INVALID_REQUEST: boom\n"
    assert outcome.exit_code == 2


class _SearchableNotFound(WriteRefused):
    """NotFound-shaped failure with controlled suggestions and remedy."""

    def __init__(self):
        super().__init__("unit u-x not found (did you mean u-a?)",
                         reason="NOT_FOUND", remedy="create it first")
        self.suggestions = ["u-a", "u-b"]


def test_refusal_suggestion_and_remedy_lines(pipe, mini_repo):
    """SPEC 9.4: suggestions print unless already in the message."""

    def handler(ctx, req):
        raise _SearchableNotFound()

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stdout == ""
    assert outcome.stderr == (
        "los: INVALID_REQUEST: unit u-x not found (did you mean u-a?)\n"
        "  did you mean: u-b\n"
        "  next: create it first\n"
    )
    assert outcome.exit_code == 2


def test_refusal_json_error_object(pipe, mini_repo):
    """SPEC 9.4: --json on a JSON-default command adds the error object."""

    from jsonschema import Draft202012Validator

    from learning_os.domain.codes import PUBLIC_CODES, REASONS

    def handler(ctx, req):
        raise _SearchableNotFound()

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP,
                                      _ns(mini_repo, json=True))
    assert outcome.stderr == (
        "los: INVALID_REQUEST: unit u-x not found (did you mean u-a?)\n"
        "  did you mean: u-b\n"
        "  next: create it first\n"
    )
    assert outcome.stdout == (
        '{"error":{"code":"INVALID_REQUEST",'
        '"message":"unit u-x not found (did you mean u-a?)",'
        '"retryable":false,'
        '"details":{"reason":"NOT_FOUND",'
        '"suggestions":["u-a","u-b"],'
        '"remedy":"create it first"}}}\n'
    )
    assert outcome.exit_code == 2
    schema_path = (Path(__file__).resolve().parent / "architecture"
                   / "cli-error.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(json.loads(outcome.stdout))
    assert schema["properties"]["error"]["properties"]["code"]["enum"] == (
        list(PUBLIC_CODES))
    assert schema["properties"]["error"]["properties"]["details"][
        "properties"]["reason"]["enum"] == list(REASONS)


def test_refusal_json_with_human_has_no_error_object(pipe, mini_repo):
    """SPEC 9.4: the stdout object needs a JSON-default command."""

    def handler(ctx, req):
        raise WriteRefused("nope")

    pipe("command", handler=handler, human=lambda payload: "NEVER")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP,
                                      _ns(mini_repo, json=True))
    assert outcome.stdout == ""
    assert outcome.stderr == "los: INVALID_REQUEST: nope\n"
    assert outcome.exit_code == 2


def test_unknown_exception_propagates(pipe, mini_repo):
    def handler(ctx, req):
        raise ValueError("boom")

    pipe("query", handler=handler)
    with pytest.raises(ValueError, match="boom"):
        pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))


def test_diagnostic_failed_exits_1_with_result(pipe, mini_repo):
    def handler(ctx, req):
        return Result({"echo": "diag"}, diagnostic_failed=True)

    pipe("query", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stdout == '{"echo":"diag"}\n'
    assert outcome.exit_code == 1


def _gateway_context(capability: str, suffix: str):
    from learning_os.contracts.gateway import (
        GatewayRequestContext,
        gateway_request_context,
    )

    intent = "sha256:" + "d" * 64
    context = GatewayRequestContext(
        request_id=f"request-{suffix}",
        idempotency_key=f"key-{suffix}",
        capability=capability,
        channel="operator",
        intent_sha256=intent,
        approval_kind="operator-approval",
        approval_subject_sha256=intent,
    )
    return gateway_request_context(context)


def _pipe_proposal(mini_repo, name: str, revision: int = 0):
    target = mini_repo / f"work/inbox/{name}.md"
    return TransactionProposal(
        capability=TEST_OP,
        writes={target: "pipe\n"},
        artifact_ids=(f"test-only:{name}",),
        expected_revisions={f"test-only:{name}": revision},
    )


def test_cli_proposal_without_gateway_request_keeps_the_legacy_refusal(
        pipe, mini_repo):
    """No gateway context: the commit step returns the legacy refusal."""

    def handler(ctx, req):
        return Result(
            {"echo": "x"}, proposal=_pipe_proposal(mini_repo, "noctx"))

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 2
    assert outcome.ok is False
    assert outcome.commit == "none"
    assert outcome.stdout == ""
    assert outcome.stderr.startswith("los: canonical writes must use ")
    assert "direct CLI application is disabled" in outcome.stderr
    assert not (mini_repo / "work/inbox/noctx.md").exists()


def test_cli_proposal_runs_after_commit_then_finish(pipe, mini_repo):
    """A real CLI commit calls after_commit once, then finish."""

    _write_gateway_wiring(mini_repo)
    order = []

    def handler(ctx, req):
        def after_commit(code, errors, confirmation):
            order.append("after_commit")
            assert code == 0
            assert errors == []

        def finish(confirmation):
            order.append("finish")
            return {"done": True, "tx": confirmation["transaction_id"]}

        return Result(
            {"echo": "x"}, proposal=_pipe_proposal(mini_repo, "order"),
            after_commit=after_commit, finish=finish)

    pipe("command", handler=handler)
    with _gateway_context(TEST_OP, "cli-order-001"):
        outcome = pipeline_module.run_cli(
            mini_repo, TEST_OP, _ns(mini_repo))
    assert order == ["after_commit", "finish"]
    assert outcome.exit_code == 0
    assert outcome.ok is True
    assert outcome.commit == "committed"
    body = json.loads(outcome.stdout)
    assert body["done"] is True
    assert body["tx"].startswith("transaction-")
    assert (mini_repo / "work/inbox/order.md").read_text(
        encoding="utf-8") == "pipe\n"


def test_cli_proposal_merges_confirmation_by_default(pipe, mini_repo):
    """Without finish, success renders {**payload, **confirmation}."""

    _write_gateway_wiring(mini_repo)

    def handler(ctx, req):
        return Result(
            {"echo": "x"}, proposal=_pipe_proposal(mini_repo, "merge"))

    pipe("command", handler=handler)
    with _gateway_context(TEST_OP, "cli-merge-001"):
        outcome = pipeline_module.run_cli(
            mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert outcome.commit == "committed"
    body = json.loads(outcome.stdout)
    assert body["echo"] == "x"
    assert body["transaction_id"].startswith("transaction-")


def test_cli_proposal_uses_on_commit_refused_lines_verbatim(
        pipe, mini_repo):
    """Custom refusal lines render once, in order, without a prefix."""

    def handler(ctx, req):
        return Result(
            {"echo": "x"}, proposal=_pipe_proposal(mini_repo, "custom"),
            on_commit_refused=lambda errors: [
                "first complaint", f"second: {len(errors)} error(s)"])

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 2
    assert outcome.stdout == ""
    assert outcome.stderr == "first complaint\nsecond: 1 error(s)\n"


def test_cli_proposal_conflict_renders_the_captured_complaint(
        pipe, mini_repo, capsys):
    """A real revision conflict prints nothing outside the outcome."""

    _write_gateway_wiring(mini_repo)

    def handler(ctx, req):
        return Result(
            {"echo": "x"}, proposal=_pipe_proposal(mini_repo, "clash"))

    pipe("command", handler=handler)
    with _gateway_context(TEST_OP, "cli-clash-first"):
        first = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert first.exit_code == 0
    capsys.readouterr()
    with _gateway_context(TEST_OP, "cli-clash-second"):
        outcome = pipeline_module.run_cli(
            mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 3
    assert outcome.ok is False
    assert outcome.stdout == ""
    assert outcome.stderr.splitlines()[0] == (
        "los: artifact revision conflict — reload the affected record "
        "before writing")
    assert json.loads(outcome.stderr.splitlines()[1]) == {
        "conflicts": {"test-only:clash": {"expected": 0, "actual": 1}}}
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_cli_after_commit_refusal_follows_cli_classification(
        pipe, mini_repo):
    """A refusal raised by after_commit renders like a handler refusal."""

    _write_gateway_wiring(mini_repo)

    def handler(ctx, req):
        def after_commit(code, errors, confirmation):
            raise WriteRefused("after-nope")

        return Result(
            {"echo": "x"}, proposal=_pipe_proposal(mini_repo, "afterbad"),
            after_commit=after_commit)

    pipe("command", handler=handler)
    with _gateway_context(TEST_OP, "cli-afterbad-001"):
        outcome = pipeline_module.run_cli(
            mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 2
    assert outcome.stdout == ""
    assert outcome.stderr == "los: INVALID_REQUEST: after-nope\n"
    assert outcome.commit == "committed"
    assert outcome.receipt["transaction_id"].startswith("transaction-")
    assert (mini_repo / outcome.receipt["receipt_path"]).is_file()
    assert outcome.replayed is False


def test_cli_proposal_snapshot_conflict_uses_cli_classification(
        pipe, mini_repo):
    """A raised snapshot conflict follows the TransactionFailure CLI row."""

    _write_gateway_wiring(mini_repo)

    def handler(ctx, req):
        proposal = _pipe_proposal(mini_repo, "stale")
        proposal = TransactionProposal(
            capability=proposal.capability, writes=proposal.writes,
            artifact_ids=proposal.artifact_ids,
            expected_revisions=dict(proposal.expected_revisions),
            expected_snapshot="sha256:" + "0" * 64)
        return Result({"echo": "x"}, proposal=proposal)

    pipe("command", handler=handler)
    with _gateway_context(TEST_OP, "cli-stale-001"):
        outcome = pipeline_module.run_cli(
            mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 2
    assert outcome.ok is False
    assert outcome.stdout == ""
    assert outcome.stderr.startswith(
        "los: STALE_SNAPSHOT: canonical snapshot conflict ")


def test_invoke_writes_exact_bytes_and_exit(pipe, mini_repo, capsys):
    pipe("query")
    exit_code = cli_adapter.invoke(_ns(mini_repo))
    out, err = capsys.readouterr()
    assert exit_code == 0
    assert out == '{"echo":"hi","n":7}\n'
    assert err == ""

    def handler(ctx, req):
        raise WriteRefused("nope")

    pipe("command", handler=handler)
    exit_code = cli_adapter.invoke(_ns(mini_repo))
    out, err = capsys.readouterr()
    assert exit_code == 2
    assert out == ""
    assert err == "los: INVALID_REQUEST: nope\n"


def test_invoke_root_resolution_matches_support_root(pipe, mini_repo, monkeypatch):
    # S13 candidate J8: adapter root spelling must equal support._root.
    calls = pipe("query")
    cli_adapter.invoke(_ns(mini_repo))
    assert calls[0]["ctx"].root == mini_repo.resolve()
    assert _repository_root() == Path(command_support.__file__).resolve().parent.parent.parent.parent

    recorded = {}

    def fake_run_cli(root, operation, args):
        recorded["root"] = root
        return pipeline_module.Outcome(
            commit="none", ok=True, payload={}, error=None,
            exit_code=0, receipt=None, replayed=False, stdout="",
            stderr="")

    monkeypatch.setattr(cli_adapter, "run_cli", fake_run_cli)
    ns = _ns(mini_repo)
    ns.root = None
    cli_adapter.invoke(ns)
    assert recorded["root"] == _repository_root()


# ---------------------------------------------------------------------------
# Gateway half (K1): the test-only operation through run_gateway.
# ---------------------------------------------------------------------------

TEST_CLI_COMMAND = "test-only-pipe"


def _write_gateway_wiring(root: Path) -> None:
    """Catalog row + payload schema + guard-carrying request schema."""
    import yaml

    from learning_os.contracts.capability_catalog import command_definitions

    catalog = root / "system" / "contracts" / "capabilities.yaml"
    data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
    data["commands"][TEST_OP] = {
        "handler": "learning_os.adapters.cli.invoke:test-only.pipe",
        "cli_command": TEST_CLI_COMMAND,
        "writes": ["work/inbox/**"],
        "invariants": [],
    }
    catalog.write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    payload_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"test-only/{TEST_OP}",
        "type": "object",
        "properties": {
            "alpha": {"type": "string"},
            "beta": {"type": "integer"},
        },
        "additionalProperties": False,
    }
    path = root / "system" / "schema" / "capabilities"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{TEST_OP}.schema.json").write_text(
        json.dumps(payload_schema, indent=2) + "\n", encoding="utf-8")
    request_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"test-only/{TEST_OP}",
        "type": "object",
        "properties": {
            "alpha": {"type": "string", "default": "A"},
            "beta": {"type": "integer", "default": 3},
            "expected_snapshot": {"type": "string"},
            "expected_revision": {"type": "array"},
        },
    }
    path = root / "system" / "schema" / "requests"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{TEST_OP}.schema.json").write_text(
        json.dumps(request_schema, indent=2) + "\n", encoding="utf-8")
    return command_definitions(root)


def _test_parser_factory():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    sub = subs.add_parser(TEST_CLI_COMMAND)
    sub.add_argument("--alpha", default="A")
    sub.add_argument("--beta", type=int, default=3)
    sub.set_defaults(func=lambda args: 0)
    return parser


def _run_test_gateway(mini_repo, envelope, *, key="k1-001"):
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.diagnostics import tracer as diag_tracer
    from learning_os.diagnostics.store import bind_store as _bind_diag_store

    if envelope is None:
        envelope = approved_v2_envelope(
            mini_repo, capability=TEST_OP, payload={}, artifact_ids=[],
            idempotency_key=key)
    _bind_diag_store(mini_repo)
    attempt = diag_tracer.begin_attempt({"capability": TEST_OP})
    return pipeline_module.run_gateway(
        mini_repo, envelope, requested=TEST_OP,
        definitions=command_definitions(mini_repo), attempt=attempt,
        replay_only=False, parser_factory=_test_parser_factory)


def test_gateway_refuses_malformed_payload_with_todays_message(
        pipe, mini_repo):
    """The K1 malformed-payload refusal carries the dispatch message."""

    from learning_os.ops.legacy import prepare_dispatch

    definitions = _write_gateway_wiring(mini_repo)
    pipe("command")
    envelope = approved_v2_envelope(
        mini_repo, capability=TEST_OP, payload={"alpha": 123},
        artifact_ids=[], idempotency_key="k1-malformed-001")
    outcome = _run_test_gateway(mini_repo, envelope)
    body = json.loads(outcome.stdout)
    assert outcome.exit_code != 0
    assert body["ok"] is False
    assert body["transaction_id"] is None
    with pytest.raises(WriteRefused) as direct:
        prepare_dispatch(
            mini_repo, definitions[TEST_OP], envelope, {"alpha": 123},
            parser_factory=_test_parser_factory)
    assert "invalid payload for test-only.pipe" in str(direct.value)
    assert body["error"]["message"] == str(direct.value)
    assert not list(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_gateway_applies_parser_defaults(pipe, mini_repo):
    """An omitted optional field arrives with its parser default."""

    definitions = _write_gateway_wiring(mini_repo)
    assert definitions[TEST_OP].cli_command == TEST_CLI_COMMAND
    calls = pipe("command")
    outcome = _run_test_gateway(mini_repo, None, key="k1-defaults-001")
    body = json.loads(outcome.stdout)
    assert outcome.exit_code == 0, outcome.stdout
    assert body["ok"] is True
    assert calls[0]["req"]["alpha"] == "A"
    assert calls[0]["req"]["beta"] == 3


def test_gateway_receives_envelope_guards_in_req(pipe, mini_repo):
    """The envelope's snapshot and revisions arrive in req."""

    from learning_os.contracts.gateway import intent_sha256
    from learning_os.fingerprint import canonical_fingerprint

    _write_gateway_wiring(mini_repo)
    calls = pipe("command")
    envelope = approved_v2_envelope(
        mini_repo, capability=TEST_OP, payload={}, artifact_ids=[],
        idempotency_key="k1-guards-001")
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    envelope["expected_revisions"] = {"test-only:k1": 0}
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    outcome = _run_test_gateway(mini_repo, envelope)
    assert outcome.exit_code == 0, outcome.stdout
    assert calls[0]["req"]["expected_snapshot"] == live
    assert calls[0]["req"]["expected_revision"] == ["test-only:k1=0"]


def test_gateway_refuses_approve_in_v2_payload(pipe, mini_repo):
    """An approve key in a V2 payload is refused before validation."""

    from learning_os.ops.legacy import prepare_dispatch

    definitions = _write_gateway_wiring(mini_repo)
    pipe("command")
    envelope = approved_v2_envelope(
        mini_repo, capability=TEST_OP, payload={"approve": True},
        artifact_ids=[], idempotency_key="k1-approve-001")
    outcome = _run_test_gateway(mini_repo, envelope)
    body = json.loads(outcome.stdout)
    assert outcome.exit_code != 0
    assert body["ok"] is False
    with pytest.raises(WriteRefused) as direct:
        prepare_dispatch(
            mini_repo, definitions[TEST_OP], envelope, {"approve": True},
            parser_factory=_test_parser_factory)
    assert body["error"]["message"] == str(direct.value)
    assert body["error"]["message"] == (
        "GatewayEnvelopeV2 approval belongs only in the envelope, "
        "not its payload")


def test_cli_check_validates_once_with_prepared_render_data(
        pipe, mini_repo, monkeypatch):
    from learning_os.ops import check as check_module

    schema_path = mini_repo / "system/schema/requests" / f"{TEST_OP}.schema.json"
    schema = json.loads(schema_path.read_text())
    schema["properties"]["check"] = {"type": "boolean"}
    schema_path.write_text(json.dumps(schema))
    prepared = {"changes": {"title": "Überblick"}, "plan_sha256": "prepared"}
    seen, validations = [], []
    real_validate = check_module.validate

    def counted(repo, *, online):
        validations.append(repo.root)
        return real_validate(repo, online=online)

    def forbidden(*args, **kwargs):
        pytest.fail("check mode must not commit, finish or run after_commit")

    def handler(ctx, req):
        seen.append((ctx.invocation, req["check"]))
        proposal = _pipe_proposal(mini_repo, "check-only")
        return Result(prepared, proposal=proposal, finish=forbidden,
                      after_commit=forbidden)

    def render(record, facts):
        assert facts is prepared
        assert record["ok"] is True
        return {**facts, "writes": record["writes"]}

    pipe("command", handler=handler, render_check=render)
    monkeypatch.setattr(check_module, "validate", counted)
    monkeypatch.setattr(pipeline_module, "commit_proposal", forbidden)
    ns = _ns(mini_repo)
    ns.check = True
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, ns)
    assert seen == [("check", True)]
    assert len(validations) == 1
    assert json.loads(outcome.stdout) == {
        **prepared, "writes": ["work/inbox/check-only.md"]}
    assert outcome.exit_code == 0
    assert (outcome.commit, outcome.receipt, outcome.replayed) == ("none", None, False)
    assert not (mini_repo / "work/inbox/check-only.md").exists()
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_cli_check_renderer_refusal_keeps_bytes_exit_and_no_commit(
        pipe, mini_repo, monkeypatch):
    schema_path = mini_repo / "system/schema/requests" / f"{TEST_OP}.schema.json"
    schema = json.loads(schema_path.read_text())
    schema["properties"]["check"] = {"type": "boolean"}
    schema_path.write_text(json.dumps(schema))

    def handler(ctx, req):
        proposal = _pipe_proposal(mini_repo, "check-refused")
        from dataclasses import replace
        return Result({"plan": "prepared"}, proposal=replace(
            proposal, deletes=None, validate_extra=lambda repo, issues: ["check refused"]))

    def render(record, prepared):
        assert prepared == {"plan": "prepared"}
        assert record["deletes"] == []
        raise WriteRefused(record["errors"][0], exit_code=3)

    pipe("command", handler=handler, render_check=render)
    ns = _ns(mini_repo)
    ns.check = True
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, ns)
    assert outcome.stdout == ""
    assert outcome.stderr == "los: INVALID_REQUEST: check refused\n"
    assert outcome.exit_code == 3
    assert outcome.commit == "none"
    assert not (mini_repo / "work/inbox/check-refused.md").exists()


def test_unadmitted_check_does_not_change_invocation(pipe, mini_repo):
    calls = pipe("query")
    ns = _ns(mini_repo)
    ns.check = True
    pipeline_module.run_cli(mini_repo, TEST_OP, ns)
    assert calls[0]["ctx"].invocation == "query"
    assert "check" not in calls[0]["req"]


def test_cli_receipt_and_replay_survive_finish_without_receipt_fields(
        pipe, mini_repo):
    import yaml

    _write_gateway_wiring(mini_repo)

    def handler(ctx, req):
        return Result({}, proposal=_pipe_proposal(mini_repo, "receipt-facts"),
                      finish=lambda confirmation: {"done": True})

    pipe("command", handler=handler)
    with _gateway_context(TEST_OP, "cli-receipt-facts"):
        first = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    with _gateway_context(TEST_OP, "cli-receipt-facts"):
        replay = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert first.stdout == replay.stdout == '{"done":true}\n'
    assert first.commit == replay.commit == "committed"
    assert first.replayed is False
    assert replay.replayed is True
    assert first.receipt == replay.receipt
    receipt = yaml.safe_load((mini_repo / first.receipt["receipt_path"]).read_text())
    assert first.receipt["transaction_id"] == receipt["id"]
    assert first.receipt["snapshot_after"] == receipt["snapshot_after"]
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 1


def test_cli_post_commit_failure_carries_actual_durable_receipt(
        pipe, mini_repo, monkeypatch):
    from learning_os.ops import commit as commit_module

    _write_gateway_wiring(mini_repo)

    def broken_touched(*args):
        raise OSError("ownership unavailable")

    def handler(ctx, req):
        return Result({}, proposal=_pipe_proposal(mini_repo, "post-failure"))

    pipe("command", handler=handler)
    monkeypatch.setattr(commit_module, "_record_touched", broken_touched)
    with _gateway_context(TEST_OP, "cli-post-failure"):
        outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 2
    assert outcome.stdout == ""
    assert outcome.commit == "committed"
    assert outcome.replayed is False
    assert (mini_repo / outcome.receipt["receipt_path"]).is_file()
    assert (mini_repo / "work/inbox/post-failure.md").read_text() == "pipe\n"


@pytest.mark.parametrize("complete, commit", [(True, "none"), (False, "unknown")])
def test_cli_projection_refusal_keeps_rollback_facts(pipe, mini_repo, complete, commit):
    from learning_os.domain.failures import ProjectionFailure

    def handler(ctx, req):
        raise ProjectionFailure("projection broke", rollback_complete=complete)

    pipe("command", handler=handler)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.stderr == "los: INVALID_REQUEST: projection broke\n"
    assert outcome.exit_code == 2
    assert outcome.commit == commit
    assert outcome.receipt is None


# ---------------------------------------------------------------------------
# S15 Task0: the render marker and purity checks (SPEC §3.5b).
# ---------------------------------------------------------------------------

CALLBACKS_DIR = Path(__file__).resolve().parent / "fixtures" / "archcheck" / "callbacks"


def _load_fixture_renderer(name: str):
    path = CALLBACKS_DIR / name
    assert path.is_file(), path
    spec = importlib.util.spec_from_file_location(f"render_fixture_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def test_render_nondeterministic_fixture_fails(pipe, mini_repo, monkeypatch):
    """The nondeterminism fixture raises through the real run_cli path."""
    render = _load_fixture_renderer("pos_render_nondeterministic.py")

    def handler(ctx, req):
        return Result({"echo": "x"}, finish=render)

    pipe("query", handler=handler)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    with pytest.raises(RenderPurityError) as caught:
        pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert str(caught.value) == f"{TEST_OP}::finish::not-deterministic"
    assert current_render() is None


def test_render_mutates_arg_fixture_fails(pipe, mini_repo, monkeypatch):
    """The mutation fixture raises through the real run_cli path."""
    render = _load_fixture_renderer("pos_render_mutates_arg.py")

    def handler(ctx, req):
        return Result({"echo": "x"}, finish=render)

    pipe("query", handler=handler)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    with pytest.raises(RenderPurityError) as caught:
        pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert str(caught.value) == f"{TEST_OP}::finish::argument-mutated"
    assert current_render() is None


def test_render_check_off_skips_purity(pipe, mini_repo, monkeypatch):
    """Without the env flag a nondeterministic renderer just runs once."""
    render = _load_fixture_renderer("pos_render_nondeterministic.py")

    def handler(ctx, req):
        return Result({"echo": "x"}, finish=render)

    pipe("query", handler=handler)
    monkeypatch.delenv("LOS_ARCH_RENDER_CHECK", raising=False)
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert json.loads(outcome.stdout)["payload"] == {}
    assert current_render() is None


def test_call_renderer_marks_and_resets(monkeypatch):
    """The marker is set during the call and reset after, check or not."""
    seen = []

    def pure(payload):
        seen.append(current_render())
        return {"ok": True}

    for flag in ("1", None):
        if flag is None:
            monkeypatch.delenv("LOS_ARCH_RENDER_CHECK", raising=False)
        else:
            monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", flag)
        seen.clear()
        assert call_renderer("op.sample", "human", pure, {"a": 1}) == {"ok": True}
        assert seen == [("op.sample", "human"), ("op.sample", "human")][: len(seen)]
        assert len(seen) == (2 if flag == "1" else 1)
        assert current_render() is None


def test_audit_hook_marks_render_io(tmp_path):
    """With the marker set, reads/listings/observations are logged as render."""
    from learning_os.ops.render import _RENDER

    log = tmp_path / "audit.jsonl"
    probe = tmp_path / "probe.txt"
    probe.write_text("x", encoding="utf-8")
    arch_audit_hook.install(str(log))
    try:
        token = _RENDER.set(("op.sample", "human"))
        try:
            with open(probe, encoding="utf-8"):
                pass
            os.listdir(tmp_path)
            observations_module.now()
        finally:
            _RENDER.reset(token)
        with open(probe, encoding="utf-8"):
            pass
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    records = arch_audit_hook.read_log(log)
    marked = [rec for rec in records if rec.get("render") is not None]
    assert {rec["event"] for rec in marked} == {
        "open", "os.listdir", "learningos.observation"}
    assert all(rec["render"] == ["op.sample", "human"] for rec in marked)
    assert all(rec.get("render") is None for rec in records
              if rec not in marked)


def test_render_violations_and_purity_scan():
    """The harness fails render-marked lines and RenderPurityError text."""
    assert render_violations([{"event": "open", "render": None}]) == []
    assert render_violations([{"event": "installed"}]) == []
    problems = render_violations([
        {"event": "open", "render": ["op.x", "human"]},
        {"event": "os.listdir", "render": ["op.x", "human"]},
    ])
    assert problems == [
        "A18 op.x::human::open: renderer performed audited I/O",
        "A18 op.x::human::os.listdir: renderer performed audited I/O",
    ]
    check_render_purity_error("los: ordinary refusal\n")
    with pytest.raises(AssertionError) as caught:
        check_render_purity_error(
            "Traceback (most recent call last):\n"
            "RenderPurityError: op.x::finish::not-deterministic\n")
    assert str(caught.value).startswith("A18 op.x::finish::RenderPurityError")


# ---------------------------------------------------------------------------
# SPEC (az), S15 item 4: type-sensitive render purity.
# ---------------------------------------------------------------------------


def test_render_type_control_argument_bool_to_int(monkeypatch):
    """Retained control: mutating False to 0 fails as argument mutated."""
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")

    def render(payload):
        payload["flag"] = 0
        return dict(payload)

    with pytest.raises(RenderPurityError) as caught:
        call_renderer("op.sample", "finish", render, {"flag": False})
    assert str(caught.value) == "op.sample::finish::argument-mutated"
    assert current_render() is None


def test_render_type_control_result_bool_to_int(monkeypatch):
    """Retained control: a result changing False to 0 is nondeterministic."""
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    calls = iter([False, 0])

    def render(payload):
        return next(calls)

    with pytest.raises(RenderPurityError) as caught:
        call_renderer("op.sample", "finish", render, {})
    assert str(caught.value) == "op.sample::finish::not-deterministic"
    assert current_render() is None


def test_render_type_control_positive(monkeypatch):
    """Exact-typed pure renderers still pass with the check on."""
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")

    def render(payload):
        return {
            "flag": False,
            "count": 0,
            "ratio": 0.0,
            "name": "",
            "missing": None,
            "nested": [{"flag": False, "tags": []}],
        }

    argument = {
        "flag": False,
        "count": 7,
        "items": [{"flag": True}, [1, "two", None]],
    }
    assert call_renderer(
        "op.sample", "finish", render, argument) == render({})
    assert argument == {
        "flag": False,
        "count": 7,
        "items": [{"flag": True}, [1, "two", None]],
    }
    assert current_render() is None


def test_render_check_on_pure_renderer_passes(pipe, mini_repo, monkeypatch):
    """With the check on, a pure finish renderer runs the CLI path cleanly."""
    def handler(ctx, req):
        return Result({"echo": "x"}, finish=lambda confirmation: {
            "echo": "x", "flag": False, "count": 0})

    pipe("query", handler=handler)
    monkeypatch.setenv("LOS_ARCH_RENDER_CHECK", "1")
    outcome = pipeline_module.run_cli(mini_repo, TEST_OP, _ns(mini_repo))
    assert outcome.exit_code == 0
    assert json.loads(outcome.stdout) == {
        "echo": "x", "flag": False, "count": 0}
    assert current_render() is None
