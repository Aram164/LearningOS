"""Markdown section editing.

The two failures asserted here were live defects in the previous regex
implementation, both reachable from ordinary repository content: LaTeX in a
workspace section, and a fenced code block containing a ``## `` line.
"""

from __future__ import annotations

import pytest

from learning_os.render import parse_sections, replace_h2_section

BODY = (
    "## Objective\n\nold objective\n\n"
    "## Current Scope\n\nkeep this\n\n"
    "## Next Action\n\nand this\n"
)


def test_replaces_only_the_named_section():
    out = replace_h2_section(BODY, "Objective", "brand new")
    assert "brand new" in out
    assert "keep this" in out and "and this" in out
    assert "old objective" not in out


def test_missing_heading_refuses_rather_than_appending():
    with pytest.raises(ValueError, match="workspace section not found"):
        replace_h2_section(BODY, "No Such Section", "x")


@pytest.mark.parametrize("content", [
    r"Let \gamma denote the learning rate.",
    r"Use \1 to refer to the first item.",
    r"A Windows path: C:\temp\notes",
    r"Backslash pair: \\ and a dollar $x$",
])
def test_author_text_is_placed_not_interpreted(content):
    """Regex substitution read backslashes as group references and crashed."""
    out = replace_h2_section(BODY, "Objective", content)
    assert content in out


def test_a_fenced_code_block_is_not_a_section_boundary():
    body = (
        "## Objective\n\n```md\n## Not a heading\nstill fenced\n```\n\n"
        "## Next Action\n\nkeep\n"
    )
    out = replace_h2_section(body, "Objective", "replaced")
    assert "## Not a heading" not in out, "fenced text must not survive as a heading"
    assert out.count("```") == 0, "the fence belonged to the replaced section"
    assert "keep" in out


def test_a_fence_in_an_untouched_section_survives_intact():
    body = (
        "## Objective\n\n```md\n## Not a heading\nstill fenced\n```\n\n"
        "## Next Action\n\nold\n"
    )
    out = replace_h2_section(body, "Next Action", "new")
    assert out.count("```") == 2
    assert "## Not a heading" in out and "still fenced" in out


def test_tilde_fences_are_honoured_too():
    body = "## Objective\n\n~~~\n## Not a heading\n~~~\n\n## Next Action\n\nkeep\n"
    _, sections = parse_sections(body)
    assert [s.heading for s in sections] == ["Objective", "Next Action"]


def test_sections_round_trip_without_drift():
    """Replacing a section with its own content must be a no-op."""
    _, sections = parse_sections(BODY)
    out = BODY
    for section in sections:
        out = replace_h2_section(out, section.heading, "\n".join(section.lines).strip())
    assert out == BODY
