"""Split the churn the fix causes into its two causes, by value.

Two things moved in the procedure world, for two different reasons:

* the **world's canonical fingerprint** (it covers ``system/schema`` and
  ``system/contracts``) — moved by F-05's record-shape change;
* the **world's warning count** — moved by F-01 Part A's scope rule, which
  reports four of the demo stage's own resources.

The pinned values live inside single long lines (a transcript's JSON, a
scenario recording's captured stdout), so the split has to be by *value*,
not by line: this script takes the updated file and puts the moved digests
back, leaving the counts where they are. The result is the file as it
stands at the commit that carries the scope rule but not the schema change.

Usage: .venv/bin/python <this file> <out dir>
"""

from __future__ import annotations

import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repository"
AREAS = ("system/procedures", "tests/scenarios/recorded", "tests/scenarios/cases",
         "tests/scenarios/files")
#: A digest long enough to be a fingerprint or a revision, never a count.
_DIGEST_RE = re.compile(r"[0-9a-f]{40,64}")


def moved_digests(old: str, new: str) -> list[tuple[str, str]]:
    """The (old, new) digest pairs that changed between the two versions."""
    old_tokens = _DIGEST_RE.findall(old)
    new_tokens = _DIGEST_RE.findall(new)
    pairs: list[tuple[str, str]] = []
    matcher = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "replace":
            continue
        for old_token, new_token in zip(old_tokens[i1:i2], new_tokens[j1:j2]):
            if old_token != new_token:
                pairs.append((old_token, new_token))
    return pairs


def changed_files() -> tuple[list[str], list[str]]:
    """The modified and the new files in the churn areas."""
    changed = subprocess.run(
        ["git", "diff", "--name-only", "40d8afe", "--", *AREAS],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    added = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *AREAS],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return changed, added


def main() -> int:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    changed, added = changed_files()

    # One global mapping: the world's fingerprints moved, so every file that
    # pins one pins the same new value.
    mapping: dict[str, str] = {}
    for relative in changed:
        head = subprocess.run(
            ["git", "show", f"40d8afe:{relative}"],
            cwd=ROOT, capture_output=True, text=True)
        if head.returncode != 0:
            continue
        old = head.stdout
        new = (ROOT / relative).read_text(encoding="utf-8")
        for old_token, new_token in moved_digests(old, new):
            mapping.setdefault(new_token, old_token)

    for relative in changed + added:
        path = ROOT / relative
        content = path.read_text(encoding="utf-8")
        reverted = content
        for new_token, old_token in mapping.items():
            reverted = reverted.replace(new_token, old_token)
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(reverted, encoding="utf-8")
    print(f"wrote {len(changed) + len(added)} digest-reverted file(s) to {out_dir}")
    print(f"digests reverted: {len(mapping)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
