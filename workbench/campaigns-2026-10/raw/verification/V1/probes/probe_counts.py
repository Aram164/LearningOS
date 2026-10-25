#!/usr/bin/env python3
"""V1 probe: the two required counts.

1. tools/learning_os/ modules that CODEMAP.md never mentions — rule: a module
   is "mentioned" when its file path (tools/learning_os/...) or its import name
   (learning_os.x.y) appears anywhere in system/developer/CODEMAP.md.
2. Component pages in system/developer/components/ that no test names — rule:
   the page identifier (e.g. "operation-pipeline") appears in no tests/**/*.py.
"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
codemap = (ROOT / "system/developer/CODEMAP.md").read_text()

mods = sorted((ROOT / "tools/learning_os").rglob("*.py"))
unmentioned = [m for m in mods
               if m.as_posix() not in codemap
               and m.as_posix()[:-3].replace("/", ".") not in codemap]
print(f"total .py modules under tools/learning_os: {len(mods)}")
print(f"CODEMAP never mentions: {len(unmentioned)}")

pages = sorted((ROOT / "system/developer/components").glob("*.md"))
test_texts = {t.relative_to(ROOT).as_posix(): t.read_text(errors="replace")
              for t in (ROOT / "tests").rglob("*.py")}
unnamed = []
for page in pages:
    ident = page.stem
    if not any(ident in txt for txt in test_texts.values()):
        unnamed.append(ident)
print(f"component pages: {len(pages)}")
print(f"pages no test names: {len(unnamed)}: {unnamed}")
