"""Explicit study-mode permission policies (default deny).

Three independently declared policies govern the sandboxed study boundary.
They are declared separately because they answer different questions, and no
entry in one list implies anything about another:

- ``STUDY_READ_COMMANDS`` / ``STUDY_COMMANDS``: what a sandboxed agent may
  ask the broker to execute at all.
- ``STUDY_PREFLIGHT_COMMANDS``: read-only ``--check`` diagnostics the broker
  forwards even though the corresponding canonical write is refused in
  study mode (e.g. ``unit-plan-revise --check`` is allowed while the
  ``unit.plan.revise`` write capability is not).
- ``STUDY_WRITE_CAPABILITIES``: the canonical writes a study envelope may
  perform. Deliberately excludes durable note writes/revisions, unit plan
  revisions, concept graph edits, review/program/delivery mutations.
- ``REVIEWED_SEALING_CAPABILITIES``: writes that additionally require a
  reviewed check record (``--guards-from``) before one-call sealing.
"""

from __future__ import annotations

STUDY_READ_COMMANDS: frozenset[str] = frozenset({
    "status",
    "capabilities",
    "bootstrap",
    "resume",
    "dossier",
    "inspect",
    "search",
    "semantic",
    "note-read",
    "inbox-read",
    "inbox-list",
    "related",
    "program-list",
    "plan-template",
    "module-list",
    "unit-list",
    "study-sequence",
    "ability-context",
    "runtime-session",
    "plan-edit-context",
    "atlas-context",
    "operations",
    "projection-observe",
})

STUDY_COMMANDS: frozenset[str] = frozenset({
    "material-search",
    "material-context",
    "material-span",
    "material-study-span",
    "material-card-settle",
})

# Read-only `--check` preflights permitted without granting write capabilities.
STUDY_PREFLIGHT_COMMANDS: dict[str, str] = {
    "source-intake": "source.intake.record",
    "unit-plan-revise": "unit.plan.revise",
}

STUDY_ALLOWED_COMMANDS: frozenset[str] = (
    STUDY_READ_COMMANDS
    | STUDY_COMMANDS
    | frozenset({"capability", *STUDY_PREFLIGHT_COMMANDS})
)

SESSION_COMMANDS: frozenset[str] = frozenset({
    "material-study-span",
    "material-card-settle",
    "material-search",
    "material-context",
})

STUDY_WRITE_CAPABILITIES: frozenset[str] = frozenset({
    "capture.create",
    "inbox.resolve",
    "stage.note.write",
    "stage.progress.update",
    "stage.attachment.add",
    "unit.note.append",
    "unit.source-selection.set",
    "detour.create",
    "detour.resolve",
    "note.evidence.add",
    "note.analysis.save",
    "note.analysis.save_batch",
    "source.feedback.record",
    "source.intake.record",
    "atlas.question.save",
    "garden.seed.create",
})

# Capabilities whose sealing replaces/revises existing records and therefore
# require a reviewed check record before a one-call submit. The set is
# declared with the admission policies (app/admission.py), which the
# gateway enforces; re-exported here for the study boundary.
from learning_os.app.admission import (  # noqa: E402
    REVIEWED_SEALING_CAPABILITIES,
)

__all__ = [
    "REVIEWED_SEALING_CAPABILITIES",
    "SESSION_COMMANDS",
    "STUDY_ALLOWED_COMMANDS",
    "STUDY_COMMANDS",
    "STUDY_PREFLIGHT_COMMANDS",
    "STUDY_READ_COMMANDS",
    "STUDY_WRITE_CAPABILITIES",
]
