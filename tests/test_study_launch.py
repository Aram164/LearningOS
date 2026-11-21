"""Cross-platform SBPL/launcher checks and macOS Seatbelt boundary tests (PLAN-D Step 5)."""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
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
        "generated/.text-cache/doc1",
        "generated/material-search",
        "generated/material-outlines",
        "generated/derived-state",
        "knowledge/summaries/doc1/pages-1-2",
        "operations/ai-actions/requests/req-1",
        "knowledge/garden",
    ):
        (core / rel).mkdir(parents=True, exist_ok=True)
    (core / "generated/.text-cache/doc1/p1.txt").write_text("CANARY_TEXT_CACHE", encoding="utf-8")
    (core / "generated/material-search/idx.sqlite3").write_text("CANARY_SEARCH", encoding="utf-8")
    (core / "generated/material-outlines/o.json").write_text(
        json.dumps({"_generated": "generated; do not edit", "canary": "CANARY_OUTLINE"}),
        encoding="utf-8",
    )
    (core / "generated/derived-state/d.json").write_text(
        json.dumps({"_generated": "generated; do not edit", "canary": "CANARY_DERIVED"}),
        encoding="utf-8",
    )
    (core / "knowledge/summaries/doc1/pages-1-2/summary.md").write_text(
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
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    sb_first = study_launch.build_seatbelt_profile(core, home_dir=fake_home)
    sb_second = study_launch.build_seatbelt_profile(core, home_dir=fake_home)
    assert sb_first == sb_second
    assert "(version 1)" in sb_first
    assert "(allow default)" in sb_first
    assert "regex" not in sb_first
    # D-02: every write is denied first; Seatbelt's last matching rule wins, so
    # the allows come after the blanket deny and the re-denies after the allows.
    lines = sb_first.splitlines()
    assert lines.count("(deny file-write*)") == 1
    blanket = lines.index("(deny file-write*)")
    assert lines.index("(allow default)") < blanket
    first_allow = next(i for i, line in enumerate(lines) if line.startswith("(allow file-write*"))
    assert blanket < first_allow
    assert '(subpath "/dev")' in lines[first_allow] and '(subpath "/private/tmp")' in lines[first_allow]

    real_core = Path(os.path.realpath(core))
    real_learningos = Path(os.path.realpath(real_core.parent))
    expected_closed = [
        real_learningos / "materials",
        real_learningos / "reading-memory",
        real_core / "generated" / ".text-cache",
        real_core / "generated" / "material-search",
        real_core / "generated" / "material-outlines",
        real_core / "generated" / "derived-state",
        real_core / "knowledge" / "summaries",
        real_core / "operations" / "ai-actions" / "requests",
    ]
    assert [Path(os.path.realpath(p)) for p in protected_reads(real_core)] == expected_closed
    for closed in expected_closed:
        expected = f'(deny file-read* (subpath "{study_launch._sbpl_quote(str(closed))}"))'
        assert expected in sb_first, expected

    req_dir = Path(os.path.realpath(real_core / "operations/ai-actions/requests"))
    allow_gitkeep = (
        '(allow file-read* '
        f'(literal "{study_launch._sbpl_quote(str(req_dir))}") '
        f'(literal "{study_launch._sbpl_quote(str(req_dir / ".gitkeep"))}"))'
    )
    deny_req = f'(deny file-read* (subpath "{study_launch._sbpl_quote(str(req_dir))}"))'
    assert sb_first.index(deny_req) < sb_first.index(allow_gitkeep)

    deny_env = f'(deny file-read* (literal "{study_launch._sbpl_quote(str(real_learningos / ".env"))}"))'
    assert deny_env in sb_first

    deny_write = f'(deny file-write* (subpath "{study_launch._sbpl_quote(str(real_learningos))}"))'
    assert deny_write in sb_first
    assert lines.index(deny_write) > first_allow

    real_wrapper = real_learningos.parent
    for rel_instr in (
        "AGENTS.md", "CLAUDE.md", "CLAUDE.local.md", "GEMINI.md", ".mcp.json",
        ".claude", ".opencode", ".codex", ".gemini",
    ):
        assert f'(deny file-write* (subpath "{study_launch._sbpl_quote(str(real_wrapper / rel_instr))}"))' in sb_first

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    with_scratch = study_launch.build_seatbelt_profile(core, home_dir=fake_home, write_roots=(scratch,))
    allow_scratch = f'(subpath "{study_launch._sbpl_quote(os.path.realpath(scratch))}")'
    assert allow_scratch in with_scratch and allow_scratch not in sb_first

    # Claude Code's per-user temp folder is denied after /private/tmp is
    # allowed, with no exception: a sandboxed Claude Code keeps its temp root
    # in the scratch directory, which is allowed after the deny, wherever it
    # was allocated.
    deny_claude_tmp = f'(deny file-write* (subpath "{study_launch._sbpl_quote(str(study_launch._CLAUDE_USER_TMP))}"))'
    assert first_allow < lines.index(deny_claude_tmp)
    assert with_scratch.index(deny_claude_tmp) < with_scratch.index(allow_scratch)
    assert sb_first.count(study_launch._sbpl_quote(str(study_launch._CLAUDE_USER_TMP))) == 1

    real_home = Path(os.path.realpath(fake_home))
    deny_home_claude = f'(deny file-write* (subpath "{study_launch._sbpl_quote(str(real_home / ".claude"))}"))'
    assert deny_home_claude in sb_first
    # A --cmd launch (runtime=None) may write no runtime state at all.
    assert _allowed_writes(sb_first) == {("subpath", "/dev"), ("subpath", "/private/tmp")}
    for home_instr in (
        ".claude.json",
        ".claude.json.backup",
        ".zshrc",
        ".zshenv",
        ".bashrc",
        ".profile",
        ".codex/AGENTS.md",
        ".codex/config.toml",
        ".gemini/GEMINI.md",
        ".gemini/settings.json",
        ".codex/plugins",
        ".codex/prompts",
    ):
        assert f'(deny file-write* (subpath "{study_launch._sbpl_quote(str(real_home / home_instr))}"))' in sb_first
    # agy's settings, knowledge, MCP config and binaries are never allowed back.
    for agy_surface in (
        ".gemini/antigravity-cli/settings.json",
        ".gemini/antigravity-cli/knowledge",
        ".gemini/antigravity-cli/mcp",
        ".gemini/antigravity-cli/bin",
        ".gemini/config",
    ):
        assert study_launch._sbpl_quote(str(real_home / agy_surface)) + '"' not in sb_first, agy_surface


def _allowed_writes(profile: str) -> set[tuple[str, str]]:
    """Every ``(subpath|literal "path")`` a profile's write allows name."""
    allowed: set[tuple[str, str]] = set()
    for line in profile.splitlines():
        if line.startswith("(allow file-write*"):
            allowed.update(re.findall(r'\((subpath|literal) "((?:[^"\\]|\\.)*)"\)', line))
    return allowed


def test_profile_allows_only_the_launched_runtimes_state(tmp_path: Path) -> None:
    """Per-session homes (ADR-022 §3): each launch may write its own study home
    and, in the real home folder, only Codex's auth.json and agy/gemini's
    traced paths. Claude Code runs on the dedicated study token, writes nothing
    in $HOME (no Keychains or refresh locks), and ~/.config/learningos is read-
    and write-denied in every launch."""
    core = tmp_path / "LearningOS" / "repository"
    core.mkdir(parents=True)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    real_home = Path(os.path.realpath(fake_home))
    real_learningos = Path(os.path.realpath(core.parent))
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    q = study_launch._sbpl_quote
    common = {
        ("subpath", "/dev"),
        ("subpath", "/private/tmp"),
        ("subpath", q(os.path.realpath(scratch))),
    }
    keychain = ("subpath", q(str(real_home / "Library/Keychains")))
    gemini_shared = {
        ("subpath", q(str(real_home / rel))) for rel in (".gemini/tmp", ".gemini/history", ".npm/_logs")
    }
    agy_state = {
        ("subpath", q(str(real_home / rel))) for rel in study_launch._AGY_WRITABLE_SUBDIRS
    } | {("literal", q(str(real_home / rel))) for rel in study_launch._AGY_WRITABLE_FILES}

    profiles: dict[str | None, str] = {}
    homes: dict[str, Path] = {}
    for runtime in (None, "claude", "codex", "agy", "gemini"):
        home = None
        if runtime in study_launch.HOMED_RUNTIMES:
            home = study_launch.runtime_home_parent(real_home, real_learningos, runtime) / S1
            homes[runtime] = home
        profiles[runtime] = study_launch.build_seatbelt_profile(
            core, home_dir=fake_home, write_roots=(scratch,), runtime=runtime, runtime_home=home,
        )

    assert _allowed_writes(profiles[None]) == common
    assert _allowed_writes(profiles["claude"]) == common | {("subpath", q(str(homes["claude"])))}
    assert _allowed_writes(profiles["codex"]) == (
        common
        | {("subpath", q(str(homes["codex"]))), ("literal", q(str(real_home / ".codex/auth.json")))}
    )
    assert _allowed_writes(profiles["agy"]) == common | agy_state | gemini_shared | {keychain}
    assert _allowed_writes(profiles["gemini"]) == common | gemini_shared | {keychain}

    # The homes live outside the real runtime folders, under one folder per
    # checkout, and carry no space (both runtimes compose shell paths there).
    for runtime, home in homes.items():
        assert home.parent.parent.parent == real_home / ".local/state/learningos/study-runtimes"
        assert home.parent.name == runtime and " " not in str(home)

    # Claude Code keeps no keychain or refresh-lock allows, and every launch
    # read- and write-denies ~/.config/learningos.
    assert "Library/Keychains" not in profiles["claude"]
    for lock_rel in (".oauth_refresh.lock", ".storage-write.lock", ".claude.lock"):
        assert lock_rel not in profiles["claude"], lock_rel
    secrets_subpath = f'(subpath "{q(str(real_home / ".config/learningos"))}")'
    for runtime, profile in profiles.items():
        assert f"(deny file-read* {secrets_subpath})" in profile, runtime
        assert f"(deny file-write* {secrets_subpath})" in profile, runtime
    # The marker of every home, and Codex's login link itself, are denied last.
    for runtime, home in homes.items():
        lines = profiles[runtime].splitlines()
        home_allow = next(i for i, line in enumerate(lines) if f'(subpath "{q(str(home))}")' in line)
        marker_deny = f'(deny file-write* (literal "{q(str(home / study_launch.RUNTIME_HOME_MARKER_NAME))}"))'
        assert lines.index(marker_deny) > home_allow, runtime
    codex_lines = profiles["codex"].splitlines()
    link_deny = f'(deny file-write* (literal "{q(str(homes["codex"] / "auth.json"))}"))'
    assert codex_lines.index(link_deny) > codex_lines.index(
        f'(allow file-write* (literal "{q(str(real_home / ".codex/auth.json"))}"))'
    )
    assert f'(literal "{q(str(homes["claude"] / "auth.json"))}")' not in profiles["claude"]


def _write_fake_claude_study_token(home: Path, token: str = "sk-ant-oat01-fake-study-token") -> Path:
    secrets = home / ".config" / "learningos"
    secrets.mkdir(parents=True, exist_ok=True)
    secrets.chmod(0o700)
    token_file = secrets / "claude_study_token"
    token_file.write_text(f"{token}\n", encoding="utf-8")
    token_file.chmod(0o600)
    return token_file


def _fake_real_runtime_folders(home: Path) -> None:
    """A real home folder with the config keys the seed must and must not copy."""
    _write_fake_claude_study_token(home)
    (home / ".claude").mkdir(parents=True)
    (home / ".claude.json").write_text(json.dumps({
        "hasCompletedOnboarding": True,
        "lastOnboardingVersion": "2.1.250",
        "oauthAccount": {"emailAddress": "someone@example.invalid"},
        "mcpServers": {"x": {"command": "evil"}},
        "projects": {"/elsewhere": {"allowedTools": ["Bash"]}},
    }), encoding="utf-8")
    (home / ".claude" / "settings.json").write_text(json.dumps({
        "model": "opus",
        "effortLevel": "xhigh",
        "theme": "dark",
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "evil"}]}]},
        "permissions": {"allow": ["Bash(*)"]},
        "env": {"FOO": "bar"},
        "enabledPlugins": {"p@m": True},
    }), encoding="utf-8")
    (home / ".codex").mkdir()
    (home / ".codex" / "config.toml").write_text(
        'model = "broken-global"\npersonality = "pragmatic"\nservice_tier = "flex"\n'
        'notify = ["/bin/sh", "-c", "evil"]\n\n[mcp_servers.x]\ncommand = "evil"\n',
        encoding="utf-8",
    )
    (home / ".codex" / "auth.json").write_text('{"tokens": {"refresh_token": "r1"}}\n', encoding="utf-8")
    (home / ".codex" / "installation_id").write_text("inst-123\n", encoding="utf-8")


def test_runtime_home_seed_reuse_and_refusals(tmp_path: Path) -> None:
    real_home = Path(os.path.realpath(tmp_path)) / "home"
    real_home.mkdir()
    _fake_real_runtime_folders(real_home)
    learningos = Path(os.path.realpath(tmp_path)) / "LearningOS"
    core = learningos / "repository"
    core.mkdir(parents=True)
    core_paths = (core,)

    def prepare(runtime: str, session: str = S1) -> Path:
        return study_launch.prepare_runtime_home(
            study_launch.resolve_runtime_home(
                runtime=runtime, session_id=session, resume_runtime_id=None,
                home_dir=real_home, real_learningos=learningos,
            ),
            runtime=runtime, real_learningos=learningos, session_id=session,
            real_home=real_home, core_paths=core_paths,
        )

    claude_home = prepare("claude")
    assert claude_home == study_launch.runtime_home_parent(real_home, learningos, "claude") / S1
    for level in (claude_home, claude_home.parent, claude_home.parent.parent):
        assert (level.stat().st_mode & 0o777) == 0o700, level
    marker = claude_home / study_launch.RUNTIME_HOME_MARKER_NAME
    assert (marker.stat().st_mode & 0o777) == 0o600
    marker_data = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_data["runtime"] == "claude" and marker_data["learningos"] == str(learningos)
    global_config = json.loads((claude_home / ".claude.json").read_text(encoding="utf-8"))
    # Onboarding done and Core trusted, so an interactive launch asks nothing;
    # the account, MCP servers and other projects stay in the real config.
    assert global_config == {
        "hasCompletedOnboarding": True,
        "lastOnboardingVersion": "2.1.250",
        "projects": {str(core): {"hasTrustDialogAccepted": True}},
    }
    # Preferences carry over; hooks, permissions, env and plugins never do.
    settings = json.loads((claude_home / "settings.json").read_text(encoding="utf-8"))
    assert settings == {"model": "opus", "effortLevel": "xhigh", "theme": "dark"}
    # Reuse keeps what the runtime wrote, and the launcher writes nothing.
    (claude_home / "projects").mkdir()
    (claude_home / "settings.json").write_text('{"theme": "light"}\n', encoding="utf-8")
    assert prepare("claude") == claude_home
    assert json.loads((claude_home / "settings.json").read_text(encoding="utf-8")) == {"theme": "light"}

    codex_home = prepare("codex")
    config = (codex_home / "config.toml").read_text(encoding="utf-8")
    parsed = tomllib.loads(config)
    assert parsed == {
        "cli_auth_credentials_store": "file",
        "personality": "pragmatic",
        "service_tier": "flex",
        "projects": {str(core): {"trust_level": "trusted"}},
    }
    assert (codex_home / "installation_id").read_text(encoding="utf-8") == "inst-123\n"
    link = codex_home / "auth.json"
    assert link.is_symlink() and os.readlink(link) == str(real_home / ".codex" / "auth.json")
    # A refresh writes through the link, in place, into the one shared login.
    with open(link, "w", encoding="utf-8") as handle:
        handle.write('{"tokens": {"refresh_token": "r2"}}\n')
    assert "r2" in (real_home / ".codex" / "auth.json").read_text(encoding="utf-8")
    assert link.is_symlink()
    assert prepare("codex") == codex_home

    # Anything but the launcher's link at auth.json is refused, never repaired.
    link.unlink()
    link.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="must link to"):
        prepare("codex")
    link.unlink()
    link.symlink_to(tmp_path / "elsewhere.json")
    with pytest.raises(ValueError, match="must link to"):
        prepare("codex")
    link.unlink()
    assert prepare("codex") == codex_home and link.is_symlink()

    # A home of another checkout or runtime, without its marker, with loose
    # permissions, or replaced by a symlink, is refused.
    other = study_launch.runtime_home_parent(real_home, learningos, "claude") / S2
    other.mkdir(mode=0o700)
    with pytest.raises(ValueError, match="ownership marker"):
        prepare("claude", S2)
    (other / study_launch.RUNTIME_HOME_MARKER_NAME).write_text(
        json.dumps({**marker_data, "learningos": "/other/LearningOS"}), encoding="utf-8",
    )
    (other / study_launch.RUNTIME_HOME_MARKER_NAME).chmod(0o600)
    with pytest.raises(ValueError, match="belongs to LearningOS root"):
        prepare("claude", S2)
    (other / study_launch.RUNTIME_HOME_MARKER_NAME).write_text(
        json.dumps({**marker_data, "runtime": "codex"}), encoding="utf-8",
    )
    with pytest.raises(ValueError, match="belongs to runtime"):
        prepare("claude", S2)
    claude_home.chmod(0o755)
    with pytest.raises(ValueError, match="unsafe permissions"):
        prepare("claude")
    claude_home.chmod(0o700)
    moved = claude_home.with_name("moved")
    claude_home.rename(moved)
    claude_home.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ValueError, match="real directory"):
        prepare("claude")
    # Never inside LearningOS/.
    with pytest.raises(ValueError, match="outside LearningOS"):
        study_launch.prepare_runtime_home(
            core / "home", runtime="claude", real_learningos=learningos, session_id=S1,
            real_home=real_home, core_paths=core_paths,
        )


def test_resume_runtime_id_finds_the_home_holding_that_vendor_session(tmp_path: Path) -> None:
    real_home = Path(os.path.realpath(tmp_path)) / "home"
    real_home.mkdir()
    learningos = Path(os.path.realpath(tmp_path)) / "LearningOS"
    (learningos / "repository").mkdir(parents=True)
    vendor = "0f3c9d0e-1111-4222-8333-444444444444"

    def make_home(runtime: str, session: str) -> Path:
        return study_launch.prepare_runtime_home(
            study_launch.runtime_home_parent(real_home, learningos, runtime) / session,
            runtime=runtime, real_learningos=learningos, session_id=session,
            real_home=real_home, core_paths=(learningos / "repository",),
        )

    def resolve(runtime: str, resume: str | None, session: str) -> Path:
        return study_launch.resolve_runtime_home(
            runtime=runtime, session_id=session, resume_runtime_id=resume,
            home_dir=real_home, real_learningos=learningos,
        )

    # A plain launch (random study session) wrote the vendor's transcript.
    first = make_home("claude", S1)
    (first / "projects" / "-core").mkdir(parents=True)
    (first / "projects" / "-core" / f"{vendor}.jsonl").write_text("{}\n", encoding="utf-8")
    derived = study_launch.session_uuid_for_runtime("claude", vendor)
    assert resolve("claude", vendor, derived) == first
    # The derived home wins once it exists; --session never searches.
    assert resolve("claude", None, derived).name == derived
    make_home("claude", derived)
    assert resolve("claude", vendor, derived).name == derived
    shutil.rmtree(resolve("claude", None, derived))
    # Unknown or unsafe ids fall back to the derived home.
    assert resolve("claude", "no-such-session", derived).name == derived
    assert resolve("claude", "../projects", derived).name == derived
    # A copy without a valid marker is ignored; two marked homes claiming the
    # same session are refused instead of guessed between.
    stray = study_launch.runtime_home_parent(real_home, learningos, "claude") / "stray"
    shutil.copytree(first, stray)
    (stray / study_launch.RUNTIME_HOME_MARKER_NAME).unlink()
    assert resolve("claude", vendor, derived) == first
    planted = make_home("claude", S2)
    (planted / "projects" / "-other").mkdir(parents=True)
    (planted / "projects" / "-other" / f"{vendor}.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="several study homes"):
        resolve("claude", vendor, derived)

    # Codex keys its transcripts by thread id in the rollout file name.
    thread = "01a1d737-bf59-7fb2-9ef1-4b9cdd7ca01b"
    codex_first = make_home("codex", S1)
    rollout_dir = codex_first / "sessions" / "2026" / "11" / "20"
    rollout_dir.mkdir(parents=True)
    (rollout_dir / f"rollout-2026-11-20T10-00-00-{thread}.jsonl").write_text("{}\n", encoding="utf-8")
    codex_derived = study_launch.session_uuid_for_runtime("codex", thread)
    assert resolve("codex", thread, codex_derived) == codex_first
    # Homes of the other runtime are never searched.
    assert resolve("codex", vendor, codex_derived).name == codex_derived


def test_child_env_points_runtimes_at_their_study_homes(tmp_path: Path) -> None:
    host = {
        "PATH": "/usr/bin",
        "HOME": "/Users/x",
        "ANTHROPIC_API_KEY": "keep",
        "CLAUDE_CONFIG_DIR": "/Users/x/.claude",
        "CLAUDE_SECURESTORAGE_CONFIG_DIR": "/Users/x/.claude",
        "CLAUDE_CODE_TMPDIR": "/private/tmp",
        "CLAUDE_CODE_OAUTH_TOKEN": "host-oauth-token",
        "CODEX_HOME": "/Users/x/.codex",
    }
    scratch = tmp_path / "scratch"
    home = tmp_path / "home"

    def env_for(runtime: str | None, *, claude_token: str | None = None) -> dict[str, str]:
        return study_launch._build_child_env(
            host, runtime=runtime, sock_path=tmp_path / "gate.sock", session_id=S1,
            scratch_dir=scratch, child_cwd=tmp_path,
            runtime_env=(
                study_launch.runtime_home_env(runtime, home, scratch, claude_token=claude_token)
                if runtime
                else None
            ),
        )

    claude = env_for("claude", claude_token="study-tok")
    assert claude["CLAUDE_CONFIG_DIR"] == str(home)
    # Unset, not empty: secure storage resolves to this home's own item, which
    # does not exist, so a 401 never borrows Aram's shared login.
    assert "CLAUDE_SECURESTORAGE_CONFIG_DIR" not in claude
    assert claude["CLAUDE_CODE_OAUTH_TOKEN"] == "study-tok"
    assert claude["CLAUDE_CODE_TMPDIR"] == str(scratch) == claude["TMPDIR"]
    # The sandbox refuses writes to the install folder; an update can only fail.
    assert claude["DISABLE_AUTOUPDATER"] == "1"
    assert "CODEX_HOME" not in claude and "ANTHROPIC_API_KEY" not in claude
    codex = env_for("codex")
    assert codex["CODEX_HOME"] == str(home)
    assert not {
        "CLAUDE_CONFIG_DIR", "CLAUDE_SECURESTORAGE_CONFIG_DIR", "CLAUDE_CODE_TMPDIR",
        "CLAUDE_CODE_OAUTH_TOKEN",
    } & set(codex)
    for runtime in (None, "agy", "gemini"):
        assert not set(study_launch._RUNTIME_HOME_ENV) & set(env_for(runtime)), runtime


#: What the Claude desktop app's Claude Code session sets for its children
#: (names seen in a real session's environment, 2026-11-20), plus what a Codex
#: or agy session sets for its own. None of it may reach a study runtime.
_HOST_SESSION_ENV = (
    "CLAUDECODE",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_CHILD_NOTES_DIR",
    "CLAUDE_CODE_HOST_SESSION_ID",
    "CLAUDE_CODE_HOST_SHORT_TEMP_DIRS",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_SESSION_ATTENDED",
    "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_EXECPATH",
    "CLAUDE_CODE_USER_EMAIL",
    "CLAUDE_CODE_ACCOUNT_UUID",
    "CLAUDE_CODE_ORGANIZATION_UUID",
    "CLAUDE_CODE_DESKTOP_APP_VERSION",
    "CLAUDE_CODE_SIMPLE",
    "CLAUDE_CODE_DISABLE_CRON",
    "CLAUDE_CODE_EAGER_FLUSH",
    "CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES",
    "CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL",
    "CLAUDE_CODE_TERMINAL_MCP_TOOLS",
    "CLAUDE_PLUGIN_DATA",
    "CLAUDE_PID",
    "CLAUDE_AGENT_SDK_VERSION",
    "CLAUDE_AGENT_SDK_MCP_NO_PREFIX",
    "CLAUDE_EFFORT",
    "CODEX_COMPANION_SESSION_ID",
    "CODEX_COMPANION_TRANSCRIPT_PATH",
    "CODEX_THREAD_ID",
    "CODEX_REFRESH_TOKEN_URL_OVERRIDE",
    "CODEX_REVOKE_TOKEN_URL_OVERRIDE",
    "ANTIGRAVITY_LS_ADDRESS",
    "ANTIGRAVITY_CSRF_TOKEN",
    "ANTIGRAVITY_CONVERSATION_ID",
    "AGY_CLI_OSC7501",
    "GEMINI_CLI_HOME",
)


def test_child_env_is_scoped_to_runtime_and_drops_host_session_state(tmp_path: Path) -> None:
    """Default-deny by exact name and selected runtime: a launch from inside a
    Claude Code, Codex or agy session hands the study runtime none of that
    session's control channels, ids, or other vendors' credentials. Claude Code
    inherits model preferences only so its dedicated study token controls auth
    and endpoint, and --cmd (runtime=None) inherits no provider variables."""
    provider = {
        "ANTHROPIC_API_KEY": "sk-ant",
        "ANTHROPIC_AUTH_TOKEN": "auth-ant",
        "ANTHROPIC_BASE_URL": "https://proxy.example.invalid",
        "ANTHROPIC_CUSTOM_HEADERS": "Authorization: secret",
        "ANTHROPIC_MODEL": "claude-opus-5-5",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5",
        "OPENAI_API_KEY": "sk-openai",
        "OPENAI_BASE_URL": "https://api.openai.com",
        "CODEX_API_KEY": "sk-codex",
        "GEMINI_API_KEY": "gem",
        "GOOGLE_API_KEY": "google",
        "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/gcp.json",
        "GOOGLE_CLOUD_PROJECT": "proj",
        "AGY_ACCOUNT": "someone@example.invalid",
        "AGY_ADC_AUTH": "1",
    }
    system = {"PATH": "/usr/bin", "HOME": "/Users/x", "LANG": "en_US.UTF-8", "LC_ALL": "C",
              "XDG_CONFIG_HOME": "/Users/x/.config", "__CF_USER_TEXT_ENCODING": "0x1F5:0:0"}
    host = {
        **system,
        **provider,
        "CLAUDE_CODE_OAUTH_TOKEN": "host-oat",
        **{name: f"host-{name}" for name in _HOST_SESSION_ENV},
        "LOS_OBSERVATIONS": "/host/obs.yaml",
        "AWS_SECRET_ACCESS_KEY": "aws",
    }
    expected = {
        None: {},
        "claude": {
            "ANTHROPIC_MODEL": provider["ANTHROPIC_MODEL"],
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": provider["ANTHROPIC_DEFAULT_HAIKU_MODEL"],
        },
        "codex": {k: provider[k] for k in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY")},
        "gemini": {
            k: provider[k]
            for k in (
                "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS",
                "GOOGLE_CLOUD_PROJECT",
            )
        },
        "agy": {
            k: provider[k]
            for k in (
                "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS",
                "GOOGLE_CLOUD_PROJECT", "AGY_ACCOUNT", "AGY_ADC_AUTH",
            )
        },
    }
    launcher_set = {study_launch.GATE_SOCK_ENV, "LOS_SESSION_ID", "LOS_SCRATCH_DIR", "TMPDIR", "PWD",
                    "PYTHONDONTWRITEBYTECODE"}
    for runtime, allowed in expected.items():
        child = study_launch._build_child_env(
            host, runtime=runtime, sock_path=tmp_path / "gate.sock", session_id=S1,
            scratch_dir=tmp_path, child_cwd=tmp_path,
        )
        leaked = sorted(set(_HOST_SESSION_ENV) & set(child))
        assert leaked == [], (runtime, leaked)
        assert {k: child[k] for k in provider if k in child} == allowed, runtime
        assert {k: child[k] for k in system} == system, runtime
        assert set(child) - launcher_set == set(system) | set(allowed), runtime
        assert "CLAUDE_CODE_OAUTH_TOKEN" not in child, runtime
        assert "LOS_OBSERVATIONS" not in child and "AWS_SECRET_ACCESS_KEY" not in child, runtime
    # Unknown runtimes fail closed with no provider variables either.
    unknown = study_launch._build_child_env(
        host, runtime="other", sock_path=tmp_path / "gate.sock", session_id=S1,
        scratch_dir=tmp_path, child_cwd=tmp_path,
    )
    assert set(unknown) - launcher_set == set(system)
    # The SSH agent's variable is not forwarded either (its socket is denied too).
    with_agent = study_launch._build_child_env(
        {**host, "SSH_AUTH_SOCK": "/private/tmp/agent.sock"}, runtime="codex",
        sock_path=tmp_path / "gate.sock", session_id=S1, scratch_dir=tmp_path, child_cwd=tmp_path,
    )
    assert "SSH_AUTH_SOCK" not in with_agent


def test_claude_study_token_reader_and_fail_closed_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dedicated Claude study token: regular 0600 file in 0700 folder, no
    symlinks/FIFOs, fails closed before a home or reading-memory session
    exists, and never echoes file contents in error messages."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    secrets_dir = fake_home / ".config" / "learningos"
    token_path = secrets_dir / "claude_study_token"

    # 1. Missing folder/file -> names `claude setup-token` and path.
    with pytest.raises(ValueError) as missing:
        study_launch.read_claude_study_token(fake_home)
    assert "claude setup-token" in str(missing.value)
    assert "claude_study_token" in str(missing.value)

    # Through launch_study: exit 2, no home created, no reading-memory session.
    core = tmp_path / "LearningOS" / "repository"
    core.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))
    fake_sb = tmp_path / "sandbox-exec"
    fake_sb.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_sb.chmod(0o755)
    rc = study_launch.launch_study(
        core_root=core, command=["claude", "-p", "hi"], session_id=S1,
        sandbox_exec=fake_sb, platform="darwin", runtime="claude",
    )
    assert rc == 2
    assert not (fake_home / ".local").exists()
    assert not (core.parent / "reading-memory").exists()

    # 2. Symlink folder refused.
    (fake_home / ".config").mkdir()
    real_other = tmp_path / "other-dir"
    real_other.mkdir()
    secrets_dir.symlink_to(real_other)
    with pytest.raises(ValueError, match="real directory"):
        study_launch.read_claude_study_token(fake_home)
    secrets_dir.unlink()

    # 3. Unsafe folder permissions refused.
    secrets_dir.mkdir(mode=0o755)
    secrets_dir.chmod(0o755)
    with pytest.raises(ValueError, match="unsafe permissions"):
        study_launch.read_claude_study_token(fake_home)
    secrets_dir.chmod(0o700)

    # 4. Symlink token file refused.
    target_file = tmp_path / "target-tok"
    target_file.write_text("SECRET_DO_NOT_ECHO\n", encoding="utf-8")
    target_file.chmod(0o600)
    token_path.symlink_to(target_file)
    with pytest.raises(ValueError) as sym_err:
        study_launch.read_claude_study_token(fake_home)
    assert "SECRET_DO_NOT_ECHO" not in str(sym_err.value)
    assert "claude setup-token" in str(sym_err.value)
    token_path.unlink()

    # 5. FIFO does not hang (O_NONBLOCK) and is refused.
    os.mkfifo(token_path, 0o600)
    with pytest.raises(ValueError, match="regular file"):
        study_launch.read_claude_study_token(fake_home)
    token_path.unlink()

    # 6. Directory at token path refused.
    token_path.mkdir(mode=0o700)
    with pytest.raises(ValueError, match="regular file"):
        study_launch.read_claude_study_token(fake_home)
    token_path.rmdir()

    # 7. Unsafe permissions on token file refused (0644, 0640, 0604).
    token_path.write_text("SECRET_DO_NOT_ECHO\n", encoding="utf-8")
    for bad_mode in (0o644, 0o640, 0o604):
        token_path.chmod(bad_mode)
        with pytest.raises(ValueError) as mode_err:
            study_launch.read_claude_study_token(fake_home)
        assert "unsafe permissions" in str(mode_err.value)
        assert "SECRET_DO_NOT_ECHO" not in str(mode_err.value)
    token_path.chmod(0o600)

    # 8. Empty / whitespace, multiline, invalid UTF-8, oversized -> all refused without echoing bytes.
    token_path.write_text("   \n\t ", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        study_launch.read_claude_study_token(fake_home)

    token_path.write_text("SECRET_LINE_1\nSECRET_LINE_2\n", encoding="utf-8")
    with pytest.raises(ValueError) as multi_err:
        study_launch.read_claude_study_token(fake_home)
    assert "single line" in str(multi_err.value)
    assert "SECRET_LINE" not in str(multi_err.value)

    token_path.write_bytes(b"\xff\xfe\xfd")
    with pytest.raises(ValueError, match="UTF-8"):
        study_launch.read_claude_study_token(fake_home)

    token_path.write_text("x" * (study_launch._CLAUDE_STUDY_TOKEN_MAX_BYTES + 10), encoding="utf-8")
    with pytest.raises(ValueError, match="exceeds"):
        study_launch.read_claude_study_token(fake_home)

    # 9. Valid token strips leading/trailing whitespace and returns cleanly.
    token_path.write_text("  sk-ant-oat01-valid-study-token  \n", encoding="utf-8")
    assert study_launch.read_claude_study_token(fake_home) == "sk-ant-oat01-valid-study-token"


def _fake_codex_version(folder: Path, version: str) -> Path:
    """A stand-in codex that answers ``--version`` like codex-cli does."""
    fake = folder / f"codex-{version.replace(' ', '_') or 'none'}"
    fake.write_text(
        f"#!/bin/sh\n[ \"$1\" = --version ] && echo 'codex-cli {version}' && exit 0\nexit 1\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    return fake


def test_codex_launch_only_for_versions_that_save_login_in_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The study home's auth.json link is safe only where Codex saves the login
    in place (0.153.4, read in its source). Any other version is refused before
    a home exists or a session starts: fail closed."""
    assert study_launch.check_codex_saves_login_in_place(
        str(_fake_codex_version(tmp_path, "0.153.4"))
    ) == "0.153.4"
    with pytest.raises(ValueError) as refused:
        study_launch.check_codex_saves_login_in_place(str(_fake_codex_version(tmp_path, "0.154.0")))
    message = str(refused.value)
    for needed in ("codex 0.154.0", "rust-v0.154.0", "FileAuthStorage::save",
                   "codex-rs/login/src/auth/storage.rs", "_CODEX_IN_PLACE_AUTH_VERSIONS"):
        assert needed in message, needed
    for unreadable in ("", "garbage", "0.153.4", "codex-cli 0.153", "codex-cli v0.153.4",
                       "codex-cli 0.153.4-beta", "other-codex-cli 0.153.4",
                       "codex-cli 0.153.4 codex-cli 0.154.0"):
        broken = tmp_path / f"broken-{len(unreadable)}-{abs(hash(unreadable))}"
        broken.write_text(f"#!/bin/sh\necho '{unreadable}'\nexit 0\n", encoding="utf-8")
        broken.chmod(0o755)
        with pytest.raises(ValueError, match="no codex-cli version"):
            study_launch.check_codex_saves_login_in_place(str(broken))
    nonzero = tmp_path / "codex-nonzero"
    nonzero.write_text("#!/bin/sh\necho 'codex-cli 0.153.4'\nexit 1\n", encoding="utf-8")
    nonzero.chmod(0o755)
    with pytest.raises(ValueError, match="no codex-cli version"):
        study_launch.check_codex_saves_login_in_place(str(nonzero))
    with pytest.raises(ValueError, match="cannot read its version"):
        study_launch.check_codex_saves_login_in_place(str(tmp_path / "no-such-codex"))

    # Through launch_study: refused with exit 2, no home created, no session.
    core = tmp_path / "LearningOS" / "repository"
    core.mkdir(parents=True)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    fake_sb = tmp_path / "sandbox-exec"
    fake_sb.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_sb.chmod(0o755)
    unverified = _fake_codex_version(tmp_path, "0.160.1")
    rc = study_launch.launch_study(
        core_root=core, command=[str(unverified), "exec", "status"], session_id=S1,
        sandbox_exec=fake_sb, platform="darwin", runtime="codex",
    )
    assert rc == 2
    assert not (fake_home / ".local").exists()
    assert not (core.parent / "reading-memory").exists()


def test_prune_runtime_homes_removes_only_stale_launcher_homes(tmp_path: Path) -> None:
    """Homes unused for 30 days (Claude Code's own transcript retention) go at the
    next launch; the launched or resumed home, recent homes and anything the
    launcher does not own stay, and a link inside a pruned home is removed,
    never followed."""
    real_home = Path(os.path.realpath(tmp_path)) / "home"
    real_home.mkdir()
    _fake_real_runtime_folders(real_home)
    learningos = Path(os.path.realpath(tmp_path)) / "LearningOS"
    other_checkout = Path(os.path.realpath(tmp_path)) / "Other" / "LearningOS"
    for checkout in (learningos, other_checkout):
        (checkout / "repository").mkdir(parents=True)
    now = time.time()
    day = 86400

    def home(checkout: Path, runtime: str, session: str, age_days: float) -> Path:
        made = study_launch.prepare_runtime_home(
            study_launch.runtime_home_parent(real_home, checkout, runtime) / session,
            runtime=runtime, real_learningos=checkout, session_id=session, real_home=real_home,
            core_paths=(checkout / "repository",),
        )
        stamp = now - age_days * day
        os.utime(made / study_launch.RUNTIME_HOME_MARKER_NAME, (stamp, stamp))
        return made

    resumed = home(learningos, "claude", S1, 90)
    stale_claude = home(learningos, "claude", S2, 31)
    stale_codex = home(other_checkout, "codex", S1, 45)
    recent = home(learningos, "codex", S2, 29)
    unmarked = study_launch.runtime_home_parent(real_home, learningos, "claude") / "not-a-home"
    unmarked.mkdir()
    (unmarked / "keep.txt").write_text("x", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("must survive", encoding="utf-8")
    (stale_claude / "link-out").symlink_to(outside)

    removed = study_launch.prune_runtime_homes(real_home, keep=resumed, now=now)
    assert sorted(removed) == sorted([stale_claude, stale_codex])
    assert resumed.is_dir() and recent.is_dir() and unmarked.is_dir()
    assert not stale_claude.exists() and not stale_codex.exists()
    # The pruned Codex home's auth.json link was removed; the real login was not.
    assert (real_home / ".codex" / "auth.json").read_text(encoding="utf-8").startswith("{")
    assert outside.read_text(encoding="utf-8") == "must survive"
    # Reusing a home refreshes its last use, so a resume never looks stale.
    again = study_launch.prepare_runtime_home(
        resumed, runtime="claude", real_learningos=learningos, session_id=S1,
        real_home=real_home, core_paths=(learningos / "repository",),
    )
    assert time.time() - (again / study_launch.RUNTIME_HOME_MARKER_NAME).stat().st_mtime < 60
    # No homes root at all is not an error.
    assert study_launch.prune_runtime_homes(tmp_path / "nobody", keep=resumed, now=now) == []


def test_profile_denies_ssh_agent_sockets_by_real_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    core = tmp_path / "LearningOS" / "repository"
    core.mkdir(parents=True)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    real_home = Path(os.path.realpath(fake_home))
    q = study_launch._sbpl_quote
    profile = study_launch.build_seatbelt_profile(
        core, home_dir=fake_home, agent_sockets=(Path("/var/run/com.apple.launchd.x/Listeners"),),
    )
    # Seatbelt matches a socket by its resolved path, so the rule names /private/var.
    real_agent = os.path.realpath("/var/run/com.apple.launchd.x/Listeners")
    assert f'(deny network-outbound (remote unix-socket (path-literal "{q(real_agent)}")))' in profile
    assert f'(deny network-outbound (remote unix-socket (subpath "{q(str(real_home / ".ssh"))}")))' in profile
    assert "regex" not in profile
    # Only the agent's sockets: no blanket network rule.
    network = [line for line in profile.splitlines() if "network" in line]
    assert len(network) == 2 and all("unix-socket" in line for line in network)
    # The agent is found from the host's variable (and, on macOS, launchd).
    monkeypatch.setenv("SSH_AUTH_SOCK", "/var/run/com.apple.launchd.y/Listeners")
    found = study_launch.host_agent_sockets(os.environ)
    assert Path(os.path.realpath("/var/run/com.apple.launchd.y/Listeners")) in found
    # A relative value is no socket path; only launchd's (if any) remains.
    assert study_launch.host_agent_sockets({"SSH_AUTH_SOCK": "relative/agent"}) == (
        study_launch.host_agent_sockets({})
    )


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
    agy_argv = study_launch._resolve_runtime_command(
        runtime="agy", use_cmd=False, extra=["--output-format", "stream-json", "-p", "hi"],
    )
    assert agy_argv == [str(fake_bin), "--output-format", "stream-json", "-p", "hi"]

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
            "-e",
            "repository/tools/los.py",
            "-m",
            "repository/tools/los.py",
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
        "-e",
        "repository/tools/los.py",  # -e inline code string stays untouched
        "-m",
        "repository/tools/los.py",  # -m module spec stays untouched
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
    core / "generated/.text-cache/doc1/p1.txt",
    core / "generated/material-search/idx.sqlite3",
    core / "generated/material-outlines/o.json",
    core / "generated/derived-state/d.json",
    core / "knowledge/summaries/doc1/pages-1-2/summary.md",
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
        [rg_bin, "--no-ignore", "CANARY_TEXT_CACHE", str(core / "generated/.text-cache")],
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
    # Written from inside the sandbox, which denies every write outside its
    # scratch directory, /dev and /private/tmp (D-02).
    ready_file = Path(tempfile.mkdtemp(prefix="los-ready-", dir="/tmp")) / "launcher-ready.txt"
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
    # Results are written from inside the sandbox, which denies tmp_path (D-02).
    results = Path(tempfile.mkdtemp(prefix="los-res-", dir="/tmp"))
    for idx, (worker, page) in enumerate(((worker_a, 3), (worker_b, 4)), start=1):
        worker.write_text(
            f"""
import json, os, subprocess
core = {str(core)!r}
out = {str(results / f"res-{idx}.json")!r}
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

    r1 = json.loads((results / "res-1.json").read_text("utf-8"))
    r2 = json.loads((results / "res-2.json").read_text("utf-8"))
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

    (tmp_path / "outside-target.json").write_text('{"intact": true}\n', encoding="utf-8")
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
#    The host wrote the target; the sandbox may not write outside scratch (D-02).
outside = tmp_root / "outside-target.json"
try:
    outside.write_text("tampered", encoding="utf-8")
    raise AssertionError("Seatbelt allowed a write outside the scratch directory")
except PermissionError as exc:
    assert exc.errno == errno.EPERM
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
# Its own study home, never the real ~/.claude, running on the study token.
config_dir = Path(os.environ["CLAUDE_CONFIG_DIR"])
assert config_dir.parent.parent.parent == Path({str(Path(os.path.realpath(tmp_path)) / "home" / ".local/state/learningos/study-runtimes")!r}), config_dir
assert "CLAUDE_SECURESTORAGE_CONFIG_DIR" not in os.environ
assert os.environ["CLAUDE_CODE_OAUTH_TOKEN"] == "sk-ant-oat01-fake-study-token"
assert os.environ["CLAUDE_CODE_TMPDIR"] == os.environ["LOS_SCRATCH_DIR"]
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

    # A fake HOME, so the study home never lands in the real ~/.local/state.
    rt_home = Path(os.path.realpath(tmp_path)) / "home"
    rt_home.mkdir()
    _write_fake_claude_study_token(rt_home)
    runtime_env = dict(
        base_env,
        PATH=f"{fakebin}{os.pathsep}{base_env.get('PATH', '')}",
        HOME=str(rt_home),
    )
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


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="macOS /usr/bin/sandbox-exec required")
def test_persistent_scratch_and_missing_guards_from_hint(
    mini_repo: Path, tmp_path: Path,
) -> None:
    core = _make_study_world(mini_repo)
    py = str(core / ".venv/bin/python")
    seal_py = str(core / "tools/seal_envelope.py")
    payload = json.dumps({"unit_id": "unit-demo-l01", "stage_id": "stage-demo", "text": "persist"})

    # 1. --persist-scratch keeps check.json across two launches with the same session UUID.
    write_script = tmp_path / "t1.py"
    write_script.write_text(
        f"""import os, subprocess, sys
from pathlib import Path
rec = Path(os.environ["LOS_SCRATCH_DIR"]) / "check.json"
p = subprocess.run([
    {py!r}, {seal_py!r},
    "--capability", "stage.note.write",
    "--payload", {payload!r},
    "--key", "persist-k1",
    "--guards", "auto",
    "--check-out", str(rec),
], check=True)
assert rec.is_file()
""",
        encoding="utf-8",
    )
    read_script = tmp_path / "t2.py"
    read_script.write_text(
        f"""import json, os, subprocess
from pathlib import Path
rec = Path(os.environ["LOS_SCRATCH_DIR"]) / "check.json"
assert rec.is_file(), f"missing {{rec}}"
p = subprocess.run([
    {py!r}, {seal_py!r},
    "--guards-from", str(rec),
    "--submit",
], capture_output=True, text=True, check=True)
assert json.loads(p.stdout)["ok"] is True
""",
        encoding="utf-8",
    )

    rc1 = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S1,
        persist_scratch=True,
    )
    assert rc1 == 0
    expected_dir = study_launch._persistent_scratch_path(
        Path(os.path.realpath(core.parent)), S1
    )
    assert (expected_dir / "check.json").is_file()
    try:
        rc2 = study_launch.launch_study(
            core_root=core,
            command=[sys.executable, str(read_script)],
            session_id=S1,
            persist_scratch=True,
        )
        assert rc2 == 0
    finally:
        shutil.rmtree(expected_dir, ignore_errors=True)

    # 2. Dedicated --scratch-dir outside LearningOS/ initializes .learningos-scratch.json,
    #    retains files for the same session UUID, write-denies the marker in Seatbelt,
    #    and refuses other sessions, pre-existing unrelated dirs (without chmod), or symlinks.
    shared_scratch = tmp_path / "dedicated-scratch"
    rc3 = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S1,
        scratch_dir_override=shared_scratch,
    )
    assert rc3 == 0
    assert (shared_scratch / "check.json").is_file()
    marker = shared_scratch / study_launch.SCRATCH_MARKER_NAME
    marker_data = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_data["owner"] == "learningos-study-scratch"
    assert marker_data["session_id"] == S1
    assert marker_data["learningos"] == str(Path(os.path.realpath(core.parent)))
    assert (shared_scratch.stat().st_mode & 0o777) == 0o700
    assert (marker.stat().st_mode & 0o777) == 0o600

    # Same session can resume into the initialized directory, hits --guards auto hint on absent
    # --guards-from file, and cannot overwrite .learningos-scratch.json inside Seatbelt.
    resume_script = tmp_path / "resume_same_session.py"
    resume_script.write_text(
        f"""import errno, os, subprocess
from pathlib import Path
scratch = Path(os.environ["LOS_SCRATCH_DIR"])
try:
    (scratch / {study_launch.SCRATCH_MARKER_NAME!r}).write_text("tamper", encoding="utf-8")
    raise SystemExit(9)
except PermissionError as exc:
    assert exc.errno == errno.EPERM
absent = scratch / "does-not-exist.json"
p = subprocess.run([
    {py!r}, {seal_py!r},
    "--guards-from", str(absent),
    "--submit",
], capture_output=True, text=True)
assert p.returncode == 2
assert "re-run --check-out / --check" in p.stderr, p.stderr
""",
        encoding="utf-8",
    )
    rc4 = study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(resume_script)],
        session_id=S1,
        scratch_dir_override=shared_scratch,
    )
    assert rc4 == 0

    # Cross-session reuse of an initialized --scratch-dir or --persist-scratch dir fails closed.
    assert study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S2,
        scratch_dir_override=shared_scratch,
    ) == 2

    # Pre-existing unrelated user directory is refused BEFORE touching permissions or files.
    unrelated_dir = tmp_path / "existing-user-dir"
    unrelated_dir.mkdir(mode=0o755)
    unrelated_dir.chmod(0o755)
    (unrelated_dir / "keep.txt").write_text("do not expose\n", encoding="utf-8")
    assert study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S1,
        scratch_dir_override=unrelated_dir,
    ) == 2
    assert (unrelated_dir.stat().st_mode & 0o777) == 0o755
    assert not (unrelated_dir / study_launch.SCRATCH_MARKER_NAME).exists()

    # Foreign-checkout marker is refused without touching directory or child.
    foreign_scratch = tmp_path / "foreign-scratch"
    foreign_scratch.mkdir(mode=0o700)
    (foreign_scratch / study_launch.SCRATCH_MARKER_NAME).write_text(
        json.dumps({
            "schema": 1,
            "owner": "learningos-study-scratch",
            "learningos": str(tmp_path / "OtherLearningOS"),
            "session_id": S1,
        }),
        encoding="utf-8",
    )
    (foreign_scratch / study_launch.SCRATCH_MARKER_NAME).chmod(0o600)
    assert study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S1,
        scratch_dir_override=foreign_scratch,
    ) == 2

    assert study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S1,
        scratch_dir_override=core / "illegal-inside-core",
    ) == 2

    sym_scratch = tmp_path / "sym-scratch"
    sym_scratch.symlink_to(shared_scratch)
    assert study_launch.launch_study(
        core_root=core,
        command=[sys.executable, str(write_script)],
        session_id=S1,
        scratch_dir_override=sym_scratch,
    ) == 2


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="Darwin /usr/bin/sandbox-exec required")
def test_seatbelt_blocks_env_instruction_writes_and_filters_child_env(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-3.2-01 / D-02 / D-04: real Seatbelt blocks .env reads, wrapper/home configs, and secret env vars."""
    core = _make_study_world(mini_repo)
    learningos = core.parent
    wrapper = learningos.parent
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)

    env_file = learningos / ".env"
    env_file.write_text("TOP_SECRET_API_KEY=canary\n", encoding="utf-8")

    wrapper_agents = wrapper / "AGENTS.md"
    wrapper_agents.write_text("# Original wrapper instructions\n", encoding="utf-8")
    (wrapper / ".claude").mkdir(exist_ok=True)
    wrapper_claude_cfg = wrapper / ".claude" / "settings.json"
    wrapper_claude_cfg.write_text('{"safe": true}\n', encoding="utf-8")

    fake_home = tmp_path / "home"
    (fake_home / ".claude" / "projects" / "existing-proj" / "memory").mkdir(parents=True)
    (fake_home / ".claude" / "projects" / "existing-proj" / "memory" / "MEMORY.md").write_text("# Original\n", encoding="utf-8")
    (fake_home / ".claude" / "settings.json").write_text('{"safe": true}\n', encoding="utf-8")
    (fake_home / ".claude" / "CLAUDE.md").write_text("# Original\n", encoding="utf-8")
    (fake_home / ".claude.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")
    (fake_home / ".zshrc").write_text("# clean\n", encoding="utf-8")
    (fake_home / ".codex").mkdir(parents=True)
    (fake_home / ".codex" / "AGENTS.md").write_text("# Original\n", encoding="utf-8")
    (fake_home / ".codex" / "config.toml").write_text("model = 'x'\n", encoding="utf-8")
    (fake_home / ".gemini").mkdir(parents=True)
    (fake_home / ".gemini" / "GEMINI.md").write_text("# Original\n", encoding="utf-8")
    (fake_home / ".gemini" / "settings.json").write_text("{}\n", encoding="utf-8")

    obs_file = tmp_path / "host-obs.yaml"
    obs_file.write_text('{"now": "2026-11-15T10:00:00+01:00"}\n', encoding="utf-8")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("FOO_PROBE", "secret_probe_value")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret_aws_value")
    monkeypatch.setenv("LOS_OBSERVATIONS", str(obs_file))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "keep-provider-key")

    core_slug = study_launch._claude_project_slug(Path(os.path.realpath(core)))
    # Deny-by-default (D-02) refuses tmp_path itself; /private/tmp stays open.
    result_out = Path(tempfile.mkdtemp(prefix="los-probe-", dir="/tmp")) / "probe-result.json"
    # A stand-in for /private/tmp/claude-<uid>, so the probe never writes into
    # the real folder other Claude Code sessions use.
    fake_claude_tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="los-claude-tmp-", dir="/tmp")))
    monkeypatch.setattr(study_launch, "_CLAUDE_USER_TMP", fake_claude_tmp)
    (fake_home / ".gemini" / "antigravity-cli" / "conversations").mkdir(parents=True)
    (fake_home / ".gemini" / "config").mkdir(parents=True)
    study_token_file = _write_fake_claude_study_token(fake_home)
    probe = f"""
import json, os
from pathlib import Path

env_p = Path({str(env_file)!r})
results = {{}}

try:
    env_p.read_text()
    results["env_read"] = "ALLOWED"
except PermissionError:
    results["env_read"] = "DENIED"

try:
    Path({str(study_token_file)!r}).read_text()
    results["study_token_read"] = "ALLOWED"
except PermissionError:
    results["study_token_read"] = "DENIED"

sym_env = Path(os.environ["LOS_SCRATCH_DIR"]) / "env-link"
sym_env.symlink_to(env_p)
try:
    sym_env.read_text()
    results["env_sym_read"] = "ALLOWED"
except PermissionError:
    results["env_sym_read"] = "DENIED"

for label, target in [
    ("wrapper_agents", {str(wrapper_agents)!r}),
    ("wrapper_claude_cfg", {str(wrapper_claude_cfg)!r}),
    ("wrapper_opencode", {str(wrapper / ".opencode" / "opencode.json")!r}),
    ("home_claude_settings", {str(fake_home / ".claude" / "settings.json")!r}),
    ("home_claude_md", {str(fake_home / ".claude" / "CLAUDE.md")!r}),
    ("home_claude_commands", {str(fake_home / ".claude" / "commands" / "x.md")!r}),
    ("home_claude_json", {str(fake_home / ".claude.json")!r}),
    ("home_claude_json_backup", {str(fake_home / ".claude.json.backup")!r}),
    ("home_zshrc", {str(fake_home / ".zshrc")!r}),
    ("home_zshenv", {str(fake_home / ".zshenv")!r}),
    ("home_bashrc", {str(fake_home / ".bashrc")!r}),
    ("home_profile", {str(fake_home / ".profile")!r}),
    ("home_existing_proj_memory", {str(fake_home / ".claude" / "projects" / "existing-proj" / "memory" / "MEMORY.md")!r}),
    ("home_core_proj_memory", {str(fake_home / ".claude" / "projects" / core_slug / "memory" / "MEMORY.md")!r}),
    ("home_codex_agents", {str(fake_home / ".codex" / "AGENTS.md")!r}),
    ("home_codex_config", {str(fake_home / ".codex" / "config.toml")!r}),
    ("home_gemini_md", {str(fake_home / ".gemini" / "GEMINI.md")!r}),
    ("home_gemini_settings", {str(fake_home / ".gemini" / "settings.json")!r}),
    # Found writable by the 2026-11-20 S1 closure probe under the old denylist.
    ("wrapper_claude_md", {str(wrapper / "CLAUDE.md")!r}),
    ("wrapper_claude_local_md", {str(wrapper / "CLAUDE.local.md")!r}),
    ("wrapper_gemini_md", {str(wrapper / "GEMINI.md")!r}),
    ("wrapper_mcp_json", {str(wrapper / ".mcp.json")!r}),
    ("parent_claude_md", {str(wrapper.parent / "CLAUDE.md")!r}),
    ("agy_settings", {str(fake_home / ".gemini" / "antigravity-cli" / "settings.json")!r}),
    ("agy_knowledge", {str(fake_home / ".gemini" / "antigravity-cli" / "knowledge" / "ki.md")!r}),
    ("agy_mcp_cache", {str(fake_home / ".gemini" / "antigravity-cli" / "mcp" / "x" / "instructions.md")!r}),
    ("agy_mcp_config", {str(fake_home / ".gemini" / "config" / "mcp_config.json")!r}),
    # Whatever no rule names is denied too: binaries, login items, git config.
    ("home_local_bin", {str(fake_home / ".local" / "bin" / "claude")!r}),
    ("home_launch_agent", {str(fake_home / "Library" / "LaunchAgents" / "evil.plist")!r}),
    ("home_gitconfig", {str(fake_home / ".gitconfig")!r}),
    ("study_token_write", {str(study_token_file)!r}),
    ("codex_plugins", {str(fake_home / ".codex" / "plugins" / "cache" / "x" / "plugin.json")!r}),
    # The OAuth refresh lock's owner record steers an unsandboxed takeover.
    ("claude_refresh_lock_owner", {str(fake_home / ".claude" / ".oauth_refresh.lock.owner")!r}),
    # State other sessions source, run or read back as their own input.
    ("claude_other_transcript", {str(fake_home / ".claude" / "projects" / "existing-proj" / "s.jsonl")!r}),
    ("claude_projects_root", {str(fake_home / ".claude" / "projects" / "session.jsonl")!r}),
    ("claude_shell_snapshot", {str(fake_home / ".claude" / "shell-snapshots" / "snapshot-zsh-1.sh")!r}),
    ("claude_session_env", {str(fake_home / ".claude" / "session-env" / "s1" / "sessionstart-hook-1.sh")!r}),
    ("claude_tasks", {str(fake_home / ".claude" / "tasks" / "s1" / "1.json")!r}),
    ("claude_todos", {str(fake_home / ".claude" / "todos" / "s1.json")!r}),
    ("claude_tmp_other_session", {str(fake_claude_tmp / "-Users-x-other" / "s1" / "tasks" / "a.output")!r}),
    ("codex_models_cache", {str(fake_home / ".codex" / "models_cache.json")!r}),
    ("codex_memories", {str(fake_home / ".codex" / "memories" / "memory_summary.md")!r}),
    ("codex_queue", {str(fake_home / ".codex" / "queue_1.sqlite")!r}),
    ("codex_state", {str(fake_home / ".codex" / "state_5.sqlite")!r}),
    ("codex_computer_use", {str(fake_home / ".codex" / "computer-use" / "Client.app" / "Client")!r}),
    ("codex_shell_snapshot", {str(fake_home / ".codex" / "shell_snapshots" / "s1.sh")!r}),
    ("codex_arg0", {str(fake_home / ".codex" / "tmp" / "arg0" / "codex-arg0x" / "apply_patch")!r}),
    ("codex_tool_cache", {str(fake_home / ".codex" / "cache" / "codex_apps_tools" / "t.json")!r}),
    ("codex_plugin_staging", {str(fake_home / ".codex" / ".tmp" / "plugins" / "p" / "plugin.json")!r}),
    ("npm_npx", {str(fake_home / ".npm" / "_npx" / "abc" / "node_modules" / "pkg" / "index.js")!r}),
    ("npm_cacache", {str(fake_home / ".npm" / "_cacache" / "index-v5" / "aa" / "x")!r}),
]:
    p = Path(target)
    try:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        p.write_text("POISONED")
        results[label] = "ALLOWED"
    except PermissionError:
        results[label] = "DENIED"

# Claude Code refreshes its OAuth token under these proper-lockfile locks: a
# directory it creates, touches and removes. Nothing may be written inside.
for label, target in [
    ("claude_refresh_lock", {str(fake_home / ".claude" / ".oauth_refresh.lock")!r}),
    ("claude_storage_lock", {str(fake_home / ".claude" / ".storage-write.lock")!r}),
    ("claude_legacy_lock", {str(fake_home / ".claude.lock")!r}),
]:
    lock = Path(target)
    try:
        lock.mkdir()
        os.utime(lock)
    except PermissionError:
        results[label] = "DENIED"
        continue
    try:
        (lock / "planted.md").write_text("POISONED")
        inner = "ALLOWED"
    except PermissionError:
        inner = "DENIED"
    try:
        lock.rmdir()
        removed = "REMOVED"
    except OSError:
        removed = "KEPT"
    results[label] = f"LOCKED,{{removed}},inner-{{inner}}"

# Runtime state an earlier profile let every launch write in the real home
# folder. A --cmd launch now writes none of it; Claude Code and Codex write
# their own study home instead (test_seatbelt_runtime_homes_...).
for label, target in [
    ("codex_installation_id", {str(fake_home / ".codex" / "installation_id")!r}),
    ("codex_log", {str(fake_home / ".codex" / "log" / "codex-tui.log")!r}),
    ("codex_auth", {str(fake_home / ".codex" / "auth.json")!r}),
    ("codex_session", {str(fake_home / ".codex" / "sessions" / "rollout.jsonl")!r}),
    ("claude_tmp_core", {str(fake_claude_tmp / core_slug / "s1" / "tasks" / "a.output")!r}),
    ("claude_debug", {str(fake_home / ".claude" / "debug" / "s1.txt")!r}),
    ("home_proj_cache", {str(fake_home / ".claude" / "projects" / core_slug / "session.jsonl")!r}),
    ("agy_conversation", {str(fake_home / ".gemini" / "antigravity-cli" / "conversations" / "c.db")!r}),
    ("keychain", {str(fake_home / "Library" / "Keychains" / "probe.db")!r}),
    ("npm_logs", {str(fake_home / ".npm" / "_logs" / "probe.log")!r}),
]:
    p = Path(target)
    try:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        p.write_text("POISONED")
        results[label] = "ALLOWED"
    except PermissionError:
        results[label] = "DENIED"
scratch_note = Path(os.environ["LOS_SCRATCH_DIR"]) / "note.txt"
scratch_note.write_text("ok\\n")
results["scratch"] = scratch_note.read_text().strip()

results["foo_probe"] = "FOO_PROBE" in os.environ
results["aws_secret"] = "AWS_SECRET_ACCESS_KEY" in os.environ
results["los_obs_leaked"] = "LOS_OBSERVATIONS" in os.environ
results["anthropic_key"] = os.environ.get("ANTHROPIC_API_KEY")
results["gate_sock"] = bool(os.environ.get("LOS_GATE_SOCK"))

Path({str(result_out)!r}).write_text(json.dumps(results))
"""
    rc = study_launch.launch_study(
        core_root=core,
        command=[str(core / ".venv/bin/python"), "-c", probe],
        session_id=S1,
    )
    assert rc == 0
    data = json.loads(result_out.read_text(encoding="utf-8"))
    assert data["env_read"] == "DENIED"
    assert data["env_sym_read"] == "DENIED"
    assert data["study_token_read"] == "DENIED"
    for key in (
        "wrapper_agents",
        "wrapper_claude_cfg",
        "wrapper_opencode",
        "home_claude_settings",
        "home_claude_md",
        "home_claude_commands",
        "home_claude_json",
        "home_claude_json_backup",
        "home_zshrc",
        "home_zshenv",
        "home_bashrc",
        "home_profile",
        "home_existing_proj_memory",
        "home_core_proj_memory",
        "home_codex_agents",
        "home_codex_config",
        "home_gemini_md",
        "home_gemini_settings",
        "wrapper_claude_md",
        "wrapper_claude_local_md",
        "wrapper_gemini_md",
        "wrapper_mcp_json",
        "parent_claude_md",
        "agy_settings",
        "agy_knowledge",
        "agy_mcp_cache",
        "agy_mcp_config",
        "home_local_bin",
        "home_launch_agent",
        "home_gitconfig",
        "study_token_write",
        "codex_plugins",
        "claude_refresh_lock_owner",
        "claude_other_transcript",
        "claude_projects_root",
        "claude_shell_snapshot",
        "claude_session_env",
        "claude_tasks",
        "claude_todos",
        "claude_tmp_other_session",
        "codex_models_cache",
        "codex_memories",
        "codex_queue",
        "codex_state",
        "codex_computer_use",
        "codex_shell_snapshot",
        "codex_arg0",
        "codex_tool_cache",
        "codex_plugin_staging",
        "npm_npx",
        "npm_cacache",
        # Formerly allowed to every launch; a --cmd launch has no runtime.
        "codex_installation_id",
        "codex_log",
        "codex_auth",
        "codex_session",
        "claude_tmp_core",
        "claude_debug",
        "home_proj_cache",
        "agy_conversation",
        "keychain",
        "npm_logs",
        # Claude Code's refresh locks are a Claude Code launch's alone.
        "claude_refresh_lock",
        "claude_storage_lock",
        "claude_legacy_lock",
    ):
        assert data[key] == "DENIED", (key, data)
    for lock_rel in (".claude/.oauth_refresh.lock", ".claude/.storage-write.lock", ".claude.lock"):
        assert not (fake_home / lock_rel).exists(), lock_rel
    assert not (fake_claude_tmp / "-Users-x-other").exists()
    assert not (fake_claude_tmp / core_slug).exists()
    shutil.rmtree(fake_claude_tmp, ignore_errors=True)
    assert not (fake_home / ".local").exists(), "a --cmd launch creates no study home"
    assert data["scratch"] == "ok"
    for planted in ("CLAUDE.md", "CLAUDE.local.md", "GEMINI.md", ".mcp.json"):
        assert not (wrapper / planted).exists(), planted
    assert data["foo_probe"] is False
    assert data["aws_secret"] is False
    assert data["los_obs_leaked"] is False
    # --cmd receives no provider credentials either.
    assert data["anthropic_key"] is None
    assert data["gate_sock"] is True
    assert wrapper_agents.read_text(encoding="utf-8") == "# Original wrapper instructions\n"


#: Runs inside Seatbelt: tries each write a JSON spec names and records the
#: outcome (also the runtime variables it sees), so one launch probes many paths.
_WRITE_PROBE = r"""
import json, os, sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text())
results = {}

def attempt(label, action):
    try:
        action()
        results[label] = "ALLOWED"
    except PermissionError:
        results[label] = "DENIED"
    except OSError as exc:
        results[label] = f"ERR {exc.errno}"

def write(path):
    p = Path(path.replace("{scratch}", os.environ["LOS_SCRATCH_DIR"]))
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        pass
    p.write_text("PROBE")

for label, path in spec.get("reads", {}).items():
    attempt(label, lambda path=path: Path(path).read_text())
for label, path in spec.get("writes", {}).items():
    attempt(label, lambda path=path: write(path))
for label, path in spec.get("through_link", {}).items():
    def through(path=path):
        fd = os.open(path, os.O_WRONLY | os.O_TRUNC)
        os.write(fd, b'{"tokens": {"refresh_token": "rotated-in-sandbox"}}\n')
        os.close(fd)
    attempt(label, through)
for label, path in spec.get("unlinks", {}).items():
    attempt(label, lambda path=path: os.unlink(path))
for label, path in spec.get("renames_over", {}).items():
    def rename_over(path=path):
        src = Path(path).with_name("probe-replacement.tmp")
        src.write_text("{}")
        os.rename(src, path)
    attempt(label, rename_over)
for label, path in spec.get("locks", {}).items():
    lock = Path(path)
    try:
        lock.mkdir()
        os.utime(lock)
    except PermissionError:
        results[label] = "DENIED"
        continue
    try:
        (lock / "planted.md").write_text("POISONED")
        inner = "ALLOWED"
    except PermissionError:
        inner = "DENIED"
    try:
        lock.rmdir()
    except OSError:
        pass
    results[label] = f"LOCKED,inner-{inner}"
for name in spec.get("env", []):
    results[f"env:{name}"] = os.environ.get(name)
results["env:LOS_SCRATCH_DIR"] = os.environ.get("LOS_SCRATCH_DIR")
Path(spec["out"]).write_text(json.dumps(results))
"""


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="Darwin /usr/bin/sandbox-exec required")
def test_seatbelt_runtime_homes_and_real_home_rules(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per-session homes (ADR-022 §3): a Claude Code or Codex launch writes its
    own study home, and in the real home folder only its login refresh paths;
    an agy launch keeps its path rules, and no launch writes another runtime's
    state."""
    core = _make_study_world(mini_repo)
    real_learningos = Path(os.path.realpath(core.parent))
    # Not under /private/tmp, which every launch may write.
    fake_home = Path(os.path.realpath(tmp_path)) / "home"
    fake_home.mkdir()
    _fake_real_runtime_folders(fake_home)
    # The parents of the paths some runtime may write: Seatbelt allows the
    # path itself, not the folders above it.
    for parent in (".gemini/antigravity-cli/conversations", "Library/Keychains", ".npm/_logs"):
        (fake_home / parent).mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))
    # Host values must never reach the child: they would point it back at a
    # shared folder or login.
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(fake_home / ".claude"))
    monkeypatch.setenv("CLAUDE_SECURESTORAGE_CONFIG_DIR", str(fake_home / ".claude"))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "host-oauth-should-drop")
    monkeypatch.setenv("CODEX_HOME", str(fake_home / ".codex"))
    monkeypatch.setenv("CLAUDE_CODE_TMPDIR", "/private/tmp")
    fake_claude_tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="los-claude-tmp-", dir="/tmp")))
    monkeypatch.setattr(study_launch, "_CLAUDE_USER_TMP", fake_claude_tmp)
    core_slug = study_launch._claude_project_slug(Path(os.path.realpath(core)))
    probe_dir = Path(tempfile.mkdtemp(prefix="los-probe-", dir="/tmp"))
    real_auth = fake_home / ".codex" / "auth.json"
    study_token_path = fake_home / ".config" / "learningos" / "claude_study_token"
    homes = {
        runtime: study_launch.runtime_home_parent(fake_home, real_learningos, runtime) / S1
        for runtime in study_launch.HOMED_RUNTIMES
    }
    # Every launch's real-home targets: (label, path) of state that belongs to
    # one runtime or to no launch at all.
    real_targets = {
        "real_claude_transcript": fake_home / ".claude" / "projects" / core_slug / "s.jsonl",
        "real_claude_debug": fake_home / ".claude" / "debug" / "s.txt",
        "real_claude_json": fake_home / ".claude.json",
        "real_claude_tmp_core": fake_claude_tmp / core_slug / "s" / "tasks" / "a.output",
        "real_codex_session": fake_home / ".codex" / "sessions" / "rollout.jsonl",
        "real_codex_installation_id": fake_home / ".codex" / "installation_id",
        "real_codex_log": fake_home / ".codex" / "log" / "codex-tui.log",
        "real_codex_auth_lock": fake_home / ".codex" / "auth.json.lock",
        "real_agy_conversation": fake_home / ".gemini" / "antigravity-cli" / "conversations" / "c.db",
        "real_keychain": fake_home / "Library" / "Keychains" / "probe.db",
        "real_npm_logs": fake_home / ".npm" / "_logs" / "probe.log",
        "real_study_token": study_token_path,
    }
    other_home = study_launch.runtime_home_parent(fake_home, real_learningos, "claude") / S2
    # The probe stands in for codex; the version check reads this one.
    verified_codex = _fake_codex_version(tmp_path, "0.153.4")

    def run(runtime: str, spec: dict[str, object]) -> dict[str, object]:
        spec_path = probe_dir / f"{runtime}-spec.json"
        out = probe_dir / f"{runtime}-out.json"
        spec_path.write_text(json.dumps({**spec, "out": str(out)}), encoding="utf-8")
        rc = study_launch.launch_study(
            core_root=core,
            command=[str(core / ".venv/bin/python"), "-c", _WRITE_PROBE, str(spec_path)],
            session_id=S1,
            runtime=runtime,
            runtime_binary=str(verified_codex) if runtime == "codex" else None,
        )
        assert rc == 0, runtime
        result: dict[str, object] = json.loads(out.read_text(encoding="utf-8"))
        return result

    try:
        other_home.mkdir(parents=True, mode=0o700)
        claude = run("claude", {
            "reads": {"read_study_token": str(study_token_path)},
            "writes": {
                **{k: str(v) for k, v in real_targets.items()},
                "home_transcript": str(homes["claude"] / "projects" / core_slug / "s.jsonl"),
                "home_shell_snapshot": str(homes["claude"] / "shell-snapshots" / "snapshot-zsh-1.sh"),
                "home_global_config": str(homes["claude"] / ".claude.json"),
                "home_marker": str(homes["claude"] / study_launch.RUNTIME_HOME_MARKER_NAME),
                "other_study_home": str(other_home / "projects" / "x" / "s.jsonl"),
                "scratch_tmp_root": f"{{scratch}}/claude-{os.getuid()}/{core_slug}/s/tasks/a.output",
            },
            "locks": {
                "refresh_lock": str(fake_home / ".claude" / ".oauth_refresh.lock"),
                "storage_lock": str(fake_home / ".claude" / ".storage-write.lock"),
                "legacy_lock": str(fake_home / ".claude.lock"),
            },
            "env": [
                "CLAUDE_CONFIG_DIR",
                "CLAUDE_SECURESTORAGE_CONFIG_DIR",
                "CLAUDE_CODE_OAUTH_TOKEN",
                "CLAUDE_CODE_TMPDIR",
                "CODEX_HOME",
            ],
        })
        assert claude["env:CLAUDE_CONFIG_DIR"] == str(homes["claude"])
        assert claude["env:CLAUDE_SECURESTORAGE_CONFIG_DIR"] is None
        assert claude["env:CLAUDE_CODE_OAUTH_TOKEN"] == "sk-ant-oat01-fake-study-token"
        assert claude["env:CLAUDE_CODE_TMPDIR"] == claude["env:LOS_SCRATCH_DIR"]
        assert claude["env:CODEX_HOME"] is None
        for key in ("home_transcript", "home_shell_snapshot", "home_global_config", "scratch_tmp_root"):
            assert claude[key] == "ALLOWED", (key, claude)
        for key in (*real_targets, "read_study_token", "home_marker", "other_study_home",
                    "refresh_lock", "storage_lock", "legacy_lock"):
            assert claude[key] == "DENIED", (key, claude)

        original_auth = real_auth.read_text(encoding="utf-8")
        codex = run("codex", {
            "reads": {"read_study_token": str(study_token_path)},
            "writes": {
                **{k: str(v) for k, v in real_targets.items()},
                "home_session": str(homes["codex"] / "sessions" / "2026" / "11" / "20" / "rollout-x.jsonl"),
                "home_models_cache": str(homes["codex"] / "models_cache.json"),
                "home_installation_id": str(homes["codex"] / "installation_id"),
                "home_marker": str(homes["codex"] / study_launch.RUNTIME_HOME_MARKER_NAME),
                "claude_home": str(homes["claude"] / "projects" / "x.jsonl"),
            },
            "through_link": {"refresh_through_link": str(homes["codex"] / "auth.json")},
            "unlinks": {"unlink_link": str(homes["codex"] / "auth.json")},
            "renames_over": {"rename_over_link": str(homes["codex"] / "auth.json")},
            "env": ["CODEX_HOME", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_OAUTH_TOKEN"],
        })
        assert codex["env:CODEX_HOME"] == str(homes["codex"])
        assert codex["env:CLAUDE_CONFIG_DIR"] is None
        assert codex["env:CLAUDE_CODE_OAUTH_TOKEN"] is None
        for key in ("home_session", "home_models_cache", "home_installation_id", "refresh_through_link"):
            assert codex[key] == "ALLOWED", (key, codex)
        for key in (*real_targets, "read_study_token", "home_marker", "claude_home",
                    "unlink_link", "rename_over_link"):
            assert codex[key] == "DENIED", (key, codex)
        # The refresh landed in the one shared login, and the link survived.
        assert "rotated-in-sandbox" in real_auth.read_text(encoding="utf-8") != original_auth
        assert os.readlink(homes["codex"] / "auth.json") == str(real_auth)

        agy = run("agy", {
            "reads": {"read_study_token": str(study_token_path)},
            "writes": {k: str(v) for k, v in real_targets.items()},
            "locks": {"refresh_lock": str(fake_home / ".claude" / ".oauth_refresh.lock")},
            "env": ["CLAUDE_CONFIG_DIR", "CODEX_HOME", "CLAUDE_CODE_OAUTH_TOKEN"],
        })
        assert agy["env:CLAUDE_CONFIG_DIR"] is None and agy["env:CODEX_HOME"] is None
        assert agy["env:CLAUDE_CODE_OAUTH_TOKEN"] is None
        for key in ("real_agy_conversation", "real_keychain", "real_npm_logs"):
            assert agy[key] == "ALLOWED", (key, agy)
        for key in (k for k in real_targets if k not in ("real_agy_conversation", "real_keychain", "real_npm_logs")):
            assert agy[key] == "DENIED", (key, agy)
        assert agy["read_study_token"] == "DENIED"
        assert agy["refresh_lock"] == "DENIED"
        assert sorted(p.name for p in homes["claude"].parent.iterdir()) == sorted([S1, S2])
        assert not study_launch.runtime_home_parent(fake_home, real_learningos, "agy").exists()
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)
        shutil.rmtree(fake_claude_tmp, ignore_errors=True)


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="Darwin /usr/bin/sandbox-exec required")
def test_seatbelt_resumed_launches_return_to_their_runtime_home(
    mini_repo: Path, tmp_path: Path,
) -> None:
    """--resume-runtime-id and --persist-scratch keep working with per-session
    homes: a resumed launch finds the transcript a plain launch wrote, and a
    repeated one returns to the same home and scratch."""
    core = _make_study_world(mini_repo)
    real_core = Path(os.path.realpath(core))
    fake_home = Path(os.path.realpath(tmp_path)) / "home"
    fake_home.mkdir()
    _fake_real_runtime_folders(fake_home)
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    # Stand-ins for the CLIs: a "turn" appends to the vendor transcript in the
    # home the launcher chose, the way the real runtime would.
    (fakebin / "claude").write_text(
        f"""#!{sys.executable}
import json, os, sys
from pathlib import Path
home = Path(os.environ["CLAUDE_CONFIG_DIR"])
assert "CLAUDE_SECURESTORAGE_CONFIG_DIR" not in os.environ
assert os.environ["CLAUDE_CODE_OAUTH_TOKEN"] == "sk-ant-oat01-fake-study-token"
trust = json.loads((home / ".claude.json").read_text())["projects"]
assert trust[{str(real_core)!r}]["hasTrustDialogAccepted"] is True
args = sys.argv[1:]
vendor = args[args.index("--resume") + 1] if "--resume" in args else args[args.index("--session-id") + 1]
transcript = home / "projects" / {study_launch._claude_project_slug(real_core)!r} / f"{{vendor}}.jsonl"
if "--resume" in args:
    assert transcript.is_file(), f"resume found no transcript in {{home}}"
transcript.parent.mkdir(parents=True, exist_ok=True)
with transcript.open("a", encoding="utf-8") as handle:
    handle.write("{{}}\\n")
turns_file = Path(os.environ["LOS_SCRATCH_DIR"]) / "turns.txt"
with turns_file.open("a", encoding="utf-8") as handle:
    handle.write("x")
print(json.dumps({{"home": str(home), "turns": len(transcript.read_text().splitlines()),
                  "scratch_turns": len(turns_file.read_text())}}))
""",
        encoding="utf-8",
    )
    (fakebin / "codex").write_text(
        f"""#!{sys.executable}
import json, os, sys
from pathlib import Path
if sys.argv[1:] == ["--version"]:
    print("codex-cli 0.153.4")
    raise SystemExit(0)
home = Path(os.environ["CODEX_HOME"])
assert os.readlink(home / "auth.json") == {str(fake_home / ".codex" / "auth.json")!r}
assert 'trust_level = "trusted"' in (home / "config.toml").read_text()
args = sys.argv[1:]
day = home / "sessions" / "2026" / "11" / "20"
if "resume" in args:
    thread = args[args.index("resume") + 1]
    assert list(day.glob(f"rollout-*-{{thread}}.jsonl")), f"no rollout for {{thread}} in {{home}}"
else:
    day.mkdir(parents=True, exist_ok=True)
    (day / "rollout-2026-11-20T10-00-00-01a1d737-bf59-7fb2-9ef1-4b9cdd7ca01b.jsonl").write_text("{{}}\\n")
print(json.dumps({{"home": str(home)}}))
""",
        encoding="utf-8",
    )
    for fake in fakebin.iterdir():
        fake.chmod(0o755)
    env = {
        "PATH": f"{fakebin}{os.pathsep}/usr/bin:/bin",
        "HOME": str(fake_home),
        # Scratch, persisted scratch and stage folders land in this test's folder.
        "TMPDIR": str(tmp_path),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    launcher = [str(core / ".venv/bin/python"), str(core / "tools/study_launch.py")]
    vendor = "0f3c9d0e-1111-4222-8333-444444444444"

    def launch(*args: str) -> dict[str, object]:
        proc = subprocess.run(
            [*launcher, *args], cwd=str(core), env=env, capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        result: dict[str, object] = json.loads(proc.stdout.strip().splitlines()[-1])
        result["stderr"] = proc.stderr
        return result

    first = launch("--runtime", "claude", "--", "--session-id", vendor)
    # Retention: the first home was last used 40 days ago, and another home
    # 31 days ago. The resume must keep (and refresh) its own home anyway,
    # and remove the other.
    first_home = Path(str(first["home"]))
    stale = study_launch.prepare_runtime_home(
        first_home.with_name("12121212-4444-4444-8444-444444444444"),
        runtime="claude", real_learningos=Path(os.path.realpath(core.parent)), session_id=S2,
        real_home=fake_home, core_paths=(real_core,),
    )
    day = 86400
    for home, age in ((first_home, 40 * day), (stale, 31 * day)):
        old = time.time() - age
        os.utime(home / study_launch.RUNTIME_HOME_MARKER_NAME, (old, old))
    resumed = launch("--runtime", "claude", "--resume-runtime-id", vendor, "--persist-scratch",
                     "--", "--resume", vendor)
    assert first_home.is_dir() and not stale.exists()
    assert "removed 1 study home(s) unused for over 30 days" in str(resumed["stderr"])
    marker_age = time.time() - (first_home / study_launch.RUNTIME_HOME_MARKER_NAME).stat().st_mtime
    assert marker_age < 300, "a resumed launch refreshes its home's last use"
    again = launch("--runtime", "claude", "--resume-runtime-id", vendor, "--persist-scratch",
                   "--", "--resume", vendor)
    assert first["home"] == resumed["home"] == again["home"]
    assert (first["turns"], resumed["turns"], again["turns"]) == (1, 2, 3)
    # --persist-scratch keys the scratch by the derived session, as before.
    assert (resumed["scratch_turns"], again["scratch_turns"]) == (1, 2)
    assert len(list(Path(tmp_path).glob("los-study-scratch-*"))) == 1
    # A study session started with --session returns to its own home.
    named = "abababab-3333-4333-8333-333333333333"
    n1 = launch("--runtime", "claude", "--session", named, "--", "--session-id", vendor)
    n2 = launch("--runtime", "claude", "--session", named, "--", "--resume", vendor)
    assert n1["home"] == n2["home"] != first["home"] and Path(str(n1["home"])).name == named

    thread = "01a1d737-bf59-7fb2-9ef1-4b9cdd7ca01b"
    c1 = launch("--runtime", "codex", "--", "exec", "status")
    c2 = launch("--runtime", "codex", "--resume-runtime-id", thread, "--", "exec", "resume", thread)
    assert c1["home"] == c2["home"]


@pytest.mark.skipif(not DARWIN_SEATBELT, reason="Darwin /usr/bin/sandbox-exec required")
def test_seatbelt_denies_ssh_agent_sockets_keeps_the_study_gate(
    mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inside the sandbox, the host's SSH agent and every socket under ~/.ssh
    refuse a connect, also through a link, while the study gate and any other
    unix socket still connect. Only connects: nothing is ever sent."""
    import socket
    import threading

    core = _make_study_world(mini_repo)
    # Short paths: a unix socket path must fit in 104 bytes.
    base = Path(os.path.realpath(tempfile.mkdtemp(prefix="losk-", dir="/tmp")))
    fake_home = base / "h"
    paths = {
        "agent": base / "a" / "Listeners",
        "ssh_dir_agent": fake_home / ".ssh" / "agent" / "s.x.agent.y",
        "other": base / "o" / "other.sock",
    }
    servers: list[socket.socket] = []
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        server = socket.socket(socket.AF_UNIX)
        server.bind(str(path))
        server.listen(8)
        servers.append(server)

    def serve(server: socket.socket) -> None:
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            conn.close()

    for server in servers:
        threading.Thread(target=serve, args=(server,), daemon=True).start()
    host_link = base / "o" / "agent-hardlink"
    os.link(paths["agent"], host_link)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("SSH_AUTH_SOCK", str(paths["agent"]))
    result_out = base / "result.json"
    probe = f"""
import json, os, socket, subprocess
from pathlib import Path
targets = {{k: v for k, v in {({k: str(v) for k, v in paths.items()})!r}.items()}}
targets["agent_host_hardlink"] = {str(host_link)!r}
targets["agent_via_tmp_alias"] = {str(paths["agent"]).replace("/private/tmp/", "/tmp/", 1)!r}
targets["gate"] = os.environ["LOS_GATE_SOCK"]
results = {{"ssh_auth_sock_env": os.environ.get("SSH_AUTH_SOCK")}}
for name, path in targets.items():
    s = socket.socket(socket.AF_UNIX)
    try:
        s.connect(path)
        results[name] = "CONNECTED"
    except OSError as exc:
        results[name] = f"ERR {{exc.errno}}"
    finally:
        s.close()
try:
    os.link(targets["agent"], os.path.join(os.environ["LOS_SCRATCH_DIR"], "agent-link"))
    results["hardlink_in_sandbox"] = "LINKED"
except OSError as exc:
    results["hardlink_in_sandbox"] = f"ERR {{exc.errno}}"
status = subprocess.run([".venv/bin/python", "tools/los.py", "status", "--json"],
                        capture_output=True, text=True)
results["gate_call_exit"] = status.returncode
Path({str(result_out)!r}).write_text(json.dumps(results))
"""
    try:
        rc = study_launch.launch_study(
            core_root=core,
            command=[str(core / ".venv/bin/python"), "-c", probe],
            session_id=S1,
        )
        assert rc == 0
        data = json.loads(result_out.read_text(encoding="utf-8"))
        assert data["ssh_auth_sock_env"] is None, data
        for denied in ("agent", "ssh_dir_agent", "agent_host_hardlink", "agent_via_tmp_alias"):
            assert data[denied] == "ERR 1", (denied, data)
        assert data["hardlink_in_sandbox"] == "ERR 1", data
        assert data["other"] == "CONNECTED", data
        assert data["gate"] == "CONNECTED", data
        assert data["gate_call_exit"] == 0, data
    finally:
        for server in servers:
            server.close()
        shutil.rmtree(base, ignore_errors=True)


def test_launcher_child_starts_in_new_session_for_group_cleanup() -> None:
    """Descendants share the launcher child's process group, so group
    termination in launch_study reaches them (Phase 2 hardening)."""
    import inspect

    source = inspect.getsource(study_launch.launch_study)
    assert "start_new_session=True" in source
    assert "os.killpg" in source
