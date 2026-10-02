#!/usr/bin/env python3
"""Kill a canonical write at chosen moments and classify what it leaves behind.

    python tests/eval/tools/interrupt_probe.py --world WORLD_REPO \
        --cmd "python tools/los.py capability capture.create --payload-file /abs/envelope.json" \
        --delays 0.02,0.05,0.1,0.2,0.3,0.5,0.8,1.2,2,3 --out interrupt.json

For the world repository (it must be an evaluation world's
``LearningOS/repository`` with EVAL-WORLD.json two levels up — the probe
refuses anything else, because it restores the world between trials):

1. copy the world repository as it stands now — tracked, untracked and
   ignored files, so prerequisites the operator prepared (a coverage audit
   under work/active/, a staged batch) survive — into a hidden pristine copy
   beside it, then run the command once uninterrupted to learn its duration
   and the shape of a complete write (which directories change, receipt
   count). If that uninterrupted run changes nothing canonical, the probe
   stops with exit 2: every kill would be vacuous;
2. for every delay: restore the pristine copy, start the command in its own process group, send
   SIGKILL to the group after the delay, then
   a. run the --after read commands (default: `tools/validate.py --compact
      --no-report` and `tools/los.py status --json`) and record what the
      world looks like to a reader *before any recovery* (`before_recovery`:
      changed files, receipts, crash journal present, the reads' output);
   b. run the --recover command (default `tools/los.py generate`, which takes
      the operator lock; LearningOS reconciles crash journals when that lock
      is taken — note that `tools/generate.py` / `make views` does not take
      it; pass --recover '' to skip), and classify the final state:

   pre-state   no canonical change, no new receipt, no journal left
   committed   exactly the complete write's shape and receipts, no journal left
   PARTIAL     anything else after recovery (change without receipt, receipt
               without change, a different shape, or a journal still present)
               — the finding to report
   finished    the command completed before the kill was sent

   A trial whose before_recovery state shows a canonical change together with
   a pending journal is flagged `exposed_before_recovery`: readers saw a write
   that recovery may still undo. Whether that matters is for the evaluation to
   judge; the probe only reports it.

Canonical paths under operations/ are compared by shape only, because receipt
and request ids differ between runs. The world is restored to its pristine
copy at the end and the copy is removed.

The envelope's expected_snapshot must match the world's state when the probe
starts; since every trial starts from the same restored state, one envelope
serves all trials.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from observe import snapshot  # noqa: E402

VOLATILE = ("operations/transactions/", "operations/gateway-requests/", "operations/ai-actions/")


def require_world(repo: Path) -> Path:
    repo = repo.resolve()
    record = repo.parent.parent / "EVAL-WORLD.json"
    if (not record.is_file() or repo.name != "repository" or repo.parent.name != "LearningOS"
            or not (repo / "tools" / "los.py").is_file()):
        raise SystemExit(f"interrupt_probe: {repo} is not an evaluation world's "
                         "LearningOS/repository (EVAL-WORLD.json two levels up); refusing "
                         "to restore it")
    try:
        named = Path(json.loads(record.read_text(encoding="utf-8"))["paths"]["repository"])
    except (ValueError, KeyError, TypeError):
        named = None
    if named is None or named.resolve() != repo:
        print(f"interrupt_probe: note: EVAL-WORLD.json names {named}; probing the copy at "
              f"{repo}", file=sys.stderr)
    return repo


class Pristine:
    """A full copy of the world repository, restored before every trial."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.holder = Path(tempfile.mkdtemp(prefix=".interrupt-probe-pristine-",
                                            dir=repo.parent.parent))
        self.copy = self.holder / "repository"
        shutil.copytree(repo, self.copy, symlinks=True)

    def restore(self) -> None:
        shutil.rmtree(self.repo)
        shutil.copytree(self.copy, self.repo, symlinks=True)

    def discard(self) -> None:
        shutil.rmtree(self.holder, ignore_errors=True)


def shape(snap: dict) -> dict:
    files = snap["canonical"]["files"]
    stable = {k: v for k, v in files.items() if not k.startswith(VOLATILE)}
    volatile_dirs = sorted({k.rsplit("/", 1)[0] for k in files if k.startswith(VOLATILE)})
    return {"stable": stable, "volatile_dirs": volatile_dirs,
            "receipts": [r for r in snap["receipts"] if not r.endswith(".gitkeep")]}


def delta(before: dict, after: dict) -> dict:
    b, a = shape(before), shape(after)
    changed = sorted(k for k in set(a["stable"]) | set(b["stable"])
                     if a["stable"].get(k) != b["stable"].get(k))
    dirs = sorted({k.rsplit("/", 1)[0] for k in changed})
    return {"changed_dirs": dirs, "changed_count": len(changed),
            "new_receipts": len(set(a["receipts"]) - set(b["receipts"])),
            "inflight": after["inflight"]}


def run_after(repo: Path, commands: list[str]) -> list[dict]:
    out = []
    for cmd in commands:
        proc = subprocess.run(shlex.split(cmd), cwd=repo, capture_output=True, text=True,
                              timeout=600)
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        out.append({"cmd": cmd, "exit": proc.returncode, "tail": tail})
    return out


def trial(repo: Path, cmd: list[str], delay: float | None) -> tuple[float, bool]:
    start = time.monotonic()
    proc = subprocess.Popen(cmd, cwd=repo, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    killed = False
    if delay is not None:
        try:
            proc.wait(timeout=delay)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            killed = True
    proc.wait()
    return time.monotonic() - start, killed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", required=True, type=Path)
    parser.add_argument("--cmd", required=True, help="the write, run from the world root")
    parser.add_argument("--delays", required=True, help="comma-separated seconds")
    parser.add_argument("--after", action="append", default=None,
                        help="read command run after each kill (repeatable)")
    parser.add_argument("--recover", default=None,
                        help="command that triggers recovery (default: tools/los.py "
                             "generate; '' to skip)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    repo = require_world(args.world)
    cmd = shlex.split(args.cmd)
    after_cmds = args.after or [f"{sys.executable} tools/validate.py --compact --no-report",
                                f"{sys.executable} tools/los.py status --json"]
    delays = [float(x) for x in args.delays.split(",") if x.strip()]
    recover_cmd = (f"{sys.executable} tools/los.py generate" if args.recover is None
                   else args.recover)

    saved = Pristine(repo)
    try:
        return probe(repo, saved, cmd, delays, after_cmds, recover_cmd, args)
    finally:
        saved.restore()
        saved.discard()


def probe(repo: Path, saved: Pristine, cmd: list[str], delays: list[float],
          after_cmds: list[str], recover_cmd: str, args) -> int:
    pristine = snapshot(repo, "pristine")
    duration, _ = trial(repo, cmd, None)
    full = snapshot(repo, "complete")
    complete = delta(pristine, full)
    if complete["changed_count"] == 0:
        print("interrupt_probe: the uninterrupted command changed nothing canonical; "
              "every kill would be vacuous. Check the envelope and its prerequisites "
              "(the world was restored).", file=sys.stderr)
        return 2

    results = []
    for delay in delays:
        saved.restore()
        before = snapshot(repo, f"before-{delay}")
        elapsed, killed = trial(repo, cmd, delay)
        after_runs = run_after(repo, after_cmds)
        mid = snapshot(repo, f"before-recovery-{delay}")
        exposed = delta(before, mid)
        recover_runs = run_after(repo, [recover_cmd]) if recover_cmd else []
        after = snapshot(repo, f"after-{delay}")
        d = delta(before, after)
        if not killed:
            outcome = "finished"
        elif d["changed_count"] == 0 and d["new_receipts"] == 0 and not d["inflight"]:
            outcome = "pre-state"
        elif (d["changed_dirs"] == complete["changed_dirs"]
              and d["changed_count"] == complete["changed_count"]
              and d["new_receipts"] == complete["new_receipts"] and not d["inflight"]):
            outcome = "committed"
        else:
            outcome = "PARTIAL"
        results.append({"delay_s": delay, "killed": killed, "elapsed_s": round(elapsed, 3),
                        "outcome": outcome, "delta": d,
                        "exposed_before_recovery": bool(exposed["changed_count"]
                                                        and exposed["inflight"]),
                        "before_recovery": {**exposed, "reads": after_runs},
                        "recovery": recover_runs})
    summary: dict[str, int] = {}
    for row in results:
        summary[row["outcome"]] = summary.get(row["outcome"], 0) + 1
    summary["exposed_before_recovery"] = sum(r["exposed_before_recovery"] for r in results)
    payload = {"probe_version": 2, "world": str(repo), "cmd": args.cmd,
               "recover": recover_cmd,
               "uninterrupted_s": round(duration, 3), "complete_write": complete,
               "summary": summary, "trials": results}
    text = json.dumps(payload, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text if not args.out else json.dumps(summary))
    return 1 if summary.get("PARTIAL") else 0


if __name__ == "__main__":
    sys.exit(main())
