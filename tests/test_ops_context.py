"""OpContext require_snapshot, member freeze and caching (PLAN D4, A17)."""

from __future__ import annotations

import contextlib
import dataclasses

from learning_os.app.context import OpContext
from learning_os.app.outcomes import _take_gateway_refusal, exit_for
from learning_os.app.registry import REGISTRY, register
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
    verified_gateway_snapshot,
)
from learning_os.domain.codes import INVALID_REQUEST, STALE_SNAPSHOT
from learning_os.domain.failures import StaleSnapshot, WriteRefused
from learning_os.store.fingerprint import canonical_fingerprint

STALE = "sha256:" + "0" * 64


def _ctx(root, gateway=None):
    return OpContext(
        root=root, operation="test.probe", channel="operator",
        invocation="command", gateway=gateway,
    )


def _gateway(expected):
    return GatewayRequestContext(
        request_id="request-probe", idempotency_key="probe-key",
        capability="test.probe", channel="operator",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "1" * 64,
        expected_snapshot=expected,
    )


def _run_expected_ok(root, expected):
    """Boolean form of require_snapshot (the dissolved _expected_ok twin)."""
    return _run_require_snapshot(_ctx(root), expected) is None, None


def _run_require_snapshot(ctx, expected):
    """The raised refusal, or None; require_snapshot never prints/records."""
    _take_gateway_refusal()
    try:
        ctx.require_snapshot(expected)
    except (StaleSnapshot, WriteRefused) as exc:
        assert _take_gateway_refusal() is None
        return exc
    assert _take_gateway_refusal() is None
    return None


def _assert_refusal(root, capsys, *, expected, gateway=None, verified=False,
                    exc_type, code):
    """require_snapshot refuses: text, code and exit 3, never printed."""
    ctx = _ctx(root, gateway=gateway)
    managers = []
    if gateway is not None:
        managers.append(gateway_request_context(gateway))
    if verified:
        managers.append(verified_gateway_snapshot(root, expected))
    with contextlib.ExitStack() as stack:
        for manager in managers:
            stack.enter_context(manager)
        ok, recorded = _run_expected_ok(root, expected)
        out, err = capsys.readouterr()
        exc = _run_require_snapshot(ctx, expected)
        out2, err2 = capsys.readouterr()
    assert ok is False
    assert exc is not None and type(exc) is exc_type
    assert (out, err, out2, err2) == ("", "", "", "")
    lines = exc.gateway_message.splitlines()
    assert lines and lines[0].startswith("los: ")
    assert str(exc) == lines[0][len("los: "):] + (
        "" if len(lines) == 1 else "\n" + "\n".join(lines[1:]))
    assert exit_for(exc, "cli") == 3
    assert exit_for(exc, "gateway.dispatch") == 3
    assert (exc.gateway_code, exc.gateway_retryable) == code
    return recorded


def test_members_are_exactly_the_spec_list():
    assert [f.name for f in dataclasses.fields(OpContext)] == [
        "root", "operation", "channel", "invocation", "gateway",
    ]
    public = {name for name, member in vars(OpContext).items()
              if not name.startswith("_") and callable(member)}
    assert public == {"repo", "snapshot_id", "require_snapshot"}


def test_repo_and_snapshot_id_load_once_per_context(mini_repo, monkeypatch):
    calls = {"load": 0, "walk": 0}
    import learning_os.app.context as context_module

    def counted_load(root):
        calls["load"] += 1
        return {"repo": "stub"}

    def counted_walk(root):
        calls["walk"] += 1
        return "ab" * 32

    monkeypatch.setattr(context_module, "load_repo", counted_load)
    monkeypatch.setattr(context_module, "canonical_fingerprint", counted_walk)
    first, second = _ctx(mini_repo), _ctx(mini_repo)
    assert first.repo() == {"repo": "stub"}
    assert first.repo() == {"repo": "stub"}
    assert first.snapshot_id() == "sha256:" + "ab" * 32
    assert first.snapshot_id() == "sha256:" + "ab" * 32
    assert calls == {"load": 1, "walk": 1}
    assert second.repo() == {"repo": "stub"}
    assert second.snapshot_id() == "sha256:" + "ab" * 32
    assert calls == {"load": 2, "walk": 2}


def test_none_is_unconditionally_ok(mini_repo, capsys):
    ok, recorded = _run_expected_ok(mini_repo, None)
    out, err = capsys.readouterr()
    assert (ok, recorded, out, err) == (True, None, "", "")
    assert _run_require_snapshot(_ctx(mini_repo), None) is None
    assert capsys.readouterr() == ("", "")


def test_empty_token_is_write_refused_with_exit_3(mini_repo, capsys):
    recorded = _assert_refusal(
        mini_repo, capsys, expected="",
        exc_type=WriteRefused, code=(INVALID_REQUEST, False))
    assert recorded is None


def test_whitespace_token_is_write_refused_with_exit_3(mini_repo, capsys):
    recorded = _assert_refusal(
        mini_repo, capsys, expected="   ",
        exc_type=WriteRefused, code=(INVALID_REQUEST, False))
    assert recorded is None


def test_empty_token_with_unverified_context_still_refuses(mini_repo, capsys):
    recorded = _assert_refusal(
        mini_repo, capsys, expected="", gateway=_gateway(""),
        exc_type=WriteRefused, code=(INVALID_REQUEST, False))
    assert recorded is None


def test_empty_token_carries_an_explicit_exit_3(mini_repo):
    exc = _run_require_snapshot(_ctx(mini_repo), "")
    assert isinstance(exc, WriteRefused) and not isinstance(exc, StaleSnapshot)
    assert exc.exit_code == 3


def test_verified_gateway_shortcut_never_walks(mini_repo, capsys, monkeypatch):
    import learning_os.app.context as context_module

    def no_walk(root):
        raise AssertionError("walked on the verified shortcut")

    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    gateway = _gateway(live)
    monkeypatch.setattr(context_module, "canonical_fingerprint", no_walk)
    with gateway_request_context(gateway), verified_gateway_snapshot(mini_repo, live):
        ok, recorded = _run_expected_ok(mini_repo, live)
        out, err = capsys.readouterr()
        exc = _run_require_snapshot(_ctx(mini_repo, gateway=gateway), live)
        out2, err2 = capsys.readouterr()
    assert (ok, recorded, out, err, exc, out2, err2) == (
        True, None, "", "", None, "", "")


def test_match_is_ok_without_a_gateway(mini_repo, capsys):
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    ok, recorded = _run_expected_ok(mini_repo, live)
    out, err = capsys.readouterr()
    assert (ok, recorded, out, err) == (True, None, "", "")
    assert _run_require_snapshot(_ctx(mini_repo), live) is None
    assert capsys.readouterr() == ("", "")


def test_match_with_unverified_context_is_ok(mini_repo, capsys):
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    gateway = _gateway(live)
    with gateway_request_context(gateway):
        ok, recorded = _run_expected_ok(mini_repo, live)
        out, err = capsys.readouterr()
        exc = _run_require_snapshot(_ctx(mini_repo, gateway=gateway), live)
        out2, err2 = capsys.readouterr()
    assert (ok, recorded, out, err, exc, out2, err2) == (
        True, None, "", "", None, "", "")


def test_stale_without_gateway_is_a_stale_snapshot(mini_repo, capsys):
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    assert live != STALE
    recorded = _assert_refusal(
        mini_repo, capsys, expected=STALE,
        exc_type=StaleSnapshot, code=(STALE_SNAPSHOT, True))
    assert recorded is None


def test_stale_with_gateway_is_a_stale_snapshot(mini_repo, capsys):
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    assert live != STALE
    recorded = _assert_refusal(
        mini_repo, capsys, expected=STALE, gateway=_gateway(STALE),
        exc_type=StaleSnapshot, code=(STALE_SNAPSHOT, True))
    assert recorded is None


def test_handler_token_mismatch_is_a_stale_snapshot(mini_repo, capsys):
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    assert live != STALE
    recorded = _assert_refusal(
        mini_repo, capsys, expected=STALE, gateway=_gateway(live),
        exc_type=StaleSnapshot, code=(STALE_SNAPSHOT, True))
    assert recorded is None


def test_stale_branches_resolve_exit_3_by_default(mini_repo):
    live = f"sha256:{canonical_fingerprint(mini_repo)}"
    for expected, gateway in ((STALE, None), (STALE, _gateway(STALE)),
                              (STALE, _gateway(live))):
        if gateway is None:
            exc = _run_require_snapshot(_ctx(mini_repo), expected)
        else:
            with gateway_request_context(gateway):
                exc = _run_require_snapshot(_ctx(mini_repo, gateway=gateway), expected)
        assert type(exc) is StaleSnapshot
        assert exc.exit_code is None
        assert exit_for(exc, "cli") == 3


def test_register_returns_the_function_unchanged():
    def handler(ctx, req):
        return None

    try:
        assert register("test.probe", kind="query")(handler) is handler
        assert REGISTRY["test.probe"].handler is handler
        assert REGISTRY["test.probe"].kind == "query"
    finally:
        REGISTRY.pop("test.probe", None)
    assert "test.probe" not in REGISTRY
