"""sources/ — the source registry, the curated collections, and the topic facet.

These three describe what a source *is* and how it may be browsed. What
currently *uses* a source is a curriculum fact and is loaded elsewhere
(ADR-007/009 keep identity independent from current use).
"""

from __future__ import annotations

from pathlib import Path

from .model import Repo, _register
from .yamlio import LoaderError, _load_registry, _load_yaml, _record_id


def load_sources(repo: Repo, root: Path) -> None:
    """Sources (consolidated or partitioned)."""
    records, origins, failures = _load_registry(
        root / "sources" / "sources.yaml", root / "sources" / "registry", "sources"
    )
    repo.parse_failures.extend(failures)
    for rec, origin in zip(records, origins, strict=True):
        sid = _record_id(rec)
        if sid is None:
            repo.parse_failures.append(
                (origin, f"{origin}: source record with missing or empty id — skipped"))
            continue
        _register(repo, repo.sources, sid, rec, origin, "source")
        repo.source_origins.setdefault(sid, origin)


def load_collections(repo: Repo, root: Path) -> None:
    """Source collections (curated reading lists): one collection per file,
    identity = kebab-case filename stem (ARCHITECTURE §3.3)."""
    collections_dir = root / "sources" / "collections"
    if not collections_dir.is_dir():
        return
    for f in sorted(collections_dir.glob("*.yaml")):
        try:
            doc = _load_yaml(f)
        except LoaderError as exc:
            repo.parse_failures.append((f, str(exc)))
            continue
        entries = doc.get("entries")
        if entries is not None and not isinstance(entries, list):
            repo.parse_failures.append(
                (f, f"{f}: 'entries' must be a list — collection skipped"))
            continue
        repo.collections[f.stem] = doc
        repo.collection_origins[f.stem] = f


def load_topics(repo: Repo, root: Path) -> None:
    """The topic facet (ADR-009).

    A closed vocabulary, loaded like the thematic groups it complements: topics
    are the medium-grained facet, groups the coarse one, and the concept graph
    carries everything finer.
    """
    topics_file = root / "sources" / "topics.yaml"
    if not topics_file.is_file():
        return
    try:
        topics_doc = _load_yaml(topics_file)
    except LoaderError as exc:
        repo.parse_failures.append((topics_file, str(exc)))
        return
    repo.topics_path = topics_file
    entries = topics_doc.get("topics", [])
    if not isinstance(entries, list):
        repo.parse_failures.append(
            (topics_file, f"{topics_file}: 'topics' must be a list"))
        return
    for topic in entries:
        if not isinstance(topic, dict):
            repo.parse_failures.append(
                (topics_file, f"{topics_file}: topic is not a mapping — skipped"))
            continue
        tid = _record_id(topic)
        if tid is None:
            repo.parse_failures.append(
                (topics_file,
                 f"{topics_file}: topic with missing or empty id — skipped"))
            continue
        _register(repo, repo.topics, tid, topic, topics_file, "topic")
