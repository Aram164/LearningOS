"""Check every digest the scenario fixtures pin, against the bytes they name.

The F-05 re-pin moved the world's fingerprint, and with it every fixture
that pins one. Two of those pins are *derived* from a file the re-pin
itself changed, so they have to be recomputed in dependency order: a
delivery record's own digest changes when its precondition moves, and an
envelope's approval-subject digest changes when the envelope's own
snapshot pin moves. Get that order wrong and the scenario silently becomes
a refusal — which is exactly what happened, and what the repository's A5
and A13 gates caught.

This script reads the repository and writes nothing. It reports, per pin,
the value the fixture names and the value the named bytes actually have.

Usage: .venv/bin/python check_pins.py [expected world fingerprint]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repository"
sys.path.insert(0, str(ROOT / "tools"))

from learning_os.store.contracts.gateway import intent_sha256  # noqa: E402

CASES = ROOT / "tests" / "scenarios" / "cases"
FILES = ROOT / "tests" / "scenarios" / "files"
#: Pins that are deliberately wrong: the mismatch and refusal fixtures.
DELIBERATELY_WRONG = {
    "sha256:" + "0" * 64,
}


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    expected_world = sys.argv[1] if len(sys.argv) > 1 else ""
    problems: list[str] = []

    for case_path in sorted(CASES.glob("*.yaml")):
        text = case_path.read_text(encoding="utf-8")
        # Every case names its own casedata directory: <operation>/<case-id>.
        for case_id in re.findall(r"^\s*- id: (\S+)", text, re.MULTILINE):
            casedata = FILES / case_path.stem / case_id
            if not casedata.is_dir():
                continue
            for delivery in casedata.glob("**/delivery.yaml"):
                pinned = _pin_for(text, delivery)
                if pinned is None or pinned in DELIBERATELY_WRONG:
                    continue
                actual = sha256_file(delivery)
                if actual != pinned:
                    problems.append(
                        f"{case_path.name} [{case_id}]: pins {pinned}\n"
                        f"    {delivery.relative_to(ROOT)} is {actual}")

    for envelope_path in sorted(FILES.glob("**/*.json")):
        try:
            envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(envelope, dict):
            continue
        approval = envelope.get("approval")
        if not isinstance(approval, dict):
            continue
        pinned = approval.get("subject_sha256")
        if not isinstance(pinned, str) or pinned in DELIBERATELY_WRONG:
            continue
        actual = intent_sha256(envelope)
        if actual != pinned:
            problems.append(
                f"{envelope_path.relative_to(ROOT)}: approval.subject_sha256 "
                f"is {pinned}\n    the envelope's intent is {actual}")

    if expected_world:
        for path in sorted(list(FILES.rglob("*.json")) + list(FILES.rglob("*.yaml"))
                           + list(CASES.glob("*.yaml"))):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(
                    r'(expected_snapshot|snapshot_id): "?(sha256:[0-9a-f]{64})"?', text):
                value = match.group(2)
                if value in DELIBERATELY_WRONG:
                    continue
                if value != expected_world:
                    problems.append(
                        f"{path.relative_to(ROOT)}: {match.group(1)} is {value}, "
                        f"the world is {expected_world}")

    for problem in problems:
        print(problem)
    print(f"{len(problems)} pin(s) disagree")
    return 0 if not problems else 1


def _pin_for(case_text: str, delivery: Path) -> str | None:
    """The digest the case file pins for this delivery record, if any."""
    for match in re.finditer(r'delivery_sha256: "?(sha256:[0-9a-f]{64})"?', case_text):
        return match.group(1)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
