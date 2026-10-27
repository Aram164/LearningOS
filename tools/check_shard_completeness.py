#!/usr/bin/env python3
"""Prove the sharded CI runs are exactly the collected suite.

Shared by validate.yml and release-pair.yml so the two gates cannot drift:
the shard manifest must partition tests/, and every executed JUnit testcase
must map back to a canonical collected node ID with multiplicity exactly
one — a duplicate plus an omission has the same count and must still fail.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def _fail(message: str) -> SystemExit:
    return SystemExit(f"shard completeness: {message}")


def check(junit_dir: Path, manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    disk = sorted(f"tests/{p.name}" for p in Path("tests").glob("test_*.py"))
    covered = Counter(f for leg in manifest["legs"].values() for f in leg)
    for name, count in sorted(covered.items()):
        expected = manifest.get("node_shards", {}).get(name, {}).get("count", 1)
        if count != expected:
            raise _fail(f"{name} appears in {count} legs, expected {expected}")
    if sorted(covered) != disk:
        raise _fail(
            ".github/shard-manifest.json does not partition tests/: "
            f"missing={sorted(set(disk) - set(covered))} "
            f"extra={sorted(set(covered) - set(disk))}")

    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-m", "not live_install"],
        capture_output=True, text=True, check=True)
    collected_ids = [line.strip() for line in out.stdout.splitlines()
                     if "::" in line and not line.startswith(" ")]
    expected_ids = Counter(collected_ids)
    if not expected_ids:
        raise _fail("full collection produced no node IDs")

    def node_id(classname: str | None, name: str | None) -> str | None:
        parts = (classname or "").split(".")
        for split in range(1, len(parts) + 1):
            candidate = ("/".join(parts[:split]) + ".py::"
                         + "::".join(parts[split:] + [name or ""]))
            if candidate in expected_ids:
                return candidate
        return None

    executed: Counter[str] = Counter()
    unmapped: list[str] = []
    skipped = 0
    for path in sorted(junit_dir.glob("junit-*.xml")):
        root = ET.parse(path).getroot()
        for case in root.iter("testcase"):
            mapped = node_id(case.get("classname"), case.get("name"))
            if mapped is None:
                unmapped.append(f"{case.get('classname')}::{case.get('name')}")
            else:
                executed[mapped] += 1
            if case.find("skipped") is not None:
                skipped += 1
            if case.find("failure") is not None or case.find("error") is not None:
                raise _fail(f"{path.name}: failing testcase "
                            f"{case.get('classname')}::{case.get('name')}")
    if unmapped:
        raise _fail(f"executed tests with no collected node ID: {unmapped[:10]}")
    if executed != expected_ids:
        missing = sorted((expected_ids - executed).elements())
        extra = sorted((executed - expected_ids).elements())
        raise _fail("shard test identities differ from the full collection: "
                    f"missing={missing[:10]} extra_or_duplicated={extra[:10]}")
    return (f"gate: {sum(executed.values())} executed test IDs == full "
            f"collection, each exactly once ({skipped} skipped, visible, "
            "never blocking)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit-dir", required=True, type=Path)
    parser.add_argument("--manifest", type=Path,
                        default=Path(".github/shard-manifest.json"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(check(args.junit_dir, args.manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
