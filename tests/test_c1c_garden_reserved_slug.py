"""C1-C finding: garden.seed.create can mint seeds its own readers never see.

``garden.seed.create`` derives the filename slug from the title (or the first
text line) with no reserved-name check, while the garden reader
(``load_garden``) skips stems named ``readme`` (and dot/underscore names) as
meta files. A seed titled "README" is created and receipted, then invisible
to ``note.content`` by stable id, to ``note.search --type garden-note``, and
to the Nebula projection.

The expected behaviour: the created seed is readable by the stable id the
system itself derives for it (or, equivalently, the create refuses a slug the
reader will never admit). On base main the create succeeds and the read
refuses with unknown-note.
"""

from __future__ import annotations

import json
from pathlib import Path

from gateway_helpers import approved_v2_call, request_artifact_id

from learning_os.derive.garden import garden_id


def _seed(root: Path, tmp: Path, title: str, key: str):
    return approved_v2_call(
        root,
        capability="garden.seed.create",
        payload={"title": title, "text": "An idea worth keeping. #meta\n"},
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key,
    )


def test_created_seed_is_readable_by_its_own_stable_id(mini_repo: Path, tmp_path: Path):  # noqa: ARG001
    proc = _seed(mini_repo, tmp_path, "README", "c1c-garden-readme-001")
    if proc.returncode != 0:
        # A fixed create may refuse a slug the garden reader never admits.
        return
    response = json.loads(proc.stdout)
    seed_path = mini_repo / response["result"]["seed_path"]
    assert seed_path.is_file(), response

    stable_id = garden_id(mini_repo / "knowledge" / "garden", seed_path)

    read = run_capability_query(mini_repo, stable_id)
    # Either the seed is readable through the system's own read capability,
    # or the create above must have refused a slug the reader never admits.
    assert read.returncode == 0, (
        f"seed created at {seed_path} but note.content refuses its stable id "
        f"{stable_id}: {read.stdout} {read.stderr}"
    )
    payload = json.loads(read.stdout)
    assert payload["content_sha256"], payload


def run_capability_query(root: Path, note_id: str):
    import subprocess
    import sys

    los = Path(__file__).resolve().parent.parent / "tools" / "los.py"
    return subprocess.run(
        [sys.executable, str(los), "--root", str(root),
         "note-read", note_id, "--limit", "100"],
        capture_output=True, text=True, timeout=120,
    )
