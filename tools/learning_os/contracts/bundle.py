"""Prototype: bundle a root JSON Schema with its transitive resource closure.

``system/contracts/manifest-vN.schema.json`` references other schemas by URI
(``https://learningos.local/schema/<name>``), which Core resolves through
:func:`learning_os.contracts.json_schema.schema_registry`. The stamped
``schema_sha256``, however, digests only the root file's bytes: a referenced
resource can change while the contract identity stays fixed. This module
computes the conservative alternative — the identity of the complete admitted
resource-document closure — beside the current implementation, changing no
production behavior.

Bundle layout (refs byte-untouched, so resolution semantics cannot shift)::

    {"_generated": <constant warning (GEN-HEADER); rides inside the digest>,
     "format": "learningos-contract-bundle/1",
     "root_uri": <root $id or file label>,
     "root": <parsed root schema>,
     "resources": [{"path": <schema-dir-relative posix path>,
                    "declared_id": <$id or null>,
                    "aliases": [every known URI for this file, sorted],
                    "schema": <parsed schema>} ... sorted by path]}

Canonical bytes (also the exact on-disk bytes: file == digested bytes)::

    json.dumps(value, sort_keys=True, separators=(",", ":"),
               ensure_ascii=True).encode("utf-8")

The identity index deliberately mirrors ``schema_registry()`` — declared
``$id`` plus filename alias per file — and ``test_registry_parity`` proves the
two admit exactly the same identities, so a future change to Core's admission
rule turns the suite red instead of silently forking a second specification.
"""

from __future__ import annotations

import hashlib
import json
import platform
from importlib import metadata as _metadata
from pathlib import Path
from typing import Any

BUNDLE_FORMAT = "learningos-contract-bundle/1"
META_FORMAT = "learningos-contract-meta/1"
SCHEMA_URI_PREFIX = "https://learningos.local/schema/"
GENERATED_WARNING = "GENERATED file - do not edit; rebuilt by tools/contract_bundle.py build"


class BundleError(ValueError):
    """A contract bundle cannot be built from the given schemas."""


def canonical_bytes(value: Any) -> bytes:
    """The one byte string a value digests to and is stored as."""

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def digest_of(data: bytes) -> str:
    """A ``sha256:<hex>`` digest in the stamped-hash spelling."""

    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _read_schema(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BundleError(f"cannot read schema {path}: {exc}") from exc
    try:
        schema = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BundleError(f"invalid JSON in schema {path}: {exc}") from exc
    if not isinstance(schema, dict):
        raise BundleError(f"schema {path} is not a JSON object")
    return schema


def build_identity_index(schema_dir: Path) -> dict[str, Path]:
    """Map every URI Core's registry admits to its physical file.

    Same admission rule as ``schema_registry()``: each top-level
    ``*.schema.json`` is known under its declared ``$id`` (when present and a
    string) and under its filename alias. Non-recursive glob, same as Core.
    """

    index: dict[str, Path] = {}
    for candidate in sorted(schema_dir.glob("*.schema.json")):
        schema = _read_schema(candidate)
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            index[schema_id] = candidate
        alias = f"{SCHEMA_URI_PREFIX}{candidate.name}"
        if alias != schema_id:
            index[alias] = candidate
    return index


def _iter_refs(node: Any) -> Any:
    """Yield every ``$ref`` string anywhere under *node*."""

    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield value
            else:
                yield from _iter_refs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_refs(item)


def _aliases_for(path: Path, index: dict[str, Path]) -> list[str]:
    return sorted(uri for uri, target in index.items() if target == path)


def resolve_closure(root_schema_path: Path, schema_dir: Path) -> dict:
    """Resolve the root plus every transitively referenced resource.

    Returns ``{"root_uri": ..., "root": ..., "resources": [...]}`` with
    resources sorted by schema-dir-relative path. Any external ``$ref`` that is
    neither the root's own ``$id`` nor an indexed identity is a hard failure.
    """

    index = build_identity_index(schema_dir)
    root = _read_schema(root_schema_path)
    root_id = root.get("$id")
    root_uri = root_id if isinstance(root_id, str) and root_id else f"file:{root_schema_path.name}"

    by_path: dict[str, dict] = {}
    stack: list[tuple[dict, str]] = [(root, str(root_schema_path))]
    seen_files: set[Path] = set()
    while stack:
        node, owner = stack.pop()
        for ref in _iter_refs(node):
            if ref.startswith("#"):
                continue
            base, _, _fragment = ref.partition("#")
            if base == root_uri:
                continue
            target = index.get(base)
            if target is None:
                raise BundleError(
                    f"unresolvable $ref {ref!r} in {owner}: no schema in "
                    f"{schema_dir} is known under that identity"
                )
            if target in seen_files:
                continue
            seen_files.add(target)
            schema = _read_schema(target)
            rel = target.relative_to(schema_dir).as_posix()
            declared = schema.get("$id")
            by_path[rel] = {
                "path": rel,
                "declared_id": declared if isinstance(declared, str) and declared else None,
                "aliases": _aliases_for(target, index),
                "schema": schema,
            }
            stack.append((schema, str(target)))
    return {
        "root_uri": root_uri,
        "root": root,
        "resources": [by_path[key] for key in sorted(by_path)],
    }


def build_bundle(root_schema_path: Path, schema_dir: Path) -> bytes:
    """The canonical bundle bytes for one root schema."""

    closure = resolve_closure(root_schema_path, schema_dir)
    return canonical_bytes({"_generated": GENERATED_WARNING, "format": BUNDLE_FORMAT, **closure})


def _lib_version(distribution: str) -> str:
    try:
        return _metadata.version(distribution)
    except _metadata.PackageNotFoundError:  # pragma: no cover - broken install
        return "unknown"


def build_meta(
    *,
    contract: dict,
    schema_label: str,
    closure_digest: str,
    resources: list[dict],
) -> dict:
    """The beside-current bundle metadata (never stamped into a manifest)."""

    return {
        "_generated": GENERATED_WARNING,
        "format": META_FORMAT,
        "contract_version": contract.get("contract_version"),
        "root_schema": schema_label,
        "root_schema_sha256": contract.get("schema_sha256"),
        "closure_sha256": closure_digest,
        "contract_keys": {
            key: list(contract.get(key) or [])
            for key in ("top_level_keys", "generated_keys", "index_keys",
                        "forbidden_top_level_keys")
        },
        "resource_count": len(resources),
        "resources": [
            {
                "path": resource["path"],
                "declared_id": resource["declared_id"],
                "aliases": resource["aliases"],
                "sha256": digest_of(canonical_bytes(resource["schema"])),
            }
            for resource in resources
        ],
        "generator": {
            "name": "learningos-contract-bundle",
            "bundle_format": BUNDLE_FORMAT,
            "python": platform.python_version(),
            "jsonschema": _lib_version("jsonschema"),
            "referencing": _lib_version("referencing"),
        },
    }
