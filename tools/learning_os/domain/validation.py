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
# Where an inline link's destination starts; the destination itself is read
# by `markdown_link_targets`, because a title, angle brackets or balanced
# parentheses are beyond what one regex captures correctly.
_MD_LINK_OPEN_RE = re.compile(r"\[[^\]]*\]\(")
_MD_ESCAPABLE = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
_MD_TITLE_CLOSE = {'"': '"', "'": "'", "(": ")"}
_MD_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_MD_CODE_SPAN_RE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL)
# Collision suffixes are short counters (-02, -03, …); longer trailing numbers
# are usually identifiers (course numbers like -1805, -6036), not suffixes.
SUFFIX_RE = re.compile(r"^(?P<base>.+)-(?P<num>\d{1,2})$")
WORKSPACE_TOKEN_RE = re.compile(r"\bworkspace-[a-z0-9]+(?:-[a-z0-9]+)*\b")


def markdown_link_targets(text: str) -> list[str]:
    """The destination of every inline Markdown link in ``text``.

    Read as CommonMark reads an inline link: ``<...>`` or a bare destination
    with balanced, or backslash-escaped, parentheses, then an optional
    ``"title"``, ``'title'`` or ``(title)``. The title is not part of the
    target, so ``[t](./missing.md "title")`` is checked like
    ``[t](./missing.md)``. Text that is not a link (``[t](a b)``, ``[t]()``)
    yields nothing, as before, and neither does a link quoted in a fenced
    block or a code span: code is shown, not followed.
    """
    if "](" not in text:
        return []
    text = _without_code(text)
    targets: list[str] = []
    for match in _MD_LINK_OPEN_RE.finditer(text):
        target = _inline_link_destination(text, match.end())
        if target:
            targets.append(target)
    return targets


def _without_code(text: str) -> str:
    """``text`` with fenced code blocks and code spans blanked out."""
    lines = text.split("\n")
    fence: str | None = None
    for index, line in enumerate(lines):
        opened = _MD_FENCE_RE.match(line)
        if fence is None:
            if opened:
                fence = opened.group(1)
                lines[index] = ""
            continue
        if opened and opened.group(1)[0] == fence[0] \
                and len(opened.group(1)) >= len(fence) \
                and not line.strip().strip(fence[0]):
            fence = None
        lines[index] = ""
    return _MD_CODE_SPAN_RE.sub(" ", "\n".join(lines))


def _skip_link_space(text: str, i: int) -> int:
    """Past spaces and tabs, and at most one line ending (CommonMark)."""
    newline_seen = False
    while i < len(text):
        if text[i] in " \t":
            i += 1
        elif text[i] == "\n" and not newline_seen:
            newline_seen = True
            i += 1
        else:
            break
    return i


def _inline_link_destination(text: str, i: int) -> str | None:
    """The destination of the inline link whose ``(`` ends at ``i``, if it is one."""
    n = len(text)
    i = _skip_link_space(text, i)
    chars: list[str] = []
    if i < n and text[i] == "<":
        j = i + 1
        while j < n and text[j] not in "<>\n":
            if text[j] == "\\" and j + 1 < n and text[j + 1] in _MD_ESCAPABLE:
                chars.append(text[j + 1])
                j += 2
                continue
            chars.append(text[j])
            j += 1
        if j >= n or text[j] != ">":
            return None
        j += 1
    else:
        depth, j = 0, i
        while j < n:
            c = text[j]
            if c == "\\" and j + 1 < n and text[j + 1] in _MD_ESCAPABLE:
                chars.append(text[j + 1])
                j += 2
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    break
                depth -= 1
            elif c.isspace() or ord(c) < 0x20 or c == "\x7f":
                break
            chars.append(c)
            j += 1
        if depth != 0:
            return None
    k = _skip_link_space(text, j)
    if k > j and k < n and text[k] in _MD_TITLE_CLOSE:
        close = _MD_TITLE_CLOSE[text[k]]
        k += 1
        while k < n and text[k] != close:
            k += 2 if text[k] == "\\" else 1
        if k >= n:
            return None
        k = _skip_link_space(text, k + 1)
    if k < n and text[k] == ")":
        return "".join(chars)
    return None


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
# The directories the generated tree holds: the projection's own (reports,
# collection views) and the caches owned by sibling producers. A test pins it
# against what the projection writes and keeps.
GENERATED_DIRECTORIES = frozenset({
    "reports", "collections", "text-cache", "summaries", "dossiers",
    "derived-state",
})

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
