"""Ephemeral session counts: the observable source the scan refuses to keep.

Three Phase-3 detectors — repeated questions, inspection patterns,
reviewer corrections — stay caller-fed because their counts exist only
in a live session: which question classes recurred, which file sets
were read together, which task classes got corrected. LearningOS must
not record any of that (Phase 4 amendment: no telemetry database), so
this module offers the two halves that keep the boundary clean:

- ``SessionCounts``: a caller-held, in-memory counter. It has no file
  IO at all — nothing here can persist, so nothing here can become a
  telemetry log by accident. A long-lived caller (an agent harness, a
  review session) holds one instance and passes ``snapshot()`` into the
  scan. A fresh instance starts empty; counts never cross sessions.
- ``parse_feed``: strict validation for a caller-supplied feed mapping
  (the ``--feed`` file shape). Malformed feeds refuse; unknown keys
  refuse, so a typo cannot silently narrow what the scan sees.

Coverage stays caller knowledge: the feed names the VOQ classes and
dossier sets already covered, because the VOQ fixtures are test-only
by plan decision and there is no runtime registry to consult. An empty
feed behaves exactly like no feed — the three detectors stay silent.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


class FeedError(ValueError):
    """A caller-supplied scan feed cannot be read as written."""


#: Feed keys, and nothing else. Unknown keys refuse.
FEED_KEYS = (
    "question_counts",
    "inspection_counts",
    "correction_counts",
    "voq_classes",
    "dossier_sets",
)


def _count(value: object, label: str) -> int:
    """A non-negative integer count. Booleans are never counts."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise FeedError(f"malformed feed: {label} is not an integer count")
    if value < 0:
        raise FeedError(f"malformed feed: {label} is negative")
    return value


def _token(value: object, label: str) -> str:
    """A non-empty string token."""
    if not isinstance(value, str) or not value.strip():
        raise FeedError(f"malformed feed: {label} is not a non-empty string")
    return value


def _string_list(value: object, label: str) -> list[str]:
    """A list of non-empty strings. A bare string is never a list."""
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise FeedError(f"malformed feed: {label} is not a list of strings")
    return [_token(item, f"{label} entry") for item in value]


def _count_map(value: object, label: str) -> dict[str, int]:
    """A class-name to count mapping."""
    if not isinstance(value, Mapping):
        raise FeedError(f"malformed feed: {label} is not a mapping")
    try:
        items = list(value.items())
    except (TypeError, ValueError) as exc:
        raise FeedError(f"malformed feed: {label}: {exc}") from exc
    counts = {}
    for name, count in items:
        key = _token(name, f"{label} class")
        counts[key] = _count(count, f"{label} count for {key!r}")
    return counts


def _inspection_rows(value: object) -> list[dict]:
    """``[{"files": [...], "count": n}]`` — JSON cannot key on file sets."""
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise FeedError("malformed feed: inspection_counts is not a list")
    rows = []
    for index, row in enumerate(value):
        label = f"inspection_counts[{index}]"
        if not isinstance(row, Mapping):
            raise FeedError(f"malformed feed: {label} is not a mapping")
        unknown = set(row) - {"files", "count"}
        if unknown:
            raise FeedError(
                f"malformed feed: {label} carries unknown keys "
                f"{sorted(str(key) for key in unknown)}")
        try:
            files = row["files"]
            count = row["count"]
        except KeyError as exc:
            raise FeedError(f"malformed feed: {label} misses {exc}") from exc
        names = _string_list(files, f"{label}.files")
        if not names:
            raise FeedError(f"malformed feed: {label}.files is empty")
        rows.append({"files": names, "count": _count(count, f"{label}.count")})
    seen: set[frozenset] = set()
    for index, row in enumerate(rows):
        key = frozenset(row["files"])
        if key in seen:
            raise FeedError(
                f"malformed feed: inspection_counts[{index}] repeats an "
                "already-listed file set")
        seen.add(key)
    return rows


def parse_feed(data: object) -> dict:
    """Validate a caller-supplied feed mapping. Fails closed.

    Returns the feed with every section present: counts as mappings,
    inspection rows as a list, coverage as string lists. Thresholds
    stay detector-side — the feed reports what happened, never what
    the scan should conclude.
    """
    if not isinstance(data, Mapping):
        raise FeedError("malformed feed: expected a mapping at the top level")
    unknown = set(data) - set(FEED_KEYS)
    if unknown:
        raise FeedError(
            "malformed feed: unknown keys "
            f"{sorted(str(key) for key in unknown)}")
    inspections = _inspection_rows(data.get("inspection_counts", []))
    dossiers = data.get("dossier_sets", [])
    if isinstance(dossiers, (str, bytes, bytearray)) or not isinstance(dossiers, Sequence):
        raise FeedError("malformed feed: dossier_sets is not a list of lists")
    return {
        "question_counts": _count_map(
            data.get("question_counts", {}), "question_counts"),
        "inspection_counts": inspections,
        "correction_counts": _count_map(
            data.get("correction_counts", {}), "correction_counts"),
        "voq_classes": _string_list(data.get("voq_classes", []), "voq_classes"),
        "dossier_sets": [
            _string_list(entry, f"dossier_sets[{index}]")
            for index, entry in enumerate(dossiers)
        ],
    }


def feed_scan_kwargs(feed: Mapping) -> dict:
    """A parsed feed as ``ScanInput`` keyword arguments.

    Counts render as sorted tuples for determinism; inspection file
    sets render sorted so the same set reads identically however the
    caller listed it. Coverage renders alongside, so detectors that
    need it (question gaps, dossier gaps) see caller-declared cover.
    """
    parsed = parse_feed(feed)
    return {
        "question_counts": tuple(sorted(parsed["question_counts"].items())),
        "inspection_counts": tuple(sorted(
            (tuple(sorted(row["files"])), row["count"])
            for row in parsed["inspection_counts"]
        )),
        "correction_counts": tuple(sorted(parsed["correction_counts"].items())),
        "voq_classes": tuple(parsed["voq_classes"]),
        "dossier_sets": tuple(tuple(entry) for entry in parsed["dossier_sets"]),
    }


def feed_is_empty(feed: Mapping) -> bool:
    """No counts at all: the detectors stay silent, as without a feed."""
    try:
        questions = feed["question_counts"]
        inspections = feed["inspection_counts"]
        corrections = feed["correction_counts"]
    except KeyError:
        return True
    return not questions and not inspections and not corrections


class SessionCounts:
    """In-memory session counters for one live caller. No persistence.

    The instance holds what one session observed; ``snapshot()``
    renders it as a ``parse_feed``-shaped mapping the caller may pass
    to the scan. Coverage (VOQ classes, dossier sets) is caller
    knowledge and stays out — counts observe, coverage declares.
    """

    def __init__(self) -> None:
        self._questions: dict[str, int] = {}
        self._inspections: dict[tuple[str, ...], int] = {}
        self._corrections: dict[str, int] = {}

    def note_question(self, question_class: str) -> None:
        """One operator question of this class was asked and answered."""
        key = _token(question_class, "question class")
        self._questions[key] = self._questions.get(key, 0) + 1

    def note_inspection(self, files: Sequence[str]) -> None:
        """One task read this exact file set together."""
        names = tuple(sorted(set(_string_list(files, "inspection files"))))
        if not names:
            raise FeedError("malformed session count: inspection files is empty")
        self._inspections[names] = self._inspections.get(names, 0) + 1

    def note_correction(self, task_class: str) -> None:
        """A reviewer corrected this task class once."""
        key = _token(task_class, "task class")
        self._corrections[key] = self._corrections.get(key, 0) + 1

    def snapshot(self) -> dict:
        """Current counts as a feed mapping. Sorted for determinism."""
        return {
            "question_counts": {
                key: self._questions[key] for key in sorted(self._questions)
            },
            "inspection_counts": [
                {"files": list(names), "count": self._inspections[names]}
                for names in sorted(self._inspections)
            ],
            "correction_counts": {
                key: self._corrections[key] for key in sorted(self._corrections)
            },
            "voq_classes": [],
            "dossier_sets": [],
        }
