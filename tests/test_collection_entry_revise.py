"""Guarded one-line correction for a curated collection entry.

`collection.entry.revise` is the narrow answer to the 2026-09-29 collection
complaint: after the Grinstead attachment, `math-bookshelf.yaml` still
claimed the download had never landed, and the only correction path was an
unguarded file edit. This capability revises one existing entry's `why` —
nothing else — under the standard check/approve/receipt machinery.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call
from repo_builders import run_los, write_yaml

HEADER = "# Curated demo shelf.\n"
OLD_WHY = "The demo book — download never landed."
NEW_WHY = "The demo book — local PDF, Chapter 4 covers conditioning."


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
    revisions = yaml.safe_load(
        (mini_repo / "operations" / "transactions" / "revisions.yaml")
        .read_text(encoding="utf-8"))
    assert revisions["revisions"]["collection:demo-bookshelf"] == 1
    stored = yaml.safe_load(
        (mini_repo / "sources" / "sources.yaml").read_text(encoding="utf-8"))
    assert all("local PDF" not in str(s) for s in stored["sources"])


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
