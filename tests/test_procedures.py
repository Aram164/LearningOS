"""The A8 procedure index and transcript runner (SPEC §7.4, PLAN D11).

S08 chose Scrut. ``INDEX.yaml`` lists every ``## `` heading of
``system/WORKFLOWS.md`` and ``system/OPERATOR.md`` plus the ``## `` headings
of ``system/CLAUDE.md`` sections 2 and 7; every ``procedure`` entry needs an
existing transcript. Each ``system/procedures/*.md`` transcript runs as
``scrut test`` with ``LOS_REPO`` set; the binary path is configured through
``LOS_SCRUT_BIN`` (default: ``.venv/bin/scrut``, where ``make setup``
installs it — see BAKEOFF.md).
"""

from __future__ import annotations

import os
import re
import subprocess
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROCEDURES = ROOT / "system" / "procedures"
INDEX_PATH = PROCEDURES / "INDEX.yaml"
RATCHETS_PATH = ROOT / "tests" / "architecture" / "ratchets.yaml"

CHECK_ID = "A8-transcripts"
FIX = "Update the transcript, or fix the doc command (PLAN D11)."

#: The indexed docs and, for CLAUDE.md, the indexed section numbers.
INDEXED_DOCS = ("system/OPERATOR.md", "system/WORKFLOWS.md", "system/CLAUDE.md")
CLAUDE_SECTIONS = ("2", "7")


def _headings(doc: str) -> list[tuple[str, int]]:
    """Every ``## `` heading of one doc, with its 1-based line number."""
    lines = (ROOT / doc).read_text(encoding="utf-8").splitlines()
    found = [(line, number) for number, line in enumerate(lines, 1)
             if line.startswith("## ")]
    if doc == "system/CLAUDE.md":
        found = [(line, number) for line, number in found
                 if re.match(r"## ([0-9]+)\. ", line)
                 and re.match(r"## ([0-9]+)\. ", line).group(1)
                 in CLAUDE_SECTIONS]
    return found


def _load_index() -> list[dict]:
    data = yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == 1, (
        f"A8 {INDEX_PATH.relative_to(ROOT)}:1: want schema 1 — {FIX}")
    sections = data.get("sections")
    assert isinstance(sections, list), (
        f"A8 {INDEX_PATH.relative_to(ROOT)}:1: want a sections list — {FIX}")
    return sections


def test_index_lists_every_heading():
    sections = _load_index()
    indexed: dict[tuple[str, str], dict] = {}
    failures = []
    for position, entry in enumerate(sections):
        if not isinstance(entry, dict):
            failures.append(
                f"A8 {INDEX_PATH.relative_to(ROOT)}: want a mapping at "
                f"sections[{position}] — {FIX}")
            continue
        doc, heading, classed = (entry.get("doc"), entry.get("heading"),
                                 entry.get("class"))
        if not isinstance(doc, str) or not isinstance(heading, str):
            failures.append(
                f"A8 {INDEX_PATH.relative_to(ROOT)}: sections[{position}] "
                f"needs string doc and heading — {FIX}")
            continue
        if classed not in ("procedure", "rule"):
            failures.append(
                f"A8 {doc}::{heading}: want class procedure|rule — "
                f"{INDEX_PATH.relative_to(ROOT)} sections[{position}] — {FIX}")
            continue
        if (doc, heading) in indexed:
            failures.append(
                f"A8 {doc}::{heading}: indexed twice — "
                f"{INDEX_PATH.relative_to(ROOT)} — {FIX}")
            continue
        indexed[(doc, heading)] = entry
    for doc in INDEXED_DOCS:
        for heading, lineno in _headings(doc):
            if (doc, heading) not in indexed:
                failures.append(
                    f"A8 {doc}::{heading}: heading not indexed — "
                    f"{doc}:{lineno} — {FIX}")
    for (doc, heading) in sorted(indexed):
        if heading not in [line for line, _ in _headings(doc)]:
            failures.append(
                f"A8 {doc}::{heading}: no such heading in {doc} — "
                f"{INDEX_PATH.relative_to(ROOT)} — {FIX}")
    assert not failures, "\n".join(failures)


def _missing_transcripts(sections: list[dict]) -> Counter:
    """``doc::heading`` of every procedure without an existing transcript."""
    missing: Counter = Counter()
    for entry in sections:
        if not isinstance(entry, dict) or entry.get("class") != "procedure":
            continue
        transcript = entry.get("transcript")
        if (not isinstance(transcript, str)
                or not (ROOT / transcript).is_file()):
            missing[f"{entry['doc']}::{entry['heading']}"] += 1
    return missing


def test_every_procedure_has_a_transcript():
    sections = _load_index()
    current = _missing_transcripts(sections)
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            doc, _, heading = signature.partition("::")
            try:
                lineno = next(number for line, number in _headings(doc)
                              if line == heading)
                where = f"{doc}:{lineno}"
            except StopIteration:
                where = INDEX_PATH.relative_to(ROOT).as_posix()
            failures.append(
                f"A8 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — {where} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A8 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)


def _scrut_bin() -> Path:
    configured = os.environ.get("LOS_SCRUT_BIN")
    if configured:
        return Path(configured)
    return ROOT / ".venv" / "bin" / "scrut"


def test_every_transcript_passes():
    transcripts = sorted(
        path for path in PROCEDURES.glob("*.md") if path.is_file())
    assert transcripts, f"no transcripts in {PROCEDURES}"
    scrut = _scrut_bin()
    assert scrut.is_file(), (
        f"scrut binary not found: {scrut} — set LOS_SCRUT_BIN to the v0.5.0"
        " binary, or run the `make setup` addition BAKEOFF.md records")
    for transcript in transcripts:
        env = dict(os.environ, LOS_REPO=str(ROOT), LOS_ARCH_RENDER_CHECK="1")
        proc = subprocess.run(
            [str(scrut), "test", str(transcript)],
            capture_output=True, text=True, timeout=600, env=env, cwd=ROOT)
        assert proc.returncode == 0, (
            f"{transcript.name} failed:\n{proc.stdout}\n{proc.stderr}")
