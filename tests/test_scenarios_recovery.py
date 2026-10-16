"""Recovery and retry scenarios against current code (PLAN 1.5, SPEC A16).

Every case runs ``los`` children against a fresh ``rich_world`` fixture,
launched through ``tests/scenario_harness.py`` with per-launch audit tokens
(SPEC amendment (m)). Deliberately crashed children carry
``LOS_ARCH_EXPECT_CRASH=1``. Crash outcomes characterize today's behavior;
they are not fixes.

Kickoff case 4 (a read escalating and recovering while a journal is
armed) runs against ``inspect``, the lock-taking read that does escalate
(ND2 resolution; see REPORT.md). ``status`` takes no operator lock and
recovers nothing: its read-through on an armed journal is characterized
as today's behavior, not desired behavior. Recovery below is driven by
``inspect``, and by lock acquisition on every later write.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

import arch_effects
import crash_points
import pytest
import scenario_harness
from conftest import build_mini_repo
from gateway_helpers import approved_v2_envelope, request_artifact_id
from scenario_fixtures import rich_world

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
LOS = REPO_ROOT / "tools" / "los.py"
TOOLS_DIR = REPO_ROOT / "tools"

FIXTURE_NOW = "2026-10-01T09:00:00+02:00"
FIXTURE_MTIME = "2026-09-28T09:00:00+02:00"

STAGE_REQUEST = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"}
STAGE_ARTIFACTS = ["unit-demo-l01", "study-map-demo-l01"]


@pytest.fixture(autouse=True)
def _berlin_clock(monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()
    yield
    time.tzset()


class _RecoveryContext:
    """The attributes scenario_harness.launch/check_witnesses need."""

    def __init__(self, *, root: Path, workdir: Path, observations_path: Path):
        self.root = root
        self.workdir = workdir
        self.observations_path = observations_path
        self.log_path = workdir / "audit.jsonl"
        self.tokens: list[str] = []


@pytest.fixture()
def session_id(monkeypatch) -> str:
    """A fresh session per test, so no session ledger row pre-exists."""
    identity = f"recovery-{uuid.uuid4().hex}"
    monkeypatch.setenv("LOS_SESSION_ID", identity)
    return identity


def _write_observations(workdir: Path, seed: str, root: Path) -> Path:
    inbox = root / "work" / "inbox"
    mtimes = {path.relative_to(root).as_posix(): FIXTURE_MTIME
              for path in sorted(inbox.iterdir()) if path.is_file()} \
        if inbox.is_dir() else {}
    data = {
        "now": FIXTURE_NOW,
        "git": {"head": None, "head_time": None, "dates": {}, "timestamps": {}},
        "ids": {"seed": seed, "counter_file": str(workdir / "ids.counter")},
        "mtimes": mtimes,
    }
    path = workdir / "observations.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


@pytest.fixture()
def ctx(tmp_path: Path, session_id: str) -> _RecoveryContext:
    root = build_mini_repo(tmp_path / "los")
    rich_world(root)
    workdir = tmp_path / "work"
    workdir.mkdir()
    return _RecoveryContext(
        root=root, workdir=workdir,
        observations_path=_write_observations(workdir, session_id, root))


@pytest.fixture()
def wrapper(ctx: _RecoveryContext) -> Path:
    return crash_points.write_wrapper(ctx.workdir / "crash_wrapper.py")


def _receipt_names(root: Path) -> list[str]:
    directory = root / "operations" / "transactions"
    if not directory.is_dir():
        return []
    return sorted(p.name for p in directory.glob("transaction-*.yaml"))


def _armed_journals(root: Path) -> list[str]:
    inflight = root / "operations" / "transactions" / ".inflight"
    if not inflight.is_dir():
        return []
    return sorted(p.name for p in inflight.iterdir()
                  if not p.name.startswith(".preparing-"))


def _envelope(ctx: _RecoveryContext, *, capability: str, request: dict,
              artifact_ids: list[str], key: str,
              session_claim: str | None = None) -> tuple[dict, Path]:
    body = approved_v2_envelope(
        ctx.root, capability=capability, payload=dict(request),
        artifact_ids=list(artifact_ids), idempotency_key=key)
    if session_claim is not None:
        body["session_id"] = session_claim
        from learning_os.contracts.gateway import intent_sha256
        body["approval"]["subject_sha256"] = intent_sha256(body)
    path = ctx.workdir / f"envelope-{key}.json"
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return body, path


def _capability_argv(ctx: _RecoveryContext, envelope_path: Path,
                     capability: str, *, replay_only: bool = False) -> list[str]:
    argv = [sys.executable, str(LOS), "--root", str(ctx.root),
           "capability", capability, "--payload-file", str(envelope_path)]
    if replay_only:
        argv.append("--replay-only")
    return argv


def _crash_argv(wrapper: Path, los_argv: list[str]) -> list[str]:
    return [sys.executable, str(wrapper), "--", *los_argv[2:]]


def _response(proc) -> dict:
    assert proc.stdout.strip(), proc.stderr[-2000:]
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# 1. lost-response exact replay
# ---------------------------------------------------------------------------

def test_lost_response_exact_replay_returns_original_receipt(ctx: _RecoveryContext):
    key = "recovery-lost-response-001"
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    _, envelope_path = _envelope(
        ctx, capability="capture.create",
        request={"text": "A fleeting thought about expectation."},
        artifact_ids=[request_artifact_id("capture.create", key)], key=key)
    first = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create"))
    assert first.returncode == 0, first.stderr[-2000:] or first.stdout[-2000:]
    first_response = _response(first)
    assert first_response["ok"] is True
    assert first_response["replayed"] is False

    # The response was lost; the client resubmits the saved envelope verbatim.
    second = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create"))
    assert second.returncode == 0, second.stderr[-2000:] or second.stdout[-2000:]
    second_response = _response(second)
    assert second_response["replayed"] is True
    assert second_response["transaction_id"] == first_response["transaction_id"]
    assert second_response["receipt_path"] == first_response["receipt_path"]

    assert _receipt_names(ctx.root) == before_receipts + [
        Path(first_response["receipt_path"]).name]
    receipts = arch_effects.new_receipts(before_receipts, ctx.root)
    assert len(receipts) == 1
    assert arch_effects.reconcile(
        before_tree, arch_effects.capture_tree(ctx.root), receipts) == []
    scenario_harness.check_witnesses(ctx)


# ---------------------------------------------------------------------------
# 2. concurrent exact retries
# ---------------------------------------------------------------------------

def test_concurrent_exact_retries_share_one_receipt(ctx: _RecoveryContext,
                                                   wrapper: Path):
    key = "recovery-concurrent-001"
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    _, envelope_path = _envelope(
        ctx, capability="capture.create",
        request={"text": "A fleeting thought about expectation."},
        artifact_ids=[request_artifact_id("capture.create", key)], key=key)
    plain = _capability_argv(ctx, envelope_path, "capture.create")
    # Both submissions are launched at once. The second child waits for the
    # first's receipt like a slow client, so its replay lookup deterministically
    # runs after the commit instead of racing it (see the module docstring).
    gated_marker = ctx.workdir / "gated.marker"
    gated = _crash_argv(wrapper, plain)
    gated_env = crash_points.crash_env(
        point=crash_points.NO_CRASH, marker=gated_marker, tools_dir=TOOLS_DIR,
        gate_dir=ctx.root / "operations" / "transactions",
        gate_before=before_receipts)
    first, second = scenario_harness.launch_many(
        ctx, [plain, gated], [None, gated_env])
    assert first.returncode == 0, first.stderr[-2000:] or first.stdout[-2000:]
    assert second.returncode == 0, second.stderr[-2000:] or second.stdout[-2000:]
    first_response = _response(first)
    second_response = _response(second)
    assert first_response["replayed"] is False
    assert second_response["replayed"] is True
    assert second_response["transaction_id"] == first_response["transaction_id"]
    assert second_response["receipt_path"] == first_response["receipt_path"]
    assert not gated_marker.exists()

    assert _receipt_names(ctx.root) == before_receipts + [
        Path(first_response["receipt_path"]).name]
    receipts = arch_effects.new_receipts(before_receipts, ctx.root)
    assert len(receipts) == 1
    assert arch_effects.reconcile(
        before_tree, arch_effects.capture_tree(ctx.root), receipts) == []
    scenario_harness.check_witnesses(ctx)


# ---------------------------------------------------------------------------
# 3. replay-only with a missing receipt / a forged confirmation
# ---------------------------------------------------------------------------

def _assert_unconfirmed_refusal(ctx: _RecoveryContext, proc,
                                before_tree: dict, before_receipts: list[str]):
    assert proc.returncode == 2, proc.stdout[-2000:] or proc.stderr[-2000:]
    response = _response(proc)
    assert response["ok"] is False
    assert response["error"]["code"] == "UNCONFIRMED"
    assert _receipt_names(ctx.root) == before_receipts
    assert arch_effects.capture_tree(ctx.root) == before_tree
    assert arch_effects.reconcile(
        before_tree, arch_effects.capture_tree(ctx.root), []) == []


def test_replay_only_with_missing_receipt_is_unconfirmed(ctx: _RecoveryContext):
    key = "recovery-missing-receipt-001"
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    _, envelope_path = _envelope(
        ctx, capability="capture.create",
        request={"text": "A fleeting thought about expectation."},
        artifact_ids=[request_artifact_id("capture.create", key)], key=key)
    proc = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create",
                              replay_only=True))
    _assert_unconfirmed_refusal(ctx, proc, before_tree, before_receipts)
    scenario_harness.check_witnesses(ctx)


def test_replay_only_with_forged_confirmation_is_unconfirmed(ctx: _RecoveryContext):
    key = "recovery-forged-confirmation-001"
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    # A persisted UI confirmation is untrusted settings JSON until Core proves
    # the exact approved intent committed: the sealed session claim alone must
    # never conjure a confirmation.
    _, envelope_path = _envelope(
        ctx, capability="capture.create",
        request={"text": "A fleeting thought about expectation."},
        artifact_ids=[request_artifact_id("capture.create", key)], key=key,
        session_claim="session-forged-001")
    proc = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create",
                              replay_only=True))
    _assert_unconfirmed_refusal(ctx, proc, before_tree, before_receipts)
    scenario_harness.check_witnesses(ctx)


# ---------------------------------------------------------------------------
# 4. reads while a crash journal is armed (ND2 resolution)
# ---------------------------------------------------------------------------

def _crash_leaving_armed_journal(ctx: _RecoveryContext, wrapper: Path,
                                 key: str):
    """Crash a write after its first write; one journal armed, tree torn.

    Returns ``(before_tree, torn_tree, journals, before_receipts)``. The
    torn paths are computed from the before/after trees, not pinned: today
    the crash leaves the updated study map on top of the pre-state.
    """
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    _, envelope_path = _envelope(
        ctx, capability="stage.progress.update", request=dict(STAGE_REQUEST),
        artifact_ids=list(STAGE_ARTIFACTS), key=key)
    marker = ctx.workdir / f"marker-{key}"
    crashed = scenario_harness.launch(
        ctx, _crash_argv(wrapper, _capability_argv(
            ctx, envelope_path, "stage.progress.update")),
        extra_env=crash_points.crash_env(
            point="after-first-write", marker=marker, tools_dir=TOOLS_DIR))
    assert crashed.returncode == crash_points.CRASH_EXIT, \
        crashed.stdout[-2000:] or crashed.stderr[-2000:]
    assert marker.is_file(), "crash point was never reached: after-first-write"
    assert marker.read_text(encoding="utf-8") == "after-first-write"
    journals = _armed_journals(ctx.root)
    assert len(journals) == 1, journals
    torn_tree = arch_effects.capture_tree(ctx.root)
    torn_paths = sorted(path for path in set(before_tree) | set(torn_tree)
                        if before_tree.get(path) != torn_tree.get(path))
    assert torn_paths, "expected the crash to leave a torn tree"
    assert torn_tree != before_tree
    return before_tree, torn_tree, journals, before_receipts


def test_inspect_while_journal_armed_escalates_and_recovers(
        ctx: _RecoveryContext, wrapper: Path):
    """Case 4 against inspect: the lock-taking read escalates and recovers."""
    key = "recovery-inspect-armed-journal"
    before_tree, _, _, before_receipts = _crash_leaving_armed_journal(
        ctx, wrapper, key)
    recovered = _inspect(ctx)
    assert recovered.returncode == 0, \
        recovered.stderr[-2000:] or recovered.stdout[-2000:]
    payload = json.loads(recovered.stdout)
    assert payload["id"] == "concept-expected-value"
    assert _armed_journals(ctx.root) == []
    after_tree = arch_effects.capture_tree(ctx.root)
    assert after_tree == before_tree
    assert arch_effects.reconcile(
        before_tree, after_tree,
        arch_effects.new_receipts(before_receipts, ctx.root),
        restored_from=before_tree) == []
    scenario_harness.check_witnesses(ctx)


def test_status_while_journal_armed_reads_through_without_recovery(
        ctx: _RecoveryContext, wrapper: Path):
    """status on an armed journal reads the torn state through: no recovery.

    TODAY'S CHARACTERIZED BEHAVIOR — NOT DESIRED BEHAVIOR. ``cmd_status``
    (``tools/learning_os/commands/query.py:64-69``) reads directly and
    never takes ``_operator_lock``, and ``los`` ``main``
    (``tools/los.py:1387``) has no global lock or recovery wrapper, so the
    armed journal and the torn file survive this read. A future pipeline
    that gives ``status`` the lock (PLAN D20) must update this test
    deliberately.
    """
    key = "recovery-status-armed-journal"
    before_tree, torn_tree, journals, _ = _crash_leaving_armed_journal(
        ctx, wrapper, key)
    proc = scenario_harness.launch(
        ctx, [sys.executable, str(LOS), "--root", str(ctx.root),
              "status", "--json"])
    assert proc.returncode == 0, proc.stderr[-2000:] or proc.stdout[-2000:]
    payload = json.loads(proc.stdout)
    assert "counts" in payload
    assert _armed_journals(ctx.root) == journals
    still = arch_effects.capture_tree(ctx.root)
    assert still == torn_tree
    assert still != before_tree
    scenario_harness.check_witnesses(ctx)


# ---------------------------------------------------------------------------
# 5. a crash at every named point
# ---------------------------------------------------------------------------

def _inspect(ctx: _RecoveryContext):
    return scenario_harness.launch(
        ctx, [sys.executable, str(LOS), "--root", str(ctx.root),
              "inspect", "concept-expected-value"])


@pytest.mark.parametrize("point", crash_points.POINTS)
def test_crash_at_named_point(ctx: _RecoveryContext, wrapper: Path, point: str):
    key = f"recovery-crash-{point}"
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    _, envelope_path = _envelope(
        ctx, capability="stage.progress.update", request=dict(STAGE_REQUEST),
        artifact_ids=list(STAGE_ARTIFACTS), key=key)
    marker = ctx.workdir / f"marker-{point}"
    crashed = scenario_harness.launch(
        ctx, _crash_argv(wrapper, _capability_argv(
            ctx, envelope_path, "stage.progress.update")),
        extra_env=crash_points.crash_env(
            point=point, marker=marker, tools_dir=TOOLS_DIR))
    assert crashed.returncode == crash_points.CRASH_EXIT, \
        crashed.stdout[-2000:] or crashed.stderr[-2000:]
    assert marker.is_file(), f"crash point was never reached: {point}"
    assert marker.read_text(encoding="utf-8") == point
    journals = _armed_journals(ctx.root)
    assert len(journals) == 1, journals

    if point != "after-receipt-before-bookkeeping":
        recovered = _inspect(ctx)
        assert recovered.returncode == 0, \
            recovered.stderr[-2000:] or recovered.stdout[-2000:]
        assert _armed_journals(ctx.root) == []
        after_tree = arch_effects.capture_tree(ctx.root)
        assert after_tree == before_tree
        assert arch_effects.reconcile(
            before_tree, after_tree,
            arch_effects.new_receipts(before_receipts, ctx.root),
            restored_from=before_tree) == []

        # The same envelope still commits afterwards: the crash left no poison.
        retried = scenario_harness.launch(
            ctx, _capability_argv(ctx, envelope_path, "stage.progress.update"))
        assert retried.returncode == 0, \
            retried.stderr[-2000:] or retried.stdout[-2000:]
        retried_response = _response(retried)
        assert retried_response["ok"] is True
        assert retried_response["replayed"] is False
        assert _receipt_names(ctx.root) == before_receipts + [
            Path(retried_response["receipt_path"]).name]
        assert arch_effects.reconcile(
            before_tree, arch_effects.capture_tree(ctx.root),
            arch_effects.new_receipts(before_receipts, ctx.root)) == []
        scenario_harness.check_witnesses(ctx)
        return

    # After the receipt: the commit is irrevocable. Recovery keeps the tree
    # and only cleans the stale journal; a replay then fails closed, because
    # this first write in the session left no ledger row to repair from.
    from learning_os.store.session_ledger import session_ledger as _session_ledger

    assert not _session_ledger(ctx.root).is_file()
    committed_tree = arch_effects.capture_tree(ctx.root)
    assert committed_tree != before_tree
    committed_names = _receipt_names(ctx.root)
    assert len(committed_names) == len(before_receipts) + 1
    committed = arch_effects.new_receipts(before_receipts, ctx.root)
    assert len(committed) == 1
    assert committed[0]["status"] == "committed"
    assert arch_effects.reconcile(before_tree, committed_tree, committed) == []

    recovered = _inspect(ctx)
    assert recovered.returncode == 0, \
        recovered.stderr[-2000:] or recovered.stdout[-2000:]
    assert _armed_journals(ctx.root) == []
    assert arch_effects.capture_tree(ctx.root) == committed_tree

    replayed = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "stage.progress.update"))
    assert replayed.returncode == 2, replayed.stdout[-2000:]
    replayed_response = _response(replayed)
    assert replayed_response["ok"] is False
    assert replayed_response["error"]["code"] == "INTERNAL_FAILURE"
    assert replayed_response["error"]["retryable"] is False
    assert "reconcile this transaction by hand" in \
        replayed_response["error"]["message"]
    assert _receipt_names(ctx.root) == committed_names
    assert arch_effects.capture_tree(ctx.root) == committed_tree
    print(f"characterized after-receipt replay response: {replayed.stdout}")
    scenario_harness.check_witnesses(ctx)


# ---------------------------------------------------------------------------
# 6. the two replay misses
# ---------------------------------------------------------------------------

def test_replay_only_miss_for_never_committed_request(ctx: _RecoveryContext):
    key = "recovery-never-committed-001"
    before_tree = arch_effects.capture_tree(ctx.root)
    before_receipts = _receipt_names(ctx.root)
    _, envelope_path = _envelope(
        ctx, capability="capture.create",
        request={"text": "A fleeting thought about expectation."},
        artifact_ids=[request_artifact_id("capture.create", key)], key=key)
    proc = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create",
                              replay_only=True))
    assert proc.returncode == 2
    response = _response(proc)
    assert response["error"]["code"] == "UNCONFIRMED"
    assert _receipt_names(ctx.root) == before_receipts
    assert arch_effects.capture_tree(ctx.root) == before_tree
    scenario_harness.check_witnesses(ctx)


def test_replay_with_removed_receipt_refuses(ctx: _RecoveryContext):
    key = "recovery-removed-receipt-001"
    _, envelope_path = _envelope(
        ctx, capability="capture.create",
        request={"text": "A fleeting thought about expectation."},
        artifact_ids=[request_artifact_id("capture.create", key)], key=key)
    committed = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create"))
    assert committed.returncode == 0, \
        committed.stderr[-2000:] or committed.stdout[-2000:]
    committed_response = _response(committed)
    posted_tree = arch_effects.capture_tree(ctx.root)
    receipt_path = ctx.root / committed_response["receipt_path"]
    assert receipt_path.is_file()
    receipt_path.unlink()
    after_delete = _receipt_names(ctx.root)

    replayed = scenario_harness.launch(
        ctx, _capability_argv(ctx, envelope_path, "capture.create"))
    assert replayed.returncode == 2, replayed.stdout[-2000:]
    replayed_response = _response(replayed)
    assert replayed_response["ok"] is False
    assert replayed_response["error"]["code"] == "INTERNAL_FAILURE"
    assert replayed_response["error"]["retryable"] is False
    assert "missing or non-canonical receipt" in \
        replayed_response["error"]["message"]
    assert receipt_path.is_file() is False
    assert _receipt_names(ctx.root) == after_delete
    assert arch_effects.capture_tree(ctx.root) == posted_tree
    scenario_harness.check_witnesses(ctx)
