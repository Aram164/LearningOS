"""Source observation and analysis-binding rules for durable material notes.

One shared implementation answers "what is this material right now": the
live digest, readability, and exact on-disk location of a recorded relpath.
Recorded digests stay historical observations; only a live re-observation
can claim current bytes. Binding rules keep every resolution honest: only
`resolved` names a registered source, and a live digest is recorded only
when the bytes behind this exact identity were actually observed.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def observe_local_material(materials_root: Path, material: str,
                           recorded_digest: str, *,
                           cache: dict[Path, str] | None = None) -> dict:
    """Observe one recorded material relpath against current bytes.

    Returns status `current` (live bytes hash to the recorded digest),
    `stale` (readable bytes differ), `missing` (no readable file), or
    `outside-boundary` (the relpath escapes the materials root).
    `live_digest` is present exactly when bytes were observed.
    """
    try:
        relative = Path(material)
    except (TypeError, ValueError):
        return {"status": "outside-boundary", "material": material}
    if not material or relative.is_absolute() or ".." in relative.parts:
        return {"status": "outside-boundary", "material": material}
    try:
        root = materials_root.resolve()
        target = (materials_root / relative).resolve()
        target.relative_to(root)
    except (OSError, ValueError):
        return {"status": "outside-boundary", "material": material}
    if target.is_symlink() or not target.is_file():
        return {"status": "missing", "material": material}
    cached = cache.get(target) if cache is not None else None
    if cached is None:
        try:
            digest = hashlib.sha256()
            with target.open("rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
        except OSError:
            return {"status": "missing", "material": material}
        live = digest.hexdigest()
        if cache is not None:
            # Same per-read cache format as materials_resolution.sha256_file.
            cache[target] = f"sha256:{live}"
    else:
        live = cached.removeprefix("sha256:")
    return {
        "status": "current" if live == recorded_digest else "stale",
        "material": material,
        "live_digest": live,
        "path": target.relative_to(root).as_posix(),
    }


def normalize_binding_spellings(binding: dict) -> str | None:
    """Canonicalize the read surface's own identifier spellings, in place.

    No read emits binding-ready values: ``material-span`` prints
    ``material://`` URIs and ``sha256:``-prefixed digests, while ``inspect``
    prints ``materials/``-prefixed paths the binding forbids. The boundary
    accepts all three and stores the canonical form (materials-relative
    path, bare hex), so existing validators, digests, and frozen-input
    hashes are unaffected.

    Strips one leading ``materials/`` and any ``sha256:`` digest prefix,
    then validates the bare hex. ``material://`` URIs are NOT resolved
    here — that needs the repository — only normalized downstream.
    Returns a refusal reason, else None. Non-string digests are left for
    the schema and handler checks, which already refuse them.
    """
    material = binding.get("material")
    if isinstance(material, str) and material.startswith("materials/"):
        binding["material"] = material[len("materials/"):]
    for field in ("recorded_source_digest", "live_source_digest"):
        value = binding.get(field)
        if value is None or not isinstance(value, str):
            continue
        bare = value.removeprefix("sha256:")
        if not re.fullmatch(r"[0-9a-f]{64}", bare):
            return (
                f"binding.{field} is malformed: expected bare 64-character "
                f"lowercase hex (or sha256:<hex>), got {value!r}"
            )
        binding[field] = bare
    return None


def binding_consistent(binding: dict) -> str | None:
    """Refusal reason for a dishonest binding, else None.

    Shape is the note schema's job; this checks the semantic contract:
    a `resolved` binding must show live bytes equal to the recorded
    digest, `stale` must show observed bytes that differ, and
    `unavailable` must not claim any live observation. `unresolved`
    may record bytes observed at the recorded path; the absent
    `source_id` is what withholds the registered-source claim.
    """
    if not isinstance(binding, dict):
        return "binding must be an object"
    resolution = binding.get("resolution")
    recorded = binding.get("recorded_source_digest")
    live = binding.get("live_source_digest")
    if resolution == "resolved":
        if not binding.get("source_id"):
            return "resolved bindings must name a registered source"
        if live is None:
            return "resolved bindings must record the observed live digest"
        if live != recorded:
            return "resolved bindings must show live bytes equal to recorded"
        return None
    if resolution == "stale":
        if live is None:
            return "stale bindings must record the observed live digest"
        if live == recorded:
            return "stale bindings must show live bytes that differ"
        return None
    if resolution == "unavailable":
        if live is not None:
            return "unavailable bindings must not claim a live observation"
        return None
    if resolution == "unresolved":
        return None
    return f"unknown resolution: {resolution!r}"
