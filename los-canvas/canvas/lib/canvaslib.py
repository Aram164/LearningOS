"""Shared helpers for the LearningOS testing canvas.

Everything here runs *against* the isolated clone. Nothing writes to the
operator's real tree: the canvas root is a temp directory, the synthetic
worlds are built inside it, and every write goes through the gateway.

The library is deliberately thin. It is a driver, not a test framework:
it knows how to run `los` in a world, how to seal and apply an envelope,
and how to record what happened.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

CANVAS_ROOT = Path(__file__).resolve().parent.parent.parent
CORE_CLONE = CANVAS_ROOT / "LearningOS" / "repository"
UI_CLONE = CANVAS_ROOT / "LearningOS" / "obsidian-ui"
LOS = CORE_CLONE / "tools" / "los.py"
VENV_PY = CORE_CLONE / ".venv" / "bin" / "python"

#: The synthetic world builder lives in the clone's test suite: it is the
#: system's own characterization world (fixture book, demo module, inbox
#: drops, garden seeds, paths, abilities, goals) and contains no operator
#: data. Copying it is what makes the canvas synthetic.
TESTS_DIR = CORE_CLONE / "tests"


@dataclass
class Run:
    """One `los` invocation and everything observable about it."""

    argv: list[str]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def json(self) -> object:
        """Parsed stdout, or None when the command printed something else."""
        text = self.stdout.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def as_record(self) -> dict:
        return {
            "argv": self.argv,
            "exit_code": self.exit_code,
            "stdout": self.stdout[-4000:],
            "stderr": self.stderr[-4000:],
        }


@dataclass
class World:
    """A synthetic LearningOS world plus the driver that acts on it."""

    root: Path
    session_id: str
    observations: Path | None = None
    notes: list[str] = field(default_factory=list)
    log: list[Run] = field(default_factory=list)

    # -- running -----------------------------------------------------------
    def los(self, *args: str, stdin: str | None = None,
            timeout: int = 180) -> Run:
        env = dict(os.environ)
        env["TZ"] = "Europe/Berlin"
        env["LOS_SESSION_ID"] = self.session_id
        proc = subprocess.run(
            [str(VENV_PY), str(LOS), "--root", str(self.root), *args],
            capture_output=True, text=True, input=stdin, timeout=timeout,
            env=env, cwd=str(self.root),
        )
        run = Run(list(args), proc.returncode, proc.stdout, proc.stderr)
        self.log.append(run)
        return run

    def json(self, *args: str, **kw) -> object:
        run = self.los(*args, **kw)
        return run.json

    def los_tool(self, tool: str, *args: str, timeout: int = 300) -> Run:
        """Run one of the clone's `tools/*.py` scripts against this world."""
        env = dict(os.environ)
        env["TZ"] = "Europe/Berlin"
        proc = subprocess.run(
            [str(VENV_PY), str(CORE_CLONE / "tools" / tool),
             "--root", str(self.root), *args],
            capture_output=True, text=True, timeout=timeout, env=env,
            cwd=str(self.root),
        )
        run = Run([tool, *args], proc.returncode, proc.stdout, proc.stderr)
        self.log.append(run)
        return run

    # -- writing -----------------------------------------------------------
    def seal(self, capability: str, payload: dict, key: str, *,
             request_id: str | None = None, channel: str = "operator",
             approval_kind: str = "operator-approval",
             guards: str = "auto",
             revisions: dict[str, int] | None = None,
             out: Path | None = None) -> Run:
        """Seal a GatewayEnvelopeV2 for one capability."""
        payload_file = self.scratch(f"payload-{key}.json")
        payload_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        out = out or self.scratch(f"envelope-{key}.json")
        argv = [
            str(VENV_PY), str(CORE_CLONE / "tools" / "seal_envelope.py"),
            "--root", str(self.root),
            "--capability", capability,
            "--payload", f"@{payload_file}",
            "--key", key,
            "--channel", channel,
            "--approval-kind", approval_kind,
            "--session-id", self.session_id,
            "--out", str(out),
        ]
        if guards:
            argv += ["--guards", guards]
        if request_id:
            argv += ["--request-id", request_id]
        for artifact, revision in sorted((revisions or {}).items()):
            argv += ["--revision", f"{artifact}={revision}"]
        env = dict(os.environ, TZ="Europe/Berlin")
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=300, env=env, cwd=str(self.root))
        run = Run(["seal", capability, key], proc.returncode, proc.stdout, proc.stderr)
        self.log.append(run)
        return run

    def apply(self, capability: str, envelope: Path, *,
              replay_only: bool = False) -> Run:
        argv = ["capability", capability, "--payload-file", str(envelope)]
        if replay_only:
            argv.append("--replay-only")
        return self.los(*argv)

    def write(self, capability: str, payload: dict, key: str, *,
              request_id: str | None = None, channel: str = "operator",
              approval_kind: str = "operator-approval",
              guards: str = "auto",
              revisions: dict[str, int] | None = None) -> tuple[Run, Run]:
        """Seal then apply. Returns (seal_run, apply_run)."""
        seal = self.seal(capability, payload, key, request_id=request_id,
                         channel=channel, approval_kind=approval_kind,
                         guards=guards, revisions=revisions)
        if seal.exit_code != 0:
            return seal, seal
        envelope = self.scratch(f"envelope-{key}.json")
        return seal, self.apply(capability, envelope)

    # -- scratch -----------------------------------------------------------
    def scratch(self, name: str) -> Path:
        """Scratch space *outside* the repository.

        `seal_envelope.py` refuses to write an envelope inside the
        repository ("point --out at scratch"), so the canvas keeps its
        own scratch directory beside the world.
        """
        d = self.root.parent.parent / "canvas-scratch" / self.session_id
        d.mkdir(parents=True, exist_ok=True)
        return d / name


def build_world(container: Path, name: str = "canvas-a") -> World:
    """Build one fresh synthetic world inside `container/name`."""
    container = (container / name).resolve()
    if container.exists():
        shutil.rmtree(container)
    container.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(TESTS_DIR))
    try:
        from scenario_harness import prepare_transcript_fixture
    finally:
        del sys.path[0]
    built = prepare_transcript_fixture("rich_world", container, seed=name)
    root = Path(built["root"]).resolve()
    world = World(root=root, session_id=f"canvas-{name}",
                  observations=Path(built["observations"]))
    world.notes.append(
        f"synthetic world at {root} (rich_world characterization fixture)")
    return world


def clone_world(source: World, container: Path, name: str) -> World:
    """Copy an existing world so a scenario can diverge from it."""
    container.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source.root.parent, container / "LearningOS")
    root = container / "LearningOS" / "repository"
    world = World(root=root, session_id=f"canvas-{name}")
    world.notes.append(f"clone of {source.root} at {root}")
    return world


def core_python() -> str:
    return str(VENV_PY)
