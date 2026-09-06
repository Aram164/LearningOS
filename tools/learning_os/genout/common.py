"""Small shared helpers: headers, slugs, git state, generation timestamps."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .. import __version__
from ..errors import TransactionFailure
from ..fingerprint import CANONICAL_ROOTS
from ..githistory import GitHistoryError, last_commit_date, read_history

LECTURE_KEY_RE = re.compile(r"^(?:VL\s*)?L?\d{1,2}\b")


SELECTOR_ROLES = ("first-learning", "review", "implementation")


def mermaid_node_ids(ids) -> dict[str, str]:
    """Map concept IDs to unique, Mermaid-safe node identifiers.

    Sanitizing an ID to Mermaid's allowed character set can map distinct IDs to
    the same token (e.g. 'concept-a-b' and 'concept-a.b' both collapse to
    'concept_a_b'). Emitting two nodes with an identical identifier silently
    merges them in the rendered graph. Assigning a disambiguating suffix on
    collision guarantees every input ID gets its own node. Deterministic:
    inputs are processed in sorted order.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for cid in sorted(ids):
        base = re.sub(r"[^0-9A-Za-z_]", "_", cid)
        if not base or not (base[0].isalpha() or base[0] == "_"):
            base = "n_" + base
        name = base
        i = 2
        while name in used:
            name = f"{base}__{i}"
            i += 1
        used.add(name)
        mapping[cid] = name
    return mapping


def _md_header(title: str, generated_at: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "> ⚠️ GENERATED file — a disposable VIEW over the canonical records, not "
        "part of the canonical architecture. Never edit; edit canonical inputs "
        f"instead. Rebuilt by `python tools/generate.py` (learning_os v{__version__}) "
        "from: knowledge/, sources/, curriculum/, records/, work/.",
        f"> Generated: {generated_at}",
        "",
    ]


def _json_header(generated_at: str) -> dict:
    return {
        "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py",
        "generator": f"learning_os v{__version__}",
        "generated_at": generated_at,
    }


def _slug(heading: str) -> str:
    """GitHub-style anchor for a Markdown heading."""
    s = heading.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in " -")
    return s.replace(" ", "-")


def _letter_toc(entries: list[tuple[str, str]]) -> list[str]:
    """Compact letter-grouped table of contents.

    entries: (display text, heading text used for the anchor), pre-sorted.
    Returns one line per starting letter: 'A: [x](#x) · [y](#y)'.
    """
    lines: list[str] = []
    by_letter: dict[str, list[str]] = {}
    for display, heading in entries:
        letter = display[:1].upper() if display else "#"
        if not letter.isalpha():
            letter = "#"
        by_letter.setdefault(letter, []).append(f"[{display}](#{_slug(heading)})")
    for letter in sorted(by_letter):
        lines.append(f"**{letter}:** " + " · ".join(by_letter[letter]))
        lines.append("")
    return lines


def _git_last_commit(root: Path, rel: str) -> str:
    try:
        return last_commit_date(root, rel)
    except GitHistoryError as exc:
        raise TransactionFailure(f"failed to read git history: {exc}") from exc


def stable_generated_at(root: Path) -> str:
    """Reproducible generation timestamp: the repository's last-commit time.

    Regenerating without new commits yields byte-for-byte identical output
    (improvement: no wall-clock noise in generated files). Falls back to a
    fixed marker for a tree without history (e.g. synthetic test repos).
    """
    try:
        ts = read_history(root, "-1", "--format=%cI").strip()
        if ts:
            return f"{ts} (last commit)"
    except GitHistoryError as exc:
        raise TransactionFailure(f"failed to read git history: {exc}") from exc
    return "(no Git history available)"


def _git_state(root: Path) -> tuple[str | None, bool]:
    """Publish cleanliness only after successful Git queries.

    An explicit non-repository response is the sole no-history exception.
    Keep Git diagnostics in English so that exception is independent of locale.
    """
    try:
        env = {**os.environ, "LC_ALL": "C"}
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=30, env=env)
        if rev.returncode != 0:
            if "fatal: not a git repository" in rev.stderr:
                return None, False
            raise TransactionFailure(f"Git failed to read revision:\n{rev.stderr.strip()}")
        if not rev.stdout.strip():
            raise TransactionFailure("Git returned an empty revision")
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--",
             *CANONICAL_ROOTS],
            cwd=root, capture_output=True, text=True, timeout=30, env=env)
        if status.returncode != 0:
            raise TransactionFailure(f"Git failed to check status:\n{status.stderr.strip()}")
        return rev.stdout.strip(), bool(status.stdout.strip())
    except subprocess.TimeoutExpired as exc:
        raise TransactionFailure("Git timed out while checking repository state") from exc
    except OSError as exc:
        raise TransactionFailure(f"Git failed to execute: {exc}") from exc


def _strip_headings(text: str | None) -> str:
    """Drop headings, blockquote callouts and list bullets so `_first_para`
    lands on actual prose. Used for the manifest's `summary` fields."""
    if not text:
        return ""
    keep = []
    for line in text.split("\n"):
        stripped = line.strip()
        if (stripped.startswith("#") or stripped.startswith(">")
                or stripped.startswith("|") or stripped.startswith("```")
                or set(stripped) <= {"-", "*", "_"} and len(stripped) >= 3):
            continue
        keep.append(line)
    return "\n".join(keep)


def _first_para(text: str | None) -> str:
    if not text:
        return ""
    for block in text.split("\n\n"):
        block = " ".join(block.split())
        if block:
            return block
    return ""
