"""Map changed files to the test groups (and test files) that must rerun.

Reads the area map from ``tests/group_map.py``. By default the changed paths
are the branch commits against --base plus uncommitted changes; pass explicit
paths with --files instead. Unknown or shared paths select every group (the
map fails closed), so this is a rerun *minimizer*, never a gate — CI and
``make system-check`` always run the full suite.

Usage:
  python tools/affected_tests.py [--base main] [--groups] [test-files...]
  python tools/affected_tests.py --files tools/los.py curriculum/...
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import group_map  # noqa: E402  (importable only after the tests/ path insert)


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=False)
    return proc.stdout if proc.returncode == 0 else ""


def changed_paths(base: str | None) -> list[str]:
    paths: list[str] = []
    if base:
        merge_base = _git("merge-base", "HEAD", base).strip()
        if merge_base:
            out = _git("diff", "--name-only", f"{merge_base}...HEAD")
            paths.extend(out.split())
    for line in _git("status", "--porcelain").splitlines():
        # Entries look like " M path", "?? path", "R  old -> new".
        entry = line[3:] if len(line) > 3 else ""
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        entry = entry.strip().strip('"')
        if entry:
            paths.append(entry)
    # De-duplicated, repo-relative, tracked-or-not (untracked test files still
    # map to their group; unknown paths fail closed to all groups).
    return sorted(set(paths))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="main",
                        help="branch base for committed changes "
                             "(falls back to uncommitted only)")
    parser.add_argument("--files", nargs="*", default=None,
                        help="explicit repo-relative paths instead of git")
    parser.add_argument("--groups", action="store_true",
                        help="print group names instead of test files")
    args = parser.parse_args(argv)

    if args.files is not None:
        paths = args.files
    else:
        base = args.base if _git("rev-parse", "--verify", args.base).strip() else None
        paths = changed_paths(base)
    if not paths:
        return 0
    groups = group_map.groups_for_paths(paths)
    if args.groups:
        print(" ".join(sorted(groups)))
    else:
        print(" ".join(group_map.tests_for_groups(groups)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
