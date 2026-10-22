"""Validation rules for Learning OS v3 (BUILD-SPEC Step 4).

Implements system/VALIDATION.md on top of the JSON Schemas in system/schema/.
Severity: E = error (blocks acceptance), W = warning.

Scope notes (documented decisions):
  - Internal-link integrity is checked for canonical trees (knowledge/, sources/,
    records/, work/) — NOT for archive/ (archived workspaces are preserved
    unchanged and may carry legacy paths) and NOT for system/ (spec package).
  - The generated-input boundary is checked for the same canonical trees.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Collision suffixes are short counters (-02, -03, …); longer trailing numbers
# are usually identifiers (course numbers like -1805, -6036), not suffixes.
SUFFIX_RE = re.compile(r"^(?P<base>.+)-(?P<num>\d{1,2})$")
WORKSPACE_TOKEN_RE = re.compile(r"\bworkspace-[a-z0-9]+(?:-[a-z0-9]+)*\b")


def id_list_items(value):
    """Iterate valid ID-shaped items; schema errors own malformed list shapes."""
    return (item for item in value if isinstance(item, str)) \
        if isinstance(value, list) else ()


def list_items(value):
    """Do not iterate a schema-invalid scalar string as a list of characters."""
    return value if isinstance(value, list) else ()


REQUIRED_WORKSPACE_SECTIONS = ("Objective", "Current Scope", "Open Questions", "Next Action")
COORDINATION_SECTIONS = ("Commitments", "Priorities", "Dependencies", "Deferrals")

# Crosswalk judgment-table heuristic vocabulary (exact header cells, case-insensitive)
JUDGMENT_HEADERS = {"strengths", "weaknesses", "level", "best for", "best-for"}

GENERATED_ALLOWED = {
    "manifest.json", "manifest.identity.json", "concept-index.md", "source-index.md", "module-view.md",
    "coordination-view.md", "dependency-report.md", "concept-map.md",
    "backlinks.json", "nebula.md", "domain-atlas.md", "reading-room.md",
    "concept-canvas.canvas", "library.md", "study-plans.md",
    "learning-requirements.md", "learning-requirements.json",
    "learner-interpretations.json",
    "learner-interpretations.md",
    ".gitkeep",
    ".DS_Store",  # OS metadata noise, gitignored — not an agent artifact
}
GENERATED_REPORT_PREFIXES = ("validation-report", "health")

# Warnings about the environment *around* the authored content — a stale
# generated view, an unmounted drive, an inventory that needs rebuilding — as
# opposed to warnings about the content itself. A preflight asking "does this
# proposed change introduce a problem?" must ignore them: they are true before
# and after the change, so treating them as blockers makes an unrelated command
# fail because a drive happens to be offline. Errors always block regardless.
ENVIRONMENTAL_WARNINGS = frozenset({
    # A pinned local-only attachment that is not on this machine (a CI
    # checkout or a fresh clone): the pin still records what belongs there.
    "ATTACH-LOCAL-ABSENT",
    "HYGIENE-VIEWS",
    "MATERIALS-MANIFEST",
    "MATERIALS-OFFLINE",
    "MATERIALS-DRIFT",
    "MATERIAL-URI-FORM",
    "HYGIENE-LOCK",
    # A correction review whose evidence bytes are not on this machine (the
    # materials tree is offline or the file is absent). The content did not
    # change, only the mount did — like MATERIALS-OFFLINE, it must stay
    # visible in every run without ever becoming a baseline regression.
    "ANGLE-REVIEW-UNVERIFIED",
})

# Warnings that depend on wall-clock age rather than on any authored file's
# content. A release can turn red with no authored change simply because time
# passed (a workspace crossed its neglect threshold, an inbox item aged out).
# Kept as its own exact set — never merged into ENVIRONMENTAL_WARNINGS, which
# is about machine state, not elapsed time — so each category's rationale
# stays legible and neither one can absorb an unrelated code by accident.
DYNAMIC_ADVISORY_WARNINGS = frozenset({
    "WS-NEGLECT",
    "INBOX-STALE",
})

# The exact, explicit union `warning_baseline.py` treats as baseline-exempt.
# Membership is by exact code only — never a prefix, a severity band, or a
# path heuristic — so an unknown future warning code is baseline-managed
# (visible and blocking on regression) unless someone deliberately adds it
# here.
BASELINE_EXEMPT_WARNINGS = ENVIRONMENTAL_WARNINGS | DYNAMIC_ADVISORY_WARNINGS

CANONICAL_TREES = ("knowledge", "sources", "records", "work", "curriculum", "projects")

# File extensions that are legitimately authored text under knowledge/ (notes and
# registries). Anything else there (PDFs, slides, images) is a misplaced binary
# — see BINARY-IN-KNOWLEDGE. (Formerly the misleadingly named IMAGE_OK.)
KNOWLEDGE_TEXT_SUFFIXES = {".md", ".yaml", ".yml"}

# knowledge/garden/ is the exploratory layer (CLAUDE.md §14): deliberately
# free-form and exempt from every structural rule. The validator skips it
# wherever it walks the canonical trees, so half-formed notes — informal links,
# bare wikilinks, references to generated/ — never block `make check`. (Stray
# non-Markdown files there are still flagged, keeping the Garden text-only.)
GARDEN_SUBTREE = ("knowledge", "garden")

# work/complaints/ is the evidence layer (OPERATOR: Report observed problems):
# dated records of what an agent observed about the system itself. Nothing
# derives from them, so a complaint that names the generated tree is evidence
# about the system, not a dependency on a derived artifact — the boundary that
# keeps the evidence-reporting workflow from being blocked by the rule it
# documents.
EVIDENCE_SUBTREE = ("work", "complaints")

# ---- Hygiene sweep (ADR-004, 2026-08-03) -----------------------------------
# Mess must be self-announcing inside the canonical repository. External
# archives and external code repositories are intentionally absent. Legacy is
# inspected only by the explicit, allowlist-driven
# ``legacy.archive.inspect`` operation; sibling worktrees such as Stratum are
# outside LearningOS validation entirely.
STALE_LOCK_AGE_S = 600       # index.lock older than this = crashed git process


def in_garden(root: Path, path: Path) -> bool:
    garden = root.joinpath(*GARDEN_SUBTREE)
    return path == garden or garden in path.parents


def in_quarantine(root: Path, path: Path) -> bool:
    """Normal validation never reads sealed prospective content."""
    quarantine = root / "curriculum" / "quarantine"
    return path == quarantine or quarantine in path.parents


def in_evidence(root: Path, path: Path) -> bool:
    """Whether a path is a dated observation about the system itself.

    The evidence layer records what happened; nothing reads it to produce
    anything else. A rule about canonical content depending on derived
    artifacts therefore does not apply to it.
    """
    evidence = root.joinpath(*EVIDENCE_SUBTREE)
    return path == evidence or evidence in path.parents


@dataclass
class Issue:
    severity: str  # "E" | "W"
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        loc = f" [{self.path}]" if self.path else ""
        return f"{self.severity} {self.code}: {self.message}{loc}"


#: Clock-derived codes outside DYNAMIC_ADVISORY_WARNINGS. HYGIENE-LOCK stays
#: out of that set on purpose: the set also exempts its members from the
#: warning baseline, and a stale lock is a real finding, not elapsed time.
_LIVE_HYGIENE_CODES = frozenset({"HYGIENE-LOCK"})


#: Message prefix of the GIT-HISTORY error the neglect check raises when
#: history is unreadable. Hygiene raises GIT-HISTORY too, for a different
#: (cached) reason — the prefix is what tells the cache splice apart.
NEGLECT_GIT_HISTORY_PREFIX = "cannot check workspace neglect: "


def is_live_advisory(issue: Issue) -> bool:
    """Whether the cache-hit path recomputes this issue live.

    The dynamic codes and HYGIENE-LOCK, plus the neglect check's own GIT-HISTORY
    error — which shares its code with hygiene's unrelated one and is
    told apart by the message prefix this module constructs.
    """
    assert isinstance(issue, Issue)
    if issue.code in DYNAMIC_ADVISORY_WARNINGS or issue.code in _LIVE_HYGIENE_CODES:
        return True
    return (issue.code == "GIT-HISTORY"
            and issue.message.startswith(NEGLECT_GIT_HISTORY_PREFIX))
