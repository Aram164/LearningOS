"""Session resume dossier: one screen answering "where was I".

The expensive recomputation in this system is not an agent re-deriving a
route — it is Aram re-deriving where he was (PHILOSOPHY §3.5). The global
resume pointer is a five-field bookmark: the address without the context.
This builder compiles the context instead: the stage, its requirement,
the evidence spec against what was actually recorded, open items, the
last result, the exam sitting it all serves, and the top-ranked goal
cluster (one row, best-effort, read-only — seeing it files nothing).

Same content-addressed discipline as the semantic dossiers, different
subject: one hash per section plus an overall digest, addressed as
``context://<unit-id>/resume-dossier@<digest16>``. Same inputs always
produce the same key. The builder is pure — every input
is explicit, nothing is walked — so the screen is a deterministic
function of the five readers that feed it. Relative time ("2 days ago")
is render-time only and never enters the hashed content.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


class ResumeDossierError(ValueError):
    """A resume dossier cannot be built from the supplied inputs."""


@dataclass(frozen=True)
class ResumeDossier:
    """One compiled return-to-study screen with its section hashes."""

    key: str
    unit_id: str
    module_id: str
    stage_id: str
    study_map_id: str
    via: str
    hashes: tuple[tuple[str, str], ...]
    content: tuple[tuple[str, object], ...]


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ResumeDossierError(
            f"resume content is not JSON-stable: {exc}") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def build_resume_dossier(
    *,
    unit_id: str,
    module_id: str,
    stage_id: str,
    study_map_id: str,
    via: str,
    requirement: Mapping[str, object] | None,
    observations: Sequence[Mapping[str, object]],
    open_items: Sequence[str],
    sittings: Sequence[Mapping[str, object]],
    titles: Mapping[str, str],
    top_cluster: Mapping[str, object] | None = None,
    stage_note: Mapping[str, object] | None = None,
) -> ResumeDossier:
    """Compile one resume screen. Pure: same inputs, same key.

    ``top_cluster`` is the single highest-ranked goal cluster, or None
    when the scan found nothing or could not run. It carries countdown-free
    fields only (no days-until: render-time countdowns never enter the
    hashed content), so the digest moves when the top cluster moves and
    never with the clock.

    ``stage_note`` is bounded facts about the stage's working note (path,
    line count, last-commit date, trailing excerpt), or None when the
    stage names no note. Requirement-linked observations stay the
    evidence; the note is what "move me on" can show when no requirement
    is authored — and the digest moves with it, like every section.
    """
    for label, value in (("unit", unit_id), ("module", module_id),
                         ("stage", stage_id), ("study map", study_map_id)):
        if not isinstance(value, str) or not value.strip():
            raise ResumeDossierError(f"a resume dossier needs a non-empty {label} id")
    if not isinstance(via, str) or not via.strip():
        raise ResumeDossierError("a resume dossier names how its stage was resolved")
    if top_cluster is not None and not isinstance(top_cluster, Mapping):
        raise ResumeDossierError("a resume dossier's top cluster is a mapping or nothing")
    if stage_note is not None and not isinstance(stage_note, Mapping):
        raise ResumeDossierError("a resume dossier's stage note is a mapping or nothing")
    try:
        sections = {
            "requirement": dict(requirement) if requirement is not None else None,
            "observations": [dict(obs) for obs in observations],
            "open-items": [str(item) for item in open_items],
            "sittings": [dict(sitting) for sitting in sittings],
            "titles": {str(key): str(value) for key, value in titles.items()},
            "via": via,
            "top-cluster": dict(top_cluster) if top_cluster is not None else None,
            "stage-note": dict(stage_note) if stage_note is not None else None,
        }
    except (TypeError, ValueError) as exc:
        raise ResumeDossierError(f"malformed resume inputs: {exc}") from exc
    hashes = {name: _digest(sections[name]) for name in sections}
    digest = _digest(sorted(hashes.items()))
    content = (
        ("stage", {"module_id": module_id, "unit_id": unit_id,
                   "study_map_id": study_map_id, "stage_id": stage_id}),
        ("via", via),
        ("requirement", sections["requirement"]),
        ("observations", sections["observations"]),
        ("open-items", sections["open-items"]),
        ("sittings", sections["sittings"]),
        ("titles", sections["titles"]),
        ("top-cluster", sections["top-cluster"]),
        ("stage-note", sections["stage-note"]),
    )
    return ResumeDossier(
        key=f"context://{unit_id}/resume-dossier@{digest[:16]}",
        unit_id=unit_id,
        module_id=module_id,
        stage_id=stage_id,
        study_map_id=study_map_id,
        via=via,
        hashes=tuple(sorted(hashes.items())),
        content=content,
    )
