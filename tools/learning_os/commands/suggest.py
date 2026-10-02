"""Shared not-found suggestions and expansion formatting for read commands.

Every read refusal funnels its candidates through here, so a mistyped id
costs one line of stderr instead of an extra discovery read: suggestions
are text, never an automatic retry. Ranking is deterministic — exact
case-fold, then zero-padding normalisation (``l5`` matches ``l05``), then
prefix, then substring, then ``difflib`` — over caller-supplied manifest
ids, at most five shown with an exact count of further strong matches.

``expansion`` is the one printed form for every runnable follow-up: the
argv after the program, with no prefix, ``shlex.join``-ed so arguments
carrying spaces survive the copy. Run one as
``.venv/bin/python tools/los.py <expansion>`` (see OPERATOR.md).
"""

from __future__ import annotations

import difflib
import re
import shlex
from collections.abc import Iterable

#: At most this many suggestions ride on a refusal; further strong
#: matches collapse into an exact "+N more" count.
MAX_SUGGESTIONS = 5

#: ``difflib`` floor for the last-chance tier. Prefix and substring hits
#: already carried the obvious near-misses; below this the guesses are
#: noise on short ids.
_DIFFLIB_CUTOFF = 0.6

_ZERO_RUN = re.compile(r"\d+")


def _normalized(value: str) -> str:
    """Case-folded id with zero-padding erased: ``l05`` meets ``l5``."""
    return _ZERO_RUN.sub(
        lambda match: match.group().lstrip("0") or "0", value.casefold())


def ranked(value: str, candidates: Iterable[str]) -> list[str]:
    """Every strong match for ``value``, best tier first, ids sorted.

    Tiers: exact case-fold, zero-padding normalisation, prefix, then
    substring — each deduplicated against the tiers above it. Pure and
    deterministic: the same value and candidate set always answer the
    same order.
    """
    wanted = value.casefold()
    ordered = sorted(set(candidates))
    tiers: list[list[str]] = [[], [], [], []]
    seen: set[str] = set()
    for candidate in ordered:
        folded = candidate.casefold()
        if folded == wanted:
            tier = 0
        elif _normalized(candidate) == _normalized(value):
            tier = 1
        elif folded.startswith(wanted):
            tier = 2
        elif wanted in folded:
            tier = 3
        else:
            continue
        if candidate not in seen:
            seen.add(candidate)
            tiers[tier].append(candidate)
    return [candidate for tier in tiers for candidate in tier]


def suggest(value: str, candidates: Iterable[str],
            limit: int = MAX_SUGGESTIONS) -> list[str]:
    """At most ``limit`` suggestions: strong matches, then ``difflib`` fill.

    The fuzzy tier only fills slots the strong tiers left empty, so a
    query with five prefix hits never pays for — or sees — a guess.
    """
    strong = ranked(value, candidates)
    shown = list(strong[:limit])
    if len(shown) < limit:
        pool = sorted(set(candidates) - set(shown))
        shown.extend(difflib.get_close_matches(
            value, pool, n=limit - len(shown), cutoff=_DIFFLIB_CUTOFF))
    return shown


def with_suggestions(base: str, value: str, candidates: Iterable[str],
                     limit: int = MAX_SUGGESTIONS) -> str:
    """``base`` plus a bounded suggestion suffix, or ``base`` unchanged."""
    shown = suggest(value, candidates, limit)
    if not shown:
        return base
    extra = max(0, len(ranked(value, candidates)) - limit)
    suffix = ", ".join(shown)
    if extra:
        suffix += f", +{extra} more"
    return f"{base} (did you mean: {suffix}?)"


def not_found(kind: str, value: str, candidates: Iterable[str],
              limit: int = MAX_SUGGESTIONS) -> str:
    """The refusal line for a mistyped id: echo plus bounded suggestions."""
    return with_suggestions(f"{kind} not found: {value}", value, candidates,
                            limit)


def expansion(*parts: str) -> str:
    """One expansion string: the argv after the program, ``shlex.join``-ed."""
    return shlex.join(parts)
