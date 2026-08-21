"""Reading the source registry and the flat-farm map off disk."""

from __future__ import annotations

import os

import yaml

from .config import (
    COLLECTION_DOMAIN,
    LOW_PRIORITY_COLLECTIONS,
    MATERIALS,
    ONLINE_DOMAIN_OVERRIDE,
    SOURCES,
    TYPE_LABEL,
)


def _authors_str(a) -> str:
    if isinstance(a, list):
        return ", ".join(str(x) for x in a)
    return str(a) if a else ""


def _pick_url(rec: dict) -> str:
    """The registered link for a source: url/homepage, else first http identifier."""
    u = rec.get("url") or rec.get("homepage")
    if u:
        return u
    idf = rec.get("identifiers")
    if isinstance(idf, dict):
        for v in idf.values():
            if str(v).startswith("http"):
                return str(v)
    return ""


def _source_blob(rec: dict) -> str:
    parts = [
        rec.get("id"), rec.get("title"), rec.get("type"), rec.get("url"),
        rec.get("organization"), str(rec.get("year") or ""), _authors_str(rec.get("authors")),
    ]
    idf = rec.get("identifiers")
    if isinstance(idf, dict):
        for k, v in idf.items():
            parts += [str(k), str(v)]
    elif idf:
        parts.append(str(idf))
    return " ".join(p for p in parts if p)


def load_sources() -> dict[str, dict]:
    out: dict[str, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("id") and node.get("title"):
                sid = node["id"]
                if sid not in out:
                    out[sid] = {
                        "id": sid,
                        "title": node.get("title"),
                        "type": node.get("type", ""),
                        "url": _pick_url(node),
                        "authors": node.get("authors"),
                        "organization": node.get("organization", ""),
                        "year": node.get("year"),
                        "identifiers": node.get("identifiers"),
                    }
                    out[sid]["blob"] = _source_blob(out[sid])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for yf in SOURCES.rglob("*.yaml"):
        if yf.parent.name == "collections":
            continue
        try:
            walk(yaml.safe_load(yf.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            print(f"  ! skipped {yf.name}: {exc}")
    return out


def load_collection_domains() -> dict[str, str]:
    coll = SOURCES / "collections"
    out: dict[str, str] = {}
    if not coll.is_dir():
        return out
    files = sorted(coll.glob("*.yaml"),
                   key=lambda p: (p.stem in LOW_PRIORITY_COLLECTIONS, p.stem))
    for cf in files:
        dom = COLLECTION_DOMAIN.get(cf.stem)
        if not dom:
            continue
        try:
            data = yaml.safe_load(cf.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        for e in (data.get("entries") or data.get("sources") or []):
            sid = (e.get("source") or e.get("id")) if isinstance(e, dict) else e
            if sid:
                out.setdefault(sid, dom)
    return out


def domain_for_online(sid: str, coll_domains: dict[str, str]) -> str:
    return ONLINE_DOMAIN_OVERRIDE.get(sid) or coll_domains.get(sid) or "Online"


def load_flat_map() -> dict[str, str]:
    flat = MATERIALS / ".flat"
    out: dict[str, str] = {}
    if not flat.is_dir():
        return out
    for link in flat.iterdir():
        if not link.is_symlink():
            continue
        resolved = (flat / os.readlink(link)).resolve()
        try:
            rel = resolved.relative_to(MATERIALS.resolve())
        except ValueError:
            continue
        out[str(rel)] = link.name
    return out


def human_size(n: int) -> str:
    step = 1024.0
    for unit in ("B", "KB", "MB", "GB"):
        if n < step:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= step
    return f"{n:.1f} TB"


def type_label(t: str) -> str:
    return TYPE_LABEL.get(t, t.title() if t else "")
