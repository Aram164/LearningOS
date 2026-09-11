"""Session resume dossier: one screen answering "where was I".

The expensive recomputation in this system is not an agent re-deriving a
route — it is Aram re-deriving where he was (PHILOSOPHY §3.5). The global
resume pointer is a five-field bookmark: the address without the context.
This builder compiles the context instead: the stage, its requirement,
the evidence spec against what was actually recorded, open items, the
last result, and the exam sitting it all serves.

Same content-addressed discipline as the semantic dossiers, different
subject: one hash per section plus an overall digest, addressed as
``context://<unit-id>/resume-dossier@<digest16>``. Same inputs always
produce the same key; a cache file whose content no longer matches its
hashes is refused rather than served. The builder is pure — every input
is explicit, nothing is walked — so the screen is a deterministic
function of the five readers that feed it. Relative time ("2 days ago")
is render-time only and never enters the hashed content.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


class ResumeDossierError(ValueError):
    """A resume dossier cannot be built, stored, or trusted as read."""


#: Cache root, shared with the semantic dossiers. Gitignored, rebuildable.
RESUME_DOSSIERS_RELATIVE = "generated/dossiers"

#: Cache document tag, so a semantic dossier is never mistaken for one.
RESUME_DOCUMENT_TYPE = "resume-dossier-v1"


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
) -> ResumeDossier:
    """Compile one resume screen. Pure: same inputs, same key."""
    for label, value in (("unit", unit_id), ("module", module_id),
                         ("stage", stage_id), ("study map", study_map_id)):
        if not isinstance(value, str) or not value.strip():
            raise ResumeDossierError(f"a resume dossier needs a non-empty {label} id")
    if not isinstance(via, str) or not via.strip():
        raise ResumeDossierError("a resume dossier names how its stage was resolved")
    try:
        sections = {
            "requirement": dict(requirement) if requirement is not None else None,
            "observations": [dict(obs) for obs in observations],
            "open-items": [str(item) for item in open_items],
            "sittings": [dict(sitting) for sitting in sittings],
            "titles": {str(key): str(value) for key, value in titles.items()},
            "via": via,
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


def _overall_digest(hashes: Mapping[str, str]) -> str:
    return _digest(sorted(hashes.items()))


def cache_path(root: Path, dossier: ResumeDossier) -> Path:
    """Where a resume dossier lives: by overall digest, never by bare id."""
    digest = _overall_digest(dict(dossier.hashes))
    return root / RESUME_DOSSIERS_RELATIVE / f"{dossier.unit_id}-resume-{digest[:16]}.json"


def _cache_document(dossier: ResumeDossier) -> dict:
    # `_generated` rides outside the hashed content: the poison check
    # covers `hashes` plus `content` only, exactly like the manifest's
    # own warning key. The validator requires the key on every
    # generated JSON file (GEN-HEADER).
    return {
        "_generated": "GENERATED file - do not edit; rebuilt by los resume",
        "type": RESUME_DOCUMENT_TYPE,
        "key": dossier.key,
        "unit_id": dossier.unit_id,
        "module_id": dossier.module_id,
        "stage_id": dossier.stage_id,
        "study_map_id": dossier.study_map_id,
        "via": dossier.via,
        "hashes": dict(dossier.hashes),
        "content": {section: value for section, value in dossier.content},
    }


def store_resume_dossier(root: Path, dossier: ResumeDossier) -> Path:
    """Write one cache file under the shared cache root. Returns its path."""
    path = cache_path(root, dossier)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(_cache_document(dossier), ensure_ascii=False,
                       sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ResumeDossierError(
            f"cannot store resume dossier {dossier.key!r}: {exc}") from exc
    return path


def load_resume_dossier(path: Path) -> ResumeDossier:
    """Read one cache file, verifying content against hashes.

    A file whose content no longer matches its hashes is refused — serving
    it would restore a context the learner never had.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResumeDossierError(
            f"cannot read resume cache {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("type") != RESUME_DOCUMENT_TYPE:
        raise ResumeDossierError(f"resume cache {path} is not a resume dossier")
    try:
        content = raw["content"]
        rebuilt = build_resume_dossier(
            unit_id=str(raw["unit_id"]),
            module_id=str(raw["module_id"]),
            stage_id=str(raw["stage_id"]),
            study_map_id=str(raw["study_map_id"]),
            via=str(raw["via"]),
            requirement=content["requirement"],
            observations=content["observations"],
            open_items=content["open-items"],
            sittings=content["sittings"],
            titles=content["titles"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ResumeDossierError(
            f"resume cache {path} is malformed: {exc}") from exc
    if dict(rebuilt.hashes) != dict(raw.get("hashes", {})) \
            or rebuilt.key != raw.get("key"):
        raise ResumeDossierError(
            f"resume cache {path} fails its hashes: refusing poison")
    return rebuilt
