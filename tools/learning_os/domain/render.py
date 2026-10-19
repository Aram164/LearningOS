"""Markdown structure editing for canonical bodies.

Section replacement is done by parsing the document into blocks, mutating one
block, and re-serialising — never by regex substitution over the raw text.

Two concrete failures motivated this (both reproducible against the previous
regex implementation):

* A replacement containing LaTeX raised ``re.error: missing <``, because
  ``re.sub`` interprets backslashes in the *replacement* string: ``\\gamma``
  reads as the start of a ``\\g<name>`` group reference. ``\\1`` was worse — it
  silently substituted a capture group instead of the author's text. Note
  bodies in this repository are full of LaTeX, so this was a live hazard.

* A fenced code block containing a line starting with ``## `` was treated as a
  section boundary, truncating the replacement early and leaving an orphaned
  fence with its contents promoted to real headings.

Author text is never interpreted here. It is placed, not substituted.
"""

from __future__ import annotations

from dataclasses import dataclass

FENCES = ("```", "~~~")


@dataclass(frozen=True)
class Section:
    """One ``## `` section: its heading text and the body lines beneath it."""

    heading: str
    lines: list[str]


def _fence_delimiter(line: str) -> str | None:
    stripped = line.lstrip()
    for fence in FENCES:
        if stripped.startswith(fence):
            return fence
    return None


def iter_blocks(body: str):
    """Yield ``(is_heading, heading_text, line)`` with fences accounted for.

    A line only counts as a heading when it is not inside a fenced code block,
    which is the distinction the regex could not make.
    """
    open_fence: str | None = None
    for line in body.split("\n"):
        delimiter = _fence_delimiter(line)
        if open_fence is not None:
            # Inside a fence: only its matching delimiter can close it.
            if delimiter == open_fence:
                open_fence = None
            yield False, None, line
            continue
        if delimiter is not None:
            open_fence = delimiter
            yield False, None, line
            continue
        if line.startswith("## "):
            yield True, line[3:].strip(), line
        else:
            yield False, None, line


def parse_sections(body: str) -> tuple[list[str], list[Section]]:
    """Split a body into (preamble lines, sections in document order)."""
    preamble: list[str] = []
    sections: list[Section] = []
    for is_heading, heading, line in iter_blocks(body):
        if is_heading:
            sections.append(Section(heading=heading or "", lines=[]))
        elif sections:
            sections[-1].lines.append(line)
        else:
            preamble.append(line)
    return preamble, sections


def serialise(preamble: list[str], sections: list[Section]) -> str:
    out: list[str] = []
    if any(line.strip() for line in preamble):
        out.extend(preamble)
        while out and not out[-1].strip():
            out.pop()
        out.append("")
    for section in sections:
        out.append(f"## {section.heading}")
        body = list(section.lines)
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        out.append("")
        out.extend(body)
        out.append("")
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) + "\n"


def replace_h2_section(body: str, heading: str, content: str) -> str:
    """Replace one ``## `` section's content, leaving its neighbours untouched.

    Raises ``ValueError`` if the heading is absent, so a caller cannot silently
    write a section the document never declared.
    """
    preamble, sections = parse_sections(body)
    for index, section in enumerate(sections):
        if section.heading == heading:
            sections[index] = Section(heading=heading, lines=content.strip().split("\n"))
            return serialise(preamble, sections)
    raise ValueError(f"workspace section not found: {heading}")
