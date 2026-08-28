"""Deterministic, no-AI Garden seed creation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_call, request_artifact_id

from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo


def run_los(
    repo_root: Path,
    mini_repo: Path,
    *args: str,
    stdin: str | None = None,
):
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root",
            str(mini_repo),
            *args,
        ],
        cwd=repo_root,
        text=True,
        input=stdin,
        capture_output=True,
    )


def test_garden_seed_capability_creates_only_a_freeform_seed(
    mini_repo: Path,
):
    key = "garden-seed-decorator-001"
    result = approved_v2_call(
        mini_repo,
        capability="garden.seed.create",
        payload={
            "title": "Decorator idea",
            "text": "The registration happens before normal execution. #python",
        },
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key,
    )

    assert result.returncode == 0, result.stderr

    response = json.loads(result.stdout)

    assert response["ok"] is True
    assert response["capability"] == "garden.seed.create"
    assert response["transaction_id"]
    assert response["receipt_path"].startswith(
        "operations/transactions/"
    )

    seed_path = response["result"]["seed_path"]
    seed = mini_repo / seed_path

    assert seed_path == "knowledge/garden/decorator-idea.md"
    assert seed.read_text(encoding="utf-8") == (
        "# Decorator idea\n\n"
        "The registration happens before normal execution. #python\n"
    )

    # Garden and Inbox are different mental modes.
    assert list((mini_repo / "work/inbox").iterdir()) == []

    # The mechanical write must not manufacture an AI request.
    requests = mini_repo / "operations/ai-actions/requests"
    assert (
        not requests.exists()
        or not list(requests.glob("*.yaml"))
    )

    receipt = yaml.safe_load(
        (mini_repo / response["receipt_path"]).read_text(
            encoding="utf-8"
        )
    )

    assert receipt["capability"] == "garden.seed.create"
    assert [row["path"] for row in receipt["writes"]] == [
        seed_path,
    ]

    # Publication may expose the seed, but no semantic decision was required.
    manifest = json.loads(
        (mini_repo / "generated/manifest.json").read_text(
            encoding="utf-8"
        )
    )
    projected = next(
        row
        for row in manifest["garden_entries"]
        if row["path"] == seed_path
    )

    assert projected["title"] == "Decorator idea"
    assert projected["tags"] == ["python"]


def test_garden_seed_without_title_preserves_body_and_uses_loader_title(
    mini_repo: Path,
):
    text = "# Loose thought\n\nSomething unfinished. #optimizer"

    first_key = "garden-seed-loose-001"
    first = approved_v2_call(
        mini_repo,
        capability="garden.seed.create",
        payload={"text": text},
        artifact_ids=[request_artifact_id("garden.seed.create", first_key)],
        idempotency_key=first_key,
    )

    assert first.returncode == 0, first.stderr

    first_result = json.loads(first.stdout)["result"]
    first_path = first_result["seed_path"]

    assert first_path == "knowledge/garden/loose-thought.md"
    assert (
        mini_repo / first_path
    ).read_text(encoding="utf-8") == text + "\n"

    # Same mechanical title/body must never overwrite the first seed.
    second_key = "garden-seed-loose-002"
    second = approved_v2_call(
        mini_repo,
        capability="garden.seed.create",
        payload={"text": text},
        artifact_ids=[request_artifact_id("garden.seed.create", second_key)],
        idempotency_key=second_key,
    )

    assert second.returncode == 0, second.stderr

    second_result = json.loads(second.stdout)["result"]

    assert (
        second_result["seed_path"]
        == "knowledge/garden/loose-thought-2.md"
    )

    repo = load_repo(mini_repo)
    titles = sorted(
        note.title
        for note in repo.garden_notes
    )

    assert titles == [
        "Loose thought",
        "Loose thought",
    ]


def test_garden_seed_direct_cli_write_is_refused(
    mini_repo: Path,
    repo_root: Path,
):
    result = run_los(
        repo_root,
        mini_repo,
        "garden-seed-create",
        "--text",
        "A valid seed that lacks gateway authority.",
        "--json",
    )
    assert result.returncode == 2
    assert "GatewayEnvelopeV2" in result.stderr
    garden = mini_repo / "knowledge/garden"
    assert not garden.exists() or not list(garden.glob("*.md"))


def test_garden_seed_rejects_empty_text_without_a_transaction(
    mini_repo: Path,
    repo_root: Path,
):
    result = run_los(
        repo_root,
        mini_repo,
        "garden-seed-create",
        "--text",
        "   ",
        "--json",
    )

    assert result.returncode == 2
    assert "empty" in result.stderr.lower()

    garden = mini_repo / "knowledge/garden"

    assert (
        not garden.exists()
        or not list(garden.glob("*.md"))
    )

    transactions = mini_repo / "operations/transactions"

    assert (
        not transactions.exists()
        or not list(transactions.glob("transaction-*.yaml"))
    )


def test_garden_seed_honours_projection_snapshot_guard(
    mini_repo: Path,
):
    repo = load_repo(mini_repo)
    write_outputs(
        repo,
        generate_all(repo, generated_at="T1"),
    )

    manifest = json.loads(
        (mini_repo / "generated/manifest.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot = manifest["_generated"]["snapshot_id"]

    # Make the authored tree newer than the caller's projection.
    note = (
        mini_repo
        / "knowledge/notes/mathematics/note-demo.md"
    )
    note.write_text(
        note.read_text(encoding="utf-8")
        + "\nChanged after projection.\n",
        encoding="utf-8",
    )

    key = "garden-seed-stale-001"
    result = approved_v2_call(
        mini_repo,
        capability="garden.seed.create",
        payload={"text": "This must not be written."},
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key,
        expected_snapshot=snapshot,
    )

    assert result.returncode == 3

    response = json.loads(result.stdout)

    assert response["ok"] is False
    assert response["transaction_id"] is None
    assert response["error"]["code"] == "STALE_SNAPSHOT"

    garden = mini_repo / "knowledge/garden"

    assert (
        not garden.exists()
        or not list(garden.glob("*.md"))
    )
