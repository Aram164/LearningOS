#!/usr/bin/env python3
"""Advisory memo of Core/UI pairs `make system-check` already verified.

The pre-push hook runs the 11–14 minute paired gate on every push, including
a pair that was verified minutes earlier at exactly these SHAs. When
`system-check` succeeds on clean trees it stamps the pair here; the hook
skips the full gate for an exact stamped pair and says so. Advisory only:
CI and the release-pair receipts remain the authority, and any new commit,
dirty tree, or toolchain change re-runs the gate.

    python tools/verified_pairs.py stamp   # record the current clean pair
    python tools/verified_pairs.py check   # exit 0 iff the current pair is stamped
    python tools/verified_pairs.py base    # print the last stamped Core SHA
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path

STAMP_FILENAME = "learningos-verified-pairs.jsonl"
STAMP_KEEP = 200


def _core_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ui_root(core: Path) -> Path:
    return core.parent / "obsidian-ui"


def _git(repo: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _clean(repo: Path) -> bool:
    return _git(repo, "status", "--porcelain") == ""


def _head(repo: Path) -> str | None:
    sha = _git(repo, "rev-parse", "HEAD")
    if sha is None or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        return None
    return sha


def _node_version() -> str:
    try:
        proc = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return proc.stdout.strip() or "unknown"


def _dist_version(name: str) -> str:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def _toolchain() -> dict[str, str]:
    python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    node = _node_version()
    pytest = _dist_version("pytest")
    ruff = _dist_version("ruff")
    digest = hashlib.sha256(
        json.dumps({"python": python, "node": node, "pytest": pytest, "ruff": ruff},
                   sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"python": python, "node": node, "pytest": pytest,
            "ruff": ruff, "digest": digest}


def _stamp_path(core: Path) -> Path | None:
    git_dir = _git(core, "rev-parse", "--git-dir")
    if git_dir is None:
        return None
    path = Path(git_dir)
    if not path.is_absolute():
        path = core / path
    return path / STAMP_FILENAME


def _read_stamps(path: Path) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    stamps = []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            stamps.append(row)
    return stamps


def _find_stamp(stamps: list[dict], core_sha: str, ui_sha: str,
               digest: str) -> dict | None:
    for row in reversed(stamps):
        if not isinstance(row, dict):
            continue
        toolchain = row.get("toolchain")
        stamp_digest = toolchain.get("digest") if isinstance(toolchain, dict) else None
        if row.get("core_sha") == core_sha and row.get("ui_sha") == ui_sha \
                and stamp_digest == digest:
            return row
    return None


def cmd_stamp() -> int:
    core = _core_root()
    ui = _ui_root(core)
    core_sha = _head(core)
    ui_sha = _head(ui) if ui.is_dir() else None
    if core_sha is None or ui_sha is None:
        print("verified-pairs: not stamping — Core/UI SHAs unavailable", file=sys.stderr)
        return 0
    if not _clean(core) or not _clean(ui):
        print("verified-pairs: not stamping — trees are dirty", file=sys.stderr)
        return 0
    path = _stamp_path(core)
    if path is None:
        print("verified-pairs: not stamping — no Core git dir", file=sys.stderr)
        return 0
    toolchain = _toolchain()
    stamps = _read_stamps(path)
    if _find_stamp(stamps, core_sha, ui_sha, toolchain["digest"]) is not None:
        print(f"verified-pairs: pair already stamped ({core_sha[:12]}/{ui_sha[:12]})")
        return 0
    stamps.append({
        "core_sha": core_sha,
        "ui_sha": ui_sha,
        "toolchain": toolchain,
        "stamped_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
    })
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n"
                    for row in stamps[-STAMP_KEEP:]),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"verified-pairs: not stamping — cannot write {path}: {exc}",
              file=sys.stderr)
        return 0
    print(f"verified-pairs: stamped {core_sha[:12]}/{ui_sha[:12]} -> {path}")
    return 0


def cmd_check() -> int:
    core = _core_root()
    ui = _ui_root(core)
    core_sha = _head(core)
    ui_sha = _head(ui) if ui.is_dir() else None
    path = _stamp_path(core)
    if core_sha is None or ui_sha is None or path is None:
        return 1
    stamp = _find_stamp(_read_stamps(path), core_sha, ui_sha,
                        _toolchain()["digest"])
    if stamp is None:
        return 1
    print(f"verified-pairs: exact stamped pair "
          f"core={core_sha[:12]} ui={ui_sha[:12]} "
          f"(stamped {stamp.get('stamped_at', 'at an unknown time')})")
    return 0


def _is_sha(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 40
            and all(c in "0123456789abcdef" for c in value))


def cmd_base() -> int:
    """Print the last stamped Core SHA: the review-gate diff base.

    A diff base, not a trust decision: the toolchain is deliberately not
    consulted. The caller diffs the working tree against the last verified
    Core commit; stamp/check semantics are unchanged.
    """
    core = _core_root()
    path = _stamp_path(core)
    if path is None:
        print("verified-pairs: no Core git dir", file=sys.stderr)
        return 1
    for row in reversed(_read_stamps(path)):
        sha = row.get("core_sha")
        if _is_sha(sha):
            print(sha)
            return 0
    print("verified-pairs: no stamped pair yet", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("stamp", "check", "base"))
    args = parser.parse_args(argv)
    if args.command == "stamp":
        return cmd_stamp()
    if args.command == "base":
        return cmd_base()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
