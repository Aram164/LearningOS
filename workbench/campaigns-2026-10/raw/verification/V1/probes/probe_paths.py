#!/usr/bin/env python3
"""V1 probe: check every backticked path-like reference in DEVELOPER.md and
system/developer/changing-contracts.md (files the system-map guard does not
read) against the checkout. Also re-sweeps the guarded files for paths outside
the guard's prefix list (e.g. src/, contracts/, generated/)."""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
BASE = ROOT / "system"

DOCS = [
    "DEVELOPER.md",
    "developer/changing-contracts.md",
    "developer/CODEMAP.md",
    "developer/C4.md",
    "developer/FLOWS.md",
]

# Prefixes the system-map guard already existence-checks in CODEMAP/C4/FLOWS.
GUARDED_PREFIXES = ("tools/", "tests/", "system/", "pyproject.toml")


def spans(text: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", text)


def looks_like_path(ref: str) -> bool:
    if " " in ref.strip() and "/" not in ref:
        return False
    return bool(re.match(r"^[\w./@-]+(\.[\w]+)?(/[\w./@-]+)*$", ref)) and (
        "/" in ref or ref.endswith((".py", ".md", ".yaml", ".json", ".toml", ".ts", ".txt"))
    )


for doc in DOCS:
    text = (BASE / doc).read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        for ref in spans(line):
            if not looks_like_path(ref):
                continue
            if doc != "DEVELOPER.md" and doc != "developer/changing-contracts.md" \
                    and ref.startswith(GUARDED_PREFIXES):
                continue  # guard already checks existence for these files
            target = ROOT / ref
            status = "EXISTS" if target.exists() else "MISSING"
            print(f"{doc}:{lineno}: `{ref}` -> {status}")
