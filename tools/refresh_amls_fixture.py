#!/usr/bin/env python3
"""Regenerate the checked-in AMLS paper-inventory fixture from the external list.

The AMLS reading list lives outside the authored tree, under
``../materials/`` (CLAUDE.md §11), so CI — which checks out only this
repository — cannot read it. The fixture at
``tests/fixtures/amls-paper-inventory.yaml`` is the repository's own record of
what that list says, which lets the wiring assertions run everywhere.

Run this whenever the external reading list changes, then re-wire the affected
study maps and commit both:

    python tools/refresh_amls_fixture.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "amls-paper-inventory.yaml"
READING_LIST = (
    ROOT.parent
    / "materials/ML/AMLS/course/amls-ss26-lectures/AMLS-Source-Papers-Reading-List.md"
)
LECTURES = [f"{i:02d}" for i in range(1, 14)]


def parse_reading_list(path: Path) -> dict:
    """Parse the reading list into {lecture: {curated: [...], bibliography: n}}.

    Part 1 lists the curated primary papers per lecture as ``- **Title**…``;
    Part 2 is the per-lecture complete bibliography, which is counted only.
    """
    curated: dict[str, list[str]] = {lec: [] for lec in LECTURES}
    bibliography: dict[str, int] = {lec: 0 for lec in LECTURES}
    part, lecture = 0, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Part 1"):
            part = 1
        elif line.startswith("# Part 2"):
            part = 2
        elif line.startswith("## ") and line[3:5].isdigit():
            lecture = line[3:5]
        elif line.startswith("- ") and lecture and part == 1:
            if not (line.startswith("- **") and "**" in line[4:]):
                raise SystemExit(f"malformed curated entry under Lecture {lecture}: {line!r}")
            curated[lecture].append(line[4:].split("**", 1)[0])
        elif line.startswith("- ") and lecture and part == 2:
            bibliography[lecture] += 1
    return {lec: {"curated": curated[lec], "bibliography": bibliography[lec]}
            for lec in LECTURES}


def main() -> int:
    if not READING_LIST.exists():
        raise SystemExit(
            f"external reading list not found: {READING_LIST}\n"
            "This script needs the materials tree beside the repository "
            "(CLAUDE.md §11); it cannot run in CI."
        )
    lectures = parse_reading_list(READING_LIST)
    payload = {
        "source": "material://source-amls-ss26-lectures/AMLS-Source-Papers-Reading-List.md",
        "captured": __import__("datetime").date.today().isoformat(),
        "totals": {
            "curated": sum(len(row["curated"]) for row in lectures.values()),
            "bibliography": sum(row["bibliography"] for row in lectures.values()),
        },
        "lectures": lectures,
    }
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(
        "# Generated — do not hand-edit. Regenerate with:\n"
        "#     python tools/refresh_amls_fixture.py\n"
        "# The repository's record of the external AMLS reading list, which lives\n"
        "# under ../materials/ and is therefore invisible to CI. The wiring test\n"
        "# asserts the study maps against this file (runs everywhere); the drift\n"
        "# test asserts this file still matches the external list (local only).\n"
        + yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"wrote {FIXTURE.relative_to(ROOT)}: "
          f"{payload['totals']['curated']} curated, "
          f"{payload['totals']['bibliography']} bibliography entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
