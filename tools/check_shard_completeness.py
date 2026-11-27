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
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from learning_os.store.contracts.write_scopes import guard_tool_output_path  # noqa: E402


def _fail(message: str) -> SystemExit:
    return SystemExit(f"shard completeness: {message}")


MANDATORY_PAIRED_WITNESS_PREFIXES: tuple[str, ...] = (
    "tests/test_ui_phase3_live_writes.py::",
    "tests/test_ui_gateway_recovery.py::",
    "tests/test_operations_gate.py::",
    "tests/test_contract_differential.py::",
)


def _parse_allow_skip(entries: Sequence[str]) -> dict[str, str]:
    allowed: dict[str, str] = {}
    for entry in entries:
        node_id, sep, reason = entry.partition("=")
        if not sep or not node_id.strip() or not reason.strip():
            raise _fail(
                f"invalid --allow-skip entry {entry!r}: expected NODE_ID=REASON"
            )
        if node_id in allowed:
            raise _fail(f"duplicate --allow-skip node ID: {node_id}")
        allowed[node_id] = reason.strip()
    return allowed


def check(
    junit_dir: Path,
    manifest_path: Path,
    *,
    require_passed_prefixes: Sequence[str] = (),
    allow_skips: Mapping[str, str] | None = None,
) -> str:
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

    clean_env = {k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"}
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True, text=True, check=True, timeout=120, env=clean_env)
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
    skipped_ids: set[str] = set()
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
                if mapped is not None:
                    skipped_ids.add(mapped)
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
    allowed = dict(allow_skips or {})
    mandatory_ids: list[str] = []
    seen_mandatory: set[str] = set()
    for prefix in require_passed_prefixes:
        matched = [nid for nid in sorted(expected_ids) if nid.startswith(prefix)]
        if not matched:
            raise _fail(
                f"mandatory witness prefix matched zero collected tests: {prefix}"
            )
        for nid in matched:
            if nid not in seen_mandatory:
                seen_mandatory.add(nid)
                mandatory_ids.append(nid)
    allowed_skips_used = 0
    mandatory_passed = 0
    for nid in mandatory_ids:
        if nid in skipped_ids:
            if nid not in allowed:
                raise _fail(f"mandatory witness skipped: {nid}")
            allowed_skips_used += 1
        else:
            mandatory_passed += 1
    if require_passed_prefixes:
        return (
            f"gate: {sum(executed.values())} executed test IDs == full "
            f"collection, each exactly once ({skipped} skipped, "
            f"{allowed_skips_used} allowed mandatory skips, "
            f"{mandatory_passed}/{len(mandatory_ids)} mandatory witnesses passed)"
        )
    return (f"gate: {sum(executed.values())} executed test IDs == full "
            f"collection, each exactly once ({skipped} skipped, visible, "
            "never blocking)")


def check_zero_skip_junit(junit_path: Path) -> str:
    """Prove a dedicated platform suite ran >= 1 testcase with 0 skips/failures."""
    if not junit_path.is_file():
        raise _fail(f"missing zero-skip JUnit XML: {junit_path}")
    try:
        root = ET.parse(junit_path).getroot()
    except ET.ParseError as exc:
        raise _fail(f"{junit_path.name}: malformed JUnit XML: {exc}") from exc
    cases = list(root.iter("testcase"))
    if not cases:
        raise _fail(f"{junit_path.name}: executed zero testcases")
    for case in cases:
        ident = f"{case.get('classname')}::{case.get('name')}"
        if case.find("skipped") is not None:
            raise _fail(f"{junit_path.name}: skipped testcase {ident}")
        if case.find("failure") is not None or case.find("error") is not None:
            raise _fail(f"{junit_path.name}: failing testcase {ident}")
    return f"zero-skip: {junit_path.name}: {len(cases)} testcases passed, 0 skipped"


def copy_audit_logs(source: Path, destination: Path) -> None:
    """Never overwrite evidence from another suite leg, even if bytes match."""
    guarded_destination = guard_tool_output_path(destination, allow_existing_dir=True)
    for path in sorted(source.glob("*.jsonl")):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"audit log must be a regular file: {path}")
        with path.open("rb") as incoming, (guarded_destination / path.name).open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit-dir", type=Path, default=None)
    parser.add_argument("--manifest", type=Path,
                        default=Path(".github/shard-manifest.json"))
    parser.add_argument(
        "--zero-skip-junit", action="append", type=Path, default=[],
        help="JUnit XML file that must contain >= 1 testcase and 0 skips/failures",
    )
    parser.add_argument(
        "--require-passed-prefix", action="append", default=[],
        help="Collected node-ID prefix that must match >= 1 test and execute without unapproved skips",
    )
    parser.add_argument(
        "--require-mandatory-paired", action="store_true",
        help="Include every mandatory Core/UI paired witness prefix in --require-passed-prefix",
    )
    parser.add_argument(
        "--allow-skip", action="append", default=[],
        help="Allow-listed mandatory skip formatted as NODE_ID=REASON",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.junit_dir is None and not args.zero_skip_junit:
        parser.error("at least one of --junit-dir or --zero-skip-junit is required")
    allow_skips = _parse_allow_skip(args.allow_skip)
    require_prefixes = list(args.require_passed_prefix)
    if args.require_mandatory_paired:
        for prefix in MANDATORY_PAIRED_WITNESS_PREFIXES:
            if prefix not in require_prefixes:
                require_prefixes.append(prefix)
    if args.junit_dir is not None:
        print(check(
            args.junit_dir,
            args.manifest,
            require_passed_prefixes=require_prefixes,
            allow_skips=allow_skips,
        ))
    for path in args.zero_skip_junit:
        print(check_zero_skip_junit(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
