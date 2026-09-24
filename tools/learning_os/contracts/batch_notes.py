"""Single source of truth for the atomic batch-note shape.

``note.analysis.save_batch`` validates the same bundle in two places: the
gateway payload schema (derived, so agents can discover the contract) and
the handler (for direct CLI use and defense in depth). Both import these
definitions, so a future edit touches this module and regenerates — never
two hand-kept copies. The generated
``system/schema/capabilities/note.analysis.save_batch.schema.json`` remains
an output of ``tools/generate_capability_schemas.py``, not a third place
to edit.
"""

from __future__ import annotations

#: Fields the handler accepts at each bundle level; anything else refuses.
ANALYSIS_FIELDS = frozenset({"id", "title", "path", "binding"})
BATCH_FIELDS = frozenset({"notes"})
BATCH_ITEM_FIELDS = frozenset({"analysis", "body_file", "body_file_sha256"})

#: Keys the gateway schema requires at each level, in published order.
BUNDLE_REQUIRED = ("notes",)
BATCH_ITEM_REQUIRED = ("analysis", "body_file", "body_file_sha256")
ANALYSIS_REQUIRED = ("id", "title", "path", "binding")

#: Notes per batch, enforced by schema and handler alike.
BATCH_MIN_NOTES = 1
BATCH_MAX_NOTES = 20


def bundle_schema() -> dict:
    """The nested ``bundle`` subschema, built from the constants above.

    Binding internals stay an opaque object here: the ``material_analysis``
    contract already has exactly one copy in ``note.schema.json`` plus the
    handler's semantic checks, and this module must not become a second.
    """
    return {
        "type": "object",
        "required": list(BUNDLE_REQUIRED),
        "additionalProperties": False,
        "properties": {
            "notes": {
                "type": "array",
                "minItems": BATCH_MIN_NOTES,
                "maxItems": BATCH_MAX_NOTES,
                "items": {
                    "type": "object",
                    "required": list(BATCH_ITEM_REQUIRED),
                    "additionalProperties": False,
                    "properties": {
                        "analysis": {
                            "type": "object",
                            "required": list(ANALYSIS_REQUIRED),
                            "additionalProperties": False,
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "path": {"type": "string"},
                                "binding": {"type": "object"},
                            },
                        },
                        "body_file": {"type": "string", "minLength": 1},
                        "body_file_sha256": {
                            "type": "string",
                            "pattern": "^sha256:[a-f0-9]{64}$",
                        },
                    },
                },
            },
        },
    }
