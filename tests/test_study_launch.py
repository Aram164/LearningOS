"""Cross-platform SBPL/launcher checks and macOS Seatbelt boundary tests (PLAN-D Step 5)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import study_launch
from repo_builders import (
    _compact_revision,
    _compact_setup,
    add_curriculum,
    write_minimal_pdf,
    write_yaml,
)

from learning_os.store.materials.reading_cards import (
    ADOPT_IDLE,
    ReadingStore,
    valid_session,
)
from learning_os.store.study_fence import protected_reads

ROOT = Path(__file__).resolve().parents[1]
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
DARWIN_SEATBELT = sys.platform == "darwin" and SANDBOX_EXEC.is_file()
BOOK = "_unsorted/review/book.pdf"
S1 = "eeeeeeee-5555-4555-8555-555555555555"
S2 = "ffffffff-6666-4666-8666-666666666666"


def _make_study_world(core: Path) -> Path:
    learningos = core.parent
    add_curriculum(core)
    shutil.copytree(
        ROOT / "tools",
        core / "tools",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copy2(ROOT / ".gitignore", core / ".gitignore")
    (core / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)
    write_minimal_pdf(
        learningos / "materials" / BOOK,
        [f"Evidence paragraph on page {n}." for n in range(1, 6)],
    )
    for rel in (
        "generated/text-cache/doc1",
        "generated/material-search",
        "generated/material-outlines",
        "generated/derived-state",
        "generated/summaries/doc1/pages-1-2",
        "operations/ai-actions/requests/req-1",
        "knowledge/garden",
    ):
        (core / rel).mkdir(parents=True, exist_ok=True)
    (core / "generated/text-cache/doc1/p1.txt").write_text("CANARY_TEXT_CACHE", encoding="utf-8")
    (core / "generated/material-search/idx.sqlite3").write_text("CANARY_SEARCH", encoding="utf-8")
    (core / "generated/material-outlines/o.json").write_text(
        json.dumps({"_generated": "generated; do not edit", "canary": "CANARY_OUTLINE"}),
        encoding="utf-8",
    )
    (core / "generated/derived-state/d.json").write_text(
        json.dumps({"_generated": "generated; do not edit", "canary": "CANARY_DERIVED"}),
        encoding="utf-8",
    )
    (core / "generated/summaries/doc1/pages-1-2/summary.md").write_text(
        "<!-- GENERATED file - do not edit -->\n\nCANARY_SUMMARY\n", encoding="utf-8",
    )
    (core / "operations/ai-actions/requests/.gitkeep").write_text("", encoding="utf-8")
    (core / "operations/ai-actions/requests/req-1/slice.md").write_text(
        "CANARY_REQUEST_SLICE", encoding="utf-8"
    )
    (learningos / "materials/secret.txt").write_text("CANARY_MATERIAL_SECRET", encoding="utf-8")
    (core / "knowledge/garden/public.md").write_text("# Public Note\n\nPUBLIC_GREP_NEEDLE\n", encoding="utf-8")

    # Initialize a real git repo so `git grep` exercises .gitignore traversal cleanly.
    for git_cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Test User"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "add", "."],
        ["git", "commit", "-q", "-m", "fixture"],
    ):
        subprocess.run(git_cmd, cwd=str(core), check=True, capture_output=True, text=True)
    return core


def test_build_seatbelt_profile_is_deterministic_non_regex_and_complete(tmp_path: Path) -> None:
    core = tmp_path / 'LearningOS "quoted"' / "repository"
    core.mkdir(parents=True)
    sb_first = study_launch.build_seatbelt_profile(core)
    sb_second = study_launch.build_seatbelt_profile(core)
    assert sb_first == sb_second
    assert "(version 1)" in sb_first
    assert "(allow default)" in sb_first
    assert "regex" not in sb_first

    real_core = Path(os.path.realpath(core))
    for closed in protected_reads(real_core):
        real_closed = Path(os.path.realpath(closed))
        expected = f'(deny file-read* (subpath "{study_launch._sbpl_quote(str(real_closed))}"))'
        assert expected in sb_first, expected

    req_dir = Path(os.path.realpath(real_core / "operations/ai-actions/requests"))
    allow_gitkeep = (
        '(allow file-read* '
        f'(literal "{study_launch._sbpl_quote(str(req_dir))}") '
        f'(literal "{study_launch._sbpl_quote(str(req_dir / ".gitkeep"))}"))'
    )
    deny_req = f'(deny file-read* (subpath "{study_launch._sbpl_quote(str(req_dir))}"))'
    assert sb_first.index(deny_req) < sb_first.index(allow_gitkeep)

    real_learningos = Path(os.path.realpath(real_core.parent))
    deny_write = f'(deny file-write* (subpath "{study_launch._sbpl_quote(str(real_learningos))}"))'
    assert deny_write in sb_first


def test_session_uuid_codex_args_and_entrypoint_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid_a = study_launch.session_uuid_for_runtime("claude", "runtime-42")
    sid_b = study_launch.session_uuid_for_runtime("claude", "runtime-42")
    sid_other = study_launch.session_uuid_for_runtime("codex", "runtime-42")
    assert sid_a == sid_b
    assert sid_a != sid_other
    assert valid_session(sid_a) and valid_session(sid_other)

    fake_bin = tmp_path / "codex"
    fake_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_bin.chmod(0o755)
    monkeypatch.setattr(study_launch.shutil, "which", lambda name: str(fake_bin))
    argv = study_launch._resolve_runtime_command(
        runtime="codex", use_cmd=False, extra=["exec", "status"],
    )
    assert argv == [
        str(fake_bin),
        "-s",
        "danger-full-access",
        "-c",
        "shell_environment_policy.inherit=all",
        "exec",
        "status",
    ]

    with pytest.raises(ValueError, match="mutually exclusive"):
        study_launch._resolve_session_id(
            explicit_session=S1, resume_runtime_id="x", runtime_tag="claude",
        )
    with pytest.raises(ValueError, match="lowercase UUID"):
        study_launch._resolve_session_id(
            explicit_session="not-a-uuid", resume_runtime_id=None, runtime_tag="claude",
        )
    with pytest.raises(ValueError, match="blank"):
        study_launch._resolve_session_id(
            explicit_session=None, resume_runtime_id="   ", runtime_tag="claude",
        )

    help_proc = subprocess.run(
        [sys.executable, str(ROOT / "tools/study_launch.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert help_proc.returncode == 0
    assert "--runtime" in help_proc.stdout and "--resume-runtime-id" in help_proc.stdout


def test_resolve_runtime_and_cmd_paths_keep_core_cwd_and_symlinks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    learningos = tmp_path / "LearningOS"
    core = learningos / "repository"
    outside = tmp_path / "outside"
    for p in (core / ".venv/bin", core / "tools", learningos / "materials/_unsorted", outside):
        p.mkdir(parents=True, exist_ok=True)
    real_python = tmp_path / "real-python"
    real_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    real_python.chmod(0o755)
    venv_py = core / ".venv/bin/python"
    venv_py.symlink_to(real_python)
    (core / "tools/los.py").write_text("# stub\n", encoding="utf-8")
    (learningos / "materials/_unsorted/book.pdf").write_text("%PDF", encoding="utf-8")
    wrapper = outside / "wrapper.sh"
    wrapper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    wrapper.chmod(0o755)
    cfg = outside / "cfg.json"
    cfg.write_text("{}", encoding="utf-8")

    real_core = Path(os.path.realpath(core))
    real_parent = Path(os.path.realpath(learningos))
    real_outside = Path(os.path.realpath(outside))
    real_materials = Path(os.path.realpath(learningos / "materials"))

    # Caller in LearningOS/ running caller-relative `repository/.venv/bin/python`:
    # preserves symlinked .venv path (never dereferencing to real_python) and resolves script arg.
    resolved_cmd = study_launch._resolve_runtime_command(
        runtime=None,
        use_cmd=True,
        extra=[
            "--",
            "repository/.venv/bin/python",
            "repository/tools/los.py",
            "-c",
            "repository/.venv/bin/python",
            "status",
        ],
        caller_cwd=real_parent,
        real_core=real_core,
    )
    assert resolved_cmd == [
        str(real_core / ".venv/bin/python"),
        str(real_core / "tools/los.py"),
        "-c",
        "repository/.venv/bin/python",  # -c inline code string stays untouched
        "status",
    ]

    # Core-relative `.venv/bin/python tools/los.py` stays untouched regardless of caller_cwd.
    core_cmd = study_launch._resolve_runtime_command(
        runtime=None,
        use_cmd=True,
        extra=["--", ".venv/bin/python", "tools/los.py", "status", "--json"],
        caller_cwd=real_outside,
        real_core=real_core,
    )
    assert core_cmd == [".venv/bin/python", "tools/los.py", "status", "--json"]

    # Outside caller-relative `./wrapper.sh --cfg=./cfg.json` resolves absolutely;
    # protected materials path `_unsorted/book.pdf` is never rewritten even from materials/.
    outside_cmd = study_launch._resolve_runtime_command(
        runtime=None,
        use_cmd=True,
        extra=["--", "./wrapper.sh", "--cfg=./cfg.json"],
        caller_cwd=real_outside,
        real_core=real_core,
    )
    assert outside_cmd == [str(real_outside / "wrapper.sh"), f"--cfg={real_outside / 'cfg.json'}"]

    mat_cmd = study_launch._resolve_runtime_command(
        runtime=None,
        use_cmd=True,
        extra=["--", ".venv/bin/python", "tools/los.py", "material-span", "--material", "_unsorted/book.pdf"],
        caller_cwd=real_materials,
        real_core=real_core,
    )
    assert mat_cmd[-1] == "_unsorted/book.pdf"

    # Relative `PATH` hits for `--runtime` become absolute so switching cwd to real_core cannot break exec.
    monkeypatch.chdir(real_outside)
    monkeypatch.setattr(study_launch.shutil, "which", lambda name: "./wrapper.sh")
    rt_cmd = study_launch._resolve_runtime_command(
        runtime="claude",
        use_cmd=False,
        extra=["--", "--settings", "./cfg.json"],
        caller_cwd=real_outside,
        real_core=real_core,
    )
    assert rt_cmd == [str(real_outside / "wrapper.sh"), "--settings", str(real_outside / "cfg.json")]


def test_non_darwin_or_missing_sandbox_exec_fails_closed(tmp_path: Path) -> None:
    core = tmp_path / "LearningOS" / "repository"
    core.mkdir(parents=True)
    marker = tmp_path / "should-not-run.txt"
    cmd = [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"]

    fake_sb = tmp_path / "sandbox-exec"
    fake_sb.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_sb.chmod(0o755)
    assert study_launch.launch_study(
        core_root=core, command=cmd, session_id=S1, sandbox_exec=fake_sb, platform="linux",
    ) == 2
    assert study_launch.launch_study(
        core_root=core,
        command=cmd,
        session_id=S1,
        sandbox_exec=tmp_path / "missing-sandbox-exec",
        platform="darwin",
    ) == 2
    assert not marker.exists()
    assert not (core.parent / "reading-memory").exists()


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="macOS /usr/bin/sandbox-exec required")
def test_seatbelt_adversarial_read_write_symlink_hardlink_and_grep_boundaries(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    core = _make_study_world(mini_repo)
    learningos = core.parent
    monkeypatch.setenv("HOME", str(learningos))

    # Materialize a future request child only *after* Seatbelt would already be active, or right before probe.
    future_req = core / "operations/ai-actions/requests/future.md"
    probe_script = tmp_path / "probe.py"
    probe_script.write_text(
        """
import errno, json, os, shutil, subprocess, sys
from pathlib import Path

core = Path(sys.argv[1])
learningos = core.parent
scratch = Path(os.environ["LOS_SCRATCH_DIR"])
assert not str(scratch).startswith(str(learningos))

# 1. Existing and newly created closed trees raise EPERM on direct read.
closed_files = [
    learningos / "materials/secret.txt",
    Path("~/materials/secret.txt").expanduser(),
    learningos / f"reading-memory/sessions/{os.environ['LOS_SESSION_ID']}.json",
    core / "generated/text-cache/doc1/p1.txt",
    core / "generated/material-search/idx.sqlite3",
    core / "generated/material-outlines/o.json",
    core / "generated/derived-state/d.json",
    core / "generated/summaries/doc1/pages-1-2/summary.md",
    core / "operations/ai-actions/requests/req-1/slice.md",
]
# Create future.md on host? Here test requests/.gitkeep vs non-gitkeep and existing tree.
for target in closed_files:
    try:
        target.read_text(encoding="utf-8")
        raise AssertionError(f"unexpectedly read closed target: {target}")
    except PermissionError as exc:
        assert exc.errno == errno.EPERM, (target, exc)

# requests/.gitkeep stays readable while non-.gitkeep request files hit EPERM.
assert (core / "operations/ai-actions/requests/.gitkeep").read_text(encoding="utf-8") == ""

# 2. Symlink in scratch pointing into closed materials/ fails with EPERM when read.
sym = scratch / "sym-secret.txt"
sym.symlink_to(learningos / "materials/secret.txt")
try:
    sym.read_text(encoding="utf-8")
    raise AssertionError("symlink bypass read closed materials/")
except PermissionError as exc:
    assert exc.errno == errno.EPERM

# 3. Hardlink into scratch pointing at closed materials/ is refused at creation or read with EPERM.
hard = scratch / "hard-secret.txt"
try:
    os.link(learningos / "materials/secret.txt", hard)
    try:
        hard.read_text(encoding="utf-8")
        raise AssertionError("hardlink bypass read closed materials/")
    except PermissionError as exc:
        assert exc.errno == errno.EPERM
except PermissionError as exc:
    assert exc.errno == errno.EPERM

# 4. LearningOS/ is write-denied; scratch is writable; public docs are readable.
for dest in (core / "hack.txt", learningos / "hack.txt"):
    try:
        dest.write_text("owned", encoding="utf-8")
        raise AssertionError(f"unexpectedly wrote {dest}")
    except PermissionError as exc:
        assert exc.errno == errno.EPERM
assert "PUBLIC_GREP_NEEDLE" in (core / "knowledge/garden/public.md").read_text(encoding="utf-8")

# 5. git grep (and rg when installed) runs from repository/ cleanly without hitting EPERM.
git_grep = subprocess.run(
    ["git", "-C", str(core), "grep", "-n", "PUBLIC_GREP_NEEDLE"],
    capture_output=True, text=True,
)
assert git_grep.returncode == 0, git_grep.stderr
assert "public.md" in git_grep.stdout

rg_bin = shutil.which("rg")
if rg_bin:
    rg_ok = subprocess.run([rg_bin, "PUBLIC_GREP_NEEDLE"], cwd=str(core), capture_output=True, text=True)
    assert rg_ok.returncode == 0, rg_ok.stderr
    rg_raw = subprocess.run(
        [rg_bin, "--no-ignore", "CANARY_TEXT_CACHE", str(core / "generated/text-cache")],
        capture_output=True, text=True,
    )
    assert rg_raw.returncode != 0
    assert "CANARY_TEXT_CACHE" not in rg_raw.stdout

# 6. stage.note.write sealed round-trip succeeds via LOS_GATE_SOCK despite write-denied LearningOS/.
py = str(core / ".venv/bin/python")
seal_py = str(core / "tools/seal_envelope.py")
check_rec = scratch / "check-rec.json"
env_out = scratch / "sealed.json"
payload = json.dumps({"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "text": "sandbox note"})
c_proc = subprocess.run(
    [py, seal_py, "--capability", "stage.note.write", "--payload", payload,
     "--key", "sb-k1", "--guards", "auto", "--check-out", str(check_rec), "--out", str(env_out)],
    cwd=str(core), capture_output=True, text=True,
)
assert c_proc.returncode == 0, c_proc.stderr
assert json.loads(check_rec.read_text(encoding="utf-8"))["ok"] is True
s_proc = subprocess.run(
    [py, seal_py, "--guards-from", str(check_rec), "--submit"],
    cwd=str(core), capture_output=True, text=True,
)
assert s_proc.returncode == 0, s_proc.stdout + s_proc.stderr
assert json.loads(s_proc.stdout)["ok"] is True

# 7. Unlisted command fails closed with exit 2.
denied = subprocess.run(
    [py, str(core / "tools/los.py"), "backup-manifest", "--json"],
    cwd=str(core), capture_output=True, text=True,
)
assert denied.returncode == 2
""",
        encoding="utf-8",
    )

    rc = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(probe_script), str(core)],
        session_id=S1,
    )
    assert rc == 0

    # Even if a child process tries reading a future non-.gitkeep file created mid-session, EPERM applies.
    future_req.write_text("CANARY_FUTURE_SLICE", encoding="utf-8")
    future_rc = study_launch.launch_study(
        core_root=core,
        command=[
            sys.executable,
            "-c",
            (
                "import errno, pathlib; "
                f"p = pathlib.Path({str(future_req)!r});\n"
                "try:\n  p.read_text()\n  raise SystemExit(9)\n"
                "except PermissionError as e:\n  raise SystemExit(0 if e.errno == errno.EPERM else 8)\n"
            ),
        ],
        session_id=S1,
    )
    assert future_rc == 0

    # Host ended_at recorded cleanly in finally.
    srow = json.loads((learningos / "reading-memory/sessions" / f"{S1}.json").read_text("utf-8"))
    assert srow.get("ended_at") is not None


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="macOS /usr/bin/sandbox-exec required")
def test_seatbelt_child_kill_and_launcher_sigkill_adopt_recovery_with_host_observations(
    mini_repo: Path, tmp_path: Path,
) -> None:
    core = _make_study_world(mini_repo)
    learningos = core.parent

    # 1. Child SIGKILL still triggers study_launch finally: session_end, making entry adoptable.
    kill_child_script = tmp_path / "kill_child.py"
    kill_child_script.write_text(
        f"""
import os, signal, subprocess, sys
core = {str(core)!r}
proc = subprocess.run(
    [core + "/.venv/bin/python", core + "/tools/los.py",
     "material-span", "--material", {BOOK!r}, "--pages", "pdf p. 1", "--extract"],
    cwd=core, capture_output=True, text=True,
)
assert proc.returncode == 0, proc.stderr
os.kill(os.getpid(), signal.SIGKILL)
""",
        encoding="utf-8",
    )
    rc_kill = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(kill_child_script)],
        session_id=S1,
    )
    assert rc_kill != 0
    s1_row = json.loads((learningos / "reading-memory/sessions" / f"{S1}.json").read_text("utf-8"))
    assert s1_row.get("ended_at") is not None

    adopt_script = tmp_path / "adopt_s1.py"
    adopt_script.write_text(
        f"""
import json, subprocess
core = {str(core)!r}
py, los = core + "/.venv/bin/python", core + "/tools/los.py"
adopted = subprocess.run([py, los, "material-card-settle", "--adopt", {S1!r}], cwd=core, capture_output=True, text=True)
assert adopted.returncode == 0, adopted.stderr
entry_id = json.loads(adopted.stdout)["entries"][0]["entry"]
settled = subprocess.run([py, los, "material-card-settle", entry_id, "--dismiss", "irrelevant", "--reason", "child killed cleanup"], cwd=core, capture_output=True, text=True)
assert settled.returncode == 0, settled.stderr
""",
        encoding="utf-8",
    )
    adopt_rc = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(adopt_script)],
        session_id=S2,
    )
    assert adopt_rc == 0
    assert list((learningos / "reading-memory/pending").glob("rd-*.json")) == []

    # 2. Ungraceful LAUNCHER SIGKILL leaves ended_at unset; host LOS_OBSERVATIONS drives ADOPT_IDLE
    # while child spoofing of LOS_OBSERVATIONS inside Seatbelt is ignored.
    t0 = datetime.fromisoformat("2026-11-12T10:00:00+01:00")
    t_idle = t0 + ADOPT_IDLE + timedelta(seconds=60)
    obs_start = tmp_path / "obs-start.yaml"
    obs_idle = tmp_path / "obs-idle.yaml"
    obs_spoof = tmp_path / "obs-spoof.yaml"
    obs_start.write_text(json.dumps({"now": t0.isoformat()}), encoding="utf-8")
    obs_idle.write_text(json.dumps({"now": t_idle.isoformat()}), encoding="utf-8")
    obs_spoof.write_text(json.dumps({"now": (t0 + timedelta(seconds=10)).isoformat()}), encoding="utf-8")

    s3 = "aaaaaaaa-7777-4777-8777-777777777777"
    s4 = "bbbbbbbb-8888-4888-8888-888888888888"
    ready_file = tmp_path / "launcher-ready.txt"
    wait_script = tmp_path / "wait_child.py"
    wait_script.write_text(
        f"""
import pathlib, subprocess, time
core = {str(core)!r}
proc = subprocess.run(
    [core + "/.venv/bin/python", core + "/tools/los.py",
     "material-span", "--material", {BOOK!r}, "--pages", "pdf p. 2", "--extract"],
    cwd=core, capture_output=True, text=True,
)
assert proc.returncode == 0, proc.stderr
pathlib.Path({str(ready_file)!r}).write_text("ready", encoding="utf-8")
time.sleep(30)
""",
        encoding="utf-8",
    )
    host_env_start = dict(os.environ, LOS_OBSERVATIONS=str(obs_start), PYTHONDONTWRITEBYTECODE="1")
    launcher = subprocess.Popen(
        [
            str(core / ".venv/bin/python"),
            str(core / "tools/study_launch.py"),
            "--root",
            str(core),
            "--session",
            s3,
            "--cmd",
            "--",
            sys.executable,
            str(wait_script),
        ],
        env=host_env_start,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 20.0
        while not ready_file.exists():
            assert launcher.poll() is None, launcher.stderr.read().decode("utf-8", "replace")
            assert time.monotonic() < deadline, "timed out waiting for launcher child readiness"
            time.sleep(0.1)
        os.kill(launcher.pid, signal.SIGKILL)
        launcher.wait(timeout=10)
    finally:
        # Clean up any orphaned sandboxed child from SIGKILLed launcher.
        try:
            os.killpg(launcher.pid, signal.SIGKILL)
        except OSError:
            pass

    s3_row = json.loads((learningos / "reading-memory/sessions" / f"{s3}.json").read_text("utf-8"))
    assert s3_row.get("ended_at") is None

    # Second launch sets host LOS_OBSERVATIONS=obs_idle; sandbox overrides LOS_OBSERVATIONS=obs_spoof.
    spoof_adopt_script = tmp_path / "spoof_adopt.py"
    spoof_adopt_script.write_text(
        f"""
import json, os, subprocess
core = {str(core)!r}
env = dict(os.environ, LOS_OBSERVATIONS={str(obs_spoof)!r})
py, los = core + "/.venv/bin/python", core + "/tools/los.py"
proc = subprocess.run([py, los, "material-card-settle", "--adopt", {s3!r}], cwd=core, env=env, capture_output=True, text=True)
assert proc.returncode == 0, proc.stderr
entry_id = json.loads(proc.stdout)["entries"][0]["entry"]
settled = subprocess.run([py, los, "material-card-settle", entry_id, "--dismiss", "irrelevant", "--reason", "idle recovery"], cwd=core, env=env, capture_output=True, text=True)
assert settled.returncode == 0, settled.stderr
""",
        encoding="utf-8",
    )
    host_env_idle = dict(os.environ, LOS_OBSERVATIONS=str(obs_idle), PYTHONDONTWRITEBYTECODE="1")
    idle_proc = subprocess.run(
        [
            str(core / ".venv/bin/python"),
            str(core / "tools/study_launch.py"),
            "--root",
            str(core),
            "--session",
            s4,
            "--cmd",
            "--",
            sys.executable,
            str(spoof_adopt_script),
        ],
        env=host_env_idle,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert idle_proc.returncode == 0, idle_proc.stderr
    assert list((learningos / "reading-memory/pending").glob("rd-*.json")) == []


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="macOS /usr/bin/sandbox-exec required")
def test_concurrent_multi_session_sandboxes_and_killed_broker_isolation(
    mini_repo: Path, tmp_path: Path,
) -> None:
    core = _make_study_world(mini_repo)

    # Launch two concurrent study sessions reading distinct PDF pages without interference.
    worker_a = tmp_path / "worker_a.py"
    worker_b = tmp_path / "worker_b.py"
    for idx, (worker, page) in enumerate(((worker_a, 3), (worker_b, 4)), start=1):
        worker.write_text(
            f"""
import json, os, subprocess
core = {str(core)!r}
out = {str(tmp_path / f"res-{idx}.json")!r}
proc = subprocess.run(
    [core + "/.venv/bin/python", core + "/tools/los.py",
     "material-span", "--material", {BOOK!r}, "--pages", "pdf p. {page}", "--extract"],
    cwd=core, capture_output=True, text=True,
)
assert proc.returncode == 0, proc.stderr
data = json.loads(proc.stdout)
with open(out, "w", encoding="utf-8") as fh:
    json.dump({{"sock": os.environ["LOS_GATE_SOCK"], "scratch": os.environ["LOS_SCRATCH_DIR"], "study": data["study"]}}, fh)
""",
            encoding="utf-8",
        )

    p1 = subprocess.Popen(
        [
            str(core / ".venv/bin/python"),
            str(core / "tools/study_launch.py"),
            "--root",
            str(core),
            "--session",
            S1,
            "--cmd",
            "--",
            sys.executable,
            str(worker_a),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p2 = subprocess.Popen(
        [
            str(core / ".venv/bin/python"),
            str(core / "tools/study_launch.py"),
            "--root",
            str(core),
            "--session",
            S2,
            "--cmd",
            "--",
            sys.executable,
            str(worker_b),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out1, err1 = p1.communicate(timeout=120)
    out2, err2 = p2.communicate(timeout=120)
    assert p1.returncode == 0, err1.decode("utf-8", "replace")
    assert p2.returncode == 0, err2.decode("utf-8", "replace")

    r1 = json.loads((tmp_path / "res-1.json").read_text("utf-8"))
    r2 = json.loads((tmp_path / "res-2.json").read_text("utf-8"))
    assert r1["sock"] != r2["sock"]
    assert r1["scratch"] != r2["scratch"]
    assert r1["study"]["session"] == S1
    assert r2["study"]["session"] == S2

    # Killed broker / bogus LOS_GATE_SOCK fails closed with exit 2 inside Seatbelt.
    bogus = Path(os.path.realpath(tempfile.mkdtemp(prefix="dead-", dir="/tmp"))) / "dead.sock"
    try:
        rc_dead = study_launch.launch_study(
            core_root=core,
            command=[
                "env",
                f"LOS_GATE_SOCK={bogus}",
                str(core / ".venv/bin/python"),
                str(core / "tools/los.py"),
                "status",
                "--json",
            ],
            session_id=S1,
        )
        assert rc_dead == 2
        assert "study broker unavailable" in (
            subprocess.run(
                [str(core / ".venv/bin/python"), str(core / "tools/los.py"), "status", "--json"],
                cwd=str(core),
                env=dict(os.environ, LOS_GATE_SOCK=str(bogus), PYTHONDONTWRITEBYTECODE="1"),
                capture_output=True,
                text=True,
                timeout=30,
            ).stderr
        )
    finally:
        shutil.rmtree(bogus.parent, ignore_errors=True)


def test_launcher_startup_failures_clean_up_resources_and_leave_session_recoverable(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Requirement 5: failures at every startup stage reap temp dirs, signal handler, and session."""
    core = _make_study_world(mini_repo)
    learningos = core.parent
    fake_sandbox = tmp_path / "fake-sandbox-exec"
    fake_sandbox.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_sandbox.chmod(0o755)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)

    created_dirs: list[Path] = []
    orig_mkdtemp = tempfile.mkdtemp

    def _tracking_mkdtemp(*args: object, **kwargs: object) -> str:
        path = Path(os.path.realpath(orig_mkdtemp(*args, **kwargs)))  # type: ignore[arg-type]
        created_dirs.append(path)
        return str(path)

    prev_sigterm = signal.getsignal(signal.SIGTERM)
    session_file = learningos / "reading-memory/sessions" / f"{S1}.json"

    def _assert_clean_and_recoverable() -> None:
        assert created_dirs, "expected launcher to allocate at least one temp directory"
        for temp_dir in created_dirs:
            assert not temp_dir.exists(), f"orphaned startup directory survived: {temp_dir}"
        created_dirs.clear()
        assert signal.getsignal(signal.SIGTERM) is prev_sigterm
        assert session_file.is_file()
        row = json.loads(session_file.read_text(encoding="utf-8"))
        assert row.get("ended_at") is not None
        # Session state remains immediately recoverable (touch start=True & session_end succeed).
        ReadingStore(core).touch(S1, start=True)
        reopened = json.loads(session_file.read_text(encoding="utf-8"))
        assert reopened.get("started_at") is not None
        assert reopened.get("ended_at") is None
        ReadingStore(core).session_end(S1)
        assert json.loads(session_file.read_text(encoding="utf-8")).get("ended_at") is not None

    # 1. Fault during stage_dir allocation (after session_started, scratch_dir, and sock_dir exist).
    monkeypatch.setattr(tempfile, "mkdtemp", _tracking_mkdtemp)
    orig_allocate = study_launch._allocate_outside_dir

    def _fail_stage_alloc(prefix: str, real_learningos: Path) -> Path:
        if prefix == "losb-":
            raise OSError("simulated stage allocation failure")
        return orig_allocate(prefix, real_learningos)

    with monkeypatch.context() as mp:
        mp.setattr(study_launch, "_allocate_outside_dir", _fail_stage_alloc)
        with pytest.raises(OSError, match="simulated stage allocation failure"):
            study_launch.launch_study(
                core_root=core,
                command=["/usr/bin/true"],
                session_id=S1,
                sandbox_exec=fake_sandbox,
                platform="darwin",
            )
    _assert_clean_and_recoverable()

    # 2. Fault during BrokerServer bind/startup (scratch_dir, sock_dir, stage_dir, and study.sb exist).
    class _FailingBrokerServer:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise OSError("simulated socket bind failure")

    with monkeypatch.context() as mp:
        mp.setattr(study_launch, "BrokerServer", _FailingBrokerServer)
        with pytest.raises(OSError, match="simulated socket bind failure"):
            study_launch.launch_study(
                core_root=core,
                command=["/usr/bin/true"],
                session_id=S1,
                sandbox_exec=fake_sandbox,
                platform="darwin",
            )
    _assert_clean_and_recoverable()

    # 3. Fault during sandbox Popen (after BrokerServer.start() and signal.signal() succeeded).
    orig_popen = subprocess.Popen

    def _fail_popen(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
        if isinstance(args[0], (list, tuple)) and str(fake_sandbox) == str(args[0][0]):
            raise OSError("simulated sandbox-exec launch failure")
        return orig_popen(*args, **kwargs)  # type: ignore[call-overload,no-any-return]

    with monkeypatch.context() as mp:
        mp.setattr(subprocess, "Popen", _fail_popen)
        with pytest.raises(OSError, match="simulated sandbox-exec launch failure"):
            study_launch.launch_study(
                core_root=core,
                command=["/usr/bin/true"],
                session_id=S1,
                sandbox_exec=fake_sandbox,
                platform="darwin",
            )
    _assert_clean_and_recoverable()

    # Subsequent session launches cleanly end-to-end with exit 0.
    monkeypatch.undo()
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    if DARWIN_SEATBELT:
        rc = study_launch.launch_study(
            core_root=core,
            command=[sys.executable, "-c", "print('recovered')"],
            session_id=S1,
        )
        assert rc == 0


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="macOS /usr/bin/sandbox-exec required")
def test_seatbelt_denies_host_stage_dir_and_allows_mediated_unit_plan_report_out(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Host broker stage dir stays Seatbelt-inaccessible while mediated --report-out succeeds."""
    core = _make_study_world(mini_repo)
    _compact_setup(core)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)

    draft_src = tmp_path / "draft-template.yaml"
    write_yaml(
        draft_src,
        _compact_revision(
            core,
            route_changes={
                "update": [
                    {
                        "route_id": "route-demo-book",
                        "fields": {"angle": "Seatbelt mediated revision angle."},
                    }
                ]
            },
        ),
    )

    probe = tmp_path / "seatbelt_stage_probe.py"
    probe.write_text(
        f"""
import errno, json, os, shutil, subprocess
from pathlib import Path

core = Path({str(core)!r})
tmp_root = Path({str(tmp_path)!r})
scratch = Path(os.environ["LOS_SCRATCH_DIR"])

# 1. Host stage dirs (losb-*) must be unreadable and unwritable from inside Seatbelt.
stage_dirs = list(tmp_root.glob("losb-*"))
assert stage_dirs, f"expected losb-* dir under {{tmp_root}}"
for sd in stage_dirs:
    try:
        list(sd.iterdir())
        raise AssertionError(f"Seatbelt allowed listing host stage dir {{sd}}")
    except PermissionError as exc:
        assert exc.errno == errno.EPERM
    try:
        (sd / "tamper.txt").write_text("tamper", encoding="utf-8")
        raise AssertionError(f"Seatbelt allowed writing host stage dir {{sd}}")
    except PermissionError as exc:
        assert exc.errno == errno.EPERM

# 2. Mediated unit-plan-revise --check --report-out writes report.json cleanly inside scratch.
draft = scratch / "rev.yaml"
shutil.copy2(Path({str(draft_src)!r}), draft)
report_out = scratch / "report.json"
ok = subprocess.run(
    [
        str(core / ".venv/bin/python"),
        str(core / "tools/los.py"),
        "unit-plan-revise",
        "unit-demo-l01",
        "--file",
        str(draft),
        "--check",
        "--report-out",
        str(report_out),
    ],
    cwd=str(core),
    capture_output=True,
    text=True,
)
assert ok.returncode == 0, ok.stderr
assert report_out.is_file()
assert json.loads(report_out.read_text(encoding="utf-8"))["ok"] is True

# 3. Symlink --report-out is refused with specific symlink/boundary error.
outside = tmp_root / "outside-target.json"
outside.write_text('{{"intact": true}}\\n', encoding="utf-8")
sym = scratch / "sym-report.json"
sym.symlink_to(outside)
bad = subprocess.run(
    [
        str(core / ".venv/bin/python"),
        str(core / "tools/los.py"),
        "unit-plan-revise",
        "unit-demo-l01",
        "--file",
        str(draft),
        "--check",
        "--report-out",
        str(sym),
    ],
    cwd=str(core),
    capture_output=True,
    text=True,
)
assert bad.returncode == 2
assert (
    "study mode blocks symlink" in bad.stderr
    or "outside the study boundary" in bad.stderr
), bad.stderr
""",
        encoding="utf-8",
    )

    rc = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(probe)],
        session_id=S1,
    )
    assert rc == 0
    assert (tmp_path / "outside-target.json").read_text(encoding="utf-8") == '{"intact": true}\n'


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="macOS /usr/bin/sandbox-exec required")
def test_study_launch_cwd_independence_from_core_parent_and_runtime_simulation(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    core = _make_study_world(mini_repo)
    learningos = core.parent
    outside = tmp_path / "outside-caller"
    outside.mkdir()
    real_core = Path(os.path.realpath(core))
    base_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

    # 1. Core-relative `--cmd -- .venv/bin/python tools/los.py ...` works from Core, Parent, and Outside.
    invocations = [
        (core, [str(core / ".venv/bin/python"), "tools/study_launch.py", "--cmd", "--",
                ".venv/bin/python", "tools/los.py", "status", "--json"]),
        (learningos, [str(core / ".venv/bin/python"), "repository/tools/study_launch.py",
                      "--cmd", "--", ".venv/bin/python", "tools/los.py", "status", "--json"]),
        (learningos, [str(core / ".venv/bin/python"), "repository/tools/study_launch.py",
                      "--root", "repository", "--cmd", "--",
                      ".venv/bin/python", "tools/los.py", "status", "--json"]),
        (outside, [str(core / ".venv/bin/python"), str(core / "tools/study_launch.py"),
                   "--root", str(core), "--cmd", "--",
                   ".venv/bin/python", "tools/los.py", "status", "--json"]),
        # Caller-relative executable/script paths from LearningOS/ parent keep working too.
        (learningos, [str(core / ".venv/bin/python"), "repository/tools/study_launch.py",
                      "--cmd", "--", "repository/.venv/bin/python",
                      "repository/tools/los.py", "status", "--json"]),
    ]
    for caller_dir, argv in invocations:
        proc = subprocess.run(
            argv, cwd=str(caller_dir), env=base_env,
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, (caller_dir, argv, proc.stderr)
        assert Path(os.path.realpath(json.loads(proc.stdout)["root"])) == real_core

    # 2. Parent-dir `--cmd -- sh -c` executes generated commands, `--omit-covered-text`,
    # seal_envelope, and preserves Seatbelt write refusal cleanly.
    s_flow = "abababab-1111-4111-8111-111111111111"
    shell_script = (
        ".venv/bin/python tools/los.py material-study-span --material _unsorted/review/book.pdf "
        "--pages 'pdf p. 1' --extract > \"$LOS_SCRATCH_DIR/span1.json\" && "
        "ENTRY=$(.venv/bin/python -c 'import json, os; print(json.load(open(os.environ[\"LOS_SCRATCH_DIR\"]+\"/span1.json\"))[\"study\"][\"reads\"][0][\"entry\"])') && "
        ".venv/bin/python tools/los.py material-card-settle \"$ENTRY\" --card "
        "'{\"paraphrase\":\"Evidence paragraph summary on page 1.\",\"kinds\":[\"statement\"],\"pointers\":[{\"page\":1,\"kind\":\"statement\",\"label\":\"claim\"}]}' >/dev/null && "
        ".venv/bin/python tools/los.py material-study-span --material _unsorted/review/book.pdf "
        "--pages 'pdf p. 1' --extract > \"$LOS_SCRATCH_DIR/covered_default.json\" && "
        ".venv/bin/python tools/los.py material-study-span --material _unsorted/review/book.pdf "
        "--pages 'pdf p. 1' --extract --omit-covered-text > \"$LOS_SCRATCH_DIR/covered_omitted.json\" && "
        ".venv/bin/python -c 'import json, os, pathlib\n"
        "s = os.environ[\"LOS_SCRATCH_DIR\"]\n"
        "d = json.loads(pathlib.Path(s + \"/covered_default.json\").read_text())\n"
        "o = json.loads(pathlib.Path(s + \"/covered_omitted.json\").read_text())\n"
        "assert \"Evidence paragraph on page 1.\" in d[\"span\"][\"spans\"][0][\"excerpt\"]\n"
        "assert \"excerpt_omitted\" not in d[\"span\"][\"spans\"][0]\n"
        "assert d[\"study\"][\"memory\"][0][\"review\"] == \"unreviewed\" and d[\"study\"][\"memory\"][0][\"coverage_evidence\"] is False\n"
        "assert o[\"span\"][\"spans\"][0][\"excerpt_omitted\"] == \"covered\" and \"excerpt\" not in o[\"span\"][\"spans\"][0]\n"
        "try:\n"
        "  pathlib.Path(\"../blocked.txt\").write_text(\"no\")\n"
        "  raise SystemExit(9)\n"
        "except PermissionError:\n"
        "  pass\n"
        "' && "
        ".venv/bin/python tools/seal_envelope.py --capability stage.note.write "
        "--payload '{\"unit_id\":\"unit-demo-l01\",\"stage_id\":\"stage-demo\",\"text\":\"from parent cwd\"}' "
        "--key parent-cwd-k1 --guards auto --submit >/dev/null"
    )
    flow_proc = subprocess.run(
        [
            str(core / ".venv/bin/python"),
            "repository/tools/study_launch.py",
            "--session", s_flow,
            "--cmd", "--", "sh", "-c", shell_script,
        ],
        cwd=str(learningos), env=base_env,
        capture_output=True, text=True, timeout=60,
    )
    assert flow_proc.returncode == 0, flow_proc.stderr

    # 3. `--runtime claude` launched from LearningOS/ (core.parent) starts in real_core, resolves
    # relative `--settings` cleanly, executes SessionStart/Stop hooks without shell operators, and
    # executes extracted save command directly from Stop hook output.
    ext_profile = tmp_path / "ext-profile"
    prof = subprocess.run(
        [str(core / ".venv/bin/python"), "repository/tools/study_hooks.py",
         "profile", "--out", str(ext_profile)],
        cwd=str(learningos), env=base_env, capture_output=True, text=True, timeout=60,
    )
    assert prof.returncode == 0, prof.stderr
    rel_settings = os.path.relpath(ext_profile / ".claude/settings.json", learningos)

    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    fake_claude = fakebin / "claude"
    fake_claude.write_text(
        f"""#!{sys.executable}
import errno, json, os, shlex, subprocess, sys
from pathlib import Path

assert Path(os.path.realpath(os.getcwd())) == Path({str(real_core)!r}), os.getcwd()
idx = sys.argv.index("--settings")
settings_path = Path(sys.argv[idx + 1])
assert settings_path.is_absolute() and settings_path.is_file(), settings_path
settings = json.loads(settings_path.read_text(encoding="utf-8"))
start_cmd = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
stop_cmd = settings["hooks"]["Stop"][0]["hooks"][0]["command"]
end_cmd = settings["hooks"]["SessionEnd"][0]["hooks"][0]["command"]

start_res = subprocess.run(["sh", "-c", start_cmd], input='{{}}', capture_output=True, text=True, check=True)
assert ".venv/bin/python tools/los.py bootstrap --brief" in start_res.stdout
assert "Note: study sandbox active:" in start_res.stdout
assert "no study sandbox active" not in start_res.stdout
assert "LOS_GATE_SOCK unset" not in start_res.stdout
assert os.environ["LOS_GATE_SOCK"] not in start_res.stdout

# Seatbelt read/write denials stay intact alongside active broker hooks.
for bad_read in (Path("../materials/secret.txt"),):
    try:
        bad_read.read_text(encoding="utf-8")
        raise AssertionError(f"Seatbelt failed to deny {{bad_read}}")
    except PermissionError as exc:
        assert exc.errno == errno.EPERM
try:
    Path("../blocked-during-hooks.txt").write_text("no", encoding="utf-8")
    raise AssertionError("Seatbelt failed to deny LearningOS write")
except PermissionError as exc:
    assert exc.errno == errno.EPERM

# Execute an unhooked/hooked study span and verify Stop gives standalone executable commands.
span = subprocess.run([".venv/bin/python", "tools/los.py", "material-study-span",
                       "--material", {BOOK!r}, "--pages", "pdf p. 2", "--extract"],
                      capture_output=True, text=True, check=True)
assert "Evidence paragraph on page 2." in span.stdout

stop1 = subprocess.run(["sh", "-c", stop_cmd], input='{{"stop_hook_active": false}}',
                       capture_output=True, text=True, check=True)
stop_obj = json.loads(stop1.stdout)
assert stop_obj["decision"] == "block"
reason = stop_obj["reason"]
for bad in (" | ", " || ", "; ", " && "):
    assert bad not in reason, bad
save_lines = [ln.strip() for ln in reason.splitlines()
              if ln.strip().startswith(".venv/bin/python tools/los.py material-card-settle ") and "--card" in ln]
assert len(save_lines) == 1, reason
filled = save_lines[0].replace(
    "'{{\\"paraphrase\\": \\"<what these pages do, in your words>\\", \\"kinds\\": [\\"<kind>\\"], \\"pointers\\": [{{\\"page\\": <page>, \\"kind\\": \\"<kind>\\", \\"label\\": \\"<what is there>\\"}}]}}'",
    shlex.quote(json.dumps({{"paraphrase": "Runtime simulation summary for page 2.", "kinds": ["statement"],
                            "pointers": [{{"page": 2, "kind": "statement", "label": "p2"}}]}})),
)
subprocess.run(["sh", "-c", filled], check=True)
stop2 = subprocess.run(["sh", "-c", stop_cmd], input='{{"stop_hook_active": false}}',
                       capture_output=True, text=True, check=True)
assert stop2.stdout.strip() == ""
end_res = subprocess.run(["sh", "-c", end_cmd], input='{{}}', capture_output=True, text=True, check=True)
assert end_res.stdout == ""
""",
        encoding="utf-8",
    )
    fake_claude.chmod(0o755)

    runtime_env = dict(base_env, PATH=f"{fakebin}{os.pathsep}{base_env.get('PATH', '')}")
    rt_session = "cdcdcdcd-2222-4222-8222-222222222222"
    rt_proc = subprocess.run(
        [
            str(core / ".venv/bin/python"),
            "repository/tools/study_launch.py",
            "--session", rt_session,
            "--runtime", "claude",
            "--", "--settings", rel_settings, "--setting-sources", "", "-p", "smoke",
        ],
        cwd=str(learningos),
        env=runtime_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert rt_proc.returncode == 0, rt_proc.stdout + rt_proc.stderr
    assert list((learningos / "reading-memory/pending").glob("rd-*.json")) == []
    rt_srow = json.loads((learningos / f"reading-memory/sessions/{rt_session}.json").read_text("utf-8"))
    assert rt_srow.get("ended_at") is not None

    # 4. Caller-relative `--cmd` executables (`repository/.venv/bin/python` from LearningOS/ and
    # `./caller-wrapper.sh` from outside/) still launch inside `real_core` so dynamically emitted
    # `.venv/bin/python tools/los.py ...` hints work identically while Seatbelt boundaries hold.
    rel_py_script = (
        "import json, os, shlex, subprocess, sys\n"
        "from pathlib import Path\n"
        f"assert Path(os.path.realpath(os.getcwd())) == Path({str(real_core)!r}), os.getcwd()\n"
        "assert sys.prefix != sys.base_prefix, (sys.prefix, sys.base_prefix)\n"
        "span = subprocess.run(\n"
        "    ['.venv/bin/python', 'tools/los.py', 'material-study-span',\n"
        f"     '--material', {BOOK!r}, '--pages', 'pdf p. 3', '--extract'],\n"
        "    capture_output=True, text=True, check=True,\n"
        ")\n"
        "span_obj = json.loads(span.stdout)\n"
        "next_action = span_obj['study']['next_action']\n"
        "save_lines = [\n"
        "    ln.strip() for ln in next_action.splitlines()\n"
        "    if ln.strip().startswith('.venv/bin/python tools/los.py material-card-settle ') and '--card' in ln\n"
        "]\n"
        "assert len(save_lines) == 1, next_action\n"
        "settle_cmd = save_lines[0].replace(\n"
        "    \"'{\\\"paraphrase\\\": \\\"<what these pages do, in your words>\\\", \\\"kinds\\\": [\\\"<kind>\\\"], \\\"pointers\\\": [{\\\"page\\\": <page>, \\\"kind\\\": \\\"<kind>\\\", \\\"label\\\": \\\"<what is there>\\\"}]}'\",\n"
        "    shlex.quote(json.dumps({'paraphrase': 'Page 3 caller-relative exec test.', 'kinds': ['statement'], 'pointers': [{'page': 3, 'kind': 'statement', 'label': 'p3'}]})),\n"
        ")\n"
        "subprocess.run(['sh', '-c', settle_cmd], check=True)\n"
        "try:\n"
        "    Path('../blocked-from-rel-cmd.txt').write_text('no', encoding='utf-8')\n"
        "    raise SystemExit(9)\n"
        "except PermissionError:\n"
        "    pass\n"
        "try:\n"
        "    Path('../materials/secret.txt').read_text(encoding='utf-8')\n"
        "    raise SystemExit(10)\n"
        "except PermissionError:\n"
        "    pass\n"
    )
    rel_exec_proc = subprocess.run(
        [
            str(core / ".venv/bin/python"),
            "repository/tools/study_launch.py",
            "--cmd",
            "--",
            "repository/.venv/bin/python",
            "-c",
            rel_py_script,
        ],
        cwd=str(learningos),
        env=base_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert rel_exec_proc.returncode == 0, rel_exec_proc.stdout + rel_exec_proc.stderr

    caller_wrapper = outside / "caller-wrapper.sh"
    caller_wrapper.write_text(
        f"""#!/bin/sh
set -eu
[ "$(cd . && pwd -P)" = "{real_core}" ]
.venv/bin/python tools/los.py status --json >/dev/null
if touch ../blocked-wrapper.txt 2>/dev/null; then
  exit 9
fi
exit 0
""",
        encoding="utf-8",
    )
    caller_wrapper.chmod(0o755)
    wrapper_proc = subprocess.run(
        [
            str(core / ".venv/bin/python"),
            str(core / "tools/study_launch.py"),
            "--root",
            str(core),
            "--cmd",
            "--",
            "./caller-wrapper.sh",
        ],
        cwd=str(outside),
        env=base_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert wrapper_proc.returncode == 0, wrapper_proc.stdout + wrapper_proc.stderr
