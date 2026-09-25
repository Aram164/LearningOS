"""Single source of truth for the Atlas question shape.

``atlas.question.save`` validates the same question in two places: the
gateway payload schema (derived, so agents can discover the contract) and
the handler (for direct CLI use and defense in depth). Both import these
definitions, so a future edit touches this module and regenerates — never
two hand-kept copies. The generated
``system/schema/capabilities/atlas.question.save.schema.json`` remains
an output of ``tools/generate_capability_schemas.py``, not a third place
to edit.

The nested shape mirrors the handler's checks, never stricter ones:
direct CLI use never sees the schema. Conditions the handler decides
from repository state (new questions require title, text and target;
a stored target is preserved; answer notes must resolve) stay out of
the schema — only the field names, the required id, and the per-field
types live here. Target, state, and answer-note internals stay
structural: their authority is ``atlas_question`` in
``system/schema/note.schema.json``, which the handler enforces after
merging, and this module must not become a second copy.
"""

from __future__ import annotations

#: Fields the handler accepts on a question; anything else refuses.
QUESTION_FIELDS = frozenset({"id", "title", "text", "target", "state", "answer_notes"})

#: Keys the gateway schema requires. Only the id: title, text, and
#: target are required for new questions but optional for updates, and
#: the schema cannot see which one this payload is.
QUESTION_REQUIRED = ("id",)


def question_schema() -> dict:
    """The nested ``question`` subschema, built from the constants above."""
    return {
        "type": "object",
        "required": list(QUESTION_REQUIRED),
        "additionalProperties": False,
        "properties": {
            "id": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "Durable note id the question lives on; "
                    "an unknown id starts a new question note."
                ),
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "description": "Question title; required for a new question.",
            },
            "text": {
                "type": "string",
                "minLength": 1,
                "description": "Question body; required for a new question.",
            },
            "target": {
                "type": "object",
                "description": (
                    "What the question is about, shaped as note "
                    "atlas_question.target in "
                    "system/schema/note.schema.json: {concepts: [...]} or "
                    "{from, type, to}. Required for a new question; "
                    "preserved, never changed, on an existing one."
                ),
            },
            "state": {
                "type": "string",
                "description": (
                    "open or resolved, per note atlas_question.state; "
                    "new questions start open."
                ),
            },
            "answer_notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Durable note ids answering the question; "
                    "each must resolve to another durable note."
                ),
            },
        },
    }
