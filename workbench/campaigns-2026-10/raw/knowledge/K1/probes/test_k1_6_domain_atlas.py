"""K1 invariant 6 (ADR-005 decision 1): generated/domain-atlas.md drops no
shelf — an unlisted collection falls back to cross-domain — and every shelf
description it prints is harvested from the canonical `description:` field."""

from __future__ import annotations

import re

import yaml

from learning_os.derive.projection import generate_all
from learning_os.store.loader import load_repo
from learning_os.derive.projection.atlas import ATLAS_COLLECTION_DOMAIN

LONG_DESC = ("A deliberately long canonical description that must be harvested "
             "verbatim up to the compaction limit: " + "detail " * 40).strip()


def _atlas_repo(mini_repo):
    """One mapped shelf with a description, one mapped shelf with a very long
    description, and one shelf the view-level domain map has never heard of."""
    from repo_builders import write_yaml

    write_yaml(mini_repo / "sources/collections/math-bookshelf.yaml", {
        "title": "Math bookshelf", "collection_kind": "catalogue",
        "description": "Canonical short description of the math shelf.",
        "entries": [{"source": "source-demo-book", "why": "Reference."}],
    })
    write_yaml(mini_repo / "sources/collections/ml-bookshelf.yaml", {
        "title": "ML bookshelf", "collection_kind": "catalogue",
        "description": LONG_DESC,
        "entries": [{"source": "source-demo-book", "why": "Reference."}],
    })
    write_yaml(mini_repo / "sources/collections/mystery-shelf.yaml", {
        "title": "Mystery shelf", "collection_kind": "catalogue",
        "description": "A shelf the view-level domain map does not name.",
        "entries": [{"source": "source-demo-book", "why": "Reference."}],
    })
    return mini_repo


def _domain_sections(atlas_text):
    sections: dict[str, list[str]] = {}
    current = None
    for line in atlas_text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def test_no_shelf_is_dropped_and_the_unmapped_one_lands_in_cross_domain(mini_repo):
    outputs = generate_all(load_repo(_atlas_repo(mini_repo)), generated_at="T1")
    atlas = outputs["domain-atlas.md"]
    sections = _domain_sections(atlas)

    linked = re.findall(r"\[([^\]]+)\]\(collections/([a-z0-9-]+)\.md\)", atlas)
    names = {name for _, name in linked}
    assert names == {"math-bookshelf", "ml-bookshelf", "mystery-shelf"}
    # Each shelf linked exactly once — no shelf silently repeated or dropped.
    assert len(linked) == 3

    assert any("collections/mystery-shelf.md" in line
               for line in sections.get("cross-domain", []))
    assert any("collections/math-bookshelf.md" in line
               for line in sections.get("mathematics", []))
    assert any("collections/ml-bookshelf.md" in line
               for line in sections.get("machine-learning", []))
    assert ATLAS_COLLECTION_DOMAIN["math-bookshelf"] == "mathematics"
    assert ATLAS_COLLECTION_DOMAIN["ml-bookshelf"] == "machine-learning"


def test_descriptions_are_harvested_from_the_canonical_field(mini_repo):
    outputs = generate_all(load_repo(_atlas_repo(mini_repo)), generated_at="T1")
    atlas = outputs["domain-atlas.md"]
    assert "Canonical short description of the math shelf." in atlas
    # The long canonical description is compacted, never replaced or authored:
    # the printed text is a prefix of the canonical text ending in the
    # ellipsis the compactor appends.
    printed = re.search(
        r"\*\*\[ML bookshelf\]\(collections/ml-bookshelf\.md\)\*\* \((\d+)\) — (.+)",
        atlas)
    assert printed, atlas
    assert printed.group(2).endswith(" …")
    assert LONG_DESC.startswith(printed.group(2)[:-2].rstrip())


def test_domains_without_shelves_say_so_and_future_buckets_appear(mini_repo):
    outputs = generate_all(load_repo(_atlas_repo(mini_repo)), generated_at="T1")
    atlas = outputs["domain-atlas.md"]
    # A domain with no shelf says so instead of going silent (algorithms has
    # no collection in this fixture).
    assert "Shelves: none yet" in atlas
    # mini_repo's only note bucket is knowledge/notes/mathematics; the atlas
    # still publishes every known domain plus the note buckets it found.
    for dom in ("mathematics", "machine-learning", "systems", "data-systems",
                "algorithms", "programming", "cross-domain"):
        assert f"## {dom}" in atlas
