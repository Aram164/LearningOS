"""C1-E: revising one coordination section must not re-flow the others.

capabilities.yaml, coordination.section.revise: "one existing coordination
section; frontmatter and other section content are preserved".
`replace_h2_section` re-serialises the WHOLE document through
`render.serialise`, which forces exactly one blank line after every
heading and trims every section's edges — so in a hand-authored file
whose Priorities section has no blank line after its heading, an
unrelated Commitments edit rewrites the Priorities section too. The
existing test in test_coordination_revision.py compares other sections
with `.strip()` and cannot see this. Fix-agnostic: any edit mechanism
that leaves the other sections' parsed lines untouched passes.
"""

from __future__ import annotations

from gateway_helpers import approved_v2_envelope, file_sha256, run_v2_capability

from learning_os.domain.render import parse_sections

PATH = "work/COORDINATION.md"


def test_other_sections_keep_their_parsed_lines(mini_repo):
    path = mini_repo / PATH
    original = path.read_text(encoding="utf-8")
    reshaped = original.replace("## Priorities\n\n(none)", "## Priorities\n(none)")
    assert reshaped != original, "the fixture variant under test is missing"
    path.write_text(reshaped, encoding="utf-8")
    before = {s.heading: list(s.lines) for s in parse_sections(reshaped)[1]}

    envelope = approved_v2_envelope(
        mini_repo, capability="coordination.section.revise",
        payload={"section": "Commitments", "text": "Cover the AMLS resit plan.",
                 "expected_content_sha256": file_sha256(path)},
        artifact_ids=["coordination"], idempotency_key="c1e-coordination-reflow")
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 0, result.stdout + result.stderr

    after = path.read_text(encoding="utf-8")
    after_sections = {s.heading: list(s.lines) for s in parse_sections(after)[1]}
    for heading, lines in before.items():
        if heading == "Commitments":
            continue
        assert after_sections.get(heading) == lines, (
            f"section {heading!r} was re-flowed by an unrelated section edit: "
            f"before {lines!r} != after {after_sections.get(heading)!r}")
