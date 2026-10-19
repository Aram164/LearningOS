"""Frozen historical test inputs, independent of the repository's Git history.

The manifest records the original commits, Git blobs and SHA-256 digests.
Only test inputs are retained; no historical production code is executed.
"""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from functools import cache
from pathlib import Path, PurePosixPath
from types import MappingProxyType

ROOT = Path(__file__).resolve().parent / "fixtures" / "history"
BASELINES = json.loads((ROOT / "manifest.json").read_text())["baselines"]


@cache
def historical_files(ref: str):
    """Return verified, immutable file bytes from one original test context."""
    baseline = BASELINES[ref]
    archive = (ROOT / baseline["archive"]).read_bytes()
    if hashlib.sha256(archive).hexdigest() != baseline["archive_sha256"]:
        raise ValueError(f"historical input archive checksum mismatch: {ref}")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as stream:
        for entry in stream.getmembers():
            if entry.isdir():
                continue
            path = PurePosixPath(entry.name)
            if (not entry.isfile() or path.is_absolute()
                    or ".." in path.parts or entry.name in files):
                raise ValueError(f"invalid historical input member: {entry.name}")
            data = stream.extractfile(entry).read()
            expected = baseline["files"][entry.name]
            if (len(data) != expected["bytes"]
                    or hashlib.sha256(data).hexdigest() != expected["sha256"]):
                raise ValueError(f"historical input checksum mismatch: {entry.name}")
            files[entry.name] = data
    if files.keys() != baseline["files"].keys():
        raise ValueError(f"historical input inventory mismatch: {ref}")
    return MappingProxyType(files)


def historical_text(ref: str, relpath: str) -> str | None:
    """Preserve an absent historical file as absent, without a Git fallback."""
    data = historical_files(ref).get(relpath)
    return None if data is None else data.decode("utf-8")
