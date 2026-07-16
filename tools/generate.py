#!/usr/bin/env python3
"""Learning OS v3 generator (BUILD-SPEC Step 5).

    python tools/generate.py            # rebuild all generated outputs

Produces, deterministically except timestamps: generated/manifest.json,
concept-index.md, source-index.md (incl. per-lecture and per-concept selector
views), module-view.md, coordination-view.md, backlinks.json, reports/health.md.

Generated files are gitignored, carry a warning header, and are never canonical
inputs. Delete generated/ at any time; this command rebuilds everything.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.genout import generate_all, write_outputs  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    repo = load_repo(root)
    outputs = generate_all(repo)
    write_outputs(repo, outputs)
    for rel in sorted(outputs):
        print(f"wrote generated/{rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
