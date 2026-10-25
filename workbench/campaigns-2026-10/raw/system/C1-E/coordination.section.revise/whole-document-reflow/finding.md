# coordination.section.revise — applying one section's edit re-flows every other section's lines

**Capability:** `coordination.section.revise` (command; same mechanism
underlies `workspace.next-action.update`). **Severity:** minor. **Batch:**
C1-E, item L2-6, 2026-10-24.

## Command

`coordination.section.revise` applied through its reviewed
GatewayEnvelopeV2 (test: `test_whole_document_reflow.py`; clone copy
`tests/test_c1e_coordination_reflow.py`, registered in
`tests/group_map.py`, group `gateway`), against a hand-authored
`work/COORDINATION.md` whose Priorities section has no blank line after
its heading (`## Priorities` directly followed by `(none)`). Fails on
base `d6c47790` in 0.77s.

## Observed (verbatim)

The apply exits 0 and commits. The untouched Priorities section's parsed
lines change from `['(none)', '']` to `['', '(none)', '']` — the blank
line that was after its body is removed and one is inserted between its
heading and its body:

```
AssertionError: section 'Priorities' was re-flowed by an unrelated section edit:
before ['(none)', ''] != after ['', '(none)', '']
```

The existing test (`tests/test_coordination_revision.py:52-54`) compares
the other sections with `.strip()` per section, which is exactly why it
cannot see this. The same re-serialisation runs for
`workspace.next-action.update` (`handlers/admin.py:378-399`), whose
invariant reads "only the Next Action section content changes".

## Expected

`system/contracts/capabilities.yaml`, `coordination.section.revise`
invariant 1: "one existing coordination section; frontmatter and other
section content are preserved". The committed bytes of the other
sections are part of their content; nothing in the contract makes
blank-line normalization an accepted side effect, and the reviewed diff
presents the write as a single-section replacement.

## Root cause

`tools/learning_os/domain/render.py:84-103` (`serialise`) rebuilds the
whole document, forcing exactly one blank line after every heading
(`out.append("")`), trimming every section body's leading/trailing blank
lines, and dropping an all-blank preamble. `replace_h2_section`
(render.py:106-117) routes the entire document through it, so editing
one section re-serialises all the others; the handler stages the result
(`handlers/admin.py:311`). The module docstring (render.py:1-20) says
section replacement is done "by parsing the document into blocks,
mutating one block, and re-serialising" — the re-serialising half is
what reaches beyond the mutated block.

## Suggested fix

Splice instead of re-serialise: `parse_sections` already knows the exact
line range of the target section, so replace those lines in the original
text and leave every other byte untouched (frontmatter, preamble and
sibling sections pass through verbatim). Alternatively keep
`serialise` but have it emit untouched sections from their original
lines rather than from the normalized form. Either way the invariant
"other section content is preserved" holds byte-for-byte, and the
fix-agnostic test passes unchanged.
