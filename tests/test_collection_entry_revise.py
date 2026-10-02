"""Guarded one-line correction for a curated collection entry.

`collection.entry.revise` is the narrow answer to the 2026-09-29 collection
complaint: after the Grinstead attachment, `math-bookshelf.yaml` still
claimed the download had never landed, and the only correction path was an
unguarded file edit. This capability revises one existing entry's `why` —
nothing else — under the standard check/approve/receipt machinery.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call
from repo_builders import run_los, write_yaml

from learning_os.genout import generate_all
from learning_os.loader import load_repo

HEADER = "# Curated demo shelf.\n"
OLD_WHY = "The demo book — download never landed."
NEW_WHY = "The demo book — local PDF, Chapter 4 covers conditioning."


def _ensure_paper(root: Path) -> None:
    registry_path = root / "sources" / "sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if "source-demo-paper" not in {s["id"] for s in registry["sources"]}:
        registry["sources"].append({
            "id": "source-demo-paper", "title": "Demo Paper", "type": "paper",
            "authors": ["P. Apier"],
            "evaluations": [{"concepts": ["concept-expected-value"],
                             "roles": ["first-learning"],
                             "level": "introductory",
                             "strengths": ["a crisp derivation"]}],
        })
        write_yaml(registry_path, registry)


def _shelf(root: Path, entries=None) -> Path:
    path = root / "sources" / "collections" / "demo-bookshelf.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"title": "Demo bookshelf", "entries": entries or [
        {"source": "source-demo-book", "group": "demo-group", "why": OLD_WHY},
        {"source": "source-demo-paper", "group": "demo-group",
         "why": "An unrelated entry."},
    ]}
    path.write_text(HEADER + yaml.safe_dump(body, sort_keys=False),
                    encoding="utf-8")
    _ensure_paper(root)
    return path


def _package(tmp_path: Path, record: dict) -> Path:
    path = tmp_path / "collection-revise.yaml"
    write_yaml(path, record)
    return path


def _revise(**changes):
    value = {"collection": "demo-bookshelf", "source": "source-demo-book",
             "why": NEW_WHY}
    value.update(changes)
    return value


def _check(root: Path, package: Path):
    proc = run_los(root, "collection-entry-revise", "--file", str(package),
                   "--check")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


def _refuses(root: Path, package: Path, fragment: str):
    proc = run_los(root, "collection-entry-revise", "--file", str(package),
                   "--check")
    assert proc.returncode == 2, proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is False
    assert fragment in body["error"], body["error"]


# --------------------------------------------------------------------- check
def test_check_reports_the_line_change_and_writes_nothing(mini_repo, tmp_path):
    target = _shelf(mini_repo)
    before = target.read_bytes()
    body = _check(mini_repo, _package(tmp_path, _revise()))
    assert body["check"] is True
    assert body["diff_sha256"].startswith("sha256:")
    assert body["artifact_ids"] == ["collection:demo-bookshelf"]
    assert body["expected_revisions"] == {"collection:demo-bookshelf": 0}
    (row,) = body["diff"]
    assert row == {"collection": "demo-bookshelf",
                   "source": "source-demo-book", "group": "demo-group",
                   "before": OLD_WHY, "after": NEW_WHY}
    assert target.read_bytes() == before


def test_revise_refuses_unknown_and_ambiguous_targets(mini_repo, tmp_path):
    _shelf(mini_repo)
    _refuses(mini_repo, _package(tmp_path, _revise(collection="no-shelf")),
             "unknown collection")
    _refuses(mini_repo, _package(tmp_path, _revise(source="source-ghost")),
             "no entry for source")
    _shelf(mini_repo, entries=[
        {"source": "source-demo-book", "group": "a", "why": "First."},
        {"source": "source-demo-book", "group": "b", "why": "Second."},
    ])
    _refuses(mini_repo, _package(tmp_path, _revise()),
             "matches 2 entries")


def test_revise_refuses_noop_foreign_and_misshapen_lines(mini_repo, tmp_path):
    _shelf(mini_repo)
    _refuses(mini_repo, _package(tmp_path, _revise(why=OLD_WHY)), "no change")
    _refuses(mini_repo, _package(tmp_path, _revise(group="other")),
             "outside the revise allowlist")
    _refuses(mini_repo, _package(tmp_path, _revise(why="   ")),
             "nonempty one-line")
    _refuses(mini_repo, _package(tmp_path, _revise(why="line one\nline two")),
             "one-line")
    _refuses(mini_repo, _package(tmp_path, {"collection": "demo-bookshelf"}),
             "needs 'collection', 'source' and 'why'")


# --------------------------------------------------------------------- apply
def test_apply_rewrites_one_line_and_preserves_the_rest(mini_repo, tmp_path):
    target = _shelf(mini_repo)
    before = target.read_bytes()
    record = _revise()
    checked = _check(mini_repo, _package(tmp_path, record))
    proc = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": record,
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-apply")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is True
    assert body["receipt_path"].endswith(".yaml")
    text = target.read_text(encoding="utf-8")
    assert text.startswith(HEADER)
    doc = yaml.safe_load(text)
    assert [e["source"] for e in doc["entries"]] == [
        "source-demo-book", "source-demo-paper"]
    assert doc["entries"][0] == {"source": "source-demo-book",
                                 "group": "demo-group", "why": NEW_WHY}
    assert doc["entries"][1] == {"source": "source-demo-paper",
                                 "group": "demo-group",
                                 "why": "An unrelated entry."}
    old_lines = before.decode("utf-8").splitlines(keepends=True)
    new_lines = text.splitlines(keepends=True)
    changes = [(tag, old_lines[i1:i2], new_lines[j1:j2])
               for tag, i1, i2, j1, j2
               in difflib.SequenceMatcher(None, old_lines, new_lines).get_opcodes()
               if tag != "equal"]
    assert len(changes) == 1
    tag, removed, added = changes[0]
    assert tag == "replace" and len(removed) == len(added) == 1
    # The fixture stores the old line escaped; the new line is literal UTF-8.
    assert "download never landed." in removed[0]
    assert NEW_WHY in added[0]
    revisions = yaml.safe_load(
        (mini_repo / "operations" / "transactions" / "revisions.yaml")
        .read_text(encoding="utf-8"))
    assert revisions["revisions"]["collection:demo-bookshelf"] == 1
    stored = yaml.safe_load(
        (mini_repo / "sources" / "sources.yaml").read_text(encoding="utf-8"))
    assert all("local PDF" not in str(s) for s in stored["sources"])


def test_approved_edit_raises_the_projected_revision(mini_repo, tmp_path):
    _shelf(mini_repo)
    record = _revise()
    checked = _check(mini_repo, _package(tmp_path, record))
    before = json.loads(
        generate_all(load_repo(mini_repo), generated_at="T1")["manifest.json"])
    shelf_before = next(row for row in before["records"]
                        if row["type"] == "collection"
                        and row["id"] == "demo-bookshelf")
    assert shelf_before["revision"] == 0
    proc = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": record,
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-revision")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    after = json.loads(
        generate_all(load_repo(mini_repo), generated_at="T2")["manifest.json"])
    shelf_after = next(row for row in after["records"]
                       if row["type"] == "collection"
                       and row["id"] == "demo-bookshelf")
    assert shelf_after["revision"] == 1


def test_apply_replaces_only_the_target_scalar(mini_repo, tmp_path):
    target = mini_repo / "sources" / "collections" / "demo-bookshelf.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# Curated demo shelf.\n"
        "# A second header line stays put.\n"
        "\n"
        'title: "Demo bookshelf"\n'
        "entries:\n"
        "  - source: source-demo-book\n"
        "    group: demo-group\n"
        "    why: >-  # target header note\n"
        "      The demo book —\n"
        "      download never landed.\n"
        "  - source: source-demo-paper\n"
        "    group: demo-group  # neighbor trailing note\n"
        "    why: >-\n"
        "      An unrelated folded\n"
        "      entry.\n",
        encoding="utf-8")
    _ensure_paper(mini_repo)
    record = _revise()
    checked = _check(mini_repo, _package(tmp_path, record))
    (row,) = checked["diff"]
    assert row["before"] == "The demo book — download never landed."
    proc = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": record,
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-splice")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert target.read_text(encoding="utf-8") == (
        "# Curated demo shelf.\n"
        "# A second header line stays put.\n"
        "\n"
        'title: "Demo bookshelf"\n'
        "entries:\n"
        "  - source: source-demo-book\n"
        "    group: demo-group\n"
        "    why: The demo book — local PDF, Chapter 4 covers conditioning."
        "  # target header note\n"
        "  - source: source-demo-paper\n"
        "    group: demo-group  # neighbor trailing note\n"
        "    why: >-\n"
        "      An unrelated folded\n"
        "      entry.\n")


def test_apply_normalizes_crlf_endings(mini_repo, tmp_path):
    target = mini_repo / "sources" / "collections" / "demo-bookshelf.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(
        b"title: Demo\r\nentries:\r\n"
        b"  - source: source-demo-book\r\n    group: demo-group\r\n"
        b"    why: Old line.\r\n")
    _ensure_paper(mini_repo)
    record = _revise()
    checked = _check(mini_repo, _package(tmp_path, record))
    proc = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": record,
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-crlf")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    # Content and layout survive; endings follow the system's universal
    # governed-write normalization, like every other capability.
    assert target.read_bytes() == (
        b"title: Demo\nentries:\n"
        b"  - source: source-demo-book\n    group: demo-group\n"
        b"    why: " + NEW_WHY.encode("utf-8") + b"\n")


def test_apply_preserves_a_missing_final_newline(mini_repo, tmp_path):
    target = mini_repo / "sources" / "collections" / "demo-bookshelf.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "title: Demo\nentries:\n"
        "  - source: source-demo-book\n    group: demo-group\n"
        "    why: Old line.", encoding="utf-8")
    _ensure_paper(mini_repo)
    record = _revise(why="New line.")
    checked = _check(mini_repo, _package(tmp_path, record))
    proc = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": record,
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-noeol")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    raw = target.read_bytes()
    assert not raw.endswith(b"\n")
    assert yaml.safe_load(raw.decode("utf-8"))["entries"][0]["why"] == \
        "New line."


def test_apply_needs_its_check_diff(mini_repo, tmp_path):
    _shelf(mini_repo)
    checked = _check(mini_repo, _package(tmp_path, _revise()))
    missing = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": _revise()}, artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-no-diff")
    inner = json.loads(json.loads(missing.stdout)["error"]["message"])
    assert inner["ok"] is False
    assert "expected-diff-sha256" in inner["error"]
    last = checked["diff_sha256"][-1]
    wrong = checked["diff_sha256"][:-1] + ("0" if last != "0" else "1")
    stale = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": _revise(), "expected_diff_sha256": wrong},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-wrong-diff")
    outer = json.loads(stale.stdout)["error"]["message"]
    assert "changed since check" in json.loads(outer)["error"]


def test_apply_refuses_a_line_changed_after_check(mini_repo, tmp_path):
    target = _shelf(mini_repo)
    checked = _check(mini_repo, _package(tmp_path, _revise()))
    doc = yaml.safe_load(target.read_text(encoding="utf-8"))
    doc["entries"][0]["why"] = "Someone else rewrote this."
    target.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    proc = approved_v2_call(
        mini_repo, capability="collection.entry.revise",
        payload={"record": _revise(),
                 "expected_diff_sha256": checked["diff_sha256"]},
        artifact_ids=["collection:demo-bookshelf"],
        idempotency_key="collection-raced")
    outer = json.loads(proc.stdout)["error"]["message"]
    assert "changed since check" in json.loads(outer)["error"]
