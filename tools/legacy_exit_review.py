#!/usr/bin/env python3
"""Read-only review of the frozen pre-v3 ``legacy/`` tree.

This tool answers a deliberately narrow question: which files in ``legacy/``
already have a migration record or a byte-for-byte copy in LearningOS, and
which files still deserve a human look before the user removes that tree?

It never writes, moves, or deletes files. It also never enters ``Job/``. The
default legacy root is the sibling at ``<semestercontext>/legacy``; pass an
explicit path after moving LearningOS elsewhere.

Examples::

    .venv/bin/python tools/legacy_exit_review.py
    .venv/bin/python tools/legacy_exit_review.py --json
    .venv/bin/python tools/legacy_exit_review.py --legacy-root /path/to/legacy
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LEARNING_OS_ROOT = ROOT.parent
DEFAULT_LEGACY_ROOT = ROOT.parents[1] / "legacy"

IGNORED_NAMES = {".DS_Store"}
IGNORED_PREFIXES = (".fuse_hidden",)
REPOSITORY_SKIP_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "generated",
    "node_modules",
}

# These are mechanics/specifications replaced in-place by v3, not learner
# material. Keeping this list here makes the judgment visible and reviewable.
SUPERSEDED_RULES: tuple[tuple[str, str], ...] = (
    ("MD-FILE-INDEX.md", "generated/manifest.json + los search/inspect"),
    ("lychee.toml", "tools/validate.py --online"),
    ("tools/check_links.py", "tools/validate.py"),
    ("Masters-Planning/tools/check_system.py", "tools/validate.py"),
    ("Plans/LearningOS_v3_Rebuild_Package.zip", "system/SPEC-README.md"),
    ("Plans/LearningOS_v3_Architecture_Revisions.md", "system/ARCHITECTURE.md"),
    ("Plans/LearningOS_v3_Spec/", "system/"),
    ("Plans/LEARNING-OS-PHILOSOPHY.md", "system/PHILOSOPHY.md"),
    ("Masters-Planning/skills-src/", "system/skills/"),
    ("Plans/archive/Chat5_DBT_Plan.md", "the archived plan's own superseded status; source PDFs preserved in LearningOS/materials/_unsorted/Legacy-DBT-review"),
    ("Plans/archive/SoSe2026_Praxisplan.md", "the archived plan's own superseded status recorded in legacy/Plans/README.md"),
)

JOB_MARKERS = (
    "/job/",
    "bifold-deem-job",
    "stratum-optimizer",
)


@dataclass(frozen=True)
class ReviewItem:
    path: str
    size: int
    sha256: str
    disposition: str
    evidence: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _is_ignored(path: Path) -> bool:
    return path.name in IGNORED_NAMES or path.name.startswith(IGNORED_PREFIXES)


def _iter_files(base: Path, *, repository: bool = False):
    for path in sorted(base.rglob("*")):
        if path.is_symlink() or not path.is_file() or _is_ignored(path):
            continue
        if repository and any(part in REPOSITORY_SKIP_PARTS for part in path.parts):
            continue
        yield path


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalise_old_path(value: str) -> str:
    value = value.strip().strip('"')
    if value.startswith("legacy/"):
        value = value.removeprefix("legacy/")
    return value.rstrip("/")


def _path_is_within(path: str, mapped: str) -> bool:
    """Return true for exact file maps and directory-prefix maps."""
    return path == mapped or path.startswith(mapped + "/")


def _mapping_for(path: str, rows: list[dict[str, str]]) -> dict[str, str] | None:
    matches = []
    for row in rows:
        old = _normalise_old_path(row.get("old_path", ""))
        if old and _path_is_within(path, old):
            matches.append((len(old), row))
    return max(matches, default=(0, None), key=lambda pair: pair[0])[1]


def _superseded_by(path: str) -> str | None:
    for old, replacement in SUPERSEDED_RULES:
        old = old.rstrip("/")
        if _path_is_within(path, old):
            return replacement
    return None


def _is_job_boundary(path: str) -> bool:
    lowered = f"/{path.lower()}"
    return any(marker in lowered for marker in JOB_MARKERS)


def _copy_index(legacy_files: list[Path]) -> dict[tuple[int, str], list[str]]:
    """Index only candidate-size files, avoiding a full materials re-hash."""
    wanted_sizes = {path.stat().st_size for path in legacy_files}
    candidates: dict[int, list[tuple[Path, str]]] = defaultdict(list)

    roots = ((ROOT, True), (LEARNING_OS_ROOT / "materials", False))
    for base, repository in roots:
        if not base.is_dir():
            continue
        for path in _iter_files(base, repository=repository):
            size = path.stat().st_size
            if size not in wanted_sizes:
                continue
            if path.is_relative_to(ROOT):
                label = path.relative_to(ROOT).as_posix()
            else:
                label = "LearningOS/" + path.relative_to(LEARNING_OS_ROOT).as_posix()
            candidates[size].append((path, label))

    index: dict[tuple[int, str], list[str]] = defaultdict(list)
    for size, paths in candidates.items():
        for path, label in paths:
            index[(size, _sha256(path))].append(label)
    return index


def review(legacy_root: Path) -> list[ReviewItem]:
    legacy_files = list(_iter_files(legacy_root))
    copies = _copy_index(legacy_files)
    path_map = _load_csv(ROOT / "migration" / "path-map.csv")
    material_map = _load_csv(ROOT / "migration" / "material-moves.csv")

    results: list[ReviewItem] = []
    for source in legacy_files:
        rel = source.relative_to(legacy_root).as_posix()
        size = source.stat().st_size
        digest = _sha256(source)

        mapped = _mapping_for(rel, path_map)
        if mapped:
            target = mapped.get("new_path", "").strip()
            kind = mapped.get("type", "mapped").strip()
            phase = mapped.get("decided_in_phase", "").strip()
            disposition = "retired-by-record" if target.upper().startswith("DELETED") else "integrated"
            evidence = f"migration/path-map.csv ({kind}; {phase}) → {target}"
        else:
            moved = _mapping_for(rel, material_map)
            if moved:
                disposition = "integrated-material"
                evidence = f"migration/material-moves.csv → {moved.get('new_path', '').strip()}"
            elif copies.get((size, digest)):
                disposition = "preserved-copy"
                evidence = "byte-identical: " + ", ".join(copies[(size, digest)][:3])
            elif replacement := _superseded_by(rel):
                disposition = "superseded-system"
                evidence = f"replaced by {replacement}"
            elif _is_job_boundary(rel):
                disposition = "job-boundary-review"
                evidence = "requires a separate explicit Job review; Job was not scanned"
            else:
                disposition = "manual-review"
                evidence = "no migration row, replacement rule, or byte-identical LearningOS copy"

        results.append(ReviewItem(rel, size, digest, disposition, evidence))
    return results


def _human_size(value: int) -> str:
    units = ("B", "KB", "MB", "GB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    raise AssertionError("unreachable")


def _markdown(items: list[ReviewItem], legacy_root: Path, *, details: bool) -> str:
    counts = Counter(item.disposition for item in items)
    total_bytes = sum(item.size for item in items)
    needs_attention = [
        item for item in items
        if item.disposition in {"manual-review", "job-boundary-review"}
    ]
    lines = [
        "# Legacy exit review",
        "",
        f"Legacy root: `{legacy_root}`",
        "",
        f"Reviewed **{len(items)} files** ({_human_size(total_bytes)}). "
        f"**{len(needs_attention)} need a human decision** before deletion.",
        "",
        "| Disposition | Files |",
        "|---|---:|",
    ]
    for disposition in sorted(counts):
        lines.append(f"| {disposition} | {counts[disposition]} |")

    lines.extend([
        "",
        "## Human decisions",
        "",
    ])
    if not needs_attention:
        lines.append("None. The audit found no unreviewed files.")
    else:
        lines.extend(["| File | Size | Why it is here |", "|---|---:|---|"])
        for item in needs_attention:
            lines.append(
                f"| `{item.path}` | {_human_size(item.size)} | {item.evidence} |"
            )

    if details:
        lines.extend(["", "## Complete inventory", ""])
        for disposition in sorted(counts):
            lines.extend([f"### {disposition}", ""])
            for item in (entry for entry in items if entry.disposition == disposition):
                lines.append(f"- `{item.path}` — {item.evidence}")
            lines.append("")

    lines.extend([
        "",
        "This report is evidence, not a deletion command. The tool never enters `Job/` "
        "and never writes, moves, or removes anything.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--legacy-root",
        type=Path,
        default=DEFAULT_LEGACY_ROOT,
        help=f"frozen legacy tree (default: {DEFAULT_LEGACY_ROOT})",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--details", action="store_true", help="include the complete inventory")
    args = parser.parse_args()

    legacy_root = args.legacy_root.expanduser().resolve()
    if not legacy_root.is_dir():
        parser.error(f"legacy root not found: {legacy_root}")

    items = review(legacy_root)
    if args.json:
        payload = {
            "legacy_root": str(legacy_root),
            "counts": dict(sorted(Counter(item.disposition for item in items).items())),
            "items": [asdict(item) for item in items],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_markdown(items, legacy_root, details=args.details), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
