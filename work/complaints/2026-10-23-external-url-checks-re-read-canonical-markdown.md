# External URL audit re-reads canonical Markdown already cached

Task: observe validation behavior during `--online` runs (Core HEAD `1d80aa03e674131a67bda37db04fce2d8076c62a`).

## Workflow and impact

`ChecksGenerated.check_external_urls()` (tools/learning_os/derive/validation/generated.py:155) collects HTTP(S) URLs from three sources: loaded canonical records, the projected manifest, and a Markdown-link sweep over every `.md` file in `CANONICAL_TREES`. The third sweep does `f.read_text(...)` on every canonical Markdown file — the same files already read once and cached by `Validator._canonical_texts()` (tools/learning_os/derive/validation/core.py:132).

Impact: every `--online` validation pass performs a second full read of ~1,200 canonical Markdown files that are already resident in memory from `_canonical_text_cache`. Each file incurs an extra `open()`+`read()` syscall pair. For a real checkout this is redundant I/O on every `--online` run, and it scales linearly with repository size. The cache exists precisely to avoid this ("read once per run"), so this sweep defeats its purpose for Markdown links.

## Reproduction and bounded proof

Run validation with `--online` on any checkout that has canonical Markdown files containing http(s) links:

```
python tools/validate.py --online --compact
```

The Markdown sweep at generated.py:169-174 calls `f.read_text()` independently of `_canonical_texts()`. No cached text is reused. Instrumenting `read_bytes_inside` (as tests/test_compute_once.py does) would show each canonical `.md` read twice per `--online` run: once by `_canonical_texts()` (used by `check_links`, `check_ownership`, etc.) and once by `check_external_urls()`.

This only affects `--online` mode; offline `make check` does not invoke `check_external_urls`. Verified by reading generated.py lines 155-183 and core.py lines 132-154 — no cache access occurs in the Markdown sweep.

## Smallest improvement and acceptance

Replace the independent `base.rglob("*.md")` + `f.read_text()` sweep with a filter over `self._canonical_texts()`:

```python
for f, text in self._canonical_texts():
    if f.suffix != ".md":
        continue
    for target in MD_LINK_RE.findall(text):
        if target.startswith(("http://", "https://")):
            urls.add(target)
```

Safeguards to retain:
- Garden and quarantine exclusions: `_canonical_texts()` already excludes them (core.py:150), so the filter is equivalent.
- `errors="replace"` read handling: `_canonical_texts()` uses the same encoding error handling (core.py:152), so behavior is unchanged.
- The `--online` network audit itself (`ThreadPoolExecutor`, `_probe_external_url`) is untouched — only the URL collection source changes.

Acceptance:
- `make check` unchanged (offline path unaffected).
- `--online` runs produce identical URL findings and identical `URL-*` issue output.
- No additional file reads: instrumented `read_bytes_inside` shows each canonical `.md` read once per `--online` run, not twice.

Filed: not yet filed. Evidence retained locally; no implementation change made during this task.