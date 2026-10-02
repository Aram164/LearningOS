"""Per-session ownership ledgers: session-end claims only its own writes (#98).

The A/B reproduction from the issue: actor A writes (standing in for the
UI), then actor B writes and closes. Before the fix both landed in one
shared ledger, so B's review listed A's files and `--commit-message` would
commit them under B's message. Now every gateway transaction records its
session, and B sees A's rows only under `other_sessions`, never staged.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest
from gateway_helpers import approved_v2_envelope, run_v2_capability
from repo_builders import run_los

from learning_os.commands import support as command_support
from learning_os.contracts.gateway import intent_sha256, request_artifact_id
from learning_os.fingerprint import canonical_fingerprint

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def _git_init(root: Path) -> None:
    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture baseline"]):
        subprocess.run(command, cwd=root, check=True)


def _ui_envelope(root: Path, key: str, text: str) -> dict:
    """A UI-channel capture envelope, as the Obsidian UI would seal it."""
    envelope = {
        "schema_version": 2,
        "request_id": f"request-{key}",
        "idempotency_key": key,
        "capability": "capture.create",
        "channel": "ui",
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": {request_artifact_id("capture.create", key): 0},
        "approval": {
            "kind": "direct-user-gesture",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {"text": text},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def _capture(root: Path, *, key: str, text: str, channel: str = "operator") -> str:
    if channel == "ui":
        envelope = _ui_envelope(root, key, text)
    else:
        envelope = approved_v2_envelope(
            root, capability="capture.create", payload={"text": text},
            artifact_ids=[request_artifact_id("capture.create", key)],
            idempotency_key=key,
        )
    result = run_v2_capability(root, envelope)
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)["result"]["captured"]


def _session_end(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), "session-end", *args],
        capture_output=True, text=True, timeout=120,
    )


def test_session_end_lists_only_its_own_channel_rows(mini_repo, monkeypatch):
    """The A/B reproduction with no named sessions: channel separation."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    actor_a = _capture(mini_repo, key="ab-repro-a-001", text="A's note",
                       channel="ui")
    actor_b = _capture(mini_repo, key="ab-repro-b-001", text="B's note",
                       channel="operator")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["session_id"] == "channel:operator"
    assert actor_b in payload["touched"]
    assert actor_a not in payload["touched"]
    assert actor_a not in "".join(payload["owned_changes"])
    assert "channel:ui" in payload["other_sessions"]
    assert actor_a in payload["other_sessions"]["channel:ui"]["paths"]
    assert payload["other_sessions"]["channel:ui"]["age_hours"] is not None


def test_session_end_commit_stages_only_its_own_rows(mini_repo, monkeypatch):
    """`--commit-message` commits B's write and leaves A's uncommitted."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    actor_a = _capture(mini_repo, key="ab-commit-a-001", text="A's note",
                       channel="ui")
    actor_b = _capture(mini_repo, key="ab-commit-b-001", text="B's note",
                       channel="operator")

    closed = _session_end(mini_repo, "--commit-message", "B's session")
    assert closed.returncode == 0, closed.stderr or closed.stdout
    committed = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=mini_repo, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert actor_b in committed
    assert actor_a not in committed
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=mini_repo,
        capture_output=True, text=True, check=True,
    ).stdout
    assert actor_a in status


def test_named_sessions_share_nothing_within_one_channel(mini_repo, monkeypatch):
    """Two agent sessions on the same channel stay separate by token."""
    _git_init(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "session-alpha")
    actor_a = _capture(mini_repo, key="token-a-001", text="alpha note")
    monkeypatch.setenv("LOS_SESSION_ID", "session-beta")
    actor_b = _capture(mini_repo, key="token-b-001", text="beta note")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["session_id"] == "session-beta"
    assert actor_b in payload["touched"]
    assert actor_a not in payload["touched"]
    assert "session-alpha" in payload["other_sessions"]
    assert actor_a in payload["other_sessions"]["session-alpha"]["paths"]


def test_ui_session_mirrors_production_identity(mini_repo, monkeypatch):
    """The UI's real identity (`LOS_SESSION_ID=ui`, channel ui) vs an agent."""
    _git_init(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "ui")
    ui_file = _capture(mini_repo, key="ui-prod-001", text="learner note",
                       channel="ui")
    monkeypatch.setenv("LOS_SESSION_ID", "agent-9")
    agent_file = _capture(mini_repo, key="agent-prod-001", text="agent note")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert agent_file in payload["touched"]
    assert ui_file not in payload["touched"]
    assert ui_file in payload["other_sessions"]["ui"]["paths"]

    # And the UI side sees the mirror image.
    monkeypatch.setenv("LOS_SESSION_ID", "ui")
    ui_review = _session_end(mini_repo, "--session-id", "ui")
    assert ui_review.returncode == 0, ui_review.stderr
    ui_payload = json.loads(ui_review.stdout)
    assert ui_file in ui_payload["touched"]
    assert agent_file not in ui_payload["touched"]


def test_review_only_close_leaves_other_sessions_ledger(mini_repo, monkeypatch):
    """Closing B must not wipe A's unclaimed rows (the UI-wipe defect)."""
    _git_init(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "session-a")
    actor_a = _capture(mini_repo, key="wipe-a-001", text="A's note")
    ledger_a = command_support._session_ledger(mini_repo, "session-a")
    assert ledger_a.is_file()
    monkeypatch.setenv("LOS_SESSION_ID", "session-b")
    _capture(mini_repo, key="wipe-b-001", text="B's note")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    assert json.loads(review.stdout)["session_closed"] is True
    assert not command_support._session_ledger(mini_repo, "session-b").exists()
    assert ledger_a.is_file(), "B's close deleted A's ledger"

    monkeypatch.setenv("LOS_SESSION_ID", "session-a")
    review_a = _session_end(mini_repo)
    assert review_a.returncode == 0, review_a.stderr
    assert actor_a in json.loads(review_a.stdout)["touched"]


def _age_own_ledger(mini_repo: Path, session: str, hours: int = 25) -> None:
    ledger = command_support._session_ledger(mini_repo, session)
    data = json.loads(ledger.read_text(encoding="utf-8"))
    aged = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=hours)).isoformat()
    for row in data["paths"].values():
        row["recorded_at"] = aged
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")


def test_stale_rows_are_reported_and_not_staged(mini_repo, monkeypatch):
    """A row older than the threshold surfaces as stale, never staged."""
    monkeypatch.setenv("LOS_SESSION_ID", "stale-session")
    _git_init(mini_repo)
    captured = _capture(mini_repo, key="stale-001", text="old note")
    _age_own_ledger(mini_repo, "stale-session")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert captured in payload["stale_paths"]
    assert captured not in payload["touched"]

    # The review-only close ended that window; a second aged window proves
    # the commit path refuses stale rows by default but stages them with
    # the explicit opt-in (after the same ownership check).
    captured = _capture(mini_repo, key="stale-002", text="old note two")
    _age_own_ledger(mini_repo, "stale-session")
    refused = _session_end(mini_repo, "--commit-message", "should not land")
    assert refused.returncode == 2
    assert "no files were touched" in refused.stderr

    included = _session_end(mini_repo, "--commit-message", "stale, reviewed",
                            "--include-stale")
    assert included.returncode == 0, included.stderr or included.stdout
    assert captured in json.loads(included.stdout)["touched"]


def test_legacy_shared_ledger_surfaces_as_foreign(mini_repo, monkeypatch):
    """Pre-session rows are reported under `legacy`, never staged."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    legacy = command_support._legacy_session_ledger(mini_repo)
    legacy.write_text(json.dumps({
        "schema_version": 1,
        "paths": {"work/inbox/legacy.md": {"state": "absent"}},
    }), encoding="utf-8")
    (mini_repo / "work/inbox/legacy.md").write_text("legacy\n", encoding="utf-8")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["touched"] == []
    assert "work/inbox/legacy.md" in payload["other_sessions"]["legacy"]["stale_paths"]

    refused = _session_end(mini_repo, "--commit-message", "must not claim legacy")
    assert refused.returncode == 2
    assert "no files were touched" in refused.stderr


def test_session_id_flag_overrides_the_environment(mini_repo, monkeypatch):
    """`--session-id` closes exactly the named session, whatever the env says."""
    _git_init(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "session-named")
    captured = _capture(mini_repo, key="flag-001", text="named note")
    monkeypatch.setenv("LOS_SESSION_ID", "session-elsewhere")

    review = _session_end(mini_repo, "--session-id", "session-named")
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["session_id"] == "session-named"
    assert captured in payload["touched"]

    # The ambient session still sees nothing of its own.
    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    assert json.loads(review.stdout)["touched"] == []


def test_replay_recovers_the_writing_channel_without_a_named_session(
        mini_repo, tmp_path, monkeypatch):
    """Exact re-dispatch repairs ownership in the writing channel's ledger.

    The replay repair runs outside any gateway request context, so ambient
    resolution alone would look in the default channel's ledger and fail
    closed with "the session ledger is gone" — the receipt's recorded
    channel recovers the ledger the original write used.
    """
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    key = "noenv-replay-001"
    envelope = _ui_envelope(mini_repo, key, "replayed seed")
    first = run_v2_capability(mini_repo, envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    captured = json.loads(first.stdout)["result"]["captured"]

    second = run_v2_capability(mini_repo, envelope)
    assert second.returncode == 0, second.stdout
    assert json.loads(second.stdout)["replayed"] is True

    recorded = command_support._load_session_paths(mini_repo, "channel:ui")
    assert captured in recorded
    assert recorded[captured]["channel"] == "ui"


def test_unknown_channel_is_refused(mini_repo):
    _git_init(mini_repo)
    refused = run_los(mini_repo, "session-end", "--channel", "pigeon")
    assert refused.returncode == 2
    assert "unknown session channel" in refused.stderr


def test_session_identity_resolution_precedence(monkeypatch):
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    assert command_support._current_session_id() == "channel:operator"
    assert command_support._current_session_id(channel="ui") == "channel:ui"
    monkeypatch.setenv("LOS_SESSION_ID", "env-session")
    assert command_support._current_session_id() == "env-session"
    assert command_support._current_session_id(channel="ui") == "env-session"
    assert command_support._current_session_id(explicit="flag") == "flag"
    monkeypatch.setenv("LOS_SESSION_ID", "   ")
    assert command_support._current_session_id() == "channel:operator"


def test_sealed_session_identity_resolution_precedence(monkeypatch):
    """Explicit flag > sealed envelope > environment > channel (#110)."""
    from learning_os.contracts.gateway import (
        GatewayRequestContext,
        gateway_request_context,
    )

    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    context = GatewayRequestContext(
        request_id="request-precedence", idempotency_key="precedence",
        capability="capture.create", channel="operator",
        intent_sha256="sha256:" + "0" * 64, approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "0" * 64,
        session_id="sealed-session",
    )
    with gateway_request_context(context):
        assert command_support._current_session_id() == "sealed-session"
        assert command_support._resolve_session_identity()[1] == "envelope"
        monkeypatch.setenv("LOS_SESSION_ID", "env-session")
        assert command_support._current_session_id() == "sealed-session"
        assert command_support._current_session_id(explicit="flag") == "flag"
        assert command_support._resolve_session_identity(explicit="flag")[1] \
            == "explicit"
    assert command_support._current_session_id() == "env-session"
    assert command_support._resolve_session_identity()[1] == "environment"


def _sealed_capture(root: Path, *, key: str, text: str, session_id: str) -> str:
    """A capture whose session travels in the sealed envelope, not the env."""
    envelope = approved_v2_envelope(
        root, capability="capture.create", payload={"text": text},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    envelope["session_id"] = session_id
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    result = run_v2_capability(root, envelope)
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)["result"]["captured"]


def test_sealed_session_ids_keep_fresh_shell_agents_disjoint(mini_repo, monkeypatch):
    """Two agents sealing their own session_id share no ledger rows (#110).

    No exported variable anywhere: each write is a fresh subprocess whose
    session comes only from its sealed envelope.
    """
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    agent_a = _sealed_capture(mini_repo, key="sealed-a-001", text="A's note",
                              session_id="agent-session-a")
    agent_b = _sealed_capture(mini_repo, key="sealed-b-001", text="B's note",
                              session_id="agent-session-b")

    review_a = _session_end(mini_repo, "--session-id", "agent-session-a")
    assert review_a.returncode == 0, review_a.stderr
    payload_a = json.loads(review_a.stdout)
    assert payload_a["session_id"] == "agent-session-a"
    assert agent_a in payload_a["touched"]
    assert agent_b not in payload_a["touched"]

    review_b = _session_end(mini_repo, "--session-id", "agent-session-b")
    assert review_b.returncode == 0, review_b.stderr
    payload_b = json.loads(review_b.stdout)
    assert payload_b["session_id"] == "agent-session-b"
    assert agent_b in payload_b["touched"]
    assert agent_a not in payload_b["touched"]


def test_unmarked_close_sees_sealed_sessions_as_foreign(mini_repo, monkeypatch):
    """An unmarked `session-end` stays valid and stages none of them."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    agent_a = _sealed_capture(mini_repo, key="sealed-foreign-001", text="A's note",
                              session_id="agent-session-a")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["session_id"] == "channel:operator"
    assert payload["touched"] == []
    assert agent_a in payload["other_sessions"]["agent-session-a"]["paths"]


def test_sealed_session_wins_over_the_environment(mini_repo, monkeypatch):
    """The envelope names the ledger even when the ambient env disagrees."""
    _git_init(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "stale-env-session")
    captured = _sealed_capture(mini_repo, key="sealed-env-001", text="sealed note",
                               session_id="sealed-session")

    review = _session_end(mini_repo, "--session-id", "sealed-session")
    assert review.returncode == 0, review.stderr
    assert captured in json.loads(review.stdout)["touched"]

    ambient = _session_end(mini_repo)
    assert ambient.returncode == 0, ambient.stderr
    assert json.loads(ambient.stdout)["touched"] == []


def test_tampered_session_id_is_unconfirmed(mini_repo, monkeypatch):
    """A session_id the approval does not cover refuses as UNCONFIRMED."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    envelope = approved_v2_envelope(
        root=mini_repo, capability="capture.create", payload={"text": "tampered"},
        artifact_ids=[request_artifact_id("capture.create", "tampered-001")],
        idempotency_key="tampered-001",
    )
    envelope["session_id"] = "added-after-sealing"
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 2, result.stdout
    assert json.loads(result.stdout)["error"]["code"] == "UNCONFIRMED"


@pytest.mark.parametrize("mutation", ["change", "remove"])
def test_sealed_session_cannot_be_changed_or_removed_after_approval(mini_repo, mutation):
    key = f"session-tamper-{mutation}"
    envelope = approved_v2_envelope(
        root=mini_repo, capability="capture.create", payload={"text": "never applied"},
        artifact_ids=[request_artifact_id("capture.create", key)], idempotency_key=key,
    )
    envelope["session_id"] = "original-session"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    if mutation == "change":
        envelope["session_id"] = "foreign-session"
    else:
        del envelope["session_id"]
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 2, result.stdout
    assert json.loads(result.stdout)["error"]["code"] == "UNCONFIRMED"
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_blank_sealed_session_is_refused_instead_of_claiming_ambient_identity(mini_repo):
    key = "session-blank-manual"
    envelope = approved_v2_envelope(
        root=mini_repo, capability="capture.create", payload={"text": "never applied"},
        artifact_ids=[request_artifact_id("capture.create", key)], idempotency_key=key,
    )
    envelope["session_id"] = " \t "
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 2, result.stdout
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_REQUEST"
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_replay_recovers_the_sealed_session_without_a_named_session(
        mini_repo, monkeypatch):
    """Exact re-dispatch repairs the sealed session's ledger, env-free."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    key = "sealed-replay-001"
    envelope = approved_v2_envelope(
        root=mini_repo, capability="capture.create",
        payload={"text": "replayed sealed seed"},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    envelope["session_id"] = "sealed-replay-session"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    first = run_v2_capability(mini_repo, envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    captured = json.loads(first.stdout)["result"]["captured"]

    monkeypatch.setenv("LOS_SESSION_ID", "unrelated-ambient-replay-session")
    second = run_v2_capability(mini_repo, envelope)
    assert second.returncode == 0, second.stdout
    assert json.loads(second.stdout)["replayed"] is True

    recorded = command_support._load_session_paths(mini_repo, "sealed-replay-session")
    assert captured in recorded
    assert recorded[captured]["channel"] == "operator"
    assert command_support._load_session_paths(mini_repo, "unrelated-ambient-replay-session") == {}


def test_session_ledgers_survive_differing_tmpdirs(mini_repo, tmp_path, monkeypatch):
    """Writes and closes under different TMPDIRs share one anchored ledger."""
    tmp_a = tmp_path / "tmp-a"
    tmp_b = tmp_path / "tmp-b"
    tmp_a.mkdir()
    tmp_b.mkdir()
    _git_init(mini_repo)
    monkeypatch.setenv("LOS_SESSION_ID", "tmpdir-session")
    monkeypatch.setenv("TMPDIR", str(tmp_a))
    captured = _capture(mini_repo, key="tmpdir-001", text="anchored note")

    monkeypatch.setenv("TMPDIR", str(tmp_b))
    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert captured in payload["touched"]

    # And a process started without TMPDIR at all sees the same ledger.
    captured_two = _capture(mini_repo, key="tmpdir-002", text="second note")
    monkeypatch.delenv("TMPDIR", raising=False)
    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    assert captured_two in json.loads(review.stdout)["touched"]
    assert list(tmp_a.iterdir()) == []
    assert list(tmp_b.iterdir()) == []


def test_previous_location_ledger_surfaces_as_foreign(mini_repo, monkeypatch):
    """A ledger left in the old temp location is found, never staged (#110)."""
    import datetime as _dt
    import hashlib as _hashlib
    import tempfile as _tempfile

    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    token = _hashlib.sha256(str(mini_repo.resolve()).encode("utf-8")).hexdigest()[:16]
    slug = _hashlib.sha256(b"channel:operator").hexdigest()[:16]
    previous = Path(_tempfile.gettempdir()) / f"learningos-{token}-{slug}-touched.json"
    recorded_at = _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat()
    previous.write_text(json.dumps({
        "schema_version": command_support.SESSION_LEDGER_SCHEMA_VERSION,
        "session_id": "channel:operator",
        "paths": {"work/inbox/previous.md": {
            "state": "absent", "channel": "operator", "recorded_at": recorded_at,
        }},
    }), encoding="utf-8")
    try:
        review = _session_end(mini_repo)
        assert review.returncode == 0, review.stderr
        payload = json.loads(review.stdout)
        assert payload["touched"] == []
        others = payload["other_sessions"]
        assert "work/inbox/previous.md" in (
            others["channel:operator (previous location)"]["paths"])
    finally:
        previous.unlink(missing_ok=True)


def test_session_end_reports_the_client_marker(mini_repo, monkeypatch):
    """LOS_CLIENT travels into the payload; unmarked stays valid and null."""
    _git_init(mini_repo)
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    monkeypatch.delenv("LOS_CLIENT", raising=False)
    plain = _session_end(mini_repo)
    assert plain.returncode == 0, plain.stderr
    assert json.loads(plain.stdout)["client"] is None

    monkeypatch.setenv("LOS_CLIENT", "obsidian-ui/test-build")
    marked = _session_end(mini_repo)
    assert marked.returncode == 0, marked.stderr
    assert json.loads(marked.stdout)["client"] == "obsidian-ui/test-build"
