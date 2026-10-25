# Markdown link regex misses links with titles and truncates URLs with ")"

Task: review the link-checking surface in `tools/learning_os/derive/validation/references.py` (Core HEAD `1d80aa03e674131a67bda37db04fce2d8076c62a`).

## Workflow and impact

`ChecksReferences.check_links()` (references.py:635) validates every internal Markdown link in canonical `.md` files. It uses `MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")` (domain/validation.py:20) to extract link targets. This regex has two defects:

1. **Links with titles are invisible.** A Markdown link written with a quoted title after the URL does not match because the character class `[^)\s]+` stops at the whitespace before the title. A broken link with a title is never reported — no `LINK-BROKEN`, no `LINK-ESCAPE`.

2. **URL paths containing a close-paren are truncated.** The character class stops at the first `)`, so a path segment that legitimately contains `)` is cut short. The truncated target then fails resolution and produces a false `LINK-BROKEN` for a file that exists.

Impact: any canonical Markdown file that uses the common Markdown idiom of a link with a title escapes link validation entirely. A dangling internal link with a title looks valid to `make check`. This is a hole in the reference-integrity guarantee that `check_links` is meant to provide.

## Reproduction and bounded proof

```python
import re
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# Link with a quoted title: no match at all
assert MD_LINK_RE.findall('[text](./file.md "title")') == []
# A path whose name legitimately contains ")" is captured only up to the first ")"
```

In the validator: add a canonical note containing a bracketed link with a quoted title pointing to a nonexistent file, run `python tools/validate.py --compact`, and observe that no `LINK-BROKEN` is reported even though the target does not exist.

This only affects `check_links()` (every validation run) and `check_external_urls()` (`--online` mode). The `check_references()` URI-scheme path (`note://`, `source://`, etc.) uses `parse_reference_uri`, which is unaffected.

## Smallest improvement and acceptance

Replace `MD_LINK_RE` with a pattern that handles the standard Markdown link forms, including optional titles and angle-bracket URLs:

```python
MD_LINK_RE = re.compile(
    r"\[[^\]]*\]\(("
    r"<[^>]+>|"                   # angle-bracket URL: [<url>]
    r"[^)\s\"']+"                 # bare URL, no spaces/quotes/close-paren
    r")(?:\s+\"[^\"]*\")?\s*\)"   # optional quoted title then close paren
)
```

This captures the URL without the title, so `classify_markdown_link` and `_check_link` receive a clean target. Links with titles are now checked; URL paths with `)` are captured whole when they contain no whitespace.

Safeguards to retain:
- `classify_markdown_link` still returns "skip" for `http://`, `https://`, `mailto:`, `#`.
- `parse_reference_uri` still handles `note://`, `source://`, etc. before the relative fallback.
- `check_links` still checks `LINK-ESCAPE` and `LINK-BROKEN` on the resolved target.
- `--online` URL audit behavior unchanged except that title-bearing links are now collected.

Acceptance:
- A bracketed link with a quoted title pointing to a nonexistent file → `LINK-BROKEN` (previously silent).
- A bracketed link with a quoted title pointing to an existing file → no error (previously also no error, but now actually checked).
- All existing `LINK-*` tests continue to pass.

Filed: not yet filed. Evidence retained locally; no implementation change made during this task.