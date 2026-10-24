"""C1-D finding: capture.create's file branch can overwrite an earlier capture.

``capture.create`` promises "original input is preserved" (capabilities.yaml)
and never overwrites: the text branch loops for a free name
(``while target.exists()``), and every other writer in this handler refuses an
existing destination. The file branch instead takes exactly ONE fallback name
— ``{stamp}-{src.name}`` — and then keeps it even when that fallback already
exists. The transaction engine overwrites by design (``_apply`` replaces the
live bytes it just backed up), so a third file capture with the same basename
inside the same clock second silently replaces the second capture's bytes while
its receipt still points at that path with its own content binding.

The frozen clock (LOS_OBSERVATIONS, the production override for
characterization) stands in for "three captures within one wall-clock second",
which real sequential use reaches easily: each capture is a fast subprocess.

Expected: the third capture refuses, or the file the second capture receipted
still carries the second capture's bytes. Observed on base main (d6c47790):
the third capture succeeds and replaces them.
"""

from __future__ import annotations

import json
from pathlib import Path

from gateway_helpers import approved_v2_call, file_sha256, request_artifact_id


def test_same_second_file_capture_never_overwrites_an_earlier_capture(
        mini_repo: Path, tmp_path: Path, monkeypatch):
    root = mini_repo
    override = tmp_path / "observations.json"
    override.write_text(json.dumps({"now": "2026-10-24T12:00:00"}), encoding="utf-8")
    monkeypatch.setenv("LOS_OBSERVATIONS", str(override))

    bodies = {1: b"alpha capture\n", 2: b"beta capture\n", 3: b"gamma capture\n"}
    sources: dict[int, Path] = {}
    for index, body in bodies.items():
        source = tmp_path / "external" / f"v{index}" / "notes.md"
        source.parent.mkdir(parents=True)
        source.write_bytes(body)
        sources[index] = source

    procs = {}
    for index in (1, 2, 3):
        key = f"c1d-capture-file-{index:03d}"
        procs[index] = approved_v2_call(
            root,
            capability="capture.create",
            payload={"file": str(sources[index]),
                     "file_sha256": file_sha256(sources[index])},
            artifact_ids=[request_artifact_id("capture.create", key)],
            idempotency_key=key,
        )

    assert procs[1].returncode == 0, procs[1].stdout + procs[1].stderr
    assert procs[2].returncode == 0, procs[2].stdout + procs[2].stderr
    second_relative = json.loads(procs[2].stdout)["result"]["captured"]
    second_file = root / second_relative

    # Fix-agnostic: the third capture must refuse, or the second capture's
    # receipted file must still hold the second capture's exact bytes.
    assert procs[3].returncode != 0 or second_file.read_bytes() == bodies[2], (
        f"the third same-second capture of 'notes.md' (rc={procs[3].returncode}) "
        f"replaced the bytes of the second capture's file {second_relative}; "
        "capture.create must never overwrite an earlier capture's bytes "
        "(the capability promises the original input is preserved, and the "
        "text branch loops for a free name to exactly that end)"
    )
