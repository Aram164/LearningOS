"""Recorded stage source-use feedback, tallied per source."""

from __future__ import annotations

POSITIVE_FEEDBACK = frozenset({"helpful", "useful-for-derivation",
                               "useful-for-review"})


MISMATCH_FEEDBACK = frozenset({"too-advanced", "wrong-perspective"})


def _use_evidence(repo):
    """Recorded stage-use evidence per source id: raw feedback counts.

    Canonical study-map data, so the read's snapshot guard already binds
    it — no observation entry is owed. Counts only; grouping into
    positive/mismatch happens at rank time from the sets above, so a new
    vocabulary value degrades to reported-but-unranked, never to a crash
    or a silent demotion.
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in repo.study_maps.values():
        stages = study_map.data.get("stages", []) or []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies


def _evidence_label(tally):
    positive = sum(count for value, count in tally.items()
                   if value in POSITIVE_FEEDBACK)
    mismatch = sum(count for value, count in tally.items()
                   if value in MISMATCH_FEEDBACK)
    return {"counts": dict(sorted(tally.items())),
            "positive": positive, "mismatch": mismatch}
