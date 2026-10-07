"""Executable documented-claim checks for doc/code mismatches (SPEC §7.5).

Scrut v0.5.0 defines no expected-failure mechanism, so a transcript case
that evidences a mismatch pins the OBSERVED behaviour (green) while the
check here holds the DOCUMENTED claim (SPEC amendment (ak)).

Each check builds a fresh disposable fixture and executes the documented
command path as ordinary code; only the documented-claim assertion sits
in ``try``, calling ``pytest.xfail`` on ``AssertionError`` (the mismatch
stands). If the claim passes, the check calls ``pytest.fail``: an
unexpectedly satisfied claim fails the gate until its mismatch is
formally resolved (Aram decision + fix session). Bare ``@xfail`` is
forbidden here because it would swallow in-test setup errors.

``MISMATCH_CHECKS`` maps each M-id to its transcript file, case title,
and the documented claim verbatim from
``tests/architecture/mismatches.yaml``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import build_mini_repo
from gateway_helpers import approved_v2_call
from repo_builders import run_los
from scenario_fixtures import rich_world

#: M-id -> transcript file, case title, documented claim (verbatim, ≤25 words).
MISMATCH_CHECKS: dict[str, dict[str, str]] = {
    "M-01": {
        "transcript": "record-evidence.md",
        "case": "The untargeted ledger needs an envelope",
        "claim": "the bare mutating commands (capture --text, note-revise, …) refuse with exit 2 (canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled)",
    },
    "M-02": {
        "transcript": "build-write-envelope.md",
        "case": "A second bare command refuses with its own first clause",
        "claim": "the bare mutating commands (capture --text, note-revise, …) refuse with exit 2 (canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled)",
    },
    "M-03": {
        "transcript": "unit-workflow.md",
        "case": "The wired removal commits (M-03)",
        "claim": "Removing a choice already wired into a study path is refused.",
    },
}

#: The §25c-quoted refusal text for the bare-mutating-command class.
SECTION_25C_REFUSAL = (
    "canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled"
)


def _transcript_world(tmp_path: Path) -> Path:
    """A fresh disposable rich_world fixture, the world transcripts run in."""
    root = build_mini_repo(tmp_path)
    rich_world(root)
    return root


def test_m01_bare_stage_result_refusal_matches_section_25c_quote(tmp_path: Path):
    """M-01 — record-evidence.md — The untargeted ledger needs an envelope.

    Documented claim: the bare mutating commands (capture --text,
    note-revise, …) refuse with exit 2 (canonical writes must use
    GatewayEnvelopeV2; direct CLI application is disabled).
    """
    root = _transcript_world(tmp_path)
    proc = run_los(
        root,
        "stage-result",
        "--workspace", "workspace-demo",
        "--unit", "unit-demo-l01",
        "--stage", "stage-demo-pending",
        "--activity", "exercise",
        "--result", "correct",
    )
    assert proc.returncode == 2, proc.stderr
    try:
        assert SECTION_25C_REFUSAL in proc.stderr
    except AssertionError:
        pytest.xfail("M-01: bare stage-result refuses with its own first clause")
    pytest.fail(
        "M-01 resolved unexpectedly: remove via formal resolution "
        "(Aram decision + fix session)"
    )


def test_m02_bare_inbox_resolve_refusal_matches_section_25c_quote(tmp_path: Path):
    """M-02 — build-write-envelope.md — A second bare command refuses with its own first clause.

    Documented claim: the bare mutating commands (capture --text,
    note-revise, …) refuse with exit 2 (canonical writes must use
    GatewayEnvelopeV2; direct CLI application is disabled).
    """
    root = _transcript_world(tmp_path)
    proc = run_los(
        root,
        "inbox-resolve",
        "note-drop.md",
        "--drop-sha256",
        "sha256:cff485a0c38476920bff529d70a47c19fddb0380750b9a0152521d7eb9b6c81d",
        "--routed-to", "note-demo",
    )
    assert proc.returncode == 2, proc.stderr
    try:
        assert SECTION_25C_REFUSAL in proc.stderr
    except AssertionError:
        pytest.xfail("M-02: bare inbox-resolve refuses with its own first clause")
    pytest.fail(
        "M-02 resolved unexpectedly: remove via formal resolution "
        "(Aram decision + fix session)"
    )


def test_m03_wired_choice_removal_is_refused(tmp_path: Path):
    """M-03 — unit-workflow.md — The wired removal commits (M-03).

    Documented claim: Removing a choice already wired into a study path
    is refused.
    """
    root = _transcript_world(tmp_path)
    # Control (J22): the unwired l02 choice removes cleanly through the
    # same envelope path, proving the world and the submitter are healthy.
    control = approved_v2_call(
        root,
        capability="unit.source-selection.set",
        payload={
            "unit_id": "unit-demo-l02",
            "source_id": "source-demo-book",
            "locator": "lecture-02.pdf",
            "action": "remove",
        },
        artifact_ids=["unit-demo-l02"],
        idempotency_key="mismatch-m03-control-l02-remove",
    )
    assert control.returncode == 0, control.stderr
    assert json.loads(control.stdout)["ok"] is True
    proc = approved_v2_call(
        root,
        capability="unit.source-selection.set",
        payload={
            "unit_id": "unit-demo-l01",
            "source_id": "source-demo-book",
            "locator": "lecture-01.pdf",
            "action": "remove",
        },
        artifact_ids=["unit-demo-l01"],
        idempotency_key="mismatch-m03-wired-l01-remove",
    )
    doc = json.loads(proc.stdout)
    assert proc.returncode in (0, 2), proc.stderr
    assert (proc.returncode, doc["ok"]) in ((0, True), (2, False)), proc.stdout
    try:
        assert proc.returncode == 2 and doc["ok"] is False
    except AssertionError:
        pytest.xfail("M-03: wired removal commits; the guard keys on unpopulated stage_ids")
    pytest.fail(
        "M-03 resolved unexpectedly: remove via formal resolution "
        "(Aram decision + fix session)"
    )
