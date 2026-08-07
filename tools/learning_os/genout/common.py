"""Small shared helpers: headers, slugs, git state, generation timestamps."""

from __future__ import annotations

import re
import subprocess
from .. import __version__
from pathlib import Path

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
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                             cwd=root, capture_output=True, text=True, timeout=30)
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def stable_generated_at(root: Path) -> str:
    """Reproducible generation timestamp: the repository's last-commit time.

    Regenerating without new commits yields byte-for-byte identical output
    (improvement: no wall-clock noise in generated files). Falls back to a
    fixed marker when Git is unavailable (e.g. synthetic test repos).
    """
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI"],
                             cwd=root, capture_output=True, text=True, timeout=30)
        ts = out.stdout.strip()
        if out.returncode == 0 and ts:
            return f"{ts} (last commit)"
    except Exception:  # noqa: BLE001
        pass
    return "(no Git history available)"


def _git_state(root: Path) -> tuple[str | None, bool]:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=30)
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--",
             "knowledge", "sources", "records", "work", "curriculum", "system/schema"],
            cwd=root, capture_output=True, text=True, timeout=30)
        return (rev.stdout.strip() or None, bool(status.stdout.strip()))
    except Exception:  # noqa: BLE001
        return None, False


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
