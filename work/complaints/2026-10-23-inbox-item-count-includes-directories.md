# Inbox item count includes directories, overstating unrouted captures

Task: review the manifest projection's `count_inbox_items` (Core HEAD `1d80aa03e674131a67bda37db04fce2d8076c62a`).

## Workflow and impact

`count_inbox_items()` (tools/learning_os/derive/projection/manifest.py:238) counts entries in `work/inbox/` using `inbox_dir.iterdir()`, which returns **all** entries — files *and* directories. It then filters only dot-prefixed names, leaving subdirectories in the count.

Impact: a folder drop in `work/inbox/` (a directory containing multiple captured files) is counted as **one** inbox item, inflating the manifest's `inbox_items` count. More importantly, any subdirectory deliberately placed in `work/inbox/` is counted as an item even though it is not a file capture. The manifest's counts section is consumed by interfaces and the health report, so an inflated count misrepresents the inbox backlog.

This only affects the manifest projection (`make views` / `projection.generate`), not validation or write paths. The `inbox-stale` advisory (`advisories.py`) correctly filters to files only, so the inconsistency is between the manifest count and the advisory: a directory in the inbox is counted as an item by the manifest but never flagged as stale by the advisory.

## Reproduction and bounded proof

```python
from pathlib import Path
import tempfile
from learning_os.derive.projection.manifest import count_inbox_items

tmp = Path(tempfile.mkdtemp())
inbox = tmp / "work" / "inbox"
inbox.mkdir(parents=True)
(inbox / "capture.md").write_text("capture\n")
(inbox / "folder-drop").mkdir()
(inbox / "folder-drop" / "nested.txt").write_text("nested\n")

assert count_inbox_items(tmp) == 2   # 1 file + 1 directory = 2 (bug: should be 1)
```

Expected: `1` (one file item). Actual: `2` (one file + one directory counted as an item).

## Smallest improvement and acceptance

Change `count_inbox_items` to count only regular files, matching the `inbox_stale_issues` rule in `advisories.py` (which skips symlinks and non-files):

```python
def count_inbox_items(root: Path) -> int:
    inbox_dir = root / "work" / "inbox"
    if not inbox_dir.is_dir():
        return 0
    return len([
        item for item in inbox_dir.iterdir()
        if item.is_file() and not item.is_symlink() and not item.name.startswith(".")
    ])
```

Safeguards to retain:
- Dot-prefixed entries are still skipped (same as before).
- Symlinks are still skipped (same as `inbox_stale_issues`).
- Missing inbox returns 0 (same as before).
- Folder drops (directories) are no longer counted as items — they are resolved via `inbox.resolve`, not counted individually.

Acceptance:
- `count_inbox_items` returns 1 for a single file in `work/inbox/` (was 2 when a directory was also present).
- A directory in `work/inbox/` contributes 0 to the count.
- All existing manifest/counts tests continue to pass.

Filed: not yet filed. Evidence retained locally; no implementation change made during this task.