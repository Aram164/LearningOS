"""Snapshot continuation evidence without recapturing or changing the baseline."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

import capture_baseline as baseline
from run_receipt import CORE, HERE, UI, source_identity


def main() -> None:
    expected_inputs = json.loads((HERE / "independent-inputs.json").read_text())
    actual_inputs = baseline.inventory(
        baseline.CORE, baseline.AUTHORED + baseline.OPERATIONAL + (".obsidian",))
    expected_outer = json.loads((HERE / "outer-dirty-inputs.json").read_text())
    actual_outer = baseline.inventory(baseline.OUTER, tuple(expected_outer))
    receipts = {}
    for path in sorted((HERE / "receipts").glob("*/receipt.json")):
        data = json.loads(path.read_text())
        receipts[str(path.relative_to(HERE))] = {
            key: data.get(key) for key in ("exit", "elapsed_seconds", "source_unchanged", "command")}
    report = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {"core": source_identity(CORE), "ui": source_identity(UI)},
        "candidate_status": {
            name: subprocess.run(["git", "status", "--porcelain=v1"], cwd=root,
                                 text=True, capture_output=True, check=True).stdout
            for name, root in (("core", CORE), ("ui", UI))},
        "original_status": {
            name: subprocess.run(["git", "status", "--porcelain=v1"], cwd=root,
                                 text=True, capture_output=True, check=True).stdout
            for name, root in (("core", baseline.CORE), ("ui", baseline.UI))},
        "original_inputs_unchanged": actual_inputs == expected_inputs,
        "original_input_differences": [key for key in sorted(set(actual_inputs) | set(expected_inputs))
                                       if actual_inputs.get(key) != expected_inputs.get(key)],
        "original_outer_dirty_bytes_unchanged": actual_outer == expected_outer,
        "outer_differences": [key for key in sorted(set(actual_outer) | set(expected_outer))
                              if actual_outer.get(key) != expected_outer.get(key)],
        "receipts": receipts,
    }
    destination = HERE / "continuation-state.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in (
        "captured_at", "original_status", "candidate_status", "original_inputs_unchanged",
        "original_input_differences", "original_outer_dirty_bytes_unchanged", "outer_differences")}, indent=2))
    print("Evidence:", destination)


if __name__ == "__main__":
    main()
