#!/usr/bin/env python3
"""ADR-007 step 4: file source records by subject, not by ingestion batch.

    python tools/migrations/registry_partition_v1.py            # dry run
    python tools/migrations/registry_partition_v1.py --apply

228 records live in files named after the migration that ingested them —
``stage2-sources.yaml``, ``stage2b-unsorted-intake.yaml``, ``external-shelf``,
``external-supplements``, ``degree-anchors``. That is the same time-dependence
ADR-007 removed from the folder tree, still present in the registry: a record's
home says *when it arrived*, not *what it is*.

Each record moves to the partition of its first thematic group. **Source ids
never change**, so no reference anywhere needs updating — only which file holds
the record.

Record text is copied verbatim, line for line, including any comment lines
attached to it. Only the ``# ===== SECTION`` banners are dropped: they grouped
records inside a batch file, and the subject partition now carries that meaning.
Original files are archived whole under ``migration/adr-007/originals/`` (the
convention already used by migration/curriculum-v2), so the batch-level headers
describing each intake survive verbatim even though nothing cites them.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from learning_os.contracts.migration_lifecycle import (
    refuse_retired_apply,
    retired_migration,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "sources" / "registry"
CONSOLIDATED = ROOT / "sources" / "sources.yaml"
ARCHIVE = ROOT / "migration" / "adr-007" / "originals"

ID_RE = re.compile(r"^(\s*)- id: (['\"]?)(source-[a-z0-9-]+)\2\s*$")
GROUP_RE = re.compile(r"^\s*thematic_group_ids: \[([^\]]*)\]")
BANNER_RE = re.compile(r"^\s*#\s*=+")

PARTITIONS = {
    "mathematics": "Mathematics — probability and statistics, analysis, linear algebra, proof craft.",
    "optimization": "Optimization & Learning Theory — convex, numerical and combinatorial optimization, statistical learning theory, kernels.",
    "machine-learning": "Machine Learning — statistical and classical ML, deep learning, RL, vision, explainers.",
    "ml-systems": "ML Systems — training and serving at scale, ML compilation, performance, data for ML.",
    "data-systems": "Data Systems — databases, distributed systems, provenance, reliability.",
    "algorithms": "Algorithms & Computation — algorithms and data structures, complexity, approximation.",
    "software": "Software & Languages — Python craft, CPython internals, engineering practice, languages, tooling.",
    "method-admin": "Method & Administration — research method, degree regulations, dataset catalogues.",
}

HEADER = """\
# {title}
#
# Filed by SUBJECT (ADR-007). A record's home says what it is, never when it
# arrived — the previous partitions were named after migration batches
# (stage2, stage2b-unsorted-intake, external-shelf, external-supplements,
# degree-anchors), which are archived verbatim under
# migration/adr-007/originals/.
#
# Partitioning does not change semantics: this is the same registry as
# sources/sources.yaml, and source ids are unchanged, so no reference moved.
sources:
"""


def split_records(path: Path):
    """(header_lines, [(source_id, primary_group, [lines])]) for one registry."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "sources:")
    except StopIteration:
        return lines, []

    header, records, pending = lines[:start + 1], [], []
    i = start + 1
    while i < len(lines):
        match = ID_RE.match(lines[i])
        if not match:
            if lines[i].strip() and not BANNER_RE.match(lines[i]):
                pending.append(lines[i])
            elif not lines[i].strip():
                pending = []
            i += 1
            continue

        sid, end = match.group(3), i + 1
        while end < len(lines) and not ID_RE.match(lines[end]):
            if BANNER_RE.match(lines[end]):
                break
            end += 1
        body = pending + lines[i:end]
        pending = []
        group = next((GROUP_RE.match(line).group(1).split(",")[0]
                      .strip().replace("thematic-group-", "")
                      for line in body if GROUP_RE.match(line)), None)
        records.append((sid, group, body))
        i = end
    return header, records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    retired = retired_migration(ROOT, "registry-partition-v1", supported_through=1)
    if refuse_retired_apply(retired, apply=args.apply):
        return 2 if args.apply else 0

    sources = [CONSOLIDATED] + sorted(REGISTRY.glob("*.yaml"))
    buckets: dict[str, list] = {name: [] for name in PARTITIONS}
    ungrouped, total = [], 0

    for path in sources:
        _, records = split_records(path)
        for sid, group, body in records:
            total += 1
            if group in buckets:
                buckets[group].append((sid, body))
            else:
                ungrouped.append((sid, group, path.name))

    print(f"read {total} record(s) from {len(sources)} file(s)")
    for name in PARTITIONS:
        print(f"  {name + '.yaml':28} {len(buckets[name]):3} record(s)")
    if ungrouped:
        print(f"\n{len(ungrouped)} record(s) have no known group — not moved:")
        for sid, group, origin in ungrouped[:10]:
            print(f"  {sid} (group={group!r}, in {origin})")
        return 1

    if not args.apply:
        print("\ndry run — rerun with --apply")
        return 0

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for path in sources:
        shutil.copy2(path, ARCHIVE / path.name)

    for name, title in PARTITIONS.items():
        rows = sorted(buckets[name], key=lambda row: row[0])
        text = HEADER.format(title=title) + "".join(
            "".join(body) for _, body in rows)
        (REGISTRY / f"{name}.yaml").write_text(text, encoding="utf-8")

    CONSOLIDATED.write_text(
        "# The consolidated registry is intentionally empty since ADR-007.\n"
        "#\n"
        "# Every source record lives in its subject partition under\n"
        "# sources/registry/. The loader reads the consolidated file and the\n"
        "# partition directory as one registry, so this file remains valid and\n"
        "# available if a record ever needs a home before its subject is settled.\n"
        "sources: []\n", encoding="utf-8")

    # Emptying rather than deleting: every record now exists in its subject
    # partition, so leaving these populated would duplicate all 228 ids and fail
    # validation immediately. A tombstone keeps the tree valid between this run
    # and the `git rm` below, which is the operator's call to make.
    superseded = [p for p in sources
                  if p != CONSOLIDATED and p.name not in {f"{n}.yaml" for n in PARTITIONS}]
    for path in superseded:
        path.write_text(
            f"# SUPERSEDED by ADR-007 — this partition was named after the\n"
            f"# migration batch that ingested its records, not their subject.\n"
            f"# Every record moved to sources/registry/<subject>.yaml with its id\n"
            f"# unchanged. The original is archived verbatim at\n"
            f"# migration/adr-007/originals/{path.name}.\n"
            f"#\n"
            f"# Safe to delete:  git rm sources/registry/{path.name}\n"
            f"sources: []\n", encoding="utf-8")

    print(f"\napplied. originals archived under {ARCHIVE.relative_to(ROOT)}/")
    print("superseded partitions emptied — remove them with:")
    for path in superseded:
        print(f"  git rm sources/registry/{path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
