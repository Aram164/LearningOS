"""Run every procedure transcript with the bake-off winner (SPEC §7.4, PLAN D11).

S08 chose Scrut. Each ``system/procedures/*.md`` transcript runs as
``scrut test`` with ``LOS_REPO`` set; the binary path is configured through
``LOS_SCRUT_BIN`` (default: ``.venv/bin/scrut``, where ``make setup``
installs it — see BAKEOFF.md). The INDEX checks arrive in S09.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCEDURES = ROOT / "system" / "procedures"


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
        env = dict(os.environ, LOS_REPO=str(ROOT))
        proc = subprocess.run(
            [str(scrut), "test", str(transcript)],
            capture_output=True, text=True, timeout=600, env=env, cwd=ROOT)
        assert proc.returncode == 0, (
            f"{transcript.name} failed:\n{proc.stdout}\n{proc.stderr}")
