"""Local-only attachments: pinned scans kept on disk but out of Git."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from learning_os.contracts import local_attachments
from learning_os.loader import load_repo
from learning_os.rules import validate

SCAN = "knowledge/attachments/note-demo/scan.pdf"
SCAN_BYTES = b"%PDF-1.4 handwritten pages\n"


def _note_with_attachment(root: Path) -> None:
    note = root / "knowledge/notes/mathematics/note-demo.md"
    text = note.read_text(encoding="utf-8")
    note.write_text(text.replace(
        "sources: [source-demo-book]\n",
        f"sources: [source-demo-book]\nattachments:\n  - {SCAN}\n", 1), encoding="utf-8")
    (root / SCAN).parent.mkdir(parents=True, exist_ok=True)
    (root / SCAN).write_bytes(SCAN_BYTES)


def _declare(root: Path, rel: str = SCAN, data: bytes = SCAN_BYTES) -> None:
    (root / local_attachments.LOCAL_ATTACHMENTS_RELATIVE).write_text(
        "schema_version: 1\ncontract: learningos-local-attachments\nfiles:\n"
        f"  {rel}:\n    bytes: {len(data)}\n"
        f"    sha256: sha256:{hashlib.sha256(data).hexdigest()}\n",
        encoding="utf-8")


def _codes(root: Path) -> dict[str, str]:
    return {issue.code: issue.severity
            for issue in validate(load_repo(root), online=False)
            if issue.code.startswith("ATTACH")}


@pytest.fixture
def scanned(mini_repo: Path) -> Path:
    _note_with_attachment(mini_repo)
    _declare(mini_repo)
    return mini_repo


def test_present_pinned_scan_is_clean(scanned: Path):
    assert _codes(scanned) == {}


def test_absent_pinned_scan_warns_instead_of_attach_missing(scanned: Path):
    (scanned / SCAN).unlink()
    assert _codes(scanned) == {"ATTACH-LOCAL-ABSENT": "W"}


def test_without_a_pin_an_absent_scan_is_still_attach_missing(mini_repo: Path):
    _note_with_attachment(mini_repo)
    (mini_repo / SCAN).unlink()
    assert _codes(mini_repo) == {"ATTACH-MISSING": "E"}


@pytest.mark.parametrize("damage", [
    lambda path: path.write_bytes(SCAN_BYTES + b"edited"),
    lambda path: path.write_bytes(SCAN_BYTES.replace(b"pages", b"PAGES")),
], ids=["size-changed", "same-size-bytes-changed"])
def test_changed_pinned_scan_is_an_error(scanned: Path, damage):
    damage(scanned / SCAN)
    assert _codes(scanned) == {"ATTACH-LOCAL-CHANGED": "E"}


def test_a_pin_no_note_owns_is_an_error(mini_repo: Path):
    (mini_repo / "knowledge/attachments/note-demo").mkdir(parents=True)
    (mini_repo / SCAN).write_bytes(SCAN_BYTES)
    _declare(mini_repo)
    codes = _codes(mini_repo)
    assert codes["ATTACH-LOCAL-ORPHAN"] == "E"


def test_an_unreadable_declaration_is_an_error_not_an_empty_list(scanned: Path):
    (scanned / local_attachments.LOCAL_ATTACHMENTS_RELATIVE).write_text(
        "schema_version: 1\ncontract: something-else\nfiles: {}\n", encoding="utf-8")
    codes = _codes(scanned)
    assert codes.get("ATTACH-LOCAL-UNREADABLE") == "E"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)


def test_git_must_ignore_and_not_track_a_pinned_scan(scanned: Path):
    _git(scanned, "init", "-q")
    assert _codes(scanned)["ATTACH-LOCAL-UNIGNORED"] == "E"
    (scanned / ".gitignore").write_text(f"/{SCAN}\n", encoding="utf-8")
    assert "ATTACH-LOCAL-UNIGNORED" not in _codes(scanned)
    _git(scanned, "add", "-f", SCAN)
    assert _codes(scanned)["ATTACH-LOCAL-TRACKED"] == "E"
    _git(scanned, "rm", "--cached", "-q", SCAN)
    assert _codes(scanned) == {}


def test_the_real_declaration_pins_exactly_the_handwritten_scans(repo_root: Path):
    declared = local_attachments.load(repo_root)
    assert declared, "the repository declares its local-only scans"
    for rel in declared:
        assert rel.startswith("knowledge/attachments/") and rel.endswith(".pdf")
    ignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
    for rel in declared:
        assert f"/{rel}" in ignore
