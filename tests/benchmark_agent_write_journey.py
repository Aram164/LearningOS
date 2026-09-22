"""Measure a cold-start, governed unit write on a disposable LearningOS fixture.

Run with the repository Python: ``python tests/benchmark_agent_write_journey.py``.
Each capability gets a fresh fixture and eight real CLI calls: discovery, brief
bootstrap, capability definition, unit context, bare-command refusal, approved
write, exact-key replay, and inspection. Bytes are CLI stdout plus stderr, not
model tokens. This is a stable synthetic baseline, not a live-vault cost claim.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOS = ROOT / "tools/los.py"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

from conftest import build_mini_repo  # noqa: E402
from repo_builders import _add_material_overview, add_curriculum  # noqa: E402

from learning_os.contracts.gateway import intent_sha256  # noqa: E402

JOURNEYS = (
    ("unit.source-selection.set", "unit-source-selection",
     ["unit-demo-l01", "source-demo-book", "lecture-01.pdf", "select",
      "--purpose", "Use the worked derivation."],
     {"unit_id": "unit-demo-l01", "source_id": "source-demo-book",
      "locator": "lecture-01.pdf", "action": "select",
      "purpose": "Use the worked derivation."}, ["unit-demo-l01"]),
    ("unit.note.append", "unit-note",
     ["unit-demo-l01", "--title", "Expected value session", "--text",
      "I connected the weighted sum to the lecture.", "--stage-id", "stage-demo"],
     {"unit_id": "unit-demo-l01", "title": "Expected value session",
      "text": "I connected the weighted sum to the lecture.",
      "stage_id": ["stage-demo"]}, ["unit-demo-l01"]),
    ("stage.progress.update", "stage-progress",
     ["unit-demo-l01", "stage-demo", "complete"],
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "status": "complete"}, ["unit-demo-l01", "study-map-demo-l01"]),
    ("source.feedback.record", "source-feedback",
     ["unit-demo-l01", "stage-demo", "source-demo-book", "too-advanced",
      "--note", "Return after the lecture."],
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "source_id": "source-demo-book", "feedback": "too-advanced",
      "note": "Return after the lecture."},
     ["unit-demo-l01", "study-map-demo-l01"]),
    ("detour.create", "detour-create",
     ["unit-demo-l01", "stage-demo", "--title", "Review finite sums",
      "--classification", "required-now"],
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "title": "Review finite sums", "classification": "required-now"},
     ["unit-demo-l01", "study-map-demo-l01"]),
)


def invoke(root: Path, *args: str, stdin: str | None = None) -> tuple[dict, int, float, int]:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        input=stdin, capture_output=True, text=True, timeout=120,
    )
    elapsed = time.perf_counter() - started
    size = len(proc.stdout.encode("utf-8")) + len(proc.stderr.encode("utf-8"))
    try:
        body = json.loads(proc.stdout)
    except json.JSONDecodeError:
        body = {"stdout": proc.stdout, "stderr": proc.stderr}
    return body, size, elapsed, proc.returncode


def one_journey(capability: str, command: str, cli_args: list[str],
                payload: dict, owners: list[str]) -> dict:
    with tempfile.TemporaryDirectory(prefix="los-write-journey-") as scratch:
        root = build_mini_repo(Path(scratch))
        add_curriculum(root)
        if capability == "unit.source-selection.set":
            _add_material_overview(root)
            unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
            unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
            unit["source_selections"] = []
            unit_path.write_text(yaml.safe_dump(unit, sort_keys=False), encoding="utf-8")

        calls: list[dict] = []

        def step(name: str, *args: str, stdin: str | None = None) -> tuple[dict, int]:
            body, size, seconds, code = invoke(root, *args, stdin=stdin)
            calls.append({"step": name, "bytes": size, "seconds": round(seconds, 3),
                          "exit_code": code})
            return body, code

        _index, code = step("capability_index", "capabilities", "--compact", "--json")
        assert code == 0
        bootstrap, code = step("brief_bootstrap", "bootstrap", "--brief")
        assert code == 0
        definition, code = step("capability_definition", "capabilities", capability, "--json")
        assert code == 0 and capability in definition["commands"]
        context, code = step("unit_context", "plan-edit-context", "unit-demo-l01", "--brief")
        assert code == 0 and context["snapshot_id"] == bootstrap["snapshot_id"]
        revisions = context["artifact_revisions"]
        assert set(owners) <= set(revisions)

        _refusal, code = step("bare_refusal", command, *cli_args)
        assert code != 0

        envelope = {
            "schema_version": 2,
            "request_id": f"request-journey-{capability}",
            "idempotency_key": f"journey-{capability}",
            "capability": capability,
            "channel": "operator",
            "expected_snapshot": bootstrap["snapshot_id"],
            "expected_revisions": {owner: revisions[owner] for owner in owners},
            "payload": payload,
            "approval": {"kind": "operator-approval", "subject_sha256": ""},
        }
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
        encoded = json.dumps(envelope)
        applied, code = step("gateway_write", "capability", capability,
                             "--payload-file", "-", stdin=encoded)
        assert code == 0 and applied["ok"] is True, applied
        receipt = applied["receipt_path"]
        assert (root / receipt).is_file()

        replay, code = step("exact_key_replay", "capability", capability,
                            "--payload-file", "-", "--replay-only", stdin=encoded)
        assert code == 0 and replay["ok"] is True, replay
        assert replay["receipt_path"] == receipt
        inspected, code = step("post_write_inspect", "inspect", "unit-demo-l01",
                               "study-map-demo-l01")
        assert code == 0 and inspected["snapshot_id"] != bootstrap["snapshot_id"]

        read_steps = {"capability_index", "brief_bootstrap",
                      "capability_definition", "unit_context"}
        return {
            "capability": capability,
            "calls": len(calls),
            "read_calls": len(read_steps),
            "read_bytes": sum(row["bytes"] for row in calls if row["step"] in read_steps),
            "total_response_bytes": sum(row["bytes"] for row in calls),
            "receipt": True,
            "exact_key_replay": True,
            "steps": calls,
        }


def main() -> None:
    rows = [one_journey(*item) for item in JOURNEYS]
    print(json.dumps({"fixture": "fresh synthetic LearningOS repository per capability",
                      "measurement": "CLI stdout+stderr UTF-8 bytes; no model tokens",
                      "journeys": rows}, indent=2))


if __name__ == "__main__":
    main()
