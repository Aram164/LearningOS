"""Phase-5 context dossiers: build once, reuse by key, invalidate by hash.

Agents rebuild the same context per task: unit facts, knowledge nodes, the
complete menu, evidence trails. A dossier materializes that bundle with one
hash per dependency plus an overall digest, addressed as
``context://<unit-id>/semantic-dossier``. Same inputs always produce the
same key (cache hit); any dependency move changes exactly its hash and the
overall digest (invalidation); a cache file whose content no longer matches
its hashes is refused rather than served (poisoning guard).

Evidence is content-addressed: the caller resolves each locator to the
content digest behind it (via the materials manifest checksums, never by
the builder — this module takes explicit inputs and never walks the
repository), so changed bytes invalidate even when the URI never moves.
Hashing locator strings alone would miss exactly that.

Dossiers live under ``generated/dossiers/`` — rebuilt views, never
hand-edited, covered by the existing no-hand-edit path: no canonical file
may reference them, and the builder plus the store take explicit paths and
never walk the repository. Freshness itself delegates to the
``DossierFresh`` predicate, so the system holds one definition of fresh.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .predicates import CONTRACT_VERSION, dossier_fresh


class DossierError(ValueError):
    """A dossier cannot be built, stored, or trusted as read."""


#: Every dependency a dossier key covers. Contract versions ride along so
#: a meaning change invalidates exactly like a content change.
DEPENDENCIES = (
    "knowledge-map",
    "source-map",
    "routes",
    "evidence",
    "semantic-contract",
    "operator-contract",
)

#: Cache root, relative to the repository. Gitignored, rebuildable.
DOSSIERS_RELATIVE = "generated/dossiers"


@dataclass(frozen=True)
class Dossier:
    """One materialized context bundle with its dependency hashes."""

    key: str
    unit_id: str
    hashes: tuple[tuple[str, str], ...]
    content: tuple[tuple[str, object], ...]
    contract_version: int = CONTRACT_VERSION


def _canonical(value: object) -> str:
    """Stable JSON for hashing. Anything unserializable refuses."""
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise DossierError(f"dossier content is not JSON-stable: {exc}") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def compute_hashes(
    *,
    knowledge_map: Mapping[str, object],
    source_map: Mapping[str, object],
    routes: Sequence[Mapping[str, object]],
    evidence: Mapping[str, str],
    contract_versions: Mapping[str, str],
) -> dict[str, str]:
    """Hash every dossier dependency separately. Total shape, hashed parts.

    ``evidence`` maps each locator to the content digest behind it,
    resolved by the caller: same URI with changed bytes must hash
    differently, which locator strings alone cannot do.
    """
    if not isinstance(knowledge_map, Mapping) \
            or not isinstance(source_map, Mapping):
        raise DossierError("knowledge map and source map come as mappings")
    if isinstance(routes, str) or not isinstance(routes, Sequence):
        raise DossierError("routes come as a list of mappings")
    if not isinstance(evidence, Mapping):
        raise DossierError("evidence comes as a locator-to-digest mapping")
    if not isinstance(contract_versions, Mapping) or not contract_versions:
        raise DossierError("contract versions come as a non-empty mapping")
    try:
        route_rows = [dict(route) for route in routes]
        trails = {str(locator): str(digest)
                  for locator, digest in evidence.items()}
        versions = {str(key): str(value)
                    for key, value in contract_versions.items()}
    except (TypeError, ValueError) as exc:
        raise DossierError(f"malformed dossier inputs: {exc}") from exc
    if any(not digest for digest in trails.values()):
        raise DossierError("evidence digests are never blank")
    if any(not version for version in versions.values()):
        raise DossierError("contract versions are never blank")
    hashes = {
        "knowledge-map": _digest(knowledge_map),
        "source-map": _digest(source_map),
        "routes": _digest(route_rows),
        "evidence": _digest(sorted(trails.items())),
    }
    for name in ("semantic-contract", "operator-contract"):
        if name not in versions:
            raise DossierError(f"contract versions miss {name!r}")
        hashes[name] = _digest(versions[name])
    return hashes


def _overall_digest(hashes: Mapping[str, str]) -> str:
    return _digest(sorted(hashes.items()))


def build_dossier(
    *,
    unit_id: str,
    knowledge_map: Mapping[str, object],
    source_map: Mapping[str, object],
    routes: Sequence[Mapping[str, object]],
    evidence: Mapping[str, str] | None = None,
    contract_versions: Mapping[str, str] | None = None,
) -> Dossier:
    """Assemble and hash one dossier. Pure: same inputs, same key."""
    if not isinstance(unit_id, str) or not unit_id.strip():
        raise DossierError("a dossier needs a non-empty unit id")
    versions = dict(contract_versions or {})
    versions.setdefault("semantic-contract", str(CONTRACT_VERSION))
    if evidence is None:
        trails: Mapping[str, str] = {}
    elif not isinstance(evidence, Mapping):
        raise DossierError("evidence comes as a locator-to-digest mapping")
    else:
        trails = evidence
    hashes = compute_hashes(
        knowledge_map=knowledge_map,
        source_map=source_map,
        routes=routes,
        evidence=trails,
        contract_versions=versions,
    )
    content = (
        ("unit", unit_id),
        ("knowledge-map", json.loads(_canonical(knowledge_map))),
        ("source-map", json.loads(_canonical(source_map))),
        ("routes", json.loads(_canonical([dict(route) for route in routes]))),
        ("evidence", {str(locator): str(digest)
                      for locator, digest in trails.items()}),
        ("contracts", versions),
    )
    digest = _overall_digest(hashes)
    return Dossier(
        key=f"context://{unit_id}/semantic-dossier@{digest[:16]}",
        unit_id=unit_id,
        hashes=tuple(sorted(hashes.items())),
        content=content,
    )


def is_fresh(dossier: Dossier, current_hashes: Mapping[str, str]) -> bool:
    """Whether a dossier still matches its dependencies. Delegates."""
    return bool(dossier_fresh(
        cached_hashes=dict(dossier.hashes),
        current_hashes=current_hashes,
    ))


# ---- content-addressed cache --------------------------------------------------


def cache_path(root: Path, dossier: Dossier) -> Path:
    """Where a dossier lives: by overall digest, never by bare unit id.

    A bare-unit filename would let a stale bundle shadow a fresh one; the
    digest in the filename makes shadowing structurally impossible.
    """
    digest = _overall_digest(dict(dossier.hashes))
    return root / DOSSIERS_RELATIVE / f"{dossier.unit_id}-{digest[:16]}.json"


#: Cache document tag, so a semantic dossier is never mistaken for a
#: resume dossier sharing the same cache root.
DOSSIER_DOCUMENT_TYPE = "semantic-dossier-v1"


def _cache_document(dossier: Dossier) -> dict:
    # `_generated` and `type` ride outside the hashed content: the poison
    # check covers `hashes` plus `content` plus `key` only, exactly like the
    # resume dossier cache beside it. The validator requires the key on
    # every generated JSON file (GEN-HEADER).
    return {
        "_generated": "GENERATED file - do not edit; rebuilt by los dossier",
        "type": DOSSIER_DOCUMENT_TYPE,
        "key": dossier.key,
        "unit_id": dossier.unit_id,
        "hashes": dict(dossier.hashes),
        "content": {section: value for section, value in dossier.content},
        "contract_version": dossier.contract_version,
    }


def store_dossier(root: Path, dossier: Dossier) -> Path:
    """Write one cache file under the cache root. Returns its path.

    Takes the root explicitly and writes beneath the cache root only —
    canonical inputs are read by the caller, never walked here.
    """
    path = cache_path(root, dossier)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(_cache_document(dossier), ensure_ascii=False,
                       sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise DossierError(f"cannot store dossier {dossier.key!r}: {exc}") from exc
    return path


def load_dossier(path: Path) -> Dossier:
    """Read one cache file, verifying content against hashes.

    A file whose content no longer matches its hashes is refused — serving
    it would be cache poisoning, and a loud refusal beats a stale context.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DossierError(f"cannot read dossier cache {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise DossierError(f"dossier cache {path} is not an object")
    try:
        stored_hashes = dict(raw["hashes"])
        content = raw["content"]
        rebuilt = build_dossier(
            unit_id=str(raw["unit_id"]),
            knowledge_map=content["knowledge-map"],
            source_map=content["source-map"],
            routes=content["routes"],
            evidence=content["evidence"],
            contract_versions=content["contracts"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DossierError(
            f"dossier cache {path} is malformed: {exc}") from exc
    if dict(rebuilt.hashes) != stored_hashes or rebuilt.key != raw.get("key"):
        raise DossierError(
            f"dossier cache {path} fails its hashes: refusing poison")
    return rebuilt
