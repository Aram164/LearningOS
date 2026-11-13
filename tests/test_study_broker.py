"""Default-deny study broker and client transport checks (PLAN-D Step 3)."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest
import seal_envelope
from repo_builders import (
    _compact_revision,
    _compact_setup,
    add_curriculum,
    write_minimal_pdf,
    write_yaml,
)

from learning_os.adapters.study_broker import (
    ALLOWED_CAPABILITIES,
    ALLOWED_LOS_COMMANDS,
    ALLOWED_LOS_READ_COMMANDS,
    ALLOWED_PREFLIGHT_COMMANDS,
    ALLOWED_STUDY_COMMANDS,
    BrokerServer,
    StudyBroker,
    dispatch_los_via_socket,
    send_broker_request,
    write_local_output_file,
)
from learning_os.app.gateway import read_content_bound_file
from learning_os.domain.failures import WriteRefused
from learning_os.store.study_fence import (
    STUDY_FENCE_CORE_ENV,
    STUDY_FENCE_SCRATCH_ENV,
    call_dir_fd_op,
    protected_reads,
)

ROOT = Path(__file__).resolve().parents[1]
SESSION = "cccccccc-3333-4333-8333-333333333333"
OTHER_SESSION = "dddddddd-4444-4444-8444-444444444444"
BOOK = "_unsorted/review/book.pdf"


class RecordingRunner:
    """Deterministic subprocess stub capturing exact broker-rewritten invocations."""

    def __init__(self, rc: int = 0, out: str = "{}\n", err: str = "") -> None:
        self.calls: list[tuple[list[str], Path, dict[str, str], str | None]] = []
        self.rc = rc
        self.out = out
        self.err = err

    def __call__(
        self,
        cmd: list[str],
        cwd: Path,
        env: dict[str, str],
        stdin_data: str | None,
    ) -> tuple[int, str, str]:
        self.calls.append((cmd, cwd, env, stdin_data))
        return self.rc, self.out, self.err


def _make_broker_world(tmp_path: Path) -> tuple[Path, Path]:
    learningos = tmp_path / "LearningOS"
    core = learningos / "repository"
    for rel in (
        "tools",
        "knowledge/notes",
        "generated/text-cache/x",
        "generated/material-search",
        "generated/material-outlines",
        "generated/derived-state",
        "operations/ai-actions/requests/req-1",
    ):
        (core / rel).mkdir(parents=True, exist_ok=True)
    (core / "operations/ai-actions/requests/.gitkeep").write_text("", encoding="utf-8")
    (core / "operations/ai-actions/requests/req-1/slice.md").write_text(
        "SECRET_SLICE", encoding="utf-8"
    )
    (core / "generated/text-cache/x/p1.txt").write_text("SECRET_TEXT_CACHE", encoding="utf-8")
    (core / "generated/material-search/idx.sqlite3").write_text("SECRET_IDX", encoding="utf-8")
    (core / "generated/material-outlines/o.json").write_text("SECRET_OUTLINE", encoding="utf-8")
    (core / "generated/derived-state/s.json").write_text("SECRET_STATE", encoding="utf-8")
    (learningos / "materials").mkdir(parents=True, exist_ok=True)
    (learningos / "materials/book.pdf").write_text("SECRET_PDF", encoding="utf-8")
    (learningos / "reading-memory").mkdir(parents=True, exist_ok=True)
    (learningos / "reading-memory/card.json").write_text("SECRET_CARD", encoding="utf-8")
    (core / "knowledge/notes/study.md").write_text("public study note", encoding="utf-8")

    scratch = Path(os.path.realpath(tmp_path / "scratch"))
    scratch.mkdir(parents=True, exist_ok=True)
    return core, scratch


@pytest.mark.parametrize("command", [
    "ai-action-list",
    "ai-action-prepare",
    "ai-action-append-slices",
    "ai-action-import-delivery",
    "ai-action-validate-delivery",
    "ai-action-apply-delivery",
    "ai-action-status",
    "note-analysis-prepare",
    "backup-manifest",
    "backup-verify",
    "legacy-archive-inspect",
    "legacy-archive-status",
    "legacy-archive-lock-publish",
    "masters-planning-dashboard",
    "masters-planning-catalog-update",
    "masters-planning-comparison-publish",
    "validate",
    "generate",
    "intelligence-scan",
    "goal",
    "observe",
    "module-create",
    "unit-map-import",
    "lineage-restamp",
    "stage-note",
    "note-create",
    "future-unlisted-command",
])
def test_unlisted_and_future_los_commands_fail_closed(tmp_path: Path, command: str) -> None:
    core, scratch = _make_broker_world(tmp_path)
    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    res = broker.handle_request({"tool": "los", "argv": [command], "cwd": str(core)})
    assert res.exit_code == 2
    assert "not allowed" in res.stderr
    assert runner.calls == []


def test_preflight_commands_require_check_and_reject_apply(tmp_path: Path) -> None:
    core, scratch = _make_broker_world(tmp_path)
    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    # Without --check, even allowlisted preflight names fail closed.
    for argv in (
        ["source-intake", "--file", str(scratch / "s.yaml")],
        ["source-intake", "--approve"],
        ["unit-plan-revise", "unit-demo-l01", "--file", str(scratch / "p.yaml")],
        [
            "unit-plan-revise",
            "unit-demo-l01",
            "--check",
            "--apply-reviewed-sha256",
            "sha256:" + "0" * 64,
        ],
    ):
        res = broker.handle_request({"tool": "los", "argv": argv, "cwd": str(core)})
        assert res.exit_code == 2, argv
    assert runner.calls == []

    # Valid --check passes when inputs are inside scratch/core and report-out is in scratch.
    draft = scratch / "plan.yaml"
    draft.write_text("plan_contract: {}\n", encoding="utf-8")
    report = scratch / "report.json"
    ok = broker.handle_request({
        "tool": "los",
        "argv": [
            "unit-plan-revise",
            "unit-demo-l01",
            "--check",
            "--file",
            str(draft),
            "--report-out",
            str(report),
        ],
        "cwd": str(core),
    })
    assert ok.exit_code == 0, ok.stderr
    assert len(runner.calls) == 1

    # --report-out outside scratch (even in core) is refused.
    bad_report = broker.handle_request({
        "tool": "los",
        "argv": [
            "unit-plan-revise",
            "unit-demo-l01",
            "--check",
            "--file",
            str(draft),
            "--report-out",
            str(core / "knowledge/out.json"),
        ],
        "cwd": str(core),
    })
    assert bad_report.exit_code == 2


@pytest.mark.parametrize("capability", [
    "ai-action.delivery.apply",
    "ai-action.delivery.import",
    "legacy.archive.lock.publish",
    "masters-planning.catalog.update",
    "masters-planning.comparison.publish",
    "module.create",
    "module.plan.import",
    "unit.map.import",
    "lineage.restamp",
    "goal.decision.record",
    "review.apply",
    "review.prepare",
    "program.semester.update",
    "collection.create",
    "future.unlisted.capability",
])
def test_unlisted_and_future_capabilities_fail_closed(tmp_path: Path, capability: str) -> None:
    core, scratch = _make_broker_world(tmp_path)
    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    env_path = scratch / "env.json"
    env_path.write_text(json.dumps({"capability": capability, "payload": {}}), encoding="utf-8")
    res_los = broker.handle_request({
        "tool": "los",
        "argv": ["capability", capability, "--payload-file", str(env_path)],
        "cwd": str(core),
    })
    assert res_los.exit_code == 2

    res_seal = broker.handle_request({
        "tool": "seal_envelope",
        "argv": ["--capability", capability, "--payload", "{}", "--key", "k1"],
        "cwd": str(core),
    })
    assert res_seal.exit_code == 2

    # Derived capability via --guards-from (no explicit --capability flag) also refuses.
    check_rec = scratch / "check.json"
    check_rec.write_text(json.dumps({
        "schema": 1,
        "ok": True,
        "capability": capability,
        "expected_snapshot": "sha256:" + "a" * 64,
        "expected_revisions": {},
        "payload": {},
        "idempotency_key": "k1",
    }), encoding="utf-8")
    res_derived = broker.handle_request({
        "tool": "seal_envelope",
        "argv": ["--guards-from", str(check_rec), "--submit"],
        "cwd": str(core),
    })
    assert res_derived.exit_code == 2
    assert runner.calls == []


def test_allowlist_counts_and_sets_match_plan_d() -> None:
    assert len(ALLOWED_LOS_READ_COMMANDS) == 23
    assert len(ALLOWED_STUDY_COMMANDS) == 5
    assert set(ALLOWED_PREFLIGHT_COMMANDS.values()) <= ALLOWED_CAPABILITIES
    assert ALLOWED_LOS_COMMANDS == (
        ALLOWED_LOS_READ_COMMANDS
        | ALLOWED_STUDY_COMMANDS
        | frozenset({"capability", *ALLOWED_PREFLIGHT_COMMANDS})
    )
    assert len(ALLOWED_CAPABILITIES) == 20


def test_material_span_rewrite_session_pinning_and_adopt(tmp_path: Path) -> None:
    core, scratch = _make_broker_world(tmp_path)
    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    # material-span --extract rewrites to material-study-span and injects --session.
    res = broker.handle_request({
        "tool": "los",
        "argv": ["material-span", "--material", BOOK, "--pages", "pdf p. 1", "--extract"],
        "cwd": str(core),
    })
    assert res.exit_code == 0, res.stderr
    cmd, _, _, _ = runner.calls[-1]
    assert "-I" in cmd
    assert "material-study-span" in cmd
    assert "--extract" in cmd
    assert cmd[-2:] == ["--session", SESSION]

    # material-span without --extract stays material-span and does not inject --session.
    res_meta = broker.handle_request({
        "tool": "los",
        "argv": ["material-span", "--material", BOOK, "--pages", "pdf p. 1"],
        "cwd": str(core),
    })
    assert res_meta.exit_code == 0, res_meta.stderr
    assert "material-span" in runner.calls[-1][0]
    assert "--session" not in runner.calls[-1][0]

    # Spoofed --session / --s / --session=OTHER / --session-id OTHER fail closed.
    for bad_los in (
        ["material-study-span", "--material", BOOK, "--pages", "p. 1", "--extract", "--session", OTHER_SESSION],
        ["material-search", "Bayes", "--s", OTHER_SESSION],
        ["material-context", "Bayes", f"--session={OTHER_SESSION}"],
    ):
        denied = broker.handle_request({"tool": "los", "argv": bad_los, "cwd": str(core)})
        assert denied.exit_code == 2, bad_los

    denied_seal = broker.handle_request({
        "tool": "seal_envelope",
        "argv": [
            "--capability", "stage.note.write",
            "--payload", json.dumps({"unit_id": "u", "stage_id": "s", "text": "x"}),
            "--key", "k1",
            "--session-id", OTHER_SESSION,
        ],
        "cwd": str(core),
    })
    assert denied_seal.exit_code == 2

    # --adopt OTHER passes through alongside injected --session <broker.session_id>.
    adopt = broker.handle_request({
        "tool": "los",
        "argv": ["material-card-settle", "--adopt", OTHER_SESSION],
        "cwd": str(core),
    })
    assert adopt.exit_code == 0, adopt.stderr
    adopt_cmd = runner.calls[-1][0]
    assert "--adopt" in adopt_cmd and OTHER_SESSION in adopt_cmd
    assert adopt_cmd[-2:] == ["--session", SESSION]


def test_root_pinning_and_host_observations_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    core, scratch = _make_broker_world(tmp_path)
    other_root = tmp_path / "other-repo"
    other_root.mkdir()
    host_obs = tmp_path / "host-observations.yaml"
    host_obs.write_text("fixed_now: '2026-11-12T12:00:00+01:00'\n", encoding="utf-8")

    monkeypatch.setenv("LOS_OBSERVATIONS", str(host_obs))
    monkeypatch.setenv("LOS_GATE_SOCK", "/tmp/should-be-stripped.sock")
    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    # Even if process env changes later, broker pins host observations captured at creation.
    monkeypatch.setenv("LOS_OBSERVATIONS", str(tmp_path / "spoofed.yaml"))

    for bad_root in (str(other_root), "../other-repo"):
        r1 = broker.handle_request({
            "tool": "los",
            "argv": ["--root", bad_root, "status", "--json"],
            "cwd": str(core),
        })
        r2 = broker.handle_request({
            "tool": "los",
            "argv": ["--r", bad_root, "status", "--json"],
            "cwd": str(core),
        })
        r3 = broker.handle_request({
            "tool": "seal_envelope",
            "argv": [
                "--root", bad_root,
                "--capability", "garden.seed.create",
                "--payload", json.dumps({"title": "t", "text": "x"}),
                "--key", "k",
            ],
            "cwd": str(core),
        })
        assert r1.exit_code == 2 and r2.exit_code == 2 and r3.exit_code == 2

    ok_omitted = broker.handle_request({
        "tool": "los",
        "argv": ["status", "--json"],
        "cwd": str(core),
    })
    assert ok_omitted.exit_code == 0, ok_omitted.stderr
    omitted_cmd, _, _, _ = runner.calls[-1]
    assert "--root" in omitted_cmd and str(broker.core_root) in omitted_cmd

    ok = broker.handle_request({
        "tool": "los",
        "argv": ["--root", str(core), "status", "--json"],
        "cwd": str(core),
    })
    assert ok.exit_code == 0, ok.stderr
    _, _, child_env, _ = runner.calls[-1]
    assert child_env["LOS_OBSERVATIONS"] == str(host_obs)
    assert child_env["LOS_SESSION_ID"] == SESSION
    assert child_env[STUDY_FENCE_CORE_ENV] == str(Path(os.path.realpath(core)))
    assert child_env[STUDY_FENCE_SCRATCH_ENV] == str(Path(os.path.realpath(scratch)))
    assert "LOS_GATE_SOCK" not in child_env


def test_host_path_firewall_blocks_protected_external_and_symlink_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    core, scratch = _make_broker_world(tmp_path)
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("SECRET_OUTSIDE", encoding="utf-8")
    symlink_in_scratch = scratch / "link-out.txt"
    symlink_in_scratch.symlink_to(outside)
    symlink_to_mat = scratch / "link-mat.pdf"
    symlink_to_mat.symlink_to(core.parent / "materials/book.pdf")

    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / "fake-home").mkdir()
    (tmp_path / "fake-home" / "secret.txt").write_text("SECRET_HOME", encoding="utf-8")

    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    protected_targets = [
        *[str(p / "child.txt") for p in protected_reads(core)],
        str(core / "operations/ai-actions/requests/req-1/slice.md"),
        str(core.parent / "materials/book.pdf"),
        str(outside),
        str(symlink_in_scratch),
        str(symlink_to_mat),
        "~/secret.txt",
    ]
    for bad in protected_targets:
        for field_payload in (
            {"file": bad},
            {"body_file": bad},
            {"content_file": bad},
            {"attachment": [bad]},
            {"bundle": {"notes": [{"body_file": bad}]}},
        ):
            res = broker.handle_request({
                "tool": "seal_envelope",
                "argv": [
                    "--capability", "capture.create",
                    "--payload", json.dumps(field_payload),
                    "--key", "k1",
                    "--submit",
                ],
                "cwd": str(core),
            })
            assert res.exit_code == 2, (bad, field_payload)

        # Also check --payload-file, --payload @PATH, and --guards-from pointing to bad paths.
        r_pf = broker.handle_request({
            "tool": "los",
            "argv": ["capability", "capture.create", "--payload-file", bad],
            "cwd": str(core),
        })
        r_at = broker.handle_request({
            "tool": "seal_envelope",
            "argv": ["--capability", "capture.create", "--payload", f"@{bad}", "--key", "k1"],
            "cwd": str(core),
        })
        r_gf = broker.handle_request({
            "tool": "seal_envelope",
            "argv": ["--guards-from", bad, "--submit"],
            "cwd": str(core),
        })
        assert r_pf.exit_code == 2 and r_at.exit_code == 2 and r_gf.exit_code == 2

    # Valid path inside scratch passes and forwards cleanly.
    good_draft = scratch / "draft.md"
    good_draft.write_text("good body", encoding="utf-8")
    ok = broker.handle_request({
        "tool": "seal_envelope",
        "argv": [
            "--capability", "capture.create",
            "--payload", json.dumps({"file": str(good_draft), "title": "t"}),
            "--key", "k-ok",
            "--submit",
        ],
        "cwd": str(core),
    })
    assert ok.exit_code == 0, ok.stderr

    # Valid non-protected path inside core passes (and protected path inside core fails).
    ok_core = broker.handle_request({
        "tool": "seal_envelope",
        "argv": [
            "--capability", "capture.create",
            "--payload", json.dumps({"file": "knowledge/notes/study.md", "title": "t"}),
            "--key", "k-core",
            "--submit",
        ],
        "cwd": str(core),
    })
    assert ok_core.exit_code == 0, ok_core.stderr
    assert len(runner.calls) == 2


def test_gateway_read_content_bound_file_enforces_study_fence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    core, scratch = _make_broker_world(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside secret", encoding="utf-8")
    good = scratch / "allowed.txt"
    good.write_text("allowed bytes", encoding="utf-8")

    monkeypatch.setenv(STUDY_FENCE_CORE_ENV, str(core))
    monkeypatch.setenv(STUDY_FENCE_SCRATCH_ENV, str(scratch))

    with pytest.raises(WriteRefused):
        read_content_bound_file(str(core.parent / "materials/book.pdf"))
    with pytest.raises(WriteRefused):
        read_content_bound_file(str(core / "generated/text-cache/x/p1.txt"))
    with pytest.raises(WriteRefused):
        read_content_bound_file(str(outside))
    with pytest.raises(WriteRefused):
        read_content_bound_file("-")

    path, data = read_content_bound_file(
        str(good), "sha256:" + hashlib.sha256(b"allowed bytes").hexdigest()
    )
    assert path == good.resolve() and data == b"allowed bytes"

    # seal_envelope._bind_file_digests also refuses under active study fence.
    with pytest.raises(ValueError, match="study mode blocks"):
        seal_envelope._bind_file_digests(ROOT, "capture.create", {"file": str(outside)})


def test_study_hook_rpc_only_allows_session_start_and_stop(tmp_path: Path) -> None:
    core, scratch = _make_broker_world(tmp_path)
    runner = RecordingRunner()
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)

    for bad_event in ("session-end", "pre-tool-use", "profile", "arbitrary"):
        denied = broker.handle_request({"tool": "study_hook", "event": bad_event})
        assert denied.exit_code == 2
    assert runner.calls == []

    for ok_event in ("session-start", "stop"):
        ok = broker.handle_request({
            "tool": "study_hook",
            "event": ok_event,
            "stop_hook_active": True,
        })
        assert ok.exit_code == 0
        cmd, _, _, stdin_data = runner.calls[-1]
        assert str(core / "tools" / "study_hooks.py") in cmd
        assert ok_event in cmd
        assert json.loads(stdin_data or "{}") == {
            "session_id": SESSION,
            "stop_hook_active": True,
        }


def test_live_unix_socket_end_to_end_round_trip_and_fail_closed(
    mini_repo: Path, tmp_path: Path,
) -> None:
    add_curriculum(mini_repo)
    shutil.copytree(
        ROOT / "tools",
        mini_repo / "tools",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (mini_repo / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)
    write_minimal_pdf(
        mini_repo.parent / "materials" / BOOK,
        [f"Evidence paragraph on page {n}." for n in range(1, 5)],
    )

    scratch = Path(os.path.realpath(tmp_path / "scratch"))
    scratch.mkdir(parents=True, exist_ok=True)
    sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losb-", dir="/tmp")))
    sock_path = sock_dir / "g.sock"

    broker = StudyBroker(mini_repo, SESSION, scratch_dir=scratch)
    server = BrokerServer(broker, sock_path)
    server.start()
    try:
        env = dict(os.environ, LOS_GATE_SOCK=str(sock_path), PYTHONDONTWRITEBYTECODE="1")
        py = str(mini_repo / ".venv/bin/python")
        los_py = str(mini_repo / "tools/los.py")
        seal_py = str(mini_repo / "tools/seal_envelope.py")

        # 1. Allowed read query succeeds via LOS_GATE_SOCK.
        status_proc = subprocess.run(
            [py, los_py, "status", "--json"],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert status_proc.returncode == 0, status_proc.stderr
        status_data = json.loads(status_proc.stdout)
        assert "learning_os" in status_data and "counts" in status_data

        # 2. Disallowed command fails closed with exit 2.
        denied_proc = subprocess.run(
            [py, los_py, "backup-manifest", "--json"],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert denied_proc.returncode == 2

        # 3. material-span --extract rewrites to material-study-span and records pending debt.
        span_proc = subprocess.run(
            [py, los_py, "material-span", "--material", BOOK, "--pages", "pdf p. 1", "--extract"],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert span_proc.returncode == 0, span_proc.stderr
        span_data = json.loads(span_proc.stdout)
        assert span_data["contract"] == "material-study-span-v1"
        assert span_data["study"]["session"] == SESSION
        entry_id = span_data["study"]["open_entries"][0]["entry"]

        # 4. Settle the opened card cleanly.
        card = {
            "paraphrase": "Evidence paragraph examined on page 1.",
            "kinds": ["statement"],
            "pointers": [{"page": 1, "kind": "statement", "label": "evidence paragraph"}],
            "concepts": [],
        }
        settle_proc = subprocess.run(
            [py, los_py, "material-card-settle", entry_id, "--card", json.dumps(card)],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert settle_proc.returncode == 0, settle_proc.stderr

        # 5. seal_envelope --guards auto --check-out and --guards-from --submit round-trip.
        check_rec = scratch / "check-rec.json"
        env_out = scratch / "sealed-env.json"
        note_payload = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "text": "studied p.1"}
        seal_check = subprocess.run(
            [
                py,
                seal_py,
                "--capability",
                "stage.note.write",
                "--payload",
                json.dumps(note_payload),
                "--key",
                "k-study-1",
                "--guards",
                "auto",
                "--check-out",
                str(check_rec),
                "--out",
                str(env_out),
            ],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert seal_check.returncode == 0, seal_check.stderr
        assert check_rec.is_file() and json.loads(check_rec.read_text())["ok"] is True
        assert env_out.is_file() and json.loads(env_out.read_text())["capability"] == "stage.note.write"

        # 6. --guards-from --submit commits cleanly via broker.
        seal_submit = subprocess.run(
            [py, seal_py, "--guards-from", str(check_rec), "--submit"],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert seal_submit.returncode == 0, seal_submit.stdout + seal_submit.stderr
        first_line = seal_submit.stdout.splitlines()[0]
        assert json.loads(first_line)["ok"] is True

        # 7. Failing --guards auto --check-out still delivers the local check record cleanly on exit 2.
        (mini_repo / "knowledge/notes/broken-for-check.md").write_text(
            "---\nid: broken-for-check\n---\n", encoding="utf-8"
        )
        fail_rec = scratch / "fail-rec.json"
        seal_fail = subprocess.run(
            [
                py,
                seal_py,
                "--capability",
                "garden.seed.create",
                "--payload",
                json.dumps({"title": "fail", "text": "seed text"}),
                "--key",
                "k-study-fail",
                "--guards",
                "auto",
                "--check-out",
                str(fail_rec),
            ],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert seal_fail.returncode == 2
        assert fail_rec.is_file() and json.loads(fail_rec.read_text())["ok"] is False
    finally:
        server.close()
        shutil.rmtree(sock_dir, ignore_errors=True)

    # Killed/closed broker fails closed with exit 2 (never bypasses).
    dead_proc = subprocess.run(
        [py, los_py, "status", "--json"],
        cwd=str(mini_repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert dead_proc.returncode == 2
    assert "study broker unavailable" in dead_proc.stderr


def test_broker_socket_incomplete_and_oversized_requests_never_stall_healthy_clients(
    tmp_path: Path,
) -> None:
    """Requirement 1: stalled partial or oversized socket frames refuse fast without blocking peers."""
    core, scratch = _make_broker_world(tmp_path)
    runner = RecordingRunner(rc=0, out='{"ok": true}\n')
    broker = StudyBroker(core, SESSION, scratch_dir=scratch, runner=runner)
    sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losres-", dir="/tmp")))
    sock_path = sock_dir / "gate.sock"
    server = BrokerServer(
        broker,
        sock_path,
        read_timeout_s=0.35,
        write_timeout_s=1.0,
        max_request_bytes=512,
        max_workers=8,
    )
    server.start()
    try:
        # 1. Stalled incomplete request stays open without newline; healthy peer must still succeed.
        stalled = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        stalled.settimeout(3.0)
        stalled.connect(str(sock_path))
        stalled.sendall(b'{"tool": "los", "argv": ["stat')

        try:
            healthy = send_broker_request(
                str(sock_path),
                {"tool": "los", "argv": ["status", "--json"]},
            )
            assert healthy["exit_code"] == 0, healthy
            assert healthy["stdout"] == '{"ok": true}\n'
            assert len(runner.calls) == 1

            chunks: list[bytes] = []
            while True:
                data = stalled.recv(4096)
                if not data:
                    break
                chunks.append(data)
            stalled_resp = json.loads(b"".join(chunks).decode("utf-8"))
            assert stalled_resp["exit_code"] == 2
            assert "timed out after" in stalled_resp["stderr"]
        finally:
            stalled.close()

        # 2. Oversized request (both newline-terminated and streaming) fails closed cleanly.
        for with_newline in (True, False):
            big = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            big.settimeout(3.0)
            big.connect(str(sock_path))
            try:
                frame = b'{"tool":"los","argv":["status"],"pad":"' + (b"x" * 1024) + b'"}'
                if with_newline:
                    frame += b"\n"
                try:
                    big.sendall(frame)
                except OSError:
                    pass
                out_chunks: list[bytes] = []
                while True:
                    try:
                        chunk = big.recv(4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    out_chunks.append(chunk)
                big_resp = json.loads(b"".join(out_chunks).decode("utf-8"))
                assert big_resp["exit_code"] == 2
                assert "exceeds max size" in big_resp["stderr"]
            finally:
                big.close()

        # Broker remains healthy after timeout + oversize rejections.
        after = send_broker_request(str(sock_path), {"tool": "los", "argv": ["status", "--json"]})
        assert after["exit_code"] == 0
        assert len(runner.calls) == 2
    finally:
        server.close()
        shutil.rmtree(sock_dir, ignore_errors=True)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_pid_dead(pid: int, timeout_s: float = 2.5) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.02)
    return not _pid_alive(pid)


def test_broker_core_subprocess_timeout_kills_process_group_and_recovers(
    tmp_path: Path,
) -> None:
    """Requirement 2: hung Core subprocess + grandchild is killed and broker stays usable."""
    core, scratch = _make_broker_world(tmp_path)
    pids_file = scratch / "pids.json"
    hang_flag = scratch / "hang.flag"
    hang_flag.write_text("1", encoding="utf-8")

    stub_los = core / "tools/los.py"
    stub_los.write_text(
        f"""
import json, os, subprocess, sys, time
from pathlib import Path

hang_flag = Path({str(hang_flag)!r})
pids_file = Path({str(pids_file)!r})
if hang_flag.exists():
    grand = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pids_file.write_text(json.dumps({{"child": os.getpid(), "grand": grand.pid}}), encoding="utf-8")
    sys.stdout.flush()
    time.sleep(60)
else:
    print(json.dumps({{"ok": True, "args": sys.argv[1:]}}))
""",
        encoding="utf-8",
    )

    broker = StudyBroker(
        core,
        SESSION,
        scratch_dir=scratch,
        python_executable=Path(sys.executable),
        core_timeout_s=0.35,
    )
    res_timeout = broker.handle_request({
        "tool": "los",
        "argv": ["status", "--json"],
        "cwd": str(core),
    })
    assert res_timeout.exit_code == 2
    assert "timed out after" in res_timeout.stderr
    pids = json.loads(pids_file.read_text(encoding="utf-8"))
    assert _wait_pid_dead(pids["child"]), f"orphan child {pids['child']} survived"
    assert _wait_pid_dead(pids["grand"]), f"orphan grandchild {pids['grand']} survived"

    # Removing hang trigger leaves the same broker healthy on subsequent requests.
    hang_flag.unlink()
    res_ok = broker.handle_request({
        "tool": "los",
        "argv": ["status", "--json"],
        "cwd": str(core),
    })
    assert res_ok.exit_code == 0, res_ok.stderr
    assert json.loads(res_ok.stdout)["ok"] is True

    # Server close() also cancels an active hung process group without deadlocking.
    hang_flag.write_text("1", encoding="utf-8")
    pids_file.unlink()
    sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="loskill-", dir="/tmp")))
    sock_path = sock_dir / "gate.sock"
    long_broker = StudyBroker(
        core,
        SESSION,
        scratch_dir=scratch,
        python_executable=Path(sys.executable),
        core_timeout_s=30.0,
    )
    server = BrokerServer(long_broker, sock_path)
    server.start()
    thread_exc: list[BaseException] = []
    client_thread = threading.Thread(
        target=lambda: _capture_client(str(sock_path), thread_exc),
        daemon=True,
    )
    try:
        client_thread.start()
        deadline = time.monotonic() + 5.0
        while not pids_file.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert pids_file.exists(), "Core stub did not start in time"
        pids2 = json.loads(pids_file.read_text(encoding="utf-8"))
    finally:
        server.close()
        client_thread.join(timeout=3.0)
        shutil.rmtree(sock_dir, ignore_errors=True)
    assert not client_thread.is_alive()
    assert _wait_pid_dead(pids2["child"])
    assert _wait_pid_dead(pids2["grand"])


def _capture_client(sock_path: str, exc_out: list[BaseException]) -> None:
    try:
        send_broker_request(sock_path, {"tool": "los", "argv": ["status", "--json"]})
    except BaseException as exc:
        exc_out.append(exc)


def test_path_race_concurrent_symlink_swap_blocks_secret_disclosure(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Requirement 3: concurrent symlink swapping never discloses outside or protected files."""
    add_curriculum(mini_repo)
    shutil.copytree(
        ROOT / "tools",
        mini_repo / "tools",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (mini_repo / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)

    outside_secret = tmp_path / "outside-secret.txt"
    outside_secret.write_text("TOP_SECRET_CANARY_999\n", encoding="utf-8")
    protected_secret = mini_repo.parent / "materials" / "secret-race.txt"
    protected_secret.parent.mkdir(parents=True, exist_ok=True)
    protected_secret.write_text("PROTECTED_MATERIAL_CANARY\n", encoding="utf-8")

    scratch = Path(os.path.realpath(tmp_path / "scratch"))
    scratch.mkdir(parents=True, exist_ok=True)
    race_file = scratch / "capture-race.md"
    race_file.write_text("Safe study capture text\n", encoding="utf-8")

    sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losrace-", dir="/tmp")))
    sock_path = sock_dir / "gate.sock"
    broker = StudyBroker(mini_repo, SESSION, scratch_dir=scratch)
    server = BrokerServer(broker, sock_path)
    server.start()

    stop_race = threading.Event()

    def _swapper() -> None:
        counter = 0
        while not stop_race.is_set():
            tmp_entry = scratch / f".swap-{counter}"
            try:
                if counter % 2 == 0:
                    tmp_entry.symlink_to(outside_secret)
                else:
                    tmp_entry.write_text("Safe study capture text\n", encoding="utf-8")
                os.replace(tmp_entry, race_file)
            except OSError:
                tmp_entry.unlink(missing_ok=True)
            counter += 1

    racer = threading.Thread(target=_swapper, daemon=True)
    py = str(mini_repo / ".venv/bin/python")
    seal_py = str(mini_repo / "tools/seal_envelope.py")
    env = dict(os.environ, LOS_GATE_SOCK=str(sock_path), PYTHONDONTWRITEBYTECODE="1")
    try:
        racer.start()
        for idx in range(8):
            proc = subprocess.run(
                [
                    py,
                    seal_py,
                    "--capability",
                    "capture.create",
                    "--payload",
                    json.dumps({"file": str(race_file)}),
                    "--key",
                    f"race-key-{idx}",
                    "--guards",
                    "auto",
                    "--submit",
                ],
                cwd=str(mini_repo),
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert "TOP_SECRET_CANARY_999" not in proc.stdout
            assert "TOP_SECRET_CANARY_999" not in proc.stderr
            if proc.returncode != 0:
                assert proc.returncode == 2, proc.stderr
                assert (
                    "study mode blocks symlink" in proc.stderr
                    or "outside the study boundary" in proc.stderr
                ), proc.stderr
            else:
                res = json.loads(proc.stdout.splitlines()[0])
                assert res["ok"] is True
    finally:
        stop_race.set()
        racer.join(timeout=2.0)
        server.close()
        shutil.rmtree(sock_dir, ignore_errors=True)

    # Every committed capture under knowledge/ must hold ONLY safe bytes, never the canary.
    for path in (mini_repo / "knowledge").rglob("*"):
        if path.is_file():
            content = path.read_text(encoding="utf-8", errors="replace")
            assert "TOP_SECRET_CANARY_999" not in content

    # Direct O_NOFOLLOW fence enforcement inside Core rejects symlink swaps & nested dir symlinks.
    monkeypatch.setenv(STUDY_FENCE_CORE_ENV, str(mini_repo))
    monkeypatch.setenv(STUDY_FENCE_SCRATCH_ENV, str(scratch))
    monkeypatch.delenv("LOS_STUDY_STAGED_MANIFEST", raising=False)
    sym_direct = scratch / "direct-sym.md"
    sym_direct.symlink_to(protected_secret)
    with pytest.raises(WriteRefused, match=r"study mode blocks (symlink|direct|file)"):
        read_content_bound_file(str(sym_direct), label="race file")
    sym_dir = scratch / "dir-sym"
    sym_dir.symlink_to(tmp_path)
    with pytest.raises(WriteRefused, match="study mode blocks symlink"):
        read_content_bound_file(str(sym_dir / "outside-secret.txt"), label="nested sym")
    dangling = scratch / "dangling-sym.md"
    dangling.symlink_to(scratch / "missing-target.md")
    with pytest.raises(WriteRefused, match="study mode blocks symlink"):
        read_content_bound_file(str(dangling), label="dangling sym")


def test_privileged_output_paths_cannot_overwrite_or_escape_via_symlinks(
    mini_repo: Path, tmp_path: Path,
) -> None:
    """Requirement 4: --report-out, --check-out, and --out block overwrites and symlinks."""
    _compact_setup(mini_repo)
    shutil.copytree(
        ROOT / "tools",
        mini_repo / "tools",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (mini_repo / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)

    scratch = Path(os.path.realpath(tmp_path / "scratch"))
    scratch.mkdir(parents=True, exist_ok=True)
    draft = scratch / "revision.yaml"
    write_yaml(
        draft,
        _compact_revision(
            mini_repo,
            route_changes={
                "update": [
                    {
                        "route_id": "route-demo-book",
                        "fields": {"angle": "A sharper mediated study angle."},
                    }
                ]
            },
        ),
    )

    outside_sentinel = tmp_path / "outside-sentinel.json"
    outside_sentinel.write_text('{"sentinel": "intact"}\n', encoding="utf-8")
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    outside_existing_sub = outside_dir / "existing-sub"
    outside_existing_sub.mkdir()

    sym_to_outside = scratch / "sym-out.json"
    sym_to_outside.symlink_to(outside_sentinel)
    sym_dir_to_outside = scratch / "sym-dir"
    sym_dir_to_outside.symlink_to(outside_dir)
    dangling_in_scratch = scratch / "dangling-out.json"
    dangling_in_scratch.symlink_to(scratch / "never-created.json")
    existing_in_scratch = scratch / "existing.json"
    existing_in_scratch.write_text('{"keep": true}\n', encoding="utf-8")
    hard_to_outside = scratch / "hard-out.json"
    os.link(outside_sentinel, hard_to_outside)
    hard_to_scratch = scratch / "hard-scratch.json"
    os.link(existing_in_scratch, hard_to_scratch)

    sock_dir = Path(os.path.realpath(tempfile.mkdtemp(prefix="losout-", dir="/tmp")))
    sock_path = sock_dir / "gate.sock"
    stage_root = tmp_path / "broker-stage"
    broker = StudyBroker(mini_repo, SESSION, scratch_dir=scratch, stage_root=stage_root)
    server = BrokerServer(broker, sock_path)
    server.start()

    py = str(mini_repo / ".venv/bin/python")
    los_py = str(mini_repo / "tools/los.py")
    seal_py = str(mini_repo / "tools/seal_envelope.py")
    env = dict(
        os.environ,
        LOS_GATE_SOCK=str(sock_path),
        LOS_SCRATCH_DIR=str(scratch),
        PYTHONDONTWRITEBYTECODE="1",
    )
    try:
        # 1. Valid mediated unit-plan-revise --check --report-out writes locally with matching SHA-256.
        valid_report = scratch / "mediated-report.json"
        ok_rev = subprocess.run(
            [
                py,
                los_py,
                "unit-plan-revise",
                "unit-demo-l01",
                "--file",
                str(draft),
                "--check",
                "--report-out",
                str(valid_report),
            ],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert ok_rev.returncode == 0, ok_rev.stderr
        assert valid_report.is_file()
        compact = json.loads(ok_rev.stdout)
        saved_meta = compact["saved_report"]
        assert Path(saved_meta["path"]) == valid_report
        assert saved_meta["sha256"] == "sha256:" + hashlib.sha256(valid_report.read_bytes()).hexdigest()
        assert json.loads(valid_report.read_text(encoding="utf-8"))["ok"] is True

        # 2. Symlink, symlinked dir (both existing-sub and nested), hardlinks, dangling symlink,
        #    protected path, outside-scratch path, pre-existing file, and == draft refusals
        #    hold identically across both CLI-mediated execution and direct broker RPC.
        bad_report_targets = [
            (str(sym_to_outside), ("study mode blocks symlink", "outside the study boundary")),
            (str(sym_dir_to_outside / "leak.json"), ("study mode blocks symlink", "outside the study boundary")),
            (str(sym_dir_to_outside / "existing-sub" / "leak.json"), ("study mode blocks symlink", "outside the study boundary")),
            (str(dangling_in_scratch), ("study mode blocks symlink",)),
            (str(hard_to_outside), ("already exists; refusing to overwrite",)),
            (str(hard_to_scratch), ("already exists; refusing to overwrite",)),
            (str(outside_dir / "leak.json"), ("outside the study boundary",)),
            (str(mini_repo / "operations/ai-actions/requests/leak.json"), ("inside protected LearningOS tree", "outside the study boundary")),
            (str(mini_repo / "knowledge/leak.json"), ("outside the study boundary",)),
            (str(existing_in_scratch), ("already exists; refusing to overwrite",)),
            (str(scratch), ("must be a file inside study scratch",)),
            (str(draft), ("must not replace the reviewed draft",)),
        ]
        for bad_path, expected_fragments in bad_report_targets:
            bad_proc = subprocess.run(
                [
                    py,
                    los_py,
                    "unit-plan-revise",
                    "unit-demo-l01",
                    "--file",
                    str(draft),
                    "--check",
                    "--report-out",
                    bad_path,
                ],
                cwd=str(mini_repo),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert bad_proc.returncode == 2, (bad_path, bad_proc.stderr)
            assert any(frag in bad_proc.stderr for frag in expected_fragments), (
                bad_path,
                bad_proc.stderr,
            )

        # 3. seal_envelope --check-out and --out reject symlinks, hardlinks, dangling symlinks,
        #    parent symlinks (existing-sub + nested), outside-scratch, and protected paths
        #    across CLI shim and direct socket RPC.
        payload_json = json.dumps({"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "text": "x"})
        bad_seal_targets = [
            (str(sym_to_outside), ("study mode blocks symlink",)),
            (str(sym_dir_to_outside / "leak.json"), ("study mode blocks symlink",)),
            (str(sym_dir_to_outside / "existing-sub" / "leak.json"), ("study mode blocks symlink",)),
            (str(dangling_in_scratch), ("study mode blocks symlink",)),
            (str(hard_to_outside), ("study mode blocks hardlink",)),
            (str(hard_to_scratch), ("study mode blocks hardlink",)),
            (str(outside_dir / "leak.json"), ("outside the study boundary",)),
            (str(scratch), ("must be a file inside study scratch",)),
            (
                str(mini_repo / "operations/ai-actions/requests/leak.json"),
                ("refusing to write", "inside protected LearningOS tree", "outside the study boundary"),
            ),
        ]
        for flag in ("--check-out", "--out"):
            for bad_path, expected_fragments in bad_seal_targets:
                seal_bad = subprocess.run(
                    [
                        py,
                        seal_py,
                        "--capability",
                        "stage.note.write",
                        "--payload",
                        payload_json,
                        "--key",
                        f"k-cli-{flag.strip('-')}",
                        "--guards",
                        "auto",
                        flag,
                        bad_path,
                    ],
                    cwd=str(mini_repo),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                assert seal_bad.returncode == 2, (flag, bad_path, seal_bad.stderr)
                assert any(frag in seal_bad.stderr for frag in expected_fragments), (
                    flag,
                    bad_path,
                    seal_bad.stderr,
                )

        # Verify invalid --report-out, --check-out, and --out are rejected on direct RPC BEFORE
        # any privileged Core execution begins (runner spy calls == 0).
        core_runner_calls = 0

        def _never_run_core(*_args: object, **_kwargs: object) -> tuple[int, str, str]:
            nonlocal core_runner_calls
            core_runner_calls += 1
            raise AssertionError("privileged Core should never run for invalid output path")

        spy_broker = StudyBroker(
            mini_repo,
            SESSION,
            scratch_dir=scratch,
            stage_root=stage_root,
            runner=_never_run_core,
        )
        spy_sock = sock_dir / "spy.sock"
        spy_server = BrokerServer(spy_broker, spy_sock)
        spy_server.start()
        try:
            for bad_path, expected_fragments in bad_report_targets:
                direct_los = send_broker_request(
                    str(spy_sock),
                    {
                        "tool": "los",
                        "argv": [
                            "unit-plan-revise",
                            "unit-demo-l01",
                            "--file",
                            str(draft),
                            "--check",
                            "--report-out",
                            bad_path,
                        ],
                        "cwd": str(mini_repo),
                    },
                )
                assert direct_los["exit_code"] == 2, (bad_path, direct_los)
                err_text = str(direct_los.get("stderr", ""))
                assert any(frag in err_text for frag in expected_fragments), (bad_path, err_text)

            for flag in ("--check-out", "--out"):
                for bad_path, expected_fragments in bad_seal_targets:
                    broker_fragments = tuple(
                        frag for frag in expected_fragments if frag != "refusing to write"
                    )
                    direct_resp = send_broker_request(
                        str(spy_sock),
                        {
                            "tool": "seal_envelope",
                            "argv": [
                                "--capability",
                                "stage.note.write",
                                "--payload",
                                payload_json,
                                "--key",
                                f"k-rpc-{flag.strip('-')}",
                                "--guards",
                                "auto",
                                flag,
                                bad_path,
                            ],
                            "cwd": str(mini_repo),
                        },
                    )
                    assert direct_resp["exit_code"] == 2, (flag, bad_path, direct_resp)
                    err_text = str(direct_resp.get("stderr", ""))
                    assert any(frag in err_text for frag in broker_fragments), (
                        flag,
                        bad_path,
                        err_text,
                    )
            assert core_runner_calls == 0
        finally:
            spy_server.close()

        # Valid --check-out and --out write cleanly locally in scratch without touching core.
        valid_check = scratch / "mediated-seal-check.json"
        valid_env = scratch / "mediated-seal-env.json"
        seal_check_ok = subprocess.run(
            [
                py,
                seal_py,
                "--capability",
                "stage.note.write",
                "--payload",
                payload_json,
                "--key",
                "k-valid-check",
                "--guards",
                "auto",
                "--check-out",
                str(valid_check),
            ],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert seal_check_ok.returncode == 0, seal_check_ok.stderr
        assert json.loads(valid_check.read_text(encoding="utf-8"))["ok"] is True

        seal_out_ok = subprocess.run(
            [
                py,
                seal_py,
                "--capability",
                "stage.note.write",
                "--payload",
                payload_json,
                "--key",
                "k-valid-out",
                "--guards",
                "auto",
                "--out",
                str(valid_env),
            ],
            cwd=str(mini_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert seal_out_ok.returncode == 0, seal_out_ok.stderr
        assert json.loads(valid_env.read_text(encoding="utf-8"))["capability"] == "stage.note.write"

        # Client-side local output helper refuses symlinks, hardlinks, parent symlinks, and outside-scratch targets.
        for bad_local, expected_errnos in (
            (sym_to_outside, (errno.ELOOP,)),
            (dangling_in_scratch, (errno.ELOOP,)),
            (sym_dir_to_outside / "nested" / "leak.json", (errno.ELOOP,)),
            (sym_dir_to_outside / "existing-sub" / "leak.json", (errno.ELOOP,)),
            (hard_to_outside, (errno.EMLINK,)),
            (hard_to_scratch, (errno.EMLINK,)),
            (outside_dir / "escape.json", (errno.EACCES,)),
        ):
            with pytest.raises(OSError) as exc_info:
                write_local_output_file(
                    str(bad_local), '{"pwn": true}\n', mkdir_parents=True, scratch_dir=scratch,
                )
            assert exc_info.value.errno in expected_errnos, (bad_local, exc_info.value)

        # Concurrent parent-directory symlink swap during client local write cannot write to outside_dir.
        race_dir = scratch / "race-parent"
        stop_race = threading.Event()
        errors_race: list[BaseException] = []

        def _swap_parent() -> None:
            while not stop_race.is_set():
                try:
                    if race_dir.is_symlink():
                        race_dir.unlink()
                    elif race_dir.exists():
                        shutil.rmtree(race_dir, ignore_errors=True)
                    race_dir.symlink_to(outside_dir)
                except OSError:
                    pass

        swapper = threading.Thread(target=_swap_parent, daemon=True)
        swapper.start()
        try:
            for i in range(40):
                try:
                    write_local_output_file(
                        str(race_dir / "sub" / f"out-{i}.json"),
                        '{"ok": true}\n',
                        mkdir_parents=True,
                        scratch_dir=scratch,
                    )
                except OSError as exc:
                    if exc.errno not in (errno.ELOOP, errno.EEXIST, errno.ENOENT, errno.ENOTDIR):
                        errors_race.append(exc)
        finally:
            stop_race.set()
            swapper.join(timeout=2.0)
        assert not errors_race, errors_race
        assert not (outside_dir / "sub").exists()

        assert outside_sentinel.read_text(encoding="utf-8") == '{"sentinel": "intact"}\n'
        assert existing_in_scratch.read_text(encoding="utf-8") == '{"keep": true}\n'
        assert not (outside_dir / "leak.json").exists()
        assert not (outside_existing_sub / "leak.json").exists()
        assert not (outside_dir / "escape.json").exists()
        assert not (mini_repo / "operations/ai-actions/requests/leak.json").exists()

        # 4. Client local --report-out write fails closed if target becomes a symlink or hardlink before write.
        old_cwd = os.getcwd()
        os.chdir(mini_repo)
        try:
            res = dispatch_los_via_socket(
                str(sock_path),
                [
                    "unit-plan-revise",
                    "unit-demo-l01",
                    "--file",
                    str(draft),
                    "--check",
                    "--report-out",
                    str(dangling_in_scratch),
                ],
            )
            assert res == 2
        finally:
            os.chdir(old_cwd)
        assert not (scratch / "never-created.json").exists()
    finally:
        server.close()
        shutil.rmtree(sock_dir, ignore_errors=True)


def test_call_dir_fd_op_retries_transient_einval() -> None:
    """Transient APFS EINVAL mid-rmdir is retried, while settled/non-EINVAL errnos surface."""
    success_calls = 0

    def _transient_then_ok() -> str:
        nonlocal success_calls
        success_calls += 1
        if success_calls == 1:
            raise OSError(errno.EINVAL, "Invalid argument")
        return "ok"

    assert call_dir_fd_op(_transient_then_ok) == "ok"
    assert success_calls == 2

    transient_calls = 0

    def _transient_then_enoent() -> int:
        nonlocal transient_calls
        transient_calls += 1
        if transient_calls < 3:
            raise OSError(errno.EINVAL, "Invalid argument")
        raise OSError(errno.ENOENT, "No such file or directory")

    with pytest.raises(OSError) as settled:
        call_dir_fd_op(_transient_then_enoent)
    assert settled.value.errno == errno.ENOENT
    assert transient_calls == 3

    eloop_calls = 0

    def _immediate_eloop() -> int:
        nonlocal eloop_calls
        eloop_calls += 1
        raise OSError(errno.ELOOP, "Too many levels of symbolic links")

    with pytest.raises(OSError) as eloop:
        call_dir_fd_op(_immediate_eloop)
    assert eloop.value.errno == errno.ELOOP
    assert eloop_calls == 1

    persistent_calls = 0

    def _persistent_einval() -> int:
        nonlocal persistent_calls
        persistent_calls += 1
        raise OSError(errno.EINVAL, "Invalid argument")

    with pytest.raises(OSError) as exhausted:
        call_dir_fd_op(_persistent_einval)
    assert exhausted.value.errno == errno.EINVAL
    assert persistent_calls == 4
