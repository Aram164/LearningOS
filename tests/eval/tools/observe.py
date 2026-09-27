#!/usr/bin/env python3
"""Observe a LearningOS world from behind the curtain, without changing it.

    python tests/eval/tools/observe.py snapshot WORLD_REPO --label before --out before.json
    python tests/eval/tools/observe.py diff before.json after.json

A snapshot records, for the repository at WORLD_REPO:

* Git HEAD and `git status --porcelain` (read with GIT_OPTIONAL_LOCKS=0, so the
  observer never takes the index lock);
* a digest per canonical file (everything not ignored by Git, outside .git and
  generated/), and one digest over all of them;
* a digest per derived file under generated/ and its total bytes;
* the transaction receipts under operations/transactions/, any crash-recovery
  journal under operations/transactions/.inflight/, AI-action request and
  delivery bundles, and the diagnostic trace store's file list;
* the product's own `los operations` listing (its trace/request ids), when the
  world's CLI can run.

`diff` reports what changed between two snapshots: canonical files added,
removed or modified; receipts added; journals left behind; derived files that
changed; and a flag for any canonical change without a new receipt (a write
that bypassed the transaction service, or one that is still in flight).

Nothing here writes inside the world. Output goes to --out or stdout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

GIT_ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                            env=GIT_ENV)
    return result.stdout if result.returncode == 0 else ""


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree(root: Path, rel_files) -> tuple[dict[str, str], str, int]:
    files: dict[str, str] = {}
    total = 0
    for rel in sorted(rel_files):
        path = root / rel
        if path.is_symlink():
            files[rel] = "symlink:" + os.readlink(path)
        elif path.is_file():
            files[rel] = _sha(path)
            total += path.stat().st_size
    digest = hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in files.items()).encode())
    return files, digest.hexdigest(), total


def canonical_files(repo: Path) -> list[str]:
    listed = _git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return [rel for rel in listed.split("\0")
            if rel and not rel.startswith("generated/") and (repo / rel).exists()]


def derived_files(repo: Path) -> list[str]:
    base = repo / "generated"
    if not base.is_dir():
        return []
    return [p.relative_to(repo).as_posix() for p in base.rglob("*") if p.is_file()]


def _listing(repo: Path, rel: str) -> list[str]:
    base = repo / rel
    if not base.exists():
        return []
    return sorted(p.relative_to(repo).as_posix() for p in base.rglob("*")
                  if p.is_file() or p.is_dir() and p.name.startswith(".preparing"))


def snapshot(repo: Path, label: str) -> dict:
    repo = repo.resolve()
    if not (repo / "tools" / "los.py").is_file():
        raise SystemExit(f"observe: {repo} is not a LearningOS repository")
    canonical, canonical_digest, canonical_bytes = _tree(repo, canonical_files(repo))
    derived, derived_digest, derived_bytes = _tree(repo, derived_files(repo))
    receipts = [p for p in _listing(repo, "operations/transactions")
                if "/.inflight" not in p and not p.endswith(".gitkeep")]
    inflight = _listing(repo, "operations/transactions/.inflight")
    ops = None
    proc = subprocess.run([sys.executable, "tools/los.py", "operations", "--limit", "50"],
                          cwd=repo, capture_output=True, text=True, timeout=120)
    if proc.returncode == 0:
        try:
            ops = json.loads(proc.stdout).get("operations")
        except json.JSONDecodeError:
            ops = None
    return {
        "observer_version": 1,
        "label": label,
        "taken_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "repository": str(repo),
        "head": _git(repo, "rev-parse", "HEAD").strip(),
        "git_status": _git(repo, "status", "--porcelain").splitlines(),
        "canonical": {"digest": canonical_digest, "bytes": canonical_bytes,
                      "count": len(canonical), "files": canonical},
        "derived": {"digest": derived_digest, "bytes": derived_bytes,
                    "count": len(derived), "files": derived},
        "receipts": receipts,
        "inflight": inflight,
        "ai_actions": _listing(repo, "operations/ai-actions"),
        "gateway_requests": _listing(repo, "operations/gateway-requests"),
        "diagnostics": _listing(repo, "operations/diagnostics"),
        "operations": ops,
    }


def _changes(a: dict, b: dict) -> dict:
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    modified = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return {"added": added, "removed": removed, "modified": modified}


def diff(before: dict, after: dict) -> dict:
    canonical = _changes(before["canonical"]["files"], after["canonical"]["files"])
    receipts_added = sorted(set(after["receipts"]) - set(before["receipts"]))
    derived = _changes(before["derived"]["files"], after["derived"]["files"])
    canonical_changed = any(canonical.values())
    ops_before = {o.get("request_id") for o in before.get("operations") or [] if isinstance(o, dict)}
    ops_after = [o for o in after.get("operations") or [] if isinstance(o, dict)
                 and o.get("request_id") not in ops_before]
    flags = []
    if canonical_changed and not receipts_added:
        flags.append("canonical-change-without-new-receipt")
    if receipts_added and not canonical_changed:
        flags.append("receipt-without-canonical-change")
    if after["inflight"]:
        flags.append("inflight-journal-present")
    if before["head"] != after["head"]:
        flags.append("head-moved")
    return {
        "from": before["label"], "to": after["label"],
        "canonical": canonical,
        "canonical_digest_changed": before["canonical"]["digest"] != after["canonical"]["digest"],
        "receipts_added": receipts_added,
        "inflight_after": after["inflight"],
        "derived": {**derived, "bytes_before": before["derived"]["bytes"],
                    "bytes_after": after["derived"]["bytes"]},
        "diagnostics_added": sorted(set(after["diagnostics"]) - set(before["diagnostics"])),
        "ai_actions_added": sorted(set(after["ai_actions"]) - set(before["ai_actions"])),
        "new_operations": ops_after,
        "head": {"before": before["head"], "after": after["head"]},
        "git_status_after": after["git_status"],
        "flags": flags,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("repo", type=Path)
    snap.add_argument("--label", default="snapshot")
    snap.add_argument("--out", type=Path)
    d = sub.add_parser("diff")
    d.add_argument("before", type=Path)
    d.add_argument("after", type=Path)
    d.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "snapshot":
        payload = snapshot(args.repo, args.label)
    else:
        payload = diff(json.loads(args.before.read_text(encoding="utf-8")),
                       json.loads(args.after.read_text(encoding="utf-8")))
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
