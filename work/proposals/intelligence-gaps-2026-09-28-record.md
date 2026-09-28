# Intelligence gaps — session counts, rank precedence, coverage ranking (2026-09-28)

Branch: `muse/intelligence-gaps-2026-09-28`. Parent review: memo review
2026-09-28 (review items 1–6). This record covers what was decided and
built; the PCC ranking itself is `pcc-coverage-ranking-2026-09-28.md`.

## Built

**Ephemeral session counts (review item 2).** The three caller-fed
detectors (repeated questions, inspection patterns, reviewer corrections)
had no servable feed. Now: `tools/learning_os/semantics/session_counts.py`
holds `SessionCounts` (in-memory only — no file IO exists on it, so it
cannot become a telemetry log), strict `parse_feed` validation, and
`feed_scan_kwargs`. `ScanInput` carries the feed; `scan_observations`
runs the three detectors only when fed (empty feed is bit-identical to
no feed); `los intelligence-scan --feed FILE` reads a caller-owned JSON
feed and never writes it. Coverage (VOQ classes, dossier sets) stays
caller-declared: the VOQ fixtures are test-only by plan decision, so the
scan cannot consult them. Proven by `tests/test_session_counts.py`
(24 tests, incl. a CLI read-only check on the feed file).

**Detector precedence (review item 4, first step).** `rank_clusters` now
breaks urgency ties by `DETECTOR_PRECEDENCE` before fan-out size: belief
risk (contested/unreviewed claims, stale lineage, superseded evidence)
surfaces above large obligation clusters; system self-improvement sorts
below learner-facing work; unknown detectors sort last so a new detector
earns precedence explicitly. Tiers still dominate. This is tunable data,
not a fitted model. Existing select/scan suites stay green unmodified.

## Decided

**Heartbeat (review item 1): on-demand stays the shipped default.** No
daemon, no installed schedule. Reasons: the scan's read-only/no-write
posture is load-bearing (a scheduled scan that files goals would be the
first automatic writer into the proposal queue — an authority change, not
an optimization), and there is no evidence yet that manual cadence misses
detections. Revisit iff a missed detection is ever traced to cadence.
Scheduled recipe (read-only scan, caller's own log, nothing installed):

```bash
# Example: weekday-morning scan of the live checkout into the caller's log.
los --root ~/Desktop/semestercontext/LearningOS/repository intelligence-scan --brief >> ~/.los-scan.log 2>&1
```

**Phase 4 amendment ratification (review item 3): draft for Aram.** The
amendment record states what was removed but not why or on whose authority.
Proposed one-line ratification (confirm or correct in your own words):

> Telemetry stays out because stored measurement of agent behavior would
> itself become behavior-shaping infrastructure — costs to maintain, gaming
> surface to defend — for gains the static router already captures; revisit
> only on a concrete routing failure the vetoes cannot express. — Aram, 2026-09-28

## Open follow-ups (not this branch)

- Runtime VOQ-class/dossier coverage source, so feeds need not declare
  cover (needs a design that respects the fixtures-are-test-only decision).
- Dossier-publish lineage question (ranking item 1). The proposed
  `unit.plan.revise` Phase B extension was removed from the backlog after
  verifying that unit revisions already use the module import's Phase B
  preflight and lineage write path.
- VOQ coverage for new predicates (cap rule is disjunctive; coverage thins).

## Fast operator follow-through

`resume --study` now offers a nearest-exam stage and one exact required-resource
locator without changing the resume pointer; it reports the recorded
registration state. `material-span` now gives the explicit local-observation
steps when a route is remote or a registered file is missing. A `log:` message
is a direct, verbatim capture request under the existing gateway, routed to a
stage only when the stage was explicitly identified in the conversation.
Goal deferrals may name a `revisit_on` date; the scan re-emits the candidate on
that date without authorizing it. None of these paths fetches material,
chooses a goal disposition, or writes during a read.
