"""Split the procedure transcripts' diff into its two causes.

The transcripts pin two things that moved for different reasons:

* the **world's canonical fingerprint** (which covers ``system/schema`` and
  ``system/contracts``) — moved by F-05's record-shape change;
* the **world's warning count** — moved by F-01 Part A's scope rule, which
  reports four of the demo stage's own resources.

This script writes the "counts only" version of each transcript, so the two
can land in separate commits with each commit's transcripts correct for the
world as it stands at that commit.

Usage: .venv/bin/python <this file> <out dir>
"""

from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repository"
PROCEDURES = "system/procedures"


def is_count_change(old: str, new: str) -> bool:
    return "warning(s)" in old or "warning(s)" in new


def is_hash_change(old: str, new: str) -> bool:
    return "sha256" in old or "sha256" in new


def split_file(original: list[str], updated: list[str]) -> list[str]:
    """The updated file with every hash-only change reverted."""
    out: list[str] = []
    matcher = difflib.SequenceMatcher(a=original, b=updated, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            out.extend(updated[j1:j2])
            continue
        old_block = original[i1:i2]
        new_block = updated[j1:j2]
        for index, new_line in enumerate(new_block):
            old_line = old_block[index] if index < len(old_block) else ""
            if (not is_count_change(old_line, new_line)
                    and is_hash_change(old_line, new_line)):
                out.append(old_line)
            else:
                out.append(new_line)
        for old_line in old_block[len(new_block):]:
            out.append(old_line)
    return out


def main() -> int:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    changed = subprocess.run(
        ["git", "diff", "--name-only", "--", PROCEDURES],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    written = 0
    for relative in changed:
        path = ROOT / relative
        original = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
        updated = path.read_text(encoding="utf-8")
        counts_only = "".join(
            line + "\n" for line in split_file(
                original.split("\n"), updated.split("\n")))
        target = out_dir / Path(relative).name
        target.write_text(counts_only, encoding="utf-8")
        written += 1
    print(f"wrote {written} count-only transcript(s) to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
