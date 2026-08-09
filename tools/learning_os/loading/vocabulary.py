"""Closed vocabularies and identity patterns the whole repository shares.

These are statements about what the canonical records may say, not about how
they are read. They live apart from the loaders so a rule module can import a
relation type without importing the file-walking machinery, and so adding a
domain loader never means editing the vocabulary.
"""

from __future__ import annotations

import re

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

ID_RE = re.compile(r"^(note|concept|source|workspace|module)-[a-z0-9]+(?:-[a-z0-9]+)*$")
PATH_ID_RE = re.compile(r"^path-[a-z0-9]+(?:-[a-z0-9]+)*$")
PROGRAM_ID_RE = re.compile(r"^program-[a-z0-9]+(?:-[a-z0-9]+)*$")
UNIT_ID_RE = re.compile(r"^unit-[a-z0-9]+(?:-[a-z0-9]+)*$")
STUDY_MAP_ID_RE = re.compile(r"^study-map-[a-z0-9]+(?:-[a-z0-9]+)*$")
PROJECT_ID_RE = re.compile(r"^project-[a-z0-9]+(?:-[a-z0-9]+)*$")
PROJECT_RELATION_ID_RE = re.compile(r"^relationship-[a-z0-9]+(?:-[a-z0-9]+)*$")

# Inline #tags in Garden notes (CLAUDE.md §14). Conservative: a tag starts with
# a lowercase letter (so ATX headings "# H", shebangs, "#1" issue refs and hex
# colours like #Fff are not tags) and may contain lowercase letters, digits,
# hyphens and underscores. It must not follow a word char, "#", "/" or "&" (so
# "##x", "path/#anchor" and HTML entities are skipped).
GARDEN_TAG_RE = re.compile(r"(?<![\w#/&])#([a-z][a-z0-9_-]*)")

# Strip fenced (``` … ```) and inline (`…`) code before pulling #tags, so a
# hashtag written as code — e.g. `#tags` in prose, or a `#include` in a snippet —
# is not mistaken for a tag.
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _strip_code(text: str) -> str:
    return _INLINE_CODE_RE.sub(" ", _CODE_FENCE_RE.sub(" ", text))


RELATION_TYPES = {
    "requires", "builds-on", "derives", "generalizes",
    "contrasts-with", "equivalent-to", "applies-in", "motivates",
}

# Direction and meaning of every relation type. Each edge is read "from <TYPE>
# to": `from` is the subject, `to` is the object. This is the single canonical
# statement of relation semantics (mirrored in the concept-relations schema
# description); tools that reason over the graph must follow it.
#   requires        from needs to as a hard prerequisite (learn `to` first)
#   builds-on       from extends/depends on to (softer prerequisite than requires)
#   derives         from is derived/obtained from to
#   generalizes     from is the more general case; to is the special case
#   contrasts-with  symmetric: from and to are usefully compared/opposed
#   equivalent-to   symmetric: from and to denote the same idea in different guises
#   applies-in      from is applied within the context/domain to
#   motivates       from provides the motivation for to
# `requires` and `builds-on` are the only prerequisite edges (they define study
# order — see tools/learning_os/genout.py PREREQ_TYPES). The remaining six are
# context, never prerequisites. `contrasts-with` and `equivalent-to` are
# symmetric in meaning; the others are directional.
RELATION_SEMANTICS = {
    "requires": "from needs to as a hard prerequisite",
    "builds-on": "from extends/depends on to (soft prerequisite)",
    "derives": "from is derived from to",
    "generalizes": "from is the general case, to the special case",
    "contrasts-with": "symmetric: usefully compared/opposed",
    "equivalent-to": "symmetric: same idea, different guise",
    "applies-in": "from is applied within the context/domain to",
    "motivates": "from provides the motivation for to",
}
PREREQUISITE_RELATIONS = ("requires", "builds-on")
SYMMETRIC_RELATIONS = ("contrasts-with", "equivalent-to")

NOTE_ROLES = {
    "synthesis", "reference", "derivation", "exercise-bank",
    "mock-exam", "implementation", "question", "crosswalk",
}

EVIDENCE_SCHEMES = (
    "note://", "source://", "concept://", "workspace://",
    "material://", "project://", "github://", "https://", "http://",
)
