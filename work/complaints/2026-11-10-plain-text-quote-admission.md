# Plain Markdown quotations refused during G8 route binding

During the 2026-11-10 coherence completion, `source-python-depth-drills` guides could not supply honest evidence for new local routes. On Core 0c45592, `AnchorReader.verify_quote` treated every `.md`/`.txt` as a timestamped transcript and refused a real guide excerpt for missing video/grid/duration metadata; `verify_unreadable` also refused because readable text requires a quote. Reproduction and material observations are retained in the external dated coherence-finish evidence directory.

Repair 9aeb032 adds explicit one-based inclusive line bounds, with exact owning file, registered digest, locator span and changed-byte checks. Video/transcript material retains its strict timestamp path and cannot use line evidence. Focused domain, anchor and gateway tests passed; final paired acceptance is still pending.

Acceptance: a real plain-text excerpt admits only at the specified file/lines; wrong text, file, range, digest, malformed UTF-8, changed bytes and transcript bypass refuse. No raw excerpt is persisted in canonical lineage. GitHub issue: pending duplicate search and filing after the main work.
