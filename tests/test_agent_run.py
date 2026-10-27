"""Runner contracts, with real CLI/gateway writes on ordinary fixtures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from repo_builders import add_curriculum, seed_live_goal_ids

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("agent_run", ROOT / "tools/agent_run.py")
agent_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agent_run)
INDEX = {"verbs": ["bootstrap", "capture", "inspect"],
         "verb_to_operation": {"bootstrap": "operator.bootstrap", "capture": "capture.create",
                               "inspect": "project.inspect"},
         "task_to_use": {"open-work-or-priority-question": "bootstrap"}}


def _run(plan, *args, **kwargs):
    """Legacy independent-step scenarios explicitly retain continue policy."""
    return agent_run.run_plan({"session_id": "runner-test", "on_error": "continue", **plan}, *args, **kwargs)


def test_resolver_accepts_verb_operation_and_task():
    assert agent_run.resolve_use("inspect", INDEX) == "inspect"
    assert agent_run.resolve_use("capture.create", INDEX) == "capture"
    assert agent_run.resolve_use("open-work-or-priority-question", INDEX) == "bootstrap"
    with pytest.raises(agent_run.AgentRunError, match="unknown"):
        agent_run.resolve_use("no-such-name", INDEX)


def _published(root, stamp):
    gen = root / "generated"
    gen.mkdir(exist_ok=True)
    (gen / "manifest.json").write_text(json.dumps({"_generated": {"snapshot_id": stamp}}))
    (gen / "manifest.identity.json").write_text(json.dumps({"snapshot_id": stamp, "manifest_sha256": "sha256:" + hashlib.sha256((gen / "manifest.json").read_bytes()).hexdigest()}))


def _receipt(root, name="w", snapshot="sha256:abc", create=True):
    path = root / "operations/transactions" / (name + ".yaml")
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("status: committed\n")
    return {"ok": True, "receipt_path": str(path.relative_to(root)), "snapshot_after": snapshot}


def test_readiness_requires_receipt_and_matching_published_pair(tmp_path):
    result = _receipt(tmp_path)
    _published(tmp_path, "sha256:abc")
    assert agent_run.write_ready(tmp_path, result)[0]
    _published(tmp_path, "sha256:other")
    assert not agent_run.write_ready(tmp_path, result)[0]
    assert not agent_run.write_ready(tmp_path, _receipt(tmp_path, "missing", create=False))[0]
    result["receipt_path"] = str(Path(__file__).resolve())
    assert not agent_run.write_ready(tmp_path, result)[0]


@pytest.mark.parametrize("ready", [True, False])
def test_pending_write_waits_and_stale_read_never_executes(tmp_path, ready):
    calls = []
    result = _receipt(tmp_path, create=ready)
    _published(tmp_path, "sha256:old")

    def executor(argv, root):
        calls.append(argv[0])
        return 0, json.dumps(result if argv[0] == "capture" else {"id": "fresh"}), ""

    timer = threading.Timer(0.02, _published, args=(tmp_path, "sha256:abc")) if ready else None
    if timer:
        timer.start()
    try:
        report = _run({"steps": [
            {"id": "w", "use": "capture", "write": True},
            {"id": "r", "use": "inspect", "depends_on": ["w"], "ready_timeout_s": 0.15},
            {"id": "free", "use": "bootstrap"},
        ]}, tmp_path, executor=executor, index=INDEX, poll_s=0.005)
    finally:
        if timer:
            timer.join()
    row = report["steps"][1]
    assert row["status"] == ("ok" if ready else "not_ready")
    if not ready:
        assert row["error"]["code"] == "NOT_READY"
        assert row["error"]["retryable"] is True
    assert calls == (["capture", "inspect", "bootstrap"] if ready else ["capture", "bootstrap"])


@pytest.mark.parametrize("change", ["external", "broken-identity"])
def test_unknown_projection_or_partial_publication_refuses_read(tmp_path, change):
    result = _receipt(tmp_path)
    _published(tmp_path, "sha256:external")
    if change == "broken-identity":
        (tmp_path / "generated/manifest.identity.json").write_text('{"snapshot_id":"different"}')
    calls = []

    def executor(argv, root):
        calls.append(argv[0])
        return 0, json.dumps(result), ""

    report = _run({"steps": [
        {"id": "w", "use": "capture", "write": True},
        {"id": "r", "use": "inspect", "depends_on": ["w"], "ready_timeout_s": 0},
    ]}, tmp_path, executor=executor, index=INDEX)
    assert calls == ["capture"]
    error = report["steps"][1]["error"]
    assert error["code"] == ("SNAPSHOT_CONFLICT" if change == "external" else "NOT_READY")
    assert error["retryable"] is (change != "external")


def test_write_hint_cannot_exempt_a_read_from_readiness(tmp_path):
    result = _receipt(tmp_path)
    _published(tmp_path, "sha256:external")
    calls = []

    def executor(argv, root):
        calls.append(argv[0])
        return 0, json.dumps(result), ""

    report = _run({"steps": [
        {"id": "w", "use": "capture", "write": True},
        {"id": "r", "use": "inspect", "write": True, "depends_on": ["w"], "ready_timeout_s": 0},
    ]}, tmp_path, executor=executor, index=INDEX)
    assert calls == ["capture"]
    assert report["steps"][1]["error"]["code"] == "SNAPSHOT_CONFLICT"


@pytest.mark.parametrize("steps", [
    [{"id": "a", "kind": "log", "text": "first", "key": "valid"},
     {"id": "b", "kind": "log", "text": "missing key"}],
    [{"id": "a", "kind": "log", "text": "first", "key": "same"},
     {"id": "b", "kind": "log", "text": "second", "key": "same"}],
])
def test_invalid_log_keys_refuse_whole_plan_before_any_write(tmp_path, steps):
    calls = []
    with pytest.raises(agent_run.AgentRunError, match="key"):
        _run({"steps": steps}, tmp_path,
                           executor=lambda *args: calls.append(args), index=INDEX)
    assert calls == []
    assert not (tmp_path / "operations").exists()


def _write_plan():
    return {"steps": [
        {"id": "a", "kind": "log", "text": "alpha fixture log", "key": "runner-alpha"},
        {"id": "b", "kind": "log", "text": "beta fixture log", "key": "runner-beta", "depends_on": ["a"]},
        {"id": "read", "use": "inspect", "args": ["unit-demo-l01"], "depends_on": ["a", "b"],
         "ready_timeout_s": 0},
    ]}


def test_real_logs_multiwrite_read_and_replay_use_selected_root(mini_repo):
    add_curriculum(mini_repo)
    assert not (mini_repo / "tools/learning_os").exists()
    plan = _write_plan()
    first = _run(plan, mini_repo)
    assert first["totals"]["ok"] == 3, first
    assert first["steps"][2]["output"]["id"] == "unit-demo-l01"
    for row in first["steps"][:2]:
        assert "0 error(s)" in row["validation"]
        assert (mini_repo / row["output"]["receipt_path"]).is_file()
    receipts = list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    assert len(receipts) == 2
    second = _run(plan, mini_repo)
    assert second["totals"]["ok"] == 3, second
    assert all(row["output"]["replayed"] for row in second["steps"][:2])
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 2
    # A distinct intent under an existing key remains a gateway conflict.
    plan["steps"][0]["text"] = "changed intent"
    conflict = _run(plan, mini_repo)
    assert conflict["steps"][0]["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 2


def test_real_stage_log_preserves_text_and_receipt(mini_repo):
    add_curriculum(mini_repo)
    text = 'learner wording: ä \\ "quoted"'
    result = _run({"steps": [{"id": "note", "kind": "log", "text": text,
        "key": "runner-stage", "unit_id": "unit-demo-l01", "stage_id": "stage-demo"}]}, mini_repo)
    assert result["totals"]["ok"] == 1, result
    note = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"
    assert text in note.read_text()
    assert (mini_repo / result["steps"][0]["output"]["receipt_path"]).is_file()


def test_real_replay_after_unknown_later_write_requires_reload(mini_repo):
    add_curriculum(mini_repo)
    first = {"id": "first", "kind": "log", "text": "first", "key": "known-first"}
    assert _run({"steps": [first]}, mini_repo)["totals"]["ok"] == 1
    external = {"id": "external", "kind": "log", "text": "later", "key": "external-later"}
    assert _run({"steps": [external]}, mini_repo)["totals"]["ok"] == 1
    result = _run({"steps": [first,
        {"id": "read", "use": "inspect", "args": ["note-demo"], "depends_on": ["first"], "ready_timeout_s": 0},
        {"id": "free", "use": "inspect", "args": ["note-demo"]},
    ]}, mini_repo)
    assert result["steps"][0]["output"]["replayed"] is True
    assert result["steps"][1]["error"]["code"] == "SNAPSHOT_CONFLICT"
    assert result["steps"][1]["error"]["retryable"] is False
    assert result["steps"][2]["status"] == "ok"
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 2


def test_real_cli_root_without_implementation_copy(mini_repo, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"steps": [{"id": "r", "use": "inspect", "args": ["note-demo"]}]}))
    proc = subprocess.run([sys.executable, str(ROOT / "tools/agent_run.py"), str(plan),
                           "--root", str(mini_repo)], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["steps"][0]["output"]["id"] == "note-demo"


@pytest.mark.parametrize("args", [["--root", "/tmp"], ["--root=/tmp"]])
def test_root_override_refuses_entire_plan(tmp_path, args):
    with pytest.raises(agent_run.AgentRunError, match="root overrides"):
        _run({"steps": [{"id": "r", "argv": [*args, "inspect", "note-demo"]}]}, tmp_path)


@pytest.mark.parametrize("text", ["a", "ä", '"\\\n', "😀"])
@pytest.mark.parametrize("fields", [None, ["x"]])
def test_summary_bounds_final_utf8_json(text, fields):
    encoded = agent_run.summarize({"x": text * 10000}, fields=fields, max_bytes=120)
    assert len(encoded.encode("utf-8")) <= 120
    assert json.loads(encoded)["_truncated_bytes"] > 120
    out = agent_run.summarize({"counts": {"modules": 15}}, fields=["counts.modules"])
    assert json.loads(out) == {"counts": {"modules": 15}}


@pytest.mark.parametrize("budget", [-1, 1, 63, 64.1, True])
def test_impossible_byte_budget_refuses_before_execution(tmp_path, budget):
    with pytest.raises(agent_run.AgentRunError, match="max_bytes"):
        _run({"steps": [{"id": "r", "use": "inspect", "summary": {"max_bytes": budget}}]}, tmp_path)


@pytest.mark.parametrize("code,out,expected", [
    (2, "", "PREFLIGHT_FAILED"),
    (1, "validator crashed", "PREFLIGHT_FAILED"),
    (0, "", "PREFLIGHT_FAILED"),
    (1, "E GLOBAL: pathless error\n1 error(s), 0 warning(s) — FAIL", "VALIDATION_FAILED"),
    (1, "E A: in scope [work/inbox/a.md]\nE B: elsewhere [curriculum/b.yaml]\n"
        "2 error(s), 0 warning(s) — FAIL", "VALIDATION_FAILED"),
])
def test_preflight_failure_blocks_execution_and_keeps_pathless_errors(tmp_path, code, out, expected):
    calls = []

    def executor(argv, root):
        calls.append(argv)
        return code, out, "validator stderr"

    result = _run({"steps": [{"id": "w", "kind": "log", "text": "x",
        "key": "preflight-test", "preflight": True, "writes": ["work/inbox/**"]}]},
        tmp_path, executor=executor, index=INDEX)
    assert calls == [["validate"]]
    error = result["steps"][0]["error"]
    assert error["code"] == expected
    if "GLOBAL" in out:
        assert error["scope"]["unrelated"][0]["path"] == ""
    if "E A:" in out:
        assert [e["code"] for e in error["scope"]["in_scope"]] == ["A"]
        assert [e["code"] for e in error["scope"]["unrelated"]] == ["B"]


def test_real_preflight_catches_unrelated_error_before_sealing(mini_repo):
    add_curriculum(mini_repo)
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text().replace("concept-expected-value", "concept-does-not-exist"))
    result = _run({"steps": [{"id": "w", "kind": "log", "text": "must not write",
        "key": "preflight-refused", "preflight": True, "writes": ["work/inbox/**"]}]}, mini_repo)
    error = result["steps"][0]["error"]
    assert error["code"] == "VALIDATION_FAILED", result
    assert error["scope"]["unrelated"]
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    assert not list((mini_repo / "work/inbox").iterdir())


def test_preflight_revalidates_after_write_and_gateway_still_checks(mini_repo):
    add_curriculum(mini_repo)
    plan = _write_plan()
    for row in plan["steps"][:2]:
        row.update(preflight=True, writes=["work/inbox/**"])
    execute = agent_run._cli_executor_factory(mini_repo)
    validations = []

    def executor(argv, root):
        if argv == ["validate"]:
            validations.append(len(list((root / "operations/transactions").glob("transaction-*.yaml"))))
        return execute(argv, root)

    result = _run(plan, mini_repo, executor=executor)
    assert result["totals"]["ok"] == 3, result
    assert validations == [0, 1]
    assert all("0 error(s)" in row["validation"] for row in result["steps"][:2])


@pytest.mark.parametrize("args", [[], ["--brief", "--json"]])
def test_cluster_expansion_is_executable_and_recovers_all_members(mini_repo, args):
    expected = seed_live_goal_ids(mini_repo, "one", "two", "three")
    execute = agent_run._cli_executor_factory(mini_repo)
    result = _run({"steps": [{"id": "q", "use": "intelligence-scan",
        "args": args, "clusters": True}]}, mini_repo, executor=execute)
    assert result["totals"]["ok"] == 1, result
    preview = result["steps"][0]["output"]
    assert "--cluster" not in preview["expand_argv"]
    assert "--brief" not in preview["expand_argv"]
    code, out, err = execute(preview["expand_argv"], mini_repo)
    assert code == 0, err
    full = json.loads(out)
    assert set(expected).issubset({goal["goal_id"] for goal in full["goals"]})
    assert preview["total_goals"] == len(full["goals"])


def test_cluster_byte_cap_preserves_counts_and_expansion(tmp_path):
    scan = {"groups": [{"cluster_id": "c", "title": "ä" * 1000,
        "member_count": 107, "sample_goal_ids": ["g1", "g2"]}],
        "total_groups": 9, "total_goals": 200, "omitted_groups": 8, "omitted_goals": 93,
        "full_result": "intelligence-scan --json"}
    report = _run({"steps": [{"id": "q", "clusters": True,
        "argv": ["intelligence-scan", "--brief", "--json"], "summary": {"max_bytes": 260}}]},
        tmp_path, executor=lambda *a: (0, json.dumps(scan), ""), index=INDEX)
    row = report["steps"][0]
    assert row["status"] == "ok", row
    assert row["out_bytes"] <= 260
    assert len(json.dumps(row["output"], ensure_ascii=False, separators=(",", ":")).encode()) <= 260
    assert row["output"]["omitted_groups"] == 9
    assert row["output"]["omitted_goals"] == 200
    assert row["output"]["expand_argv"] == ["intelligence-scan", "--json"]


def test_followup_projection_cannot_precede_latest_required_write(tmp_path):
    a = _receipt(tmp_path, "a", "sha256:A")
    b = _receipt(tmp_path, "b", "sha256:B")
    c = _receipt(tmp_path, "c", "sha256:C")
    _published(tmp_path, "sha256:A")
    assert not agent_run.writes_ready(tmp_path, [a, b], [a, b])[0]
    _published(tmp_path, "sha256:B")
    assert agent_run.writes_ready(tmp_path, [b, a], [a, b])[0]
    _published(tmp_path, "sha256:C")
    assert agent_run.writes_ready(tmp_path, [a, b], [a, b, c])[0]


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_followup_nonfinite_output_is_per_step_failure(tmp_path, number):
    def executor(argv, root):
        return (0, '{"x":' + number + '}', "") if argv[0] == "inspect" else (0, '{"ok":true}', "")
    report = agent_run.run_plan({"on_error": "continue", "steps": [
        {"id": "bad", "use": "inspect"}, {"id": "good", "use": "bootstrap"},
    ]}, tmp_path, executor=executor, index=INDEX)
    assert report["steps"][0]["error"]["code"] == "INVALID_STEP_OUTPUT"
    assert report["steps"][1]["status"] == "ok"
    assert report["totals"]["ok"] == 1


def test_followup_missing_fields_are_explicit_and_bounded():
    result = agent_run.summarize({"a": 1, "empty": None}, fields=["a", "empty", "nope.deep"], max_bytes=120)
    decoded = json.loads(result)
    assert decoded == {"a": 1, "empty": None, "_missing_fields": ["nope.deep"]}
    assert len(result.encode()) <= 120
    truncated = json.loads(agent_run.summarize({"a": "ä" * 1000}, fields=["a", "missing"], max_bytes=120))
    assert truncated["_missing_fields"] == ["missing"]
    with pytest.raises(agent_run.AgentRunError, match="metadata"):
        agent_run.summarize({}, fields=["missing" * 100], max_bytes=64)


@pytest.mark.parametrize("explicit", [False, True])
def test_followup_stop_policy_preserves_commit_and_skips_later_write(mini_repo, explicit):
    add_curriculum(mini_repo)
    plan = {"session_id": "stop-policy", "steps": [
        {"id": "a", "kind": "log", "text": "first committed", "key": "stop-a"},
        {"id": "bad", "use": "inspect", "args": ["not-a-record"]},
        {"id": "b", "kind": "log", "text": "must not commit", "key": "stop-b"},
    ]}
    if explicit:
        plan["on_error"] = "stop"
    report = agent_run.run_plan(plan, mini_repo)
    assert report["steps"][0]["status"] == "ok"
    assert report["steps"][1]["status"] == "error"
    assert report["steps"][2]["status"] == "skipped"
    assert report["steps"][2]["error"]["code"] == "PLAN_STOPPED"
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 1


def test_followup_plan_sessions_isolate_ledgers_and_restore_environment(mini_repo, monkeypatch):
    from learning_os.store.session_ledger import load_session_paths
    add_curriculum(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "outside-session")
    for session in ("agent-A", "agent-B"):
        plan = {"session_id": session, "steps": [{"id": "log", "kind": "log", "text": session, "key": session}]}
        report = agent_run.run_plan(plan, mini_repo)
        assert report["totals"]["ok"] == 1, report
        assert report["session_id"] == session
    a = load_session_paths(mini_repo, "agent-A")
    b = load_session_paths(mini_repo, "agent-B")
    a_captures = {path for path in a if path.startswith("work/inbox/")}
    b_captures = {path for path in b if path.startswith("work/inbox/")}
    assert len(a_captures) == len(b_captures) == 1
    assert not a_captures.intersection(b_captures)
    assert not load_session_paths(mini_repo, "outside-session")
    import os
    assert os.environ["LOS_SESSION_ID"] == "outside-session"


@pytest.mark.parametrize("bound_session", ["other-session", "plan-session"])
def test_followup_gateway_requires_matching_sealed_session(mini_repo, tmp_path, bound_session):
    from gateway_helpers import approved_v2_envelope, request_artifact_id

    from learning_os.store.contracts.gateway import intent_sha256
    add_curriculum(mini_repo)
    envelope = approved_v2_envelope(mini_repo, capability="capture.create", payload={"text": "wrong session"},
        artifact_ids=[request_artifact_id("capture.create", "bound-session")], idempotency_key="bound-session")
    envelope["session_id"] = bound_session
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(envelope))
    before = path.read_bytes()
    report = agent_run.run_plan({"session_id": "plan-session", "steps": [
        {"id": "write", "use": "capability", "args": ["capture.create", "--payload-file", str(path)]}
    ]}, mini_repo)
    receipts = list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    if bound_session == "other-session":
        assert report["steps"][0]["error"]["code"] == "SESSION_MISMATCH"
        assert not receipts
    else:
        assert report["steps"][0]["status"] == "ok", report
        assert len(receipts) == 1
    assert path.read_bytes() == before


@pytest.mark.parametrize("extra", [{}, {"session_id": ""}, {"session_id": " x "},
                                    {"session_id": "x" * 129},
                                    {"session_id": "s", "on_error": "ignore"}])
def test_write_plan_session_and_policy_validate_before_execution(tmp_path, extra):
    calls = []
    with pytest.raises(agent_run.AgentRunError):
        agent_run.run_plan({**extra, "steps": [
            {"id": "write", "kind": "log", "text": "x", "key": "key"}
        ]}, tmp_path, executor=lambda *a: calls.append(a), index=INDEX)
    assert calls == []


def test_session_environment_restores_when_execution_raises(tmp_path, monkeypatch):
    import os
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)

    def fail(argv, root):
        assert os.environ["LOS_SESSION_ID"] == "local-session"
        raise OSError("broken executor")

    report = agent_run.run_plan({"session_id": "local-session", "steps": [
        {"id": "fail", "use": "inspect"}, {"id": "skipped", "use": "bootstrap"},
    ]}, tmp_path, executor=fail, index=INDEX)
    assert report["steps"][0]["status"] == "error"
    assert report["steps"][1]["status"] == "skipped"
    assert "LOS_SESSION_ID" not in os.environ


def test_parser_classified_writer_requires_plan_session(mini_repo):
    with pytest.raises(agent_run.AgentRunError, match="session_id"):
        agent_run.run_plan({"steps": [{"id": "goal", "use": "goal", "args": ["missing"]}]}, mini_repo)
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_nonfinite_cli_failure_returns_complete_report(tmp_path, monkeypatch, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"on_error": "continue", "steps": [
        {"id": "bad", "use": "inspect"}, {"id": "good", "use": "bootstrap"},
    ]}))
    original = agent_run.run_plan

    def run(plan, root, **kwargs):
        def executor(argv, root):
            return 0, '{"x":NaN}' if argv[0] == "inspect" else '{"ok":true}', ""
        return original(plan, root, executor=executor, index=INDEX)

    monkeypatch.setattr(agent_run, "run_plan", run)
    monkeypatch.setattr(sys, "argv", ["agent_run.py", str(plan), "--root", str(tmp_path)])
    assert agent_run.main() == 3
    report = json.loads(capsys.readouterr().out)
    assert report["steps"][0]["error"]["code"] == "INVALID_STEP_OUTPUT"
    assert report["steps"][1]["status"] == "ok"


def test_internal_seal_marker_cannot_be_supplied_by_plan(mini_repo):
    add_curriculum(mini_repo)
    with pytest.raises(agent_run.AgentRunError, match="internal"):
        agent_run.run_plan({"steps": [{"id": "write", "argv": [
            "__seal_submit__", "capture.create", '{"text":"must not write"}', "private-bypass",
        ]}]}, mini_repo)
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_prefixed_gateway_write_cannot_escape_session_requirement(mini_repo, tmp_path):
    from gateway_helpers import approved_v2_envelope, request_artifact_id
    add_curriculum(mini_repo)
    key = "prefixed-gateway"
    envelope = approved_v2_envelope(mini_repo, capability="capture.create", payload={"text": "must not write"},
        artifact_ids=[request_artifact_id("capture.create", key)], idempotency_key=key)
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(envelope))
    report = agent_run.run_plan({"steps": [{"id": "write", "argv": [
        "--lock-timeout", "1", "capability", "capture.create", "--payload-file", str(path),
    ]}]}, mini_repo)
    assert report["steps"][0]["error"]["code"] == "SESSION_REQUIRED"
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


@pytest.mark.parametrize("flag", ["--roo", "--r"])
def test_abbreviated_root_override_cannot_change_selected_root(mini_repo, tmp_path, flag):
    from conftest import build_mini_repo
    other = build_mini_repo(tmp_path / "other")
    note = other / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text().replace("id: note-demo", "id: note-other"))
    report = agent_run.run_plan({"steps": [{"id": "read", "argv": [
        flag, str(other), "inspect", "note-other",
    ]}]}, mini_repo)
    assert report["steps"][0]["error"]["code"] == "ROOT_MISMATCH"


def test_abbreviated_session_override_is_checked_after_parsing(mini_repo, monkeypatch):
    from learning_os.adapters import cli_entry
    original = cli_entry.run
    calls = []

    def spy(namespace):
        if namespace.command == "session-end":
            calls.append(namespace.session_id)
            return 0
        return original(namespace)

    monkeypatch.setattr(cli_entry, "run", spy)
    report = agent_run.run_plan({"session_id": "plan-session", "steps": [
        {"id": "end", "argv": ["session-end", "--session-i", "other-session"]},
    ]}, mini_repo)
    assert report["steps"][0]["error"]["code"] == "SESSION_MISMATCH"
    assert calls == []


def test_flag_like_log_values_are_passed_as_values(mini_repo):
    add_curriculum(mini_repo)
    report = agent_run.run_plan({"session_id": "--root", "steps": [
        {"id": "log", "kind": "log", "text": "flag-like values", "key": "flag-like-values"},
    ]}, mini_repo)
    assert report["steps"][0]["status"] == "ok", report


def test_takeover_whole_report_cap_is_always_enforced(tmp_path):
    report = _run({'report_max_bytes': 4096, 'steps': [
        {'id': str(i), 'argv': ['inspect'], 'summary': {'max_bytes': 1500}}
        for i in range(10)]}, tmp_path, index=INDEX,
        executor=lambda *_: (0, json.dumps({'value': 'x' * 1200}), 'notice'))
    assert len((agent_run._json(report) + '\n').encode()) <= 4096
    full = Path(report['full_report'])
    assert full.is_file()
    assert len(json.loads(full.read_text())['steps']) == 10
    from learning_os.app.agent_reporting import expand_report
    expanded = expand_report(full)
    assert len(expanded['steps']) == 10
    assert all(r['raw']['stderr'] == 'notice' for r in expanded['steps'])
    assert expanded['steps'][0]['raw']['stdout'] == json.dumps({'value': 'x' * 1200})
    (full.parent / 'raw-steps.jsonl').write_bytes(b'{}\n')
    with pytest.raises((ValueError, KeyError)):
        expand_report(full)


def test_takeover_late_bad_arguments_refuse_before_any_write(tmp_path):
    calls = []
    report = _run({'steps': [
        {'id': 'write', 'kind': 'log', 'text': 'must not execute', 'key': 'stable-key'},
        {'id': 'invalid', 'use': 'does-not-exist'}]}, tmp_path, index=INDEX,
        executor=lambda *args: calls.append(args))
    assert calls == []
    assert report['steps'][1]['status'] == 'error'


def test_takeover_parallel_reads_do_not_cross_write_barrier(tmp_path):
    calls = []
    def executor(argv, root):
        calls.append(argv[0])
        return 0, '{"value":1}', ''
    _run({'read_workers': 2, 'steps': [
        {'id': 'a', 'argv': ['inspect']},
        {'id': 'w', 'argv': ['capture'], 'write': True},
        {'id': 'b', 'argv': ['bootstrap']}]}, tmp_path, index=INDEX, executor=executor)
    assert calls == ['inspect', 'capture', 'bootstrap']


def test_takeover_global_deadline_bounds_readiness(tmp_path):
    import time
    result = _receipt(tmp_path)
    _published(tmp_path, 'sha256:other')
    calls = []
    def executor(argv, root):
        calls.append(argv[0])
        return 0, json.dumps(result), ''
    started = time.monotonic()
    report = _run({'deadline_s': 0.04, 'steps': [
        {'id': 'w', 'argv': ['capture'], 'write': True},
        {'id': 'r', 'argv': ['inspect'], 'depends_on': ['w'], 'ready_timeout_s': 5}]},
        tmp_path, index=INDEX, executor=executor, poll_s=0.005)
    assert time.monotonic() - started < 1
    assert report['steps'][1]['status'] == 'deadline'
    assert calls == ['capture']


def test_takeover_real_process_wave_and_write_barrier(mini_repo):
    report = _run({'read_workers': 2, 'steps': [
        {'id': 'a', 'argv': ['inspect', 'note-demo']},
        {'id': 'b', 'argv': ['bootstrap', '--brief']},
        {'id': 'w', 'kind': 'log', 'text': 'worker barrier', 'key': 'worker-barrier'},
        {'id': 'after', 'argv': ['inspect', 'note-demo'], 'depends_on': ['w']}]}, mini_repo)
    assert report['totals']['ok'] == 4, report
    assert report['totals']['process_count'] == 4  # runner + two persistent workers + sealer
    assert report['steps'][2]['commit_certainty'] == 'committed'


def test_takeover_read_epoch_reuses_model_and_detects_authored_change(mini_repo):
    from learning_os.app.read_session import ReadSession
    session = ReadSession(mini_repo)
    session.put(('inspect', 'note-demo'), {'value': 'old'})
    note = mini_repo / 'knowledge/notes/mathematics/note-demo.md'
    note.write_text(note.read_text() + '\nChanged authored content.\n')
    assert session.get(('inspect', 'note-demo')) is None
    report = _run({'steps': [
        {'id': 'a', 'argv': ['inspect', 'note-demo']},
        {'id': 'b', 'argv': ['inspect', 'note-demo']}]}, mini_repo)
    assert report['totals']['ok'] == 2, report
    assert report['totals']['memo_hits'] == 1
    assert report['totals']['model_loads'] <= 1


def test_takeover_report_schema_and_missing_fields_survive_cap(tmp_path):
    from jsonschema import Draft202012Validator
    report = _run({'report_max_bytes': 2048, 'steps': [
        {'id': 'a', 'argv': ['inspect'], 'summary': {'fields': ['missing'], 'max_bytes': 1000}}]},
        tmp_path, index=INDEX, executor=lambda *_: (0, '{}', ''))
    schema = json.loads((ROOT / 'system/contracts/agent-plan-report.schema.json').read_text())
    Draft202012Validator(schema).validate(report)
    assert report['steps'][0]['output']['_missing_fields'] == ['missing']


def test_takeover_typed_preflight_keeps_error_severity(mini_repo, monkeypatch):
    from learning_os.app import validation_service
    from learning_os.domain.validation import Issue
    monkeypatch.setattr(validation_service, 'status_issues',
                        lambda *a, **k: [Issue('E', 'SYNTHETIC', 'blocked', 'unrelated.yaml')])
    report = validation_service.diagnostic_report(mini_repo)
    assert report['trustworthy'] is True and report['ok'] is False
    assert report['errors'][0]['path'] == 'unrelated.yaml'


def test_artifact_failure_preserves_commit_and_blocks_later_writes(tmp_path, monkeypatch):
    from learning_os.app.agent_reporting import ReportStore
    result = _receipt(tmp_path)
    calls = []
    def execute(argv, root):
        calls.append(argv[0])
        return 0, json.dumps(result), ''
    monkeypatch.setattr(ReportStore, 'record', lambda *_: (_ for _ in ()).throw(OSError('disk full')))
    report = _run({'on_error': 'continue', 'steps': [
        {'id': 'first', 'argv': ['capture'], 'write': True},
        {'id': 'later', 'argv': ['capture'], 'write': True}]},
        tmp_path, index=INDEX, executor=execute)
    assert calls == ['capture']
    assert report['steps'][0]['commit_certainty'] == 'committed'
    assert report['steps'][0]['receipt']['receipt_path'] == result['receipt_path']
    assert report['steps'][0]['error']['code'] == 'ARTIFACT_FAILED'
    assert report['steps'][1]['status'] == 'error'  # record of the refusal also fails


def test_explicit_read_commands_need_no_task_catalogue(mini_repo, monkeypatch):
    from learning_os.store.contracts import verb_catalogue
    def unnecessary(*_):
        raise AssertionError('an explicit command must not expand task prose')
    monkeypatch.setattr(verb_catalogue, 'build_verb_catalogue', unnecessary)
    report = _run({'steps': [{'id': 'read', 'argv': ['inspect', 'note-demo']}]}, mini_repo)
    assert report['totals']['ok'] == 1, report


@pytest.mark.parametrize("kind", [None, "unknown", "porcelain", "command", "query", "tool"])
def test_write_classification_is_conservative_and_independent_of_task_resolution(mini_repo, monkeypatch, kind):
    from dataclasses import replace

    from learning_os.app.registry import REGISTRY

    executor = agent_run._cli_executor_factory(mini_repo.resolve())
    original = REGISTRY["project.inspect"]
    if kind is None:
        monkeypatch.delitem(REGISTRY, "project.inspect")
    else:
        monkeypatch.setitem(REGISTRY, "project.inspect", replace(original, kind=kind))
    direct = agent_run.build_index(mini_repo, executor, resolve_tasks=False)
    expanded = agent_run.build_index(mini_repo, executor, resolve_tasks=True)
    assert set(direct["write_verbs"]) == set(expanded["write_verbs"])
    for index in (direct, expanded):
        assert {"session-end", "generate", "ai-action-prepare", "ai-action-append-slices",
                "ai-action-import-delivery"}.issubset(index["write_verbs"])
        assert ("inspect" in index["write_verbs"]) is (kind not in {"query", "tool"})
        assert "bootstrap" not in index["write_verbs"]
        assert "capabilities" not in index["write_verbs"]


@pytest.mark.parametrize("form", ["argv", "prefixed", "use"])
@pytest.mark.parametrize("mixed", [False, True])
def test_session_end_commit_push_requires_plan_session_before_dispatch(mini_repo, monkeypatch, form, mixed):
    from types import SimpleNamespace

    from learning_os.adapters import cli

    calls = []
    monkeypatch.setattr(cli, "invoke_outcome", lambda ns: (
        calls.append(ns.command) or SimpleNamespace(exit_code=0, stdout='{"ok":true}', stderr="")))
    args = ["--commit-message", "fixture commit", "--push"]
    step = ({"id": "end", "use": "session.end", "args": args} if form == "use" else
            {"id": "end", "argv": [*(["--lock-timeout", "1"] if form == "prefixed" else []), "session-end", *args]})
    step["write"] = False  # A presentation hint cannot weaken registry effects.
    steps = ([{"id": "read", "use": "inspect", "args": ["note-demo"]}] if mixed else []) + [step]
    try:
        report = agent_run.run_plan({"steps": steps}, mini_repo)
    except agent_run.AgentRunError as exc:
        assert exc.code == "SESSION_REQUIRED"
    else:
        assert report["steps"][-1]["error"]["code"] == "SESSION_REQUIRED", report
    assert calls == []


@pytest.mark.parametrize("use", [False, True])
def test_uncertain_write_blocks_porcelain_but_allows_independent_read(mini_repo, monkeypatch, use):
    from types import SimpleNamespace

    from learning_os.adapters import cli

    calls = []

    def lost_write_response(argv, **kwargs):
        assert any(str(arg).endswith("/seal_envelope.py") for arg in argv)
        calls.append("seal")
        return subprocess.CompletedProcess(argv, 1, "", "fixture lost write response")

    def dispatch(namespace):
        calls.append(namespace.command)
        return SimpleNamespace(exit_code=0, stdout='{"ok":true}', stderr="")

    monkeypatch.setattr(agent_run.subprocess, "run", lost_write_response)
    monkeypatch.setattr(cli, "invoke_outcome", dispatch)
    step = ({"id": "end", "use": "session-end", "args": ["--commit-message", "fixture", "--push"]}
            if use else {"id": "end", "argv": ["session-end", "--commit-message", "fixture", "--push"]})
    report = agent_run.run_plan({"session_id": "classification-fixture", "on_error": "continue", "steps": [
        {"id": "write", "kind": "log", "text": "fixture", "key": "classification-fixture"},
        step, {"id": "read", "argv": ["inspect", "note-demo"]},
    ]}, mini_repo)
    assert calls == ["seal", "inspect"], report
    assert report["steps"][0]["commit_certainty"] == "uncertain"
    assert report["steps"][1]["status"] == "skipped"
    assert report["steps"][1]["error"]["code"] == "PLAN_STOPPED"
    assert report["steps"][2]["status"] == "ok"


def test_describing_porcelain_requires_no_write_session(mini_repo):
    report = agent_run.run_plan({"steps": [
        {"id": "describe", "use": "session-end", "describe": True},
    ]}, mini_repo)
    assert report["totals"]["ok"] == 1, report
    assert report["steps"][0]["commit_certainty"] == "none"


def test_external_feed_reads_are_neither_memoized_nor_parallel(mini_repo, tmp_path):
    feed = tmp_path / 'external-feed.json'
    feed.write_text('{}')
    report = _run({'read_workers': 4, 'steps': [
        {'id': str(i), 'argv': ['intelligence-scan', '--brief', '--json', '--fe', str(feed)]}
        for i in range(2)]}, mini_repo)
    assert report['totals']['ok'] == 2, report
    assert report['totals']['memo_hits'] == 0
    assert report['totals']['process_count'] == 1
    assert report['totals']['model_loads'] == 2
