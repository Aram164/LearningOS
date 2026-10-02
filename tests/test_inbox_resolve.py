"""The inbox can trend toward empty: resolve routed drops to the archive.

`inbox.resolve` (``inbox-resolve``) moves one named drop — or one file
inside a drop folder — byte-identical to ``archive/inbox/YYYY/``. It
requires the drop's SHA-256 and a non-empty ``routed_to`` list; one
receipt names both endpoints plus ``routed_to``. `INBOX-STALE` considers
each file recursively by its own age, and `inbox-list` reports the age.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import time
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call, file_sha256
from repo_builders import run_los

from learning_os.commands.inbox import _folder_digest
from learning_os.loader import load_repo
from learning_os.rules import validate


def _resolve(mini_repo: Path, key: str, name: str, drop_sha256: str, routed_to: list,
             expected_snapshot: str | None = None):
    year = str(_dt.date.today().year)
    inbox = mini_repo / "work" / "inbox"
    target = inbox / name
    if target.is_dir():
        rels = sorted(path.relative_to(inbox).as_posix()
                      for path in target.rglob("*") if path.is_file())
    else:
        rels = [name]
    artifacts = [f"file:work/inbox/{rel}" for rel in rels]
    artifacts += [f"file:archive/inbox/{year}/{rel}" for rel in rels]
    return approved_v2_call(
        mini_repo,
        capability="inbox.resolve",
        payload={"name": name, "drop_sha256": drop_sha256,
                 "routed_to": routed_to},
        artifact_ids=artifacts,
        idempotency_key=key,
        expected_snapshot=expected_snapshot,
    )


def test_inbox_resolve_moves_a_routed_drop_to_the_archive(mini_repo: Path):
    drop = mini_repo / "work/inbox/20261002-derivation.md"
    drop.write_text("# Derivation\n\nWorked.\n", encoding="utf-8")
    digest = file_sha256(drop)
    proc = _resolve(mini_repo, "inbox-resolve-001", drop.name, digest,
                    ["note-demo"])
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    assert response["result"]["resolved"] == drop.name
    assert response["result"]["routed_to"] == ["note-demo"]
    year = str(_dt.date.today().year)
    archived = mini_repo / f"archive/inbox/{year}/{drop.name}"
    assert not drop.exists()
    assert archived.is_file()
    assert archived.read_bytes() == b"# Derivation\n\nWorked.\n"
    assert response["result"]["archived"] == [f"archive/inbox/{year}/{drop.name}"]
    receipt = yaml.safe_load(
        (mini_repo / response["receipt_path"]).read_text(encoding="utf-8"))
    paths = sorted(row["path"] for row in receipt["writes"])
    assert paths == [f"archive/inbox/{year}/{drop.name}",
                     f"work/inbox/{drop.name}"]
    assert receipt["metadata"]["routed_to"] == ["note-demo"]


def test_inbox_resolve_moves_one_file_inside_a_drop_folder(mini_repo: Path):
    folder = mini_repo / "work/inbox/complaints"
    folder.mkdir()
    (folder / "a.md").write_text("a\n", encoding="utf-8")
    (folder / "b.md").write_text("b\n", encoding="utf-8")
    digest = file_sha256(folder / "a.md")
    proc = _resolve(mini_repo, "inbox-resolve-002", "complaints/a.md", digest,
                    ["#55"])
    assert proc.returncode == 0, proc.stderr
    year = str(_dt.date.today().year)
    assert not (folder / "a.md").exists()
    assert (folder / "b.md").is_file()
    assert (mini_repo / f"archive/inbox/{year}/complaints/a.md").read_bytes() == b"a\n"
    # Resolving the last file prunes the emptied folder, never the inbox.
    digest = file_sha256(folder / "b.md")
    proc = _resolve(mini_repo, "inbox-resolve-003", "complaints/b.md", digest,
                    ["#57"])
    assert proc.returncode == 0, proc.stderr
    assert not folder.exists()
    assert (mini_repo / "work/inbox").is_dir()


def test_inbox_resolve_moves_a_whole_folder(mini_repo: Path):
    folder = mini_repo / "work/inbox/pack"
    folder.mkdir()
    (folder / "one.md").write_bytes(b"one\n")
    (folder / "two.md").write_bytes(b"two\n")
    digest = _folder_digest({"pack/one.md": b"one\n", "pack/two.md": b"two\n"})
    proc = _resolve(mini_repo, "inbox-resolve-004", "pack", digest,
                    ["workspace-demo/scratch"])
    assert proc.returncode == 0, proc.stderr
    year = str(_dt.date.today().year)
    assert not folder.exists()
    assert (mini_repo / f"archive/inbox/{year}/pack/one.md").read_bytes() == b"one\n"
    assert (mini_repo / f"archive/inbox/{year}/pack/two.md").read_bytes() == b"two\n"


def test_inbox_resolve_refuses_a_changed_drop(mini_repo: Path):
    drop = mini_repo / "work/inbox/note.md"
    drop.write_text("first\n", encoding="utf-8")
    digest = file_sha256(drop)
    drop.write_text("second\n", encoding="utf-8")
    proc = _resolve(mini_repo, "inbox-resolve-005", drop.name, digest,
                    ["note-demo"])
    assert proc.returncode == 2
    assert "changed since read" in json.loads(proc.stdout)["error"]["message"]
    assert drop.read_text(encoding="utf-8") == "second\n"
    year = str(_dt.date.today().year)
    assert not (mini_repo / "archive/inbox" / year / drop.name).exists()


def test_inbox_resolve_refuses_a_stale_snapshot(mini_repo: Path):
    drop = mini_repo / "work/inbox/note.md"
    drop.write_text("first\n", encoding="utf-8")
    proc = _resolve(mini_repo, "inbox-resolve-006", drop.name,
                    file_sha256(drop), ["note-demo"],
                    expected_snapshot="sha256:" + "0" * 64)
    assert proc.returncode == 3
    assert json.loads(proc.stdout)["error"]["code"] == "STALE_SNAPSHOT"
    assert drop.is_file()


def test_inbox_resolve_requires_a_routed_to_destination(mini_repo: Path):
    drop = mini_repo / "work/inbox/note.md"
    drop.write_text("first\n", encoding="utf-8")
    proc = _resolve(mini_repo, "inbox-resolve-007", drop.name,
                    file_sha256(drop), [])
    assert proc.returncode == 2
    assert "non-empty routed_to" in json.loads(proc.stdout)["error"]["message"]
    assert drop.is_file()


def test_inbox_resolve_never_overwrites_the_archive(mini_repo: Path):
    drop = mini_repo / "work/inbox/note.md"
    drop.write_text("first\n", encoding="utf-8")
    year = str(_dt.date.today().year)
    held = mini_repo / "archive/inbox" / year / drop.name
    held.parent.mkdir(parents=True)
    held.write_text("held\n", encoding="utf-8")
    proc = _resolve(mini_repo, "inbox-resolve-008", drop.name,
                    file_sha256(drop), ["note-demo"])
    assert proc.returncode == 2
    assert "never overwrites" in json.loads(proc.stdout)["error"]["message"]
    assert held.read_text(encoding="utf-8") == "held\n"
    assert drop.is_file()


def test_inbox_resolve_without_an_envelope_refuses(mini_repo: Path):
    drop = mini_repo / "work/inbox/note.md"
    drop.write_text("first\n", encoding="utf-8")
    proc = run_los(mini_repo, "inbox-resolve", drop.name,
                   "--drop-sha256", file_sha256(drop),
                   "--routed-to", "note-demo")
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
    assert drop.is_file()


def _backdate(path: Path, days: int) -> None:
    stamp = time.time() - days * 86400
    os.utime(path, (stamp, stamp))


def test_inbox_stale_flags_an_old_file_nested_in_a_subfolder(mini_repo: Path):
    folder = mini_repo / "work/inbox/complaints"
    folder.mkdir()
    old = folder / "old.md"
    old.write_text("old\n", encoding="utf-8")
    fresh = mini_repo / "work/inbox/fresh.md"
    fresh.write_text("fresh\n", encoding="utf-8")
    _backdate(old, 20)
    issues = validate(load_repo(mini_repo), online=False)
    stale = [issue for issue in issues if issue.code == "INBOX-STALE"]
    assert len(stale) == 1
    assert "complaints/old.md" in stale[0].message
    assert "20 days old" in stale[0].message


def test_inbox_list_reports_each_files_age(mini_repo: Path):
    inbox = mini_repo / "work/inbox"
    (inbox / "fresh.md").write_text("fresh\n", encoding="utf-8")
    old = inbox / "old.md"
    old.write_text("old\n", encoding="utf-8")
    _backdate(old, 20)
    proc = run_los(mini_repo, "inbox-list")
    assert proc.returncode == 0, proc.stderr
    rows = {row["id"]: row for row in json.loads(proc.stdout)}
    assert rows["fresh.md"]["age_days"] == 0
    assert rows["old.md"]["age_days"] == 20
    assert all("age_days" in row for row in rows.values())
