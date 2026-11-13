"""Default-deny study broker and client transport checks (PLAN-D Step 3)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
import seal_envelope
from repo_builders import add_curriculum, write_minimal_pdf

from learning_os.adapters.study_broker import (
    ALLOWED_CAPABILITIES,
    ALLOWED_LOS_COMMANDS,
    ALLOWED_LOS_READ_COMMANDS,
    ALLOWED_PREFLIGHT_COMMANDS,
    ALLOWED_STUDY_COMMANDS,
    BrokerServer,
    StudyBroker,
)
from learning_os.app.gateway import (
    STUDY_FENCE_CORE_ENV,
    STUDY_FENCE_SCRATCH_ENV,
    read_content_bound_file,
)
from learning_os.domain.failures import WriteRefused
from learning_os.store.materials.reading_cards import protected_reads

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
