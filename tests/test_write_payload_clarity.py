"""Write-payload clarity: named refusals, declared input shapes, seal guidance.

#100 names the unknown fields (and the accepted ones) in the note,
analysis and question refusals, with a dedicated message when the id is
missing. #93 declares every opaque ``json_object`` payload field's
accepted input shape so ``capabilities NAME --json`` shows it. #105
teaches ``seal_envelope.py --guards auto`` to tell a bad payload from
underivable guards, and adds id suggestions to the write handlers'
not-found refusals.
"""

from __future__ import annotations

import json

import pytest
from repo_builders import run_los

from learning_os.commands.support import WriteRefused

# ------------------------------------------------------------------ #100


def test_note_precheck_names_the_unknown_fields():
    from learning_os.commands.note import _precheck_note

    with pytest.raises(WriteRefused) as refused:
        _precheck_note(
            {"id": "note-x", "title": "T", "domain": "math", "role": "synthesis"},
            b"body",
        )
    message = str(refused.value)
    assert "note has unknown fields: domain" in message
    assert (
        "accepted: id, title, path, role, concepts, sources, contexts, "
        "supersedes" in message
    )
    assert "type/created/state/authorship/semantic_review are set by the handler" in message


def test_note_precheck_gives_a_missing_id_its_own_message():
    from learning_os.commands.note import _precheck_note

    with pytest.raises(WriteRefused, match="^note needs a string id$"):
        _precheck_note({"title": "T"}, b"body")
    # An unknown field still wins over a missing id: one refusal, the
    # actionable one.
    with pytest.raises(WriteRefused, match="unknown fields: domain"):
        _precheck_note({"title": "T", "domain": "math"}, b"body")


def test_analysis_precheck_names_the_unknown_fields():
    from learning_os.commands.analysis import _precheck_analysis

    with pytest.raises(WriteRefused) as refused:
        _precheck_analysis({"id": "note-x", "title": "T", "domain": "math"}, b"body")
    message = str(refused.value)
    assert "analysis has unknown fields: domain" in message
    assert "accepted: id, title, path, binding" in message
    assert "type/created/state/authorship/semantic_review are set by the handler" in message


def test_analysis_precheck_gives_a_missing_id_its_own_message():
    from learning_os.commands.analysis import _precheck_analysis

    with pytest.raises(WriteRefused, match="^analysis needs a string id$"):
        _precheck_analysis({"title": "T"}, b"body")


def test_question_save_names_the_unknown_fields(mini_repo):
    result = run_los(
        mini_repo, "atlas-question-save", "--question",
        json.dumps({"id": "note-q", "title": "T", "domain": "math"}),
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "question has unknown fields: domain" in result.stderr
    assert "accepted: id, title, text, target, state, answer_notes" in result.stderr
    assert "type/role/created/authorship are set by the handler" in result.stderr


def test_question_save_gives_a_missing_id_its_own_message(mini_repo):
    result = run_los(
        mini_repo, "atlas-question-save", "--question",
        json.dumps({"title": "T"}),
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "question needs a string id" in result.stderr
