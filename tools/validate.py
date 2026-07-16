#!/usr/bin/env python3
"""Learning OS v3 unified validator (BUILD-SPEC Step 4).

    python tools/validate.py            # full offline validation
    python tools/validate.py --online   # + external URL audit

Enforces system/schema/*.schema.json plus every rule in system/VALIDATION.md.
Replaces the legacy check_links.py / check_system.py / routine offline lychee runs.
Writes generated/reports/validation-report.md; exit code 1 on errors.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.loader import load_repo  # noqa: E402
from learning_os.rules import render_report, validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true",
                        help="also audit external URLs (link rot never blocks offline validation)")
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--no-report", action="store_true",
                        help="do not write generated/reports/validation-report.md")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    repo = load_repo(root)
    issues = validate(repo, online=args.online)

    errors = [i for i in issues if i.severity == "E"]
    warnings = [i for i in issues if i.severity == "W"]
    for issue in issues:
        print(issue)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) — "
          f"{'FAIL' if errors else 'OK'}")

    if not args.no_report:
        generated_at = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
        report_dir = root / "generated" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "validation-report.md").write_text(
            render_report(issues, generated_at), encoding="utf-8")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
