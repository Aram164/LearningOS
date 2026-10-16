"""Downward-owned command plumbing with a single owner (S13 candidate).

The operator lock, gateway refusal cellar, publish helpers and small
leaves, moved verbatim from commands.support so the ops pipeline can
import them downward. The session-ledger readers moved on to
`store/session_ledger.py` (S29); the operator-lock path still resolves
its state directory through that module's helpers.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fresh-manifest reads, moved verbatim from commands.support for the S15 pilot
# conversions (SPEC (az) item 2: the shared fresh-manifest closure moves below
# its callers instead of taking a new upward A1 import).










# ---------------------------------------------------------------------------
# Read preflight, moved verbatim from commands.reads (SPEC (az) item 2).




# ---------------------------------------------------------------------------
# Content-bound input, moved verbatim from commands.support (SPEC (az) item 2).










# ---------------------------------------------------------------------------
# Structured record/file input, moved verbatim from commands.support for the
# plan record/file conversions (SPEC (bo) item 2).


# ---------------------------------------------------------------------------
# Canonical YAML serialization, moved verbatim from commands.support
# (SPEC (az) item 2).










# ---------------------------------------------------------------------------
# Material planning helpers, moved verbatim from commands.material for the
# route.patch conversion (SPEC (az) item 2, (bd)).









# ---------------------------------------------------------------------------
# Notes shared helpers, moved verbatim from commands.support, commands.capability,
# commands.query and commands.reads for the wave-1 notes conversions (SPEC (bl),
# CODEX-WAVE1-DISPOSITIONS-20261010 items 2-3). Bodies and signatures unchanged;
# _window_values is the extracted value-based core of commands.reads._window.
















# Atlas authoring guards, moved verbatim from commands.atlas for the
# atlas.question.save conversion (SPEC (bo) 2).






# ---------------------------------------------------------------------------
# Atlas relation registries, moved verbatim from commands.atlas for the
# concept.relations.change conversion (SPEC (bo) 2).





# At most this many untargeted rows ride the screen; the section's
# ``total`` stays exact past the bound. Moved verbatim from
# commands.resume for the plan reads (SPEC (bo) item 2).


# ---------------------------------------------------------------------------
# Analysis-note scope and freshness, moved verbatim from commands.reads
# for the plan reads (SPEC (bo) item 2).











# ---------------------------------------------------------------------------
# Offset/limit validation with the exact commands.reads._window rules,
# added with exactly the conductor's text for the plan reads and the
# notes wave (SPEC (bs) item 4).


# ---------------------------------------------------------------------------
# Use-evidence tallies and note bytes, moved verbatim from
# commands.reads for the plan reads (SPEC (bo) item 2).


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

# Value-based window core (SPEC (bl) item 3): the exact validations and
# messages of commands/reads.py:_window, taking request values directly so
# converted handlers pass no namespace.


# ---------------------------------------------------------------------------
# Inbox discovery rows, moved verbatim from commands/query.py (SPEC (bo)
# item 2): the status conversion needs them while search and inbox-list
# still call them from commands.


# ---------------------------------------------------------------------------
# Ranked intelligence scan, moved verbatim from commands/intelligence.py
# (SPEC (bo) item 2): the intelligence-scan conversion needs ranked_scan
# while cmd_resume still calls it from commands. It rests here: the body
# keeps its load_repo, which A4 forbids inside ops/handlers.










# ---------------------------------------------------------------------------
# Stage-use evidence tallies, moved verbatim from commands/reads.py
# (SPEC (bo) item 2): cli.related's related_records and plan's
# material-context both need them, so they rest here.


# The declared source-feedback vocabulary, grouped for ranking. Positive
# values say the source served; mismatch values say it did not fit this
# use. "skipped" is recorded evidence about the stage, not about the
# source, so it is reported and never ranks.




